#!/usr/bin/env python3
"""A search-first front for /installers/ (2026-10-24). Stamps into installers/index.html:
- the hero (counts from data, no unverified "all rated 4+ stars" or "15 states" claims),
- INSTALLERS-FRONT: a city + service search that goes straight to the ranked list, photo service tiles, a hiring quiz, province and state cards
  with every city's link, three "how we rank" cards, and a learn row,
- the old four-step finder, kept but folded into a closed <details> (IF-OLD markers),
- the stats strip numbers.
City and service links come from installers/rankings.json (one entry per ranking page). A post-step; idempotent.
Usage: python3 scripts/build_installers_front.py"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import learn_kit as lk  # noqa: E402
import regions  # noqa: E402

PAGE = ROOT / "installers" / "index.html"
e = html.escape
FS, FE = "<!-- INSTALLERS-FRONT-START -->", "<!-- INSTALLERS-FRONT-END -->"
OS, OE = "<!-- IF-OLD-START -->", "<!-- IF-OLD-END -->"
SERVICES = [("heat-pump", "Heat pump"), ("solar", "Solar panels"), ("battery", "Home battery"), ("insulation", "Insulation"), ("energy-advisor", "Energy advisor or auditor")]
TILES = [("heat-pump", "Heat pumps", "heat-pump-house", "teal"), ("solar", "Solar", "solar-roof", "amber"), ("battery", "Batteries", "modern-home", "ink"),
         ("insulation", "Insulation", "rebate-plans", "sage")]


def data():
    rk = json.loads((ROOT / "installers" / "rankings.json").read_text(encoding="utf-8"))
    cities = {}
    for r in rk:
        key = (r["region"], r["url"].split("/")[3])
        c = cities.setdefault(key, {"code": r["region"], "slug": key[1], "label": r["city"], "services": {}})
        c["services"]["energy-advisor" if r["service"] in ("energy-advisor", "energy-auditor") else r["service"]] = r["url"]
    return cities


def best(c):
    for s in ("heat-pump", "solar", "battery", "insulation", "energy-advisor"):
        if s in c["services"]:
            return c["services"][s]


def front(cities):
    opts, js = [], {}
    for c in cities.values():
        rg = regions.BY_CODE[c["code"]]["name"]
        lab = f'{c["label"]}, {rg}'
        opts.append(f'<option value="{e(lab)}">')
        js[lab.lower()] = c["services"]
    sel = "".join(f'<option value="{v}">{e(n)}</option>' for v, n in SERVICES)
    tiles = "".join(
        f'<button type="button" class="if-tile" data-s="{s}"><img src="/assets/learn/{img}-640.webp" width="640" height="427" alt="" loading="lazy"><span class="if-tile-t t-{tone}">{e(n)}</span></button>'
        for s, n, img, tone in TILES)
    groups = []
    for label, rs in regions.grouped():
        cards = []
        for r in rs:
            cs = sorted((c for c in cities.values() if c["code"] == r["code"]), key=lambda c: c["label"])
            if not cs:
                continue
            names = {"heat-pump": "Heat pump", "solar": "Solar", "battery": "Battery", "insulation": "Insulation", "energy-advisor": "Advisor"}
            lis = "".join(f'<li><b>{e(c["label"])}</b><span>' + " ".join(f'<a href="{c["services"][s]}">{names[s]}</a>' for s in names if s in c["services"]) + "</span></li>" for c in cs)
            cards.append(f'<details class="if-region"><summary><b>{e(r["name"])}</b><span>{len(cs)} cities</span></summary><ul>{lis}</ul></details>')
        groups.append(f'<h3 class="if-h3">{e(label)}</h3><div class="if-regions">{"".join(cards)}</div>')
    how = "".join(f'<a class="about-promise" href="{h}"><img src="/assets/learn/{img}-640.webp" width="640" height="427" alt="" loading="lazy"><span><b>{e(t)}</b>{e(b)}</span></a>'
                  for h, img, t, b in [("/installers/how-we-rank/", "duplex-home", "Ranked by Google reviews", "A rating weighted by how many reviews a company has. Nobody pays to rank higher, and rankings are not paid for."),
                                      ("/blog/9-questions-to-ask-heat-pump-installer/", "hiring-roof", "Ask nine questions first", "What to ask before you sign, and how to read the answers."),
                                      ("/blog/fair-heat-pump-quote-canada/", "rebate-plans", "Compare three quotes", "How to line up quotes so you can see the real price differences.")])
    row = lk.not_ready_row("heat-pump", key="/installers/", heading="Before you hire", sub="Short reads and quick quizzes. Learn the rules first, then call.")
    script = ("(function(){var D=" + json.dumps(js, separators=(",", ":")) + ";var f=document.getElementById('if-bar');if(!f)return;var q=document.getElementById('if-q'),s=document.getElementById('if-s'),m=document.getElementById('if-msg');"
              "document.querySelectorAll('.if-tile').forEach(function(b){b.addEventListener('click',function(){s.value=b.dataset.s;q.focus();q.scrollIntoView({block:'center',behavior:'smooth'})})});"
              "f.addEventListener('submit',function(ev){ev.preventDefault();var k=q.value.trim().toLowerCase(),c=D[k];if(!c){var h=Object.keys(D).filter(function(x){return x.indexOf(k)===0});if(h.length===1)c=D[h[0]]}"
              "if(!c){m.textContent='Pick your city from the list so we can open its installer ranking.';m.hidden=false;return}"
              "var u=c[s.value];if(!u){u=c['heat-pump']||c.solar||c.battery||c.insulation||c['energy-advisor'];m.textContent='We do not have that list for this city yet. Showing the closest one.'}"
              "if(window.gtag)gtag('event','installer_search',{service:s.value});location.href=u});var P=new URLSearchParams(location.search);if(P.get('city')){q.value=P.get('city');if(P.get('service'))s.value=P.get('service');f.dispatchEvent(new Event('submit',{cancelable:true}))}})();")
    return f"""{FS}
<section class="if-front"><div class="if-in">
<form class="if-bar" id="if-bar" autocomplete="off"><div class="hub-search-f"><input id="if-q" list="if-cities" placeholder="Your city, like Kelowna" aria-label="Your city"></div>
<div class="hub-search-f"><select id="if-s" aria-label="What you need">{sel}</select></div><button type="submit">See top-rated installers</button></form>
<datalist id="if-cities">{"".join(opts)}</datalist>
<p id="if-msg" class="if-msg" role="alert" hidden></p>
<div class="if-trust"><span>Ranked by Google reviews</span><span>Not paid for</span><span>Rebates linked to the official page</span></div>
<h2 class="if-h2">What do you need done?</h2><div class="if-tiles">{tiles}</div>
<div class="learn-wrap" style="padding:0">{lk.general_quiz("hiring")}</div>
<h2 class="if-h2">Or pick your province or state</h2>{"".join(groups)}
<h2 class="if-h2">How we rank, and how to choose</h2><div class="about-promises">{how}</div>
<div class="learn-wrap" style="padding:0">{row}</div>
</div></section>
<script>{script}</script>
{FE}"""


FAQ_RE = re.compile(r'<section class="section[^"]*" id="faq">[\s\S]*?</section>')


def faq_section(old):
    """Rebuild the "Questions homeowners ask before hiring" block as grouped accordions with category chips (same questions, answers and sources)."""
    intro = re.search(r'<p class="is-433de30b">([\s\S]*?)</p>', old)
    groups = []
    for g in re.finditer(r'<h3 class="[^"]*">([^<]+)</h3>([\s\S]*?)(?=<h3 class="|<p class="is-d0927fc1">|</div>\s*<p class)', old):
        items = []
        for it in re.finditer(r'<div class="faq-item[^"]*">\s*<p class="[^"]*">([\s\S]*?)</p>\s*<p class="[^"]*">([\s\S]*?)</p>\s*(?:<p class="src[^"]*">([\s\S]*?)</p>)?', g.group(2)):
            items.append((it.group(1).strip(), it.group(2).strip(), (it.group(3) or "").strip()))
        if items:
            groups.append((html.unescape(g.group(1).strip()), items))
    note = re.search(r'<p class="is-d0927fc1">([\s\S]*?)</p>', old)
    chips = '<button type="button" aria-pressed="true" data-g="">All</button>' + "".join(f'<button type="button" aria-pressed="false" data-g="{i}">{e(n)}</button>' for i, (n, _) in enumerate(groups))
    body = "".join(
        f'<div class="faq-grp" data-g="{i}"><h3 class="if-h3">{e(n)}</h3>' + "".join(
            f'<details class="faq-d"><summary>{q}</summary><div><p>{a}</p>' + (f'<p class="src">{s}</p>' if s else "") + "</div></details>" for q, a, s in its) + "</div>"
        for i, (n, its) in enumerate(groups))
    js = ("(function(){var s=document.getElementById('faq');if(!s)return;s.querySelectorAll('.faq-cats button').forEach(function(b){b.addEventListener('click',function(){"
          "s.querySelectorAll('.faq-cats button').forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false')});"
          "s.querySelectorAll('.faq-grp').forEach(function(g){g.hidden=b.dataset.g!==''&&g.dataset.g!==b.dataset.g})})})})();")
    return (f'<section class="section" id="faq"><div class="if-in"><div class="eyebrow">Before you hire</div><h2 class="if-h2" style="margin-top:6px">Questions homeowners ask before hiring an installer</h2>'
            f'<p style="font-size:19px;max-width:44em">{intro.group(1).strip() if intro else ""}</p><div class="faq-cats">{chips}</div>{body}'
            f'<p style="font-size:15px;color:var(--muted)">{note.group(1).strip() if note else ""}</p></div></section><script>{js}</script>')


def main():
    t = PAGE.read_text(encoding="utf-8")
    cities = data()
    total = len(cities)
    nreg = len({c["code"] for c in cities.values()})
    lists = len(json.loads((ROOT / "installers" / "rankings.json").read_text(encoding="utf-8")))
    # hero
    t = re.sub(r'<section class="hero[^"]*">\s*<div class="wrap">\s*<h1>[\s\S]*?</section>',
               f'<section class="hero hero-photo"><div class="wrap"><h1>Find top-rated installers near you</h1>'
               f'<p>{lists} ranked lists for heat pumps, solar, batteries, insulation and energy advisors, in {total} cities across {nreg} provinces and states. Type your city and see who has the best Google reviews.</p></div></section>',
               t, count=1)
    t = re.sub(r"<!-- HUB-SEARCH-START -->[\s\S]*?<!-- HUB-SEARCH-END -->\n?", "", t)
    t = re.sub(re.escape(FS) + r"[\s\S]*?" + re.escape(FE) + r"\n?", "", t)
    i = t.index("</section>", t.index('<section class="hero hero-photo">')) + len("</section>")
    t = t[:i] + "\n" + front(cities) + t[i:]
    # retire the old step-by-step finder, its filters, the near-you box, the city lists and the 1,300-line static directory:
    # the search and province cards above replace them (2026-10-25)
    t = re.sub(re.escape(OS) + r"[\s\S]*?" + re.escape(OE), "", t)
    t = re.sub(r'<section class="section finder-tool">[\s\S]*?</section>', "", t, count=1)
    t = re.sub(r'<section class="section[^"]*" id="program-filter-section">[\s\S]*?</section>', "", t, count=1)
    t = re.sub(r'<section class="section near-you[^"]*" id="near-you">[\s\S]*?</section>', "", t, count=1)
    t = re.sub(r"<!-- RANKINGS-INDEX-START -->[\s\S]*?<!-- RANKINGS-INDEX-END -->", "", t)
    t = re.sub(r'<section class="section[^"]*" id="full-directory"[\s\S]*?</section>\s*(?=<section class="section[^"]*" id="faq")', "", t, count=1)
    t = re.sub(r"<script>\s*// IMPORTANT: adding a city to any of the \*_CITIES[\s\S]*?</script>", "", t, count=1)
    m = FAQ_RE.search(t)
    if m and 'class="faq-item' in m.group(0):
        t = t[:m.start()] + faq_section(m.group(0)) + t[m.end():]
    # stats strip
    t = t.replace('<div class="stat-num">1,300+</div>\n        <div class="stat-label">Google-rated installers</div>', f'<div class="stat-num">{lists}</div>\n        <div class="stat-label">Installer lists ranked by Google reviews</div>')
    t = re.sub(r'<div class="stat-num" id="stat-cities">[^<]*</div>\s*<div class="stat-label">[^<]*</div>', f'<div class="stat-num" id="stat-cities">{total}</div>\n        <div class="stat-label">Cities in {nreg} provinces and states</div>', t, count=1)
    PAGE.write_text(t, encoding="utf-8")
    print(f"installers front: {total} cities, {lists} lists")


if __name__ == "__main__":
    main()
