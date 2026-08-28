#!/usr/bin/env python3
"""
Scrape REAL heat pump (HVAC) and solar installers from Google Places API (NEW v1).
Writes directly to the HomePowerRebate-Installers Google Sheet.

Usage:
  python3 scrape_google_places_installers.py heat-pump --province=on
      (no key on the command line — you'll be prompted, input hidden, nothing saved)
  python3 scrape_google_places_installers.py YOUR_API_KEY heat-pump --province=on --debug
      (key still accepted as an explicit first argument if you prefer)

Notes:
  - Uses the NEW Places API (v1) searchText endpoint.
  - REQUIRES an X-Goog-FieldMask header (that was the bug before).
  - Field names are the NEW API names: userRatingCount, nationalPhoneNumber, etc.
  - One searchText call returns everything we need — no separate details call.
"""

import sys
import time
import getpass
import requests
from pathlib import Path

# Optional: Google Sheets write
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
RATE_LIMIT_DELAY = 0.3

# The exact Google Sheet to write to (ID from its URL). Targeting by ID — not by
# name — guarantees we hit THIS sheet and never accidentally create/find another.
SHEET_ID = "11YrVuRF2xutjeaPlL9zwd2LwzmBAxfFujFGMdadph-4"

# Filter criteria
MIN_RATING = 4.0
MIN_REVIEWS = 10
MAX_PER_CITY = 5

# Fields we want back from searchText. This IS the required field mask.
FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.rating",
    "places.userRatingCount",
    "places.nationalPhoneNumber",
    "places.websiteUri",
    "places.googleMapsUri",
    "places.primaryType",
    "places.photos",
])

# Google Places API does NOT return email addresses — column left blank on purpose.
PHOTO_MAX_PX = 640

# --- Business-type filtering ----------------------------------------------
# Keep only businesses that actually install/service the equipment. We check
# the NEW API's primaryType AND the business name, because Google's typing is
# inconsistent (many legit HVAC shops are typed "plumber").
HEATPUMP_GOOD_TYPES = {
    "hvac_contractor", "heating_contractor", "air_conditioning_contractor",
    "plumber", "general_contractor",
}
HEATPUMP_GOOD_WORDS = (
    "heating", "cooling", "hvac", "furnace", "air condition", "heat pump",
    "mechanical", "refrigeration", "gas",
)
SOLAR_GOOD_TYPES = {"solar_energy_contractor", "electrician", "general_contractor"}
SOLAR_GOOD_WORDS = ("solar", "photovoltaic", "pv ", "renewable", "energy")

INSULATION_GOOD_TYPES = {"insulation_contractor", "general_contractor"}
INSULATION_GOOD_WORDS = (
    "insulation", "spray foam", "attic", "weatherization", "air sealing",
    "batt", "blown-in", "blown in",
)

WINDOWS_GOOD_TYPES = {"general_contractor", "window_installation_service", "door_shop"}
WINDOWS_GOOD_WORDS = (
    "window", "door", "glazing", "glass", "fenestration",
)

EV_CHARGER_GOOD_TYPES = {"electrician", "general_contractor"}
EV_CHARGER_GOOD_WORDS = (
    "electric", "electrical", "ev charg", "charging station", "wiring",
)

# Reject these for every trade — they're never installers, just adjacent
# noise (duct cleaning shops, supply houses, real estate, etc.). Trade-specific
# words that used to sit in this generic list (insulation, window) now live
# in each trade's own GOOD_WORDS instead, since those are exactly what we
# want to find when searching for insulation/window installers.
BAD_WORDS = (
    "duct cleaning", "restoration", "supply", "supplies", "handyman",
    "appliance repair", "roofing", "chimney",
    "real estate", "property manage",
)

BC_CITIES = {
    "Abbotsford": {"lat": 49.0504, "lng": -122.3045},
    "Burnaby": {"lat": 49.2503, "lng": -122.9712},
    "Chilliwack": {"lat": 49.1667, "lng": -122.1},
    "Coquitlam": {"lat": 49.2851, "lng": -122.7876},
    "Fort St. John": {"lat": 56.2500, "lng": -120.8467},
    "Kamloops": {"lat": 50.0754, "lng": -120.3045},
    "Kelowna": {"lat": 49.8866, "lng": -119.4961},
    "Langley": {"lat": 49.1042, "lng": -122.6598},
    "Maple Ridge": {"lat": 49.1956, "lng": -122.5948},
    "Nanaimo": {"lat": 49.1604, "lng": -123.9506},
    "Penticton": {"lat": 49.4927, "lng": -119.5871},
    "Prince George": {"lat": 53.9167, "lng": -122.3},
    "Richmond": {"lat": 49.1667, "lng": -123.1333},
    "Squamish": {"lat": 49.7161, "lng": -123.1563},
    "Surrey": {"lat": 49.0504, "lng": -122.5045},
    "Vancouver": {"lat": 49.2827, "lng": -123.1207},
    "Vernon": {"lat": 50.2667, "lng": -119.2667},
    "Victoria": {"lat": 48.4261, "lng": -123.3597},
}

ONTARIO_CITIES = {
    "Toronto": {"lat": 43.6532, "lng": -79.3832},
    "Ottawa": {"lat": 45.4215, "lng": -75.6972},
    "Mississauga": {"lat": 43.5890, "lng": -79.6441},
    "Brampton": {"lat": 43.7315, "lng": -79.7624},
    "Hamilton": {"lat": 43.2557, "lng": -79.8711},
    "Markham": {"lat": 43.8561, "lng": -79.3370},
    "Vaughan": {"lat": 43.8361, "lng": -79.4985},
    "Richmond Hill": {"lat": 43.8828, "lng": -79.4403},
    "Barrie": {"lat": 44.3894, "lng": -79.6903},
    "London": {"lat": 42.9849, "lng": -81.2453},
    "Kitchener": {"lat": 43.4516, "lng": -80.4925},
    "Windsor": {"lat": 42.3149, "lng": -83.0364},
    "Oakville": {"lat": 43.4675, "lng": -79.6877},
    "Oshawa": {"lat": 43.8971, "lng": -78.8658},
    "Whitby": {"lat": 43.8975, "lng": -78.9428},
    "Burlington": {"lat": 43.3255, "lng": -79.7990},
    "Cambridge": {"lat": 43.3616, "lng": -80.3144},
    "Greater Sudbury": {"lat": 46.4917, "lng": -80.9930},
}

ALBERTA_CITIES = {
    "Calgary": {"lat": 51.0447, "lng": -114.0719},
    "Edmonton": {"lat": 53.5461, "lng": -113.4938},
    "Red Deer": {"lat": 52.2681, "lng": -113.8112},
    "Lethbridge": {"lat": 49.6956, "lng": -112.8451},
    "St. Albert": {"lat": 53.6303, "lng": -113.6256},
}

NOVA_SCOTIA_CITIES = {
    "Halifax": {"lat": 44.6488, "lng": -63.5752},
}

MASSACHUSETTS_CITIES = {
    "Boston": {"lat": 42.3601, "lng": -71.0589},
    "Worcester": {"lat": 42.2626, "lng": -71.8023},
    "Springfield": {"lat": 42.1015, "lng": -72.5898},
    "Cambridge": {"lat": 42.3736, "lng": -71.1097},
    "Lowell": {"lat": 42.6334, "lng": -71.3162},
    "Brockton": {"lat": 42.0834, "lng": -71.0184},
    "New Bedford": {"lat": 41.6362, "lng": -70.9342},
    "Quincy": {"lat": 42.2529, "lng": -71.0023},
    "Lynn": {"lat": 42.4668, "lng": -70.9495},
    "Fall River": {"lat": 41.7015, "lng": -71.1550},
    "Newton": {"lat": 42.3370, "lng": -71.2092},
    "Somerville": {"lat": 42.3876, "lng": -71.0995},
}

NY_CITIES = {
    "Beacon": {"lat": 41.5048, "lng": -73.9696},
    "Kingston": {"lat": 41.9270, "lng": -73.9974},
    "Newburgh": {"lat": 41.5034, "lng": -74.0104},
    "Poughkeepsie": {"lat": 41.7004, "lng": -73.9210},
    "Saugerties": {"lat": 42.0787, "lng": -73.9526},
    "Mount Vernon": {"lat": 40.9126, "lng": -73.8371},
    "New Rochelle": {"lat": 40.9115, "lng": -73.7823},
    "New York City": {"lat": 40.7128, "lng": -74.0060},
    "White Plains": {"lat": 41.0340, "lng": -73.7629},
    "Yonkers": {"lat": 40.9312, "lng": -73.8988},
    "Albany": {"lat": 42.6526, "lng": -73.7562},
    "Buffalo": {"lat": 42.8864, "lng": -78.8784},
    "Rochester": {"lat": 43.1566, "lng": -77.6088},
    "Syracuse": {"lat": 43.0481, "lng": -76.1474},
    "Babylon": {"lat": 40.6987, "lng": -73.3256},
    "Brookhaven": {"lat": 40.8720, "lng": -72.9812},
    "Huntington": {"lat": 40.8676, "lng": -73.4257},
    "Islip": {"lat": 40.7301, "lng": -73.2101},
    "Oyster Bay": {"lat": 40.8757, "lng": -73.5323},
    "Smithtown": {"lat": 40.8557, "lng": -73.2004},
    "Southampton": {"lat": 40.8848, "lng": -72.3893},
}

CA_CITIES = {
    "Burbank": {"lat": 34.1808, "lng": -118.3090},
    "Glendale": {"lat": 34.1425, "lng": -118.2551},
    "Long Beach": {"lat": 33.7701, "lng": -118.1937},
    "Los Angeles": {"lat": 34.0522, "lng": -118.2437},
    "Pasadena": {"lat": 34.1478, "lng": -118.1445},
    "Santa Monica": {"lat": 34.0195, "lng": -118.4912},
    "Berkeley": {"lat": 37.8715, "lng": -122.2730},
    "Fremont": {"lat": 37.5485, "lng": -121.9886},
    "Oakland": {"lat": 37.8044, "lng": -122.2712},
    "San Francisco": {"lat": 37.7749, "lng": -122.4194},
    "San Jose": {"lat": 37.3382, "lng": -121.8863},
    "Moreno Valley": {"lat": 33.9425, "lng": -117.2297},
    "Ontario": {"lat": 34.0633, "lng": -117.6509},
    "Riverside": {"lat": 33.9806, "lng": -117.3755},
    "San Bernardino": {"lat": 34.1083, "lng": -117.2898},
    "Chula Vista": {"lat": 32.6401, "lng": -117.0842},
    "Escondido": {"lat": 33.1192, "lng": -117.0864},
    "San Diego": {"lat": 32.7157, "lng": -117.1611},
    "Folsom": {"lat": 38.6779, "lng": -121.1761},
    "Rancho Cordova": {"lat": 38.5891, "lng": -121.3027},
    "Roseville": {"lat": 38.7521, "lng": -121.2880},
    "Sacramento": {"lat": 38.5816, "lng": -121.4944},
}

PENNSYLVANIA_CITIES = {
    "Philadelphia": {"lat": 39.9526, "lng": -75.1652},
    "Pittsburgh": {"lat": 40.4406, "lng": -79.9959},
    "Allentown": {"lat": 40.6084, "lng": -75.4902},
    "Erie": {"lat": 42.1292, "lng": -80.0851},
}

COLORADO_CITIES = {
    "Denver": {"lat": 39.7392, "lng": -104.9903},
    "Colorado Springs": {"lat": 38.8339, "lng": -104.8214},
    "Aurora": {"lat": 39.7294, "lng": -104.8319},
    "Fort Collins": {"lat": 40.5853, "lng": -105.0844},
    "Boulder": {"lat": 40.0150, "lng": -105.2705},
}

VERMONT_CITIES = {
    "Burlington": {"lat": 44.4759, "lng": -73.2121},
    "South Burlington": {"lat": 44.4670, "lng": -73.1709},
    "Rutland": {"lat": 43.6106, "lng": -72.9726},
    "Barre": {"lat": 44.1970, "lng": -72.5020},
    "Montpelier": {"lat": 44.2601, "lng": -72.5754},
}

PROVINCES = {
    "bc": {"cities": BC_CITIES, "abbrev": "BC", "csv_prefix": ""},
    "pa": {"cities": PENNSYLVANIA_CITIES, "abbrev": "PA", "csv_prefix": "pa-"},
    "co": {"cities": COLORADO_CITIES, "abbrev": "CO", "csv_prefix": "co-"},
    "vt": {"cities": VERMONT_CITIES, "abbrev": "VT", "csv_prefix": "vt-"},
    "on": {"cities": ONTARIO_CITIES, "abbrev": "ON", "csv_prefix": "on-"},
    "ab": {"cities": ALBERTA_CITIES, "abbrev": "AB", "csv_prefix": "ab-"},
    "ns": {"cities": NOVA_SCOTIA_CITIES, "abbrev": "NS", "csv_prefix": "ns-"},
    "ma": {"cities": MASSACHUSETTS_CITIES, "abbrev": "MA", "csv_prefix": "ma-"},
    "ny": {"cities": NY_CITIES, "abbrev": "NY", "csv_prefix": "ny-"},
    "ca": {"cities": CA_CITIES, "abbrev": "CA", "csv_prefix": "ca-"},
}


def search_text(api_key, query, lat, lng, debug=False):
    """One searchText call. Returns list of place dicts (NEW API shape)."""
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,   # <-- REQUIRED. Without this you get HTTP 400.
        "Content-Type": "application/json",
    }
    payload = {
        "textQuery": query,
        "locationBias": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": 25000.0,
            }
        },
        "maxResultCount": 20,
    }

    try:
        resp = requests.post(SEARCH_URL, json=payload, headers=headers, timeout=10)
        if resp.status_code != 200:
            if debug:
                print(f"    HTTP {resp.status_code}: {resp.text[:300]}")
            return []
        return resp.json().get("places", [])
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"    request error: {e}")
        return []


def display_name_text(place):
    """displayName in the NEW API is {'text': ..., 'languageCode': ...}."""
    dn = place.get("displayName", {})
    if isinstance(dn, dict):
        return dn.get("text", "")
    return str(dn or "")


def city_from_address(address, cities):
    """
    Return the cities-dict key that appears in this address, or None.
    Normalizes periods so 'Fort St John' matches 'Fort St. John'.
    """
    norm = address.lower().replace(".", "")
    for city in cities:
        if city.lower().replace(".", "") in norm:
            return city
    return None


def is_relevant_installer(name, primary_type, installer_type):
    """
    Decide whether a business is actually an installer for this service.
    Rejects adjacent trades (duct cleaning, supply houses, electricians-only,
    restoration, etc.) and requires a positive HVAC/solar signal.
    """
    name_l = name.lower()

    # Hard reject adjacent trades.
    for bad in BAD_WORDS:
        if bad in name_l:
            return False

    type_map = {
        "solar": (SOLAR_GOOD_TYPES, SOLAR_GOOD_WORDS),
        "insulation": (INSULATION_GOOD_TYPES, INSULATION_GOOD_WORDS),
        "windows-doors": (WINDOWS_GOOD_TYPES, WINDOWS_GOOD_WORDS),
        "ev-charger": (EV_CHARGER_GOOD_TYPES, EV_CHARGER_GOOD_WORDS),
    }
    good_types, good_words = type_map.get(installer_type, (HEATPUMP_GOOD_TYPES, HEATPUMP_GOOD_WORDS))

    if primary_type in good_types:
        return True
    return any(w in name_l for w in good_words)


def resolve_photo_url(api_key, photo_name, debug=False):
    """
    Turn a photo resource name (places/XXX/photos/YYY) into a usable image URL.
    Uses skipHttpRedirect=true so we get back a clean googleusercontent.com URL
    (no API key baked into the link we store / put on the website).
    """
    if not photo_name:
        return ""
    url = f"https://places.googleapis.com/v1/{photo_name}/media"
    try:
        resp = requests.get(
            url,
            params={
                "maxWidthPx": PHOTO_MAX_PX,
                "skipHttpRedirect": "true",
                "key": api_key,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            if debug:
                print(f"      photo HTTP {resp.status_code}: {resp.text[:150]}")
            return ""
        return resp.json().get("photoUri", "")
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"      photo error: {e}")
        return ""


def scrape_installers(api_key, installer_type, province="bc", debug=False):
    all_installers = []

    prov = PROVINCES[province]
    cities = prov["cities"]
    prov_abbrev = prov["abbrev"]

    if "heat" in installer_type or "pump" in installer_type:
        queries = ["HVAC contractor", "heating contractor", "furnace repair"]
    elif "solar" in installer_type:
        queries = ["solar installer", "solar panel installation", "solar energy company"]
    elif installer_type == "insulation":
        queries = ["insulation contractor", "attic insulation company", "spray foam insulation"]
    elif installer_type == "windows-doors":
        queries = ["window installation company", "window and door company", "replacement windows"]
    elif installer_type == "ev-charger":
        queries = ["electrician", "ev charger installation", "electrical contractor"]
    else:
        print(f"Unknown type: {installer_type}")
        return []

    print(f"\n🔍 Searching {installer_type} installers across {len(cities)} {prov_abbrev} cities")
    print(f"   Queries: {queries}")
    print(f"   Criteria: {MIN_RATING}+ stars, {MIN_REVIEWS}+ reviews, max {MAX_PER_CITY} per city")
    print(f"   Filters: real installer types only, assigned to actual city, no cross-city dupes\n")

    # Phase 1 — gather every qualified, relevant business GLOBALLY (dedupe by place_id).
    global_found = {}  # place_id -> installer dict
    n_rejected_type = 0
    n_rejected_offlist = 0

    for city_name, coords in cities.items():
        print(f"  searching near {city_name}...", end=" ", flush=True)
        new_here = 0

        for query in queries:
            full_query = f"{query} in {city_name} {prov_abbrev}"
            time.sleep(RATE_LIMIT_DELAY)
            places = search_text(api_key, full_query, coords["lat"], coords["lng"], debug=debug)

            for p in places:
                pid = p.get("id", "")
                if not pid or pid in global_found:
                    continue

                rating = p.get("rating", 0) or 0
                reviews = p.get("userRatingCount", 0) or 0
                if rating < MIN_RATING or reviews < MIN_REVIEWS:
                    continue

                name = display_name_text(p)
                primary_type = p.get("primaryType", "")

                # Reject adjacent trades / wrong business types.
                if not is_relevant_installer(name, primary_type, installer_type):
                    n_rejected_type += 1
                    if debug:
                        print(f"\n      ✗ type-reject: {name[:40]} ({primary_type})", end="")
                    continue

                # Assign to the ACTUAL city from the address (not the search city).
                address = p.get("formattedAddress", "")
                actual_city = city_from_address(address, cities)
                if actual_city is None:
                    # Business is outside our target cities — skip it.
                    n_rejected_offlist += 1
                    if debug:
                        print(f"\n      ✗ off-list city: {name[:40]} ({address[:40]})", end="")
                    continue

                photos = p.get("photos", []) or []
                photo_name = photos[0].get("name", "") if photos else ""

                global_found[pid] = {
                    "city": actual_city,
                    "name": name,
                    "address": address,
                    "phone": p.get("nationalPhoneNumber", ""),
                    "email": "",  # Places API can't provide this
                    "website": p.get("websiteUri", ""),
                    "rating": rating,
                    "review_count": reviews,
                    "gmaps_url": p.get("googleMapsUri", ""),
                    "photo_name": photo_name,
                    "image_url": "",
                    "recommended": False,  # set for the top pick per city below
                    "type": installer_type,
                }
                new_here += 1

        print(f"{new_here} new")

    # Phase 2 — group by actual city, take the top N per city.
    by_city = {}
    for inst in global_found.values():
        by_city.setdefault(inst["city"], []).append(inst)

    print(f"\n📋 Selecting top {MAX_PER_CITY} per city "
          f"({n_rejected_type} wrong-type + {n_rejected_offlist} off-list rejected)\n")

    for city_name in cities:
        ranked = sorted(
            by_city.get(city_name, []),
            key=lambda x: (-x["rating"], -x["review_count"]),
        )[:MAX_PER_CITY]

        # Auto-recommend the top pick per city (highest rating, then most reviews).
        # This seeds the "Recommended" tab; you can override in the Sheet later.
        if ranked:
            ranked[0]["recommended"] = True

        # Resolve photos for just the survivors (keeps API calls low).
        for inst in ranked:
            if inst["photo_name"]:
                time.sleep(RATE_LIMIT_DELAY)
                inst["image_url"] = resolve_photo_url(api_key, inst["photo_name"], debug=debug)

        all_installers.extend(ranked)
        n_photos = sum(1 for i in ranked if i["image_url"])
        status = f"✓ {len(ranked)}" if ranked else "⚠️  0"
        print(f"  {city_name}... {status} qualified ({n_photos} with photos)")

    return all_installers


def save_to_csv(installers, installer_type, province="bc"):
    prefix = PROVINCES[province]["csv_prefix"]
    csv_path = Path(f"installers/{prefix}{installer_type}-installers-real.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    def esc(v):
        s = str(v)
        if "," in s or '"' in s:
            s = '"' + s.replace('"', '""') + '"'
        return s

    with open(csv_path, "w") as f:
        f.write("City,Business Name,Address,Phone,Email,Website,Image URL,Google Rating,Review Count,Google Maps URL,HomePowerRebate Recommended,Notes,Last Updated\n")
        for i in installers:
            f.write(",".join(esc(x) for x in [
                i["city"], i["name"], i["address"], i["phone"], i["email"],
                i["website"], i["image_url"], i["rating"], i["review_count"],
                i["gmaps_url"], "Yes" if i.get("recommended") else "No", "",
                time.strftime("%Y-%m-%d"),
            ]) + "\n")

    print(f"\n✓ Saved backup CSV: {csv_path}")


SHEET_HEADER = ["City", "Business Name", "Address", "Phone", "Email", "Website",
                "Image URL", "Google Rating", "Review Count", "Google Maps URL",
                "HomePowerRebate Recommended", "Notes", "Last Updated"]

LOG_TAB = "Installer Log"
LOG_HEADER = ["Date Added", "Service", "City", "Business Name", "Phone",
              "Website", "Rating", "Reviews", "Google Maps URL"]


def tab_name_for(installer_type, province="bc"):
    """Each service+province gets its own tab so runs don't overwrite each other.
    BC keeps its original unsuffixed tab names (no change to existing data);
    Ontario gets its own tabs so a run here can never clear BC's real data."""
    base = "Solar" if "solar" in installer_type else "Heat Pumps"
    return base if province == "bc" else f"{base} - {PROVINCES[province]['abbrev']}"


def installer_key(inst):
    """Stable identity for an installer across runs (for de-duping the log)."""
    return inst.get("gmaps_url") or f"{inst.get('name','')}|{inst.get('city','')}"


def append_to_log(spreadsheet, installers, installer_type):
    """
    Append-only audit trail: records every installer ever added, with the date.
    Never cleared. Re-runs only add installers not already logged, so your
    history is preserved even when the live 'Heat Pumps'/'Solar' tabs refresh.
    """
    try:
        try:
            log_ws = spreadsheet.worksheet(LOG_TAB)
        except gspread.WorksheetNotFound:
            log_ws = spreadsheet.add_worksheet(title=LOG_TAB, rows=1000, cols=len(LOG_HEADER))
            log_ws.update(values=[LOG_HEADER], range_name="A1")

        # Which installers are already logged? (dedupe by Google Maps URL / name+city)
        existing = log_ws.get_all_values()
        logged_keys = set()
        for row in existing[1:]:  # skip header
            gmaps = row[8] if len(row) > 8 else ""
            name = row[3] if len(row) > 3 else ""
            city = row[2] if len(row) > 2 else ""
            logged_keys.add(gmaps or f"{name}|{city}")

        today = time.strftime("%Y-%m-%d")
        service = "Solar" if "solar" in installer_type else "Heat Pump"
        new_rows = []
        for i in installers:
            if installer_key(i) in logged_keys:
                continue
            new_rows.append([
                today, service, i["city"], i["name"], i["phone"],
                i["website"], i["rating"], i["review_count"], i["gmaps_url"],
            ])

        if new_rows:
            log_ws.append_rows(new_rows)
            print(f"🗒️  Logged {len(new_rows)} new installer(s) to '{LOG_TAB}' "
                  f"(record now preserved across runs)")
        else:
            print(f"🗒️  No new installers to log (all already in '{LOG_TAB}')")
        return True
    except Exception as e:
        print(f"⚠️  Log write skipped: {e}")
        return False


def remove_stale_sheet1(spreadsheet):
    """
    Delete the old default 'Sheet1' (held the original synthetic data) once real
    data lives in the named service tabs. Guards: never delete the last sheet,
    and never touch anything other than a tab literally named 'Sheet1'.
    """
    try:
        titles = [ws.title for ws in spreadsheet.worksheets()]
        if "Sheet1" in titles and len(titles) > 1:
            spreadsheet.del_worksheet(spreadsheet.worksheet("Sheet1"))
            print("🧹 Removed stale 'Sheet1' (old placeholder data)")
    except Exception as e:
        print(f"⚠️  Could not remove Sheet1: {e}")


def write_to_google_sheet(installers, installer_type, province="bc"):
    if not GSPREAD_AVAILABLE:
        print("⚠️  gspread not installed — skipping Sheet write (CSV still saved).")
        print("   pip install gspread google-auth-oauthlib")
        return False

    # Look in the common locations (repo root and installers/).
    creds_path = None
    for candidate in [Path("google-credentials.json"), Path("installers/google-credentials.json")]:
        if candidate.exists():
            creds_path = candidate
            break
    if creds_path is None:
        print("⚠️  google-credentials.json not found — skipping Sheet write (CSV still saved).")
        return False

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)

        # Use a dedicated tab per service+province (create it if missing).
        tab = tab_name_for(installer_type, province)
        try:
            ws = spreadsheet.worksheet(tab)
            ws.clear()
        except gspread.WorksheetNotFound:
            ws = spreadsheet.add_worksheet(title=tab, rows=200, cols=len(SHEET_HEADER))

        print(f"\n📝 Writing {len(installers)} installers to Sheet tab '{tab}'...")

        rows = [SHEET_HEADER]
        for i in installers:
            rows.append([
                i["city"], i["name"], i["address"], i["phone"], i["email"],
                i["website"], i["image_url"], i["rating"], i["review_count"],
                i["gmaps_url"], "Yes" if i.get("recommended") else "No", "",
                time.strftime("%Y-%m-%d"),
            ])

        # values first, then range_name — new gspread signature (no deprecation warning).
        ws.update(values=rows, range_name="A1")
        print(f"✅ Wrote {len(installers)} installers to tab '{tab}'")

        # Persistent audit trail of every installer ever added.
        append_to_log(spreadsheet, installers, installer_type)

        # Clean up the old placeholder tab now that real data is in named tabs.
        remove_stale_sheet1(spreadsheet)
        return True
    except Exception as e:
        print(f"❌ Sheet write error: {e}")
        return False


if __name__ == "__main__":
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]

    if len(positional) < 1:
        print("Usage: python3 scrape_google_places_installers.py [heat-pump|solar] [--province=bc|on] [--debug]")
        print("       (omit the API key entirely — you'll be prompted for it, input hidden)")
        sys.exit(1)

    # Accept the key as an explicit first positional arg for backward
    # compatibility, but the normal path now is: no key on the command line
    # at all, just the installer type — then prompt interactively so the key
    # never has to survive a copy-paste, an export, or a shell history file.
    if positional[0].lower() in ("heat-pump", "solar"):
        installer_type = positional[0].lower()
        api_key = getpass.getpass("Google Places API key (input hidden, not saved anywhere): ").strip()
    elif len(positional) >= 2:
        api_key = positional[0]
        installer_type = positional[1].lower()
    else:
        print("Usage: python3 scrape_google_places_installers.py [heat-pump|solar] [--province=bc|on] [--debug]")
        sys.exit(1)

    if not api_key:
        print("No API key entered — aborting.")
        sys.exit(1)

    debug = "--debug" in flags
    province = "bc"
    for arg in flags:
        if arg.startswith("--province="):
            province = arg.split("=", 1)[1].lower()
    if province not in PROVINCES:
        print(f"Unknown province '{province}'. Choices: {list(PROVINCES)}")
        sys.exit(1)

    installers = scrape_installers(api_key, installer_type, province=province, debug=debug)

    if not installers:
        print("\n❌ No qualified installers found. Re-run with --debug to see raw results.")
        sys.exit(1)

    print(f"\n📊 Total qualified: {len(installers)} installers")
    save_to_csv(installers, installer_type, province=province)
    write_to_google_sheet(installers, installer_type, province=province)
