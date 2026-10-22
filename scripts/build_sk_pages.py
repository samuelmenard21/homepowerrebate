#!/usr/bin/env python3
"""sk region pages: engine scripts/city_pages.py, settings in data/regions.json, prose in data/sk/pages/ (state-hub.json and <city>/index.json).
Usage: python3 scripts/build_sk_pages.py [city ...] [--hubs] [--state]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import city_pages  # noqa: E402

if __name__ == "__main__":
    city_pages.main("sk")
