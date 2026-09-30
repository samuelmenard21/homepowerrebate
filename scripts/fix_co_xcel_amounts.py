#!/usr/bin/env python3
"""Fix Denver/Aurora/Boulder heat pump + water heater pages to Xcel's 2026 Rebate Summary (effective Oct 1, 2026):
cold-climate heat pump $750 per heating ton, $1,500 with the gas-home bonus; ASHP $300/$600 per cooling ton;
heat pump water heater $750, $1,500 with the bonus. The pages had the old $2,250 per ton / $9,000 figures."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD_HP = ("Xcel Energy pays $2,250 per ton of heating capacity for a qualifying cold-climate heat pump (a 3-ton system nets $6,750; "
          "a 4-ton system nets $9,000), or $900 per ton for a standard-efficiency heat pump.")
NEW_HP = ("Xcel Energy pays $750 per heating ton for a qualifying cold-climate heat pump, so a 3-ton system gets $2,250. Homes heated with "
          "Xcel natural gas get a bonus from October 1, 2026 that doubles it to $1,500 per ton, or $4,500 for 3 tons. A standard heat pump gets "
          "$300 per cooling ton, or $600 with the bonus. Homes with electric heat, such as baseboards, get the standard amount only.")
HP = [
    (OLD_HP, NEW_HP),
    ("<strong>Up to $9,000</strong>", "<strong>$750 to $1,500 per heating ton</strong>"),
    ('<div class="amount">Up to $9,000</div>', '<div class="amount">$750 to $1,500 per ton</div>'),
    ("Denver's heat pump rebate comes with a hard deadline built in. The full per-ton payment from Xcel Energy drops by about a third after October 1, 2026, so timing your install matters as much as picking a contractor.",
     "Denver's heat pump rebate has a date built in. Xcel Energy adds a gas-home bonus on October 1, 2026 that doubles the per-ton payment, so what your home heats with matters as much as picking a contractor."),
    ("Will the $2,250-per-ton rate still be there when I'm ready to install?", "Does my heating fuel change the Xcel rebate?"),
    ("Not necessarily — that rate is explicitly scheduled to drop to roughly $1,500 per ton after October 1, 2026, and Xcel can also adjust funding or eligibility rules before that date. Get a written quote with your install date locked in, and check Xcel's own rebate page rather than relying on this page's number if you're planning to install anywhere near that cutoff.",
     "Yes. Xcel's 2026 rebate sheet, effective October 1, 2026, pays $750 per heating ton as the standard rebate and $1,500 per ton to homes that heat with Xcel natural gas. Homes with electric heat, such as baseboards, get the standard amount. Xcel can change funding or rules, so get a written quote and check Xcel's own rebate page before you sign."),
    ("Xcel Energy, and why the date on your quote matters", "Xcel Energy, and why your heating fuel matters"),
    ("The $2,250-per-ton figure above is good only through October 1, 2026. After that, Xcel's cold-climate heat pump rebate drops roughly a third, to about $1,500 per ton, which means two Denver homeowners getting identical quotes six weeks apart could end up with rebates a couple thousand dollars apart for the same equipment. That timing detail is worth building into your installer conversation now rather than discovering it after signing.",
     "Xcel's cold-climate heat pump rebate is $750 per heating ton, and $1,500 per ton for homes heated with Xcel natural gas from October 1, 2026. Two Denver neighbours with identical quotes can end up a couple thousand dollars apart if one heats with gas and the other with baseboards. Tell your installer what you heat with now rather than finding out after signing."),
    ("Stack the flat $1,000 Colorado tax credit and DRCOG's Power Ahead Colorado rebate on top of Xcel's per-ton payment and the total climbs well past the $9,000 headline for a properly sized system installed before the cutoff.",
     "Stack the flat $1,000 Colorado tax credit and DRCOG's Power Ahead Colorado rebate on top of Xcel's per-ton payment and the total climbs for a properly sized system."),
    ("Up to $9,000", "$750 to $1,500 per ton"),
    ("so the per-ton rate and the October 1, 2026 cutoff apply identically", "so the per-ton rate and the October 1, 2026 gas-bonus start apply identically"),
    ("Xcel pays $2,250 per ton for a cold-climate system through October 1, 2026, then roughly $1,500 per ton after that date.",
     "Xcel pays $750 per heating ton for a cold-climate system, or $1,500 per ton for gas-heated homes from October 1, 2026."),
    ("$2,250 per ton for a cold-climate heat pump through October 1, 2026, then a drop to roughly $1,500 per ton,",
     "$750 per heating ton for a cold-climate heat pump, or $1,500 per ton for gas-heated homes from October 1, 2026,"),
]
WH = [
    ('<div class="amount">$2,250 flat</div>', '<div class="amount">$750 to $1,500</div>'),
    ("A flat $2,250 from Xcel Energy, no income test attached.", "$750 from Xcel Energy, or $1,500 for gas-heated homes from October 1, 2026, with no income test."),
    ("Xcel Energy pays this out flat, $2,250 toward a qualifying heat pump water heater, with no income test to clear.",
     "Xcel Energy pays $750 toward a qualifying heat pump water heater, or $1,500 if your home heats with Xcel natural gas from October 1, 2026. There is no income test to clear."),
    ("Xcel Energy pays a flat $2,250 rebate for a qualifying heat pump water heater, with no income qualification required for the standard rebate.",
     "Xcel Energy pays $750 for a qualifying heat pump water heater, or $1,500 for gas-heated homes from October 1, 2026. No income qualification is required for the standard rebate."),
    ("Xcel Energy's standard offer is a flat $2,250 for a qualifying heat pump water heater, no income test required,", "Xcel Energy's standard offer is $750 for a qualifying heat pump water heater ($1,500 for gas-heated homes from October 1, 2026), no income test required,"),
    ("Combined with Xcel's flat $2,250, an income-qualified Boulder household could realistically see over $4,000 back",
     "Combined with Xcel's $750, an income-qualified Boulder household could see up to $2,750 back, or $3,500 with the gas bonus,"),
    ("layered on top of Xcel's flat $2,250.", "layered on top of Xcel's $750 rebate."),
    ("administers the $2,250 rebate itself", "administers the water heater rebate itself"),
    ("administers the standard $2,250 rebate directly", "administers the standard $750 rebate directly"),
    ("$2,250 flat", "$750"),
    ("flat $2,250", "$750"),
    ("$2,250", "$750"),
]
CITIES = ["denver", "aurora", "boulder"]


def main():
    for c in CITIES:
        for cat, table in (("heat-pump", HP), ("water-heater", WH)):
            f = ROOT / "us/co" / c / cat / "index.html"
            t = f.read_text(encoding="utf-8")
            for a, b in table:
                t = t.replace(a, b)
            f.write_text(t, encoding="utf-8")
            left = [m.group(0) for m in re.finditer(r"\$2,250|\$9,000|\$6,750|a third|\$900 per", t)]
            print(c, cat, "leftover:", left)


if __name__ == "__main__":
    main()
