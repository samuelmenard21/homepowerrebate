#!/usr/bin/env python3
"""Fails when a region or city in data/regions.json is missing from any place that lists regions or cities.

Checks, for every region: its hub page exists; the homepage names it (meta description, structured data, region card, hero picker);
llms.txt, the rebate finder (/get-quotes/), the menu and footer (on a sample page), the sitemap and the calculator index
(when it has a calculator) list it; lead-router.js accepts it in the installer survey. For every city (California's list holds regional hubs, so it skips the picker and email checks): its page exists, the sitemap,
the menu, the homepage picker and PowerScore list it, and city-rebate-lookup.json has a summary for the homeowner emails.
The homepage city count must equal the number of cities. Run after scripts/sync_regions.py; exit 1 lists every gap.
Usage: python3 scripts/check_region_coverage.py"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import regions  # noqa: E402
from build_get_quotes import city_slugs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://homepowerrebate.com"


def city_key(name):
    """Same normalization as normalizeCityKey() in lead-router.js."""
    return " ".join(name.lower().replace(".", "").replace(",", "").split())


def read(p):
    f = ROOT / p
    return f.read_text(encoding="utf-8", errors="ignore") if f.exists() else ""


def main():
    home, llms, gq, sitemap = read("index.html"), read("llms.txt"), read("get-quotes/index.html"), read("sitemap.xml")
    calc, router, sample = read("calculator/index.html"), read("lead-router.js"), read("about.html")
    lookup = json.loads(read("city-rebate-lookup.json") or "{}")
    ps = read("powerscore-data.json")
    m = re.search(r'name="description" content="([^"]*)"', home)
    desc = m.group(1) if m else ""
    m = re.search(r"window\.HPR_CITIES=(\[.*?\]);", home)
    picker = {r["c"]: {k[0] for k in r["k"]} for r in json.loads(m.group(1))} if m else {}
    m = re.search(r"const SURVEY_REGIONS = \[([^\]]*)\]", router)
    survey = set(re.findall(r"'([a-z]+)'", m.group(1))) if m else set()
    if "import REGION_DATA from './data/regions.json'" in router and "REGION_LIST.map(r => r.code)" in router:
        survey = {r["code"] for r in regions.REGIONS}  # the Worker reads data/regions.json itself
    survey_page = read("installers/survey/index.html")
    gaps = []
    total = 0
    for r in regions.REGIONS:
        code, name, hub = r["code"], r["name"], f'/{r["path"]}/'
        short = "BC" if code == "bc" else name
        need = {
            "hub page": (ROOT / r["path"] / "index.html").exists(),
            "homepage structured data": f'"{name}, ' in home,
            "homepage region card": f'<th scope="row"><a href="{hub}">' in home,  # the "Compare places" table (was the region cards)
            "homepage picker": code in picker,
            "llms.txt": hub in llms,
            "rebate finder": f'"c":"{code}"' in gq.replace(" ", "") or f'"code": "{code}"' in gq or f'"code":"{code}"' in gq,
            "menu tab": f"province-tab-{code}" in sample,
            "footer": f'<a href="{hub}">' in sample,
            "sitemap": f"{BASE}{hub}" in sitemap,
            "installer survey (lead-router.js)": code in survey,
            "installer survey page": f'<option value="{code}"' in survey_page,
        }
        if r.get("calc_label"):
            need["calculator index"] = f"/calculator/{code}/" in calc
        gaps += [f"{name}: missing from {k}" for k, ok in need.items() if not ok]
        slugs = city_slugs(code)
        total += len(slugs)
        for href, label in r["cities"]:
            slug = href.strip("/").split("/")[-1]
            cneed = {
                "city page": (ROOT / href.strip("/") / "index.html").exists(),
                "sitemap": f"{BASE}{href}" in sitemap,
                "menu": f'href="{href}"' in sample,
                "homepage picker": code == "ca" or slug in picker.get(code, set()),
                "PowerScore": f'"{href}"' in ps or f"{href}" in ps,
                "email rebate summary (city-rebate-lookup.json)": code == "ca" or f"{code}|{city_key(label)}" in lookup or f"{code}|{city_key(slug.replace('-', ' '))}" in lookup,
            }
            gaps += [f"{label} ({name}): missing from {k}" for k, ok in cneed.items() if not ok]
    m = re.search(r'data-city-count="(\d+)"', home)
    if not m or int(m.group(1)) != total:
        gaps.append(f"homepage city count says {m.group(1) if m else '?'}, cities total {total}")
    if gaps:
        print("\n".join("GAP  " + g for g in gaps))
        print(f"\n{len(gaps)} gaps. Run python3 scripts/sync_regions.py, then fix anything left by hand (city pages, email summaries).")
        sys.exit(1)
    print(f"OK   {len(regions.REGIONS)} regions, {total} cities listed everywhere")


if __name__ == "__main__":
    main()
