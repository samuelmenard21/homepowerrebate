#!/usr/bin/env python3
"""French pages: every file in data/fr/*.json plus the original /fr/qc/thermopompe/ (data/qc/fr-thermopompe.json), hand-written prose in French.
Cards name verified facts in data/verified-facts/qc.json (status, date, source come from the facts). English menu and footer are the shared ones.
Each file has: path (the French URL), en (the English counterpart, linked both ways with hreflang by add_hreflang.py), title, desc, h1, badge, lead, cards, sections, faq, refs, facts,
optional crumb (last breadcrumb label) and crumb_mid ([[label, href], ...] between Canada and the page). Amounts live only in the facts files; check_fr_pages.py fails when a card figure is not in its fact.
Usage: python3 scripts/build_fr_pages.py"""
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
PILL_FR = {"active": ("status-open", "Ouvert"), "check": ("status-limited", "À vérifier"), "closed": ("status-closed", "Fermé"), "waitlist": ("status-limited", "En attente"),
           "upcoming": ("status-limited", "À venir"), "paused": ("status-limited", "Suspendu"), "info": ("status-open", "Info")}
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def card(c):
    cls, label = PILL_FR[c.get("status", "active")]
    return (f'<div class="rebate-card"><span class="program-status {cls}">{label}</span><h4>{e(c["title"])}</h4><div class="amount">{e(c["amount"])}</div>'
            f'<p style="font-size:14px;margin:8px 0 0;">{c["note"]}</p></div>')


def sources():
    return [ROOT / "data/qc/fr-thermopompe.json"] + sorted((ROOT / "data/fr").glob("*.json"))


def main():
    for src in sources():
        build(json.loads(src.read_text()))


def build(d):
    path, en = d["path"], d["en"]
    crumb, crumb_mid = d.get("crumb", "Thermopompe au Québec"), d.get("crumb_mid", [])
    fids = [i for cd in d["cards"] for i in cd.get("facts", [])] + d.get("facts", [])
    for i in fids:
        assert i in FACTS, f"unknown fact {i}"
    for cd in d["cards"]:
        cd["status"] = FACTS[cd["facts"][0]]["status"]
    checked = max(FACTS[i]["verified_on"] for i in fids)
    dt = date.fromisoformat(checked)
    when = f"{dt.day} {MOIS[dt.month - 1]} {dt.year}"
    cards = "".join(card(x) for x in d["cards"])
    links = "".join(f'<li><a href="{u}">{e(t)}</a> : {b}</li>\n' for t, u, b in d["links"])
    steps = "".join(f"<li>{s}</li>\n" for s in d["claim_steps"])
    faq = "".join(f'<div class="faq-item"><h3>{e(q)}</h3><p>{a}</p></div>\n' for q, a in d["faq"])
    sources = ", ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a>' for t, u in d["refs"])
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
<h2>Pour aller plus loin</h2>
<ul>
{links}</ul>
<h2>Questions fréquentes</h2>
{faq}
<p style="font-size:14px;">Par <a href="/about">Sam Menard</a>. Sources, lues le {when} : {sources}.</p>"""
    w = ca.words(article)
    ext = {u for u in re.findall(r'href="(https?://[^"]+)"', article) if "homepowerrebate" not in u}
    problems = []
    if w < 750:
        problems.append(f"{w} mots (<750)")
    if len(d["faq"]) < 4:
        problems.append("moins de 4 questions")
    if len(ext) < 3:
        problems.append("moins de 3 liens externes")
    if article.count("—") + article.count("&mdash;") > 1:
        problems.append("plus d'un tiret long")
    if problems:
        raise SystemExit(f"{path}: " + "; ".join(problems))
    title, desc = d["title"], d["desc"]
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": "fr-CA", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", html.unescape(a))}} for q, a in d["faq"]]}
    ld = [{"@context": "https://schema.org", "@type": "Article", "inLanguage": "fr-CA", "headline": title, "description": desc, "author": ca.AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
           "datePublished": checked, "dateModified": checked, "mainEntityOfPage": BASE + path},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Accueil", "item": BASE + "/"}, {"@type": "ListItem", "position": 2, "name": "Canada", "item": BASE + "/ca/"},
              ] + [{"@type": "ListItem", "position": 3 + i, "name": lb, "item": BASE + hr} for i, (lb, hr) in enumerate(crumb_mid)] + [{"@type": "ListItem", "position": 3 + len(crumb_mid), "name": crumb, "item": BASE + path}]}, faq_ld]
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    alt = (f'<link rel="alternate" hreflang="fr-CA" href="{BASE}{path}"><link rel="alternate" hreflang="en-CA" href="{BASE}{en}"><link rel="alternate" hreflang="x-default" href="{BASE}{en}">')
    page = f"""<!DOCTYPE html>
<html lang="fr-CA"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-W33G4TGRHD');</script>
<meta name="description" content="{e(desc)}"><meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large"><link rel="canonical" href="{BASE}{path}">
{alt}
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{BASE}{path}"><meta property="og:type" content="article"><meta property="og:locale" content="fr_CA">
<meta property="og:image" content="{BASE}/og-image.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
{ca.CSS}
{lds}</head><body>
{navfooter.render_nav("ca", "")}
<nav class="hpr-breadcrumb" aria-label="Fil d'Ariane"><ol><li><a href="/">Accueil</a></li><li><a href="/ca/">Canada</a></li>{"".join(f'<li><a href="{hr}">{e(lb)}</a></li>' for lb, hr in crumb_mid)}<li aria-current="page">{e(crumb)}</li></ol></nav>
<section class="hero"><div class="wrap"><div class="amount-badge">{e(d['badge'])}</div><h1>{e(d['h1'])}</h1><p>{d['lead']}</p></div></section>
<article class="article"><div class="wrap">
{article}
</div></article>
{navfooter.render_footer("ca", "", "", path)}
</body></html>
"""
    out = ROOT / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    print("built", path, w, "mots")


if __name__ == "__main__":
    main()
