#!/usr/bin/env python3
"""A photo on every blog post (2026-10-24): one free-licence Unsplash photo chosen by the post's topic (learn_kit.photo_for), credited under it.
Placed at the top of the article body (after the opening <article> and its wrap), or right after the hero when a post has no <article>.
The same choice feeds the card on /blog/ (build_blog_index.py). Marker-wrapped (BLOG-PHOTO-START/END), idempotent, a post-step.
Learn articles carry their own photo and are skipped.
Usage: python3 scripts/add_blog_photos.py"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import learn_kit as lk  # noqa: E402

S, E = "<!-- BLOG-PHOTO-START -->", "<!-- BLOG-PHOTO-END -->"
OLD = re.compile(r"\n?" + re.escape(S) + r"[\s\S]*?" + re.escape(E))


def main():
    own = set(lk.articles())
    n = 0
    for f in sorted((ROOT / "blog").glob("*/index.html")):
        slug = f.parent.name
        if slug in own:
            continue
        t = f.read_text(encoding="utf-8")
        t2 = OLD.sub("", t)
        h1 = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", t2)
        title = re.sub(r"<[^>]+>", "", h1.group(1)) if h1 else ""
        fig = lk.post_figure(slug, title)
        block = f"{S}{fig}{E}"
        m = re.search(r"<article\b[^>]*>(\s*<div class=\"wrap\"[^>]*>)?", t2)
        if m:
            i = m.end()
        else:
            # no <article>: right after the breadcrumb, or the opening <main> tag
            m = re.search(r"<!-- CANONICAL-BREADCRUMB-END -->|<main\b[^>]*>", t2)
            if not m:
                continue
            i = m.end()
            block = f'{S}<div class="wrap">{fig}</div>{E}'
        t2 = t2[:i] + block + t2[i:]
        if t2 != t:
            f.write_text(t2, encoding="utf-8")
            n += 1
    print(f"blog photos: {n} posts updated")


if __name__ == "__main__":
    main()
