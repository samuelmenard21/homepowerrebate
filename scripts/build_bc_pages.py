#!/usr/bin/env python3
"""BC city category pages and city hubs. The engine is scripts/city_pages.py; settings are the "city_pages" block for bc in
data/regions.json; prose is in data/bc/pages/<city>/<category>.json.
Usage: python3 scripts/build_bc_pages.py [city ...] [--hubs]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import city_pages  # noqa: E402

if __name__ == "__main__":
    city_pages.main("bc")
