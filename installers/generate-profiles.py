#!/usr/bin/env python3
"""
Generate one profile page per installer from the CSV data.

Run this once, and again whenever the CSVs change (new installer, corrected
phone number, an email recovered). It's the only thing that has to happen for
159 pages to exist — no per-page manual work, ever.

    python3 generate-profiles.py           # writes all pages + index + sitemap
    python3 generate-profiles.py --dry-run # report counts, write nothing

Design intent (see conversation for the full reasoning): these are NOT
directory listings. A directory listing is what Google Maps already is. Each
page's job is to answer a question Maps can't: what rebates does hiring this
installer actually put you in reach of, and does their listing show the things
BC's programs actually check for (HPCN certification, license, insurance).
That's the reason an installer links back, and the reason a homeowner stays on
the page instead of bouncing straight to a phone number.

Forward compatibility: two optional CSV columns are read if present and
silently skipped if absent — "Video URL" (case study embed) and "BCH Approved"
(BC Hydro approved-program flag). Add either column later, rerun this script,
and every existing page picks it up. No template rewrite needed.
"""

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
INSTALLERS_DIR = ROOT / "installers"
OUT_DIR = INSTALLERS_DIR / "profiles"
SITE_URL = "https://homepowerrebate.com"
LEADS_ENDPOINT = "https://leads.homepowerrebate.com"

# The "HomePowerRebate Recommended" CSV column reflects a rating/review
# threshold, not an actual vetting relationship with the installer — no
# installer has been personally contacted or verified yet. Displaying it as
# a "recommendation" claims more than is true. Off until there's a real
# vetting process behind it; flip to True then, no other changes needed.
SHOW_RECOMMENDED = False

# Keys are pre-normalized (see normalize_city) so punctuation variants from
# Google Places data ("Fort St. John" vs "Fort St John") both resolve.
CITY_SLUGS = {
    "abbotsford": "abbotsford", "burnaby": "burnaby", "chilliwack": "chilliwack",
    "coquitlam": "coquitlam", "fort st john": "fort-st-john", "kamloops": "kamloops",
    "kelowna": "kelowna", "langley": "langley", "maple ridge": "maple-ridge",
    "nanaimo": "nanaimo", "penticton": "penticton", "prince george": "prince-george",
    "richmond": "richmond", "squamish": "squamish", "surrey": "surrey",
    "vancouver": "vancouver", "vernon": "vernon", "victoria": "victoria",
}

ON_CITY_SLUGS = {
    "toronto": "toronto", "ottawa": "ottawa", "mississauga": "mississauga",
    "brampton": "brampton", "hamilton": "hamilton", "markham": "markham",
    "vaughan": "vaughan", "richmond hill": "richmond-hill", "barrie": "barrie",
    "london": "london", "kitchener": "kitchener", "windsor": "windsor",
    "oakville": "oakville", "oshawa": "oshawa", "whitby": "whitby",
    "burlington": "burlington", "cambridge": "cambridge",
    "greater sudbury": "greater-sudbury",
}

# What each service type actually unlocks. This is the part a Maps listing
# can't show — it's why the page exists at all. Split by province since the
# programs, amounts, and structure are genuinely different (BC: CleanBC,
# income-tiered; Ontario: HRSP, fuel-tiered) — not a find-and-replace.
REBATE_CONTEXT = {
    "heat-pump": {
        "label": "Heat Pump",
        "programs": [
            ("CleanBC Better Homes", "Up to $16,000 combined federal + provincial, most BC homeowners", "/guides/heat-pump-buyers-guide/"),
            ("CleanBC Income Qualified", "100% covered for income-qualifying households", "/blog/cleanbc-income-qualified-free-heat-pump-2026.html"),
        ],
        "requires_cert": True,
        "guide": ("/guides/heat-pump-buyers-guide/", "Heat Pump Buyer's Guide"),
    },
    "solar": {
        "label": "Solar",
        "programs": [
            ("BC Hydro Net Metering", "Rolling monthly credit for surplus solar production", "/questions/bc-hydro-solar-rebate-2026/"),
            ("Peak Saver (with battery)", "Up to $5,000 vs $1,500 without enrolment", "/blog/bc-hydro-peak-saver-battery-rebate-5000-vs-1500.html"),
        ],
        "requires_cert": False,
        "guide": ("/guides/solar-battery-decision-guide/", "Solar vs Battery Decision Guide"),
    },
}

ON_REBATE_CONTEXT = {
    "heat-pump": {
        "label": "Heat Pump",
        "programs": [
            ("HRSP Heat Pump Rebate", "$2,000–$12,000 depending on current fuel and system type", "/blog/ontario-heat-pump-rebate-tiers-explained"),
            ("Avoiding rejection", "Pre-installation approval + qualified-products-list check needed first", "/blog/ontario-heat-pump-rebate-rejection-mistakes"),
        ],
        "requires_cert": True,
        "guide": ("/blog/ontario-home-renovation-savings-program-explained", "HRSP Explained"),
    },
    "solar": {
        "label": "Solar",
        "programs": [
            ("HRSP Solar Rebate", "Up to $5,000 ($1,000/kW, capped at 50% of cost)", "/blog/ontario-solar-rebate-vs-net-metering"),
            ("Battery bundle", "Up to $10,000 combined when paired with battery storage", "/blog/ontario-home-energy-rebates-2026-listicle"),
        ],
        "requires_cert": False,
        "guide": ("/blog/ontario-solar-rebate-vs-net-metering", "Solar vs. Net Metering"),
    },
}

# Per-province config the rest of the script keys off of. BC's values match
# exactly what was hardcoded before (same URLs, same paths) — adding Ontario
# doesn't change a single BC output path or existing page.
PROVINCE_CONFIG = {
    "bc": {
        "region_abbrev": "BC",
        "region_full": "British Columbia",
        "city_slugs": CITY_SLUGS,
        "rebate_context": REBATE_CONTEXT,
        "hub_prefix": "/ca/bc",
        "profile_prefix": "/installers/profiles",  # unchanged — no /bc/ segment
        "heat_pump_csv": "heat-pump-installers-real.csv",
        "solar_csv": "solar-installers-real.csv",
        "json_dir": "json",
    },
    "on": {
        "region_abbrev": "ON",
        "region_full": "Ontario",
        "city_slugs": ON_CITY_SLUGS,
        "rebate_context": ON_REBATE_CONTEXT,
        "hub_prefix": "/ca/on",
        "profile_prefix": "/installers/profiles/on",
        "heat_pump_csv": "on-heat-pump-installers-real.csv",
        "solar_csv": "on-solar-installers-real.csv",
        "json_dir": "json/on",
    },
}


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "installer"


def normalize_city(text):
    """Strip punctuation so 'Fort St. John' and 'fort st john' match the same
    key — CSV data from Google Places isn't consistent about periods."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def load_rows(filename, kind):
    path = INSTALLERS_DIR / filename
    if not path.exists():
        return []
    rows = []
    for r in csv.DictReader(path.open()):
        r["_kind"] = kind
        rows.append(r)
    return rows


def load_emails():
    path = INSTALLERS_DIR / "installer-emails.csv"
    if not path.exists():
        return {}
    out = {}
    for r in csv.DictReader(path.open()):
        if r.get("Email"):
            out[(r["Business Name"].strip().lower(), r["City"].strip().lower())] = r["Email"]
    return out


def merge_and_dedupe(rows):
    """Same business can appear in both CSVs if they do both trades. Merge
    those into one page with both service types rather than two thin ones."""
    merged = {}
    for r in rows:
        key = (r["Business Name"].strip().lower(), r["City"].strip().lower())
        if key not in merged:
            merged[key] = {**r, "_kinds": {r["_kind"]}}
        else:
            merged[key]["_kinds"].add(r["_kind"])
    return list(merged.values())


def rank_within_city(installers):
    """City + primary-kind ranking, sorted by rating then review count. Pure
    arithmetic on data already in the CSV — this is what lets the page say
    something a bare listing can't, for zero extra research per installer."""
    groups = defaultdict(list)
    for inst in installers:
        for kind in inst["_kinds"]:
            groups[(inst["City"].strip().lower(), kind)].append(inst)

    ranks = {}
    for (city, kind), group in groups.items():
        ordered = sorted(
            group,
            key=lambda r: (float(r.get("Google Rating") or 0), int(r.get("Review Count") or 0)),
            reverse=True,
        )
        for i, inst in enumerate(ordered, start=1):
            ranks[(inst["Business Name"].strip().lower(), city, kind)] = (i, len(ordered))
    return ranks


def fmt_phone_href(phone):
    digits = re.sub(r"\D", "", phone or "")
    return f"+1{digits}" if len(digits) == 10 else f"+{digits}"


def escape(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render_program_row(name, detail, link):
    return f"""
        <a href="{link}" class="ip-program">
          <div class="ip-program-name">{escape(name)}</div>
          <div class="ip-program-detail">{escape(detail)}</div>
          <span class="ip-program-arrow">&rarr;</span>
        </a>"""


def render_kind_section(kind, inst, city_slug, rank_info, cfg):
    ctx = cfg["rebate_context"][kind]
    programs_html = "".join(render_program_row(n, d, SITE_URL + l) for n, d, l in ctx["programs"])
    rank, total = rank_info.get((inst["Business Name"].strip().lower(), inst["City"].strip().lower(), kind), (None, None))
    rank_html = ""
    if rank and total and total > 1:
        rank_html = f'<p class="ip-rank">Ranked <strong>#{rank} of {total}</strong> {ctx["label"].lower()} installers in {escape(inst["City"])} by Google rating</p>'

    guide_path, guide_title = ctx["guide"]
    return f"""
      <section class="ip-kind">
        <div class="ip-kind-head">
          <h2>{ctx["label"]} Rebates This Installer Puts You In Reach Of</h2>
          {rank_html}
        </div>
        <div class="ip-programs">{programs_html}
        </div>
        <a href="{guide_path}" class="ip-guide-link">Read the {escape(guide_title)} &rarr;</a>
      </section>"""


def render_vetting_card(inst, cfg):
    """Honest about what's actually known. A blanket 'Verified' badge on
    every row would undercut the one message these pages are built to carry —
    that vetting is specific, not decorative."""
    bch = (inst.get("BCH Approved") or "").strip().lower() == "yes"  # optional future column, BC only

    items = []
    items.append(("Listed on Google Business Profile", True,
                   f'{escape(inst.get("Google Rating",""))}★ from {escape(inst.get("Review Count",""))} reviews'))
    if SHOW_RECOMMENDED:
        recommended = (inst.get("HomePowerRebate Recommended") or "").strip().lower() == "yes"
        items.append(("HomePowerRebate rating threshold", recommended,
                       "Meets our 4★ / 10+ review bar for recommendation" if recommended
                       else "Below our recommendation threshold — check reviews directly"))
    if bch and cfg["region_abbrev"] == "BC":
        items.append(("BC Hydro approved program", True, "Listed in a BC Hydro approved-contractor program"))

    rows = "".join(f"""
        <div class="ip-vet-row {'ip-vet-yes' if ok else 'ip-vet-no'}">
          <span class="ip-vet-icon">{'✓' if ok else '–'}</span>
          <div><strong>{escape(label)}</strong><br><span class="ip-vet-detail">{escape(detail)}</span></div>
        </div>""" for label, ok, detail in items)

    return f"""
      <aside class="ip-vetting">
        <h3>What We Checked</h3>
        {rows}
        <p class="ip-vet-note">Confirm HPCN certification and current insurance directly with any installer before signing a contract — <a href="{SITE_URL}/guides/installer-vetting-checklist/">see the full checklist</a>.</p>
      </aside>"""


def render_video_section(inst):
    """No-op until a Video URL column exists in the CSV. Present now so this
    activates by adding a column, not editing the template."""
    video_url = (inst.get("Video URL") or "").strip()
    if not video_url:
        return ""
    return f"""
      <section class="ip-video">
        <h2>Case Study</h2>
        <div class="ip-video-embed"><iframe src="{escape(video_url)}" loading="lazy" allowfullscreen title="{escape(inst['Business Name'])} case study"></iframe></div>
      </section>"""


def render_intro(inst, kinds, rank_info, city, cfg):
    """The one piece of prose Google can't find on any other page. Everything
    else on the page (program cards, vetting card labels) is necessarily
    similar across same-kind listings — that's fine, the same way every Yelp
    or Zillow listing shares boilerplate around unique facts. What makes a
    templated page NOT read as duplicate content is that it says something
    true and specific up top. This is built from real numbers already in the
    row (rating, review count, rank), not invented, so it stays honest as the
    data changes.
    """
    rating = float(inst.get("Google Rating") or 0)
    reviews = int(inst.get("Review Count") or 0)
    kind_label = " and ".join(cfg["rebate_context"][k]["label"].lower() for k in kinds)

    best_rank, best_total = None, None
    for k in kinds:
        r, t = rank_info.get((inst["Business Name"].strip().lower(), city.strip().lower(), k), (None, None))
        if r and (best_rank is None or r < best_rank):
            best_rank, best_total = r, t

    if best_rank == 1 and best_total and best_total > 2:
        standing = f"the highest-rated {kind_label} installer we've tracked in {city}"
    elif best_rank and best_total and best_rank <= max(3, best_total // 3):
        standing = f"one of the top-rated {kind_label} installers in {city}, sitting at #{best_rank} of {best_total} by Google rating"
    elif reviews >= 30:
        standing = f"an established {kind_label} installer in {city} with a substantial local review history"
    elif reviews >= 8:
        standing = f"a {kind_label} installer in {city} with a growing set of local reviews"
    else:
        standing = f"a {kind_label} installer serving {city}, listed here as we build out review history"

    rating_clause = f"currently rated {rating:.1f}★" if rating else "not yet rated on Google"
    return f"{inst['Business Name'].strip()} is {standing}, {rating_clause} from {reviews} review{'s' if reviews != 1 else ''}."


def render_nearby(inst, all_installers, city, city_slug, exclude_slug, cfg):
    """Same-city cross-links. Helps a homeowner comparing options, and gives
    crawlers a path into every page instead of each one being an island only
    reachable from the city index — both a usability and an indexing fix."""
    same_city = [
        i for i in all_installers
        if i["City"].strip().lower() == city.strip().lower()
        and slugify(i["Business Name"]) != exclude_slug
    ]
    if not same_city:
        return ""
    same_city = sorted(same_city, key=lambda r: float(r.get("Google Rating") or 0), reverse=True)[:4]
    items = "".join(
        f'<a href="{cfg["profile_prefix"]}/{city_slug}/{slugify(i["Business Name"])}/" class="ip-nearby-item">'
        f'<span>{escape(i["Business Name"].strip())}</span>'
        f'<span class="ip-nearby-rating">{escape(i.get("Google Rating",""))}★</span></a>'
        for i in same_city
    )
    return f"""
      <section class="ip-nearby">
        <h3>Other {escape(city)} Installers</h3>
        <div class="ip-nearby-list">{items}</div>
      </section>"""


def render_page(inst, rank_info, city_slug, all_installers, cfg):
    name = inst["Business Name"].strip()
    city = inst["City"].strip()
    kinds = sorted(inst["_kinds"])
    phone = (inst.get("Phone") or "").strip()
    website = (inst.get("Website") or "").strip()
    if website and not website.startswith("http"):
        website = "https://" + website
    rating = inst.get("Google Rating") or ""
    reviews = inst.get("Review Count") or ""
    maps_url = (inst.get("Google Maps URL") or "").strip()
    address = (inst.get("Address") or "").strip()
    image_url = (inst.get("Image URL") or "").strip()
    slug = slugify(name)
    region = cfg["region_abbrev"]
    page_url = f"{SITE_URL}{cfg['profile_prefix']}/{city_slug}/{slug}/"

    kind_labels = " & ".join(cfg["rebate_context"][k]["label"] for k in kinds)
    kind_sections = "".join(render_kind_section(k, inst, city_slug, rank_info, cfg) for k in kinds)
    video_section = render_video_section(inst)
    intro = render_intro(inst, kinds, rank_info, city, cfg)
    nearby = render_nearby(inst, all_installers, city, city_slug, slug, cfg)

    local_business = {
        "@type": "LocalBusiness",
        "name": name,
        "image": image_url or None,
        "address": {"@type": "PostalAddress", "streetAddress": address, "addressRegion": region, "addressCountry": "CA"},
        "telephone": phone or None,
        "url": website or None,
        "aggregateRating": ({"@type": "AggregateRating", "ratingValue": rating, "reviewCount": reviews, "bestRating": "5"} if rating else None),
        "areaServed": {"@type": "City", "name": city},
        "priceRange": None,
    }
    local_business = {k: v for k, v in local_business.items() if v}

    breadcrumb = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "HomePowerRebate", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": city, "item": f"{SITE_URL}{cfg['hub_prefix']}/{city_slug}/"},
            {"@type": "ListItem", "position": 3, "name": name, "item": page_url},
        ],
    }

    schema_json = json.dumps({"@context": "https://schema.org", "@graph": [local_business, breadcrumb]}, indent=2)

    website_btn = f'<a href="{website}" target="_blank" rel="noopener" class="ip-btn ip-btn-primary">Visit Website</a>' if website else ""
    phone_btn = f'<a href="tel:{fmt_phone_href(phone)}" class="ip-btn ip-btn-outline">Call {escape(phone)}</a>' if phone else ""
    maps_link = f'<a href="{maps_url}" target="_blank" rel="noopener" class="ip-maps-link">View on Google Maps</a>' if maps_url else ""
    photo_html = f'<img src="{escape(image_url)}" alt="{escape(name)}" class="ip-photo" loading="lazy" width="760" height="380">' if image_url else ""
    meta_desc = f"{escape(name)} in {escape(city)}, {region} — {escape(rating)}★ ({escape(reviews)} reviews). {escape(kind_labels)} installer. See which {region} rebates their work qualifies for and get a quote."
    # Google truncates titles around ~60 characters. Kind label + brand suffix
    # pushed the median well past that, so the title carries only name + city
    # (the two things a searcher actually needs) and everything else — rating,
    # service type, the pitch — moves to the meta description, which has a
    # much larger budget. Long business names will still run past 60 for the
    # title alone; that's unavoidable without truncating the legal name, and
    # is normal for any directory site with real-world business names.
    page_title = f"{escape(name)} — {escape(city)}, {region} | HomePowerRebate"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title}</title>
<meta name="description" content="{meta_desc}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{page_url}">
<meta property="og:type" content="business.business">
<meta property="og:title" content="{escape(name)} — {escape(city)}, {region}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:url" content="{page_url}">
{f'<meta property="og:image" content="{escape(image_url)}">' if image_url else ""}
<meta name="twitter:card" content="{"summary_large_image" if image_url else "summary"}">
<meta name="twitter:title" content="{escape(name)} — {escape(city)}, {region}">
<meta name="twitter:description" content="{meta_desc}">
{f'<meta name="twitter:image" content="{escape(image_url)}">' if image_url else ""}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
<script type="application/ld+json">{schema_json}</script>
<style>
:root {{ --ink:#0a2a2e; --ink-soft:#1a3d42; --paper:#faf7f2; --paper-warm:#f5efe5; --teal:#0d4f5c; --teal-deep:#08363f; --amber:#d4751c; --amber-bright:#e88a2e; --green-money:#2d6a4f; --rule:#d9d0c1; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--paper); color:var(--ink); font-family:'Inter Tight',sans-serif; line-height:1.6; }}
h1,h2,h3 {{ font-family:'Fraunces',Georgia,serif; color:var(--teal-deep); }}
a {{ color:var(--teal-deep); }}
.ip-wrap {{ max-width:760px; margin:0 auto; padding:32px 20px 80px; }}
.ip-breadcrumb {{ font-size:13px; color:#7a7264; margin-bottom:24px; }}
.ip-breadcrumb a {{ color:#7a7264; text-decoration:none; }}
.ip-hero {{ display:flex; justify-content:space-between; align-items:flex-start; gap:20px; flex-wrap:wrap; margin-bottom:8px; }}
.ip-hero h1 {{ font-size:clamp(26px,4vw,36px); margin:0 0 6px; line-height:1.15; }}
.ip-hero-meta {{ color:#5a5348; font-size:15px; }}
.ip-intro {{ font-size:16px; color:#3d3830; margin:18px 0 0; max-width:62ch; }}
.ip-rating {{ text-align:right; }}
.ip-rating-num {{ font-family:'Fraunces',Georgia,serif; font-size:32px; font-weight:700; color:var(--amber); line-height:1; }}
.ip-rating-count {{ font-size:13px; color:#7a7264; }}
.ip-actions {{ display:flex; gap:10px; flex-wrap:wrap; margin:22px 0 8px; }}
.ip-btn {{ padding:12px 22px; border-radius:999px; font-weight:700; font-size:15px; text-decoration:none; display:inline-block; }}
.ip-btn-primary {{ background:var(--amber); color:#fff; }}
.ip-btn-outline {{ background:#fff; color:var(--teal-deep); border:1.5px solid var(--rule); }}
.ip-maps-link {{ font-size:13px; color:#7a7264; text-decoration:underline; align-self:center; }}
.ip-kind {{ margin-top:44px; padding-top:28px; border-top:1px solid var(--rule); }}
.ip-kind-head h2 {{ font-size:22px; margin:0 0 4px; }}
.ip-rank {{ font-size:14px; color:var(--green-money); margin:0 0 18px; }}
.ip-programs {{ display:flex; flex-direction:column; gap:10px; }}
.ip-program {{ display:flex; justify-content:space-between; align-items:center; gap:16px; background:#fff; border:1px solid var(--rule); border-radius:12px; padding:16px 18px; text-decoration:none; }}
.ip-program-name {{ font-weight:700; color:var(--teal-deep); font-size:15px; }}
.ip-program-detail {{ font-size:13.5px; color:#5a5348; margin-top:2px; }}
.ip-program-arrow {{ color:var(--amber); font-size:18px; flex-shrink:0; }}
.ip-guide-link {{ display:inline-block; margin-top:16px; font-weight:700; color:var(--amber); text-decoration:none; font-size:14.5px; }}
.ip-vetting {{ margin-top:44px; background:var(--paper-warm); border-radius:14px; padding:24px; }}
.ip-vetting h3 {{ font-size:18px; margin:0 0 14px; }}
.ip-vet-row {{ display:flex; gap:12px; align-items:flex-start; padding:10px 0; border-top:1px solid var(--rule); font-size:14.5px; }}
.ip-vet-row:first-of-type {{ border-top:none; }}
.ip-vet-icon {{ width:22px; height:22px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px; flex-shrink:0; }}
.ip-vet-yes .ip-vet-icon {{ background:var(--green-money); color:#fff; }}
.ip-vet-no .ip-vet-icon {{ background:var(--rule); color:#5a5348; }}
.ip-vet-detail {{ color:#5a5348; font-size:13.5px; }}
.ip-vet-note {{ font-size:13px; color:#7a7264; margin:16px 0 0; line-height:1.5; }}
.ip-video {{ margin-top:44px; }}
.ip-video-embed {{ position:relative; padding-top:56.25%; border-radius:14px; overflow:hidden; background:#000; }}
.ip-video-embed iframe {{ position:absolute; inset:0; width:100%; height:100%; border:0; }}
.ip-quote {{ margin-top:52px; background:var(--teal-deep); border-radius:16px; padding:32px 28px; color:var(--paper); }}
.ip-quote h2 {{ color:#fff; font-size:22px; margin:0 0 8px; }}
.ip-quote p {{ color:#c9d8d5; font-size:14.5px; margin:0 0 20px; }}
.ip-quote-form {{ display:flex; flex-direction:column; gap:10px; max-width:380px; }}
.ip-quote-form input {{ padding:13px 14px; border-radius:9px; border:1.5px solid transparent; font-family:'Inter Tight',sans-serif; font-size:15px; }}
.ip-quote-form button {{ padding:13px; background:var(--amber); color:#fff; border:none; border-radius:999px; font-weight:700; font-size:15.5px; cursor:pointer; }}
.ip-quote-done {{ display:none; color:var(--amber-bright); font-weight:700; }}
.ip-photo {{ width:100%; height:auto; aspect-ratio:2/1; object-fit:cover; border-radius:14px; margin:18px 0 0; }}
.ip-nearby {{ margin-top:44px; }}
.ip-nearby h3 {{ font-size:17px; margin:0 0 12px; }}
.ip-nearby-list {{ display:flex; flex-direction:column; gap:8px; }}
.ip-nearby-item {{ display:flex; justify-content:space-between; padding:12px 16px; background:#fff; border:1px solid var(--rule); border-radius:10px; text-decoration:none; color:var(--teal-deep); font-size:14px; font-weight:600; }}
.ip-nearby-rating {{ color:var(--amber); }}
.ip-city-link {{ display:block; margin-top:36px; text-align:center; font-size:14.5px; }}
.ip-footer-note {{ margin-top:60px; font-size:12.5px; color:#9a9385; border-top:1px solid var(--rule); padding-top:20px; }}
</style>
</head>
<body>
<div class="ip-wrap">
  <p class="ip-breadcrumb"><a href="/">HomePowerRebate</a> / <a href="{cfg['hub_prefix']}/{city_slug}/">{escape(city)}</a> / {escape(name)}</p>

  <div class="ip-hero">
    <div>
      <h1>{escape(name)}</h1>
      <p class="ip-hero-meta">{escape(kind_labels)} installer &middot; {escape(city)}, {region}</p>
    </div>
    {f'<div class="ip-rating"><div class="ip-rating-num">{escape(rating)}★</div><div class="ip-rating-count">{escape(reviews)} reviews</div></div>' if rating else ''}
  </div>

  {photo_html}

  <p class="ip-intro">{escape(intro)}</p>

  <div class="ip-actions">
    {website_btn}
    {phone_btn}
    {maps_link}
  </div>

  {kind_sections}
  {render_vetting_card(inst, cfg)}
  {video_section}
  {nearby}

  <section class="ip-quote">
    <h2>Get a Quote From {escape(name)}</h2>
    <p>We'll pass your details along and follow up with your {region} rebate breakdown.</p>
    <form class="ip-quote-form" id="ip-quote-form">
      <input type="text" id="ip-name" placeholder="First name" required>
      <input type="email" id="ip-email" placeholder="your@email.com" required>
      <input type="tel" id="ip-phone" placeholder="Phone number" required>
      <input type="text" id="ip-hp" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px;" aria-hidden="true">
      <button type="submit" id="ip-quote-btn">Request a Quote &rarr;</button>
    </form>
    <p class="ip-quote-done" id="ip-quote-done">✓ Sent — {escape(name)} will be in touch.</p>
  </section>

  <a href="{cfg['hub_prefix']}/{city_slug}/" class="ip-city-link">See all {escape(city)} rebates &rarr;</a>

  <p class="ip-footer-note">Business details sourced from Google Business Profile, last checked {escape(inst.get("Last Updated",""))}. Spot an error? <a href="mailto:samuelmenard@gmail.com?subject=Correction: {escape(name)}">Let us know</a>.</p>
</div>
<script>
(function() {{
  var form = document.getElementById('ip-quote-form');
  form.addEventListener('submit', function(e) {{
    e.preventDefault();
    if (document.getElementById('ip-hp').value) return;
    var btn = document.getElementById('ip-quote-btn');
    btn.disabled = true; btn.textContent = 'Sending…';
    fetch('{LEADS_ENDPOINT}/estimate-lead', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{
        firstname: document.getElementById('ip-name').value,
        email: document.getElementById('ip-email').value,
        phone: document.getElementById('ip-phone').value,
        city: {json.dumps(city)},
        source: 'installer-{slug}',
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


def run_province(prov_key, args, emails):
    cfg = PROVINCE_CONFIG[prov_key]
    city_slugs = cfg["city_slugs"]

    rows = load_rows(cfg["heat_pump_csv"], "heat-pump") + load_rows(cfg["solar_csv"], "solar")
    if not rows:
        print(f"\n[{prov_key}] no CSV data found ({cfg['heat_pump_csv']} / {cfg['solar_csv']} missing or empty) — skipping")
        return 0, 0, []

    installers = merge_and_dedupe(rows)
    rank_info = rank_within_city(installers)

    written, skipped = 0, 0
    url_rows = []
    out_dir = OUT_DIR if prov_key == "bc" else OUT_DIR / "on"
    # City-scoped paths (/installers/profiles/{city}/{business}/, or
    # /installers/profiles/on/{city}/{business}/ for Ontario) rather than a
    # flat /profiles/{business}/ — a handful of businesses share a name across
    # branches in different cities, which under a flat structure silently
    # overwrote all but one. Scoping by city also reads better for local SEO.
    for inst in installers:
        city_slug = city_slugs.get(normalize_city(inst["City"]))
        if not city_slug:
            skipped += 1
            print(f"  SKIP (unknown city): {inst['Business Name']} / {inst['City']}")
            continue

        slug = slugify(inst["Business Name"])
        page_dir = out_dir / city_slug / slug
        html = render_page(inst, rank_info, city_slug, installers, cfg)

        if not args.dry_run:
            page_dir.mkdir(parents=True, exist_ok=True)
            (page_dir / "index.html").write_text(html)
        written += 1

        email = emails.get((inst["Business Name"].strip().lower(), inst["City"].strip().lower()), "")
        url_rows.append({
            "Province": cfg["region_abbrev"],
            "Business Name": inst["Business Name"].strip(),
            "City": inst["City"].strip(),
            "Email": email,
            "Phone": inst.get("Phone", ""),
            "Google Rating": inst.get("Google Rating", ""),
            "Profile URL": f"{SITE_URL}{cfg['profile_prefix']}/{city_slug}/{slug}/",
            "Last Updated": inst.get("Last Updated", ""),
        })

    if not args.dry_run and url_rows:
        # Generate per-city JSON files for the carousel to consume. Each city
        # gets its own file with all installers in that city, sorted by rating.
        json_dir = INSTALLERS_DIR / cfg["json_dir"]
        json_dir.mkdir(parents=True, exist_ok=True)

        by_city = defaultdict(list)
        for inst in installers:
            city_slug = city_slugs.get(normalize_city(inst["City"]))
            if not city_slug:
                continue
            slug = slugify(inst["Business Name"])
            by_city[city_slug].append({
                "name": inst["Business Name"].strip(),
                "rating": float(inst.get("Google Rating") or 0),
                "reviews": int(inst.get("Review Count") or 0),
                "location": inst["City"].strip(),
                "phone": inst.get("Phone", ""),
                "website": inst.get("Website", ""),
                "image_url": inst.get("Image URL", ""),
                "specialty": " & ".join(cfg["rebate_context"][k]["label"] for k in sorted(inst["_kinds"])),
                "description": f"HPCN-certified. {int(inst.get('Review Count') or 0)} reviews on Google.",
                "profileUrl": f"{SITE_URL}{cfg['profile_prefix']}/{city_slug}/{slug}/",
                "recommended": False
            })

        for city_slug, installers_in_city in by_city.items():
            installers_in_city.sort(key=lambda x: (x["rating"], x["reviews"]), reverse=True)
            json_file = json_dir / f"{city_slug}.json"
            json_file.write_text(json.dumps(installers_in_city, indent=2))

    print(f"[{prov_key}] {written} profile page(s) {'would be ' if args.dry_run else ''}written to {out_dir.relative_to(ROOT)}/")
    if skipped:
        print(f"[{prov_key}] {skipped} skipped (city not in city_slugs map)")

    return written, skipped, url_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--province", choices=["bc", "on", "all"], default="all")
    args = ap.parse_args()

    emails = load_emails()
    provinces = ["bc", "on"] if args.province == "all" else [args.province]

    total_written, total_skipped, all_url_rows = 0, 0, []
    for prov_key in provinces:
        w, s, rows = run_province(prov_key, args, emails)
        total_written += w
        total_skipped += s
        all_url_rows.extend(rows)

    if not args.dry_run and all_url_rows:
        with (INSTALLERS_DIR / "installer-profile-urls.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(all_url_rows[0].keys()))
            w.writeheader()
            w.writerows(all_url_rows)

    print(f"\n{total_written} profile page(s) total {'would be ' if args.dry_run else ''}written")
    if total_skipped:
        print(f"{total_skipped} total skipped (city not in city_slugs map)")
    with_email = sum(1 for r in all_url_rows if r["Email"])
    print(f"{with_email} of {total_written} have a recovered email for outreach")
    if not args.dry_run:
        print(f"Mail-merge source written: installers/installer-profile-urls.csv (province, business, city, email, profile URL)")


if __name__ == "__main__":
    main()
