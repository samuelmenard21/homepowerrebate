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


def region_city_category_items(code, city_leaf, category):
    """Build the (label, url_or_None) trail for a ca/<region>/... or
    us/<region>/... page — url_or_None is None for the current page."""
    items = []
    region_label = REGION_LABELS.get(code, code.upper())
    region_url = "/" + REGION_KEY_BY_CODE[code]
    if city_leaf is None:
        items.append((region_label, None))
    else:
        items.append((region_label, region_url))
        city_label = CITY_LABELS.get(code, {}).get(city_leaf, city_leaf.replace("-", " ").title())
        city_url = CITY_URLS.get(code, {}).get(city_leaf, f"{region_url}/{city_leaf}/")
        if category is None:
            items.append((city_label, None))
        else:
            items.append((city_label, city_url))
            cat_label = CATEGORY_LABELS.get(category, category.replace("-", " ").title())
            items.append((cat_label, None))
    return items


def render_breadcrumb(items):
    """items: list of (label, url_or_None); url None marks the current page."""
    lis = [f'<li><a href="/">Home</a></li>']
    for label, url in items:
        if url:
            lis.append(f'<li><a href="{url}">{html.escape(label)}</a></li>')
        else:
            lis.append(f'<li aria-current="page">{html.escape(label)}</li>')
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


# Top-level sections that get a simple "Home > Section" (or deeper) trail.
# label=None means: derive it from the page's own <h1> (falling back to a
# title-cased slug) — used for individual posts/guides/questions.
SECTION_LABELS = {
    "blog": "Blog",
    "guides": "Guides",
    "installers": "Find an Installer",
    "questions": "Rebate Questions",
    "partners": "Partners",
    "contact": "Contact",
    "about": "About",
    "privacy": "Privacy Policy",
    "terms": "Terms",
    "calculator": "Heat Pump Savings Calculator",
    "share-your-cost": "Share Your Cost",
    "retrofit-assessment": "Retrofit Assessment",
    "powerscore": "PowerScore",
    "stacking-calculator": "Rebate Stacking Calculator",
}

H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL | re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")


def derive_title(content: str, slug: str) -> str:
    m = H1_RE.search(content)
    if m:
        text = TAG_RE.sub("", m.group(1))
        text = re.sub(r"\s+", " ", text).strip()
        if text and len(text) <= 70:
            return text
    return slug.replace("-", " ").title()


def get_other_section_items(rel_path: Path, content: str):
    """Breadcrumb items for everything outside ca/us: blog, guides,
    installers, questions, powerscore, stacking-calculator, static pages."""
    parts = list(rel_path.parts)
    if parts and parts[-1] == "index.html":
        parts = parts[:-1]
    elif parts and parts[-1].endswith(".html"):
        parts[-1] = parts[-1][: -len(".html")]
    if not parts:
        return None

    top = parts[0]
    if top not in SECTION_LABELS:
        return None
    if top == "installers" and len(parts) >= 2 and parts[1] == "profiles":
        return None  # already has its own ip-breadcrumb

    section_label = SECTION_LABELS[top]

    # stacking-calculator/<ca|us>/<region>/[<city>/] — reuse the region/city
    # trail, prefixed with the calculator section.
    if top == "stacking-calculator" and len(parts) >= 3 and parts[1] in ("ca", "us"):
        code = REGION_PREFIX_TO_CODE.get((parts[1], parts[2]))
        if code:
            # no region-level index page exists under stacking-calculator/,
            # only /stacking-calculator/<region>/<city>/ — so the region
            # itself isn't a clickable crumb, just Section > City.
            calc_url = "/stacking-calculator/"
            items = [(section_label, calc_url)]
            city_leaf = parts[3] if len(parts) >= 4 else None
            region_label = REGION_LABELS.get(code, code.upper())
            if city_leaf is None:
                items.append((region_label, None))
            else:
                city_label = CITY_LABELS.get(code, {}).get(city_leaf, city_leaf.replace("-", " ").title())
                items.append((f"{region_label} — {city_label}", None))
            return items

    if len(parts) == 1:
        # the section's own index page (blog/, guides/, powerscore/, ...)
        return [(section_label, None)]

    # a leaf page one level under a section (blog/<slug>, guides/<slug>,
    # questions/<slug>) — Home > Section > <derived title>
    leaf_slug = parts[-1]
    section_url = "/" + top + "/" if top != "installers" else "/installers"
    title = derive_title(content, leaf_slug)
    return [(section_label, section_url), (title, None)]


def process_file(path: Path, dry_run: bool):
    rel = path.relative_to(ROOT)
    content = path.read_text(errors="ignore")
    if "<html" not in content.lower():
        return None

    ctx = get_breadcrumb_context(rel)
    if ctx is not None:
        code, city_leaf, category = ctx
        items = region_city_category_items(code, city_leaf, category)
    else:
        items = get_other_section_items(rel, content)
        if items is None:
            return None

    breadcrumb_html = render_breadcrumb(items)
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


TARGET_TOP_DIRS = {"ca", "us"} | set(SECTION_LABELS)


def find_pages():
    pages = []
    for p in ROOT.rglob("*.html"):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in EXCLUDE_DIRS or any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if len(rel.parts) == 1:
            # root-level flat files like about.html, privacy.html, terms.html
            if rel.stem in SECTION_LABELS:
                pages.append(p)
            continue
        if rel.parts[0] not in TARGET_TOP_DIRS:
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
