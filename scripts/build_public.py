#!/usr/bin/env python3
"""Copy only the public website into dist/ for Cloudflare Pages.

Until 2026-09-28 Pages published the whole repo, so internal docs (*.md), spreadsheets (*.csv),
scripts, Worker code and data files were all downloadable from homepowerrebate.com.
Cloudflare Pages settings: Build command `python3 scripts/build_public.py`, Build output directory `dist`.

Rule: allowlist by file type and location. Anything not listed stays private.
  python3 scripts/build_public.py            # build dist/
  python3 scripts/build_public.py --check    # list what would be excluded, build nothing
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

PUBLIC_EXT = {".html", ".css", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".ico", ".avif",
              ".woff", ".woff2", ".ttf", ".otf", ".xml", ".webmanifest", ".mp4", ".webm", ".pdf"}
PUBLIC_FILES = {"robots.txt", "llms.txt", "_redirects", "_headers", "form-handlers.js",
                "form-handlers-with-installer-select.js", "128e460777465d0f18b1a1d82780a08b.txt"}
PUBLIC_PREFIXES = ("installers/json/", "rebate-tracker/changes.json", "calculator/data/", "calculator/rebate-engine.js", "calculator/widget.js")
PRIVATE_DIRS = {"scripts", "data", "reports", ".claude", ".github", "node_modules", "_partials", "dist",
                "meta-worker", "pinterest-worker", "powerscore-history"}
# Dev/template pages that are real .html files but never meant to be public.
PRIVATE_HTML = {"og-image.html", "CITY_PAGE_TEMPLATE_OPTIMIZED.html", "ONTARIO_CITY_PAGE_TEMPLATE.html",
                "city-page-template-with-carousel.html", "installer-carousel-component.html", "installer-carousel.html",
                "solar-carousel.html", "unified-carousel.html", "pinterest-pin-templates.html", "preview.html", "nav-footer.html"}


def tracked_files():
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True)
    if out.returncode == 0 and out.stdout.strip():
        return [Path(p) for p in out.stdout.splitlines()]
    return [p.relative_to(ROOT) for p in ROOT.rglob("*") if p.is_file()]


def is_public(rel: Path) -> bool:
    s = rel.as_posix()
    if rel.parts[0] in PRIVATE_DIRS or any(part.startswith(".") for part in rel.parts):
        return False
    if s in PUBLIC_FILES or s.startswith(PUBLIC_PREFIXES):
        return True
    if rel.name in PRIVATE_HTML:
        return False
    return rel.suffix.lower() in PUBLIC_EXT


def main():
    files = tracked_files()
    pub = [f for f in files if (ROOT / f).is_file() and is_public(f)]
    priv = [f for f in files if f not in set(pub)]
    if "--check" in sys.argv:
        for f in sorted(priv):
            print("private:", f)
        print(f"{len(pub)} public, {len(priv)} private")
        return
    if DIST.exists():
        shutil.rmtree(DIST)
    fixes = json.loads((ROOT / "data" / "link-fixes.json").read_text()) if (ROOT / "data" / "link-fixes.json").exists() else {}
    if fixes:
        sys.path.insert(0, str(ROOT / "scripts"))
        from fix_dead_links import apply_fixes
    changed = 0
    for f in pub:
        dst = DIST / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        if fixes and f.suffix == ".html":
            t = (ROOT / f).read_text(encoding="utf-8", errors="ignore")
            new = apply_fixes(t, fixes.get("replace", {}), fixes.get("remove", []))
            # Site search (Pagefind) should only index pages we want found: skip anything marked noindex.
            if re.search(r'<meta\s+name="robots"[^>]*noindex', new, re.I) and "data-pagefind-ignore" not in new:
                new = re.sub(r"<body", '<body data-pagefind-ignore="all"', new, count=1)
            # Site search relevance: a page's main heading counts far more than repeated words in its body.
            new = re.sub(r'<header class="hero">(.*?)</header>', r'<div class="hero">\1</div>', new, count=1, flags=re.S)  # Pagefind skips <header>
            new = re.sub(r"<h1(?![^>]*data-pagefind-weight)", '<h1 data-pagefind-weight="10"', new, count=1)
            dst.write_text(new, encoding="utf-8")
            changed += new != t
        else:
            shutil.copy2(ROOT / f, dst)
    print(f"dist/: {len(pub)} public files; {len(priv)} private files left out; dead-link fixes applied to {changed} pages")


if __name__ == "__main__":
    main()
