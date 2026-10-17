#!/usr/bin/env python3
"""Minnesota city category pages in the shared layout used for California, BC, Ontario, Colorado and Nova Scotia.
Prose is hand-written per page in data/mn/pages/<city>/<category>.json (hpr-category-page-localization bans fill-in-the-blank templates).
Local facts come from data/mn-housing-acs.json (US Census ACS 5-year 2020-2024, tables B25001/B25003/B25024/B25034/B25040; scripts/pull_mn_acs.py)
and city-climate-data.json. Minnesota programs differ by utility (Xcel Energy, CenterPoint Energy, Minnesota Power, Rochester Public Utilities, plus the City of Minneapolis), so pages are built only where a city has something distinct to say.
Smart thermostats is a state page (build_state_topic_pages.py); other city category URLs redirect (data/redirects-pending/mn.txt). Same quality gate as scripts/build_ca_pages.py.
Usage: python3 scripts/build_mn_pages.py [--hubs] [city ...]"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import city_pages  # noqa: E402  (city pages and hubs: the shared engine)
import build_ca_pages as ca  # noqa: E402  (shared CSS, card(), words(), AUTHOR, FACTS)

e = html.escape
BASE = ca.BASE
FACTS = ca.FACTS
NAMES = city_pages.Region("mn").names  # city names live in data/regions.json (city_pages)


# ---------------------------------------------------------------------------------------------------------------------
# State hub (/us/mn/): writes the base page. build_hub_tops.py, build_hub_showcase.py and build_hub_tidy.py then add the
# short answer and table, stats strip, city finder and contents block, exactly as for every other region hub.
HUB_TITLE = "Minnesota Home Energy Rebates 2026: Cold-Climate Heat Pumps, Insulation, Water Heaters"
HUB_DESC = ("Minnesota home energy rebates for 2026 from Xcel Energy, CenterPoint Energy, Minnesota Power, Rochester Public Utilities and Minneapolis, "
            "with the amount, the rules and the date we last read each official page.")


def build_state_hub():
    d = json.loads((ROOT / "data/mn/pages/state-hub.json").read_text())
    vt = (ROOT / "us/vt/index.html").read_text(encoding="utf-8")
    # borrow the hub template's stylesheets (inline <style> blocks are gone since the 2026-10-11 template move)
    css = "\n".join(re.findall(r'<link rel="stylesheet" href="/assets/tpl/(?:hub|common)-[^"]+" data-hpr-tpl>', vt[:vt.find("</head>")]))
    cards = "".join(
        f'<div class="rebate-card"><h4 aria-level="3">{e(NAMES[s])}</h4><p style="margin-bottom:8px;">{e(u)}</p><p><a href="/us/mn/{s}/">View {e(NAMES[s])} rebates &rarr;</a></p></div>'
        for s, u in [("minneapolis", "City rebate, Xcel Energy and CenterPoint Energy"), ("saint-paul", "Xcel Energy and CenterPoint Energy"),
                     ("rochester", "Rochester Public Utilities (city-owned electric company)"), ("duluth", "Minnesota Power")])
    secs = "".join(f"<h2>{h}</h2>{b.replace('{cards}', cards)}" for h, b in d["sections"])
    faq = "".join(f'<h3>{e(q)}</h3><p>{e(a)}</p>' for q, a in d["faq"])
    cat_links = (
        '<h3>Heat pumps</h3><ul><li><a href="/us/mn/minneapolis/heat-pump/">Minneapolis heat pump rebates</a></li><li><a href="/us/mn/rochester/heat-pump/">Rochester heat pump rebates</a></li>'
        '<li><a href="/us/mn/duluth/heat-pump/">Duluth heat pump rebates</a></li></ul>'
        '<h3>Water heaters</h3><ul><li><a href="/us/mn/rochester/water-heater/">Rochester water heater rebates</a></li><li><a href="/us/mn/duluth/water-heater/">Duluth water heater rebates</a></li></ul>'
        '<h3>Insulation</h3><ul><li><a href="/us/mn/minneapolis/insulation/">Minneapolis insulation rebates</a></li></ul>'
        '<h3>Thermostats</h3><ul><li><a href="/us/mn/smart-thermostats/">Minnesota smart thermostat rebates</a></li></ul>')
    refs = [("Xcel Energy Minnesota home rebates", "https://mn.my.xcelenergy.com/s/residential/home-rebates"),
            ("CenterPoint Energy Minnesota efficiency programs", "https://www.centerpointenergy.com/en-us/savings-solutions/energy-efficiency"),
            ("Minnesota Power residential rebates", "https://www.mnpower.com/ProgramsRebates/RebatesAndSavings"),
            ("Rochester Public Utilities residential rebates", "https://www.rpu.org/rebates-programs/conserve-save-rebates/residential-rebates/"),
            ("City of Minneapolis Green Cost Share", "https://www.minneapolismn.gov/government/programs-initiatives/environmental-programs/green-cost-share/energy-efficiency/energy-rebates/"),
            ("Save Energy Minnesota (Department of Commerce)", "https://mn.gov/commerce/energy/consumer/energy-programs/save-energy-mn.jsp")]
    src = "<ul>" + "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a></li>' for t, u in refs) + "</ul>"
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in d["faq"]]}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE}, {"@type": "ListItem", "position": 2, "name": "Minnesota", "item": BASE + "/us/mn/"}]}
    links = ('<p style="max-width:880px;margin:12px auto;padding:0 20px;"><b>Program guides:</b> <a href="/programs/xcel-energy-minnesota-rebates/">Xcel Energy</a> · '
             '<a href="/programs/centerpoint-energy-minnesota-rebates/">CenterPoint Energy</a> · <a href="/programs/minnesota-power-rebates/">Minnesota Power</a> · '
             '<a href="/programs/rochester-public-utilities-rebates/">Rochester Public Utilities</a> · <a href="/programs/save-energy-minnesota/">Save Energy Minnesota</a></p>')
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(HUB_TITLE)}</title>
<meta name="description" content="{e(HUB_DESC)}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="{BASE}/us/mn/">
<meta property="og:title" content="{e(HUB_TITLE)}">
<meta property="og:description" content="{e(HUB_DESC)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{BASE}/us/mn/">
<meta property="og:image" content="{BASE}/og-image.jpg">
<meta name="twitter:title" content="{e(HUB_TITLE)}">
<meta name="twitter:description" content="{e(HUB_DESC)}">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-W33G4TGRHD');</script>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(crumb, ensure_ascii=False)}</script>
{css}
</head>
<body>
{navfooter.render_nav("mn", "")}
<!-- CANONICAL-BREADCRUMB-START -->
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">Minnesota</li></ol></nav>
<!-- CANONICAL-BREADCRUMB-END -->
<header class="hero"><div class="wrap"><div class="eyebrow">Xcel Energy · CenterPoint · Minnesota Power</div><h1>Home Energy Rebates in Minnesota</h1><p class="sub">A plain guide to 2026 Minnesota home energy rebates, with cold-climate heat pumps first. Each amount comes from the program's own page.</p></div></header>
<!-- PROGRAM-LINKS-START -->{links}<!-- PROGRAM-LINKS-END -->
<!-- CALC-LINK-START --><p style="max-width:880px;margin:12px auto;padding:0 20px;"><b>Not sure what you qualify for?</b> <a href="/calculator/mn/">Use the Minnesota rebate calculator</a>.</p><!-- CALC-LINK-END -->
<article class="article">
  <div class="wrap">
{secs}
<h2>Rebate finder, by category</h2>
<details class="hub-fold"><summary>Open the full rebate list</summary>
{cat_links}
</details>
<h2>Quick questions</h2>
<details class="hub-fold"><summary>Read the questions and answers</summary>
{faq}
</details>
<h2>Sources</h2>
<details class="hub-fold"><summary>See the sources</summary>
{src}
</details>
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. We read each page on October 6, 2026.</p>
  </div>
</article>
{navfooter.render_footer("mn", "", "", "/us/mn/")}
</body>
</html>
"""
    out = ROOT / "us/mn/index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    print("built /us/mn/", ca.words(secs), "words")

if __name__ == "__main__":
    if "--state" in sys.argv:
        build_state_hub()
        sys.exit(0)
    city_pages.main("mn")
