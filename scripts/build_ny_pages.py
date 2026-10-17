#!/usr/bin/env python3
"""NY city category pages under each utility (/us/ny/<utility>/<city>/<category>/): engine scripts/city_pages.py, settings in data/regions.json (city_pages), prose in data/ny/pages/<utility>/<city>/<category>.json.
Usage: python3 scripts/build_ny_pages.py [city ...]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import city_pages  # noqa: E402

if __name__ == "__main__":
    city_pages.main("ny")
