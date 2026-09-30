#!/usr/bin/env python3
"""Check every internal link and canonical in the site's HTML. Exit 1 if any are broken.

  python3 scripts/check_links.py            # internal links, canonicals, sitemap entries
  python3 scripts/check_links.py --external [--apply]  # also check external links (network). --apply adds confirmed-dead business links to data/link-fixes.json; program/official ones go to reports/links-to-reverify.md
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
    if path.startswith("/pagefind/"):  # search index is generated at publish time, not stored in the repo
        return True
    if not path or path == "/":
        return True
    rel = path.lstrip("/")
    for c in (ROOT / rel, ROOT / rel / "index.html", ROOT / (rel + ".html")):
        if c.exists():
            return True
    return any(r.match(path) or r.match(path.rstrip("/")) or r.match(path.rstrip("/") + "/") for r in rules)


# Official program sources: a dead link here means the fact needs re-verifying, so it is never auto-removed.
PROTECTED = re.compile(r"\.gov(\.|/|$)|\.gc\.ca|gov\.[a-z]{2}\.ca|\.ca\.gov|novascotia\.ca|ontario\.ca|alberta\.ca|bchydro|fortisbc|efficiencyns|"
                       r"nspower|hydro|energy|electric|utilit|power|nyserda|masssave|sdge|sce\.com|pge\.com|smud|ladwp|epcor|atco|enbridge|"
                       r"saveonenergy|cleanbc|betterhomes|irs\.gov|dsire|energystar|cityof|town|county|region|\.ca/programs", re.I)
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
     "Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-CA,en;q=0.9"}


def probe(u):
    import requests
    try:
        r = requests.get(u, allow_redirects=True, timeout=15, stream=True, headers=H)
        return r.status_code
    except Exception as e:
        return type(e).__name__


def external_check(ext):
    """Two independent checks. Confirmed-dead links to businesses are added to data/link-fixes.json (removed at publish
    time); dead links to official/program sources go to reports/links-to-reverify.md for a human."""
    import json
    from concurrent.futures import ThreadPoolExecutor
    urls = sorted(ext)
    with ThreadPoolExecutor(48) as ex:
        first = dict(zip(urls, ex.map(probe, urls)))
        suspect = [u for u in urls if first[u] not in (200, 202, 401, 403, 429)]
        second = dict(zip(suspect, ex.map(probe, suspect)))
    dead = [u for u in suspect if second[u] not in (200, 202, 401, 403, 429)]
    hard = [u for u in dead if second[u] in (404, 410) or first[u] in (404, 410) or "Connection" in str(second[u]) or "SSL" in str(second[u])]
    auto = [u for u in hard if not PROTECTED.search(urlparse(u).netloc + urlparse(u).path)]
    review = [u for u in dead if u not in auto]
    fx = ROOT / "data" / "link-fixes.json"
    data = json.loads(fx.read_text()) if fx.exists() else {"replace": {}, "remove": []}
    new = [u for u in auto if u not in data["remove"] and u not in data["replace"]]
    if "--apply" in sys.argv and new:
        data["remove"] = sorted(set(data["remove"]) | set(new))
        fx.write_text(json.dumps(data, indent=1))
    rep = ROOT / "reports" / "links-to-reverify.md"
    rep.parent.mkdir(exist_ok=True)
    rep.write_text("# Dead links to official or program sources: re-verify the fact, then fix or replace the link\n\n" + "\n".join(
        f"- {second.get(u, first[u])} {u} ({len(ext[u])} pages, e.g. {sorted(ext[u])[0]})" for u in review) + "\n")
    print(f"{len(urls)} external links; {len(dead)} dead after two checks; {len(new)} business links "
          f"{'added to data/link-fixes.json (removed at publish)' if '--apply' in sys.argv else 'would be removed (use --apply)'}; "
          f"{len(review)} program/official links listed in reports/links-to-reverify.md")


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
        external_check(ext)
    sys.exit(1 if broken else 0)


if __name__ == "__main__":
    main()
