#!/usr/bin/env python3
"""
Rewrite the body of stand-alone BC blog posts that carried stale or invented numbers
(pre-July-2026 CleanBC amounts, "$11,350 insulation stack", invented battery/brand
facts, made-up payback math). Facts: data/verified-facts/bc-blog.json (2026-09-26).

Touches only: <title>, meta description, og:title/og:description, Article/BlogPosting/
FAQPage JSON-LD (replaced), BreadcrumbList name, breadcrumb label, and the content between
CANONICAL-BREADCRUMB-END and the canonical nav/footer JS (or CANONICAL-FOOTER-START).
Idempotent. Usage: python3 scripts/fix_bc_blog_standalone.py
"""
import html
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_bc_blog_city_guides as g  # noqa: E402

S = dict(g.S)
S.update({
    "sb_tc": ("BC Hydro solar and battery rebate terms (July 29, 2026)", "https://www.bchydro.com/content/dam/BCHydro/customer-portal/documents/power-smart/residential/programs/solar-battery-rebate-terms-and-conditions.pdf"),
    "sb": ("BC Hydro solar and battery rebates", "https://app.bchydro.com/accounts-billing/electrical-connections/customer-generation/solar-battery-rebates.html"),
    "tesla": ("BC Hydro ineligible products (Tesla)", "https://www.bchydro.com/powersmart/ineligible-product-information.html"),
    "batlist": ("BC Hydro qualified battery list", "https://www.bchydro.com/content/dam/BCHydro/customer-portal/documents/power-smart/residential/programs/energy-storage-battery-list.pdf"),
    "rs2289": ("BC Hydro self-generation rate updates", "https://www.bchydro.com/toolbar/about/strategies-plans-regulatory/rate-design/self-generation-rate-updates.html"),
    "peak": ("BC Hydro Peak Saver", "https://www.bchydro.com/powersmart/residential/rebates-programs/peak-saver.html"),
    "hpwh_list": ("NEEA qualified heat pump water heaters", "https://neea.org/our-work/advanced-water-heater-specification"),
})
g.S.update(S)
TODAY_H = g.TODAY_H

CSS = """<style id="bcblog-post-css">
.hpr-post{max-width:760px;margin:0 auto;padding:36px 20px 56px;color:var(--ink,#0a2a2e)}
.hpr-post h1{font-family:'Fraunces',Georgia,serif;font-size:clamp(28px,5vw,40px);line-height:1.2;margin:6px 0 10px;font-weight:500}
.hpr-post h2{font-family:'Fraunces',Georgia,serif;font-size:25px;margin:34px 0 12px;font-weight:500;line-height:1.25}
.hpr-post h3{font-size:18px;margin:22px 0 8px}
.hpr-post p,.hpr-post li{font-size:17px;line-height:1.65;color:var(--ink-soft,#1a3d42)}
.hpr-post p{margin:0 0 16px}.hpr-post ul,.hpr-post ol{margin:0 0 18px 22px}.hpr-post li{margin-bottom:8px}
.hpr-post a{color:var(--teal-deep,#08363f);font-weight:600;text-decoration:underline;text-decoration-color:var(--amber,#d4751c)}
.hpr-post .hpr-eyebrow{font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--amber,#d4751c)}
.hpr-post .hpr-meta{font-size:14px;color:var(--sage,#6b8e7f)}
.hpr-post .callout{background:var(--paper-warm,#f5efe5);border-left:4px solid var(--amber,#d4751c);border-radius:8px;padding:18px 22px;margin:22px 0}
.hpr-post .callout p{margin:0}
.hpr-post .related a{display:block;padding:10px 0;border-bottom:1px solid var(--rule,#d9d0c1);text-decoration:none}
.hpr-post .related h4{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--sage,#6b8e7f);margin:36px 0 8px}
</style>"""

CTA = ('<div class="hpr-cta"><h3>See your city\'s rebates</h3><p>Compare top-rated local installers, ranked by Google reviews. '
       'Free for homeowners, and we\'ll tell you honestly if the math doesn\'t work for your home.</p>'
       '<a class="hpr-btn" href="/ca/bc/">See your city\'s rebates &rarr;</a></div>')


def table(head, rows):
    return ('<div class="hpr-table"><table><thead><tr>' + "".join(f"<th>{h}</th>" for h in head) + "</tr></thead><tbody>" +
            "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows) + "</tbody></table></div>")


def short(txt):
    return f'<div class="callout hpr-short"><p><strong>Short answer:</strong> {txt}</p></div>'


ESP_HP = table(["Heat pump type (switching from gas, oil or propane)", "Level 1", "Level 2", "Level 3"], [
    ["Central ducted, or multi-split with 3+ heads", "$13,000", "$7,000", "$3,500"],
    ["2-head multi-split, or two single-head mini-splits", "$11,000", "$5,500", "$1,000"],
    ["Single-head mini-split", "$5,500", "$4,500", "$1,000"],
    ["Switching from electric heat (any type)", "$5,000", "Not eligible", "Not eligible"],
])
ESP_INC = table(["People in home", "Level 1 up to", "Level 2 up to", "Level 3 up to"], [
    ["1", "$51,100", "$63,900", "$102,100"], ["2", "$63,600", "$79,500", "$127,200"], ["3", "$78,200", "$97,700", "$156,300"],
    ["4", "$94,900", "$118,600", "$189,800"], ["5", "$107,600", "$134,500", "$215,200"], ["6", "$121,400", "$151,700", "$242,700"],
    ["7+", "$135,100", "$168,900", "$270,200"]])

P = {}

# ---------------------------------------------------------------------------------------------
P["cleanbc-rebate-changes-july-2026"] = dict(
    eyebrow="Program change", title="CleanBC Rebate Changes July 2026: New Amounts",
    desc="CleanBC income-qualified rebates changed on July 6, 2026. New heat pump maximums ($13,000 / $7,000 / $3,500), what was cut, and what to do now.",
    crumb="CleanBC changes July 2026",
    body=[
        short("For invoices dated on or after <strong>July 6, 2026</strong>, the CleanBC Energy Savings Program pays less. The top heat pump rebate for switching from gas, oil or propane is now <strong>$13,000</strong> (Income Level 1), <strong>$7,000</strong> (Level 2) and <strong>$3,500</strong> (Level 3). Homes switching from electric heat can get up to <strong>$5,000</strong>, but only at Level 1."),
        "<p>If you read an older article that says \"$16,000 / $12,000 / $10,500\", those were the amounts before July 6. They no longer apply to new invoices.</p>",
        "<h2>New CleanBC heat pump amounts (from July 6, 2026)</h2>", ESP_HP,
        "<p>CleanBC pays 100% of eligible costs up to these maximums. Homes at or north of 100 Mile House that are on BC Hydro get a northern top-up of $3,000 (or $1,500 for a single-head mini-split) at Levels 1 and 2.</p>",
        "<h2>What else changed</h2><ul>"
        "<li><strong>The Level 2 electric stream is gone.</strong> Only Level 1 homes can get CleanBC money for replacing electric heat.</li>"
        "<li><strong>No insulation or window rebates</strong> are listed in the July 2026 Energy Savings Program rules.</li>"
        "<li><strong>Heat pump water heater:</strong> up to $3,500 when converting from fossil fuel (all levels); from electric, $3,500 at Level 1 and $2,800 at Level 2.</li>"
        "<li><strong>Electrical service upgrade</strong> (only when switching from fossil fuel): $5,000 / $3,500 / $1,500.</li>"
        "<li><strong>Ventilation and health-and-safety</strong> add-ons (HRV up to $1,600, bathroom fan $300, $800 for things like mould or asbestos) only when paired with a heat pump or heat pump water heater.</li></ul>",
        "<h2>Who qualifies? The income limits</h2><p>It's based on the number of people in your home and the combined pre-tax income of the adults.</p>" + ESP_INC,
        "<h2>What didn't change</h2><p>BC Hydro's own rebates are separate from CleanBC and are open to any income: up to $4,000 for a heat pump that replaces electric heat, $1,000/kW for solar (up to $5,000), and up to $5,000 for a battery with Peak Saver. If you heat with gas and don't qualify by income, there is no general heat pump rebate right now; that ended April 11, 2025.</p>",
        "<h2>What to do next</h2><ol><li>Check your income level in the table.</li><li>Pre-register with the Energy Savings Program before any work starts.</li><li>Use a program-registered contractor.</li><li>If you don't qualify, check <a href=\"/blog/heat-pump-rebate-guide-bc-2026/\">BC Hydro's heat pump rebate</a>.</li></ol>",
    ],
    faqs=[("How much is the CleanBC heat pump rebate now?", "For invoices from July 6, 2026: up to $13,000 at Income Level 1, $7,000 at Level 2 and $3,500 at Level 3 when switching from gas, oil or propane to a central or 3+ head system. Electric-to-heat-pump is $5,000 at Level 1 only."),
          ("Is the $16,000 CleanBC rebate gone?", "Yes, for new invoices. $16,000 was the old Level 1 maximum before July 6, 2026. Today the only way to reach $16,000 is $13,000 plus the $3,000 northern top-up, for Level 1 homes at or north of 100 Mile House."),
          ("Does CleanBC still pay for insulation?", "Not in the July 2026 Energy Savings Program rules. BC Hydro and FortisBC still have their own insulation rebates.")],
    sources=["esp", "bch_hp"],
    related=[("/blog/free-heat-pump-bc-income-qualified/", "Can you get a free heat pump in BC?"), ("/blog/heat-pump-rebates-income-tiers-bc-2026/", "Heat pump rebates by income level"), ("/blog/heat-pump-rebate-guide-bc-2026/", "BC heat pump rebates 2026")],
)

P["cleanbc-income-qualified-free-heat-pump-2026"] = dict(
    eyebrow="Income-qualified", title="CleanBC Free Heat Pump 2026: Who Qualifies",
    desc="Who qualifies for a free or nearly free heat pump in BC in 2026: official CleanBC income limits, new July 2026 amounts, and ECAP.",
    crumb="CleanBC income-qualified heat pump",
    body=[
        short("If your household income is under the CleanBC limits (for a family of four, up to <strong>$94,900</strong> for Level 1), CleanBC pays 100% of eligible heat pump costs up to <strong>$13,000</strong> when you switch from gas, oil or propane. If your system costs less than the cap, it can be free. ECAP, run by BC Hydro and FortisBC, can also install upgrades for free."),
        "<h2>The official 2026 income limits</h2><p>Add up the pre-tax income of every adult in the home (not dependants). These are the limits for invoices from July 6, 2026:</p>" + ESP_INC,
        "<h2>How much CleanBC pays</h2>" + ESP_HP + "<p>Northern top-up: +$3,000 (or +$1,500 for one head) at Levels 1 and 2, for BC Hydro homes at or north of 100 Mile House.</p>",
        "<h2>Is it really free?</h2><p>It can be. CleanBC pays 100% of eligible costs up to the maximum. A Level 1 home switching from gas to a heat pump that costs less than $13,000 would pay nothing for the heat pump. If it costs more, you pay the difference. Level 2 and 3 homes get less, so for them it's a big discount, not free.</p>",
        "<h2>ECAP: free upgrades, no application math</h2><p>The Energy Conservation Assistance Program gives income-qualified households a free home energy evaluation. If you qualify, the evaluator arranges free upgrades. Some homes get a heat pump or insulation; others get smaller items. You don't pick the upgrades.</p>",
        "<h2>Just above the limit?</h2><ul><li>If you heat with electric baseboards or an electric furnace, BC Hydro pays up to $4,000 at any income (FortisBC also pays up to $4,000 in its electric areas).</li><li>FortisBC electric customers who are income-qualified can get up to $12,000.</li><li>The federal Greener Homes Grant is closed.</li></ul>",
        "<h2>What to do next</h2><ol><li>Check your level in the table above.</li><li>Gather a CRA Notice of Assessment for each adult.</li><li>Pre-register with the CleanBC Energy Savings Program, or apply to ECAP through your utility, before any work starts.</li><li>Use a registered contractor; self-installs don't qualify.</li></ol>",
    ],
    faqs=[("What is the income limit for a free heat pump in BC?", "For Level 1 (the highest rebates): $51,100 for one person, $63,600 for two, $78,200 for three, $94,900 for four, up to $135,100 for seven or more."),
          ("How much does CleanBC pay for an income-qualified heat pump?", "From July 6, 2026: up to $13,000 (Level 1), $7,000 (Level 2) or $3,500 (Level 3) for a central or 3+ head system replacing gas, oil or propane. From electric heat, $5,000 at Level 1 only."),
          ("Can renters apply?", "The program rules include a path for tenants with the owner's consent, but the owner is involved. Check the program rules before you start.")],
    sources=["esp", "ecap", "bch_income", "fb_iq"],
    related=[("/blog/free-heat-pump-bc-income-qualified/", "Free heat pump in BC: city-by-city guides"), ("/blog/cleanbc-rebate-changes-july-2026/", "What changed on July 6, 2026")],
)

P["heat-pump-rebates-income-tiers-bc-2026"] = dict(
    eyebrow="Guide", title="BC Heat Pump Rebates by Income Level (2026)",
    desc="How BC heat pump rebates change with income in 2026: official CleanBC Level 1, 2 and 3 limits and amounts, plus the BC Hydro rebate open to everyone.",
    crumb="Heat pump rebates by income",
    body=[
        short("Your income level decides your CleanBC amount. Switching from gas, oil or propane to a central heat pump: <strong>$13,000</strong> at Level 1, <strong>$7,000</strong> at Level 2, <strong>$3,500</strong> at Level 3. Above Level 3, there's no CleanBC rebate. Separately, BC Hydro pays up to <strong>$4,000</strong> at any income if the heat pump replaces electric heat."),
        "<h2>Step 1: find your level</h2>" + ESP_INC,
        "<h2>Step 2: find your amount</h2>" + ESP_HP,
        "<h2>A worked example</h2><p>A family of four with gas heat and a combined income of $100,000 is Level 2 (between $94,900 and $118,600). A central ducted heat pump gets up to $7,000. If their income were $90,000, they'd be Level 1 and get up to $13,000. If it were $200,000, they'd be above Level 3 and get no CleanBC rebate.</p>",
        "<h2>If your home is on FortisBC electricity</h2><p>In Kelowna, Penticton and other FortisBC electric areas, FortisBC pays up to $4,000 for replacing electric heat at any income, or up to $12,000 (central ducted) if you're under the Level 1 limits.</p>",
        "<h2>Other rules to know</h2><ul><li>Home value limits apply to the CleanBC program; check the current BC Assessment cap in the program rules.</li><li>Use a CleanBC Energy Savings Program registered contractor.</li><li>Pre-register before work starts.</li></ul>",
    ],
    faqs=[("What are the CleanBC income levels for a family of four?", "Level 1 up to $94,900, Level 2 up to $118,600, Level 3 up to $189,800 in combined pre-tax adult income."),
          ("Does Level 3 get more than Level 2?", "No. Level 3 gets the least: up to $3,500 for a central system from fossil fuel, versus $7,000 at Level 2 and $13,000 at Level 1."),
          ("Can I get BC Hydro's rebate if I earn too much for CleanBC?", "Yes, if the heat pump replaces electric heat. BC Hydro's up-to-$4,000 rebate has no income test.")],
    sources=["esp", "bch_hp", "fb_iq"],
    related=[("/blog/cleanbc-income-qualified-free-heat-pump-2026/", "Who qualifies for a free heat pump"), ("/blog/heat-pump-rebate-guide-bc-2026/", "BC heat pump rebates 2026")],
)

INS = table(["Where", "Rebate formula", "Max"], [
    ["Attic (flat or cathedral)", "$0.02 x R-value added x sq. ft.", "$900"],
    ["Exterior wall cavities", "$0.09 x R-value added x sq. ft.", "$1,200"],
    ["Exterior wall sheathing", "$0.09 x R-value added x sq. ft.", "$1,200"],
    ["Basement or crawlspace walls", "$0.09 x R-value added x sq. ft.", "$1,200"],
    ["Other (exposed floor, floor over crawlspace, headers)", "$0.07 x R-value added x sq. ft.", "$1,000"]])

P["insulation-rebates-bc-stack-federal-provincial"] = dict(
    eyebrow="Insulation", title="BC Insulation Rebates 2026: What You Can Get",
    desc="BC insulation rebates in 2026: BC Hydro and FortisBC pay by square foot and R-value added (attic up to $900, walls up to $1,200). Rules and bonuses.",
    crumb="BC insulation rebates 2026", keep_lead=True,
    body=[
        short("In 2026, BC insulation rebates come from <strong>BC Hydro</strong> (for electrically heated homes) or <strong>FortisBC</strong> (gas or FortisBC electric customers). Both pay by area and R-value added: up to <strong>$900</strong> for an attic and up to <strong>$1,200</strong> each for walls and basement. Doing a second upgrade can add a bonus. The federal Greener Homes Grant is closed, and the July 2026 CleanBC income-qualified rules don't include insulation."),
        "<h2>How much: the insulation rebate formula</h2>" + INS +
        "<p>Example: a 1,000 sq. ft. attic topped up by R-40 works out to $0.02 x 40 x 1,000 = $800. Minimum R-value added: R-12 for attics and wall cavities, R-3.8 for sheathing, R-10 for basement walls, R-20 for other areas.</p>",
        "<h2>BC Hydro or FortisBC: which one do you use?</h2><ul><li><strong>BC Hydro:</strong> for BC Hydro customers with electrically heated homes. Your contractor must be a Home Performance Contractor Network (HPCN) member.</li><li><strong>FortisBC:</strong> for FortisBC natural gas customers and FortisBC electric customers (plus Penticton, Summerland, Grand Forks and Nelson Hydro).</li></ul><p>Apply within six months of your invoice. Self-installs don't qualify.</p>",
        "<h2>Bonuses for doing more</h2><p>BC Hydro offers a bonus of up to $2,000 for completing more than one upgrade. FortisBC pays a $300 two-upgrade bonus, or $20 per 1% EnerGuide rating improvement ($750 to $2,000) if you do before-and-after evaluations.</p>",
        "<h2>Income-qualified?</h2><p>ECAP (run by BC Hydro and FortisBC) can install insulation for free in some homes after a free evaluation. FortisBC also has an income-qualified insulation rebate.</p>",
        "<h2>Is insulation worth it?</h2><p>Usually, yes, especially in the attic. It's often the cheapest upgrade per dollar saved, and a better-insulated home can use a smaller heat pump. Ask for the R-value before and after in writing on your quote.</p>",
    ],
    faqs=[("How much is the BC Hydro insulation rebate?", "It's $0.02 x R-value added x square feet for attics (up to $900), and $0.09 for walls, sheathing and basements (up to $1,200 each)."),
          ("Can I stack federal, provincial and utility insulation rebates?", "Not the way older articles describe. The federal Greener Homes Grant is closed, and the July 2026 CleanBC income-qualified program doesn't list insulation. Your main option is BC Hydro or FortisBC, plus their multi-upgrade bonus."),
          ("Do I need an HPCN contractor?", "Yes, for BC Hydro's insulation rebate. Self-installs don't qualify for BC Hydro or FortisBC.")],
    sources=["bch_ins", "fb_ins", "fb_bonus", "ecap", "esp"],
    related=[("/blog/insulation-buying-guide-bc/", "Insulation buying guide for BC"), ("/blog/heat-pump-rebate-guide-bc-2026/", "BC heat pump rebates 2026")],
)

P["bc-cities-ranked-total-rebate-stack"] = dict(
    eyebrow="Cities", title="BC Home Rebates by City (2026): What Differs",
    desc="Do BC home rebates change by city? Mostly no. What actually differs in 2026: your utility, the northern top-up, and a few city loans and EV top-ups.",
    crumb="BC rebates by city",
    body=[
        short("Most BC rebates are the <strong>same everywhere</strong>. What changes by city is: <strong>which utility</strong> you're on (Kelowna and Penticton use FortisBC programs), whether you're <strong>north of 100 Mile House</strong> (a CleanBC top-up for income-qualified homes), and a few <strong>local loans and EV charger top-ups</strong>. We don't rank cities by dollar totals, because those totals were guesses."),
        "<h2>What's the same in every BC Hydro city</h2><ul><li>Heat pump replacing electric heat: up to $4,000 (+ up to $1,000 for installs Aug 1 - Oct 31, 2026)</li><li>Solar: $1,000/kW up to $5,000; battery up to $5,000 with Peak Saver</li><li>Insulation: attic up to $900, walls or basement up to $1,200</li><li>Windows and doors: $100 each up to $2,000 (not in City of Vancouver)</li><li>CleanBC income-qualified heat pump: up to $13,000 / $7,000 / $3,500 by income level</li></ul>",
        "<h2>What's different, city by city</h2>" + table(["City", "What's different"], [
            ["Kelowna", "FortisBC electricity: use FortisBC rebates (heat pump up to $4,000, or $12,000 income-qualified). No BC Hydro solar/battery rebates or Peak Saver."],
            ["Penticton", "City electric utility; FortisBC rebates apply. City Home Energy Loan Program: up to $10,000 on your electric bill."],
            ["Nanaimo", "City zero-interest retrofit loan up to $15,000 on property tax (2026 intake Sept 14 - Oct 31). RDN electoral areas: +$150 EV charger top-up."],
            ["Kamloops", "+ up to $150 on BC Hydro's EV charger rebate."],
            ["Squamish", "+ up to $150 on BC Hydro's EV charger rebate."],
            ["Prince George, Fort St. John", "North of 100 Mile House: +$3,000 CleanBC northern top-up (Levels 1-2)."],
            ["Vancouver", "BC Hydro and FortisBC window rebates don't apply in the City of Vancouver."],
            ["Vernon", "BC Hydro electricity (unlike Kelowna), so BC Hydro programs apply."],
            ["Abbotsford, Burnaby, Chilliwack, Coquitlam, Langley, Maple Ridge, Richmond, Surrey, Victoria", "No current city cash top-up we could confirm. Standard BC Hydro and CleanBC rebates apply."],
        ]),
        "<h2>What about city heat pump top-ups?</h2><p>Some cities ran heat pump top-ups under the older CleanBC program. The official pages for those offers no longer load, so we don't count them. If your city says it has one, great; ask for the current terms in writing.</p>",
        "<h2>What to do next</h2><p>Pick your city below to see its rebates and compare top-rated installers.</p>" + g.city_picker(lambda s: f"heat-pump-rebate-guide-{s}-2026"),
    ],
    faqs=[("Which BC city has the best rebates?", "For most homes, none: the main rebates are the same across BC Hydro's area. Nanaimo and Penticton stand out for city loans, and Prince George and Fort St. John for the northern top-up (income-qualified)."),
          ("Does Kelowna get BC Hydro rebates?", "No. Kelowna's electricity is FortisBC, so FortisBC's programs apply instead.")],
    sources=["bch_hp", "esp", "fb_hp", "nanaimo", "penticton", "bch_evtop", "bch_win"],
    related=[("/blog/bc-hydro-vs-fortisbc-rebates-which-better/", "BC Hydro vs FortisBC rebates"), ("/blog/heat-pump-rebate-guide-bc-2026/", "BC heat pump rebates 2026")],
)

P["bc-hydro-schedule-2289-battery-payback"] = dict(
    eyebrow="Rate change", title="BC Hydro Rate Schedule 2289: Solar and Battery",
    desc="BC Hydro's self-generation rate (RS 2289) started July 1, 2026: 10 cents/kWh for exported power, paid each bill. What it means for solar and battery owners.",
    crumb="BC Hydro Schedule 2289",
    body=[
        short("Since <strong>July 1, 2026</strong>, new BC Hydro solar customers are on <strong>Rate Schedule 2289</strong>. Power you send to the grid earns <strong>10 cents per kWh</strong>, credited each billing cycle. The old net metering rate (RS 1289) is closed to new customers. Existing net metering customers keep RS 1289 until 10 years after their start date. This makes using your own solar power (including storing it in a battery) worth more than exporting it."),
        "<h2>RS 1289 vs RS 2289</h2>" + table(["", "Net metering (RS 1289)", "Self-generation (RS 2289)"], [
            ["Who", "Existing customers only (closed to new)", "New customers from July 1, 2026"],
            ["Excess power", "Banked as kWh credits against your bill", "Bought at 10 cents per kWh"],
            ["How often", "Settled yearly", "Each billing cycle"],
            ["How long", "Until 10 years after your start date, then moved to RS 2289", "Ongoing"]]),
        "<h2>What it means for a battery</h2><p>Under RS 2289, every kWh you export earns 10 cents. Every kWh you use from your own panels or battery saves you whatever you'd have paid BC Hydro for it. When your electricity price is higher than 10 cents, storing solar in a battery and using it later is worth more than exporting it. The export rate is flat, so there's no bonus for exporting at a certain time of day.</p>"
        "<p>We don't publish a payback number here because it depends on your use, system size and rate. Ask your installer to show the math with your own bills.</p>",
        "<h2>Battery rebate rules (unchanged by RS 2289)</h2><ul><li>$500 per kWh, up to $5,000 if you enroll in Peak Saver within 14 days of the in-service date; up to $1,500 paired with solar otherwise.</li><li>Must be on BC Hydro's qualified battery list and at least 5 kWh. Tesla batteries are not eligible.</li><li>Must be installed by an HPCN member contractor.</li></ul>",
        "<h2>What to do next</h2><ol><li>Size solar to what you use, not to fill the roof.</li><li>If you want backup power, compare approved batteries.</li><li>Get your self-generation application accepted before you install.</li></ol>",
    ],
    faqs=[("What does BC Hydro pay for exported solar in 2026?", "10 cents per kWh on Rate Schedule 2289, credited each billing cycle, for customers who joined from July 1, 2026."),
          ("Can I stay on net metering?", "If you were already on RS 1289, yes, until 10 years after your net metering start date. Then you move to RS 2289."),
          ("Does a Tesla Powerwall get a BC Hydro rebate?", "No. All Tesla batteries have been excluded since March 12, 2025.")],
    sources=["rs2289", "sb", "sb_tc", "tesla"],
    related=[("/blog/bc-net-metering-ended-self-generation-rate-2026/", "BC ended net metering: what changed"), ("/blog/bc-approved-home-battery-rebate/", "How to choose an approved battery")],
)

P["bc-net-metering-ended-self-generation-rate-2026"] = dict(
    eyebrow="Program change", title="BC Net Metering Ended: The 2026 Solar Rate",
    desc="BC Hydro closed net metering to new customers on July 1, 2026. New solar is paid 10 cents/kWh for exports on RS 2289. What changed and what to do.",
    crumb="BC net metering ended",
    body=[
        short("Yes. As of <strong>July 1, 2026</strong>, BC Hydro's net metering rate (RS 1289) is closed to new customers. New solar homes go on the self-generation rate (<strong>RS 2289</strong>), which pays <strong>10 cents per kWh</strong> for power you export, each billing cycle. If you were already on net metering, you stay on it until 10 years after your start date."),
        "<h2>What changed</h2>" + table(["", "Before (RS 1289)", "Now (RS 2289)"], [
            ["Exported power", "Banked as kWh credits", "Paid 10 cents/kWh"], ["Settlement", "Yearly", "Each bill"], ["Available to", "Existing customers", "New customers"]]),
        "<h2>How to size solar now</h2><p>Because exports earn a flat 10 cents, the best value is in power you use yourself. Size your system to your yearly use instead of filling the roof. A battery lets you store daytime solar for the evening.</p>",
        "<h2>Rebates still available</h2><ul><li><strong>Solar:</strong> $1,000 per kW, up to $5,000, and no more than 50% of cost.</li><li><strong>Battery:</strong> $500 per kWh, up to $5,000 if you enroll in Peak Saver within 14 calendar days of the in-service date (no exceptions), or up to $1,500 paired with solar without Peak Saver.</li><li>Your contractor must be a Home Performance Contractor Network (HPCN) member, and your self-generation application must be accepted before you install.</li></ul>",
        "<h2>What to do next</h2><ol><li>Get your last 12 months of use from your BC Hydro account.</li><li>Get quotes from HPCN member contractors.</li><li>If you add a battery, put a reminder for Peak Saver enrollment in the first 14 days.</li></ol>",
    ],
    faqs=[("Did BC end net metering?", "For new customers, yes, on July 1, 2026. Existing net metering customers stay on it until 10 years after their start date."),
          ("How much does BC Hydro pay for solar exports now?", "10 cents per kWh on RS 2289, credited every billing cycle."),
          ("What's the Peak Saver deadline for the battery rebate?", "You must enroll the battery in Peak Saver within 14 calendar days of the in-service date to get the higher rebate. BC Hydro says no exceptions.")],
    sources=["rs2289", "sb", "sb_tc"],
    related=[("/blog/bc-hydro-schedule-2289-battery-payback/", "Schedule 2289 and your battery"), ("/blog/is-bc-hydro-solar-rebate-worth-it/", "Is the BC Hydro solar rebate worth it?")],
)

P["bc-hydro-peak-saver-battery-rebate-5000-vs-1500"] = dict(
    eyebrow="Battery rebate", title="BC Hydro Battery Rebate: $5,000 vs $1,500",
    desc="Why BC Hydro's battery rebate is $5,000 with Peak Saver and $1,500 without, the 14-day enrollment rule, and which batteries qualify.",
    crumb="Battery rebate: $5,000 vs $1,500",
    body=[
        short("BC Hydro pays <strong>$500 per kWh</strong> of battery. The cap is <strong>$5,000</strong> if you enroll the battery in Peak Saver within <strong>14 calendar days</strong> of the in-service date, or <strong>$1,500</strong> if you pair it with solar and don't enroll. A battery without solar and without Peak Saver gets nothing. Tesla batteries are not eligible."),
        "<h2>The rebate at a glance</h2>" + table(["Your setup", "Max rebate"], [
            ["Battery + Peak Saver (with or without solar)", "$5,000"], ["Battery + solar, no Peak Saver", "$1,500"], ["Battery only, no Peak Saver", "$0"], ["Any Tesla battery", "$0"]])
        + "<p>The rebate is also capped at 50% of installed cost. A 10 kWh battery works out to $5,000 at $500/kWh.</p>",
        "<h2>What Peak Saver asks of you</h2><p>During winter peaks (November to March), BC Hydro can draw on your battery for events up to four hours long. You can opt out of an event, but opting out of more than half may cost you that season's reward. In return, Peak Saver pays a $500 enrollment reward and $250 each winter for a battery.</p>",
        "<h2>Don't miss the 14-day window</h2><p>BC Hydro's terms say you must enroll within 14 calendar days of the in-service date for the higher rebate, and no exceptions are granted for late enrollment. Put it in your calendar, and ask your installer to confirm it's done. <a href=\"/blog/peak-saver-14-day-window-3500-mistake/\">More on the 14-day rule</a>.</p>",
        "<h2>Which batteries qualify?</h2><p>Only batteries on BC Hydro's qualified product list, at least 5 kWh, installed by an HPCN member contractor. Check the list before you buy; it changes.</p>",
    ],
    faqs=[("How do I get the $5,000 BC Hydro battery rebate?", "Install a qualified battery with an HPCN member contractor, and enroll it in Peak Saver within 14 calendar days of the in-service date."),
          ("When do Peak Saver battery events happen?", "In winter, November to March, for up to four hours at a time. You can opt out of events."),
          ("Does Tesla Powerwall qualify?", "No. All Tesla batteries have been excluded from BC Hydro and CleanBC rebates since March 12, 2025, unless the project was applied for before that date.")],
    sources=["sb", "sb_tc", "batlist", "tesla", "peak"],
    related=[("/blog/bc-approved-home-battery-rebate/", "How to choose an approved battery"), ("/blog/bc-hydro-peak-saver-explained/", "Peak Saver, explained")],
)

P["peak-saver-14-day-window-3500-mistake"] = dict(
    eyebrow="Critical deadline", title="Peak Saver 14-Day Rule: The $3,500 Battery Mistake",
    desc="BC Hydro's battery rebate drops from $5,000 to $1,500 if you don't enroll in Peak Saver within 14 calendar days of in-service. How to avoid it.",
    crumb="Peak Saver 14-day rule",
    body=[
        short("To get BC Hydro's full <strong>$5,000</strong> battery rebate, you must enroll the battery in Peak Saver within <strong>14 calendar days of its in-service date</strong>. Miss it and a solar-paired battery gets <strong>$1,500</strong> at most; a battery-only system gets nothing. BC Hydro says it grants no exceptions for late enrollment."),
        "<h2>Why this costs people $3,500</h2><p>A 10 kWh battery earns $500/kWh, so $5,000 with Peak Saver. Without Peak Saver, the cap is $1,500. The gap is $3,500, lost by missing one form in a two-week window.</p>",
        "<h2>How to not miss it</h2><ol><li>Before install, ask your contractor who will handle Peak Saver enrollment, and get it in writing.</li><li>Write down the in-service date the day your system goes live.</li><li>Set a reminder for day 7, not day 14.</li><li>Save the enrollment confirmation with your rebate paperwork.</li></ol>",
        "<h2>What Peak Saver asks of you</h2><p>Winter events, November to March, up to four hours each. You can opt out, but skipping more than half may cost you that season's $250 reward.</p>",
    ],
    faqs=[("How long do I have to enroll my battery in Peak Saver?", "14 calendar days from the in-service date, to qualify for the higher rebate."),
          ("Can BC Hydro make an exception if I enroll late?", "BC Hydro's rebate terms say no exceptions are granted for late enrollment.")],
    sources=["sb_tc", "sb", "peak"],
    related=[("/blog/bc-hydro-peak-saver-battery-rebate-5000-vs-1500/", "$5,000 vs $1,500 battery rebate"), ("/blog/bc-hydro-peak-saver-explained/", "Peak Saver, explained")],
)

P["bc-hydro-rebate-deadlines-2026"] = dict(
    eyebrow="Deadlines", title="BC Hydro Rebate Deadlines 2026: Key Dates",
    desc="Key 2026 dates for BC home rebates: the Oct 31 heat pump bonus, CleanBC's July 6 change, RS 2289 on July 1, and the 14-day Peak Saver rule.",
    crumb="BC Hydro rebate deadlines 2026",
    body=[
        short("The next date that matters: <strong>October 31, 2026</strong>, the last day to finish a heat pump install for BC Hydro's bonus of up to <strong>$1,000</strong> (first come, first served). Also: apply for most BC Hydro renovation rebates within <strong>six months</strong> of your invoice, and enroll a battery in Peak Saver within <strong>14 days</strong> of in-service."),
        "<h2>2026 dates at a glance</h2>" + table(["Date", "What happened or happens"], [
            ["July 1, 2026", "Net metering (RS 1289) closed to new customers; RS 2289 pays 10 cents/kWh for exports"],
            ["July 6, 2026", "CleanBC income-qualified rebates cut (heat pump max now $13,000 / $7,000 / $3,500)"],
            ["Aug 1 - Oct 31, 2026", "BC Hydro heat pump bonus of up to $1,000 for installs completed in this window"],
            ["Sept 14 - Oct 31, 2026", "City of Nanaimo zero-interest retrofit loan intake"],
            ["October 2026", "Free Mysa/Sinopé thermostats for BC Hydro baseboard homes start"],
            ["November - March", "Peak Saver event season"]]),
        "<h2>Deadlines that repeat</h2><ul><li><strong>6 months:</strong> apply for BC Hydro heat pump, insulation, window and water heater rebates within six months of the invoice.</li><li><strong>14 days:</strong> enroll a new battery in Peak Saver within 14 calendar days of its in-service date for the $5,000 cap.</li><li><strong>Before install:</strong> solar and battery need an accepted self-generation application before you install.</li><li><strong>180 days:</strong> EV charger rebate applications.</li></ul>",
        "<h2>Contractor rules</h2><p>BC Hydro's heat pump, insulation, solar and battery rebates all require a Home Performance Contractor Network (HPCN) member. Ask for their membership before you sign.</p>",
    ],
    faqs=[("When does the BC Hydro heat pump bonus end?", "Installs must be completed by October 31, 2026. It's up to $1,000, first come, first served."),
          ("How long do I have to apply for a BC Hydro rebate?", "Six months from the invoice date for most home renovation rebates. For EV chargers, 180 days.")],
    sources=["bch_hp", "esp", "rs2289", "sb_tc", "thermo", "nanaimo", "bch_ev"],
    related=[("/blog/cleanbc-rebate-changes-july-2026/", "CleanBC changes July 2026"), ("/blog/bc-net-metering-ended-self-generation-rate-2026/", "Net metering ended")],
)

P["heat-pump-or-solar-bc"] = dict(
    eyebrow="Decision guide", title="Heat Pump or Solar First in BC? An Honest Answer",
    desc="Heat pump or solar first in BC? For most homes with electric or oil heat, the heat pump. How the 2026 rebates and rates change the choice.",
    crumb="Heat pump or solar first?",
    body=[
        short("For most BC homes with <strong>electric baseboards, an electric furnace or oil heat</strong>, do the <strong>heat pump first</strong>: it cuts the biggest bill, it adds cooling, and the rebate is up to $4,000 (or much more if income-qualified). Solar makes more sense after, sized to your new, lower use. Since July 2026, exported solar earns only 10 cents/kWh, so oversizing solar doesn't pay."),
        "<h2>Rebates side by side</h2>" + table(["", "Heat pump", "Solar (+ battery)"], [
            ["BC Hydro", "Up to $4,000 (from electric heat), + up to $1,000 bonus to Oct 31, 2026", "$1,000/kW up to $5,000; battery up to $5,000 with Peak Saver"],
            ["Income-qualified (CleanBC)", "Up to $13,000 from gas/oil/propane; $5,000 from electric (Level 1)", "None"],
            ["FortisBC areas", "Up to $4,000; $12,000 income-qualified", "No BC Hydro solar rebate"]]),
        "<h2>Why the heat pump usually wins first</h2><ul><li>Heating is usually the biggest part of a BC home's energy bill.</li><li>A heat pump makes each unit of electricity go further than baseboards.</li><li>It adds summer cooling.</li><li>Solar sized after the heat pump fits your real new use.</li></ul>",
        "<h2>When solar might come first</h2><ul><li>You already have a heat pump.</li><li>You want backup power (solar plus an approved battery).</li><li>You heat with gas and don't qualify for the income-based rebate, so a heat pump has no rebate for you right now.</li></ul>",
        "<p>We don't quote a single payback number, because it depends on your bills and your home. Ask installers to show the math using your last 12 months of bills.</p>",
    ],
    faqs=[("Should I get a heat pump or solar first in BC?", "For most homes with electric or oil heat, the heat pump first. Then size solar to your new, lower use."),
          ("Can I get both rebates?", "Yes. BC Hydro's heat pump and solar rebates are separate programs and you can claim both if you qualify.")],
    sources=["bch_hp", "sb", "rs2289", "esp"],
    related=[("/blog/is-bc-hydro-solar-rebate-worth-it/", "Is the BC Hydro solar rebate worth it?"), ("/blog/heat-pump-rebate-guide-bc-2026/", "BC heat pump rebates 2026")],
)

TESLA_TXT = ("As of <strong>March 12, 2025</strong>, all Tesla products (Powerwall 2 and 3, Tesla chargers and inverters) are <strong>not eligible</strong> for BC Hydro or CleanBC rebates. "
             "The only exception is a project that applied for self-generation before that date. An approved battery with Peak Saver can get up to <strong>$5,000</strong>.")

P["tesla-powerwall-bc-hydro-rebate-not-qualified-alternatives"] = dict(
    eyebrow="Battery rebate", title="Tesla Powerwall BC Hydro Rebate: Not Eligible",
    desc="Tesla Powerwall gets no BC Hydro rebate: Tesla products have been ineligible since March 12, 2025. What does qualify and how to check.",
    crumb="Powerwall and the BC Hydro rebate",
    body=[
        short(TESLA_TXT),
        "<h2>Why Powerwall gets $0</h2><p>BC Hydro's official ineligible-products page says that as of March 12, 2025, Tesla products are not eligible for CleanBC and BC Hydro rebates. That includes Powerwall 2 and Powerwall 3. It's a policy decision by BC Hydro, not a problem with how well the battery works.</p>",
        "<h2>What does qualify</h2><p>Batteries on BC Hydro's <strong>qualified product list</strong> (the current list is dated July 21, 2026). The battery must be at least 5 kWh, installed by an HPCN member contractor, and approved through a self-generation application before you install. Check the list yourself before you buy; it changes.</p>",
        "<h2>What the rebate is worth</h2>" + table(["Setup", "Max rebate"], [["Approved battery + Peak Saver", "$5,000"], ["Approved battery + solar, no Peak Saver", "$1,500"], ["Any Tesla battery", "$0"]]),
        "<h2>If you still want a Powerwall</h2><p>That's your call. It's a capable battery. Just compare the full price without any rebate against an approved battery's price minus up to $5,000. We don't publish product prices, because they change; get written quotes for both.</p>",
    ],
    faqs=[("Does Tesla Powerwall qualify for the BC Hydro battery rebate?", "No. Tesla products have not been eligible since March 12, 2025, unless the self-generation application was submitted before that date."),
          ("What batteries qualify for BC Hydro's rebate?", "Those on BC Hydro's qualified battery list, at least 5 kWh, installed by an HPCN member. Check the current list before buying.")],
    sources=["tesla", "batlist", "sb_tc", "sb"],
    related=[("/blog/bc-approved-home-battery-rebate/", "How to choose an approved battery"), ("/blog/bc-hydro-peak-saver-battery-rebate-5000-vs-1500/", "$5,000 vs $1,500 battery rebate")],
)

P["tesla-powerwall-mistake"] = dict(
    eyebrow="Battery", title="Why Your Neighbour's Powerwall Got No BC Rebate",
    desc="Tesla batteries lost BC Hydro and CleanBC rebate eligibility on March 12, 2025. Why a Powerwall gets $0 in BC and how to check a battery first.",
    crumb="The Powerwall rebate mistake",
    body=[
        short(TESLA_TXT),
        "<h2>How it happens</h2><p>Powerwall is the best-known home battery, so many people ask for it by name. In BC, choosing any Tesla battery means no BC Hydro rebate. Some quotes still don't mention this.</p>",
        "<h2>How to avoid it</h2><ol><li>Check the battery model against BC Hydro's qualified product list.</li><li>Confirm your contractor is an HPCN member.</li><li>Get your self-generation application accepted before install.</li><li>Enroll in Peak Saver within 14 days of in-service for the $5,000 cap.</li></ol>",
    ],
    faqs=[("When did Tesla batteries stop qualifying in BC?", "March 12, 2025."), ("Is any Tesla product eligible?", "No. BC Hydro lists Tesla batteries, chargers and inverters as ineligible, with exceptions only for applications made before March 12, 2025.")],
    sources=["tesla", "batlist", "sb_tc"],
    related=[("/blog/tesla-powerwall-bc-hydro-rebate-not-qualified-alternatives/", "Powerwall and the BC Hydro rebate"), ("/blog/bc-approved-home-battery-rebate/", "How to choose an approved battery")],
)

P["tesla-powerwall-vs-eguana-evolve"] = dict(
    eyebrow="Battery comparison", title="Tesla Powerwall vs Eguana Evolve in BC",
    desc="Tesla Powerwall vs Eguana Evolve for BC homes: which can get the BC Hydro rebate, and what to compare before you buy.",
    crumb="Powerwall vs Eguana Evolve",
    body=[
        short("The big difference in BC is the rebate. <strong>Tesla Powerwall</strong> gets <strong>$0</strong> from BC Hydro (Tesla products have been ineligible since March 12, 2025). An <strong>Eguana Evolve</strong> or any other battery on BC Hydro's qualified list can get up to <strong>$5,000</strong> with Peak Saver. Check the current list for the exact model before you buy."),
        "<h2>What to compare</h2>" + table(["", "Tesla Powerwall", "Eguana Evolve"], [
            ["BC Hydro rebate", "$0 (Tesla excluded)", "Up to $5,000 with Peak Saver, if the model is on the qualified list"],
            ["Made by", "Tesla (US)", "Eguana Technologies (Calgary, Alberta)"],
            ["Specs", "Check Tesla's current spec sheet", "Check Eguana's current spec sheet"]]),
        "<p>Compare usable capacity (kWh), continuous power (kW), warranty years and throughput, and whether the battery can back up the circuits you care about. Get those from each maker's current spec sheet and your written quote.</p>",
        "<h2>Rebate rules for any battery</h2><ul><li>$500/kWh, up to $5,000 with Peak Saver (enroll within 14 days of in-service), or $1,500 paired with solar without it.</li><li>At least 5 kWh, on the qualified list, installed by an HPCN member.</li></ul>",
    ],
    faqs=[("Does Eguana Evolve qualify for the BC Hydro rebate?", "Check BC Hydro's current qualified battery list for the exact model. Qualified batteries can get up to $5,000 with Peak Saver."),
          ("Does Powerwall qualify?", "No. Tesla products have been ineligible for BC Hydro and CleanBC rebates since March 12, 2025.")],
    sources=["tesla", "batlist", "sb_tc"],
    related=[("/blog/bc-approved-home-battery-rebate/", "How to choose an approved battery"), ("/blog/tesla-powerwall-bc-hydro-rebate-not-qualified-alternatives/", "Powerwall and the BC Hydro rebate")],
)

P["mitsubishi-vs-daikin-heat-pump-bc-cost"] = dict(
    eyebrow="Heat pump brands", title="Mitsubishi vs Daikin Heat Pump in BC: Rebates",
    desc="Mitsubishi vs Daikin heat pumps in BC: both can qualify for the same rebates if the model is on the list. What actually matters when choosing.",
    crumb="Mitsubishi vs Daikin in BC",
    body=[
        short("The <strong>rebate doesn't depend on the brand</strong>. A Mitsubishi or Daikin model gets the same BC Hydro rebate (up to $4,000 from electric heat) or CleanBC amount if that exact model is on the eligible list and properly sized. Choose on the model's cold-weather output, the installer's experience and local service, not the logo."),
        "<h2>Rebates are the same for both</h2><ul><li><strong>BC Hydro:</strong> up to $4,000 whole home / $1,500 partial, replacing electric heat. The model must be on BC Hydro's list: variable-speed, AHRI number, HSPF2 8.5+, SEER2 15.2+.</li><li><strong>CleanBC (income-qualified):</strong> up to $13,000 / $7,000 / $3,500 from gas, oil or propane.</li><li><strong>FortisBC areas:</strong> up to $4,000; must be NEEP cold-climate certified for whole home.</li></ul>",
        "<h2>What to compare between two quotes</h2><ol><li><strong>Heating output at cold temperatures</strong> (look up the exact model on the NEEP cold-climate list).</li><li><strong>Sizing:</strong> did the installer do a heat load calculation?</li><li><strong>Warranty</strong> and who does service locally.</li><li><strong>Total price</strong> for the same scope.</li></ol>",
        "<p>For a deeper brand comparison, see <a href=\"/blog/heat-pump-brands-comparison-mitsubishi-daikin-bosch/\">Mitsubishi vs Daikin vs Bosch</a>.</p>",
    ],
    faqs=[("Do Mitsubishi and Daikin get the same BC rebate?", "Yes, if the specific model is on the eligible list and sized correctly. Rebates are not brand-based."),
          ("Which is better for northern BC?", "Compare the exact models' heating output at low temperatures on the NEEP cold-climate list, and plan for backup heat on the coldest days.")],
    sources=["bch_hp", "esp", "fb_hp"],
    related=[("/blog/heat-pump-brands-comparison-mitsubishi-daikin-bosch/", "Mitsubishi vs Daikin vs Bosch"), ("/blog/heat-pump-rebate-guide-bc-2026/", "BC heat pump rebates 2026")],
)

P["smart-thermostat-peak-saver-optimization"] = dict(
    eyebrow="Peak Saver", title="Smart Thermostats and Peak Saver in BC (2026)",
    desc="Which smart thermostats work with BC Hydro Peak Saver (line-voltage baseboard only), the $100 + $50 rewards, and the free Mysa/Sinopé offer from Oct 2026.",
    crumb="Smart thermostats and Peak Saver",
    body=[
        short("BC Hydro's Peak Saver thermostat rewards are for <strong>line-voltage baseboard thermostats</strong> like <strong>Mysa</strong> and <strong>Sinopé</strong>: <strong>$100</strong> to enroll and <strong>$50</strong> each winter. From October 2026, baseboard-heated BC Hydro customers can get up to <strong>five free</strong> Mysa or Sinopé thermostats, already enrolled. Ecobee and Nest don't qualify, because they don't control baseboards."),
        "<h2>How Peak Saver works for thermostats</h2><ul><li>Events run November to March, up to four hours each.</li><li>Your thermostat turns the heat down slightly during an event. You can opt out.</li><li>Opting out of more than half the events may cost you that season's reward.</li></ul>",
        "<h2>Getting the most from it</h2><ol><li>Pre-heat: many people raise the temperature a little before the usual 4-9 p.m. winter peak.</li><li>Keep doors closed in rooms you're heating.</li><li>Opt out only when you really need to, so you keep your seasonal reward.</li></ol>",
        "<h2>Not on baseboards?</h2><p>If you have a furnace or heat pump, BC Hydro's thermostat rewards don't apply. FortisBC electric customers with central electric heat can get up to $150 for a connected thermostat.</p>",
    ],
    faqs=[("Which thermostats qualify for BC Hydro Peak Saver?", "Line-voltage baseboard thermostats such as Mysa and Sinopé. Ecobee and Nest don't qualify."),
          ("How much does Peak Saver pay for a thermostat?", "$100 to enroll and $50 each winter. The free thermostats from October 2026 pay $50 a season, or $100 if income-qualified.")],
    sources=["thermo", "peak", "fb_thermo"],
    related=[("/blog/smart-thermostat-comparison-nest-ecobee-honeywell-mysa/", "Smart thermostat comparison"), ("/blog/bc-hydro-peak-saver-explained/", "Peak Saver, explained")],
)

P["stack-bc-hydro-greener-homes"] = dict(
    eyebrow="Stacking", title="How to Stack BC Rebates in 2026: Real Example",
    desc="How BC home rebates stack in 2026 now that Greener Homes is closed: BC Hydro solar, battery, heat pump and insulation, plus income-qualified CleanBC.",
    crumb="Stacking BC rebates 2026",
    body=[
        short("You can stack rebates that cover <strong>different upgrades</strong>: for example, BC Hydro solar (up to $5,000), battery with Peak Saver (up to $5,000), a heat pump replacing electric heat (up to $4,000) and insulation (by area, e.g. up to $900 for the attic). The federal Greener Homes Grant is closed. You can't claim two rebates for the same heat pump."),
        "<h2>A worked example (BC Hydro, electric baseboards)</h2>" + table(["Upgrade", "Rebate", "Rule"], [
            ["Whole-home heat pump", "Up to $4,000 (+ up to $1,000 if done by Oct 31, 2026)", "Replaces electric heat; HPCN"],
            ["Attic insulation, 1,000 sq. ft., +R40", "$800", "$0.02 x R x sq. ft., max $900"],
            ["Multi-upgrade bonus", "Up to $2,000", "More than one upgrade"],
            ["Solar, 5 kW", "$5,000", "$1,000/kW, max 50% of cost"],
            ["Battery, 10 kWh + Peak Saver", "$5,000", "Enroll within 14 days"]])
        + "<p>Your amounts depend on your home and quotes. A gas-heated home would not get the BC Hydro heat pump rebate; it would need to qualify by income for CleanBC.</p>",
        "<h2>What's closed</h2><ul><li>Federal Greener Homes Grant (closed).</li><li>The general CleanBC fuel-switching rebate for non-income-qualified homes (ended April 11, 2025).</li></ul>",
    ],
    faqs=[("Can I combine BC Hydro and CleanBC rebates?", "For different upgrades, yes. For the same heat pump, you get one primary heating rebate."),
          ("Is Canada Greener Homes still open?", "The Greener Homes Grant is closed. Check canada.ca for any current federal program.")],
    sources=["bch_hp", "bch_ins", "sb", "sb_tc", "esp"],
    related=[("/blog/bc-hydro-vs-fortisbc-rebates-which-better/", "BC Hydro vs FortisBC rebates"), ("/blog/insulation-rebates-bc-stack-federal-provincial/", "BC insulation rebates 2026")],
)

P["trane-carrier-heat-pumps-bc"] = dict(
    eyebrow="Heat pump brands", title="Trane and Carrier Heat Pumps in BC: Rebates",
    desc="Can a Trane or Carrier heat pump get BC rebates? Yes, if the exact model is on the eligible list. What to check before you sign.",
    crumb="Trane and Carrier heat pumps in BC",
    body=[
        short("Yes, a <strong>Trane or Carrier</strong> heat pump can get the same BC rebates as any other brand, as long as the <strong>exact model</strong> is on the eligible list and installed by a qualifying contractor. Rebates are based on the model's ratings, not the brand name."),
        "<h2>What the model needs</h2><ul><li><strong>BC Hydro:</strong> variable-speed compressor, AHRI reference number, HSPF2 of 8.5 or more, SEER2 of 15.2 or more, and on BC Hydro's eligible list.</li><li><strong>FortisBC whole-home:</strong> NEEP cold-climate certified.</li><li><strong>CleanBC:</strong> SEER2 15.2 and HSPF2 8.5 (Region IV), variable speed, at least 1 ton.</li></ul>",
        "<h2>What to ask the installer</h2><ol><li>The AHRI number for the full outdoor + indoor match.</li><li>The heat load calculation.</li><li>Where parts come from and how fast they can get them.</li><li>Whether they're an HPCN member (needed for BC Hydro).</li></ol>",
    ],
    faqs=[("Do Trane heat pumps qualify for BC Hydro rebates?", "Only specific models that meet BC Hydro's criteria and are on its eligible list. Check the AHRI number."),
          ("Is brand important for the rebate?", "No. The rebate depends on the model's ratings and the install, not the brand.")],
    sources=["bch_hp", "fb_hp", "esp"],
    related=[("/blog/heat-pump-brands-comparison-mitsubishi-daikin-bosch/", "Mitsubishi vs Daikin vs Bosch"), ("/blog/heat-pumps-explained-bc/", "Heat pumps explained")],
)

P["water-heater-buying-guide-bc"] = dict(
    eyebrow="Buying guide", title="BC Water Heater Guide 2026: Tank, Tankless, Heat Pump",
    desc="Tank vs tankless vs heat pump water heaters in BC, and the 2026 rebates: $1,000 from BC Hydro or FortisBC, more if income-qualified.",
    crumb="Water heater buying guide",
    body=[
        short("Only <strong>heat pump water heaters</strong> get the main BC rebates. BC Hydro pays up to <strong>$1,000</strong> when you replace an electric water heater (FortisBC pays $1,000 in its electric areas). Income-qualified homes can get up to <strong>$3,500</strong> through CleanBC. Standard tanks and tankless units don't get these rebates."),
        "<h2>The three types</h2>" + table(["Type", "Rebate", "Good to know"], [
            ["Standard tank (gas or electric)", "None", "Cheapest to buy; highest to run if electric"],
            ["Tankless", "None of the main rebates", "Gas units may need a bigger gas line"],
            ["Heat pump water heater", "Up to $1,000 (BC Hydro/FortisBC, from electric); CleanBC up to $3,500 if income-qualified", "Needs space and airflow; cools the room it's in"]]),
        "<h2>Rebate rules</h2><ul><li>The unit must be Tier 2 or higher on NEEA's Advanced Water Heater Specification list.</li><li>BC Hydro and FortisBC: must replace an existing electric storage tank that is your primary water heater; licensed contractor; apply within six months.</li><li>CleanBC (income-qualified): $3,500 from fossil fuel at any level; from electric, $3,500 at Level 1 and $2,800 at Level 2.</li></ul>",
        "<h2>Is it worth it?</h2><p>If you have an electric tank, usually yes: a heat pump water heater uses much less electricity for the same hot water. Get quotes and ask where it will go, because it needs space around it.</p>",
    ],
    faqs=[("How much is the BC Hydro heat pump water heater rebate?", "Up to $1,000 when replacing an electric water heater with a qualifying heat pump model."),
          ("Does a tankless water heater get a BC rebate?", "Not from the BC Hydro or CleanBC heat pump water heater rebates.")],
    sources=["bch_hpwh", "esp"],
    related=[("/blog/insulation-buying-guide-bc/", "Insulation buying guide"), ("/blog/heat-pump-rebate-guide-bc-2026/", "BC heat pump rebates 2026")],
)

P["windows-buying-guide-bc"] = dict(
    eyebrow="Buying guide", title="BC Windows Guide 2026: Double vs Triple Pane",
    desc="Double vs triple pane, vinyl vs fiberglass windows in BC, and the 2026 rebate: $100 per window or door up to $2,000 (U-factor 1.22 or less).",
    crumb="Windows buying guide",
    body=[
        short("BC Hydro and FortisBC pay <strong>$100 per window or door, up to $2,000</strong>, if each unit has a <strong>U-factor of 1.22 W/m²·K or less</strong> and a licensed contractor installs it. The City of Vancouver is excluded. Windows are pricey for the energy they save, so replace them when they're failing, and do insulation first if you can."),
        "<h2>Double vs triple pane</h2><p>Triple-pane windows usually reach lower U-factors and feel warmer in cold climates, but cost more. In mild coastal areas, a good double-pane low-E window often meets the 1.22 rule. Check the label: the U-factor, not the pane count, decides the rebate.</p>",
        "<h2>Frame materials</h2><ul><li><strong>Vinyl:</strong> most common and usually lowest cost.</li><li><strong>Fiberglass:</strong> stiffer and stable in heat and cold; usually costs more.</li><li><strong>Wood or clad:</strong> nice look, more upkeep.</li></ul>",
        "<h2>Rebate rules</h2><ul><li>$100 each, up to $2,000.</li><li>U-factor 1.22 or less; certified by CSA, Intertek, Labtest, QAI or NFRC.</li><li>Replacing existing windows or doors; no skylights.</li><li>Licensed contractor; apply within six months.</li><li>Not in the City of Vancouver.</li></ul>",
        "<p>We don't list per-window prices, because they vary a lot. Get two or three quotes that show the U-factor for each unit.</p>",
    ],
    faqs=[("How much is the BC window rebate?", "$100 per window or door, up to $2,000, from BC Hydro or FortisBC."),
          ("Do triple-pane windows get a bigger rebate?", "No. Any qualifying window gets $100. The rule is the U-factor (1.22 or less).")],
    sources=["bch_win", "fb_win"],
    related=[("/blog/window-doors-replacement-rebates-bc-guide/", "BC window and door rebates"), ("/blog/insulation-buying-guide-bc/", "Insulation buying guide")],
)

P["insulation-buying-guide-bc"] = dict(
    eyebrow="Buying guide", title="BC Insulation Guide 2026: Types and Rebates",
    desc="Blown-in fiberglass vs cellulose vs spray foam for BC homes, and how the 2026 BC Hydro and FortisBC insulation rebates are calculated.",
    crumb="Insulation buying guide",
    body=[
        short("For most BC attics, <strong>blown-in fiberglass or cellulose</strong> is the go-to. Spray foam is best for small, tricky spots like rim joists. BC Hydro (electric heat) and FortisBC pay by area and R-value added: attic up to <strong>$900</strong>, walls or basement up to <strong>$1,200</strong>."),
        "<h2>The main types</h2>" + table(["Type", "Best for", "Notes"], [
            ["Blown-in fiberglass", "Open attics", "Light, doesn't settle much"],
            ["Blown-in cellulose", "Attics, closed walls", "Denser; good at slowing air movement"],
            ["Spray foam", "Rim joists, crawlspaces, air sealing", "Costs more per sq. ft.; seals air leaks"],
            ["Rigid board", "Basement walls, exterior sheathing", "Often used during renos or re-siding"]]),
        "<h2>How the rebate is calculated</h2>" + INS,
        "<h2>What to ask your installer</h2><ol><li>Existing and final R-value, in writing.</li><li>Will they air seal before insulating?</li><li>Are they an HPCN member (needed for BC Hydro)?</li><li>Will they include photos you need for the rebate?</li></ol>",
    ],
    faqs=[("How much is the BC Hydro attic insulation rebate?", "$0.02 x R-value added x square feet, up to $900."),
          ("Does CleanBC pay for insulation in 2026?", "Not in the July 2026 Energy Savings Program rules. Use BC Hydro or FortisBC.")],
    sources=["bch_ins", "fb_ins", "esp"],
    related=[("/blog/insulation-rebates-bc-stack-federal-provincial/", "BC insulation rebates 2026"), ("/blog/windows-buying-guide-bc/", "Windows buying guide")],
)


# ---------------------------------------------------------------------------------------------
def render(slug, p):
    parts = [f'<main class="hpr-post">',
             f'  <div class="hpr-eyebrow">{p["eyebrow"]}</div>',
             f'  <h1>{html.escape(p["title"])}</h1>',
             f'  <p class="hpr-meta">By <a href="/about">Sam Menard</a> &middot; Updated {TODAY_H}</p>']
    parts += p["body"]
    parts.append("<h2>What to do next</h2>" if not any("What to do next" in b for b in p["body"]) else "")
    if "What to do next" not in "".join(p["body"]):
        parts.append("<ol><li>Check who your electric utility is.</li><li>Check whether your income qualifies for CleanBC.</li><li>Get quotes from qualified contractors and apply on time.</li></ol>")
    parts.append(g.faq_html(p["faqs"]))
    if p.get("lead"):
        parts.append(p["lead"])
    parts.append(CTA)
    parts.append(g.sources_line(p["sources"]))
    parts.append(g.related(p["related"]))
    parts.append("</main>\n\n")
    return "\n".join(x for x in parts if x)


def apply(slug, p):
    f = ROOT / "blog" / slug / "index.html"
    t = f.read_text()
    esc = html.escape
    title, desc = p["title"], p["desc"]
    t = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", t, count=1, flags=re.S)
    t = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(desc)}">', t, count=1)
    t = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc(title)}">', t, count=1)
    t = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{esc(desc)}">', t, count=1)
    pub = "2026-07-01"
    for m in reversed(list(re.finditer(r'<script type="application/ld\+json">(.*?)</script>\s*', t, re.S))):
        d = json.loads(m.group(1))
        typ = d.get("@type")
        if typ in ("Article", "BlogPosting", "FAQPage", "HowTo"):
            pub = d.get("datePublished", pub)
            t = t[:m.start()] + t[m.end():]
        elif typ == "BreadcrumbList":
            for it in d.get("itemListElement", []):
                if it.get("position") == 3:
                    it["name"] = p["crumb"]
            t = t[:m.start()] + g.jld(d) + "\n" + t[m.end():]
    art = {"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc,
           "datePublished": pub, "dateModified": g.TODAY,
           "author": {"@type": "Person", "name": "Sam Menard", "url": "https://homepowerrebate.com/about"},
           "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": "https://homepowerrebate.com"},
           "mainEntityOfPage": f"https://homepowerrebate.com/blog/{slug}/"}
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": g.strip_tags(q), "acceptedAnswer": {"@type": "Answer", "text": g.strip_tags(a)}} for q, a in p["faqs"]]}
    i = t.find('<script type="application/ld+json">')
    if i < 0:
        i = t.find("</head>")
    t = t[:i] + g.jld(art) + "\n" + g.jld(faq) + "\n" + t[i:]
    for cid, css in (('id="bcblog-css"', g.CSS), ('id="bcblog-post-css"', CSS)):
        if cid not in t:
            t = t.replace("</head>", css + "\n</head>", 1)
    t = re.sub(r'(<nav class="hpr-breadcrumb".*?<li aria-current="page">).*?(</li>)', lambda m: m.group(1) + esc(p["crumb"]) + m.group(2), t, count=1, flags=re.S)
    marker = "<!-- CANONICAL-BREADCRUMB-END -->"
    s = t.index(marker) + len(marker)
    fend = t.index("<!-- CANONICAL-FOOTER-START")
    js = re.search(r"<script>\s*/\* CANONICAL-NAV-FOOTER-JS-START", t[s:fend])
    e = s + js.start() if js else fend
    region = t[s:e]
    lead = ""
    if p.get("keep_lead"):
        m = re.search(r'<div id="insulation-lead" class="lead-card">.*?</form>\s*</div>\s*</div>', region, re.S)
        if m:
            lead = m.group(0)
            lead = lead.replace("we'll connect you with a vetted, HPCN-certified installer in your city who'll quote the job and handle the rebate paperwork for you.",
                                "we'll show you top-rated local insulation installers, ranked by Google reviews. Free for homeowners.")
            lead = lead.replace("Get Matched With an Installer &rarr;", "Compare top-rated installers &rarr;")
        # keep the lead-form script
        sm = re.search(r"<script>\s*\(function \(\) \{\s*var WORKER.*?</script>", region, re.S)
        lead_js = sm.group(0) if sm else ""
    else:
        lead_js = ""
    p2 = dict(p, lead=lead)
    t = t[:s] + "\n\n" + render(slug, p2) + (lead_js + "\n\n" if lead_js else "") + t[e:]
    f.write_text(t)


def main():
    for slug, p in P.items():
        apply(slug, p)
    print(f"rewrote {len(P)} pages")


if __name__ == "__main__":
    main()
