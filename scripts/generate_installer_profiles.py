#!/usr/bin/env python3
"""
Generate installer profile pages (installers/profiles/<region>/<city>/<slug>/index.html)
from the per-city JSON files (installers/json/<region>/{,solar/}<city>.json).

This mirrors the hand-built BC profile template exactly (see e.g.
installers/profiles/kelowna/air-temp-heating-cooling-specialist/index.html) —
same CSS, same LocalBusiness+AggregateRating+BreadcrumbList JSON-LD, same
vetting block + license-verify links, same quote form. No profile-page
generator existed in scripts/ before this (confirmed via a background-agent
search on 2026-08-30), so this fills that gap for CA and NY specifically,
generalizable to future regions via REGIONS below.

Run from the Powerrebate root:
  python3 scripts/generate_installer_profiles.py
"""
import json
import os
import re
import html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def slugify(name):
    s = name.lower().strip()
    s = re.sub(r"[&']", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


# Each region: where its JSON lives, where its site hub pages live per city,
# the state/province abbreviation for the address, the program-verification
# copy (region-correct — never borrow another region's program name), and
# whether category subpages exist (CA: heat-pump/, solar/ dirs) or the city
# has one combined index.html covering every category (NY).
REGIONS = {
    "ca": {
        "json_dir": os.path.join(ROOT, "installers/json/ca"),
        "profiles_dir": os.path.join(ROOT, "installers/profiles/ca"),
        "state": "CA",
        "hub_style": "category-subpage",  # /us/ca/<group>/<city>/<category>/
        "city_to_group": {
            "berkeley": "bay-area", "fremont": "bay-area", "oakland": "bay-area",
            "san-francisco": "bay-area", "san-jose": "bay-area",
            "burbank": "los-angeles", "glendale": "los-angeles", "long-beach": "los-angeles",
            "los-angeles": "los-angeles", "pasadena": "los-angeles", "santa-monica": "los-angeles",
            "folsom": "sacramento", "rancho-cordova": "sacramento", "roseville": "sacramento",
            "sacramento": "sacramento",
            "chula-vista": "san-diego", "escondido": "san-diego", "san-diego": "san-diego",
            "moreno-valley": "inland-empire", "ontario": "inland-empire",
            "riverside": "inland-empire", "san-bernardino": "inland-empire",
            # Standalone cities — no metro-group subfolder, page lives directly
            # at /us/ca/<city>/ like PA/CO/VT. None here is a real sentinel,
            # not a missing mapping — city_hub_url falls back to the flat
            # path when it sees one.
            "fresno": None, "bakersfield": None,
        },
        "breadcrumb_region_name": "California",
        "vetting_note": "Confirm current licensing, insurance, and program eligibility directly with any installer before signing a contract",
        "verify_links": [
            ("https://www.cslb.ca.gov/OnlineServices/CheckLicenseII/CheckLicense.aspx",
             "Verify this installer's CA Contractors State License Board registration"),
        ],
        "program_name": "Local rebate programs",
    },
    "ny": {
        "json_dir": os.path.join(ROOT, "installers/json/ny"),
        "profiles_dir": os.path.join(ROOT, "installers/profiles/ny"),
        "state": "NY",
        "hub_style": "combined-index",  # /us/ny/<utility>/<city>/
        "city_to_utility": {
            "beacon": "central-hudson", "kingston": "central-hudson", "newburgh": "central-hudson",
            "poughkeepsie": "central-hudson", "saugerties": "central-hudson",
            "mount-vernon": "con-edison", "new-rochelle": "con-edison", "new-york-city": "con-edison",
            "white-plains": "con-edison", "yonkers": "con-edison",
            "albany": "national-grid", "buffalo": "national-grid", "rochester": "national-grid",
            "syracuse": "national-grid",
            "babylon": "pseg", "brookhaven": "pseg", "huntington": "pseg", "islip": "pseg",
            "oyster-bay": "pseg", "smithtown": "pseg", "southampton": "pseg",
        },
        "breadcrumb_region_name": "New York",
        # NY has no statewide contractor license (confirmed via research, Aug 30 2026) —
        # it's fragmented by city/county, so the honest copy directs homeowners to
        # check locally rather than implying one lookup tool covers the whole state.
        "vetting_note": "NY has no single statewide contractor license &mdash; confirm current licensing, insurance, and program eligibility directly with any installer, and check your city or county's own licensing office",
        "verify_links": [
            ("https://www.nyc.gov/site/buildings/index.page", "NYC: verify a license via the DOB (New York City installers only)"),
        ],
        "program_name": "NYS Clean Heat & utility rebates",
    },
    "vt": {
        "json_dir": os.path.join(ROOT, "installers/json/vt"),
        "profiles_dir": os.path.join(ROOT, "installers/profiles/vt"),
        "state": "VT",
        "hub_style": "flat-index",  # /us/vt/<city>/ — no utility or metro-group segment
        "breadcrumb_region_name": "Vermont",
        # Vermont has no statewide general contractor license (one of the few
        # states without one) — same honest framing as NY above rather than
        # implying a lookup tool that doesn't exist.
        "vetting_note": "Vermont has no statewide general contractor license &mdash; confirm current insurance and program eligibility directly with any installer before signing a contract",
        "verify_links": [],
        "program_name": "Efficiency Vermont rebates",
    },
}

CSS = """:root { --ink:#0a2a2e; --ink-soft:#1a3d42; --paper:#faf7f2; --paper-warm:#f5efe5; --teal:#0d4f5c; --teal-deep:#08363f; --amber:#d4751c; --amber-bright:#e88a2e; --green-money:#2d6a4f; --rule:#d9d0c1; }
* { box-sizing:border-box; }
body { margin:0; background:var(--paper); color:var(--ink); font-family:'Inter Tight',sans-serif; line-height:1.6; }
h1,h2,h3 { font-family:'Fraunces',Georgia,serif; color:var(--teal-deep); }
a { color:var(--teal-deep); }
.ip-wrap { max-width:760px; margin:0 auto; padding:32px 20px 80px; }
.ip-breadcrumb { font-size:13px; color:#7a7264; margin-bottom:24px; }
.ip-breadcrumb a { color:#7a7264; text-decoration:none; }
.ip-hero { display:flex; justify-content:space-between; align-items:flex-start; gap:20px; flex-wrap:wrap; margin-bottom:8px; }
.ip-hero h1 { font-size:clamp(26px,4vw,36px); margin:0 0 6px; line-height:1.15; }
.ip-hero-meta { color:#5a5348; font-size:15px; }
.ip-intro { font-size:16px; color:#3d3830; margin:18px 0 0; max-width:62ch; }
.ip-rating { text-align:right; }
.ip-rating-num { font-family:'Fraunces',Georgia,serif; font-size:32px; font-weight:700; color:var(--amber); line-height:1; }
.ip-rating-count { font-size:13px; color:#7a7264; }
.ip-actions { display:flex; gap:10px; flex-wrap:wrap; margin:22px 0 8px; }
.ip-btn { padding:12px 22px; border-radius:999px; font-weight:700; font-size:15px; text-decoration:none; display:inline-block; }
.ip-btn-primary { background:var(--amber); color:#fff; }
.ip-btn-outline { background:#fff; color:var(--teal-deep); border:1.5px solid var(--rule); }
.ip-maps-link { font-size:13px; color:#7a7264; text-decoration:underline; align-self:center; }
.ip-kind { margin-top:44px; padding-top:28px; border-top:1px solid var(--rule); }
.ip-kind-head h2 { font-size:22px; margin:0 0 4px; }
.ip-rank { font-size:14px; color:var(--green-money); margin:0 0 18px; }
.ip-programs { display:flex; flex-direction:column; gap:10px; }
.ip-program { display:flex; justify-content:space-between; align-items:center; gap:16px; background:#fff; border:1px solid var(--rule); border-radius:12px; padding:16px 18px; text-decoration:none; }
.ip-program-name { font-weight:700; color:var(--teal-deep); font-size:15px; }
.ip-program-detail { font-size:13.5px; color:#5a5348; margin-top:2px; }
.ip-program-arrow { color:var(--amber); font-size:18px; flex-shrink:0; }
.ip-guide-link { display:inline-block; margin-top:16px; font-weight:700; color:var(--amber); text-decoration:none; font-size:14.5px; }
.ip-vetting { margin-top:44px; background:var(--paper-warm); border-radius:14px; padding:24px; }
.ip-vetting h3 { font-size:18px; margin:0 0 14px; }
.ip-vet-row { display:flex; gap:12px; align-items:flex-start; padding:10px 0; border-top:1px solid var(--rule); font-size:14.5px; }
.ip-vet-row:first-of-type { border-top:none; }
.ip-vet-icon { width:22px; height:22px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px; flex-shrink:0; }
.ip-vet-yes .ip-vet-icon { background:var(--green-money); color:#fff; }
.ip-vet-detail { color:#5a5348; font-size:13.5px; }
.ip-vet-note { font-size:13px; color:#7a7264; margin:16px 0 0; line-height:1.5; }
.ip-verify-links { margin-top:14px; display:flex; flex-direction:column; gap:6px; }
.ip-verify-links a { font-size:13.5px; font-weight:600; }
.ip-photo { width:100%; height:auto; aspect-ratio:2/1; object-fit:cover; border-radius:14px; margin:18px 0 0; }
.ip-nearby { margin-top:44px; }
.ip-nearby h3 { font-size:17px; margin:0 0 12px; }
.ip-nearby-list { display:flex; flex-direction:column; gap:8px; }
.ip-nearby-item { display:flex; justify-content:space-between; padding:12px 16px; background:#fff; border:1px solid var(--rule); border-radius:10px; text-decoration:none; color:var(--teal-deep); font-size:14px; font-weight:600; }
.ip-nearby-rating { color:var(--amber); }
.ip-city-link { display:block; margin-top:36px; text-align:center; font-size:14.5px; }
.ip-footer-note { margin-top:60px; font-size:12.5px; color:#9a9385; border-top:1px solid var(--rule); padding-top:20px; }
.ip-quote { margin-top:52px; background:var(--teal-deep); border-radius:16px; padding:32px 28px; color:var(--paper); }
.ip-quote h2 { color:#fff; font-size:22px; margin:0 0 8px; }
.ip-quote p { color:#c9d8d5; font-size:14.5px; margin:0 0 20px; }
.ip-quote-form { display:flex; flex-direction:column; gap:10px; max-width:380px; }
.ip-quote-form input { padding:13px 14px; border-radius:9px; border:1.5px solid transparent; font-family:'Inter Tight',sans-serif; font-size:15px; }
.ip-quote-form button { padding:13px; background:var(--amber); color:#fff; border:none; border-radius:999px; font-weight:700; font-size:15.5px; cursor:pointer; }
.ip-quote-done { display:none; color:var(--amber-bright); font-weight:700; }"""


missing_category_pages = set()  # tracked for the end-of-run report


def city_hub_url(region_key, city_slug, category):
    cfg = REGIONS[region_key]
    if cfg["hub_style"] == "category-subpage":
        group = cfg["city_to_group"][city_slug]
        if group is None:
            # Standalone city — no metro-group subfolder (e.g. Fresno,
            # Bakersfield), page lives directly at /us/<region>/<city>/.
            local_dir = os.path.join(ROOT, "us", region_key, city_slug, category)
            if not os.path.isdir(local_dir):
                missing_category_pages.add(f"us/{region_key}/{city_slug}/{category}/")
                return f"https://homepowerrebate.com/us/{region_key}/{city_slug}/"
            return f"https://homepowerrebate.com/us/{region_key}/{city_slug}/{category}/"
        local_dir = os.path.join(ROOT, "us", region_key, group, city_slug, category)
        if not os.path.isdir(local_dir):
            # Site doesn't have this category built for this city yet (a real,
            # pre-existing content gap — e.g. most CA cities have no /solar/
            # page). Link to the city's main hub instead of a 404.
            missing_category_pages.add(f"us/{region_key}/{group}/{city_slug}/{category}/")
            return f"https://homepowerrebate.com/us/{region_key}/{group}/{city_slug}/"
        return f"https://homepowerrebate.com/us/{region_key}/{group}/{city_slug}/{category}/"
    elif cfg["hub_style"] == "combined-index":
        utility = cfg["city_to_utility"][city_slug]
        return f"https://homepowerrebate.com/us/{region_key}/{utility}/{city_slug}/"
    else:  # flat-index — city page lives directly at /us/<region>/<city>/
        return f"https://homepowerrebate.com/us/{region_key}/{city_slug}/"


def city_display_name(city_slug):
    return city_slug.replace("-", " ").title()


def address_region_from_location(location, fallback_state):
    m = re.search(r",\s*([A-Z]{2})\s*\d{5}", location)
    return m.group(1) if m else fallback_state


def render_profile(region_key, city_slug, listings, all_in_city_by_cat):
    """listings: list of (installer_dict, category, rank, total) for every
    category this business appears under in this city — usually one, but a
    business offering both heat-pump AND solar service gets a single merged
    page rather than one category silently overwriting the other."""
    cfg = REGIONS[region_key]
    city_name = city_display_name(city_slug)
    installer = listings[0][0]  # base fields (name/rating/etc.) are identical across listings
    name = installer["name"]
    slug = slugify(name)
    rating = installer["rating"]
    reviews = installer["reviews"]
    state = address_region_from_location(installer["location"], cfg["state"])
    specialty = " & ".join(dict.fromkeys(inst["specialty"] for inst, _, _, _ in listings))
    image = installer["image_url"]
    escaped_name = html.escape(name)

    canonical = f"https://homepowerrebate.com/installers/profiles/{region_key}/{city_slug}/{slug}/"
    breadcrumb_city_url = f"https://homepowerrebate.com/us/{region_key}/"  # generic state hub, safe fallback
    primary_category = listings[0][1]
    hub_url = city_hub_url(region_key, city_slug, primary_category)

    rank_lines = []
    program_cards = []
    for inst, category, rank, total in listings:
        label = "Heat Pump & HVAC" if category == "heat-pump" else "Solar"
        rank_lines.append(f"Ranked <strong>#{rank} of {total}</strong> {label.lower()} installers in {city_name} by Google rating")
        program_href = city_hub_url(region_key, city_slug, category)
        program_name = cfg["program_name"]
        program_detail = f"See {city_name}'s current {('heat pump' if category == 'heat-pump' else 'solar')} rebate breakdown for exact numbers"
        program_cards.append(f'''    <a href="{program_href}" class="ip-program">
      <div class="ip-program-name">{program_name} ({label})</div>
      <div class="ip-program-detail">{program_detail}</div>
      <span class="ip-program-arrow">&rarr;</span>
    </a>''')
    rank_html = "<br>".join(rank_lines)
    programs_html = "\n".join(program_cards)

    verify_html = "\n".join(
        f'          <a href="{url}" target="_blank" rel="noopener">{label} &rarr;</a>'
        for url, label in cfg["verify_links"]
    )

    # Nearby list pulled from the primary category's city roster only, to keep
    # it to real same-category peers rather than mixing heat-pump and solar lists.
    all_in_city = all_in_city_by_cat[primary_category]
    nearby = [i for i in all_in_city if i["name"] != name][:9]
    nearby_html = "".join(
        f'<a href="/installers/profiles/{region_key}/{city_slug}/{slugify(n["name"])}/" class="ip-nearby-item">'
        f'<span>{html.escape(n["name"])}</span><span class="ip-nearby-rating">{n["rating"]:.0f}★</span></a>'
        for n in nearby
    )

    quote_source = f'installer-{region_key}-{slug}'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escaped_name} — {city_name}, {state} | HomePowerRebate</title>

<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-W33G4TGRHD');
</script>

<meta name="description" content="{escaped_name} in {city_name}, {state} — {rating:.1f}★ ({reviews} reviews). {specialty} installer. See which rebates their work qualifies for and get a quote.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="business.business">
<meta property="og:title" content="{escaped_name} — {city_name}, {state}">
<meta property="og:description" content="{escaped_name} in {city_name}, {state} — {rating:.1f}★ ({reviews} reviews). {specialty} installer. See which rebates their work qualifies for and get a quote.">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escaped_name} — {city_name}, {state}">
<meta name="twitter:description" content="{escaped_name} in {city_name}, {state} — {rating:.1f}★ ({reviews} reviews). {specialty} installer.">
<meta name="twitter:image" content="{image}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
<script type="application/ld+json">{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "LocalBusiness",
      "name": {json.dumps(name)},
      "image": {json.dumps(image)},
      "address": {{
        "@type": "PostalAddress",
        "streetAddress": {json.dumps(installer["location"])},
        "addressRegion": {json.dumps(state)},
        "addressCountry": "US"
      }},
      "telephone": {json.dumps(installer["phone"])},
      "url": {json.dumps(installer["website"])},
      "aggregateRating": {{
        "@type": "AggregateRating",
        "ratingValue": {json.dumps(str(rating))},
        "reviewCount": {json.dumps(str(reviews))},
        "bestRating": "5"
      }},
      "areaServed": {{
        "@type": "City",
        "name": {json.dumps(city_name)}
      }}
    }},
    {{
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "HomePowerRebate", "item": "https://homepowerrebate.com/"}},
        {{"@type": "ListItem", "position": 2, "name": {json.dumps(city_name)}, "item": {json.dumps(breadcrumb_city_url)}}},
        {{"@type": "ListItem", "position": 3, "name": {json.dumps(name)}, "item": {json.dumps(canonical)}}}
      ]
    }}
  ]
}}</script>
<style>
{CSS}
</style>
</head>
<body>
<div class="ip-wrap">
  <p class="ip-breadcrumb"><a href="/">HomePowerRebate</a> / <a href="{hub_url}">{city_name}</a> / {escaped_name}</p>

  <div class="ip-hero">
    <div>
      <h1>{escaped_name}</h1>
      <p class="ip-hero-meta">{specialty} &middot; {city_name}, {state}</p>
    </div>
    <div class="ip-rating"><div class="ip-rating-num">{rating:.0f}★</div><div class="ip-rating-count">{reviews} reviews</div></div>
  </div>

  <img src="{image}" alt="{escaped_name}" class="ip-photo" loading="lazy" width="760" height="380">

  <p class="ip-intro">{escaped_name} is a {specialty.lower()} provider in {city_name} with a current Google rating of {rating:.1f}★ from {reviews} reviews.</p>

  <div class="ip-actions">
    <a href="{installer["website"]}" target="_blank" rel="noopener" class="ip-btn ip-btn-primary">Visit Website</a>
    <a href="tel:{re.sub(r"[^0-9+]", "", installer["phone"])}" class="ip-btn ip-btn-outline">Call {installer["phone"]}</a>
    <a href="{installer["gmaps_url"]}" target="_blank" rel="noopener" class="ip-maps-link">View on Google Maps</a>
  </div>

  <section class="ip-kind">
    <div class="ip-kind-head">
      <h2>{specialty} Rebates This Installer Puts You In Reach Of</h2>
      <p class="ip-rank">{rank_html}</p>
    </div>
    <div class="ip-programs">
{programs_html}
    </div>
  </section>

  <aside class="ip-vetting">
    <h3>What We Checked</h3>
    <div class="ip-vet-row ip-vet-yes">
      <span class="ip-vet-icon">✓</span>
      <div><strong>Listed on Google Business Profile</strong><br><span class="ip-vet-detail">{rating:.1f}★ from {reviews} reviews</span></div>
    </div>
    <p class="ip-vet-note">{cfg["vetting_note"]} &mdash; <a href="https://homepowerrebate.com/guides/installer-vetting-checklist/">see the full checklist</a>.</p>
    <div class="ip-verify-links">
{verify_html}
    </div>
  </aside>

  <section class="ip-nearby">
    <h3>Other {city_name} Installers</h3>
    <div class="ip-nearby-list">{nearby_html}</div>
  </section>

  <section class="ip-quote">
    <h2>Get a Quote From {escaped_name}</h2>
    <p>We'll pass your details along and follow up with your rebate breakdown.</p>
    <form class="ip-quote-form" id="ip-quote-form">
      <input type="text" id="ip-name" placeholder="First name" required>
      <input type="email" id="ip-email" placeholder="your@email.com" required>
      <input type="tel" id="ip-phone" placeholder="Phone number" required>
      <input type="text" id="ip-hp" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px;" aria-hidden="true">
      <button type="submit" id="ip-quote-btn">Request a Quote &rarr;</button>
    </form>
    <p class="ip-quote-done" id="ip-quote-done">✓ Sent &mdash; {escaped_name} will be in touch.</p>
  </section>

  <a href="{hub_url}" class="ip-city-link">See all {city_name} rebates &rarr;</a>

  <p class="ip-footer-note">Business details sourced from Google Business Profile, last checked via Google Places API. Spot an error? <a href="/contact?subject=Correction: {escaped_name}">Let us know</a>.</p>
</div>
<script>
(function() {{
  var form = document.getElementById('ip-quote-form');
  form.addEventListener('submit', function(e) {{
    e.preventDefault();
    if (document.getElementById('ip-hp').value) return;
    var btn = document.getElementById('ip-quote-btn');
    btn.disabled = true; btn.textContent = 'Sending…';
    fetch('https://leads.homepowerrebate.com/estimate-lead', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{
        firstname: document.getElementById('ip-name').value,
        email: document.getElementById('ip-email').value,
        phone: document.getElementById('ip-phone').value,
        city: {json.dumps(city_name)},
        source: {json.dumps(quote_source)},
        installer: {json.dumps(name)}
      }})
    }}).catch(function(err) {{ console.error('quote request error', err); }})
      .finally(function() {{
        form.style.display = 'none';
        document.getElementById('ip-quote-done').style.display = 'block';
      }});
  }});
}})();
</script>
</body>
</html>
"""


def build_region(region_key):
    cfg = REGIONS[region_key]
    total_pages = 0

    # Discover every city that has a JSON file in either category.
    cat_dirs = {}
    for category, subdir in [("heat-pump", ""), ("solar", "solar")]:
        d = os.path.join(cfg["json_dir"], subdir) if subdir else cfg["json_dir"]
        cat_dirs[category] = d

    cities = set()
    for d in cat_dirs.values():
        if os.path.isdir(d):
            cities.update(f[:-5] for f in os.listdir(d) if f.endswith(".json"))

    for city_slug in sorted(cities):
        all_in_city_by_cat = {}
        for category, d in cat_dirs.items():
            path = os.path.join(d, f"{city_slug}.json")
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    all_in_city_by_cat[category] = json.load(f)
            else:
                all_in_city_by_cat[category] = []

        # Group by slug across categories so a business in both categories
        # gets one merged page instead of one category overwriting the other.
        by_slug = {}
        for category, installers in all_in_city_by_cat.items():
            for idx, installer in enumerate(installers):
                slug = slugify(installer["name"])
                by_slug.setdefault(slug, []).append((installer, category, idx + 1, len(installers)))

        for slug, listings in by_slug.items():
            out_dir = os.path.join(cfg["profiles_dir"], city_slug, slug)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, "index.html")
            html_out = render_profile(region_key, city_slug, listings, all_in_city_by_cat)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html_out)
            total_pages += 1

    return total_pages


if __name__ == "__main__":
    grand = 0
    for region_key in REGIONS:
        n = build_region(region_key)
        print(f"{region_key}: {n} profile pages")
        grand += n
    print(f"\nTotal: {grand} profile pages generated")
    if missing_category_pages:
        print(f"\n⚠️  {len(missing_category_pages)} category pages don't exist yet on the site")
        print(f"   (profiles link to the city's main hub instead, not a 404 — but this")
        print(f"    is a real content gap worth filling separately):")
        for p in sorted(missing_category_pages):
            print(f"     - {p}")
