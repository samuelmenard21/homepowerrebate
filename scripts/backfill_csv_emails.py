#!/usr/bin/env python3
"""
Backfill the Email column in the *-installers-real.csv source files from
installer-emails.csv (recovered by installers/find-installer-emails.py).

The scraper (scrape_google_places_installers.py) leaves Email blank on
purpose — the Places API doesn't return it. find-installer-emails.py
already recovered real addresses for ~70% of installers sitewide into
installers/installer-emails.csv, but that file was never merged back into
the *-real.csv files that scripts/generate_installer_json_from_real.py
reads — so the site's live JSON never saw them.

This is the missing link: CSV -> CSV merge, then re-run the JSON generator.

Run from the Powerrebate root:
  python3 scripts/backfill_csv_emails.py
  python3 scripts/generate_installer_json_from_real.py
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
INSTALLERS_DIR = ROOT / "installers"
EMAILS_CSV = INSTALLERS_DIR / "installer-emails.csv"

TARGET_CSVS = [
    "heat-pump-installers-real.csv", "solar-installers-real.csv",
    "on-heat-pump-installers-real.csv", "on-solar-installers-real.csv",
    "ab-heat-pump-installers-real.csv", "ab-solar-installers-real.csv",
    "ns-heat-pump-installers-real.csv", "ns-solar-installers-real.csv",
    "ma-heat-pump-installers-real.csv", "ma-solar-installers-real.csv",
]


def load_email_map():
    if not EMAILS_CSV.exists():
        sys.exit(f"Not found: {EMAILS_CSV} — run installers/find-installer-emails.py first.")
    out = {}
    with EMAILS_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            email = (row.get("Email") or "").strip()
            if not email:
                continue
            key = (row["Business Name"].strip().lower(), row["City"].strip().lower())
            out[key] = email
    return out


def main():
    email_map = load_email_map()
    print(f"Loaded {len(email_map)} recovered emails.")

    total_filled = 0
    for name in TARGET_CSVS:
        path = INSTALLERS_DIR / name
        if not path.exists():
            print(f"SKIP (not found): {name}")
            continue

        with path.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            fieldnames = rows[0].keys() if rows else []

        if "Email" not in fieldnames:
            print(f"SKIP (no Email column): {name}")
            continue

        filled = 0
        for row in rows:
            if (row.get("Email") or "").strip():
                continue  # already has one
            key = (row["Business Name"].strip().lower(), row["City"].strip().lower())
            if key in email_map:
                row["Email"] = email_map[key]
                filled += 1

        if filled:
            with path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

        total_filled += filled
        print(f"{name}: filled {filled} of {len(rows)} rows")

    print(f"\nTotal emails backfilled: {total_filled}")
    print("Next: python3 scripts/generate_installer_json_from_real.py")


if __name__ == "__main__":
    main()
