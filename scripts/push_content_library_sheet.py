#!/usr/bin/env python3
"""
Push the blog/guides/questions/tools content list (built from live site HTML)
into a "Content Library" tab in the HomePowerRebate-Installers Google Sheet,
so there's one place to browse every published page.

Run from the Powerrebate root:
  python3 scripts/push_content_library_sheet.py
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
TAB_NAME = "Content Library"
CSV_PATH = Path("/tmp/content_sheet.csv")


def find_creds_path():
    for candidate in [ROOT / "google-credentials.json", ROOT / "installers" / "google-credentials.json"]:
        if candidate.exists():
            return candidate
    sys.exit("google-credentials.json not found in repo root or installers/.")


def main():
    if not CSV_PATH.exists():
        sys.exit(f"Not found: {CSV_PATH}")

    with CSV_PATH.open(encoding="utf-8") as f:
        rows = list(csv.reader(f))

    creds = Credentials.from_service_account_file(str(find_creds_path()), scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)

    try:
        ws = spreadsheet.worksheet(TAB_NAME)
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=TAB_NAME, rows=len(rows) + 10, cols=6)

    ws.update(values=rows, range_name="A1")
    ws.format("A1:D1", {"textFormat": {"bold": True}})
    ws.freeze(rows=1)
    try:
        ws.columns_auto_resize(0, 3)
    except Exception:
        pass

    print(f"Wrote {len(rows) - 1} pages to '{TAB_NAME}' tab.")
    print(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/")


if __name__ == "__main__":
    main()
