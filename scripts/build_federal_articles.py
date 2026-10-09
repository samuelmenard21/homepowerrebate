#!/usr/bin/env python3
"""Federal heat pump rebate series: /blog/<slug>/ from hand-written data/federal/<slug>.json.
Fields: title, desc, h1, lead, badge, sections [[h2, html]], faq [[q, a]], refs [[text, url]], related [[text, url]], published (ISO), updated (ISO).
Figures must come from data/verified-facts (federal-*, bc, on, ns, ab, general) or the page's refs. Same gate as the utility pages.
Usage: python3 scripts/build_federal_articles.py [slug ...]"""
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
PILLAR = ("National Heat Pump Rebate: everything confirmed so far", "/programs/national-heat-pump-rebate/")


def build(slug):
    d = json.loads((ROOT / "data/federal" / f"{slug}.json").read_text())
    path = f"/blog/{slug}/"
    nice = date.fromisoformat(d["updated"]).strftime("%B %-d, %Y")
    faq = "".join(f'<div class="faq-item"><h3>{e(q)}</h3><p>{a}</p></div>\n' for q, a in d["faq"])
    refs = ", ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a>' for t, u in d["refs"])
    rel = "".join(f'<li><a href="{u}">{t}</a></li>' for t, u in [PILLAR] + d["related"])
    article = f"""<p class="byline">By <a href="/about">Sam Menard</a> · Updated {nice}</p>
{''.join(f"<h2>{h}</h2>{b}" for h, b in d['sections'])}
<div class="callout"><strong>Want your exact number?</strong> Run our <a href="/calculator/on/" style="color:var(--teal,#0d4f5c); font-weight:600;">rebate calculator</a>, or <a href="/get-quotes/" style="color:var(--teal,#0d4f5c); font-weight:600;">get a plan emailed with the top-rated installers near you</a>.</div>
<h2>Common questions</h2>
{faq}
<h2>More on the federal heat pump rebate</h2>
<ul>{rel}</ul>
<p style="font-size:14px;">Sources, read {nice}: {refs}.</p>"""
    w = ca.words(article)
    ext = set(re.findall(r'href="(https?://[^"]+)"', article))
    problems = []
    if w < 750:
        problems.append(f"{w} words (<750)")
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
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": d["h1"], "description": desc, "author": ca.AUTHOR,
           "publisher": {"@type": "Organization", "name": "HomePowerRebate"}, "datePublished": d["published"], "dateModified": d["updated"], "mainEntityOfPage": BASE + path},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE}, {"@type": "ListItem", "position": 2, "name": "Blog", "item": BASE + "/blog/"},
              {"@type": "ListItem", "position": 3, "name": d["h1"], "item": BASE + path}]},
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", html.unescape(a))}} for q, a in d["faq"]]}]
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
<style>.faq-item{{border-bottom:1px solid #d9d0c1;padding:14px 0}}.faq-item h3{{margin:0 0 6px;font-size:18px}}.faq-item p{{margin:0}}.byline{{font-size:14px;color:#5a5348;margin:0 0 16px}}</style>
{lds}</head><body>
{navfooter.render_nav("on", "")}
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/blog/">Blog</a></li><li aria-current="page">{e(d['h1'])}</li></ol></nav>
<section class="hero"><div class="wrap"><div class="amount-badge">{e(d['badge'])}</div><h1>{e(d['h1'])}</h1><p>{d['lead']}</p></div></section>
<article class="article"><div class="wrap">
{article}
</div></article>
{navfooter.render_footer("on", "", "", path)}
</body></html>
"""
    out = ROOT / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    return path, w


if __name__ == "__main__":
    only = set(sys.argv[1:])
    for f in sorted((ROOT / "data/federal").glob("*.json")):
        if only and f.stem not in only:
            continue
        r = build(f.stem)
        print("built", r[0], r[1], "words")
