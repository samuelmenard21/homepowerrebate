#!/usr/bin/env python3
"""
Add a "Local Installers" section to NY city pages — every other region on the
site (BC/AB/MA/CA) shows installer cards on its city/category pages, but NY's
20 city pages had none at all (found 2026-08-30 while wiring up the new NY
installer data — user flagged the inconsistency directly).

NY city pages have wildly inconsistent internal templates (different h2
headings present/absent per page — same issue hit when adding the payback-
math section earlier today), so this uses the same reliable anchor: insert
as a standalone section right before <footer>, which is universal across all
20 files.

Reads installers/json/ny/{,solar/}<city>.json (merged + deduped, same as the
/installers/ directory's own logic), shows up to 4 heat-pump + up to 4 solar
installers (labeled), links to the full profile pages.

Run from the Powerrebate root:
  python3 scripts/add_ny_installer_cards.py
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CITIES = {
    "mount-vernon": ("Mount Vernon", "con-edison"),
    "new-rochelle": ("New Rochelle", "con-edison"),
    "new-york-city": ("New York City", "con-edison"),
    "white-plains": ("White Plains", "con-edison"),
    "yonkers": ("Yonkers", "con-edison"),
    "babylon": ("Babylon", "pseg"),
    "brookhaven": ("Brookhaven", "pseg"),
    "huntington": ("Huntington", "pseg"),
    "islip": ("Islip", "pseg"),
    "oyster-bay": ("Oyster Bay", "pseg"),
    "smithtown": ("Smithtown", "pseg"),
    "southampton": ("Southampton", "pseg"),
    "albany": ("Albany", "national-grid"),
    "buffalo": ("Buffalo", "national-grid"),
    "rochester": ("Rochester", "national-grid"),
    "syracuse": ("Syracuse", "national-grid"),
    "beacon": ("Beacon", "central-hudson"),
    "kingston": ("Kingston", "central-hudson"),
    "newburgh": ("Newburgh", "central-hudson"),
    "poughkeepsie": ("Poughkeepsie", "central-hudson"),
    "saugerties": ("Saugerties", "central-hudson"),
}


def slugify(name):
    s = name.lower().strip()
    s = re.sub(r"[&']", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def load(city_slug, sub):
    path = os.path.join(ROOT, "installers/json/ny", sub, f"{city_slug}.json") if sub else os.path.join(ROOT, "installers/json/ny", f"{city_slug}.json")
    if not os.path.exists(path):
        return []
    data = json.load(open(path, encoding="utf-8"))
    return sorted(data, key=lambda x: (-x.get("recommended", False), -x["rating"], -x["reviews"]))[:4]


def card(inst, city_slug, label):
    name = html.escape(inst["name"])
    rating = inst["rating"]
    reviews = inst["reviews"]
    slug = slugify(inst["name"])
    return (
        f'      <a href="/installers/profiles/ny/{city_slug}/{slug}/" class="installer-card" style="display:block; text-decoration:none;">\n'
        f'        <div><div class="name">{name}</div><div class="stars">&#9733; {rating:.1f} ({reviews} reviews) &middot; {label}</div></div>\n'
        f'      </a>'
    )


def build_section(city_slug, display_name):
    hp = load(city_slug, "")
    solar = load(city_slug, "solar")
    if not hp and not solar:
        return None

    cards = [card(i, city_slug, "Heat Pump") for i in hp] + [card(i, city_slug, "Solar") for i in solar]
    return f'''<section class="wrap" style="padding:0 28px 32px;">
  <h2 style="font-family:'Fraunces',Georgia,serif; font-size:24px; color:var(--teal-deep,#08363f); margin:0 0 12px;">Local Installers in {display_name}</h2>
  <p style="font-size:15px; color:var(--ink-soft,#1a3d42); margin-bottom:14px;">Real, currently-reviewed installers serving {display_name}, pulled from Google reviews. We're not paid to list anyone here.</p>
  <div style="display:flex; flex-direction:column; gap:10px;">
{chr(10).join(cards)}
  </div>
  <p style="margin-top:12px; font-size:14px;"><a href="/installers/">See all {display_name} installers &rarr;</a></p>
</section>

'''


def main():
    updated = 0
    for city_slug, (display_name, utility) in CITIES.items():
        page_path = os.path.join(ROOT, "us/ny", utility, city_slug, "index.html")
        if not os.path.exists(page_path):
            print(f"  SKIP {city_slug}: page not found at {page_path}")
            continue
        text = open(page_path, encoding="utf-8").read()
        if "Local Installers in" in text:
            print(f"  SKIP {city_slug}: already has an installer section")
            continue
        section = build_section(city_slug, display_name)
        if section is None:
            print(f"  SKIP {city_slug}: no installer data")
            continue
        idx = text.find("<footer")
        if idx == -1:
            print(f"  SKIP {city_slug}: no <footer> anchor found")
            continue
        new_text = text[:idx] + section + text[idx:]
        open(page_path, "w", encoding="utf-8").write(new_text)
        print(f"  OK {city_slug}")
        updated += 1
    print(f"\nUpdated {updated}/{len(CITIES)} NY city pages")


if __name__ == "__main__":
    main()
