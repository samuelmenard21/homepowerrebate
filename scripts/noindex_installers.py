#!/usr/bin/env python3
"""Mark every page under the prefixes in data/noindex-sections.json as `noindex, follow` (post-step, 2026-11-08).

Why: see `_why` in the JSON. The pages stay live and keep passing link value (`follow`); generate_sitemap.py drops noindex
pages on its own. Idempotent. To bring a section back, remove its prefix (or add the page to `keep_indexed`) and rebuild
the pages with their generator (this script only ever adds noindex, it never removes it).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "data" / "noindex-sections.json").read_text(encoding="utf-8"))
ROBOTS = re.compile(r'<meta\s+name="robots"\s+content="([^"]*)"\s*/?>', re.I)
NOINDEX = '<meta name="robots" content="noindex, follow">'


def main() -> int:
    changed = 0
    for prefix in CFG["prefixes"]:
        for f in sorted((ROOT / prefix).rglob("*.html")):
            rel = f.relative_to(ROOT).as_posix()
            if any(rel.startswith(k) for k in CFG.get("keep_indexed", [])):
                continue
            h = f.read_text(encoding="utf-8")
            m = ROBOTS.search(h)
            if m:
                if "noindex" in m.group(1).lower():
                    continue
                h = h[:m.start()] + NOINDEX + h[m.end():]
            elif "<head>" in h:  # no robots tag at all: add one
                h = h.replace("<head>", "<head>" + NOINDEX, 1)
            else:
                continue  # fragments and widgets without a head
            f.write_text(h, encoding="utf-8")
            changed += 1
    print(f"{changed} pages set to noindex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
