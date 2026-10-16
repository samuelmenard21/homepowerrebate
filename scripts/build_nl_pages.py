#!/usr/bin/env python3
"""Newfoundland and Labrador pages: the province hub (/ca/nl/, --state) and city hubs (--hubs) in the shared layout used for Nova Scotia.
Prose is hand-written in data/nl/pages/state-hub.json and data/nl/pages/<city>/index.json (no fill-in templates).
Local facts come from data/nl-housing-census2021.json (Statistics Canada 2021 Census, table 98-10-0233-01; scripts/pull_nl_census.py).
Program facts are in data/verified-facts/nl.json (takeCHARGE and Government of NL pages). Same quality gate as scripts/build_ns_pages.py.
Usage: python3 scripts/build_nl_pages.py --state | --hubs [city ...]"""
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
LABEL = {"insulation": "Insulation", "windows": "Windows & Doors", "water-heater": "Water Heater", "heat-pump": "Heat Pump", "solar": "Solar", "battery": "Battery Storage",
         "ev-charger": "EV Charger", "smart-thermostats": "Smart Thermostat", "appliances": "Appliance", "hrv": "HRV & Ventilation"}
BUILT = []
HUB = ["index"]
NAMES = {"st-johns": "St. John's", "mount-pearl": "Mount Pearl", "paradise": "Paradise", "corner-brook": "Corner Brook", "labrador-city": "Labrador City"}
HP_ROWS = [r for r in rank.load_rows() if r["region"] == "nl" and r["service"] == "heat-pump"]


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
    more = f'<p style="margin-top:8px;"><a href="/installers/nl/{slug}/{kind}/">See all {e(name)} installers &rarr;</a></p>' if (ROOT / f"installers/nl/{slug}/{kind}/index.html").exists() else ""
    return f"<h2>Top-rated installers in {e(name)}</h2><p>{intro}</p>\n{cards}{more}"


def build(slug, cat):
    name = NAMES[slug]
    pj = ROOT / "data/nl/pages" / slug / f"{cat}.json"
    if not pj.exists():
        return None
    d = json.loads(pj.read_text())
    hub = f"/ca/nl/{slug}/"
    is_hub = cat == "index"
    path = hub if is_hub else f"{hub}{cat}/"
    fids = [i for cd in d["cards"] for i in cd.get("facts", [])] + d.get("facts", [])
    for i in fids:
        assert i in FACTS, f"unknown fact {i}"
    checked = max(FACTS[i]["verified_on"] for i in fids)
    when = date.fromisoformat(checked).strftime("%B %-d, %Y")
    sibs = [k for k in LABEL if k != cat and (ROOT / f"ca/nl/{slug}/{k}/index.html").exists()]
    sib = "".join(f'<span style="margin-right:14px;"><a href="{hub}{k}/">{LABEL[k]} Rebates in {e(name)}</a></span>\n' for k in sibs)
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
<div class="callout"><strong>Want a number for your home?</strong> Run our <a href="/calculator/nl/" style="color:var(--teal,#0d4f5c); font-weight:600;">Newfoundland and Labrador rebate calculator</a>, or <a href="/get-quotes/?province=nl&amp;city={slug}" style="color:var(--teal,#0d4f5c); font-weight:600;">get a plan emailed with the top-rated installers in {e(name)}</a>.</div>
<h2>Common questions</h2>
{faq}
<h2>What to do next</h2>
{d['next']}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read {when}: {sources}. <a href="{hub}">All {e(name)} rebates &rarr;</a> <a href="/programs/newfoundland-oil-to-electric-rebate/">Oil to Electric rebate guide &rarr;</a></p>"""
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
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE}, {"@type": "ListItem", "position": 2, "name": "Newfoundland and Labrador", "item": BASE + "/ca/nl/"},
              {"@type": "ListItem", "position": 3, "name": name, "item": BASE + hub}] + ([] if is_hub else [{"@type": "ListItem", "position": 4, "name": LABEL[cat], "item": BASE + path}])}, faq_ld]
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
{navfooter.render_nav("nl", slug)}
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/ca/nl/">Newfoundland and Labrador</a></li>{"" if is_hub else f'<li><a href="{hub}">{e(name)}</a></li>'}<li aria-current="page">{e(name) if is_hub else LABEL[cat]}</li></ol></nav>
<section class="hero"><div class="wrap"><div class="amount-badge">{e(d['badge'])}</div><h1>{e(d['h1'])}</h1><p>{d['lead']}</p></div></section>
<section class="wrap" style="padding:24px 28px 0;"><div style="font-size:14px; line-height:2.2;">
{"" if is_hub else f'<span style="margin-right:14px;"><a href="{hub}">&larr; Back to {e(name)} rebate hub</a></span>' + chr(10) + sib}</div></section>
<article class="article"><div class="wrap">
{article}
</div></article>
{navfooter.render_footer("nl", slug, name, path)}
</body></html>
"""
    out = ROOT / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    return path, w


# ---------------------------------------------------------------------------------------------------------------------
# Province hub (/ca/nl/): writes the base page. build_hub_tops.py, build_hub_showcase.py and build_hub_tidy.py then add the
# short answer and table, stats strip, city finder and contents block, exactly as for every other region hub.
HUB_TITLE = "Newfoundland and Labrador Home Energy Rebates 2026: Oil to Electric, Heat Pumps, Insulation"
HUB_DESC = ("Newfoundland and Labrador home rebates for 2026: up to $22,000 to switch from oil to a heat pump, takeCHARGE insulation, "
            "air sealing and HRV rebates, no-cost upgrades for lower incomes and the $500 oil supplement. Every amount sourced.")


def build_state_hub():
    d = json.loads((ROOT / "data/nl/pages/state-hub.json").read_text())
    for i in d["facts"]:
        assert i in FACTS, f"unknown fact {i}"
    when = date.fromisoformat(max(FACTS[i]["verified_on"] for i in d["facts"])).strftime("%B %-d, %Y")
    # borrow the hub template's stylesheets from a converted hub (inline <style> blocks are gone since the 2026-10-11 template move)
    mn = (ROOT / "us/mn/index.html").read_text(encoding="utf-8")
    head = mn[:mn.find("</head>")]
    css = "\n".join(re.findall(r'<link rel="stylesheet" href="/assets/tpl/(?:hub|common)-[^"]+" data-hpr-tpl>', head))
    cards = "".join(
        f'<div class="rebate-card"><h4 aria-level="3">{e(NAMES[s])}</h4><p style="margin-bottom:8px;">{e(u)}</p><p><a href="/ca/nl/{s}/">View {e(NAMES[s])} rebates &rarr;</a></p></div>'
        for s, u in [("st-johns", "Newfoundland Power, takeCHARGE and the City's Shift program"), ("mount-pearl", "1970s and 80s homes, many with a basement apartment"),
                     ("paradise", "Newer homes: check the 2014 insulation rule"), ("corner-brook", "Older homes on the west coast"), ("labrador-city", "NL Hydro customers in Labrador West")])
    secs = "".join(f"<h2>{h}</h2>{b.replace('{cards}', cards)}" for h, b in d["sections"])
    faq = "".join(f'<h3>{e(q)}</h3><p>{e(a)}</p>' for q, a in d["faq"])
    src = "<ul>" + "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a></li>' for t, u in d["refs"]) + "</ul>"
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in d["faq"]]}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE}, {"@type": "ListItem", "position": 2, "name": "Newfoundland and Labrador", "item": BASE + "/ca/nl/"}]}
    links = ('<p style="max-width:880px;margin:12px auto;padding:0 20px;"><b>Program guides:</b> <a href="/programs/newfoundland-oil-to-electric-rebate/">Oil to Electric rebate</a> · '
             '<a href="/programs/national-heat-pump-rebate/">National Heat Pump Rebate</a></p>')
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(HUB_TITLE)}</title>
<meta name="description" content="{e(HUB_DESC)}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="{BASE}/ca/nl/">
<meta property="og:title" content="{e(HUB_TITLE)}">
<meta property="og:description" content="{e(HUB_DESC)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{BASE}/ca/nl/">
<meta property="og:image" content="{BASE}/og-image.jpg">
<meta name="twitter:title" content="{e(HUB_TITLE)}">
<meta name="twitter:description" content="{e(HUB_DESC)}">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-W33G4TGRHD');</script>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(crumb, ensure_ascii=False)}</script>
{css}
</head>
<body>
{navfooter.render_nav("nl", "")}
<!-- CANONICAL-BREADCRUMB-START -->
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">Newfoundland and Labrador</li></ol></nav>
<!-- CANONICAL-BREADCRUMB-END -->
<header class="hero"><div class="wrap"><div class="eyebrow">takeCHARGE · Newfoundland Power · NL Hydro</div><h1>Home Energy Rebates in Newfoundland and Labrador</h1><p class="sub">A plain guide to 2026 home energy rebates in Newfoundland and Labrador, starting with getting off oil. Each amount comes from the program's own page.</p></div></header>
<!-- PROGRAM-LINKS-START -->{links}<!-- PROGRAM-LINKS-END -->
<!-- CALC-LINK-START --><p style="max-width:880px;margin:12px auto;padding:0 20px;"><b>Not sure what you qualify for?</b> <a href="/calculator/nl/">Use the Newfoundland and Labrador rebate calculator</a>.</p><!-- CALC-LINK-END -->
<article class="article">
  <div class="wrap">
{secs}
<h2>Quick questions</h2>
<details class="hub-fold"><summary>Read the questions and answers</summary>
{faq}
</details>
<h2>Sources</h2>
<details class="hub-fold"><summary>See the sources</summary>
{src}
</details>
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. We read each page on {when}.</p>
  </div>
</article>
{navfooter.render_footer("nl", "", "", "/ca/nl/")}
</body>
</html>
"""
    out = ROOT / "ca/nl/index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    print("built /ca/nl/", ca.words(secs), "words")


if __name__ == "__main__":
    if "--state" in sys.argv:
        build_state_hub()
        sys.exit()
    only = {a for a in sys.argv[1:] if not a.startswith("--")}
    for slug in NAMES:
        if only and slug not in only:
            continue
        for cat in (HUB if "--hubs" in sys.argv else BUILT):
            r = build(slug, cat)
            if r:
                print("built", r[0], r[1], "words")
