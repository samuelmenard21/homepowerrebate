#!/usr/bin/env python3
"""
Correct stale/wrong rebate claims on the 18 BC city hubs (ca/bc/<city>/index.html)
to the verified facts in data/verified-facts/bc-pages.json and bc-blog.json
(checked 2026-09-26/27): BC Hydro heat pump $4,000 (electric-heat replacements
only) + $1,000 bonus to Oct 31 2026; CleanBC income-qualified $13,000/$7,000/
$3,500 for gas/oil/propane; FortisBC areas (Kelowna, Penticton) differ.

Idempotent: each rule only matches the old wording.
Run from the Powerrebate root:  python3 scripts/fix_bc_hub_rebate_claims.py [--dry-run]
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CITIES = ["abbotsford", "burnaby", "chilliwack", "coquitlam", "fort-st-john", "kamloops", "kelowna",
          "langley", "maple-ridge", "nanaimo", "penticton", "prince-george", "richmond", "squamish",
          "surrey", "vancouver", "vernon", "victoria", "fraser-valley"]
FORTIS = {"kelowna", "penticton"}
NORTH = {"prince-george", "fort-st-john"}


def rules(slug, name):
    fortis = slug in FORTIS
    util = "FortisBC" if fortis else "BC Hydro"
    hp_util = ("FortisBC pays up to $4,000 ($1,500 partial) for a heat pump, or up to $12,000 for a central system if your income qualifies. "
               "BC Hydro rebates don't apply here.") if fortis else \
              ("BC Hydro pays up to $4,000 ($1,500 partial) when a heat pump replaces electric heat, plus up to $1,000 more for installs finished Aug 1 to Oct 31, 2026.")
    north = " (up to $16,000 with the northern top-up)" if slug in NORTH else ""
    cleanbc = f"CleanBC's income-qualified program pays up to $13,000 / $7,000 / $3,500 (income levels 1 / 2 / 3) to switch from gas, oil or propane{north}."
    snippet = (
        f'<p class="snippet-answer"><strong>In 2026, {name} homeowners can get up to $4,000 from {util} for a whole-home heat pump'
        + ("" if fortis else " when it replaces electric heat (plus up to $1,000 more for installs finished by October 31, 2026)")
        + f". Income-qualified households switching from gas, oil or propane can get up to $13,000 through CleanBC{north}. "
        + ("Solar, battery, insulation and window rebates here come from FortisBC or the City, not BC Hydro." if fortis else
           "BC Hydro also pays up to $5,000 for solar panels, up to $5,500 for insulation, up to $1,000 for a heat-pump water heater and up to $550 for an EV charger.")
        + "</strong></p>")
    return [
        # hero stat
        (r'(color:#fff;">)\$13,000(</div><div style="font-size:12px; color:rgba\(250,247,242,\.7\); margin-top:4px;">)Heat Pump rebate(</div>)',
         lambda m: f"{m.group(1)}$4,000{m.group(2)}Heat pump rebate ({util}){m.group(3)}"),
        # answer snippet with invented stacked total
        (r'<p class="snippet-answer"><strong>In 2026, an? [^<]*?homeowner can claim up to \$13,000 for a heat pump[^,]*,.*?Stacked together, the rebates can total roughly \$[\d,]+\.</strong></p>',
         lambda m: snippet),
        # CleanBC program card
        (r'<h4>CleanBC heat pump rebate</h4>\s*<span class="program-amount">\$4,000&ndash;\$13,000</span>\s*</div>\s*<p>The centrepiece\..*?</p>\s*<div class="how"><strong>How it works:</strong>.*?</div>',
         lambda m: ('<h4>Heat pump rebates</h4>\n        <span class="program-amount">$1,500&ndash;$13,000</span>\n      </div>\n'
                    f'      <p>{hp_util} {cleanbc}</p>\n'
                    '      <div class="how"><strong>How it works:</strong> A registered contractor (HPCN member) installs it and usually handles the paperwork. '
                    'For CleanBC\'s income-qualified program you register <em>before</em> work starts; BC Hydro needs no pre-approval. Apply within six months of the invoice. '
                    '<a href="https://www.bchydro.com/powersmart/residential/rebates-programs/home-renovation/renovating-heating-system.html" target="_blank" rel="noopener">BC Hydro rules</a> &middot; '
                    '<a href="https://betterhomesbc.ca/" target="_blank" rel="noopener">CleanBC</a></div>')),
        # income tier intro
        (r'These are the general CleanBC tiers; your exact amount is confirmed by the EnerGuide evaluation\.',
         lambda m: "CleanBC's income limits depend on household size. For a family of four (pre-tax, July 6, 2026 rules): Level 1 up to $94,900, Level 2 up to $118,600, Level 3 up to $189,800."),
        # tier cards
        (r'<h4>Lower income</h4>\s*<p><strong>Highest support</strong></p>\s*<div class="amount">up to \$13,000</div>\s*<p>Plus possible free-install \(ECAP\) and federal Affordability top-ups\.</p>',
         lambda m: f'<h4>Income Level 1</h4>\n        <p><strong>Highest support</strong></p>\n        <div class="amount">up to $13,000</div>\n        <p>Switching from gas, oil or propane{north}. Up to $5,000 if you\'re replacing electric heat. Free installs (ECAP) may also apply.</p>'),
        (r'<h4>Middle income</h4>\s*<p><strong>Enhanced support</strong></p>\s*<div class="amount">up to \$12,000</div>\s*<p>Sliding scale between the standard and lower-income amounts\.</p>',
         lambda m: '<h4>Income Level 2 / 3</h4>\n        <p><strong>Enhanced support</strong></p>\n        <div class="amount">up to $7,000</div>\n        <p>Level 2 gets up to $7,000 and Level 3 up to $3,500, for gas, oil or propane switches only.</p>'),
        (r'<h4>Standard</h4>\s*<p><strong>No income test</strong></p>\s*<div class="amount">\$4,000</div>\s*<p>Every eligible BC household gets at least this for a qualifying heat pump\.</p>',
         lambda m: ('<h4>No income test</h4>\n        <p><strong>' + util + '</strong></p>\n        <div class="amount">up to $4,000</div>\n        <p>'
                    + ("From FortisBC for a qualifying heat pump ($1,500 partial)." if fortis else
                       "From BC Hydro, only when the heat pump replaces electric heat. Gas homes above CleanBC's income limits don't get a provincial heat pump rebate right now.")
                    + '</p>')),
        # furnace box
        (r"If your gas furnace is aging, the rebate math favors a heat pump\. You'll claim <strong>\$4,000–\$13,000</strong> \(depending on income\), plus (.*?)\. Total rebate \+ financing can cover 50–70% of a new heat pump system—and you gain cooling, better resilience, and lower bills\.",
         lambda m: ("If your gas furnace is aging, check CleanBC's income-qualified program first: up to <strong>$13,000</strong> (Level 1), $7,000 (Level 2) or $3,500 (Level 3) to switch to a heat pump"
                    f"{north}. BC Hydro's $4,000 rebate is only for replacing electric heat. Above the income limits there's no provincial rebate for a gas-to-heat-pump switch right now, "
                    "so compare quotes and " + ("local financing" if m.group(1) == "local financing when available" else m.group(1)) + ". You also gain air conditioning.")),
        # finder: heat pump card
        (r'<h4>BC Hydro whole-home heat pump</h4>\s*<div class="finder-amount">\$4,000&ndash;\$13,000</div>\s*<p>Depends on income and project scope; income-qualified households can reach up to \$16,000 through CleanBC\.</p>',
         lambda m: (f'<h4>{util} whole-home heat pump</h4>\n        <div class="finder-amount">Up to $4,000</div>\n        <p>'
                    + ("FortisBC rebate; up to $12,000 for a central system if income-qualified." if fortis else
                       "Replacing electric heat ($1,500 partial), plus up to $1,000 for installs finished by Oct 31, 2026. Income-qualified gas/oil/propane switches: up to $13,000 via CleanBC.")
                    + '</p>')),
        # heat pump water heater (program card + finder)
        (r'(<h4>Heat pump water heater rebate</h4>\s*<span class="program-amount">)\$1,000&ndash;\$3,000(</span>\s*</div>\s*<p>A heat pump water heater uses ~&#8531; the energy of a standard electric tank\.) Replaces gas, electric, or oil tanks\.(</p>\s*<div class="how"><strong>How it works:</strong>) Rebate amount depends on your utility and income level\.',
         lambda m: (f"{m.group(1)}up to $3,500{m.group(2)}{m.group(3)} "
                    + ("Check FortisBC's current offer." if fortis else "BC Hydro pays up to $1,000 when it replaces an electric tank.")
                    + " Income-qualified CleanBC households switching from gas, oil or propane can get up to $3,500.")),
        (r'(<h4>Heat-pump water heater rebate</h4>\s*<div class="finder-amount">)\$1,000&ndash;\$3,000(</div>\s*<p>)Varies by unit size and whether you\'re on BC Hydro or FortisBC\.',
         lambda m: f"{m.group(1)}Up to $1,000{m.group(2)}" + ("Check FortisBC's offer; up to $3,500 if income-qualified (CleanBC)." if fortis else "BC Hydro, replacing an electric tank. Up to $3,500 if income-qualified and switching from gas/oil (CleanBC).")),
        # appliance quick win (offer ended Jan 2, 2026)
        (r'Product Rebates: \$150–\$500 Off Appliances</h4>\s*<p([^>]*)>Replacing a fridge, washer, or dryer\? BC Hydro\'s instant rebate refunds up to \$150 per appliance on Energy Star models \(dishwashers and cooktops aren\'t currently included\)\. Window runs through Jan 2, 2026\.',
         lambda m: (f"Appliance rebates: check what's running now</h4>\n      <p{m.group(1)}>BC Hydro runs instant in-store discounts on efficient appliances at certain times of year. "
                    "The last offer ended January 2, 2026, so check BC Hydro's deals page before you shop.")),
        # smart thermostat / in-store
        (r'(<h4>Smart thermostats &amp; in-store rebates</h4>\s*<span class="program-amount">)free&ndash;\$200(</span>)',
         lambda m: f"{m.group(1)}Free{m.group(2)}"),
        (r' At 300\+ BC stores, instant in-store rebates knock \$10&ndash;\$200 off efficient products\.', lambda m: ""),
        # "What you can claim" heat pump card
        (r'(<h4>&#128293; Heat Pump</h4>\s*<div class="amount">)\$4,000&ndash;\$13,000(</div>\s*<p>)Replaces a gas furnace or electric baseboards\. Income-qualified reaches up to \$13,000 &mdash; an electrical panel upgrade can push this higher \(ask your installer for the current combined ceiling\)',
         lambda m: (f"{m.group(1)}Up to $4,000{m.group(2)}"
                    + ("Up to $4,000 from FortisBC ($12,000 for a central system if income-qualified)" if fortis else
                       "Up to $4,000 from BC Hydro when it replaces electric heat (+ up to $1,000 bonus to Oct 31, 2026)")
                    + f". Switching from gas, oil or propane? Income-qualified households get up to $13,000 through CleanBC{north}")),
        # heat pump card, any wording
        (r'(<h4>&#128293; Heat Pump</h4>\s*<div class="amount">)\$4,000&ndash;\$13,000(</div>\s*<p>).*?(</p>)',
         lambda m: (f"{m.group(1)}Up to $4,000{m.group(2)}"
                    + ("Up to $4,000 from FortisBC ($12,000 for a central system if income-qualified)" if fortis else
                       "Up to $4,000 from BC Hydro when it replaces electric heat (+ up to $1,000 bonus to Oct 31, 2026)")
                    + f". Switching from gas, oil or propane? Income-qualified households get up to $13,000 through CleanBC{north}.{m.group(3)}")),
        # FAQ with unverified municipal top-up
        (r'CleanBC pays \$4,000&ndash;\$13,000, and the City adds up to \$2,000 more\.',
         lambda m: ("BC Hydro pays up to $4,000 when a heat pump replaces electric heat, and income-qualified households switching from gas can get up to $13,000 through CleanBC. "
                    "Ask the City whether it currently offers a heat pump top-up; we couldn't confirm one for 2026.")),
        # ended municipal top-up note box
        (r'<span class="tag tag-local">Local bonus: real cash</span>\s*<h4>[^<]*adds up to \$2,000 on your heat pump\.</h4>\s*<p>.*?href="([^"]+)".*?</p>',
         lambda m: ('<span class="tag tag-local">Heads-up</span>\n      <h4>' + name + "'s heat pump top-up has ended.</h4>\n      <p>" + name
                    + ' used to add up to $2,000 on a heat pump through the CleanBC municipal top-up program, which <strong>ended on August 31, 2025</strong>. '
                    + f'Check the City\'s <a href="{m.group(1)}" target="_blank" rel="noopener">home energy page</a> for any new local offers.</p>')),
        (r"It's also one of the few BC cities that adds its own money on top of the provincial rebates &mdash; so you stack CleanBC, both utilities, the City's top-up, and federal money for lower-income households\.",
         lambda m: "You can stack BC Hydro, FortisBC and CleanBC programs, and lower-income households get the most help."),
        (r' &mdash; and [A-Z][A-Za-z .]+ adds up to \$2,000 more \(below\)', lambda m: ""),
        (r'\s*<p[^>]*>[A-Z][A-Za-z .]+ adds its own up-to-\$2,000 heat pump top-up on top of these provincial and utility rebates &mdash; see the heat pump breakdown above for the full stack\.</p>', lambda m: ""),
        (r'CleanBC pays \$4,000–\$13,000, and the City adds up to \$2,000 more\.',
         lambda m: ("BC Hydro pays up to $4,000 when a heat pump replaces electric heat, and income-qualified households switching from gas can get up to $13,000 through CleanBC. "
                    "The City's old $2,000 top-up ended on August 31, 2025.")),
        # invented "honest math" totals
        (r'<p>A typical household keeps <strong>\$5,000&ndash;\$13,000</strong>.*?</p>',
         lambda m: ("<p>" + ("On FortisBC, a whole-home heat pump gets up to <strong>$4,000</strong> (up to $12,000 for a central system if income-qualified). "
                             if fortis else
                             "If you heat with electricity, expect up to <strong>$4,000</strong> for a whole-home heat pump (plus up to $1,000 if it's finished by October 31, 2026), "
                             "and add insulation (up to $5,500), windows (up to $2,000) and solar ($5,000) where they fit. ")
                    + f"If you heat with gas, the provincial heat pump money is income-qualified: up to <strong>$13,000</strong> at Level 1{north}.</p>")),
        # stack image alt text
        (r'alt="How BC home-energy rebates stack for an? [^"]*combined up to about \$35,000\."',
         lambda m: (f'alt="How BC home-energy rebates stack for a {name} home: heat pump up to $4,000 from BC Hydro when replacing electric heat, or up to $13,000 if income-qualified through CleanBC; '
                    'insulation up to $5,500; solar $5,000; battery up to $5,000; heat pump water heater up to $1,000; windows up to $2,000; EV charger up to $550."')),
        # stale northern fuel-switching amounts
        (r'switching off fossil heat pays <strong>more</strong>: up to <strong>\$6,000</strong> to replace oil heating with a heat pump, or up to <strong>\$8,000</strong> to replace natural gas or propane &mdash; on top of the standard CleanBC amounts\.',
         lambda m: "income-qualified households switching off fossil heat get more: CleanBC adds a <strong>$3,000 northern top-up</strong> (income levels 1 and 2) for a central or multi-zone heat pump, or $1,500 for a single-head unit."),
        (r'higher northern fuel-switching top-ups &mdash; up to \$6,000 \(oil\) or \$8,000 \(gas/propane\)',
         lambda m: "CleanBC's $3,000 northern top-up for income-qualified households"),
        # bespoke per-city FAQ phrasing (visible + JSON-LD dash variants)
        (r'CleanBC pays \$4,000(?:&ndash;|–)\$13,000 \(routed through FortisBC/CleanBC here\)',
         lambda m: "FortisBC pays up to $4,000 (up to $12,000 for a central system if income-qualified)"),
        (r'CleanBC pays \$4,000(?:&ndash;|–)\$13,000',
         lambda m: ("FortisBC pays up to $4,000 (up to $12,000 for a central system if income-qualified)" if fortis else
                    "BC Hydro pays up to $4,000 when you replace electric heat, and CleanBC up to $13,000 if your income qualifies")),
        (r'the CleanBC heat pump rebate \(\$4,000(?:&ndash;|–)\$13,000\)',
         lambda m: "a heat pump rebate (up to $4,000 from BC Hydro if you're replacing electric heat, or up to $13,000 through CleanBC if your income qualifies)"),
        (r'\(\$4,000(?:&ndash;|–)\$13,000\)', lambda m: "(up to $13,000 if your income qualifies)"),
        (r'up to \$6,000 \(oil\) or \$8,000 \(gas/propane\)(?: on top of (?:the )?standard CleanBC amounts)?',
         lambda m: "a $3,000 northern top-up on top of CleanBC's income-qualified amounts"),
        (r'<p>A typical household[^<]*keeps <strong>\$5,000&ndash;\$13,000</strong>.*?</p>',
         lambda m: ("<p>" + ("On FortisBC, a whole-home heat pump gets up to <strong>$4,000</strong> (up to $12,000 for a central system if income-qualified). "
                             if fortis else
                             "If you heat with electricity, expect up to <strong>$4,000</strong> for a whole-home heat pump (plus up to $1,000 if it's finished by October 31, 2026), "
                             "and add insulation (up to $5,500), windows (up to $2,000) and solar ($5,000) where they fit. ")
                    + f"If you heat with gas, the provincial heat pump money is income-qualified: up to <strong>$13,000</strong> at Level 1{north}.</p>")),
        # Fraser Valley regional page
        (r'heat pumps \(\$4,000(?:&ndash;|–)\$13,000\)', lambda m: "heat pumps (up to $4,000 from BC Hydro replacing electric heat; up to $13,000 through CleanBC if income-qualified)"),
        (r'water heaters \(up to \$3,000\)', lambda m: "heat pump water heaters (up to $1,000; up to $3,500 if income-qualified)"),
        (r'The \$4,000(?:&ndash;|–)\$13,000 heat pump rebate is designed exactly for fuel-switching households like yours',
         lambda m: "Gas-heated households can get up to $13,000 through CleanBC if their income qualifies"),
        (r'\$4,000(?:&ndash;|–)\$13,000 for replacing gas furnace, oil system, or electric baseboards\.',
         lambda m: "Up to $4,000 (BC Hydro) replacing electric baseboards; up to $13,000 (CleanBC, income-qualified) replacing a gas furnace or oil system."),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    totals = {}
    for slug in CITIES:
        p = ROOT / "ca" / "bc" / slug / "index.html"
        s = p.read_text(encoding="utf-8")
        m = re.search(r"<h1[^>]*>.*?(?:in|for) ([A-Z][A-Za-z. ]+?)(?: Homeowners|,| 20|<)", s, flags=re.S)
        name = {"fraser-valley": "Fraser Valley", "fort-st-john": "Fort St. John", "prince-george": "Prince George", "maple-ridge": "Maple Ridge"}.get(slug, slug.title())
        hits = []
        for i, (pat, rep) in enumerate(rules(slug, name)):
            s, n = re.subn(pat, rep, s, flags=re.S)
            hits.append(n)
            totals[i] = totals.get(i, 0) + n
        if not args.dry_run:
            p.write_text(s, encoding="utf-8")
        print(f"{slug:14} {''.join(str(h) for h in hits)}")
    print("rule totals:", totals)


if __name__ == "__main__":
    main()
