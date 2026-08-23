#!/usr/bin/env python3
"""Generate /powerscore/index.html from powerscore-data.json.

Reads the computed PowerScore data (see scripts/build_powerscore.py) and
renders a static, data-driven leaderboard page using the site's existing
nav/footer partial, palette, and typography.
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "powerscore-data.json").read_text())

CAT_LABELS = DATA["category_labels"]
CATEGORIES = list(CAT_LABELS.keys())
CAT_EMOJI = {
    "heat-pump": "&#128293;",
    "insulation": "&#127777;&#65039;",
    "solar": "&#9728;&#65039;",
    "battery": "&#128267;",
    "water-heater": "&#128167;",
    "smart-thermostats": "&#127777;&#65039;",
    "ev-charger": "&#128663;",
    "windows-doors": "&#129003;",
}

rows = DATA["leaderboard_overall"]
total_cities = DATA["stats"]["total_cities"]
total_regions = DATA["stats"]["total_regions"]


def esc(s):
    return html.escape(str(s), quote=True)


def score_band(score):
    if score >= 75:
        return "band-great"
    if score >= 50:
        return "band-good"
    if score >= 25:
        return "band-fair"
    return "band-low"


def gauge_style(score):
    pct = max(0, min(100, score))
    deg = pct * 3.6
    return f"--score-deg:{deg}deg;"


# ---------- Overall leaderboard rows ----------
def render_overall_rows():
    out = []
    for i, r in enumerate(rows, start=1):
        pills = "".join(
            f'<span class="cat-pill {score_band(r["categories"][c]["score"])}" title="{esc(CAT_LABELS[c])}: {r["categories"][c]["score"]}/100">{CAT_EMOJI[c]}{r["categories"][c]["score"]:.0f}</span>'
            for c in CATEGORIES
        )
        out.append(f'''<tr id="city-{esc(r["region"]).replace("/", "-")}-{esc(r["slug"]).replace("/", "-")}" data-slug="{esc(r["region"])}/{esc(r["slug"])}" data-overall="{r["overall"]}">
  <td class="rank-cell">#{i}</td>
  <td class="city-cell"><a href="{esc(r["url"])}">{esc(r["label"])}</a><span class="region-tag">{esc(r["region_label"])}</span></td>
  <td class="overall-cell"><span class="overall-badge {score_band(r["overall"])}">{r["overall"]:.0f}</span></td>
  <td class="pills-cell">{pills}</td>
</tr>''')
    return "\n".join(out)


# ---------- Per-category leaderboards ----------
def render_category_section(cat):
    cat_rows = DATA["leaderboard_by_category"][cat]
    items = []
    for i, r in enumerate(cat_rows[:25], start=1):
        status_label = {"open": "Open", "limited": "Funding Limited", "closed": "No Rebate / Closed"}[r["status"]]
        status_class = {"open": "status-pill-open", "limited": "status-pill-limited", "closed": "status-pill-closed"}[r["status"]]
        dollar = f"${r['dollar_value']:,.0f}" if r["dollar_value"] else "&mdash;"
        items.append(f'''<tr>
  <td class="rank-cell">#{i}</td>
  <td class="city-cell"><a href="{esc(r["url"])}">{esc(r["label"])}</a><span class="region-tag">{esc(r["region_label"])}</span></td>
  <td><span class="overall-badge small {score_band(r["score"])}">{r["score"]:.0f}</span></td>
  <td>{dollar}</td>
  <td><span class="status-pill {status_class}">{status_label}</span></td>
</tr>''')
    return "\n".join(items)


def render_category_tabs():
    buttons = []
    panels = []
    for i, cat in enumerate(CATEGORIES):
        active = " active" if i == 0 else ""
        buttons.append(f'<button type="button" class="cat-tab{active}" data-cat="{cat}" onclick="showCategory(\'{cat}\')">{CAT_EMOJI[cat]} {esc(CAT_LABELS[cat])}</button>')
        panels.append(f'''<div class="cat-panel{active}" id="panel-{cat}">
  <h3>Best cities for {esc(CAT_LABELS[cat])} rebates</h3>
  <div class="table-wrap">
  <table class="score-table">
    <thead><tr><th>Rank</th><th>City</th><th>Score</th><th>Top $ Available</th><th>Status</th></tr></thead>
    <tbody>
{render_category_section(cat)}
    </tbody>
  </table>
  </div>
</div>''')
    return "\n".join(buttons), "\n".join(panels)


# ---------- City picker options ----------
def render_city_options():
    out = []
    for r in rows:
        out.append(f'<option value="{esc(r["region"])}/{esc(r["slug"])}">{esc(r["label"])}, {esc(r["region_label"])}</option>')
    return "\n".join(out)


# ---------- JSON-LD ----------
def render_jsonld():
    dataset = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "HomePowerRebate PowerScore City Rebate Rankings",
        "description": "A calculated 0-100 score for every city HomePowerRebate covers, ranking how much home-energy rebate money is available, how many programs stack, and whether funding is open, based on published rebate amounts.",
        "url": "https://homepowerrebate.com/powerscore/",
        "creator": {"@type": "Organization", "name": "HomePowerRebate"},
        "variableMeasured": ["Overall PowerScore"] + [CAT_LABELS[c] + " PowerScore" for c in CATEGORIES],
        "temporalCoverage": "2026",
    }
    top5 = rows[:5]
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "PowerScore: See How Your City's Home Energy Rebates Rank",
        "description": f"We scored all {total_cities} cities HomePowerRebate covers across {total_regions} regions on rebate dollar value, program status, and stackability to build a 0-100 PowerScore leaderboard.",
        "author": {"@type": "Person", "name": "Sam Menard", "url": "https://homepowerrebate.com/about"},
        "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
        "mainEntityOfPage": "https://homepowerrebate.com/powerscore/",
        "datePublished": "2026-08-23",
        "dateModified": "2026-08-23",
    }
    return (
        '<script type="application/ld+json">' + json.dumps(dataset) + "</script>\n"
        '<script type="application/ld+json">' + json.dumps(article) + "</script>"
    )


overall_rows_html = render_overall_rows()
cat_buttons_html, cat_panels_html = render_category_tabs()
city_options_html = render_city_options()
jsonld_html = render_jsonld()

TOP_CITY = rows[0]
BOTTOM_REGION_COUNT = total_regions

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PowerScore: City Rebate Rankings 2026 | HomePowerRebate</title>

<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-W33G4TGRHD');
</script>

<meta name="description" content="Every city HomePowerRebate covers, scored 0-100 on rebate dollar value, program status, and stackability. See how your city ranks for heat pump, solar, battery, and 5 more categories.">
<link rel="canonical" href="https://homepowerrebate.com/powerscore/">
<meta property="og:title" content="PowerScore: City Rebate Rankings 2026 | HomePowerRebate">
<meta property="og:description" content="We scored {total_cities} cities across {total_regions} regions on rebate value, status, and stackability. See how your city ranks.">
<meta property="og:type" content="article">
<meta property="og:image" content="https://homepowerrebate.com/og-image.svg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:type" content="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">

{jsonld_html}

<style>
:root {{
  --ink: #0a2a2e;
  --ink-soft: #1a3d42;
  --paper: #faf7f2;
  --paper-warm: #f5efe5;
  --teal: #0d4f5c;
  --teal-deep: #08363f;
  --amber: #d4751c;
  --amber-bright: #e88a2e;
  --green-money: #2d6a4f;
  --red-flag: #b04545;
  --rule: #d9d0c1;
  --sage: #6f8f7a;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--paper); color: var(--ink); font-family: 'Inter Tight', sans-serif; line-height: 1.6; }}
h1, h2, h3, h4 {{ font-family: 'Fraunces', serif; color: var(--teal-deep); }}
.wrap {{ max-width: 1180px; margin: 0 auto; padding: 0 28px; }}
a {{ color: var(--teal); }}

/* ---- hero ---- */
.hero {{ background: linear-gradient(135deg, var(--teal-deep), var(--teal)); color: #fff; padding: 64px 28px 56px; text-align: center; }}
.hero .eyebrow {{ font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: rgba(255,255,255,0.75); margin-bottom: 14px; }}
.hero h1 {{ color: #fff; font-size: clamp(32px, 5vw, 50px); line-height: 1.12; margin: 0 0 16px; max-width: 780px; margin-left: auto; margin-right: auto; }}
.hero p.lead {{ font-size: 17px; color: rgba(255,255,255,0.85); max-width: 620px; margin: 0 auto 28px; }}
.hero-stats {{ display: flex; justify-content: center; gap: 36px; flex-wrap: wrap; margin-top: 8px; }}
.hero-stat {{ text-align: center; }}
.hero-stat .num {{ font-family: 'Fraunces', serif; font-size: 30px; font-weight: 700; color: var(--amber-bright); }}
.hero-stat .lbl {{ font-size: 12px; color: rgba(255,255,255,0.7); text-transform: uppercase; letter-spacing: .05em; }}

/* ---- city picker + gauge ---- */
.picker-section {{ padding: 48px 28px; }}
.picker-card {{ background: #fff; border: 1px solid var(--rule); border-radius: 16px; padding: 32px; box-shadow: 0 6px 24px rgba(10,42,46,0.06); }}
.picker-card h2 {{ margin-top: 0; font-size: 24px; }}
.picker-row {{ display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }}
.picker-row select {{ flex: 1; min-width: 240px; padding: 12px 14px; border-radius: 8px; border: 1px solid var(--rule); font-family: 'Inter Tight', sans-serif; font-size: 15px; background: #fff; color: var(--ink); }}
.picker-row button {{ padding: 12px 22px; background: var(--amber); color: #fff; border: none; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 15px; }}
.picker-row button:hover {{ background: var(--amber-bright); }}

.result-box {{ display: none; margin-top: 28px; padding-top: 28px; border-top: 1px solid var(--rule); align-items: center; gap: 32px; flex-wrap: wrap; }}
.result-box.show {{ display: flex; }}
.gauge {{ --score-deg: 0deg; width: 148px; height: 148px; border-radius: 50%; flex-shrink: 0; background: conic-gradient(var(--amber) var(--score-deg), #eee var(--score-deg)); display: flex; align-items: center; justify-content: center; position: relative; }}
.gauge::before {{ content: ''; position: absolute; inset: 12px; background: #fff; border-radius: 50%; }}
.gauge .gauge-num {{ position: relative; font-family: 'Fraunces', serif; font-weight: 700; font-size: 38px; color: var(--teal-deep); }}
.gauge .gauge-sub {{ position: relative; font-size: 11px; color: var(--sage); text-transform: uppercase; letter-spacing: .04em; margin-top: -6px; }}
.result-text h3 {{ margin: 0 0 6px; font-size: 22px; }}
.result-text p {{ margin: 0 0 12px; color: var(--ink-soft); font-size: 15px; }}
.result-text a.cta {{ display: inline-block; padding: 10px 20px; background: var(--teal-deep); color: #fff; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; }}

/* ---- category badges/pills ---- */
.overall-badge {{ display: inline-flex; align-items: center; justify-content: center; min-width: 40px; height: 40px; border-radius: 50%; font-family: 'Fraunces', serif; font-weight: 700; font-size: 16px; color: #fff; }}
.overall-badge.small {{ min-width: 32px; height: 32px; font-size: 13px; }}
.band-great {{ background: var(--green-money); }}
.band-good {{ background: var(--teal); }}
.band-fair {{ background: var(--amber); }}
.band-low {{ background: var(--red-flag); }}

.cat-pill {{ display: inline-flex; align-items: center; gap: 3px; font-size: 11px; font-weight: 700; padding: 3px 7px; border-radius: 999px; margin: 2px; color: #fff; white-space: nowrap; }}
.cat-pill.band-great {{ background: rgba(45,106,79,0.9); }}
.cat-pill.band-good {{ background: rgba(13,79,92,0.9); }}
.cat-pill.band-fair {{ background: rgba(212,117,28,0.9); }}
.cat-pill.band-low {{ background: rgba(176,69,69,0.85); }}

.status-pill {{ display: inline-block; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 999px; text-transform: uppercase; letter-spacing: .03em; }}
.status-pill-open {{ background: #eaf3ee; color: var(--green-money); }}
.status-pill-limited {{ background: #fdf3e7; color: var(--amber); }}
.status-pill-closed {{ background: #fdf2f0; color: var(--red-flag); }}

/* ---- leaderboard table ---- */
.section {{ padding: 48px 0; }}
.section-title {{ font-size: 28px; margin-bottom: 6px; }}
.section-sub {{ color: var(--ink-soft); margin-bottom: 24px; max-width: 700px; }}
.table-wrap {{ overflow-x: auto; border: 1px solid var(--rule); border-radius: 12px; background: #fff; }}
table.score-table {{ width: 100%; border-collapse: collapse; font-size: 14px; min-width: 640px; }}
.score-table thead th {{ text-align: left; background: var(--paper-warm); color: var(--teal-deep); font-weight: 700; padding: 12px 14px; border-bottom: 1px solid var(--rule); position: sticky; top: 0; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
.score-table td {{ padding: 10px 14px; border-bottom: 1px solid var(--rule); vertical-align: middle; }}
.score-table tbody tr:hover {{ background: var(--paper-warm); }}
.score-table tbody tr:last-child td {{ border-bottom: none; }}
.rank-cell {{ color: var(--sage); font-weight: 700; width: 48px; }}
.city-cell a {{ font-weight: 700; text-decoration: none; color: var(--teal-deep); }}
.city-cell a:hover {{ text-decoration: underline; }}
.region-tag {{ display: block; font-size: 11px; color: var(--sage); text-transform: uppercase; letter-spacing: .03em; }}
.pills-cell {{ min-width: 320px; }}

/* ---- category tabs ---- */
.cat-tabs {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 24px; }}
.cat-tab {{ padding: 10px 16px; border-radius: 999px; border: 1px solid var(--rule); background: #fff; font-family: 'Inter Tight', sans-serif; font-weight: 600; font-size: 13px; cursor: pointer; color: var(--ink); }}
.cat-tab.active {{ background: var(--teal-deep); color: #fff; border-color: var(--teal-deep); }}
.cat-panel {{ display: none; }}
.cat-panel.active {{ display: block; }}
.cat-panel h3 {{ font-size: 20px; margin-bottom: 14px; }}

.methodology {{ background: var(--paper-warm); padding: 48px 0; }}
.methodology .box {{ background: #fff; border: 1px solid var(--rule); border-radius: 12px; padding: 28px; }}
.methodology ul {{ margin: 12px 0 0; padding-left: 20px; }}
.methodology li {{ margin-bottom: 8px; }}

@media (max-width: 640px) {{
  .result-box {{ flex-direction: column; text-align: center; }}
  .pills-cell {{ min-width: 240px; }}
}}
</style>
</head>
<body>

<!-- ============================== NAV (canonical, from _partials/nav-footer.html) ============================== -->
<nav class="nav">
  <div class="nav-inner" style="display:flex; justify-content:space-between; align-items:center;">
    <a href="/" class="logo">
      <span class="logo-mark"></span>
      <span>Home<span class="logo-power">Power</span>Rebate</span>
    </a>
    <div style="display:flex; align-items:center; gap:16px;" class="nav-desktop-only">
      <a href="/installers" style="color:var(--ink-soft); font-weight:600; font-size:15px; text-decoration:none;">Find an Installer</a>
      <a href="/retrofit-assessment/" style="color:var(--ink-soft); font-weight:600; font-size:15px; text-decoration:none;">Assessment</a>
      <a href="/blog" style="color:var(--ink-soft); font-weight:600; font-size:15px; text-decoration:none;">Blog</a>
    </div>
    <div style="display:none; align-items:center; gap:12px;" class="nav-mobile-only">
      <a href="/installers" style="color:var(--ink-soft); font-weight:600; font-size:14px; text-decoration:none;">Installers</a>
      <a href="/retrofit-assessment/" style="color:var(--ink-soft); font-weight:600; font-size:14px; text-decoration:none;">Assessment</a>
    </div>
    <button onclick="toggleCityDropdown()" class="nav-pick" style="border:none; cursor:pointer;">
      Pick your city
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
    </button>
  </div>

  <div id="city-dropdown-modal" style="display:none; position:absolute; top:56px; right:20px; background:#fff; border:1px solid var(--rule); border-radius:12px; box-shadow:0 8px 24px rgba(10,42,46,0.12); z-index:49; max-width:300px; max-height:70vh; overflow-y:auto;">
    <div style="padding:16px 16px 0;">
      <div style="display:flex; gap:6px; margin-bottom:12px;">
        <button type="button" onclick="showProvinceCities('on')" id="province-tab-on" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:var(--teal-deep); color:#fff; font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Ontario</button>
        <button type="button" onclick="showProvinceCities('bc')" id="province-tab-bc" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">British Columbia</button>
        <button type="button" onclick="showProvinceCities('ca')" id="province-tab-ca" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">California (US)</button>
      </div>
      <div style="display:flex; gap:6px; margin-bottom:12px;">
        <button type="button" onclick="showProvinceCities('ab')" id="province-tab-ab" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Alberta</button>
        <button type="button" onclick="showProvinceCities('ns')" id="province-tab-ns" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Nova Scotia</button>
      </div>
      <div style="display:flex; gap:6px; margin-bottom:12px;">
        <button type="button" onclick="showProvinceCities('ma')" id="province-tab-ma" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Massachusetts</button>
        <button type="button" onclick="showProvinceCities('ny')" id="province-tab-ny" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">New York</button>
      </div>
    </div>
    <div style="padding:0 16px 16px;">
    <div id="province-cities-on" style="display:grid; gap:8px;">
      <a href="/ca/on/toronto">Toronto</a><a href="/ca/on/ottawa">Ottawa</a><a href="/ca/on/mississauga">Mississauga</a><a href="/ca/on/brampton">Brampton</a><a href="/ca/on/hamilton">Hamilton</a><a href="/ca/on/markham">Markham</a><a href="/ca/on/vaughan">Vaughan</a><a href="/ca/on/richmond-hill">Richmond Hill</a><a href="/ca/on/barrie">Barrie</a><a href="/ca/on/london">London</a><a href="/ca/on/kitchener">Kitchener</a><a href="/ca/on/windsor">Windsor</a><a href="/ca/on/oakville">Oakville</a><a href="/ca/on/oshawa">Oshawa</a><a href="/ca/on/whitby">Whitby</a><a href="/ca/on/burlington">Burlington</a><a href="/ca/on/cambridge">Cambridge</a><a href="/ca/on/greater-sudbury">Greater Sudbury</a>
    </div>
    <div id="province-cities-bc" style="display:none; gap:8px;">
      <a href="/ca/bc/abbotsford">Abbotsford</a><a href="/ca/bc/burnaby">Burnaby</a><a href="/ca/bc/chilliwack">Chilliwack</a><a href="/ca/bc/coquitlam">Coquitlam</a><a href="/ca/bc/fort-st-john">Fort St. John</a><a href="/ca/bc/kamloops">Kamloops</a><a href="/ca/bc/kelowna">Kelowna</a><a href="/ca/bc/langley">Langley</a><a href="/ca/bc/maple-ridge">Maple Ridge</a><a href="/ca/bc/nanaimo">Nanaimo</a><a href="/ca/bc/penticton">Penticton</a><a href="/ca/bc/prince-george">Prince George</a><a href="/ca/bc/richmond">Richmond</a><a href="/ca/bc/squamish">Squamish</a><a href="/ca/bc/surrey">Surrey</a><a href="/ca/bc/vancouver">Vancouver</a><a href="/ca/bc/vernon">Vernon</a><a href="/ca/bc/victoria">Victoria</a>
    </div>
    <div id="province-cities-ab" style="display:none; gap:8px;">
      <a href="/ca/ab/calgary">Calgary</a><a href="/ca/ab/edmonton">Edmonton</a><a href="/ca/ab/red-deer">Red Deer</a><a href="/ca/ab/lethbridge">Lethbridge</a><a href="/ca/ab/st-albert">St. Albert</a>
    </div>
    <div id="province-cities-ns" style="display:none; gap:8px;">
      <a href="/ca/ns/halifax">Halifax</a>
    </div>
    <div id="province-cities-ma" style="display:none; gap:8px;">
      <a href="/us/ma/boston">Boston</a><a href="/us/ma/worcester">Worcester</a><a href="/us/ma/springfield">Springfield</a><a href="/us/ma/cambridge">Cambridge</a><a href="/us/ma/lowell">Lowell</a><a href="/us/ma/brockton">Brockton</a><a href="/us/ma/new-bedford">New Bedford</a><a href="/us/ma/quincy">Quincy</a><a href="/us/ma/lynn">Lynn</a><a href="/us/ma/fall-river">Fall River</a><a href="/us/ma/newton">Newton</a><a href="/us/ma/somerville">Somerville</a>
    </div>
    <div id="province-cities-ca" style="display:none; gap:8px;">
      <a href="/us/ca/los-angeles/">Los Angeles</a><a href="/us/ca/sacramento/">Sacramento</a><a href="/us/ca/bay-area/">Bay Area</a><a href="/us/ca/san-diego/">San Diego</a><a href="/us/ca/inland-empire/">Inland Empire</a>
    </div>
    <div id="province-cities-ny" style="display:none; gap:8px;">
      <a href="/us/ny/con-edison/new-york-city/">New York City</a><a href="/us/ny/con-edison/yonkers/">Yonkers</a><a href="/us/ny/con-edison/mount-vernon/">Mount Vernon</a><a href="/us/ny/con-edison/new-rochelle/">New Rochelle</a><a href="/us/ny/con-edison/white-plains/">White Plains</a><a href="/us/ny/pseg/brookhaven/">Brookhaven</a><a href="/us/ny/pseg/islip/">Islip</a><a href="/us/ny/pseg/babylon/">Babylon</a><a href="/us/ny/pseg/huntington/">Huntington</a><a href="/us/ny/pseg/smithtown/">Smithtown</a><a href="/us/ny/pseg/oyster-bay/">Oyster Bay</a><a href="/us/ny/pseg/southampton/">Southampton</a><a href="/us/ny/central-hudson/poughkeepsie/">Poughkeepsie</a><a href="/us/ny/central-hudson/newburgh/">Newburgh</a><a href="/us/ny/central-hudson/kingston/">Kingston</a><a href="/us/ny/central-hudson/beacon/">Beacon</a><a href="/us/ny/central-hudson/saugerties/">Saugerties</a><a href="/us/ny/national-grid/albany/">Albany</a><a href="/us/ny/national-grid/buffalo/">Buffalo</a><a href="/us/ny/national-grid/rochester/">Rochester</a><a href="/us/ny/national-grid/syracuse/">Syracuse</a><a href="/us/ny/national-grid/yonkers/">Yonkers (National Grid)</a>
    </div>
    </div>
  </div>
</nav>
<!-- ============================== /NAV ============================== -->

<header class="hero">
  <div class="wrap">
    <div class="eyebrow">New &middot; PowerScore</div>
    <h1>See how your city's rebates stack up</h1>
    <p class="lead">We scored every city we cover &mdash; {total_cities} in all, across {total_regions} regions &mdash; on rebate dollar value, program status, and how many funding layers stack. Find your city below.</p>
    <div class="hero-stats">
      <div class="hero-stat"><div class="num">{total_cities}</div><div class="lbl">Cities Scored</div></div>
      <div class="hero-stat"><div class="num">8</div><div class="lbl">Categories</div></div>
      <div class="hero-stat"><div class="num">{total_regions}</div><div class="lbl">Regions</div></div>
      <div class="hero-stat"><div class="num">{TOP_CITY['label']}</div><div class="lbl">#1 Overall</div></div>
    </div>
  </div>
</header>

<section class="picker-section">
  <div class="wrap">
    <div class="picker-card">
      <h2>Find your city's PowerScore</h2>
      <div class="picker-row">
        <select id="city-select" aria-label="Choose your city">
          <option value="">Choose your city&hellip;</option>
          {city_options_html}
        </select>
        <button type="button" onclick="lookupCity()">Show my score</button>
      </div>
      <div class="result-box" id="result-box">
        <div class="gauge" id="result-gauge"><span class="gauge-num" id="result-num">0</span></div>
        <div class="result-text">
          <h3 id="result-title">&mdash;</h3>
          <p id="result-desc">&mdash;</p>
          <a class="cta" id="result-cta" href="#">See the full rebate guide &rarr;</a>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="section" style="background:#fff;">
  <div class="wrap">
    <h2 class="section-title" id="leaderboard">Full PowerScore leaderboard</h2>
    <p class="section-sub">Ranked by overall PowerScore &mdash; the average of all 8 category scores. Hover any pill to see the category. &#128293; heat pump &middot; &#9728;&#65039; solar &middot; &#128267; battery &middot; &#127777;&#65039; insulation &middot; &#128167; water heater &middot; thermostat &middot; &#128663; EV charger &middot; &#129003; windows/doors.</p>
    <div class="table-wrap">
      <table class="score-table" id="leaderboard-table">
        <thead><tr><th>Rank</th><th>City</th><th>PowerScore</th><th>Category breakdown</th></tr></thead>
        <tbody>
{overall_rows_html}
        </tbody>
      </table>
    </div>
  </div>
</section>

<section class="section" style="background: var(--paper-warm);">
  <div class="wrap">
    <h2 class="section-title" id="by-category">Best cities by category</h2>
    <p class="section-sub">Same scoring, one category at a time &mdash; the top 25 cities for each. Great for shopping around if you're flexible on where you'll do the work (or just bragging rights).</p>
    <div class="cat-tabs">
{cat_buttons_html}
    </div>
{cat_panels_html}
  </div>
</section>

<section class="methodology">
  <div class="wrap">
    <div class="box">
      <h2 style="margin-top:0; font-size:24px;">How PowerScore is calculated</h2>
      <p>Every city gets a score from 0&ndash;100 in each of 8 categories, built entirely from the rebate numbers already published on each city's page &mdash; nothing here is estimated or invented.</p>
      <ul>
        <li><strong>60% Dollar value</strong> &mdash; the top rebate amount available in that category, normalized against the highest amount found among cities in the same region (BC cities compare to BC's max, Ontario to Ontario's max, and so on &mdash; not across borders, since program structures differ completely between provinces, states, and countries).</li>
        <li><strong>25% Program status</strong> &mdash; Open programs get full credit, Funding Limited/Unclear programs get partial credit, and Closed or nonexistent programs get zero.</li>
        <li><strong>15% Stackability</strong> &mdash; how many distinct funding layers apply (federal, provincial/state, utility, municipal) &mdash; more layers that stack together score higher.</li>
      </ul>
      <p>A city's <strong>overall PowerScore</strong> is the plain average of its 8 category scores. We recalculate this whenever the underlying city pages are updated with new rebate figures.</p>
    </div>
  </div>
</section>

<!-- ============================ FOOTER ============================= -->
<section style="background: linear-gradient(135deg, rgba(13, 79, 92, 0.95), rgba(8, 54, 63, 0.98)); padding: 56px 24px; margin: 0;">
  <div class="wrap" style="text-align: center; color: #fff; max-width: 600px;">
    <div style="font-size: 13px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: rgba(212, 117, 28, 0.9); margin-bottom: 14px;">From Sam</div>
    <h2 style="font-family: 'Fraunces', Georgia, serif; font-size: 32px; line-height: 1.2; margin-bottom: 14px; color: #fff;">Get my weekly email</h2>
    <p style="font-size: 15px; color: rgba(250, 247, 242, 0.85); margin-bottom: 24px;">Every Friday: what I'm learning about rebates across every province and state we cover, heat pump reality checks, solar economics, and the installers I trust. Real stuff, no marketing.</p>
    <form id="newsletter-form" style="display: flex; flex-direction: column; gap: 10px;">
      <input type="email" id="newsletter-email" placeholder="your@email.com" required style="padding: 12px 14px; border: none; border-radius: 6px; font-family: 'Inter Tight', sans-serif; font-size: 14px; background: #fff; color: var(--ink);">
      <input type="hidden" id="newsletter-city" value="">
      <input type="hidden" id="newsletter-page" value="/powerscore/">
      <button type="submit" style="padding: 12px 24px; background: #d4751c; color: #fff; border: none; border-radius: 6px; font-weight: 600; font-size: 14px; cursor: pointer; font-family: 'Inter Tight', sans-serif;">Subscribe</button>
      <p style="font-size: 11px; color: rgba(250, 247, 242, 0.6); margin-top: 6px;">No spam, ever. Unsubscribe anytime.</p>
    </form>
    <div id="newsletter-response" style="display: none; margin-top: 12px; padding: 12px; background: rgba(45, 106, 79, 0.2); border-radius: 6px; border: 1px solid rgba(45, 106, 79, 0.4); font-size: 13px;"></div>
  </div>
</section>

<footer class="footer">
  <div class="footer-inner">
    <div class="footer-top">
      <div>
        <div class="footer-brand">Home<span class="logo-power">Power</span>Rebate</div>
        <p class="footer-tagline">Helping homeowners understand rebates and choose trusted installers. Real numbers. Your choice.</p>
      </div>
      <div>
        <div class="footer-col-title">Canada</div>
        <ul class="footer-col-links">
          <li><a href="/ca/">All Provinces</a></li>
          <li><a href="/ca/bc">British Columbia</a></li>
          <li><a href="/ca/on">Ontario</a></li>
          <li><a href="/ca/ab">Alberta</a></li>
          <li><a href="/ca/ns">Nova Scotia</a></li>
        </ul>
      </div>
      <div>
        <div class="footer-col-title">United States</div>
        <ul class="footer-col-links">
          <li><a href="/us/">All States</a></li>
          <li><a href="/us/ca">California</a></li>
          <li><a href="/us/ny">New York</a></li>
          <li><a href="/us/ma">Massachusetts</a></li>
        </ul>
      </div>
      <div>
        <div class="footer-col-title">Guides &amp; Tools</div>
        <ul class="footer-col-links">
          <li><a href="/powerscore/">PowerScore Rankings</a></li>
          <li><a href="/installers/">Find an Installer</a></li>
          <li><a href="/retrofit-assessment/">Retrofit Assessment</a></li>
          <li><a href="/share-your-cost/">Share Your Cost</a></li>
          <li><a href="/blog">Full Blog</a></li>
          <li><a href="/questions/">Rebate Questions</a></li>
          <li><a href="/ca/">Canada by Province</a></li>
          <li><a href="/us/">US by State</a></li>
        </ul>
      </div>
      <div>
        <div class="footer-col-title">Company</div>
        <ul class="footer-col-links">
          <li><a href="/about">About</a></li>
          <li><a href="/partners/">Partners</a></li>
          <li><a href="/privacy">Privacy</a></li>
          <li><a href="/terms">Terms</a></li>
          <li><a href="/contact">Contact</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <div>&copy; 2026 HomePowerRebate &middot; Independent guide. By <a href="/about" style="color:inherit;">Sam Menard</a>. <a href="https://www.facebook.com/profile.php?id=61592376033225" style="color:inherit; text-decoration:none;">Follow on Facebook</a></div>
      <div>Made in Canada 🇨🇦</div>
    </div>
  </div>
</footer>
<!-- =========================== /FOOTER ============================= -->

<script>
function toggleCityDropdown() {{
  const modal = document.getElementById('city-dropdown-modal');
  if (modal) modal.style.display = modal.style.display === 'none' ? 'block' : 'none';
}}
function showProvinceCities(prov) {{
  const regions = ['on', 'bc', 'ab', 'ns', 'ma', 'ca', 'ny'];
  regions.forEach(function(r) {{
    const panel = document.getElementById('province-cities-' + r);
    const tab = document.getElementById('province-tab-' + r);
    if (!panel || !tab) return;
    panel.style.display = (prov === r) ? 'grid' : 'none';
    tab.style.background = (prov === r) ? 'var(--teal-deep)' : '#fff';
    tab.style.color = (prov === r) ? '#fff' : 'var(--ink)';
  }});
}}
document.getElementById('newsletter-form')?.addEventListener('submit', async (e) => {{
  e.preventDefault();
  const email = document.getElementById('newsletter-email').value;
  const city = document.getElementById('newsletter-city').value;
  const page = document.getElementById('newsletter-page').value;
  const responseEl = document.getElementById('newsletter-response');
  const button = document.querySelector('#newsletter-form button');
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = 'Subscribing...';
  try {{
    const response = await fetch('https://leads.homepowerrebate.com/newsletter', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ email, city, page }})
    }});
    if (!response.ok) throw new Error('Subscription failed');
    responseEl.textContent = "You're in! Check your inbox for a welcome email.";
    responseEl.style.display = 'block';
    document.getElementById('newsletter-form').style.display = 'none';
  }} catch (error) {{
    responseEl.textContent = 'Something went wrong — please try again or email us directly.';
    responseEl.style.display = 'block';
    responseEl.style.background = 'rgba(163, 64, 47, 0.2)';
    responseEl.style.borderColor = 'rgba(163, 64, 47, 0.4)';
    button.disabled = false;
    button.textContent = originalText;
  }}
}});

/* ---- PowerScore page-specific JS ---- */
const POWERSCORE_ROWS = {json.dumps([{"key": r["region"] + "/" + r["slug"], "label": r["label"], "region": r["region_label"], "overall": r["overall"], "url": r["url"], "rank": i + 1} for i, r in enumerate(rows)])};
const POWERSCORE_TOTAL = {total_cities};

function bandWord(score) {{
  if (score >= 75) return 'excellent';
  if (score >= 50) return 'solid';
  if (score >= 25) return 'limited';
  return 'thin';
}}

function lookupCity() {{
  const sel = document.getElementById('city-select');
  const key = sel.value;
  if (!key) return;
  const item = POWERSCORE_ROWS.find(r => r.key === key);
  if (!item) return;
  const regionTotal = POWERSCORE_ROWS.filter(r => r.region === item.region).length;
  const regionRank = POWERSCORE_ROWS.filter(r => r.region === item.region).sort((a,b)=>b.overall-a.overall).findIndex(r => r.key === key) + 1;

  document.getElementById('result-box').classList.add('show');
  document.getElementById('result-num').textContent = Math.round(item.overall);
  document.getElementById('result-gauge').style.setProperty('--score-deg', (item.overall * 3.6) + 'deg');
  document.getElementById('result-title').textContent = item.label + ': ' + Math.round(item.overall) + ' / 100';
  document.getElementById('result-desc').textContent = item.label + ' ranks #' + regionRank + ' of ' + regionTotal + ' in ' + item.region + ' (#' + item.rank + ' of ' + POWERSCORE_TOTAL + ' overall) — ' + bandWord(item.overall) + ' rebate coverage.';
  document.getElementById('result-cta').href = item.url;

  const rowId = 'city-' + key.replace(/\\//g, '-');
  const row = document.getElementById(rowId);
  if (row) {{
    document.querySelectorAll('.score-table tbody tr').forEach(tr => tr.style.background = '');
    row.style.background = 'var(--paper-warm)';
  }}
}}

function showCategory(cat) {{
  document.querySelectorAll('.cat-tab').forEach(btn => btn.classList.toggle('active', btn.dataset.cat === cat));
  document.querySelectorAll('.cat-panel').forEach(panel => panel.classList.toggle('active', panel.id === 'panel-' + cat));
}}
</script>

</body>
</html>
'''

out_path = ROOT / "powerscore" / "index.html"
out_path.write_text(page)
print(f"Wrote {out_path} ({len(page):,} bytes)")
