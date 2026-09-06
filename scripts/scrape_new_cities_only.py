#!/usr/bin/env python3
"""
One-off: scrape installers for ONLY the 10 newly-built cities (not a whole
province re-scrape, which would touch every existing city's CSV rows).

Reuses scrape_installers() from scrape_google_places_installers.py but with
each province's city dict temporarily filtered down to just the new cities,
then APPENDS the results into the existing province CSV (dedup by
name+city) instead of overwriting it.

Usage: python3 scripts/scrape_new_cities_only.py
  (prompts for the API key, hidden input, not saved)
"""
import csv
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import scrape_google_places_installers as sgp

ROOT = Path(__file__).parent.parent

NEW_CITIES = {
    "on": ["Guelph", "Kingston", "Niagara Falls", "Peterborough",
           "Sault Ste. Marie", "Thunder Bay", "Timmins"],
    "ab": ["Fort McMurray"],
    "ns": ["Cape Breton"],
    "ma": ["Lawrence"],
}

SHEET_HEADER = sgp.SHEET_HEADER


def append_installers_to_csv(installers, installer_type, province):
    prefix = sgp.PROVINCES[province]["csv_prefix"]
    csv_path = ROOT / "installers" / f"{prefix}{installer_type}-installers-real.csv"

    existing_rows = []
    existing_keys = set()
    if csv_path.exists():
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing_rows.append(row)
                existing_keys.add((row["Business Name"].strip().lower(), row["City"].strip().lower()))

    new_rows = []
    for i in installers:
        key = (i["name"].strip().lower(), i["city"].strip().lower())
        if key in existing_keys:
            continue
        new_rows.append({
            "City": i["city"], "Business Name": i["name"], "Address": i["address"],
            "Phone": i["phone"], "Email": i["email"], "Website": i["website"],
            "Image URL": i["image_url"], "Google Rating": i["rating"],
            "Review Count": i["review_count"], "Google Maps URL": i["gmaps_url"],
            "HomePowerRebate Recommended": "Yes" if i.get("recommended") else "No",
            "Notes": "", "Last Updated": __import__("time").strftime("%Y-%m-%d"),
        })

    if not new_rows:
        print(f"  (no new rows for {csv_path.name} — nothing to append)")
        return 0

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SHEET_HEADER)
        w.writeheader()
        for row in existing_rows:
            w.writerow(row)
        for row in new_rows:
            w.writerow(row)

    print(f"  ✓ appended {len(new_rows)} row(s) to {csv_path.relative_to(ROOT)}")
    return len(new_rows)


def main():
    api_key = getpass.getpass("Google Places API key (hidden, not saved): ").strip()
    if not api_key:
        sys.exit("No key entered — aborting.")

    total = 0
    for province, city_names in NEW_CITIES.items():
        full_cities = sgp.PROVINCES[province]["cities"]
        filtered = {k: v for k, v in full_cities.items() if k in city_names}
        missing = set(city_names) - set(filtered)
        if missing:
            print(f"⚠️  {province}: missing coords for {missing} — check the cities dict")

        # Temporarily narrow this province's city dict so scrape_installers()
        # only queries the new cities, not the whole province again.
        original_cities = sgp.PROVINCES[province]["cities"]
        sgp.PROVINCES[province]["cities"] = filtered
        try:
            for installer_type in ("heat-pump", "solar"):
                print(f"\n=== {province.upper()} / {installer_type} ({list(filtered)}) ===")
                results = sgp.scrape_installers(api_key, installer_type, province=province, debug=False)
                n = append_installers_to_csv(results, installer_type, province)
                total += n
        finally:
            sgp.PROVINCES[province]["cities"] = original_cities

    print(f"\n✅ Done — {total} new installer rows added across all new cities")


if __name__ == "__main__":
    main()
