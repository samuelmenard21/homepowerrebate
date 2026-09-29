#!/usr/bin/env python3
"""Check every internal link and canonical in the site's HTML. Exit 1 if any are broken.

  python3 scripts/check_links.py            # internal links, canonicals, sitemap entries
  python3 scripts/check_links.py --external # also HEAD-check external source links (slow, network)
A link is fine if it points at a real file/folder index, or matches a _redirects rule
(including splats). Run before committing site-wide changes.
"""
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"scripts", "data", "reports", "dist", "node_modules", "_partials", ".git", ".claude"}
SKIP_FILES = {"og-image.html", "CITY_PAGE_TEMPLATE_OPTIMIZED.html", "ONTARIO_CITY_PAGE_TEMPLATE.html", "city-page-template-with-carousel.html",
              "installer-carousel-component.html", "installer-carousel.html", "solar-carousel.html", "unified-carousel.html",
              "pinterest-pin-templates.html", "preview.html", "nav-footer.html"}
HOST = "homepowerrebate.com"


def redirect_rules():
    rules = []
    f = ROOT / "_redirects"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            p = line.split()
            if len(p) >= 2 and not line.startswith("#"):
                rules.append(re.compile("^" + re.escape(p[0]).replace(r"\*", ".*") + "$"))
    return rules


def exists(path, rules):
    path = unquote(path.split("#")[0].split("?")[0])
    if not path or path == "/":
        return True
    rel = path.lstrip("/")
    for c in (ROOT / rel, ROOT / rel / "index.html", ROOT / (rel + ".html")):
        if c.exists():
            return True
    return any(r.match(path) or r.match(path.rstrip("/")) or r.match(path.rstrip("/") + "/") for r in rules)


def main():
    rules = redirect_rules()
    broken = defaultdict(list)
    ext = defaultdict(set)
    pages = [p for p in ROOT.rglob("*.html") if not (set(p.relative_to(ROOT).parts) & SKIP_DIRS) and p.name not in SKIP_FILES]
    for p in pages:
        t = p.read_text(encoding="utf-8", errors="ignore")
        t = re.sub(r"<!--.*?-->|<script.*?</script>", "", t, flags=re.S)
        for m in re.finditer(r'<(?:a|link)\b[^>]*?href="([^"]+)"', t):
            if re.search(r'rel="(?:preconnect|dns-prefetch)"', m.group(0)):
                continue
            h = m.group(1).strip()
            if h.startswith(("mailto:", "tel:", "javascript:", "#", "data:")):
                continue
            u = urlparse(h)
            if u.scheme in ("http", "https") and u.netloc.replace("www.", "") != HOST:
                ext[h].add(str(p.relative_to(ROOT)))
                continue
            path = u.path if not u.netloc else u.path
            if not path.startswith("/"):
                path = "/" + str(p.parent.relative_to(ROOT) / path)
            if not exists(path, rules):
                broken[h].append(str(p.relative_to(ROOT)))
    # sitemap entries must exist
    sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8") if (ROOT / "sitemap.xml").exists() else ""
    for u in re.findall(r"<loc>([^<]+)</loc>", sm):
        if not exists(urlparse(u).path, []):
            broken["SITEMAP " + u].append("sitemap.xml")
    for h, where in sorted(broken.items(), key=lambda x: -len(x[1])):
        print(f"BROKEN {h}  ({len(where)} pages, e.g. {where[0]})")
    print(f"{len(pages)} pages, {len(broken)} broken internal targets, {len(ext)} distinct external links")
    if "--external" in sys.argv:
        import requests
        from concurrent.futures import ThreadPoolExecutor
        H = {"User-Agent": "Mozilla/5.0 HPR-linkcheck"}

        def probe(u):
            try:
                r = requests.head(u, allow_redirects=True, timeout=10, headers=H)
                if r.status_code in (403, 405, 400, 501):
                    r = requests.get(u, timeout=10, stream=True, headers=H)
                return u, r.status_code
            except Exception as e:
                return u, type(e).__name__

        with ThreadPoolExecutor(48) as ex:
            results = list(ex.map(probe, sorted(ext)))
        bad = 0
        for u, code in results:
            if code == 200 or (isinstance(code, int) and code in (401, 403, 429)):
                continue
            bad += 1
            print(f"EXTERNAL {code} {u}  ({len(ext[u])} pages, e.g. {sorted(ext[u])[0]})")
        print(f"{bad} external links need a look")
    sys.exit(1 if broken else 0)


if __name__ == "__main__":
    main()
