#!/usr/bin/env python3
"""Put the LEARN blocks (guide cards, tips, quiz) on pages (2026-10-23, widened the same day).
- Installer ranking pages: "How to read these results" tips, then the card row, right before the closing "See every rebate" box.
- Region hubs (/ca/<r>/, /us/<r>/), city hubs and city category pages, region topic pages (/ca/<r>/<topic>/) and /programs/<slug>/:
  the card row (and, for BC and Ontario pages, one quiz), placed above the shared footer with navfooter.content_insert_point.
Cards come from data/learn/*.json (learn_kit.pick: articles tagged for the page's service first, rotated by page path). A quiz is added only where
the article's quiz_regions includes the page's region (the questions state BC and Ontario rules): region hubs, city hubs and heat pump pages.
Everything sits between LEARN-START/END markers so re-runs replace it. Advisor and auditor ranking pages get nothing.
Styles and the quiz script are in _partials/nav-footer.html (shared CSS/JS).
Usage: python3 scripts/add_learn_blocks.py"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import learn_kit as lk  # noqa: E402

S, E = "<!-- LEARN-START -->", "<!-- LEARN-END -->"
ANCHOR = '<div class="cta"><h3>See every rebate in'
SKIP = {"energy-advisor", "energy-auditor"}
OLD = re.compile(re.escape(S) + r"[\s\S]*?" + re.escape(E) + r"\n?")
SERVICES = {"heat-pump", "solar", "battery"}
# pages that sit just under the 90% near-duplicate limit: a row of identical card text pushed BC solar pages over it (check_duplicate_content.py)
NO_ROW = {("bc", "solar")}
QUIZ_PAGES = {"index", "heat-pump"}  # hubs, city hubs and heat pump pages carry a quiz (BC and Ontario only)


def place(f, t, block):
    """Replace any old block, then insert the new one; returns the new text or None when the page has no place for it."""
    t2 = OLD.sub("", t)
    if "<footer" not in t2 and navfooter.FOOTER_MARKER_START not in t2:
        return None
    i = navfooter.content_insert_point(t2)
    return t2[:i] + block + t2[i:]


def quiz_for(region, kind, service, key):
    """The one quiz for a page: the heat pump myths quiz on heat pump pages, otherwise the rebate-mistakes quiz."""
    if kind not in QUIZ_PAGES:
        return ""
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
        block = f"{S}\n{lk.tips('installer')}\n{lk.not_ready_row(service, key=str(f))}\n{E}\n"
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
    return out


def wide():
    n = 0
    for f, region, kind, service in pages():
        t = f.read_text(encoding="utf-8")
        if "<footer" not in t and navfooter.FOOTER_MARKER_START not in t:
            continue
        if (region, kind) in NO_ROW:
            t2 = OLD.sub("", t)
            if t2 != t:
                f.write_text(t2, encoding="utf-8")
                n += 1
            continue
        if kind == "program":
            heading, sub = "Learn the rules before you apply", "Short reads and quick quizzes on how rebate programs work."
        else:
            heading, sub = "Not ready to talk to a contractor yet?", "Short reads and quick quizzes. Learn the rules first, then call."
        body = lk.not_ready_row(service, key=str(f), heading=heading, sub=sub) + quiz_for(region, kind, service, str(f))
        block = f'{S}\n<div class="learn-wrap">{body}</div>\n{E}\n'
        t2 = place(f, t, block)
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
