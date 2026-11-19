#!/usr/bin/env python3
"""Reviewed-by line on pages named in data/reviewers.json (post-step, 2026-11-19).

The file is empty on purpose until a registered energy advisor has read a page and agreed to be named; with no entry this
removes any old block and writes nothing. The line goes right after the page's first </h1>, between REVIEWED-BY markers.
Never add a name Sam has not been given permission to show.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARK = ("<!-- REVIEWED-BY-START -->", "<!-- REVIEWED-BY-END -->")
STRIP = re.compile(r"\n?" + re.escape(MARK[0]) + r"[\s\S]*?" + re.escape(MARK[1]) + r"\n?")


def line(r):
    who = html.escape(r["name"])
    if r.get("url"):
        who = f'<a href="{html.escape(r["url"])}" rel="noopener">{who}</a>'
    org = f", {html.escape(r['organization'])}" if r.get("organization") else ""
    return (f'<p class="reviewed-by" style="max-width:880px;margin:10px auto 0;padding:0 20px;font-size:14px;opacity:.85;">'
            f'Reviewed by {who}, {html.escape(r["role"])}{org}, on {html.escape(r["reviewed_on"])}.</p>')


def main():
    pages = json.loads((ROOT / "data" / "reviewers.json").read_text(encoding="utf-8")).get("pages", {})
    n = 0
    for p, r in pages.items():
        f = ROOT / p.strip("/") / "index.html"
        if not f.exists():
            print("missing page", p)
            continue
        t0 = f.read_text(encoding="utf-8")
        t = STRIP.sub("", t0)
        m = re.search(r"</h1>", t)
        if m:
            t = t[:m.end()] + "\n" + MARK[0] + line(r) + MARK[1] + "\n" + t[m.end():]
        if t != t0:
            f.write_text(t, encoding="utf-8")
            n += 1
    print(f"reviewed-by: {len(pages)} pages listed, {n} files changed")


if __name__ == "__main__":
    main()
