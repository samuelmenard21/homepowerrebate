#!/usr/bin/env python3
"""Utility and program pages: /programs/<slug>/ from hand-written data/utilities/<slug>.json, plus the /programs/ index.
Every rebate card names the verified fact it comes from (status, date and source link come from the fact, so a closed program cannot show as open).
Prose is hand-written (hpr-category-page-localization). Same quality gate as build_ca_pages.py, with a 700-word floor.
Usage: python3 scripts/build_utility_pages.py [slug ...]"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import regions
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_ca_pages as ca  # noqa: E402
import page_kit as kit  # noqa: E402  (shared page components)

e = html.escape
BASE = ca.BASE
FACTS = ca.FACTS
CALC = regions.CALC
HOME = {"ca": "California", "bc": "British Columbia", "on": "Ontario"}


def build(slug):
    d = json.loads((ROOT / "data/utilities" / f"{slug}.json").read_text())
    path = f"/programs/{slug}/"
    nav = d.get("nav", "ca")
    iso, when = kit.checked(kit.fact_ids(d))
    cities = "".join(f'<li><a href="{u}">{e(t)}</a>: {b}</li>\n' for t, u, b in d.get("cities", []))
    guides = "".join(f'<li><a href="{u}">{e(t)}</a></li>\n' for t, u in d.get("guides", []))
    steps = "".join(f"<li>{s}</li>\n" for s in d["claim_steps"])
    calc_url, calc_name = CALC.get(nav, ("/calculator/", "home") if d.get("no_region_calc") else CALC["ca"])
    article = f"""<h2>{d['cards_heading']}</h2>
{d['cards_intro']}
<div class="rebate-grid">
{kit.cards(d)}
</div>
{d.get('after_cards', '')}
{kit.sections(d)}
<h2>{d['claim_heading']}</h2>
<ol>
{steps}</ol>
{f'<h2>Our pages for {e(d["short"])} customers</h2><ul>{cities}</ul>' if cities else ''}
{f'<h2>Guides</h2><ul>{guides}</ul>' if guides else ''}
{kit.callout(calc_url, calc_name, "/get-quotes/", "", near_you=True)}
<h2>Common questions</h2>
{kit.faq(d)}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read {when}: {kit.sources(d)}. <a href="/programs/">All rebate programs &rarr;</a></p>"""
    w = kit.quality_gate(article, d, path, loose_refs=True, min_words=700)
    trail = [("Home", "/"), ("Rebate programs", "/programs/"), (d["short"], path)]
    lds = kit.ld_scripts([kit.article_ld(d["title"], d["desc"], iso, path), kit.breadcrumb_ld(trail), kit.faq_ld(d)])
    crumb = kit.breadcrumb([("Home", "/"), ("Rebate programs", "/programs/"), (e(d["short"]), path)])
    kit.write_page(path, d["title"], d["desc"], lds, navfooter.render_nav(nav, ""), crumb, kit.hero(d), None, article, navfooter.render_footer(nav, "", "", path))
    return path, w


def title_of(p):
    m = re.search(r"<title>(.*?)</title>", p.read_text(encoding="utf-8"), re.S)
    return html.unescape(m.group(1)).strip() if m else p.parent.name


def index():
    items = []
    for f in sorted((ROOT / "programs").glob("*/index.html")):
        slug = f.parent.name
        if slug == "utility-comparison":
            continue
        j = ROOT / "data/utilities" / f"{slug}.json"
        if j.exists():
            d = json.loads(j.read_text())
            items.append((d.get("group", "Other"), d["short"], f"/programs/{slug}/", d["desc"]))
        else:
            m = re.search(r'<meta name="description" content="(.*?)"', f.read_text(encoding="utf-8"), re.S)
            items.append(("Provinces and states", re.sub(r"\s*[|:].*$", "", title_of(f)), f"/programs/{slug}/", html.unescape(m.group(1)) if m else ""))
    groups = {}
    for g, n, u, desc in items:
        groups.setdefault(g, []).append((n, u, desc))
    body = '<p style="background:#f5efe5;border-left:4px solid #d4751c;padding:14px 18px;"><b>Compare them:</b> see <a href="/programs/utility-comparison/">25 utilities side by side</a>, with a 3-ton heat pump example and the status of every program.</p>\n'
    for g in sorted(groups):
        body += f"<h2>{e(g)}</h2><ul>" + "".join(f'<li><a href="{u}">{e(n)}</a>: {e(dsc)}</li>' for n, u, dsc in sorted(groups[g])) + "</ul>\n"
    path = "/programs/"
    title = "Rebate Programs by Utility and Program (2026)"
    desc = "Every utility and program we track: what each pays, who qualifies and when we last checked it against the official page."
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-W33G4TGRHD');</script>
<meta name="description" content="{e(desc)}"><meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large"><link rel="canonical" href="{BASE}{path}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{BASE}{path}"><meta property="og:type" content="website">
<meta property="og:image" content="{BASE}/og-image.jpg">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
</head><body>
{navfooter.render_nav("ca", "")}
<section class="hero"><div class="wrap"><h1>Rebate Programs by Utility and Program</h1><p>Each page lists what the program pays, who qualifies and the date we last read the official page. Amounts come from our verified facts file, so a closed program never shows as open.</p></div></section>
<article class="article"><div class="wrap">
{body}
</div></article>
{navfooter.render_footer("ca", "", "", path)}
</body></html>
"""
    out = ROOT / "programs" / "index.html"
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    return len(items)


if __name__ == "__main__":
    only = set(sys.argv[1:])
    for f in sorted((ROOT / "data/utilities").glob("*.json")):
        if only and f.stem not in only:
            continue
        r = build(f.stem)
        print("built", r[0], r[1], "words")
    print("index:", index(), "programs")
