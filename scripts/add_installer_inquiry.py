#!/usr/bin/env python3
"""Add an installer who asked to be listed. Rankings stay Google-rating based; an inquiry never changes rank.

  python3 scripts/add_installer_inquiry.py --region ca --city Escondido --service heat-pump \\
      --name "We Care Plumbing Heating and Air" --address "445 Ryan Dr #101, San Marcos, CA 92078" \\
      --contact sam@example.com [--dry-run]

Steps it performs (see installers/INQUIRIES.md for the checks a person does first):
  1. Looks the business up on Google Places (your key is prompted for, hidden, never saved) and checks the match:
     the name must match, the type must be a real installer for the service, and the address must be near the city.
  2. Writes (or refreshes) its row in installers/<region>-<service>-installers-real.csv with Google's own rating and count.
     The email the installer sent from is stored as the contact email.
  3. Logs the inquiry in data/installer-inquiries.json (status, date, what Google returned).
  4. Prints the rebuild commands (JSON, profiles, rankings, get-quotes).
Nothing is paid for or promised: the listing appears only if the installer's Google rating and review count place it in the list.
"""
import argparse, csv, getpass, json, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import scrape_google_places_installers as sc
import regions

LOG = ROOT / "data" / "installer-inquiries.json"
HEADER = ["City", "Business Name", "Address", "Phone", "Email", "Website", "Image URL", "Google Rating", "Review Count",
          "Google Maps URL", "HomePowerRebate Recommended", "Notes", "Last Updated"]


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("&", "and"))


def csv_path(region, service):
    prefix = "" if region == "bc" else f"{region}-"
    return ROOT / "installers" / f"{prefix}{service}-installers-real.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True, choices=regions.CODES)
    ap.add_argument("--city", required=True, help="City name as in the region's city list, e.g. Escondido")
    ap.add_argument("--service", required=True, choices=["heat-pump", "solar", "insulation", "battery", "windows-doors", "ev-charger"])
    ap.add_argument("--name", required=True)
    ap.add_argument("--address", default="")
    ap.add_argument("--contact", default="", help="Email the installer wrote from (stored as the contact email)")
    ap.add_argument("--place-json", help="Use a saved Places result instead of calling Google (for tests)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    prov = sc.PROVINCES.get(a.region)
    if not prov or a.city not in prov["cities"]:
        raise SystemExit(f"{a.city} is not in the {a.region} city list in scrape_google_places_installers.py. "
                         f"Rankings exist only for cities with a page; add the city page first, or list the business under a nearby city it serves.")
    geo = prov["cities"][a.city]
    if a.place_json:
        places = json.loads(Path(a.place_json).read_text())
    else:
        key = getpass.getpass("Google Places API key (hidden): ").strip()
        places = sc.search_text(key, f"{a.name} {a.address}".strip(), geo["lat"], geo["lng"], debug=True)
    match = [p for p in places if norm(sc.display_name_text(p)) == norm(a.name) or norm(a.name) in norm(sc.display_name_text(p))]
    if not match:
        raise SystemExit("No Google Maps listing matches that name. Do not add it. Ask the installer for their Google Maps link.")
    p = match[0]
    name = sc.display_name_text(p)
    if not sc.is_relevant_installer(name, p.get("primaryType", ""), a.service):
        raise SystemExit(f"Google lists '{name}' as '{p.get('primaryType')}', which does not read as a {a.service} installer. Review by hand.")
    row = {"City": a.city, "Business Name": name, "Address": p.get("formattedAddress", ""),
           "Phone": p.get("nationalPhoneNumber", ""), "Email": a.contact, "Website": p.get("websiteUri", ""), "Image URL": "",
           "Google Rating": p.get("rating", ""), "Review Count": p.get("userRatingCount", ""),
           "Google Maps URL": p.get("googleMapsUri", ""), "HomePowerRebate Recommended": "No",
           "Notes": "Added on request; unverified license until checked", "Last Updated": time.strftime("%Y-%m-%d")}
    print(json.dumps(row, indent=1))
    if a.dry_run:
        return
    path = csv_path(a.region, a.service)
    rows = list(csv.DictReader(path.open(encoding="utf-8"))) if path.exists() else []
    rows = [r for r in rows if not (norm(r["Business Name"]) == norm(name) and r["City"] == a.city)]
    rows.append(row)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in HEADER})
    log = json.loads(LOG.read_text()) if LOG.exists() else {"inquiries": []}
    log["inquiries"].append({"date": time.strftime("%Y-%m-%d"), "name": name, "city": a.city, "region": a.region, "service": a.service,
                             "contact": a.contact, "google_rating": row["Google Rating"], "google_reviews": row["Review Count"],
                             "maps_url": row["Google Maps URL"], "status": "listed-by-rating", "license_checked": False})
    LOG.write_text(json.dumps(log, indent=1, ensure_ascii=False))
    print(f"\nWrote {path.relative_to(ROOT)}. Now run:\n"
          "  python3 scripts/generate_installer_json_from_real.py\n  python3 scripts/generate_installer_profiles.py\n"
          "  python3 scripts/build_installer_rankings.py\n  python3 scripts/build_get_quotes.py\n"
          "  python3 scripts/generate_sitemap.py\nthen git add -f data/installer-inquiries.json installers/*.csv")


if __name__ == "__main__":
    main()
