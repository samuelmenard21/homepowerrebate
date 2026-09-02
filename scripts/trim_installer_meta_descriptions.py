#!/usr/bin/env python3
"""
Shorten the installer profile meta/og/twitter descriptions to fit SEO's
~155-160 char guideline — found 2026-09-01 by an SEO audit that the per-page
rewrite done earlier that day (scripts/rewrite_installer_descriptions.py)
produced real, specific, non-duplicate descriptions, but some run 229-257
chars because the full rebate program "detail" clause can be long.

Does NOT touch the visible on-page <p class="ip-intro"> content — that can
stay full-length, it's not a meta tag with a length constraint. Only trims
the <meta name="description">, og:description, and twitter:description tags.

Strategy, in order, first one that fits under 155 chars wins:
  1. Full sentence as-is (already fine on most pages).
  2. Same sentence with the "— {program detail}" clause dropped (keeps the
     program NAME, drops the potentially-long explanation of it).
  3. A shorter fallback sentence (name + rank/rating + city only).
Never invents new content — every version is a subset of what the per-page
rewrite already established as real.

Run from the Powerrebate root:
  python3 scripts/trim_installer_meta_descriptions.py --dry-run
  python3 scripts/trim_installer_meta_descriptions.py
"""
import argparse
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_LEN = 155


def shorten(desc):
    if len(desc) <= MAX_LEN:
        return desc, "full"

    # Drop the "— {detail}" clause if present, keep everything before it.
    dash_m = re.search(r"^(.*?) — ", desc)
    if dash_m:
        without_detail = dash_m.group(1).rstrip(".") + "."
        if len(without_detail) <= MAX_LEN:
            return without_detail, "no_detail"

    # Fall back to just the first sentence (up to the first period).
    first_sentence_m = re.match(r"^(.*?\.)\s", desc)
    if first_sentence_m and len(first_sentence_m.group(1)) <= MAX_LEN:
        return first_sentence_m.group(1), "first_sentence_only"

    return None, "no_fit"


def process(path, dry_run):
    text = open(path, encoding="utf-8").read()
    m = re.search(r'<meta name="description" content="([^"]+)"', text)
    if not m:
        return "no_meta_tag"
    current = m.group(1).replace("&quot;", '"')
    if len(current) <= MAX_LEN:
        return "already_short"

    new_desc, method = shorten(current)
    if not new_desc:
        return "no_fit_found"

    escaped = new_desc.replace('"', "&quot;")
    for pattern in [
        r'(<meta name="description" content=")[^"]*(")',
        r'(<meta property="og:description" content=")[^"]*(")',
        r'(<meta name="twitter:description" content=")[^"]*(")',
    ]:
        text = re.sub(pattern, lambda mm: mm.group(1) + escaped + mm.group(2), text)

    if not dry_run:
        open(path, "w", encoding="utf-8").write(text)
    return f"trimmed_{method}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(ROOT, "installers/profiles/**/index.html"), recursive=True))
    stats = {}
    no_fit = []
    for f in files:
        result = process(f, args.dry_run)
        stats[result] = stats.get(result, 0) + 1
        if result == "no_fit_found":
            no_fit.append(os.path.relpath(f, ROOT))

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Processed {len(files)} profile pages:")
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    if no_fit:
        print("\nCould not shorten (needs a manual look):")
        for p in no_fit[:10]:
            print(f"  {p}")


if __name__ == "__main__":
    main()
