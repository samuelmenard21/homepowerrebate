#!/usr/bin/env python3
"""California city category pages in the same layout as the Ontario and BC pages (hero badge, rebate cards, claim steps, visible FAQ, installers).
Prose is hand-written per page in data/ca/pages/<city>/<category>.json (the hpr-category-page-localization skill bans fill-in-the-blank templates).
This script only assembles: facts-driven cards and sources, installers from installers/json, schema, nav and footer. A page with no JSON file is not built.
Usage: python3 scripts/build_ca_pages.py [city ...]"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
from build_calculator import load_facts  # noqa: E402
from ca_cities import CITIES  # noqa: E402

e = html.escape
BASE = "https://homepowerrebate.com"
AUTHOR = {"@type": "Person", "@id": f"{BASE}/#sam", "name": "Sam Menard", "url": f"{BASE}/about"}
FACTS = load_facts()
TEMPLATE = (ROOT / "ca/on/kitchener/heat-pump/index.html").read_text(encoding="utf-8")
CSS = "".join(re.findall(r"<style[\s\S]*?</style>", TEMPLATE))
LABEL = {"heat-pump": "Heat Pump", "water-heater": "Water Heater", "solar": "Solar", "battery": "Battery Storage", "ev-charger": "EV Charger", "insulation": "Insulation",
         "smart-thermostats": "Smart Thermostat", "appliances": "Appliance", "windows-doors": "Windows & Doors", "hrv": "HRV & Ventilation"}
INSTALLER_SET = {"heat-pump": "hvac", "water-heater": "hvac", "hrv": "hvac", "smart-thermostats": "hvac", "solar": "solar", "battery": "solar"}
PILL = {"active": ("status-open", "Open"), "check": ("status-limited", "Check first"), "closed": ("status-closed", "Closed"), "waitlist": ("status-limited", "On hold"),
        "upcoming": ("status-limited", "Coming"), "paused": ("status-limited", "Paused"), "info": ("status-open", "Info")}


def installers(slug, kind):
    p = ROOT / "installers/json/ca" / ("solar" if kind == "solar" else "") / f"{slug}.json"
    if not p.exists():
        return []
    rows = [r for r in json.loads(p.read_text()) if r.get("rating") and r.get("reviews", 0) >= 10]
    rows.sort(key=lambda r: (-(r["rating"] * min(r["reviews"], 200) / 200 ** 0), -r["reviews"]))
    rows.sort(key=lambda r: (-r["rating"], -r["reviews"]))
    return rows[:5]


def installer_html(slug, name, kind, intro):
    rows = installers(slug, kind)
    if not rows:
        return ""
    cards = ""
    for r in rows:
        site = re.sub(r"[?&]utm_[^&]*", "", r.get("website") or "").rstrip("?")
        link = f'<a class="site-link" href="{e(site)}" target="_blank" rel="noopener">Visit site &rarr;</a>' if site else ""
        cards += f'<div class="installer-card"><div><div class="name">{e(r["name"])}</div><div class="stars">&#9733; {r["rating"]:.1f} ({r["reviews"]:,} reviews)</div></div>{link}</div>\n'
    return (f"<h2>Installers in {e(name)}</h2><p>{intro}</p>\n{cards}"
            f'<p style="margin-top:8px;"><a href="/installers/ca/{slug}/{"solar" if kind == "solar" else "heat-pump"}/">See all {e(name)} installers &rarr;</a></p>')


def card(c):
    cls, label = PILL[c.get("status", "active")]
    return (f'<div class="rebate-card"><span class="program-status {cls}">{label}</span><h4>{(f"<a href='{c['href']}'>" + e(c["title"]) + "</a>") if c.get("href") else e(c["title"])}</h4><div class="amount">{e(c["amount"])}</div>'
            f'<p style="font-size:14px;margin:8px 0 0;">{c["note"]}</p></div>')


def words(h):
    return len(re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).split())


def build(slug, cat):
    c = CITIES[slug]
    name, area = c["name"], c["area"]
    pj = ROOT / "data/ca/pages" / slug / f"{cat}.json"
    if not pj.exists():
        return None
    d = json.loads(pj.read_text())
    hub = f"/us/ca/{area}/{slug}/"
    path = hub if cat == "index" else f"{hub}{cat}/"
    is_hub = cat == "index"
    fids = [i for cd in d["cards"] for i in cd.get("facts", [])] + d.get("facts", [])
    for i in fids:
        assert i in FACTS, f"unknown fact {i}"
    checked = max(FACTS[i]["verified_on"] for i in fids)
    when = date.fromisoformat(checked).strftime("%B %-d, %Y")
    sibs = [] if is_hub else [k for k in LABEL if (ROOT / "data/ca/pages" / slug / f"{k}.json").exists() and k != cat]
    sib = "".join(f'<span style="margin-right:14px;"><a href="/us/ca/{area}/{slug}/{k}/">{LABEL[k]} Rebates in {e(name)}</a></span>\n' for k in sibs)
    cards = "".join(card(x) for x in d["cards"])
    kind = "hvac" if is_hub else INSTALLER_SET.get(cat)
    if d.get("no_installers"):
        kind = None
    inst = installer_html(slug, name, kind, d["installers_intro"]) if kind else ""
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
{inst}
{claim}
<div class="callout"><strong>Want your exact number?</strong> Run our <a href="/calculator/ca/" style="color:var(--teal,#0d4f5c); font-weight:600;">California rebate calculator</a>, or <a href="/get-quotes/?province=ca&amp;city={slug}" style="color:var(--teal,#0d4f5c); font-weight:600;">get a plan emailed with the top-rated installers in {e(name)}</a>.</div>
<h2>Common questions</h2>
{faq}
<h2>What to do next</h2>
{d['next']}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read {when}: {sources}. <a href="{hub}">All {e(name)} rebates &rarr;</a></p>"""
    # quality gate
    w = words(article)
    ext = {m for m in re.findall(r'href="(https?://[^"]+)"', article)}
    dashes = article.count("—") + article.count("&mdash;")
    problems = []
    if w < d.get("min_words", 750):
        problems.append(f"{w} words (<750)")
    if len(d["faq"]) < 4:
        problems.append("fewer than 4 FAQ items")
    if len([u for u in ext if "homepowerrebate" not in u and not re.search(r"(maps\.google|^https?://[^/]*$)", u)]) < 3:
        problems.append("fewer than 3 external references")
    if dashes > 1:
        problems.append(f"{dashes} em dashes")
    if re.search(r"waitlist|unclear|fully subscribed", article, re.I):
        problems.append("contains a PowerScore status keyword")
    if problems:
        raise SystemExit(f"{path}: " + "; ".join(problems))
    title = d["title"]
    desc = d["desc"]
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", html.unescape(a))}} for q, a in d["faq"]]}
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "author": AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
           "datePublished": checked, "dateModified": checked, "mainEntityOfPage": BASE + path},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE}, {"@type": "ListItem", "position": 2, "name": "California", "item": BASE + "/us/ca/"},
              {"@type": "ListItem", "position": 3, "name": name, "item": BASE + hub}, {"@type": "ListItem", "position": 4, "name": LABEL[cat], "item": BASE + path}] if not is_hub else [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE}, {"@type": "ListItem", "position": 2, "name": "California", "item": BASE + "/us/ca/"},
              {"@type": "ListItem", "position": 3, "name": name, "item": BASE + hub}]}, faq_ld]
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
{CSS}
{lds}</head><body>
{navfooter.render_nav("ca", "")}
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/us/ca/">California</a></li>{"" if is_hub else f'<li><a href="{hub}">{e(name)}</a></li>'}<li aria-current="page">{LABEL[cat] if not is_hub else e(name)}</li></ol></nav>
<section class="hero"><div class="wrap"><div class="amount-badge">{e(d['badge'])}</div><h1>{e(d['h1'])}</h1><p>{d['lead']}</p></div></section>
<section class="wrap" style="padding:24px 28px 0;"><div style="font-size:14px; line-height:2.2;">
{"" if is_hub else f'<span style="margin-right:14px;"><a href="{hub}">&larr; Back to {e(name)} rebate hub</a></span>'}
{sib}</div></section>
<article class="article"><div class="wrap">
{article}
</div></article>
{navfooter.render_footer("ca", "", "", path)}
</body></html>
"""
    out = ROOT / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    return path, w


if __name__ == "__main__":
    only = set(sys.argv[1:])
    for slug in CITIES:
        if only and slug not in only:
            continue
        for cat in ["index"] + list(LABEL):
            r = build(slug, cat)
            if r:
                print("built", r[0], r[1], "words")
