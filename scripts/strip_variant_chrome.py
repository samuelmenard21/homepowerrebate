#!/usr/bin/env python3
"""Template variants (_partials/templates/base/*.css) are verbatim copies of old inline <style> blocks. Many of them
also carry an old copy of the shared header, footer and breadcrumb CSS, and a variant linked after /assets/site.css
silently undoes later fixes to the shared CSS (on 2026-10-13 it made the phone header 185px instead of 157px on 1,243
pages). The menu, footer, breadcrumb and floating CTA are stamped from _partials/nav-footer.html, so only the shared
CSS styles them: this script removes every variant rule whose selectors all target that chrome.

  python3 scripts/strip_variant_chrome.py          # rewrite the variant files, then run the restamp
  python3 scripts/strip_variant_chrome.py --check  # exit 1 if any variant still styles the chrome

The registered hash in variants.json is of the original inline block (how the restamp recognises a generator's
output), so editing the served file does not break matching."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "_partials" / "templates" / "base"

# class names stamped by _partials/nav-footer.html
CHROME = re.compile(r"^\.(nav|nav-inner|nav-pick|nav-desktop-only|nav-mobile-only|logo|logo-mark|logo-power|footer|footer-[a-z-]+"
                    r"|hpr-breadcrumb|sticky-cta)\b")


def is_chrome_selector(sel: str) -> bool:
    """True when every comma part starts at a chrome class (descendants of the chrome included)."""
    parts = [p.strip() for p in sel.split(",") if p.strip()]
    return bool(parts) and all(CHROME.match(re.sub(r"^(html|body)\s+", "", p)) for p in parts)


def blocks(css: str):
    """Yield (prelude, body, start, end) for each top-level block; body is None for @import-style statements."""
    i, n = 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            return
        prelude = css[i:j]
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == "{":
                depth += 1
            elif css[k] == "}":
                depth -= 1
            k += 1
        yield prelude, css[j + 1:k - 1], i, k
        i = k


def strip(css: str):
    out, last, removed = [], 0, 0
    for prelude, body, s, e in blocks(css):
        p = re.sub(r"/\*.*?\*/", "", prelude, flags=re.S).strip()
        if p.startswith("@media") or p.startswith("@supports"):
            inner, r = strip(body)
            removed += r
            if r:
                kept = re.sub(r"/\*.*?\*/", "", inner).strip()
                lead = prelude[:len(prelude) - len(prelude.lstrip())]
                out.append(css[last:s] + (lead + prelude.strip() + " {" + inner + "}" if kept else lead.rstrip(" \t")))
                last = e
            continue
        if not p.startswith("@") and is_chrome_selector(p):
            lead = prelude[:len(prelude) - len(prelude.lstrip())]
            out.append(css[last:s] + lead.rstrip(" \t"))
            last = e
            removed += 1
    out.append(css[last:])
    return "".join(out), removed


def main():
    check = "--check" in sys.argv
    total, files = 0, 0
    for f in sorted(BASE.glob("*.css")):
        css = f.read_text(encoding="utf-8")
        new, r = strip(css)
        if not r:
            continue
        total += r
        files += 1
        if check:
            print(f"FAIL {f.relative_to(ROOT)}: {r} rule(s) style the shared menu, footer or breadcrumb")
        else:
            new = re.sub(r"\n{3,}", "\n\n", new)
            if not new.strip():
                new = "/* Old copy of the shared menu and footer CSS; /assets/site.css styles them now. */\n"
            f.write_text(new, encoding="utf-8")
    if check:
        print("OK   no variant styles the shared chrome" if not total else f"{total} rule(s) in {files} file(s)")
        sys.exit(1 if total else 0)
    print(f"removed {total} chrome rule(s) from {files} variant file(s)")


if __name__ == "__main__":
    main()
