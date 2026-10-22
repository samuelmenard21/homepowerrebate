#!/usr/bin/env python3
"""Reciprocal hreflang for French pages: puts the French alternate (and x-default) into the head of each English counterpart.

Reads the same files as build_fr_pages.py (path = French URL, en = English URL). The block sits between HREFLANG-START and
HREFLANG-END markers so a re-run replaces it. An English page that already carries hreflang outside the markers (the older
/ca/qc/heat-pump/ page) is left alone. Idempotent; a post-step, so it survives any rebuild of the English page.
Usage: python3 scripts/add_hreflang.py"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_fr_pages  # noqa: E402

BASE = "https://homepowerrebate.com"
S, E = "<!-- HREFLANG-START -->", "<!-- HREFLANG-END -->"


def main():
    changed = 0
    for src in build_fr_pages.sources():
        d = json.loads(src.read_text())
        page = ROOT / d["en"].strip("/") / "index.html"
        if not page.exists():
            print("missing English page", d["en"])
            continue
        t = page.read_text(encoding="utf-8")
        t = re.sub(r"\n?" + re.escape(S) + r".*?" + re.escape(E), "", t, flags=re.S)
        if re.search(r"<link[^>]+hreflang", t):  # a head alternate only: the visible "Version française" link also has an hreflang attribute
            page.write_text(t, encoding="utf-8")  # already has its own pair
            continue
        block = (f'\n{S}<link rel="alternate" hreflang="en-CA" href="{BASE}{d["en"]}"><link rel="alternate" hreflang="fr-CA" href="{BASE}{d["path"]}">'
                 f'<link rel="alternate" hreflang="x-default" href="{BASE}{d["en"]}">{E}')
        t = t.replace("</head>", block + "\n</head>", 1)
        page.write_text(t, encoding="utf-8")
        changed += 1
    print("hreflang added to", changed, "English pages")


if __name__ == "__main__":
    main()
