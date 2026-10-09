#!/usr/bin/env python3
"""Minnesota city category pages in the shared layout used for California, BC, Ontario, Colorado and Nova Scotia.
Prose is hand-written per page in data/mn/pages/<city>/<category>.json (hpr-category-page-localization bans fill-in-the-blank templates).
Local facts come from data/mn-housing-acs.json (US Census ACS 5-year 2020-2024, tables B25001/B25003/B25024/B25034/B25040; scripts/pull_mn_acs.py)
and city-climate-data.json. Minnesota programs differ by utility (Xcel Energy, CenterPoint Energy, Minnesota Power, Rochester Public Utilities, plus the City of Minneapolis), so pages are built only where a city has something distinct to say.
Smart thermostats is a state page (build_state_topic_pages.py); other city category URLs redirect (data/redirects-pending/mn.txt). Same quality gate as scripts/build_ca_pages.py.
Usage: python3 scripts/build_mn_pages.py [--hubs] [city ...]"""
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
BUILT = ["heat-pump", "water-heater", "insulation"]
STATE = {"smart-thermostats": "Smart Thermostat"}
HUB = ["index"]
NAMES = {"minneapolis": "Minneapolis", "saint-paul": "Saint Paul", "rochester": "Rochester", "duluth": "Duluth"}
ROWS = [r for r in rank.load_rows() if r["region"] == "mn"]  # none yet: Minnesota has no installer data, so no installer block is shown


def installers(slug, cat):
    svc = "insulation" if cat == "insulation" else "heat-pump"
    rows = [r for r in ROWS if r["service"] == svc and rank.slugify(r["city"]) == slug and r.get("reviews", 0) >= 5]
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
    kind = "insulation" if cat == "insulation" else "heat-pump"
    more = f'<p style="margin-top:8px;"><a href="/installers/mn/{slug}/{kind}/">See all {e(name)} installers &rarr;</a></p>' if (ROOT / f"installers/mn/{slug}/{kind}/index.html").exists() else ""
    return f"<h2>Top-rated installers in {e(name)}</h2><p>{intro}</p>\n{cards}{more}"


def build(slug, cat):
    name = NAMES[slug]
    pj = ROOT / "data/mn/pages" / slug / f"{cat}.json"
    if not pj.exists():
        return None
    d = json.loads(pj.read_text())
    hub = f"/us/mn/{slug}/"
    is_hub = cat == "index"
    path = hub if is_hub else f"{hub}{cat}/"
    fids = [i for cd in d["cards"] for i in cd.get("facts", [])] + d.get("facts", [])
    for i in fids:
        assert i in FACTS, f"unknown fact {i}"
    for cd in d["cards"]:
        if cd.get("facts") and "status" not in cd:
            cd["status"] = FACTS[cd["facts"][0]]["status"]
    checked = max(FACTS[i]["verified_on"] for i in fids)
    when = date.fromisoformat(checked).strftime("%B %-d, %Y")
    sibs = [k for k in LABEL if k != cat and (ROOT / "data/mn/pages" / slug / f"{k}.json").exists()]
    sibs_state = [k for k in STATE if k != cat and (ROOT / "data/state-topics" / f"mn-{k}.json").exists()]
    sib = "".join(f'<span style="margin-right:14px;"><a href="{hub}{k}/">{LABEL[k]} Rebates in {e(name)}</a></span>\n' for k in sibs)
    sib += "".join(f'<span style="margin-right:14px;"><a href="/us/mn/{k}/">Minnesota {STATE[k]} Rebates</a></span>\n' for k in sibs_state)
    guides = ("<h2>Every rebate guide for " + e(name) + "</h2><ul>" + "".join(f'<li><a href="{hub}{k}/">{LABEL[k]} rebates in {e(name)}</a></li>' for k in sibs) + "".join(f'<li><a href="/us/mn/{k}/">Minnesota {STATE[k].lower()} rebates (all utilities side by side)</a></li>' for k in sibs_state) + "</ul>") if is_hub else ""
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
<div class="callout"><strong>Want your exact number?</strong> Run our <a href="/calculator/mn/" style="color:var(--teal,#0d4f5c); font-weight:600;">Minnesota rebate calculator</a>, or <a href="/get-quotes/?city={slug}&amp;province=mn" style="color:var(--teal,#0d4f5c); font-weight:600;">get a plan emailed with the top-rated installers in {e(name)}</a>.</div>
<h2>Common questions</h2>
{faq}
<h2>What to do next</h2>
{d['next']}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read {when}: {sources}. <a href="{hub}">All {e(name)} rebates &rarr;</a> <a href="{d.get('program_url', '/programs/xcel-energy-minnesota-rebates/')}">{e(d.get('program_label', 'Every Xcel Energy Minnesota rebate'))} &rarr;</a></p>"""
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
    if False:
        problems.append("enhanced amount without income condition")
    if problems:
        raise SystemExit(f"{path}: " + "; ".join(problems))
    title, desc = d["title"], d["desc"]
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", html.unescape(a))}} for q, a in d["faq"]]}
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "author": ca.AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
           "datePublished": checked, "dateModified": checked, "mainEntityOfPage": BASE + path},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE}, {"@type": "ListItem", "position": 2, "name": "Minnesota", "item": BASE + "/us/mn/"},
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
{navfooter.render_nav("mn", slug)}
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/us/mn/">Minnesota</a></li>{"" if is_hub else f'<li><a href="{hub}">{e(name)}</a></li>'}<li aria-current="page">{e(name) if is_hub else LABEL[cat]}</li></ol></nav>
<section class="hero"><div class="wrap"><div class="amount-badge">{e(d['badge'])}</div><h1>{e(d['h1'])}</h1><p>{d['lead']}</p></div></section>
<section class="wrap" style="padding:24px 28px 0;"><div style="font-size:14px; line-height:2.2;">
{"" if is_hub else f'<span style="margin-right:14px;"><a href="{hub}">&larr; Back to {e(name)} rebate hub</a></span>' + chr(10) + sib}</div></section>
<article class="article"><div class="wrap">
{article}
</div></article>
{navfooter.render_footer("mn", slug, name, path)}
</body></html>
"""
    out = ROOT / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    return path, w


def _main():
    only = {a for a in sys.argv[1:] if not a.startswith("--")}
    for slug in NAMES:
        if only and slug not in only:
            continue
        for cat in (HUB if "--hubs" in sys.argv else BUILT):
            r = build(slug, cat)
            if r:
                print("built", r[0], r[1], "words")


# ---------------------------------------------------------------------------------------------------------------------
# State hub (/us/mn/): writes the base page. build_hub_tops.py, build_hub_showcase.py and build_hub_tidy.py then add the
# short answer and table, stats strip, city finder and contents block, exactly as for every other region hub.
HUB_TITLE = "Minnesota Home Energy Rebates 2026: Cold-Climate Heat Pumps, Insulation, Water Heaters"
HUB_DESC = ("Minnesota home energy rebates for 2026 from Xcel Energy, CenterPoint Energy, Minnesota Power, Rochester Public Utilities and Minneapolis, "
            "with the amount, the rules and the date we last read each official page.")


def build_state_hub():
    d = json.loads((ROOT / "data/mn/pages/state-hub.json").read_text())
    vt = (ROOT / "us/vt/index.html").read_text(encoding="utf-8")
    css = "\n".join(re.findall(r"<style>.*?</style>", vt[:vt.find("<!-- CANONICAL-NAV-START -->")], re.S))
    cards = "".join(
        f'<div class="rebate-card"><h4>{e(NAMES[s])}</h4><p style="margin-bottom:8px;">{e(u)}</p><p><a href="/us/mn/{s}/">View {e(NAMES[s])} rebates &rarr;</a></p></div>'
        for s, u in [("minneapolis", "City rebate, Xcel Energy and CenterPoint Energy"), ("saint-paul", "Xcel Energy and CenterPoint Energy"),
                     ("rochester", "Rochester Public Utilities (city-owned electric company)"), ("duluth", "Minnesota Power")])
    secs = "".join(f"<h2>{h}</h2>{b.replace('{cards}', cards)}" for h, b in d["sections"])
    faq = "".join(f'<h3>{e(q)}</h3><p>{e(a)}</p>' for q, a in d["faq"])
    cat_links = (
        '<h3>Heat pumps</h3><ul><li><a href="/us/mn/minneapolis/heat-pump/">Minneapolis heat pump rebates</a></li><li><a href="/us/mn/rochester/heat-pump/">Rochester heat pump rebates</a></li>'
        '<li><a href="/us/mn/duluth/heat-pump/">Duluth heat pump rebates</a></li></ul>'
        '<h3>Water heaters</h3><ul><li><a href="/us/mn/rochester/water-heater/">Rochester water heater rebates</a></li><li><a href="/us/mn/duluth/water-heater/">Duluth water heater rebates</a></li></ul>'
        '<h3>Insulation</h3><ul><li><a href="/us/mn/minneapolis/insulation/">Minneapolis insulation rebates</a></li></ul>'
        '<h3>Thermostats</h3><ul><li><a href="/us/mn/smart-thermostats/">Minnesota smart thermostat rebates</a></li></ul>')
    refs = [("Xcel Energy Minnesota home rebates", "https://mn.my.xcelenergy.com/s/residential/home-rebates"),
            ("CenterPoint Energy Minnesota efficiency programs", "https://www.centerpointenergy.com/en-us/savings-solutions/energy-efficiency"),
            ("Minnesota Power residential rebates", "https://www.mnpower.com/ProgramsRebates/RebatesAndSavings"),
            ("Rochester Public Utilities residential rebates", "https://www.rpu.org/rebates-programs/conserve-save-rebates/residential-rebates/"),
            ("City of Minneapolis Green Cost Share", "https://www.minneapolismn.gov/government/programs-initiatives/environmental-programs/green-cost-share/energy-efficiency/energy-rebates/"),
            ("Save Energy Minnesota (Department of Commerce)", "https://mn.gov/commerce/energy/consumer/energy-programs/save-energy-mn.jsp")]
    src = "<ul>" + "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a></li>' for t, u in refs) + "</ul>"
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in d["faq"]]}
    crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE}, {"@type": "ListItem", "position": 2, "name": "Minnesota", "item": BASE + "/us/mn/"}]}
    links = ('<p style="max-width:880px;margin:12px auto;padding:0 20px;"><b>Program guides:</b> <a href="/programs/xcel-energy-minnesota-rebates/">Xcel Energy</a> · '
             '<a href="/programs/centerpoint-energy-minnesota-rebates/">CenterPoint Energy</a> · <a href="/programs/minnesota-power-rebates/">Minnesota Power</a> · '
             '<a href="/programs/rochester-public-utilities-rebates/">Rochester Public Utilities</a> · <a href="/programs/save-energy-minnesota/">Save Energy Minnesota</a></p>')
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(HUB_TITLE)}</title>
<meta name="description" content="{e(HUB_DESC)}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="{BASE}/us/mn/">
<meta property="og:title" content="{e(HUB_TITLE)}">
<meta property="og:description" content="{e(HUB_DESC)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{BASE}/us/mn/">
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
{navfooter.render_nav("mn", "")}
<!-- CANONICAL-BREADCRUMB-START -->
<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">Minnesota</li></ol></nav>
<!-- CANONICAL-BREADCRUMB-END -->
<header class="hero"><div class="wrap"><div class="eyebrow">Xcel Energy · CenterPoint · Minnesota Power</div><h1>Home Energy Rebates in Minnesota</h1><p class="sub">A plain guide to 2026 Minnesota home energy rebates, with cold-climate heat pumps first. Each amount comes from the program's own page.</p></div></header>
<!-- PROGRAM-LINKS-START -->{links}<!-- PROGRAM-LINKS-END -->
<!-- CALC-LINK-START --><p style="max-width:880px;margin:12px auto;padding:0 20px;"><b>Not sure what you qualify for?</b> <a href="/calculator/mn/">Use the Minnesota rebate calculator</a>.</p><!-- CALC-LINK-END -->
<article class="article">
  <div class="wrap">
{secs}
<h2>Rebate finder, by category</h2>
<details class="hub-fold"><summary>Open the full rebate list</summary>
{cat_links}
</details>
<h2>Quick questions</h2>
<details class="hub-fold"><summary>Read the questions and answers</summary>
{faq}
</details>
<h2>Sources</h2>
<details class="hub-fold"><summary>See the sources</summary>
{src}
</details>
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. We read each page on October 6, 2026.</p>
  </div>
</article>
{navfooter.render_footer("mn", "", "", "/us/mn/")}
</body>
</html>
"""
    out = ROOT / "us/mn/index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    print("built /us/mn/", ca.words(secs), "words")


if __name__ == "__main__":
    if "--state" in sys.argv:
        build_state_hub()
    else:
        _main()
