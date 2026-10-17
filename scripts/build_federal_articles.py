#!/usr/bin/env python3
"""Federal heat pump rebate series: /blog/<slug>/ from hand-written data/federal/<slug>.json.
Fields: title, desc, h1, lead, badge, sections [[h2, html]], faq [[q, a]], refs [[text, url]], related [[text, url]], published (ISO), updated (ISO).
Figures must come from data/verified-facts (federal-*, bc, on, ns, ab, general) or the page's refs. Same gate as the utility pages.
Usage: python3 scripts/build_federal_articles.py [slug ...]"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_ca_pages as ca  # noqa: E402
import page_kit as kit  # noqa: E402  (shared page components)

e = html.escape
BASE = ca.BASE
PILLAR = ("National Heat Pump Rebate: everything confirmed so far", "/programs/national-heat-pump-rebate/")


# byline and FAQ spacing for these articles (served as a template variant file by the restamp)
STYLE = "<style>.faq-item{border-bottom:1px solid #d9d0c1;padding:14px 0}.faq-item h3{margin:0 0 6px;font-size:18px}.faq-item p{margin:0}.byline{font-size:14px;color:#5a5348;margin:0 0 16px}</style>"


def build(slug):
    d = json.loads((ROOT / "data/federal" / f"{slug}.json").read_text())
    path = f"/blog/{slug}/"
    nice = date.fromisoformat(d["updated"]).strftime("%B %-d, %Y")
    refs = ", ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a>' for t, u in d["refs"])
    rel = "".join(f'<li><a href="{u}">{t}</a></li>' for t, u in [PILLAR] + d["related"])
    article = f"""<p class="byline">By <a href="/about">Sam Menard</a> · Updated {nice}</p>
{kit.sections(d)}
<div class="callout"><strong>Want a number for your home?</strong> Run our <a href="{d.get('calc', '/calculator/on/')}" style="color:var(--teal,#0d4f5c); font-weight:600;">rebate calculator</a>, or <a href="/get-quotes/" style="color:var(--teal,#0d4f5c); font-weight:600;">get a plan emailed with the top-rated installers near you</a>.</div>
<h2>Common questions</h2>
{kit.faq(d)}
<h2>More on the federal heat pump rebate</h2>
<ul>{rel}</ul>
<p style="font-size:14px;">Sources, read {nice}: {refs}.</p>"""
    w = kit.quality_gate(article, d, path, loose_refs=True)
    nav = d.get("nav", "on")
    trail = [("Home", "/"), ("Blog", "/blog/"), (d["h1"], path)]
    lds = kit.ld_scripts([kit.article_ld(d["h1"], d["desc"], d["updated"], path, published=d["published"]), kit.breadcrumb_ld(trail), kit.faq_ld(d)])
    crumb = kit.breadcrumb([("Home", "/"), ("Blog", "/blog/"), (e(d["h1"]), path)])
    kit.write_page(path, d["title"], d["desc"], lds, navfooter.render_nav(nav, ""), crumb, kit.hero(d), None, article,
                   navfooter.render_footer(nav, "", "", path), extra_css=STYLE)
    return path, w


if __name__ == "__main__":
    only = set(sys.argv[1:])
    for f in sorted((ROOT / "data/federal").glob("*.json")):
        if only and f.stem not in only:
            continue
        r = build(f.stem)
        print("built", r[0], r[1], "words")
