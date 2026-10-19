#!/usr/bin/env python3
"""Site-wide SEO clean-up that generators do not do themselves. Run after the generators, before link steps (see CLAUDE.md). Safe to re-run.
1. og:image points at og-image.jpg (Facebook, LinkedIn and X do not render SVG).
2. Article authorship: JSON-LD author "HomePowerRebate" (Organization) becomes Sam Menard (Person, same @id as the About page).
3. Titles on indexable pages: drop the " | HomePowerRebate" suffix when the title is longer than 60 characters, trim very long ones at the colon,
   and add the state or province when two cities share a name (Kingston, Burlington, Cambridge).
4. Installer profile pages: remove AggregateRating built from Google Maps ratings (Google allows review markup only for reviews collected on your own site)."""
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import regions
ROOT = Path(__file__).resolve().parent.parent
SKIP = ("_partials/", "scripts/", "claude/", "calculator/embed/", "data/", "ONTARIO_", "CITY_", "city-page", "installer-", "pinterest", "unified", "solar-carousel", "og-image", "preview", "nav-footer", "node_modules")
REGION = regions.ABBR_BY_PATH
AUTHOR = '"author": {"@type": "Person", "@id": "https://homepowerrebate.com/about#sam-menard", "name": "Sam Menard", "url": "https://homepowerrebate.com/about"}'
AUTHOR_RE = re.compile(r'"author":\s*\{\s*"@type":\s*"Organization",\s*"name":\s*"HomePowerRebate"(?:,\s*"url":\s*"[^"]*")?\s*\}')
RATING_RE = re.compile(r',?\s*"aggregateRating":\s*\{[^{}]*\}|,?\s*"AggregateRating":\s*\{[^{}]*\}', re.I)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
SUFFIX = " | HomePowerRebate"


def fit_title(t, limit=60):
    """Longest prefix of t that fits: cut at a colon, then at the last comma/dash/"and" clause, then at a word."""
    import html as _h
    plain = _h.unescape(t)
    if len(plain) <= limit:
        return t
    for sep in (":", " | ", " - "):
        if sep in plain:
            head, tail = plain.split(sep, 1)
            out = head
            for clause in re.split(r",\s*|\s+and\s+", tail.strip()):
                nxt = f"{head}: {clause}" if out == head else f"{out}, {clause}"
                if len(nxt) <= limit:
                    out = nxt
                else:
                    break
            if len(out) <= limit and len(out) > len(head) - 1:
                return _h.escape(out, quote=False)
            break
    cut = plain[:limit].rsplit(" ", 1)[0].rstrip(" ,:;-&")
    return _h.escape(cut, quote=False)


DESC_RE = re.compile(r'(<meta name="description" content=")([^"]*)(")')


def fit_desc(d, limit=160):
    import html as _h
    plain = _h.unescape(d)
    if len(plain) <= limit:
        return d
    cut = plain[:limit]
    m = max(cut.rfind(". "), cut.rfind("; "))
    if m >= 90:
        cut = cut[: m + 1]
    else:
        cut = cut[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,:;-&") + "."
    return _h.escape(cut, quote=True)


def shorten(t):
    if len(t) <= 60 or not t.endswith(SUFFIX):
        return fit_title(t)
    base = t[: -len(SUFFIX)]
    if len(base) <= 62 or ":" not in base:
        return fit_title(base)
    head, tail = base.split(":", 1)
    clause = tail.strip().split(",")[0].strip()
    return fit_title(f"{head}: {clause}" if len(head) + 2 + len(clause) <= 62 else head)


files = [f for f in subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True).stdout.split() if not f.startswith(SKIP) and (ROOT / f).exists()]
pages = {}
for f in files:
    s = (ROOT / f).read_text(encoding="utf-8", errors="ignore")
    pages[f] = s
changed = defaultdict(int)
titles = defaultdict(list)
for f, s in pages.items():
    o = s
    s = s.replace('og:image" content="https://homepowerrebate.com/og-image.svg"', 'og:image" content="https://homepowerrebate.com/og-image.jpg"').replace('og:image:type" content="image/svg+xml"', 'og:image:type" content="image/jpeg"')
    if s != o:
        changed["og"] += 1
    o2 = s
    s = AUTHOR_RE.sub(AUTHOR, s).replace('"https://homepowerrebate.com/#sam"', '"https://homepowerrebate.com/about#sam-menard"')  # one Person @id site-wide
    if s != o2:
        changed["author"] += 1
    if f.startswith("installers/profiles/") and "aggregaterating" in s.lower():
        n = RATING_RE.sub("", s)
        if n != s:
            s = n
            changed["rating"] += 1
    indexable = "noindex" not in s[:6000] and f != "index.html" and f != "404.html"
    m = TITLE_RE.search(s)
    if m and indexable:
        new = shorten(m.group(1).strip())
        if new != m.group(1).strip():
            s = s[: m.start()] + f"<title>{new}</title>" + s[m.end():]
            changed["title"] += 1
        titles[TITLE_RE.search(s).group(1).strip()].append(f)
    if 'name="twitter:card"' in s and indexable:
        tt, dd = TITLE_RE.search(s), DESC_RE.search(s)
        add = ""
        if tt and 'name="twitter:title"' not in s:
            add += f'<meta name="twitter:title" content="{tt.group(1).strip().replace(chr(34), "&quot;")}">\n'
        if dd and 'name="twitter:description"' not in s:
            add += f'<meta name="twitter:description" content="{dd.group(2)}">\n'
        if add:
            # outside the OG-CARD block: the restamp rewrites that block and would drop them
            at = "<!-- OG-CARD-START -->" if "<!-- OG-CARD-START -->" in s else '<meta name="twitter:card"'
            s = s.replace(at, add + at, 1)
            changed["xcard"] += 1
    if indexable:
        md = DESC_RE.search(s)
        if md and len(md.group(2)) > 160:
            nd = fit_desc(md.group(2))
            if nd != md.group(2):
                s = s[: md.start(2)] + nd + s[md.end(2):]
                changed["desc"] += 1
    pages[f] = s
for t, fs in titles.items():
    if len(fs) < 2:
        continue
    for f in fs:
        reg = next((v for k, v in REGION.items() if f.startswith(k + "/")), None)
        if not reg:
            continue
        parts = f.split("/")
        city = parts[parts.index(next(p for p in parts if p == "index.html")) - 1] if parts[-1] == "index.html" else parts[-2]
        s = pages[f]
        cands = [p for p in parts[:-1] if p not in regions.region_dirs_exclusion()]
        name = next((p.replace("-", " ").title() for p in cands if p.replace("-", " ").title() in t), None)
        if name:
            nt = t.replace(name, f"{name}, {reg}", 1)
        else:
            nt = t.replace(SUFFIX, f" ({reg}){SUFFIX}") if t.endswith(SUFFIX) else t + f" ({reg})"
        s = TITLE_RE.sub(f"<title>{nt}</title>", s, count=1)
        pages[f] = s
        changed["dup"] += 1
for f, s in pages.items():
    p = ROOT / f
    if p.read_text(encoding="utf-8", errors="ignore") != s:
        p.write_text(s, encoding="utf-8")
print(dict(changed))
