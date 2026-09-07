#!/usr/bin/env python3
"""
Visible breadcrumb trail (Home > Region > City > Category) for every region/
city/category page under ca/ and us/.

Found 2026-09-07 auditing internal linking: these ~1,200+ pages (the core
programmatic content, highest SEO value on the site) only carry a JSON-LD
BreadcrumbList — invisible to users and not a crawlable <a> link, so it
does nothing for internal link equity. Only installer profile pages (their
own lightweight ip-breadcrumb) and ~125 other pages had a real, visible,
clickable breadcrumb.

This derives the trail from the same city/region data
apply_canonical_nav_footer.py uses, so it never drifts from the nav/footer
canonicalization. Idempotent — wrapped in CANONICAL-BREADCRUMB markers,
inserted right after the canonical nav block.

Run from the Powerrebate root:
  python3 scripts/apply_breadcrumbs.py --dry-run
  python3 scripts/apply_breadcrumbs.py
"""
import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POWERSCORE_DATA = ROOT / "powerscore-data.json"
EXCLUDE_DIRS = {".git", "node_modules", "scripts", ".claude", "_partials"}

REGION_PREFIX_TO_CODE = {
    ("ca", "bc"): "bc", ("ca", "on"): "on", ("ca", "ab"): "ab", ("ca", "ns"): "ns",
    ("us", "ma"): "ma", ("us", "ny"): "ny", ("us", "ca"): "ca",
    ("us", "pa"): "pa", ("us", "co"): "co", ("us", "vt"): "vt",
}
REGION_KEY_BY_CODE = {
    "bc": "ca/bc", "on": "ca/on", "ab": "ca/ab", "ns": "ca/ns",
    "ma": "us/ma", "ny": "us/ny", "ca": "us/ca",
    "pa": "us/pa", "co": "us/co", "vt": "us/vt",
}
CATEGORY_NAMES = {
    "heat-pump", "insulation", "solar", "battery", "water-heater",
    "smart-thermostats", "ev-charger", "windows-doors", "windows",
}
CATEGORY_LABELS = {
    "heat-pump": "Heat Pump", "insulation": "Insulation", "solar": "Solar",
    "battery": "Battery Storage", "water-heater": "Water Heater",
    "smart-thermostats": "Smart Thermostat", "ev-charger": "EV Charger",
    "windows-doors": "Windows & Doors", "windows": "Windows & Doors",
}


def load_data():
    data = json.loads(POWERSCORE_DATA.read_text())
    region_labels = {}
    city_labels = {}   # code -> {leaf: label}
    city_urls = {}      # code -> {leaf: url}
    for region_key, region in data["regions"].items():
        code = None
        for c, rk in REGION_KEY_BY_CODE.items():
            if rk == region_key:
                code = c
                break
        if not code:
            continue
        region_labels[code] = region["label"]
        city_labels.setdefault(code, {})
        city_urls.setdefault(code, {})
        for slug, city in region["cities"].items():
            leaf = slug.rstrip("/").split("/")[-1]
            city_labels[code][leaf] = city["label"]
            city_urls[code][leaf] = city["url"]
    return region_labels, city_labels, city_urls


REGION_LABELS, CITY_LABELS, CITY_URLS = load_data()

BC_MARKER_START = "<!-- CANONICAL-BREADCRUMB-START -->"
BC_MARKER_END = "<!-- CANONICAL-BREADCRUMB-END -->"
OLD_BC_RE = re.compile(re.escape(BC_MARKER_START) + r".*?" + re.escape(BC_MARKER_END), re.DOTALL)
NAV_MARKER_END = "<!-- CANONICAL-NAV-END -->"
NAV_TAG_END_COMMENT = "<!-- ============================== /NAV ============================== -->"

BREADCRUMB_CSS = """<style>
/* CANONICAL-BREADCRUMB-CSS-START */
.hpr-breadcrumb { max-width: 1180px; margin: 0 auto; padding: 14px 28px; font-size: 13px; color: var(--ink-soft); }
.hpr-breadcrumb ol { list-style: none; display: flex; flex-wrap: wrap; gap: 0; margin: 0; padding: 0; }
.hpr-breadcrumb li { display: flex; align-items: center; }
.hpr-breadcrumb li:not(:last-child)::after { content: '/'; margin: 0 8px; color: var(--rule); }
.hpr-breadcrumb a { color: var(--ink-soft); text-decoration: none; }
.hpr-breadcrumb a:hover { color: var(--teal-deep); text-decoration: underline; }
.hpr-breadcrumb li[aria-current="page"] { color: var(--ink); font-weight: 600; }
@media (max-width: 600px) { .hpr-breadcrumb { padding: 10px 20px; font-size: 12px; } }
/* CANONICAL-BREADCRUMB-CSS-END */
</style>"""
CSS_MARKER_START = "/* CANONICAL-BREADCRUMB-CSS-START */"
CSS_MARKER_END = "/* CANONICAL-BREADCRUMB-CSS-END */"
OLD_CSS_RE = re.compile(
    r"<style>\s*" + re.escape(CSS_MARKER_START) + r".*?" + re.escape(CSS_MARKER_END) + r"\s*</style>",
    re.DOTALL,
)


def get_breadcrumb_context(rel_path: Path):
    parts = rel_path.parts
    if len(parts) < 2 or parts[0] not in ("ca", "us"):
        return None
    code = REGION_PREFIX_TO_CODE.get((parts[0], parts[1]))
    if not code:
        return None
    remainder = list(parts[2:])
    if remainder and remainder[-1] == "index.html":
        remainder = remainder[:-1]
    elif remainder and remainder[-1].endswith(".html"):
        remainder[-1] = remainder[-1][: -len(".html")]

    category = None
    if remainder and remainder[-1] in CATEGORY_NAMES:
        category = remainder[-1]
        remainder = remainder[:-1]

    city_leaf = remainder[-1] if remainder else None
    return code, city_leaf, category


def render_breadcrumb(code, city_leaf, category):
    items = [('<a href="/">Home</a>', False)]
    region_label = REGION_LABELS.get(code, code.upper())
    region_url = "/" + REGION_KEY_BY_CODE[code]
    at_region_page = city_leaf is None
    if at_region_page:
        items.append((html.escape(region_label), True))
    else:
        items.append((f'<a href="{region_url}">{html.escape(region_label)}</a>', False))
        city_label = CITY_LABELS.get(code, {}).get(city_leaf, city_leaf.replace("-", " ").title())
        city_url = CITY_URLS.get(code, {}).get(city_leaf, f"{region_url}/{city_leaf}/")
        if category is None:
            items.append((html.escape(city_label), True))
        else:
            items.append((f'<a href="{city_url}">{html.escape(city_label)}</a>', False))
            cat_label = CATEGORY_LABELS.get(category, category.replace("-", " ").title())
            items.append((html.escape(cat_label), True))

    lis = []
    for text, is_current in items:
        if is_current:
            lis.append(f'<li aria-current="page">{text}</li>')
        else:
            lis.append(f"<li>{text}</li>")
    inner = "".join(lis)
    return (
        f'{BC_MARKER_START}\n'
        f'<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol>{inner}</ol></nav>\n'
        f'{BC_MARKER_END}'
    )


def ensure_css(content: str) -> str:
    if OLD_CSS_RE.search(content):
        content = OLD_CSS_RE.sub(lambda m: BREADCRUMB_CSS, content, count=1)
    else:
        content = content.replace("</head>", BREADCRUMB_CSS + "\n</head>", 1)
    return content


def process_file(path: Path, dry_run: bool):
    rel = path.relative_to(ROOT)
    ctx = get_breadcrumb_context(rel)
    if ctx is None:
        return None
    code, city_leaf, category = ctx
    content = path.read_text(errors="ignore")
    if "<html" not in content.lower():
        return None

    breadcrumb_html = render_breadcrumb(code, city_leaf, category)
    original = content

    if OLD_BC_RE.search(content):
        content = OLD_BC_RE.sub(lambda m: breadcrumb_html, content, count=1)
        action = "restamped"
    elif NAV_MARKER_END in content:
        content = content.replace(NAV_MARKER_END, NAV_MARKER_END + "\n" + breadcrumb_html, 1)
        action = "inserted-after-canonical-nav"
    elif NAV_TAG_END_COMMENT in content:
        content = content.replace(NAV_TAG_END_COMMENT, NAV_TAG_END_COMMENT + "\n" + breadcrumb_html, 1)
        action = "inserted-after-nav-comment"
    else:
        return {"path": str(rel), "action": "skipped-no-nav-anchor", "changed": False}

    content = ensure_css(content)

    if content != original and not dry_run:
        path.write_text(content)

    return {"path": str(rel), "action": action, "changed": content != original}


def find_pages():
    pages = []
    for p in ROOT.rglob("*.html"):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in EXCLUDE_DIRS or any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if rel.parts[0] not in ("ca", "us"):
            continue
        pages.append(p)
    return sorted(pages)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    results = []
    for p in find_pages():
        r = process_file(p, args.dry_run)
        if r:
            results.append(r)

    from collections import Counter
    counts = Counter(r["action"] for r in results)
    print(f"Scanned {len(results)} ca/us pages.")
    for a, c in sorted(counts.items()):
        print(f"  {a}: {c}")
    skipped = [r for r in results if r["action"] == "skipped-no-nav-anchor"]
    if skipped:
        print("Sample skipped (no nav anchor found):")
        for r in skipped[:10]:
            print(f"  {r['path']}")


if __name__ == "__main__":
    main()
