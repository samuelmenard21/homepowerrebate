#!/usr/bin/env python3
"""Add BreadcrumbList JSON-LD to indexable pages that have none (Oct 2026 SEO check found 85, mostly top-level guides and old us/ca hubs).

Levels come from the URL path; each level is named by that page's own H1 (or a title-cased slug when the folder has no page).
Marker-wrapped in <head>, so re-runs replace rather than duplicate. Pages a generator already gives a BreadcrumbList are left alone.
Run after the generators, before the link steps.
Usage: python3 scripts/add_breadcrumb_ld.py [--dry-run]"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://homepowerrebate.com"
S, E = "<!-- BREADCRUMB-LD-START -->", "<!-- BREADCRUMB-LD-END -->"
NAMES = {"blog": "Blog", "questions": "Questions", "us": "United States", "ca": "Canada", "installers": "Installers", "programs": "Rebate programs", "contact": "Contact", "powerscore": "PowerScore", "get-quotes": "Get quotes"}
SKIP = ("dist/", "worktrees/", ".", "_partials/", "calculator/embed/", "scripts/", "data/", "node_modules/")


def name_of(rel_dir):
    if rel_dir in NAMES:
        return NAMES[rel_dir]
    f = ROOT / rel_dir / "index.html"
    if f.exists():
        h = f.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
        if m:
            t = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
            t = re.split(r"\s*[:(|]\s*", t)[0].strip()
            if 3 <= len(t) <= 70:
                return t
    return rel_dir.rstrip("/").split("/")[-1].replace("-", " ").title()


def main():
    dry = "--dry-run" in sys.argv
    n = 0
    for f in sorted(ROOT.glob("**/index.html")):
        rel = str(f.relative_to(ROOT))
        if rel == "index.html" or rel.startswith(SKIP) or "node_modules/" in rel:
            continue
        h = f.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"<meta[^>]+robots[^>]+noindex", h, re.I) or "http-equiv=\"refresh\"" in h:
            continue
        body = h.replace(h[h.find(S):h.find(E) + len(E)], "") if S in h else h
        if "BreadcrumbList" in body:
            continue
        parts = rel.split("/")[:-1]
        items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"}]
        for i in range(1, len(parts) + 1):
            d = "/".join(parts[:i])
            items.append({"@type": "ListItem", "position": i + 1, "name": name_of(d), "item": f"{BASE}/{d}/"})
        blk = S + '<script type="application/ld+json">' + json.dumps(
            {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}, ensure_ascii=False) + "</script>" + E
        new = re.sub(re.escape(S) + ".*?" + re.escape(E), lambda m: blk, h, flags=re.S) if S in h else h.replace("</head>", blk + "\n</head>", 1)
        if new != h:
            n += 1
            if dry:
                print(rel, [x["name"] for x in items])
            else:
                f.write_text(new, encoding="utf-8")
    print(f"{n} pages {'would get' if dry else 'got'} a BreadcrumbList")


if __name__ == "__main__":
    main()
