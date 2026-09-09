#!/usr/bin/env python3
"""
Layer 2 (climate) of the category-page-localization playbook: inject real,
city-specific 10-year climate data (from city-climate-data.json, built by
build_city_climate_data.py against Open-Meteo's historical archive — real
measured temperatures, same methodology for every city so numbers are
comparable) into the categories where climate is actually relevant to the
homeowner's decision: heat-pump, hrv, insulation, windows/windows-doors.

Applies to every region, including BC (BC was skipped in Layer 1 since
its utility doesn't vary by city — climate is BC's differentiator, and
BC's climate genuinely varies enormously: coastal Victoria vs. interior
Kamloops vs. northern Fort St John).

Same anchor strategy as Layer 1: insert before <h2>Next steps</h2>, so it
stacks after the Layer 1 utility section rather than needing to find a
category-specific insertion point.

Usage:
    python3 scripts/apply_layer2_climate_data.py --dry-run
    python3 scripts/apply_layer2_climate_data.py
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLIMATE = json.loads((ROOT / "city-climate-data.json").read_text())

CLIMATE_CATEGORIES = {"heat-pump", "hrv", "insulation", "windows", "windows-doors"}

NEXT_STEPS_RE = re.compile(r'(\s*<h2>Next steps</h2>)')


def find_climate(region_code, city_slug):
    key = f"{region_code}|{city_slug.replace('-', ' ')}"
    return CLIMATE.get(key)


def build_section(city, cat_dir, data):
    avg_low = data["avg_january_low_c"]
    coldest = data["coldest_recorded_c"]
    years = data["sample_years"]

    if cat_dir == "heat-pump":
        body = (
            f"Over the last 10 winters ({years}), {city}'s average January "
            f"daily low has been {avg_low}&deg;C, with a coldest recorded day "
            f"of {coldest}&deg;C — real measured data, not a rounded estimate. "
            f"A modern cold-climate heat pump (the kind required for the "
            f"rebate above) keeps pulling heat efficiently down to roughly "
            f"-25&deg;C or colder, so it's built for weather colder than "
            f"{city} has actually seen in the last decade."
        )
        heading = f"Will it keep {city} warm? What the last 10 winters actually looked like"
    elif cat_dir == "hrv":
        body = (
            f"{city}'s average January daily low over the last 10 winters "
            f"({years}) has been {avg_low}&deg;C, with a coldest recorded day "
            f"of {coldest}&deg;C. Colder outdoor air holds less moisture, "
            f"which is exactly why a well-sealed {city} home needs "
            f"mechanical ventilation in the first place — without an HRV, "
            f"that sealed-up house traps humidity indoors instead of "
            f"exchanging stale air for fresh air without losing the heat "
            f"you paid for."
        )
        heading = f"Why ventilation matters more in {city}'s winters"
    else:  # insulation, windows, windows-doors
        body = (
            f"{city}'s average January daily low has been {avg_low}&deg;C "
            f"over the last 10 winters ({years}), with a coldest recorded "
            f"day of {coldest}&deg;C — real measured data. The colder it "
            f"gets outside, the more a poorly insulated wall or an old "
            f"window actually costs you in heat loss, which is the real "
            f"math behind why this rebate exists and why the payback tends "
            f"to be faster in a climate like {city}'s than in a milder one."
        )
        heading = f"What {city}'s winters mean for this upgrade's payback"

    return f'\n    <h2>{heading}</h2>\n    <p>{body}</p>\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--region", help="limit to one region code")
    args = ap.parse_args()

    applied, already_present, unmapped, no_anchor, skipped_category = [], [], [], [], 0

    for top in ("ca", "us"):
        base = ROOT / top
        if not base.exists():
            continue
        for index_file in base.rglob("index.html"):
            cat_dir = index_file.parent.name
            if cat_dir not in CLIMATE_CATEGORIES:
                skipped_category += 1
                continue

            city_dir = index_file.parent.parent
            city_slug = city_dir.name
            rel_parts = index_file.relative_to(ROOT).parts
            region_code = rel_parts[1]

            if args.region and region_code != args.region:
                continue

            data = find_climate(region_code, city_slug)
            if not data:
                unmapped.append((index_file, f"no climate data for {region_code}|{city_slug.replace('-', ' ')}"))
                continue

            html = index_file.read_text(errors="ignore")
            city_display = city_slug.replace("-", " ").title()
            marker = f"{data['avg_january_low_c']}&deg;C"
            if marker in html:
                already_present.append(index_file)
                continue

            if not NEXT_STEPS_RE.search(html):
                no_anchor.append(index_file)
                continue

            section = build_section(city_display, cat_dir, data)
            new_html = NEXT_STEPS_RE.sub(section + r"\1", html, count=1)

            applied.append(index_file)
            if not args.dry_run:
                index_file.write_text(new_html)

    print(f"Applied:            {len(applied)}")
    print(f"Already present:    {len(already_present)}")
    print(f"Skipped (category): {skipped_category}")
    print(f"Unmapped:           {len(unmapped)}")
    print(f"No anchor found:    {len(no_anchor)}")

    if unmapped:
        print("\n--- Unmapped (no city-climate-data.json entry) ---")
        for path, reason in unmapped[:40]:
            print(f"  {path.relative_to(ROOT)}  ({reason})")
        if len(unmapped) > 40:
            print(f"  ... and {len(unmapped) - 40} more")

    if args.dry_run:
        print("\n(dry run — no files written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
