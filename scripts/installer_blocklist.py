#!/usr/bin/env python3
"""Installers who asked to be taken off the site, kept off for good.

data/installer-blocklist.json lists them (name, city, email, website, Google
Maps cid, reason, date). A blocked company matches on any of: email, cid,
website domain, or business name + city. The rankings builder drops matching
CSV rows and the Google Places scraper never writes them back.

  python3 scripts/installer_blocklist.py   # fails if a blocked installer is in any installer CSV or JSON
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "data" / "installer-blocklist.json"


def _norm(s):
    return re.sub(r"[^a-z0-9]+", "", str(s or "").lower().replace("&", "and"))


def _domain(url):
    d = re.sub(r"^https?://", "", str(url or "").strip().lower()).split("/")[0]
    return d[4:] if d.startswith("www.") else d


def _cid(url):
    m = re.search(r"cid=(\d+)", str(url or ""))
    return m.group(1) if m else ""


def _load():
    if not FILE.exists():
        return []
    return json.loads(FILE.read_text(encoding="utf-8"))


_KEYS = None


def _keys():
    global _KEYS
    if _KEYS is None:
        k = set()
        for b in _load():
            if b.get("email"):
                k.add(("email", b["email"].strip().lower()))
            if b.get("cid"):
                k.add(("cid", str(b["cid"])))
            if b.get("website"):
                k.add(("domain", _domain(b["website"])))
            if b.get("name"):
                k.add(("name", _norm(b["name"]), _norm(b.get("city"))))
        _KEYS = k
    return _KEYS


def is_blocked(name="", city="", email="", website="", gmaps=""):
    k = _keys()
    if not k:
        return False
    return any(x in k for x in [
        ("email", str(email or "").strip().lower()),
        ("cid", _cid(gmaps)),
        ("domain", _domain(website)),
        ("name", _norm(name), _norm(city)),
    ] if x[1])


def main():
    hits = []
    for f in sorted((ROOT / "installers").glob("*-installers-real.csv")):
        for r in csv.DictReader(f.open(encoding="utf-8")):
            if is_blocked(r.get("Business Name"), r.get("City"), r.get("Email"), r.get("Website"), r.get("Google Maps URL")):
                hits.append(f"{f.relative_to(ROOT)}: {r.get('Business Name')} ({r.get('City')})")
    for f in sorted((ROOT / "installers" / "json").rglob("*.json")):
        try:
            items = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        city = f.stem.replace("-", " ")
        for it in items if isinstance(items, list) else []:
            if isinstance(it, dict) and is_blocked(it.get("name"), city, it.get("email"), it.get("website"), it.get("gmaps_url")):
                hits.append(f"{f.relative_to(ROOT)}: {it.get('name')}")
    for h in hits:
        print("BLOCKED INSTALLER LISTED:", h)
    print(f"{len(_load())} blocked installers, {len(hits)} still listed.")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
