#!/usr/bin/env python3
"""New Jersey pages (Newark, Jersey City, Toms River, Atlantic City) in the shared layout used for Pennsylvania, California, BC, Ontario and Nova Scotia.
Copied from scripts/build_pa_pages.py. Prose is hand-written per page in data/nj/pages/<city>/<category>.json; the statewide hub is data/nj/state-hub.json.
Local facts come from data/nj-housing-acs.json (US Census ACS 5-year 2020-2024 via scripts/pull_nj_acs.py). Amounts come only from data/verified-facts/nj.json.
Statewide topics (solar, battery, EV charger, water heater, thermostats, appliances, insulation) are data/state-topics/nj-*.json (scripts/build_state_topic_pages.py).
Same quality gate as build_ca_pages.py. No New Jersey installers are ranked yet, so no installer block is built.
Usage: python3 scripts/build_nj_pages.py [city ...] [--hubs] [--state]"""
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

e = html.escape
BASE = ca.BASE
FACTS = ca.FACTS
LABEL = {"insulation": "Insulation", "windows-doors": "Windows & Doors", "water-heater": "Water Heater", "heat-pump": "Heat Pump", "solar": "Solar", "battery": "Battery Storage",
         "ev-charger": "EV Charger", "smart-thermostats": "Smart Thermostat", "appliances": "Appliance", "hrv": "HRV & Ventilation"}
BUILT = ["heat-pump"]
HUB = ["index"]
NAMES = {"newark": "Newark", "jersey-city": "Jersey City", "toms-river": "Toms River", "atlantic-city": "Atlantic City"}
UTILITY = {"newark": ("/programs/pseg-rebates/", "PSE&G"), "jersey-city": ("/programs/pseg-rebates/", "PSE&G"),
           "toms-river": ("/programs/jcpl-rebates/", "JCP&L"), "atlantic-city": ("/programs/atlantic-city-electric-rebates/", "Atlantic City Electric")}
TOPICS = [("solar", "Solar"), ("battery", "Home battery"), ("ev-charger", "Electric car and charger"), ("water-heater", "Heat pump water heater"),
          ("smart-thermostats", "Smart thermostat"), ("appliances", "Appliance"), ("insulation", "Insulation and weatherization")]
LABEL_TOPIC = dict(TOPICS)


def finish(path, page):
    out = ROOT / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")


def gate(path, article, d):
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
    if re.search(r"\$16,000|Greener Homes", article):
        problems.append("stale figure")
    if problems:
        raise SystemExit(f"{path}: " + "; ".join(problems))
    return w


def head(title, desc, path, lds):
    return f"""<!DOCTYPE html>
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
"""


def jsonld(d, title, desc, checked, path, crumbs):
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", html.unescape(a))}} for q, a in d["faq"]]}
    items = [{"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + u} for i, (n, u) in enumerate(crumbs)]
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "author": ca.AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
           "datePublished": checked, "dateModified": checked, "mainEntityOfPage": BASE + path},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}, faq_ld]
    return "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)


def build(slug, cat):
    name = NAMES[slug]
    pj = ROOT / "data/nj/pages" / slug / f"{cat}.json"
    if not pj.exists():
        return None
    d = json.loads(pj.read_text())
    hub = f"/us/nj/{slug}/"
    is_hub = cat == "index"
    path = hub if is_hub else f"{hub}{cat}/"
    fids = [i for cd in d["cards"] for i in cd.get("facts", [])] + d.get("facts", [])
    for i in fids:
        assert i in FACTS, f"unknown fact {i}"
    checked = max(FACTS[i]["verified_on"] for i in fids)
    when = date.fromisoformat(checked).strftime("%B %-d, %Y")
    sibs = [k for k in LABEL if k != cat and (ROOT / f"us/nj/{slug}/{k}/index.html").exists()]
    sib = "".join(f'<span style="margin-right:14px;"><a href="{hub}{k}/">{LABEL[k]} Rebates in {e(name)}</a></span>\n' for k in sibs)
    guides = ""
    if is_hub:
        li = "".join(f'<li><a href="{hub}{k}/">{LABEL[k]} rebates in {e(name)}</a></li>' for k in sibs)
        li += "".join(f'<li><a href="/us/nj/{k}/">{t} rebates in New Jersey</a></li>' for k, t in TOPICS if (ROOT / f"us/nj/{k}/index.html").exists())
        guides = f"<h2>Every rebate guide for {e(name)} homes</h2><ul>{li}</ul>"
    cards = "".join(ca.card(x) for x in d["cards"])
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
{claim}
<div class="callout"><strong>Want your exact number?</strong> Run our <a href="/calculator/nj/" style="color:var(--teal,#0d4f5c); font-weight:600;">New Jersey rebate calculator</a>, or <a href="/get-quotes/" style="color:var(--teal,#0d4f5c); font-weight:600;">get a plan emailed with the top-rated installers near you</a>.</div>
<h2>Common questions</h2>
{faq}
<h2>What to do next</h2>
{d['next']}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read {when}: {sources}. <a href="{hub}">All {e(name)} rebates &rarr;</a> <a href="{UTILITY[slug][0]}">Every {UTILITY[slug][1]} rebate &rarr;</a> <a href="/us/nj/">All New Jersey rebates &rarr;</a></p>"""
    w = gate(path, article, d)
    title, desc = d["title"], d["desc"]
    crumbs = [("Home", "/"), ("New Jersey", "/us/nj/"), (name, hub)] + ([] if is_hub else [(LABEL[cat], path)])
    lds = jsonld(d, title, desc, checked, path, crumbs)
    page = head(title, desc, path, lds) + f"""{navfooter.render_nav("nj", slug)}
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/us/nj/">New Jersey</a></li>{"" if is_hub else f'<li><a href="{hub}">{e(name)}</a></li>'}<li aria-current="page">{e(name) if is_hub else LABEL[cat]}</li></ol></nav>
<section class="hero"><div class="wrap"><div class="amount-badge">{e(d['badge'])}</div><h1>{e(d['h1'])}</h1><p>{d['lead']}</p></div></section>
<section class="wrap" style="padding:24px 28px 0;"><div style="font-size:14px; line-height:2.2;">
{'<span style="margin-right:14px;"><a href="/us/nj/">&larr; All New Jersey rebates</a></span>' if is_hub else f'<span style="margin-right:14px;"><a href="{hub}">&larr; Back to {e(name)} rebate hub</a></span>' + chr(10) + sib}</div></section>
<article class="article"><div class="wrap">
{article}
</div></article>
{navfooter.render_footer("nj", slug, name, path)}
</body></html>
"""
    finish(path, page)
    return path, w


def build_state():
    d = json.loads((ROOT / "data/nj/state-hub.json").read_text())
    path = "/us/nj/"
    fids = d["facts"]
    for i in fids:
        assert i in FACTS, f"unknown fact {i}"
    checked = max(FACTS[i]["verified_on"] for i in fids)
    when = date.fromisoformat(checked).strftime("%B %-d, %Y")
    city_li = "".join(f'<li><a href="/us/nj/{s}/">{n} rebates</a>: {d["cities"][s]}</li>' for s, n in NAMES.items())
    hp = "".join(f'<li><a href="/us/nj/{s}/heat-pump/">{NAMES[s]} heat pump rebates</a></li>' for s in NAMES if (ROOT / f"us/nj/{s}/heat-pump/index.html").exists())
    topic_li = "".join(f'<li><a href="/us/nj/{k}/">{t} rebates in New Jersey</a>: {d["topics"][k]}</li>' for k, t in TOPICS if (ROOT / f"us/nj/{k}/index.html").exists())
    util_li = "".join(f'<li><a href="/programs/{s}/">{n}</a>: {b}</li>' for s, n, b in d["utilities"])
    faq = "".join(f'<div class="faq-item"><h3>{e(q)}</h3><p>{a}</p></div>\n' for q, a in d["faq"])
    sources = " ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a>' + ("," if i < len(d["refs"]) - 1 else "") for i, (t, u) in enumerate(d["refs"]))
    article = f"""{''.join(f"<h2>{h}</h2>{b}" for h, b in d['sections'])}
<h2>Find your utility</h2>
{d['utility_intro']}
<ul>{util_li}</ul>
<h2>New Jersey city guides</h2>
{d['city_intro']}
<ul>{city_li}</ul>
<ul>{hp}</ul>
<h2>Statewide guides by upgrade</h2>
{d['topic_intro']}
<ul>{topic_li}</ul>
<div class="callout"><strong>Want your exact number?</strong> Run our <a href="/calculator/nj/" style="color:var(--teal,#0d4f5c); font-weight:600;">New Jersey rebate calculator</a>, or <a href="/get-quotes/" style="color:var(--teal,#0d4f5c); font-weight:600;">get a plan emailed with the top-rated installers near you</a>.</div>
<h2>Common questions</h2>
{faq}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read {when}: {sources}.</p>"""
    w = gate(path, article, d)
    title, desc = d["title"], d["desc"]
    lds = jsonld(d, title, desc, checked, path, [("Home", "/"), ("New Jersey", path)])
    page = head(title, desc, path, lds) + f"""{navfooter.render_nav("nj", "")}
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">New Jersey</li></ol></nav>
<header class="hero"><div class="wrap"><h1>{e(d['h1'])}</h1><p class="sub">{d['lead']}</p></div></header>
<article class="article"><div class="wrap">
{article}
</div></article>
{navfooter.render_footer("nj", "", "", path)}
</body></html>
"""
    finish(path, page)
    return path, w


if __name__ == "__main__":
    only = {a for a in sys.argv[1:] if not a.startswith("--")}
    if "--state" in sys.argv:
        r = build_state()
        print("built", r[0], r[1], "words")
    for slug in NAMES:
        if only and slug not in only:
            continue
        for cat in (HUB if "--hubs" in sys.argv else BUILT):
            r = build(slug, cat)
            if r:
                print("built", r[0], r[1], "words")
