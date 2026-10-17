#!/usr/bin/env python3
"""One command to run after adding a region or a city to data/regions.json.

Rebuilds everything that lists regions or cities, in the right order, then checks that nothing was missed:
rebate finder, homepage (hero picker, city count, region cards, meta and structured-data region lists), llms.txt, calculators,
PowerScore and its badges, the hub pipeline, the homepage PowerScore and feed, the menu and footer on every page (restamp),
the SEO and link post-steps, sitemap and source registry, then check_hub_layout, check_internal_links and
check_region_coverage. What it cannot write for you (city pages, the email summary in city-rebate-lookup.json) shows up as a GAP.
Usage: python3 scripts/sync_regions.py"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STEPS = [
    "build_get_quotes", "build_home_hero", "build_home_region_cards", "build_about_coverage", "build_calculator",
    "build_powerscore", "build_powerscore_page", "update_powerscore_badges",
    "build_hub_tops", "build_hub_showcase", "build_hub_tidy", "apply_canonical_nav_footer",
    "build_home_powerscore", "build_home_feed", "build_internal_boosts", "link_discovered", "apply_canonical_nav_footer",
    "fix_seo_meta", "add_aeo_markup", "link_orphans", "fix_redirected_links", "follow_official_sources",
    "apply_canonical_nav_footer", "apply_canonical_nav_footer",
    "generate_sitemap", "build_source_registry",
]
CHECKS = ["check_hub_layout", "check_internal_links", "check_region_coverage"]


def run(name):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / f"{name}.py")], cwd=ROOT, capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or [""])[-1]
    print(f"{'ok  ' if r.returncode == 0 else 'FAIL'} {name}: {last[:140]}")
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:])
    return r.returncode == 0


def main():
    ok = all([run(s) for s in STEPS])
    ok = all([run(c) for c in CHECKS]) and ok
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
