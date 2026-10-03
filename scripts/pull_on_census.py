#!/usr/bin/env python3
"""Pulls Ontario city housing counts from Statistics Canada 2021 Census table 98-10-0233-01 (WDS API) into data/on-housing-census2021.json.
Same fields as data/bc-housing-census2021.json. Results are keyed by the echoed coordinate, never by request order."""
import json, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
GEO = {"toronto": 2386, "ottawa": 2285, "mississauga": 2388, "brampton": 2389, "hamilton": 2415, "markham": 2376, "vaughan": 2375, "richmond-hill": 2377,
       "barrie": 2557, "london": 2509, "kitchener": 2442, "windsor": 2482, "oakville": 2410, "oshawa": 2368, "whitby": 2367, "burlington": 2411,
       "cambridge": 2441, "greater-sudbury": 2686, "guelph": 2402, "kingston": 2312, "niagara-falls": 2424, "peterborough": 2355,
       "sault-ste-marie": 2757, "thunder-bay": 2776, "timmins": 2717}
def coord(g, p=1, s=1, c=1, t=1): return f"{g}.{p}.{s}.1.{c}.{t}.0.0.0.0"
req = {}
for slug, g in GEO.items():
    req[(slug, "households")] = coord(g)
    for p in range(2, 14): req[(slug, f"period{p}")] = coord(g, p=p)
    req[(slug, "detached")] = coord(g, s=2)
    for sc,nm in ((3,"apt5"),(4,"othatt"),(5,"duplex"),(6,"apt<5"),(7,"othsingle"),(8,"row"),(9,"semi"),(10,"movable")): req[(slug, "st_"+nm)] = coord(g, s=sc)
    req[(slug, "owner")] = coord(g, t=2)
    req[(slug, "renter")] = coord(g, t=3)
    req[(slug, "major")] = coord(g, c=4)
    req[(slug, "minor")] = coord(g, c=3)
    for p in range(2, 8): req[(slug, f"osfh{p}")] = coord(g, p=p, s=2, t=2)
keys = list(req)
out = {}
for i in range(0, len(keys), 150):
    batch = keys[i:i + 150]
    body = json.dumps([{"productId": 98100233, "coordinate": req[k], "latestN": 1} for k in batch]).encode()
    r = urllib.request.Request("https://www150.statcan.gc.ca/t1/wds/rest/getDataFromCubePidCoordAndLatestNPeriods", body, {"Content-Type": "application/json"})
    res = json.load(urllib.request.urlopen(r, timeout=120))
    by = {}
    for x in res:
        o = x["object"]; by[o["coordinate"]] = o["vectorDataPoint"][0]["value"] if o.get("vectorDataPoint") else None
    for k in batch:
        out[k] = by.get(req[k] + "") if req[k] in by else by.get(req[k].rstrip("0.").rstrip("."))
res = {}
miss = [k for k, v in out.items() if v is None]
for slug in GEO:
    g = lambda n: out[(slug, n)]
    res[slug] = {"households": g("households"), "period": {str(p): g(f"period{p}") for p in range(2, 14)}, "major_repairs": g("major"), "minor_repairs": g("minor"),
                 "single_detached": g("detached"), "struct": {nm: (g("st_"+nm) or 0) for nm in ("apt5","othatt","duplex","apt<5","othsingle","row","semi","movable")}, "owner": g("owner"), "renter": g("renter"),
                 "owner_sfh_pre1981": sum(g(f"osfh{p}") or 0 for p in range(2, 7)), "owner_sfh_1981_90": g("osfh7")}
res["_source"] = "Statistics Canada, 2021 Census of Population, table 98-10-0233-01 (WDS API)"
(ROOT / "data/on-housing-census2021.json").write_text(json.dumps(res, indent=1))
print("missing", len(miss), miss[:5])
for s in GEO: print(s, res[s]["households"], res[s]["single_detached"], res[s]["owner"], res[s]["owner_sfh_pre1981"])
