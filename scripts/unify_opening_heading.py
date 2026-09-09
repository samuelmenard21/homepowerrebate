#!/usr/bin/env python3
"""
Unifies the opening <h2> heading text across all category pages to match
the current generator scripts' target ("How much you get") — the site's
generator scripts (generate_ca_solar_pages.py, generate_ca_battery_
insulation_pages.py, generate_ny_water_heater_pages.py) all regex-target
this exact heading; pages on an older vintage heading text ("The
breakdown" for all 24 Ontario cities, "How much rebate you get" for all
18 BC cities — confirmed via audit, no other regions/cities affected)
would silently be skipped by any future generator rerun.

Only replaces the literal <h2>...</h2> tag occurrence — NOT other
occurrences of the same phrase (e.g. a meta-description sentence like
"How much rebate you get for heat-pump in Kelowna..." stays as natural
English, only the section heading itself changes).

Usage:
    python3 scripts/unify_opening_heading.py --dry-run
    python3 scripts/unify_opening_heading.py
"""
import argparse
import glob
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATEGORY_DIRS = {
    "heat-pump", "solar", "battery", "water-heater", "insulation",
    "windows", "windows-doors", "ev-charger", "smart-thermostats", "hrv",
    "appliances",
}
OLD_HEADINGS = ["<h2>The breakdown</h2>", "<h2>How much rebate you get</h2>"]
NEW_HEADING = "<h2>How much you get</h2>"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = glob.glob(str(ROOT / "ca" / "**" / "index.html"), recursive=True) + \
            glob.glob(str(ROOT / "us" / "**" / "index.html"), recursive=True)

    changed = []
    for f in files:
        p = Path(f)
        cat = p.parent.name
        if cat not in CATEGORY_DIRS:
            continue
        html = p.read_text(errors="ignore")
        new_html = html
        for old in OLD_HEADINGS:
            new_html = new_html.replace(old, NEW_HEADING, 1)  # only the h2 tag itself, once
        if new_html != html:
            changed.append(p.relative_to(ROOT))
            if not args.dry_run:
                p.write_text(new_html)

    print(f"{'Would change' if args.dry_run else 'Changed'}: {len(changed)} files")
    if args.dry_run:
        for c in changed[:10]:
            print(f"  {c}")
        if len(changed) > 10:
            print(f"  ... and {len(changed) - 10} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
