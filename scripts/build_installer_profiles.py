#!/usr/bin/env python3
"""Build every installer profile (installers/profiles/**) in one run, in the right order.

Profiles used to be made by two generators at different times and then patched by eight scripts, so pages built months
apart looked different. This runs the whole chain, so every profile comes from the same render function and the same
data: render_profile() in generate_installer_profiles.py, the ranking CSVs, installers/json, installers/rankings.json,
city-rebate-lookup.json, data/installer-place-ids.json and data/installer-owner-notes.json.

  python3 scripts/build_installer_profiles.py

Then run scripts/post_steps.py (rebuild_all.py does both).
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STEPS = [
    "generate_installer_profiles",                 # profiles of installers in installers/json (overwrites)
    "add_missing_installer_profiles --refresh",    # every other ranked installer, from the ranking CSVs
    "refresh_profile_details",                     # rating format, the city's rebate amount, the quote box city
    "enrich_installer_profiles",                   # "Also installs", area notes, and the FAQ (after the rebate card is refreshed)
    "fix_profile_layout",                          # responsive layout block
    "fix_installer_places",                        # Google Maps attribution, no rating markup
    "add_profile_badge_links",                     # "Is this your company?" badge card per ranking
    "fix_profile_nearby_links",                    # profile-to-profile links to pages that exist
    "add_profile_photos",                          # initials tile and view-time photo
    "add_owner_notes",                             # company-supplied notes
    "add_installer_profile_urls",                  # profileUrl in installers/json for the directory
]


def main():
    for step in STEPS:
        name, *args = step.split()
        r = subprocess.run([sys.executable, f"scripts/{name}.py", *args], cwd=ROOT, capture_output=True, text=True)
        print(("FAILED " if r.returncode else "ok     ") + step, flush=True)
        if r.returncode:
            print("   ", (r.stderr or r.stdout).strip()[-500:])
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
