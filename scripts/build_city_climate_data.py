#!/usr/bin/env python3
"""
Layer 2 (climate) data builder for the category-page-localization playbook.

Geocodes every city in city-rebate-lookup.json (plus any known gaps, e.g.
Mount Vernon NY which is missing from that file) via the free Open-Meteo
geocoding API, disambiguated by province/state so "Mount Vernon" doesn't
resolve to the wrong one of several US cities with that name. Then pulls
10 years of real daily-minimum-temperature history from Open-Meteo's
historical archive API (no key required) and computes:
  - avg_january_low: mean daily low across every January in the window
  - coldest_recorded: the single coldest day in the window

This is real measured data, not a generated/estimated figure, and every
city goes through the same methodology so the numbers are comparable
against each other (unlike hand-pulling one city from a web search and
another from a different source).

Output: city-climate-data.json, keyed the same way as
city-rebate-lookup.json ("<region>|<city lowercase>"), so it can be
applied by a parallel script the same way apply_layer1_utility_data.py
applies the utility lookup.

Usage:
    python3 scripts/build_city_climate_data.py            # build/update
    python3 scripts/build_city_climate_data.py --refresh   # re-fetch all, ignore cache
"""
import argparse
import json
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _geocode_util import geocode, http_get_json  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LOOKUP_PATH = ROOT / "city-rebate-lookup.json"
OUT_PATH = ROOT / "city-climate-data.json"

# Known gap: not in city-rebate-lookup.json but has live pages (see
# apply_layer1_utility_data.py's UTILITY_DIR_NAMES fallback for the same gap).
EXTRA_CITIES = [
    {"key": "ny|mount vernon", "city": "Mount Vernon", "region": "NY"},
]


def fetch_climate(lat, lon, tz):
    q = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "start_date": "2015-01-01", "end_date": "2024-12-31",
        "daily": "temperature_2m_min", "timezone": tz,
    })
    data = http_get_json(f"https://archive-api.open-meteo.com/v1/archive?{q}")
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    temps = daily.get("temperature_2m_min", [])
    jan = [t for d, t in zip(dates, temps) if d[5:7] == "01" and t is not None]
    all_valid = [t for t in temps if t is not None]
    if not jan or not all_valid:
        return None
    return {
        "avg_january_low_c": round(sum(jan) / len(jan), 1),
        "coldest_recorded_c": round(min(all_valid), 1),
        "sample_years": "2015-2024",
        "sample_january_days": len(jan),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="ignore existing output, re-fetch everything")
    args = ap.parse_args()

    lookup = json.loads(LOOKUP_PATH.read_text())
    cities = [{"key": k, "city": v["city"], "region": v["region"]} for k, v in lookup.items()]
    cities += EXTRA_CITIES

    existing = {}
    if OUT_PATH.exists() and not args.refresh:
        existing = json.loads(OUT_PATH.read_text())

    out = dict(existing)
    failures = []

    for i, c in enumerate(cities):
        key = c["key"]
        if key in existing and not args.refresh:
            continue

        region_code = key.split("|")[0]
        print(f"[{i+1}/{len(cities)}] {c['city']}, {c['region']}...", end=" ", flush=True)
        try:
            geo, quality = geocode(c["city"], region_code)
            if not geo:
                print("GEOCODE FAILED (no result in expected country)")
                failures.append((key, "no geocode result in expected country"))
                continue
            climate = fetch_climate(geo["latitude"], geo["longitude"], geo["timezone"])
            if not climate:
                print("CLIMATE FETCH FAILED")
                failures.append((key, "climate archive returned no data"))
                continue
            out[key] = {
                "city": c["city"],
                "region": c["region"],
                "lat": geo["latitude"],
                "lon": geo["longitude"],
                "geocoded_admin1": geo.get("admin1"),
                "geocoded_country": geo.get("country_code"),
                "match_quality": quality,
                **climate,
            }
            flag = "" if quality == "exact" else "  [REVIEW: admin1 mismatch]"
            print(f"OK  avg Jan low {climate['avg_january_low_c']}C, coldest {climate['coldest_recorded_c']}C  "
                  f"(matched: {geo.get('admin1')}, {geo.get('country_code')}){flag}")
        except Exception as e:
            print(f"ERROR: {e}")
            failures.append((key, str(e)))
        time.sleep(1.2)  # be polite to the free API (0.3s hit 429s in practice)

    OUT_PATH.write_text(json.dumps(out, indent=2, sort_keys=True))
    print(f"\nWrote {len(out)} cities to {OUT_PATH.relative_to(ROOT)}")
    if failures:
        print(f"\n{len(failures)} failures:")
        for key, reason in failures:
            print(f"  {key}: {reason}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
