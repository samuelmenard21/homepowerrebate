#!/usr/bin/env python3
"""Newsletter content (2026-10-24). Two jobs, both built only from data we already keep.

  python3 scripts/build_newsletter.py welcome
      Writes data/newsletter/welcome.json: the 10 best guides for each region, picked from data/blog-index.json (the topic order there is the priority order).
      The lead router bundles it and sends it the moment someone subscribes. Re-run after build_blog_index.py and redeploy the Worker.

  python3 scripts/build_newsletter.py issue 2026-11
      Builds the monthly issue that goes out in that month (id = the month it is sent), from:
        - rebate-tracker/changes.json entries dated in the last ~5 weeks, plus "coming" entries dated in the next two months (the monthly check writes these),
        - /rebate-deadlines/ rows (data/rebate-deadlines.json) that fall in the next 45 days,
        - blog posts first committed in the previous month (git),
        - a link to the /data-release/<previous month>/ page, which lists every change with its source.
      Optional hand edits live in data/newsletter/<id>.override.json: {"subject", "preview", "intro", "drop": ["program name"], "items": [...], "posts": [...]}.
      Writes /embed/newsletter/<id>/ and /embed/newsletter/latest/ (noindex, no site menu): the web version of the email, with the issue data inside
      as JSON. The Worker reads /embed/newsletter/latest/ on the 2nd of each month and sends it only when its id is the current month and `ready` is true.
      `ready` needs at least 3 real items (changes or deadlines). Otherwise nothing is sent that month and the weekly summary says so.
"""
import html
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
e = html.escape
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
REGIONS = json.loads((ROOT / "data/regions.json").read_text())["regions"]
BY_CODE = {r["code"]: r for r in REGIONS}
NAME_TO_ABBR = {r["name"].lower(): r["abbr"] for r in REGIONS}
NAME_TO_ABBR.update({"bc": "BC", "british columbia": "BC"})
SECTION_ORDER = ["start", "avoid", "heat", "bills", "shell", "solar", "rank"]
TAGS = {"new": "NEW", "raised": "RAISED", "ended": "ENDED", "paused": "PAUSED", "cut": "CUT", "changed": "CHANGED", "coming": "COMING UP"}


def short(s, n):
    s = " ".join((s or "").split())
    if len(s) <= n:
        return s
    cut = s[:n - 1].rsplit(" ", 1)[0].rstrip(",;:. ")
    return cut + "…"


# ---------------------------------------------------------------- welcome
def welcome():
    idx = json.loads((ROOT / "data/blog-index.json").read_text())
    secs = {s["id"]: s["posts"] for s in idx["sections"]}
    posts, label_of = {}, {}
    for sid in SECTION_ORDER:
        for p in secs.get(sid, []):
            label = p["region"]
            abbr = NAME_TO_ABBR.get(label.lower())
            posts[p["slug"]] = {"t": p["title"], "d": short(p["desc"], 150), "r": abbr or label}
            label_of[p["slug"]] = (sid, label, abbr)

    def pick(match, limit, taken):
        out = []
        lists = [[p["slug"] for p in secs.get(sid, []) if match(label_of[p["slug"]])] for sid in SECTION_ORDER]
        i = 0
        while len(out) < limit and any(i < len(l) for l in lists):
            for l in lists:
                if i < len(l) and l[i] not in taken and len(out) < limit:
                    out.append(l[i])
                    taken.add(l[i])
            i += 1
        return out

    def everywhere(l):
        return l[1] == "Everywhere"

    def build(abbr, country):
        taken = set()
        got = pick(lambda l: l[2] == abbr, 6, taken) if abbr else []
        if country == "ca":
            got += pick(lambda l: l[1] == "Canada", 3, taken)
        elif country == "us":
            got += pick(lambda l: l[1] in ("United States", "MA and NY") and (abbr in ("MA", "NY") or l[1] == "United States"), 2, taken)
        got += pick(everywhere, 10 - len(got), taken)
        if len(got) < 10 and country == "ca":
            got += pick(lambda l: l[1] == "Canada", 10 - len(got), taken)
        return got[:10]

    by_region = {r["abbr"]: build(r["abbr"], r["country"]) for r in REGIONS}
    default = build(None, None)
    # Someone not on a region page: show the biggest guides for the two big audiences first, then everything general.
    used = {s for l in by_region.values() for s in l} | set(default)
    out = {"posts": {s: posts[s] for s in sorted(used)}, "by_region": by_region, "default": default}
    d = ROOT / "data/newsletter"
    d.mkdir(parents=True, exist_ok=True)
    (d / "welcome.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    thin = [a for a, l in by_region.items() if len(l) < 10]
    print(f"welcome.json: {len(by_region)} regions, {len(used)} guides." + (f" Under 10 guides: {thin}" if thin else ""))
    for a in ("BC", "ON", "CA", "PA", "MB"):
        print(a, [posts[s]["t"][:48] for s in by_region[a]][:10])


# ---------------------------------------------------------------- monthly issue
def tracker_region(code):
    """Tracker region code to (abbr or scope, display name)."""
    if code == "CA-FED":
        return "CA-FED", "Canada"
    if code == "US":
        return "US", "United States"
    for r in REGIONS:
        if r["abbr"] == code:
            return code, r["name"]
    return "ALL", "Everywhere"


def calc_url(abbr):
    for r in REGIONS:
        if r["abbr"] == abbr:
            return f"https://homepowerrebate.com/calculator/{r['code']}/"
    if abbr == "CA-FED":
        return "https://homepowerrebate.com/programs/national-heat-pump-rebate/"
    return "https://homepowerrebate.com/rebate-tracker/"


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)


def new_posts(start, end):
    """Blog posts first added to the repo between start and end."""
    idx = json.loads((ROOT / "data/blog-index.json").read_text())
    meta = {p["slug"]: (p["title"], p["region"], p["desc"]) for s in idx["sections"] for p in s["posts"]}
    try:
        out = git("log", f"--since={start.isoformat()}", f"--until={end.isoformat()}", "--diff-filter=A", "--name-only", "--format=", "--", "blog/*/index.html")
    except Exception:
        return []
    seen, posts = set(), []
    for line in out.splitlines():
        m = re.match(r"blog/([^/]+)/index\.html$", line.strip())
        if m and m.group(1) in meta and m.group(1) not in seen:
            seen.add(m.group(1))
            t, region, desc = meta[m.group(1)]
            posts.append({"t": t, "d": short(desc, 140), "r": NAME_TO_ABBR.get(region.lower(), region), "region": region, "url": f"https://homepowerrebate.com/blog/{m.group(1)}/"})
    return posts


def issue(iid):
    y, m = map(int, iid.split("-"))
    send_day = date(y, m, 2)
    prev_end = date(y, m, 1)
    prev_start = (prev_end - timedelta(days=1)).replace(day=1)
    prev_id = f"{prev_start.year}-{prev_start.month:02d}"
    items, seen_deadline = [], set()

    tr = json.loads((ROOT / "rebate-tracker/changes.json").read_text())["entries"]
    for x in tr:
        try:
            d = datetime.strptime(x["date"], "%Y-%m-%d").date()
        except ValueError:
            continue  # month-only or year-only entries have no day to place them
        recent = send_day - timedelta(days=36) <= d <= send_day
        soon = x["status"] == "coming" and send_day <= d <= send_day + timedelta(days=62)
        if not (recent or soon):
            continue
        abbr, name = tracker_region(x["region"])
        deadline = x.get("deadline")
        tag = "CLOSING SOON" if deadline and send_day <= datetime.strptime(deadline, "%Y-%m-%d").date() <= send_day + timedelta(days=45) else TAGS.get(x["status"], "CHANGED")
        if deadline:
            seen_deadline.add((abbr, deadline))
        body = " ".join(filter(None, [x["change"], x.get("instead", "")]))
        items.append({"tag": tag, "r": abbr, "region": name, "title": x["program"], "body": body, "url": calc_url(abbr), "source": x.get("source", ""),
                      "rank": 0 if tag == "CLOSING SOON" else 1})

    dl = json.loads((ROOT / "data/rebate-deadlines.json").read_text())["rows"]
    for x in dl:
        d = datetime.strptime(x["date"], "%Y-%m-%d").date()
        if not (send_day <= d <= send_day + timedelta(days=45)):
            continue
        abbr, name = tracker_region(x["region"])
        if (abbr, x["date"]) in seen_deadline:
            continue
        items.append({"tag": "CLOSING SOON", "r": abbr, "region": name, "title": f'{x["upgrade"]} deadline: {MONTHS[d.month - 1]} {d.day}', "body": x["what"],
                      "url": "https://homepowerrebate.com" + x["page"], "source": "", "rank": 0})

    posts = new_posts(prev_start, prev_end)[:6]
    ov_path = ROOT / f"data/newsletter/{iid}.override.json"
    ov = json.loads(ov_path.read_text()) if ov_path.exists() else {}
    drop = {s.lower() for s in ov.get("drop", [])}
    items = [i for i in items if i["title"].lower() not in drop] + ov.get("items", [])
    posts = ov.get("posts", posts)
    items.sort(key=lambda i: i.get("rank", 1))

    month_name = MONTHS[m - 1]
    if ov.get("subject"):
        subject = ov["subject"]
    elif items:
        lead = items[0]
        more = len(items) - 1
        subject = f"{month_name} rebate update: {short(lead['title'], 52)}" + (f" and {more} more" if more else "")
    else:
        subject = f"{month_name} rebate update"
    data = {"id": iid, "ready": len(items) >= 3, "subject": subject, "preview": ov.get("preview") or short(" ".join(i["title"] for i in items[:3]), 110),
            "intro": ov.get("intro") or f"Here is what changed since last month, and what is closing soon. Every figure is read from the program's own page.",
            "items": items, "posts": posts, "release_url": f"https://homepowerrebate.com/data-release/{prev_id}/", "release_month": f"{MONTHS[prev_start.month - 1]} {prev_start.year}"}
    write_issue_page(data)
    print(f"issue {iid}: {len(items)} items, {len(posts)} new guides, ready={data['ready']}")
    print("subject:", subject)
    if not data["ready"]:
        print("Fewer than 3 items: the Worker will skip this month. Add items to data/newsletter/%s.override.json or fix the tracker." % iid)


def write_issue_page(d):
    rows = "".join(
        f'<h3 style="margin:22px 0 4px;font-size:17px;"><span style="font-size:11px;letter-spacing:.05em;color:#a15d10;">{e(i["tag"])}</span> · {e(i["region"])}<br>{e(i["title"])}</h3>'
        f'<p style="margin:0 0 6px;line-height:1.55;">{e(i["body"])}</p><p style="margin:0;font-size:14px;"><a href="{e(i["url"])}">See how it affects your home</a>'
        + (f' · <a href="{e(i["source"])}" rel="noopener">Official source</a>' if i.get("source") else "") + "</p>"
        for i in d["items"])
    posts = "".join(f'<li><a href="{e(p["url"])}">{e(p["t"])}</a></li>' for p in d["posts"])
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, follow"><title>{e(d["subject"])}</title></head>
<body style="margin:0;background:#f5efe5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:#0a2a2e;">
<div style="max-width:620px;margin:0 auto;padding:28px 18px;">
<p style="margin:0;font-size:13px;color:#6b7d80;">HomePowerRebate monthly update · web version</p>
<h1 style="font-family:Georgia,serif;font-weight:500;font-size:28px;margin:8px 0 10px;">{e(d["subject"])}</h1>
<p style="line-height:1.55;">{e(d["intro"])}</p>{rows}
{('<h2 style="font-family:Georgia,serif;font-weight:500;margin-top:32px;">New guides</h2><ul>' + posts + '</ul>') if posts else ''}
<p style="margin-top:28px;"><a href="{e(d["release_url"])}">Every program change in {e(d["release_month"])}, with sources</a></p>
<p style="font-size:13px;color:#6b7d80;margin-top:28px;">This page is the web copy of the monthly email. The emailed version is tailored to each subscriber's province or state.</p>
</div>
<script type="application/json" id="issue-data">{json.dumps(d, ensure_ascii=False).replace("</", "<\\/")}</script>
</body></html>
"""
    for sub in (d["id"], "latest"):
        p = ROOT / "embed/newsletter" / sub / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(page)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "welcome":
        welcome()
    elif len(sys.argv) >= 3 and sys.argv[1] == "issue" and re.fullmatch(r"\d{4}-\d{2}", sys.argv[2]):
        issue(sys.argv[2])
    else:
        sys.exit(__doc__)
