#!/usr/bin/env python3
"""
Convert the REAL installer CSVs (from scrape_google_places_installers.py) into
the per-city JSON files the carousel loads.

Reads:
  installers/heat-pump-installers-real.csv  -> installers/json/{city}.json
  installers/solar-installers-real.csv       -> installers/json/solar/{city}.json

Run from the Powerrebate root:
  python3 scripts/generate_installer_json_from_real.py
"""

import csv
import json
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JOBS = [
    {
        "csv": os.path.join(ROOT, "installers/heat-pump-installers-real.csv"),
        "out_dir": os.path.join(ROOT, "installers/json"),
        "specialty": "Heat Pump & HVAC Installation",
        "description_tpl": "Local heating & cooling pro serving {city}. {rating}★ from {reviews} Google reviews.",
    },
    {
        "csv": os.path.join(ROOT, "installers/solar-installers-real.csv"),
        "out_dir": os.path.join(ROOT, "installers/json/solar"),
        "specialty": "Solar Installation",
        "description_tpl": "Local solar installer serving {city}. {rating}★ from {reviews} Google reviews.",
    },
    # Ontario — separate CSVs (scrape_google_places_installers.py --province=on)
    # and a province-prefixed output dir, so these never collide with BC's files.
    {
        "csv": os.path.join(ROOT, "installers/on-heat-pump-installers-real.csv"),
        "out_dir": os.path.join(ROOT, "installers/json/on"),
        "specialty": "Heat Pump & HVAC Installation",
        "description_tpl": "Local heating & cooling pro serving {city}. {rating}★ from {reviews} Google reviews.",
    },
    {
        "csv": os.path.join(ROOT, "installers/on-solar-installers-real.csv"),
        "out_dir": os.path.join(ROOT, "installers/json/on/solar"),
        "specialty": "Solar Installation",
        "description_tpl": "Local solar installer serving {city}. {rating}★ from {reviews} Google reviews.",
    },
]


def city_slug(city):
    return city.lower().replace(" ", "-").replace(".", "")


def to_float(v, default=0.0):
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def to_int(v, default=0):
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return default


def build(job):
    if not os.path.exists(job["csv"]):
        print(f"⚠️  Skipping — CSV not found: {os.path.basename(job['csv'])}")
        return 0

    by_city = defaultdict(list)
    with open(job["csv"], "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            city = (row.get("City") or "").strip()
            name = (row.get("Business Name") or "").strip()
            if not city or not name:
                continue

            rating = to_float(row.get("Google Rating"))
            reviews = to_int(row.get("Review Count"))

            by_city[city].append({
                "name": name,
                "location": (row.get("Address") or "").strip(),
                "phone": (row.get("Phone") or "").strip(),
                "email": (row.get("Email") or "").strip(),
                "website": (row.get("Website") or "").strip(),
                "rating": rating,
                "reviews": reviews,
                "gmaps_url": (row.get("Google Maps URL") or "").strip(),
                "recommended": (row.get("HomePowerRebate Recommended") or "").strip().lower() == "yes",
                "specialty": job["specialty"],
                "description": job["description_tpl"].format(city=city, rating=rating, reviews=reviews),
                "image_url": (row.get("Image URL") or "").strip(),
            })

    os.makedirs(job["out_dir"], exist_ok=True)
    total = 0
    for city, installers in by_city.items():
        installers.sort(key=lambda x: (-x["recommended"], -x["rating"], -x["reviews"]))
        out_path = os.path.join(job["out_dir"], f"{city_slug(city)}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(installers, f, indent=2)
        total += len(installers)
        print(f"  ✓ {city}: {len(installers)} → {os.path.relpath(out_path, ROOT)}")

    return total


if __name__ == "__main__":
    grand = 0
    for job in JOBS:
        print(f"\n📂 {os.path.basename(job['csv'])}")
        grand += build(job)
    print(f"\n✅ Wrote {grand} installers across all city JSON files")
