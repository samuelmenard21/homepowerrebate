#!/usr/bin/env python3
"""The homepage (index.html), built from data only (2026-10-17).

Every figure on the page comes from a data file, so the page cannot drift from the facts:
- regions, cities and the city picker: data/regions.json (via build_get_quotes.city_slugs)
- the hero rebate sheet and the region list: data/calc/<code>.json programs, with status, check date and source from
  data/verified-facts/*.json (only active programs count; a program that needs another one is never the headline)
- federal notes: facts federal-0 (Canada) and general-8 (US 25C/25D)
- PowerScore lists: powerscore-data.json; what changed: rebate-tracker/changes.json; deadlines: build_rebate_deadlines
- guides: titles and summaries from data/blog-index.json
The page has no inline CSS: its design is the home family file _partials/templates/home.css (part of /assets/site.css).
The menu, footer and shared script come from the restamp (apply_canonical_nav_footer.py); this script keeps whatever the
last restamp wrote between those markers. Old entry points (build_home_hero, build_home_powerscore, build_home_feed) call main().
Usage: python3 scripts/build_home.py, then python3 scripts/post_steps.py"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import regions  # noqa: E402
import learn_kit as lk  # noqa: E402
from build_get_quotes import REG, OV, city_slugs  # noqa: E402
from status_pills import STATUS  # noqa: E402

SITE = "https://homepowerrebate.com"
esc = html.escape
CATS = [  # homepage upgrade buckets: (id, label, calc upgrade ids)
    ("heat-pump", "Heat pump", ("heat-pump",)),
    ("insulation", "Insulation and windows", ("insulation", "windows")),
    ("solar", "Solar panels", ("solar",)),
    ("battery", "Home battery", ("battery",)),
    ("water-heater", "Water heater", ("water-heater",)),
    ("ev", "EV charger", ("ev",)),
    ("thermostat", "Smart thermostat", ("thermostat",)),
]
CAT_OF = {u: c for c, _, us in CATS for u in us}
TZ = {  # browser time zone -> region shown in the sheet first (Canadian zones also preselect the province)
    "America/Vancouver": "bc", "America/Edmonton": "ab", "America/Toronto": "on", "America/Halifax": "ns", "America/Glace_Bay": "ns",
    "America/St_Johns": "nl", "America/Los_Angeles": "ca", "America/New_York": "ny", "America/Chicago": "il", "America/Denver": "co",
    "America/Detroit": "mi",
}
FEATURED = ["should-you-wait-federal-heat-pump-rebate", "9-questions-to-ask-heat-pump-installer", "is-my-contractors-rebate-quote-a-scam", "7-ways-to-lose-your-home-energy-rebate", "heat-pump-myths-busted",
            "7-california-heat-pump-rebates-you-can-stack", "fair-heat-pump-quote-canada", "why-insulation-first-energy-retrofit"]
GUIDES = [
    ("/guides/heat-pump-buyers-guide/", "Heat pump buyer's guide"), ("/guides/solar-battery-decision-guide/", "Solar or battery: which first?"),
    ("/insulation-rebates/", "Insulation rebates"), ("/heat-pump-water-heater/", "Heat pump water heaters"), ("/batteries/", "Home batteries compared"),
    ("/smart-thermostats/", "Smart thermostat rebates"), ("/furnace-rebates/", "Furnace and AC rebates"),
    ("/guides/rebate-stacking-explained/", "How rebate stacking works"), ("/guides/which-rebate-first/", "Which upgrade to do first"),
    ("/solar-quote-checker/", "Check a solar quote"), ("/rebate-deadlines/", "Rebate deadlines"), ("/programs/", "Every program and utility"),
    ("/blog/ma-ny-year-end-rebate-deadlines-2026/", "Massachusetts and New York year-end deadlines"), ("/calculator/", "Rebate calculators"),
    ("/programs/national-heat-pump-rebate/", "Canada's new federal heat pump rebate"),
]
HP_BY_PROVINCE = [("/ca/bc/heat-pump/", "BC"), ("/ca/on/heat-pump/", "Ontario"), ("/ca/ab/heat-pump/", "Alberta"), ("/ca/ns/heat-pump/", "Nova Scotia"),
                  ("/ca/qc/heat-pump/", "Quebec")]
CHANGE_TAG = {"coming": ("Coming up", "soon"), "new": ("New", "open"), "raised": ("Raised", "open"), "changed": ("Changed", "info"),
              "cut": ("Cut", "closed"), "paused": ("Paused", "soon"), "ended": ("Ended", "closed")}
ICON = {  # one stroke family, 24px grid, 1.7 stroke
    "heat-pump": '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="10" cy="12" r="4"/><path d="M10 8v8M6 12h8M17 9h1.5M17 12h1.5M17 15h1.5"/>',
    "insulation": '<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/><path d="M8 13c1.3 0 1.3 1.5 2.6 1.5s1.3-1.5 2.6-1.5 1.3 1.5 2.6 1.5M8 17c1.3 0 1.3 1.5 2.6 1.5s1.3-1.5 2.6-1.5 1.3 1.5 2.6 1.5"/>',
    "solar": '<path d="M5 6h14l2 9H3z"/><path d="M4 10.5h16M10 6l-1 9M14 6l1 9M12 15v4M8 19h8"/>',
    "battery": '<rect x="6" y="4" width="12" height="17" rx="2"/><path d="M10 2h4M12.8 8.5 10.5 13h3l-2.3 4.5"/>',
    "water-heater": '<rect x="6" y="3" width="12" height="18" rx="5"/><path d="M12 9c-1.6 2-2.4 3.2-2.4 4.3a2.4 2.4 0 0 0 4.8 0c0-1.1-.8-2.3-2.4-4.3z"/>',
    "ev": '<path d="M9 3v4M15 3v4M7 7h10v4a5 5 0 0 1-10 0z"/><path d="M12 16v2.5a2.5 2.5 0 0 0 2.5 2.5H18"/>',
    "thermostat": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5v4.5l3 2"/><path d="M7.5 17.5h9" opacity=".0"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "check": '<path d="M5 12.5 10 17l9-10"/>',
}


def icon(name, cls="hm-ic"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><use href="#hi-{name}"/></svg>'


def sprite():
    syms = "".join(f'<symbol id="hi-{k}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{v}</symbol>'
                   for k, v in ICON.items())
    return f'<svg width="0" height="0" style="position:absolute" aria-hidden="true">{syms}</svg>'


def load_facts():
    out = {}
    for f in (ROOT / "data" / "verified-facts").glob("*.json"):
        for x in json.loads(f.read_text())["facts"]:
            out[x["id"]] = x
    return out


FACTS = load_facts()


def money(n, cur=""):
    return f"${n:,.0f}" + (f" {cur}" if cur else "")


def amount_of(a):
    if "max" in a:
        return a["max"]
    if "by" in a:
        return max(a["values"].values())
    if "per" in a:
        return a["per"].get("cap", 0)
    return 0


def amount_text(a):
    if a.get("label"):
        return a["label"]
    n = amount_of(a)
    if n:
        return "Up to " + money(n)
    if "per" in a:
        return f'{money(a["per"]["rate"])} per {a["per"]["unit"]}'
    return ""


def lower_income(p):
    w = json.dumps([p.get("when", {}), p.get("when_any", [])])
    return any(k in w for k in ('"income_level"', '"income"', '"enhanced"')) or "income-qualified" in p["name"].lower()


def short_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.strftime('%b')} {d.day}, {d.year}"


def region_rows(code):
    """Best program per upgrade bucket for one region, from the calculator data (active programs, never an add-on)."""
    f = ROOT / "data" / "calc" / f"{code}.json"
    if not f.exists():
        return [], None
    sp = json.loads(f.read_text())
    best, fed = {}, None
    for p in sp["programs"]:
        fact = FACTS.get(p["fact"], {})
        st = fact.get("status")
        if p["fact"].startswith("federal-"):
            fed = fed or (p, fact)
            continue
        if st not in ("active", "upcoming") or p.get("requires") or CAT_OF.get(p.get("upgrade")) is None:
            continue
        txt = amount_text(p["amount"])
        if not txt:
            continue
        cat = CAT_OF[p["upgrade"]]
        slot = best.setdefault(cat, {})
        k = ("iq" if lower_income(p) else "all") if st == "active" else "soon"
        if k not in slot or amount_of(p["amount"]) > slot[k][0]:
            slot[k] = (amount_of(p["amount"]), p, fact, txt)
    rows = []
    for cat, label, _ in CATS:
        slot = best.get(cat)
        if not slot:
            continue
        main = slot.get("all") or slot.get("iq") or slot["soon"]
        _, p, fact, txt = main
        row = {"cat": cat, "label": label, "name": p["name"], "amt": txt, "n": amount_of(p["amount"]), "iq": main is slot.get("iq"),
               "st": fact["status"], "on": fact.get("verified_on", ""), "src": fact.get("source_url", "")}
        if "all" in slot and "iq" in slot and slot["iq"][0] > slot["all"][0]:
            row["more"] = "Lower incomes: " + slot["iq"][3][0].lower() + slot["iq"][3][1:]
            row["more_n"] = slot["iq"][0]
        rows.append(row)
    if fed:
        p, fact = fed
        rows.append({"cat": "heat-pump", "label": "Federal heat pump rebate", "name": "National Heat Pump Rebate (not open yet)",
                     "amt": p["amount"].get("label") or "", "n": 0, "iq": False, "st": fact.get("status", "upcoming"),
                     "on": fact.get("verified_on", ""), "src": "/programs/national-heat-pump-rebate/", "fed": True})
    return rows, sp


def region_data():
    out = []
    for r in regions.REGIONS:
        rows, sp = region_rows(r["code"])
        main = [x for x in rows if not x.get("fed") and x["st"] == "active"]
        top = max(main, key=lambda x: (not x["iq"], x["n"]), default=None)
        iq = max([(x.get("more_n", 0), x["label"]) for x in main] + [(x["n"], x["label"]) for x in main if x["iq"]], default=(0, ""))
        if top and iq[0] > top["n"] and not top["iq"]:
            top = {**top, "extra": f"Lower incomes: up to {money(iq[0])} for a {iq[1].lower()}"}
        out.append({"c": r["code"], "n": r["name"], "abbr": r["abbr"], "country": r["country"], "hub": f'/{r["path"]}/',
                    "cur": (sp or {}).get("currency", "CAD" if r["country"] == "ca" else "USD"), "rows": rows, "top": top,
                    "cities": r["cities"], "count": len(city_slugs(r["code"])), "blurb": r.get("home_blurb", ""),
                    "checked": max([x["on"] for x in main if x["on"]], default="")})
    return out


# ---------------------------------------------------------------- blocks

def pill(st):
    return f'<span class="rb-status rb-{st}">{STATUS[st][0]}</span>'


def sheet_row(x, cur):
    src = x["src"]
    ext = src.startswith("http")
    name = esc(x["name"])
    link = f'<a href="{esc(src)}"{" rel=\"noopener\"" if ext else ""}>{name}</a>' if src else name
    iq = '<span class="hm-iq">Lower incomes</span>' if x["iq"] else ""
    more = f'<span class="hm-row-m">{esc(x["more"])}</span>' if x.get("more") else ""
    return (f'<li class="hm-row" data-cat="{x["cat"]}">{icon(x["cat"])}<div class="hm-row-t"><b>{esc(x["label"])}</b>'
            f'<span class="hm-row-p">{link}{iq}</span>{more}</div><div class="hm-row-a"><span class="hm-amt">{esc(x["amt"])}</span>{pill(x["st"])}</div></li>')


def sheet(r):
    cur = "Canadian dollars" if r["cur"] == "CAD" else "US dollars"
    rows = "".join(sheet_row(x, r["cur"]) for x in r["rows"])
    checked = f'Last checked {short_date(r["checked"])}' if r["checked"] else "Checked monthly"
    return f'''<aside class="hm-sheet" aria-labelledby="hm-sheet-h" aria-live="polite">
      <div class="hm-sheet-head"><h2 id="hm-sheet-h" class="hm-sheet-title">Open now in <span data-s="name">{esc(r["n"])}</span></h2>
        <p class="hm-sheet-sub" data-s="sub">The biggest open rebate for each upgrade, in {cur}. Most homes get less, and each one has its own rules.</p></div>
      <ul class="hm-rows" data-s="rows">{rows}</ul>
      <div class="hm-sheet-foot"><span data-s="checked">{checked} against the official program pages.</span>
        <a href="{r["hub"]}" data-s="hub">All {esc(r["n"])} programs {icon("arrow", "hm-ar")}</a></div>
    </aside>'''


def hero(regs, total, picker):
    default = regs[0]
    popular = " ".join(f'<a href="{u}">{n}</a>' for u, n in [("/ca/on/toronto/", "Toronto"), ("/ca/bc/vancouver/", "Vancouver"), ("/ca/ab/calgary/", "Calgary"), ("/us/ma/boston/", "Boston"),
                                                             ("/us/ca/los-angeles/", "Los Angeles"), ("/us/co/denver/", "Denver")])  # the biggest cities we cover
    return f'''<!-- HOME-HERO-START -->
<section class="hm-hero" aria-labelledby="hm-h1">
  <div class="hm-wrap hm-hero-grid">
    <div class="hm-hero-copy">
      <a class="hm-news hm-for-ca" href="#federal-alert"><b>New in Canada</b> Ottawa's heat pump rebate: up to $10,000, opening early 2027. <span>Get the launch email</span></a>
      <a class="hm-news hm-for-us" href="#regions"><b>US update</b> The 30% federal tax credits ended. State and utility rebates are still open. <span>Pick your state</span></a>
      <h1 id="hm-h1">Find every home energy rebate in your city.</h1>
      <p class="hm-lede" data-city-count="{total}">Heat pumps, solar, batteries, insulation and more, in {total} cities across Canada and the US. Every amount links to the official program, and we check them every month.</p>
      <form id="hero-find" class="hm-find" action="/get-quotes/" method="get">
        <div class="hm-bar"><label class="sr-only" for="hf-prov">Province or state</label><select id="hf-prov" name="province" required><option value="">Province or state</option></select>
          <label class="sr-only" for="hf-city">City</label><select id="hf-city" name="city" required><option value="">City</option></select>
          <button type="submit" class="hm-btn">Go to my city {icon("arrow", "hm-ar")}</button></div>
        <p class="hm-find-note">Free. No email needed to see the numbers, and no sales calls.</p>
        <p class="hm-pop"><span>Popular:</span> {popular}</p>
      </form>
      <ul class="hm-proof">
        <li>{icon("check", "hm-ck")}Every amount has its source and check date</li>
        <li>{icon("check", "hm-ck")}Closed programs are shown as closed</li>
        <li>{icon("check", "hm-ck")}<span><a href="/installers/how-we-rank/">Installers ranked by Google reviews</a>. Nobody pays to be listed</span></li>
      </ul>
    </div>
  </div>
</section>
<script>(function(){{var D=window.HPR_CITIES={json.dumps(picker, separators=(",", ":"))};var p=document.getElementById("hf-prov"),c=document.getElementById("hf-city");
var G="",gl;D.forEach(function(r){{if(r.g!==G){{G=r.g;gl=document.createElement("optgroup");gl.label=G==="ca"?"Canada":"United States";p.appendChild(gl)}}var o=document.createElement("option");o.value=r.c;o.textContent=r.n;gl.appendChild(o)}});
function fill(){{c.textContent="";var h=document.createElement("option");h.value="";h.textContent="Choose your city";c.appendChild(h);
var r=D.filter(function(x){{return x.c===p.value}})[0];if(r)r.k.forEach(function(k){{var o=document.createElement("option");o.value=k[0];o.textContent=k[1];c.appendChild(o)}})}}
p.addEventListener("change",function(){{fill();if(window.HPR_SHEET&&p.value)window.HPR_SHEET(p.value)}});window.HPR_FILL=fill;
var U={{}};D.forEach(function(r){{r.k.forEach(function(k){{U[r.c+"|"+k[0]]=k[2]||""}})}});
document.getElementById("hero-find").addEventListener("submit",function(ev){{ev.preventDefault();if(!p.value||!c.value)return;var u=U[p.value+"|"+c.value]||("/get-quotes/?province="+encodeURIComponent(p.value)+"&city="+encodeURIComponent(c.value));
if(window.gtag)gtag("event","home_city_go",{{province:p.value}});location.href=u}});
p.addEventListener("change",function(){{}});}})();</script>
<!-- HOME-HERO-END -->'''


def federal():
    """Canada: the shared federal alert box (add_federal_alert.block, FED-ALERT markers, right after HOME-HERO-END, so the
    alert post-step can replace it in place). US: the 25C/25D note from fact general-8."""
    import add_federal_alert as fa
    box = fa.block(fa.HOME, anchor="federal-alert", big=True, wrap=True, slim=True).strip()  # same call as add_federal_alert.canadian_pages()
    us = FACTS["general-8-us-federal-25c-25d-tax-credits"]
    return f'''{box}
<section class="hm-usfed" aria-labelledby="hm-usfed-h">
  <div class="hm-wrap hm-usfed-in">
    <h2 id="hm-usfed-h">In the US, the federal tax credits ended {pill(us["status"])}</h2>
    <p>The 25C and 25D tax credits, worth 30% of the cost, only cover work finished by December 31, 2025. State, city and utility rebates are still open, and you can see them for your state below. <a href="/programs/federal-tax-credits-2026/">What changed</a> &middot; <a href="{esc(us["source_url"])}" rel="noopener">IRS page</a></p>
  </div>
</section>'''


def how(regs=None):
    steps = [("modern-home", "A modern white house at dusk", "Pick your city.", "Rebates depend on where you live and who sends your power bill, so we start there."),
             ("solar-roof", "Solar panels on a tiled house roof", "See every rebate, open or closed.", "Each one shows the amount, who qualifies, its status and a link to the official page."),
             ("duplex-home", "A single-story duplex house with a front porch", "Compare top-rated installers.", "We rank local companies by Google reviews. You choose who to call, and we never sell your details.")]
    lis = "".join(f'<li><img src="/assets/learn/{f}-640.webp" width="640" height="427" alt="{esc(alt)}" loading="lazy"><b>{esc(h)}</b> {esc(b)}</li>' for f, alt, h, b in steps)
    return f'''<section class="hm-sec hm-how" aria-labelledby="hm-how-h">
  <div class="hm-wrap">
    <h2 id="hm-how-h">How it works, and how we keep it honest</h2>
    <ol class="hm-steps hm-steps-photos">{lis}</ol>
    {trust_inner(regs) if regs else ""}
  </div>
</section>'''


PLAN = [("heat-pump", "heat-pumps", "Heat pumps", "heat-pump-house"), ("solar", "solar", "Solar panels", "solar-roof"), ("battery", "batteries", "Home battery", "modern-home"),
        ("insulation", "insulation", "Insulation", "rebate-plans"), ("water-heater", "water-heating", "Water heating", "kitchen"),
        ("ev", "ev-chargers", "EV chargers", "ev-charger"), ("thermostat", "smart-thermostats", "Smart thermostats", "thermostat")]


def planning(regs):
    amt = {}  # no place is assumed: amounts appear once a province or state is picked
    tiles = "".join(
        f'<a class="hm-tile" href="/learn/{slug}/" data-cat="{cat}"><img src="/assets/learn/{img}-640.webp" width="640" height="427" alt="" loading="lazy">'
        f'<span class="hm-tile-b"><b>{esc(name)}</b><em data-amt>See the guide</em></span></a>' for cat, slug, name, img in PLAN)
    return f'''<section class="hm-sec hm-plan" aria-labelledby="hm-plan-h">
  <div class="hm-wrap">
    <h2 id="hm-plan-h">What are you planning?</h2>
    <p class="hm-intro">Pick an upgrade for a plain guide and the biggest rebate open in <span data-plan-where>your province or state</span> today. Pick yours above to see it.</p>
    <div class="hm-tiles">{tiles}</div>
  </div>
</section>'''


def quiz_section():
    d = lk.articles()["7-ways-to-lose-your-home-energy-rebate"]
    return f'''<section class="hm-sec hm-quiz" aria-label="Quick quiz"><div class="hm-wrap">{lk.quiz("7-ways-to-lose-your-home-energy-rebate", d["quiz"])}</div></section>'''


def installers_strip():
    return '''<section class="hm-banner" aria-labelledby="hm-inst-h">
  <div class="hm-wrap hm-banner-in">
    <div><h2 id="hm-inst-h">Looking for an installer?</h2><p>See the top-rated companies in your city, ranked by Google reviews. Nobody pays to rank higher.</p></div>
    <a href="/installers/" class="hm-btn">Find top-rated installers {icon("arrow", "hm-ar")}</a>
  </div>
</section>'''


def learn():
    cards = lk.not_ready_row("heat-pump", key="/", heading="Quick reads and quizzes", sub="Learn the rules in five minutes, then pick your city.")
    ups = " &middot; ".join(f'<a href="/learn/{s}/">{n}</a>' for s, n in [("heat-pumps", "Heat pumps"), ("solar", "Solar"), ("batteries", "Batteries"), ("insulation", "Insulation"), ("water-heating", "Water heating")])
    return f'''<section class="hm-sec hm-learn" aria-labelledby="hm-learn-h">
  <div class="hm-wrap">{cards.replace("<h2>", '<h2 id="hm-learn-h">', 1)}
    <p class="hm-hp"><b>Learn by upgrade:</b> {ups}</p>
  </div>
</section>'''


def reg_row(r):
    t = r["top"]
    if t:
        amt = esc(t["amt"])
        detail = esc(t["name"]) + (' <span class="hm-iq">Lower incomes</span>' if t["iq"] else "")
        if t.get("extra"):
            detail += f' <span class="hm-reg-m">{esc(t["extra"])}</span>'
    else:
        amt, detail = "", esc(r["blurb"])
    cities = " ".join(f'<a href="{h}">{esc(n)}</a>' for h, n in r["cities"][:4])
    more = f'<a href="{r["hub"]}" class="hm-more">All {r["count"]}</a>' if r["count"] > 4 else ""
    return (f'<li class="hm-reg" data-c="{r["c"]}"><div class="hm-reg-main"><a href="{r["hub"]}" class="hm-reg-name">{esc(r["n"])}</a>'
            f'<span class="hm-reg-count">{r["count"]} {"city" if r["count"] == 1 else "cities"}</span></div>'
            f'<div class="hm-reg-top"><span class="hm-amt">{amt}</span> <span class="hm-cur">{r["cur"] if amt.startswith("Up to $") else ""}</span>'
            f'<span class="hm-reg-p">{detail}</span></div>'
            f'<div class="hm-reg-cities">{cities}{more}</div></li>')


def region_ledger(regs):
    """Compare places (2026-10-25): one row per province or state, one column per upgrade, the biggest open amount in each cell.
    The hero already gets a visitor to a city; this section is for comparing places and browsing to a region hub."""
    cols = [(c, l) for c, l, _ in CATS]
    head = '<th scope="col">Place</th>' + "".join(f'<th scope="col">{icon(c)}<span>{esc(l)}</span></th>' for c, l in cols)
    body = ""
    for country, name, cur, unit in (("ca", "Canada", "CAD", "provinces and territories"), ("us", "United States", "USD", "states")):
        rs = [r for r in regs if r["country"] == country]
        best = {c: max([next((x["n"] for x in r["rows"] if x["cat"] == c and not x.get("fed")), 0) for r in rs] or [0]) for c, _ in cols}
        body += f'<tr class="hm-mx-grp"><th colspan="{len(cols) + 1}" scope="colgroup">{name} <span>amounts in {cur}, {len(rs)} {unit}</span></th></tr>'
        for r in rs:
            cells = ""
            for c, _ in cols:
                x = next((x for x in r["rows"] if x["cat"] == c and not x.get("fed")), None)
                if not x:
                    cells += '<td class="hm-mx-none"><span aria-label="No open program found">&ndash;</span></td>'
                    continue
                a = x["amt"][len("Up to "):] if x["amt"].startswith("Up to ") else x["amt"]
                hot = ' class="hm-mx-hot"' if x["n"] > 0 and x["n"] == best[c] else ""
                cells += f'<td{hot}><a href="{r["hub"]}" title="{esc(x["name"])}">{esc(a)}</a></td>'
            body += f'<tr><th scope="row"><a href="{r["hub"]}">{esc(r["n"])}</a><span>{r["count"]} {"city" if r["count"] == 1 else "cities"}</span></th>{cells}</tr>'
    return f'''<section class="hm-sec hm-ledger" id="regions" aria-labelledby="hm-reg-h">
  <div class="hm-wrap">
    <h2 id="hm-reg-h">Compare places</h2>
    <p class="hm-intro">The biggest open rebate for each upgrade, by province and state. The highest in each column is marked. Most homes get less, and each program has its own rules. Tap a place to see its cities.</p>
    <div class="hm-mx-wrap"><table class="hm-mx"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>
  </div>
</section>'''


def powerscore():
    d = json.loads((ROOT / "powerscore-data.json").read_text())
    names = regions.ABBR_BY_PATH
    cols = ""
    for country in ("Canada", "United States"):
        top = [c for c in d["leaderboard_overall"] if c["country"] == country][:5]
        lis = "".join(f'<li><a href="{c["url"]}"><span class="hm-ps-city">{esc(c["label"])}, {names[c["region"]]}</span>'
                      f'<span class="hm-ps-bar" style="--s:{round(c["overall"])}"></span><b>{round(c["overall"])}</b></a></li>' for c in top)
        cols += f'<div class="hm-ps-{"ca" if country == "Canada" else "us"}"><h3>{country}</h3><ol class="hm-ps">{lis}</ol></div>'
    n = d["stats"]["total_cities"]
    return f'''<section class="hm-sec hm-psec" aria-labelledby="hm-ps-h">
  <div class="hm-wrap">
    <h2 id="hm-ps-h">Which cities have the most rebate money open?</h2>
    <p class="hm-intro">PowerScore rates all {n} cities from 0 to 100 on how much rebate money is open today, how many programs stack, and whether they are open, paused or closed.</p>
    <div class="hm-ps-cols">{cols}</div>
    <p><a href="/powerscore/" class="hm-btn-line">See the full leaderboard</a></p>
  </div>
</section>'''


def changes():
    from build_rebate_deadlines import open_rows, fmt, REGIONS as DL_REGIONS
    data = json.loads((ROOT / "rebate-tracker" / "changes.json").read_text())
    d = data["entries"]
    reg_name = {**regions.NAME_BY_ABBR, "US": "United States", "CA-FED": "Canada"}
    hub = {**regions.HUB_URL, "CA-FED": "/programs/national-heat-pump-rebate/"}
    coming = sorted([x for x in d if x["status"] == "coming"], key=lambda x: x["date"])
    recent = sorted([x for x in d if x["status"] != "coming"], key=lambda x: x["date"], reverse=True)[:5]
    items = ""
    for x in coming[:1] + recent[:2]:
        lab, tone = CHANGE_TAG[x["status"]]
        reg = esc(reg_name.get(x["region"], x["region"]))
        where = f'<a href="{hub[x["region"]]}">{reg}</a>' if x["region"] in hub else reg
        items += (f'<li><span class="hm-chg hm-chg-{tone}">{lab}</span><div><b>{esc(x["program"])}</b>'
                  f'<span class="hm-meta">{where} &middot; {esc(x["date"])}</span><p>{esc(x["change"])}</p></div></li>')
    dl = "".join(f'<li class="hf-close" data-deadline="{x["date"]}"><b class="hf-when">{esc(fmt(x["date"]))}</b>'
                 f'<a href="{x["page"]}">{esc(x["program"])}</a><span class="hm-meta">{esc(DL_REGIONS[x["region"]])}</span></li>' for x in open_rows()[:3])
    return f'''<section class="hm-sec hm-changes" aria-labelledby="hm-chg-h">
  <div class="hm-wrap hm-chg-grid">
    <div>
      <h2 id="hm-chg-h">What changed lately</h2>
      <p class="hm-intro">Programs open, change and close all year. We check each one against its own page. Last full check: {esc(short_date(data["checked"]))}.</p>
      <ul class="hm-feed">{items}</ul>
      <p><a href="/rebate-tracker/" class="hm-btn-line">See every change</a></p>
    </div>
    <aside class="hm-deadlines" aria-labelledby="hm-dl-h">
      <h3 id="hm-dl-h">Deadlines coming up</h3>
      <ul>{dl}</ul>
      <p><a href="/rebate-deadlines/">All upcoming deadlines</a></p>
    </aside>
  </div>
</section>
<script>document.querySelectorAll(".hf-close").forEach(function(e){{var t=new Date(e.dataset.deadline+"T23:59:59");var d=Math.ceil((t-new Date())/864e5);var w=e.querySelector(".hf-when");if(d<0)e.remove();else w.textContent+=" \\u00b7 "+(d===0?"today":d+" day"+(d>1?"s":"")+" left")}});</script>'''


def trust_inner(regs):
    n = len(FACTS)
    shut = sum(1 for x in FACTS.values() if x.get("status") in ("closed", "paused", "waitlist"))
    latest = max(x.get("verified_on", "") for x in FACTS.values())
    return f'''<div class="hm-trustbox">
    <div class="hm-trust-grid">
      <p><b>{n:,}</b>rebate amounts and rules we track. Each one has the official page we read it on and the date we read it. The latest check was {esc(short_date(latest))}.</p>
      <p><b>{shut}</b>of them are closed, paused or on hold right now. We show them that way instead of hiding them, so you know what not to count on.</p>
      <p><b>$0</b>paid by any installer to be listed or to rank higher. We rank by Google reviews only, and our <a href="/installers/how-we-rank/">ranking page</a> will say so if that ever changes.</p>
    </div>
    <p class="hm-founder">HomePowerRebate is independent. It is not run by a utility, an installer or a government. It was built by <a href="/about">Sam Menard</a>. Spot a mistake? <a href="/contact/">Tell us</a> and we will fix it.</p>
</div>'''


def guides():
    idx = {p["slug"]: p for s in json.loads((ROOT / "data" / "blog-index.json").read_text())["sections"] for p in s["posts"]}
    from build_blog_index import card as post_card
    posts = "".join(post_card(idx[s]) for s in FEATURED if s in idx)
    links = "".join(f'<li><a href="{h}">{esc(t)}</a></li>' for h, t in GUIDES)
    js = ("(function(){var r=document.getElementById('hm-guides-row');if(!r)return;var c=r.querySelector('.bx-car');r.querySelectorAll('.bx-arrow').forEach(function(b){b.addEventListener('click',"
          "function(){c.scrollBy({left:(b.dataset.d==='1'?1:-1)*Math.min(c.clientWidth*.9,720),behavior:'smooth'})})})})();")
    return f'''<section class="hm-sec hm-guides" aria-labelledby="hm-g-h">
  <div class="hm-wrap">
    <div class="bx-row hm-g-row" id="hm-guides-row"><div class="bx-head"><div><h2 id="hm-g-h">Read this before you sign anything</h2><p>Short guides on what to check, what to ask and what to avoid.</p></div>
      <div class="bx-ctl"><button type="button" class="bx-arrow" data-d="-1" aria-label="Scroll left">&larr;</button><button type="button" class="bx-arrow" data-d="1" aria-label="Scroll right">&rarr;</button></div></div>
      <div class="bx-car">{posts}</div></div>
    <h3>Guides by upgrade</h3>
    <ul class="hm-links">{links}</ul>
    <p class="hm-hp">Heat pump rebates by province: {" &middot; ".join(f'<a href="{h}">{t}</a>' for h, t in HP_BY_PROVINCE)}</p>
    <p><a href="/blog/" class="hm-btn-line">Read all articles</a></p>
  </div>
</section>
<script>{js}</script>'''


def faq_items(regs, total):
    ca = [r["n"] for r in regs if r["country"] == "ca"]
    us = [r["n"] for r in regs if r["country"] == "us"]
    ser = lambda xs: ", ".join(xs[:-1]) + " and " + xs[-1]  # noqa: E731
    return [
        ("Is HomePowerRebate free?",
         "Yes. It is free for homeowners. Installers do not pay to be listed or to rank higher, and we do not charge referral fees right now."),
        ("Are you part of the government or a utility?",
         "No. We are independent. We read each program's official page and link to it next to every amount, so you can check it yourself."),
        ("How do you know the amounts are right?",
         f"We keep {len(FACTS):,} rebate amounts and rules, each with its source page and the date we read it, and we re-read them every month. When a program closes or pauses, we mark it that way."),
        ("Can I get Canada's new federal heat pump rebate now?",
         "Not yet. Ottawa plans up to $10,000 for households below the median income and $2,000 for other eligible homeowners, starting in early 2027. The income line is not published yet. You can sign up above to get an email when it opens."),
        ("Is there still a US federal tax credit for heat pumps or solar?",
         "No. The 25C and 25D tax credits ended on December 31, 2025, and only cover work finished before then. State, city and utility rebates are still open in many places."),
        ("Which places do you cover?",
         f"{total} cities in {len(regs)} provinces and states. In Canada: {ser(ca)}. In the US: {ser(us)}."),
        ("How do you rank installers?",
         "By Google rating and number of reviews, so lots of good reviews count more than a few. Companies cannot pay to move up or to hide reviews."),
    ]


def faq(items):
    qs = "".join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in items)
    return f'''<section class="hm-sec hm-faq" aria-labelledby="hm-faq-h">
  <div class="hm-wrap hm-narrow">
    <h2 id="hm-faq-h">Questions people ask us</h2>
    {qs}
  </div>
</section>'''


def close():
    return f'''<section class="hm-close" aria-labelledby="hm-close-h">
  <div class="hm-wrap">
    <h2 id="hm-close-h">See what your home can get.</h2>
    <p>Pick your city. It takes about 20 seconds, and you do not need to give your email.</p>
    <a href="/get-quotes/" class="hm-btn">See my rebates {icon("arrow", "hm-ar")}</a>
  </div>
</section>'''


def page_script(regs):
    data = {r["c"]: {"n": r["n"], "hub": r["hub"], "cur": r["cur"], "checked": short_date(r["checked"]) if r["checked"] else "",
                     "rows": [{**{k: x[k] for k in ("cat", "label", "name", "amt", "iq", "st", "src")}, **({"more": x["more"]} if x.get("more") else {}), **({"fed": 1} if x.get("fed") else {})} for x in r["rows"]]} for r in regs}
    labels = {k: v[0] for k, v in STATUS.items()}
    return f'''<script>(function(){{var R={json.dumps(data, separators=(",", ":"))},L={json.dumps(labels, separators=(",", ":"))},TZ={json.dumps(TZ, separators=(",", ":"))};
function e(s){{return String(s).replace(/[&<>"]/g,function(c){{return{{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]}})}}
function ic(n,c){{return '<svg class="'+(c||"hm-ic")+'" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><use href="#hi-'+n+'"/></svg>'}}
function row(x){{var s=x.src,a=s?'<a href="'+e(s)+'"'+(s.indexOf("http")===0?' rel="noopener"':"")+'>'+e(x.name)+'</a>':e(x.name);
return '<li class="hm-row" data-cat="'+x.cat+'">'+ic(x.cat)+'<div class="hm-row-t"><b>'+e(x.label)+'</b><span class="hm-row-p">'+a+(x.iq?'<span class="hm-iq">Lower incomes</span>':"")+'</span>'+(x.more?'<span class="hm-row-m">'+e(x.more)+'</span>':"")+'</div><div class="hm-row-a"><span class="hm-amt">'+e(x.amt)+'</span><span class="rb-status rb-'+x.st+'">'+L[x.st]+'</span></div></li>'}}
var sh=document.querySelector(".hm-sheet");
window.HPR_SHEET=function(c){{var r=R[c];if(!r)return;document.querySelectorAll(".hm-tile").forEach(function(tl){{var x=r.rows.filter(function(y){{return y.cat===tl.dataset.cat&&!y.fed&&y.label.indexOf("Federal")<0}})[0];tl.querySelector("[data-amt]").textContent=x?x.amt:"See the guide"}});var w=document.querySelector("[data-plan-where]");if(w)w.textContent=r.n;if(!sh)return;var q=function(k){{return sh.querySelector('[data-s="'+k+'"]')}};
q("name").textContent=r.n;q("sub").textContent="The biggest open rebate for each upgrade, in "+(r.cur==="CAD"?"Canadian":"US")+" dollars. Most homes get less, and each one has its own rules.";
q("rows").innerHTML=r.rows.map(row).join("");q("checked").textContent=(r.checked?"Last checked "+r.checked:"Checked monthly")+" against the official program pages.";
var h=q("hub");h.href=r.hub;h.firstChild.textContent="All "+r.n+" programs ";sh.classList.remove("hm-in");void sh.offsetWidth;sh.classList.add("hm-in")}};
var z="";try{{z=Intl.DateTimeFormat().resolvedOptions().timeZone||""}}catch(x){{}}
var g=TZ[z],p=document.getElementById("hf-prov"),K=(document.documentElement.getAttribute("data-country")||"").toLowerCase();
if(K==="us"||K==="ca"){{var cur=K==="us"?"USD":"CAD";if(!g||!R[g]||R[g].cur!==cur){{g="";for(var k in R){{if(R[k].cur===cur){{g=k;break}}}}}}}}
document.querySelectorAll(".hm-tab").forEach(function(b){{b.addEventListener("click",function(){{var c=b.dataset.cat;
document.querySelectorAll(".hm-tab").forEach(function(x){{x.setAttribute("aria-pressed",x===b?"true":"false")}});
document.querySelectorAll(".hm-reg").forEach(function(li){{var r=R[li.dataset.c];if(!r)return;var rows=r.rows.filter(function(x){{return !x.fed&&x.label.indexOf("Federal")<0}});
var x=c?rows.filter(function(y){{return y.cat===c}})[0]:li._top;if(!li._top)li._top=null;
var t=li.querySelector(".hm-reg-top");if(!li._html)li._html=t.innerHTML;
if(!c){{t.innerHTML=li._html;li.classList.remove("hm-none");return}}
if(!x){{t.innerHTML='<span class="hm-reg-p">No open rebate found for this upgrade.</span>';li.classList.add("hm-none");return}}
li.classList.remove("hm-none");t.innerHTML='<span class="hm-amt">'+e(x.amt)+'</span> <span class="hm-cur">'+(x.amt.indexOf("Up to $")===0?r.cur:"")+'</span><span class="hm-reg-p">'+e(x.name)+(x.iq?' <span class="hm-iq">Lower incomes</span>':"")+(x.more?' <span class="hm-reg-m">'+e(x.more)+'</span>':"")+(x.st!=="active"?' <span class="rb-status rb-'+x.st+'">'+L[x.st]+'</span>':"")+'</span>'}})}})}});
}})();</script>'''


# ---------------------------------------------------------------- head

def head(regs, total, faqs, modified, keep):
    ca = [r for r in regs if r["country"] == "ca"]
    us = [r for r in regs if r["country"] == "us"]
    title = "Home Energy Rebates by City, Canada & US | HomePowerRebate"
    desc = (f"See every heat pump, solar, battery and insulation rebate open in your city, with its source and the date we checked it. "
            f"{total} cities in Canada and the US.")
    og_title = "Every home energy rebate in your city, checked monthly"
    area = [{"@type": "AdministrativeArea", "name": f'{r["n"]}, {"Canada" if r["country"] == "ca" else "United States"}'} for r in ca + us]
    org = {"@type": "Organization", "@id": f"{SITE}/#org", "name": "HomePowerRebate", "alternateName": ["Home Power Rebate", "HomePowerRebate.com"],
           "url": f"{SITE}/", "logo": f"{SITE}/logo.png", "email": "hello@homepowerrebate.com",
           "description": (f"Independent guide to home energy rebates in {total} cities across Canada and the United States. Every amount links to the "
                           "official program and is re-checked monthly. Installers are ranked by Google reviews; nobody pays to be listed."),
           "sameAs": ["https://www.youtube.com/@HomePowerRebate", "https://www.facebook.com/profile.php?id=61592376033225"],
           "foundingDate": "2026", "founder": {"@type": "Person", "@id": f"{SITE}/about#sam-menard", "name": "Sam Menard", "url": f"{SITE}/about",
                                                "sameAs": ["https://www.linkedin.com/in/sammenard/"]},
           "areaServed": area, "contactPoint": {"@type": "ContactPoint", "url": f"{SITE}/contact/", "contactType": "customer support", "availableLanguage": "English"}}
    site = {"@type": "WebSite", "@id": f"{SITE}/#website", "name": "HomePowerRebate", "url": f"{SITE}/", "publisher": {"@id": f"{SITE}/#org"},
            "inLanguage": "en", "potentialAction": {"@type": "SearchAction", "target": f"{SITE}/search/?q={{search_term_string}}", "query-input": "required name=search_term_string"}}
    page = {"@type": "WebPage", "@id": f"{SITE}/#webpage", "url": f"{SITE}/", "name": title, "description": desc, "isPartOf": {"@id": f"{SITE}/#website"},
            "about": {"@id": f"{SITE}/#org"}, "dateModified": modified, "inLanguage": "en",
            "speakable": {"@type": "SpeakableSpecification", "cssSelector": ["#hm-h1", ".hm-lede", ".hm-faq details p"]}}
    regions_list = {"@type": "ItemList", "name": "Provinces and states covered by HomePowerRebate", "numberOfItems": len(regs),
                    "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": f'{r["n"]}, {"Canada" if r["country"] == "ca" else "United States"}',
                                         "url": f'{SITE}{r["hub"]}'} for i, r in enumerate(ca + us)]}
    faqld = {"@type": "FAQPage", "@id": f"{SITE}/#faq", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    ld = json.dumps({"@context": "https://schema.org", "@graph": [org, site, page, regions_list, faqld]}, ensure_ascii=False)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script>{country_script()}</script>
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="{SITE}/">
<meta name="google-site-verification" content="Yyio4MZpG_tVGKuE9hbSKTYb0Yo9LFWoNF_3_UxVkGE" />
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-W33G4TGRHD');
</script>
<!-- Ahrefs Web Analytics -->
<script src="https://analytics.ahrefs.com/analytics.js" data-key="jh0L6rKfXn+1HhCOGF8fXQ" async></script>
<meta property="og:title" content="{esc(og_title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}/">
<meta property="og:site_name" content="HomePowerRebate">
<meta property="og:locale" content="en_CA">
<meta property="og:locale:alternate" content="en_US">
<meta name="twitter:title" content="{esc(og_title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="author" content="Sam Menard">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{keep.get("font", "")}
<script type="application/ld+json">{ld}</script>
{keep.get("css", "")}
<meta name="theme-color" content="#08363f">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
{keep.get("og", "")}
</head>'''


US_ZONES = ("America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "America/Phoenix", "America/Detroit",
            "America/Anchorage", "America/Boise", "Pacific/Honolulu", "America/Indiana/", "America/Kentucky/", "America/North_Dakota/")
CA_ZONES = ("America/Vancouver", "America/Edmonton", "America/Winnipeg", "America/Regina", "America/Toronto", "America/Halifax",
            "America/Glace_Bay", "America/Moncton", "America/St_Johns", "America/Whitehorse", "America/Yellowknife", "America/Iqaluit")


def country_script():
    """Sets <html data-country="US|CA"> before first paint, so home.css can put the visitor's country first (US: the tax
    credit note and US states first, the Canadian alert box after the regions; Canada: the reverse). Both countries' content
    is always in the page; only the order changes. The edge function sets the attribute from the IP; this is the fallback."""
    return ('(function(){var d=document.documentElement,q=(location.search.match(/[?&]country=(us|ca)/i)||[])[1];'
            'if(q){d.setAttribute("data-country",q.toUpperCase());return}if(d.getAttribute("data-country"))return;'
            'var z="";try{z=Intl.DateTimeFormat().resolvedOptions().timeZone||""}catch(e){}'
            f'var U={json.dumps(US_ZONES, separators=(",", ":"))},C={json.dumps(CA_ZONES, separators=(",", ":"))};'
            'function m(a){return a.some(function(x){return x.slice(-1)==="/"?z.indexOf(x)===0:z===x})}'
            'if(m(U))d.setAttribute("data-country","US");else if(m(C))d.setAttribute("data-country","CA")})();')


def between(s, a, b, inclusive=True):
    i = s.find(a)
    if i < 0:
        return ""
    j = s.index(b, i) + len(b)
    return s[i:j] if inclusive else s[i + len(a):j - len(b)]


def main():
    f = ROOT / "index.html"
    old = f.read_text(encoding="utf-8")
    keep = {
        "font": between(old, "<!-- FONT-PRELOAD-START -->", "<!-- FONT-PRELOAD-END -->"),
        "og": between(old, "<!-- OG-CARD-START -->", "<!-- OG-CARD-END -->"),
        "css": (re.search(r'<link rel="stylesheet" href="/assets/site\.css\?v=[0-9a-f]+" data-hpr-site-css>', old) or [""])[0],
    }
    nav = between(old, "<!-- CANONICAL-NAV-START -->", "<!-- CANONICAL-NAV-END -->")
    foot = between(old, "<!-- CANONICAL-FOOTER-START -->", "<!-- CANONICAL-FOOTER-END -->")
    js = between(old, "<script>\n/* CANONICAL-NAV-FOOTER-JS-START */", "/* CANONICAL-NAV-FOOTER-JS-END */\n</script>")
    regs = region_data()
    hubs = {code: {h.strip("/").split("/")[-1]: h for h, _ in regions.BY_CODE[code]["cities"]} for code, _, _, _ in REG}
    picker = sorted(({"c": code, "n": name, "g": regions.COUNTRY_BY_CODE[code], "k": [[c, OV.get(c, c.replace("-", " ").title()), hubs[code].get(c, "")] for c in city_slugs(code)]} for code, name, _, _ in REG),
                    key=lambda r: regions.order_key(r["c"]))  # Canada, then the United States, A to Z
    total = sum(len(r["k"]) for r in picker)
    faqs = faq_items(regs, total)
    modified = max(x.get("verified_on", "") for x in FACTS.values())
    body = "\n".join([
        hero(regs, total, picker), federal(), quiz_section(), planning(regs), installers_strip(), powerscore(), region_ledger(regs), changes(), how(regs), guides(), faq(faqs), close(),
    ])
    out = (head(regs, total, faqs, modified, keep) + '\n<body class="tpl-home">\n<a class="skip-link" href="#main">Skip to main content</a>\n'
           + sprite() + "\n" + nav + '\n<main id="main" tabindex="-1" class="layout-wide layout-home">\n' + body + "\n</main>\n" + foot + "\n"
           + page_script(regs) + "\n" + js + "\n</body>\n</html>\n")
    f.write_text(out, encoding="utf-8")
    print(f"Homepage built: {len(regs)} regions, {total} cities, {sum(len(r['rows']) for r in regs)} sheet rows")


if __name__ == "__main__":
    main()
