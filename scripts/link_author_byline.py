#!/usr/bin/env python3
"""Point every "Sam Menard" byline and author URL at the author page (post-step, 2026-11-19).

Generators and the shared footer already write /author/sam-menard/; this catches older text and any generator that still
writes /about, so the author page is the one place a byline goes. Replaces `href="/about"...>Sam Menard` links and the
`"url": "https://homepowerrebate.com/about"` of a Person named Sam Menard in JSON-LD. The About page itself is left alone.
Idempotent.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUTHOR = "/author/sam-menard/"
LINK = re.compile(r'(href=")/about("[^>]*>Sam Menard</a>)')
LD = re.compile(r'("name": ?"Sam Menard", ?"url": ?")https://homepowerrebate\.com/about(")')
SKIP = {"about.html", "author"}


def main():
    n = 0
    for f in ROOT.rglob("*.html"):
        rel = f.relative_to(ROOT)
        if rel.parts[0] in {"node_modules", "scripts", "dist", "_partials", ".claude"} or rel.as_posix() in SKIP or rel.parts[0] == "author":
            continue
        t = f.read_text(encoding="utf-8")
        if "Sam Menard" not in t:
            continue
        u = LD.sub(lambda m: m.group(1) + "https://homepowerrebate.com" + AUTHOR + m.group(2), LINK.sub(lambda m: m.group(1) + AUTHOR + m.group(2), t))
        if u != t:
            f.write_text(u, encoding="utf-8")
            n += 1
    print(f"author byline links: {n} files changed")


if __name__ == "__main__":
    main()
