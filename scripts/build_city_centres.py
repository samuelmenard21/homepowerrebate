#!/usr/bin/env python3
"""City centre coordinates for the heat pump near-me finder (2026-11-04).

Own data, one point per ranked heat pump city, used only in the visitor's browser to pick the nearest city (nothing is stored or sent).
Reads lat/lon from city-climate-data.json (Open-Meteo geocoding, already in the repo) and geocodes the cities it lacks with the same
public Open-Meteo geocoder, checking the state. Not Google Places data. Writes data/city-centres.json (git add -f).
Usage: python3 scripts/build_city_centres.py"""
import json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_heat_pump_hub as hub  # noqa: E402

STATE = {"il": "Illinois", "mi": "Michigan", "mn": "Minnesota", "nj": "New Jersey", "wa": "Washington"}
norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower().replace(".", "")).strip()


def geocode(name, state):
    q = urllib.parse.urlencode({"name": name, "count": 10, "country_code": "US"})
    with urllib.request.urlopen(f"https://geocoding-api.open-meteo.com/v1/search?{q}", timeout=20) as r:
        res = json.load(r).get("results", [])
    res = [x for x in res if x.get("admin1") == state and norm(x["name"]) == norm(name)]
    if not res:
        raise SystemExit(f"no geocode for {name}, {state}")
    x = max(res, key=lambda x: x.get("population", 0))
    return round(x["latitude"], 4), round(x["longitude"], 4)


def main():
    cl = json.loads((ROOT / "city-climate-data.json").read_text(encoding="utf-8"))
    idx = {(k.split("|")[0], norm(k.split("|")[1])): v for k, v in cl.items()}
    out = {}
    for c in hub.city_rows():
        v = idx.get((c["region"], norm(c["city"])))
        if v:
            pt = [round(v["lat"], 4), round(v["lon"], 4)]
        else:
            pt = list(geocode(c["city"], STATE[c["region"]])); time.sleep(0.3)
        out[c["url"]] = pt
    (ROOT / "data" / "city-centres.json").write_text(json.dumps(out, indent=0), encoding="utf-8")
    print(len(out), "cities")


if __name__ == "__main__":
    main()
