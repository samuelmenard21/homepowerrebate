#!/usr/bin/env python3
"""Weekly report for the federal heat pump rebate launch list (2026-10-17): are people seeing the box, and are they signing up?

Reads the production D1 database (homepowerrebate-outcomes) through wrangler:
- alerts: one row per signup (page carries ?src= when the visitor came from a shared or installer link)
- alert_views: how often the box was at least half on screen, per day and page (scripts in _partials/nav-footer.html)
Prints a Markdown report and saves it to data/reports/federal-alert/<date>.md (data/ is gitignored, so it stays local).
Search traffic (Search Console) is added by the weekly scheduled task with the seo CLI; this script covers the list itself.
Usage: python3 scripts/federal_alert_report.py [--days 7]"""
import argparse
import datetime as dt
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DB = "homepowerrebate-outcomes"


def q(sql):
    out = subprocess.run(["npx", "wrangler", "d1", "execute", DB, "--remote", "--json", "--command", sql],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return json.loads(out)[0]["results"]


def split(page):
    """'/ca/bc/?src=share-email' -> ('/ca/bc/', 'share-email'); no src -> '(site)'."""
    u = urlsplit(page or "")
    return u.path or "(unknown)", parse_qs(u.query).get("src", ["(site)"])[0]


def kind(path):
    if path == "/":
        return "Homepage"
    if path.startswith("/heat-pump-rebate-alert"):
        return "Share page"
    if path.startswith("/programs/national-heat-pump-rebate") or "federal" in path or path.startswith("/blog/should-you-wait"):
        return "Federal guide and articles"
    if path.startswith("/get-quotes"):
        return "Rebate finder"
    if path.startswith("/calculator/"):
        return "Calculators"
    if path.startswith("/programs/"):
        return "Program pages"
    if path.startswith("/blog/"):
        return "Blog posts"
    if path.endswith("/heat-pump/"):
        return "Heat pump pages"
    parts = path.strip("/").split("/")
    if len(parts) == 2:
        return "Province hubs" if parts[0] == "ca" else "Other"
    if len(parts) == 3:
        return "City hubs"
    if path == "/ca/":
        return "Province hubs"
    return "City and topic pages"


def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "n/a"


def table(head, rows):
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--days", type=int, default=7)
    days = a.parse_args().days
    today = dt.date.today()
    start = today - dt.timedelta(days=days)
    prev = start - dt.timedelta(days=days)
    s, p = start.isoformat(), prev.isoformat()

    total = q("SELECT COUNT(*) n FROM alerts WHERE list='federal-hp' AND unsubscribed=0")[0]["n"]
    unsub = q("SELECT COUNT(*) n FROM alerts WHERE list='federal-hp' AND unsubscribed=1")[0]["n"]
    signups = q(f"SELECT page, province, created_at FROM alerts WHERE list='federal-hp' AND created_at >= '{p}'")
    views = q(f"SELECT day, page, views FROM alert_views WHERE list='federal-hp' AND day >= '{p}'")
    by_prov = q("SELECT COALESCE(NULLIF(province,''),'(not given)') pr, COUNT(*) n FROM alerts WHERE list='federal-hp' AND unsubscribed=0 GROUP BY pr ORDER BY n DESC")

    now_s = [r for r in signups if r["created_at"][:10] >= s]
    prev_s = [r for r in signups if r["created_at"][:10] < s]
    now_v = [r for r in views if r["day"] >= s]
    prev_v = [r for r in views if r["day"] < s]
    v_now, v_prev = sum(r["views"] for r in now_v), sum(r["views"] for r in prev_v)

    lines = [f"# Federal heat pump rebate list: week to {today.isoformat()}", "",
             f"**{total:,} people on the list** ({unsub} unsubscribed). Goal: several thousand by launch (early 2027).", "",
             table(["", f"Last {days} days", f"{days} days before", "Change"], [
                 ["Box seen (half on screen)", f"{v_now:,}", f"{v_prev:,}", f"{v_now - v_prev:+,}"],
                 ["Signups", len(now_s), len(prev_s), f"{len(now_s) - len(prev_s):+}"],
                 ["Signups per 100 views", pct(len(now_s), v_now), pct(len(prev_s), v_prev), ""]]), ""]

    # by placement type
    agg = defaultdict(lambda: [0, 0])
    for r in now_v:
        agg[kind(split(r["page"])[0])][0] += r["views"]
    for r in now_s:
        agg[kind(split(r["page"])[0])][1] += 1
    rows = sorted(agg.items(), key=lambda x: -x[1][0])
    lines += ["## Where the box works (last %d days)" % days, "",
              table(["Placement", "Views", "Signups", "Rate"], [[k, f"{v:,}", n, pct(n, v)] for k, (v, n) in rows]), ""]

    # by source (shared links, installers)
    src = defaultdict(lambda: [0, 0])
    for r in now_v:
        src[split(r["page"])[1]][0] += r["views"]
    for r in now_s:
        src[split(r["page"])[1]][1] += 1
    lines += ["## Where visitors came from (?src=)", "",
              table(["Source", "Views", "Signups"], [[k, f"{v:,}", n] for k, (v, n) in sorted(src.items(), key=lambda x: (-x[1][1], -x[1][0]))]), ""]

    # top pages
    pages = defaultdict(lambda: [0, 0])
    for r in now_v:
        pages[split(r["page"])[0]][0] += r["views"]
    for r in now_s:
        pages[split(r["page"])[0]][1] += 1
    top = sorted(pages.items(), key=lambda x: (-x[1][0], -x[1][1]))[:15]
    lines += ["## Top pages (by views)", "", table(["Page", "Views", "Signups", "Rate"], [[k, f"{v:,}", n, pct(n, v)] for k, (v, n) in top]), ""]

    lines += ["## List by province (all time)", "", table(["Province", "People"], [[r["pr"], r["n"]] for r in by_prov]), ""]

    daily = defaultdict(int)
    for r in now_s:
        daily[r["created_at"][:10]] += 1
    lines += ["## Signups per day", "", table(["Day", "Signups"], [[d, daily.get(d, 0)] for d in
                                                                  [(start + dt.timedelta(days=i + 1)).isoformat() for i in range(days)]]), ""]
    if v_now == 0:
        lines += ["Note: no views were counted this week. Check that the shared JS is live (open a page with the box and look for a POST to leads.homepowerrebate.com/alert/seen) and that the lead router is deployed.", ""]

    report = "\n".join(lines)
    out = ROOT / "data" / "reports" / "federal-alert" / f"{today.isoformat()}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nSaved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
