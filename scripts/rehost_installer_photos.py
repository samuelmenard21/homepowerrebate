#!/usr/bin/env python3
"""
Permanently fix broken installer photos by downloading the actual image
bytes and hosting them ourselves, instead of linking Google's raw Places
photo URLs (which are ephemeral session tokens, not permanent links — found
2026-09-01 when Big Bird Plumbing & Heating's photo 403'd; confirmed the
same dead-link pattern across 867 of 896 installer profile pages).

For every installer profile page:
  1. Read the business name + address from the page's own JSON-LD.
  2. Re-search Google Places (Text Search, NEW v1 API) for that exact
     business to get a CURRENT photo resource name (the old one we stored
     is long expired and can't be reused).
  3. Download the actual JPEG bytes for that photo (no skipHttpRedirect —
     we follow the redirect and save the bytes ourselves this time, which
     is the actual fix; the old scraper stored the redirect URL instead of
     the bytes, which is why it expired).
  4. Save to installers/photos/<same path as the profile page>.jpg — mirrors
     the profile's own directory structure, so there's no ambiguity about
     which photo belongs to which page.
  5. Update the profile page's <img src>, og:image, twitter:image, and the
     JSON-LD "image" field to the new permanent local path.
  6. Update the matching entry in installers/json/*.json (the "image_url"
     field) so future page regeneration also picks up the permanent path.

Never re-fetches a photo that's already been downloaded (resumable — safe
to stop and re-run). Rate-limited to be a reasonable API citizen.

Usage (run this yourself, in your own terminal — never paste the API key
into a chat with an assistant):
  python3 scripts/rehost_installer_photos.py --dry-run   # see what it would do, no API calls, no key needed
  python3 scripts/rehost_installer_photos.py             # prompts for the key (input hidden, never saved)
  python3 scripts/rehost_installer_photos.py --limit 20  # test on a small batch first
"""
import argparse
import getpass
import html
import json
import os
import re
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTOS_DIR = os.path.join(ROOT, "installers/photos")
SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
RATE_LIMIT_DELAY = 0.3
PHOTO_MAX_PX = 800

FIELD_MASK = "places.id,places.displayName,places.formattedAddress,places.photos"


def search_business(api_key, name, address, debug=False):
    query = f"{name}, {address}"
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
        "Content-Type": "application/json",
    }
    payload = {"textQuery": query, "maxResultCount": 3}
    try:
        resp = requests.post(SEARCH_URL, json=payload, headers=headers, timeout=10)
        if resp.status_code != 200:
            if debug:
                print(f"      search HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        places = resp.json().get("places", [])
        return places[0] if places else None
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"      search error: {e}")
        return None


def download_photo_bytes(api_key, photo_name, debug=False):
    """Fetch the ACTUAL image bytes (not just a redirect URL) so they can
    be hosted permanently and never expire."""
    url = f"https://places.googleapis.com/v1/{photo_name}/media"
    try:
        resp = requests.get(
            url,
            params={"maxWidthPx": PHOTO_MAX_PX, "key": api_key},
            timeout=15,
            allow_redirects=True,
        )
        if resp.status_code != 200 or not resp.content:
            if debug:
                print(f"      photo HTTP {resp.status_code}")
            return None
        return resp.content
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"      photo error: {e}")
        return None


def extract_name_and_address(page_text):
    name_m = re.search(r'"name":\s*"([^"]+)"', page_text)
    if not name_m:
        return None, None
    name = name_m.group(1).replace('\\u0026', '&').replace('\\"', '"')

    addr_m = re.search(r'"streetAddress":\s*"([^"]+)"', page_text)
    if addr_m:
        return name, addr_m.group(1).replace('\\u0026', '&').replace('\\"', '"')

    # Fallback for the simpler PA/CO/VT-era template, which has no
    # streetAddress in its JSON-LD — use areaServed.name (the city) instead,
    # since a name + city query is still specific enough to re-find the
    # business via Places Text Search.
    area_m = re.search(r'"areaServed":\s*\{[^}]*"name":\s*"([^"]+)"', page_text)
    if area_m:
        return name, area_m.group(1).replace('\\u0026', '&').replace('\\"', '"')

    return None, None


def relative_photo_path(profile_path):
    rel = os.path.relpath(os.path.dirname(profile_path), os.path.join(ROOT, "installers/profiles"))
    return os.path.join(PHOTOS_DIR, rel + ".jpg")


def update_profile_page(profile_path, new_photo_url):
    text = open(profile_path, encoding="utf-8").read()
    old_url_pattern = re.compile(r'https://lh3\.googleusercontent\.com/place-photos/[^"\'\s]+')
    new_text, n = old_url_pattern.subn(new_photo_url, text)
    if n == 0:
        return False
    open(profile_path, "w", encoding="utf-8").write(new_text)
    return True


def update_json_entry(business_name, city_slug, new_photo_url):
    """Best-effort: update image_url in any installers/json/*/<city>.json
    (and category subdirs) that contains a matching business name."""
    updated = 0
    for root, _, files in os.walk(os.path.join(ROOT, "installers/json")):
        for fname in files:
            if fname != f"{city_slug}.json":
                continue
            path = os.path.join(root, fname)
            try:
                data = json.load(open(path, encoding="utf-8"))
            except Exception:
                continue
            changed = False
            for entry in data:
                if entry.get("name") == business_name and entry.get("image_url", "").startswith(
                    "https://lh3.googleusercontent.com"
                ):
                    entry["image_url"] = new_photo_url
                    changed = True
            if changed:
                json.dump(data, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
                updated += 1
    return updated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="No API calls, no key needed — just report what's broken")
    ap.add_argument("--limit", type=int, default=None, help="Process at most N pages (for testing)")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    profile_paths = []
    for root, _, files in os.walk(os.path.join(ROOT, "installers/profiles")):
        if "index.html" in files:
            p = os.path.join(root, "index.html")
            text = open(p, encoding="utf-8").read()
            if "lh3.googleusercontent.com/place-photos" in text:
                profile_paths.append(p)
    profile_paths.sort()

    if args.dry_run:
        print(f"{len(profile_paths)} profile pages still have a dead Google Places photo URL.")
        print("Run without --dry-run (you'll be prompted for your API key, input hidden, never saved) to fix them.")
        return

    api_key = getpass.getpass("Google Places API key (input hidden, not saved anywhere): ").strip()
    if not api_key:
        print("No key entered, aborting.")
        return

    os.makedirs(PHOTOS_DIR, exist_ok=True)

    if args.limit:
        profile_paths = profile_paths[: args.limit]

    fixed, no_match, no_photo, already_done = 0, 0, 0, 0

    for i, profile_path in enumerate(profile_paths, 1):
        rel_display = os.path.relpath(profile_path, ROOT)
        local_photo_path = relative_photo_path(profile_path)

        if os.path.exists(local_photo_path):
            # Photo already downloaded in a prior run — just make sure the page points to it.
            city_slug = os.path.basename(os.path.dirname(os.path.dirname(profile_path)))
            new_url = "https://homepowerrebate.com/installers/photos/" + os.path.relpath(
                local_photo_path, PHOTOS_DIR
            )
            update_profile_page(profile_path, new_url)
            already_done += 1
            continue

        text = open(profile_path, encoding="utf-8").read()
        name, address = extract_name_and_address(text)
        if not name or not address:
            print(f"  [{i}/{len(profile_paths)}] SKIP (no name/address found): {rel_display}")
            no_match += 1
            continue

        place = search_business(api_key, name, address, debug=args.debug)
        time.sleep(RATE_LIMIT_DELAY)
        if not place:
            print(f"  [{i}/{len(profile_paths)}] NO MATCH: {name}")
            no_match += 1
            continue

        photos = place.get("photos", [])
        if not photos:
            print(f"  [{i}/{len(profile_paths)}] NO PHOTO AVAILABLE: {name}")
            no_photo += 1
            continue

        photo_bytes = download_photo_bytes(api_key, photos[0]["name"], debug=args.debug)
        time.sleep(RATE_LIMIT_DELAY)
        if not photo_bytes:
            print(f"  [{i}/{len(profile_paths)}] PHOTO DOWNLOAD FAILED: {name}")
            no_photo += 1
            continue

        os.makedirs(os.path.dirname(local_photo_path), exist_ok=True)
        open(local_photo_path, "wb").write(photo_bytes)

        new_url = "https://homepowerrebate.com/installers/photos/" + os.path.relpath(local_photo_path, PHOTOS_DIR)
        update_profile_page(profile_path, new_url)

        city_slug = os.path.basename(os.path.dirname(os.path.dirname(profile_path)))
        update_json_entry(name, city_slug, new_url)

        print(f"  [{i}/{len(profile_paths)}] FIXED: {name}")
        fixed += 1

    print(
        f"\nDone. fixed={fixed} already_done={already_done} no_match={no_match} "
        f"no_photo_available={no_photo} total={len(profile_paths)}"
    )


if __name__ == "__main__":
    main()
