#!/usr/bin/env python3
"""Build the /blog/ index from data/blog-index.json.

Posts are grouped by topic, not region. Each card carries a region label, and inside a
section the regions are spread evenly (posts for every area first, then each region's
posts placed at even intervals) so no one province or state fills a long run of cards.
Writes the hero and post sections between BLOG-INDEX-START/END markers in blog/index.html
and updates the title and descriptions. Nav, footer and other injected blocks are left alone.
Usage: python3 scripts/build_blog_index.py   (git add -f data/blog-index.json)"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "blog" / "index.html"
DATA = ROOT / "data" / "blog-index.json"
S, E = "<!-- BLOG-INDEX-START -->", "<!-- BLOG-INDEX-END -->"
FIRST = ("Everywhere", "Canada")  # shown first in each section, in this order

TITLE = "Home Energy Rebate Guides | HomePowerRebate"
DESC = ("Plain-language guides to heat pump, solar, battery, insulation and other home energy rebates "
        "in your city, across Canada and the US: who qualifies, how much, and how to apply.")
AREAS = [("BC", "/ca/bc/"), ("Ontario", "/ca/on/"), ("Alberta", "/ca/ab/"), ("Nova Scotia", "/ca/ns/"),
         ("California", "/us/ca/"), ("New York", "/us/ny/"), ("Massachusetts", "/us/ma/"),
         ("Pennsylvania", "/us/pa/"), ("Colorado", "/us/co/"), ("Vermont", "/us/vt/")]

e = html.escape
CHIP = ("display:inline-block;padding:8px 14px;border-radius:999px;font-size:14px;font-weight:600;"
        "text-decoration:none;white-space:nowrap;")


def spread(posts):
    """Everywhere/Canada posts first; other regions interleaved by even spacing."""
    head = [p for f in FIRST for p in posts if p["region"] == f]
    rest = [p for p in posts if p["region"] not in FIRST]
    groups = {}
    for p in rest:
        groups.setdefault(p["region"], []).append(p)
    keyed = []
    for r, (region, ps) in enumerate(groups.items()):
        for i, p in enumerate(ps):
            keyed.append((i / len(ps), len(ps), r, p))
    # each region's first post leads (smaller regions first), then even spacing
    return head + [k[3] for k in sorted(keyed, key=lambda k: k[:3])]


def card(p):
    return (f'<a href="/blog/{p["slug"]}/" class="post-card"><span class="tag">{e(p["region"])}</span>'
            f'<h3>{e(p["title"])}</h3><p>{e(p["desc"])}</p></a>')


def build(data):
    secs = data["sections"]
    areas = "".join(f'<a href="{u}" style="{CHIP}background:rgba(250,247,242,.1);color:#fff;'
                    f'border:1px solid rgba(250,247,242,.35);">{e(n)}</a>' for n, u in AREAS)
    topics = "".join(f'<a href="#{s["id"]}" style="{CHIP}background:#fff;color:var(--teal);'
                     f'border:1px solid var(--rule);">{e(s["heading"].split(":")[0])}</a>' for s in secs)
    out = [S, """
<header class="hub-hero">
  <div class="wrap-wide">
    <div class="eyebrow">Rebate guides</div>
    <h1>Understand the rebates in your city.</h1>
    <p class="sub">Plain guides to heat pump, solar, battery, insulation and other home energy rebates. Learn who qualifies, how much you can get and how to apply where you live.</p>
    <p style="margin:26px 0 10px;font-size:14px;font-weight:600;color:rgba(250,247,242,.82);">Find the rebates for your area:</p>
    <nav aria-label="Rebates by area" style="display:flex;flex-wrap:wrap;justify-content:flex-start;gap:8px;padding:0;background:none;border:0;position:static;">""" + areas + """</nav>
  </div>
</header>
<section style="padding:36px 0 0;">
  <div class="wrap-wide">
    <p style="margin:0 0 10px;font-size:14px;font-weight:600;color:var(--ink-soft);">Jump to a topic:</p><nav aria-label="Guide topics" style="display:flex;flex-wrap:wrap;justify-content:flex-start;gap:8px;padding:0;background:none;border:0;position:static;">""" + topics + """</nav>
  </div>
</section>
"""]
    for s in secs:
        cards = "\n".join(card(p) for p in spread(s["posts"]))
        out.append(f"""<section id="{s['id']}" style="padding:44px 0 8px;scroll-margin-top:90px;">
  <div class="wrap-wide">
    <h2 style="font-size:clamp(26px,4vw,34px);margin:0 0 8px;">{e(s['heading'])}</h2>
    <p style="margin:0;color:var(--ink-soft);max-width:640px;">{e(s['intro'])}</p>
    <div class="post-grid" style="margin-top:24px;">
{cards}
    </div>
  </div>
</section>
""")
    out.append('<div style="height:48px;"></div>\n' + E)
    return "".join(out)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    slugs = [p["slug"] for s in data["sections"] for p in s["posts"]]
    dup = {x for x in slugs if slugs.count(x) > 1}
    assert not dup, f"listed twice: {dup}"
    gone = [x for x in slugs if not (ROOT / "blog" / x / "index.html").exists()]
    assert not gone, f"no such post: {gone}"
    t = PAGE.read_text(encoding="utf-8")
    block = build(data)
    if S in t:
        t = re.sub(re.escape(S) + r"[\s\S]*?" + re.escape(E), lambda m: block, t)
    else:  # first run: replace the old hero and the old card section
        m = re.search(r'<header class="hub-hero">[\s\S]*?</header>\s*<section style="padding:56px 0;">[\s\S]*?</section>\n', t)
        assert m, "old blog hero/grid not found"
        t = t[:m.start()] + block + "\n" + t[m.end():]
    t = re.sub(r"<title>.*?</title>", f"<title>{TITLE}</title>", t, count=1)
    t = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{TITLE}">', t, count=1)
    t = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{e(DESC)}">', t, count=1)
    t = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{e(DESC)}">', t, count=1)
    PAGE.write_text(t, encoding="utf-8")
    print(f"blog index: {len(slugs)} posts in {len(data['sections'])} topic sections")


if __name__ == "__main__":
    main()
