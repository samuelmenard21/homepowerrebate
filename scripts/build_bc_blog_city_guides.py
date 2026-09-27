#!/usr/bin/env python3
"""
Rebuild the body of the four BC blog city families (plus their BC-wide hubs):

  blog/heat-pump-rebate-guide-<city>-2026/      (hub: heat-pump-rebate-guide-bc-2026)
  blog/free-heat-pump-bc-income-qualified-<city>/ (hub: free-heat-pump-bc-income-qualified)
  blog/energy-saving-ideas-bc-home-<city>/      (hub: energy-saving-ideas-bc-home)
  blog/window-doors-replacement-rebates-bc-guide-<city>/ (hub: window-doors-replacement-rebates-bc-guide)

Why: the old pages were find-and-replace copies (98-99% identical) and carried stale
or wrong numbers ("$4,000-$16,000", "~$21,000", "EnerGuide required", "Kelowna is FortisBC
but amounts are the same", invented savings). Every number here comes from
data/verified-facts/bc-blog.json (checked 2026-09-26).

What it touches: only <title>, meta description, og:title/og:description, the Article/
BlogPosting JSON-LD (replaced by Article + FAQPage), the BreadcrumbList name, the
breadcrumb label, and everything between CANONICAL-BREADCRUMB-END and </article>.
Nav, footer, CSS and scripts are left alone. Idempotent: re-running gives the same output.

Usage: python3 scripts/build_bc_blog_city_guides.py [--check]
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = "2026-09-26"
TODAY_H = "September 26, 2026"

# ---------------------------------------------------------------- sources
S = {
    "bch_hp": ("BC Hydro heat pump rebates", "https://www.bchydro.com/powersmart/residential/rebates-programs/home-renovation/renovating-heating-system.html"),
    "bch_ins": ("BC Hydro insulation rebates", "https://www.bchydro.com/powersmart/residential/rebates-programs/home-renovation/renovating-insulation.html"),
    "bch_win": ("BC Hydro window and door rebates", "https://www.bchydro.com/powersmart/residential/rebates-programs/home-renovation/renovating-windows-and-doors.html"),
    "bch_hpwh": ("BC Hydro heat pump water heater rebate", "https://www.bchydro.com/powersmart/residential/rebates-programs/home-renovation/renovating-water-heater.html"),
    "bch_income": ("BC Hydro programs based on income", "https://www.bchydro.com/powersmart/residential/rebates-programs/savings-based-on-income.html"),
    "bch_ev": ("BC Hydro home EV charger rebate", "https://www.bchydro.com/powersmart/electric-vehicles/rebates-incentives/rebates-home-chargers.html"),
    "bch_evtop": ("BC Hydro charger rebate top-ups", "https://www.bchydro.com/powersmart/electric-vehicles/rebates-incentives/local-rebate-top-ups.html"),
    "thermo": ("B.C. government: free smart thermostats (2026)", "https://news.gov.bc.ca/releases/2026ECS0037-000794"),
    "esp": ("CleanBC Energy Savings Program rules (July 6, 2026)", "https://betterhomesbc.ca/wp-content/uploads/2026/07/RebateEligibilityRequirements_ESP_6July2026.pdf"),
    "fb_hp": ("FortisBC heat pump rebate", "https://www.fortisbc.com/rebates/detail/air-source-heat-pump-rebate"),
    "fb_iq": ("FortisBC income-qualified heat pump rebate", "https://www.fortisbc.com/rebates/detail/iqheatpump"),
    "fb_win": ("FortisBC window and door rebates", "https://www.fortisbc.com/rebates/detail/door-window-rebates"),
    "fb_ins": ("FortisBC insulation rebates", "https://www.fortisbc.com/rebates/detail/insulation-rebates"),
    "fb_thermo": ("FortisBC connected thermostat rebate", "https://www.fortisbc.com/rebates/detail/connected-thermostat-rebates"),
    "fb_bonus": ("FortisBC home renovation bonus rebates", "https://www.fortisbc.com/rebates/detail/home-renovation-bonus-rebates"),
    "ecap": ("ECAP: free home energy evaluation and upgrades", "https://www.fortisbc.com/rebates/detail/free-home-energy-evaluation-and-upgrades"),
    "nanaimo": ("City of Nanaimo retrofit loans (Sept 2026)", "https://www.nanaimo.ca/NewsReleases/NR260901ApplicationsOpeningForCityOfNanaimoZeroInterestHomeRetrofitLoans.html"),
    "penticton": ("City of Penticton Home Energy Loan Program", "https://www.penticton.ca/city-services/utility-electrical-services/electric-water-accounts/home-energy-loan-program-help"),
}

# ---------------------------------------------------------------- cities
# utility: bch = BC Hydro, fortis = FortisBC electric, pent = City of Penticton electric (FortisBC rebates apply)
# Every "local" line below is either a verified program (see facts file) or plain, non-numeric local context.
CITIES = {
    "abbotsford": dict(name="Abbotsford", util="bch", gas="FortisBC", north=False,
        where="in the Fraser Valley, where winters are wetter and a little colder than in Vancouver, and summers get hot enough that cooling matters",
        home="Lots of Abbotsford homes are 1980s-1990s houses with a gas furnace and ducts. That makes a central ducted heat pump the natural fit, but it also means most families here are on gas, not electric heat, so the BC Hydro rebate often does not apply.",
        tip="If you have a gas furnace and air conditioning already, ask about replacing the AC with a heat pump when it wears out. The heat pump covers cooling and most heating, and the furnace stays as backup.",
        local=["Abbotsford is on BC Hydro for power and FortisBC for gas. A gas-heated home here only gets heat pump money through the income-qualified CleanBC program right now."],
        faq=("Does Abbotsford have its own heat pump top-up?", "We could not confirm a current City of Abbotsford top-up. The provincial and BC Hydro rebates on this page are the ones we can confirm. Ask the city's sustainability team before you plan around a local top-up.")),
    "burnaby": dict(name="Burnaby", util="bch", gas="FortisBC", north=False,
        where="in Metro Vancouver, with mild, rainy winters that suit heat pumps very well",
        home="Burnaby has many condos and townhomes as well as older houses with baseboard heat. For a house on baseboards, a ductless multi-split is the usual path to BC Hydro's whole-home rebate.",
        tip="Many Burnaby homes are strata. If you live in a condo or townhouse, check your strata bylaws before you book an install, because outdoor units usually need approval.",
        local=["The City of Burnaby's climate-friendly home upgrades page points residents to provincial rebates and the free CleanBC Energy Coach. We did not find a separate city cash top-up."],
        faq=("Can I get a heat pump rebate for a Burnaby condo?", "BC Hydro runs separate offers for condos and apartments. The house rebates on this page are for single-family homes, row homes and similar. Check BC Hydro's condo page and your strata rules first.")),
    "chilliwack": dict(name="Chilliwack", util="bch", gas="FortisBC", north=False,
        where="at the east end of the Fraser Valley, where outflow winds can make winter feel much colder than the thermometer says",
        home="Chilliwack has a mix of older rural homes, some on oil or propane, and newer subdivisions on gas. Homes still on oil or propane are the ones with the most to gain from switching.",
        tip="Size matters here. Ask your installer to size the heat pump for Chilliwack's cold outflow days, not an average winter day. BC Hydro's whole-home rebate needs a heat load calculation anyway.",
        local=["The City of Chilliwack has an information page on CleanBC rebates and top-ups. We could not confirm a separate, current city-funded cash top-up."],
        faq=("Is Chilliwack too cold for a heat pump?", "No. Cold-climate heat pumps keep heating well below -5°C. BC Hydro's whole-home rebate already requires the system to meet 100% of your heat at -5°C, and your backup heat covers rare colder days.")),
    "coquitlam": dict(name="Coquitlam", util="bch", gas="FortisBC", north=False,
        where="in the Tri-Cities, where the hillside neighbourhoods get more rain and a bit more cold than the flats near the river",
        home="Coquitlam has plenty of split-level and hillside homes built in the 1970s to 1990s. Many have baseboard heat upstairs and a gas furnace or fireplace below, which is why partial-home setups are common here.",
        tip="If part of your home is on baseboards and part on gas, remember the BC Hydro rebate is for replacing electric heat. Ask your installer which rebate your mix actually fits before you pick the system.",
        local=["Coquitlam gets electricity from BC Hydro and gas from FortisBC. If your home uses both (say, baseboards upstairs and a gas fireplace below), both utilities' rebate rules can matter, so check each one.",
               "We could not confirm a current City of Coquitlam heat pump top-up."],
        faq=("Does Coquitlam add money on top of the provincial rebates?", "We could not confirm a current City of Coquitlam top-up. Check coquitlam.ca before you count on one.")),
    "fort-st-john": dict(name="Fort St. John", util="bch", gas="Pacific Northern Gas", north=True,
        where="in the Peace region, one of the coldest parts of BC, with long winters and deep cold snaps",
        home="Most Fort St. John homes heat with natural gas from Pacific Northern Gas. A heat pump here works as the main heat for much of the year, with a backup for the coldest weeks.",
        tip="Plan for a strong backup. In the Peace, a heat pump plus a furnace or electric backup is the honest setup. Ask for a cold-climate model and a proper load calculation.",
        local=["Fort St. John is north of 100 Mile House, so income-qualified homes switching from gas, oil or propane can get the CleanBC northern top-up of $3,000 (or $1,500 for a single-head mini-split), for Income Levels 1 and 2."],
        faq=("Does the northern top-up apply in Fort St. John?", "Yes, if you qualify for the CleanBC Energy Savings Program at Income Level 1 or 2, are switching from fossil fuel, and are connected to BC Hydro. It adds $3,000 for ducted, multi-split or two single-head systems, or $1,500 for one single-head mini-split.")),
    "kamloops": dict(name="Kamloops", util="bch", gas="FortisBC", north=False,
        where="in the Thompson valley, with hot, dry summers and cold, clear winter spells",
        home="Kamloops homes need real heating and real cooling. That makes a heat pump a two-for-one, since it replaces the air conditioner and does most of the heating too.",
        tip="If your AC is near the end of its life, that is the time to switch. You pay once for a system that heats and cools, instead of replacing the AC like-for-like.",
        local=["The City of Kamloops adds up to $150 to BC Hydro's home EV charger rebate. It is added automatically when you apply through BC Hydro."],
        faq=("Does Kamloops get the northern top-up?", "No. The CleanBC northern top-up starts at 100 Mile House and goes north. Kamloops is south of that line.")),
    "kelowna": dict(name="Kelowna", util="fortis", gas="FortisBC", north=False,
        where="in the Okanagan, with hot summers and cold, grey inversion winters",
        home="Kelowna is FortisBC country for both electricity and gas. That means BC Hydro's rebates and Peak Saver do not apply here. FortisBC runs its own heat pump, insulation and window rebates instead.",
        tip="Because the utility is FortisBC, apply through FortisBC's rebate portal, not BC Hydro's. Your contractor should know the FortisBC rules, including the cold-climate listing needed for the whole-home rebate.",
        local=["FortisBC is the electric utility in Kelowna, so BC Hydro programs (including Peak Saver and BC Hydro's heat pump rebate) are not available. Use FortisBC's matching programs."],
        faq=("Can Kelowna homeowners use BC Hydro rebates?", "No. Kelowna's electricity comes from FortisBC, and FortisBC customers are not eligible for BC Hydro programs. FortisBC offers its own heat pump rebate (up to $4,000) and an income-qualified version (up to $12,000).")),
    "langley": dict(name="Langley", util="bch", gas="FortisBC", north=False,
        where="between Surrey and Abbotsford, with a mix of suburban streets and acreages",
        home="Langley has newer gas-heated subdivisions and older acreage homes, some still on oil or propane. Acreage homes on oil or propane usually get the biggest benefit from switching.",
        tip="On an acreage, the outdoor unit can sit far from the house, but longer line sets cost more. Ask for the placement in writing on your quote.",
        local=["We could not confirm a current City or Township of Langley heat pump top-up. Check with your municipality (the City and Township are separate) before you count on one."],
        faq=("Is Langley City different from Langley Township for rebates?", "The provincial and BC Hydro rebates are the same in both. Any local top-up would come from your own municipality, and we could not confirm a current one in either.")),
    "maple-ridge": dict(name="Maple Ridge", util="bch", gas="FortisBC", north=False,
        where="on the north side of the Fraser, where it tends to be wetter and a bit colder than central Metro Vancouver",
        home="Maple Ridge has a lot of 1970s-1990s houses, many with baseboard heat in at least part of the home. Those homes are a good match for BC Hydro's electric-to-heat-pump rebate.",
        tip="If you have baseboards, pair the heat pump with attic insulation. BC Hydro pays a bonus of up to $2,000 when you do more than one upgrade.",
        local=["Maple Ridge is on BC Hydro, so the BC Hydro electric-to-heat-pump rebate, insulation rebate and Peak Saver all apply to electrically heated homes here.",
               "Some online sources describe a Maple-Ridge-only top-up, but they appear to be mixing it up with BC Hydro's rebate. We could not confirm a city program."],
        faq=("Does Maple Ridge have its own top-up?", "We could not confirm a Maple-Ridge-only top-up. Some websites mix up BC Hydro's rebates with a city program. Check mapleridge.ca before you count on one.")),
    "nanaimo": dict(name="Nanaimo", util="bch", gas="FortisBC", north=False,
        where="on central Vancouver Island, with mild, wet winters that are close to ideal for heat pumps",
        home="Many Nanaimo homes use baseboards, oil or older gas furnaces. The island's mild winters mean a well-sized heat pump can carry nearly the whole heating load.",
        tip="Nanaimo is one of the few cities in our list with its own low-cost financing. If the up-front cost is what's stopping you, look at the city loan below before you give up.",
        local=["City of Nanaimo Home Energy Retrofit Financing: zero-interest loans up to $15,000, paid back over 10 years on your property tax bill. It covers heat pumps, insulation, windows and doors, and solar. Applications are open Sept 14 to Oct 31, 2026, and you must register with the free Home Energy Navigator.",
               "The Regional District of Nanaimo adds $150 to BC Hydro's home EV charger rebate for homes in its electoral areas (a separate application)."],
        faq=("What is Nanaimo's zero-interest retrofit loan?", "The City of Nanaimo lends up to $15,000 at 0% for heat pumps, insulation, windows and doors, or solar. You repay it over 10 years on your property tax bill. The 2026 intake runs Sept 14 to Oct 31.")),
    "penticton": dict(name="Penticton", util="pent", gas="FortisBC", north=False,
        where="in the South Okanagan, with hot summers and fairly mild winters for the Interior",
        home="Penticton runs its own electric utility. Penticton electric customers use FortisBC's rebate programs, not BC Hydro's.",
        tip="Penticton's own loan can cover the part rebates don't. Pair it with FortisBC's rebate and you may not need to pay much up front.",
        local=["City of Penticton Home Energy Loan Program (HELP): up to $10,000 over 10 years, repaid on your city electric bill at prime plus 0.5%. It covers upgrades that match FortisBC's rebates (heat pumps, insulation, windows and doors, air sealing). The city says the program is being redesigned, so confirm the terms first.",
               "Penticton electric customers qualify for FortisBC's electric rebates, including the heat pump rebate."],
        faq=("Who gives heat pump rebates in Penticton?", "FortisBC. Penticton's city electric utility customers are eligible for FortisBC's heat pump rebate (up to $4,000, or up to $12,000 if income-qualified), not BC Hydro's.")),
    "prince-george": dict(name="Prince George", util="bch", gas="FortisBC", north=True,
        where="in northern BC, with long, cold winters",
        home="Most Prince George homes heat with natural gas. A cold-climate heat pump can carry much of the load, with a furnace or electric backup for the coldest stretches.",
        tip="Ask for a model that holds its heating output at low temperatures, and ask how the backup will switch on. A good installer will show you the numbers for Prince George winters.",
        local=["Prince George is north of 100 Mile House, so income-qualified homes switching from gas, oil or propane can get the CleanBC northern top-up of $3,000 (or $1,500 for a single-head mini-split), for Income Levels 1 and 2."],
        faq=("Does a heat pump work in a Prince George winter?", "Yes, as part of a system. A cold-climate heat pump handles most of the year. On the coldest days, backup heat takes over. For income-qualified homes, the northern top-up helps cover the cost.")),
    "richmond": dict(name="Richmond", util="bch", gas="FortisBC", north=False,
        where="on the Fraser delta, with some of the mildest winters in the Lower Mainland",
        home="Richmond has many gas-heated houses and a lot of townhomes. Mild winters mean heat pumps run very efficiently here.",
        tip="With mild winters, a smaller system often does the job. Get two quotes and compare the heat load numbers, not just the price.",
        local=["An older Richmond heat pump top-up tied to the previous CleanBC program appears to have closed. We could not confirm a current one."],
        faq=("Is there still a Richmond heat pump top-up?", "We could not confirm one. The older top-up pages no longer load. Ask the City of Richmond before you count on it.")),
    "squamish": dict(name="Squamish", util="bch", gas="FortisBC", north=False,
        where="between the ocean and the mountains, with wet winters and strong outflow winds",
        home="Squamish has lots of newer homes and townhouses, plus older houses on baseboards. Wind exposure is a real factor for where an outdoor unit goes.",
        tip="Place the outdoor unit out of the worst wind and off the ground so snow and rain can drain. Ask your installer how they will protect it.",
        local=["The District of Squamish adds up to $150 to BC Hydro's home EV charger rebate. It is added automatically when you apply through BC Hydro."],
        faq=("Are there Squamish-only rebates?", "The one we could confirm is the District of Squamish EV charger top-up of up to $150. For heat pumps, use the BC Hydro and CleanBC rebates on this page.")),
    "surrey": dict(name="Surrey", util="bch", gas="FortisBC", north=False,
        where="in the Lower Mainland, with mild coastal winters",
        home="Surrey is big and varied, from older ranchers in Whalley and Guildford to new builds in South Surrey. Most houses heat with gas. Some older homes and basement suites use baseboards.",
        tip="If you have a basement suite on baseboards, it can be a good spot for a single mini-split. BC Hydro's partial-home rebate may apply if the heat pump meets at least half the home's heating.",
        local=["The City of Surrey offers retrofit support that connects residents to existing rebates. We did not find a separate city cash top-up."],
        faq=("Does Surrey pay its own heat pump rebate?", "We did not find a city cash rebate. Surrey offers help finding and applying for existing rebates.")),
    "vancouver": dict(name="Vancouver", util="bch", gas="FortisBC", north=False,
        where="on the coast, with mild, wet winters",
        home="Most Vancouver houses heat with gas. The city has pushed hard toward heat pumps for years, and many older homes have enough ducting for a central system.",
        tip="Window rebates from BC Hydro and FortisBC do not apply inside City of Vancouver limits, so put your budget into the heat pump and insulation first.",
        local=["BC Hydro and FortisBC both list the City of Vancouver as not eligible for their window and door rebate.",
               "The City of Vancouver has offered its own heat pump top-ups in the past. The official pages did not load when we checked, so confirm with the city before you count on one."],
        faq=("Can I get a window rebate in Vancouver?", "Not from BC Hydro or FortisBC. Both list the City of Vancouver as excluded from their window and door rebate.")),
    "vernon": dict(name="Vernon", util="bch", gas="FortisBC", north=False,
        where="in the North Okanagan, with hot summers and colder winters than the South Okanagan",
        home="Vernon gets its power from BC Hydro and its gas from FortisBC. So BC Hydro's rebates and Peak Saver apply here, unlike in Kelowna.",
        tip="Neighbours in Kelowna use FortisBC programs. In Vernon, apply through BC Hydro, so don't follow a Kelowna quote's rebate math.",
        local=["Vernon's electric utility is BC Hydro, so BC Hydro rebates and Peak Saver apply."],
        faq=("Is Vernon on BC Hydro or FortisBC?", "Electricity in Vernon comes from BC Hydro; natural gas comes from FortisBC. Use BC Hydro's electric rebates.")),
    "victoria": dict(name="Victoria", util="bch", gas="FortisBC", north=False,
        where="on southern Vancouver Island, with the mildest winters in Canada",
        home="Victoria has a lot of older character homes, many heated by oil, gas or baseboards. Oil-heated homes are the biggest winners from switching.",
        tip="If you still have an oil tank, ask about removal costs up front. Insurers often care about old tanks, and the heat pump project is the natural time to deal with it.",
        local=["The City of Victoria's rental retrofit program is for apartment building owners, not homeowners."],
        faq=("Is Victoria a good place for a heat pump?", "Yes. Victoria's mild winters mean heat pumps run efficiently almost all year. The main question is which rebate fits your current heat.")),
}
ORDER = list(CITIES)

# ---------------------------------------------------------------- helpers
def a(key, label=None):
    name, url = S[key]
    return f'<a href="{url}" target="_blank" rel="noopener">{label or name}</a>'


def sources_line(keys):
    return ('<p class="hpr-sources"><strong>Sources, checked ' + TODAY_H + ':</strong> ' +
            " · ".join(a(k) for k in keys) + '.</p>')


def util_name(c):
    return {"bch": "BC Hydro", "fortis": "FortisBC", "pent": "City of Penticton (FortisBC rebates)"}[c["util"]]


def fortis(c):
    return c is not None and c["util"] in ("fortis", "pent")


def local_block(c):
    items = c["local"] or [f"We could not confirm a current {c['name']}-only rebate or top-up. The provincial and utility rebates on this page are the ones we could check."]
    return "<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


def cta(c):
    city = c["name"] if c else None
    href = f"/get-quotes/?city={c['name'].replace(' ', '+')}&province=BC" if c else "/ca/bc/"
    label = f"Compare top-rated {city} installers" if c else "See your city's rebates"
    return (f'<div class="hpr-cta"><h3>{"See your city" + chr(39) + "s rebates" if not c else "Ready to check your home in " + city + "?"}</h3>'
            f'<p>Compare top-rated local installers, ranked by Google reviews. Free for homeowners, and we\'ll tell you honestly if the math doesn\'t work for your home.</p>'
            f'<a class="hpr-btn" href="{href}">{label} &rarr;</a></div>')


def city_picker(fam_slug):
    links = " · ".join(f'<a href="/blog/{fam_slug(s)}/">{CITIES[s]["name"]}</a>' for s in ORDER)
    return f'<p class="hpr-cities"><strong>Pick your city:</strong> {links}</p>'


def faq_html(faqs):
    out = ['<h2>Questions people ask</h2>']
    for q, ans in faqs:
        out.append(f'<h3>{q}</h3><p>{ans}</p>')
    return "\n".join(out)


def related(links):
    return '<div class="related"><h4>Keep reading</h4>' + "".join(f'<a href="{h}">{t}</a>' for h, t in links) + '</div>'


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


# ---------------------------------------------------------------- family: heat pump rebate guide
def hp_slug(s):
    return f"heat-pump-rebate-guide-{s}-2026"


def build_hp(c, slug):
    nm = c["name"] if c else "BC"
    where = f"in {nm}" if c else "in BC"
    if c and fortis(c):
        short = (f"In {nm}, heat pump rebates come from <strong>FortisBC</strong>, not BC Hydro. If you heat with electric baseboards or an electric furnace, "
                 f"FortisBC pays up to <strong>$4,000</strong> for a whole-home heat pump or <strong>$1,500</strong> for a partial one. "
                 f"Income-qualified homes can get up to <strong>$12,000</strong>. If you heat with gas, only income-qualified homes get CleanBC money now.")
    else:
        short = (f"If you heat with <strong>electric baseboards or an electric furnace</strong>, BC Hydro pays up to <strong>$4,000</strong> for a whole-home heat pump "
                 f"or <strong>$1,500</strong> for a partial one, plus up to <strong>$1,000</strong> extra for installs finished Aug 1 to Oct 31, 2026. "
                 f"If you heat with <strong>gas, oil or propane</strong>, only income-qualified homes get a rebate now: up to <strong>$13,000</strong> at the lowest income level"
                 + (", plus a <strong>$3,000</strong> northern top-up here." if c and c["north"] else ".")
                 + (" In Kelowna and Penticton, FortisBC runs the electric rebates instead." if not c else ""))
    title = f"Heat Pump Rebates in {nm}, BC (2026 Guide)" if c else "BC Heat Pump Rebates 2026: What You Can Get"
    desc = (f"{nm} heat pump rebates for 2026: " + ("FortisBC up to $4,000 ($12,000 income-qualified)" if c and fortis(c) else "BC Hydro up to $4,000 from electric heat, CleanBC up to $13,000 if income-qualified")
            + ". Who qualifies and what to do next.")
    body = [f'<div class="callout hpr-short"><p><strong>Short answer:</strong> {short}</p></div>']
    if c:
        body.append(f"<p>{nm} is {c['where']}. {c['home']}</p>")
    else:
        body.append("<p>There is no longer one \"BC heat pump rebate\" for everyone. What you can get depends on three things: who your electric utility is, what heats your home now, and your household income. This guide walks through each one in plain language.</p>")

    body.append(f"<h2>Which heat pump rebate fits your home {where}?</h2>")
    rows = []
    if not c or not fortis(c):
        rows += [
            ("Electric baseboards or electric furnace (any income)", "BC Hydro", "Up to $4,000 whole home, $1,500 partial, plus up to $1,000 bonus for installs done Aug 1 - Oct 31, 2026"),
            ("Gas, oil or propane, income-qualified", "CleanBC Energy Savings Program", "Up to $13,000 (Level 1), $7,000 (Level 2), $3,500 (Level 3) for a central or 3-head system" + (" + $3,000 northern top-up" if (c and c["north"]) else "")),
            ("Electric heat, income Level 1", "CleanBC Energy Savings Program", "Up to $5,000 (Level 1 only)"),
            ("Gas, oil or propane, not income-qualified", "None right now", "The general fuel-switching rebate ended April 11, 2025"),
        ]
    if not c or fortis(c):
        rows += [
            ("FortisBC electric customer (Kelowna, Penticton), electric heat" if not c else "Electric baseboards or electric furnace", "FortisBC", "Up to $4,000 whole home, $1,500 partial"),
            ("FortisBC electric customer, income-qualified" if not c else "Electric heat, income-qualified", "FortisBC", "Up to $12,000 central ducted, $9,000 mini/multi-split, $5,000 partial"),
        ]
        if c:
            rows.append(("Gas, income-qualified", "CleanBC Energy Savings Program", "Up to $13,000 (Level 1), $7,000 (Level 2), $3,500 (Level 3) for a central or 3-head system"))
    body.append('<div class="hpr-table"><table><thead><tr><th>Your home now</th><th>Who pays</th><th>How much</th></tr></thead><tbody>' +
                "".join(f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td></tr>" for r in rows) + "</tbody></table></div>")

    if not c or not fortis(c):
        body.append("<h2>What \"whole home\" really means for BC Hydro</h2>"
                    "<p>To get the full $4,000, the heat pump has to meet <strong>100% of your home's heating at -5°C</strong>. The contractor proves this with a heat load calculation. "
                    "If it covers at least half your heating, you get the $1,500 partial rebate instead. Other rules: your installer must be a member of BC Hydro's Home Performance Contractor Network (HPCN), "
                    "and the unit must be on BC Hydro's eligible list (variable-speed, with an AHRI number, HSPF2 of 8.5 or more and SEER2 of 15.2 or more). Apply within six months of your invoice.</p>")
    if not c or fortis(c):
        body.append("<h2>How FortisBC's heat pump rebate works</h2>"
                    "<p>FortisBC's rebate is for replacing electric heat. For the $4,000 whole-home amount, the heat pump must be NEEP cold-climate certified and sized from a heat load calculation. "
                    "A single mini-split only counts for homes of 1,200 sq. ft. or less. FortisBC also pays a $300 bonus when you do a second eligible upgrade, like insulation.</p>")

    body.append("<h2>Income-qualified? Check this first</h2>"
                "<p>If your household income is under the CleanBC limits, you may get most or all of the cost covered. For a family of four, Level 1 is up to $94,900, Level 2 up to $118,600 and Level 3 up to $189,800 (combined pre-tax income). "
                f'See <a href="/blog/free-heat-pump-bc-income-qualified{"-" + slug if c else ""}/">can you get a free heat pump{" in " + nm if c else ""}</a> for the full table.</p>')

    if c:
        body.append(f"<h2>What's different in {nm}</h2>{local_block(c)}<p><strong>My tip for {nm}:</strong> {c['tip']}</p>")
    else:
        body.append("<h2>Your city</h2><p>Most of BC is BC Hydro. Kelowna is FortisBC, and Penticton runs its own utility that uses FortisBC's rebates. Prince George and Fort St. John are north of 100 Mile House, so income-qualified homes there get a northern top-up. Nanaimo and Penticton have city retrofit loans.</p>" + city_picker(hp_slug))

    body.append("<h2>What to do next</h2><ol>"
                "<li><strong>Check your current heat.</strong> Electric, gas, oil or propane decides which rebate you can get.</li>"
                "<li><strong>Check your income</strong> against the CleanBC table. If you qualify, pre-register before any work starts.</li>"
                f"<li><strong>Hire a qualified contractor</strong>{' (an HPCN member for BC Hydro)' if not fortis(c) else ''}. They do the heat load calculation and pick an eligible model.</li>"
                "<li><strong>Ask about insulation too.</strong> Doing two upgrades can add a bonus, and a tighter home needs a smaller heat pump.</li>"
                "<li><strong>Apply within six months</strong> of your final invoice.</li></ol>")

    faqs = []
    if not c or not fortis(c):
        faqs.append(("Is the BC Hydro heat pump rebate for gas homes?", "No. BC Hydro's rebate is only for replacing electric heat. Gas, oil and propane homes can only get a rebate through the income-qualified CleanBC Energy Savings Program right now."))
        faqs.append(("Is the BC Hydro whole-home rebate based on 80% of my space?", "No. BC Hydro's whole-home rebate needs the heat pump to meet 100% of your heating at -5°C. Covering 50% or more gets the $1,500 partial rebate."))
    else:
        faqs.append((f"Does BC Hydro's heat pump rebate apply in {nm}?", f"No. {nm} homes use FortisBC's rebates. FortisBC pays up to $4,000 for replacing electric heat, or up to $12,000 if you are income-qualified."))
    faqs.append(("Did CleanBC rebates change in 2026?", "Yes. For invoices on or after July 6, 2026, the income-qualified maximums dropped. The top amount for a gas-to-heat-pump switch is now $13,000 at Level 1, and electric-to-heat-pump is $5,000 at Level 1 only."))
    if c:
        faqs.append(c["faq"])
    body.append(faq_html(faqs))
    body.append(cta(c))
    src = ["esp"] + (["fb_hp", "fb_iq"] if (not c or fortis(c)) else []) + (["bch_hp"] if (not c or not fortis(c)) else [])
    if c and c["util"] == "pent" or (c and c["name"] == "Nanaimo"):
        src.append("penticton" if c["util"] == "pent" else "nanaimo")
    body.append(sources_line(src))
    rel = [("/blog/cleanbc-rebate-changes-july-2026/", "What changed in CleanBC rebates on July 6, 2026"),
           ("/blog/heat-pump-bc-winter-actually-works/", "Do heat pumps work in a BC winter?")]
    if c:
        rel = [(f"/ca/bc/{slug}/heat-pump/", f"{nm} heat pump rebates and installers"), (f"/ca/bc/{slug}/", f"All {nm} rebates")] + rel + [("/blog/heat-pump-rebate-guide-bc-2026/", "The BC-wide heat pump rebate guide")]
    body.append(related(rel))
    return title, desc, f"Heat pump rebates in {nm}" if c else "BC heat pump rebates", "The complete guide" + (f" &middot; {nm}" if c else ""), faqs, "\n".join(body), "Who pays, how much, and what to do first."


# ---------------------------------------------------------------- family: free heat pump
def free_slug(s):
    return f"free-heat-pump-bc-income-qualified-{s}"


INCOME_TABLE = ('<div class="hpr-table"><table><thead><tr><th>People in home</th><th>Level 1 up to</th><th>Level 2 up to</th><th>Level 3 up to</th></tr></thead><tbody>'
                "<tr><td>1</td><td>$51,100</td><td>$63,900</td><td>$102,100</td></tr>"
                "<tr><td>2</td><td>$63,600</td><td>$79,500</td><td>$127,200</td></tr>"
                "<tr><td>3</td><td>$78,200</td><td>$97,700</td><td>$156,300</td></tr>"
                "<tr><td>4</td><td>$94,900</td><td>$118,600</td><td>$189,800</td></tr>"
                "<tr><td>5</td><td>$107,600</td><td>$134,500</td><td>$215,200</td></tr>"
                "<tr><td>6</td><td>$121,400</td><td>$151,700</td><td>$242,700</td></tr>"
                "<tr><td>7+</td><td>$135,100</td><td>$168,900</td><td>$270,200</td></tr>"
                "</tbody></table></div>")


def build_free(c, slug):
    nm = c["name"] if c else "BC"
    title = f"Free Heat Pump in {nm}? Income-Qualified Rebates 2026" if c else "Free Heat Pump in BC? Income-Qualified Rebates 2026"
    desc = f"Can you get a free heat pump in {nm}? If your income qualifies, ECAP or CleanBC can cover most or all of it. Income limits and 2026 amounts."
    fb = c and fortis(c)
    short = (f"Sometimes. If your household income is low enough, you can get a heat pump installed for little or nothing {'in ' + nm if c else 'in BC'}. "
             "There are two routes: <strong>ECAP</strong>, where the utility installs upgrades for free, and the <strong>CleanBC Energy Savings Program</strong>, which pays 100% of eligible costs up to a limit"
             + (f", or FortisBC's income-qualified rebate of up to <strong>$12,000</strong>" if fb else "")
             + ". The limit is up to <strong>$13,000</strong> if you're switching from gas, oil or propane at Income Level 1"
             + (", plus <strong>$3,000</strong> more here in the north" if c and c["north"] else "") + ".")
    body = [f'<div class="callout hpr-short"><p><strong>Short answer:</strong> {short}</p></div>']
    if c:
        body.append(f"<p>{nm} is {c['where']}. {c['home']}</p>")
    body.append("<h2>Who qualifies? The 2026 income limits</h2>"
                "<p>It's based on how many people live in your home and the combined pre-tax income of the adults. These are the CleanBC limits for invoices from July 6, 2026:</p>" + INCOME_TABLE +
                "<p>You'll need proof of income, like a CRA Notice of Assessment, for every adult in the home.</p>")
    body.append("<h2>How much you can get, by current heat</h2>"
                '<div class="hpr-table"><table><thead><tr><th>Switching from</th><th>Level 1</th><th>Level 2</th><th>Level 3</th></tr></thead><tbody>'
                "<tr><td>Gas, oil or propane: central ducted or 3+ heads</td><td>$13,000</td><td>$7,000</td><td>$3,500</td></tr>"
                "<tr><td>Gas, oil or propane: 2 heads</td><td>$11,000</td><td>$5,500</td><td>$1,000</td></tr>"
                "<tr><td>Gas, oil or propane: 1 head</td><td>$5,500</td><td>$4,500</td><td>$1,000</td></tr>"
                "<tr><td>Electric heat</td><td>$5,000</td><td>Not eligible</td><td>Not eligible</td></tr>"
                "</tbody></table></div>"
                + ("<p><strong>Northern top-up:</strong> because this home is north of 100 Mile House, Levels 1 and 2 add $3,000 (or $1,500 for a single head).</p>" if c and c["north"] else "")
                + "<p>These are maximums. CleanBC pays 100% of eligible costs up to the limit, so a modest system can cost you nothing. The rates changed on July 6, 2026. If you see \"$16,000\" elsewhere, that's the old amount.</p>")
    if fb:
        body.append(f"<h2>The FortisBC route in {nm}</h2><p>Because {nm} is on FortisBC electricity, income-qualified homes with electric heat can also use FortisBC's rebate: up to $12,000 for a central ducted system, $9,000 for mini- or multi-split, or $5,000 partial. The income limits match CleanBC Level 1.</p>")
    body.append("<h2>ECAP: the truly free option</h2>"
                "<p>The Energy Conservation Assistance Program is run by BC Hydro and FortisBC. An energy evaluator visits for free, and if you qualify, they install upgrades for free. Some homes get a heat pump or insulation; others get smaller items. You don't choose the upgrades; the evaluator does.</p>")
    if c:
        body.append(f"<h2>What's different in {nm}</h2>{local_block(c)}<p><strong>My tip for {nm}:</strong> {c['tip']}</p>")
    else:
        body.append("<h2>Your city</h2>" + city_picker(free_slug))
    body.append("<h2>What to do next</h2><ol>"
                "<li>Count the people in your home and add up the adults' income. Compare to the table.</li>"
                "<li>Pre-register with the CleanBC Energy Savings Program <strong>before</strong> any work starts, or apply to ECAP through your utility.</li>"
                "<li>Use a program-registered contractor. Self-installs are not eligible.</li>"
                "<li>If you don't qualify, check the regular rebates in our heat pump guide.</li></ol>")
    faqs = [("Is the heat pump really free?", "It can be. CleanBC pays 100% of eligible costs up to the limit, and ECAP installs upgrades at no charge. If your system costs more than the limit, you pay the difference."),
            ("Can I get the income-qualified rebate if I already have electric heat?", "Only at Income Level 1, up to $5,000. The Level 2 electric stream was discontinued in July 2026."
             + (" In your area, FortisBC's own income-qualified rebate is another option." if fb else " BC Hydro's regular rebate (up to $4,000) is open to any income."))]
    if c:
        faqs.append(c["faq"])
    body.append(faq_html(faqs))
    body.append(cta(c))
    body.append(sources_line(["esp", "ecap", "bch_income"] + (["fb_iq"] if fb or not c else [])))
    rel = [("/blog/heat-pump-rebates-income-tiers-bc-2026/", "BC heat pump income tiers explained"), ("/blog/cleanbc-rebate-changes-july-2026/", "What changed on July 6, 2026")]
    if c:
        rel = [(f"/blog/heat-pump-rebate-guide-{slug}-2026/", f"The full {nm} heat pump rebate guide"), (f"/ca/bc/{slug}/heat-pump/", f"{nm} heat pump installers")] + rel + [("/blog/free-heat-pump-bc-income-qualified/", "The BC-wide version of this guide")]
    body.append(related(rel))
    return title, desc, f"Free heat pump in {nm}?", None, faqs, "\n".join(body), "If your income qualifies, it can be. Here are the 2026 rules."


# ---------------------------------------------------------------- family: energy saving ideas
def es_slug(s):
    return f"energy-saving-ideas-bc-home-{s}"


def build_es(c, slug):
    nm = c["name"] if c else "BC"
    fb = c and fortis(c)
    util = util_name(c) if c else "BC Hydro or FortisBC"
    title = f"Cut Your Power Bill in {nm}: Free and Cheap Ideas" if c else "Cut Your BC Power Bill: Free and Cheap Ideas"
    desc = f"Simple ways to cut your {util} bill in {nm}, from free habits to low-cost fixes, plus the 2026 programs that help pay for bigger upgrades."
    if fb:
        short = f"Start with free habits (thermostat set-backs, cold-water laundry, blinds), then seal drafts for a few dollars. {nm} is on FortisBC, so the thermostat rebate (up to $150) is for central electric systems, and BC Hydro's Peak Saver doesn't apply."
    else:
        short = (f"Start with free habits (thermostat set-backs, cold-water laundry, blinds), then seal drafts for a few dollars. If you have baseboard heat, BC Hydro is giving out up to five <strong>free Mysa or Sinopé thermostats</strong> from October 2026."
                 + (" Kelowna and Penticton are on FortisBC, which has its own programs." if not c else ""))
    body = [f'<div class="callout hpr-short"><p><strong>Short answer:</strong> {short}</p></div>']
    if c:
        body.append(f"<p>{nm} is {c['where']}. That shapes where your energy goes: heating in winter{', and cooling in summer' if c['util'] != 'bch' or slug in ('kamloops','vernon','abbotsford','chilliwack') else ''}. {c['home']}</p>")
    body.append("<h2>Free: do these this week</h2><ul>"
                "<li><strong>Turn the heat down</strong> when you're asleep or out. Lower heat means less energy used.</li>"
                "<li><strong>Use your blinds.</strong> Open south-facing ones on sunny winter days; close them at night.</li>"
                "<li><strong>Wash in cold water</strong> and run full loads. Heating water is most of a washer's energy.</li>"
                "<li><strong>Close doors and turn off baseboards</strong> in rooms you don't use.</li>"
                "<li><strong>Clean or change filters</strong> on your furnace or heat pump so it doesn't work harder than it needs to.</li></ul>")
    body.append("<h2>Cheap: a few dollars each</h2><ul>"
                "<li><strong>Weatherstripping</strong> around doors and windows.</li>"
                "<li><strong>Foam gaskets</strong> behind outlet covers on outside walls.</li>"
                "<li><strong>Pipe insulation</strong> on the first few feet of hot water pipe.</li>"
                "<li><strong>LED bulbs</strong> in the lights you use most.</li></ul>"
                "<p>To find drafts, hold your hand near window and door frames on a windy day.</p>")
    if fb:
        body.append(f"<h2>Thermostats and programs in {nm}</h2><p>FortisBC gives up to <strong>$150</strong> for a connected thermostat, but only if you have an electric central system (furnace, boiler or heat pump). FortisBC also runs a Power Hours program that rewards using less power at peak times. BC Hydro's Peak Saver and free thermostats are for BC Hydro customers only.</p>")
    else:
        body.append("<h2>Free smart thermostats and Peak Saver</h2><p>If your home has <strong>electric baseboards</strong> and you're a BC Hydro customer, you can get up to five free Mysa or Sinopé line-voltage thermostats starting in October 2026. They come pre-enrolled in Peak Saver, which pays a $50 reward each winter ($100 if income-qualified). "
                    "Peak Saver events run November to March, last up to four hours, and you can opt out. Ecobee and Nest do not qualify, because they don't control baseboards.</p>")
    body.append("<h2>Bigger upgrades, when you're ready</h2><ul>" +
                ("<li><strong>Insulation:</strong> FortisBC pays by area and R-value added, up to $900 for an attic and $1,200 for walls or basement.</li><li><strong>Heat pump:</strong> up to $4,000 from FortisBC if you replace electric heat.</li><li><strong>Heat pump water heater:</strong> $1,000 from FortisBC when replacing an electric tank.</li>"
                 if fb else
                 "<li><strong>Insulation:</strong> BC Hydro pays by area and R-value added, up to $900 for an attic and $1,200 for walls or basement (for electrically heated homes).</li><li><strong>Heat pump:</strong> up to $4,000 from BC Hydro if you replace electric heat.</li><li><strong>Heat pump water heater:</strong> up to $1,000 from BC Hydro when replacing an electric tank.</li>") +
                "<li><strong>Income-qualified?</strong> ECAP gives a free home energy evaluation and free upgrades.</li></ul>")
    if c:
        body.append(f"<h2>What's different in {nm}</h2>{local_block(c)}<p><strong>My tip for {nm}:</strong> {c['tip']}</p>")
    else:
        body.append("<h2>Your city</h2>" + city_picker(es_slug))
    faqs = [("What is the cheapest way to cut my heating bill?", "Turning the heat down at night and when you're out costs nothing. Sealing drafts costs a few dollars. After that, insulation usually gives the most back."),
            ("Do Ecobee or Nest thermostats get a BC Hydro rebate?", "No. BC Hydro's free thermostats and Peak Saver thermostat rewards are for line-voltage baseboard thermostats like Mysa and Sinopé.")]
    if c:
        faqs.append(c["faq"])
    body.append(faq_html(faqs))
    body.append(cta(c))
    body.append(sources_line((["fb_thermo", "fb_ins", "fb_hp"] if fb else ["thermo", "bch_ins", "bch_hp", "bch_hpwh"]) + ["ecap"]))
    rel = [("/blog/bc-hydro-peak-saver-explained/", "BC Hydro Peak Saver, explained"), ("/blog/insulation-buying-guide-bc/", "Insulation buying guide for BC")]
    if c:
        rel = [(f"/ca/bc/{slug}/", f"All {nm} rebates"), (f"/blog/heat-pump-rebate-guide-{slug}-2026/", f"{nm} heat pump rebate guide")] + rel + [("/blog/energy-saving-ideas-bc-home/", "The BC-wide version of this guide")]
    body.append(related(rel))
    return title, desc, f"Cut your {nm} power bill", None, faqs, "\n".join(body), "Free habits first, cheap fixes next, then the rebates that help pay for the big stuff."


# ---------------------------------------------------------------- family: windows
def win_slug(s):
    return f"window-doors-replacement-rebates-bc-guide-{s}"


def build_win(c, slug):
    nm = c["name"] if c else "BC"
    fb = c and fortis(c)
    van = c and slug == "vancouver"
    who = "FortisBC" if fb else ("BC Hydro" if c else "BC Hydro or FortisBC")
    title = f"Window and Door Rebates in {nm}, BC (2026)" if c else "BC Window and Door Rebates 2026: $100 Each"
    desc = (f"{nm} window and door rebates for 2026: " + ("not available inside City of Vancouver limits. What to do instead." if van else f"{who} pays $100 per window or door, up to $2,000. Rules and next steps."))
    if van:
        short = "Not in the City of Vancouver. BC Hydro and FortisBC both exclude City of Vancouver homes from their window and door rebate. The income-qualified CleanBC program doesn't cover windows either. Put your rebate dollars into insulation and a heat pump first."
    else:
        short = (f"{who} pays <strong>$100 per window or door, up to $2,000</strong>. The new unit must have a U-factor of 1.22 or lower (metric), be certified, and be installed by a licensed contractor. Apply within six months of your invoice."
                 + (" (City of Vancouver homes are excluded.)" if not c else ""))
    body = [f'<div class="callout hpr-short"><p><strong>Short answer:</strong> {short}</p></div>']
    if c:
        body.append(f"<p>{nm} is {c['where']}. {c['home']}</p>")
    body.append("<h2>The window and door rebate rules</h2><ul>"
                "<li><strong>Amount:</strong> $100 for each window or door, up to $2,000 per home.</li>"
                "<li><strong>Efficiency:</strong> U-factor of 1.22 W/m²·K or less. Your quote should list it.</li>"
                "<li><strong>Certified</strong> by CSA, Intertek, Labtest, QAI or NFRC.</li>"
                "<li><strong>Replacing</strong> existing windows or doors between heated and unheated space. Skylights don't count.</li>"
                "<li><strong>Installed by a licensed contractor</strong>. Self-installs don't qualify.</li>"
                "<li><strong>Apply within six months</strong> of the invoice.</li></ul>"
                + ("" if fb else "<p>BC Hydro's window rebate is part of its home renovation rebates for electrically heated homes. If you heat with gas, check FortisBC's version, which is open to FortisBC gas customers too.</p>"))
    body.append("<h2>Bonuses for doing more than one upgrade</h2><p>" +
                ("FortisBC adds a $300 bonus when you do windows (worth at least $250 in rebates) plus another eligible upgrade, or a bonus of $750 to $2,000 based on how much your EnerGuide rating improves." if fb else
                 "BC Hydro offers a bonus of up to $2,000 when you complete more than one upgrade, like windows plus insulation. FortisBC has a $300 two-upgrade bonus.") + "</p>")
    body.append("<h2>Is replacing windows worth it?</h2><p>Honestly, windows are one of the most expensive upgrades for the energy they save. If your windows are in decent shape, insulation and air sealing usually save more per dollar. Replace windows when they're failing, fogged or drafty, and use the rebate to take the edge off.</p>"
                "<p>The income-qualified CleanBC Energy Savings Program (July 2026 rules) does not include windows. ECAP may cover some draftproofing for income-qualified homes.</p>")
    if c:
        body.append(f"<h2>What's different in {nm}</h2>{local_block(c)}")
    else:
        body.append("<h2>Your city</h2>" + city_picker(win_slug))
    body.append("<h2>What to do next</h2><ol><li>Check which utility heats your home.</li><li>Get quotes that list the U-factor and certification of each unit.</li><li>Ask about insulation at the same time to earn the bonus.</li><li>Keep your invoice and photos of the labels, and apply within six months.</li></ol>")
    faqs = [("How much is the BC window rebate?", "$100 per window or door, up to $2,000, from BC Hydro or FortisBC. The City of Vancouver is excluded."),
            ("Do ENERGY STAR windows automatically qualify?", "Not automatically. The rule is a U-factor of 1.22 W/m²·K or less and certification by a listed body. Check the number on the label or quote.")]
    if c:
        faqs.append(c["faq"])
    body.append(faq_html(faqs))
    body.append(cta(c))
    body.append(sources_line(["fb_win", "fb_bonus"] if fb else ["bch_win", "fb_win", "esp"]))
    rel = [("/blog/windows-buying-guide-bc/", "Windows buying guide for BC"), ("/blog/insulation-buying-guide-bc/", "Insulation buying guide for BC")]
    if c:
        rel = [(f"/ca/bc/{slug}/windows/", f"{nm} window rebates and installers"), (f"/ca/bc/{slug}/", f"All {nm} rebates")] + rel + [("/blog/window-doors-replacement-rebates-bc-guide/", "The BC-wide version of this guide")]
    body.append(related(rel))
    return title, desc, f"Window and door rebates in {nm}", None, faqs, "\n".join(body), "What the rebate pays, what qualifies, and whether it's worth it."


FAMILIES = [
    (hp_slug, "heat-pump-rebate-guide-bc-2026", build_hp),
    (free_slug, "free-heat-pump-bc-income-qualified", build_free),
    (es_slug, "energy-saving-ideas-bc-home", build_es),
    (win_slug, "window-doors-replacement-rebates-bc-guide", build_win),
]

CSS = """<style id="bcblog-css">
.hpr-table{overflow-x:auto;margin:20px 0}.hpr-table table{width:100%;border-collapse:collapse;font-size:15px;background:#fff}
.hpr-table th,.hpr-table td{border:1px solid var(--rule,#d9d0c1);padding:10px 12px;text-align:left;vertical-align:top}
.hpr-table th{background:var(--paper-warm,#f5efe5)}
.hpr-cta{background:var(--teal-deep,#08363f);color:#fff;border-radius:16px;padding:28px 24px;margin:36px 0;text-align:center}
.hpr-cta h3{color:#fff;margin-bottom:8px}.hpr-cta p{color:rgba(255,255,255,.88)!important}
.hpr-btn{display:inline-block;background:var(--amber,#d4751c);color:#fff!important;padding:12px 22px;border-radius:999px;text-decoration:none!important;font-weight:600}
.hpr-sources{font-size:14px!important}.hpr-cities{font-size:15px!important;line-height:1.9}
</style>"""


def jld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, indent=2, ensure_ascii=False) + "\n</script>"


def rewrite(path, slug_dir, title, desc, crumb, eyebrow, faqs, body, sub):
    t = path.read_text()
    url = f"https://homepowerrebate.com/blog/{slug_dir}/"
    esc = html.escape
    t = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", t, count=1, flags=re.S)
    t = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(desc)}">', t, count=1)
    t = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc(title)}">', t, count=1)
    t = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{esc(desc)}">', t, count=1)
    # replace Article/BlogPosting (+ any old FAQPage) JSON-LD with ours
    blocks = list(re.finditer(r'<script type="application/ld\+json">(.*?)</script>\s*', t, re.S))
    pub = "2026-09-01"
    first = None
    for m in reversed(blocks):
        try:
            d = json.loads(m.group(1))
        except Exception:
            continue
        typ = d.get("@type")
        if typ in ("Article", "BlogPosting", "FAQPage"):
            pub = d.get("datePublished", pub) if typ != "FAQPage" else pub
            first = m.start()
            t = t[:m.start()] + t[m.end():]
        elif typ == "BreadcrumbList":
            for it in d.get("itemListElement", []):
                if it.get("position") == 3:
                    it["name"] = crumb
            t = t[:m.start()] + jld(d) + "\n" + t[m.end():]
    art = {"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc,
           "datePublished": pub, "dateModified": TODAY,
           "author": {"@type": "Person", "name": "Sam Menard", "url": "https://homepowerrebate.com/about"},
           "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": "https://homepowerrebate.com"},
           "mainEntityOfPage": url}
    faq = {"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": strip_tags(q), "acceptedAnswer": {"@type": "Answer", "text": strip_tags(ans)}} for q, ans in faqs]}
    new_ld = jld(art) + "\n" + jld(faq) + "\n"
    first = t.find('<script type="application/ld+json">')
    if first < 0:
        first = t.find("</head>")
    t = t[:first] + new_ld + t[first:]
    if 'id="bcblog-css"' not in t:
        t = t.replace("</head>", CSS + "\n</head>", 1)
    # breadcrumb label
    t = re.sub(r'(<nav class="hpr-breadcrumb".*?<li aria-current="page">).*?(</li>)', lambda m: m.group(1) + esc(crumb) + m.group(2), t, count=1, flags=re.S)
    # body region
    s = t.index("<!-- CANONICAL-BREADCRUMB-END -->") + len("<!-- CANONICAL-BREADCRUMB-END -->")
    e = t.index("</article>") + len("</article>")
    meta = f'<p class="post-meta meta">By <a href="/about" style="color:inherit;text-decoration:underline;">Sam Menard</a> &middot; Updated {TODAY_H}</p>'
    if 'class="post-header"' in t[s:e]:
        head = (f'\n\n<header class="post-header">\n  <div class="wrap">\n    <div class="post-eyebrow">{eyebrow or "Guide"}</div>\n'
                f'    <h1>{esc(title)}</h1>\n    {meta}\n  </div>\n</header>\n\n<article>\n  <div class="wrap">\n')
    else:
        head = (f'\n\n<section class="hero">\n  <div class="wrap">\n    <h1>{esc(title)}</h1>\n    <p>{sub}</p>\n  </div>\n</section>\n\n'
                f'<article class="article">\n  <div class="wrap">\n    {meta}\n')
    t = t[:s] + head + body + "\n  </div>\n</article>" + t[e:]
    return t


def main():
    check = "--check" in sys.argv
    changed = 0
    for slugf, hub, builder in FAMILIES:
        targets = [(slugf(s), CITIES[s], s) for s in ORDER] + [(hub, None, None)]
        for d, c, s in targets:
            p = ROOT / "blog" / d / "index.html"
            title, desc, crumb, eyebrow, faqs, body, sub = builder(c, s)
            new = rewrite(p, d, title, desc, crumb, eyebrow, faqs, body, sub)
            if new != p.read_text():
                changed += 1
                if not check:
                    p.write_text(new)
    print(f"{'would change' if check else 'changed'} {changed} pages")


if __name__ == "__main__":
    main()
