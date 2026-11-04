#!/usr/bin/env python3
"""Ratchet on one-off stylesheet combinations (2026-11-04).

Templated pages must share a stylesheet set. A page counts as one-off when it links a stylesheet set used by fewer than
MIN_PAGES pages, or links any stylesheet in the body (hand-assembled pages). The count may only go down: the baseline is
_partials/stylesheet-combos-baseline.json (total, and per top-level folder). New pages that land on their own variant fail the check.

  python3 scripts/check_stylesheet_combos.py            check against the baseline
  python3 scripts/check_stylesheet_combos.py --list     list one-off pages by folder
  python3 scripts/check_stylesheet_combos.py --update-baseline   after fixing pages, lower the baseline
"""
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "_partials" / "stylesheet-combos-baseline.json"
MIN_PAGES = 10
LINK = re.compile(r'<link rel="stylesheet" href="(/assets/[^"?]+)')
SKIP = ("scripts/", "_partials/", "node_modules/", "embed/")


def pages():
    files = subprocess.check_output(["git", "ls-files", "*.html"], cwd=ROOT, text=True).split()
    for f in files:
        if f.startswith(SKIP) or "/embed/" in f or "/embed" == f[:6]:
            continue
        h = (ROOT / f).read_text(encoding="utf-8", errors="ignore")
        if "<html" in h and "</head>" in h and "<!DOCTYPE" in h[:200].upper() or "<html" in h:
            yield f, h


def scan():
    combos = collections.defaultdict(list)
    bodylinked = set()
    for f, h in pages():
        if "</head>" not in h:
            continue
        links = tuple(LINK.findall(h))
        if not links:
            continue
        combos[links].append(f)
        if LINK.search(h.split("</head>", 1)[1]):
            bodylinked.add(f)
    one_off = {}
    for links, fs in combos.items():
        for f in fs:
            if len(fs) < MIN_PAGES or f in bodylinked:
                one_off[f] = links
    return one_off


def folder(f):
    p = f.split("/")
    return "/".join(p[:2]) if p[0] in ("ca", "us") and len(p) > 2 else p[0]


def main():
    one = scan()
    by = collections.Counter(folder(f) for f in one)
    if "--list" in sys.argv:
        for k, v in by.most_common():
            print(f"{v:4d}  {k}")
        print(f"{len(one)} one-off pages")
        return 0
    if "--update-baseline" in sys.argv:
        BASE.write_text(json.dumps({"total": len(one), "folders": dict(by)}, indent=1, sort_keys=True) + "\n")
        print("baseline", len(one))
        return 0
    base = json.loads(BASE.read_text()) if BASE.exists() else {"total": 0, "folders": {}}
    bad = [(k, v, base["folders"].get(k, 0)) for k, v in by.items() if v > base["folders"].get(k, 0)]
    for k, v, b in bad:
        print(f"FAIL {k}: {v} one-off pages (baseline {b}); put new pages on the shared article/hub/ranking template")
        for f in sorted(f for f in one if folder(f) == k)[:5]:
            print("   ", f, [x.split("/")[-1] for x in one[f]])
    print(f"{len(one)} one-off pages (baseline {base['total']})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
