"""
Shared geocoding helper for the city-data builder scripts
(build_city_climate_data.py, build_city_solar_data.py).

IMPORTANT: Open-Meteo's geocoding API `country` query param does NOT
reliably filter results — verified by testing: a "Fort St John" query with
country=CA still returned a Queensland, Australia result as its only hit.
Country filtering here is done client-side instead, and a result outside
the expected country is never accepted, even as a last resort. That
fallback-to-any-country behavior was a real bug caught in an early run:
"Fort St John, BC" silently resolved to Queensland, Australia (22C Jan
low) and "Vernon, BC" to Texas — both would have shipped false climate
claims to city pages if not caught before applying the data.

Keep this file as the single source of truth for geocoding — do not
copy/paste geocode logic into a new builder script.
"""
import json
import re
import time
import urllib.parse
import urllib.request

REGION_TO_ADMIN1 = {
    "ab": "Alberta", "bc": "British Columbia", "on": "Ontario", "ns": "Nova Scotia",
    "ca": "California", "ny": "New York", "ma": "Massachusetts", "pa": "Pennsylvania",
    "co": "Colorado", "vt": "Vermont",
}
REGION_TO_COUNTRY = {
    "ab": "CA", "bc": "CA", "on": "CA", "ns": "CA",
    "ca": "US", "ny": "US", "ma": "US", "pa": "US", "co": "US", "vt": "US",
}


def http_get_json(url, retries=3):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                return json.loads(r.read())
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1.5)


def _geocode_query(city_name, region_code, count=20):
    admin1 = REGION_TO_ADMIN1[region_code]
    country = REGION_TO_COUNTRY[region_code]
    q = urllib.parse.urlencode({"name": city_name, "count": count})
    data = http_get_json(f"https://geocoding-api.open-meteo.com/v1/search?{q}")
    results = [r for r in (data.get("results") or []) if r.get("country_code") == country]
    if not results:
        return None, "no_country_match"
    for r in results:
        if r.get("admin1") == admin1:
            return r, "exact"
    return results[0], "country_only"


# A handful of city names Open-Meteo's geocoder only recognizes with
# French-Canadian abbreviations spelled out in full (periods included) —
# found by testing directly, not guessed. Add to this as new failures
# surface rather than looping indefinitely on regex variants.
NAME_OVERRIDES = {
    "sault ste marie": "Sault Ste. Marie",
}


def geocode(city_name, region_code):
    """Returns (result_dict_or_None, quality_str). quality is 'exact',
    'country_only' (right country, admin1 didn't match — spot-check these),
    or None result means no match found in the expected country at all."""
    override = NAME_OVERRIDES.get(city_name.lower())
    if override:
        result, quality = _geocode_query(override, region_code)
        if result is not None:
            return result, quality

    result, quality = _geocode_query(city_name, region_code)
    if result is None:
        alt = re.sub(r'\bSt\b\.?', 'St.', city_name)
        if alt != city_name:
            result, quality = _geocode_query(alt, region_code)
    return result, quality
