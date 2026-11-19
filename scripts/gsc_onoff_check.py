#!/usr/bin/env python3
"""Is the site "on" or "off" in Google today?

Since 2026-11-02 Search Console impressions flip between about 2,000 a day
("on") and under 150 ("off"). This prints the last N days of impressions and
clicks, marks each day on/off, and lists fixed searches to run by hand,
signed out. Read-only: it only calls `seo gsc-query` (needs the saved
`homepowerrebate` project). Search Console lags 2 to 3 days.

    python3 scripts/gsc_onoff_check.py            # last 14 days
    python3 scripts/gsc_onoff_check.py --days 30
    python3 scripts/gsc_onoff_check.py --write-log   # refresh reports/gsc-daily-onoff-log.md
"""
import argparse, datetime as dt, json, subprocess, sys
from pathlib import Path

ON_AT, OFF_BELOW = 1000, 150          # impressions a day
PROJECT = "homepowerrebate"
LOG = Path(__file__).resolve().parent.parent / "reports" / "gsc-daily-onoff-log.md"

# Run these signed out, in a private window, location Canada. Note the
# position (or "not in the top 50") for each; the exact-title searches
# find our pages only if the page is indexed and trusted.
SEARCHES = [
    "homepowerrebate",
    "Federal Heat Pump Rebate: $10,000 or $2,000 from Early 2027",
    "NS Heating Rebate Status: Check It and See When $400 Pays",
    "Bosch vs Mitsubishi Heat Pump 2026: Which Wins?",
    "NL Oil Rebate 2026: Apply Online for $400 to $1,000",
]


def pull(start, end):
    out = subprocess.run(
        ["seo", "gsc-query", f"--project={PROJECT}", "--refresh", "--dimensions=date",
         f"--start-date={start}", f"--end-date={end}", "--json"],
        capture_output=True, text=True)
    if out.returncode:
        sys.exit(out.stderr or "seo gsc-query failed")
    return [(r["keys"][0], r["clicks"], r["impressions"], r["position"])
            for r in json.loads(out.stdout)["rows"]]


def state(impr):
    return "ON" if impr >= ON_AT else "off" if impr < OFF_BELOW else "mid"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--start")
    ap.add_argument("--write-log", action="store_true")
    a = ap.parse_args()
    today = dt.date.today()
    start = a.start or (today - dt.timedelta(days=a.days)).isoformat()
    rows = pull(start, today.isoformat())
    print(f"{'date':<11}{'impr':>7}{'clicks':>8}{'pos':>7}  state")
    for d, c, i, p in rows:
        print(f"{d:<11}{i:>7}{c:>8}{p:>7.1f}  {state(i)}")
    last5 = rows[-5:]
    on5 = sum(1 for r in last5 if state(r[2]) == "ON")
    print(f"\nON in last {len(last5)} reported days: {on5} (Step 2 gate: 3 of 5)")
    print("Last reported day:", rows[-1][0], "(Search Console lags 2 to 3 days)")
    print("\nSearches to run signed out, by hand:")
    for s in SEARCHES:
        print("  -", s)
    if a.write_log:
        lines = ["# Search Console daily on/off log", "",
                 f"Updated {today}. Source: `python3 scripts/gsc_onoff_check.py --write-log`.",
                 f"ON = {ON_AT}+ impressions a day, off = under {OFF_BELOW}.", "",
                 "| Date | Impressions | Clicks | Avg position | State |", "|---|---:|---:|---:|---|"]
        lines += [f"| {d} | {i} | {c} | {p:.1f} | {state(i)} |" for d, c, i, p in rows]
        lines += ["", f"ON in the last {len(last5)} reported days: {on5}. Step 2 gate: 3 of 5.", "",
                  "## Hand checks (signed out)", ""] + [f"- {s}" for s in SEARCHES]
        LOG.write_text("\n".join(lines) + "\n")
        print("wrote", LOG)


if __name__ == "__main__":
    main()
