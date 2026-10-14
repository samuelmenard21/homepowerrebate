#!/usr/bin/env python3
"""Build /rebate-deadlines/ from data/rebate-deadlines.json.

Each row names a fact in data/verified-facts/*.json; status, verified date and source come from the fact.
A row is left out once its date has passed or its fact is no longer active, so a closed offer never shows.
Re-run weekly (or after any facts change), then the post-steps in CLAUDE.md and the sitemap.
"""
import glob
import html
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell, page_css, AUTHOR  # noqa: E402
from build_installer_rankings import BASE  # noqa: E402

PATH = "/rebate-deadlines/"
e = html.escape
REGIONS = {"BC": "British Columbia", "AB": "Alberta", "ON": "Ontario", "MA": "Massachusetts", "NY": "New York", "CA": "California",
           "CT": "Connecticut", "ME": "Maine", "VT": "Vermont", "NJ": "New Jersey", "IL": "Illinois", "MI": "Michigan",
           "MN": "Minnesota", "CO": "Colorado", "WA": "Washington"}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def fmt(d):
    y, m, dd = d.split("-")
    return f"{MONTHS[int(m) - 1]} {int(dd)}, {y}"


def facts():
    out = {}
    for p in glob.glob(str(ROOT / "data" / "verified-facts" / "*.json")):
        d = json.loads(Path(p).read_text())
        for f in (d["facts"] if isinstance(d, dict) else d):
            out[f["id"]] = f
    return out


def build(today=None):
    today = today or date.today().isoformat()
    fx = facts()
    rows = []
    for r in json.loads((ROOT / "data" / "rebate-deadlines.json").read_text())["rows"]:
        f = fx.get(r["fact"])
        if not f:
            sys.exit(f"Unknown fact {r['fact']}")
        if f.get("status") != "active" or r["date"] < today:
            continue
        rows.append({**r, "source": f["source_url"], "verified": f["verified_on"], "program": f["program"]})
    rows.sort(key=lambda r: (r["date"], r["region"]))
    if not rows:
        sys.exit("No open deadlines; not writing an empty page.")

    groups, cur = [], None
    for r in rows:
        if r["date"] != cur:
            cur = r["date"]
            groups.append((cur, []))
        groups[-1][1].append(r)

    def item(r):
        return (f'<article class="dl-item" data-region="{r["region"]}"><div class="dl-meta">{e(REGIONS[r["region"]])} · {e(r["upgrade"])}</div>'
                f'<h3>{e(r["program"])}</h3><p>{e(r["what"])}</p>'
                f'<p class="dl-links"><a href="{e(r["page"])}">Our guide</a> · <a href="{e(r["source"])}" rel="noopener">Official source</a>'
                f' · Checked {e(fmt(r["verified"]))}</p></article>')

    sections = "".join(f'<section class="dl-group"><h2>{e(fmt(d))} <span class="dl-n">({len(items)})</span></h2>'
                       + "".join(item(r) for r in items) + "</section>" for d, items in groups)
    used = [k for k in REGIONS if any(r["region"] == k for r in rows)]
    buttons = '<button type="button" class="dl-f on" data-r="all">All</button>' + "".join(
        f'<button type="button" class="dl-f" data-r="{k}">{e(REGIONS[k])}</button>' for k in used)
    first = groups[0]
    short = (f"{len(rows)} home energy rebate deadlines are coming up in Canada and the US. The next one is {fmt(first[0])}: "
             + "; ".join(f'{r["program"]}' for r in first[1][:3]) + ". Many year-end offers need the work done, not just signed, by December 31.")
    updated = fmt(today)
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">Rebate deadlines</li></ol></nav>
<header class="hero"><div class="wrap"><h1>Home Rebate Deadlines Coming Up</h1>
<p>Heat pump, insulation, appliance and EV charger rebates that end soon, soonest first. Updated {updated}.</p></div></header>
<section class="body"><div class="wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> {e(short)}</p></div>
<p>Read each deadline closely. Some mean the install must be finished. Others mean the form must be in. A contractor who is booked up may not finish in time, so ask for a firm date in writing.</p>
<div class="dl-filters" role="group" aria-label="Filter by province or state">{buttons}</div>
{sections}
<h2>How we keep this list</h2>
<p>Every row comes from the program's own page, which we re-read before adding it. A deadline drops off this page the day after it passes, and a program that closes early is removed when we find out. Spot something out of date? Email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a>.</p>
<p><b>More on deadlines:</b> <a href="/blog/bc-hydro-rebate-deadlines-2026/">BC Hydro rebate deadlines</a> · <a href="/blog/ma-ny-year-end-rebate-deadlines-2026/">Massachusetts and New York year-end deadlines</a></p>
<p><b>Related:</b> <a href="/rebate-tracker/">Rebate tracker: what ended and what's new</a> · <a href="/programs/">Programs by utility</a> · <a href="/installers/">Top-rated installers by city</a></p>
</div></section>
<script>
document.querySelectorAll('.dl-f').forEach(b=>b.addEventListener('click',()=>{{
document.querySelectorAll('.dl-f').forEach(x=>x.classList.toggle('on',x===b));const r=b.dataset.r;
document.querySelectorAll('.dl-item').forEach(i=>i.hidden=!(r==='all'||i.dataset.region===r));
document.querySelectorAll('.dl-group').forEach(g=>g.hidden=![...g.querySelectorAll('.dl-item')].some(i=>!i.hidden));}}));
</script>"""
    css = """.dl-filters{display:flex;flex-wrap:wrap;gap:8px;margin:22px 0;}.dl-f{background:#fff;border:1px solid #d9d0c1;border-radius:999px;padding:10px 14px;font:inherit;font-size:14px;cursor:pointer;min-height:44px;}
.dl-f.on{background:#0d4f5c;color:#fff;border-color:#0d4f5c;}.dl-group h2{border-left:6px solid #d4751c;padding-left:12px;}.dl-n{font-weight:400;color:#1a3d42;font-size:.8em;}
.dl-item{background:#fff;border:1px solid #d9d0c1;border-radius:10px;padding:16px 18px;margin:12px 0;}.dl-item h3{margin:4px 0 6px;font-size:18px;}.dl-item p{margin:6px 0;}
.dl-meta{font-size:13px;font-weight:700;color:#1a3d42;text-transform:uppercase;letter-spacing:.04em;}.dl-links{font-size:14px;}"""
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": "Home Rebate Deadlines Coming Up",
           "description": short, "datePublished": "2026-10-13", "dateModified": today, "author": AUTHOR,
           "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE}, "mainEntityOfPage": BASE + PATH}]
    page = shell("Home Rebate Deadlines 2026: Heat Pump, Insulation, EV Charger",
                 f"{len(rows)} home energy rebate deadlines in Canada and the US, soonest first: BC Hydro, Mass Save, Home Renovation Savings and more. Each links to the official source.",
                 PATH, "on", body, ld, css=page_css("2026-09-29"))
    page = page.replace("</style>", css + "</style>", 1)
    (ROOT / "rebate-deadlines").mkdir(exist_ok=True)
    (ROOT / "rebate-deadlines" / "index.html").write_text(page, encoding="utf-8")
    print(f"Wrote {PATH}: {len(rows)} deadlines from {fmt(rows[0]['date'])} to {fmt(rows[-1]['date'])}.")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else None)
