#!/usr/bin/env python3
"""
Layer 1 of the category-page-localization playbook (see
.claude/skills/hpr-category-page-localization/SKILL.md): inject a real,
already-verified per-city utility name into every city x category page,
sitewide, in every region where utilities actually differ by city.

Zero new research — city-rebate-lookup.json already has a verified
`utility` field per city from each city's onboarding research. This script
only surfaces it. BC is skipped: every BC city in the lookup maps to the
same utility (BC Hydro), so the section wouldn't distinguish anything —
BC's differentiation comes from Layer 2 (climate data) instead.

Anchor: every one of the 1,127 category pages ends with an <h2>Next
steps</h2> section (verified — the one heading present on 100% of them,
even though earlier headings vary a lot by category/region/vintage). The
new section is inserted immediately before that, so it works regardless
of what template variant the rest of the page uses.

Usage:
    python3 scripts/apply_layer1_utility_data.py --dry-run   # report only
    python3 scripts/apply_layer1_utility_data.py             # apply
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOOKUP = json.loads((ROOT / "city-rebate-lookup.json").read_text())

CATEGORY_DIRS = {
    "heat-pump", "solar", "battery", "water-heater", "insulation",
    "windows", "windows-doors", "ev-charger", "smart-thermostats", "hrv",
    "appliances",
}

# ca/<region> and us/<region> path segments -> lookup key prefix + "province"/"state" wording
CA_REGIONS = {"bc", "on", "ab", "ns"}
US_REGIONS = {"ca", "ny", "ma", "pa", "co", "vt"}

NEXT_STEPS_RE = re.compile(r'(\s*<h2>Next steps</h2>)')

CATEGORY_LABELS = {
    "heat-pump": "heat pump", "solar": "solar", "battery": "battery storage",
    "water-heater": "water heater", "insulation": "insulation",
    "windows": "windows and doors", "windows-doors": "windows and doors",
    "ev-charger": "EV charger", "smart-thermostats": "smart thermostat",
    "hrv": "HRV", "appliances": "appliance",
}


def category_kind(cat_dir):
    if cat_dir == "solar":
        return "net_metering"
    if cat_dir == "battery":
        return "battery"
    if cat_dir == "ev-charger":
        return "ev"
    return "capacity_billing"


def build_section(utility, city, cat_dir, area_word):
    label = CATEGORY_LABELS.get(cat_dir, cat_dir)
    kind = category_kind(cat_dir)

    if kind == "net_metering":
        body = (
            f"{utility} is the local electric utility for {city}, and it's the "
            f"utility that actually credits you for solar power your system sends "
            f"back to the grid. The {label} rebate above is a {area_word}-wide "
            f"program and doesn't depend on which utility serves you — but net "
            f"metering terms (how much you're credited, how credits carry over) "
            f"are set by {utility}, not the {area_word}. Ask {utility} directly "
            f"about their current net metering terms before you sign anything."
        )
    elif kind == "battery":
        body = (
            f"{utility} is the local electric utility for {city}. The {label} "
            f"rebate above is a {area_word}-wide program, so which utility bills "
            f"you doesn't change what you qualify for — but {utility} is who to "
            f"ask about backup-power or peak-demand programs a battery might make "
            f"you eligible for, and who handles interconnection paperwork if your "
            f"battery is paired with solar."
        )
    elif kind == "ev":
        body = (
            f"{utility} is the local electric utility for {city}. The {label} "
            f"rebate above is a {area_word}-wide program, so which utility bills "
            f"you doesn't change what you qualify for — but {utility} is who to "
            f"ask about time-of-use or EV-specific electricity rates, since "
            f"charging overnight on the right rate plan can meaningfully change "
            f"your running cost. Some utilities also run their own home-charger "
            f"incentive on top of the {area_word} one — worth a quick call to "
            f"{utility} to check."
        )
    else:
        body = (
            f"{utility} is the local electric utility for {city}. The {label} "
            f"rebate above comes from a {area_word}-wide program, so which "
            f"utility bills you doesn't change what you qualify for. Where it can "
            f"matter: {utility} is who to contact about your home's electrical "
            f"service capacity if your installer flags an upgrade, and who bills "
            f"the electricity your new equipment uses once it's running. Some "
            f"utilities layer their own incentive on top of the {area_word} "
            f"rebate — worth a quick call to {utility} to ask directly."
        )

    return f'\n    <h2>Your utility: {utility}</h2>\n    <p>{body}</p>\n'


# Some regions (e.g. NY) organize city directories under a utility-named
# parent directory (us/ny/con-edison/mount-vernon/...). If a city is
# missing from city-rebate-lookup.json but sits under one of these, that
# directory name IS the utility — already part of the site's own
# information architecture, not a guess.
UTILITY_DIR_NAMES = {
    "con-edison": "Con Edison",
    "pseg": "PSEG Long Island",
    "national-grid": "National Grid",
    "central-hudson": "Central Hudson",
}


def find_utility(region_code, city_slug, utility_parent_dir=None):
    city_key = city_slug.replace("-", " ")
    key = f"{region_code}|{city_key}"
    entry = LOOKUP.get(key)
    if entry:
        return entry["utility"]
    if utility_parent_dir in UTILITY_DIR_NAMES:
        return UTILITY_DIR_NAMES[utility_parent_dir]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--region", help="limit to one region code, e.g. on, ca, ny")
    args = ap.parse_args()

    applied, skipped_bc, unmapped, already_present, no_anchor = [], [], [], [], []

    for top in ("ca", "us"):
        base = ROOT / top
        if not base.exists():
            continue
        for index_file in base.rglob("index.html"):
            cat_dir = index_file.parent.name
            if cat_dir not in CATEGORY_DIRS:
                continue

            city_dir = index_file.parent.parent
            city_slug = city_dir.name

            # Region code is the path segment right after ca/ or us/
            rel_parts = index_file.relative_to(ROOT).parts
            region_code = rel_parts[1]

            if args.region and region_code != args.region:
                continue

            if region_code == "bc":
                skipped_bc.append(index_file)
                continue

            if region_code not in CA_REGIONS and region_code not in US_REGIONS:
                unmapped.append((index_file, "unrecognized region"))
                continue

            area_word = "province" if region_code in CA_REGIONS else "state"

            grandparent = city_dir.parent.name if city_dir.parent != base else None
            utility = find_utility(region_code, city_slug, grandparent)
            if not utility:
                unmapped.append((index_file, f"no lookup entry for {region_code}|{city_slug.replace('-', ' ')}"))
                continue

            html = index_file.read_text(errors="ignore")
            if f"Your utility: {utility}" in html:
                already_present.append(index_file)
                continue

            if not NEXT_STEPS_RE.search(html):
                no_anchor.append(index_file)
                continue

            city_display = city_slug.replace("-", " ").title()
            section = build_section(utility, city_display, cat_dir, area_word)
            new_html = NEXT_STEPS_RE.sub(section + r"\1", html, count=1)

            applied.append(index_file)
            if not args.dry_run:
                index_file.write_text(new_html)

    print(f"Applied:          {len(applied)}")
    print(f"Already present:  {len(already_present)}")
    print(f"Skipped (BC):     {len(skipped_bc)}")
    print(f"Unmapped:         {len(unmapped)}")
    print(f"No anchor found:  {len(no_anchor)}")

    if unmapped:
        print("\n--- Unmapped (no city-rebate-lookup.json entry) ---")
        for path, reason in unmapped[:40]:
            print(f"  {path.relative_to(ROOT)}  ({reason})")
        if len(unmapped) > 40:
            print(f"  ... and {len(unmapped) - 40} more")

    if no_anchor:
        print("\n--- No 'Next steps' anchor found (needs manual look) ---")
        for path in no_anchor[:20]:
            print(f"  {path.relative_to(ROOT)}")

    if args.dry_run:
        print("\n(dry run — no files written)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
