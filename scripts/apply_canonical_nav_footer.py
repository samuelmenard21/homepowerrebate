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
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import regions
PARTIAL = ROOT / "_partials" / "nav-footer.html"
POWERSCORE_DATA = ROOT / "powerscore-data.json"

EXCLUDE_DIRS = {".git", "node_modules", "scripts", ".claude", "_partials", "dist"}
EXCLUDE_FILES = {
    "404.html", "og-image.html", "nav-footer.html",
    "CITY_PAGE_TEMPLATE_OPTIMIZED.html", "ONTARIO_CITY_PAGE_TEMPLATE.html",
    "city-page-template-with-carousel.html", "installer-carousel-component.html",
    "installer-carousel.html", "solar-carousel.html", "unified-carousel.html",
    "pinterest-pin-templates.html", "preview.html",
}

PROV_CODES = set(regions.CODES)
# ca/<x> or us/<x> path prefix -> province-tab code
REGION_PREFIX_TO_CODE = dict(regions.CODE_BY_PREFIX)
CATEGORY_NAMES = {
    "heat-pump", "insulation", "solar", "battery", "water-heater",
    "smart-thermostats", "ev-charger", "windows-doors", "windows", "appliances", "hrv",
}


def load_city_labels():
    """prov_code -> {leaf_city_slug: Label} built from powerscore-data.json,
    which already enumerates every real city page with a clean label."""
    data = json.loads(POWERSCORE_DATA.read_text())
    out = {}
    region_key_to_code = dict(regions.CODE_BY_PATH)
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


def content_insert_point(html_text: str) -> int:
    """Where to insert new page content so it sits ABOVE the shared footer block.
    Inserting just before "<footer" puts content inside the CANONICAL-FOOTER markers,
    and the next restamp deletes it (happened to 327 pages before 2026-09-28).
    Returns -1 if neither anchor exists."""
    i = html_text.find(FOOTER_MARKER_START)
    return i if i >= 0 else html_text.find("<footer")


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

    # installers/<region-code>/<city>/<service>/ (ranking pages, build_installer_rankings.py)
    if len(parts) >= 3 and parts[0] == "installers" and parts[1] in REGION_PREFIX_TO_CODE.values():
        code, leaf = parts[1], parts[2]
        if leaf not in ("index.html",):
            label = CITY_LABELS.get(code, {}).get(leaf, leaf.replace("-", " ").title())
            return code, leaf, label, page_path

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
    text = regions.expand_tokens(PARTIAL.read_text())

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


def render_footer(prov, city_slug, city_label, page_path, skip_newsletter=False):
    html = FOOTER_RAW
    if skip_newsletter:
        # The page already has its own newsletter form. Two forms share the same ids (only the first works) and read as a duplicate.
        html = NEWSLETTER_SECTION_RE.sub("", html, count=1)
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


SITE_CSS_PATH = ROOT / "assets" / "site.css"
SITE_CSS_LINK_RE = re.compile(r'<link rel="stylesheet" href="/assets/site\.css\?v=[0-9a-f]+" data-hpr-site-css>')
_SITE_CSS = {}


# Page templates. A family of generated pages that used to carry the same inline <style> block (a "variant": older
# generators left several slightly different copies) now links that block as a cached file, /assets/tpl/<variant>.css,
# in exactly the same place (verbatim rules, same cascade position: rendering cannot change), and gets the body class
# tpl-<family>, which scopes the family's shared design in _partials/templates/<family>.css (part of site.css).
# Sources: _partials/templates/base/<variant>.css, registered in _partials/templates/variants.json with the normalised
# sha1 of the block. Add variants with scripts/adopt_template_variants.py.
TEMPLATES_DIR = ROOT / "_partials" / "templates"
TPL_ASSETS = ROOT / "assets" / "tpl"
TEMPLATE_VARIANTS = {k: (v["family"], v["hash"]) for k, v in json.loads((TEMPLATES_DIR / "variants.json").read_text()).items()} if (TEMPLATES_DIR / "variants.json").exists() else {}
# a generator that copies its CSS from an already converted page has no inline block left: recognise it by structure
TEMPLATE_SIGNATURE = {"article": ('<section class="hero"><div class="wrap"><div class="amount-badge">', '<article class="article">')}
# families recognised by structure alone, whose pages keep their own CSS (the design file only adds to it)
FAMILY_SIGNATURE = {"hub": ('<header class="hero hub-hero">', "<!-- HUB-TOP-START -->")}
STYLE_RE = re.compile(r'<style(?: id="([\w-]+)")?>([\s\S]*?)</style>\n?')
TPL_LINK_RE = re.compile(r'<link rel="stylesheet" href="/assets/tpl/([a-z0-9-]+)\.css\?v=[0-9a-f]+" data-hpr-tpl(?: id="[\w-]+")?>\n?')


def _template_css() -> str:
    out = []
    for name in FAMILIES:
        p = TEMPLATES_DIR / f"{name}.css"
        if p.exists():
            out.append(f"/* ===== template design: {name} ({p.name}) ===== */\n" + p.read_text(encoding="utf-8"))
    return "\n".join(out)


_TPL_LINKS = {}


def tpl_link(variant: str, el_id: str = "") -> str:
    if el_id:  # the inline block had an id that its generator looks for: keep it on the link
        return tpl_link(variant).replace(" data-hpr-tpl>", f' data-hpr-tpl id="{el_id}">')
    if variant not in _TPL_LINKS:
        body = (TEMPLATES_DIR / "base" / f"{variant}.css").read_text(encoding="utf-8")
        h = __import__("hashlib").sha1(body.encode()).hexdigest()[:10]
        _TPL_LINKS[variant] = f'<link rel="stylesheet" href="/assets/tpl/{variant}.css?v={h}" data-hpr-tpl>\n'
    return _TPL_LINKS[variant]


def write_tpl_assets():
    TPL_ASSETS.mkdir(parents=True, exist_ok=True)
    keep = set()
    for v in TEMPLATE_VARIANTS:
        body = (TEMPLATES_DIR / "base" / f"{v}.css").read_text(encoding="utf-8")
        out = TPL_ASSETS / f"{v}.css"
        keep.add(out.name)
        if not out.exists() or out.read_text(encoding="utf-8") != body:
            out.write_text(body, encoding="utf-8")
    for f in TPL_ASSETS.glob("*.css"):
        if f.name not in keep:
            f.unlink()


def site_css_body() -> str:
    """The shared CSS as served from /assets/site.css (with the metric-matched fallback fonts in every font stack)."""
    if "body" not in _SITE_CSS:
        _SITE_CSS["body"] = ("/* HomePowerRebate shared styles. Generated from _partials/nav-footer.html and _partials/templates/ by scripts/apply_canonical_nav_footer.py; edit those, not this file. */\n"
                             + add_font_fallbacks(CSS_RAW + "\n" + _template_css()) + "\n")
    return _SITE_CSS["body"]


def _norm_hash(css: str) -> str:
    return __import__("hashlib").sha1(" ".join(css.split()).encode()).hexdigest()


def _set_body_classes(content: str, add=(), drop=lambda c: False) -> str:
    bm = re.search(r"<body\b([^>]*)>", content)
    if not bm:
        return content
    attrs = bm.group(1)
    cm = re.search(r'\bclass="([^"]*)"', attrs)
    have = cm.group(1).split() if cm else []
    new = [c for c in have if not drop(c)] + [c for c in add if c not in have]
    if new == have:
        return content
    if cm:
        attrs = attrs.replace(cm.group(0), f'class="{" ".join(new)}"') if new else attrs.replace(" " + cm.group(0), "")
    else:
        attrs += f' class="{" ".join(new)}"'
    return content[:bm.start()] + f"<body{attrs}>" + content[bm.end():]


CANON_RE = re.compile(r'<link rel="canonical" href="https://homepowerrebate\.com(/[^"]*)"')
# every page belongs to exactly one family (body class tpl-<family>); see page_family()
FAMILIES = ("article", "ranking", "hub", "profile", "stacking", "powerscore", "calculator", "home", "page")


def page_family(content: str, linked: list) -> str:
    """The page's template family: structure first, then the variants it links, then its URL."""
    for fam, sig in FAMILY_SIGNATURE.items():
        if all(x in content for x in sig):
            return fam
    for v in linked:
        fam = TEMPLATE_VARIANTS.get(v, ("", ""))[0]
        if fam in ("article", "ranking"):
            return fam
    if 'class="ip-wrap"' in content:
        return "profile"
    cm = CANON_RE.search(content)
    path = cm.group(1) if cm else ""
    if path in ("/", ""):
        return "home" if 'id="hero-find"' in content else "page"
    for prefix, fam in (("/stacking-calculator/", "stacking"), ("/powerscore/", "powerscore"), ("/calculator/", "calculator")):
        if path.startswith(prefix):
            return fam
    return "page"


def ensure_template(content: str) -> str:
    """Swap every registered inline <style> block for its cached /assets/tpl/ file (same place, same rules) and give
    the page its family class."""
    by_hash = {h: v for v, (_, h) in TEMPLATE_VARIANTS.items()}
    out, last = [], 0
    for m in STYLE_RE.finditer(content):
        v = by_hash.get(_norm_hash(m.group(2)))
        if v:
            out.append(content[last:m.start()] + tpl_link(v, m.group(1) or ""))
            last = m.end()
    content = "".join(out) + content[last:]
    # refresh versions; drop links to variants no longer registered
    content = TPL_LINK_RE.sub(lambda m: (tpl_link(m.group(1), (re.search(r' id="([\w-]+)"', m.group(0)) or [None, ""])[1]) if m.group(1) in TEMPLATE_VARIANTS else m.group(0)), content)
    linked = TPL_LINK_RE.findall(content)
    # a generator that copied its CSS from an already converted page has no inline block left: recognise it by structure
    if not linked:
        for sv, sig in TEMPLATE_SIGNATURE.items():
            if all(x in content for x in sig) and not any(".amount-badge" in blk for _, blk in STYLE_RE.findall(content)):
                pos = SITE_CSS_LINK_RE.search(content) or OLD_CSS_BLOCK_RE.search(content)
                link = tpl_link(sv)
                content = content[:pos.start()] + link + content[pos.start():] if pos else content.replace("</head>", link + "</head>", 1)
                linked = [sv]
                break
    fam = page_family(content, linked)
    return _set_body_classes(content, [f"tpl-{fam}"], drop=lambda c: (c.startswith("tpl-") and c != f"tpl-{fam}") or c.startswith("tplb-"))
    # pages converted before variants had their own class (2026-10-10): tpl-<family> alone means the family's own variant
    fam = re.search(r'<body[^>]*\bclass="[^"]*\btpl-([a-z-]+)', content)
    if fam and fam.group(1) in TEMPLATE_VARIANTS:
        return _add_body_classes(content, [f"tplb-{fam.group(1)}"])
    for v, sig in TEMPLATE_SIGNATURE.items():
        if all(x in content for x in sig) and not any(".amount-badge" in blk for _, blk in STYLE_RE.findall(content)):
            return _add_body_classes(content, [f"tpl-{TEMPLATE_VARIANTS[v][0]}", f"tplb-{v}"])
    return content


def site_css_link() -> str:
    h = __import__("hashlib").sha1(site_css_body().encode()).hexdigest()[:10]
    return f'<link rel="stylesheet" href="/assets/site.css?v={h}" data-hpr-site-css>'


def write_site_css():
    write_tpl_assets()
    _write_site_css()


def _write_site_css():
    """The shared CSS lives in one cached file (/assets/site.css) instead of a copy inside every page.
    Source of truth stays the SHARED CSS block in _partials/nav-footer.html; the link carries a content hash so
    browsers and Cloudflare pick up a change at once and can cache the file for a year."""
    SITE_CSS_PATH.parent.mkdir(parents=True, exist_ok=True)
    body = site_css_body()
    if not SITE_CSS_PATH.exists() or SITE_CSS_PATH.read_text() != body:
        SITE_CSS_PATH.write_text(body)


OG_S, OG_E = "<!-- OG-CARD-START -->", "<!-- OG-CARD-END -->"
OG_BLOCK_RE = re.compile(re.escape(OG_S) + r".*?" + re.escape(OG_E) + r"\n?", re.S)
OG_OLD_RE = re.compile(r'<meta (?:property|name)="(?:og:image(?::[a-z]+)?|twitter:image(?::alt)?|twitter:card)" content="[^"]*">\n?')
_OG_MANIFEST = {}


def ensure_og(content: str) -> str:
    """Point og:image and twitter:image at the page's own share card (og/<path>.jpg, scripts/build_og_cards.py)."""
    if not _OG_MANIFEST:
        mp = ROOT / "og" / "manifest.json"
        _OG_MANIFEST.update(json.loads(mp.read_text()) if mp.exists() else {"": ""})
    cm = CANON_RE.search(content)
    if not cm:
        return content
    card = "og/" + (re.sub(r"\.html$", "", cm.group(1).strip("/")) or "home") + ".jpg"
    v = _OG_MANIFEST.get(card)
    if not v:
        return content
    title = html.unescape((re.search(r"<title>(.*?)</title>", content, re.S) or [None, ""])[1]).strip()
    url = f"https://homepowerrebate.com/{card}?v={v}"
    block = (f'{OG_S}\n<meta property="og:image" content="{url}">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
             f'<meta property="og:image:type" content="image/jpeg">\n<meta property="og:image:alt" content="{html.escape(title, quote=True)}">\n'
             f'<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:image" content="{url}">\n{OG_E}\n')
    content = OG_BLOCK_RE.sub("", content)
    content = OG_OLD_RE.sub("", content)
    return content.replace("</head>", block + "</head>", 1)


def ensure_shared_assets(content: str) -> str:
    js_block = f"<script>\n{JS_MARKER_START}\n{JS_RAW}\n{JS_MARKER_END}\n</script>"
    content = ensure_template(content)
    content = ensure_og(content)
    # the link sits exactly where the inline block was, so the cascade order is unchanged
    if OLD_CSS_BLOCK_RE.search(content):
        content = OLD_CSS_BLOCK_RE.sub(lambda m: site_css_link(), content, count=1)
    elif SITE_CSS_LINK_RE.search(content):
        content = SITE_CSS_LINK_RE.sub(lambda m: site_css_link(), content, count=1)
    else:
        content = content.replace("</head>", site_css_link() + "\n</head>", 1)
    if OLD_JS_BLOCK_RE.search(content):
        content = OLD_JS_BLOCK_RE.sub(lambda m: js_block, content, count=1)
    else:
        content = content.replace("</body>", js_block + "\n</body>", 1)
    return content

CHROME_RE = re.compile(r"<nav\b.*?</nav>|<footer\b.*?</footer>|<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->",
                       re.DOTALL | re.IGNORECASE)


def visible_words(html_text: str) -> set:
    return set(re.sub(r"<[^>]+>", " ", CHROME_RE.sub(" ", html_text)).split())


def content_loss(before: str, after: str) -> list:
    """Visible words (outside nav/footer/script/style/comments) present before but gone after."""
    return sorted(visible_words(before) - visible_words(after))[:20]


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
_TAG_RE = re.compile(r"<(/?)([a-zA-Z][\w-]*)([^<>]*?)(/?)>")


def balanced(fragment: str) -> bool:
    """True when every tag opened in the fragment is closed inside it (script/style/comments ignored)."""
    frag = re.sub(r"<(script|style)\b.*?</\1>|<!--.*?-->", "", fragment, flags=re.S | re.I)
    stack = []
    for m in _TAG_RE.finditer(frag):
        close, name, _, selfclose = m.groups()
        name = name.lower()
        if name in VOID or selfclose:
            continue
        if not close:
            stack.append(name)
        else:
            if name not in stack:
                return False
            while stack and stack[-1] != name:
                stack.pop()  # implied end tags (li, p, td) are tolerated
            stack.pop()
    return all(n in ("li", "p", "td", "tr", "th", "dd", "dt", "option", "tbody", "thead") for n in stack)


FONT_CSS_RE = re.compile(r'<link href="(https://fonts\.googleapis\.com/css2[^"]*)" rel="stylesheet">')
ICON_LINKS = ('<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n<link rel="icon" href="/favicon.ico" sizes="48x48">\n'
              '<link rel="apple-touch-icon" href="/apple-touch-icon.png">')


_FAMILY_RE = re.compile(r"font-family:[^;}\"<]*")
_FALLBACKS = (("Fraunces", "'Fraunces Fallback'"), ("Inter Tight", "'Inter Tight Fallback'"))


def add_font_fallbacks(content: str) -> str:
    """Put the metric-matched fallback face right after each web font in every font-family list. Idempotent."""
    def fix(m):
        s = m.group(0)
        for web, fb in _FALLBACKS:
            if "Fallback" in s:
                break
            s = re.sub(r"""(['"]%s['"])""" % web, lambda x: x.group(1) + ", " + fb, s, count=1)
        return s
    # never touch @font-face rules: a face has exactly one family name (the inline latin faces live between the FONT-PRELOAD markers)
    parts = re.split(r"(<!-- FONT-PRELOAD-START -->.*?<!-- FONT-PRELOAD-END -->)", content, flags=re.S)
    return "".join(p if i % 2 else _FAMILY_RE.sub(fix, p) for i, p in enumerate(parts))


FONT_FILES = ("https://fonts.gstatic.com/s/fraunces/v38/6NU78FyLNQOQZAnv9bYEvDiIdE9Ea92uemAk_WBq8U_9v0c2Wa0KxC9TeP2Xz5c.woff2",
              "https://fonts.gstatic.com/s/intertight/v9/NGSwv5HMAFg6IuGlBNMjxLsH8ahuQ2e8.woff2")
_LATIN = ("U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, "
          "U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD")
FONT_HEAD = (
    "<!-- FONT-PRELOAD-START -->\n"
    + "".join(f'<link rel="preload" as="font" type="font/woff2" crossorigin href="{u}">\n' for u in FONT_FILES)
    + "<style>@font-face{font-family:'Fraunces';font-style:normal;font-weight:400 700;font-display:swap;src:url(" + FONT_FILES[0] + ") format('woff2');unicode-range:" + _LATIN + "}"
    + "@font-face{font-family:'Inter Tight';font-style:normal;font-weight:400 700;font-display:swap;src:url(" + FONT_FILES[1] + ") format('woff2');unicode-range:" + _LATIN + "}</style>\n"
    "<!-- FONT-PRELOAD-END -->"
)
_FONT_HEAD_RE = re.compile(r"<!-- FONT-PRELOAD-START -->.*?<!-- FONT-PRELOAD-END -->", re.S)


RAIL_S, RAIL_E = "<!-- PAGE-RAIL-START -->", "<!-- PAGE-RAIL-END -->"
_RAIL_RE = re.compile(re.escape(RAIL_S) + r".*?" + re.escape(RAIL_E) + r"\n?", re.S)
# the same 'On this page' list for phones and tablets, folded, right under the hero (hidden where the side panel shows)
MTOC_S, MTOC_E = "<!-- MOBILE-TOC-START -->", "<!-- MOBILE-TOC-END -->"
_MTOC_RE = re.compile(re.escape(MTOC_S) + r".*?" + re.escape(MTOC_E) + r"\n?", re.S)
# long-form templates that get the desktop side panel (page types with no full-width colour bands)
_RAIL_PATH = re.compile(r"^(blog/[^/]+/|guides/[^/]+/|questions/[^/]+/|programs/(?!utility-comparison)[^/]+/|(ca|us)/[a-z]+/([a-z-]+/)?[a-z-]+/[a-z-]+/|(ca|us)/[a-z]+/[a-z-]+/)index\.html$|^blog-[^/]+\.html$")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", html.unescape(text).lower()).strip("-")[:48] or "section"


_VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


def top_level_children(body: str):
    """[(tag, attrs)] for the direct children of a fragment (script, style and comments masked)."""
    masked = re.sub(r"<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->", lambda m: " " * len(m.group(0)), body, flags=re.S | re.I)
    kids, depth = [], 0
    for m in re.finditer(r"<(/?)([a-zA-Z][\w-]*)([^<>]*?)(/?)>", masked):
        close, name, attrs, selfclose = m.groups()
        name = name.lower()
        if name in _VOID_TAGS or selfclose:
            if depth == 0:
                kids.append((name, attrs))
            continue
        if not close:
            if depth == 0:
                kids.append((name, attrs))
            depth += 1
        else:
            depth = max(0, depth - 1)
    return kids


def child_end(body: str, idx: int) -> int:
    """Offset just after the idx-th direct child of a fragment (same masking as top_level_children); -1 if not found."""
    masked = re.sub(r"<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->", lambda m: " " * len(m.group(0)), body, flags=re.S | re.I)
    n, depth = -1, 0
    for m in re.finditer(r"<(/?)([a-zA-Z][\w-]*)([^<>]*?)(/?)>", masked):
        close, name, attrs, selfclose = m.groups()
        name = name.lower()
        if name in _VOID_TAGS or selfclose:
            if depth == 0:
                n += 1
                if n == idx:
                    return m.end()
            continue
        if not close:
            if depth == 0:
                n += 1
            depth += 1
        else:
            depth = max(0, depth - 1)
            if depth == 0 and n == idx:
                return m.end()
    return -1


def ensure_rail(content: str, rel: str, plan_href: str) -> str:
    """Desktop side panel for long-form pages: an 'On this page' list built from the page's own h2 headings plus a rebate-plan call to action.
    Static HTML (no layout shift); hidden below 1180px. Idempotent: the block lives between PAGE-RAIL markers and main gets class has-rail."""
    content = _MTOC_RE.sub("", _RAIL_RE.sub("", content))
    m = re.search(r'<main id="main"( tabindex="-1")?( class="has-rail")?>', content)
    if not m or not _RAIL_PATH.match(str(rel).replace("\\", "/")):
        return content
    start = m.end()
    end = content.find("</main>", start)
    if end == -1:
        return content
    body = content[start:end]
    if re.search(r'<section class="section|class="cta-box|class="final-cta', body):
        return content  # full-width coloured bands: a side panel would break the stripes
    used = set(re.findall(r'\bid="([^"]+)"', content))
    items = []
    def add_id(h):
        tag, text = h.group(1), h.group(3)
        label = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", text))).strip()
        am = re.search(r'\bid="([^"]+)"', tag)
        if am:
            hid = am.group(1)
        else:
            base = _slug(label); hid = base; i = 2
            while hid in used:
                hid = f"{base}-{i}"; i += 1
            used.add(hid)
            tag = tag[:-1] + f' id="{hid}">'
        if label and len(label) <= 90:
            items.append((hid, label))
        return tag + h.group(2) + h.group(3) + "</h2>"
    new_body = re.sub(r"(<h2\b[^>]*>)()(.*?)</h2>", add_id, body, flags=re.S)
    if len(items) < 3:
        return content
    kids = top_level_children(new_body)
    hero_idx = max((i for i, (n, a) in enumerate(kids) if re.search(r'class="[^"]*\b(hero|post-header)\b', a)), default=-1)
    row = hero_idx + 2  # 1-based grid row right after the last hero block
    lis = "".join(f'<li><a href="#{i}">{html.escape(l)}</a></li>' for i, l in items[:12])
    rail = (f'{RAIL_S}\n<aside class="page-rail" aria-label="On this page" style="grid-row: {row} / span 400"><nav class="rail-toc" aria-label="Page sections"><p class="rail-h">On this page</p><ol>{lis}</ol></nav>'
            f'<div class="rail-cta"><p class="rail-cta-h">Get your free rebate plan</p><p>See which rebates you qualify for. Free, and no sales calls.</p>'
            f'<a class="rail-btn" href="{plan_href}">Get my plan</a></div></aside>\n{RAIL_E}\n')
    cut = child_end(new_body, hero_idx) if hero_idx >= 0 else -1
    if cut > 0:
        mtoc = (f'\n{MTOC_S}\n<details class="toc-mobile"><summary>On this page</summary><ol>{lis}</ol></details>\n{MTOC_E}\n')
        new_body = new_body[:cut] + mtoc + new_body[cut:].lstrip("\n")
    new_main_open = '<main id="main"' + (m.group(1) or "") + ' class="has-rail">'
    return content[:m.start()] + new_main_open + new_body + rail + content[end:]


_WIDE_PATH = re.compile(r"^(ca|us)/[a-z]+/[a-z-]+/index\.html$")


def page_css(content: str) -> str:
    """The page's own CSS in cascade order: inline blocks with the /assets/tpl/ files they became put back in place."""
    def inline(m):
        p = TEMPLATES_DIR / "base" / f"{m.group(1)}.css"
        return "<style>" + p.read_text(encoding="utf-8") + "</style>" if p.exists() else ""
    return "\n".join(b for _, b in STYLE_RE.findall(TPL_LINK_RE.sub(inline, content)))


def ensure_wide(content: str, rel: str) -> str:
    """City hubs with full-width colour bands keep their stripes but use a wider content column (main.has-wide, 1100px from 1280px). Idempotent."""
    content = content.replace('<main id="main" tabindex="-1" class="has-wide">', '<main id="main" tabindex="-1">').replace('<main id="main" class="has-wide">', '<main id="main">')
    if 'class="has-rail"' in content or not _WIDE_PATH.match(str(rel).replace("\\", "/")):
        return content
    widths = [int(x) for x in re.findall(r"\.wrap\s*\{[^}]*max-width:\s*(\d+)px", page_css(content))]
    if not widths or not (700 <= widths[0] <= 960):
        return content
    return re.sub(r'<main id="main"( tabindex="-1")?>', lambda m: '<main id="main"' + (m.group(1) or "") + ' class="has-wide">', content, count=1)


_LAYOUT_WIDE_PATH = re.compile(r"^(index\.html|installers/index\.html|installers/[a-z]+/[a-z-]+/[a-z-]+/index\.html|powerscore/index\.html)$")


def ensure_layout_wide(content: str, rel: str) -> str:
    """Homepage, installer directory and installer ranking pages use the fluid container (main.layout-wide). Idempotent."""
    content = re.sub(r'(<main id="main"(?: tabindex="-1")?) class="layout-wide(?: layout-home)?">', r"\1>", content)
    if not _LAYOUT_WIDE_PATH.match(str(rel).replace("\\", "/")):
        return content
    cls = "layout-wide layout-home" if str(rel).replace("\\", "/") == "index.html" else "layout-wide"
    return re.sub(r'<main id="main"( tabindex="-1")?>', lambda m: '<main id="main"' + (m.group(1) or "") + ' class="' + cls + '">', content, count=1)


def ensure_fast_head(content: str) -> str:
    """Performance and polish in <head>, idempotent:
    - Google Fonts stylesheet loads without blocking first paint (preload, then apply on load; noscript fallback; display=swap is in the URL)
    - favicon and touch icon links
    - the form-handlers script is deferred"""
    content = FONT_CSS_RE.sub(lambda m: (f'<link rel="preload" as="style" href="{m.group(1)}" onload="this.onload=null;this.rel=\'stylesheet\'">\n'
                                         f'<noscript><link rel="stylesheet" href="{m.group(1)}"></noscript>'), content, count=1)
    # latin fonts: inline @font-face plus preload, so the files download from the first bytes of the page instead of after the stylesheet request
    if "</head>" in content:
        if _FONT_HEAD_RE.search(content):
            content = _FONT_HEAD_RE.sub(lambda m: FONT_HEAD, content, count=1)
        else:
            m = re.search(r'<link rel="preload" as="style" href="https://fonts\.googleapis\.com', content) or re.search(r'<link rel="preconnect" href="https://fonts\.gstatic\.com"', content)
            if m:
                content = content[:m.start()] + FONT_HEAD + "\n" + content[m.start():]
    # The inline latin faces cover English text; the Google stylesheet would re-declare them with a swap after first paint, which shifts the layout. Drop it.
    content = re.sub(r'<link rel="preload" as="style" href="https://fonts\.googleapis\.com/css2[^"]*" onload="[^"]*">\n?', "", content)
    content = re.sub(r'<noscript><link rel="stylesheet" href="https://fonts\.googleapis\.com/css2[^"]*"></noscript>\n?', "", content)
    if 'rel="icon"' not in content and "</head>" in content:
        content = content.replace("</head>", ICON_LINKS + "\n</head>", 1)
    content = re.sub(r'<script src="(/form-handlers[^"]*\.js)"></script>', r'<script defer src="\1"></script>', content)
    return add_font_fallbacks(content)


def ensure_landmarks(content: str) -> str:
    """Skip link, <main id="main"> between the canonical nav and footer, and theme-color. Idempotent."""
    if 'name="theme-color"' not in content and "</head>" in content:
        content = content.replace("</head>", '<meta name="theme-color" content="#faf7f2">\n</head>', 1)
    has_main = re.search(r"<main\b", content, re.I)
    if has_main:
        if not re.search(r"<main\b[^>]*\bid=", content, re.I):
            content = re.sub(r"<main\b", '<main id="main"', content, count=1, flags=re.I)
    else:
        a = content.find(NAV_MARKER_END)
        b = content.find(FOOTER_MARKER_START)
        if a == -1 or b == -1 or b < a:
            return content
        a += len(NAV_MARKER_END)
        if not balanced(content[a:b]):
            # markup between nav and footer does not nest cleanly (stray or unclosed tags): do not wrap, tag the page's own content container instead
            seg = content[a:b]
            m = re.search(r"<article\b", seg) or re.search(r"<section\b", seg)
            if not m:
                return content
            tag_end = seg.index(">", m.start())
            tag = seg[m.start():tag_end]
            if "role=" not in tag and "id=" not in tag:
                seg = seg[:tag_end] + ' role="main" id="main"' + seg[tag_end:]
                content = content[:a] + seg + content[b:]
        else:
            content = content[:a] + '\n<main id="main" tabindex="-1">' + content[a:b] + "</main>\n" + content[b:]
    if 'class="skip-link"' not in content and 'id="main"' in content:
        content = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + '\n<a class="skip-link" href="#main">Skip to main content</a>', content, count=1)
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
    outside_footer = OLD_CANONICAL_FOOTER_RE.sub("", content)
    footer_html = render_footer(prov, city_slug, city_label, page_path,
                                skip_newsletter='id="newsletter-form"' in outside_footer)

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
    content = ensure_landmarks(content)
    _pm = re.search(r'href="(/get-quotes/[^"]*)"', nav_html)
    content = ensure_rail(content, rel, _pm.group(1) if _pm else "/get-quotes/")
    content = ensure_wide(content, rel)
    content = ensure_layout_wide(content, rel)
    content = ensure_fast_head(content)

    # Safety net (added 2026-09-28): some pages had real content (e.g. "Learn more about
    # <city> rebates" guide cards) sitting between the old footer markers, and a restamp
    # silently deleted it on 323 pages. Never write a page that would lose any visible
    # text other than what lived inside its old <nav>/<footer> tags.
    # Dropping the footer newsletter on a page that has its own form is intentional, not content loss.
    # --newsletter-copy: the newsletter block's own wording was changed on purpose in the partial, so it is not compared.
    baseline = NEWSLETTER_SECTION_RE.sub("", original) if ('id="newsletter-form"' in outside_footer or "--newsletter-copy" in sys.argv) else original
    if "--newsletter-copy" in sys.argv:
        baseline = re.sub(r'<a id="sticky-cta".*?</a>', '', baseline, flags=re.S)
    lost = content_loss(baseline, content)
    if lost:
        return {"path": str(rel), "province": prov, "city": city_label,
                "actions": action + ["SKIPPED:would-remove-content"], "changed": False, "lost": lost}

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
    write_site_css()
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--newsletter-copy", action="store_true", help="newsletter wording changed on purpose; do not treat as content loss")
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
    skipped = [r for r in results if r.get("lost")]
    if skipped:
        print(f"SKIPPED {len(skipped)} pages that would lose content (fix them by hand):")
        for r in skipped[:25]:
            print(f"  {r['path']}: {' '.join(r['lost'][:8])}")
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
