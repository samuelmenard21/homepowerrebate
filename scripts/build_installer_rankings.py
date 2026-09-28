#!/usr/bin/env python3
"""
Build "Top-rated <service> installers in <city>" ranking pages from the
installer CSVs (installers/*-installers-real.csv), one per city x service
with at least MIN_INSTALLERS rated companies.

  /installers/<region>/<city-slug>/<heat-pump|solar>/index.html

Ranking is a review-weighted (Bayesian) Google rating so a 4.9 from 500
reviews beats a 5.0 from 3. Pages are regenerated wholesale on each run —
edit this script, not the output. Also writes installers/rankings.json
(the index used by the installers hub and city pages).

Run from the Powerrebate root:
  python3 scripts/build_installer_rankings.py --dry-run
  python3 scripts/build_installer_rankings.py
"""
import argparse
import csv
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402

BASE = "https://homepowerrebate.com"
MIN_INSTALLERS = 3
PRIOR_REVIEWS = 25   # Bayesian weight
PRIOR_RATING = 4.5
MODIFIED = date.today().isoformat()

REGIONS = {
    # code: (country dir, region dir, short label, long name)
    "bc": ("ca", "bc", "BC", "British Columbia"),
    "on": ("ca", "on", "ON", "Ontario"),
    "ab": ("ca", "ab", "AB", "Alberta"),
    "ns": ("ca", "ns", "NS", "Nova Scotia"),
    "ma": ("us", "ma", "MA", "Massachusetts"),
    "ny": ("us", "ny", "NY", "New York"),
    "ca": ("us", "ca", "CA", "California"),
    "pa": ("us", "pa", "PA", "Pennsylvania"),
    "co": ("us", "co", "CO", "Colorado"),
    "vt": ("us", "vt", "VT", "Vermont"),
}
SERVICES = {
    "heat-pump": {"name": "Heat Pump", "lower": "heat pump", "rebate_cat": "heat-pump"},
    "solar": {"name": "Solar", "lower": "solar", "rebate_cat": "solar"},
}


def slugify(s):
    s = s.lower().replace("&", "and").replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def load_rows():
    rows = []
    for f in sorted((ROOT / "installers").glob("*-installers-real.csv")):
        m = re.match(r"(?:([a-z]{2})-)?(heat-pump|solar)-installers-real\.csv$", f.name)
        if not m:
            continue
        region, service = (m.group(1) or "bc"), m.group(2)
        for r in csv.DictReader(f.open(encoding="utf-8")):
            try:
                rating, reviews = float(r["Google Rating"]), int(float(r["Review Count"]))
            except (ValueError, KeyError):
                continue
            rows.append({
                "region": region, "service": service, "city": r["City"].strip(),
                "name": r["Business Name"].strip(), "phone": r.get("Phone", "").strip(),
                "website": r.get("Website", "").strip(), "email": r.get("Email", "").strip(), "gmaps": r.get("Google Maps URL", "").strip(),
                "rating": rating, "reviews": reviews, "address": re.sub(r",\s*(Canada|United States|USA)$", "", r.get("Address", "").strip()),
                "updated": r.get("Last Updated", "").strip(),
            })
    return rows


def city_hubs():
    """(region_code, lower label) -> {'label', 'url', 'slug'} from powerscore-data.json."""
    data = json.loads((ROOT / "powerscore-data.json").read_text())
    out = {}
    for key, reg in data["regions"].items():
        code = next((c for c, v in REGIONS.items() if f"{v[0]}/{v[1]}" == key), None)
        if not code:
            continue
        for slug, city in reg["cities"].items():
            hub = {"label": city["label"], "url": city["url"], "slug": slug.rstrip("/").split("/")[-1]}
            out[(code, city["label"].lower())] = hub
            out[(code, hub["slug"])] = hub
    return out


def find_hub(hubs, region, city):
    return hubs.get((region, city.lower())) or hubs.get((region, slugify(city)))


def profile_url(region, city, name):
    city_slug, name_slug = slugify(city), slugify(name)
    for rel in (f"installers/profiles/{city_slug}/{name_slug}",
                f"installers/profiles/{region}/{city_slug}/{name_slug}"):
        if (ROOT / rel / "index.html").exists():
            return "/" + rel + "/"
    return ""


def score(r):
    v = r["reviews"]
    return (v / (v + PRIOR_REVIEWS)) * r["rating"] + (PRIOR_REVIEWS / (v + PRIOR_REVIEWS)) * PRIOR_RATING


def esc(s):
    return html.escape(s, quote=True)


CSS = """
:root{--ink:#0a2a2e;--ink-soft:#1a3d42;--paper:#faf7f2;--paper-warm:#f5efe5;--teal:#0d4f5c;--teal-deep:#08363f;--amber:#d4751c;--amber-bright:#e88a2e;--sage:#6b8e7f;--green-money:#2d6a4f;--rule:#d9d0c1;}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter Tight',-apple-system,BlinkMacSystemFont,sans-serif;color:var(--ink);background:var(--paper);line-height:1.6;-webkit-font-smoothing:antialiased}
h1,h2,h3{font-family:'Fraunces',Georgia,serif;font-weight:500;line-height:1.2;letter-spacing:-.01em}
.wrap{max-width:860px;margin:0 auto;padding:0 20px}
.hero{background:var(--teal-deep);color:var(--paper);padding:44px 0 36px}
.hero h1{font-size:clamp(27px,5vw,40px);color:#fff;margin-bottom:12px}
.hero p{color:rgba(250,247,242,.82);font-size:16.5px}
.hero .meta{font-size:13px;color:rgba(250,247,242,.6);margin-top:10px}
section.body{padding:32px 0 56px}
section.body h2{font-size:25px;margin:34px 0 12px}
section.body p,section.body li{font-size:16px;color:var(--ink-soft)}
section.body p{margin-bottom:14px}
section.body ul,section.body ol{margin:0 0 16px 22px}
section.body li{margin-bottom:7px}
section.body a{color:var(--teal-deep);font-weight:600;text-decoration:underline;text-decoration-color:var(--amber);text-underline-offset:2px}
.callout{background:var(--paper-warm);border:1px solid var(--rule);border-left:4px solid var(--green-money);border-radius:8px;padding:16px 18px;margin:4px 0 22px}
.callout p{margin:0}
.rank-list{list-style:none;margin:0 0 10px!important;padding:0}
.rank{background:#fff;border:1px solid var(--rule);border-radius:12px;padding:14px 16px;margin-bottom:10px!important;display:grid;grid-template-columns:34px 1fr;gap:4px 12px}
.rank .n{grid-row:span 2;font-family:'Fraunces',Georgia,serif;font-size:22px;color:var(--amber);font-weight:700}
.rank .nm{font-weight:700;color:var(--ink);font-size:16.5px}
.rank .nm a{color:var(--ink);text-decoration:none}
.rank .st{font-size:14px;color:var(--ink-soft)}
.rank .st b{color:var(--ink)}
.rank .act{grid-column:2;font-size:13.5px;display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:4px}
.badge{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;background:var(--green-money);color:#fff;border-radius:999px;padding:2px 8px;margin-left:6px;vertical-align:2px}
.small{font-size:13.5px!important;color:var(--sage)!important}
.cta{background:var(--amber);color:#fff;border-radius:14px;padding:26px 22px;text-align:center;margin-top:36px}
.cta h3{color:#fff;font-size:21px;margin-bottom:8px}
.cta p{color:rgba(255,255,255,.92)!important;margin-bottom:14px}
.cta a{display:inline-block;background:var(--ink);color:#fff!important;text-decoration:none!important;padding:12px 24px;border-radius:999px;font-weight:700}
.hpr-breadcrumb{max-width:1180px;margin:0 auto;padding:14px 28px;font-size:13px;color:var(--ink-soft)}
.hpr-breadcrumb ol{list-style:none;display:flex;flex-wrap:wrap;margin:0;padding:0}
.hpr-breadcrumb li{display:flex;align-items:center}
.hpr-breadcrumb li:not(:last-child)::after{content:'/';margin:0 8px;color:var(--rule)}
.hpr-breadcrumb a{color:var(--ink-soft);text-decoration:none}
.hpr-breadcrumb li[aria-current="page"]{color:var(--ink);font-weight:600}
@media (max-width:600px){.hpr-breadcrumb{padding:10px 20px;font-size:12px}}
"""


CLIMATE = json.loads((ROOT / "city-climate-data.json").read_text())
SOLAR = json.loads((ROOT / "city-solar-data.json").read_text())


def city_data(table, region, city_label):
    return table.get(f"{region}|{city_label.lower()}") or table.get(f"{region}|{city_label.lower().replace('.', '')}")


def pct_rank(values, v, higher_is_better=True):
    """Share of tracked cities this one beats."""
    vals = [x for x in values if x is not None]
    beat = sum(1 for x in vals if (v > x if higher_is_better else v < x))
    return round(100 * beat / max(len(vals) - 1, 1))


def temp(c, us):
    return f"{c:.0f}°C ({c * 9 / 5 + 32:.0f}°F)" if us else f"{c:.0f}°C"


def climate_section(region, service, city_label):
    us = REGIONS[region][0] == "us"
    if service == "heat-pump":
        d = city_data(CLIMATE, region, city_label)
        if not d or d.get("avg_january_low_c") is None:
            return ""
        low, cold = d["avg_january_low_c"], d.get("coldest_recorded_c")
        warmer = pct_rank([v.get("avg_january_low_c") for v in CLIMATE.values()], low, higher_is_better=True)
        if cold is not None and cold <= -30:
            advice = ("That's true cold-climate territory. Ask for models rated to keep heating near your coldest temperatures, "
                      "compare each model's heating output at -25°C, and plan for backup heat on the worst nights.")
        elif cold is not None and cold <= -20:
            advice = ("Choose a cold-climate model, and compare heating output at -20°C, not just at mild temperatures. "
                      "Keeping some backup heat for rare deep-cold snaps is common and sensible.")
        else:
            advice = ("Winters here are mild enough that most cold-climate heat pumps can heat your whole home. "
                      "Sizing and installation quality matter more than squeezing out extra cold-weather rating.")
        cold_txt = f", and the coldest temperature recorded from {d.get('sample_years','2015-2024')} was <b>{temp(cold, us)}</b>" if cold is not None else ""
        return (f"<h2>What {esc(city_label)}'s winter means for your heat pump</h2>"
                f"<p>In {esc(city_label)}, the average January low is <b>{temp(low, us)}</b>{cold_txt}. "
                f"That's milder than {warmer}% of the 123 cities we track. {advice}</p>"
                f'<p class="small">Source: Open-Meteo historical weather data, {d.get("sample_years","2015-2024")}.</p>')
    d = city_data(SOLAR, region, city_label)
    if not d or not d.get("approx_peak_sun_hours"):
        return ""
    psh = d["approx_peak_sun_hours"]
    kwh = round(psh * 365 * 0.8 / 10) * 10
    sunnier = pct_rank([v.get("approx_peak_sun_hours") for v in SOLAR.values()], psh, higher_is_better=True)
    return (f"<h2>How much sun does {esc(city_label)} get?</h2>"
            f"<p>{esc(city_label)} averages about <b>{psh:.1f} peak sun hours a day</b>, more than {sunnier}% of the 123 cities we track. "
            f"As a rough guide, each kilowatt of panels here makes about <b>{kwh:,} kWh a year</b> (after typical system losses). "
            f"A good installer will give you a roof-specific estimate that accounts for shading and roof angle.</p>"
            f'<p class="small">Source: Open-Meteo historical solar radiation, {d.get("sample_years","2020-2024")}. Production estimate assumes 80% system efficiency.</p>')


def hire_tips(region, service):
    tips = []
    if service == "heat-pump":
        tips += [
            "Ask for a room-by-room heat loss calculation. A quote that guesses the size from square footage alone is a red flag.",
            "Ask for the exact model and its heating output at your area's coldest temperature, not just the brand.",
            "Ask who handles the rebate paperwork and whether the model is on your rebate program's eligible list.",
        ]
        if region == "bc":
            tips.append("For BC Hydro and CleanBC rebates, the installer must be registered with the Home Performance Contractor Network (HPCN) or the program. Ask before you sign.")
    else:
        tips += [
            "Ask for a production estimate for your roof (kWh per year) and how shading was measured.",
            "Ask which panels and inverter they use, and who backs the warranty if the company closes.",
            "Ask how your utility credits extra power you send to the grid, and whether a battery makes sense for you.",
        ]
    return tips


def build_page(region, service, city_label, hub, installers, other_service_url):
    c_dir, r_dir, short, long_name = REGIONS[region]
    svc = SERVICES[service]
    city_slug = hub["slug"] if hub else slugify(city_label)
    path = f"/installers/{region}/{city_slug}/{service}/"
    url = BASE + path
    ranked = sorted(installers, key=score, reverse=True)
    n = len(ranked)
    total_reviews = sum(r["reviews"] for r in ranked)
    avg = sum(r["rating"] * r["reviews"] for r in ranked) / max(total_reviews, 1)
    top3 = ranked[:3]
    most_reviewed = max(ranked, key=lambda r: r["reviews"])
    updated = max((r["updated"] for r in ranked if r["updated"]), default=MODIFIED)
    upd_h = date.fromisoformat(updated).strftime("%B %Y") if re.match(r"\d{4}-\d\d-\d\d$", updated) else updated

    title = f"Best {svc['name']} Installers in {city_label}, {short} (2026)"
    desc = (f"The top-rated {svc['lower']} installers in {city_label}, {short}, ranked by "
            f"{total_reviews:,} Google reviews. Compare {n} local companies, plus what to ask before you hire.")
    top_line = ", ".join(f"{r['name']} ({r['rating']:.1f}★, {r['reviews']:,} reviews)" for r in top3)

    items = []
    for i, r in enumerate(ranked, 1):
        prof = profile_url(region, r["city"], r["name"])
        name_html = f'<a href="{prof}">{esc(r["name"])}</a>' if prof else esc(r["name"])
        badge = '<span class="badge">Top pick</span>' if i <= 3 else ""
        acts = []
        if r["phone"]:
            tel = re.sub(r"[^\d+]", "", r["phone"])
            acts.append(f'<a href="tel:{tel}">Call {esc(r["phone"])}</a>')
        if r["website"]:
            acts.append(f'<a href="{esc(r["website"])}" rel="nofollow noopener" target="_blank">Website</a>')
        if r["gmaps"]:
            acts.append(f'<a href="{esc(r["gmaps"])}" rel="nofollow noopener" target="_blank">Google reviews</a>')
        if prof:
            acts.append(f'<a href="{prof}">Profile</a>')
        items.append(
            f'<li class="rank"><div class="n">{i}</div><div class="nm">{name_html}{badge}</div>'
            f'<div class="st"><b>{r["rating"]:.1f}★</b> from <b>{r["reviews"]:,}</b> Google reviews'
            + (f'<br>{esc(r["address"])}' if r["address"] else "") + '</div>'
            f'<div class="act">{" · ".join(acts)}</div></li>')

    city_hub_url = hub["url"] if hub else ""
    rebate_url = (city_hub_url + svc["rebate_cat"] + "/") if city_hub_url and (ROOT / (city_hub_url.strip("/") + "/" + svc["rebate_cat"]) / "index.html").exists() else city_hub_url
    rebate_line = (f'<p>Before you call anyone, check <a href="{rebate_url}">what {svc["lower"]} rebates you can get in {esc(city_label)}</a>. '
                   f'Many programs require approval or a registered contractor <em>before</em> work starts.</p>') if rebate_url else ""
    other_line = (f'<p>Also comparing {"solar" if service == "heat-pump" else "heat pumps"}? See the '
                  f'<a href="{other_service_url}">top-rated {"solar" if service == "heat-pump" else "heat pump"} installers in {esc(city_label)}</a>.</p>') if other_service_url else ""

    vet_line = ('<p>Full checklist: <a href="/guides/installer-vetting-checklist/">how to vet an HPCN installer in BC</a>.</p>'
                if region == "bc" and service == "heat-pump" else "")
    faqs = [
        (f"Who is the best {svc['lower']} installer in {city_label}?",
         f"Based on Google reviews, the top-rated {svc['lower']} installers in {city_label} are {top_line}. "
         f"We rank by a review-weighted score, so companies with many strong reviews rank above those with only a few."),
    ]

    crumbs = [("Home", "/"), ("Installers", "/installers/")]
    if city_hub_url:
        crumbs.append((city_label, city_hub_url))
    crumbs.append((f"{svc['name']} installers", None))
    crumb_html = "".join(
        f'<li><a href="{u}">{esc(t)}</a></li>' if u else f'<li aria-current="page">{esc(t)}</li>' for t, u in crumbs)

    ld = [
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i, "name": t, **({"item": BASE + u} if u else {})}
            for i, (t, u) in enumerate(crumbs, 1)]},
        {"@context": "https://schema.org", "@type": "ItemList", "name": title, "numberOfItems": n,
         "itemListElement": [
             {"@type": "ListItem", "position": i, "name": r["name"],
              **({"url": BASE + profile_url(region, r["city"], r["name"])} if profile_url(region, r["city"], r["name"]) else {})}
             for i, r in enumerate(ranked, 1)]},
    ]
    ld_html = "\n".join(f'<script type="application/ld+json">\n{json.dumps(o, ensure_ascii=False, indent=1)}\n</script>' for o in ld)

    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol>{crumb_html}</ol></nav>
<header class="hero"><div class="wrap">
<h1>Top-Rated {svc['name']} Installers in {esc(city_label)}, {short}</h1>
<p>{n} local companies ranked by {total_reviews:,} Google reviews. Free to compare, no sign-up.</p>
<p class="meta">Ratings collected {upd_h} · Page updated {date.fromisoformat(MODIFIED).strftime('%B %-d, %Y')}</p>
</div></header>
<section class="body"><div class="wrap">
<div class="callout"><p><strong>Short answer:</strong> The top-rated {svc['lower']} installers in {esc(city_label)} are {esc(top_line)}.</p></div>

<h2>{svc['name']} installers in {esc(city_label)}, ranked</h2>
<ol class="rank-list">
{chr(10).join(items)}
</ol>
<p class="small">Together these {n} companies average {avg:.1f}★ across {total_reviews:,} reviews. {esc(most_reviewed['name'])} has the most reviews ({most_reviewed['reviews']:,}).</p>

<p class="small">Ranked by Google rating weighted by review count, collected {upd_h}. Rankings are never paid for. <a href="/installers/how-we-rank/">How we rank and how we make money</a>.</p>
<p class="small"><b>Listed here?</b> <a href="/installers/badge/">Get your free top-rated badge</a> for your website.</p>

{climate_section(region, service, city_label)}

<h2>Before you hire a {svc['lower']} installer</h2>
<ol>
{chr(10).join('<li>' + esc(t) + '</li>' for t in hire_tips(region, service))}
</ol>
{vet_line}
{rebate_line}
{other_line}

<div class="cta"><h3>See every rebate in {esc(city_label)}</h3>
<p>Compare top-rated local installers, ranked by Google reviews, and see the rebates you can stack. Free for homeowners.</p>
<a href="{rebate_url or '/#city-picker'}">See {esc(city_label)} rebates →</a></div>
</div></section>"""

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-W33G4TGRHD');</script>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/og-image.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
{ld_html}
</head>
<body>
{navfooter.render_nav(region, city_slug)}
{body}
{navfooter.render_footer(region, city_slug, city_label, path)}
</body>
</html>
"""
    page = navfooter.ensure_shared_assets(page)
    return path, page, {"region": region, "service": service, "city": city_label, "url": path,
                        "count": n, "reviews": total_reviews, "top": [r["name"] for r in top3]}


def body_text(html_out, city_label):
    a = html_out.find('<section class="body">')
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_out[a:html_out.find("</section>", a)]))
    return re.sub(re.escape(city_label), "CITY", t, flags=re.I)


def near_duplicates(pages, limit=0.90):
    """Paths whose body is >= limit similar to a sibling (same region+service).
    The page with fewer installers in each offending pair is the one held back."""
    import difflib
    import itertools
    flagged = set()
    groups = {}
    for p in pages:
        groups.setdefault((p["region"], p["service"]), []).append(p)
    for sibs in groups.values():
        for a, b in itertools.combinations(sibs, 2):
            if difflib.SequenceMatcher(None, a["text"], b["text"], autojunk=False).ratio() >= limit:
                flagged.add((a if a["count"] < b["count"] else b)["url"])
    return flagged


def method_page():
    path = "/installers/how-we-rank/"
    body = """<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/installers/">Installers</a></li><li aria-current="page">How we rank</li></ol></nav>
<header class="hero"><div class="wrap"><h1>How We Rank Installers</h1>
<p>Our installer rankings come from public Google reviews, weighted so that lots of good reviews count more than a few. Here's exactly how, and how we make money.</p></div></header>
<section class="body"><div class="wrap">
<h2>The formula</h2>
<p>For each company we take its Google rating and its number of reviews, then calculate a review-weighted score (a Bayesian average):</p>
<p><b>score = (reviews ÷ (reviews + 25)) × rating + (25 ÷ (reviews + 25)) × 4.5</b></p>
<p>In plain words: every company starts near an average of 4.5 stars. The more reviews it has, the more its real rating counts. A 4.9 from 400 reviews scores higher than a 5.0 from 3, because 400 happy customers is stronger proof than 3.</p>
<h2>Where the data comes from</h2>
<ul><li>Google Business Profile ratings and review counts for installers that serve each city.</li>
<li>Each ranking page shows the month the ratings were collected. Ratings change, so always read recent reviews yourself, including the negative ones.</li>
<li>We only publish a city ranking when at least three rated companies serve it.</li></ul>
<h2>How we make money</h2>
<p>HomePowerRebate is free for homeowners. Some installers pay us a referral fee when a homeowner hires them through our site. <b>That fee never changes where a company ranks.</b> Companies can't pay to be listed higher or to remove bad reviews.</p>
<h2>What rankings can't tell you</h2>
<p>Reviews measure customer happiness, not technical skill. Before you hire, get two or more written quotes, ask how the system was sized, confirm licence and insurance, and ask who handles the rebate paperwork.</p>
<p><a href="/installers/">Browse installers by city →</a></p>
</div></section>"""
    title = "How We Rank Installers | HomePowerRebate"
    desc = "How HomePowerRebate ranks local heat pump and solar installers using review-weighted Google ratings, and how we make money."
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-W33G4TGRHD');</script>
<meta name="description" content="{desc}"><meta name="robots" content="index, follow"><link rel="canonical" href="{BASE}{path}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
{navfooter.render_nav("on", "")}
{body}
{navfooter.render_footer("on", "", "", path)}
</body></html>
"""
    return path, navfooter.ensure_shared_assets(page)


HUB_START, HUB_END = "<!-- RANKINGS-INDEX-START -->", "<!-- RANKINGS-INDEX-END -->"


def update_installers_hub(index):
    hub_path = ROOT / "installers" / "index.html"
    s = hub_path.read_text(encoding="utf-8")
    by_region = {}
    for m in index:
        if m.get("indexed"):
            by_region.setdefault(m["region"], {}).setdefault(m["city"], {})[m["service"]] = m["url"]
    blocks = []
    for code, (_, _, _, long_name) in REGIONS.items():
        cities = by_region.get(code)
        if not cities:
            continue
        rows = []
        for city in sorted(cities):
            links = " · ".join(f'<a href="{cities[city][sv]}">{SERVICES[sv]["name"]}</a>'
                               for sv in ("heat-pump", "solar") if sv in cities[city])
            rows.append(f'<li><strong>{esc(city)}</strong>: {links}</li>')
        blocks.append(f'<details style="margin-bottom:10px;"><summary style="cursor:pointer;font-weight:700;font-size:17px;">{long_name} ({len(cities)} cities)</summary>'
                      f'<ul style="columns:2 220px;margin:12px 0 0 18px;font-size:15px;line-height:1.9;">{"".join(rows)}</ul></details>')
    section = (f'{HUB_START}\n<section class="section" id="top-rated-by-city"><div class="wrap">'
               '<h2>Top-Rated Installers by City</h2>'
               '<p>Each city page ranks local heat pump and solar companies by Google reviews, weighted so lots of good reviews count more than a few. '
               '<a href="/installers/how-we-rank/">How we rank</a>.</p>'
               + "".join(blocks) + f'</div></section>\n{HUB_END}')
    if HUB_START in s:
        s = re.sub(re.escape(HUB_START) + r".*?" + re.escape(HUB_END), lambda m: section, s, count=1, flags=re.S)
    else:
        anchor = '<section class="section" id="full-directory"'
        assert anchor in s, "installers hub anchor missing"
        s = s.replace(anchor, section + "\n\n" + anchor, 1)
    hub_path.write_text(s, encoding="utf-8")


LINK_START, LINK_END = "<!-- RANKINGS-LINK-START -->", "<!-- RANKINGS-LINK-END -->"
CAROUSEL_RE = re.compile(r'<section class="unified-carousel-section".*?</section>', re.S)


def rankings_block(city, entries):
    """Small card linking a city page to its ranked installer lists."""
    items = []
    for sv in ("heat-pump", "solar"):
        e = entries.get(sv)
        if not e:
            continue
        top = ", ".join(esc(n) for n in e["top"][:3])
        items.append(
            f'<a href="{e["url"]}" style="flex:1;min-width:240px;background:#fff;border:1px solid #d9d0c1;border-radius:10px;'
            f'padding:18px 20px;text-decoration:none;color:#0a2a2e;display:block;">'
            f'<strong style="font-size:17px;">Top-rated {SERVICES[sv]["name"].lower()} installers in {esc(city)} &rarr;</strong>'
            f'<span style="display:block;font-size:14px;color:#1a3d42;margin-top:6px;">{e["count"]} local companies ranked by '
            f'{e["reviews"]:,} Google reviews. Top picks: {top}.</span></a>')
    return (f'{LINK_START}\n<section style="max-width:1100px;margin:0 auto 48px;padding:0 28px;" id="top-rated-installers">'
            f'<h2 style="font-family:\'Fraunces\',Georgia,serif;font-size:26px;margin-bottom:8px;">Compare top-rated installers in {esc(city)}</h2>'
            f'<p style="font-size:15px;color:#1a3d42;margin-bottom:16px;">Free for homeowners. We rank local companies by their Google reviews, '
            f'weighted so many good reviews beat a handful. <a href="/installers/how-we-rank/">How we rank</a>.</p>'
            f'<div style="display:flex;gap:14px;flex-wrap:wrap;">{"".join(items)}</div></section>\n{LINK_END}')


def inject_block(s, block, anchor_re=None):
    if LINK_START in s:
        return re.sub(re.escape(LINK_START) + r".*?" + re.escape(LINK_END), lambda m: block, s, count=1, flags=re.S)
    m = anchor_re.search(s) if anchor_re else None
    if m:
        return s[:m.end()] + "\n" + block + s[m.end():]
    i = s.find('<footer')
    return s[:i] + block + "\n" + s[i:] if i >= 0 else s


def link_city_pages(index, hubs):
    """Link each city hub and its heat-pump/solar pages to the matching ranking pages."""
    by_hub = {}
    for e in index:
        hub = find_hub(hubs, e["region"], e["city"])
        if hub:
            by_hub.setdefault(hub["url"], (hub["label"], {}))[1][e["service"]] = e
    changed = 0
    for hub_url, (city, entries) in by_hub.items():
        targets = [(hub_url, entries, CAROUSEL_RE)]
        targets += [(f"{hub_url}{sv}/", {sv: e}, None) for sv, e in entries.items()]
        for url, ents, anchor in targets:
            f = ROOT / url.strip("/") / "index.html"
            if not f.exists():
                continue
            s = f.read_text(encoding="utf-8")
            new = inject_block(s, rankings_block(city, ents), anchor)
            if len(ents) == 1:
                sv, e = next(iter(ents.items()))
                new = re.sub(r'href="/installers/">(See all [^<]*installers)', rf'href="{e["url"]}">\1', new)
            if new != s:
                f.write_text(new, encoding="utf-8")
                changed += 1
    return changed


def badge_svg(city, service):
    """City-specific 'Top-rated' badge (design A: seal with house medallion + five stars).
    Pure SVG with system font stacks, because web fonts don't load inside an <img>."""
    label = f"TOP-RATED {SERVICES[service]['name'].upper()} INSTALLER"
    c = esc(city)
    size = 40 if len(city) <= 11 else 34 if len(city) <= 14 else 28 if len(city) <= 18 else 23
    star = "M12 2l3 6.3 6.9 1-5 4.8 1.2 6.9L12 17.8 5.9 21l1.2-6.9-5-4.8 6.9-1z"
    stars = "".join(f'<path transform="translate({172 + i * 20} 118) scale(0.72)" d="{star}" fill="#e88a2e"/>' for i in range(5))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="480" height="192" viewBox="0 0 480 192" role="img" aria-label="Top-rated {SERVICES[service]['name'].lower()} installer in {c}, ranked by Google reviews - homepowerrebate.com">
<rect width="480" height="192" rx="20" fill="#08363f"/>
<circle cx="92" cy="96" r="60" fill="#d4751c"/>
<circle cx="92" cy="96" r="51" fill="none" stroke="#faf7f2" stroke-width="1.5" stroke-dasharray="2 4"/>
<path d="M92 62L62 87h8v30h16V100h12v17h16V87h8z" fill="#faf7f2" stroke="#faf7f2" stroke-width="3" stroke-linejoin="round"/>
<rect x="102" y="68" width="7" height="12" fill="#faf7f2"/>
<text x="92" y="138" text-anchor="middle" font-family="Helvetica,Arial,sans-serif" font-size="11" font-weight="700" letter-spacing="2" fill="#faf7f2">{date.today().year}</text>
<text x="172" y="58" font-family="Helvetica,Arial,sans-serif" font-size="12.5" font-weight="700" letter-spacing="1.6" fill="#e88a2e">{label}</text>
<text x="172" y="100" font-family="Georgia,'Times New Roman',serif" font-size="{size}" font-weight="700" fill="#faf7f2">{c}</text>
{stars}
<text x="276" y="131" font-family="Helvetica,Arial,sans-serif" font-size="13" fill="#faf7f2" fill-opacity="0.8">Ranked by Google reviews</text>
<text x="172" y="160" font-family="Helvetica,Arial,sans-serif" font-size="15" font-weight="700" fill="#faf7f2">homepowerrebate.com</text>
</svg>
"""


def badge_page(index):
    path = "/installers/badge/"
    opts = sorted((m for m in index if m.get("indexed")), key=lambda m: (m["region"], m["city"], m["service"]))
    data = json.dumps([{"u": m["url"], "c": m["city"], "s": SERVICES[m["service"]]["name"].lower(), "t": m["top"]} for m in opts], ensure_ascii=False)
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/installers/">Installers</a></li><li aria-current="page">Badge</li></ol></nav>
<header class="hero"><div class="wrap"><h1>Your Top-Rated Installer Badge</h1>
<p>If your company appears on one of our city rankings, you've earned it from your Google reviews. Show it on your website, free.</p></div></header>
<section class="body"><div class="wrap">
<h2>Get your badge</h2>
<p><label for="bdg-pick"><b>Pick your ranking page</b></label><br><select id="bdg-pick" style="width:100%;max-width:480px;padding:10px;font:inherit;font-size:16px;"></select></p>
<p id="bdg-who" class="small"></p>
<p id="bdg-prev"></p>
<p><label for="bdg-code"><b>Copy this code into your website</b></label></p>
<textarea id="bdg-code" readonly rows="4" style="width:100%;font-family:monospace;font-size:13px;padding:10px;"></textarea>
<p><button type="button" id="bdg-copy" style="background:#d4751c;color:#fff;border:0;border-radius:8px;padding:12px 20px;font:inherit;font-weight:700;cursor:pointer;">Copy code</button></p>
<h2>The rules</h2>
<ul><li>Only companies listed on the ranking page can use its badge.</li>
<li>Rankings come from Google reviews and are updated regularly. If you drop off a ranking, please remove the badge.</li>
<li>The badge is free. You don't need to show it to be ranked, and showing it doesn't change your rank. <a href="/installers/how-we-rank/">How we rank</a>.</li>
<li>Questions or a correction? Email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a>.</li></ul>
</div></section>
<script>
const B={data};
const sel=document.getElementById('bdg-pick');
B.forEach((b,i)=>{{const o=document.createElement('option');o.value=i;o.textContent=b.c+' \u2014 '+b.s;sel.appendChild(o);}});
function show(){{const b=B[sel.value],url='{BASE}'+b.u;
const code='<a href="'+url+'" title="Top-rated '+b.s+' installer in '+b.c+'"><img src="'+url+'badge.svg" width="320" height="128" alt="Top-rated '+b.s+' installer in '+b.c+' on HomePowerRebate"></a>';
document.getElementById('bdg-code').value=code;
document.getElementById('bdg-prev').innerHTML='<img src="'+b.u+'badge.svg" width="320" height="128" alt="Badge preview">';
document.getElementById('bdg-who').textContent='Listed on this page: '+b.t.join(', ')+(b.t.length>=3?' and others':'')+'.';}}
sel.addEventListener('change',show);
document.getElementById('bdg-copy').addEventListener('click',()=>{{const t=document.getElementById('bdg-code');t.select();navigator.clipboard&&navigator.clipboard.writeText(t.value);}});
show();
</script>"""
    title = "Top-Rated Installer Badge | HomePowerRebate"
    desc = "Listed on a HomePowerRebate city ranking? Add your free top-rated installer badge to your website."
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}"><meta name="robots" content="noindex, follow"><link rel="canonical" href="{BASE}{path}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
{navfooter.render_nav("on", "")}
{body}
{navfooter.render_footer("on", "", "", path)}
</body></html>
"""
    return path, navfooter.ensure_shared_assets(page)


def outreach_list(index, rows):
    """Mail-merge CSV: each listed installer with a public email -> its ranking page and badge code."""
    by_page = {(m["region"], m["service"], m["city"]): m for m in index if m.get("indexed")}
    out = [["business", "email", "city", "service", "ranking_url", "badge_page", "rating", "reviews"]]
    seen = set()
    for r in rows:
        hub_city = next((m for k, m in by_page.items() if k[0] == r["region"] and k[1] == r["service"]
                         and (k[2].lower() == r["city"].lower() or slugify(k[2]) == slugify(r["city"]))), None)
        email = (r.get("email") or "").strip()
        if not hub_city or "@" not in email or (email, hub_city["url"]) in seen:
            continue
        seen.add((email, hub_city["url"]))
        out.append([r["name"], email, hub_city["city"], SERVICES[r["service"]]["name"], BASE + hub_city["url"],
                    BASE + "/installers/badge/", r.get("rating", ""), r.get("reviews", "")])
    with open(ROOT / "data" / "outreach-rankings.csv", "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(out)
    return len(out) - 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = load_rows()
    hubs = city_hubs()
    groups = {}
    for r in rows:
        groups.setdefault((r["region"], r["service"], r["city"]), []).append(r)
    eligible = {k: v for k, v in groups.items() if len(v) >= MIN_INSTALLERS}

    def page_path(region, service, city):
        hub = find_hub(hubs, region, city)
        return f"/installers/{region}/{hub['slug'] if hub else slugify(city)}/{service}/"

    index, built, written, no_hub = [], [], 0, []
    for (region, service, city), inst in sorted(eligible.items()):
        hub = find_hub(hubs, region, city)
        if not hub:
            no_hub.append(f"{region}/{city}")
        other = "solar" if service == "heat-pump" else "heat-pump"
        other_url = page_path(region, other, city) if (region, other, city) in eligible else ""
        label = hub["label"] if hub else city
        path, html_out, meta = build_page(region, service, label, hub, inst, other_url)
        built.append({**meta, "html": html_out, "text": body_text(html_out, label)})

    held = near_duplicates(built)
    for b in built:
        html_out = b.pop("html")
        b.pop("text")
        if b["url"] in held:
            html_out = html_out.replace('content="index, follow, max-snippet:-1, max-image-preview:large"', 'content="noindex, follow"', 1)
            b["indexed"] = False
        else:
            b["indexed"] = True
        index.append(b)
        if not args.dry_run:
            out = ROOT / b["url"].strip("/") / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(html_out, encoding="utf-8")
            written += 1

    if not args.dry_run:
        mp, mhtml = method_page()
        (ROOT / mp.strip("/")).mkdir(parents=True, exist_ok=True)
        (ROOT / mp.strip("/") / "index.html").write_text(mhtml, encoding="utf-8")
        update_installers_hub(index)
        for m in index:
            if m.get("indexed"):
                (ROOT / m["url"].strip("/") / "badge.svg").write_text(badge_svg(m["city"], m["service"]), encoding="utf-8")
        bp, bhtml = badge_page(index)
        (ROOT / bp.strip("/")).mkdir(parents=True, exist_ok=True)
        (ROOT / bp.strip("/") / "index.html").write_text(bhtml, encoding="utf-8")
        print(f"{outreach_list(index, rows)} installers with public emails in data/outreach-rankings.csv (not published).")
        print(f"{link_city_pages(index, hubs)} city pages linked to their rankings.")
        (ROOT / "installers" / "rankings.json").write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(rows)} installers, {len(groups)} city/service groups, {len(eligible)} pages "
          f"({'dry run' if args.dry_run else f'{written} written'}).")
    print(f"{len(held)} held back as noindex (>=90% similar to a sibling): {', '.join(sorted(held))}")
    if no_hub:
        print(f"{len(no_hub)} without a matching city hub (no rebate link): {', '.join(no_hub[:12])}")


if __name__ == "__main__":
    main()
