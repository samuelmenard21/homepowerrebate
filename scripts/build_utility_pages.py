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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_ca_pages as ca  # noqa: E402

e = html.escape
BASE = ca.BASE
FACTS = ca.FACTS
CALC = {"on": ("/calculator/on/", "Ontario"), "ca": ("/calculator/ca/", "California"), "bc": ("/calculator/bc/", "BC"), "ny": ("/calculator/ny/", "New York"), "vt": ("/calculator/vt/", "Vermont"), "nj": ("/calculator/nj/", "New Jersey"), "ns": ("/calculator/ns/", "Nova Scotia")}
HOME = {"ca": "California", "bc": "British Columbia", "on": "Ontario"}


def build(slug):
    d = json.loads((ROOT / "data/utilities" / f"{slug}.json").read_text())
    path = f"/programs/{slug}/"
    nav = d.get("nav", "ca")
    fids = [i for cd in d["cards"] for i in cd.get("facts", [])]
    for i in fids:
        assert i in FACTS, f"unknown fact {i}"
    checked = max(FACTS[i]["verified_on"] for i in fids)
    when = date.fromisoformat(checked).strftime("%B %-d, %Y")
    cards = "".join(ca.card(x) for x in d["cards"])
    cities = "".join(f'<li><a href="{u}">{e(t)}</a>: {b}</li>\n' for t, u, b in d.get("cities", []))
    guides = "".join(f'<li><a href="{u}">{e(t)}</a></li>\n' for t, u in d.get("guides", []))
    steps = "".join(f"<li>{s}</li>\n" for s in d["claim_steps"])
    faq = "".join(f'<div class="faq-item"><h3>{e(q)}</h3><p>{a}</p></div>\n' for q, a in d["faq"])
    sources = " ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a>' + ("," if i < len(d["refs"]) - 1 else "") for i, (t, u) in enumerate(d["refs"]))
    calc_url, calc_name = CALC.get(nav, CALC["ca"])
    article = f"""<h2>{d['cards_heading']}</h2>
{d['cards_intro']}
<div class="rebate-grid">
{cards}
</div>
{d.get('after_cards', '')}
{''.join(f"<h2>{h}</h2>{b}" for h, b in d['sections'])}
<h2>{d['claim_heading']}</h2>
<ol>
{steps}</ol>
{f'<h2>Our pages for {e(d["short"])} customers</h2><ul>{cities}</ul>' if cities else ''}
{f'<h2>Guides</h2><ul>{guides}</ul>' if guides else ''}
<div class="callout"><strong>Want your exact number?</strong> Run our <a href="{calc_url}" style="color:var(--teal,#0d4f5c); font-weight:600;">{calc_name} rebate calculator</a>, or <a href="/get-quotes/" style="color:var(--teal,#0d4f5c); font-weight:600;">get a plan emailed with the top-rated installers near you</a>.</div>
<h2>Common questions</h2>
{faq}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read {when}: {sources}. <a href="/programs/">All rebate programs &rarr;</a></p>"""
    w = ca.words(article)
    ext = {m for m in re.findall(r'href="(https?://[^"]+)"', article)}
    problems = []
    if w < d.get("min_words", 700):
        problems.append(f"{w} words (<700)")
    if len(d["faq"]) < 4:
        problems.append("fewer than 4 FAQ items")
    if len([u for u in ext if "homepowerrebate" not in u]) < 3:
        problems.append("fewer than 3 external references")
    if article.count("—") + article.count("&mdash;") > 1:
        problems.append("more than 1 em dash")
    if re.search(r"waitlist|unclear|fully subscribed", article, re.I):
        problems.append("contains a PowerScore status keyword")
    if problems:
        raise SystemExit(f"{path}: " + "; ".join(problems))
    title, desc = d["title"], d["desc"]
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", html.unescape(a))}} for q, a in d["faq"]]}
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "author": ca.AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
           "datePublished": checked, "dateModified": checked, "mainEntityOfPath": BASE + path},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE}, {"@type": "ListItem", "position": 2, "name": "Rebate programs", "item": BASE + "/programs/"},
              {"@type": "ListItem", "position": 3, "name": d["short"], "item": BASE + path}]}, faq_ld]
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
{navfooter.render_nav(nav, "")}
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/programs/">Rebate programs</a></li><li aria-current="page">{e(d['short'])}</li></ol></nav>
<section class="hero"><div class="wrap"><div class="amount-badge">{e(d['badge'])}</div><h1>{e(d['h1'])}</h1><p>{d['lead']}</p></div></section>
<article class="article"><div class="wrap">
{article}
</div></article>
{navfooter.render_footer(nav, "", "", path)}
</body></html>
"""
    out = ROOT / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
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
{ca.CSS}
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
