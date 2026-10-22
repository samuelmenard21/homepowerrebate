#!/usr/bin/env python3
"""yt region pages: engine scripts/city_pages.py, settings in data/regions.json, prose in data/yt/pages/ (state-hub.json and <city>/index.json).
Usage: python3 scripts/build_yt_pages.py [city ...] [--hubs] [--state]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import city_pages  # noqa: E402

if __name__ == "__main__":
    city_pages.main("yt")
