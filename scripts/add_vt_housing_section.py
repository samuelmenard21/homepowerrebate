#!/usr/bin/env python3
"""Adds a 'heating fuel and housing' section to the Montpelier and Barre hubs from data/vt-housing-acs2024.json (ACS 2020-2024, city place level).
Wrapped in VT-HOUSING markers so re-runs replace it. Prose is hand-written per city."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as nf
D = json.load(open(ROOT / "data/vt-housing-acs2024.json"))
pct = lambda n, d: f"{100 * n / d:.0f}%"
ACS = '<a href="https://data.census.gov/table/ACSDT5Y2024.B25040" target="_blank" rel="noopener">US Census Bureau American Community Survey, 2020 to 2024</a>'
M, B = D["montpelier"], D["barre"]
TEXT = {
"montpelier": f"""<h2>What Montpelier homes burn today, and why it changes your rebate math</h2>
<p>Of {M['occupied']:,} occupied homes in the city of Montpelier, {M['oil']:,} ({pct(M['oil'], M['occupied'])}) heat mainly with fuel oil or kerosene, {M['lp_gas']:,} ({pct(M['lp_gas'], M['occupied'])}) with bottled or tank propane, {M['electric']:,} ({pct(M['electric'], M['occupied'])}) with electricity, {M['wood']:,} ({pct(M['wood'], M['occupied'])}) with wood and only {M['utility_gas']:,} ({pct(M['utility_gas'], M['occupied'])}) with piped natural gas, according to the {ACS}. Propane is a bigger slice here than in Barre, and it is usually the most expensive way to heat a house, which is where a heat pump saves the most.</p>
<p>About {pct(M['built_1939_or_earlier'], M['housing_units'])} of Montpelier's housing units ({M['built_1939_or_earlier']:,} of {M['housing_units']:,}) were built in 1939 or earlier, and {pct(M['owner'], M['occupied'])} of occupied homes are owner-occupied. For an older house, Efficiency Vermont's weatherization rebate (up to $3,000, or $7,000 for income-eligible homes) usually belongs ahead of the heat pump, because a tighter house needs a smaller system. Renters are {pct(M['renter'], M['occupied'])} of households, and Efficiency Vermont lists a separate Home Performance offer for owners of one-to-four-unit rental buildings.</p>
<p>Montpelier sits in Washington County, so the Green Mountain Power income limit for a household of four is $91,200 (80% of area median income) for the $2,000 per condenser rebate. The January average low in our climate file is -11.9&deg;C, and the coldest recorded in 2015 to 2024 was -30.7&deg;C, which is why we only point to cold-climate models on Efficiency Vermont's qualifying list.</p>""",
"barre": f"""<h2>Oil country: what Barre homes burn and what that means for a heat pump</h2>
<p>Barre is more oil-dependent than its neighbour. Of {B['occupied']:,} occupied homes in the city of Barre, {B['oil']:,} ({pct(B['oil'], B['occupied'])}) heat mainly with fuel oil or kerosene, {B['lp_gas']:,} ({pct(B['lp_gas'], B['occupied'])}) with propane, {B['electric']:,} ({pct(B['electric'], B['occupied'])}) with electricity, {B['wood']:,} ({pct(B['wood'], B['occupied'])}) with wood and just {B['utility_gas']:,} ({pct(B['utility_gas'], B['occupied'])}) with piped natural gas, per the {ACS}. Any household on oil that moves part of its load to a cold-climate heat pump replaces the fuel most exposed to price swings.</p>
<p>The housing is also older: {B['built_1939_or_earlier']:,} of {B['housing_units']:,} units ({pct(B['built_1939_or_earlier'], B['housing_units'])}) date from 1939 or earlier. Barre is nearly evenly split between owners ({B['owner']:,}) and renters ({B['renter']:,}), so many readers here will be landlords or tenants. Efficiency Vermont lists Home Performance with ENERGY STAR for one-to-four-unit rental owners. The heat pump income bonus is not available to rental property owners, so landlords should read the eligibility tab before counting on it.</p>
<p>Barre is also in Washington County: a four-person household must be at or under $91,200 for Green Mountain Power's $2,000 per condenser rebate. The January average low is -11.9&deg;C, with a record low of -30.9&deg;C in 2015 to 2024. A homeowner with an oil boiler and radiators and no ductwork usually starts with a ductless system for the main living area, then decides whether to keep the boiler for the coldest nights.</p>"""}
for city, body in TEXT.items():
    p = ROOT / f"us/vt/{city}/index.html"
    s = p.read_text(encoding="utf-8")
    block = f"<!-- VT-HOUSING-START --><section class=\"wrap\" style=\"max-width:860px;margin:0 auto;padding:8px 20px 24px;line-height:1.65;\">{body}</section><!-- VT-HOUSING-END -->"
    s = re.sub(r"<!-- VT-HOUSING-START -->.*?<!-- VT-HOUSING-END -->", "", s, flags=re.S)
    i = nf.content_insert_point(s)
    assert i >= 0
    p.write_text(s[:i] + block + "\n" + s[i:], encoding="utf-8")
    print("updated", p)
