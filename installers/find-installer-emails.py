#!/usr/bin/env python3
"""
Recover contact emails for the installer list.

The Google Places API doesn't return email addresses, which is why the Email
column came back empty. Most of these businesses publish one on their own site,
so this visits each website and pulls it from the usual places.

Only reads publicly published pages. Rate-limited and identifies itself.

    python3 find-installer-emails.py            # writes installer-emails.csv
    python3 find-installer-emails.py --limit 10 # try a handful first
"""

import argparse
import csv
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

try:
    import requests
except ImportError:
    sys.exit("pip3 install requests")

HERE = Path(__file__).parent
SOURCES = ["heat-pump-installers-real.csv", "solar-installers-real.csv"]
OUT = HERE / "installer-emails.csv"

UA = "HomePowerRebateBot/1.0 (+https://homepowerrebate.com; installer directory)"
CONTACT_PATHS = ["", "/contact", "/contact-us", "/contact.html", "/about", "/get-a-quote"]

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Addresses that show up in markup but aren't real contacts.
JUNK_DOMAINS = {
    "example.com", "sentry.io", "wix.com", "wixpress.com", "squarespace.com",
    "godaddy.com", "shopify.com", "googlemail.com", "schema.org", "w3.org",
    "sentry.wixpress.com", "domain.com", "email.com", "yourdomain.com",
}
JUNK_PREFIXES = ("noreply", "no-reply", "donotreply", "postmaster", "abuse", "sentry")
# Image filenames regularly parse as addresses (logo@2x.png).
BAD_TLDS = ("png", "jpg", "jpeg", "gif", "svg", "webp", "css", "js", "woff", "ttf")


def clean(email):
    email = email.strip().strip(".,;:'\"()<>").lower()
    if "@" not in email:
        return None
    local, _, domain = email.partition("@")
    if domain in JUNK_DOMAINS or domain.endswith(BAD_TLDS):
        return None
    if local.startswith(JUNK_PREFIXES):
        return None
    if len(local) < 2 or len(domain) < 4 or "." not in domain:
        return None
    return email


def score(email, site_domain):
    """Prefer an address on the company's own domain, then a role account."""
    domain = email.split("@")[1]
    s = 0
    if site_domain and domain.endswith(site_domain.replace("www.", "")):
        s += 100
    if email.split("@")[0] in ("info", "contact", "sales", "hello", "office", "admin"):
        s += 20
    if any(f in domain for f in ("gmail", "hotmail", "outlook", "yahoo", "shaw", "telus")):
        s += 5
    return s


def scrape(row):
    website = (row.get("Website") or "").strip()
    result = {
        "City": row["City"],
        "Business Name": row["Business Name"],
        "Phone": row.get("Phone", ""),
        "Website": website,
        "Google Rating": row.get("Google Rating", ""),
        "Review Count": row.get("Review Count", ""),
        "Email": "",
        "Source": "",
    }
    if not website:
        result["Source"] = "no website"
        return result

    if not website.startswith("http"):
        website = "https://" + website
    site_domain = urlparse(website).netloc

    found = {}
    session = requests.Session()
    session.headers["User-Agent"] = UA

    for path in CONTACT_PATHS:
        url = urljoin(website, path) if path else website
        try:
            r = session.get(url, timeout=10, allow_redirects=True)
            if r.status_code != 200 or "text/html" not in r.headers.get("content-type", ""):
                continue
            html = r.text
            # mailto: links are the most reliable signal
            for m in re.findall(r'mailto:([^"\'?>\s]+)', html, re.I):
                e = clean(m)
                if e:
                    found[e] = max(found.get(e, 0), score(e, site_domain) + 50)
            for m in EMAIL_RE.findall(html):
                e = clean(m)
                if e:
                    found[e] = max(found.get(e, 0), score(e, site_domain))
            if found:
                result["Source"] = url
                break
        except Exception:
            continue
        finally:
            time.sleep(0.4)  # be polite

    if found:
        result["Email"] = max(found, key=found.get)
    elif not result["Source"]:
        result["Source"] = "not found"
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    rows, seen = [], set()
    for src in SOURCES:
        p = HERE / src
        if not p.exists():
            continue
        for r in csv.DictReader(p.open()):
            key = (r["Business Name"].strip().lower(), r["City"].strip().lower())
            if key not in seen:
                seen.add(key)
                rows.append(r)

    if args.limit:
        rows = rows[: args.limit]
    print(f"Checking {len(rows)} businesses...\n", flush=True)

    results, done = [], 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(scrape, r): r for r in rows}
        for f in as_completed(futures):
            res = f.result()
            results.append(res)
            done += 1
            mark = "OK " if res["Email"] else "-- "
            print(f"  [{done:>3}/{len(rows)}] {mark} {res['Business Name'][:38]:40} {res['Email']}", flush=True)

    results.sort(key=lambda r: (r["City"], r["Business Name"]))
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    hits = sum(1 for r in results if r["Email"])
    print(f"\n{hits}/{len(results)} emails found ({hits/len(results)*100:.0f}%)")
    print(f"Written to {OUT.name}")
    print("\nNo email usually means the site only offers a contact form.")


if __name__ == "__main__":
    main()
