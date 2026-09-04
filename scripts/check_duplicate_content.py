#!/usr/bin/env python3
"""
Doorway/near-duplicate content checker.

Walks every category subpage under ca/ and us/, strips city-identifying
tokens (city name variants, slug, postal/utility hints) from the page body,
hashes what's left, and groups pages whose hash matches within the same
category. A match means two "different" city pages are the same content
with only the city name swapped — a doorway-page problem that has hurt
this site's SEO more than once (see reports/seo-audit-fixes-2026-09-03.md §3).

Run this:
  - before shipping ANY new city page or new page cluster
  - as part of CI / pre-push if you wire that up
  - periodically as a standing audit (monthly is reasonable)

Usage:
    python3 scripts/check_duplicate_content.py
    python3 scripts/check_duplicate_content.py --category water-heater
    python3 scripts/check_duplicate_content.py --fail-on-duplicates   # exit 1 if any found, for CI

Exit code 0 = clean. Exit code 1 = duplicates found (only with --fail-on-duplicates).
"""
import argparse
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATEGORY_DIRS = {
    "heat-pump", "solar", "battery", "water-heater", "insulation",
    "windows", "windows-doors", "ev-charger", "smart-thermostats", "hrv",
    "appliances",
}

# Tags/attrs whose text content is expected to legitimately vary only in
# boilerplate ways (nav, footer) — strip these entirely before hashing so
# real shared chrome doesn't produce false positives.
STRIP_BLOCK_RE = re.compile(
    r"<(nav|footer|header)\b.*?</\1>", re.IGNORECASE | re.DOTALL
)
TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def city_name_from_path(p: Path) -> str:
    # category dir's parent is the city dir
    return p.parent.name


def normalize(html: str, city_dir_name: str) -> str:
    html = STRIP_BLOCK_RE.sub("", html)
    # Build a set of plausible city-name surface forms from the slug
    words = city_dir_name.replace("-", " ").split()
    for w in words:
        if len(w) < 3:
            continue
        html = re.sub(re.escape(w), "[CITY]", html, flags=re.IGNORECASE)
    html = re.sub(re.escape(city_dir_name), "[CITY]", html, flags=re.IGNORECASE)
    text = TAG_RE.sub(" ", html)
    text = WHITESPACE_RE.sub(" ", text).strip().lower()
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", help="only check this category dir name")
    ap.add_argument("--fail-on-duplicates", action="store_true")
    args = ap.parse_args()

    groups = defaultdict(list)  # (region_cluster, category, hash) -> [paths]

    for region_root in ("ca", "us"):
        base = ROOT / region_root
        if not base.exists():
            continue
        for index_file in base.rglob("index.html"):
            cat_dir = index_file.parent.name
            if cat_dir not in CATEGORY_DIRS:
                continue
            if args.category and cat_dir != args.category:
                continue
            city_dir = index_file.parent.parent
            cluster = str(city_dir.parent.relative_to(ROOT))  # groups siblings under the same metro/region dir
            html = index_file.read_text(errors="ignore")
            norm = normalize(html, city_dir.name)
            h = hashlib.md5(norm.encode()).hexdigest()
            groups[(cluster, cat_dir, h)].append(index_file.relative_to(ROOT))

    dupes = {k: v for k, v in groups.items() if len(v) > 1}

    if not dupes:
        print("Clean — no byte-identical (city-name-normalized) sibling pages found.")
        return 0

    print(f"Found {len(dupes)} duplicate group(s):\n")
    for (cluster, cat, h), paths in sorted(dupes.items()):
        print(f"  [{cluster} / {cat}]  {len(paths)} identical pages:")
        for p in paths:
            print(f"    - {p}")
        print()

    if args.fail_on_duplicates:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
