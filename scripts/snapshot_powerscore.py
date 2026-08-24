#!/usr/bin/env python3
"""
snapshot_powerscore.py — copies the current powerscore-data.json into
powerscore-history/ as a timestamped snapshot (powerscore-history/YYYY-MM-DD.json).

Run this once a month (right after regenerating powerscore-data.json via
scripts/build_powerscore.py) to build up a history of PowerScore snapshots that
scripts/powerscore_movers.py can diff against for the "who moved" content series.

Usage:
  python3 scripts/snapshot_powerscore.py             # snapshot dated today
  python3 scripts/snapshot_powerscore.py 2026-09-23   # snapshot dated explicitly
"""
import json
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "powerscore-data.json"
HISTORY_DIR = ROOT / "powerscore-history"


def main():
    if not SRC.exists():
        print(f"ERROR: {SRC} not found. Run scripts/build_powerscore.py first.")
        sys.exit(1)

    snapshot_date = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()

    HISTORY_DIR.mkdir(exist_ok=True)
    dest = HISTORY_DIR / f"{snapshot_date}.json"

    if dest.exists():
        print(f"Snapshot {dest} already exists — overwriting.")

    # Validate it's real JSON before copying (fail loud, not silent).
    with open(SRC) as f:
        data = json.load(f)

    shutil.copyfile(SRC, dest)

    n_cities = data.get("stats", {}).get("total_cities", "?")
    print(f"Snapshot written: {dest}")
    print(f"  generated: {data.get('generated')}")
    print(f"  cities: {n_cities}")

    existing = sorted(p.name for p in HISTORY_DIR.glob("*.json") if p.name != "movers-latest.json")
    print(f"  total snapshots in history: {len(existing)} ({', '.join(existing)})")


if __name__ == "__main__":
    main()
