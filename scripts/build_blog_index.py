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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import learn_kit as lk  # noqa: E402
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
    f, alt, _, _ = lk.photo_for(p["slug"], p["title"])
    return (f'<a href="/blog/{p["slug"]}/" class="post-card"><img class="pc-photo" src="/assets/learn/{f}-640.webp" width="640" height="427" alt="{e(alt)}" loading="lazy">'
            f'<div class="pc-body"><span class="tag">{e(p["region"])}</span><h3>{e(p["title"])}</h3><p>{e(p["desc"])}</p></div></a>')


TOPIC_TILES = {"start": "Start here", "heat": "Heat pumps", "solar": "Solar and batteries", "shell": "Insulation and windows", "bills": "Lower your bills", "avoid": "Avoid mistakes", "rank": "What is changing"}
EDITORS = ["should-you-wait-federal-heat-pump-rebate", "9-questions-to-ask-heat-pump-installer", "7-ways-to-lose-your-home-energy-rebate", "heat-pump-myths-busted",
           "fair-heat-pump-quote-canada", "why-insulation-first-energy-retrofit", "what-happens-in-an-energy-audit", "is-my-contractors-rebate-quote-a-scam"]
JS = r"""
(function(){var root=document.getElementById('bx');if(!root)return;
root.querySelectorAll('.bx-row').forEach(function(row){var car=row.querySelector('.bx-car');
 row.querySelectorAll('.bx-arrow').forEach(function(b){b.addEventListener('click',function(){car.scrollBy({left:(b.dataset.d==='1'?1:-1)*Math.min(car.clientWidth*.9,720),behavior:'smooth'})})});
 var all=row.querySelector('.bx-all');if(all)all.addEventListener('click',function(){var on=row.classList.toggle('is-grid');all.textContent=on?'Show as a row':'View all '+all.dataset.n})});
var q=document.getElementById('bx-q'),pl=document.getElementById('bx-place'),msg=document.getElementById('bx-none');
function filter(){var s=(q.value||'').trim().toLowerCase(),p=pl.value,shown=0;
 root.querySelectorAll('.post-card').forEach(function(c){var ok=(!p||c.dataset.r===p)&&(!s||c.dataset.t.indexOf(s)>-1);c.hidden=!ok;if(ok)shown++});
 root.querySelectorAll('.bx-row').forEach(function(r){r.hidden=!r.querySelector('.post-card:not([hidden])')});
 msg.hidden=shown>0;if(window.gtag&&s)gtag('event','blog_search',{term:s})}
q.addEventListener('input',filter);pl.addEventListener('change',filter);
})();
"""


def cards_row(posts, rid, heading, intro, region_attr=True):
    cs = "\n".join(card(p).replace('<a href=', f'<a data-r="{e(p["region"])}" data-t="{e((p["title"] + " " + p["desc"]).lower())}" href=', 1) for p in posts)
    return (f'<section class="bx-row" id="{rid}"><div class="bx-head"><div><h2>{e(heading)}</h2><p>{e(intro)}</p></div><div class="bx-ctl">'
            f'<button type="button" class="bx-all" data-n="{len(posts)}">View all {len(posts)}</button>'
            f'<button type="button" class="bx-arrow" data-d="-1" aria-label="Scroll left">&larr;</button><button type="button" class="bx-arrow" data-d="1" aria-label="Scroll right">&rarr;</button></div></div>'
            f'<div class="bx-car">{cs}</div></section>')


def build(data):
    secs = data["sections"]
    by = {p["slug"]: p for s in secs for p in s["posts"]}
    regions_seen = sorted({p["region"] for p in by.values()})
    place = '<option value="">Everywhere</option>' + "".join(f'<option value="{e(r)}">{e(r)}</option>' for r in regions_seen)
    chips = "".join(f'<a href="#{s["id"]}" class="bx-chip">{e(TOPIC_TILES.get(s["id"], s["heading"]))}</a>' for s in secs)
    quiz = lk.articles()["heat-pump-myths-busted"]
    quiz_html = lk.quiz("heat-pump-myths-busted", quiz["quiz"])
    more = "".join(lk.card(sl, a) for sl, a in lk.articles().items())
    editors = [by[s] for s in EDITORS if s in by]
    ups = "".join(
        f'<a class="learn-card" href="/learn/{s}/"><div class="learn-tile t-{tone}"><img src="/assets/learn/{img}-640.webp" width="640" height="427" alt="" loading="lazy"><span class="learn-kick">Guide</span><span class="learn-big">{e(n)}</span></div>'
        f'<span class="learn-more">Open the guide →</span></a>'
        for s, n, img, tone in [("heat-pumps", "Heat pumps", "heat-pump-house", "teal"), ("solar", "Solar", "solar-roof", "amber"), ("batteries", "Batteries", "modern-home", "ink"),
                                ("insulation", "Insulation", "rebate-plans", "sage"), ("water-heating", "Water heating", "kitchen", "teal"), ("windows", "Windows and doors", "living-room", "sage"),
                                ("ev-chargers", "EV chargers", "ev-charger", "teal"), ("smart-thermostats", "Thermostats", "thermostat", "amber"), ("appliances", "Appliances", "kitchen", "amber")])
    out = [S, f"""
<header class="bx-hero hero hero-photo"><div class="wrap-wide">
  <div class="eyebrow">Learn</div>
  <h1>Learn what your home can get.</h1>
  <p class="sub">Plain guides, quick quizzes and checklists on heat pumps, solar, batteries, insulation and more. Pick a topic, or search for your question.</p>
  <div class="bx-tools"><label class="bx-search"><span class="sr-only">Search guides</span><input id="bx-q" type="search" placeholder="Search guides, like heat pump quote" autocomplete="off"></label>
  <label class="bx-place"><span class="sr-only">Show guides for</span><select id="bx-place">{place}</select></label></div>
  <nav class="bx-chips" aria-label="Topics">{chips}<a href="#quizzes" class="bx-chip bx-chip-quiz">Quizzes</a></nav>
</div></header>
<div id="bx">
<section class="learn-wrap" id="quizzes"><h2 class="bx-h">Start with a quick quiz</h2>{quiz_html}</section>
{cards_row(editors, "editors", "Editor's picks", "The guides we would read first.")}
"""]
    for s in secs:
        intro = s["intro"]
        out.append(cards_row(list(spread(s["posts"])), s["id"], s["heading"].split(":")[0] if s["id"] == "start" else s["heading"], intro))
    out.append(f"""<section class="bx-row bx-quizrow" id="more-quizzes"><div class="bx-head"><div><h2>More reads and quizzes</h2><p>Listicles, myth busters and short quizzes. Five minutes each.</p></div></div>
<div class="learn-wrap" style="padding:0"><div class="learn-grid">{more}</div></div></section>
<section class="bx-row" id="by-upgrade"><div class="bx-head"><div><h2>Learn by upgrade</h2><p>One guide for each upgrade, with every open rebate we track.</p></div></div>
<div class="learn-wrap" style="padding:0"><div class="learn-grid bx-five">{ups}</div></div></section>
<p id="bx-none" class="bx-none" hidden>No guides match that. Try a shorter search, or choose Everywhere.</p>
</div>
<section class="bx-places"><div class="wrap-wide"><h2>Rebates by place</h2><nav aria-label="Rebates by area">{"".join(f'<a href="{u}" class="bx-chip">{e(n)}</a>' for n, u in AREAS)}</nav></div></section>
<script>{JS}</script>
<div style="height:48px;"></div>
""")
    out.append(E)
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
