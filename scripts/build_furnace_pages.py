#!/usr/bin/env python3
"""Build the "furnace or heat pump?" rebate pages: /furnace-rebates/ plus one page per region.

Answers real Search Console demand ("bc hydro furnace rebate", "ontario new furnace rebate",
"alberta furnace rebates", "bc hydro air conditioner rebate") that no page answered.
Every amount comes from data/verified-facts/*.json (checked Sept 2026) or the official page
linked in SOURCES. Re-run after editing REGIONS; output is fully generated.
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
from build_installer_rankings import BASE, CSS  # noqa: E402

CHECKED = "September 28, 2026"
ISO = "2026-09-28"
AUTHOR = {"@type": "Person", "name": "Sam Menard", "url": f"{BASE}/about"}

REGIONS = {
    "bc": {
        "slug": "bc", "nav": "bc", "name": "BC", "long": "British Columbia", "rank_region": "bc",
        "title": "BC Furnace & AC Rebates 2026: What You Can Get",
        "desc": "BC Hydro has no furnace or AC rebate in 2026. Here's what is available: FortisBC gas furnace offers, heat pump rebates up to $4,000, and CleanBC up to $13,000.",
        "h1": "BC Furnace and Air Conditioner Rebates (2026)",
        "short": "<b>BC Hydro does not give rebates for furnaces or air conditioners in 2026.</b> Its air conditioner offer has ended. "
                 "If you heat with gas, FortisBC has offered a rebate for replacing an old gas furnace with a high-efficiency one. "
                 "The biggest money is for a heat pump, which heats <i>and</i> cools: up to $4,000 from BC Hydro if you're replacing electric heat, "
                 "or up to $13,000 from CleanBC if your household income qualifies and you're switching off gas, oil or propane.",
        "table": [
            ("New gas furnace", "FortisBC (gas customers)", "Has offered up to $1,000 for a 95%+ AFUE ENERGY STAR furnace replacing one 10+ years old. Confirm it's still open in the FortisBC rebate finder."),
            ("New air conditioner", "BC Hydro", "None. BC Hydro's air conditioner offer has ended."),
            ("Heat pump (replacing electric heat)", "BC Hydro", "Up to $4,000 whole-home, or $1,500 partial. Plus up to $1,000 bonus for installs done Aug 1 to Oct 31, 2026."),
            ("Heat pump (replacing gas, oil or propane)", "CleanBC Energy Savings Program", "Income-qualified only: $13,000 / $7,000 / $3,500 by income level. +$3,000 northern top-up for levels 1 and 2."),
            ("Heat pump + gas furnace backup (dual fuel)", "FortisBC (income-qualified)", "FortisBC has offered a large income-qualified dual fuel rebate. Confirm the current amount with FortisBC."),
            ("Free upgrades", "BC Hydro / FortisBC ECAP", "Free assessment and upgrades for income-qualified homes. Some homes get a free heat pump."),
        ],
        "decide": [
            ("Your furnace is gas and under 15 years old", "Keep it. Add a heat pump for cooling and mild-weather heating if summers are getting hot. The furnace becomes backup."),
            ("Your furnace is gas and failing, and your income qualifies", "Look hard at a heat pump first. CleanBC can pay $3,500 to $13,000, which often costs less out of pocket than a new furnace plus AC."),
            ("Your furnace is gas and failing, income doesn't qualify", "Get two quotes: a new furnace (plus AC if you want cooling) and a heat pump. There's no general BC rebate for switching off gas, so compare the real totals."),
            ("You heat with electric baseboards or an electric furnace", "A heat pump is almost always the move. It's the only path with a BC Hydro rebate (up to $4,000) and it cuts your heating bill."),
            ("You only want air conditioning", "Buy a heat pump instead of an AC. It costs about the same, cools just as well, and heats too. A plain AC gets no rebate."),
        ],
        "faq": [
            ("Does BC Hydro give a rebate for a new furnace?", "No. BC Hydro doesn't rebate furnaces. It rebates heat pumps that replace electric heat: up to $4,000, plus up to $1,000 bonus for installs finished by October 31, 2026."),
            ("Does BC Hydro have an air conditioner rebate?", "No. BC Hydro's air conditioner offer has ended. A heat pump cools like an AC and can qualify for a rebate if it replaces electric heat."),
            ("Can I get a rebate to replace my gas furnace with a heat pump in BC?", "Only if your household income qualifies. The CleanBC Energy Savings Program pays $13,000, $7,000 or $3,500 depending on income. The general gas-to-heat-pump rebate ended April 11, 2025."),
            ("Is there a FortisBC furnace rebate?", "FortisBC has offered up to $1,000 for replacing a 10+ year old gas furnace with a 95%+ efficient ENERGY STAR model. Its rebate pages were being reorganized when we checked, so confirm in the FortisBC rebate finder before you buy."),
            ("What should I do if my furnace dies in winter?", "Get it working first: a repair or a like-for-like replacement is fine in an emergency. If you have time, get a heat pump quote too, because rebates only apply to heat pumps and you usually need pre-approval."),
        ],
        "sources": [
            ("BC Hydro heat pump rebate", "https://www.bchydro.com/powersmart/residential/rebates-programs/home-renovation/renovating-heating-system.html"),
            ("BC Hydro product rebates", "https://www.bchydro.com/powersmart/residential/rebates-programs/product-rebates.html"),
            ("CleanBC Energy Savings Program (July 6, 2026 rules)", "https://betterhomesbc.ca/wp-content/uploads/2026/07/RebateEligibilityRequirements_ESP_6July2026.pdf"),
            ("FortisBC rebates and offers", "https://www.fortisbc.com/rebates-and-energy-savings/rebates-and-offers"),
            ("FortisBC ECAP free upgrades", "https://www.fortisbc.com/rebates/detail/free-home-energy-evaluation-and-upgrades"),
        ],
        "links": [("/ca/bc/", "BC rebates by city"), ("/blog/bc-hydro-vs-fortisbc-rebates-which-better/", "BC Hydro vs FortisBC rebates"), ("/blog/furnace-buying-guide/", "Furnace buying guide")],
    },
    "ontario": {
        "slug": "ontario", "nav": "on", "name": "Ontario", "long": "Ontario", "rank_region": "on",
        "title": "Ontario New Furnace Rebate 2026: The Honest Answer",
        "desc": "There's no Ontario rebate for a new gas furnace in 2026. Heat pumps get up to $2,000 for Enbridge gas homes, or $7,500 if you heat with electric, oil or propane.",
        "h1": "Is There an Ontario Rebate for a New Furnace? (2026)",
        "short": "<b>No. There is no Ontario rebate for a new gas furnace in 2026.</b> The Home Renovation Savings Program (run by Enbridge Gas and Save on Energy) pays for cold-climate heat pumps instead. "
                 "If your home heats with Enbridge gas, you can get $500 per ton, up to $2,000. If you heat with electricity, oil, propane or wood, it's $1,250 per ton, up to $7,500. "
                 "You must be pre-approved before the install.",
        "table": [
            ("New gas furnace", "Home Renovation Savings", "None ($0)."),
            ("New central air conditioner", "Home Renovation Savings", "None for a plain AC."),
            ("Cold-climate heat pump, gas-heated home", "Home Renovation Savings (Enbridge customers)", "$500/ton, up to $2,000. Pre-approval required."),
            ("Cold-climate heat pump, electric/oil/propane/wood home", "Home Renovation Savings", "$1,250/ton, up to $7,500. Pre-approval required."),
            ("Ground source heat pump", "Home Renovation Savings", "Up to $12,000 (non-gas homes) or up to $3,000 (gas homes)."),
            ("Smart thermostat", "Home Renovation Savings", "$125."),
            ("Free upgrades", "Energy Affordability Program", "Free for income-qualified homes, including cold-climate heat pumps for oil-heated homes."),
            ("Low-interest loans", "Toronto HELP, Better Homes Ottawa", "Up to $125,000, repaid on your property tax bill."),
        ],
        "decide": [
            ("Your gas furnace is under 15 years old and works", "Keep it. When your AC dies, replace the AC with a cold-climate heat pump (up to $2,000 back). The furnace backs it up on the coldest days."),
            ("Your gas furnace is failing", "Quote both: a new furnace (no rebate) and a heat pump with a small furnace as backup, or a full heat pump. Compare the real totals after the $2,000 rebate."),
            ("You heat with oil, propane or electric baseboards", "A cold-climate heat pump is the strong move: up to $7,500 back and much lower heating bills than oil or propane."),
            ("Your income is limited", "Apply to the Energy Affordability Program first. It can cover upgrades for free."),
            ("You're in Toronto or Ottawa", "Your city's loan program can cover what the rebate doesn't, repaid over up to 20 years on your tax bill."),
        ],
        "faq": [
            ("Is there a rebate for a new furnace in Ontario?", "No. The Home Renovation Savings Program pays $0 for a new gas furnace. It pays for cold-climate heat pumps instead."),
            ("How much is the Ontario heat pump rebate if I have a gas furnace?", "$500 per ton, up to $2,000, for a cold-climate air source heat pump if you're an Enbridge Gas customer. Pre-approval is required."),
            ("How much is it if I heat with oil, propane or electricity?", "$1,250 per ton, up to $7,500, for a cold-climate air source heat pump. Ground source can get up to $12,000."),
            ("Can I keep my furnace and add a heat pump?", "Yes. Many Ontario homes keep the gas furnace as backup and let the heat pump do most of the heating and all of the cooling."),
            ("Is Enbridge still giving furnace rebates?", "Not for gas furnaces. Enbridge's rebates now run through the Home Renovation Savings Program, which covers heat pumps, insulation, windows and thermostats."),
        ],
        "sources": [
            ("Home Renovation Savings: heat pumps", "https://homerenovationsavings.ca/heat-pumps"),
            ("Home Renovation Savings program", "https://homerenovationsavings.ca/"),
            ("Energy Affordability Program", "https://saveonenergy.ca/For-Your-Home/Energy-Affordability-Program"),
            ("Toronto HELP loan", "https://www.toronto.ca/services-payments/water-environment/environmental-grants-incentives/home-energy-loan-program-help/"),
            ("Better Homes Ottawa Loan", "https://ottawa.ca/en/city-hall/budget-finance-and-corporate-planning/funding/environmental-funding/better-homes-ottawa/better-homes-ottawa-loan-program"),
        ],
        "links": [("/ca/on/", "Ontario rebates by city"), ("/blog/ontario-home-renovation-savings-program-explained/", "Home Renovation Savings explained"), ("/blog/furnace-buying-guide/", "Furnace buying guide")],
    },
    "california": {
        "slug": "california", "nav": "ca", "name": "California", "long": "California", "rank_region": "ca",
        "title": "California Furnace & AC Rebates 2026 (PG&E, SCE, SMUD)",
        "desc": "PG&E has no furnace or AC rebate for most homes in 2026, and TECH and HEEHRA heat pump funds are full. What's left: SMUD up to $5,000 and free ESA repairs.",
        "h1": "California Furnace and Air Conditioner Rebates (2026)",
        "short": "<b>Most California homes can't get a rebate for a new furnace or air conditioner in 2026.</b> PG&E's rebate page lists no furnace, AC or heat pump rebate. "
                 "The two big statewide heat pump programs are full: TECH Clean California is waitlist-only, and HEEHRA was fully reserved on February 24, 2026. The federal tax credits ended December 31, 2025. "
                 "What's still open: SMUD customers get up to $3,000 for a heat pump plus up to $2,000 when switching off gas, and income-qualified PG&E customers can get a broken or unsafe gas furnace repaired or replaced free through the Energy Savings Assistance program.",
        "table": [
            ("New gas furnace", "PG&E / SCE / SDG&E", "No rebate. Income-qualified homes can get an unsafe or broken furnace repaired or replaced free (ESA)."),
            ("New central air conditioner", "PG&E / SCE / SDG&E", "No rebate listed for homeowners."),
            ("Heat pump (statewide)", "TECH Clean California", "Waitlist only since Nov 14, 2025. Was $1,000 to $5,000."),
            ("Heat pump (income-qualified)", "HEEHRA (state IRA rebates)", "Fully reserved Feb 24, 2026; new requests waitlisted. Was up to $8,000."),
            ("Heat pump (Sacramento)", "SMUD", "Up to $3,000 for a two-stage or variable-speed heat pump, plus up to $2,000 Go Electric bonus when replacing a gas furnace."),
            ("Heat pump (LA city)", "LADWP", "Check LADWP's current Consumer Rebate Program amounts."),
            ("Federal tax credit", "IRS 25C", "Ended for installs after Dec 31, 2025."),
            ("Free upgrades (income-qualified)", "Energy Savings Assistance (ESA)", "Free furnace and water heater repair or replacement if PG&E finds the gas unit broken or unsafe. Owners and renters."),
        ],
        "decide": [
            ("Your gas furnace works and your AC is dying", "Replace the AC with a heat pump. It costs about the same, cools the same, and can take over most heating. Keep the furnace as backup."),
            ("Your gas furnace is failing and you're a SMUD customer", "Get a heat pump quote first. Up to $5,000 in SMUD rebates often makes it cheaper than a new furnace plus AC."),
            ("Your gas furnace is failing and you're PG&E, SCE or SDG&E", "There's no rebate either way right now. Compare real quotes for a furnace + AC and for a heat pump. Coastal and valley winters are mild, so heat pumps work well."),
            ("Your income is limited", "Apply for Energy Savings Assistance first. If your furnace is broken or unsafe, it can be fixed or replaced free."),
            ("You're on a TECH or HEEHRA waitlist", "Don't sign until your reservation is confirmed. Contractors apply for these, so ask yours to check."),
        ],
        "faq": [
            ("Does PG&E give a rebate for a new furnace?", "No, not for most homes. PG&E's rebate page lists no furnace rebate in 2026. Income-qualified customers can get a broken or unsafe gas furnace repaired or replaced free through the Energy Savings Assistance program."),
            ("Is there a California rebate for a new air conditioner?", "Not from PG&E, SCE or SDG&E for most homeowners. A heat pump replaces an AC and also heats, but the statewide heat pump rebates are full right now."),
            ("Is TECH Clean California still available?", "Single-family incentives were fully reserved on November 14, 2025. New requests go on a waitlist."),
            ("Can I still get the federal tax credit for a heat pump or furnace?", "No. The 25C credit ended for equipment installed after December 31, 2025."),
            ("What does SMUD pay to switch from a gas furnace?", "Up to $3,000 for a qualifying heat pump, plus up to $2,000 from the Go Electric bonus when you replace a gas furnace or gas water heater."),
        ],
        "sources": [
            ("PG&E rebates and incentives", "https://www.pge.com/en/save-energy-and-money/rebates-and-incentives.html"),
            ("PG&E Energy Savings Assistance", "https://www.pge.com/en/save-energy-and-money/energy-saving-programs/energy-savings-assistance-program.html"),
            ("TECH Clean California", "https://techcleanca.com/incentives/single-family-incentives/"),
            ("California Energy Commission: HEEHRA", "https://www.energy.ca.gov/programs-and-topics/programs/inflation-reduction-act-residential-energy-rebate-programs"),
            ("SMUD rebates", "https://www.smud.org/Rebates-and-Savings-Tips/Rebates-for-My-Home"),
            ("SMUD Go Electric bonus", "https://www.smud.org/Rebates-and-Savings-Tips/Improve-Home-Efficiency/Go-Electric-Bonus-Package"),
            ("IRS 25C credit", "https://www.irs.gov/credits-deductions/energy-efficient-home-improvement-credit"),
        ],
        "links": [("/us/ca/", "California rebates by city"), ("/blog/7-california-heat-pump-rebates-you-can-stack/", "California heat pump rebates you can stack"), ("/blog/pge-pre-approval-guide/", "PG&E pre-approval guide")],
    },
    "alberta": {
        "slug": "alberta", "nav": "ab", "name": "Alberta", "long": "Alberta", "rank_region": "ab",
        "title": "Alberta Furnace Rebates 2026: What's Actually Left",
        "desc": "Alberta has no provincial or utility furnace or AC rebate in 2026. Here's what's left: free upgrades for low-income Calgarians and CEIP financing where it's open.",
        "h1": "Alberta Furnace and Air Conditioner Rebates (2026)",
        "short": "<b>Alberta has no provincial or utility rebate for a new furnace or air conditioner in 2026,</b> and we found no ENMAX, ATCO, EPCOR or FortisAlberta heat pump rebate either. "
                 "The federal Greener Homes grant and loan are closed, and the federal oil-to-heat-pump grant closed to Albertans on July 31, 2026. "
                 "What's left: free upgrades (including furnaces) for income-qualified Calgarians, and low-interest CEIP financing in towns where it's open.",
        "table": [
            ("New furnace", "Province / utilities", "None found."),
            ("New air conditioner", "Province / utilities", "None found."),
            ("Heat pump", "Province / utilities", "None found. Federal grants are closed."),
            ("Free furnace and insulation (income-qualified)", "Calgary Home Upgrades Program", "Free. Waitlist in 2026."),
            ("Low-interest financing", "Clean Energy Improvement Program (CEIP)", "Calgary: closed until winter 2026/27. Lethbridge: at capacity. St. Albert: waitlist. Check your town's status."),
        ],
        "decide": [
            ("Your furnace works", "Keep it and service it. Alberta gas is cheap compared to other provinces, so there's no rebate pushing you to switch."),
            ("Your furnace is failing", "Replace it with a high-efficiency (95%+ AFUE) model. If you also want cooling, quote a heat pump against a central AC: it costs about the same and gives you backup heat."),
            ("You live in Calgary and your income is limited", "Apply to the Calgary Home Upgrades Program. It can replace a furnace for free."),
            ("You want to spread the cost", "Check whether CEIP is open in your town. It's repaid on your property tax bill."),
        ],
        "faq": [
            ("Are there furnace rebates in Alberta?", "Not from the province or the major utilities in 2026. Income-qualified Calgarians can get a free furnace through the Calgary Home Upgrades Program."),
            ("Is there an air conditioner rebate in Alberta?", "We found none in 2026. If you're buying cooling, a heat pump costs about the same as central AC and also heats."),
            ("Is the Canada Greener Homes Grant still open?", "No. The Greener Homes grant and loan are closed, and the federal oil-to-heat-pump grant closed to Albertans on July 31, 2026."),
            ("Does ENMAX or ATCO offer a heat pump rebate?", "We couldn't find one on their official sites in September 2026."),
        ],
        "sources": [
            ("Calgary Home Upgrades Program", "https://www.homeupgradesprogram.ca/calgary"),
            ("Calgary CEIP", "https://www.calgary.ca/environment/programs/clean-energy-improvement-program.html"),
            ("CEIP participating towns", "https://ceip.abmunis.ca/residential/residential-program-locations/"),
            ("Canada Greener Homes Initiative (NRCan)", "https://natural-resources.canada.ca/energy-efficiency/home-energy-efficiency/canada-greener-homes-initiative/canada-greener-homes-initiative"),
        ],
        "links": [("/ca/ab/", "Alberta rebates by city"), ("/blog/furnace-buying-guide/", "Furnace buying guide")],
    },
}

e = html.escape


def installer_links(code):
    rows = [r for r in json.loads((ROOT / "installers" / "rankings.json").read_text())
            if r["region"] == code and r["service"] == "heat-pump" and r.get("indexed")]
    rows.sort(key=lambda r: -r["reviews"])
    return rows[:8]


def page(r):
    path = f"/furnace-rebates/{r['slug']}/"
    table = "".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td><td>{e(c)}</td></tr>" for a, b, c in r["table"])
    decide = "".join(f"<tr><td><b>{e(a)}</b></td><td>{e(b)}</td></tr>" for a, b in r["decide"])
    faq = "".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in r["faq"])
    inst = installer_links(r["rank_region"])
    inst_html = "".join(f'<li><a href="{i["url"]}">Top-rated heat pump installers in {e(i["city"])}</a> ({i["reviews"]:,} Google reviews)</li>' for i in inst)
    srcs = " · ".join(f'<a href="{u}" rel="noopener">{e(n)}</a>' for n, u in r["sources"])
    links = " · ".join(f'<a href="{u}">{e(n)}</a>' for u, n in r["links"] + [("/blog/heat-pump-vs-air-conditioner-furnace/", "Furnace and AC vs heat pump")])
    others = " · ".join(f'<a href="/furnace-rebates/{o["slug"]}/">{o["long"]}</a>' for o in REGIONS.values() if o is not r)
    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": r["h1"], "description": r["desc"],
         "datePublished": ISO, "dateModified": ISO, "author": AUTHOR,
         "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE},
         "mainEntityOfPage": BASE + path},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in r["faq"]]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Furnace rebates", "item": BASE + "/furnace-rebates/"},
            {"@type": "ListItem", "position": 3, "name": r["long"], "item": BASE + path}]},
    ]
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/furnace-rebates/">Furnace rebates</a></li><li aria-current="page">{e(r['long'])}</li></ol></nav>
<header class="hero"><div class="wrap"><h1>{e(r['h1'])}</h1>
<p>Updated {CHECKED}. Written by <a href="/about" style="color:inherit;text-decoration:underline;">Sam Menard</a>.</p></div></header>
<section class="body"><div class="wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;margin-bottom:28px;"><p style="margin:0;"><b>Short answer:</b> {r['short']}</p></div>
<h2>What rebates exist for heating and cooling in {e(r['name'])}?</h2>
<div style="overflow-x:auto;"><table><thead><tr><th>Upgrade</th><th>Program</th><th>What you get</th></tr></thead><tbody>{table}</tbody></table></div>
<h2>Should you replace your furnace or switch to a heat pump?</h2>
<p>It depends on your furnace's age, your fuel, and your income. Find the row that sounds like you:</p>
<div style="overflow-x:auto;"><table><thead><tr><th>If&hellip;</th><th>Our honest advice</th></tr></thead><tbody>{decide}</tbody></table></div>
<h2>Before you sign a quote</h2>
<ul><li>Get at least two written quotes, and ask each installer to quote both a furnace and a heat pump.</li>
<li>Ask how they sized the system. A good installer does a heat-loss calculation, not a rule of thumb.</li>
<li>If you want a rebate, get pre-approval <i>before</i> the install. Most programs refuse claims for work already done.</li>
<li>Ask who files the rebate paperwork, and get it in writing.</li></ul>
<h2>Compare top-rated installers near you</h2>
<p>Free for homeowners. We rank local heating companies by their Google reviews. <a href="/installers/how-we-rank/">How we rank</a>.</p>
<ul>{inst_html}</ul>
<p><a href="/installers/">See every city &rarr;</a></p>
<h2>Common questions</h2>
{faq}
<p style="font-size:14px;color:#1a3d42;margin-top:28px;"><b>Sources, checked {CHECKED}:</b> {srcs}. Amounts change; confirm with the program before you buy.</p>
<p><b>Related:</b> {links}</p>
<p><b>Other regions:</b> {others}</p>
</div></section>"""
    return path, shell(r["title"] + " | HomePowerRebate", r["desc"], path, r["nav"], body, ld)


def hub():
    path = "/furnace-rebates/"
    cards = "".join(f'<li><a href="/furnace-rebates/{r["slug"]}/"><b>{e(r["long"])}</b></a>: {e(r["desc"])}</li>' for r in REGIONS.values())
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">Furnace rebates</li></ol></nav>
<header class="hero"><div class="wrap"><h1>Furnace and AC Rebates by Province and State (2026)</h1>
<p>Updated {CHECKED}.</p></div></header>
<section class="body"><div class="wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;margin-bottom:28px;"><p style="margin:0;"><b>Short answer:</b> In 2026, almost no program in Canada or California pays you to buy a new gas furnace or a plain air conditioner. The money has moved to heat pumps, which heat and cool in one system. Pick your province to see what's really available and whether switching makes sense for your home.</p></div>
<ul style="line-height:1.9;">{cards}</ul>
<p>Not sure which system fits? Read <a href="/blog/heat-pump-vs-air-conditioner-furnace/">furnace and AC vs heat pump</a>.</p>
</div></section>"""
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Furnace and AC Rebates by Province and State", "url": BASE + path, "dateModified": ISO}]
    return path, shell("Furnace & AC Rebates by Province & State (2026) | HomePowerRebate",
                       "Is there a rebate for a new furnace or air conditioner? Province-by-province answers for BC, Ontario, Alberta and California, checked September 2026.",
                       path, "on", body, ld)


def shell(title, desc, path, nav, body, ld):
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    out = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-W33G4TGRHD');</script>
<meta name="description" content="{e(desc)}"><meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large"><link rel="canonical" href="{BASE}{path}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{BASE}{path}"><meta property="og:type" content="article">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}
table{{width:100%;border-collapse:collapse;margin:12px 0 24px;font-size:15px;}}th,td{{text-align:left;padding:10px 12px;border-bottom:1px solid #d9d0c1;vertical-align:top;}}th{{background:#f5efe5;}}</style>
{lds}</head><body>
{navfooter.render_nav(nav, "")}
{body}
{navfooter.render_footer(nav, "", "", path)}
</body></html>
"""
    return navfooter.ensure_shared_assets(out)


LINK_START, LINK_END = "<!-- FURNACE-LINK-START -->", "<!-- FURNACE-LINK-END -->"
# Pages already getting furnace/AC impressions in Search Console -> which region pages to link.
INBOUND = {
    "blog/heat-pump-vs-air-conditioner-furnace/index.html": ("bc", "ontario", "alberta", "california"),
    "blog/bc-hydro-product-rebates-appliances/index.html": ("bc",),
    "ca/bc/index.html": ("bc",),
    "ca/on/index.html": ("ontario",),
    "ca/ab/index.html": ("alberta",),
    "us/ca/index.html": ("california",),
    "blog/pge-pre-approval-guide/index.html": ("california",),
}


def link_inbound():
    for rel, slugs in INBOUND.items():
        f = ROOT / rel
        s = f.read_text(encoding="utf-8")
        links = " · ".join(f'<a href="/furnace-rebates/{REGIONS[k]["slug"]}/">{REGIONS[k]["long"]} furnace &amp; AC rebates</a>' for k in slugs)
        block = (f'{LINK_START}<p style="max-width:760px;margin:24px auto;padding:14px 18px;background:#f5efe5;border-radius:8px;">'
                 f'<b>Replacing a furnace or air conditioner?</b> See what rebates really exist, and when a heat pump makes more sense: {links}</p>{LINK_END}')
        if LINK_START in s:
            s = s[:s.index(LINK_START)] + block + s[s.index(LINK_END) + len(LINK_END):]
        elif "<h2>Heat pump rebates in 2026</h2>" in s:
            s = s.replace("<h2>Heat pump rebates in 2026</h2>", block + "\n    <h2>Heat pump rebates in 2026</h2>", 1)
        else:
            i = s.index("<footer")
            s = s[:i] + block + "\n" + s[i:]
        f.write_text(s, encoding="utf-8")


def main():
    link_inbound()
    pages = [hub()] + [page(r) for r in REGIONS.values()]
    for path, out in pages:
        f = ROOT / path.strip("/") / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(out, encoding="utf-8")
    print(f"{len(pages)} furnace pages written.")


if __name__ == "__main__":
    main()
