#!/usr/bin/env python3
"""Add contextual internal links to pages that rank 9-30 in Search Console but had few inbound links.

Sep 2026 GSC: the SMUD rebate post (EV charger queries, pos 29-30) had 2 inbound links; the Nova Scotia
heat pump water heater pages (pos 21-40) had 4-8. Links go on the pages a searcher would actually be on.
Marker-wrapped, so re-runs replace rather than duplicate. Run after any city rebuild.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from apply_canonical_nav_footer import content_insert_point  # noqa: E402

SMUD = "/blog/smud-rebate-breakdown/"
NS_GUIDE = "/blog/water-heater-buying-guide-ns/"
NS_CALC = "/heat-pump-water-heater/nova-scotia/"

BOX = ('<section style="max-width:880px;margin:24px auto;padding:0 20px;"><p style="background:#f5efe5;border-radius:8px;'
       'padding:14px 18px;margin:0;">{}</p></section>')

# (marker, html, [pages])
SMUD_CITIES = ["sacramento/sacramento", "sacramento/folsom", "sacramento/rancho-cordova"]
JOBS = [
    ("SMUD-LINK", f'<b>On SMUD power?</b> See <a href="{SMUD}">every SMUD rebate: EV charger up to $600, heat pump up to $3,000, water heater and battery</a>.',
     ["us/ca/sacramento/index.html"] + [f"us/ca/{c}/{s}/index.html" for c in SMUD_CITIES for s in ("", "ev-charger", "heat-pump", "water-heater", "battery")]),
    ("SMUD-LINK", f'<b>Sacramento-area homes on SMUD:</b> the <a href="{SMUD}">SMUD EV charger rebate (Charge@Home, up to $600) and other SMUD rebates</a>.',
     ["us/ca/index.html"]),
    ("NS-GUIDE-LINK", f'<b>Replacing an electric tank?</b> Read the <a href="{NS_GUIDE}">Nova Scotia heat pump water heater cost, sizing and rebate guide</a>, or <a href="{NS_CALC}">work out your savings at NS Power rates</a>.',
     ["ca/ns/index.html", "ca/ns/halifax/index.html", "ca/ns/cape-breton/index.html",
      "ca/ns/halifax/water-heater/index.html", "ca/ns/cape-breton/water-heater/index.html", "heat-pump-water-heater/index.html"]),
    ("NS-GUIDE-LINK", f'<b>Sizing, cost and basements:</b> the <a href="{NS_GUIDE}">Nova Scotia heat pump water heater buying guide</a> covers what size to buy and whether it suits a cold basement.',
     ["heat-pump-water-heater/nova-scotia/index.html"]),
    ("NS-CALC-LINK", f'<b>Do the math:</b> the <a href="{NS_CALC}">Nova Scotia heat pump water heater savings calculator</a> uses NS Power\'s current rate.',
     ["blog/water-heater-buying-guide-ns/index.html"]),
]

NM = "/blog/net-metering-vs-net-billing/"
GH = "/blog/greener-homes-grant-explained/"
JOBS += [
    ("NET-METERING-LINK", f'<b>Planning solar?</b> Read <a href="{NM}">net metering vs net billing: what the difference means for your savings</a>.',
     ["blog/bc-net-metering-ended-self-generation-rate-2026/index.html", "blog/ontario-solar-rebate-vs-net-metering/index.html",
      "us/ca/index.html", "ca/bc/index.html", "ca/on/index.html"]
     + sorted(str(p.relative_to(ROOT)) for p in (ROOT / "ca" / "bc").glob("*/solar/index.html"))),
    ("GREENER-LINK", f'<b>Looking for the Canada Greener Homes Grant?</b> It has closed. See <a href="{GH}">what replaced it and where to look in your province</a>.',
     ["ca/bc/index.html", "ca/on/index.html", "ca/ab/index.html", "ca/ns/index.html", "rebate-tracker/index.html"]),
]

OT = "/ca/on/ottawa/smart-thermostats/"
JOBS += [
    ("OTTAWA-THERMOSTAT-LINK", f'<b>Looking for a free thermostat in Ottawa?</b> See <a href="{OT}">who qualifies for a free smart thermostat and how to get the $125 rebate</a>.',
     ["ca/on/ottawa/index.html", "ca/on/ottawa/appliances/index.html", "ca/on/ottawa/heat-pump/index.html", "ca/on/ottawa/insulation/index.html",
      "ca/on/ottawa/windows-doors/index.html", "ca/on/ottawa/water-heater/index.html",
      "ca/on/ottawa/solar/index.html", "ca/on/ottawa/battery/index.html"]),
]
PSV = "/blog/bc-hydro-peak-saver-explained/"
BCH = "/programs/bc-hydro-rebates/"
JOBS += [
    ("PEAK-SAVER-WORTH-LINK", f'<b>Is the BC Hydro Peak Saver battery rebate worth it?</b> Read <a href="{PSV}">the Peak Saver program explained</a>, including what you earn per device.',
     ["blog/bc-hydro-peak-saver-battery-rebate-5000-vs-1500/index.html", "questions/peak-saver-program-bc-how-it-works/index.html",
      "blog/is-bc-hydro-solar-rebate-worth-it/index.html", "programs/bc-hydro-peak-saver/index.html"]),
    ("BCH-REBATES-LINK", f'<b>BC Hydro customer?</b> See <a href="{BCH}">every BC Hydro rebate, with amounts and rules</a>.',
     ["blog/bc-hydro-product-rebates-appliances/index.html", "smart-thermostats/index.html", "ca/bc/index.html"]
     + sorted(str(p.relative_to(ROOT)) for p in (ROOT / "ca" / "bc").glob("*/index.html"))),
]
CATS = ("heat-pump", "water-heater", "smart-thermostats", "ev-charger", "insulation", "appliances")


def _city(region, city):
    base = ROOT / "us" / region / city
    return [str((base / "index.html").relative_to(ROOT))] + [f"us/{region}/{city}/{c}/index.html" for c in CATS]


JOBS += [
    ("PECO-PROGRAM-LINK", '<b>PECO customer?</b> See <a href="/programs/peco-rebates/">every PECO rebate: heat pump $200 to $300, water heater $350, thermostat $25 to $50</a>.',
     _city("pa", "philadelphia")),
    ("PPL-PROGRAM-LINK", '<b>PPL Electric customer?</b> See <a href="/programs/ppl-electric-rebates/">every PPL Electric rebate, with heat pump, water heater, insulation and thermostat amounts</a>.',
     _city("pa", "allentown")),
    ("XCEL-PROGRAM-LINK", '<b>Xcel Energy customer?</b> See <a href="/programs/xcel-energy-colorado-rebates/">every Xcel Energy Colorado rebate, including the heat pump bonus for gas-heated homes</a>.',
     _city("co", "denver") + _city("co", "aurora") + _city("co", "boulder")),
]
INS = "/insulation-rebates/"
JOBS += [
    ("INSULATION-HUB-LINK", f'<b>Insulation rebates in every region:</b> compare <a href="{INS}">insulation rebates by province and state</a>, with a BC attic calculator.',
     ["blog/attic-insulation-guide/index.html", "blog/insulation-buying-guide-bc/index.html", "blog/insulation-buying-guide-ca/index.html",
      "blog/insulation-buying-guide-on/index.html", "blog/insulation-rebates-bc-stack-federal-provincial/index.html",
      "blog/why-insulation-first-energy-retrofit/index.html", "ca/bc/index.html", "ca/on/index.html", "ca/ab/index.html", "ca/ns/index.html",
      "us/ma/index.html", "us/ny/index.html", "us/ca/index.html", "us/co/index.html", "us/pa/index.html", "installers/index.html"]
     + sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("ca/*/*/insulation/index.html"))
     + sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("us/*/*/insulation/index.html"))
     + sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("us/*/*/*/insulation/index.html"))),
]

GREENER_BLOCK = """<!-- GREENER-PROVINCES-START -->
<h2>Greener Homes closed across Canada. Where to look in your province</h2>
<div style="overflow-x:auto;"><table style="width:100%;min-width:520px;border-collapse:collapse;font-size:15px;">
<tr style="background:#f5efe5;"><th style="text-align:left;padding:8px;">Province</th><th style="text-align:left;padding:8px;">Main program now</th><th style="text-align:left;padding:8px;">Guide</th></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">British Columbia</td><td style="padding:8px;border-top:1px solid #d9d0c1;">BC Hydro heat pump rebate up to $4,000; CleanBC income-qualified up to $13,000, $7,000 or $3,500</td><td style="padding:8px;border-top:1px solid #d9d0c1;"><a href="/programs/bc-hydro-rebates/">BC Hydro</a> · <a href="/programs/cleanbc-rebates/">CleanBC</a></td></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">Ontario</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Home Renovation Savings: heat pumps up to $12,000, plus insulation, solar and battery</td><td style="padding:8px;border-top:1px solid #d9d0c1;"><a href="/programs/home-renovation-savings/">Home Renovation Savings</a></td></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">Nova Scotia</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Home Energy Assessment rebates up to $5,000; moderate-income homes can add up to $5,000 more</td><td style="padding:8px;border-top:1px solid #d9d0c1;"><a href="/programs/efficiency-nova-scotia/">Efficiency Nova Scotia</a></td></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">Alberta</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Local Clean Energy Improvement Program financing where it is open (Calgary's is closed until winter 2026/2027)</td><td style="padding:8px;border-top:1px solid #d9d0c1;"><a href="/programs/alberta-energy-rebates/">Alberta guide</a></td></tr>
</table></div>
<p style="font-size:13.5px;color:#6b8e7f;">Amounts checked September 2026 against each program's official page; the <a href="/rebate-tracker/">rebate tracker</a> lists every change with sources.</p>
<!-- GREENER-PROVINCES-END -->
"""


ATTIC_BLOCK = """<!-- ATTIC-REBATES-START -->
<h2>Attic insulation rebates by region</h2>
<div style="overflow-x:auto;"><table style="width:100%;min-width:520px;border-collapse:collapse;font-size:15px;">
<tr style="background:#f5efe5;"><th style="text-align:left;padding:8px;">Where</th><th style="text-align:left;padding:8px;">Attic rebate</th><th style="text-align:left;padding:8px;">Key rule</th></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">BC (BC Hydro)</td><td style="padding:8px;border-top:1px solid #d9d0c1;">$0.02 per sq ft per R added, up to $900</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Electric heat, HPCN contractor, at least R-12 added</td></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">Ontario</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Up to $1,250 without an assessment; to R-50 with one: $1,500, $1,200 or $900</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Assessment before and after for the larger amounts</td></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">Nova Scotia</td><td style="padding:8px;border-top:1px solid #d9d0c1;">To R-50, up to $750</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Through a Home Energy Assessment</td></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">Massachusetts</td><td style="padding:8px;border-top:1px solid #d9d0c1;">75% to 100% off insulation and air sealing</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Start with the free Mass Save assessment</td></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">New York</td><td style="padding:8px;border-top:1px solid #d9d0c1;">$2,500 or $3,000 seal-and-insulate package</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Comfort Home contractors, participating counties</td></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">California (SMUD)</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Up to $3,000 for air sealing, attic insulation and ducts</td><td style="padding:8px;border-top:1px solid #d9d0c1;">SMUD Contractor Network</td></tr>
</table></div>
<p>See every program, with sources and more regions, on the <a href="/insulation-rebates/">insulation rebates by province and state</a> page.</p>
<!-- ATTIC-REBATES-END -->
"""


OTTAWA_EAP = """<!-- OTTAWA-EAP-START -->
<h2>Free thermostat in Ottawa: do you qualify?</h2>
<p>Ontario's <b>Energy Affordability Program</b> installs a programmable or smart thermostat for free in homes heated by electricity or oil, along with other upgrades. Hydro Ottawa lists it on its programs page. You qualify if you own, rent or lease your home in Ontario and your household income is under the limit, or if you get ODSP, Ontario Works or OESP help.</p>
<div style="overflow-x:auto;"><table style="width:100%;min-width:420px;border-collapse:collapse;font-size:15px;">
<tr style="background:#f5efe5;"><th style="text-align:left;padding:8px;">Household</th><th style="text-align:left;padding:8px;">Income limit for free thermostat and upgrades (before tax)</th></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">1 person</td><td style="padding:8px;border-top:1px solid #d9d0c1;">$48,220</td></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">Family of 4</td><td style="padding:8px;border-top:1px solid #d9d0c1;">$96,439</td></tr>
</table></div>
<p><b>How to apply:</b> call 1-844-770-3148 or use the online form on the <a href="https://www.saveonenergy.ca/en/For-Your-Home/Energy-Affordability-Program" rel="nofollow noopener" target="_blank">Save on Energy program page</a>. The program says it replies within three business days. If your income is over the limit, or you heat with gas, use the $125 rebate below instead. Limits checked September 2026.</p>
<!-- OTTAWA-EAP-END -->
"""


def ottawa_eap():
    f = ROOT / "ca/on/ottawa/smart-thermostats/index.html"
    t = f.read_text(encoding="utf-8")
    S, E = "<!-- OTTAWA-EAP-START -->", "<!-- OTTAWA-EAP-END -->"
    if S in t:
        new = re.sub(re.escape(S) + ".*?" + re.escape(E) + r"\n?", lambda m: OTTAWA_EAP, t, count=1, flags=re.S)
    else:
        m = re.search(r"<h2[^>]*>\s*How much you get", t)
        if not m:
            print("no 'How much you get' heading")
            return 0
        new = t[:m.start()] + OTTAWA_EAP + t[m.start():]
    if new != t:
        f.write_text(new, encoding="utf-8")
        return 1
    return 0


PEAK_WORTH = """<!-- PEAK-WORTH-SECTION-START -->
<h2>Is the BC Hydro Peak Saver battery rebate worth it?</h2>
<p><b>For most homes with a battery, yes.</b> Enrolling is what unlocks the larger battery rebate: up to $5,000 with Peak Saver, against up to $1,500 if the battery is paired with solar and not enrolled. On top of that, Peak Saver pays $500 once and about $250 each winter, roughly $3,000 over 10 years for one battery. The trade-off is that BC Hydro can briefly draw power from your battery during very high demand across the grid. If backup power during outages is your main reason for a battery, see below how much control you keep. Other devices earn less: see the <a href="/programs/bc-hydro-peak-saver/">Peak Saver credits by device</a>.</p>
<!-- PEAK-WORTH-SECTION-END -->
"""


def peak_section():
    f = ROOT / "blog/bc-hydro-peak-saver-explained/index.html"
    t = f.read_text(encoding="utf-8")
    S, E = "<!-- PEAK-WORTH-SECTION-START -->", "<!-- PEAK-WORTH-SECTION-END -->"
    if S in t:
        new = re.sub(re.escape(S) + ".*?" + re.escape(E) + r"\n?", lambda m: PEAK_WORTH, t, count=1, flags=re.S)
    else:
        m = re.search(r"<h2[^>]*>\s*What it pays", t)
        if not m:
            print("no 'What it pays' heading")
            return 0
        new = t[:m.start()] + PEAK_WORTH + t[m.start():]
    if new != t:
        f.write_text(new, encoding="utf-8")
        return 1
    return 0


RVALUE_BLOCK = """<!-- CANADA-RVALUES-START -->
<h2>Canada: attic R-value targets by climate zone</h2>
<p>Natural Resources Canada's <em>Keeping the Heat In</em> guide recommends attic insulation by climate zone, measured in heating degree-days (HDD), a count of how cold a place is over the year. Colder zones need more. Find your zone, then check your local building code, which may set a different minimum.</p>
<div style="overflow-x:auto;"><table style="width:100%;min-width:560px;border-collapse:collapse;font-size:15px;">
<tr style="background:#f5efe5;"><th style="text-align:left;padding:8px;">Zone</th><th style="text-align:left;padding:8px;">Heating degree-days</th><th style="text-align:left;padding:8px;">BC examples</th><th style="text-align:left;padding:8px;">Recommended attic</th></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">4</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Under 3,000</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Vancouver, Victoria, Surrey, Burnaby</td><td style="padding:8px;border-top:1px solid #d9d0c1;"><b>R-45</b> (RSI 7.9)</td></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">5</td><td style="padding:8px;border-top:1px solid #d9d0c1;">3,000 to 3,999</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Kamloops, Kelowna, Nanaimo, Vernon</td><td style="padding:8px;border-top:1px solid #d9d0c1;"><b>R-55</b> (RSI 9.7)</td></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">6</td><td style="padding:8px;border-top:1px solid #d9d0c1;">4,000 to 4,999</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Prince George, Cranbrook, Whistler</td><td style="padding:8px;border-top:1px solid #d9d0c1;"><b>R-60</b> (RSI 10.6)</td></tr>
<tr><td style="padding:8px;border-top:1px solid #d9d0c1;">7a to 8</td><td style="padding:8px;border-top:1px solid #d9d0c1;">5,000 and above</td><td style="padding:8px;border-top:1px solid #d9d0c1;">Fort St. John, Dawson Creek, Fort Nelson</td><td style="padding:8px;border-top:1px solid #d9d0c1;"><b>R-80</b> (RSI 14.1)</td></tr>
</table></div>
<p style="font-size:13.5px;color:#6b8e7f;">Sources: <a href="https://natural-resources.canada.ca/energy-efficiency/home-energy-efficiency/keeping-heat-section-2-your-house-works" rel="nofollow noopener" target="_blank">Natural Resources Canada, Table 2-1</a> · <a href="https://betterhomesbc.ca/definitions/climate-zones/" rel="nofollow noopener" target="_blank">Better Homes BC climate zones</a>. Checked September 29, 2026. These are guidelines, not code.</p>
<ul>
<li><b>Rebates may stop short of the guideline.</b> Ontario's and Nova Scotia's attic rebates are for insulating up to R-50, which is below the guideline for zones 5 and up. You can add more at your own cost.</li>
<li><b>Adding over old insulation with a plastic vapour barrier?</b> Natural Resources Canada says to put at least twice the insulating value above the barrier as below it (its example: R-12 below means at least R-24 on top). That keeps moisture from getting trapped.</li>
<li><b>Not in BC?</b> Look up your town's heating degree-days and match it to the zone above.</li>
</ul>
<!-- CANADA-RVALUES-END -->
"""


def rvalue_section():
    f = ROOT / "blog/attic-insulation-guide/index.html"
    t = f.read_text(encoding="utf-8")
    S, E = "<!-- CANADA-RVALUES-START -->", "<!-- CANADA-RVALUES-END -->"
    if S in t:
        new = re.sub(re.escape(S) + ".*?" + re.escape(E) + r"\n?", lambda m: RVALUE_BLOCK, t, count=1, flags=re.S)
    else:
        m = re.search(r"<h2[^>]*>\s*Why air sealing comes first", t)
        if not m:
            print("no air sealing heading")
            return 0
        new = t[:m.start()] + RVALUE_BLOCK + t[m.start():]
    if new != t:
        f.write_text(new, encoding="utf-8")
        return 1
    return 0


def attic_section():
    f = ROOT / "blog/attic-insulation-guide/index.html"
    t = f.read_text(encoding="utf-8")
    S, E = "<!-- ATTIC-REBATES-START -->", "<!-- ATTIC-REBATES-END -->"
    if S in t:
        new = re.sub(re.escape(S) + ".*?" + re.escape(E) + r"\n?", lambda m: ATTIC_BLOCK, t, count=1, flags=re.S)
    else:
        m = re.search(r"<h2[^>]*>\s*What to do next", t)
        if not m:
            print("no next-steps heading")
            return 0
        new = t[:m.start()] + ATTIC_BLOCK + t[m.start():]
    if new != t:
        f.write_text(new, encoding="utf-8")
        return 1
    return 0


def greener_section():
    f = ROOT / "blog/greener-homes-grant-explained/index.html"
    t = f.read_text(encoding="utf-8")
    S, E = "<!-- GREENER-PROVINCES-START -->", "<!-- GREENER-PROVINCES-END -->"
    if S in t:
        new = re.sub(re.escape(S) + ".*?" + re.escape(E) + r"\n?", lambda m: GREENER_BLOCK, t, count=1, flags=re.S)
    else:
        m = re.search(r"<h2[^>]*>\s*The takeaway", t)
        if not m:
            print("no takeaway heading")
            return 0
        new = t[:m.start()] + GREENER_BLOCK + t[m.start():]
    if new != t:
        f.write_text(new, encoding="utf-8")
        return 1
    return 0


HUB_INDEXES = {f"{r}/index.html" for r in ("ca/bc", "ca/on", "ca/ab", "ca/ns", "us/ma", "us/ny", "us/ca", "us/pa", "us/co", "us/vt", "us/mi")}
HUB_SKIP = {"NET-METERING-LINK", "GREENER-LINK", "INSULATION-HUB-LINK", "BCH-REBATES-LINK"}  # these live in the hub "Explore more" row now


# Oct 2026 GSC (last 24h): /ca/ns/ took 342 of 830 impressions for HARP status and payment-date queries; Ontario furnace queries rank 28-57;
# thermostat comparison and Bosch vs Mitsubishi rank 7-24 with few inbound links.
HARP = "/programs/nova-scotia-heating-assistance-rebate-harp/"
THERMO = "/blog/smart-thermostat-comparison-nest-ecobee-honeywell-mysa/"
BRANDS = "/blog/heat-pump-brands-comparison-mitsubishi-daikin-bosch/"
FURN_ON = "/furnace-rebates/ontario/"
JOBS += [
    ("HARP-LINK", f'<b>Need help with this winter\'s heating bill?</b> The <a href="{HARP}">Nova Scotia Heating Assistance Rebate (HARP) pays $400 for 2026-27: who qualifies, how to check your status and when it pays</a>.',
     sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("ca/ns/*/index.html")) + sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("ca/ns/*/*/index.html"))
     + ["blog/water-heater-buying-guide-ns/index.html", "programs/efficiency-nova-scotia/index.html", "rebate-tracker/index.html"]),
    ("THERMO-COMPARE-LINK", f'<b>Mysa, Ecobee or Nest?</b> See <a href="{THERMO}">which smart thermostat fits your heating (baseboards, furnace or mini-split)</a> before you buy.',
     sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("ca/*/*/smart-thermostats/index.html"))
     + ["smart-thermostats/index.html", "blog/ontario-smart-thermostats-100-rebate-compared/index.html"]),
    ("BRANDS-COMPARE-LINK", f'<b>Choosing a brand?</b> Compare <a href="{BRANDS}">Bosch vs Mitsubishi vs Daikin cold-climate heat pumps</a>: winter specs, warranties and rebates.',
     sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("ca/*/*/heat-pump/index.html"))),
    ("FURNACE-ON-LINK", f'<b>Replacing a gas furnace?</b> There is no Ontario rebate for a new furnace in 2026. See <a href="{FURN_ON}">what a heat pump gets instead: $500 per ton for Enbridge gas homes, up to $7,500 for oil, propane and electric</a>.',
     sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("ca/on/*/heat-pump/index.html")) + sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("ca/on/*/index.html"))),
]


BCH_FREE_THERMO = "/programs/bc-hydro-free-smart-thermostats/"
JOBS += [
    ("BCH-FREE-THERMO-LINK", f'<b>Baseboard heat on BC Hydro?</b> See <a href="{BCH_FREE_THERMO}">how to get up to 5 free Mysa or Sinopé smart thermostats this fall</a>, plus $50 a winter from Peak Saver.',
     sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("ca/bc/*/smart-thermostats/index.html"))
     + ["smart-thermostats/index.html", "programs/bc-hydro-peak-saver/index.html", "programs/bc-hydro-rebates/index.html",
        "blog/smart-thermostat-comparison-nest-ecobee-honeywell-mysa/index.html", "blog/bc-hydro-peak-saver-explained/index.html",
        "blog/smart-thermostat-peak-saver-optimization/index.html", "blog/bc-hydro-product-rebates-appliances/index.html"]),
]


# Oct 2026: one state-level page per topic where every city has the same answer (city URLs 301 here).
def _hub_and_cities(region):
    base = ROOT / region
    return [f"{region}/index.html"] + sorted(str(p.relative_to(ROOT)) for p in base.glob("*/index.html")) + sorted(str(p.relative_to(ROOT)) for p in base.glob("*/*/index.html") if p.parent.parent.name not in ("battery", "ev-charger"))


STATE_TOPICS = [
    ("us/ma", "/us/ma/battery/", "Massachusetts home battery rebates and incentives"),
    ("us/pa", "/us/pa/battery/", "Pennsylvania home battery rebates and incentives"),
    ("us/co", "/us/co/battery/", "Colorado home battery rebates and incentives"),
    ("us/ny", "/us/ny/battery/", "New York home battery rebates and incentives"),
    ("us/ma", "/us/ma/ev-charger/", "Massachusetts home EV charger rebates"),
    ("us/ma", "/us/ma/hrv/", "Massachusetts HRV and ERV rebates"),
    ("us/ma", "/us/ma/appliances/", "Massachusetts appliance rebates"),
    ("ca/ab", "/ca/ab/ev-charger/", "Alberta home EV charger rebates"),
    ("ca/on", "/ca/on/ev-charger/", "Ontario home EV charger rebates"),
    ("ca/on", "/ca/on/hrv/", "Ontario HRV and ERV rebates"),
    ("us/co", "/us/co/solar/", "Colorado home solar rebates"),
    ("us/co", "/us/co/ev-charger/", "Colorado home EV charger rebates"),
    ("us/pa", "/us/pa/solar/", "Pennsylvania home solar rebates"),
    ("us/vt", "/us/vt/solar/", "Vermont home solar rebates"),
    ("us/vt", "/us/vt/ev-charger/", "Vermont home EV charger rebates"),
    ("ca/ns", "/ca/ns/hrv/", "Nova Scotia HRV and ERV rebates"),
]
for region, url, label in STATE_TOPICS:
    marker = "STATE-" + url.strip("/").replace("/", "-").upper() + "-LINK"
    pages = [p for p in (_hub_and_cities(region) if region != "us/ny" else [f"{region}/index.html"] + sorted(str(p.relative_to(ROOT)) for p in (ROOT / region).glob("*/*/index.html"))) if not p.startswith(url.strip("/"))]
    JOBS.append((marker, f'<b>Statewide answer:</b> see <a href="{url}">{label}</a>, with what is open, what has closed and the dates to watch.', pages))


ROOF_PAGES = sorted(str(p.relative_to(ROOT)) for pat in ("ca/on/*/solar/index.html", "ca/bc/*/solar/index.html", "us/ma/*/index.html") for p in ROOT.glob(pat)) + sorted(str(p.relative_to(ROOT)) for pat in ("us/ny/**/solar/index.html", "us/ca/**/solar/index.html", "ca/ns/*/solar/index.html", "us/pa/solar/index.html", "us/co/solar/index.html") for p in ROOT.glob(pat)) + ["us/ma/index.html", "solar-quote-checker/index.html"]
JOBS.append(("ROOF-CHECK-LINK", '<b>See your own roof:</b> try the free <a href="/roof-check/">Solar Roof Check</a>. Type your address to see how many panels fit and which verified solar rebates apply.', ROOF_PAGES))


UT_JOBS = [
    ("UTILITY-SDGE-LINK", '<b>On SDG&E power?</b> See <a href="/programs/sdge-rebates/">what SDG&E customers can claim: free upgrades for income-eligible homes, coaching for gas homes and what has ended</a>.',
     ["us/ca/san-diego/index.html", "us/ca/san-diego/chula-vista/index.html", "us/ca/san-diego/escondido/index.html", "us/ca/san-diego/san-diego/index.html"]),
    ("UTILITY-AVA-LINK", '<b>Buying power from Ava?</b> See <a href="/programs/ava-community-energy-rebates/">what Ava Community Energy offers and where heat pump money comes from</a>.',
     ["us/ca/bay-area/oakland/index.html", "us/ca/bay-area/berkeley/index.html", "us/ca/bay-area/fremont/index.html"]),
    ("UTILITY-MVU-LINK", '<b>On Moreno Valley Utility?</b> See <a href="/programs/moreno-valley-utility-rebates/">MVU rebates: $140 to $160 per ton for AC and heat pumps, the EV incentive and the rate discount</a>.',
     ["us/ca/inland-empire/moreno-valley/index.html"]),
    ("UTILITY-SOE-LINK", '<b>All Ontario programs in one place:</b> see <a href="/programs/save-on-energy-rebates/">what Save on Energy pays</a>, and <a href="/programs/enbridge-gas-rebates/">what Enbridge gas customers get</a>.',
     ["ca/on/index.html"] + sorted(str(p.relative_to(ROOT)) for p in (ROOT / "ca/on").glob("*/index.html"))),
]
JOBS += UT_JOBS


def main():
    n = greener_section() + attic_section() + ottawa_eap() + peak_section() + rvalue_section()
    for marker, html, pages in JOBS:
        S, E = f"<!-- {marker}-START -->", f"<!-- {marker}-END -->"
        blk = S + BOX.format(html) + E
        for rel in pages:
            if marker in HUB_SKIP and rel in HUB_INDEXES:
                continue
            f = ROOT / rel
            if not f.exists():
                continue
            t = f.read_text(encoding="utf-8")
            if S in t:
                new = re.sub(re.escape(S) + ".*?" + re.escape(E), lambda m: blk, t, count=1, flags=re.S)
            else:
                i = content_insert_point(t)
                if i < 0:
                    print("no insert point:", rel)
                    continue
                new = t[:i] + blk + "\n" + t[i:]
            if new != t:
                f.write_text(new, encoding="utf-8")
                n += 1
    print(f"{n} pages updated")


if __name__ == "__main__":
    main()
