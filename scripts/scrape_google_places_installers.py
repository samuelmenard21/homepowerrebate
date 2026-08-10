#!/usr/bin/env python3
"""
Scrape REAL heat pump (HVAC) and solar installers from Google Places API (NEW v1).
Writes directly to the HomePowerRebate-Installers Google Sheet.

Usage:
  python3 scrape_google_places_installers.py YOUR_API_KEY heat-pump
  python3 scrape_google_places_installers.py YOUR_API_KEY solar --debug

Notes:
  - Uses the NEW Places API (v1) searchText endpoint.
  - REQUIRES an X-Goog-FieldMask header (that was the bug before).
  - Field names are the NEW API names: userRatingCount, nationalPhoneNumber, etc.
  - One searchText call returns everything we need — no separate details call.
"""

import sys
import time
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

# Always reject these — they're adjacent trades, not installers.
BAD_WORDS = (
    "duct cleaning", "restoration", "supply", "supplies", "handyman",
    "appliance repair", "roofing", "chimney", "insulation", "window",
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

PROVINCES = {
    "bc": {"cities": BC_CITIES, "abbrev": "BC", "csv_prefix": ""},
    "on": {"cities": ONTARIO_CITIES, "abbrev": "ON", "csv_prefix": "on-"},
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

    if installer_type == "solar":
        good_types, good_words = SOLAR_GOOD_TYPES, SOLAR_GOOD_WORDS
    else:
        good_types, good_words = HEATPUMP_GOOD_TYPES, HEATPUMP_GOOD_WORDS

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
    if len(sys.argv) < 3:
        print("Usage: python3 scrape_google_places_installers.py API_KEY [heat-pump|solar] [--province=bc|on] [--debug]")
        sys.exit(1)

    api_key = sys.argv[1]
    installer_type = sys.argv[2].lower()
    debug = "--debug" in sys.argv
    province = "bc"
    for arg in sys.argv[3:]:
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
