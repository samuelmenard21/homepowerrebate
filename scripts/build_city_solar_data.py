#!/usr/bin/env python3
"""
Solar-irradiance data builder, same pattern as build_city_climate_data.py —
real measured data (Open-Meteo historical archive, no key required) instead
of an estimate, same methodology for every city so numbers are comparable.

Computes average daily shortwave radiation (MJ/m^2) over 5 years and
converts to approximate peak sun hours/day (1 kWh = 3.6 MJ) — the figure
homeowners and installers actually reason about for solar payback.

Output: city-solar-data.json, same "<region>|<city lowercase>" keying as
city-rebate-lookup.json and city-climate-data.json.

Usage:
    python3 scripts/build_city_solar_data.py
    python3 scripts/build_city_solar_data.py --refresh
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
OUT_PATH = ROOT / "city-solar-data.json"

EXTRA_CITIES = [{"key": "ny|mount vernon", "city": "Mount Vernon", "region": "NY"}]


def fetch_solar(lat, lon, tz):
    q = urllib.parse.urlencode({
        "latitude": lat, "longitude": lon,
        "start_date": "2020-01-01", "end_date": "2024-12-31",
        "daily": "shortwave_radiation_sum", "timezone": tz,
    })
    data = http_get_json(f"https://archive-api.open-meteo.com/v1/archive?{q}")
    vals = [v for v in data.get("daily", {}).get("shortwave_radiation_sum", []) if v is not None]
    if not vals:
        return None
    avg_mj = sum(vals) / len(vals)
    return {
        "avg_daily_radiation_mj_m2": round(avg_mj, 2),
        "approx_peak_sun_hours": round(avg_mj / 3.6, 2),
        "sample_years": "2020-2024",
        "sample_days": len(vals),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
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
            solar = fetch_solar(geo["latitude"], geo["longitude"], geo["timezone"])
            if not solar:
                print("SOLAR FETCH FAILED")
                failures.append((key, "archive returned no radiation data"))
                continue
            out[key] = {"city": c["city"], "region": c["region"], "lat": geo["latitude"], "lon": geo["longitude"],
                        "match_quality": quality, **solar}
            flag = "" if quality == "exact" else "  [REVIEW: admin1 mismatch]"
            print(f"OK  {solar['approx_peak_sun_hours']} peak sun hrs/day{flag}")
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
