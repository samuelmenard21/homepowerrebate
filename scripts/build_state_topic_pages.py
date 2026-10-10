#!/usr/bin/env python3
"""State/province topic pages, e.g. /us/ma/battery/ or /ca/ab/ev-charger/, from hand-written data/state-topics/<region>-<topic>.json.
One honest page per state answers state-level searches better than near-identical city copies (those city URLs redirect here).
Cards name verified facts; each card's status pill comes from its first fact. Same quality gate as build_ca_pages.py (750 words).
Usage: python3 scripts/build_state_topic_pages.py [name ...]"""
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


def build(name):
    d = json.loads((ROOT / "data/state-topics" / f"{name}.json").read_text())
    path, nav, region = d["path"], d["nav"], d["region"]
    hub_name, hub = d["hub_name"], d["hub"]
    fids = [i for cd in d["cards"] for i in cd.get("facts", [])] + d.get("facts", [])
    for i in fids:
        assert i in FACTS, f"unknown fact {i}"
    for cd in d["cards"]:
        if cd.get("facts") and "status" not in cd:
            cd["status"] = FACTS[cd["facts"][0]]["status"]
    checked = max(FACTS[i]["verified_on"] for i in fids)
    when = date.fromisoformat(checked).strftime("%B %-d, %Y")
    cards = "".join(ca.card(x) for x in d["cards"])
    links = "".join(f'<li><a href="{u}">{e(t)}</a>: {b}</li>\n' for t, u, b in d["links"])
    steps = "".join(f"<li>{s}</li>\n" for s in d["claim_steps"])
    faq = "".join(f'<div class="faq-item"><h3>{e(q)}</h3><p>{a}</p></div>\n' for q, a in d["faq"])
    sources = " ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a>' + ("," if i < len(d["refs"]) - 1 else "") for i, (t, u) in enumerate(d["refs"]))
    calc = f"/calculator/{region}/"
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
<h2>More for {e(hub_name)} homes</h2>
<ul>
<li><a href="{hub}">{e(hub_name)} home rebates: every program in one place</a></li>
{links}</ul>
<div class="callout"><strong>Want your exact number?</strong> Run our <a href="{calc}" style="color:var(--teal,#0d4f5c); font-weight:600;">{e(hub_name)} rebate calculator</a>, or <a href="/get-quotes/" style="color:var(--teal,#0d4f5c); font-weight:600;">get a plan emailed with the top-rated installers near you</a>.</div>
<h2>Common questions</h2>
{faq}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read {when}: {sources}.</p>"""
    w = ca.words(article)
    ext = {u for u in re.findall(r'href="(https?://[^"]+)"', article) if "homepowerrebate" not in u}
    problems = []
    if w < 750:
        problems.append(f"{w} words (<750)")
    if len(d["faq"]) < 4:
        problems.append("fewer than 4 FAQ items")
    if len(ext) < 3:
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
           "datePublished": checked, "dateModified": checked, "mainEntityOfPage": BASE + path},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"}, {"@type": "ListItem", "position": 2, "name": hub_name, "item": BASE + hub},
              {"@type": "ListItem", "position": 3, "name": d["short"], "item": BASE + path}]}, faq_ld]
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-W33G4TGRHD');</script>
<meta name="description" content="{e(desc)}"><meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large"><link rel="canonical" href="{BASE}{path}">{d.get("alternates", "")}
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{BASE}{path}"><meta property="og:type" content="article">
<meta property="og:image" content="{BASE}/og-image.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
{ca.CSS}
{lds}</head><body>
{navfooter.render_nav(nav, "")}
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="{hub}">{e(hub_name)}</a></li><li aria-current="page">{e(d['short'])}</li></ol></nav>
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


if __name__ == "__main__":
    only = set(sys.argv[1:])
    for f in sorted((ROOT / "data/state-topics").glob("*.json")):
        if only and f.stem not in only:
            continue
        p, w = build(f.stem)
        print("built", p, w, "words")
