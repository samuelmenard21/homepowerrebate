#!/usr/bin/env python3
"""Hand-kept blocks (RELATED-GUIDES, LOCAL-REBATE-BOX) that no generator writes. They live in data/preserved-blocks.json
(page path -> marker-wrapped HTML) and are put back just above </main> after every rebuild, so a generator run cannot drop them.
Usage: python3 scripts/restore_preserved_blocks.py            restore blocks on pages that lack them
       python3 scripts/restore_preserved_blocks.py --capture  read the blocks from the committed pages into the data file"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "preserved-blocks.json"
NAMES = ("RELATED-GUIDES", "LOCAL-REBATE-BOX")
RE = {n: re.compile(rf"<!-- {n}-START -->.*?<!-- {n}-END -->", re.S) for n in NAMES}


def capture():
    out = {}
    files = subprocess.check_output(["git", "ls-files", "*.html"], cwd=ROOT, text=True).split()
    for f in files:
        if f.startswith("_"):
            continue
        s = subprocess.run(["git", "show", f"HEAD:{f}"], cwd=ROOT, capture_output=True, text=True).stdout
        found = [m.group(0) for n in NAMES for m in RE[n].finditer(s) if "<!-- CANONICAL-FOOTER-START" not in m.group(0)]
        if found:
            out[f] = found
    DATA.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"captured {len(out)} pages")


def main():
    if "--capture" in sys.argv:
        return capture()
    data = json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {}
    n = 0
    for f, blocks in data.items():
        p = ROOT / f
        if not p.exists():
            continue
        s = p.read_text(encoding="utf-8")
        new = s
        for b in blocks:
            name = next(x for x in NAMES if b.startswith(f"<!-- {x}-START"))
            if RE[name].search(new):
                new = RE[name].sub(lambda m: b, new, count=1)
            else:
                i = new.rfind("</main>")
                if i == -1:
                    continue
                new = new[:i] + b + "\n" + new[i:]
        if new != s:
            p.write_text(new, encoding="utf-8")
            n += 1
    print(f"restored blocks on {n} pages")


if __name__ == "__main__":
    main()
