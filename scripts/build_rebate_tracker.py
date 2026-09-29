#!/usr/bin/env python3
"""Build /rebate-tracker/ from rebate-tracker/changes.json.

A dated, sourced list of home energy programs that ended, paused, were cut, or are new.
Monthly: re-check every source, edit changes.json (update "checked", add/modify entries),
re-run this script, regenerate the sitemap, push.
"""
import html
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell, AUTHOR  # noqa: E402
from build_installer_rankings import BASE  # noqa: E402

PATH = "/rebate-tracker/"
e = html.escape
REGIONS = {"BC": "British Columbia", "ON": "Ontario", "AB": "Alberta", "NS": "Nova Scotia", "CA-FED": "Canada (federal)",
           "US": "United States (federal)", "CA": "California", "NY": "New York", "MA": "Massachusetts"}
REGION_HUB = {"BC": "/ca/bc/", "ON": "/ca/on/", "AB": "/ca/ab/", "NS": "/ca/ns/", "CA": "/us/ca/", "NY": "/us/ny/", "MA": "/us/ma/"}
GROUPS = [("coming", "Deadlines coming up", "#d4751c"), ("new", "New programs", "#2d6a4f"), ("raised", "Rebates that went up", "#2d6a4f"),
          ("ended", "Programs that ended", "#8a2a1c"), ("paused", "Paused, full or waitlist-only", "#8a5a00"),
          ("cut", "Rebates that were cut", "#8a2a1c"), ("changed", "Rule changes", "#0d4f5c")]


def fmt_date(d):
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    parts = d.split("-")
    if len(parts) == 3:
        return f"{months[int(parts[1]) - 1]} {int(parts[2])}, {parts[0]}"
    if len(parts) == 2:
        return f"{months[int(parts[1]) - 1]} {parts[0]}"
    return parts[0]


def card(x):
    hub = REGION_HUB.get(x["region"])
    region = e(REGIONS[x["region"]])
    region_html = f'<a href="{hub}">{region}</a>' if hub else region
    return (f'<article class="rt-item" data-region="{x["region"]}"><div class="rt-meta">{e(fmt_date(x["date"]))} · {region_html}</div>'
            f'<h3>{e(x["program"])}</h3><p>{e(x["change"])}</p>'
            f'<p class="rt-do"><b>What to do:</b> {e(x["instead"])}</p>'
            f'<p class="rt-src"><a href="{e(x["source"])}" rel="noopener">Official source</a></p></article>')


def build():
    data = json.loads((ROOT / "rebate-tracker" / "changes.json").read_text())
    entries = sorted(data["entries"], key=lambda x: x["date"], reverse=True)
    checked = fmt_date(data["checked"])
    counts = {g: sum(1 for x in entries if x["status"] == g) for g, _, _ in GROUPS}
    sections = ""
    for g, title, color in GROUPS:
        items = [x for x in entries if x["status"] == g]
        if not items:
            continue
        sections += (f'<section class="rt-group" data-group="{g}"><h2 style="border-left:6px solid {color};padding-left:12px;">{e(title)} ({len(items)})</h2>'
                     + "".join(card(x) for x in items) + "</section>")
    used = [r for r in REGIONS if any(x["region"] == r for x in entries)]
    buttons = '<button type="button" class="rt-f on" data-r="all">All</button>' + "".join(
        f'<button type="button" class="rt-f" data-r="{r}">{e(REGIONS[r])}</button>' for r in used)
    ended = counts["ended"] + counts["paused"] + counts["cut"]
    short = (f"As of {checked}, we track {len(entries)} recent changes to home energy rebates across Canada and the US. "
             f"{ended} programs ended, paused or were cut, including the Canada Greener Homes Grant, the US federal 25C and 25D tax credits, "
             f"TECH Clean California and California's HEEHRA rebates. {counts['new'] + counts['raised']} are new or increased.")
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">Rebate tracker</li></ol></nav>
<header class="hero"><div class="wrap"><h1>Home Energy Rebate Tracker: What Ended, What's New</h1>
<p>Updated monthly. Last checked {checked}. Every change links to the official source.</p></div></header>
<section class="body"><div class="wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> {e(short)}</p></div>
<p>Programs close quietly, often when their money runs out. Before you sign a contract, check that the rebate you're counting on is still open.</p>
<div class="rt-filters" role="group" aria-label="Filter by region">{buttons}</div>
{sections}
<h2>How we keep this list</h2>
<p>Once a month we re-check every official program page on this list and add programs we find that are new. If something here is out of date, email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a> and we'll check it within a week.</p>
<p><b>Monthly digests:</b> <a href="/rebate-tracker/2026-09/">July to September 2026</a></p>
<p><b>Related:</b> <a href="/furnace-rebates/">Furnace and AC rebates by province and state</a> · <a href="/solar-quote-checker/">Solar quote checker</a> · <a href="/installers/">Top-rated installers by city</a></p>
</div></section>
<script>
document.querySelectorAll('.rt-f').forEach(b=>b.addEventListener('click',()=>{{
document.querySelectorAll('.rt-f').forEach(x=>x.classList.toggle('on',x===b));const r=b.dataset.r;
document.querySelectorAll('.rt-item').forEach(i=>i.hidden=!(r==='all'||i.dataset.region===r));
document.querySelectorAll('.rt-group').forEach(g=>g.hidden=![...g.querySelectorAll('.rt-item')].some(i=>!i.hidden));}}));
</script>"""
    css = """.rt-filters{display:flex;flex-wrap:wrap;gap:8px;margin:22px 0;}.rt-f{background:#fff;border:1px solid #d9d0c1;border-radius:999px;padding:10px 14px;font:inherit;font-size:14px;cursor:pointer;min-height:44px;}
.rt-f.on{background:#0d4f5c;color:#fff;border-color:#0d4f5c;}.rt-item{background:#fff;border:1px solid #d9d0c1;border-radius:10px;padding:16px 18px;margin:12px 0;}
.rt-item h3{margin:4px 0 6px;font-size:18px;}.rt-item p{margin:6px 0;}.rt-meta{font-size:13px;font-weight:700;color:#1a3d42;text-transform:uppercase;letter-spacing:.04em;}
.rt-do{font-size:15px;}.rt-src{font-size:14px;}"""
    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": "Home Energy Rebate Tracker: What Ended, What's New",
         "description": short, "datePublished": "2026-09-28", "dateModified": data["checked"], "author": AUTHOR,
         "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE}, "mainEntityOfPage": BASE + PATH},
        {"@context": "https://schema.org", "@type": "Dataset", "name": "Home energy rebate program changes (Canada and US)",
         "description": "Dated list of home energy rebate programs that ended, paused, were cut, or launched, each linked to its official source.",
         "url": BASE + PATH, "dateModified": data["checked"], "creator": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE},
         "license": "https://creativecommons.org/licenses/by/4.0/", "isAccessibleForFree": True,
         "distribution": {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": BASE + PATH + "changes.json"}},
    ]
    page = shell("Rebate Tracker 2026: Which Home Rebates Ended? | HomePowerRebate",
                 "Which home energy rebates ended or changed? Greener Homes, US 25C/25D credits, TECH, HEEHRA and more. Updated monthly with official sources.",
                 PATH, "on", body, ld)
    page = page.replace("</style>", css + "</style>", 1)
    (ROOT / "rebate-tracker" / "index.html").write_text(page, encoding="utf-8")
    print(f"Wrote {PATH}: {len(entries)} entries, checked {checked}.")


if __name__ == "__main__":
    build()
