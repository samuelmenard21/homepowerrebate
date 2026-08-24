#!/usr/bin/env python3
"""
powerscore_movers.py — computes per-city PowerScore deltas between two snapshots
in powerscore-history/, and outputs a "movers" report (top gainers, top losers,
biggest single-category swings).

Usage:
  python3 scripts/powerscore_movers.py                       # latest two snapshots
  python3 scripts/powerscore_movers.py 2026-07-23 2026-08-23  # explicit pair

NOTE: as of this writing there is only ONE snapshot in powerscore-history/
(2026-08-23.json, the baseline). Real month-over-month deltas require at least
two snapshots taken on different dates, after two runs of build_powerscore.py.
Until then this script will fall back to comparing the single snapshot against
itself, purely as a dry-run / schema check — every delta will be 0.0 and the
report is explicitly labeled as a self-comparison, not a real movers story.
Re-run scripts/snapshot_powerscore.py next month to get real data.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HISTORY_DIR = ROOT / "powerscore-history"
OUT_JSON = HISTORY_DIR / "movers-latest.json"

TOP_N = 10
CATEGORY_SWING_TOP_N = 10


def load_snapshots():
    files = sorted(p for p in HISTORY_DIR.glob("*.json") if p.name != "movers-latest.json")
    return files


def flatten_cities(data):
    """Return dict keyed by 'region/slug' -> city record (overall + categories)."""
    out = {}
    for region_key, region in data.get("regions", {}).items():
        cities = region.get("cities", {})
        for slug, city in cities.items():
            key = f"{region_key}/{slug}"
            out[key] = {
                "region": region_key,
                "region_label": region.get("label"),
                "slug": slug,
                "label": city.get("label"),
                "url": city.get("url"),
                "overall": city.get("overall"),
                "categories": city.get("categories", {}),
            }
    return out


def compute_movers(old_data, new_data, old_label, new_label, is_self_compare):
    old_cities = flatten_cities(old_data)
    new_cities = flatten_cities(new_data)

    deltas = []
    category_swings = []

    for key, new_city in new_cities.items():
        old_city = old_cities.get(key)
        if old_city is None:
            continue  # new city added since last snapshot; not a "mover"
        overall_delta = round(new_city["overall"] - old_city["overall"], 1)
        deltas.append({
            "key": key,
            "label": new_city["label"],
            "region_label": new_city["region_label"],
            "url": new_city["url"],
            "old_overall": old_city["overall"],
            "new_overall": new_city["overall"],
            "delta": overall_delta,
        })

        for cat, new_cat_data in new_city["categories"].items():
            old_cat_data = old_city["categories"].get(cat)
            if old_cat_data is None:
                continue
            cat_delta = round(new_cat_data["score"] - old_cat_data["score"], 1)
            if cat_delta != 0:
                category_swings.append({
                    "key": key,
                    "label": new_city["label"],
                    "region_label": new_city["region_label"],
                    "category": cat,
                    "old_score": old_cat_data["score"],
                    "new_score": new_cat_data["score"],
                    "delta": cat_delta,
                })

    gainers = sorted([d for d in deltas if d["delta"] > 0], key=lambda d: -d["delta"])[:TOP_N]
    losers = sorted([d for d in deltas if d["delta"] < 0], key=lambda d: d["delta"])[:TOP_N]
    unchanged_count = sum(1 for d in deltas if d["delta"] == 0)

    category_swings_sorted = sorted(category_swings, key=lambda d: -abs(d["delta"]))[:CATEGORY_SWING_TOP_N]

    return {
        "is_self_compare": is_self_compare,
        "old_snapshot": old_label,
        "new_snapshot": new_label,
        "cities_compared": len(deltas),
        "cities_unchanged": unchanged_count,
        "top_gainers": gainers,
        "top_losers": losers,
        "biggest_category_swings": category_swings_sorted,
    }


def print_report(report):
    print("=" * 60)
    if report["is_self_compare"]:
        print("PowerScore Movers — DRY RUN (self-comparison, schema check only)")
        print(f"Only one snapshot exists ({report['new_snapshot']}). Comparing it")
        print("against itself to validate the pipeline. All deltas will be 0.0.")
        print("Run scripts/snapshot_powerscore.py again next month for real data.")
    else:
        print(f"PowerScore Movers — {report['old_snapshot']} -> {report['new_snapshot']}")
    print("=" * 60)
    print(f"Cities compared: {report['cities_compared']}  |  Unchanged: {report['cities_unchanged']}")

    print("\nTOP GAINERS")
    if not report["top_gainers"]:
        print("  (none)")
    for d in report["top_gainers"]:
        print(f"  +{d['delta']:>5.1f}  {d['label']} ({d['region_label']})  {d['old_overall']} -> {d['new_overall']}")

    print("\nTOP LOSERS")
    if not report["top_losers"]:
        print("  (none)")
    for d in report["top_losers"]:
        print(f"  {d['delta']:>6.1f}  {d['label']} ({d['region_label']})  {d['old_overall']} -> {d['new_overall']}")

    print("\nBIGGEST CATEGORY SWINGS")
    if not report["biggest_category_swings"]:
        print("  (none)")
    for d in report["biggest_category_swings"]:
        sign = "+" if d["delta"] > 0 else ""
        print(f"  {sign}{d['delta']:>5.1f}  {d['label']} / {d['category']}  {d['old_score']} -> {d['new_score']}")
    print()


def main():
    HISTORY_DIR.mkdir(exist_ok=True)
    files = load_snapshots()

    if not files:
        print("ERROR: no snapshots found in powerscore-history/. Run scripts/snapshot_powerscore.py first.")
        sys.exit(1)

    if len(sys.argv) >= 3:
        old_path = HISTORY_DIR / f"{sys.argv[1]}.json"
        new_path = HISTORY_DIR / f"{sys.argv[2]}.json"
        if not old_path.exists() or not new_path.exists():
            print(f"ERROR: could not find both {old_path} and {new_path}")
            sys.exit(1)
        is_self_compare = old_path == new_path
    elif len(files) == 1:
        old_path = new_path = files[0]
        is_self_compare = True
    else:
        old_path, new_path = files[-2], files[-1]
        is_self_compare = False

    with open(old_path) as f:
        old_data = json.load(f)
    with open(new_path) as f:
        new_data = json.load(f)

    report = compute_movers(old_data, new_data, old_path.stem, new_path.stem, is_self_compare)

    print_report(report)

    with open(OUT_JSON, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report written: {OUT_JSON}")


if __name__ == "__main__":
    main()
