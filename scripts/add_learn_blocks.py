#!/usr/bin/env python3
"""Put the LEARN blocks on installer ranking pages (2026-10-23): "How to read these results" tips, then a row of three guide and quiz cards
("Not ready to talk to a contractor yet?"), right before the closing "See every rebate" box. Cards come from data/learn/*.json
(learn_kit.pick: articles tagged for the page's service first). Wrapped in LEARN-START/END markers so re-runs replace the block.
Advisor and auditor ranking pages get no block. Styles and the quiz script are in _partials/nav-footer.html (shared CSS/JS).
Usage: python3 scripts/add_learn_blocks.py"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import learn_kit as lk  # noqa: E402

S, E = "<!-- LEARN-START -->", "<!-- LEARN-END -->"
ANCHOR = '<div class="cta"><h3>See every rebate in'
SKIP = {"energy-advisor", "energy-auditor"}
OLD = re.compile(re.escape(S) + r"[\s\S]*?" + re.escape(E) + r"\n?")


def main():
    n = 0
    for f in sorted((ROOT / "installers").glob("*/*/*/index.html")):
        service = f.parent.name
        if service in SKIP:
            continue
        t = f.read_text(encoding="utf-8")
        if ANCHOR not in t:
            continue
        t2 = OLD.sub("", t)
        block = f"{S}\n{lk.tips('installer')}\n{lk.not_ready_row(service)}\n{E}\n"
        i = t2.index(ANCHOR)
        t2 = t2[:i] + block + t2[i:]
        if t2 != t:
            f.write_text(t2, encoding="utf-8")
            n += 1
    print(f"learn blocks: {n} ranking pages updated")


if __name__ == "__main__":
    main()
