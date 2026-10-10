#!/usr/bin/env python3
"""Keep /installers/ on the same city list as the homepage and /get-quotes/.
One source of truth: build_get_quotes.city_slugs() (installer folders plus data/regions.json) and regions.REGIONS.
Rewrites the per-region city arrays in installers/index.html between CITY-LISTS-START/END, and the city and region counts in the hero, stats and meta text. Idempotent.
Usage: python3 scripts/sync_installer_directory.py"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_get_quotes import REG, OV, city_slugs  # noqa: E402

START, END = "// CITY-LISTS-START", "// CITY-LISTS-END"
LABELS = {**OV, "saint-paul": "Saint Paul", "cape-breton": "Cape Breton"}


def label(slug):
    return LABELS.get(slug, slug.replace("-", " ").title())


def build():
    lists, total = [], 0
    for code, _name, _abbr, _jdir in REG:
        names = [label(c) for c in city_slugs(code)]
        total += len(names)
        body = ", ".join(repr(n).replace('"', "\\'") for n in names)
        lists.append(f"const {code.upper()}_CITIES = [{body}];")
    return "\n".join(lists), total, len(REG)


def main():
    p = ROOT / "installers/index.html"
    s = p.read_text(encoding="utf-8")
    block, cities, regions = build()
    if START in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: f"{START}\n{block}\n{END}", s, count=1, flags=re.S)
    else:
        a = s.index("const BC_CITIES = [")
        b = s.index("// Kept for anything still referencing the old flat name.")
        s = s[:a] + f"{START}\n{block}\n{END}\n" + s[b:]
    s = re.sub(r"across \d+ states and provinces and \d+ cities", f"across {regions} states and provinces and {cities} cities", s)
    s = re.sub(r'(id="stat-cities">)\d+(</div>)', rf"\g<1>{cities}\g<2>", s)
    s = re.sub(r"(Cities in )\d+( states and provinces)", rf"\g<1>{regions}\g<2>", s)
    p.write_text(s, encoding="utf-8")
    print(f"{cities} cities in {regions} regions")


if __name__ == "__main__":
    main()
