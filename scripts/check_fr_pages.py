#!/usr/bin/env python3
"""Fails when a dollar figure on a French card is not in the fact the card names (data/verified-facts/*.json).

The French pages (data/fr/*.json, built by build_fr_pages.py) hold prose, never a second copy of the data: each card points at a fact id,
and status, date and source come from the fact. This check compares the numbers, so changing an amount in a facts file flags every
French card that still shows the old figure. French writes 6 700 $ and 0,40 $; the facts write $6,700 and $0.40; both are read as 6700 and 0.40.
Usage: python3 scripts/check_fr_pages.py"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_fr_pages  # noqa: E402


def facts():
    out = {}
    for f in (ROOT / "data/verified-facts").glob("*.json"):
        for x in json.loads(f.read_text())["facts"]:
            out[x["id"]] = x
    return out


def fr_numbers(s):
    s = s.replace(" ", " ")
    nums = set()
    for m in re.finditer(r"(\d{1,3}(?: \d{3})*(?:,\d{1,3})?)\s*\$", s):
        nums.add(m.group(1).replace(" ", "").replace(",", "."))
    return nums


def en_numbers(x):
    t = " ".join(str(x.get(k, "")) for k in ("claim", "amount", "eligibility", "notes", "dates"))
    nums = set()
    for m in re.finditer(r"\$(\d{1,3}(?:,\d{3})*(?:\.\d+)?)", t):
        nums.add(m.group(1).replace(",", ""))
    for m in re.finditer(r"(?<![\d$.,])(\d{1,3}(?:,\d{3})+|\d+)(?![\d,])", t):  # per-kW and per-BTU style figures without a dollar sign nearby
        nums.add(m.group(1).replace(",", ""))
    return {n.rstrip("0").rstrip(".") if "." in n else n for n in nums} | nums


def norm(n):
    return n.rstrip("0").rstrip(".") if "." in n else n


def main():
    F, bad, cards = facts(), [], 0
    for src in build_fr_pages.sources():
        d = json.loads(src.read_text())
        for c in d["cards"]:
            for fid in c["facts"]:
                if fid not in F:
                    bad.append(f'{d["path"]}: unknown fact {fid}')
                    continue
            cards += 1
            have = set()
            for fid in c["facts"]:
                have |= {norm(n) for n in en_numbers(F[fid])}
            for n in fr_numbers(c["amount"]):
                if norm(n) not in have:
                    bad.append(f'{d["path"]}: card "{c["title"]}" shows {n} $ which is not in {", ".join(c["facts"])}')
    print("\n".join(bad) or f"OK: {cards} French cards match their facts")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
