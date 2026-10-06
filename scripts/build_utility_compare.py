#!/usr/bin/env python3
"""/programs/utility-comparison/: the utilities on this site side by side. Reads data/utilities/*.json so every amount and status matches the utility page (status comes from the
fact each card names). The 3-ton table does the arithmetic only for programs that state a per-ton rate on their card; flat and whole-home amounts are listed separately.
Writes data/state-topics/utility-comparison.json and builds it with build_state_topic_pages.py. Usage: python3 scripts/build_utility_compare.py"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_ca_pages as ca  # noqa: E402
import build_state_topic_pages as st  # noqa: E402

e = html.escape
U = {p.stem: json.loads(p.read_text()) for p in (ROOT / "data/utilities").glob("*.json")}
PILL = {"active": "Open", "check": "Check first", "closed": "Closed", "waitlist": "On hold", "upcoming": "Coming", "paused": "Paused", "info": "Info"}


def card(slug, title):
    for c in U[slug]["cards"]:
        if c["title"] == title:
            s = c.get("status") or ca.FACTS[c["facts"][0]]["status"]
            return c["amount"], PILL[s]
    raise KeyError((slug, title))


# (utility page, region, heat pump card, water heater card, EV charger card, free-help card)
ROWS = [
 ("smud-rebates", "California", "Heat pump heating and cooling", "Heat pump water heater", "EV charger at home", None),
 ("ladwp-rebates", "California", "Heat pump heating and cooling", "Heat pump water heater", "EV charger", "Solar and storage equity funds"),
 ("burbank-water-and-power-rebates", "California", "Heat pump heating and cooling", "Other electrification", "EV charger", None),
 ("glendale-water-and-power-rebates", "California", "Heat pump, replacing a gas furnace", "Heat pump water heater", None, None),
 ("pasadena-water-and-power-rebates", "California", "Heat pump", "Heat pump water heater", "EV charger", None),
 ("riverside-public-utilities-rebates", "California", "Heat pump and air conditioning", "ENERGY STAR products", "EV rebates", None),
 ("moreno-valley-utility-rebates", "California", "Central AC and heat pump replacement", None, "5-5-5 EV incentive", "Income-based rate discount"),
 ("san-jose-clean-energy-rebates", "California", "Heat pump HVAC", "Heat pump water heater", None, None),
 ("cleanpowersf-rebates", "California", "Heat pump heating credit", "Heat pump water heater credit", None, None),
 ("pge-rebates", "California", None, None, "Residential EV charging rebate", "Energy Savings Assistance"),
 ("sce-rebates", "California", None, None, "Charge Ready Home panel upgrade", "Energy Savings Assistance"),
 ("sdge-rebates", "California", None, None, None, "Energy Savings Assistance (ESA)"),
 ("san-diego-community-power-rebates", "California", None, None, "EV Flex Connect", "Equitable Building Decarbonization"),
 ("ava-community-energy-rebates", "California", None, None, None, "Ava rate options and bill help"),
 ("con-edison-rebates", "New York", "Air-source heat pump, single-family", "Heat pump water heater", "SmartCharge New York", None),
 ("national-grid-rebates", "New York", "Air-source heat pump, full load", "Heat pump water heater", None, "Whole Home Electrification Program"),
 ("nyseg-and-rge-rebates", "New York", "NYSEG air-source heat pump", "Heat pump water heater", None, None),
 ("central-hudson-rebates", "New York", "Air-source heat pump", "Heat pump water heater", None, None),
 ("orange-and-rockland-rebates", "New York", "Air-source heat pump", "Heat pump water heater", None, None),
 ("pseg-long-island-rebates", "New York", "Whole-house heat pump", "Heat pump water heater", None, None),
 ("efficiency-vermont-rebates", "Vermont", "Ductless heat pump", "Heat pump water heater", None, "Income bonus on heat pumps"),
 ("green-mountain-power-rebates", "Vermont", "Income-eligible heat pump rebate", "Heat pump water heater", None, None),
 ("fortisbc-rebates", "British Columbia", "Heat pump (electric customers)", "Heat pump water heater", "Connected thermostat and EV charger", "Free evaluation and upgrades"),
 ("save-on-energy-rebates", "Ontario", "Heat pump", None, "EV charger", "Energy Affordability Program"),
 ("enbridge-gas-rebates", "Ontario", "Heat pump (gas homes)", None, None, "Home Winterproofing"),
]
# 3-ton example: only programs whose card states a per-ton rate (rate, cap or None, note)
TON = [
 ("burbank-water-and-power-rebates", "Heat pump heating and cooling", 1000, 2500, "Must replace a gas appliance."),
 ("glendale-water-and-power-rebates", "Heat pump, replacing a gas furnace", 1000, 5000, "Replacing a gas furnace."),
 ("save-on-energy-rebates", "Heat pump", 1250, 7500, "Electric, oil, propane or wood home."),
 ("riverside-public-utilities-rebates", "Heat pump and air conditioning", 750, None, "No cap stated on our card."),
 ("pasadena-water-and-power-rebates", "Heat pump", 170, None, "Base rate."),
 ("enbridge-gas-rebates", "Heat pump (gas homes)", 500, 2000, "Gas-heated home or rental."),
 ("moreno-valley-utility-rebates", "Central AC and heat pump replacement", 150, None, "Midpoint of $140 and $160 for an in-city purchase, SEER 16 or more."),
]


def cell(slug, title):
    if not title:
        return '<td class="cmp-none">No amount in our facts</td>'
    amt, pill = card(slug, title)
    return f'<td>{e(amt)}<br><span class="cmp-pill">{pill}</span></td>'


def table():
    head = "<tr><th>Utility</th><th>Heat pump</th><th>Water heater</th><th>EV charger</th><th>Free or income help</th></tr>"
    out, region = [], None
    for slug, reg, hp, wh, ev, fr in ROWS:
        if reg != region:
            out.append(f'<tr class="cmp-reg"><td colspan="5">{e(reg)}</td></tr>')
            region = reg
        out.append(f'<tr><td><a href="/programs/{slug}/">{e(U[slug]["short"])}</a></td>{cell(slug,hp)}{cell(slug,wh)}{cell(slug,ev)}{cell(slug,fr)}</tr>')
    return '<div class="tw"><table class="cmp">' + head + "".join(out) + "</table></div>"


def ton_table():
    rows = []
    for slug, title, rate, cap, note in TON:
        raw = rate * 3
        val = min(raw, cap) if cap else raw
        rows.append((val, slug, rate, cap, note))
    rows.sort(reverse=True)
    body = "".join(f'<tr><td><a href="/programs/{s}/">{e(U[s]["short"])}</a></td><td>${r:,} per ton</td><td>{("$"+format(c,",")) if c else "none stated"}</td><td><b>${v:,}</b></td><td>{e(n)}</td></tr>' for v, s, r, c, n in rows)
    return '<div class="tw"><table class="cmp"><tr><th>Utility</th><th>Rate</th><th>Cap</th><th>3-ton system</th><th>Condition</th></tr>' + body + "</table></div>"


css = '<style>.cmp{border-collapse:collapse;width:100%;font-size:14px}.cmp th,.cmp td{border:1px solid #e5dccb;padding:8px 10px;text-align:left;vertical-align:top}.cmp th{background:#f5efe5}.cmp-reg td{background:#08363f;color:#fff;font-weight:700}.cmp-none{color:#777}.cmp-pill{font-size:12px;color:#555}.tw{overflow-x:auto}</style>'
d = {
 "path": "/programs/utility-comparison/", "nav": "ca", "region": "ca", "hub_name": "Utility programs", "hub": "/programs/", "short": "Utility comparison",
 "title": "Utility Rebates Compared 2026: Heat Pumps, Water Heaters, EV Chargers",
 "desc": "Compare 25 utilities side by side for 2026: heat pump amounts on a 3-ton system, water heater and EV charger rebates, and free help, each with its status and a link to the full page.",
 "h1": "Utility Rebates Compared, 2026", "badge": "25 utilities, same questions",
 "lead": "Different utilities pay for different things, and the headline numbers are not comparable until you put them on the same footing. This page lines up the utilities we have read, shows what a 3-ton heat pump earns where the rate is per ton, and says plainly where we found no amount.",
 "cards_heading": "How to read this comparison",
 "cards_intro": "<p>Every figure comes from the utility's own page, and each cell shows the status of the program it names. A cell that says no amount in our facts means we did not find a published amount, not that the utility pays nothing. Open the utility's page for the details and the date we read it.</p>",
 "cards": [],
 "after_cards": css,
 "sections": [
  ["What a 3-ton heat pump earns, where the rate is per ton", "<p>Per-ton rates are the one place a fair comparison is possible, so we did the arithmetic for a typical 3-ton system and applied each program's cap. The table is sorted by the result. It leaves out utilities that pay a flat amount or a whole-home tier, which are in the next table.</p>" + ton_table() + "<p>The conditions matter as much as the amount: several of these programs only pay when the heat pump replaces a gas appliance, and the Ontario figure depends on how you heat. A bigger number is not better if your home does not qualify.</p>"],
  ["Every utility, by what it pays", "<p>The table groups utilities by region. Flat amounts, tiers and ranges appear as the utility states them, with the status pill for the program behind each number.</p>" + table()],
  ["Why the headline numbers mislead", "<p>New York's utilities advertise whole-home maximums such as $14,000 that only apply to a weatherized home in a Disadvantaged Community that removes its old system. California's municipal utilities pay per ton or per upgrade, so a small system earns little. Ontario's amount depends on how you heat. Compare the condition column, not just the dollar figure.</p>"],
  ["Where a utility pays nothing we could find", "<p>Several large utilities, including PG&E, SCE, SDG&E and Ava, have no cash heat pump rebate in our facts. That is a finding about published, primary-source offers on the dates we read them, and utilities do change programs. Their pages explain what exists instead, such as free income-qualified upgrades and EV charger help.</p>"],
  ["Free help is worth checking first", "<p>Income-qualified programs, such as SDG&E's Energy Savings Assistance, Enbridge's Home Winterproofing, Ontario's Energy Affordability Program and Moreno Valley's rate discount, give free upgrades or lower bills. They are often worth more than a rebate, and they should be checked before you spend your own money.</p>"]],
 "claim_heading": "How to use this comparison",
 "claim_steps": ["Find your utility by the name on your bill.", "Open its page and read the status and date on each program.", "Check the free help column first if your income may qualify.", "Use the 3-ton table only to compare per-ton programs.", "Confirm every amount with the program before you sign a contract."],
 "links": [["Compare all PowerScore cities", "/powerscore/", "city rankings"], ["All utility and program pages", "/programs/", "every page in the series"]],
 "faq": [["Which utility pays the most for a heat pump?", "On a 3-ton system with per-ton rates, Save on Energy's electric, oil, propane and wood rate is the largest in our table, then Glendale and Burbank. New York utilities advertise larger whole-home maximums under conditions."], ["Why do some utilities show no amount?", "We found no published amount in the program pages we read. It does not prove nothing exists, so check the utility's own page."], ["Are these amounts current?", "Each utility page shows the date we read it, and statuses come from the verified facts behind each card."], ["Is a bigger rebate always better?", "No. Check the conditions, such as replacing a gas appliance, weatherization or income limits."], ["Does the comparison include federal credits?", "No. The federal 25C and 25D credits ended for installs after December 31, 2025."]],
 "refs": [["Save on Energy: For Your Home", "https://saveonenergy.ca/en/For-Your-Home"], ["NYS Clean Heat program", "https://cleanheat.ny.gov/"], ["SMUD rebates", "https://www.smud.org/Rebates-and-Savings-Tips/Rebates-for-My-Home"], ["LADWP residential programs", "https://www.ladwp.com/residential-services/programs-and-rebates-residential"]],
 "facts": ["us-ca-0-federal-25c-25d-tax-credits"],
}
(ROOT / "data/state-topics/utility-comparison.json").write_text(json.dumps(d, indent=1, ensure_ascii=False))
print(st.build("utility-comparison"))
