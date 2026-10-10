#!/usr/bin/env python3
"""Add profileUrl to each installer record in installers/json/** when that installer's profile page exists.

The installer directory (installers/index.html) links its cards to `profileUrl`; without it the card links to "#".
Run after anything that regenerates installers/json or installers/profiles. Idempotent; rewrites a file only when a URL changes,
keeping its exact formatting (2-space indent). A record whose profile page does not exist gets no profileUrl (never a guessed link).
Usage: python3 scripts/add_installer_profile_urls.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSON_DIR = ROOT / "installers" / "json"


def slugify(s):
    s = s.lower().replace("&", "and").replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def profile_url(region, city_slug, name):
    name_slug = slugify(name)
    for rel in (f"installers/profiles/{city_slug}/{name_slug}", f"installers/profiles/{region}/{city_slug}/{name_slug}"):
        if (ROOT / rel / "index.html").exists():
            return "/" + rel + "/"
    return ""


def region_of(path):
    parts = [x for x in path.relative_to(JSON_DIR).parts[:-1] if x != "solar"]
    return parts[0] if parts else "bc"


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
        region, city = region_of(f), f.stem
        dirty = False
        for rec in data:
            if not isinstance(rec, dict) or not rec.get("name"):
                continue
            total += 1
            url = profile_url(region, city, rec["name"])
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
