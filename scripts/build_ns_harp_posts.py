#!/usr/bin/env python3
"""Build the two Nova Scotia HARP blog posts from data/blog-new/<slug>.json,
cloning the page chrome (nav, footer, styles) from an existing blog post.
Fields: title, desc, h1, crumb, lead, callout, sections [[h2, html]], faq [[q, a]], refs [[text, url]], published, updated, read.
Usage: python3 scripts/build_ns_harp_posts.py   (builds every file in data/blog-new)"""
import html, json, re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://homepowerrebate.com"
TEMPLATE = ROOT / "blog/nova-scotia-heat-pump-rebate-disappeared/index.html"


def ld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, indent=1, ensure_ascii=False) + "\n</script>\n"


def build(path):
    d = json.loads(path.read_text())
    slug = path.stem
    url = f"{BASE}/blog/{slug}/"
    e = html.escape
    t = TEMPLATE.read_text(encoding="utf-8")
    nice = date.fromisoformat(d["updated"]).strftime("%B %-d, %Y")
    t = re.sub(r"<title>.*?</title>", f"<title>{e(d['title'])}</title>", t, count=1, flags=re.S)
    for pat, val in [(r'(name="description" content=")[^"]*', d["desc"]), (r'(property="og:title" content=")[^"]*', d["title"]),
                     (r'(property="og:description" content=")[^"]*', d["desc"])]:
        t = re.sub(pat, lambda m: m.group(1) + e(val, quote=True), t, count=1)
    t = t.replace("https://homepowerrebate.com/blog/nova-scotia-heat-pump-rebate-disappeared/", url)
    # swap all JSON-LD blocks in the head for ours
    t = re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>\s*', "", t)
    person = {"@type": "Person", "name": "Sam Menard", "url": f"{BASE}/about"}
    blog = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": d["h1"], "description": d["desc"],
            "datePublished": d["published"], "dateModified": d["updated"], "author": person,
            "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE + "/"}, "mainEntityOfPage": url}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": BASE + "/blog"},
        {"@type": "ListItem", "position": 3, "name": d["crumb"], "item": url}]}
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", html.unescape(a))}} for q, a in d["faq"]]}
    t = t.replace("</head>", ld(blog) + ld(crumbs) + ld(faq) + "</head>", 1)
    t = re.sub(r'(<li aria-current="page">).*?(</li>)', lambda m: m.group(1) + e(d["crumb"]) + m.group(2), t, count=1)
    hero = (f'<section class="hero">\n  <div class="wrap">\n    <h1>{e(d["h1"])}</h1>\n    <p>{d["lead"]}</p>\n'
            f'    <p class="meta">By <a href="/about" style="color:inherit;text-decoration:underline;">Sam Menard</a> &middot; Updated {nice} &middot; {d["read"]} min read</p>\n  </div>\n</section>')
    t = re.sub(r'<section class="hero">[\s\S]*?</section>', lambda m: hero, t, count=1)
    body = f'<div class="callout">{d["callout"]}</div>\n'
    body += "".join(f"<h2>{h}</h2>\n{b}\n" for h, b in d["sections"])
    body += "<h2>Common questions</h2>\n" + "".join(f"<h3>{e(q)}</h3>\n<p>{a}</p>\n" for q, a in d["faq"])
    body += "<h2>Related reading</h2>\n<ul>\n" + "".join(f'<li><a href="{u}">{x}</a></li>\n' for x, u in d["related"]) + "</ul>\n"
    body += f'<p style="font-size:13px; color:var(--ink-soft); margin-top:32px;">Sources, read {nice}: ' + ", ".join(
        f'<a href="{e(u)}" target="_blank" rel="noopener">{e(x)}</a>' for x, u in d["refs"]) + ".</p>\n"
    t = re.sub(r'(<article class="article">\s*<div class="wrap">)[\s\S]*?(</div>\s*</article>)', lambda m: m.group(1) + "\n" + body + "\n  " + m.group(2), t, count=1)
    out = ROOT / "blog" / slug
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(t, encoding="utf-8")
    print("built", slug)


if __name__ == "__main__":
    for p in sorted((ROOT / "data/blog-new").glob("nova-scotia-*.json")):
        build(p)
