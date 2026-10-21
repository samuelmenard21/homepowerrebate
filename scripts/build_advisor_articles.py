#!/usr/bin/env python3
"""Energy advisor and rebate articles (added 2026-10-20): /blog/<slug>/ from hand-written data/advisors/<slug>.json.
Same fields, quality gate and page layout as the federal series (build_federal_articles.build). Figures must come from
data/verified-facts (the post names its facts) or the post's refs. Add the post to data/blog-index.json, then run
scripts/build_blog_index.py. git add -f data/advisors.
Usage: python3 scripts/build_advisor_articles.py [slug ...]"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_federal_articles as fa  # noqa: E402
import page_kit as kit  # noqa: E402

if __name__ == "__main__":
    only = set(sys.argv[1:])
    for f in sorted((ROOT / "data/advisors").glob("*.json")):
        if only and f.stem not in only:
            continue
        kit.fact_ids({"cards": [], **__import__("json").loads(f.read_text())})  # every named fact must exist
        path, w = fa.build(f.stem, "advisors", pillar=False)
        print("built", path, w, "words")
