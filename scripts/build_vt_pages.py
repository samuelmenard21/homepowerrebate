#!/usr/bin/env python3
"""VT city category pages and city hubs: engine scripts/city_pages.py, settings in data/regions.json (city_pages), prose in data/vt/pages/<city>/<category>.json.
Usage: python3 scripts/build_vt_pages.py [city ...] [--hubs]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import city_pages  # noqa: E402

if __name__ == "__main__":
    city_pages.main("vt")
