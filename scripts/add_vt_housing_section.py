#!/usr/bin/env python3
"""Retired 2026-10-06. The Montpelier and Barre ACS housing sections (heating fuel, housing age, tenure) are now written into the
hand-built hubs and category pages from data/vt-housing-acs2024.json by scripts/build_vt_pages.py. Running this script would duplicate them,
so it only removes any leftover VT-HOUSING block from the five Vermont city hubs."""
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
for city in ["burlington", "south-burlington", "rutland", "montpelier", "barre"]:
    p = ROOT / f"us/vt/{city}/index.html"
    s = p.read_text(encoding="utf-8")
    n = re.sub(r"<!-- VT-HOUSING-START -->.*?<!-- VT-HOUSING-END -->", "", s, flags=re.S)
    if n != s:
        p.write_text(n, encoding="utf-8")
        print("removed leftover block from", p)
