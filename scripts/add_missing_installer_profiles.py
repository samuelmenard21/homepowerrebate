#!/usr/bin/env python3
"""Create a profile page for every installer on a ranking page that has none (never overwrites an existing profile).

Rows come from installers/*-installers-real.csv (the same data the ranking pages use), so every ranked company, in every service,
gets a profile. Profiles stay noindex (see generate_installer_profiles.render_profile). Run before build_installer_rankings.py.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_installer_rankings as br
import generate_installer_profiles as gp

SPECIALTY = {"heat-pump": "Heat Pump & HVAC Installation", "solar": "Solar Installation",
             "insulation": "Insulation", "battery": "Home Battery Installation"}


def main():
    by_city = {}
    for r in br.load_rows():
        by_city.setdefault((r["region"], br.slugify(r["city"])), {}).setdefault(r["service"], []).append(r)
    made = skipped = 0
    for (region, city_slug), svcs in sorted(by_city.items()):
        if region not in gp.REGIONS:
            continue
        cfg = gp.REGIONS[region]
        by_cat = {}
        for svc, rs in svcs.items():
            by_cat[svc] = [{
                "name": r["name"], "location": r["address"], "phone": r["phone"], "email": r["email"],
                "website": r["website"], "rating": r["rating"], "reviews": r["reviews"], "gmaps_url": r["gmaps"],
                "recommended": False, "specialty": SPECIALTY[svc],
                "description": f'Local pro serving {gp.city_display_name(city_slug)}. {r["rating"]:.1f}★ from {r["reviews"]:,} Google reviews.',
                "image_url": "",
            } for r in sorted(rs, key=br.score, reverse=True)]
        by_slug = {}
        for svc, insts in by_cat.items():
            for idx, inst in enumerate(insts):
                by_slug.setdefault(gp.slugify(inst["name"]), []).append((inst, svc, idx + 1, len(insts)))
        for slug, listings in by_slug.items():
            name = listings[0][0]["name"]
            out_dir = os.path.join(cfg["profiles_dir"], city_slug, slug)
            out_path = os.path.join(out_dir, "index.html")
            if os.path.exists(out_path) or br.profile_url(region, city_slug, name):
                skipped += 1
                continue
            os.makedirs(out_dir, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(gp.render_profile(region, city_slug, listings, by_cat))
            made += 1
    print(f"created {made} profile pages, {skipped} already existed")


if __name__ == "__main__":
    main()
