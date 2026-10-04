#!/usr/bin/env python3
"""Pull housing facts for the New York city category pages from the US Census Bureau ACS 5-year estimates (2020-2024).
api.census.gov now requires a key, so this reads the same Census tables through the Census Reporter API (no key).
Tables: B25001 (housing units), B25003 (tenure), B25024 (units in structure), B25034 (year built), B25040 (house heating fuel).
Writes data/ny-housing-acs.json. Usage: python3 scripts/pull_ny_acs.py"""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE = "acs2024_5yr"
PLACES = {"new-york-city": "16000US3651000", "buffalo": "16000US3611000", "rochester": "16000US3663000", "syracuse": "16000US3673000", "albany": "16000US3601000",
          "beacon": "16000US3605100", "kingston": "16000US3639727", "newburgh": "16000US3650034", "poughkeepsie": "16000US3659641", "mount-vernon": "16000US3649121",
          "new-rochelle": "16000US3650617", "white-plains": "16000US3681677", "yonkers": "16000US3684000", "brookhaven": "06000US3610310000", "babylon": "06000US3610304000",
          "huntington": "06000US3610337000", "islip": "06000US3610338000", "smithtown": "06000US3610368000", "oyster-bay": "06000US3605956000"}
TABLES = ["B25001", "B25003", "B25024", "B25034", "B25040"]


def pct(a, b):
    return round(100.0 * a / b, 1)


def main():
    geos = ",".join(PLACES.values())
    url = f"https://api.censusreporter.org/1.0/data/show/{RELEASE}?table_ids={','.join(TABLES)}&geo_ids={geos}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (HomePowerRebate data pull)"})
    d = json.load(urllib.request.urlopen(req, timeout=90))
    out = {"_source": {"dataset": "US Census Bureau, American Community Survey 5-year estimates 2020-2024",
                       "tables": {"B25001": "Housing Units", "B25003": "Tenure", "B25024": "Units in Structure", "B25034": "Year Structure Built", "B25040": "House Heating Fuel"},
                       "api": url, "via": "Census Reporter API (republishes Census Bureau ACS tables)",
                       "table_url": "https://data.census.gov/table/ACSDT5Y2024.B25040"}, "cities": {}}
    for slug, fips in PLACES.items():
        g = fips
        t = {k: v["estimate"] for k, v in d["data"][g].items()}
        e = lambda tab, n: t[tab][f"{tab}{n:03d}"]
        yb = e("B25034", 1)
        hf = e("B25040", 1)
        ten = e("B25003", 1)
        out["cities"][slug] = {
            "name": d["geography"][g]["name"],
            "housing_units": int(e("B25001", 1)),
            "occupied_units": int(ten),
            "pct_owner": pct(e("B25003", 2), ten), "pct_renter": pct(e("B25003", 3), ten),
            "pct_single_detached": pct(e("B25024", 2), e("B25024", 1)),
            "pct_two_to_four_units": pct(e("B25024", 4) + e("B25024", 5), e("B25024", 1)),
            "pct_built_before_1980": pct(sum(e("B25034", n) for n in range(7, 12)), yb),
            "pct_built_1939_earlier": pct(e("B25034", 11), yb),
            "pct_built_2000_later": pct(sum(e("B25034", n) for n in range(2, 5)), yb),
            "pct_heat_utility_gas": pct(e("B25040", 2), hf), "pct_heat_bottled_gas": pct(e("B25040", 3), hf),
            "pct_heat_electricity": pct(e("B25040", 4), hf), "pct_heat_fuel_oil": pct(e("B25040", 5), hf),
        }
    (ROOT / "data/ny-housing-acs.json").write_text(json.dumps(out, indent=1))
    for k, v in out["cities"].items():
        print(k, v)


if __name__ == "__main__":
    main()
