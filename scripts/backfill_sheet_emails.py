#!/usr/bin/env python3
"""
Backfill the Email column in the HomePowerRebate-Installers Google Sheet from
installer-emails.csv (recovered by installers/find-installer-emails.py).

The scraper leaves Email blank on purpose (Places API doesn't return it) —
this is the one script that writes real emails back into the Sheet, across
every "Heat Pumps"/"Solar" tab (BC, ON, AB, NS, MA), so the Sheet stays the
source of truth for outreach instead of drifting from the site's local data.

Run from the Powerrebate root:
  python3 scripts/backfill_sheet_emails.py
"""

import csv
import sys
from pathlib import Path

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    sys.exit("pip3 install gspread google-auth-oauthlib")

ROOT = Path(__file__).parent.parent
SHEET_ID = "11YrVuRF2xutjeaPlL9zwd2LwzmBAxfFujFGMdadph-4"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

TABS = [
    "Heat Pumps", "Solar",
    "Heat Pumps - ON", "Solar - ON",
    "Heat Pumps - AB", "Solar - AB",
    "Heat Pumps - NS", "Solar - NS",
    "Heat Pumps - MA", "Solar - MA",
]


def load_email_map():
    path = ROOT / "installers" / "installer-emails.csv"
    if not path.exists():
        sys.exit(f"Not found: {path} — run installers/find-installer-emails.py first.")
    out = {}
    with path.open() as f:
        for row in csv.DictReader(f):
            email = (row.get("Email") or "").strip()
            if not email:
                continue
            key = (row["Business Name"].strip().lower(), row["City"].strip().lower())
            out[key] = email
    return out


def find_creds_path():
    for candidate in [ROOT / "google-credentials.json", ROOT / "installers" / "google-credentials.json"]:
        if candidate.exists():
            return candidate
    sys.exit("google-credentials.json not found in repo root or installers/.")


def main():
    email_map = load_email_map()
    print(f"Loaded {len(email_map)} recovered emails from installer-emails.csv")

    creds = Credentials.from_service_account_file(str(find_creds_path()), scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)

    total_updated = 0
    for tab in TABS:
        try:
            ws = spreadsheet.worksheet(tab)
        except gspread.WorksheetNotFound:
            continue

        values = ws.get_all_values()
        if not values:
            continue
        header = values[0]
        try:
            name_col = header.index("Business Name")
            city_col = header.index("City")
            email_col = header.index("Email")
        except ValueError:
            print(f"  [{tab}] missing expected columns — skipped")
            continue

        updates = []
        tab_updated = 0
        for row_idx, row in enumerate(values[1:], start=2):  # 1-indexed, +1 for header
            if len(row) <= max(name_col, city_col, email_col):
                continue
            key = (row[name_col].strip().lower(), row[city_col].strip().lower())
            recovered = email_map.get(key)
            existing = row[email_col].strip()
            if recovered and recovered != existing:
                col_letter = gspread.utils.rowcol_to_a1(row_idx, email_col + 1)
                updates.append({"range": col_letter, "values": [[recovered]]})
                tab_updated += 1

        if updates:
            ws.batch_update(updates)
            print(f"  [{tab}] updated {tab_updated} email(s)")
            total_updated += tab_updated
        else:
            print(f"  [{tab}] no changes")

    print(f"\nTotal: {total_updated} email(s) written to the Sheet")


if __name__ == "__main__":
    main()
