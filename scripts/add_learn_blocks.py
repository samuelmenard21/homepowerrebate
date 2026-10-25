#!/usr/bin/env python3
"""Put the LEARN blocks (guide cards, tips, quiz) on pages (2026-10-23, widened the same day).
- Installer ranking pages: "How to read these results" tips, then the card row, right before the closing "See every rebate" box.
- Region hubs (/ca/<r>/, /us/<r>/), city hubs and city category pages, region topic pages (/ca/<r>/<topic>/) and /programs/<slug>/:
  the card row (and, for BC and Ontario pages, one quiz), placed above the shared footer with navfooter.content_insert_point.
Cards come from data/learn/*.json (learn_kit.pick: articles tagged for the page's service first, rotated by page path). A quiz is added only where
the article's quiz_regions includes the page's region (the questions state BC and Ontario rules): region hubs, city hubs and heat pump pages.
Region hubs outside BC and Ontario get a quiz built from their verified amounts (learn_kit.region_quiz). Everything sits between LEARN-START/END markers so re-runs replace it. Advisor and auditor ranking pages get nothing.
Styles and the quiz script are in _partials/nav-footer.html (shared CSS/JS).
Usage: python3 scripts/add_learn_blocks.py"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import learn_kit as lk  # noqa: E402
import regions  # noqa: E402

S, E = "<!-- LEARN-START -->", "<!-- LEARN-END -->"
QS, QE = "<!-- LEARN-QUIZ-START -->", "<!-- LEARN-QUIZ-END -->"
QOLD = re.compile(r"\n?" + re.escape(QS) + r"[\s\S]*?" + re.escape(QE))
ANCHOR = '<div class="cta"><h3>See every rebate in'
SKIP = {"energy-advisor", "energy-auditor"}
OLD = re.compile(re.escape(S) + r"[\s\S]*?" + re.escape(E) + r"\n?")
SERVICES = {"heat-pump", "solar", "battery"}
# pages that sit just under the 90% near-duplicate limit: a row of identical card text pushed BC solar pages over it (check_duplicate_content.py)
NO_ROW = {("bc", "solar"), ("on", "index")}  # ("on", "index") means Ontario city hubs; the region hub keeps its row
QUIZ_PAGES = {"index", "heat-pump"}  # hubs, city hubs and heat pump pages carry a quiz (BC and Ontario only)


def place(f, t, block):
    """Replace any old block, then insert the new one; returns the new text or None when the page has no place for it."""
    t2 = OLD.sub("", t)
    if "<footer" not in t2 and navfooter.FOOTER_MARKER_START not in t2:
        return None
    i = navfooter.content_insert_point(t2)
    j = t2.find("<!-- DISCOVERED-LINKS-START -->")
    if 0 <= j < i:
        i = j  # same order as a fresh rebuild: learn row, then the related-pages box (link_discovered inserts before the footer)
    return t2[:i] + block + t2[i:]


def quiz_for(region, kind, service, key, region_hub=False):
    """The one quiz for a page: the heat pump myths quiz on heat pump pages, otherwise the rebate-mistakes quiz."""
    if kind not in QUIZ_PAGES or (kind == "index" and not region_hub):
        return ""  # city hubs carry no quiz: the same block on every city hub pushed Ontario hubs over the 90% near-duplicate limit
    if region_hub and region not in ("bc", "on"):
        q = lk.region_quiz(region) if (ROOT / "calculator" / "data" / f"{region}.json").exists() else None
        return lk.quiz(f"{region}-rebates", q) if q else ""
    want = "heat-pump-myths-busted" if service == "heat-pump" else "7-ways-to-lose-your-home-energy-rebate"
    d = lk.articles().get(want)
    if not d or region not in d.get("quiz_regions", []):
        return ""
    return lk.quiz(want, d["quiz"])


def rankings():
    n = 0
    for f in sorted((ROOT / "installers").glob("*/*/*/index.html")):
        service = f.parent.name
        if service in SKIP:
            continue
        t = f.read_text(encoding="utf-8")
        if ANCHOR not in t:
            continue
        t2 = OLD.sub("", t)
        block = f"{S}\n{lk.tips('installer')}\n{lk.not_ready_row(service, key=str(f.relative_to(ROOT)))}\n{E}\n"
        i = t2.index(ANCHOR)
        t2 = t2[:i] + block + t2[i:]
        if t2 != t:
            f.write_text(t2, encoding="utf-8")
            n += 1
    return n


def pages():
    """(file, region, kind, service) for hubs, city hubs, city category pages, region topic pages and program pages."""
    out = []
    for f in sorted(ROOT.glob("ca/*/index.html")) + sorted(ROOT.glob("us/*/index.html")):
        out.append((f, f.parts[-2], "index", "general"))
    for pat in ("ca/*/*/index.html", "us/*/*/index.html"):
        for f in sorted(ROOT.glob(pat)):
            reg, name = f.parts[-3], f.parts[-2]
            if name == "fr":
                continue  # French pages keep their own wording
            out.append((f, reg, "index" if (f.parent / "heat-pump").exists() or name not in SERVICES | {"insulation", "windows-doors", "water-heater"} else name, name if name in SERVICES else "general"))
    for pat in ("ca/*/*/*/index.html", "us/*/*/*/index.html"):
        for f in sorted(ROOT.glob(pat)):
            reg, name = f.parts[-4], f.parts[-2]
            if name == "fr":
                continue
            out.append((f, reg, name, name if name in SERVICES else "general"))
    for f in sorted(ROOT.glob("programs/*/index.html")):
        out.append((f, "", "program", "general"))
    own = set(lk.articles()) | set(h.stem for h in (ROOT / "data" / "learn-hubs").glob("*.json"))
    for f in sorted(ROOT.glob("blog/*/index.html")):
        if f.parent.name not in own:
            slug = f.parent.name
            svc = next((s for k, s in (("heat-pump", "heat-pump"), ("solar", "solar"), ("battery", "battery"), ("insulation", "insulation")) if k in slug), "general")
            out.append((f, "", "blog", svc))
    for f in (ROOT / "energy-advisors" / "index.html", ROOT / "energy-auditors" / "index.html", ROOT / "powerscore" / "index.html", ROOT / "powerscore" / "leaderboard" / "index.html"):
        if f.exists():
            out.append((f, "", "program", "general"))
    for f in sorted(ROOT.glob("questions/*/index.html")):
        out.append((f, "", "question", "general"))
    for f in sorted(ROOT.glob("calculator/*/index.html")):
        if f.parent.name not in ("embed", "data", "widget"):
            out.append((f, "", "calculator", "general"))
    return out


def post_quiz(slug):
    """A quiz for a blog post: the region's own quiz (from its verified amounts) when the post names one region, otherwise a rotating general one."""
    import zlib
    idx = {p["slug"]: p["region"] for s in json.loads((ROOT / "data" / "blog-index.json").read_text(encoding="utf-8"))["sections"] for p in s["posts"]}
    label = idx.get(slug, "Everywhere")
    code = next((r["code"] for r in regions.REGIONS if label in (r["name"], r.get("abbr"))), "")
    if code and code not in ("bc", "on") and (ROOT / "calculator" / "data" / f"{code}.json").exists():
        q = lk.region_quiz(code)
        if q:
            return lk.quiz(f"{code}-rebates", q)
    pick = ("heat-pump-myths-busted", "7-ways-to-lose-your-home-energy-rebate", "9-questions-to-ask-heat-pump-installer")[zlib.crc32(slug.encode()) % 3]
    d = lk.articles()[pick]
    return lk.quiz(pick, d["quiz"])


def wide():
    n = 0
    for f, region, kind, service in pages():
        t = f.read_text(encoding="utf-8")
        if "<footer" not in t and navfooter.FOOTER_MARKER_START not in t:
            continue
        if (region, kind) in NO_ROW and not f.parent.parent.name in ("ca", "us"):
            t2 = QOLD.sub("", OLD.sub("", t))
            if t2 != t:
                f.write_text(t2, encoding="utf-8")
                n += 1
            continue
        if kind in ("program", "blog", "question", "calculator"):
            heading = "Keep learning" if kind in ("blog", "question") else "Learn the rules before you apply"
            sub = "Short reads and quick quizzes on how rebate programs work."
        else:
            heading, sub = "Not ready to talk to a contractor yet?", "Short reads and quick quizzes. Learn the rules first, then call."
        key = str(f.relative_to(ROOT))
        region_hub = f.parent.parent.name in ("ca", "us")
        row = lk.not_ready_row(service, key=key, heading=heading, sub=sub)
        quiz = post_quiz(f.parent.name) if kind == "blog" else quiz_for(region, kind, service, key, region_hub=region_hub)
        # the quiz goes at the top of the page (the most engaging thing); the card row stays at the bottom
        t2 = QOLD.sub("", OLD.sub("", t))
        anchor = next((m for m in ("<!-- HUB-STATS-END -->" if region_hub else "", "<!-- HUB-SEARCH-END -->", "<!-- BLOG-PHOTO-END -->") if m and m in t2), None)
        if quiz and anchor:
            i = t2.index(anchor) + len(anchor)
            t2 = t2[:i] + f"\n{QS}\n<div class=\"learn-wrap\">{quiz}</div>\n{QE}" + t2[i:]
        elif quiz:
            row += quiz  # no top anchor on this page: the quiz sits with the row
        block = f'{S}\n<div class="learn-wrap">{row}</div>\n{E}\n'
        t2 = place(f, t2, block)
        if t2 and t2 != t:
            f.write_text(t2, encoding="utf-8")
            n += 1
    return n


def main():
    r = rankings()
    w = wide()
    print(f"learn blocks: {r} ranking pages, {w} hubs, city, topic and program pages updated")


if __name__ == "__main__":
    main()
