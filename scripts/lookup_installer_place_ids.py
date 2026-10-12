#!/usr/bin/env python3
"""Find the Google place ID for every installer profile page, for the photo Worker (photo-worker/).

Google's Places policies allow storing place IDs indefinitely (and nothing else), and a Text Search that asks only for
places.id is the "Text Search Essentials (IDs Only)" SKU, which has no charge. So this costs nothing and stores only
what is allowed. Writes data/installer-place-ids.json: {"installers/profiles/<...>/index.html": "<place id>"}.
Resumable: profiles already in the file are skipped (pass --refresh to redo all). Then run
python3 scripts/add_profile_photos.py and `git add -f data/installer-place-ids.json`.

Usage (in your own terminal; never paste the key into a chat):
  python3 scripts/lookup_installer_place_ids.py      (asks for the key; typing is hidden)
The key needs "Places API (New)" enabled. The query is the business name plus its street address from the profile page.
"""
import getpass
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "installer-place-ids.json"
LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


def profile_query(html_text):
    """Business name plus street address, or plus the city and region from the page's hero line."""
    name = street = ""
    for blk in LD_RE.findall(html_text):
        try:
            data = json.loads(blk)
        except ValueError:
            continue
        for node in data.get("@graph", [data]) if isinstance(data, dict) else []:
            if isinstance(node, dict) and node.get("@type") == "LocalBusiness" and node.get("name"):
                name = node["name"]
                addr = node.get("address")
                street = addr.get("streetAddress", "") if isinstance(addr, dict) else ""
    if not name:
        h1 = re.search(r"<h1>(.*?)</h1>", html_text, re.S)
        name = re.sub(r"<[^>]+>", "", h1.group(1)).strip() if h1 else ""
    meta = re.search(r'<p class="ip-hero-meta">.*?&middot;\s*([^<]+)</p>', html_text)
    where = street or (meta.group(1).strip() if meta else "")
    return html.unescape(f"{name} {where}".strip()) if name else ""


def search(query, key):
    """Retries dropped connections and Google's 429/5xx a few times with a growing pause before giving up."""
    for attempt in range(5):
        try:
            return _search(query, key)
        except urllib.error.HTTPError as ex:
            if ex.code not in (429, 500, 502, 503, 504) or attempt == 4:
                raise
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            if attempt == 4:
                raise
        time.sleep(2 ** attempt)


def _search(query, key):
    req = urllib.request.Request(
        "https://places.googleapis.com/v1/places:searchText",
        data=json.dumps({"textQuery": query, "pageSize": 1}).encode(),
        headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": "places.id"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        places = json.load(r).get("places") or []
    return places[0]["id"] if places else None


def main():
    key = os.environ.get("GOOGLE_PLACES_KEY", "").strip()
    if not key:
        # asked in the terminal, not echoed and never saved
        key = getpass.getpass("Google API key (Places API (New)), then Enter: ").strip()
    if not key:
        sys.exit("No key given.")
    ids = {} if "--refresh" in sys.argv or not OUT.exists() else json.loads(OUT.read_text(encoding="utf-8"))
    pages = sorted((ROOT / "installers" / "profiles").rglob("index.html"))
    found = missed = 0
    for i, p in enumerate(pages, 1):
        rel = str(p.relative_to(ROOT))
        if rel in ids:
            continue
        q = profile_query(p.read_text(encoding="utf-8", errors="replace"))
        if not q:
            missed += 1
            continue
        try:
            pid = search(q, key)
        except urllib.error.HTTPError as ex:  # bad key, API not enabled, quota: show Google's own message
            detail = ex.read().decode(errors="replace")
            try:
                detail = json.loads(detail)["error"]["message"]
            except (ValueError, KeyError, TypeError):
                pass
            print(f"stopped at {rel}: HTTP {ex.code}: {detail}")
            break
        except Exception as ex:  # network hiccup: keep what we have, re-run later
            print(f"stopped at {rel}: {ex}")
            break
        if pid:
            ids[rel] = pid
            found += 1
        else:
            missed += 1
        if i % 100 == 0:
            OUT.write_text(json.dumps(ids, indent=0, sort_keys=True) + "\n", encoding="utf-8")
            print(f"{i}/{len(pages)}")
        time.sleep(0.05)
    OUT.write_text(json.dumps(ids, indent=0, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(ids)} profiles have a place ID ({found} new, {missed} not found).")


if __name__ == "__main__":
    main()
