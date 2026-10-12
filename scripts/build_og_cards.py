#!/usr/bin/env python3
"""Social share cards: one 1200 x 630 image per page, in the site design, saying what that page actually says.

Each card shows the page's own headline, a one-line key fact taken from the page (a rebate amount badge, a ranking's
company and review counts, an installer's Google rating, a hub's biggest open rebate) and an honest trust line. Nothing
is invented: a page without a clear key fact gets no key line.
Cards are rendered from _partials/og-card.html in headless Chrome (node scripts/og/render.js, then Pillow) and saved
as og/<page path>.jpg; og/manifest.json stores a hash of each card's data so unchanged cards are not re-rendered.
The restamp (apply_canonical_nav_footer.py) points og:image and twitter:image at the card whenever one exists.
Usage: python3 scripts/build_og_cards.py [--only <path prefix>]   (needs node and puppeteer-core, see scripts/og/)"""
import hashlib
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as nf  # noqa: E402

OG = ROOT / "og"
TRUST = {
    "profile": "Ratings from Google Maps · Rankings never paid for",
    "ranking": "Ranked by Google reviews · Never paid for · Free",
    "default": "Free · Every amount links to the official program",
}


def text(s):
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()
    return re.sub(r" ([.,!?;:])", r"\1", t)  # "your <em>rebate</em>." must not read "rebate ."


def first(pattern, s, flags=re.S):
    m = re.search(pattern, s, flags)
    return text(m.group(1)) if m else ""


def card_path(url_path):
    p = url_path.strip("/")
    p = re.sub(r"\.html$", "", p)
    return f"og/{p or 'home'}.jpg"


def page_data(rel, s):
    cm = nf.CANON_RE.search(s)
    path = cm.group(1) if cm else "/" + rel.replace("index.html", "")
    fam = (re.search(r'<body[^>]*class="[^"]*\btpl-([a-z]+)', s) or [None, "page"])[1]
    h1 = first(r"<h1\b[^>]*>(.*?)</h1>", s)
    nav = re.search(r'<nav class="hpr-breadcrumb".*?</nav>', s, re.S)
    crumbs = [text(x) for x in re.findall(r"<li[^>]*>(.*?)</li>", nav.group(0))] if nav else []
    eyebrow, key, trust = "", "", TRUST["default"]
    if fam == "profile":
        meta = first(r'class="ip-hero-meta">(.*?)</p>', s)
        rating = first(r'class="ip-rating-num">(.*?)</div>', s)
        count = first(r'class="ip-rating-count">(.*?)</div>', s)
        eyebrow = meta
        key = f"{rating} from {count}" if rating and count else ""
        trust = TRUST["profile"]
    elif fam == "ranking":
        stats = dict((text(b2), text(b1)) for b1, b2 in re.findall(r'<div class="stat"><b>(.*?)</b><span>(.*?)</span></div>', s))
        n, rv = stats.get("Companies"), stats.get("Google reviews")
        key = f"{n} local companies ranked by {rv} Google reviews" if n and rv else ""
        eyebrow = " · ".join(crumbs[-2:]) if len(crumbs) >= 2 else "Top-rated installers"
        trust = TRUST["ranking"]
    elif fam == "hub":
        eyebrow = first(r'<header class="hero hub-hero"><div class="wrap"><div class="eyebrow">(.*?)</div>', s)
        big = re.search(r'<div class="hs-stat"><b>([^<]*)<small>([^<]*)</small></b><span>biggest single rebate</span>', s)
        key = f"Biggest open rebate: {text(big.group(1))} ({text(big.group(2)).lower()})" if big else ""
    elif 'class="ps-gap"' in s:  # /powerscore/: the rebate gap, best region vs lowest
        gap = re.findall(r'<span class="ps-gap-name">(.*?)</span>.*?<b>(\d+)</b>', s, re.S)
        n = first(r'Three things we learned scoring (\d+) cities', s)
        if len(gap) >= 2:
            key = f"{text(gap[0][0])} {gap[0][1]} vs {text(gap[-1][0])} {gap[-1][1]}, average PowerScore"
        eyebrow = f"PowerScore · {n} cities ranked" if n else "PowerScore"
    else:
        badge = first(r'class="amount-badge">(.*?)</div>', s)
        key = badge if badge and len(badge) <= 70 else ""
        if len(crumbs) >= 3:
            eyebrow = " · ".join(crumbs[1:-1][-2:])
        elif len(crumbs) == 2:
            eyebrow = crumbs[0] if crumbs[0] != "Home" else ""
        if fam == "home":
            eyebrow = "Canada and the United States"
    if not h1:
        h1 = first(r"<title>(.*?)</title>", s)
    return {"path": path, "out": card_path(path), "family": fam, "eyebrow": eyebrow[:80], "title": h1[:140], "key": key[:90], "trust": trust}


def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else ""
    man_path = OG / "manifest.json"
    manifest = json.loads(man_path.read_text()) if man_path.exists() else {}
    todo, keep = [], set()
    for rel in subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "*.html"], text=True).split():
        if rel.startswith(("_partials/", "scripts/", "data/", "drafts/")):
            continue
        s = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
        if "CANONICAL-NAV-START" not in s or "calculator/embed/" in rel:
            continue
        d = page_data(rel, s)
        if d["out"] in keep:  # two files for one URL (an old .html copy beside the folder page): one card
            continue
        keep.add(d["out"])
        if only and not d["path"].startswith(only):
            continue
        h = hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()[:12]
        if manifest.get(d["out"]) == h and (ROOT / d["out"]).exists():
            continue
        d["hash"] = h
        todo.append(d)
    print(f"{len(todo)} cards to render")
    if todo:
        job = ROOT / "og" / ".job.json"
        job.parent.mkdir(exist_ok=True)
        job.write_text(json.dumps(todo))
        subprocess.run(["node", str(ROOT / "scripts" / "og" / "render.js"), str(job), str(ROOT)], check=True)
        job.unlink()
        from PIL import Image
        for d in todo:  # Chrome renders PNG; an optimised progressive JPEG is about half the size of Chrome's own
            png = ROOT / d["out"].replace(".jpg", ".png")
            Image.open(png).convert("RGB").save(ROOT / d["out"], "JPEG", quality=62, optimize=True, progressive=True)
            png.unlink()
            manifest[d["out"]] = d["hash"]
    for k in [k for k in manifest if k not in keep]:  # pages that no longer exist
        manifest.pop(k)
        (ROOT / k).unlink(missing_ok=True)
    man_path.write_text(json.dumps(manifest, indent=0, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
