#!/usr/bin/env python3
"""Rewrite a blog post's text from data/blog-refresh/<slug>.json while keeping the page's chrome (nav, footer, styles).
Fields: title, desc, h1, lead, sections [[h2, html]], faq [[q, a]], refs [[text, url]], updated (ISO date).
Usage: python3 scripts/refresh_blog_post.py <slug> [<slug> ...]   (no arguments = every file in data/blog-refresh)"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://homepowerrebate.com"
CSS = "<style>.faq-item{border-bottom:1px solid #d9d0c1;padding:14px 0}.faq-item h3{margin:0 0 6px;font-size:18px}.faq-item p{margin:0}.byline{font-size:14px;color:#5a5348;margin:0 0 16px}</style>"


def apply(slug):
    d = json.loads((ROOT / "data/blog-refresh" / f"{slug}.json").read_text())
    p = ROOT / "blog" / slug / "index.html"
    t = p.read_text(encoding="utf-8")
    e = html.escape
    upd = d["updated"]
    nice = date.fromisoformat(upd).strftime("%B %-d, %Y")
    t = re.sub(r"<title>.*?</title>", f"<title>{e(d['title'])}</title>", t, count=1, flags=re.S)
    for pat, val in [(r'(name="description" content=")[^"]*', d["desc"]), (r'(property="og:title" content=")[^"]*', d["title"]), (r'(property="og:description" content=")[^"]*', d["desc"]),
                     (r'(name="twitter:title" content=")[^"]*', d["title"]), (r'(name="twitter:description" content=")[^"]*', d["desc"])]:
        t = re.sub(pat, lambda m: m.group(1) + e(val), t, count=1)
    t = re.sub(r'(<li aria-current="page">).*?(</li>)', lambda m: m.group(1) + e(d["h1"]) + m.group(2), t, count=1)
    t = re.sub(r"(<section class=\"hero\">\s*<div class=\"wrap\">\s*)<h1>.*?</h1>\s*<p>.*?</p>", lambda m: m.group(1) + f"<h1>{e(d['h1'])}</h1>\n    <p>{d['lead']}</p>", t, count=1, flags=re.S)
    body = f'<p class="byline">By <a href="/about">Sam Menard</a> · Updated {nice}</p>\n'
    body += "".join(f"<h2>{h}</h2>\n{b}\n" for h, b in d["sections"])
    if d.get("faq"):
        body += "<h2>Common questions</h2>\n" + "".join(f'<div class="faq-item"><h3>{e(q)}</h3><p>{a}</p></div>\n' for q, a in d["faq"])
    if d.get("refs"):
        body += "<p style=\"font-size:14px;\">Sources, read " + nice + ": " + ", ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(x)}</a>' for x, u in d["refs"]) + ".</p>\n"
    t = re.sub(r'(<article class="article">\s*<div class="wrap">).*?(</div>\s*</article>)', lambda m: m.group(1) + "\n" + body + "\n  " + m.group(2), t, count=1, flags=re.S)
    t = re.sub(r'<script type="application/ld\+json">\{[^<]*?"@type": ?"(?:Article|FAQPage)"[\s\S]*?</script>\s*', "", t)
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": d["h1"], "description": d["desc"], "datePublished": d.get("published", upd), "dateModified": upd,
           "author": {"@type": "Person", "@id": f"{BASE}/#sam", "name": "Sam Menard", "url": f"{BASE}/about"}, "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
           "mainEntityOfPage": f"{BASE}/blog/{slug}/"}]
    if d.get("faq"):
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", html.unescape(a))}} for q, a in d["faq"]]})
    scripts = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    t = t.replace("</head>", (CSS if ".byline{" not in t else "") + scripts + "\n</head>", 1)
    p.write_text(t, encoding="utf-8")
    print("refreshed", slug)


if __name__ == "__main__":
    slugs = sys.argv[1:] or [f.stem for f in sorted((ROOT / "data/blog-refresh").glob("*.json"))]
    for s in slugs:
        apply(s)
