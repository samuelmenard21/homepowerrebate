#!/usr/bin/env python3
"""
Keep only real energy advisors (Canada) and home energy auditors (US) in installers/*energy-advisor- and
*energy-auditor-installers-real.csv.

The Places search for "registered energy advisor" also returns oil companies, HVAC shops
and solar firms with "Energy" in their name. A row stays only when the company's own
website (home page, or an /energy-advisor style page it links to) mentions EnerGuide,
a registered energy advisor, or home energy evaluations/assessments/audits. Everything
dropped is written to data/installer-cleanup-log.csv with the reason.

  python3 scripts/verify_energy_advisors.py            # check and rewrite the CSVs
  python3 scripts/verify_energy_advisors.py --dry-run  # print what would be dropped
"""
import argparse
import csv
import re
import ssl
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIGNAL = re.compile(r"energuide|registered energy advis|energy advisor|home energy (?:evaluation|assessment|audit)|"
                    r"energy (?:evaluation|assessment|audit)s?\b|blower door|pre-retrofit|post-retrofit|resnet|home energy score", re.I)
SIGNAL_CASED = re.compile(r"\bBPI\b|\bHERS (?:rat|index|score)")  # case-sensitive: "hers" is also a pronoun
SUBPAGE = re.compile(r'href="([^"#]*(?:energuide|energy-advis|evaluation|assessment|audit|services)[^"#]*)"', re.I)
# Owner-confirmed advisors (an email from the company) stay even if their site blocks our reader.
CONFIRMED = {"thrive energy inc"}
CTX = ssl.create_default_context()


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh) HomePowerRebate-advisor-check"})
    try:
        with urllib.request.urlopen(req, timeout=15, context=CTX) as r:
            return r.read(600_000).decode("utf-8", "ignore"), r.geturl()
    except Exception:
        return "", url


def is_advisor(website):
    if not website:
        return False, "no website"
    page, final = fetch(website)
    if not page:
        return False, "website did not load"
    text = re.sub(r"<[^>]+>", " ", page)
    if SIGNAL.search(text) or SIGNAL_CASED.search(text):
        return True, "home page"
    for href in list(dict.fromkeys(SUBPAGE.findall(page)))[:4]:
        sub = urllib.request.urljoin(final, href)
        if not sub.startswith("http"):
            continue
        sp, _ = fetch(sub)
        st = re.sub(r"<[^>]+>", " ", sp)
        if SIGNAL.search(st) or SIGNAL_CASED.search(st):
            return True, sub
    return False, "website never mentions EnerGuide or energy evaluations"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    log = []
    for f in sorted((ROOT / "installers").glob("*energy-a[du]*-installers-real.csv")):
        rows = list(csv.DictReader(f.open(encoding="utf-8")))
        if not rows:
            continue
        keep = []
        sites = {r.get("Website", "").strip() for r in rows if r["Business Name"].strip().lower() not in CONFIRMED}
        with ThreadPoolExecutor(12) as pool:  # one fetch per website, 12 at a time
            checked = dict(zip(sites, pool.map(is_advisor, sites)))
        for r in rows:
            name = r["Business Name"].strip()
            if name.lower() in CONFIRMED:
                ok, why = True, "confirmed by the company"
            else:
                ok, why = checked[r.get("Website", "").strip()]
            print(f"{'KEEP' if ok else 'DROP'}  {f.name[:2]}  {r['City']:<16} {name[:50]:<50} {why[:60]}")
            if ok:
                keep.append(r)
            else:
                log.append([f.name, name, r["City"], "row removed", f"advisor check: {why}"])
        if not args.dry_run:
            with f.open("w", newline="", encoding="utf-8") as out:
                w = csv.DictWriter(out, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(keep)
    if log and not args.dry_run:
        with (ROOT / "data" / "installer-cleanup-log.csv").open("a", newline="", encoding="utf-8") as out:
            csv.writer(out).writerows(log)
    print(f"{len(log)} rows dropped.")


if __name__ == "__main__":
    sys.exit(main())
