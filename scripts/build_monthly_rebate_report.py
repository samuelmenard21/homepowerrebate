#!/usr/bin/env python3
"""Monthly digest: /rebate-tracker/YYYY-MM/  built only from rebate-tracker/changes.json (each entry sourced).

  python3 scripts/build_monthly_rebate_report.py 2026-09 [--since 2026-07-01]
Covers entries dated from --since (default: first of the month) to the end of that month, plus deadlines
that fall in the next 60 days. Run after updating changes.json each month, then regenerate the sitemap.
"""
import html
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell, AUTHOR  # noqa: E402
from build_installer_rankings import BASE  # noqa: E402
from build_rebate_tracker import REGIONS, REGION_HUB, GROUPS, fmt_date, card  # noqa: E402

e = html.escape
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def parse(d):
    p = [int(x) for x in d.split("-")]
    return date(p[0], p[1] if len(p) > 1 else 1, p[2] if len(p) > 2 else 1)


def main():
    ym = sys.argv[1]
    y, m = map(int, ym.split("-"))
    start = date(y, m, 1)
    if "--since" in sys.argv:
        start = parse(sys.argv[sys.argv.index("--since") + 1])
    end = date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)
    data = json.loads((ROOT / "rebate-tracker" / "changes.json").read_text())
    checked = fmt_date(data["checked"])
    E_ = data["entries"]
    inwin = sorted([x for x in E_ if x["status"] != "coming" and start <= parse(x["date"]) <= end], key=lambda x: parse(x["date"]), reverse=True)
    soon = sorted([x for x in E_ if x["status"] == "coming" or (end < parse(x["date"]) <= end + timedelta(days=60))], key=lambda x: parse(x["date"]))
    label = f"{MONTHS[m - 1]} {y}"
    span = label if start.month == m and start.year == y else f"{MONTHS[start.month - 1]} to {label}"
    n = {s: sum(1 for x in inwin if x["status"] == s) for s in ("ended", "paused", "cut", "new", "raised", "changed")}
    closed = n["ended"] + n["paused"] + n["cut"]
    opened = n["new"] + n["raised"]
    path = f"/rebate-tracker/{ym}/"

    short = (f"{span}: {len(inwin)} rebate changes we track. {closed} programs ended, paused or were cut, {opened} were new or increased"
             f"{f', and {n['changed']} changed their rules' if n['changed'] else ''}. "
             f"{len(soon)} deadline{'s are' if len(soon) != 1 else ' is'} coming up: "
             + "; ".join(f"{x['program']} ({fmt_date(x['date'])})" for x in soon[:3]) + ".")

    rows = ""
    for r in REGIONS:
        rs = [x for x in inwin if x["region"] == r]
        if rs:
            hub = REGION_HUB.get(r)
            name = f'<a href="{hub}">{e(REGIONS[r])}</a>' if hub else e(REGIONS[r])
            rows += f"<tr><td>{name}</td><td>{len(rs)}</td><td>{e('; '.join(x['program'] for x in rs))}</td></tr>"
    table = f'<div style="overflow-x:auto;"><table style="min-width:520px;"><tr><th>Where</th><th>Changes</th><th>Programs</th></tr>{rows}</table></div>'

    todo = "".join(f'<li><b>{e(x["program"])}</b> ({e(fmt_date(x["date"]))}): {e(x["instead"])}</li>' for x in soon)
    sections = ""
    for g, title, color in GROUPS:
        items = [x for x in inwin if x["status"] == g]
        if items:
            sections += f'<h2 style="border-left:6px solid {color};padding-left:12px;">{e(title)} ({len(items)})</h2>' + "".join(card(x) for x in items)

    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/rebate-tracker/">Rebate tracker</a></li><li aria-current="page">{e(label)}</li></ol></nav>
<header class="hero"><div class="wrap"><h1>Home Energy Rebate Changes: {e(span)}</h1>
<p>What ended, what's new, and what to do before the next deadline. Last checked {checked}.</p><p class="meta">By {e(AUTHOR['name'])}</p></div></header>
<section class="body"><div class="wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> {e(short)}</p></div>
<h2>Deadlines and things to do next</h2>
<ul>{todo}</ul>
<h2>Changes by region</h2>
{table}
{sections}
<h2>How this list is made</h2>
<p>Every entry comes from an official program page, linked on each card. We re-check each source once a month. See the full running list on the <a href="/rebate-tracker/">rebate tracker</a>, or email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a> if something looks out of date.</p>
</div></section>"""
    css = ".rt-item{background:#fff;border:1px solid #d9d0c1;border-radius:10px;padding:16px 18px;margin:12px 0;}.rt-item h3{margin:4px 0 6px;font-size:18px;}.rt-item p{margin:6px 0;}.rt-meta{font-size:13px;font-weight:700;color:#1a3d42;text-transform:uppercase;letter-spacing:.04em;}"
    title = f"Home Energy Rebate Changes, {span}: What Ended and What's New"
    desc = f"{len(inwin)} home rebate changes, {span}: {closed} ended, paused or cut, {opened} new or raised, plus deadlines coming up. Each linked to its official source."
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "datePublished": data["checked"],
           "dateModified": data["checked"], "author": AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE},
           "mainEntityOfPage": BASE + path},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Rebate tracker", "item": BASE + "/rebate-tracker/"},
              {"@type": "ListItem", "position": 3, "name": label}]}]
    page = shell(title + " | HomePowerRebate", desc, path, "on", body, ld).replace("</style>", css + "</style>", 1)
    out = ROOT / "rebate-tracker" / ym / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"Wrote {path}: {len(inwin)} changes in window, {len(soon)} upcoming.")


if __name__ == "__main__":
    main()
