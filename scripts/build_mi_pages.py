#!/usr/bin/env python3
"""Michigan city pages (Detroit and Ann Arbor on DTE, Grand Rapids on Consumers Energy, Lansing on its own Board of Water & Light) in the shared layout.
Copied from scripts/build_pa_pages.py. Prose is hand-written per page in data/mi/pages/<city>/<category>.json.
Local facts come from data/mi-housing-acs.json (US Census ACS 5-year 2020-2024 via scripts/pull_mi_acs.py). Amounts come only from data/verified-facts/mi.json.
A city gets a category page only where it has something distinct to say; other categories are statewide pages (data/state-topics/mi-*.json).
No Michigan installer rows exist in the ranking data yet, so the installer block is skipped (see installers()).
Usage: python3 scripts/build_mi_pages.py [city ...] [--hubs]"""
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
NAMES = city_pages.Region("mi").names  # city names live in data/regions.json (city_pages)


def state_hub():
    """The Michigan hub (/us/mi/): hero, program links and the hand-written legacy sections. build_hub_tops, build_hub_showcase and build_hub_tidy add the standard blocks."""
    d = json.loads((ROOT / "data/mi/pages/state-hub.json").read_text())
    path = "/us/mi/"
    checked = max(f["verified_on"] for f in FACTS.values() if f["id"].startswith("mi-"))
    body = "".join(f"<h2>{h}</h2>{b}" for h, b in d["sections"])
    faq = "".join(f'<div class="faq-item"><h3>{e(q)}</h3><p>{a}</p></div>\n' for q, a in d["faq"])
    sources = " ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a>' + ("," if i < len(d["refs"]) - 1 else "") for i, (t, u) in enumerate(d["refs"]))
    when = date.fromisoformat(checked).strftime("%B %-d, %Y")
    article = f"""{body}<h2>Common questions</h2>
{faq}<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read {when}: {sources}</p>"""
    ext = {m for m in re.findall(r'href="(https?://[^"]+)"', article)}
    problems = []
    if ca.words(article) < 450:
        problems.append("hub body under 450 words")
    if len(d["faq"]) < 4 or len(ext) < 3:
        problems.append("faq or references too few")
    if article.count("—") + article.count("&mdash;") > 1 or re.search(r"waitlist|unclear|fully subscribed", article, re.I):
        problems.append("banned wording")
    if problems:
        raise SystemExit("/us/mi/: " + "; ".join(problems))
    title, desc = d["title"], d["desc"]
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", html.unescape(a))}} for q, a in d["faq"]]}
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "author": ca.AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
           "datePublished": checked, "dateModified": checked, "mainEntityOfPage": BASE + path},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE}, {"@type": "ListItem", "position": 2, "name": "Michigan", "item": BASE + path}]}, faq_ld]
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    links = ["dte-energy-rebates", "consumers-energy-rebates", "lansing-bwl-rebates", "ann-arbor-a2zero-rebates"]
    names = {"dte-energy-rebates": "DTE Energy rebates", "consumers-energy-rebates": "Consumers Energy rebates", "lansing-bwl-rebates": "Lansing BWL rebates", "ann-arbor-a2zero-rebates": "Ann Arbor A2ZERO rebates"}
    pl = ('<!-- PROGRAM-LINKS-START --><p style="max-width:880px;margin:12px auto;padding:0 20px;"><b>Program guides:</b> '
          + " · ".join(f'<a href="/programs/{k}/">{names[k]}</a>' for k in links) + ' · <a href="/programs/federal-tax-credits-2026/">2026 tax credits</a></p><!-- PROGRAM-LINKS-END -->')
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
{navfooter.render_nav("mi", "")}
<header class="hero"><div class="wrap"><div class="eyebrow">DTE · Consumers · Lansing BWL · Ann Arbor</div><h1>{e(d['h1'])}</h1><p class="sub">{e(d['sub'])}</p></div></header>
{pl}
<article class="article"><div class="wrap">
{article}
</div></article>
{navfooter.render_footer("mi", "", "", path)}
</body></html>
"""
    out = ROOT / "us/mi/index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    print("built /us/mi/")

if __name__ == "__main__":
    if "--state" in sys.argv:
        state_hub()
        sys.exit(0)
    city_pages.main("mi")
