#!/usr/bin/env python3
"""Listicle and quiz articles: /blog/<slug>/ from hand-written data/learn/<slug>.json (2026-10-23).
Fields: title, desc, h1, badge, lead, read, takeaways[html], intro (html), list_heading, items [[h3 html, body html]], quote (optional),
quiz {title,intro,qs[{q,options,answer,why}],messages[3],cta}, faq [[q,a]], refs [[text,url]], related [[text,url]], card {tile,tone,kicker,chips},
services[], published, updated. Figures must come from data/verified-facts or the page's refs. Same quality gate as the other article builders.
Usage: python3 scripts/build_learn_articles.py [slug ...]   (git add -f data/learn)"""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_federal_articles as fed  # noqa: E402
import learn_kit as lk  # noqa: E402
import page_kit as kit  # noqa: E402

e = kit.e if hasattr(kit, "e") else __import__("html").escape


def build(slug, d):
    path = f"/blog/{slug}/"
    nice = date.fromisoformat(d["updated"]).strftime("%B %-d, %Y")
    refs = ", ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a>' for t, u in d["refs"])
    quote = f'<blockquote class="learn-quote">{d["quote"]}</blockquote>' if d.get("quote") else ""
    article = f"""<p class="byline">By <a href="/about">Sam Menard</a> · {e(d["read"])} · Updated {nice}</p>
{lk.figure(d)}
{lk.takeaways(d)}
{d["intro"]}
<h2>{d["list_heading"]}</h2>
{lk.listicle(d)}
{quote}
{lk.quiz(slug, d["quiz"])}
<div class="callout"><strong>Want a number for your home?</strong> Run our <a href="{d.get("calc", "/calculator/on/")}" style="color:var(--teal,#0d4f5c); font-weight:600;">rebate calculator</a>, or <a href="/get-quotes/" style="color:var(--teal,#0d4f5c); font-weight:600;">see your rebates and the top-rated installers near you</a>.</div>
<h2>Common questions</h2>
{kit.faq(d)}
<h2>Keep reading</h2>
{lk.strip(d["related"])}
<p style="font-size:14px;">Sources, read {nice}: {refs}.</p>"""
    w = kit.quality_gate(article, d, path, loose_refs=True)
    trail = [("Home", "/"), ("Blog", "/blog/"), (d["h1"], path)]
    lds = kit.ld_scripts([kit.article_ld(d["h1"], d["desc"], d["updated"], path, published=d["published"]), kit.breadcrumb_ld(trail), kit.faq_ld(d)])
    crumb = kit.breadcrumb([("Home", "/"), ("Blog", "/blog/"), (e(d["h1"]), path)])
    kit.write_page(path, d["title"], d["desc"], lds, navfooter.render_nav("on", ""), crumb, kit.hero(d), None, article,
                   navfooter.render_footer("on", "", "", path), extra_css=fed.STYLE)
    return path, w


if __name__ == "__main__":
    only = set(sys.argv[1:])
    for s, d in lk.articles().items():
        if only and s not in only:
            continue
        print("built", *build(s, d), "words")
