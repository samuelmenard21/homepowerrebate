#!/usr/bin/env python3
"""
Regenerate each city category page's static .installer-card block from the
same JSON files that power the /installers/ directory — so a page's visible
installer list never drifts from the JSON (new installer added, an email
recovered, a rating changed) without someone remembering to re-run this.

Scope: heat-pump and solar only — the two categories with real generated
JSON (installers/json/<region>/{,solar/}<city>.json). water-heater/battery
installer-card blocks exist on some pages too but aren't backed by JSON yet,
so they're intentionally left untouched here.

This keeps the pages STATIC HTML (server-rendered, crawlable) — it's a
build-time sync, not a runtime fetch. Re-run this after any change to the
installer JSON (a new scrape, an email backfill, a manual correction).

Run from the Powerrebate root:
  python3 scripts/sync_installer_cards_from_json.py           # apply
  python3 scripts/sync_installer_cards_from_json.py --dry-run # report only
"""
import argparse
import glob
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP_N = 4

# region_code -> (page_glob_pattern, json_subdir_under_installers/json)
# page_glob_pattern uses {city} as the placeholder for the page's own city
# slug so each match can be looked up against its own JSON file.
REGIONS = {
    "bc": {"pages": "ca/bc/*/heat-pump/index.html", "json": ""},  # BC has no province prefix
    "bc-solar": {"pages": "ca/bc/*/solar/index.html", "json": "solar"},
    "ab": {"pages": "ca/ab/*/heat-pump/index.html", "json": "ab"},
    "ab-solar": {"pages": "ca/ab/*/solar/index.html", "json": "ab/solar"},
    "ma": {"pages": "us/ma/*/heat-pump/index.html", "json": "ma"},
    "ma-solar": {"pages": "us/ma/*/solar/index.html", "json": "ma/solar"},
    "ca": {"pages": "us/ca/*/*/heat-pump/index.html", "json": "ca"},
    "ca-solar": {"pages": "us/ca/*/*/solar/index.html", "json": "ca/solar"},
    # NY intentionally excluded: its city pages (us/ny/<utility>/<city>/index.html)
    # have no .installer-card block at all — installer visibility there comes
    # only from the /installers/ directory and its static fallback, not
    # embedded cards, so there's nothing for this script to sync.
}


def city_slug_from_path(path):
    # .../<city>/heat-pump/index.html or .../<city>/solar/index.html
    parts = path.split(os.sep)
    return parts[-3]


def slugify(name):
    s = name.lower().strip()
    s = re.sub(r"[&']", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def build_cards(installers, style):
    """Two indentation variants exist on the site (found 2026-08-30, same
    content, different whitespace): BC/AB/MA use a 6-space-indented inner
    block; CA/NY use unindented inner divs. Match whichever the page already
    uses so the diff stays whitespace-only where content didn't change."""
    cards = []
    for inst in installers[:TOP_N]:
        name = html.escape(inst["name"])
        rating = inst["rating"]
        reviews = inst["reviews"]
        website = inst.get("website") or ""
        if style == "indented":
            cards.append(
                f'    <div class="installer-card">\n'
                f'      <div><div class="name">{name}</div><div class="stars">&#9733; {rating:.1f} ({reviews} reviews)</div></div>\n'
                f'      <a class="site-link" href="{html.escape(website)}" target="_blank" rel="noopener">Visit site &rarr;</a>\n'
                f'    </div>'
            )
        else:  # "flat"
            cards.append(
                f'    <div class="installer-card">\n'
                f'  <div><div class="name">{name}</div><div class="stars">&#9733; {rating:.1f} ({reviews} reviews)</div></div>\n'
                f'  <a class="site-link" href="{html.escape(website)}" target="_blank" rel="noopener">Visit site &rarr;</a>\n'
                f'</div>'
            )
    return "\n".join(cards)


CARD_BLOCK_RE_INDENTED = re.compile(
    r'(    <div class="installer-card">\n(?:      .*\n)+?    </div>\n)+',
)
CARD_BLOCK_RE_FLAT = re.compile(
    r'(    <div class="installer-card">\n(?:  .*\n)+?</div>\n)+',
)


def sync_page(page_path, json_dir_key, dry_run):
    city_slug = city_slug_from_path(page_path)
    json_path = os.path.join(ROOT, "installers/json", json_dir_key, f"{city_slug}.json") if json_dir_key else os.path.join(ROOT, "installers/json", f"{city_slug}.json")
    if not os.path.exists(json_path):
        return None  # no data for this city, leave the page alone

    installers = json.load(open(json_path, encoding="utf-8"))
    installers = sorted(installers, key=lambda x: (-x.get("recommended", False), -x["rating"], -x["reviews"]))
    if not installers:
        return None

    text = open(page_path, encoding="utf-8").read()
    m = CARD_BLOCK_RE_INDENTED.search(text)
    style = "indented"
    if not m:
        m = CARD_BLOCK_RE_FLAT.search(text)
        style = "flat"
    if not m:
        return "no installer-card block found"

    old_block = m.group(0)
    new_block = build_cards(installers, style) + "\n"
    if old_block == new_block:
        return "already in sync"

    if not dry_run:
        new_text = text[:m.start()] + new_block + text[m.end():]
        open(page_path, "w", encoding="utf-8").write(new_text)
    return f"updated ({len(installers)} installers available, showing top {min(TOP_N, len(installers))})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    stats = {"updated": 0, "already_in_sync": 0, "no_data": 0, "no_block": 0}
    for key, cfg in REGIONS.items():
        pages = sorted(glob.glob(os.path.join(ROOT, cfg["pages"])))
        for page_path in pages:
            result = sync_page(page_path, cfg["json"], args.dry_run)
            rel = os.path.relpath(page_path, ROOT)
            if result is None:
                stats["no_data"] += 1
                continue
            if result == "already in sync":
                stats["already_in_sync"] += 1
                continue
            if result == "no installer-card block found":
                stats["no_block"] += 1
                continue
            stats["updated"] += 1
            print(f"  {rel}: {result}")

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}updated={stats['updated']} "
          f"already_in_sync={stats['already_in_sync']} "
          f"no_data={stats['no_data']} no_installer_card_block={stats['no_block']}")


if __name__ == "__main__":
    main()
