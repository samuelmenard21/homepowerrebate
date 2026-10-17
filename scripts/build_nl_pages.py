#!/usr/bin/env python3
"""Newfoundland and Labrador pages: the province hub (/ca/nl/, --state) and city hubs (--hubs) in the shared layout used for Nova Scotia.
Prose is hand-written in data/nl/pages/state-hub.json and data/nl/pages/<city>/index.json (no fill-in templates).
Local facts come from data/nl-housing-census2021.json (Statistics Canada 2021 Census, table 98-10-0233-01; scripts/pull_nl_census.py).
Program facts are in data/verified-facts/nl.json (takeCHARGE and Government of NL pages). Same quality gate as scripts/build_ns_pages.py.
Usage: python3 scripts/build_nl_pages.py --state | --hubs [city ...]"""
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
NAMES = city_pages.Region("nl").names  # city names live in data/regions.json (city_pages)


# ---------------------------------------------------------------------------------------------------------------------
# Province hub (/ca/nl/): writes the base page. build_hub_tops.py, build_hub_showcase.py and build_hub_tidy.py then add the
# short answer and table, stats strip, city finder and contents block, exactly as for every other region hub.
HUB_TITLE = "Newfoundland and Labrador Home Energy Rebates 2026: Oil to Electric, Heat Pumps, Insulation"
HUB_DESC = ("Newfoundland and Labrador home rebates for 2026: up to $22,000 to switch from oil to a heat pump, takeCHARGE insulation, "
            "air sealing and HRV rebates, no-cost upgrades for lower incomes and the $500 oil supplement. Every amount sourced.")


def build_state_hub():
    d = json.loads((ROOT / "data/nl/pages/state-hub.json").read_text())
    for i in d["facts"]:
        assert i in FACTS, f"unknown fact {i}"
    when = date.fromisoformat(max(FACTS[i]["verified_on"] for i in d["facts"])).strftime("%B %-d, %Y")
    # borrow the hub template's stylesheets from a converted hub (inline <style> blocks are gone since the 2026-10-11 template move)
    mn = (ROOT / "us/mn/index.html").read_text(encoding="utf-8")
    head = mn[:mn.find("</head>")]
    css = "\n".join(re.findall(r'<link rel="stylesheet" href="/assets/tpl/(?:hub|common)-[^"]+" data-hpr-tpl>', head))
    cards = "".join(
        f'<div class="rebate-card"><h4 aria-level="3">{e(NAMES[s])}</h4><p style="margin-bottom:8px;">{e(u)}</p><p><a href="/ca/nl/{s}/">View {e(NAMES[s])} rebates &rarr;</a></p></div>'
        for s, u in [("st-johns", "Newfoundland Power, takeCHARGE and the City's Shift program"), ("mount-pearl", "1970s and 80s homes, many with a basement apartment"),
                     ("paradise", "Newer homes: check the 2014 insulation rule"), ("corner-brook", "Older homes on the west coast"), ("labrador-city", "NL Hydro customers in Labrador West")])
    secs = "".join(f"<h2>{h}</h2>{b.replace('{cards}', cards)}" for h, b in d["sections"])
    faq = "".join(f'<h3>{e(q)}</h3><p>{e(a)}</p>' for q, a in d["faq"])
    src = "<ul>" + "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a></li>' for t, u in d["refs"]) + "</ul>"
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in d["faq"]]}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE}, {"@type": "ListItem", "position": 2, "name": "Newfoundland and Labrador", "item": BASE + "/ca/nl/"}]}
    links = ('<p style="max-width:880px;margin:12px auto;padding:0 20px;"><b>Program guides:</b> <a href="/programs/newfoundland-oil-to-electric-rebate/">Oil to Electric rebate</a> · '
             '<a href="/programs/national-heat-pump-rebate/">National Heat Pump Rebate</a></p>')
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(HUB_TITLE)}</title>
<meta name="description" content="{e(HUB_DESC)}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="{BASE}/ca/nl/">
<meta property="og:title" content="{e(HUB_TITLE)}">
<meta property="og:description" content="{e(HUB_DESC)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{BASE}/ca/nl/">
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
{navfooter.render_nav("nl", "")}
<!-- CANONICAL-BREADCRUMB-START -->
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">Newfoundland and Labrador</li></ol></nav>
<!-- CANONICAL-BREADCRUMB-END -->
<header class="hero"><div class="wrap"><div class="eyebrow">takeCHARGE · Newfoundland Power · NL Hydro</div><h1>Home Energy Rebates in Newfoundland and Labrador</h1><p class="sub">A plain guide to 2026 home energy rebates in Newfoundland and Labrador, starting with getting off oil. Each amount comes from the program's own page.</p></div></header>
<!-- PROGRAM-LINKS-START -->{links}<!-- PROGRAM-LINKS-END -->
<!-- CALC-LINK-START --><p style="max-width:880px;margin:12px auto;padding:0 20px;"><b>Not sure what you qualify for?</b> <a href="/calculator/nl/">Use the Newfoundland and Labrador rebate calculator</a>.</p><!-- CALC-LINK-END -->
<article class="article">
  <div class="wrap">
{secs}
<h2>Quick questions</h2>
<details class="hub-fold"><summary>Read the questions and answers</summary>
{faq}
</details>
<h2>Sources</h2>
<details class="hub-fold"><summary>See the sources</summary>
{src}
</details>
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. We read each page on {when}.</p>
  </div>
</article>
{navfooter.render_footer("nl", "", "", "/ca/nl/")}
</body>
</html>
"""
    out = ROOT / "ca/nl/index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    print("built /ca/nl/", ca.words(secs), "words")

if __name__ == "__main__":
    if "--state" in sys.argv:
        build_state_hub()
        sys.exit(0)
    city_pages.main("nl")
