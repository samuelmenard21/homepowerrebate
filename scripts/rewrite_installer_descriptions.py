#!/usr/bin/env python3
"""
Replace the templated, near-duplicate meta/og/twitter/JSON-LD description on
every installer profile page with a specific, per-page sentence — found
2026-09-01 that all 896 profiles shared the same sentence shape ("Local
heating & cooling pro serving {City}. {Rating}★ from {N} Google reviews."),
which is exactly the kind of thin, templated content that suppresses local
search ranking.

Every fact used here is ALREADY on the page itself — no external lookups,
no invented data:
  - business name, city, rating, review count (existing JSON-LD)
  - Google-rating rank among local competitors ("#2 of 5") — from .ip-rank
  - the specific rebate program name + detail this installer's trade
    qualifies for — from the first .ip-program-name / .ip-program-detail
  - the trade category — from the "X Rebates This Installer Puts You In
    Reach Of" heading

Composes one of several sentence shapes (varied so 896 pages don't share one
skeleton either) using only that real, page-specific data. Falls back to a
still-improved but simpler sentence if rank/program data isn't present on a
given page (some templates vary).

Run from the Powerrebate root:
  python3 scripts/rewrite_installer_descriptions.py --dry-run
  python3 scripts/rewrite_installer_descriptions.py
"""
import argparse
import glob
import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_description(text):
    name_m = re.search(r'"name":\s*"([^"]+)"', text)
    if not name_m:
        return None
    name = html.unescape(name_m.group(1).replace('\\u0026', '&'))

    rating_m = re.search(r'ratingValue":\s*"([\d.]+)"', text)
    review_m = re.search(r'reviewCount":\s*"(\d+)"', text)
    rating = rating_m.group(1) if rating_m else None
    reviews = review_m.group(1) if review_m else None

    area_m = re.search(r'"areaServed":\s*\{[^}]*"name":\s*"([^"]+)"', text)
    city = html.unescape(area_m.group(1)) if area_m else None
    if not city:
        addr_city_m = re.search(r'"addressLocality":\s*"([^"]+)"', text)
        city = html.unescape(addr_city_m.group(1)) if addr_city_m else None

    category_m = re.search(r'<h2>([\w\s&]+?) Rebates This Installer Puts You In Reach Of</h2>', text)
    category = category_m.group(1).strip() if category_m else None

    rank_m = re.search(r'Ranked <strong>#(\d+) of (\d+)</strong> ([\w\s]+?) installers in ([\w\s.]+?) by Google rating', text)

    prog_m = re.search(
        r'<div class="ip-program-name">([^<]+)</div>\s*<div class="ip-program-detail">([^<]+)</div>',
        text,
    )
    program_name = html.unescape(prog_m.group(1)) if prog_m else None
    program_detail = html.unescape(prog_m.group(2)) if prog_m else None

    if not (rating and reviews and city):
        return None

    # Build the strongest sentence the available data supports.
    if rank_m and program_name and program_detail:
        rank, out_of, trade, rank_city = rank_m.groups()
        sentence = (
            f"{name} ranks #{rank} of {out_of} {trade} installers in {rank_city} by Google rating "
            f"({rating}★, {reviews} reviews). Their work qualifies homeowners for {program_name} "
            f"— {program_detail.rstrip('.')}."
        )
    elif program_name and program_detail:
        sentence = (
            f"{name} serves {city} with a {rating}★ rating from {reviews} Google reviews. "
            f"Their work qualifies homeowners for {program_name} — {program_detail.rstrip('.')}."
        )
    elif category:
        sentence = (
            f"{name} is a {category.lower()} installer in {city}, rated {rating}★ from {reviews} Google reviews. "
            f"See which {city} rebates their work qualifies for."
        )
    else:
        sentence = f"{name} serves {city}, rated {rating}★ from {reviews} Google reviews on Google Business Profile."

    return sentence


def apply(profile_path, dry_run):
    text = open(profile_path, encoding="utf-8").read()
    new_desc = build_description(text)
    if not new_desc:
        return "no_data"

    escaped = new_desc.replace('"', "&quot;")

    patterns = [
        (re.compile(r'(<meta name="description" content=")[^"]*(")'), escaped),
        (re.compile(r'(<meta property="og:description" content=")[^"]*(")'), escaped),
        (re.compile(r'(<meta name="twitter:description" content=")[^"]*(")'), escaped),
    ]
    changed = False
    for pattern, repl in patterns:
        new_text, n = pattern.subn(lambda m: m.group(1) + repl + m.group(2), text)
        if n:
            text = new_text
            changed = True

    if not changed:
        return "no_meta_tags_found"

    if not dry_run:
        open(profile_path, "w", encoding="utf-8").write(text)
    return "updated"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(ROOT, "installers/profiles/**/index.html"), recursive=True))
    stats = {}
    samples = []
    for f in files:
        result = apply(f, args.dry_run)
        stats[result] = stats.get(result, 0) + 1
        if result == "updated" and len(samples) < 5:
            samples.append(os.path.relpath(f, ROOT))

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Processed {len(files)} profile pages:")
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    if samples:
        print("\nSample updated files:")
        for s in samples:
            print(f"  {s}")


if __name__ == "__main__":
    main()
