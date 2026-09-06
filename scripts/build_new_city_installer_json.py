#!/usr/bin/env python3
"""
Build installer JSON for the 10 newly-added cities in the SAME format the
site's carousel actually fetches (installers/json/{region}/{city}.json for
heat-pump, installers/json/{region}/solar/{city}.json for solar) — matching
generate_installer_json_from_real.py's schema exactly, but scoped to only
these cities so no existing city's file is touched.
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JOBS = [
    ("installers/on-heat-pump-installers-real.csv", "installers/json/on",
     "Heat Pump & HVAC Installation",
     "Local heating & cooling pro serving {city}. {rating}★ from {reviews} Google reviews.",
     {"Guelph", "Kingston", "Niagara Falls", "Peterborough", "Sault Ste. Marie", "Thunder Bay", "Timmins"}),
    ("installers/on-solar-installers-real.csv", "installers/json/on/solar",
     "Solar Installation",
     "Local solar installer serving {city}. {rating}★ from {reviews} Google reviews.",
     {"Guelph", "Kingston", "Niagara Falls", "Peterborough", "Sault Ste. Marie", "Thunder Bay", "Timmins"}),
    ("installers/ab-heat-pump-installers-real.csv", "installers/json/ab",
     "Heat Pump & HVAC Installation",
     "Local heating & cooling pro serving {city}. {rating}★ from {reviews} Google reviews.",
     {"Fort McMurray"}),
    ("installers/ab-solar-installers-real.csv", "installers/json/ab/solar",
     "Solar Installation",
     "Local solar installer serving {city}. {rating}★ from {reviews} Google reviews.",
     {"Fort McMurray"}),
    ("installers/ns-heat-pump-installers-real.csv", "installers/json/ns",
     "Heat Pump & HVAC Installation",
     "Local heating & cooling pro serving {city}. {rating}★ from {reviews} Google reviews.",
     {"Cape Breton"}),
    ("installers/ns-solar-installers-real.csv", "installers/json/ns/solar",
     "Solar Installation",
     "Local solar installer serving {city}. {rating}★ from {reviews} Google reviews.",
     {"Cape Breton"}),
    ("installers/ma-heat-pump-installers-real.csv", "installers/json/ma",
     "Heat Pump & HVAC Installation",
     "Local heating & cooling pro serving {city}. {rating}★ from {reviews} Google reviews.",
     {"Lawrence"}),
    ("installers/ma-solar-installers-real.csv", "installers/json/ma/solar",
     "Solar Installation",
     "Local solar installer serving {city}. {rating}★ from {reviews} Google reviews.",
     {"Lawrence"}),
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


for csv_rel, out_dir_rel, specialty, desc_tpl, target_cities in JOBS:
    csv_path = os.path.join(ROOT, csv_rel)
    out_dir = os.path.join(ROOT, out_dir_rel)
    if not os.path.exists(csv_path):
        print(f"skip (missing): {csv_rel}")
        continue

    by_city = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            city = (row.get("City") or "").strip()
            if city not in target_cities:
                continue
            name = (row.get("Business Name") or "").strip()
            if not name:
                continue
            rating = to_float(row.get("Google Rating"))
            reviews = to_int(row.get("Review Count"))
            by_city.setdefault(city, []).append({
                "name": name,
                "location": (row.get("Address") or "").strip(),
                "phone": (row.get("Phone") or "").strip(),
                "email": (row.get("Email") or "").strip(),
                "website": (row.get("Website") or "").strip(),
                "rating": rating,
                "reviews": reviews,
                "gmaps_url": (row.get("Google Maps URL") or "").strip(),
                "recommended": (row.get("HomePowerRebate Recommended") or "").strip().lower() == "yes",
                "specialty": specialty,
                "description": desc_tpl.format(city=city, rating=rating, reviews=reviews),
                "image_url": (row.get("Image URL") or "").strip(),
            })

    os.makedirs(out_dir, exist_ok=True)
    for city, installers in by_city.items():
        installers.sort(key=lambda x: (-x["recommended"], -x["rating"], -x["reviews"]))
        out_path = os.path.join(out_dir, f"{city_slug(city)}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(installers, f, indent=2)
        print(f"  wrote {len(installers)} -> {os.path.relpath(out_path, ROOT)}")

print("done")
