#!/usr/bin/env python3
"""Fail if an internal link points at a page that does not exist or at a URL _redirects sends elsewhere.
Run after any generator, before committing. Fix redirected links with scripts/fix_redirected_links.py."""
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
red = set()
for line in (ROOT / "_redirects").read_text().splitlines():
    p = line.split()
    if len(p) >= 2 and not line.startswith("#"):
        red.add(p[0].rstrip("/") or "/")
tracked = set(subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split())


def exists(path):
    p = path.strip("/")
    if not p:
        return True
    return f"{p}/index.html" in tracked or p in tracked or f"{p}.html" in tracked or (ROOT / p / "index.html").exists() or (ROOT / f"{p}.html").exists()


missing, redirected = Counter(), Counter()
src = {}
for f in subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True).stdout.split():
    if f.startswith(("_partials/", "calculator/embed/", "ONTARIO_", "city-page-template", "scripts/", "CITY_PAGE_TEMPLATE")) or not (ROOT / f).exists():
        continue
    for h in set(re.findall(r'href="(/[^"#?]*)"', (ROOT / f).read_text(errors="ignore"))):
        k = h.rstrip("/") or "/"
        if k in red:
            redirected[h] += 1
            src.setdefault(h, f)
        elif not exists(h) and not re.search(r"\.(css|js|json|xml|txt|svg|png|jpg|webp|pdf|ico)$", h) and not h.startswith(("/cdn-cgi", "//")):
            missing[h] += 1
            src.setdefault(h, f)
for name, c in (("redirected", redirected), ("missing", missing)):
    print(f"{name}: {sum(c.values())} links, {len(c)} distinct")
    for h, n in c.most_common(8):
        print(f"  {n:4} {h}   e.g. {src[h]}")
sys.exit(1 if redirected or missing else 0)
