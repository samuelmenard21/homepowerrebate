#!/usr/bin/env python3
"""The energy advisor and home energy auditor profile page (2026-10-20 redesign), one template for every company.

Called by build_advisor_directory.profile(). Layout: dark hero with a drawn house, a facts strip, then a main column
(call the advisor first, what an advisor does, why the visit matters, rebates, rankings, where they work, services,
what we checked, FAQ) beside a sticky contact card, and a closing call to action. Design: _partials/templates/advisor.css
(body class tpl-advisor, set by the restamp from the main element's class "ad-page").

Rules this page keeps:
- Rebate cards come from data/advisor-rebates.json: each names a verified fact, only active facts are shown, and the
  amount, status, date and source come from the facts file. A region with no entry shows no rebate card.
- Nothing says a company confirmed anything. Google data is shown with attribution and never goes into structured data.
- The generic sections describe what registered advisors do, not what this company offers; the page says so.
"""
import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import page_kit
import status_pills

ROOT = Path(__file__).resolve().parent.parent
e = html.escape
REBATES = json.loads((ROOT / "data" / "advisor-rebates.json").read_text())
FACTS = page_kit.FACTS
CA_REGIONS = {"ON": "on", "BC": "bc", "NS": "ns", "NL": "nl", "AB": "ab"}
NRCAN_COST_FACT = FACTS["general-22-nrcan-energuide-evaluation-cost"]
# the article that explains each region's assessment rebate (data/advisors/*.json), linked from the rebate card
GUIDES = {"ON": "/blog/ontario-home-renovation-savings-energy-audit-first/", "BC": "/blog/bc-heat-pump-rebate-energy-advisor-heat-load-calculation/",
          "NS": "/blog/nova-scotia-home-energy-assessment-rebates-explained/", "NL": "/blog/newfoundland-air-sealing-blower-door-test-takecharge/"}
US_GUIDE = "/blog/free-utility-home-energy-assessment-before-private-auditor/"

SYMBOLS = """<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">
<symbol id="ad-report" viewBox="0 0 24 24"><path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5"/><path d="M9 13l3-2.5 3 2.5M10 12.8V17h4v-4.2"/></symbol>
<symbol id="ad-heat" viewBox="0 0 24 24"><path d="M10 14.5V5a2 2 0 014 0v9.5a4 4 0 11-4 0z"/><path d="M12 9v7"/></symbol>
<symbol id="ad-fan" viewBox="0 0 24 24"><circle cx="12" cy="12" r="1.8"/><path d="M12 10.2C12 6 10 4 7.5 4 6 4 6 6.5 8 8.5c1 1 2.4 1.5 4 1.7zM13.8 12c4.2 0 6.2-2 6.2-4.5 0-1.5-2.5-1.5-4.5.5-1 1-1.5 2.4-1.7 4zM12 13.8c0 4.2 2 6.2 4.5 6.2 1.5 0 1.5-2.5-.5-4.5-1-1-2.4-1.5-4-1.7zM10.2 12c-4.2 0-6.2 2-6.2 4.5 0 1.5 2.5 1.5 4.5-.5 1-1 1.5-2.4 1.7-4z"/></symbol>
<symbol id="ad-plan" viewBox="0 0 24 24"><path d="M3 20h18M5 20V9l7-5 7 5v11"/><path d="M9 20v-6h6v6M9 9h6"/></symbol>
<symbol id="ad-ruler" viewBox="0 0 24 24"><path d="M3 16L16 3l5 5L8 21z"/><path d="M7 12l2 2M10 9l2 2M13 6l2 2"/></symbol>
<symbol id="ad-eye" viewBox="0 0 24 24"><path d="M2 12s3.5-6.5 10-6.5S22 12 22 12s-3.5 6.5-10 6.5S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></symbol>
<symbol id="ad-phone" viewBox="0 0 24 24"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 005 5L15 13l5 2v4a2 2 0 01-2 2A16 16 0 013 6a2 2 0 012-2z"/></symbol>
<symbol id="ad-stop" viewBox="0 0 24 24"><path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17v.01"/></symbol>
</svg>"""

HOUSE = """<svg viewBox="0 0 480 420" role="img" aria-label="Cross-section of a house with arrows showing heat escaping through the attic, walls, windows, door and floor">
<defs><pattern id="ad-grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0v24" fill="none" stroke="#ffffff" stroke-opacity=".06"/></pattern>
<pattern id="ad-hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0v10" stroke="#e88a2e" stroke-opacity=".55" stroke-width="2"/></pattern></defs>
<rect width="480" height="420" rx="18" fill="url(#ad-grid)"/>
<g fill="none" stroke="#cfe3e1" stroke-width="2.5" stroke-linejoin="round"><path d="M76 178L240 70l164 108"/><rect x="96" y="178" width="288" height="166"/><path d="M60 344h360"/>
<rect x="124" y="214" width="62" height="56" fill="#08363f"/><path d="M155 214v56M124 242h62"/><rect x="294" y="214" width="62" height="56" fill="#08363f"/><path d="M325 214v56M294 242h62"/></g>
<path d="M104 178l136-90 136 90z" fill="url(#ad-hatch)"/><rect x="214" y="262" width="52" height="82" fill="none" stroke="#e88a2e" stroke-width="2.5"/><rect x="60" y="344" width="360" height="12" fill="#1b6b79"/>
<path class="ad-heat" d="M240 60V26"/><path class="ad-heat" d="M170 100L146 70" style="animation-delay:-.6s"/><path class="ad-heat" d="M310 100l24-30" style="animation-delay:-1.2s"/>
<path class="ad-heat" d="M96 250H52" style="animation-delay:-.4s"/><path class="ad-heat" d="M384 250h44" style="animation-delay:-.9s"/>
<path class="ad-heat" d="M124 236l-30-40" style="animation-delay:-1.4s"/><path class="ad-heat" d="M356 236l30-40" style="animation-delay:-.2s"/><path class="ad-heat" d="M240 356v36" style="animation-delay:-1s"/>
<g font-family="Inter Tight,sans-serif" font-size="19" font-weight="600" fill="#fff"><text x="256" y="40">Attic</text><text x="8" y="236">Walls</text><text x="394" y="226">Windows</text><text x="256" y="388">Floor and air leaks</text></g></svg>"""

SIZING = """<svg viewBox="0 0 560 250" role="img" aria-label="Illustration: a heat pump sized by guess is taller than what the house needs; one sized from a calculation matches it">
<g font-family="Inter Tight,sans-serif" font-size="18" fill="#cfe3e1"><rect x="60" y="86" width="120" height="124" rx="8" fill="#6b8e7f"/><rect x="220" y="26" width="120" height="184" rx="8" fill="#e88a2e"/><rect x="380" y="86" width="120" height="124" rx="8" fill="#e3f1e8"/>
<path d="M30 86H530" stroke="#fff" stroke-width="2" stroke-dasharray="6 7"/><text x="30" y="68" fill="#fff" font-weight="600">What the house needs</text><line x1="30" y1="210" x2="530" y2="210" stroke="#fff" stroke-opacity=".4"/>
<text x="120" y="236" text-anchor="middle">Your house</text><text x="280" y="236" text-anchor="middle" fill="#fff" font-weight="600">Guessed size</text><text x="440" y="236" text-anchor="middle" fill="#fff" font-weight="600">Sized by calculation</text></g></svg>"""


def tel(p):
    return re.sub(r"[^\d+]", "", p)


def icon(name, cls="ad-i"):
    return f'<svg class="{cls}" aria-hidden="true"><use href="#ad-{name}"/></svg>'


def row(ic, title, body, get=""):
    return (f'<div class="ad-row"><div class="ad-ic">{icon(ic)}</div><div><h3>{title}</h3><p>{body}</p>'
            + (f'<p class="ad-get"><b>You get:</b> {get}</p>' if get else "") + "</div></div>")


def nice_date(iso):
    return date.fromisoformat(iso).strftime("%B %-d, %Y")


def rebate_rows(country, region_codes):
    """Active, verified programs where an assessment comes first, for the regions this company serves."""
    out, seen = [], set()
    for code in region_codes:
        for ent in REBATES.get(country, {}).get(code, []):
            f = FACTS[ent["fact"]]
            if f["status"] != "active" or ent["fact"] in seen:
                continue
            seen.add(ent["fact"])
            _, tone, _cls = status_pills.STATUS[f["status"]]
            label = status_pills.STATUS[f["status"]][0]
            amt = f["amount"][:1].upper() + f["amount"][1:]
            host = urlparse(f["source_url"]).netloc.removeprefix("www.")
            out.append(f'<div class="r"><div class="ad-amt">{e(amt)}</div><div><div class="l"><span class="ad-pill {tone}">{label}</span></div>'
                       f'<h3>{e(ent["title"])}</h3><p>{e(ent["role"])}</p>'
                       f'<p class="ad-src">Source: <a href="{e(f["source_url"])}" target="_blank" rel="noopener">{e(host)}</a> · read {nice_date(f["verified_on"])}'
                       f' · <a href="{ent["href"]}">See the rebate page</a> · <a href="{GUIDES.get(code, US_GUIDE) if country == "ca" else US_GUIDE}">Read the guide</a></p></div></div>')
    return out


def render(c, kind, ranks, path, ctx):
    """Return the profile page HTML (with @@CHECKED@@ placeholders). ctx supplies the builder's helpers and data."""
    name, g, country = c["name"], c["google"], c["country"]
    ca = country == "ca"
    PROV, STATE, HUBS, SITES, OWNER = ctx["PROV_NAMES"], ctx["STATE_NAMES"], ctx["HUBS"], ctx["SITES"], ctx["OWNER"]
    names = lambda codes: [PROV.get(x, STATE.get(x, x)) for x in codes]  # noqa: E731
    regions_txt = ", ".join(names(c["regions"]))
    w = ctx["who"](c, kind)
    listed = c["sources"][0].startswith(("NRCan", "RESNET"))
    od = OWNER.get(name)
    cities = sorted({(r, ci) for r, ci in c["cities"]}, key=lambda x: x[1])
    first_reg = next((r for r, _ in cities), None)
    first_city = next((ci for _, ci in cities), None)
    adv = "registered energy advisor" if ca else "home energy auditor"

    # ---- contact
    phones = [(reg, ph) for reg, ph in c["phones"].items() if ph][:3]
    web = c["website"]
    primary_phone = phones[0][1] if phones else ""
    cta = []
    if web:
        cta.append(f'<a class="ad-btn ad-btn-amber" href="{e(web)}" target="_blank" rel="noopener">Visit their website</a>')
        if primary_phone:
            cta.append(f'<a class="ad-btn ad-btn-line" href="tel:{tel(primary_phone)}">Call {e(primary_phone)}</a>')
    elif primary_phone:
        cta.append(f'<a class="ad-btn ad-btn-amber" href="tel:{tel(primary_phone)}">Call {e(primary_phone)}</a>')
    else:
        cta.append(f'<a class="ad-btn ad-btn-amber" href="{e(kind["src"])}" target="_blank" rel="noopener">Find contact details on the register</a>')
    tels = "".join(f'<a class="ad-tel" href="tel:{tel(ph)}">{icon("phone")}{e(ph)}'
                   + (f' <span class="ad-fine" style="margin:0">({e(reg)})</span>' if len(phones) > 1 else "") + "</a>" for reg, ph in phones)
    actions = ""
    if web:
        actions += f'<a class="ad-btn ad-btn-amber ad-btn-wide" href="{e(web)}" target="_blank" rel="noopener">Visit their website</a>'
    if c["email"]:
        actions += f'<a class="ad-btn ad-btn-dark ad-btn-wide" href="mailto:{e(c["email"])}">Email them</a>'
    rate = ""
    if g and g.get("rating"):
        rate = (f'<div class="ad-rate"><b>{g["rating"]:.1f}</b><span class="ad-stars" aria-hidden="true">★★★★★</span></div>'
                f'<p class="ad-fine" style="margin-top:2px">{g["reviews"]:,} Google reviews · Google Maps</p>')
    maps = f'<a class="ad-maps" href="{e(g["maps"])}" target="_blank" rel="noopener">View on Google Maps</a>' if g and g.get("maps") else ""
    contact = (f'<aside class="ad-rail" id="contact"><div class="ad-contact"><h2>Contact this company</h2>{rate}{tels}'
               f'<div class="ad-actions">{actions}</div>{maps}'
               f'<p class="ad-fine">Call or message before you hire an installer. Ask for the price of every visit up front.</p></div></aside>')

    # ---- hero and strip
    sub = ("A registered energy advisor visits your home, tests it and tells you which upgrades to do first. Call before you hire an installer."
           if ca else
           "A home energy auditor tests how much energy your house uses and where it leaks, so you fix the biggest problems first.")
    n_reg = len(c["regions"])
    area_b = ", ".join(c["regions"]) if n_reg <= 3 else f"{n_reg} {'provinces' if ca else 'states'}"
    f1 = (f'<b>{g["rating"]:.1f} ★</b><span>{g["reviews"]:,} Google reviews</span>' if g and g.get("rating")
          else '<b>Not rated</b><span>No Google rating found</span>')
    if listed:
        f2 = ('<b>NRCan</b><span>Licensed EnerGuide organization</span>' if ca else '<b>RESNET</b><span>HERS rating company</span>')
    else:
        f2 = '<b>Registered</b><span>Energy advisors</span>'
    strip = "".join(f'<div class="ad-fact">{x}</div>' for x in
                    (f1, f2, f'<b>{e(area_b)}</b><span>{"Provinces" if ca else "States"} served</span>', '<b>@@CHECKED@@</b><span>Page last checked</span>'))
    hero = (f'<header class="ad-hero"><div class="ad-wrap"><div class="ad-hero-grid"><div>'
            f'<p class="ad-kind">{e(w[:1].upper() + w[1:])} · {e(regions_txt)}</p><h1>{e(name)}</h1><p class="ad-sub">{sub}</p>'
            f'<div class="ad-cta-row">{"".join(cta)}</div></div>'
            f'<div class="ad-fig">{HOUSE}<p class="ad-cap">Illustration of where a house can lose heat. An advisor measures yours.</p></div></div></div></header>')

    # ---- main column
    s = []
    if ca:
        s.append(f"""<section id="first"><h2>Call the energy advisor first</h2>
<p class="ad-lede">Some rebates want an advisor involved before any work starts. For example, Ontario's assessment stream needs the pre-audit first, and a rebate can be lost if the work starts earlier.</p>
<div class="ad-window"><div class="ad-zones"><div class="ad-zone before"><h3>Before work starts <span class="ad-pill open">Where the advisor goes</span></h3><ol>
<li class="go"><i>1</i><div><b>Energy advisor visits</b><span>Tests the house. Writes the EnerGuide evaluation and, for a heat pump, the heat load calculation.</span></div></li>
<li><i>2</i><div><b>You choose upgrades</b><span>In the right order: sealing and insulation can come before the heat pump.</span></div></li></ol></div>
<div class="ad-zone after"><h3>After work starts</h3><ol>
<li><i>3</i><div><b>Installer</b><span>Quotes and fits equipment sized to the calculation.</span></div></li>
<li><i>4</i><div><b>Final check</b><span>Some programs also want a second evaluation when the work is done.</span></div></li></ol></div></div>
<div class="ad-marker">{icon("stop")}Check your program's page before you hire anyone. The order is set by the program, not by us.</div></div></section>""")
        step4 = ('<b>BC:</b> Step Code energy modelling and airtightness testing show a new build meets the BC Energy Step Code.'
                 if "BC" in c["regions"] else
                 "Advisors also deliver NRCan's ENERGY STAR for New Homes and R-2000 programs for new builds.")
        s.append(f"""<section id="what"><h2>What an energy advisor does</h2>
<p class="ad-lede">A registered advisor is a third-party expert who does not sell equipment, so the advice is about your house, not a product. These are the standard services. Ask this company which ones it offers.</p>
<div class="ad-rows">{row("report", "EnerGuide evaluation", "Shows where your house is losing energy and which upgrades will make the biggest difference, so you spend money in the right order.", "an EnerGuide rating and a report to take to a rebate program.")}
{row("heat", "Heat load calculation", "Works out how much heating and cooling the house actually needs, room by room, so the heat pump is sized properly.", "a number any installer can quote against.")}
{row("fan", "Airtightness testing", "A blower door test pulls air through the house to measure how leaky it is.", "a before and after measure of how airtight the house is.")}
{row("plan", "New builds", step4)}</div></section>""")
        s.append(f"""<section id="visit"><h2>Why the visit matters</h2>
<p>A heat load calculation done without visiting the house is an estimate. Equipment sized without one is often bigger than the house needs, which costs more up front and runs less efficiently.</p>
<div class="ad-figure">{SIZING}<p class="ad-cap">Illustration only, not measured data.</p></div>
<div class="ad-onsite"><div>{icon("eye")}<b>Check</b><span>The insulation and the windows.</span></div><div>{icon("ruler")}<b>Measure</b><span>The house, room by room.</span></div>
<div>{icon("fan")}<b>Test</b><span>A blower door test shows how airtight it is.</span></div></div>
<p class="ad-fine">The advisor starts outside and moves inside, then enters the data into energy software that calculates your rating (NRCan, read {nice_date(page_kit.FACTS["general-24-nrcan-energuide-visit"]["verified_on"])}).</p></section>""")
    else:
        s.append(f"""<section id="what"><h2>What a home energy auditor does</h2>
<p class="ad-lede">An auditor tests your house and writes a report that ranks the fixes. These are the standard services. Ask this company which ones it offers.</p>
<div class="ad-rows">{row("eye", "Home energy audit", "Looks at insulation, windows, heating and cooling equipment, and finds where the house wastes energy.", "a report that puts the fixes in order.")}
{row("fan", "Blower door test", "A fan pulls air through the house to measure how leaky it is.", "a measure of how airtight the house is.")}
{row("report", "HERS rating", "RESNET lists HERS rating companies. A HERS rating scores how efficient a home is.", "a rating you can compare between homes.")}</div></section>""")

    reb = rebate_rows(country, c["regions"])
    if reb:
        head = "Rebates where an assessment comes first" if ca else "Check your utility's own assessment first"
        intro = ("Verified programs for the places this company works. Rules change, so open the program page before you book anyone."
                 if ca else "Some utilities offer their own assessment at low or no cost. Check yours before you pay for a private audit.")
        s.append(f'<section id="rebates"><h2>{head}</h2><p>{intro}</p><div class="ad-led">{"".join(reb)}</div></section>')
    elif ca:
        hub_codes = [(PROV.get(x, x), x.lower()) for x in c["regions"] if (ROOT / "ca" / x.lower() / "index.html").exists()]
        links = " ".join(f'<a href="/ca/{code}/">{e(nm)} rebates</a>.' for nm, code in hub_codes[:2])
        s.append(f'<section id="rebates"><h2>Which rebates need an advisor here?</h2><p>We list a rebate only after we have read the program\'s own page, and we have not yet verified one in {e(regions_txt)} that needs an advisor first. Ask the advisor which programs apply to your home. {links}</p></section>')
    if ca and "BC" in c["regions"]:
        bc = FACTS["bc-pages-44-better-homes-bc-program-qualified-advisors"]
        s.append(f'<section id="bcnote"><h2>Using BC rebates? Check the BC list</h2><p>Some BC Hydro add-on rebates need an EnerGuide evaluation. <a href="{e(bc["source_url"])}" target="_blank" rel="noopener">Better Homes BC</a> lists advisors who also completed BC rebate training, and tells homeowners to interview and choose their own. Ask whether this company is on that list. Read {nice_date(bc["verified_on"])}.</p></section>')
    if ca and "NS" in c["regions"]:
        s.append('<section id="nsnote"><h2>In Nova Scotia, start with Efficiency Nova Scotia</h2><p>NRCan lists no licensed service organization for Nova Scotia. Homeowners book the rebate assessment through <a href="/ca/ns/">Efficiency Nova Scotia</a>, so ask any advisor here how their work fits that program.</p></section>')

    rk = ranks.get((country, name.lower()), [])
    if rk:
        rows = "".join(f'<a href="{u}" class="ad-rank"><b>#{i} of {n} in {e(city)}</b><span>Top-rated {kind["pros"]}, ranked by Google reviews →</span></a>'
                       for reg, city, i, n, u in sorted(rk, key=lambda x: (x[2], x[1])))
        s.append(f'<section id="ranks"><h2>Where {e(name)} ranks</h2><div class="ad-rows" style="margin-top:18px">{rows}</div></section>')

    # where they work
    chips = "".join((f'<a class="ad-chip" href="{HUBS[(r, ci.lower())][0]}">{e(ci)}</a>' if (r, ci.lower()) in HUBS else f'<span class="ad-chip">{e(ci)}</span>') for r, ci in cities)
    if od:
        where = f'<p>{e(od["base"])} {e(od["area"])}</p>' + (f'<p>Cities we cover where it works:</p><div class="ad-chips">{chips}</div>' if chips else "")
    elif ca and listed:
        where = (f'<p>NRCan lists {e(name)} as licensed to serve postal codes in {e(regions_txt)}.</p>'
                 + (f'<p>That includes these cities we cover:</p><div class="ad-chips">{chips}</div>' if chips else '<p>None of them are cities we have pages for yet.</p>'))
    elif ca:
        where = f'<p>{e(name)} works as registered energy advisors in {e(regions_txt)}.</p>' + (f'<p>Cities we cover where it works:</p><div class="ad-chips">{chips}</div>' if chips else "")
    else:
        where = (f'<p>RESNET lists {e(name)} as a HERS rating company in {e(regions_txt)}.</p>'
                 + (f'<p>Its office is within 80 km of these cities we cover:</p><div class="ad-chips">{chips}</div>' if chips else '<p>We could not place its office near a city we cover.</p>'))
    s.append(f'<section id="area"><h2>Where they work</h2>{where}</section>')

    # services
    svc_chips = ""
    if od:
        svc_chips = f'<h2>Services</h2><div class="ad-chips">{"".join(f"<span class=\"ad-chip\">{e(x)}</span>" for x in od["services"])}</div>'
    else:
        svc, checked = ctx["services"](c)
        if svc:
            svc_chips = (f'<h2>Services their website mentions</h2><div class="ad-chips">{"".join(f"<span class=\"ad-chip\">{e(x)}</span>" for x in svc)}</div>'
                         '<p class="ad-fine">We read their website and noted what it mentions. Ask them to confirm before you book.</p>')
    if svc_chips:
        s.append(f'<section id="services">{svc_chips}'
                 + (f'<p style="margin-top:22px"><a class="ad-btn ad-btn-dark" href="{e(web)}" target="_blank" rel="noopener">Visit their website to book</a></p>' if web else "") + "</section>")

    # what we checked
    src = f'<a href="{kind["src"]}" target="_blank" rel="noopener">{e(kind["src_name"])}</a>'
    checks = [f'<div><b>{"Official list" if listed else "Listed"}</b><p>{(f"Listed by {src}. This is the official list we use, not a paid placement." if listed else f"Listed as a team of registered energy advisors in {e(regions_txt)}.")}</p></div>']
    if g and g.get("rating"):
        checks.append(f'<div><b>Google Maps</b><p>{g["rating"]:.1f} stars from {g["reviews"]:,} reviews. Ratings and review counts from Google Maps.</p></div>')
    else:
        checks.append('<div><b>No Google rating</b><p>We could not match this company to a rated Google Maps listing, so it is not in our city rankings.</p></div>')
    checks.append("<div><b>Always</b><p>Nobody pays to be listed and money never changes where a company ranks.</p></div>")
    s.append(f'<section id="checked"><h2>What we checked</h2><div class="ad-checks">{"".join(checks)}</div>'
             f'<p class="ad-fine" style="margin-top:16px">{adv[:1].upper() + adv[1:]}s are independent businesses. Ask for the price of every visit up front, and whether their report counts for the rebate program you plan to use.</p></section>')

    # faq
    assert "$600 to $1,000" in NRCAN_COST_FACT["amount"]
    cost = (f'NRCan says both evaluations together average $600 to $1,000, '
            f'depending on the provider and province, and are usually paid after the service. Ask this company for its own price. '
            f'<a href="{e(NRCAN_COST_FACT["source_url"])}" target="_blank" rel="noopener">NRCan, read {nice_date(NRCAN_COST_FACT["verified_on"])}</a>.')
    if ca:
        faq = [("Do I need an energy advisor?", "Not for every project. Some rebates require one, and a visit helps you pick upgrades in the right order. Check your program page first."),
               ("How is an advisor different from an installer?", "An advisor tests and measures your home and does not sell equipment. An installer fits it. The advisor's numbers help the installer size it properly."),
               ("What does it cost?", cost),
               ("Can I book one after the install?", "For many programs, no. Ontario's assessment stream, for one, needs the pre-audit before any work starts."),
               ("How do I find a registered advisor?", f'Homeowners book through an NRCan licensed service organization, which sends a registered advisor. <a href="{e(NRCAN_COST_FACT["source_url"])}" target="_blank" rel="noopener">NRCan lists them</a>, and <a href="/energy-advisors/">our directory</a> shows every organization by province.')]
    else:
        faq = [("Do I need a home energy auditor?", "Not for every project. Start with your utility, since some offer their own assessment at low or no cost, then decide whether you need an independent rater."),
               ("What is a HERS rating company?", f'RESNET lists the companies that can give a HERS rating. <a href="{e(kind["src"])}" target="_blank" rel="noopener">See the RESNET list</a>.'),
               ("What does it cost?", "Prices vary by company and home. Ask for the price of every visit up front, and whether the report counts for the rebate program you plan to use.")]
    s.append(f'<section id="faq"><h2>Questions people ask</h2>{"".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in faq)}</section>')

    # claim box
    claim = (f'<div class="ad-claim"><p><b>Is this your company?</b> Tell us what to add or correct: services, areas, languages, or the rebate programs you know best. Email '
             f'<a href="mailto:hello@homepowerrebate.com?subject={e("Profile: " + name)}">hello@homepowerrebate.com</a>.</p>'
             f'<p>Yours to use with clients:</p>{ctx["pro_tools"](country, first_reg, first_city)}</div>')

    main = (f'<div class="ad-wrap ad-layout"><div class="ad-main">{"".join(s)}{claim}'
            f'<p class="ad-fine" style="margin-top:24px">Listing from {src}{", ratings and review counts from Google Maps" if g else ""}, checked @@CHECKED@@. '
            f'Spot an error? <a href="/contact/?subject={e("Correction: " + name)}">Let us know</a>. <a href="{kind["root"]}">See every {kind["pro"]} we list</a>.</p></div>{contact}</div>')
    final = ('<section class="ad-final"><div class="ad-wrap"><h2>Find out what your home needs before you spend a dollar</h2>'
             f'<p>Contact {e(name)} before you book an installer.</p><div class="ad-cta-row">{"".join(cta[:1])}</div></div></section>')
    bar_btns = []
    if primary_phone:
        bar_btns.append(f'<a class="ad-btn ad-btn-dark" href="tel:{tel(primary_phone)}">Call</a>')
    if web:
        bar_btns.append(f'<a class="ad-btn ad-btn-amber" href="{e(web)}" target="_blank" rel="noopener">Website</a>')
    bar = f'<nav class="ad-bar{" one" if len(bar_btns) < 2 else ""}" aria-label="Contact">{"".join(bar_btns)}</nav>' if bar_btns else ""
    return f'{SYMBOLS}<main id="main" tabindex="-1" class="ad-page">{hero}<div class="ad-strip"><div class="ad-wrap">{strip}</div></div>{main}{final}{bar}</main>'
