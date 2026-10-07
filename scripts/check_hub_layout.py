#!/usr/bin/env python3
"""Every region hub must have the same blocks in the same order. Exits 1 if any hub drifts.
Order: hero, stats strip, short answer + open programs table, what changed, program links, city finder + biggest rebates + explore,
on-this-page contents, then legacy sections (long ones folded). Required data per hub: data/hub-tops/<code>.json and
data/verified-facts/<code>.json. New region checklist: see 'Adding a region' in CLAUDE.md.
  python3 scripts/check_hub_layout.py"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUBS = ["ca/bc", "ca/on", "ca/ab", "ca/ns", "us/ma", "us/ny", "us/ca", "us/pa", "us/co", "us/vt", "us/mi"]
ORDER = ["HUB-STATS", "HUB-TOP", "HUB-CHANGES", "HUB-SHOWCASE", "HUB-TOC"]


def main():
    bad = 0
    for h in HUBS:
        t = (ROOT / h / "index.html").read_text(encoding="utf-8")
        pos = [t.find(f"<!-- {m}-START -->") for m in ORDER]
        problems = [f"missing {m}" for m, p in zip(ORDER, pos) if p < 0]
        found = [p for p in pos if p >= 0]
        if found != sorted(found):
            problems.append("blocks out of order")
        for m in ORDER:
            if t.count(f"<!-- {m}-START -->") > 1:
                problems.append(f"duplicate {m}")
        code = h.split("/")[1]
        facts = {"bc": "bc-pages", "ca": "us-ca"}.get(code, code)
        for d in ("hub-tops", "verified-facts"):
            name = facts if d == "verified-facts" else code
            if not (ROOT / "data" / d / f"{name}.json").exists() and not (d == "hub-tops" and code in ("bc", "on", "ca")):
                problems.append(f"no data/{d}/{name}.json")
        if len(re.findall(r"<h1\b", t)) != 1:
            problems.append("h1 count is not 1")
        print(("OK   " if not problems else "FAIL ") + h + ("  " + "; ".join(problems) if problems else ""))
        bad += bool(problems)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
