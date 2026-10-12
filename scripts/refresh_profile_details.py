#!/usr/bin/env python3
"""Surgical, idempotent touch-up of existing installer profile pages (never regenerates them, so curated photos and text stay).

1. Rating shows one decimal ("4.8★", not "5★") and the review count has a comma, in the header and in "Other installers".
2. The rebate card shows the city's real amount from city-rebate-lookup.json (only when it contains a dollar figure).
3. The quote box names the city.
Run after generate_installer_profiles.py / add_missing_installer_profiles.py.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROF = ROOT / "installers" / "profiles"
LOOKUP = json.loads((ROOT / "city-rebate-lookup.json").read_text(encoding="utf-8"))
CAT = {"Heat Pump & HVAC": "heat_pump", "Solar": "solar", "Insulation": "insulation", "Home Battery": "battery"}
RATING = re.compile(r"(\d\.\d)★ from ([\d,]+) reviews on Google Maps")


def region_city(f):
    parts = f.relative_to(PROF).parts[:-2]
    if len(parts) == 2:
        return parts[0], parts[1]
    if len(parts) == 1:
        city = parts[0]
        hits = [r for r in ("bc", "on") if f"{r}|{city.replace('-', ' ')}" in LOOKUP]
        return (hits[0] if len(hits) == 1 else None), city
    return None, None


def main():
    pages = {f: f.read_text(encoding="utf-8") for f in PROF.rglob("index.html")}
    ratings = {}
    for f, h in pages.items():
        m = RATING.search(h)
        if m:
            ratings["/" + str(f.parent.relative_to(ROOT)) + "/"] = float(m.group(1))
    changed = 0
    for f, h in pages.items():
        o = h
        m = RATING.search(h)
        if m:
            h = re.sub(r'(<div class="ip-rating-num">)\d(?:\.\d)?★(</div><div class="ip-rating-count">)[\d,]+ (?:Google )?reviews',
                       lambda x: f'{x.group(1)}{m.group(1)}★{x.group(2)}{m.group(2)} Google reviews', h)
        h = re.sub(r'(<a href="(/installers/profiles/[^"]+/)" class="ip-nearby-item"><span>[^<]*</span><span class="ip-nearby-rating">)\d(?:\.\d)?★',
                   lambda x: f'{x.group(1)}{ratings[x.group(2)]:.1f}★' if x.group(2) in ratings else x.group(0), h)
        region, city = region_city(f)
        if region and city:
            lk = LOOKUP.get(f"{region}|{city.replace('-', ' ')}")
            if lk:
                def card(x):
                    cat = CAT.get(x.group(2).strip())
                    amt = (lk.get("categories") or {}).get(cat or "")
                    if not amt or "$" not in amt:
                        return x.group(0)
                    return (f'<div class="ip-program-name">{html.escape(lk.get("utility") or x.group(1))}</div>'
                            f'<div class="ip-program-detail">{html.escape(amt)} <span style="color:#7a7264">(see the city page for eligibility and sources)</span></div>')
                h = re.sub(r'<div class="ip-program-name">([^<]*?) \(([^)]*)\)</div>\s*<div class="ip-program-detail">See [^<]*</div>', card, h)
            cname = city.replace("-", " ").title().replace("Mcmurray", "McMurray")
            h = h.replace("<p>We'll pass your details along and follow up with your rebate breakdown.</p>",
                          f"<p>Tell them you're in {cname}. We'll pass your details along and follow up with your {cname} rebate breakdown. Free, and nobody pays to be listed.</p>")
        if h != o:
            f.write_text(h, encoding="utf-8")
            changed += 1
    print(f"touched up {changed} of {len(pages)} profile pages")


if __name__ == "__main__":
    main()
