#!/usr/bin/env python3
"""Open dataset export of the verified rebate facts, for Zenodo, GitHub and Data Is Plural (2026-10-27).
Writes data-release/dataset/<YYYY-MM>/ with:
  rebate-programs.csv  every fact in data/verified-facts/*.json as it stands today (one row per program rule), with its official source and the date we read it
  rebate-changes.csv   what changed since a baseline commit: programs added, status changes, amount changes (same logic as the monthly data release page)
  README.md            what the data is, every column, how it was collected, limits, license (CC BY 4.0) and how to cite
  datapackage.json     machine-readable description (Frictionless Data) of the two tables
Built only from the facts files, so nothing is typed here. Internal `notes` are left out on purpose.
CSV is gitignored and the host serves no .csv, so the files are uploaded by hand (Zenodo, GitHub); only this script is committed.
Usage: python3 scripts/build_dataset_export.py 2026-10 [--baseline <git ref>]   (default baseline: last commit before the month began)
"""
import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_data_release as dr  # noqa: E402

COUNTRY = {"Canada (federal)": "CA", "General": ""}
CA_PROV = {"British Columbia", "Ontario", "Alberta", "Nova Scotia", "Manitoba", "Saskatchewan", "Quebec", "Newfoundland and Labrador",
           "Prince Edward Island", "New Brunswick", "Yukon", "Northwest Territories", "Nunavut"}
PROGRAM_COLS = ["id", "region", "country", "program", "status", "amount", "eligibility", "dates", "claim", "source_url", "verified_on"]
CHANGE_COLS = ["change", "id", "region", "program", "status_now", "status_was", "amount_now", "amount_was", "source_url", "verified_on"]
DESC = {
    "id": "Stable id of the fact, e.g. federal-0-national-heat-pump-rebate. A program keeps its id when its amount or status changes in our files.",
    "region": "Province, state or other area the rule applies to (federal facts are 'Canada (federal)').",
    "country": "CA, US, or empty for facts that apply to neither (general notes).",
    "program": "Program name as the administrator calls it.",
    "status": "One of: active (open now), upcoming (announced, not open), waitlist, paused, closed, check (we could not confirm), info (background note, not a rebate).",
    "amount": "Rebate amount as published, in the program's own currency (CAD for Canada, USD for the US). Text, because programs publish ranges, per-ton rates and conditions.",
    "eligibility": "Who qualifies, as published.",
    "dates": "Opening, closing or deadline dates as published.",
    "claim": "One-sentence summary of the program rule, written by us.",
    "source_url": "Official page the rule was read from (utility, government or program administrator).",
    "verified_on": "ISO date we last read that page.",
    "change": "added, status_changed or amount_changed, compared with the baseline.",
    "status_now": "Status today.", "status_was": "Status at the baseline (status_changed rows).",
    "amount_now": "Amount today.", "amount_was": "Amount at the baseline (amount_changed rows).",
}


def country_of(region):
    if region in COUNTRY:
        return COUNTRY[region]
    return "CA" if region in CA_PROV else "US"


def clean(s):
    return " ".join((s or "").split())


def programs(names):
    rows = []
    for f in sorted((ROOT / "data/verified-facts").glob("*.json")):
        region = names.get(f.stem, f.stem)
        for x in json.loads(f.read_text())["facts"]:
            rows.append({"id": x["id"], "region": region, "country": country_of(region), "program": clean(x["program"]), "status": x["status"],
                         "amount": clean(x.get("amount")), "eligibility": clean(x.get("eligibility")), "dates": clean(x.get("dates")),
                         "claim": clean(x.get("claim")), "source_url": x.get("source_url", ""), "verified_on": x.get("verified_on", "")})
    return rows


def changes(baseline, names):
    added, status, amount, _, _ = dr.fact_diff(baseline, names)
    rows = []
    for r in added:
        rows.append({"change": "added", "id": r["id"], "region": r["region"], "program": clean(r["program"]), "status_now": r["status"], "status_was": "",
                     "amount_now": clean(r["amount"]), "amount_was": "", "source_url": r["source"], "verified_on": r["verified_on"]})
    for r in status:
        rows.append({"change": "status_changed", "id": r["id"], "region": r["region"], "program": clean(r["program"]), "status_now": r["status"],
                     "status_was": r["was"], "amount_now": clean(r["amount"]), "amount_was": "", "source_url": r["source"], "verified_on": r["verified_on"]})
    for r in amount:
        rows.append({"change": "amount_changed", "id": r["id"], "region": r["region"], "program": clean(r["program"]), "status_now": r["status"],
                     "status_was": "", "amount_now": clean(r["amount"]), "amount_was": clean(r["was_amount"]), "source_url": r["source"], "verified_on": r["verified_on"]})
    return rows


def write_csv(path, cols, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def readme(month, prog, chg, baseline_date, today):
    st = {}
    for r in prog:
        st[r["status"]] = st.get(r["status"], 0) + 1
    regions = sorted({r["region"] for r in prog})
    kinds = {}
    for r in chg:
        kinds[r["change"]] = kinds.get(r["change"], 0) + 1
    cols = "\n".join(f"- `{c}`: {DESC[c]}" for c in PROGRAM_COLS)
    ccols = "\n".join(f"- `{c}`: {DESC[c]}" for c in CHANGE_COLS if c in DESC and c not in PROGRAM_COLS or c in ("id", "region", "program", "source_url", "verified_on"))
    return f"""# Home energy rebate programs in Canada and the US, with sources and change history ({month})

A hand-checked table of home energy rebate rules (heat pumps, solar, batteries, insulation, windows, water heaters, EV chargers, heating bill help) for
Canadian provinces and US states, one row per program rule, each with the official page it was read from and the date we last read it. A second table lists what changed
since {baseline_date}: programs added, status changes (open, closed, paused, starting soon) and amount changes.

Published by HomePowerRebate (https://homepowerrebate.com/), an independent site, not a government or utility. Snapshot date: {today}.

## Files

- `rebate-programs.csv`: {len(prog)} rows, current snapshot. Status counts: {", ".join(f"{k} {v}" for k, v in sorted(st.items()))}.
- `rebate-changes.csv`: {len(chg)} rows since {baseline_date} ({", ".join(f"{k} {v}" for k, v in sorted(kinds.items()))}). Many "added" rows are new regions we started covering, not new programs.
- `datapackage.json`: machine-readable schema for both tables.

## Columns: rebate-programs.csv

{cols}

## Columns: rebate-changes.csv

Same names as above where they overlap, plus:
- `change`: added, status_changed or amount_changed, compared with the baseline.
- `status_now`, `status_was`, `amount_now`, `amount_was`: the value today and at the baseline.

## Coverage

{len(regions)} regions: {", ".join(regions)}.
Coverage is what we have read, not a complete census of every local program. A region with few rows is under-covered, not rebate-free.

## How it was collected

Rows are read from the program administrator's own page (utility, provincial or state agency, federal department), and `source_url` names that page. A few details, mostly about the federal program announced Oct 8, 2026, rest on news reports of government documents; the `claim` or `eligibility` text says so where that is the case.\nRows with status `check` are ones we could not confirm on the official page. Status `info` rows are background notes, not rebates. Rows without a `source_url` (at most a few) were not linked to one page.\nRebate rules change often. Treat `verified_on` as the freshness date and confirm with the administrator before relying on a row to apply.

## Limits

- Amounts are text as published (ranges, per-ton rates, conditions), not normalised numbers.
- Eligibility and dates are shortened to what fits one cell; the source page has the full rules.
- Currency is CAD for Canadian programs and USD for US programs.
- This is information, not advice, and not an offer or a guarantee of any rebate.

## License and citation

Creative Commons Attribution 4.0 International (CC BY 4.0): https://creativecommons.org/licenses/by/4.0/ . Use it freely, including commercially, with credit.

Suggested citation: HomePowerRebate (2026). Home energy rebate programs in Canada and the US, with sources and change history ({month}). https://homepowerrebate.com/data-release/

Questions or corrections: hello@homepowerrebate.com
"""


def datapackage(month, today):
    def table(name, cols):
        return {"name": name, "path": f"{name}.csv", "format": "csv", "mediatype": "text/csv", "encoding": "utf-8",
                "schema": {"fields": [{"name": c, "type": "date" if c == "verified_on" else "string", "description": DESC[c]} for c in cols]}}
    return {"name": f"home-energy-rebate-programs-{month}", "title": "Home energy rebate programs in Canada and the US, with sources and change history",
            "version": month, "created": today, "licenses": [{"name": "CC-BY-4.0", "path": "https://creativecommons.org/licenses/by/4.0/", "title": "Creative Commons Attribution 4.0"}],
            "homepage": "https://homepowerrebate.com/data-release/", "resources": [table("rebate-programs", PROGRAM_COLS), table("rebate-changes", CHANGE_COLS)]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("month")
    ap.add_argument("--baseline")
    a = ap.parse_args()
    y, m = a.month.split("-")
    first = f"{y}-{m}-01"
    base = a.baseline or subprocess.check_output(["git", "rev-list", "-1", f"--before={first}", "HEAD"], cwd=ROOT, text=True).strip()
    bdate = subprocess.check_output(["git", "show", "-s", "--format=%cs", base], cwd=ROOT, text=True).strip()
    names = dr.region_names()
    prog, chg = programs(names), changes(base, names)
    out = ROOT / "data-release" / "dataset" / a.month
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "rebate-programs.csv", PROGRAM_COLS, prog)
    write_csv(out / "rebate-changes.csv", CHANGE_COLS, chg)
    today = date.today().isoformat()
    (out / "README.md").write_text(readme(a.month, prog, chg, bdate, today), encoding="utf-8")
    (out / "datapackage.json").write_text(json.dumps(datapackage(a.month, today), indent=2), encoding="utf-8")
    for f in sorted(out.iterdir()):
        print(f"{f.name}: {f.stat().st_size:,} bytes sha256 {hashlib.sha256(f.read_bytes()).hexdigest()[:12]}")
    print(f"{len(prog)} programs, {len(chg)} changes since {bdate} ({base[:8]}) -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
