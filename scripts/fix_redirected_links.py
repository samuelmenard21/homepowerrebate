#!/usr/bin/env python3
"""Rewrite internal links that point at URLs _redirects sends elsewhere, so visitors and Googlebot skip the extra hop.
Also swaps the retired /retrofit-assessment/ page for /get-quotes/ (anchor labels included). Safe to re-run; run after any generator that may link to removed pages."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
red = {}
for line in (ROOT / "_redirects").read_text().splitlines():
    p = line.split()
    if len(p) >= 2 and not line.startswith("#") and p[1].startswith("/"):
        red[p[0].rstrip("/") or "/"] = p[1]


def target(path):
    seen = 0
    while path.rstrip("/") in red and seen < 5:
        path = red[path.rstrip("/")]
        seen += 1
    return path


files = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True).stdout.split()
changed = links = 0
for f in files:
    if f.startswith(("_partials/", "calculator/embed/")):
        continue
    p = ROOT / f
    if not p.exists():
        continue
    s = p.read_text(encoding="utf-8", errors="ignore")
    o = s
    s = re.sub(r'(href="/retrofit-assessment/"[^>]*>)(Assessment|Retrofit Assessment)(<)', lambda m: m.group(1).replace("/retrofit-assessment/", "/get-quotes/") + "Get my plan" + m.group(3), s)

    def sub(m):
        global links
        h = m.group(1)
        base, sep, rest = re.match(r"([^?#]*)([?#].*)?$", h).group(1), "", (re.match(r"([^?#]*)([?#].*)?$", h).group(2) or "")
        k = base.rstrip("/") or "/"
        if k in red:
            links += 1
            return f'href="{target(base)}{rest}"'
        return m.group(0)
    s = re.sub(r'href="(/[^"]*)"', sub, s)
    if s != o:
        p.write_text(s, encoding="utf-8")
        changed += 1
print("files changed", changed, "links rewritten", links)
