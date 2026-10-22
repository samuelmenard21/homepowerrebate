#!/usr/bin/env python3
"""pe region hub base page: engine scripts/city_pages.py, settings in data/regions.json, prose in data/pe/pages/state-hub.json.
Usage: python3 scripts/build_pe_pages.py --state"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import city_pages  # noqa: E402

if __name__ == "__main__":
    city_pages.main("pe")
