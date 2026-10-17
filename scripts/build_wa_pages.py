#!/usr/bin/env python3
"""Washington city category pages in the shared layout used for California, BC, Ontario, Washington and Nova Scotia.
Prose is hand-written per page in data/wa/pages/<city>/<category>.json (hpr-category-page-localization bans fill-in-the-blank templates).
Local facts come from data/wa-housing-acs.json (US Census ACS 5-year 2020-2024, tables B25001/B25003/B25024/B25034/B25040; scripts/pull_co_acs.py)
and city-climate-data.json. Washington programs differ by utility (Puget Sound Energy, Seattle City Light, Avista, Tacoma Power, Clark Public Utilities), so heat-pump, water-heater, insulation and windows-doors pages are built per city where that city's utility pays something distinct.
Battery, solar, EV charger and smart thermostats are state pages (build_state_topic_pages.py); other city category URLs redirect (data/redirects-pending/wa.txt). Same quality gate as scripts/build_ca_pages.py.
Usage: python3 scripts/build_wa_pages.py [city ...]"""
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
NAMES = city_pages.Region("wa").names  # city names live in data/regions.json (city_pages)


def build_state_hub():
    """Base /us/wa/ page. build_hub_tops, build_hub_showcase and build_hub_tidy add the stats strip, open-programs table, city finder and contents."""
    d = json.loads((ROOT / "data/wa/state-hub.json").read_text())
    path = "/us/wa/"
    fids = [x["fact"] for x in json.loads((ROOT / "data/hub-tops/wa.json").read_text())["rows"]]
    checked = max(f["verified_on"] for f in FACTS.values() if f["id"].startswith("wa-"))
    when = date.fromisoformat(checked).strftime("%B %-d, %Y")
    secs = "".join(f"<h2>{h}</h2>{b}" for h, b in d["sections"])
    faq = "".join(f'<div class="faq-item"><h3>{e(q)}</h3><p>{a}</p></div>\n' for q, a in d["faq"])
    sources = " ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a>' + ("," if i < len(d["refs"]) - 1 else "") for i, (t, u) in enumerate(d["refs"]))
    article = f"""{secs}
<div class="callout"><strong>Want a number for your home?</strong> Run our <a href="/calculator/wa/" style="color:var(--teal,#0d4f5c); font-weight:600;">Washington rebate calculator</a>.</div>
<h2 id="quick-questions">Quick Questions</h2>
{faq}
<h2 id="sources">Sources</h2>
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Last read {when}: {sources}.</p>"""
    w = ca.words(article)
    if w < 750:
        raise SystemExit(f"{path}: {w} words (<750)")
    title, desc = d["title"], d["desc"]
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", html.unescape(a))}} for q, a in d["faq"]]}
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE}, {"@type": "ListItem", "position": 2, "name": "Washington", "item": BASE + path}]}, faq_ld]
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-W33G4TGRHD');</script>
<meta name="description" content="{e(desc)}"><meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large"><link rel="canonical" href="{BASE}{path}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{BASE}{path}"><meta property="og:type" content="article">
<meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}">
<meta property="og:image" content="{BASE}/og-image.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
{ca.CSS}
{lds}</head><body>
{navfooter.render_nav("wa", "")}
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">Washington</li></ol></nav>
<header class="hero"><div class="wrap"><div class="eyebrow">{e(d['eyebrow'])}</div><h1>{e(d['h1'])}</h1><p class="sub">{e(d['sub'])}</p></div></header>
<article class="article"><div class="wrap">
{article}
</div></article>
{navfooter.render_footer("wa", "", "", path)}
</body></html>
"""
    out = ROOT / "us/wa/index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    print("built", path, w, "words")

if __name__ == "__main__":
    if "--state-hub" in sys.argv:
        build_state_hub()
        sys.exit(0)
    city_pages.main("wa")
