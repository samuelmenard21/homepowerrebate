#!/usr/bin/env python3
"""New York city category pages (/us/ny/<utility>/<city>/<category>/) in the shared layout used for California, BC, Ontario and Nova Scotia.
Prose is hand-written per page in data/ny/pages/<utility>/<city>/<category>.json (hpr-category-page-localization bans fill-in-the-blank templates).
Local facts come from data/ny-housing-acs.json (US Census ACS 5-year 2020-2024; scripts/pull_ny_acs.py).
Cities that share a utility get the same statewide and utility offers, so a category is built only where it has something distinct to say;
the rest redirect to the city hub (see the New York block in _redirects). Hubs and heat-pump pages are built elsewhere. Same quality gate as scripts/build_ca_pages.py.
Usage: python3 scripts/build_ny_pages.py [city ...]"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_ca_pages as ca  # noqa: E402  (shared CSS, card(), words(), AUTHOR, FACTS)

e = html.escape
BASE = ca.BASE
FACTS = ca.FACTS
LABEL = {"insulation": "Insulation", "windows": "Windows & Doors", "water-heater": "Water Heater", "heat-pump": "Heat Pump", "solar": "Solar", "battery": "Battery Storage",
         "ev-charger": "EV Charger", "smart-thermostats": "Smart Thermostat", "appliances": "Appliance", "hrv": "HRV & Ventilation"}
LABEL["windows-doors"] = "Windows & Doors"
BUILT = ["battery", "ev-charger", "insulation", "smart-thermostats", "solar", "water-heater", "windows-doors", "appliances", "hrv"]
UTIL = {"con-edison": "Con Edison", "national-grid": "National Grid", "pseg": "PSEG Long Island", "central-hudson": "Central Hudson"}
PROGRAM = {"con-edison": "con-edison-rebates", "national-grid": "national-grid-rebates", "pseg": "pseg-long-island-rebates", "central-hudson": "central-hudson-rebates"}
PROGRAM_CITY = {"rochester": ("nyseg-and-rge-rebates", "RG&E")}
CITY_NAME = {"new-york-city": "New York City", "oyster-bay": "Oyster Bay", "mount-vernon": "Mount Vernon", "new-rochelle": "New Rochelle", "white-plains": "White Plains"}
NAMES = {c.name: (u.name, CITY_NAME.get(c.name, c.name.replace("-", " ").title()))
         for u in (ROOT / "us/ny").iterdir() if u.is_dir() and u.name in UTIL for c in u.iterdir() if (c / "index.html").exists()}

def build(slug, cat):
    util, name = NAMES[slug]
    pj = ROOT / "data/ny/pages" / util / slug / f"{cat}.json"
    if not pj.exists():
        return None
    d = json.loads(pj.read_text())
    hub = f"/us/ny/{util}/{slug}/"
    prog, progname = PROGRAM_CITY.get(slug, (PROGRAM[util], UTIL[util]))
    is_hub = cat == "index"
    path = hub if is_hub else f"{hub}{cat}/"
    fids = [i for cd in d["cards"] for i in cd.get("facts", [])] + d.get("facts", [])
    for i in fids:
        assert i in FACTS, f"unknown fact {i}"
    checked = max(FACTS[i]["verified_on"] for i in fids)
    when = date.fromisoformat(checked).strftime("%B %-d, %Y")
    sibs = [k for k in LABEL if k != cat and (ROOT / f"us/ny/{util}/{slug}/{k}/index.html").exists() and (k == "heat-pump" or (ROOT / "data/ny/pages" / util / slug / f"{k}.json").exists())]
    sib = "".join(f'<span style="margin-right:14px;"><a href="{hub}{k}/">{LABEL[k]} Rebates in {e(name)}</a></span>\n' for k in sibs)
    guides = ("<h2>Every rebate guide for " + e(name) + "</h2><ul>" + "".join(f'<li><a href="{hub}{k}/">{LABEL[k]} rebates in {e(name)}</a></li>' for k in sibs) + "</ul>") if is_hub else ""
    cards = "".join(ca.card(x) for x in d["cards"])
    inst = ""
    steps = "".join(f"<li>{s}</li>\n" for s in d.get("claim_steps", []))
    claim = f"<h2>{d['claim_heading']}</h2>\n<ol>\n{steps}</ol>" if steps else ""
    faq = "".join(f'<div class="faq-item"><h3>{e(q)}</h3><p>{a}</p></div>\n' for q, a in d["faq"])
    sources = " ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a>' + ("," if i < len(d["refs"]) - 1 else "") for i, (t, u) in enumerate(d["refs"]))
    article = f"""<h2>{d['cards_heading']}</h2>
{d['cards_intro']}
<div class="rebate-grid">
{cards}
</div>
{d.get('after_cards', '')}
{''.join(f"<h2>{h}</h2>{b}" for h, b in d['sections'])}
{guides}
{inst}
{claim}
<div class="callout"><strong>Want your exact number?</strong> Run our <a href="/calculator/ny/" style="color:var(--teal,#0d4f5c); font-weight:600;">New York rebate calculator</a>, or <a href="/get-quotes/?state=ny&amp;city={slug}" style="color:var(--teal,#0d4f5c); font-weight:600;">get a plan emailed with the top-rated installers in {e(name)}</a>.</div>
<h2>Common questions</h2>
{faq}
<h2>What to do next</h2>
{d['next']}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read {when}: {sources}. <a href="{hub}">All {e(name)} rebates &rarr;</a> <a href="/programs/{prog}/">Every {e(progname)} rebate &rarr;</a></p>"""
    w = ca.words(article)
    ext = {m for m in re.findall(r'href="(https?://[^"]+)"', article)}
    problems = []
    if w < d.get("min_words", 750):
        problems.append(f"{w} words (<750)")
    if len(d["faq"]) < 4:
        problems.append("fewer than 4 FAQ items")
    if len([u for u in ext if "homepowerrebate" not in u and not re.search(r"(maps\.google|^https?://[^/]*$)", u)]) < 3:
        problems.append("fewer than 3 external references")
    dashes = article.count("—") + article.count("&mdash;")
    if dashes > 1:
        problems.append(f"{dashes} em dashes")
    if re.search(r"waitlist|unclear|fully subscribed", article, re.I):
        problems.append("contains a PowerScore status keyword")
    if "$11,350" in article or "Greener Homes" in article and "ended" not in article:
        problems.append("stale federal figure")
    if problems:
        raise SystemExit(f"{path}: " + "; ".join(problems))
    title, desc = d["title"], d["desc"]
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", html.unescape(a))}} for q, a in d["faq"]]}
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "author": ca.AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
           "datePublished": checked, "dateModified": checked, "mainEntityOfPage": BASE + path},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE}, {"@type": "ListItem", "position": 2, "name": "New York", "item": BASE + "/us/ny/"},
              {"@type": "ListItem", "position": 3, "name": UTIL[util], "item": BASE + f"/us/ny/{util}/"}, {"@type": "ListItem", "position": 4, "name": name, "item": BASE + hub}] + ([] if is_hub else [{"@type": "ListItem", "position": 5, "name": LABEL[cat], "item": BASE + path}])}, faq_ld]
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-W33G4TGRHD');</script>
<meta name="description" content="{e(desc)}"><meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large"><link rel="canonical" href="{BASE}{path}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{BASE}{path}"><meta property="og:type" content="article">
<meta property="og:image" content="{BASE}/og-image.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
{ca.CSS}
{lds}</head><body>
{navfooter.render_nav("ny", slug)}
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/us/ny/">New York</a></li><li><a href="/us/ny/{util}/">{e(UTIL[util])}</a></li>{"" if is_hub else f'<li><a href="{hub}">{e(name)}</a></li>'}<li aria-current="page">{e(name) if is_hub else LABEL[cat]}</li></ol></nav>
<section class="hero"><div class="wrap"><div class="amount-badge">{e(d['badge'])}</div><h1>{e(d['h1'])}</h1><p>{d['lead']}</p></div></section>
<section class="wrap" style="padding:24px 28px 0;"><div style="font-size:14px; line-height:2.2;">
{"" if is_hub else f'<span style="margin-right:14px;"><a href="{hub}">&larr; Back to {e(name)} rebate hub</a></span>' + chr(10) + sib}</div></section>
<article class="article"><div class="wrap">
{article}
</div></article>
{navfooter.render_footer("ny", slug, name, path)}
</body></html>
"""
    out = ROOT / path.strip("/") / "index.html"
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    return path, w


if __name__ == "__main__":
    only = {a for a in sys.argv[1:] if not a.startswith("--")}
    for slug in sorted(NAMES):
        if only and slug not in only:
            continue
        for cat in BUILT:
            r = build(slug, cat)
            if r:
                print("built", r[0], r[1], "words")
