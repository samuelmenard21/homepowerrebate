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
SOURCES = [
    "heat-pump-installers-real.csv", "solar-installers-real.csv",
    "on-heat-pump-installers-real.csv", "on-solar-installers-real.csv",
    "ab-heat-pump-installers-real.csv", "ab-solar-installers-real.csv",
    "ns-heat-pump-installers-real.csv", "ns-solar-installers-real.csv",
    "ma-heat-pump-installers-real.csv", "ma-solar-installers-real.csv",
    "pa-heat-pump-installers-real.csv", "pa-solar-installers-real.csv",
    "co-heat-pump-installers-real.csv", "co-solar-installers-real.csv",
    "vt-heat-pump-installers-real.csv", "vt-solar-installers-real.csv",
    "ca-heat-pump-installers-real.csv", "ca-solar-installers-real.csv",
    "ny-heat-pump-installers-real.csv", "ny-solar-installers-real.csv",
]
OUT = HERE / "installer-emails.csv"

UA = "HomePowerRebateBot/1.0 (+https://homepowerrebate.com; installer directory)"
CONTACT_PATHS = [
    "", "/contact", "/contact-us", "/contact-us/", "/contact.html", "/contactus",
    "/contact-info", "/get-in-touch", "/reach-us", "/pages/contact",
    "/pages/contact-us", "/about", "/about-us",
]
LINK_RE = re.compile(r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.I | re.S)
CONTACT_LINK_HINTS = ("contact", "get-in-touch", "reach-us", "get-a-quote", "quote", "email-us")

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Addresses that show up in markup but aren't real contacts.
JUNK_DOMAINS = {
    "example.com", "sentry.io", "wix.com", "wixpress.com", "squarespace.com",
    "godaddy.com", "shopify.com", "googlemail.com", "schema.org", "w3.org",
    "sentry.wixpress.com", "domain.com", "email.com", "yourdomain.com",
    # "example@mysite.com" is a template-builder placeholder left in page
    # markup (found live on 5 real installer pages, 2026-09-02) — same
    # class of false positive as example.com/domain.com above, just a
    # different platform's default.
    "mysite.com",
}
JUNK_PREFIXES = ("noreply", "no-reply", "donotreply", "postmaster", "abuse", "sentry")
# Image filenames regularly parse as addresses (logo@2x.png).
BAD_TLDS = ("png", "jpg", "jpeg", "gif", "svg", "webp", "css", "js", "woff", "ttf")


def clean(email):
    email = email.strip().strip(".,;:'\"()<>").lower()
    # The regex's local-part class includes "%" (needed for real addresses
    # like first%2Elast@x.com in the wild), but that also lets it swallow a
    # leading URL-encoded space ("%20info@...") from unescaped page text.
    # Strip any leading %XX escape sequences before validating.
    email = re.sub(r"^(%[0-9a-fA-F]{2})+", "", email)
    if "@" not in email:
        return None
    local, _, domain = email.partition("@")
    if domain in JUNK_DOMAINS or any(domain.endswith("." + d) for d in JUNK_DOMAINS):
        return None
    if domain.endswith(BAD_TLDS):
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


def fetch(session, url):
    """GET with an http:// fallback for sites with broken/missing SSL."""
    try:
        r = session.get(url, timeout=10, allow_redirects=True)
        if r.status_code == 200 and "text/html" in r.headers.get("content-type", ""):
            return r
    except requests.exceptions.SSLError:
        pass
    except Exception:
        return None
    if url.startswith("https://"):
        try:
            r = session.get("http://" + url[len("https://"):], timeout=10, allow_redirects=True)
            if r.status_code == 200 and "text/html" in r.headers.get("content-type", ""):
                return r
        except Exception:
            return None
    return None


def extract_emails(html, site_domain, found):
    for m in re.findall(r'mailto:([^"\'?>\s]+)', html, re.I):
        e = clean(m)
        if e:
            found[e] = max(found.get(e, 0), score(e, site_domain) + 50)
    for m in EMAIL_RE.findall(html):
        e = clean(m)
        if e:
            found[e] = max(found.get(e, 0), score(e, site_domain))


def discover_contact_links(html, base_url):
    """Follow real nav/footer links whose href or text suggests a contact
    page — catches sites whose URL structure doesn't match any of the
    guessed CONTACT_PATHS (e.g. /pages/get-a-quote, /contactus-2)."""
    candidates = []
    for href, text in LINK_RE.findall(html):
        hay = (href + " " + re.sub(r"<[^>]+>", "", text)).lower()
        if any(hint in hay for hint in CONTACT_LINK_HINTS):
            candidates.append(urljoin(base_url, href))
    # de-dupe, cap so a large site doesn't blow up the crawl budget
    seen, out = set(), []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
        if len(out) >= 4:
            break
    return out


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
    visited = set()
    queue = list(CONTACT_PATHS)
    discovered_links = False

    while queue:
        path = queue.pop(0)
        url = urljoin(website, path) if path else website
        if url in visited:
            continue
        visited.add(url)

        r = fetch(session, url)
        time.sleep(0.4)  # be polite
        if r is None:
            continue

        extract_emails(r.text, site_domain, found)
        if found:
            result["Source"] = url
            break

        # Only crawl the homepage's own links once, after the fixed guesses
        # are exhausted — avoids following links from every guessed page.
        if not discovered_links and url in (website, website + "/"):
            queue.extend(discover_contact_links(r.text, url))
            discovered_links = True

    if found:
        result["Email"] = max(found, key=found.get)
    elif not result["Source"]:
        result["Source"] = "not found"
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--retry-missing", action="store_true",
                     help="Only re-scrape rows that came up empty last run "
                          "(reads existing installer-emails.csv, keeps found "
                          "emails as-is, retries only the misses).")
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

    existing = {}
    if args.retry_missing:
        if not OUT.exists():
            sys.exit(f"--retry-missing needs an existing {OUT.name} — run without it first.")
        for r in csv.DictReader(OUT.open()):
            key = (r["Business Name"].strip().lower(), r["City"].strip().lower())
            existing[key] = r
        # Only re-scrape the ones that had no website or no email found —
        # "no website" rows would just fail again, so skip those too.
        rows = [
            r for r in rows
            if existing.get((r["Business Name"].strip().lower(), r["City"].strip().lower()), {}).get("Email", "") == ""
            and (r.get("Website") or "").strip()
        ]

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

    if args.retry_missing:
        # Merge: keep every previously-found email, overlay retry results.
        for res in results:
            key = (res["Business Name"].strip().lower(), res["City"].strip().lower())
            existing[key] = res
        results = list(existing.values())

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
