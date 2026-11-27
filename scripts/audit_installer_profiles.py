#!/usr/bin/env python3
"""Audit installers' Google Business Profiles from the ranking CSVs.

Support only. This never changes a ranking (rankings stay ordered by Google
reviews) and sends nothing: installer outreach is paused. It reads
installers/*-real.csv, skips blocked companies, and for each company marks the
Whitespark 2026 top-10 map factors it can judge from the fields we already hold
(name, address, phone, website, rating, review count). Everything else (primary
category, hours, pin, review recency, photos, replies, services) is listed as
unknown, never guessed. See .claude/skills/google-business-profile/SKILL.md.

  python3 scripts/audit_installer_profiles.py --city Kelowna
  python3 scripts/audit_installer_profiles.py --region bc --service heat-pump --limit 20
  python3 scripts/audit_installer_profiles.py --region on --out data/reports/installer-profile-audit/on.md
  python3 scripts/audit_installer_profiles.py --summary          # counts only, all regions

Notes are plain words (Grade 6). The Google photo URL column is never read or
printed (Places photos may not be stored).
"""
import argparse
import csv
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import installer_blocklist as bl  # noqa: E402

SERVICES = ["energy-advisor", "energy-auditor", "heat-pump", "solar", "battery", "insulation",
            "windows-doors", "water-heater", "ev-charger", "smart-thermostats", "hrv", "appliances"]
SOCIAL = ("wa.me", "whatsapp.", "facebook.", "fb.com", "instagram.", "linktr.ee", "linkin.bio",
          "business.site", "sites.google.", "yelp.", "tiktok.", "x.com", "twitter.")
MAILBOX = re.compile(r"\b(p\.?\s?o\.?\s?box|po box|mailbox|ups store|pmb\s?\d|postal box|virtual office)\b", re.I)
PHONE_IN_NAME = re.compile(r"\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}")
URL_IN_NAME = re.compile(r"(www\.|https?://|\.com\b|\.ca\b|\.net\b)", re.I)
BAD_NAME_BITS = re.compile(r"\s[|:]\s|\s-\s.*\b(near me|best|24/?7|emergency|#1)\b|\bnear me\b|\bbest\b", re.I)

# effort: 1 = ten minutes, 2 = an hour, 3 = a few weeks
FIXES = {
    "name-stuffed": (1, "Your name on Google has extra words in it (a city, a service or a slogan). Change it to the name on your sign and your papers. Extra words can get the profile suspended."),
    "name-url-phone": (1, "Your name on Google has a phone number or web address in it. Take it out. Google does not allow that."),
    "name-caps": (1, "Your name is in ALL CAPS. Google asks for normal capital letters, the way the name is on your sign."),
    "no-website": (1, "No website is listed. Add your website link so people and Google can see what you do."),
    "social-site": (1, "The website link is a chat or social page. Point it to a real page on your own website."),
    "no-phone": (1, "No phone number is listed. Add a local number that you answer."),
    "mailbox-address": (2, "The address looks like a mailbox or P.O. box. Show a real place where you work, or hide the address and set the areas you serve."),
    "no-address": (2, "No street address is shown. If you work from home, set your service areas (up to 20 cities) instead of leaving it blank."),
    "low-rating": (3, "The rating is under 4.0. Reply calmly to every bad review and ask each happy customer for a review the day the job ends."),
    "mid-rating": (3, "The rating is under 4.5. About 3 in 10 people only call businesses rated 4.5 or higher. Reply to every review and ask every customer."),
    "few-reviews": (3, "There are fewer than 20 reviews. Almost half of people will not call a business with fewer than 20. Send every customer a direct review link when the job ends."),
    "gap-reviews": (3, "The top three in your city have many more reviews. Ask every customer, not just the happy ones, and keep asking every month."),
}


def parse_name(path):
    stem = path.name.replace("-installers-real.csv", "")
    for s in sorted(SERVICES, key=len, reverse=True):
        if stem == s:
            return "bc", s
        if stem.endswith("-" + s):
            return stem[: -len(s) - 1], s
    return None, None


def as_int(v):
    try:
        return int(float(str(v).replace(",", "")))
    except ValueError:
        return None


def as_float(v):
    try:
        return float(v)
    except ValueError:
        return None


def load(region=None, service=None, city=None):
    rows = []
    for p in sorted((ROOT / "installers").glob("*-real.csv")):
        reg, svc = parse_name(p)
        if not svc or (region and reg != region) or (service and svc != service):
            continue
        with open(p, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if city and r.get("City", "").strip().lower() != city.lower():
                    continue
                if bl.is_blocked(r.get("Business Name", ""), r.get("City", ""), r.get("Email", ""),
                                 r.get("Website", ""), r.get("Google Maps URL", "")):
                    continue
                r["_region"], r["_service"] = reg, svc
                rows.append(r)
    return rows


def company_key(r):
    m = re.search(r"cid=(\d+)", r.get("Google Maps URL", ""))
    return m.group(1) if m else (re.sub(r"\W+", "", r["Business Name"].lower()), r["City"].lower())


def peers(rows):
    """Median review count of the three most reviewed companies per region, city and service."""
    by = defaultdict(list)
    for r in rows:
        n = as_int(r.get("Review Count"))
        if n is not None:
            by[(r["_region"], r["City"], r["_service"])].append(n)
    return {k: statistics.median(sorted(v, reverse=True)[:3]) for k, v in by.items() if len(v) >= 3}


def audit(group, top3):
    r = group[0]
    name = r["Business Name"].strip()
    site = (r.get("Website") or "").strip().lower()
    addr = (r.get("Address") or "").strip()
    rating = as_float(r.get("Google Rating"))
    n = as_int(r.get("Review Count"))
    flags = []
    if PHONE_IN_NAME.search(name) or URL_IN_NAME.search(name):
        flags.append("name-url-phone")
    elif BAD_NAME_BITS.search(name) or len(name) > 70:
        flags.append("name-stuffed")
    letters = re.sub(r"[^A-Za-z]", "", name)
    if len(letters) > 4 and letters.isupper():
        flags.append("name-caps")
    if not site:
        flags.append("no-website")
    elif any(s in site for s in SOCIAL):
        flags.append("social-site")
    if not (r.get("Phone") or "").strip():
        flags.append("no-phone")
    if not addr:
        flags.append("no-address")
    elif MAILBOX.search(addr):
        flags.append("mailbox-address")
    if rating is not None:
        if rating < 4.0:
            flags.append("low-rating")
        elif rating < 4.5:
            flags.append("mid-rating")
    if n is not None and n < 20:
        flags.append("few-reviews")
    else:
        gap = [top3.get((g["_region"], g["City"], g["_service"])) for g in group]
        gap = max([x for x in gap if x] or [0])
        if n is not None and gap and n < 50 and n < gap * 0.4:
            flags.append("gap-reviews")
    # factor table: S set by them, E earned, F fixed
    in_city = r["City"].lower() in addr.lower() if addr else None
    return {
        "name": name, "city": r["City"], "region": r["_region"],
        "services": sorted({g["_service"] for g in group}), "rating": rating, "reviews": n,
        "website": r.get("Website", ""), "maps": r.get("Google Maps URL", ""),
        "flags": flags, "address_in_city": in_city, "fixes": sorted(flags, key=lambda f: FIXES[f][0]),
    }


UNKNOWN = ("primary and extra categories, hours and holiday hours, pin placement, reviews in the last 90 days, "
           "photos, owner replies, services list, attributes")


def render(results, limit):
    out = []
    for a in results[:limit] if limit else results:
        rating = f"{a['rating']:.1f}" if a["rating"] is not None else "?"
        out.append(f"### {a['name']} ({a['city']}, {a['region'].upper()})")
        out.append(f"{', '.join(a['services'])} | {rating} stars | {a['reviews'] if a['reviews'] is not None else '?'} reviews")
        if a["maps"]:
            out.append(f"Maps: {a['maps']}")
        if not a["fixes"]:
            out.append("Nothing to fix from the fields we hold.")
        for i, f in enumerate(a["fixes"][:3], 1):
            out.append(f"{i}. {FIXES[f][1]}")
        if len(a["fixes"]) > 3:
            out.append(f"(Also: {', '.join(a['fixes'][3:])})")
        if a["address_in_city"] is False:
            out.append(f"Note: the address is not in {a['city']}. That cannot be fixed, so do not advise it.")
        out.append(f"Unknown from our data, check on Maps: {UNKNOWN}.")
        out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--region", help="csv prefix: bc (no prefix), on, ab, ca, ma ...")
    ap.add_argument("--service")
    ap.add_argument("--city")
    ap.add_argument("--recommended-only", action="store_true", help="only rows marked Recommended")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()

    rows = load(a.region, a.service, a.city)
    top3 = peers(rows)
    groups = defaultdict(list)
    for r in rows:
        if a.recommended_only and r.get("HomePowerRebate Recommended") != "Yes":
            continue
        groups[company_key(r)].append(r)
    results = [audit(g, top3) for g in groups.values()]
    results.sort(key=lambda x: (-len(x["fixes"]), x["city"], x["name"]))

    c = Counter(f for x in results for f in x["flags"])
    summary = [f"Audited {len(results)} companies from {len(rows)} ranking rows.",
               f"With at least one fix: {sum(1 for x in results if x['flags'])}."]
    summary += [f"- {f}: {n}" for f, n in c.most_common()]
    text = "\n".join(summary)
    if not a.summary:
        text += "\n\n" + render(results, a.limit)
    if a.out:
        p = Path(a.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {p} ({len(results)} companies)")
    else:
        print(text)


if __name__ == "__main__":
    main()
