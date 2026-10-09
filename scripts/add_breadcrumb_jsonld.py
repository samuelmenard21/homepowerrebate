#!/usr/bin/env python3
"""BreadcrumbList JSON-LD from each page's visible breadcrumb (nav.hpr-breadcrumb), for pages that lack it.

- Pages that already show a breadcrumb get markup that mirrors the visible trail.
- A few top-level pages have no breadcrumb yet; TRAILS gives them a visible one (same markup as the rest of the site) plus the markup.
Idempotent: markup sits between ADDED-BREADCRUMB-LD-START/END markers, the visible trail between ADDED-BREADCRUMB-START/END (distinct from the markers apply_breadcrumbs.py uses). Pages that already carry any BreadcrumbList are left alone.
Usage: python3 scripts/add_breadcrumb_jsonld.py
"""
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://homepowerrebate.com"
SKIP = ("scripts/", "_partials/", "data/", "drafts/")
LD_S, LD_E = "<!-- ADDED-BREADCRUMB-LD-START -->", "<!-- ADDED-BREADCRUMB-LD-END -->"
VB_S, VB_E = "<!-- ADDED-BREADCRUMB-START -->", "<!-- ADDED-BREADCRUMB-END -->"
# pages with no visible breadcrumb: trail of (label, url); the last item is the page itself
TRAILS = {
    "calculator/index.html": [("Home", "/"), ("Calculators", None)],
    "eguana.html": [("Home", "/"), ("Batteries", "/batteries/"), ("Eguana Evolve", None)],
    "powerscore/index.html": [("Home", "/"), ("PowerScore", None)],
    "programs/index.html": [("Home", "/"), ("Rebate programs", None)],
    "roof-check/index.html": [("Home", "/"), ("Solar roof check", None)],
}
CRUMB_NAV = re.compile(r'<nav class="hpr-breadcrumb"[^>]*>.*?</nav>', re.S)
LEGACY = re.compile(r'<div class="breadcrumb">\s*<a href="/">Home</a>\s*/\s*([^<]+?)\s*</div>', re.S)
BLOCK = lambda a, b: re.compile(re.escape(a) + r".*?" + re.escape(b) + r"\n?", re.S)


def visible_nav(trail):
    items = "".join(f'<li><a href="{u}">{html.escape(t)}</a></li>' if u else f'<li aria-current="page">{html.escape(t)}</li>' for t, u in trail)
    return f'{VB_S}\n<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol>{items}</ol></nav>\n{VB_E}'


def trail_from_nav(nav):
    out = []
    for li in re.findall(r"<li\b[^>]*>(.*?)</li>", nav, re.S):
        a = re.search(r'<a href="([^"]+)"[^>]*>(.*?)</a>', li, re.S)
        out.append((html.unescape(re.sub(r"<[^>]+>", "", a.group(2) if a else li)).strip(), a.group(1) if a else None))
    return out


def ld(trail, canon):
    items = []
    for i, (t, u) in enumerate(trail, 1):
        item = {"@type": "ListItem", "position": i, "name": t}
        url = (BASE + u) if u else canon if i == len(trail) else None
        if url:
            item["item"] = url
        items.append(item)
    return LD_S + '\n<script type="application/ld+json">' + json.dumps(
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}, ensure_ascii=False, separators=(", ", ": ")) + "</script>\n" + LD_E


def process(rel):
    p = ROOT / rel
    s = p.read_text(encoding="utf-8", errors="ignore")
    if re.search(r"<meta[^>]*noindex", s) or "</head>" not in s:
        return False
    canon = re.search(r'rel="canonical" href="([^"]+)"', s)
    if not canon:
        return False
    original = s
    s = BLOCK(LD_S, LD_E).sub("", s)
    if "BreadcrumbList" in s:
        return False
    trail = None
    m = CRUMB_NAV.search(s)
    if m:
        trail = trail_from_nav(m.group(0))
    elif rel in TRAILS:
        trail = TRAILS[rel]
        s = BLOCK(VB_S, VB_E).sub("", s)
        vis = visible_nav(trail)
        # place it between the shared nav and the page content
        main = re.search(r"<main\b", s)
        end = s.find("<!-- CANONICAL-NAV-END -->")
        if main:
            s = s[:main.start()] + vis + "\n" + s[main.start():]
        elif end != -1:
            e = end + len("<!-- CANONICAL-NAV-END -->")
            s = s[:e] + "\n" + vis + s[e:]
        else:
            return False
    else:
        lm = LEGACY.search(s)
        if lm:
            trail = [("Home", "/"), (lm.group(1).strip(), None)]
    if not trail or len(trail) < 2:
        return False
    s = s.replace("</head>", ld(trail, canon.group(1)) + "\n</head>", 1)
    if s != original:
        p.write_text(s, encoding="utf-8")
        return True
    return False


def main():
    files = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "*.html"], text=True).split()
    n = 0
    for f in files:
        if f.startswith(SKIP) or re.match(r"^[A-Z_]+.*\.html$", f) or "template" in f.lower():
            continue
        if process(f):
            n += 1
            print("breadcrumb markup:", f)
    print(f"{n} pages updated")


if __name__ == "__main__":
    main()
