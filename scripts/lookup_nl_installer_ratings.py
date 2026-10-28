#!/usr/bin/env python3
"""Google Places lookup for the NL participating installers (one Text Search per company, 111 calls): place id, Google name and
address, rating, review count, business status. No photos, no review text. Writes data/nl/installer-places.json, which
build_nl_installers.py reads to show a rating and the "Top rated" sort. Ratings are an Enterprise Places field (about 1,000 free
calls a month), so this is one request per company and nothing else. A match is "ok" only when Google's name is close to the
takeCHARGE company name and the address is in Newfoundland and Labrador; the rest are "check" and are not shown.
Usage (in your own terminal; never paste the key into a chat):
  python3 scripts/lookup_nl_installer_ratings.py          (asks for the key; typing is hidden; re-run to resume)
  python3 scripts/lookup_nl_installer_ratings.py --retry  (look up the "check" and missing ones again)
The key needs "Places API (New)" enabled. Then: python3 scripts/build_nl_installers.py && python3 scripts/post_steps.py"""
import difflib
import getpass
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_nl_installers as nl  # noqa: E402

OUT = ROOT / "data/nl/installer-places.json"
MASK = "places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.businessStatus"


def norm(s):
    s = s.lower().replace("&", " and ")
    s = re.sub(r"\b(ltd|limited|inc|incorporated|nl|nf|co|company|the|and|enterprises?)\b", " ", s)
    return re.sub(r"[^a-z0-9]", "", s)


def search(name, key):
    body = {"textQuery": f"{name} Newfoundland and Labrador", "regionCode": "CA", "pageSize": 3}
    req = urllib.request.Request("https://places.googleapis.com/v1/places:searchText", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": MASK})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r).get("places") or []
        except urllib.error.HTTPError as ex:
            if ex.code not in (429, 500, 502, 503, 504) or attempt == 4:
                raise
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            if attempt == 4:
                raise
        time.sleep(2 ** attempt)


def best(name, places):
    scored = []
    for p in places:
        g = p.get("displayName", {}).get("text", "")
        addr = p.get("formattedAddress", "")
        sim = difflib.SequenceMatcher(None, norm(name), norm(g)).ratio()
        in_nl = bool(re.search(r"\bNL\b|Newfoundland|Labrador", addr))
        scored.append((sim, in_nl, p))
    scored.sort(key=lambda x: (x[1], x[0]), reverse=True)
    return scored[0] if scored else None


def main():
    retry = "--retry" in sys.argv
    key = os.environ.get("GOOGLE_PLACES_KEY", "").strip()
    if not key:
        key = getpass.getpass("Google Places API key (hidden, not saved): ").strip()
    if not key:
        sys.exit("No key given.")
    done = json.loads(OUT.read_text()) if OUT.exists() else {}
    cos = nl.merge()
    todo = [c for c in cos if nl.key(c["name"]) not in done or (retry and done[nl.key(c["name"])].get("match") != "ok")]
    print(f"{len(cos)} companies, {len(todo)} to look up.")
    for i, c in enumerate(todo, 1):
        k = nl.key(c["name"])
        try:
            places = search(c["name"], key)
        except urllib.error.HTTPError as ex:
            OUT.write_text(json.dumps(done, indent=1, sort_keys=True) + "\n", encoding="utf-8")
            sys.exit(f"Stopped after {i - 1} lookups: Google said {ex.code} {ex.read().decode()[:300]}")
        hit = best(c["name"], places)
        rec = {"company": c["name"], "fetched": date.today().isoformat(), "match": "none"}
        if hit:
            sim, in_nl, p = hit
            rec.update({"place_id": p["id"], "google_name": p.get("displayName", {}).get("text", ""), "address": p.get("formattedAddress", ""),
                        "rating": p.get("rating"), "reviews": p.get("userRatingCount", 0), "status": p.get("businessStatus", ""),
                        "similarity": round(sim, 2), "match": "ok" if (sim >= 0.6 and in_nl and p.get("rating")) else "check"})
        done[k] = rec
        print(f"{i:3}/{len(todo)} {c['name'][:42]:42} -> {rec.get('google_name', '-')[:38]:38} {rec.get('rating', '')} ({rec.get('reviews', '')}) {rec['match']}")
        if i % 10 == 0:
            OUT.write_text(json.dumps(done, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        time.sleep(0.15)
    OUT.write_text(json.dumps(done, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    ok = sum(1 for r in done.values() if r["match"] == "ok")
    print(f"Done. {ok} matched with a rating, {len(done) - ok} to check or none. Saved {OUT}")


if __name__ == "__main__":
    main()
