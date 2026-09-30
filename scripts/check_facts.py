#!/usr/bin/env python3
"""Lint data/verified-facts/*.json. Every fact needs an id, a status, a verified_on date and a source.

Statuses: active, upcoming, waitlist, paused, closed, check (could not confirm), info (a note, not a program).
A fact with status active/upcoming/waitlist/paused must have an https source_url. Exits 1 on any problem.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUSES = {"active", "upcoming", "waitlist", "paused", "closed", "check", "info"}
bad = []
ids = set()
for f in sorted((ROOT / "data" / "verified-facts").glob("*.json")):
    d = json.loads(f.read_text())
    for x in d["facts"]:
        tag = f"{f.name}: {x.get('program', '?')[:50]}"
        if x.get("status") not in STATUSES:
            bad.append(f"{tag}: bad or missing status {x.get('status')!r}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", x.get("verified_on", "")):
            bad.append(f"{tag}: bad or missing verified_on")
        if x.get("id") in ids or not x.get("id"):
            bad.append(f"{tag}: duplicate or missing id")
        ids.add(x.get("id"))
        if x.get("status") in {"active", "upcoming", "waitlist", "paused"} and not str(x.get("source_url", "")).startswith("https://"):
            bad.append(f"{tag}: {x['status']} fact has no https source_url")
print("\n".join(bad) or f"OK: {len(ids)} facts")
sys.exit(1 if bad else 0)
