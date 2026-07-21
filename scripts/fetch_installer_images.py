#!/usr/bin/env python3
"""
Fetch installer images from Google Places API and update JSON files.
Usage: python3 fetch_installer_images.py YOUR_API_KEY
"""

import json
import requests
import sys
import os
import time
from pathlib import Path

# Configuration
PLACES_API_BASE = "https://maps.googleapis.com/maps/api/place"
PLACEHOLDER_IMAGE = "https://via.placeholder.com/400x300?text=No+Image"
RATE_LIMIT_DELAY = 0.2  # seconds between API calls

def search_place(api_key, business_name, location):
    """Search for a business on Google Places and get photo URL."""
    try:
        # Search for the place
        search_url = f"{PLACES_API_BASE}/textsearch/json"
        search_params = {
            "query": f"{business_name} {location}",
            "key": api_key
        }

        response = requests.get(search_url, params=search_params, timeout=5)
        response.raise_for_status()
        results = response.json()

        if results.get("results") and len(results["results"]) > 0:
            place = results["results"][0]
            place_id = place.get("place_id")

            if place_id:
                # Get place details including photos
                details_url = f"{PLACES_API_BASE}/details/json"
                details_params = {
                    "place_id": place_id,
                    "fields": "photos,formatted_address,rating",
                    "key": api_key
                }

                details_response = requests.get(details_url, params=details_params, timeout=5)
                details_response.raise_for_status()
                details = details_response.json()

                if details.get("result", {}).get("photos"):
                    photo = details["result"]["photos"][0]
                    photo_reference = photo.get("photo_reference")

                    if photo_reference:
                        # Construct photo URL
                        photo_url = f"{PLACES_API_BASE}/photo?maxwidth=400&photo_reference={photo_reference}&key={api_key}"
                        return photo_url, "success"

        return None, "no_results"

    except requests.exceptions.RequestException as e:
        return None, f"error: {str(e)}"
    except Exception as e:
        return None, f"error: {str(e)}"


def update_json_files(api_key, json_dir="installers/json"):
    """Update all installer JSON files with image URLs."""

    json_path = Path(json_dir)
    if not json_path.exists():
        print(f"Error: {json_dir} not found")
        return

    stats = {"updated": 0, "skipped": 0, "errors": 0}

    # Process heat pump installers
    hp_files = sorted(json_path.glob("*.json"))
    print(f"\n📷 Fetching images for {len(hp_files)} heat pump cities...")

    for filepath in hp_files:
        with open(filepath, 'r') as f:
            installers = json.load(f)

        city_name = filepath.stem.replace("-", " ").title()
        print(f"\n  {city_name}:")

        for installer in installers:
            # Skip if already has image
            if installer.get("image_url"):
                print(f"    ✓ {installer['name']} (already has image)")
                stats["skipped"] += 1
                continue

            # Fetch image from Google Places
            image_url, status = search_place(
                api_key,
                installer["name"],
                installer["location"]
            )

            if image_url:
                installer["image_url"] = image_url
                print(f"    ✓ {installer['name']}")
                stats["updated"] += 1
            else:
                # Use placeholder
                installer["image_url"] = PLACEHOLDER_IMAGE
                print(f"    ⚠ {installer['name']} ({status})")
                stats["errors"] += 1

            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)

        # Write updated installers back
        with open(filepath, 'w') as f:
            json.dump(installers, f, indent=2)

    # Process solar installers
    solar_files = sorted(json_path.glob("solar/*.json"))
    print(f"\n📷 Fetching images for {len(solar_files)} solar cities...")

    for filepath in solar_files:
        with open(filepath, 'r') as f:
            installers = json.load(f)

        city_name = filepath.stem.replace("-", " ").title()
        print(f"\n  {city_name} (Solar):")

        for installer in installers:
            if installer.get("image_url"):
                print(f"    ✓ {installer['name']} (already has image)")
                stats["skipped"] += 1
                continue

            image_url, status = search_place(
                api_key,
                f"{installer['name']} solar",
                installer["location"]
            )

            if image_url:
                installer["image_url"] = image_url
                print(f"    ✓ {installer['name']}")
                stats["updated"] += 1
            else:
                installer["image_url"] = PLACEHOLDER_IMAGE
                print(f"    ⚠ {installer['name']} ({status})")
                stats["errors"] += 1

            time.sleep(RATE_LIMIT_DELAY)

        with open(filepath, 'w') as f:
            json.dump(installers, f, indent=2)

    # Summary
    print(f"\n✅ Complete!")
    print(f"   Updated: {stats['updated']}")
    print(f"   Skipped: {stats['skipped']}")
    print(f"   Fallbacks: {stats['errors']}")
    print(f"   Total: {stats['updated'] + stats['skipped'] + stats['errors']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_installer_images.py YOUR_GOOGLE_PLACES_API_KEY")
        print("\nGet your API key from:")
        print("  https://console.cloud.google.com")
        sys.exit(1)

    api_key = sys.argv[1]

    # Verify we're in the right directory
    if not os.path.exists("installers/json"):
        print("Error: installers/json directory not found")
        print("Run this script from the Powerrebate root directory")
        sys.exit(1)

    update_json_files(api_key)
