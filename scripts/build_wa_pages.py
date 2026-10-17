#!/usr/bin/env python3
"""WA city category pages, city hubs and the region hub: engine scripts/city_pages.py, settings in data/regions.json (city_pages), prose in data/wa/ (pages/<city>/<category>.json and state-hub.json).
Usage: python3 scripts/build_wa_pages.py [city ...] [--hubs] [--state-hub]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import city_pages  # noqa: E402

if __name__ == "__main__":
    city_pages.main("wa")
