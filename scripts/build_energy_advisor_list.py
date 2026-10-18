#!/usr/bin/env python3
"""
Energy advisor lists for Canadian cities, from NRCan's official register (added 2026-10-17).

Source of truth: data/nrcan-service-organizations.json, NRCan's table of service organizations licensed to deliver
EnerGuide evaluations for existing homes, each with the postal code areas (FSAs) it serves. Every registered energy
advisor books through one of these. A Google Maps search for "energy advisor" mixes in HVAC dealers, financial
planners and home inspectors, so it is not used to decide who is an advisor.

1. Each city's FSAs come from the postal codes in our installer addresses for that city (plus CITY_FSAS below).
2. An organization serves a city when its FSA list overlaps the city's.
3. Google ratings: one Places Text Search per organization (about 180 calls; ratings are a higher-priced Places field,
   so we never search per city). A result counts only when its name matches the organization's name.
4. data/energy-advisors-extra.json adds advisor firms that told us themselves that they are registered advisors
   working under a service organization's licence (for example Thrive Energy, Kelowna).

US version (home energy auditors): data/resnet-rating-companies-2026.json, RESNET's list of HERS rating companies that
completed ratings in 2025, by state (no cities). One Places search per company gives its address; a company is listed
for every one of our cities in its state within US_RADIUS_KM of its office. Writes <state>-energy-auditor-...csv.

Writes installers/<prefix>energy-advisor-installers-real.csv (the format build_installer_rankings.py reads). Rows with
no Google match keep a blank rating; the ranking page lists them under the ranked ones.

  python3 scripts/build_energy_advisor_list.py            # asks for the Places key (hidden), then writes the CSVs
  python3 scripts/build_energy_advisor_list.py --offline  # reuse data/energy-advisor-places.json, no API calls
"""
import argparse
import collections
import csv
import getpass
import html
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import regions  # noqa: E402

NRCAN = ROOT / "data" / "nrcan-service-organizations.json"
RESNET = ROOT / "data" / "resnet-rating-companies-2026.json"
US_RADIUS_KM = 80   # HERS raters and auditors travel; NRCan lists Canadian service areas the same way
EXTRA = ROOT / "data" / "energy-advisors-extra.json"
CACHE = ROOT / "data" / "energy-advisor-places.json"
DIRECTORY = ROOT / "data" / "energy-advisor-directory.json"   # every company, matched or not (read by build_advisor_directory.py)   # Places matches (place id, rating, review count, website, maps link)
PROV = {"ab": "AB", "bc": "BC", "on": "ON", "ns": "NS", "nl": "NL", "mb": "MB", "sk": "SK", "qc": "QC", "nb": "NB"}
PREFIX = {"bc": ""}   # BC files have no region prefix (installers/energy-advisor-installers-real.csv)
# Cities with no installer addresses to learn FSAs from (Canada Post FSAs for the city itself).
CITY_FSAS = {
    ("nl", "St. John's"): {"A1A", "A1B", "A1C", "A1E", "A1G", "A1H"},
    ("nl", "Mount Pearl"): {"A1N"},
    ("nl", "Paradise"): {"A1L"},
    ("nl", "Corner Brook"): {"A2H"},
    ("nl", "Labrador City"): {"A2V"},
}
SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELDS = ",".join(["places.id", "places.displayName", "places.formattedAddress", "places.rating", "places.userRatingCount",
                   "places.websiteUri", "places.googleMapsUri", "places.nationalPhoneNumber", "places.location"])
STOP = {"inc", "ltd", "ltee", "corp", "corporation", "limited", "co", "the", "and", "of", "canada", "incorporated", "llc"}


def clean_name(n):
    """'Enerhome Consulting Ltd.(Vancouver Island)' -> ('Enerhome Consulting Ltd.', 'Vancouver Island')."""
    n = html.unescape(n).replace("\xa0", " ").strip()
    m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", n)
    return (m.group(1).strip(), m.group(2).strip()) if m else (n, "")


def tokens(n):
    return {t for t in re.findall(r"[a-z0-9]+", n.lower()) if t not in STOP}


# Google matches rejected by hand on 2026-10-17 (a doctor, a tax office, a lawn company... with a similar name).
REJECT = {
    "US-MA|John Hayes", "US-NY|Alexander Schwartz", "US-NJ|Neil Goldman", "US-MA|Victoria Services, Inc.",
    "US-CO|Absolute Green", "US-MA|Outer Cape Energy", "US-NY|Energy Master & Environmental Solutions",
    "US-MA|Associated Energy, LLC", "US-MA|New England Home Energy LLC", "US-NY|PEG, LLC", "US-MA|Konosky Associates Inc",
    "US-WA|Home Builders Association Tri-Cities", "YT|Government of Yukon Energy Mines and Resources",
}
PROVINCE_WORDS = {"alberta", "british columbia", "bc", "ontario", "on", "ab", "sk", "mb", "nb", "ns", "nl", "pei", "national",
                  "saskatchewan", "manitoba", "quebec", "québec", "new brunswick", "nova scotia"}


def branch(where):
    """'Kingston' for 'AmeriSpec of Canada (Kingston)'; '' when the bracket only names a province or 'National'."""
    w = where.lower().strip()
    if not w or w in PROVINCE_WORDS or w.startswith(("nsc", "green communities", "lower mainland", "bc ", "calgary &")):
        return ""
    return where


def google_ok(key, raw, g):
    """A cached match counts unless rejected by hand, and a branch office must be that branch's own listing."""
    if not g.get("place") or key in REJECT:
        return False
    b = branch(clean_name(raw)[1])
    if b:
        words = tokens(b) - {"area", "and", "region", "east", "west", "north", "south"}
        hay = (g.get("name", "") + " " + g.get("address", "")).lower()
        return bool(words) and all(w in hay for w in words)
    return True


def same_business(org, place_name):
    a, b = tokens(org), tokens(place_name)
    if not a or not b:
        return False
    return len(a & b) / len(a) >= 0.67


def city_fsas():
    fsa = collections.defaultdict(set)
    for f in (ROOT / "installers").glob("*-installers-real.csv"):
        m = re.match(r"(?:([a-z]{2})-)?(heat-pump|solar|insulation|battery)-installers-real\.csv$", f.name)
        if not m:
            continue
        reg = m.group(1) or "bc"
        if regions.BY_CODE.get(reg, {}).get("country") != "ca":
            continue
        for r in csv.DictReader(f.open(encoding="utf-8")):
            p = re.search(r"\b([A-Z]\d[A-Z]) ?\d[A-Z]\d\b", r.get("Address", ""))
            if p:
                fsa[(reg, r["City"].strip())].add(p.group(1))
    for k, v in CITY_FSAS.items():
        fsa[k] |= v
    return fsa


def search(key, query):
    import urllib.request
    req = urllib.request.Request(SEARCH_URL, data=json.dumps({"textQuery": query, "maxResultCount": 5}).encode(),
                                 headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": FIELDS, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()).get("places", [])
    except Exception as e:  # one failed lookup leaves that organization unrated
        print(f"   lookup failed for {query!r}: {e}")
        return []


def us_city_coords():
    """Our US cities with coordinates, from the installer scraper's city lists (one list for the whole site)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("scrape", ROOT / "scripts" / "scrape_google_places_installers.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return {code: p["cities"] for code, p in mod.PROVINCES.items() if regions.BY_CODE.get(code, {}).get("country") == "us"}


def km(a, b):
    import math
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def match_entry(hit):
    loc = hit.get("location") or {}
    return {"place": hit.get("id"), "name": hit["displayName"]["text"], "address": hit.get("formattedAddress", ""),
            "rating": hit.get("rating"), "reviews": hit.get("userRatingCount"), "website": hit.get("websiteUri", ""),
            "maps": hit.get("googleMapsUri", ""), "phone": hit.get("nationalPhoneNumber", ""),
            "lat": loc.get("latitude"), "lng": loc.get("longitude")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    orgs = json.loads(NRCAN.read_text())["organizations"]
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    us_cities = us_city_coords()
    resnet = [c for c in json.loads(RESNET.read_text())["companies"] if c["state"].lower() in us_cities]
    want = sorted({(o["p"], o["n"]) for o in orgs} - set(map(tuple, (k.split("|", 1) for k in cache))))
    want_us = [c for c in resnet if f"US-{c['state']}|{c['name']}" not in cache]
    if (want or want_us) and not args.offline:
        key = getpass.getpass(f"Google Places API key for {len(want) + len(want_us)} lookups (hidden, not saved): ").strip()
        for prov, raw in want:
            name, where = clean_name(raw)
            area = "" if where.lower() in ("national", "") or len(where) <= 3 else where
            q = f"{name} {area} {prov} energy advisor".replace("  ", " ")
            hit = next((p for p in search(key, q) if same_business(name, p.get("displayName", {}).get("text", ""))), None)
            cache[f"{prov}|{raw}"] = {"query": q, **(match_entry(hit) if hit else {})}
            print(f"{'match' if hit else '  -  '}  {prov} {name[:45]:<45} {hit['displayName']['text'][:40] if hit else ''}")
            time.sleep(0.2)
        for c in want_us:
            name, _ = clean_name(c["name"])
            q = f"{name} {c['state']}"
            hit = next((p for p in search(key, q) if same_business(name, p.get("displayName", {}).get("text", ""))), None)
            cache[f"US-{c['state']}|{c['name']}"] = {"query": q, **(match_entry(hit) if hit else {})}
            print(f"{'match' if hit else '  -  '}  {c['state']} {name[:45]:<45} {hit['displayName']['text'][:40] if hit else ''}")
            time.sleep(0.2)
        CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False) + "\n")

    fsa = city_fsas()
    extra = json.loads(EXTRA.read_text()) if EXTRA.exists() else []
    today = time.strftime("%Y-%m-%d")
    by_region = collections.defaultdict(list)
    companies = {}

    def company(country, name, **kw):
        c = companies.setdefault((country, name.lower()), {"country": country, "name": name, "regions": [], "phones": {}, "cities": [],
                                                            "website": "", "email": "", "google": None, "sources": []})
        for k in ("website", "email"):
            c[k] = c[k] or kw.get(k, "")
        if kw.get("google") and not c["google"]:
            c["google"] = kw["google"]
        if kw.get("region") and kw["region"] not in c["regions"]:
            c["regions"].append(kw["region"])
        if kw.get("phone") and kw.get("region"):
            c["phones"].setdefault(kw["region"], kw["phone"])
        if kw.get("source") and kw["source"] not in c["sources"]:
            c["sources"].append(kw["source"])
        if kw.get("city") and kw["city"] not in c["cities"]:
            c["cities"].append(kw["city"])
        return c

    def gpub(g):
        return {k: g[k] for k in ("rating", "reviews", "address", "maps", "place") if g.get(k)} if g.get("place") else None

    NR_SRC = "NRCan licensed EnerGuide service organization"
    for o in orgs:   # every NRCan organization goes in the directory, whether or not it serves one of our cities
        name, where = clean_name(o["n"])
        key = f"{o['p']}|{o['n']}"
        g = cache.get(key, {})
        g = g if google_ok(key, o["n"], g) else {}
        if branch(where):
            name = g.get("name") or f"{name} ({where})"
        company("ca", name, region=o["p"], phone=o["ph"].split(",")[0].strip(), website=g.get("website", ""), google=gpub(g), source=NR_SRC)
    for (reg, city), fs in sorted(fsa.items()):
        seen = set()
        for o in orgs:
            if o["p"] != PROV.get(reg) or not fs & set(o["fsa"].split()):
                continue
            name, where = clean_name(o["n"])
            key = f"{o['p']}|{o['n']}"
            g = cache.get(key, {})
            g = g if google_ok(key, o["n"], g) else {}
            if branch(where):   # a branch office: its own Google name, or the NRCan name with the branch
                name = g.get("name") or f"{name} ({where})"
            if name.lower() in seen:   # the same company listed twice for one province
                continue
            seen.add(name.lower())
            company("ca", name, city=[reg, city])
            by_region[reg].append({
                "City": city, "Business Name": name, "Address": g.get("address", ""), "Phone": o["ph"].split(",")[0].strip(),
                "Email": "", "Website": g.get("website", ""), "Image URL": "", "Google Rating": g.get("rating") or "",
                "Review Count": g.get("reviews") or "", "Google Maps URL": g.get("maps", ""), "HomePowerRebate Recommended": "No",
                "Notes": "NRCan licensed service organization", "Last Updated": today})
        for e in extra:
            if e["region"] == reg and e["city"] == city and e["name"].lower() not in seen:
                company("ca", e["name"], region=PROV[reg], phone=e.get("phone", ""), website=e.get("website", ""), email=e.get("email", ""),
                        google={"rating": float(e["rating"]), "reviews": int(e["reviews"]), "address": e.get("address", ""), "maps": e.get("maps", "")}
                        if e.get("rating") else None, source=e.get("note", "Registered energy advisor (confirmed by the company)"), city=[reg, city])
                by_region[reg].append({
                    "City": city, "Business Name": e["name"], "Address": e.get("address", ""), "Phone": e.get("phone", ""),
                    "Email": e.get("email", ""), "Website": e.get("website", ""), "Image URL": "", "Google Rating": e.get("rating", ""),
                    "Review Count": e.get("reviews", ""), "Google Maps URL": e.get("maps", ""), "HomePowerRebate Recommended": "No",
                    "Notes": e.get("note", "Registered energy advisor (confirmed by the company)"), "Last Updated": e.get("updated", today)})
    # US: each RESNET company is listed for every one of our cities in its state within US_RADIUS_KM of its office.
    for c in resnet:
        key = f"US-{c['state']}|{c['name']}"
        g = cache.get(key, {})
        g = g if google_ok(key, c["name"], g) else {}
        reg = c["state"].lower()
        name, _ = clean_name(c["name"])
        site = c.get("website") or g.get("website", "")
        company("us", name, region=c["state"], phone=g.get("phone", ""), website=site if not site or site.startswith("http") else "https://" + site,
                email=c.get("email", ""), google=gpub(g), source="RESNET HERS rating company (2026 list)")
        if not g.get("lat") or reg not in us_cities:
            continue
        for city, xy in us_cities[reg].items():
            if km((g["lat"], g["lng"]), (xy["lat"], xy["lng"])) > US_RADIUS_KM:
                continue
            company("us", name, city=[reg, city])
            by_region[("us", reg)].append({
                "City": city, "Business Name": name, "Address": g.get("address", ""), "Phone": g.get("phone", ""),
                "Email": c.get("email", ""), "Website": c.get("website") or g.get("website", ""), "Image URL": "",
                "Google Rating": g.get("rating") or "", "Review Count": g.get("reviews") or "", "Google Maps URL": g.get("maps", ""),
                "HomePowerRebate Recommended": "No", "Notes": "RESNET HERS rating company (2026 list)", "Last Updated": today})
    DIRECTORY.write_text(json.dumps({"built": today, "sources": {
        "nrcan": json.loads(NRCAN.read_text())["source_url"], "resnet": json.loads(RESNET.read_text())["source_url"]},
        "companies": sorted(companies.values(), key=lambda c: (c["country"], c["name"].lower()))}, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(companies)} companies in {DIRECTORY.name}")
    header = ["City", "Business Name", "Address", "Phone", "Email", "Website", "Image URL", "Google Rating", "Review Count",
              "Google Maps URL", "HomePowerRebate Recommended", "Notes", "Last Updated"]
    for reg, rows in by_region.items():
        if isinstance(reg, tuple):
            out = ROOT / "installers" / f"{reg[1]}-energy-auditor-installers-real.csv"
        else:
            out = ROOT / "installers" / f"{PREFIX.get(reg, reg + '-')}energy-advisor-installers-real.csv"
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            w.writerows(rows)
        rated = sum(1 for r in rows if r["Google Rating"])
        print(f"{out.name}: {len(rows)} city listings, {rated} with a Google rating")


if __name__ == "__main__":
    main()
