#!/usr/bin/env python3
"""Critical CSS per stylesheet combination (2026-11-02).

Pages that share the same set of /assets stylesheets (for example site.css + a ranking variant) show the same components in the first
screen. This script samples a few pages of each large combination, asks Chrome which rules style something in the first screen at
390 and 1280 px (scripts/critical_css.js), merges them, and writes _partials/critical/<id>.css plus index.json. The restamp
(apply_canonical_nav_footer.py, ensure_critical_css) inlines that CSS in every page with the same combination and loads the full
files without blocking the first paint. If a file is stale the page only paints a little less styled until the full CSS arrives.

  python3 scripts/build_critical_css.py [--min-pages 10] [--samples 5] [--base http://localhost:8888]
Needs a local server on --base serving this folder, puppeteer-core (PUPPETEER_CORE) and Chrome. Re-run after changing shared CSS.
"""
import argparse, collections, hashlib, json, os, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_partials" / "critical"
SKIP = ("node_modules", ".claude", "scripts", "_partials", "embed", "calculator/embed")
LINK_RE = re.compile(r'<link rel="stylesheet" href="(/assets/[^"?]+)')


BODY_LINKED = set()


def signatures():
    sig = collections.defaultdict(list)
    for p in sorted(ROOT.rglob("*.html")):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith(SKIP) or "/embed/" in rel:
            continue
        try:
            h = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "<html" not in h or "</head>" not in h:
            continue
        links = tuple(LINK_RE.findall(h))  # whole page: a few hand-assembled pages link a second variant in the body
        if links:
            sig[links].append(rel)
            if LINK_RE.findall(h.split("</head>", 1)[1]):
                BODY_LINKED.add(links)
    return sig


def sig_id(links):
    return hashlib.sha1("|".join(links).encode()).hexdigest()[:10]


def url_of(rel):
    return "/" + rel[:-len("index.html")] if rel.endswith("index.html") else "/" + rel


def pick(pages, n):
    """The shallowest page (index and hub pages differ from leaf pages) plus pages spread through the sorted list."""
    top = min(pages, key=lambda r: (r.count("/"), r))
    if len(pages) <= n:
        return pages
    spread = [pages[round(i * (len(pages) - 1) / (n - 2))] for i in range(n - 1)]
    return list(dict.fromkeys([top] + spread))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-pages", type=int, default=10)
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--base", default="http://localhost:8888")
    ap.add_argument("--update", action="store_true", help="only combinations with a stylesheet link in the body; keep the other files")
    ap.add_argument("--sig", help="only the combination whose id starts with this (implies --update)")
    ap.add_argument("--extra", default="", help="comma-separated page paths (relative, e.g. blog/x/index.html) added to every sampled combination that contains them")
    ap.add_argument("--like", help="only combinations with a stylesheet whose path contains this (implies --update)")
    ap.add_argument("--reuse", help="reuse a saved capture json instead of running Chrome")
    a = ap.parse_args()
    sys.path.insert(0, str(ROOT / "scripts"))
    from apply_canonical_nav_footer import minify_css
    allsigs = signatures()
    sigs = {k: v for k, v in allsigs.items() if len(v) >= a.min_pages or "/assets/fam/home.css" in k or any("hub" in l for l in k)}
    if a.like:
        a.update = True
        sigs = {k: v for k, v in allsigs.items() if any(a.like in l for l in k)}
    elif a.sig:
        a.update = True
        sigs = {k: v for k, v in allsigs.items() if sig_id(k).startswith(a.sig)}
    elif a.update:
        sigs = {k: v for k, v in allsigs.items() if k in BODY_LINKED}
    samples = {k: pick(v, a.samples * 2 if len(v) >= 100 else a.samples) for k, v in sigs.items()}
    extra = [x for x in a.extra.split(",") if x]
    for k, v in sigs.items():
        samples[k] = list(dict.fromkeys(samples[k] + [x for x in extra if x in v]))
    paths = sorted({url_of(r) for v in samples.values() for r in v})
    cap = Path(a.reuse) if a.reuse else Path(tempfile.gettempdir()) / "critical-capture.json"
    if not a.reuse:
        print(f"{len(sigs)} combinations, {len(paths)} sample pages")
        subprocess.run(["node", str(ROOT / "scripts" / "critical_css.js"), a.base, str(cap)] + paths, check=True)
    data = json.loads(cap.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    index = json.loads((OUT / "index.json").read_text()) if a.update and (OUT / "index.json").exists() else {}
    if not a.update:
        for old in OUT.glob("*.css"):
            old.unlink()
    for links, pages in sigs.items():
        order = {l: i for i, l in enumerate(links)}
        items = {}
        for r in samples[links]:
            for e in data.get(url_of(r), []):
                if e["s"] not in order:
                    continue
                items[(e["s"], tuple(e["i"]), tuple(e["m"]))] = e
        kept = sorted(items.values(), key=lambda e: (order[e["s"]], e["i"]))
        body = "".join(e["t"] for e in kept if not e.get("kf"))
        css, wrap = [], None
        for e in kept:
            if e.get("kf"):
                if e["kf"] in body:
                    css.append(e["t"])
                continue
            m = tuple(e["m"])
            if m != wrap:
                if wrap:
                    css.append("}" * len(wrap))
                css.extend(f"{c}{{" for c in m)
                wrap = m
            css.append(e["t"])
        if wrap:
            css.append("}" * len(wrap))
        text = minify_css("".join(css)).strip()
        sid = sig_id(links)
        (OUT / f"{sid}.css").write_text(text + "\n", encoding="utf-8")
        index[sid] = {"links": list(links), "pages": len(pages), "bytes": len(text)}
        print(f"{sid}  {len(pages):5d} pages  {len(text):6d} bytes  {[l.split('/')[-1] for l in links]}")
    (OUT / "index.json").write_text(json.dumps(index, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
