#!/usr/bin/env python3
"""
Read each energy advisor's and auditor's website once and note which services it mentions (added 2026-10-17).

Profiles show these as "Services mentioned on their website" tags. We record facts (does the site mention EnerGuide
evaluations, blower door testing...), never copy their wording. Websites come from the Google match
(data/energy-advisor-places.json) or the RESNET list. Results: data/energy-advisor-sites.json, keyed by website.
A site is re-read only when it has no entry or --refresh is given.

  python3 scripts/scan_advisor_websites.py [--refresh]
"""
import argparse
import json
import re
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "energy-advisor-sites.json"
CTX = ssl.create_default_context()
# tag -> (pattern, case-sensitive?)
SERVICES = {
    "EnerGuide home evaluations": (r"energuide", False),
    "Pre- and post-retrofit evaluations": (r"pre-?\s?retrofit|post-?\s?retrofit|pre and post", False),
    "Blower door testing": (r"blower[- ]door|air ?tightness test|air leakage test", False),
    "Thermal imaging": (r"thermal imag|infrared (?:scan|camera|imag)|thermography", False),
    "New home energy ratings": (r"new home|new construction|energy star for new homes|net zero home|step code", False),
    "Rebate and grant help": (r"rebate|grant|incentive", False),
    "Home inspections": (r"home inspection", False),
    "HERS ratings": (r"\bHERS\b", True),
    "BPI certified": (r"\bBPI\b", True),
    "Home Energy Score": (r"home energy score", False),
    "Commercial buildings": (r"commercial building|multi-?unit|multifamily|multi-family", False),
    "French service": (r"\bfrançais\b|en français", False),
}
LINKS = re.compile(r'href="([^"#]*(?:service|energuide|evaluation|assessment|audit|rating|about)[^"#]*)"', re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh) HomePowerRebate-directory"})
    try:
        with urllib.request.urlopen(req, timeout=15, context=CTX) as r:
            return r.read(800_000).decode("utf-8", "ignore"), r.geturl()
    except Exception:
        return "", url


def text(page):
    page = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", page, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page))


def scan(url):
    page, final = fetch(url)
    if not page:
        return url, {"loaded": False, "checked": date.today().isoformat()}
    body = text(page)
    for href in list(dict.fromkeys(LINKS.findall(page)))[:3]:
        sub = urllib.request.urljoin(final, href)
        if sub.startswith("http") and sub.split("/")[2] == final.split("/")[2]:
            body += " " + text(fetch(sub)[0])
    tags = [t for t, (pat, cased) in SERVICES.items() if re.search(pat, body, 0 if cased else re.I)]
    return url, {"loaded": True, "services": tags, "checked": date.today().isoformat()}


def websites():
    sites = set()
    places = json.loads((ROOT / "data" / "energy-advisor-places.json").read_text())
    sites |= {v["website"] for v in places.values() if v.get("website")}
    for c in json.loads((ROOT / "data" / "resnet-rating-companies-2026.json").read_text())["companies"]:
        if c.get("website"):
            sites.add(c["website"] if c["website"].startswith("http") else "https://" + c["website"])
    for e in json.loads((ROOT / "data" / "energy-advisors-extra.json").read_text()):
        if e.get("website"):
            sites.add(e["website"])
    return sorted(sites)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    done = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [u for u in websites() if args.refresh or u not in done]
    with ThreadPoolExecutor(12) as pool:
        for url, res in pool.map(scan, todo):
            done[url] = res
    OUT.write_text(json.dumps(done, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"{len(todo)} websites read, {sum(1 for v in done.values() if v.get('loaded'))} of {len(done)} loaded.")


if __name__ == "__main__":
    main()
