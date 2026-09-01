#!/usr/bin/env python3
"""
Regenerate sitemap.xml from the actual pages on disk — found 2026-09-01 that
the existing sitemap.xml is a static, one-time snapshot from 2026-08-23 that
was never regenerated as the site grew: it had 1,332 URLs while the site
actually has 2,207+ pages (only 322 of 896 installer profiles, 744 of 968
rebate pages, and 82 of 127 blog posts were listed — zero of today's new
content was included at all). A sitemap this incomplete meaningfully slows
discovery/indexing for whatever's missing from it.

Walks the real file tree instead of hand-maintaining a URL list, so it can
be safely re-run after any batch of new pages (a new region, a new blog
post, a new installer scrape) without drifting out of date again.

Priority/changefreq tiers (kept consistent with the existing sitemap's own
scheme, extended to cover categories it was missing):
  1.0  homepage
  0.8  province/state hubs, powerscore hub
  0.7  city hub pages (ca/*/​<city>/index.html, us/*/​<city>/index.html)
  0.65 city/category rebate pages (heat-pump, solar, water-heater, etc.)
  0.6  blog posts, stacking-calculator pages
  0.55 installer profiles
  0.5  powerscore compare pages, questions pages
  0.4  static pages (about, privacy, terms, contact, etc.)

Run from the Powerrebate root:
  python3 scripts/generate_sitemap.py --dry-run   # report counts only
  python3 scripts/generate_sitemap.py             # write sitemap.xml
"""
import argparse
import datetime
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://homepowerrebate.com"
TODAY = datetime.date.today().isoformat()

EXCLUDE_DIRS = {".git", "node_modules", "scripts", ".claude", "installers/photos"}


def url_for(path):
    rel = os.path.relpath(path, ROOT)
    if rel == "index.html":
        return "/"
    rel = rel[: -len("index.html")] if rel.endswith("index.html") else rel
    if not rel.startswith("/"):
        rel = "/" + rel
    return rel


def classify(rel_path):
    """Return (priority, changefreq) for a given site-relative URL path."""
    p = rel_path

    if p == "/":
        return "1.0", "weekly"
    if p.startswith("/powerscore/compare/"):
        return "0.5", "monthly"
    if p == "/powerscore/" or p.startswith("/powerscore/") and p.count("/") <= 2:
        return "0.8", "weekly"
    if p.startswith("/questions/"):
        return "0.5", "monthly"
    if p.startswith("/blog/"):
        return "0.6", "monthly"
    if p.startswith("/installers/profiles/"):
        return "0.55", "monthly"
    if p.startswith("/installers/"):
        return "0.6", "weekly"
    if p.startswith("/stacking-calculator/"):
        return "0.6", "monthly"

    # ca/<region>/index.html or us/<state>/index.html = province/state hub
    parts = [x for x in p.split("/") if x]
    if parts and parts[0] in ("ca", "us"):
        if len(parts) == 1:
            return "0.8", "weekly"  # /ca/ or /us/ index
        if len(parts) == 2:
            return "0.8", "weekly"  # region hub, e.g. /ca/bc/
        if len(parts) == 3:
            return "0.7", "weekly"  # city hub, e.g. /ca/bc/vancouver/
            # NY has an extra utility segment: /us/ny/<utility>/<city>/
        if len(parts) == 4 and parts[0] == "us" and parts[1] == "ny":
            return "0.7", "weekly"
        return "0.65", "weekly"  # category page, e.g. /ca/bc/vancouver/heat-pump/

    return "0.4", "monthly"


def find_pages():
    pages = []
    for root, dirs, files in os.walk(ROOT):
        rel_root = os.path.relpath(root, ROOT)
        top = rel_root.split(os.sep)[0]
        if top in EXCLUDE_DIRS or rel_root.startswith(".claude"):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        if "index.html" in files:
            pages.append(os.path.join(root, "index.html"))
        for f in files:
            if f.endswith(".html") and f != "index.html":
                pages.append(os.path.join(root, f))
    return sorted(set(pages))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pages = find_pages()
    entries = []
    by_tier = {}
    for page_path in pages:
        rel_url = url_for(page_path)
        # skip legal/utility pages Google shouldn't waste crawl budget on
        if rel_url in ("/robots.txt",):
            continue
        priority, changefreq = classify(rel_url)
        entries.append((rel_url, priority, changefreq))
        by_tier[priority] = by_tier.get(priority, 0) + 1

    entries.sort(key=lambda e: e[0])

    print(f"Found {len(entries)} pages to include (was 1,332 in the stale sitemap).")
    for tier, count in sorted(by_tier.items(), key=lambda x: -float(x[0])):
        print(f"  priority {tier}: {count} pages")

    if args.dry_run:
        return

    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for rel_url, priority, changefreq in entries:
        loc = BASE_URL + rel_url
        lines.append(
            f'  <url><loc>{loc}</loc><lastmod>{TODAY}</lastmod>'
            f'<changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>'
        )
    lines.append("</urlset>")

    out_path = os.path.join(ROOT, "sitemap.xml")
    open(out_path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"\nWrote {out_path} with {len(entries)} URLs.")


if __name__ == "__main__":
    main()
