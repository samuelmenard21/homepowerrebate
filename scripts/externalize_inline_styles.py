#!/usr/bin/env python3
"""Move inline style="..." attributes into classes (homepage and installer index).

Run LAST, after any generator that writes these pages, so generator-injected inline styles are cleaned too.
Each distinct style string becomes a class `is-<hash>` in a block between EXTRACTED-INLINE-START/END in <head>
(re-runs read the block, add new rules and drop unused ones, so it is idempotent).

The shared CSS (_partials/nav-footer.html) raises inline text under 13px and fixes amber/sage text contrast with
[style*=...] selectors. Those cannot see classes, so the same rules are applied here to the declarations.
Styles that other shared attribute selectors still target are left inline (see KEEP_INLINE).
Usage: python3 scripts/externalize_inline_styles.py [page.html ...]
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["index.html", "installers/index.html"]
S, E = "/* EXTRACTED-INLINE-START */", "/* EXTRACTED-INLINE-END */"
SPEC = "body .{c}.{c}.{c}"

# shared-CSS attribute selectors we cannot reproduce on a class: leave these inline
KEEP_INLINE = [
    re.compile(r"line-height:\s*2\.2"),
    re.compile(r"border:\s*1px solid var\(--rule\)"),
]
SEGMENT = re.compile(r"(<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->)", re.S | re.I)
TAG = re.compile(r"<([a-zA-Z][\w-]*)((?:\s+[^<>]*?)?)(/?)>", re.S)
STYLE_ATTR = re.compile(r"""\sstyle=(?:"([^"]*)"|'([^']*)')""", re.S)
CLASS_ATTR = re.compile(r"""\sclass=(?:"([^"]*)"|'([^']*)')""", re.S)


def normalise(css):
    decls = [d.strip() for d in css.strip().split(";") if d.strip()]
    return "; ".join(decls)


def adjust(decls, tag):
    """Apply the same floors and contrast fixes the shared CSS applies to inline styles."""
    out = []
    amber_bg = False
    for d in decls.split("; "):
        k, _, v = d.partition(":")
        k, v = k.strip().lower(), v.strip()
        m = re.fullmatch(r"(\d+(?:\.\d+)?)px", v) if k == "font-size" else None
        if m and float(m.group(1)) < 13:
            d = "font-size: 13px !important"
        elif k == "color" and re.fullmatch(r"var\(--amber\)", v):
            d = "color: #a4540a !important"
        elif k == "color" and re.fullmatch(r"var\(--sage\)", v):
            d = "color: #4f6f61 !important"
        elif k == "background" and tag in ("a", "button") and re.fullmatch(r"(var\(--amber\)|#d4751c)", v, re.I):
            amber_bg = True
        out.append(d)
    if amber_bg:
        out = [d for d in out if not re.match(r"(background|color)\s*:", d)] + ["background: #b4590a !important", "color: #fff !important"]
    return "; ".join(out)


def process(text, existing):
    rules = {}  # class -> declarations
    kept = 0

    def retag(m):
        nonlocal kept
        tag, attrs, slash = m.group(1), m.group(2), m.group(3)
        sm = STYLE_ATTR.search(attrs)
        if not sm:
            return m.group(0)
        raw = sm.group(1) if sm.group(1) is not None else sm.group(2)
        if "{{" in raw or "&quot;" in raw or "{%" in raw:
            return m.group(0)
        norm = normalise(raw)
        if not norm or any(k.search(norm) for k in KEEP_INLINE):
            kept += 1
            return m.group(0)
        decls = adjust(norm, tag.lower())
        cls = "is-" + hashlib.sha1(decls.encode()).hexdigest()[:8]
        rules[cls] = decls
        attrs = attrs[:sm.start()] + attrs[sm.end():]
        cm = CLASS_ATTR.search(attrs)
        if cm:
            val = cm.group(1) if cm.group(1) is not None else cm.group(2)
            attrs = attrs[:cm.start()] + f' class="{val} {cls}"' + attrs[cm.end():]
        else:
            attrs = attrs + f' class="{cls}"'
        return f"<{tag}{attrs}{slash}>"

    parts = SEGMENT.split(text)
    for i in range(0, len(parts), 2):  # even indexes are markup, odd are script/style/comment
        parts[i] = TAG.sub(retag, parts[i])
    return "".join(parts), rules, kept


def block_html(rules):
    lines = [S]
    for cls in sorted(rules):
        lines.append(SPEC.format(c=cls) + " { " + rules[cls].rstrip(";") + "; }")
    lines.append(E)
    return "<style>\n" + "\n".join(lines) + "\n</style>"


BLOCK_RE = re.compile(r"<style>\s*" + re.escape(S) + r".*?" + re.escape(E) + r"\s*</style>\n?", re.S)
RULE_RE = re.compile(r"body (\.is-[0-9a-f]{8})\.is-[0-9a-f]{8}\.is-[0-9a-f]{8} \{ (.*?) \}", re.S)


def run(path):
    p = ROOT / path
    html = p.read_text(encoding="utf-8")
    old = {}
    bm = BLOCK_RE.search(html)
    if bm:
        for m in RULE_RE.finditer(bm.group(0)):
            old[m.group(1)[1:]] = m.group(2).rstrip(";")
        html = html[:bm.start()] + html[bm.end():]
    new_html, rules, kept = process(html, old)
    used = set(re.findall(r"\bis-[0-9a-f]{8}\b", new_html))
    allrules = {c: d for c, d in {**old, **rules}.items() if c in used}
    new_html = new_html.replace("</head>", block_html(allrules) + "\n</head>", 1)
    p.write_text(new_html, encoding="utf-8")
    left = len(re.findall(r'<[a-zA-Z][^<>]*\sstyle="', SEGMENT.sub("", new_html)))
    print(f"{path}: {len(allrules)} classes, {kept} kept inline by rule, {left} inline style attributes remain")


if __name__ == "__main__":
    for pg in (sys.argv[1:] or PAGES):
        run(pg)
