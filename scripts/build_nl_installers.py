#!/usr/bin/env python3
"""/ca/nl/oil-to-electric-installers/: takeCHARGE's three participating-installer lists (PDF, February 2024) merged into one
searchable directory. Source rows: data/nl/participating-installers.json (read from the PDF by zooming each page; phone numbers as
printed). Prose and the other takeCHARGE program cards: data/nl/installers-page.json (cards name verified facts nl-12 to nl-17).
The list is NOT ranked: takeCHARGE does not endorse any company and we have no Google data for these companies.
Usage: python3 scripts/build_nl_installers.py   then   python3 scripts/post_steps.py   (git add -f data/nl)"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import page_kit as kit  # noqa: E402

e = html.escape
RAW = json.loads((ROOT / "data/nl/participating-installers.json").read_text(encoding="utf-8"))
PAGE = json.loads((ROOT / "data/nl/installers-page.json").read_text(encoding="utf-8"))
_PL = ROOT / "data/nl/installer-places.json"  # from scripts/lookup_nl_installer_ratings.py (Google place id, rating, review count)
PLACES = {k: v for k, v in (json.loads(_PL.read_text(encoding="utf-8")) if _PL.exists() else {}).items() if v.get("match") == "ok"}


def score(r):
    """The same review-weighted score as our installer rankings (see /installers/how-we-rank/): 25 reviews of weight, prior 4.5."""
    n = r["reviews"]
    return n / (n + 25) * r["rating"] + 25 / (n + 25) * 4.5

AREAS = [("avalon", "St. John's and the Avalon"), ("bonavista", "Bonavista and Eastern"), ("burin", "Burin Peninsula"), ("central", "Central"),
         ("western", "Western"), ("northern", "Northern Peninsula"), ("southwest", "South West Coast"), ("labrador", "Labrador")]
AREA_LABEL = dict(AREAS)
# the same company is spelled slightly differently across the three lists
ALIAS = {"coleaircontractingltd": "coleairecontractingltd", "normoresheating": "normoresheatingservice"}
DISPLAY = {"coleairecontractingltd": "Cole Aire Contracting Ltd", "normoresheatingservice": "Normore's Heating"}


def key(name):
    k = re.sub(r"[^a-z0-9]", "", name.lower())
    return ALIAS.get(k, k)


def area_tags(text):
    t = text.lower()
    tags = set()
    if "all areas" in t:
        tags |= {"avalon", "central", "western"}
    if any(w in t for w in ("avalon", "st. john", "mount pearl")):
        tags.add("avalon")
    if any(w in t for w in ("bonavista", "eastern", "fogo", "clarenville", "random island")):
        tags.add("bonavista")
    if "burin" in t:
        tags.add("burin")
    if "central" in t:
        tags.add("central")
    if "western" in t:
        tags.add("western")
    if "northern peninsula" in t:
        tags.add("northern")
    if "south west coast" in t:
        tags.add("southwest")
    if "labrador" in t:
        tags.add("labrador")
    assert tags, text
    return tags


def phones(raw_list):
    """Split '709-832-4097/1047' style strings: full numbers become call buttons, short leftovers are shown as printed."""
    out, extra = [], []
    for raw in raw_list:
        for tok in re.split(r"\s*/\s*", raw):
            digits = re.sub(r"\D", "", tok.split("Ext")[0])
            ext = re.search(r"Ext\s*(\d+)", tok)
            if len(digits) == 10 or (len(digits) == 11 and digits[0] == "1"):
                d10 = digits[-10:]
                pretty = f"{d10[:3]}-{d10[3:6]}-{d10[6:]}"
                if len(digits) == 11:
                    pretty = "1-" + pretty
                item = (pretty, "+1" + d10, ext.group(1) if ext else "")
                if item not in out:
                    out.append(item)
            elif tok.strip():
                extra.append(tok.strip())
    return out, extra


def merge():
    cos = {}

    def get(name):
        k = key(name)
        return cos.setdefault(k, {"key": k, "name": DISPLAY.get(k, name), "areas": set(), "area_text": [], "phones": [], "names": [], "hp": False, "eb": False, "brands": []})
    for lst, tag in (("heat_pump_mechanics", "hp"), ("brand_certified", "hp"), ("boiler_furnace", "eb")):
        for r in RAW[lst]:
            c = get(r["company"])
            c["areas"] |= area_tags(r["area"])
            if r["area"] not in c["area_text"]:
                c["area_text"].append(r["area"])
            c[tag] = True
            if lst == "heat_pump_mechanics":
                c["mechanic"] = True
            c["phones"].append(r["phone"])
            for n in re.split(r"\s*/\s*", r["names"].replace(" - Maxwell Electric", "")):
                if n and n not in c["names"]:
                    c["names"].append(n)
            for b in r.get("brands", "").split(","):
                b = re.sub(r"^Kerr (Controls )?- ", "", b.strip())
                for part in re.split(r"/(?!Haire)", b):
                    part = part.strip()
                    if part and part not in c["brands"]:
                        c["brands"].append(part)
    return sorted(cos.values(), key=lambda c: re.sub(r"[^a-z0-9]", "", c["name"].lower()))


def brand_key(b):
    return re.sub(r"[^a-z0-9]", "", b.lower())


def card(c, idx=0):
    ph, extra = phones(c["phones"])
    areas = " ".join(a for a, _ in AREAS if a in c["areas"])
    svc = " ".join(s for s, on in (("hp", c["hp"]), ("eb", c["eb"])) if on)
    brands = " ".join(brand_key(b) for b in c["brands"])
    texts = c["area_text"]
    if any("all areas" in x.lower() for x in texts):
        where = "All areas (Avalon, Central and Western)"
    else:
        where = "; ".join(texts)
    search = " ".join([c["name"], where, " ".join(c["names"]), " ".join(c["brands"])]).lower()
    tags = "".join(f'<span class="nli-tag nli-tag-{s}">{l}</span>' for s, l in (("hp", "Heat pumps"), ("eb", "Electric furnace or boiler")) if c["hp" if s == "hp" else "eb"])
    mech = '<span class="nli-tag nli-tag-m">Journeyperson refrigeration mechanic</span>' if c.get("mechanic") else ""
    br = f'<p class="nli-brands"><b>Heat pump brands:</b> {e(", ".join(c["brands"]))}</p>' if c["brands"] else ""
    calls = "".join(f'<a class="nli-call" href="tel:{t}">Call {p}{(" ext. " + x) if x else ""}</a>' for p, t, x in ph[:3])
    rest = [f"{p}{(' ext. ' + x) if x else ''}" for p, _t, x in ph[3:]] + extra
    more = f'<p class="nli-note">Also on the list: {e(", ".join(rest))}</p>' if rest else ""
    who = f'<p class="nli-who">Ask for: {e(", ".join(c["names"][:4]))}</p>' if c["names"] else ""
    pl = PLACES.get(c["key"])
    rating = ""
    sc = ""
    if pl:
        sc = f"{score(pl):.3f}"
        rating = (f'<p class="nli-rating"><span class="nli-star" aria-hidden="true">&#9733;</span> <b>{pl["rating"]:.1f}</b> '
                  f'<span>({pl["reviews"]:,} Google reviews)</span> <a href="https://www.google.com/maps/place/?q=place_id:{pl["place_id"]}" target="_blank" rel="noopener">Google Maps</a></p>')
    return (f'<li class="nli-card" data-i="{idx}" data-score="{sc}" data-areas="{areas}" data-svc="{svc}" data-brands="{brands}" data-search="{e(search, quote=True)}">'
            f'<h3>{e(c["name"])}</h3>{rating}<p class="nli-where"><b>Works in:</b> {e(where)}</p><p class="nli-tags">{tags}{mech}</p>{br}{who}'
            f'<div class="nli-calls">{calls}</div>{more}</li>')


def widget(cos):
    area_btns = "".join(f'<button type="button" class="nli-chip" data-area="{a}" aria-pressed="false">{e(l)}</button>' for a, l in AREAS)
    all_brands = {}
    for c in cos:
        for b in c["brands"]:
            all_brands.setdefault(brand_key(b), b)
    brand_opts = "".join(f'<option value="{k}">{e(v)}</option>' for k, v in sorted(all_brands.items(), key=lambda kv: kv[1].lower()))
    cards = "".join(card(c, i) for i, c in enumerate(cos))
    has_ratings = any(c["key"] in PLACES for c in cos)
    sort_ui = ('<div><label class="nli-lab" for="nli-sort">Sort by</label><select id="nli-sort" class="nli-sel"><option value="">A to Z (default)</option><option value="top">Top rated on Google</option></select></div>') if has_ratings else ""
    return f'''<div class="nli nli-scope" id="nli">
<div class="nli-bar">
<label class="nli-lab" for="nli-q">Search by company, town or name</label>
<input id="nli-q" class="nli-q" type="search" placeholder="Try Gander, Marystown or Tucker" autocomplete="off">
<p class="nli-lab">Where is your home?</p>
<div class="nli-chips" role="group" aria-label="Area">{area_btns}</div>
<div class="nli-row"><div><label class="nli-lab" for="nli-svc">What do you need installed?</label>
<select id="nli-svc" class="nli-sel"><option value="">Anything</option><option value="hp">A heat pump</option><option value="eb">An electric furnace or boiler</option></select></div>
<div><label class="nli-lab" for="nli-brand">Heat pump brand</label>
<select id="nli-brand" class="nli-sel"><option value="">Any brand</option>{brand_opts}</select></div>{sort_ui}</div>
<p class="nli-count" id="nli-count" aria-live="polite">Showing all {len(cos)} companies</p>
<button type="button" class="nli-reset" id="nli-reset" hidden>Clear filters</button>
</div>
<ul class="nli-list" id="nli-list">{cards}</ul>
<p class="nli-empty" id="nli-empty" hidden>No company matches those filters. Try a different area, or clear the filters. If you are in a small community, call a company in the nearest area: many serve more than their home town.</p>
</div>
<script>
(function(){{
  var list=document.getElementById('nli-list'); if(!list) return;
  var cards=[].slice.call(list.children), q=document.getElementById('nli-q'), svc=document.getElementById('nli-svc'), br=document.getElementById('nli-brand'),
      srt=document.getElementById('nli-sort'), chips=[].slice.call(document.querySelectorAll('.nli-chip')), cnt=document.getElementById('nli-count'), emp=document.getElementById('nli-empty'), rs=document.getElementById('nli-reset'), area='';
  function run(){{
    var t=q.value.trim().toLowerCase(), n=0;
    cards.forEach(function(c){{
      var ok=(!area||c.dataset.areas.split(' ').indexOf(area)>-1)&&(!svc.value||c.dataset.svc.split(' ').indexOf(svc.value)>-1)&&(!br.value||c.dataset.brands.split(' ').indexOf(br.value)>-1)&&(!t||c.dataset.search.indexOf(t)>-1);
      c.hidden=!ok; if(ok) n++;
    }});
    var on=area||svc.value||br.value||t;
    cnt.textContent=on?('Showing '+n+' of '+cards.length+' companies'):('Showing all '+cards.length+' companies');
    emp.hidden=n>0; rs.hidden=!on;
  }}
  chips.forEach(function(b){{ b.addEventListener('click',function(){{ var same=area===b.dataset.area; area=same?'':b.dataset.area; chips.forEach(function(x){{ x.setAttribute('aria-pressed',String(x.dataset.area===area)); }}); run(); }}); }});
  function order(){{
    var top=srt&&srt.value==='top';
    cards.slice().sort(function(a,b){{
      if(top){{ var x=parseFloat(a.dataset.score)||0, y=parseFloat(b.dataset.score)||0; if(x!==y) return y-x; }}
      return (+a.dataset.i)-(+b.dataset.i);
    }}).forEach(function(c){{ list.appendChild(c); }});
  }}
  if(srt) srt.addEventListener('change',order);
  [q,svc,br].forEach(function(el){{ el.addEventListener('input',run); el.addEventListener('change',run); }});
  rs.addEventListener('click',function(){{ q.value=''; svc.value=''; br.value=''; area=''; if(srt){{ srt.value=''; order(); }} chips.forEach(function(x){{ x.setAttribute('aria-pressed','false'); }}); run(); }});
  var h=(location.hash||'').replace('#',''); chips.forEach(function(b){{ if(b.dataset.area===h){{ b.click(); }} }});
}})();
</script>'''


STYLE = """<style>
.nli-scope { margin: 18px 0 34px; }
.nli-scope .nli-bar { padding: 18px; border: 1px solid var(--card-rule, #e3dacb); border-radius: var(--radius-card, 16px); background: #fff; box-shadow: var(--shadow-card, none); }
.nli-scope .nli-lab { display: block; margin: 0 0 6px; font-size: 15px; font-weight: 700; color: var(--ink, #0a2a2e); max-width: none; }
.nli-scope .nli-q, .nli-scope .nli-sel { width: 100%; min-height: 48px; padding: 0 14px; font: inherit; font-size: 16px; color: var(--ink, #0a2a2e); background: #fff; border: 1px solid #b9ae9c; border-radius: 10px; box-sizing: border-box; }
.nli-scope .nli-q { margin-bottom: 16px; }
.nli-scope .nli-chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 16px; }
.nli-scope .nli-chip { min-height: 44px; padding: 0 16px; font: inherit; font-size: 15px; font-weight: 600; color: var(--teal-deep, #08363f); background: #f6f0e6; border: 1px solid #d9d0c1; border-radius: 999px; cursor: pointer; }
.nli-scope .nli-chip[aria-pressed="true"] { color: #fff; background: var(--teal, #0d4f5c); border-color: var(--teal, #0d4f5c); }
.nli-scope .nli-row { display: grid; gap: 14px; margin: 0 0 12px; }
@media (min-width: 640px) { .nli-scope .nli-row { grid-template-columns: 1fr 1fr; } }
.nli-scope .nli-count { margin: 8px 0 0; font-size: 15px; font-weight: 700; color: var(--teal, #0d4f5c); max-width: none; }
.nli-scope .nli-reset { margin-top: 8px; min-height: 44px; padding: 0 14px; font: inherit; font-size: 15px; font-weight: 600; color: var(--amber-text, #a4540a); background: none; border: 0; text-decoration: underline; cursor: pointer; }
.nli-scope .nli-list { list-style: none; margin: 18px 0 0; padding: 0; display: grid; gap: 14px; grid-template-columns: repeat(auto-fill, minmax(min(100%, 300px), 1fr)); max-width: none; }
.nli-scope .nli-card { margin: 0; padding: 18px; border: 1px solid var(--card-rule, #e3dacb); border-radius: var(--radius-card, 16px); background: #fff; box-shadow: var(--shadow-card, none); }
.nli-scope .nli-card[hidden] { display: none; }
.nli-scope .nli-card h3 { margin: 0 0 8px; font-size: 19px; line-height: 1.25; }
.nli-scope .nli-card p { margin: 0 0 8px; font-size: 15px; max-width: none; }
.nli-scope .nli-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.nli-scope .nli-tag { display: inline-block; padding: 2px 10px; font-size: 13px; font-weight: 700; border-radius: 999px; }
.nli-scope .nli-tag-hp { color: #1b4332; background: #d8f3dc; }
.nli-scope .nli-tag-eb { color: #7a4a00; background: #ffe8c2; }
.nli-scope .nli-tag-m { color: #08363f; background: #dbeaee; }
.nli-scope .nli-rating { color: var(--ink, #0a2a2e); }
.nli-scope .nli-rating span { color: var(--muted, #5a6b6e); }
.nli-scope .nli-star { color: #d4751c; }
.nli-scope .nli-who, .nli-scope .nli-note { color: var(--muted, #5a6b6e); font-size: 14px !important; }
.nli-scope .nli-calls { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.nli-scope .nli-call { display: inline-flex; align-items: center; min-height: 44px; padding: 0 16px; font-size: 15px; font-weight: 700; color: #fff; background: #a4540a; border-radius: 10px; text-decoration: none; }
.nli-scope .nli-call:hover { background: #8a4607; }
.nli-scope .nli-empty { margin: 18px 0; padding: 16px; border-radius: 12px; background: #f6f0e6; }
</style>"""


def build():
    cos = merge()
    d = dict(PAGE)
    n = len(cos)
    d["badge"] = d["badge"].replace("{N}", str(n))
    fids = kit.fact_ids(d)
    for cd in d["cards"]:
        cd["status"] = kit.FACTS[cd["facts"][0]]["status"]
    iso, when = kit.checked(fids)
    steps = "".join(f"<li>{s}</li>\n" for s in d["claim_steps"])
    links = "".join(f'<li><a href="{u}">{e(t)}</a>: {b}</li>\n' for t, u, b in d["links"])
    hp = sum(1 for c in cos if c["hp"])
    eb = sum(1 for c in cos if c["eb"])
    if PLACES:
        got = [r for r in PLACES.values()]
        when = date.fromisoformat(max(r["fetched"] for r in got)).strftime("%B %Y")
        for s in d["sections"]:
            if s[0].startswith("Why we do not rank"):
                s[0] = "How to read the Google ratings"
                s[1] = (f"<p>takeCHARGE's list decides who can do Oil to Electric work. We then added each company's Google rating and review count where we found a matching Google listing: {len(got)} of the {n} companies. "
                        f"The page starts A to Z. Pick \"Top rated on Google\" to sort by our review-weighted score, the same one we use on our installer rankings: a 4.9 from 200 reviews beats a 5.0 from 3. Companies without a rating stay at the bottom, A to Z. "
                        f"A rating is a guide, not a stamp. takeCHARGE does not endorse any company, so read the recent reviews and get two or three quotes. Ratings and review counts from Google Maps, collected {when}. "
                        f"<a href=\"/installers/how-we-rank/\">How we rank</a>.</p>")
    top = (f'<div class="callout"><strong>Short answer:</strong> Only installers on takeCHARGE\'s list can earn you the Oil to Electric rebate. '
           f'There are {n} companies on it: {hp} for heat pumps and {eb} for electric furnaces and boilers. Get a written quote from one of them '
           f'<em>before</em> you apply. takeCHARGE does not endorse any company, so the list starts A to Z.{" You can sort by Google rating." if PLACES else ""}</div>')
    article = f"""{top}
<h2>Find an installer near you</h2>
<p>Tap your area, or type a town or company name. Tap a phone number on your phone to call. The list is takeCHARGE's, dated February 2024, and we read it on October 27, 2026. <a href="https://takechargenl.ca/wp-content/uploads/2023/07/Oil-to-Electric-Participating-Installers.pdf" target="_blank" rel="noopener">See the original PDF</a>.</p>
{widget(cos)}
{kit.sections(d)}
<h2>{d['claim_heading']}</h2>
<ol>
{steps}</ol>
<h2>{d['cards_heading']}</h2>
{d['cards_intro']}
<div class="rebate-grid">
{kit.cards(d)}
</div>
<h2>More for Newfoundland and Labrador homes</h2>
<ul>
<li><a href="{d['hub']}">Newfoundland and Labrador home rebates: every program in one place</a></li>
{links}</ul>
<h2>Common questions</h2>
{kit.faq(d)}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read {when}: {kit.sources(d)}. Phone numbers are as printed by takeCHARGE; confirm details with the installer.</p>"""
    w = kit.quality_gate(article, d, d["path"], loose_refs=True)
    trail = [("Home", "/"), (d["hub_name"], d["hub"]), (d["short"], d["path"])]
    lds = kit.ld_scripts([kit.article_ld(d["title"], d["desc"], iso, d["path"]), kit.breadcrumb_ld(trail, home_slash=True), kit.faq_ld(d)])
    crumb = kit.breadcrumb([("Home", "/"), (e(d["hub_name"]), d["hub"]), (e(d["short"]), d["path"])])
    kit.write_page(d["path"], d["title"], d["desc"], lds, navfooter.render_nav(d["nav"], ""), crumb, kit.hero(d), None, article,
                   navfooter.render_footer(d["nav"], "", "", d["path"]), d.get("alternates", ""), STYLE)
    print(f"built {d['path']}: {n} companies ({hp} heat pump, {eb} furnace/boiler), {w} words")


if __name__ == "__main__":
    build()
