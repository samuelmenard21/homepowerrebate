#!/usr/bin/env python3
"""Find public contact emails for installers that have none, and write them into the CSVs and the live JSON.

  python3 scripts/refresh_installer_emails.py --regions nj,il,wa,mn,mi          # the new regions
  python3 scripts/refresh_installer_emails.py --regions all --limit 20          # try a few first
  python3 scripts/refresh_installer_emails.py --regions nj --dry-run            # report only, write nothing

Only rows with a website and an empty Email are visited. Only pages the business publishes itself are read
(same rules as installers/find-installer-emails.py: polite rate, identifies itself, skips template and no-reply addresses).
Found emails go to: installers/<region>-<service>-installers-real.csv (Email column), installers/json/** (matching "email" fields, only
when empty; file formatting is preserved), and data/installer-emails-found.csv (a log with the page each came from).
Never overwrites an email that is already there. Afterwards run build_installer_rankings.py (updates the lead-routing allow list)
and backfill_installer_emails_to_pages.py (adds the Email button to profile pages).
Outreach rules (CASL for Canada, CAN-SPAM for the US) are in installers/OUTREACH.md: a published business address is for business-relevant mail only.
"""
import argparse, csv, importlib.util, json, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import regions

spec = importlib.util.spec_from_file_location("find_installer_emails", ROOT / "installers" / "find-installer-emails.py")
fie = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fie)

LOG = ROOT / "data" / "installer-emails-found.csv"


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("&", "and"))


def csv_files(codes):
    for p in sorted((ROOT / "installers").glob("*-installers-real.csv")):
        m = re.match(r"(?:([a-z]{2})-)?(heat-pump|solar|insulation|battery|ev-charger|windows-doors)-installers-real\.csv$", p.name)
        if m and (codes is None or (m.group(1) or "bc") in codes):
            yield p


def update_json(found):
    """found: {(norm name, norm city): email}. Sets email only where it is empty; keeps each file's formatting."""
    changed = 0
    for jp in (ROOT / "installers" / "json").rglob("*.json"):
        try:
            raw = jp.read_text()
            data = json.loads(raw)
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        city = norm(jp.stem.replace("-", " "))
        touched = False
        for item in data:
            if isinstance(item, dict) and not item.get("email"):
                e = found.get((norm(item.get("name", "")), city))
                if e:
                    item["email"] = e
                    touched = True
        if not touched:
            continue
        for kw in ({"indent": 2}, {"indent": 2, "ensure_ascii": False}):
            if json.dumps(json.loads(raw), **kw) in (raw, raw.rstrip("\n")):
                jp.write_text(json.dumps(data, **kw) + ("\n" if raw.endswith("\n") else ""))
                changed += 1
                break
        else:
            print("  skipped (format not reproducible):", jp.relative_to(ROOT))
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regions", default="all", help="comma list of region codes, or all")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    codes = None if a.regions == "all" else set(a.regions.split(","))
    bad = (codes or set()) - set(regions.CODES)
    if bad:
        sys.exit(f"Unknown region(s): {sorted(bad)}")

    files = list(csv_files(codes))
    rows = {}
    for p in files:
        for r in csv.DictReader(p.open(encoding="utf-8")):
            if not (r.get("Email") or "").strip() and (r.get("Website") or "").strip():
                rows.setdefault((norm(r["Business Name"]), norm(r["City"])), r)
    todo = list(rows.values())[: a.limit or None]
    print(f"{len(todo)} businesses with a website and no email (from {len(files)} CSV files)", flush=True)
    found, log = {}, []
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs = {pool.submit(fie.scrape, r): r for r in todo}
        for i, f in enumerate(as_completed(futs), 1):
            res = f.result()
            if res.get("Email"):
                found[(norm(res["Business Name"]), norm(res["City"]))] = res["Email"]
                log.append((res["City"], res["Business Name"], res["Website"], res["Email"], res.get("Source", "")))
            print(f"  [{i:>4}/{len(todo)}] {'OK ' if res.get('Email') else '-- '} {res['Business Name'][:40]:42} {res.get('Email', '')}", flush=True)
    print(f"\n{len(found)}/{len(todo)} emails found")
    if a.dry_run or not found:
        return
    for p in files:
        rows_ = list(csv.DictReader(p.open(encoding="utf-8")))
        names = rows_[0].keys() if rows_ else []
        n = 0
        for r in rows_:
            if not (r.get("Email") or "").strip():
                e = found.get((norm(r["Business Name"]), norm(r["City"])))
                if e:
                    r["Email"] = e
                    n += 1
        if n:
            with p.open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(names))
                w.writeheader()
                w.writerows(rows_)
            print(f"  {p.name}: {n} emails")
    print(f"JSON files updated: {update_json(found)}")
    new = not LOG.exists()
    with LOG.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["City", "Business", "Website", "Email", "Found on", "Date"])
        for row in log:
            w.writerow([*row, time.strftime("%Y-%m-%d")])
    print("Next: python3 scripts/build_installer_rankings.py && python3 scripts/backfill_installer_emails_to_pages.py && python3 scripts/build_get_quotes.py")


if __name__ == "__main__":
    main()
