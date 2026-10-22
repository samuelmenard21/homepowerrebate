#!/usr/bin/env python3
"""Monthly "what changed" data release: /data-release/YYYY-MM/ and the index /data-release/ (2026-10-22).
Built only from things we already keep:
  - data/verified-facts/*.json now vs the same files in the last commit before the month began (git show): programs added, status changes, amount changes,
    counts of open / starting soon / closed. Every row names the program, the region, the change and the official source.
  - powerscore-history/ snapshots (scripts/snapshot_powerscore.py) vs the current powerscore-data.json: biggest gainers and losers among cities in both,
    and how many cities were added. The comparison dates are printed on the page.
  - the download buttons build a CSV in the browser from the page's own JSON (the host does not serve .csv files).
Usage, once a month after the monthly rebate check and build_powerscore.py:
  python3 scripts/snapshot_powerscore.py && python3 scripts/build_data_release.py 2026-10 [--baseline <git ref>] && python3 scripts/post_steps.py
Then rerun scripts/generate_sitemap.py. Never edit the page by hand: fix the facts and rerun.
"""
import html
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import page_kit as kit  # noqa: E402

e = html.escape
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
FILE_REGION = {"bc-pages": "British Columbia", "bc-blog": "British Columbia", "bc-strata": "British Columbia", "us-ca": "California", "us-ca-la-munis": "California",
               "federal": "Canada (federal)", "general": "General", "ct": "Connecticut", "me": "Maine"}
STATUS_WORD = {"active": "Open", "upcoming": "Starts soon", "waitlist": "Waitlist", "paused": "Paused", "closed": "Closed", "check": "Confirm status", "info": "Note"}


def region_names():
    out = dict(FILE_REGION)
    for r in json.loads((ROOT / "data/regions.json").read_text())["regions"]:
        for f in r.get("facts_files", []):
            out.setdefault(f, r["name"])
    return out


def git_show(ref, rel):
    try:
        return json.loads(subprocess.check_output(["git", "show", f"{ref}:{rel}"], cwd=ROOT, stderr=subprocess.DEVNULL))
    except Exception:
        return None


def money_short(s, n=140):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[:n - 3].rstrip() + "..."


def fact_diff(baseline, names):
    added, status, amount = [], [], []
    now_c, then_c = {}, {}
    for f in sorted((ROOT / "data/verified-facts").glob("*.json")):
        stem, region = f.stem, names.get(f.stem, f.stem)
        new = json.loads(f.read_text())["facts"]
        old = (git_show(baseline, f"data/verified-facts/{f.name}") or {}).get("facts", [])
        o = {x["id"]: x for x in old}
        for x in new:
            now_c[x["status"]] = now_c.get(x["status"], 0) + 1
            row = {"region": region, "id": x["id"], "program": x["program"], "status": x["status"], "amount": x.get("amount", ""), "verified_on": x.get("verified_on", ""), "source": x.get("source_url", "")}
            if x["id"] not in o:
                added.append(row)
                continue
            p = o[x["id"]]
            if p.get("status") != x["status"]:
                status.append({**row, "was": p.get("status", "")})
            if " ".join((p.get("amount") or "").split()).casefold() != " ".join((x.get("amount") or "").split()).casefold():
                amount.append({**row, "was_amount": p.get("amount", "")})
        for x in old:
            then_c[x["status"]] = then_c.get(x["status"], 0) + 1
    return added, status, amount, now_c, then_c


def movers(start):
    hist = sorted(p for p in (ROOT / "powerscore-history").glob("20*.json"))
    prior = [p for p in hist if p.stem <= start.isoformat()]
    old_f = prior[-1] if prior else (hist[0] if hist else None)
    if not old_f:
        return None
    old = json.loads(old_f.read_text())
    new = json.loads((ROOT / "powerscore-data.json").read_text())

    def flat(d):
        return {f"{rk}/{slug}": {"label": c["label"], "url": c["url"], "region": r["label"], "overall": c["overall"], "usd": c.get("potential_usd", 0)} for rk, r in d["regions"].items() for slug, c in r["cities"].items()}
    a, b = flat(old), flat(new)
    both = [(k, a[k], b[k]) for k in a if k in b]
    delta = sorted([(round(nv["overall"] - ov["overall"], 1), k, ov, nv) for k, ov, nv in both], key=lambda r: -r[0])
    return {"old_date": old.get("generated"), "new_date": new.get("generated"), "old_n": len(a), "new_n": len(b), "both": len(both),
            "up": [d for d in delta if d[0] > 0][:10], "down": [d for d in sorted(delta, key=lambda r: r[0]) if d[0] < 0][:10], "same": sum(1 for d in delta if d[0] == 0),
            "added_regions": sorted(set(r["label"] for r in new["regions"].values()) - set(r["label"] for r in old["regions"].values()))}


def table(head, rows):
    return f'<div style="overflow-x:auto;"><table class="dr-table"><thead><tr>{"".join(f"<th>{h}</th>" for h in head)}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def src(u):
    return f' <a href="{e(u)}" rel="noopener" target="_blank">Source</a>' if u else ""


def build(ym, baseline):
    y, m = map(int, ym.split("-"))
    start = date(y, m, 1)
    names = region_names()
    added, status, amount, now_c, then_c = fact_diff(baseline, names)
    base_date = subprocess.check_output(["git", "log", "-1", "--format=%cs", baseline], cwd=ROOT, text=True).strip()
    mv = movers(start)
    month = f"{MONTHS[m - 1]} {y}"
    path = f"/data-release/{ym}/"
    total = sum(now_c.values())
    nregions = len({names.get(f.stem, f.stem) for f in (ROOT / "data/verified-facts").glob("*.json")})
    by_region = {}
    for r in added:
        by_region.setdefault(r["region"], []).append(r)
    opened_new = sum(1 for r in added if r["status"] == "active")

    headline = (f"<p>Since {e(base_date)}, we added {len(added)} programs and facts, changed the status of {len(status)} and changed the amount on {len(amount)}. "
                f"We now track {total} programs across {nregions} regions and funding sources, and {now_c.get('active', 0)} of them are open (it was {then_c.get('active', 0)} on {e(base_date)}). "
                f"{now_c.get('upcoming', 0)} start soon, {now_c.get('closed', 0)} are closed and {now_c.get('check', 0)} need their status confirmed.</p>")
    stat_cards = "".join(f'<div class="dr-stat"><b>{v}</b>{k}</div>' for v, k in [(len(added), "new programs and facts"), (len(status), "status changes"), (len(amount), "amount changes"), (now_c.get("active", 0), "open programs now")])

    st_rows = [f'<tr><td>{e(r["region"])}</td><td>{e(r["program"])}{src(r["source"])}</td><td>{e(STATUS_WORD.get(r["was"], r["was"]))} to <b>{e(STATUS_WORD.get(r["status"], r["status"]))}</b></td><td>{e(r["amount"])}</td><td>{e(r["verified_on"])}</td></tr>' for r in sorted(status, key=lambda r: (r["region"], r["program"]))]
    status_html = (table(["Region", "Program", "Change", "Amount", "Checked"], st_rows) if st_rows else "<p>No program changed status this month.</p>")
    am_rows = [f'<tr><td>{e(r["region"])}</td><td>{e(r["program"])}{src(r["source"])}</td><td>{e(money_short(r["was_amount"], 200))}</td><td><b>{e(money_short(r["amount"], 200))}</b></td><td>{e(STATUS_WORD.get(r["status"], r["status"]))}</td></tr>' for r in sorted(amount, key=lambda r: (r["region"], r["program"]))]
    amount_html = (table(["Region", "Program", "Was", "Now", "Status"], am_rows) if am_rows else "<p>No amount changed this month.</p>")
    reg_rows = [f'<tr><td>{e(k)}</td><td>{len(v)}</td><td>{sum(1 for r in v if r["status"] == "active")}</td></tr>' for k, v in sorted(by_region.items(), key=lambda kv: -len(kv[1]))]
    new_detail = ""
    for k, v in sorted(by_region.items()):
        opens = [r for r in v if r["status"] == "active" and r["amount"] and r["amount"].lower() not in ("n/a", "no amount")]
        if opens:
            new_detail += (f'<details><summary>{e(k)}: {len(opens)} open programs with an amount</summary>'
                           + table(["Program", "Amount", "Checked"], [f'<tr><td>{e(r["program"])}{src(r["source"])}</td><td>{e(money_short(r["amount"]))}</td><td>{e(r["verified_on"])}</td></tr>' for r in sorted(opens, key=lambda r: r["program"])]) + "</details>")
    if mv:
        def mrow(rows, sign):
            return [f'<tr><td><a href="{nv["url"]}">{e(nv["label"])}</a></td><td>{e(nv["region"])}</td><td>{ov["overall"]} to {nv["overall"]}</td><td>{sign}{abs(d)}</td></tr>' for d, k, ov, nv in rows]
        mv_html = (f"<p>We compare PowerScore snapshots from {e(str(mv['old_date']))} and {e(str(mv['new_date']))}. Of {mv['new_n']} cities scored now, {mv['both']} were also scored in the older snapshot and {mv['new_n'] - mv['both']} are new"
                   + (f" (new regions: {e(', '.join(mv['added_regions']))})" if mv["added_regions"] else "") + f". {mv['same']} of the {mv['both']} did not change.</p>"
                   + (f"<h3>Biggest gains</h3>{table(['City', 'Region', 'PowerScore', 'Change'], mrow(mv['up'], '+'))}" if mv["up"] else "<p>No city gained.</p>")
                   + (f"<h3>Biggest drops</h3>{table(['City', 'Region', 'PowerScore', 'Change'], mrow(mv['down'], '-'))}" if mv["down"] else "<p>No city dropped.</p>")
                   + '<p>Scores move when a program opens, closes or changes amount, and when the scoring yardstick moves with new cities. See the <a href="/powerscore/leaderboard/">national leaderboard</a> for today\'s ranking.</p>')
    else:
        mv_html = "<p>No earlier PowerScore snapshot is available to compare.</p>"

    payload = json.dumps({"status": status, "amount": amount, "added": added}, ensure_ascii=False).replace("</", "<\\/")
    article = f"""<p>This is our {month} data release: what changed in the home energy rebate programs we track, in one place, with a source for every row. It is built from our verified program facts, not from news. Cite it freely and link back.</p>
<div class="dr-stats">{stat_cards}</div>
{headline}
<h2 id="status">Programs that changed status</h2>
<p>A program moves between open, starting soon, waitlist, paused, closed and "confirm status" when its own page says so. We re-read the page before we change a status.</p>
{status_html}
<h2 id="amounts">Amounts that changed</h2>
<p>Maximums as the program publishes them. Many programs pay less than the maximum, depending on your home and income.</p>
{amount_html}
<h2 id="new">New programs and facts</h2>
<p>{len(added)} new entries, {opened_new} of them open today. Most come from regions and cities we added this month. Entries by region:</p>
{table(["Region", "New entries", "Open now"], reg_rows)}
{new_detail}
<h2 id="powerscore">PowerScore movers</h2>
{mv_html}
<h2 id="data">Get the data</h2>
<p>Download this month's changes as a spreadsheet file (CSV). It is made in your browser from the tables above.</p>
<p><button type="button" class="dr-btn" data-set="status">Status changes (CSV)</button> <button type="button" class="dr-btn" data-set="amount">Amount changes (CSV)</button> <button type="button" class="dr-btn" data-set="added">New programs (CSV)</button></p>
<h2 id="method">How we made this</h2>
<p>We compare our verified program facts today with the same facts in the last version saved before {e(base_date)}. A fact is a program, its status, its amount, its rules and the official page it came from, with the date we last read that page. We change a fact only after reading the official page. The monthly <a href="/rebate-tracker/">rebate tracker</a> lists dated news; this release lists what changed in our data. Past releases are on the <a href="/data-release/">data release page</a>.</p>
<h2 id="faq">Common questions</h2>
{kit.faq({"faq": FAQ})}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Cite as: HomePowerRebate, {month} data release, homepowerrebate.com{path}.</p>
<script>
(function () {{
  var D = {payload};
  var COLS = {{ status: ['region', 'program', 'was', 'status', 'amount', 'verified_on', 'source'], amount: ['region', 'program', 'was_amount', 'amount', 'status', 'verified_on', 'source'], added: ['region', 'program', 'status', 'amount', 'verified_on', 'source'] }};
  function q(v) {{ v = String(v == null ? '' : v); return /[",\\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }}
  document.addEventListener('click', function (ev) {{
    var b = ev.target.closest && ev.target.closest('.dr-btn'); if (!b) return;
    var k = b.dataset.set, cols = COLS[k], rows = [cols.join(',')].concat(D[k].map(function (r) {{ return cols.map(function (c) {{ return q(r[c]); }}).join(','); }}));
    var a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([rows.join('\\n')], {{ type: 'text/csv' }})); a.download = 'homepowerrebate-{ym}-' + k + '.csv'; document.body.appendChild(a); a.click(); a.remove();
  }});
}})();
</script>"""
    title = f"Home Rebate Changes in {month}: Data Release"
    desc = f"What changed in {month}: {len(added)} new programs, {len(status)} status changes and {len(amount)} amount changes, plus PowerScore movers. Sourced, with CSV downloads."
    hero = {"badge": "Data release", "h1": f"What changed in home energy rebates: {month}", "lead": f"{len(added)} new programs, {len(status)} status changes and {len(amount)} amount changes, with the official source for every row."}
    trail = [("Home", "/"), ("Data releases", "/data-release/"), (month, path)]
    lds = kit.ld_scripts([kit.article_ld(title, desc, kit_date(ym), path), kit.breadcrumb_ld(trail, home_slash=True), kit.faq_ld({"faq": FAQ})])
    kit.write_page(path, title, desc, lds, navfooter.render_nav("", ""), kit.breadcrumb(trail), kit.hero(hero), None, article, navfooter.render_footer("", "", "", path), extra_css=CSS)
    return {"ym": ym, "month": month, "path": path, "added": len(added), "status": len(status), "amount": len(amount), "open": now_c.get("active", 0)}


def kit_date(ym):
    return date.today().isoformat()


def index(entries):
    rows = "".join(f'<li><a href="{x["path"]}"><b>{e(x["month"])}</b></a>: {x["added"]} new programs, {x["status"]} status changes, {x["amount"]} amount changes ({x["open"]} programs open at the time)</li>' for x in sorted(entries, key=lambda x: x["ym"], reverse=True))
    article = f"""<p>Once a month we publish what changed in the home energy rebate programs we track across Canada and the United States: programs that opened or closed, amounts that moved, new programs added and the cities whose PowerScore moved most. Every row names the official source.</p>
<ul>{rows}</ul>
<p>Looking for dated news instead? See the <a href="/rebate-tracker/">rebate tracker</a>. To get the next release by email, use the monthly update form at the foot of this page.</p>"""
    title, desc = "Monthly Home Rebate Data Releases", "Every month: which home energy rebate programs opened, closed or changed amount, with sources and downloads."
    trail = [("Home", "/"), ("Data releases", "/data-release/")]
    lds = kit.ld_scripts([kit.breadcrumb_ld(trail, home_slash=True)])
    hero = {"badge": "Monthly", "h1": "Monthly home rebate data releases", "lead": "What changed, with a source for every row."}
    kit.write_page("/data-release/", title, desc, lds, navfooter.render_nav("", ""), kit.breadcrumb(trail), kit.hero(hero), None, article, navfooter.render_footer("", "", "", "/data-release/"))


FAQ = [("What does a status change mean?", "A program moved between open, starting soon, waitlist, paused, closed or confirm status because its own page said so. We re-read the page before we change it."),
       ("Why do so many new programs appear?", "We added new provinces, states and cities. Each new region brings its own programs, each with a source and a checked date."),
       ("Can I reuse this data?", "Yes. Please cite HomePowerRebate and link to this page. The CSV buttons give you the rows."),
       ("Are these amounts what I will get?", "No. They are the maximums programs publish. Your amount depends on your home, utility and income. Use the rebate calculator for your own numbers.")]

CSS = """<style>
.dr-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:16px 0}
.dr-stat{padding:14px;background:#fff7ea;border-left:4px solid var(--amber);border-radius:6px;font-size:14px}.dr-stat b{display:block;font-family:'Fraunces',Georgia,serif;font-size:30px;color:var(--teal-deep)}
.dr-table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--card-rule);margin:12px 0;font-size:14.5px}
.dr-table th,.dr-table td{padding:9px 11px;text-align:left;border-bottom:1px solid var(--card-rule);vertical-align:top}
.dr-table th{background:#f5efe5;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-soft)}
.dr-btn{min-height:44px;margin:4px 6px 4px 0;padding:0 16px;font:inherit;font-weight:700;color:#fff;background:#a4540a;border:0;border-radius:8px;cursor:pointer}
details{margin:8px 0}summary{cursor:pointer;font-weight:700;padding:6px 0}
</style>"""


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    ym = args[0]
    y, m = map(int, ym.split("-"))
    baseline = sys.argv[sys.argv.index("--baseline") + 1] if "--baseline" in sys.argv else subprocess.check_output(
        ["git", "log", f"--before={y}-{m:02d}-01 00:00", "-1", "--format=%H"], cwd=ROOT, text=True).strip()
    if not baseline:
        sys.exit("no commit before the start of the month")
    res = build(ym, baseline)
    known = {}
    f = ROOT / "data-release" / "releases.json"
    if f.exists():
        known = {x["ym"]: x for x in json.loads(f.read_text())}
    known[ym] = res
    f.parent.mkdir(exist_ok=True)
    f.write_text(json.dumps(list(known.values()), indent=1))
    index(list(known.values()))
    print("built", res)


if __name__ == "__main__":
    main()
