#!/usr/bin/env python3
"""Illinois city category pages (Chicago, Aurora, Naperville, Peoria) and the statewide hub in the shared layout used for California, BC, Ontario and Nova Scotia.
Copied from scripts/build_pa_pages.py. Prose is hand-written per page in data/il/pages/<city>/<category>.json.
Local facts come from data/il-housing-acs.json (US Census ACS 5-year 2020-2024 via scripts/pull_il_acs.py) and city-climate-data.json.
Amounts come only from data/verified-facts/il.json. Ameren Illinois amounts could not be read (il-18), so Peoria has a hub only. Same quality gate as build_ca_pages.py.
Usage: python3 scripts/build_pa_pages.py [city ...]"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_ca_pages as ca  # noqa: E402  (shared CSS, card(), words(), AUTHOR, FACTS)
import build_installer_rankings as rank  # noqa: E402

e = html.escape
BASE = ca.BASE
FACTS = ca.FACTS
LABEL = {"insulation": "Insulation", "windows-doors": "Windows & Doors", "water-heater": "Water Heater", "heat-pump": "Heat Pump", "solar": "Solar", "battery": "Battery Storage",
         "ev-charger": "EV Charger", "smart-thermostats": "Smart Thermostat", "appliances": "Appliance", "hrv": "HRV & Ventilation"}
BUILT = ["heat-pump", "water-heater", "insulation", "smart-thermostats"]
HUB = ["index"]
NAMES = {"state": "Illinois", "chicago": "Chicago", "aurora": "Aurora", "naperville": "Naperville", "peoria": "Peoria"}
CITY_SLUGS = ["chicago", "aurora", "naperville", "peoria"]
UTILITY = {"state": ("/programs/", "Illinois utility"), "chicago": ("/programs/comed-rebates/", "ComEd"), "aurora": ("/programs/comed-rebates/", "ComEd"),
           "naperville": ("/programs/naperville-electric-rebates/", "Naperville Electric"), "peoria": ("/programs/ameren-illinois-rebates/", "Ameren Illinois")}
HP_ROWS = [r for r in rank.load_rows() if r["region"] == "il" and r["service"] == "heat-pump"]


def installers(slug, cat):
    if cat in ("heat-pump", "water-heater", "index"):
        rows = [r for r in HP_ROWS if rank.slugify(r["city"]) == slug and r.get("reviews", 0) >= 5]
    else:
        rows = []
    rows.sort(key=lambda r: -rank.score(r))
    return rows[:5]


def installer_html(slug, name, cat, intro):
    rows = installers(slug, cat)
    if not rows:
        return ""
    cards = ""
    for r in rows:
        site = re.sub(r"[?&]utm_[^&]*", "", r.get("website") or "").rstrip("?")
        link = f'<a class="site-link" href="{e(site)}" target="_blank" rel="noopener">Visit site &rarr;</a>' if site else ""
        cards += f'<div class="installer-card"><div><div class="name">{e(r["name"])}</div><div class="stars">&#9733; {r["rating"]:.1f} ({r["reviews"]:,} Google reviews)</div></div>{link}</div>\n'
    kind = "heat-pump"
    more = f'<p style="margin-top:8px;"><a href="/installers/il/{slug}/{kind}/">See all {e(name)} installers &rarr;</a></p>' if (ROOT / f"installers/il/{slug}/{kind}/index.html").exists() else ""
    return f"<h2>Top-rated installers in {e(name)}</h2><p>{intro}</p>\n{cards}{more}"


def build(slug, cat):
    name = NAMES[slug]
    pj = ROOT / "data/il/pages" / slug / f"{cat}.json"
    if not pj.exists():
        return None
    d = json.loads(pj.read_text())
    state = slug == "state"
    hub = "/us/il/" if state else f"/us/il/{slug}/"
    is_hub = cat == "index"
    path = hub if is_hub else f"{hub}{cat}/"
    fids = [i for cd in d["cards"] for i in cd.get("facts", [])] + d.get("facts", [])
    for i in fids:
        assert i in FACTS, f"unknown fact {i}"
    checked = max(FACTS[i]["verified_on"] for i in fids)
    when = date.fromisoformat(checked).strftime("%B %-d, %Y")
    sibs = [] if state else [k for k in LABEL if k != cat and (ROOT / f"us/il/{slug}/{k}/index.html").exists()]
    sib = "".join(f'<span style="margin-right:14px;"><a href="{hub}{k}/">{LABEL[k]} Rebates in {e(name)}</a></span>\n' for k in sibs)
    if state:
        topics = [(k, t) for k, t in (("solar", "Solar rebates"), ("appliances", "Appliance rebates")) if (ROOT / f"us/il/{k}/index.html").exists()]
        guides = ("<h2>City guides and statewide guides</h2><ul>" + "".join(f'<li><a href="/us/il/{c}/">{NAMES[c]} rebates</a></li>' for c in CITY_SLUGS if (ROOT / f"us/il/{c}/index.html").exists())
                  + "".join(f'<li><a href="/us/il/{k}/">Illinois {t.lower()}</a></li>' for k, t in topics) + "</ul>")
    else:
        guides = ("<h2>Every rebate guide for " + e(name) + "</h2><ul>" + "".join(f'<li><a href="{hub}{k}/">{LABEL[k]} rebates in {e(name)}</a></li>' for k in sibs) + "</ul>") if is_hub else ""
    cards = "".join(ca.card(x) for x in d["cards"])
    inst = "" if d.get("no_installers") else installer_html(slug, name, cat, d.get("installers_intro", ""))
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
{guides}
{inst}
{claim}
<div class="callout"><strong>Want your exact number?</strong> Run our <a href="/calculator/il/" style="color:var(--teal,#0d4f5c); font-weight:600;">Illinois rebate calculator</a>, or <a href="/get-quotes/?province=il&amp;city={slug}" style="color:var(--teal,#0d4f5c); font-weight:600;">get a plan emailed with the top-rated installers in {e(name)}</a>.</div>
<h2>Common questions</h2>
{faq}
<h2>What to do next</h2>
{d['next']}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read {when}: {sources}. <a href="{hub}">All {e(name)} rebates &rarr;</a> <a href="{UTILITY[slug][0]}">Every {UTILITY[slug][1]} rebate &rarr;</a></p>"""
    w = ca.words(article)
    ext = {m for m in re.findall(r'href="(https?://[^"]+)"', article)}
    problems = []
    if w < d.get("min_words", 750):
        problems.append(f"{w} words (<750)")
    if len(d["faq"]) < 4:
        problems.append("fewer than 4 FAQ items")
    if len([u for u in ext if "homepowerrebate" not in u and not re.search(r"(maps\.google|^https?://[^/]*$)", u)]) < 3:
        problems.append("fewer than 3 external references")
    dashes = article.count("—") + article.count("&mdash;")
    if dashes > 1:
        problems.append(f"{dashes} em dashes")
    if re.search(r"waitlist|unclear|fully subscribed", article, re.I):
        problems.append("contains a PowerScore status keyword")
    if "$11,350" in article or "Greener Homes" in article and "ended" not in article:
        problems.append("stale federal figure")
    if problems:
        raise SystemExit(f"{path}: " + "; ".join(problems))
    title, desc = d["title"], d["desc"]
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", html.unescape(a))}} for q, a in d["faq"]]}
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "author": ca.AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
           "datePublished": checked, "dateModified": checked, "mainEntityOfPage": BASE + path},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE}, {"@type": "ListItem", "position": 2, "name": "Illinois", "item": BASE + "/us/il/"},
              ] + ([] if state else [{"@type": "ListItem", "position": 3, "name": name, "item": BASE + hub}]) + ([] if is_hub else [{"@type": "ListItem", "position": 4, "name": LABEL[cat], "item": BASE + path}])}, faq_ld]
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
{navfooter.render_nav("il", "" if state else slug)}
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li>{"" if state else "<li><a href=\"/us/il/\">Illinois</a></li>"}{"" if is_hub else f'<li><a href="{hub}">{e(name)}</a></li>'}<li aria-current="page">{e(name) if is_hub else LABEL[cat]}</li></ol></nav>
<section class="hero"><div class="wrap"><div class="amount-badge">{e(d['badge'])}</div><h1>{e(d['h1'])}</h1><p>{d['lead']}</p></div></section>
<section class="wrap" style="padding:24px 28px 0;"><div style="font-size:14px; line-height:2.2;">
{"" if is_hub else f'<span style="margin-right:14px;"><a href="{hub}">&larr; Back to {e(name)} rebate hub</a></span>' + chr(10) + sib}</div></section>
<article class="article"><div class="wrap">
{article}
</div></article>
{navfooter.render_footer("il", "" if state else slug, "" if state else name, path)}
</body></html>
"""
    out = ROOT / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    return path, w


if __name__ == "__main__":
    only = {a for a in sys.argv[1:] if not a.startswith("--")}
    for slug in NAMES:
        if only and slug not in only:
            continue
        for cat in (HUB if "--hubs" in sys.argv else BUILT):
            r = build(slug, cat)
            if r:
                print("built", r[0], r[1], "words")
