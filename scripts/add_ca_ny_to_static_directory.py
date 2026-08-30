#!/usr/bin/env python3
"""
Add CA and NY sections to installers/index.html's "Every Installer, By City"
block — the static, server-rendered, crawlable fallback content that backs
up the page's JS-driven interactive directory tool (found missing entirely
for CA/NY on 2026-08-30, same bug class as the REGIONS jsonBase/profileBase
mismatch fixed in the same session — the intro text already claimed CA/NY
coverage, but no city sections existed).

Reads installers/json/ca/{,solar/}*.json and installers/json/ny/{,solar/}*.json
(merging + deduping heat-pump and solar listings per city, same as the
interactive tool's own loadInstallers() logic), and inserts one .directory-city
block per city, matching the exact markup already used for every other region.

Run from the Powerrebate root:
  python3 scripts/add_ca_ny_to_static_directory.py
"""
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(ROOT, "installers/index.html")

REGIONS = [
    ("ca", "us/ca", [
        ("berkeley", "Berkeley", "bay-area"), ("fremont", "Fremont", "bay-area"),
        ("oakland", "Oakland", "bay-area"), ("san-francisco", "San Francisco", "bay-area"),
        ("san-jose", "San Jose", "bay-area"),
        ("burbank", "Burbank", "los-angeles"), ("glendale", "Glendale", "los-angeles"),
        ("long-beach", "Long Beach", "los-angeles"), ("los-angeles", "Los Angeles", "los-angeles"),
        ("pasadena", "Pasadena", "los-angeles"), ("santa-monica", "Santa Monica", "los-angeles"),
        ("folsom", "Folsom", "sacramento"), ("rancho-cordova", "Rancho Cordova", "sacramento"),
        ("roseville", "Roseville", "sacramento"), ("sacramento", "Sacramento", "sacramento"),
        ("chula-vista", "Chula Vista", "san-diego"), ("escondido", "Escondido", "san-diego"),
        ("san-diego", "San Diego", "san-diego"),
        ("moreno-valley", "Moreno Valley", "inland-empire"), ("ontario", "Ontario", "inland-empire"),
        ("riverside", "Riverside", "inland-empire"), ("san-bernardino", "San Bernardino", "inland-empire"),
    ]),
    ("ny", "us/ny", [
        ("beacon", "Beacon", "central-hudson"), ("kingston", "Kingston", "central-hudson"),
        ("newburgh", "Newburgh", "central-hudson"), ("poughkeepsie", "Poughkeepsie", "central-hudson"),
        ("saugerties", "Saugerties", "central-hudson"),
        ("mount-vernon", "Mount Vernon", "con-edison"), ("new-rochelle", "New Rochelle", "con-edison"),
        ("new-york-city", "New York City", "con-edison"), ("white-plains", "White Plains", "con-edison"),
        ("yonkers", "Yonkers", "con-edison"),
        ("albany", "Albany", "national-grid"), ("buffalo", "Buffalo", "national-grid"),
        ("rochester", "Rochester", "national-grid"), ("syracuse", "Syracuse", "national-grid"),
        ("babylon", "Babylon", "pseg"), ("brookhaven", "Brookhaven", "pseg"),
        ("huntington", "Huntington", "pseg"), ("islip", "Islip", "pseg"),
        ("oyster-bay", "Oyster Bay", "pseg"), ("smithtown", "Smithtown", "pseg"),
        ("southampton", "Southampton", "pseg"),
    ]),
]

# CA uses region-group hub URLs (/us/ca/<group>/<city>/), NY uses utility hub
# URLs (/us/ny/<utility>/<city>/) — matches city_hub_url() in
# generate_installer_profiles.py.
CA_GROUP = {c: g for c, _, g in REGIONS[0][2]}
NY_UTILITY = {c: g for c, _, g in REGIONS[1][2]}


def hub_url(region_code, city_slug):
    if region_code == "ca":
        return f"/us/ca/{CA_GROUP[city_slug]}/{city_slug}"
    else:
        return f"/us/ny/{NY_UTILITY[city_slug]}/{city_slug}"


def load_city_installers(region_code, city_slug):
    base = os.path.join(ROOT, "installers/json", region_code)
    merged = {}
    for sub in ["", "solar"]:
        path = os.path.join(base, sub, f"{city_slug}.json") if sub else os.path.join(base, f"{city_slug}.json")
        if os.path.exists(path):
            for inst in json.load(open(path, encoding="utf-8")):
                merged[inst["name"]] = inst  # dedupe by name
    return sorted(merged.values(), key=lambda x: x["name"])


def slugify(name):
    import re
    s = name.lower().strip()
    s = re.sub(r"[&']", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def build_city_block(region_code, city_slug, display_name):
    installers = load_city_installers(region_code, city_slug)
    if not installers:
        return "", 0
    items = "\n".join(
        f'        <li><a href="/installers/profiles/{region_code}/{city_slug}/{slugify(i["name"])}/">{html.escape(i["name"])}</a></li>'
        for i in installers
    )
    block = f'''      <div class="directory-city">
        <h3 style="font-family:'Fraunces',serif; font-size:18px; color:var(--teal-deep); margin:20px 0 8px;"><a href="{hub_url(region_code, city_slug)}" style="color:var(--teal-deep);">{display_name}</a></h3>
        <ul style="columns:2; column-gap:24px; list-style:none; padding:0; margin:0; font-size:14px; line-height:1.9;">
{items}
        </ul>
      </div>'''
    return block, len(installers)


def main():
    text = open(INDEX_PATH, encoding="utf-8").read()

    anchor = '''      <div class="directory-city">
        <h3 style="font-family:'Fraunces',serif; font-size:18px; color:var(--teal-deep); margin:20px 0 8px;"><a href="/us/vt/montpelier" style="color:var(--teal-deep);">Montpelier</a></h3>
        <ul style="columns:2; column-gap:24px; list-style:none; padding:0; margin:0; font-size:14px; line-height:1.9;">
        <li><a href="/installers/profiles/vt/montpelier/lloyd-plumbing-heating-air-electrical/">Lloyd Plumbing Heating Air Electrical</a></li>
        <li><a href="/installers/profiles/vt/montpelier/techno-metal-post-vermont/">Techno Metal Post Vermont</a></li>
        </ul>
      </div>'''
    assert anchor in text, "template drifted — Montpelier block not found verbatim, check installers/index.html structure"

    if "us/ca/bay-area/berkeley" in text or 'profiles/ca/' in text:
        print("CA/NY sections already present — skipping (run not idempotent by design, avoid duplicate blocks).")
        return

    new_blocks = []
    total_new = 0
    for region_code, _, cities in REGIONS:
        for city_slug, display_name, _group in cities:
            block, n = build_city_block(region_code, city_slug, display_name)
            if block:
                new_blocks.append(block)
                total_new += n

    insertion = "\n" + "\n".join(new_blocks)
    text = text.replace(anchor, anchor + insertion)

    # Fix the stale "660+" claim in the section intro to the real current total.
    existing_count = text.count('<li><a href="/installers/profiles/') - 0  # already includes new ones now
    text = text.replace(
        "A complete, static list of all 660+ installer profiles",
        f"A complete, static list of all {existing_count}+ installer profiles",
    )

    open(INDEX_PATH, "w", encoding="utf-8").write(text)
    print(f"Added {total_new} installers across {len(new_blocks)} cities (CA + NY).")
    print(f"Total static profile links now: {existing_count}")


if __name__ == "__main__":
    main()
