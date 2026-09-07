#!/usr/bin/env python3
"""
Single source of truth for nav + footer across the entire site.

Problem this fixes: the nav dropdown and footer were hand-copy-pasted onto
each page over many build sessions. At least 4 structurally different nav
variants existed (canonical province-tab picker, homepage's country->region
drill-down, blog's flat BC-only grid, and ~1,049 installer profile pages
with no nav/footer at all), and even the "canonical" partial itself was
missing Pennsylvania/Colorado/Vermont. Adding a new state meant hand-editing
HTML across hundreds of files and reliably missing some of them.

This script makes _partials/nav-footer.html the actual source of truth: it
parses that file's NAV/FOOTER/SHARED CSS/SHARED JS blocks, renders them per
page (substituting the current city/province context), and re-stamps every
page's nav + footer from it. Re-run any time the partial or the city data
changes (e.g. after adding a new state/province) to propagate everywhere.

Run from the Powerrebate root:
  python3 scripts/apply_canonical_nav_footer.py --dry-run   # report only
  python3 scripts/apply_canonical_nav_footer.py             # write changes
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTIAL = ROOT / "_partials" / "nav-footer.html"
POWERSCORE_DATA = ROOT / "powerscore-data.json"

EXCLUDE_DIRS = {".git", "node_modules", "scripts", ".claude", "_partials"}
EXCLUDE_FILES = {
    "404.html", "og-image.html", "nav-footer.html",
    "CITY_PAGE_TEMPLATE_OPTIMIZED.html", "ONTARIO_CITY_PAGE_TEMPLATE.html",
    "city-page-template-with-carousel.html", "installer-carousel-component.html",
    "installer-carousel.html", "solar-carousel.html", "unified-carousel.html",
    "pinterest-pin-templates.html", "preview.html",
}

PROV_CODES = {"on", "bc", "ab", "ns", "ma", "ca", "ny", "pa", "co", "vt"}
# ca/<x> or us/<x> path prefix -> province-tab code
REGION_PREFIX_TO_CODE = {
    ("ca", "bc"): "bc", ("ca", "on"): "on", ("ca", "ab"): "ab", ("ca", "ns"): "ns",
    ("us", "ma"): "ma", ("us", "ny"): "ny", ("us", "ca"): "ca",
    ("us", "pa"): "pa", ("us", "co"): "co", ("us", "vt"): "vt",
}
CATEGORY_NAMES = {
    "heat-pump", "insulation", "solar", "battery", "water-heater",
    "smart-thermostats", "ev-charger", "windows-doors", "windows",
}


def load_city_labels():
    """prov_code -> {leaf_city_slug: Label} built from powerscore-data.json,
    which already enumerates every real city page with a clean label."""
    data = json.loads(POWERSCORE_DATA.read_text())
    out = {}
    region_key_to_code = {
        "ca/bc": "bc", "ca/on": "on", "ca/ab": "ab", "ca/ns": "ns",
        "us/ma": "ma", "us/ny": "ny", "us/ca": "ca",
        "us/pa": "pa", "us/co": "co", "us/vt": "vt",
    }
    for region_key, region in data["regions"].items():
        code = region_key_to_code.get(region_key)
        if not code:
            continue
        out.setdefault(code, {})
        for slug, city in region["cities"].items():
            leaf = slug.rstrip("/").split("/")[-1]
            out[code][leaf] = city["label"]
    return out


CITY_LABELS = load_city_labels()

BREADCRUMB_HREF_RE = re.compile(r'href="(/(?:ca|us)/[a-z0-9\-]+(?:/[a-z0-9\-]+)*)/?"')


def get_context(rel_path: Path, content: str):
    """Return (province_code, city_slug, city_label, page_path)."""
    parts = rel_path.parts
    page_path = "/" + str(rel_path.parent).replace("\\", "/")
    if rel_path.name != "index.html":
        page_path = "/" + str(rel_path.with_suffix("")).replace("\\", "/")
    if page_path == "/.":
        page_path = "/"
    if not page_path.endswith("/") and page_path != "/":
        page_path += "/"

    # installers/profiles/<city-or-region>/... — no province in the path
    # itself; pull it from the page's own breadcrumb link to the city hub.
    if len(parts) >= 2 and parts[0] == "installers" and parts[1] == "profiles":
        for m in BREADCRUMB_HREF_RE.finditer(content):
            href_parts = [p for p in m.group(1).split("/") if p]
            if len(href_parts) >= 2 and href_parts[0] in ("ca", "us"):
                code = REGION_PREFIX_TO_CODE.get((href_parts[0], href_parts[1]))
                if code:
                    leaf = href_parts[-1]
                    label = CITY_LABELS.get(code, {}).get(leaf, leaf.replace("-", " ").title())
                    return code, leaf, label, page_path
        return "on", "", "", page_path

    # ca/<prov>/... or us/<state>/...
    if len(parts) >= 2 and parts[0] in ("ca", "us"):
        code = REGION_PREFIX_TO_CODE.get((parts[0], parts[1]))
        if code:
            remainder = list(parts[2:])
            if remainder and remainder[-1] == "index.html":
                remainder = remainder[:-1]
            elif remainder and remainder[-1].endswith(".html"):
                remainder[-1] = remainder[-1][: -len(".html")]
            while remainder and remainder[-1] in CATEGORY_NAMES:
                remainder = remainder[:-1]
            if remainder:
                leaf = remainder[-1]
                label = CITY_LABELS.get(code, {}).get(leaf, leaf.replace("-", " ").title())
                return code, leaf, label, page_path
            return code, "", "", page_path

    return "on", "", "", page_path


def parse_partial():
    text = PARTIAL.read_text()

    def block(start_marker, end_marker):
        s = text.index(start_marker) + len(start_marker)
        e = text.index(end_marker, s)
        return text[s:e].strip("\n")

    nav = block("<!-- ============================== NAV ============================== -->",
                "<!-- ============================ /NAV ")
    footer = block("<!-- ============================ FOOTER ============================= -->",
                   "<!-- =========================== /FOOTER ")
    css = block("<!-- ============================ SHARED CSS ========================== -->",
                "<!-- =========================== /SHARED CSS ")
    js = block("<!-- ============================ SHARED JS =========================== -->",
               "<!-- =========================== /SHARED JS ")
    # strip the leading html-comment instruction line inside css/js blocks
    css = re.sub(r"^<!-- Add to every page.*?-->\n", "", css)
    # the extracted blocks include their own <style>/<script> wrapper tags —
    # strip those since ensure_shared_assets() adds its own wrapper.
    css = re.sub(r"^\s*<style>\s*\n?", "", css.strip())
    css = re.sub(r"\n?\s*</style>\s*$", "", css)
    js = re.sub(r"^\s*<script>\s*\n?", "", js.strip())
    js = re.sub(r"\n?\s*</script>\s*$", "", js)
    return nav.strip(), footer.strip(), css.strip(), js.strip()


NAV_RAW, FOOTER_RAW, CSS_RAW, JS_RAW = parse_partial()

NAV_MARKER_START = "<!-- CANONICAL-NAV-START -->"
NAV_MARKER_END = "<!-- CANONICAL-NAV-END -->"
FOOTER_MARKER_START = "<!-- CANONICAL-FOOTER-START -->"
FOOTER_MARKER_END = "<!-- CANONICAL-FOOTER-END -->"
CSS_MARKER_START = "/* CANONICAL-NAV-FOOTER-CSS-START */"
CSS_MARKER_END = "/* CANONICAL-NAV-FOOTER-CSS-END */"
JS_MARKER_START = "/* CANONICAL-NAV-FOOTER-JS-START */"
JS_MARKER_END = "/* CANONICAL-NAV-FOOTER-JS-END */"


def render_nav(prov, city_slug):
    html = NAV_RAW
    html = html.replace("{{CURRENT_CITY_SLUG}}", city_slug)
    html = html.replace("{{CURRENT_PROVINCE}}", prov)
    # highlight the current province's tab instead of the template default ("on")
    if prov and prov != "on":
        html = html.replace(
            f'id="province-tab-on" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:var(--teal-deep); color:#fff;',
            f'id="province-tab-on" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink);',
        )
        html = html.replace(
            f'id="province-tab-{prov}" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink);',
            f'id="province-tab-{prov}" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:var(--teal-deep); color:#fff;',
        )
        html = html.replace(
            'id="province-cities-on" style="display:grid; gap:8px;">',
            'id="province-cities-on" style="display:none; gap:8px;">',
        )
        html = html.replace(
            f'id="province-cities-{prov}" style="display:none; gap:8px;">',
            f'id="province-cities-{prov}" style="display:grid; gap:8px;">',
        )
    return f"{NAV_MARKER_START}\n{html}\n{NAV_MARKER_END}"


def render_footer(prov, city_slug, city_label, page_path):
    html = FOOTER_RAW
    html = html.replace("{{CURRENT_CITY_SLUG}}", city_slug)
    html = html.replace("{{CURRENT_CITY_LABEL}}", city_label)
    html = html.replace("{{PAGE_PATH}}", page_path)
    return f"{FOOTER_MARKER_START}\n{html}\n{FOOTER_MARKER_END}"


NAV_TAG_RE = re.compile(r"<nav\b[^>]*>.*?</nav>", re.DOTALL | re.IGNORECASE)
FOOTER_TAG_RE = re.compile(r"<footer\b[^>]*>.*?</footer>", re.DOTALL | re.IGNORECASE)
NEWSLETTER_SECTION_RE = re.compile(
    r'<section[^>]*>\s*<div class="wrap"[^>]*>\s*<div[^>]*>From Sam</div>.*?</section>',
    re.DOTALL,
)
OLD_CANONICAL_NAV_RE = re.compile(
    re.escape(NAV_MARKER_START) + r".*?" + re.escape(NAV_MARKER_END), re.DOTALL
)
OLD_CANONICAL_FOOTER_RE = re.compile(
    re.escape(FOOTER_MARKER_START) + r".*?" + re.escape(FOOTER_MARKER_END), re.DOTALL
)


OLD_CSS_BLOCK_RE = re.compile(
    r"<style>\s*" + re.escape(CSS_MARKER_START) + r".*?" + re.escape(CSS_MARKER_END) + r"\s*</style>",
    re.DOTALL,
)
OLD_JS_BLOCK_RE = re.compile(
    r"<script>\s*" + re.escape(JS_MARKER_START) + r".*?" + re.escape(JS_MARKER_END) + r"\s*</script>",
    re.DOTALL,
)


def ensure_shared_assets(content: str) -> str:
    css_block = f"<style>\n{CSS_MARKER_START}\n{CSS_RAW}\n{CSS_MARKER_END}\n</style>"
    js_block = f"<script>\n{JS_MARKER_START}\n{JS_RAW}\n{JS_MARKER_END}\n</script>"
    if OLD_CSS_BLOCK_RE.search(content):
        content = OLD_CSS_BLOCK_RE.sub(lambda m: css_block, content, count=1)
    else:
        content = content.replace("</head>", css_block + "\n</head>", 1)
    if OLD_JS_BLOCK_RE.search(content):
        content = OLD_JS_BLOCK_RE.sub(lambda m: js_block, content, count=1)
    else:
        content = content.replace("</body>", js_block + "\n</body>", 1)
    return content


def process_file(path: Path, dry_run: bool):
    rel = path.relative_to(ROOT)
    content = path.read_text(errors="ignore")
    if "<html" not in content.lower():
        return None

    # strip any pre-existing canonical nav/footer before context-sniffing so
    # a restamp run doesn't mistake the nav's own city links (or a stale
    # rendering) for the page's real breadcrumb/content signal.
    context_source = OLD_CANONICAL_NAV_RE.sub("", content)
    context_source = OLD_CANONICAL_FOOTER_RE.sub("", context_source)
    prov, city_slug, city_label, page_path = get_context(rel, context_source)
    nav_html = render_nav(prov, city_slug)
    footer_html = render_footer(prov, city_slug, city_label, page_path)

    original = content
    action = []

    # Re-stamp (or remove-and-replace) any prior canonical block first, so
    # re-running this script is idempotent.
    if OLD_CANONICAL_NAV_RE.search(content):
        content = OLD_CANONICAL_NAV_RE.sub(lambda m: nav_html, content, count=1)
        action.append("nav:restamped")
    elif NAV_TAG_RE.search(content):
        content = NAV_TAG_RE.sub(lambda m: nav_html, content, count=1)
        action.append("nav:replaced")
    elif "<body" in content.lower():
        content = re.sub(r"(<body[^>]*>)", r"\1\n" + nav_html.replace("\\", "\\\\"), content, count=1)
        action.append("nav:inserted")

    if OLD_CANONICAL_FOOTER_RE.search(content):
        content = OLD_CANONICAL_FOOTER_RE.sub(lambda m: footer_html, content, count=1)
        action.append("footer:restamped")
    elif NEWSLETTER_SECTION_RE.search(content) and FOOTER_TAG_RE.search(content):
        combined_re = re.compile(
            NEWSLETTER_SECTION_RE.pattern + r"\s*" + FOOTER_TAG_RE.pattern, re.DOTALL
        )
        if combined_re.search(content):
            content = combined_re.sub(lambda m: footer_html, content, count=1)
            action.append("footer:replaced(with-newsletter)")
        else:
            content = FOOTER_TAG_RE.sub(lambda m: footer_html, content, count=1)
            action.append("footer:replaced(footer-only)")
    elif FOOTER_TAG_RE.search(content):
        content = FOOTER_TAG_RE.sub(lambda m: footer_html, content, count=1)
        action.append("footer:replaced(footer-only)")
    elif "</body>" in content:
        content = content.replace("</body>", footer_html + "\n</body>", 1)
        action.append("footer:inserted")

    content = ensure_shared_assets(content)

    if content != original and not dry_run:
        path.write_text(content)

    return {
        "path": str(rel),
        "province": prov,
        "city": city_label,
        "actions": action,
        "changed": content != original,
    }


def find_pages():
    pages = []
    for p in ROOT.rglob("*.html"):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in EXCLUDE_DIRS:
            continue
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if p.name in EXCLUDE_FILES:
            continue
        pages.append(p)
    return sorted(pages)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    pages = find_pages()
    if args.limit:
        pages = pages[: args.limit]

    results = []
    for p in pages:
        r = process_file(p, args.dry_run)
        if r:
            results.append(r)

    changed = [r for r in results if r["changed"]]
    no_nav_no_footer = [
        r for r in results
        if r["changed"] is False and not r["actions"]
    ]
    from collections import Counter
    action_counts = Counter(a for r in results for a in r["actions"])

    print(f"Scanned {len(results)} pages, changed {len(changed)}.")
    print("Action breakdown:")
    for a, c in sorted(action_counts.items()):
        print(f"  {a}: {c}")
    print(f"Pages untouched (no nav/footer pattern matched, no action taken): {len(no_nav_no_footer)}")
    if no_nav_no_footer[:15]:
        print("Sample untouched pages:")
        for r in no_nav_no_footer[:15]:
            print(f"  {r['path']}")


if __name__ == "__main__":
    main()
