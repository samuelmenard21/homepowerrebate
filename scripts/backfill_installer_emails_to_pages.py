#!/usr/bin/env python3
"""
Add an email contact link to every installer profile page — found 2026-09-01
that email data was fully recovered into installers/json/*/*.json months ago
(and re-confirmed present there) but the profile-page generator never
rendered it: 0 of 896 profile pages had a mailto: link despite the site
claiming "installers with emails" in project notes.

Two path conventions exist:
  - BC (original, unprefixed): installers/profiles/<city>/<slug>/index.html
    -> installers/json/<city>.json
  - Every other region (prefixed): installers/profiles/<region>/<city>/<slug>/index.html
    -> installers/json/<region>/<city>.json (plus category subdirs like
       .../solar/<city>.json for businesses only in the solar list)

Matches business name (from the page's JSON-LD "name" field) against every
JSON file for that city (base + solar + any other category subdir) since a
business can appear in multiple category lists. Inserts an "Email" button
into the .ip-actions row (uniform across all 896 pages, confirmed via grep)
right after the Call button, using the same ip-btn-outline style.

Run from the Powerrebate root:
  python3 scripts/backfill_installer_emails_to_pages.py --dry-run
  python3 scripts/backfill_installer_emails_to_pages.py
"""
import argparse
import glob
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGION_CODES = {"ab", "ma", "ns", "ca", "ny", "pa", "co", "vt", "on"}


def slugify(name):
    s = name.lower().strip()
    s = re.sub(r"[&']", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def find_json_candidates(profile_path):
    """Return list of json file paths that might contain this business,
    based on the profile page's own directory structure."""
    rel = os.path.relpath(profile_path, os.path.join(ROOT, "installers/profiles"))
    parts = rel.split(os.sep)  # e.g. ["ab","calgary","some-slug","index.html"] or ["abbotsford","some-slug","index.html"]

    candidates = []
    if len(parts) == 4 and parts[0] in REGION_CODES:
        region, city = parts[0], parts[1]
        base = os.path.join(ROOT, "installers/json", region)
        candidates.append(os.path.join(base, f"{city}.json"))
        for sub in ("solar", "insulation", "battery", "water-heater"):
            candidates.append(os.path.join(base, sub, f"{city}.json"))
    elif len(parts) == 3:
        city = parts[0]
        base = os.path.join(ROOT, "installers/json")
        candidates.append(os.path.join(base, f"{city}.json"))
        candidates.append(os.path.join(base, "solar", f"{city}.json"))
    return [c for c in candidates if os.path.exists(c)]


def find_email(profile_path, business_name):
    target_slug = slugify(business_name)
    for jf in find_json_candidates(profile_path):
        try:
            data = json.load(open(jf, encoding="utf-8"))
        except Exception:
            continue
        for entry in data:
            if slugify(entry.get("name", "")) == target_slug:
                email = entry.get("email")
                if email:
                    return email
    return None


def process(profile_path, dry_run):
    text = open(profile_path, encoding="utf-8").read()
    if "mailto:" in text:
        return "already_has_email"

    m = re.search(r'"name":\s*"([^"]+)"', text)
    if not m:
        return "no_name_found"
    business_name = m.group(1).replace('\\u0026', '&').replace('\\"', '"')

    email = find_email(profile_path, business_name)
    if not email:
        return "no_email_in_data"

    call_btn_re = re.compile(r'(<a href="tel:[^"]*" class="ip-btn ip-btn-outline">[^<]*</a>)')
    m2 = call_btn_re.search(text)
    if not m2:
        website_btn_re = re.compile(r'(<a href="[^"]*" target="_blank" rel="noopener" class="ip-btn ip-btn-primary">Visit Website</a>)')
        m2 = website_btn_re.search(text)
    if not m2:
        return "no_call_button_anchor"

    email_link = f'\n    <a href="mailto:{html.escape(email)}" class="ip-btn ip-btn-outline">Email {html.escape(business_name)}</a>'
    new_text = text[:m2.end()] + email_link + text[m2.end():]

    if not dry_run:
        open(profile_path, "w", encoding="utf-8").write(new_text)
    return "added"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(ROOT, "installers/profiles/**/index.html"), recursive=True))
    stats = {}
    no_data = []
    for f in files:
        result = process(f, args.dry_run)
        stats[result] = stats.get(result, 0) + 1
        if result == "no_email_in_data":
            no_data.append(os.path.relpath(f, ROOT))

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Processed {len(files)} profile pages:")
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    if no_data:
        print(f"\nFirst 10 with no email in source data:")
        for p in no_data[:10]:
            print(f"  {p}")


if __name__ == "__main__":
    main()
