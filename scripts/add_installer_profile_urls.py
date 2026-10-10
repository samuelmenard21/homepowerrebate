#!/usr/bin/env python3
"""Add profileUrl to each installer record in installers/json/** when that installer's profile page exists.

The installer directory (installers/index.html) links its cards to `profileUrl`; without it the card links to "#".
Run after anything that regenerates installers/json or installers/profiles. Idempotent; rewrites a file only when a URL changes,
keeping its exact formatting (2-space indent). A record whose profile page does not exist gets no profileUrl (never a guessed link).
Usage: python3 scripts/add_installer_profile_urls.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import regions

ROOT = Path(__file__).resolve().parent.parent
JSON_DIR = ROOT / "installers" / "json"


def slugify(s):
    s = s.lower().replace("&", "and").replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def slugify_gen(s):
    """The profile generators drop '&' and apostrophes instead of writing 'and'; both spellings exist on disk."""
    s = re.sub(r"[&']", "", s.lower().strip())
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def profile_url(region, city_slug, name):
    for name_slug in dict.fromkeys((slugify(name), slugify_gen(name))):
        for rel in (f"installers/profiles/{city_slug}/{name_slug}", f"installers/profiles/{region}/{city_slug}/{name_slug}"):
            if (ROOT / rel / "index.html").exists():
                return "/" + rel + "/"
    return ""


BC_CITIES = {h.strip("/").split("/")[-1] for h, _ in regions.BY_CODE["bc"]["cities"]}


def region_of(path):
    parts = [x for x in path.relative_to(JSON_DIR).parts[:-1] if x != "solar"]
    return parts[0] if parts else "bc"


def regions_to_try(path):
    """Top-level files in installers/json/ are BC cities, but also hold flat copies of some CA and NY cities; those link to their real region's pages."""
    r = region_of(path)
    if r != "bc" or path.stem in BC_CITIES:
        return [r]
    return [c for c in regions.CODES if c != "bc"]


def main():
    files = changed = linked = total = 0
    for f in sorted(JSON_DIR.rglob("*.json")):
        raw = f.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, list):
            continue
        fmt = next(((ea, nl) for ea in (False, True) for nl in ("", "\n") if json.dumps(data, indent=2, ensure_ascii=ea) + nl == raw), None)
        if fmt is None:
            continue
        files += 1
        tries, city = regions_to_try(f), f.stem
        dirty = False
        for rec in data:
            if not isinstance(rec, dict) or not rec.get("name"):
                continue
            total += 1
            url = next((u for u in (profile_url(r, city, rec["name"]) for r in tries) if u), "")
            if url:
                linked += 1
                if rec.get("profileUrl") != url:
                    rec["profileUrl"] = url
                    dirty = True
            elif "profileUrl" in rec:
                del rec["profileUrl"]
                dirty = True
        if dirty:
            f.write_text(json.dumps(data, indent=2, ensure_ascii=fmt[0]) + fmt[1], encoding="utf-8")
            changed += 1
    print(f"{files} files, {total} installers, {linked} linked to a profile page, {changed} files rewritten")


if __name__ == "__main__":
    main()
