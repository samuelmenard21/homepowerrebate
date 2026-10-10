#!/usr/bin/env python3
"""Fix skipped heading levels (h2 followed directly by h4) without changing how anything looks.

Walks each page's headings in order; when a heading jumps more than one level deeper than the one before it, it gets
aria-level = previous level + 1, so assistive technology reads a clean outline (Lighthouse/axe 'heading-order').
Idempotent: existing aria-level values are honoured. Usage: python3 scripts/fix_heading_order.py
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = ("scripts/", "_partials/", "data/", "drafts/")
HEAD = re.compile(r"<h([1-6])\b([^>]*)>", re.I)
MASK = re.compile(r"<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->", re.S | re.I)


def fix(html):
    # blank out script/style/comments (same length) so only real headings are matched
    masked = MASK.sub(lambda m: " " * len(m.group(0)), html)
    out, last, prev, n = [], 0, 0, 0
    for m in HEAD.finditer(masked):
        level, attrs = int(m.group(1)), m.group(2)
        am = re.search(r'aria-level="(\d)"', attrs)
        eff = int(am.group(1)) if am else level
        if prev and eff > prev + 1 and not am:
            eff = prev + 1
            tag = html[m.start():m.end()]
            out.append(html[last:m.start()] + tag[:-1] + f' aria-level="{eff}">')
            last = m.end()
            n += 1
        prev = eff
    out.append(html[last:])
    return "".join(out), n


def main():
    files = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "*.html"], text=True).split()
    pages = headings = 0
    for f in files:
        if f.startswith(SKIP):
            continue
        p = ROOT / f
        s = p.read_text(encoding="utf-8", errors="ignore")
        t, n = fix(s)
        if n:
            p.write_text(t, encoding="utf-8")
            pages += 1
            headings += n
    print(f"{headings} headings fixed on {pages} pages")


if __name__ == "__main__":
    main()
