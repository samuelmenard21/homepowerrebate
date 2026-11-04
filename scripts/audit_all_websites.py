#!/usr/bin/env python3
"""Capture and score the homepage of every installer we list (2026-11-04).

One polite fetch per company website (like a visitor; 10 at a time, different hosts), the same 11 checks as installer_review.py, plus the
site platform (WordPress, Wix, Squarespace...), whether the phone number on the page matches the one on the Google listing, and a
"gaps" count. Writes to the owner's private outreach folder, NOT the published site:
  outreach/website-audits.jsonl  (one line per company; rerun skips companies already done unless --refresh)
  outreach/website-audits.csv    (sorted by most gaps first: the list of companies a website or Google profile service could help)
Usage: python3 scripts/audit_all_websites.py [--workers 10] [--limit N] [--refresh]"""
import argparse
import csv
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_installer_rankings as br  # noqa: E402
import installer_review as ir  # noqa: E402

OUT = Path("/Users/sammenard/Downloads/Powerrebate/outreach")
PLATFORMS = [("WordPress", r"wp-content|wp-includes|wordpress"), ("Wix", r"wixstatic|wix\.com|_wixCIDX"), ("Squarespace", r"squarespace"),
             ("Shopify", r"cdn\.shopify|shopify"), ("Webflow", r"webflow"), ("GoDaddy", r"godaddy|secureserver\.net|websitebuilder"),
             ("Weebly", r"weebly"), ("Duda", r"duda(cdn|mobile)|dudaone"), ("HubSpot", r"hs-scripts|hubspot"), ("Joomla", r"joomla")]
lock = threading.Lock()


def domain(u):
    h = urlparse(u if "//" in u else "//" + u).netloc.lower()
    return re.sub(r"^www\.", "", h)


def digits(s):
    return re.sub(r"\D", "", s)[-10:]


def audit(rec):
    site = rec["website"].split("?")[0] if rec["website"] else ""
    out = {k: rec[k] for k in ("name", "region", "city", "services", "email", "phone", "website", "rating", "reviews", "rank")}
    if not site:
        return {**out, "status": "no website on listing", "gaps": 99}
    url, body, secs, err = ir.fetch(site)
    if err:
        return {**out, "status": "fetch failed: " + err[:80], "gaps": 0}
    checks = ir.site_checks(url, body, secs, rec["city"], rec["service"])
    low = body.lower()
    plat = next((n for n, rx in PLATFORMS if re.search(rx, low)), "unknown")
    text = ir.strip(body)
    nap = bool(digits(rec["phone"])) and digits(rec["phone"]) in digits_all(text + " " + body)
    title = (re.search(r"(?is)<title[^>]*>(.*?)</title>", body) or [0, ""])[1].strip()[:140]
    fails = [c[0] for c in checks if not c[1]]
    return {**out, "status": "ok", "final_url": url, "load_s": round(secs, 2) if secs else None, "html_kb": round(len(body) / 1024), "platform": plat,
            "phone_on_page_matches_google": nap, "title": re.sub(r"\s+", " ", title), "passed": len(checks) - len(fails), "of": len(checks),
            "failed_checks": fails, "gaps": len(fails) + (0 if nap else 1)}


def digits_all(s):
    return re.sub(r"\D", "", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    rows = br.load_rows()
    by = {}
    for r in rows:   # one record per company website (a company listed for several services is audited once)
        k = domain(r["website"]) or ("name:" + br.slugify(r["name"]) + r["city"].lower())
        rec = by.setdefault(k, {"name": r["name"], "region": r["region"], "city": r["city"], "services": [], "email": r["email"], "phone": r["phone"],
                                "website": r["website"], "rating": r["rating"], "reviews": r["reviews"], "service": r["service"], "rank": ""})
        rec["services"].append(r["service"])
        if r["reviews"] > rec["reviews"]:
            rec.update({"rating": r["rating"], "reviews": r["reviews"]})
        if not rec["email"] and r["email"]:
            rec["email"] = r["email"]
    recs = list(by.values())
    for r in recs:
        r["services"] = ",".join(sorted(set(r["services"])))
    if a.limit:
        recs = recs[: a.limit]
    jl = OUT / "website-audits.jsonl"
    done = {}
    if jl.exists() and not a.refresh:
        for line in jl.read_text().splitlines():
            d = json.loads(line)
            done[(d["name"], d["city"])] = d
    todo = [r for r in recs if (r["name"], r["city"]) not in done]
    print(f"{len(recs)} companies, {len(done)} already audited, {len(todo)} to do")
    with jl.open("a") as fh, ThreadPoolExecutor(a.workers) as ex:
        for i, res in enumerate(ex.map(audit, todo), 1):
            with lock:
                fh.write(json.dumps(res, ensure_ascii=False) + "\n")
                fh.flush()
            done[(res["name"], res["city"])] = res
            if i % 100 == 0:
                print(i, "done", flush=True)
    allr = sorted(done.values(), key=lambda d: (-d.get("gaps", 0), -float(d.get("reviews") or 0)))
    cols = ["name", "region", "city", "services", "rating", "reviews", "email", "phone", "website", "status", "platform", "load_s", "passed", "of", "gaps",
            "phone_on_page_matches_google", "failed_checks", "title"]
    with (OUT / "website-audits.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for d in allr:
            w.writerow([("; ".join(d[c]) if isinstance(d.get(c), list) else d.get(c, "")) for c in cols])
    ok = sum(1 for d in allr if d.get("status") == "ok")
    print(f"{len(allr)} companies in {OUT/'website-audits.csv'}; {ok} sites read, {sum(1 for d in allr if d.get('status','').startswith('fetch'))} failed, "
          f"{sum(1 for d in allr if d.get('status','').startswith('no website'))} with no website.")


if __name__ == "__main__":
    main()
