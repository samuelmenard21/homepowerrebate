#!/usr/bin/env python3
"""Build /smart-thermostats/: every verified smart thermostat rebate, by province and state.

Every row comes from data/verified-facts/*.json (checked against the official source). Regions with
no verified thermostat program say so rather than guessing. Re-run after the monthly rebate check.
Also injects a <!-- THERMO-LINK --> block into the existing thermostat articles.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell, CHECKED, ISO, AUTHOR  # noqa: E402
import apply_canonical_nav_footer as navfooter  # noqa: E402
from build_installer_rankings import BASE  # noqa: E402

PATH = "/smart-thermostats/"
e = html.escape

# (region, hub, program, amount, who qualifies, which thermostats, source)
ROWS = [
    ("British Columbia", "/ca/bc/", "Free smart thermostats (BC Hydro and the Province)", "Free, up to 5 per home",
     "BC Hydro customers with electric baseboard heat. You're signed up for Peak Saver. Starts October 2026.", "Mysa or Sinopé (baseboard)",
     "https://news.gov.bc.ca/releases/2026ECS0037-000794"),
    ("British Columbia", "/ca/bc/", "BC Hydro Peak Saver", "$100 to sign up, then $50 each winter",
     "BC Hydro customers. Join at least half of the winter peak events (Nov to March, 4 hours max).", "Mysa or Sinopé (baseboard)",
     "https://www.bchydro.com/powersmart/residential/rebates-programs/peak-saver/enroll-smart-home-devices.html"),
    ("British Columbia", "/ca/bc/", "FortisBC connected thermostat rebate", "Up to $150",
     "FortisBC or city electric customers (Penticton, Summerland, Grand Forks, Nelson Hydro) with electric central heat.", "Eligible connected models",
     "https://www.fortisbc.com/rebates-and-energy-savings/rebates-and-offers"),
    ("Ontario", "/ca/on/", "Home Renovation Savings", "$125",
     "Enbridge gas heat, or electric heat or cooling. First thermostat rebate only. Upload your receipt within 60 days.",
     "Specific ecobee, Google Nest, Honeywell Home, Copeland Sensi, Mysa and Sinopé models",
     "https://homerenovationsavings.ca/without-assessment/smart-thermostat"),
    ("Ontario", "/ca/on/", "Save on Energy Peak Perks", "$75 to sign up, then $20 a year",
     "Any Ontario electricity customer with central AC or a heat pump and an eligible Wi-Fi thermostat. Not high-rise units.", "Eligible Wi-Fi thermostats",
     "https://saveonenergy.ca/For-Your-Home/Peak-Perks"),
    ("Ontario", "/ca/on/", "Energy Affordability Program", "Free (can include a thermostat)",
     "Income-qualified households, owners or renters.", "Installed for you",
     "https://saveonenergy.ca/For-Your-Home/Energy-Affordability-Program"),
    ("Alberta", "/ca/ab/", "Red Deer smart thermostat rebate", "$50",
     "Red Deer residents, one per utility account. Apply by Dec 31, 2026 or until funds run out.", "ENERGY STAR certified smart thermostats",
     "https://www.reddeer.ca/city-services/environment-and-conservation/your-home/energy-efficiency/smart-thermostat-rebate/"),
    ("Alberta", "/ca/ab/", "EPCOR Peak Rewards (pilot)", "$50 card, then $25 a season",
     "Select Edmonton neighbourhoods, central AC required, a thermostat you already own. No free thermostats.", "Eligible thermostats",
     "https://www.epcor.com/ca/en/ab/edmonton/conservation/incentives/peak-rewards-thermostats.html"),
    ("Nova Scotia", "/ca/ns/", "Efficiency Nova Scotia instant rebate", "$45 off at checkout",
     "Thermostats for electric heat, at participating stores.", "Electric-heat thermostats (e.g. Mysa)",
     "https://www.efficiencyns.ca/programs-rebates/instant-rebates"),
    ("Nova Scotia", "/ca/ns/", "Efficiency Nova Scotia free installation", "Free, installed (worth up to $160)",
     "Electrically heated homes whose current thermostat is analog or not programmable.", "Installed for you",
     "https://www.efficiencyns.ca/programs-rebates/free-product-installation"),
    ("California", "/us/ca/", "SMUD smart thermostat rebate", "$50 instant",
     "SMUD customers (Sacramento area), through the SMUD Energy Store.", "Eligible smart thermostats",
     "https://www.smud.org/Rebates-and-Savings-Tips/Rebates-for-My-Home"),
    ("California", "/us/ca/", "SCE Smart Energy Program", "$75 bill credit",
     "SCE customers who enroll an eligible thermostat in demand response.", "Eligible smart thermostats",
     "https://www.sce.com/residential/demand-response/smart-energy-program"),
    ("California", "/us/ca/", "Pasadena Water and Power", "$50 (+$10 if bought in Pasadena)",
     "PWP residential customers. Bill Payment Assistance customers get $50 more per unit.", "Eligible smart thermostats",
     "https://pwp.cityofpasadena.net/smartthermostatrebate/"),
    ("California", "/us/ca/", "Burbank Water and Power", "Up to $75",
     "BWP residential customers.", "Eligible smart thermostats",
     "https://www.burbankwaterandpower.com/residential-rebates"),
    ("New York", "/us/ny/", "PSEG Long Island", "$100 to $130",
     "PSEG Long Island customers.", "ENERGY STAR smart thermostats",
     "https://www.psegliny.com/saveenergyandmoney/energystarrebates"),
]
NOT_VERIFIED = [("Massachusetts", "/us/ma/"), ("Colorado", "/us/co/"), ("Pennsylvania", "/us/pa/"), ("Vermont", "/us/vt/")]

ARTICLES = [
    ("/blog/smart-thermostat-comparison-nest-ecobee-honeywell-mysa/", "Mysa vs Ecobee vs Nest: which thermostat fits your heat"),
    ("/blog/mysa-vs-ecobee-thermostat/", "Mysa vs Ecobee: baseboards vs furnaces"),
    ("/blog/ontario-smart-thermostats-100-rebate-compared/", "Ontario's $125 rebate: 7 eligible thermostats compared"),
    ("/blog/smart-thermostat-buying-guide-on/", "Smart thermostat buying guide for Ontario"),
    ("/blog/smart-thermostat-buying-guide-ma/", "Smart thermostat buying guide for Massachusetts"),
    ("/blog/smart-thermostat-peak-saver-optimization/", "Getting the most from BC Hydro Peak Saver"),
]

FAQ = [
    ("Can I get a free smart thermostat?",
     "Sometimes. BC Hydro customers with baseboard heat can get up to 5 free Mysa or Sinopé thermostats starting October 2026. "
     "Efficiency Nova Scotia installs one free in electrically heated homes with an old thermostat. In Ontario, the free path is the "
     "income-qualified Energy Affordability Program."),
    ("Will an ecobee or Nest work with my baseboard heaters?",
     "No. Ecobee, Nest and most Honeywell smart thermostats are low-voltage. They run furnaces, boilers, central AC and heat pumps. "
     "Baseboard heaters need a line-voltage thermostat like Mysa or Sinopé, one per room or zone."),
    ("What's the difference between a rebate and a bill credit program?",
     "A rebate pays you back once for buying the thermostat. A bill credit (or demand response) program pays you to let your utility "
     "adjust your temperature a little during a few peak hours each season. You can usually opt out of any single event."),
    ("Is there a federal smart thermostat rebate?",
     "No. In Canada the Greener Homes Grant is closed, and in the US there is no federal rebate for a smart thermostat. Rebates now come from "
     "provinces, states, utilities and cities."),
]


def build():
    regions = []
    for r in ROWS:
        if r[0] not in regions:
            regions.append(r[0])
    tables = ""
    for reg in regions:
        rows = [r for r in ROWS if r[0] == reg]
        tables += (f'<h3 id="{reg.lower().replace(" ", "-")}"><a href="{rows[0][1]}">{e(reg)}</a></h3><div class="tw"><table>'
                   '<tr><th>Program</th><th>What you get</th><th>Who qualifies</th><th>Thermostats</th></tr>'
                   + "".join(f'<tr><td><a href="{e(src)}" rel="nofollow noopener" target="_blank">{e(p)}</a></td><td><b>{e(a)}</b></td>'
                             f'<td>{e(w)}</td><td>{e(t)}</td></tr>' for _, _, p, a, w, t, src in rows)
                   + "</table></div>")
    nv = ", ".join(f'<a href="{u}">{e(n)}</a>' for n, u in NOT_VERIFIED)
    short = ("The best deals right now: up to 5 free Mysa or Sinopé thermostats for BC Hydro customers with baseboard heat, "
             "$125 back in Ontario through Home Renovation Savings, and a free installed thermostat for electrically heated homes in Nova Scotia. "
             "First check your heat type: baseboard heaters need a different thermostat than a furnace or heat pump.")
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">Smart thermostat rebates</li></ol></nav>
<header class="hero"><div class="wrap"><h1>Smart Thermostat Rebates 2026: Every Program in Canada and the US</h1>
<p>{len(ROWS)} programs across {len(regions)} provinces and states, each linked to its official source. Last checked {CHECKED}.</p>
<p class="meta">By {AUTHOR['name']}</p></div></header>
<section class="body"><div class="wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> {e(short)}</p></div>

<h2>Step 1: What kind of heat do you have?</h2>
<p>This decides which thermostat you can use, and which rebates you can get.</p>
<div class="tw"><table><tr><th>Your heat</th><th>Thermostat type</th><th>Common brands</th></tr>
<tr><td>Electric baseboard heaters</td><td>Line-voltage, one per room</td><td>Mysa, Sinopé</td></tr>
<tr><td>Furnace, boiler, central AC or ducted heat pump</td><td>Low-voltage (24V), one for the house</td><td>ecobee, Google Nest, Honeywell Home, Sensi</td></tr>
<tr><td>Ductless mini-split heat pump</td><td>Usually the maker's own remote or Wi-Fi add-on</td><td>Mysa for mini-splits, brand Wi-Fi kits</td></tr>
</table></div>
<p>Not sure? Look at your wall. A thick thermostat on each baseboard's wall, or on the heater itself, is line-voltage. One thin thermostat for the whole house is low-voltage.</p>

<h2>Step 2: Smart thermostat rebates by province and state</h2>
{tables}
<p><b>No verified statewide thermostat rebate on file:</b> {nv}. Many utilities there run their own offers, so check your utility's rebate page before you buy.</p>

<h2>Rebate or bill credit: which is better?</h2>
<p>A <b>rebate</b> pays you back once. A <b>bill credit</b> program (sometimes called demand response) pays you to let your utility nudge your temperature for a few hours on the busiest days. Over a few years, bill credits can pay more than a one-time rebate. You can often do both, but read the rules: some rebates exclude you if you've had a thermostat rebate before.</p>

<h2>Deep dives</h2>
<ul>{"".join(f'<li><a href="{u}">{e(t)}</a></li>' for u, t in ARTICLES)}</ul>

<h2>Common questions</h2>
{"".join(f'<h3>{e(q)}</h3><p>{e(a)}</p>' for q, a in FAQ)}

<p><b>Related:</b> <a href="/rebate-tracker/">Rebate tracker: what ended and what's new</a> · <a href="/furnace-rebates/">Furnace and AC rebates</a> · <a href="/installers/">Top-rated installers by city</a></p>
<p class="small">Something out of date? Email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a> and we'll check it within a week.</p>
</div></section>"""
    css = ".tw{overflow-x:auto;-webkit-overflow-scrolling:touch}.tw table{min-width:560px}section.body h3{font-size:20px;margin:26px 0 6px}"
    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": "Smart Thermostat Rebates 2026: Every Program in Canada and the US",
         "description": short, "datePublished": "2026-09-29", "dateModified": ISO, "author": AUTHOR,
         "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE}, "mainEntityOfPage": BASE + PATH},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    page = shell("Smart Thermostat Rebates 2026: Canada & US Programs | HomePowerRebate",
                 "Every smart thermostat rebate in 2026: free Mysa thermostats in BC, $125 in Ontario, free installs in Nova Scotia, plus California and New York utility rebates.",
                 PATH, "on", body, ld)
    page = page.replace("</style>", css + "</style>", 1)
    out = ROOT / PATH.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"Wrote {PATH}: {len(ROWS)} programs, {len(regions)} regions")
    link_articles()


START, END = "<!-- THERMO-LINK-START -->", "<!-- THERMO-LINK-END -->"


def link_articles():
    block = (f'{START}<p style="background:#f5efe5;border-radius:8px;padding:14px 16px;"><b>Every thermostat rebate in one place:</b> '
             f'<a href="{PATH}">smart thermostat rebates by province and state</a>, with official sources.</p>{END}')
    n = 0
    for u, _ in ARTICLES:
        f = ROOT / u.strip("/") / "index.html"
        if not f.exists():
            continue
        s = f.read_text(encoding="utf-8")
        if START in s:
            s = re.sub(re.escape(START) + ".*?" + re.escape(END), block, s, flags=re.S)
        else:
            i = s.find("</article>")
            if i < 0:
                i = navfooter.content_insert_point(s)
            if i < 0:
                continue
            s = s[:i] + block + "\n" + s[i:]
        f.write_text(s, encoding="utf-8")
        n += 1
    print(f"Linked {n} thermostat articles to the hub")


if __name__ == "__main__":
    build()
