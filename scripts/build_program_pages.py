#!/usr/bin/env python3
"""Program guides for the most-searched rebate programs: /programs/<slug>/.

People search the program name ("bc hydro rebates", "nys clean heat", "mass save") more than
"rebates in my city". Every amount comes from data/verified-facts/*.json with its official source;
recent changes come from rebate-tracker/changes.json. Re-run after the monthly check.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell, AUTHOR  # noqa: E402

e = html.escape
BASE = "https://homepowerrebate.com"
TRACK = json.loads((ROOT / "rebate-tracker" / "changes.json").read_text())
CHECKED = TRACK["checked"]
CHECKED_H = date.fromisoformat(CHECKED).strftime("%B %-d, %Y")

PROGRAMS = {
    "bc-hydro-rebates": {
        "name": "BC Hydro rebates", "region": "BC", "hub": "/ca/bc/", "rank_region": "bc",
        "title": "BC Hydro Rebates 2026: Every Offer, Amount and Rule",
        "desc": "All BC Hydro rebates in 2026: heat pumps up to $4,000, solar up to $5,000, batteries up to $5,000, Peak Saver credits and free thermostats. Rules and official sources.",
        "h1": "BC Hydro Rebates 2026: What They Pay and How to Qualify",
        "short": "BC Hydro pays up to $4,000 for a heat pump that replaces electric heat (plus a bonus up to $1,000 for installs done by October 31, 2026), up to $5,000 for solar, and up to $5,000 for a battery if you join Peak Saver. Baseboard-heated homes can get free smart thermostats. You must be a BC Hydro customer; FortisBC customers aren't eligible.",
        "rows": [
            ("Heat pump, whole home", "Up to $4,000", "Replacing electric heat; covers 100% of heating at -5°C; HPCN installer.", "https://www.bchydro.com/powersmart/residential/rebates-programs/home-renovation/renovating-heating-system.html"),
            ("Heat pump, partial", "$1,500", "Covers at least 50% of heating; replacing electric heat.", "https://www.bchydro.com/powersmart/residential/rebates-programs/home-renovation/renovating-heating-system.html"),
            ("Heat pump bonus", "Up to $1,000", "Installs completed August 1 to October 31, 2026.", "https://www.bchydro.com/powersmart/residential/rebates-programs/home-renovation/renovating-heating-system.html"),
            ("Solar panels", "$1,000 per kW, up to $5,000", "Max 50% of cost; technical acceptance before you install.", "https://app.bchydro.com/accounts-billing/electrical-connections/customer-generation/solar-battery-rebates.html"),
            ("Home battery", "$500 per kWh: up to $1,500, or $5,000 with Peak Saver", "Max 50% of cost; on the qualified list. Tesla gets $0.", "https://app.bchydro.com/accounts-billing/electrical-connections/customer-generation/solar-battery-rebates.html"),
            ("Peak Saver", "Battery $500 then $250 a winter; thermostat $100 then $50", "Bill credits for joining winter peak events.", "https://www.bchydro.com/powersmart/residential/rebates-programs/peak-saver/enroll-smart-home-devices.html"),
            ("Smart thermostats", "Free, up to 5", "Baseboard heat; from October 2026.", "https://news.gov.bc.ca/releases/2026ECS0037-000794"),
        ],
        "steps": ["Check your bill: you must be a BC Hydro customer (FortisBC customers use FortisBC's rebates).",
                  "For a heat pump, hire an installer registered with the Home Performance Contractor Network (HPCN).",
                  "For solar or a battery, get BC Hydro's technical acceptance before anything is installed.",
                  "Apply after the work is done, with your invoice, while funding lasts."],
        "faq": [("Does a Tesla Powerwall qualify for the BC Hydro rebate?", "No. Tesla products have been ineligible since March 12, 2025, so a Powerwall gets $0 from the battery rebate. It can still earn Peak Saver credits."),
                ("Can I get the BC Hydro heat pump rebate if I heat with gas?", "No. BC Hydro's heat pump rebate is for replacing electric heat. Homes switching from gas, oil or propane can look at CleanBC's income-qualified rebates."),
                ("I'm in Kelowna. Can I get BC Hydro rebates?", "Only if BC Hydro is your electric utility. FortisBC electric customers aren't eligible for BC Hydro rebates and use FortisBC's own offers.")],
        "keys": ["BC Hydro", "net metering", "Peak Saver"],
        "related": [("/programs/cleanbc-rebates/", "CleanBC income-qualified rebates"), ("/batteries/", "Home battery guides"), ("/smart-thermostats/", "Smart thermostat rebates")],
    },
    "cleanbc-rebates": {
        "name": "CleanBC rebates", "region": "BC", "hub": "/ca/bc/", "rank_region": "bc",
        "title": "CleanBC Rebates 2026: Heat Pumps up to $13,000 (Income-Qualified)",
        "desc": "CleanBC's Energy Savings Program in 2026: $13,000, $7,000 or $3,500 to switch from gas, oil or propane to a heat pump, a $3,000 northern top-up, and up to $5,000 from electric heat.",
        "h1": "CleanBC Heat Pump Rebates 2026 (Income-Qualified)",
        "short": "CleanBC's Energy Savings Program is for income-qualified BC homes. Switching from gas, oil or propane to a heat pump pays $13,000, $7,000 or $3,500 depending on your income level, plus a $3,000 top-up for levels 1 and 2 in northern BC. Homes switching from electric heat can get up to $5,000 at income level 1. These rules apply to invoices from July 6, 2026.",
        "rows": [
            ("Heat pump from gas, oil or propane, level 1", "$13,000", "Central system or 3+ indoor heads.", "https://betterhomesbc.ca/wp-content/uploads/2026/07/RebateEligibilityRequirements_ESP_6July2026.pdf"),
            ("Heat pump from gas, oil or propane, level 2", "$7,000", "Central system or 3+ indoor heads.", "https://betterhomesbc.ca/wp-content/uploads/2026/07/RebateEligibilityRequirements_ESP_6July2026.pdf"),
            ("Heat pump from gas, oil or propane, level 3", "$3,500", "Central system or 3+ indoor heads.", "https://betterhomesbc.ca/wp-content/uploads/2026/07/RebateEligibilityRequirements_ESP_6July2026.pdf"),
            ("Northern top-up", "+$3,000", "Levels 1 and 2, 100 Mile House and north.", "https://betterhomesbc.ca/wp-content/uploads/2026/07/RebateEligibilityRequirements_ESP_6July2026.pdf"),
            ("Heat pump from electric heat", "Up to $5,000", "Income level 1 only.", "https://betterhomesbc.ca/wp-content/uploads/2026/07/RebateEligibilityRequirements_ESP_6July2026.pdf"),
        ],
        "steps": ["Check your income level on CleanBC's Better Homes site. The limits depend on household size.",
                  "Get quotes from a registered contractor, and ask them to confirm the rebate amount for your level.",
                  "Keep invoices dated July 6, 2026 or later; older invoices fall under the previous rules."],
        "faq": [("Is there a CleanBC heat pump rebate if I don't qualify by income?", "The Energy Savings Program is income-qualified. If you heat with electricity, BC Hydro's rebate of up to $4,000 doesn't have an income test."),
                ("Can I get $16,000 from CleanBC?", "Only at income level 1 in northern BC: $13,000 plus the $3,000 northern top-up. Most homes get less.")],
        "keys": ["CleanBC"],
        "related": [("/programs/bc-hydro-rebates/", "BC Hydro rebates"), ("/furnace-rebates/bc/", "BC furnace and AC rebates")],
    },
    "home-renovation-savings": {
        "name": "Home Renovation Savings", "region": "ON", "hub": "/ca/on/", "rank_region": "on",
        "title": "Home Renovation Savings Program 2026: Ontario Rebates Explained",
        "desc": "Ontario's Home Renovation Savings Program in 2026: heat pumps up to $12,000, solar and battery up to $10,000, insulation up to $7,700, $125 thermostats. What it pays and how to apply.",
        "h1": "Ontario Home Renovation Savings Program 2026",
        "short": "The Home Renovation Savings Program is Ontario's main home energy rebate. It pays $1,250 to $2,000 per ton for a heat pump (up to $12,000), up to $5,000 each for solar and a battery, up to $7,700 for insulation with an energy assessment, and $125 for a smart thermostat. Some rebates need an assessment before and after the work.",
        "rows": [
            ("Heat pump", "$1,250 to $2,000 per ton, up to $12,000", "Amount depends on your home and track.", "https://homerenovationsavings.ca/heat-pumps"),
            ("Heat pump, Enbridge gas customers", "$500 per ton, up to $2,000", "Active Enbridge Gas account.", "https://homerenovationsavings.ca/heat-pumps"),
            ("Solar", "$1,000 per kW, up to $5,000", "Max 50% of cost. No net-metering agreement.", "https://www.homerenovationsavings.ca/without-assessment/solar"),
            ("Battery", "$300 per kWh, up to $5,000", "Max 50% of cost.", "https://www.homerenovationsavings.ca/without-assessment/solar"),
            ("Insulation (with assessment)", "Up to $7,700", "Attic, walls, basement and more; pre- and post-work assessment.", "https://homerenovationsavings.ca/with-assessment"),
            ("Attic insulation (no assessment)", "Up to $1,250", "", "https://homerenovationsavings.ca/"),
            ("Windows and doors", "$100 per opening", "Assessment track.", "https://homerenovationsavings.ca/with-assessment"),
            ("Smart thermostat", "$125", "First thermostat rebate; claim within 60 days.", "https://homerenovationsavings.ca/without-assessment/smart-thermostat"),
            ("Gas furnace", "$0", "Not covered.", "https://homerenovationsavings.ca/"),
        ],
        "steps": ["Decide on a track: some upgrades (thermostat, attic, solar) need no assessment; bigger insulation and window rebates do.",
                  "For the assessment track, book a registered energy advisor before any work starts.",
                  "Do the work, then submit receipts (within 60 days for a thermostat) or book the post-work assessment."],
        "faq": [("Does Home Renovation Savings cover a new gas furnace?", "No. Gas furnaces get $0. Heat pumps, insulation, windows and thermostats are covered."),
                ("Can I take the solar rebate and keep net metering?", "No. If you take the Home Renovation Savings solar rebate, you can't also sign a net-metering agreement with your utility.")],
        "keys": ["Home Renovation Savings", "RetrofitWR"],
        "related": [("/smart-thermostats/", "Smart thermostat rebates"), ("/furnace-rebates/ontario/", "Ontario furnace and AC rebates"), ("/batteries/", "Home battery guides")],
    },
    "nys-clean-heat": {
        "name": "NYS Clean Heat", "region": "NY", "hub": "/us/ny/", "rank_region": "ny",
        "title": "NYS Clean Heat 2026: Heat Pump Rebates by Utility",
        "desc": "NYS Clean Heat heat pump rebates in 2026 by utility: Con Edison, National Grid and NYSEG up to $10,000, Central Hudson up to $8,000, O&R up to $9,000. Caps, rules and PSEG Long Island.",
        "h1": "NYS Clean Heat Heat Pump Rebates 2026, by Utility",
        "short": "NYS Clean Heat is New York's heat pump rebate, paid through your electric utility. For an air-source heat pump in a single-family home, Con Edison, National Grid, NYSEG and RG&E pay up to $10,000 (more in disadvantaged communities), Orange & Rockland up to $9,000 and Central Hudson up to $8,000. You must use a participating contractor. Long Island (PSEG) runs its own program.",
        "rows": [
            ("Con Edison (NYC, Westchester)", "Up to $10,000 ($11,000 in a DAC)", "Home must be 'service adequate'.", "https://www.coned.com/en/save-money/rebates-incentives-tax-credits/rebates-incentives-tax-credits-for-residential-customers/electric-heating-and-cooling-technology-for-renters-homeowners/save-on-a-central-air-source-heat-pump"),
            ("National Grid (upstate)", "Up to $10,000 ($12,000 in a DAC)", "Buffalo, Syracuse, Albany.", "https://cleanheat.ny.gov/assets/pdf/NYS%20Clean%20Heat%20Program%20Manual%202025_v2.pdf"),
            ("RG&E (Rochester)", "Up to $10,000", "Rochester is RG&E, not National Grid.", "https://cleanheat.ny.gov/assets/pdf/NYS%20Clean%20Heat%20Program%20Manual%202025_v2.pdf"),
            ("NYSEG", "Up to $10,000 ($11,000 in a DAC)", "", "https://cleanheat.ny.gov/assets/pdf/NYS%20Clean%20Heat%20Program%20Manual%202025_v2.pdf"),
            ("Orange & Rockland", "Up to $9,000 ($10,000 in a DAC)", "", "https://cleanheat.ny.gov/assets/pdf/NYS%20Clean%20Heat%20Program%20Manual%202025_v2.pdf"),
            ("Central Hudson", "Up to $8,000", "Poughkeepsie, Kingston, Newburgh, Beacon.", "https://cleanheat.ny.gov/assets/pdf/NYS%20Clean%20Heat%20Program%20Manual%202025_v2.pdf"),
            ("Heat pump water heater", "$1,000 to $1,250", "Clean Heat utilities.", "https://cleanheat.ny.gov/assets/pdf/NYS%20Clean%20Heat%20Program%20Manual%202025_v2.pdf"),
            ("Project cap", "70% of cost (85% in some cases)", "All Clean Heat utilities.", "https://cleanheat.ny.gov/assets/pdf/NYS%20Clean%20Heat%20Program%20Manual%202025_v2.pdf"),
            ("PSEG Long Island (separate program)", "$4,000 / $5,000 / $7,500", "NEEP-listed, whole-home sizing, participating contractor.", "https://www.psegliny.com/en/saveenergyandmoney/homeefficiency/HomeComfort/HeatPumps/Rebates"),
        ],
        "steps": ["Find your electric utility on your bill; the rebate comes from them.",
                  "Hire a NYS Clean Heat participating contractor. They usually apply for the rebate for you.",
                  "Check the quote shows the rebate taken off, and that it stays under the 70% project cap."],
        "faq": [("Is NYS Clean Heat income-qualified?", "No. It's for all electric customers of participating utilities with 1 to 4 family homes. Income-qualified New Yorkers can also look at EmPower+."),
                ("Does Long Island get NYS Clean Heat?", "No. PSEG Long Island runs its own heat pump rebates of $4,000, $5,000 or $7,500.")],
        "keys": ["Clean Heat", "Con Edison", "EmPower"],
        "related": [("/blog/new-york-empower-plus-guide/", "EmPower+ guide"), ("/rebate-tracker/", "Rebate tracker")],
    },
    "mass-save": {
        "name": "Mass Save", "region": "MA", "hub": "/us/ma/", "rank_region": "ma",
        "title": "Mass Save Rebates 2026: Heat Pumps, Insulation, Loans",
        "desc": "Mass Save rebates in 2026: heat pumps up to $8,500 (up to $16,000 income-qualified), 75-100% off insulation, $750 heat pump water heaters, 0% HEAT Loan up to $25,000.",
        "h1": "Mass Save Rebates 2026: What You Can Get",
        "short": "Mass Save pays up to $8,500 for an air-source heat pump, or up to $16,000 (sometimes no cost) for income-qualified homes. Insulation is 75% to 100% off after a free home energy assessment, heat pump water heaters get $750, and the 0% HEAT Loan covers up to $25,000. It's for Eversource, National Grid, Unitil and Cape Light Compact customers, not municipal light plant towns.",
        "rows": [
            ("Air-source heat pump", "Up to $8,500", "Standard rebate. Install in 2026, apply by February 28, 2027.", "https://goclean.masscec.com/homeowners/air-source-heat-pumps/"),
            ("Heat pump, income-qualified", "Up to $16,000 or no cost", "Moderate-income and income-eligible tiers.", "https://goclean.masscec.com/homeowners/air-source-heat-pumps/"),
            ("Ground-source heat pump", "$13,500, up to $25,000", "", "https://web.archive.org/web/20260716095731/https://www.masssave.com/residential/rebates-offers-services/heating-and-cooling/heat-pumps/ground-source-heat-pumps"),
            ("Home energy assessment", "Free", "Owners and renters.", "https://goclean.masscec.com/homeowners/weatherization/"),
            ("Insulation and air sealing", "75% to 100% off", "100% generally for income-qualified homes.", "https://goclean.masscec.com/homeowners/weatherization/"),
            ("Heat pump water heater", "$750", "", "https://goclean.masscec.com/homeowners/heat-pump-water-heater/"),
            ("HEAT Loan", "0%, up to $25,000", "Up to 7 years.", "https://goclean.masscec.com/homeowners/air-source-heat-pumps/"),
            ("Battery (ConnectedSolutions)", "About $1,375 a year for a 5 kW battery", "Paid for summer peak events.", "https://goclean.masscec.com/homeowners/battery-storage/"),
        ],
        "steps": ["Check your electric utility: Mass Save covers Eversource, National Grid, Unitil and Cape Light Compact, not municipal light plant towns.",
                  "Book the free home energy assessment; it unlocks insulation discounts and the HEAT Loan.",
                  "Use an installer who works with Mass Save, and apply by February 28, 2027 for 2026 installs."],
        "faq": [("Why did my town not qualify for Mass Save?", "Towns with a municipal light plant (like Belmont, Concord or Holyoke) aren't in Mass Save. They have their own programs and the state's MLP Z-Loan."),
                ("Did Mass Save cut its rebates?", "Regulators cut the 2025-2027 Mass Save budget by $500 million in February 2025. Heat pump rebates of up to $8,500 are still offered.")],
        "keys": ["Mass Save", "Boston"],
        "related": [("/blog/mass-save-home-energy-assessment-explained/", "Mass Save home energy assessment"), ("/batteries/", "Home battery guides")],
    },
    "efficiency-nova-scotia": {
        "name": "Efficiency Nova Scotia rebates", "region": "NS", "hub": "/ca/ns/", "rank_region": "ns",
        "title": "Efficiency Nova Scotia Rebates 2026: What's Open and What Closed",
        "desc": "Efficiency Nova Scotia rebates in 2026: up to $5,000 through a Home Energy Assessment, $800 heat pump water heaters, $300-$500 per ton heat pumps, and which programs closed (OHPA, SolarHomes).",
        "h1": "Efficiency Nova Scotia Rebates 2026",
        "short": "Most Efficiency Nova Scotia rebates now go through a Home Energy Assessment ($199): any homeowner can get up to $5,000 for the upgrades it recommends, including $300 to $500 per ton for a new heat pump and up to $750 for attic insulation. Heat pump water heaters get $800, instantly at the store. Moderate-income homes that don't heat with electricity can add up to $5,000 more. The oil-to-heat-pump program and SolarHomes are closed.",
        "rows": [
            ("Home Energy Assessment rebates", "Up to $5,000", "Assessment fee $199. Do the upgrades between the first and final assessment, within 12 months.", "https://assets.ctfassets.net/hro74sf4x6k2/3WUCMiBurFYsS5L8O0Dg0K/e980fabca778e3ed2e7c2a0b4ff8e56a/Home-Energy-Assessment-Rebate-Guide-Aug-2026.pdf"),
            ("Heat pump, ductless", "$300 per ton", "New capacity only; replacing a heat pump doesn't qualify. Qualifying model, certified installer.", "https://assets.ctfassets.net/hro74sf4x6k2/3WUCMiBurFYsS5L8O0Dg0K/e980fabca778e3ed2e7c2a0b4ff8e56a/Home-Energy-Assessment-Rebate-Guide-Aug-2026.pdf"),
            ("Heat pump, central ducted", "$500 per ton", "Newly added capacity.", "https://assets.ctfassets.net/hro74sf4x6k2/3WUCMiBurFYsS5L8O0Dg0K/e980fabca778e3ed2e7c2a0b4ff8e56a/Home-Energy-Assessment-Rebate-Guide-Aug-2026.pdf"),
            ("Heat pump water heater", "$800", "ENERGY STAR. Instant at participating stores, or through the assessment if you didn't take the instant rebate.", "https://www.efficiencyns.ca/programs-rebates/instant-rebates"),
            ("Attic insulation to R-50", "Up to $750", "Walls up to $1,500; basement walls up to $1,200.", "https://assets.ctfassets.net/hro74sf4x6k2/3WUCMiBurFYsS5L8O0Dg0K/e980fabca778e3ed2e7c2a0b4ff8e56a/Home-Energy-Assessment-Rebate-Guide-Aug-2026.pdf"),
            ("Smart thermostat (electric heat)", "$45 instant, or free installed", "Free installation is for electrically heated homes.", "https://www.efficiencyns.ca/programs-rebates/free-product-installation"),
            ("Moderate Income Rebate", "Up to $5,000 more", "Homes mainly heated with oil, propane or wood, not electricity. Income limits apply; pre-approval needed.", "https://www.efficiencyns.ca/programs-rebates/moderate-income-rebate"),
            ("Oil to Heat Pump Affordability", "Closed", "Closed to new applicants July 2, 2026.", "https://www.efficiencyns.ca/programs-rebates/oil-to-heat-pump-affordability-program"),
            ("SolarHomes", "Closed to homeowners", "Stopped taking applications April 17, 2025.", "https://www.efficiencyns.ca/programs-rebates/solarhomes"),
        ],
        "steps": ["Book a Home Energy Assessment ($199) before you start. Upgrades done before it don't count.",
                  "Do the recommended upgrades within 12 months, using qualifying products and a certified installer for heat pumps.",
                  "Book the final assessment. The rebate cheque usually arrives within about 90 days.",
                  "Buying a heat pump water heater or thermostat? Take the instant rebate at the store instead."],
        "faq": [("Can I still get a rebate for replacing my old heat pump in Nova Scotia?", "Not through the Home Energy Assessment. Its heat pump rebate is only for newly added capacity; replacement heat pumps aren't eligible."),
                ("Is there a solar rebate in Nova Scotia in 2026?", "Not for homeowners. SolarHomes closed to homeowners in April 2025. Halifax homeowners can finance solar through Solar City."),
                ("Is there a battery rebate in Nova Scotia?", "We found no current Efficiency Nova Scotia battery rebate as of our last check.")],
        "keys": ["Efficiency Nova Scotia", "OHPA", "Moderate Income", "SolarHomes", "HARP"],
        "related": [("/heat-pump-water-heater/nova-scotia/", "Heat pump water heaters in Nova Scotia"), ("/ca/ns/halifax/", "Halifax rebates"), ("/ca/ns/cape-breton/", "Cape Breton rebates")],
    },
    "bc-hydro-peak-saver": {
        "name": "BC Hydro Peak Saver", "region": "BC", "hub": "/ca/bc/", "rank_region": "bc",
        "title": "BC Hydro Peak Saver: Is It Worth It? (2026 Credits by Device)",
        "desc": "Is BC Hydro Peak Saver worth it? What it pays for a battery ($500 then $250 a winter), thermostat, EV charger and water heater, what you give up, and why it unlocks the $5,000 battery rebate.",
        "h1": "BC Hydro Peak Saver: Is It Worth It?",
        "short": "For most people, yes. Peak Saver pays bill credits for letting BC Hydro briefly dial back a device on winter evenings, up to 4 hours at a time, and you can opt out of any event. A home battery earns $500 to join and about $250 each winter, and joining raises the battery rebate from $1,500 to up to $5,000. Baseboard thermostats earn $100, then $50 a winter.",
        "rows": [
            ("Home battery", "$500 to join, then $250 a winter", "Also unlocks the battery rebate of up to $5,000 (instead of $1,500).", "https://www.bchydro.com/powersmart/residential/rebates-programs/peak-saver/enroll-smart-home-devices.html"),
            ("Smart thermostat (baseboard)", "$100 to join, then $50 a winter", "Line-voltage thermostats like Mysa and Sinope. Ecobee and Nest don't qualify.", "https://www.bchydro.com/powersmart/residential/rebates-programs/peak-saver/enroll-smart-home-devices.html"),
            ("EV charger", "$250 to join, then $50 a winter", "", "https://www.bchydro.com/powersmart/residential/rebates-programs/peak-saver/enroll-smart-home-devices.html"),
            ("Water heater controller", "$100 to join, then $50 a winter", "", "https://www.bchydro.com/powersmart/residential/rebates-programs/peak-saver/enroll-smart-home-devices.html"),
            ("Free thermostats", "Up to 5, free", "Baseboard-heated homes, from October 2026, enrolled in Peak Saver.", "https://news.gov.bc.ca/releases/2026ECS0037-000794"),
        ],
        "steps": ["Check your device is on BC Hydro's eligible list (a battery must also be on the rebate's qualified list).",
                  "Enroll through BC Hydro's Peak Saver page or your device's app.",
                  "During events (November to March, up to 4 hours), your device eases off. Opt out any time you need to."],
        "faq": [("Is the BC Hydro Peak Saver battery rebate worth it?", "Usually. Joining Peak Saver raises the battery rebate from up to $1,500 to up to $5,000, and adds $500 plus about $250 a winter, roughly $3,000 over 10 years. The trade-off: during some winter evening events your battery sends power back instead of saving all of it for an outage."),
                ("Will Peak Saver leave my house cold?", "Events last up to 4 hours and you can opt out of any of them. Thermostats usually lower the temperature a few degrees, not shut off."),
                ("Can a Tesla Powerwall join Peak Saver?", "Tesla batteries get no BC Hydro battery rebate. Check BC Hydro's current device list for Peak Saver credits.")],
        "keys": ["Peak Saver"],
        "related": [("/programs/bc-hydro-rebates/", "All BC Hydro rebates"), ("/batteries/", "Home battery guides"), ("/smart-thermostats/", "Smart thermostat rebates")],
    },
    "alberta-energy-rebates": {
        "name": "Alberta energy rebates", "region": "AB", "hub": "/ca/ab/", "rank_region": "ab",
        "title": "Alberta Energy Rebates 2026: What's Actually Available (ENMAX, EPCOR, CEIP)",
        "desc": "Alberta home energy rebates in 2026, checked against official sources: no ENMAX or ATCO heat pump rebate, Calgary and Edmonton CEIP financing, Red Deer's $50 thermostat rebate, EPCOR Peak Rewards.",
        "h1": "Alberta Energy Rebates 2026: What's Really Available",
        "short": "Alberta has few home energy rebates in 2026. We found no current ENMAX, ATCO, EPCOR or FortisAlberta heat pump or solar rebate on any official site. What exists: Clean Energy Improvement Program (CEIP) financing repaid on your property tax (Calgary's intake reopens winter 2026/27), a $50 smart thermostat rebate in Red Deer, EPCOR's Peak Rewards pilot, and free upgrades for income-qualified Calgarians.",
        "rows": [
            ("ENMAX / ATCO / EPCOR / FortisAlberta heat pump or solar rebate", "None found", "Amounts you see online come from installer blogs, not the utilities.", ""),
            ("Calgary CEIP (financing)", "Up to $50,000, up to 20 years", "Repaid on your property tax bill. Intake closed until winter 2026/2027.", "https://www.calgary.ca/environment/programs/clean-energy-improvement-program.html"),
            ("CEIP in other towns", "Varies", "Edmonton, Lethbridge, St. Albert and others. Not Red Deer or Fort McMurray.", "https://ceip.abmunis.ca/residential/residential-program-locations/"),
            ("Red Deer smart thermostat", "$50", "ENERGY STAR certified; one per utility account.", "https://www.reddeer.ca/city-services/environment-and-conservation/your-home/energy-efficiency/smart-thermostat-rebate/"),
            ("EPCOR Peak Rewards (pilot)", "$50 card, then $25 a season", "Thermostat you already own, central AC, select Edmonton neighbourhoods.", "https://www.epcor.com/ca/en/ab/edmonton/conservation/incentives/peak-rewards-thermostats.html"),
            ("Calgary Home Upgrades Program", "Free upgrades", "Income-qualified; furnace, insulation, air sealing. Waitlist.", "https://www.homeupgradesprogram.ca/calgary"),
            ("Oil to Heat Pump Affordability (federal)", "Closed in Alberta", "Last day to apply was July 31, 2026.", "https://natural-resources.canada.ca/energy-efficiency/home-energy-efficiency/canada-greener-homes-initiative/canada-greener-homes-initiative"),
        ],
        "steps": ["Check whether your town offers CEIP and when intake opens.",
                  "If a quote mentions a 'utility rebate', ask the installer for the official program link before you count on it.",
                  "In Red Deer, keep your thermostat receipt and apply in the same calendar year."],
        "faq": [("Does ENMAX have a heat pump rebate?", "Not that we could find. As of our last check, no official ENMAX, ATCO, EPCOR or FortisAlberta page offers a heat pump or solar rebate. Ask for the program link if a quote lists one."),
                ("Is there a smart thermostat rebate in Alberta?", "Only locally: Red Deer pays $50, and EPCOR's Peak Rewards pilot pays $50 plus $25 a season in select Edmonton neighbourhoods."),
                ("Can I still get the Oil to Heat Pump grant in Alberta?", "No. The last day for Alberta residents to apply was July 31, 2026.")],
        "keys": ["CEIP", "Alberta", "Calgary", "Edmonton", "Red Deer"],
        "related": [("/ca/ab/calgary/", "Calgary rebates"), ("/ca/ab/edmonton/", "Edmonton rebates"), ("/smart-thermostats/", "Smart thermostat rebates")],
    },
    "federal-tax-credits-2026": {
        "name": "Federal tax credits", "region": "US", "hub": "/us/", "rank_region": "ny",
        "title": "Heat Pump and Solar Tax Credits 2026: Federal Credits Ended. What's Left",
        "desc": "The 30% federal tax credits for heat pumps (25C) and solar and batteries (25D) ended December 31, 2025. What still pays in 2026: NYS Clean Heat, Mass Save, SMUD, LADWP, Efficiency Vermont and more.",
        "h1": "Heat Pump and Solar Tax Credits in 2026: What Replaced Them",
        "short": "The federal tax credits are gone for 2026 installs. The 30% Energy Efficient Home Improvement Credit (25C, heat pumps and insulation) and the 30% Residential Clean Energy Credit (25D, solar, batteries and geothermal) don't apply to anything installed after December 31, 2025. State and utility rebates are now the main help: up to $10,000 or more for a heat pump in New York, up to $8,500 in Massachusetts, and utility rebates in California and Vermont.",
        "rows": [
            ("Federal 25C (heat pumps, insulation, windows)", "Ended", "Only for improvements made through December 31, 2025.", "https://www.irs.gov/credits-deductions/energy-efficient-home-improvement-credit"),
            ("Federal 25D (solar, batteries, geothermal)", "Ended", "Not available for property placed in service after December 31, 2025.", "https://www.irs.gov/credits-deductions/residential-clean-energy-credit"),
            ("New York: NYS Clean Heat", "Up to $10,000 (more in a DAC)", "Through your electric utility; participating contractor. Long Island: PSEG $4,000 to $7,500.", "https://cleanheat.ny.gov/"),
            ("New York: EmPower+", "Free up to $12,000 to $14,000", "Low-income homes; moderate income gets 50% up to $6,000 to $7,000.", "https://www.nyserda.ny.gov/All-Programs/EmPower-New-York-Program"),
            ("Massachusetts: Mass Save", "Up to $8,500 (up to $16,000 income-qualified)", "Plus 0% HEAT Loan and 75% to 100% off insulation.", "https://goclean.masscec.com/homeowners/air-source-heat-pumps/"),
            ("Massachusetts: state solar tax credit", "15% of cost", "State income tax credit; still available.", "https://goclean.masscec.com/homeowners/solar-electricity/"),
            ("California: SMUD (Sacramento)", "Heat pump up to $3,000; water heater up to $4,000", "Plus up to $2,000 Go Electric bonus when replacing gas.", "https://www.smud.org/Rebates-and-Savings-Tips/Rebates-for-My-Home"),
            ("California: LADWP (Los Angeles)", "Heat pump up to $2,500 per ton", "Water heater up to $2,500.", "https://www.ladwp.com/residential-services/assistance-programs/consumer-rebate-program"),
            ("California: TECH Clean California and HEEHRA", "Fully reserved", "Waitlist only.", "https://techcleanca.com/incentives/single-family-incentives/"),
            ("Vermont: Efficiency Vermont", "Up to $2,200 ducted heat pump", "Plus income bonuses and up to $2,000 from Green Mountain Power for income-eligible homes.", "https://www.efficiencyvermont.com/rebates/list/heat-pump-heating-cooling-system"),
        ],
        "steps": ["If your install finished in 2025, you can still claim 25C or 25D on your 2025 tax return with IRS Form 5695.",
                  "For 2026 installs, look up your electric utility and state program; that's where the money is now.",
                  "Many rebates need a participating contractor or approval before work starts. Check before you sign.",
                  "Be wary of quotes that still subtract a 30% federal tax credit for a 2026 install."],
        "faq": [("Is there a federal tax credit for heat pumps in 2026?", "No. The 25C credit covers improvements made through December 31, 2025 only. For 2026, look at state and utility rebates."),
                ("Can I still get the 30% solar tax credit?", "Not for a system installed after December 31, 2025. The 25D credit ended early under the 2025 federal budget law (the One Big Beautiful Bill)."),
                ("I installed a heat pump in December 2025. Can I still claim it?", "Yes, if it was installed by December 31, 2025. Claim it on your 2025 return with Form 5695."),
                ("What replaced the federal tax credits?", "Nothing federal for most homeowners. State and utility programs like NYS Clean Heat, Mass Save and Efficiency Vermont are now the main rebates.")],
        "keys": ["25C", "25D", "tax credit", "federal"],
        "related": [("/programs/nys-clean-heat/", "NYS Clean Heat"), ("/programs/mass-save/", "Mass Save"), ("/us/ca/", "California rebates"), ("/us/vt/", "Vermont rebates")],
    },
    "peco-rebates": {
        "name": "PECO rebates", "region": "PA", "hub": "/us/pa/", "rank_region": "pa",
        "title": "PECO Rebates 2026: Heat Pump, Water Heater, Thermostat and Appliance Amounts",
        "desc": "What PECO pays in 2026, from PECO's own program pages: heat pumps $200 to $300, mini-splits $150 to $300, heat pump water heater $350, smart thermostat $25 to $50. Rules and deadlines.",
        "h1": "PECO Rebates 2026: What They Pay and How to Apply",
        "short": "PECO pays $200 to $300 for an air source heat pump, $150 to $300 for a ductless mini-split, $350 for an ENERGY STAR heat pump water heater and $25 to $50 for a smart thermostat, for PECO electric customers. Apply within 90 days of buying or installing. Natural gas rebate levels drop on October 1, 2026. We found no PECO rebate for a home EV charger.",
        "rows": [
            ("Air source heat pump", "$200 or $300", "$200 at 15.2 to 17.0 SEER2; $300 at 17.1 SEER2 or higher. Both need 11.0 EER2 and 7.8 HSPF2 or better. PECO electric customers.", "https://www.peco.com/ways-to-save/for-your-home/rebates-discounts/heating-cooling-rebates"),
            ("Ductless mini-split heat pump", "$150 or $300", "$150 at 15.2 to 17.0 SEER2; $300 at 17.1 SEER2 or higher. Same EER2 and HSPF2 minimums.", "https://www.peco.com/ways-to-save/for-your-home/rebates-discounts/heating-cooling-rebates"),
            ("Central air conditioning", "$150 or $200", "$150 at 15.2 to 15.9 SEER2; $200 at 16.0 SEER2 or higher; 12.0 EER2 or better.", "https://www.peco.com/ways-to-save/for-your-home/rebates-discounts/heating-cooling-rebates"),
            ("Heat pump or AC maintenance", "$50 heat pump, $25 AC", "Tune-up rebate.", "https://www.peco.com/ways-to-save/for-your-home/rebates-discounts/heating-cooling-rebates"),
            ("Smart thermostat", "$50 instant or $25 after install", "PECO also lists $25 to $50 on its appliance page.", "https://www.peco.com/ways-to-save/for-your-home/rebates-discounts/appliance-rebates"),
            ("Heat pump water heater", "$350", "ENERGY STAR certified, electric. New equipment in a PECO electric home.", "https://www.peco.com/ways-to-save/for-your-home/rebates-discounts/appliance-rebates"),
            ("Appliances", "$10 to $25 each", "ENERGY STAR clothes washer $25, dryer $15, refrigerator $20, dehumidifier $25, air purifier $25, room air conditioner $10.", "https://www.peco.com/ways-to-save/for-your-home/rebates-discounts/appliance-rebates"),
            ("Natural gas furnace, boiler and water heater", "Lower from October 1, 2026", "PECO's page says natural gas rebate levels are reduced for requests submitted on or after October 1, 2026. Check PECO for the new amounts.", "https://www.peco.com/ways-to-save/for-your-home/rebates-discounts/heating-cooling-rebates"),
        ],
        "steps": ["Check your bill: you must be a PECO electric or natural gas customer, and the rebate must match your fuel.",
                  "Buy or install ENERGY STAR certified equipment that meets the efficiency numbers above.",
                  "Keep a paid receipt showing the model number, manufacturer, price and date.",
                  "Apply within 90 days of the purchase or installation. If you took an instant discount at the store, you can't claim the same rebate again."],
        "faq": [("How much is the PECO heat pump rebate?", "PECO pays $200 or $300 for an air source heat pump and $150 or $300 for a ductless mini-split, depending on the efficiency rating. It's for PECO electric customers."),
                ("Does PECO give a rebate for a heat pump water heater?", "Yes. PECO pays $350 for an ENERGY STAR certified heat pump water heater in a home with PECO electric service."),
                ("Is there a PECO rebate for a home EV charger?", "We did not find one on PECO's rebate pages. Check PECO's EV pages before you buy, because offers can change."),
                ("How long do I have to apply?", "PECO says the application must be received within 90 days of the purchase or installation.")],
        "keys": ["PECO"],
        "related": [("/programs/federal-tax-credits-2026/", "2026 tax credits"), ("/us/pa/philadelphia/", "Philadelphia rebates"), ("/smart-thermostats/", "Smart thermostat rebates")],
    },
    "ppl-electric-rebates": {
        "name": "PPL Electric rebates", "region": "PA", "hub": "/us/pa/", "rank_region": "pa",
        "title": "PPL Electric Rebates 2026: Heat Pump, Water Heater, Insulation and Thermostat",
        "desc": "PPL Electric's 2026 rebates from its program portal: heat pumps $225 to $500, heat pump water heater $400, smart thermostat $50 or $100, insulation up to $500. Income-based amounts and deadlines.",
        "h1": "PPL Electric Rebates 2026: What They Pay and How to Apply",
        "short": "PPL Electric pays $225 or $325 for an air source heat pump, $225 for a mini-split, $500 for a ground source heat pump, $400 for a heat pump water heater and $50 or $100 for a smart thermostat. It also lists insulation rebates up to $500 and air sealing up to $150. Several rebates have two amounts, and which one you get depends on your income.",
        "rows": [
            ("Air source heat pump", "$225 or $325", "Two amounts listed; PPL's Check Best Offers tool shows which applies to you.", "https://ppl.clearesult.com/rebates"),
            ("Mini-split heat pump", "$225", "Ductless heat pump.", "https://ppl.clearesult.com/rebates"),
            ("Ground source heat pump", "$500", "", "https://ppl.clearesult.com/rebates"),
            ("Heat pump water heater", "$400", "ENERGY STAR certified.", "https://ppl.clearesult.com/rebates"),
            ("Smart thermostat", "$50 or $100", "ENERGY STAR certified; two amounts, based on your offer.", "https://ppl.clearesult.com/rebates"),
            ("Attic, exterior wall or rim joist insulation", "Up to $200 or $500", "Two levels; Check Best Offers shows which applies to you.", "https://ppl.clearesult.com/rebates"),
            ("Air sealing", "Up to $150", "", "https://ppl.clearesult.com/rebates"),
            ("Refrigerator, dehumidifier, air purifier", "$50 or $75; $25 or $50; $25", "ENERGY STAR certified.", "https://ppl.clearesult.com/rebates"),
            ("WRAP", "Free", "Free in-home energy survey and products for income-eligible customers.", "https://pplelectric.com/site/ways-to-save/rebates-and-incentives"),
        ],
        "steps": ["Confirm PPL Electric delivers your power. It does even if you buy from another supplier.",
                  "Sign in and use PPL's Check Best Offers tool to see which amount you qualify for.",
                  "Install ENERGY STAR certified equipment, or hire a contractor for insulation and air sealing.",
                  "Apply online or by mail. PPL says applications are generally due within 180 days of installation."],
        "faq": [("How much is the PPL Electric heat pump rebate?", "PPL lists $225 or $325 for an air source heat pump, $225 for a mini-split and $500 for a ground source heat pump. The amount depends on your offer, which PPL's Check Best Offers tool shows."),
                ("Does PPL give a heat pump water heater rebate?", "Yes. PPL lists $400 for an ENERGY STAR certified heat pump water heater."),
                ("How long do I have to apply for a PPL rebate?", "PPL says applications are generally due within 180 days of installation. Equipment installed on May 31, 2026 or earlier is no longer eligible."),
                ("Is there a PPL EV charger rebate?", "PPL lists Optimized EV Charging as a program, but its rebate page shows no dollar amount. Ask PPL for details before you buy a charger.")],
        "keys": ["PPL"],
        "related": [("/programs/federal-tax-credits-2026/", "2026 tax credits"), ("/us/pa/allentown/", "Allentown rebates"), ("/insulation-rebates/", "Insulation rebates by region")],
    },
    "xcel-energy-colorado-rebates": {
        "name": "Xcel Energy Colorado rebates", "region": "CO", "hub": "/us/co/", "rank_region": "co",
        "title": "Xcel Energy Colorado Rebates 2026: Heat Pump, Water Heater, Thermostat and EV Charger",
        "desc": "Xcel Energy Colorado rebates from Xcel's own 2026 rebate sheet: heat pumps $750 per heating ton, water heater $750, thermostat $50, EV charger up to $500. Gas-home bonuses from Oct 1, 2026.",
        "h1": "Xcel Energy Colorado Rebates 2026: What They Pay and How to Qualify",
        "short": "Xcel Energy pays $750 per heating ton for a cold-climate heat pump, $500 for a mini-split, $750 for a heat pump water heater and $50 for a smart thermostat, plus up to $500 for a home EV charger. Homes heated with Xcel natural gas get bonuses that double most heat pump amounts from October 1, 2026. Installs must be invoiced by December 31, 2026, and funding is first come, first served.",
        "rows": [
            ("Cold-climate air source heat pump (ducted)", "$750 per heating ton at 5°F; $1,500 with gas bonus", "15.2 SEER2, 10 EER2, 8.1 HSPF2 and strong output at 5°F. Xcel participating contractor.", "https://xcelnew.my.salesforce.com/sfc/p/1U0000011ttV/a/R300000VaKHh/LOhy1LXjBUFmC3Wtx5nXUMWKdLrID1qbswR8JUCuM8Q"),
            ("Air source heat pump (ducted)", "$300 per cooling ton; $600 with gas bonus", "15.2 SEER2, 11.7 EER2, 7.8 HSPF2.", "https://xcelnew.my.salesforce.com/sfc/p/1U0000011ttV/a/R300000VaKHh/LOhy1LXjBUFmC3Wtx5nXUMWKdLrID1qbswR8JUCuM8Q"),
            ("Mini-split (non-ducted) heat pump", "$500", "Standard or cold-climate models. You can install it yourself and still qualify.", "https://xcelnew.my.salesforce.com/sfc/p/1U0000011ttV/a/R300000VaKHh/LOhy1LXjBUFmC3Wtx5nXUMWKdLrID1qbswR8JUCuM8Q"),
            ("Ground source heat pump", "$1,100 per heating ton; $2,200 with gas bonus", "16 EER2, 3.3 COP, closed loop.", "https://xcelnew.my.salesforce.com/sfc/p/1U0000011ttV/a/R300000VaKHh/LOhy1LXjBUFmC3Wtx5nXUMWKdLrID1qbswR8JUCuM8Q"),
            ("Heat pump water heater", "$750; $1,500 with gas bonus", "ENERGY STAR, 3.3 UEF.", "https://xcelnew.my.salesforce.com/sfc/p/1U0000011ttV/a/R300000VaKHh/LOhy1LXjBUFmC3Wtx5nXUMWKdLrID1qbswR8JUCuM8Q"),
            ("Smart thermostat", "$50; or $100 credit plus $25 a year in AC Rewards", "ENERGY STAR rated. Electric customers can enroll in AC Rewards.", "https://xcelnew.my.salesforce.com/sfc/p/1U0000011ttV/a/R300000VaKHh/LOhy1LXjBUFmC3Wtx5nXUMWKdLrID1qbswR8JUCuM8Q"),
            ("Attic, wall insulation and air sealing", "30% of cost, up to $500 attic, $350 wall, $400 air sealing", "Xcel gas or electric heat. Gas customers get 1.5 times the standard rebate.", "https://xcelnew.my.salesforce.com/sfc/p/1U0000011ttV/a/R300000VaKHh/LOhy1LXjBUFmC3Wtx5nXUMWKdLrID1qbswR8JUCuM8Q"),
            ("Home energy audit", "$100, $160 or $200", "Standard, blower door or infrared audit; 60% of the cost, up to those amounts.", "https://xcelnew.my.salesforce.com/sfc/p/1U0000011ttV/a/R300000VaKHh/LOhy1LXjBUFmC3Wtx5nXUMWKdLrID1qbswR8JUCuM8Q"),
            ("Home EV charger and wiring", "Up to $500; up to $2,300 income-qualified", "Enroll in Optimize Your Charge. Up to $800 in a disproportionately impacted community. First come, first served.", "https://co.my.xcelenergy.com/s/residential/ev-charging/incentives/charger-wiring-rebate"),
        ],
        "steps": ["Confirm you are an Xcel Energy electric or natural gas customer in Colorado.",
                  "For a heat pump, get a quote from an Xcel Trade Partner Network contractor, who applies the rebate for you. Mini-splits can be self-installed.",
                  "Have the work invoiced by December 31, 2026. Xcel accepts applications through September 30, 2027.",
                  "For an EV charger, enroll in Optimize Your Charge first, then apply in My Account."],
        "faq": [("How much is the Xcel Energy heat pump rebate?", "For a cold-climate ducted heat pump, $750 per heating ton at 5°F, or $1,500 per ton with the gas bonus. Mini-splits get $500. Amounts are on Xcel's 2026 rebate sheet."),
                ("Who gets the Xcel heat pump bonus?", "Homes heated with natural gas from Xcel Energy. Homes with electric heat, such as baseboards, get the standard rebate only, because bonuses ended for them on November 16, 2025."),
                ("What is the deadline for Xcel heat pump rebates?", "Installs must be invoiced by December 31, 2026, and Xcel accepts applications through September 30, 2027. Funding is limited."),
                ("Can I still get a federal tax credit for a heat pump in Colorado?", "No. The federal 25C credit ended for installs after December 31, 2025. Xcel's rebates are the main incentive now.")],
        "keys": ["Xcel"],
        "related": [("/programs/federal-tax-credits-2026/", "2026 tax credits"), ("/us/co/denver/", "Denver rebates"), ("/insulation-rebates/", "Insulation rebates by region")],
    },
}


def changes(keys, region):
    items = [x for x in TRACK["entries"] if x["region"] == region and any(k.lower() in (x["program"] + x["change"]).lower() for k in keys)]
    items.sort(key=lambda x: x["date"], reverse=True)
    return items[:4]


def page(slug, p):
    path = f"/programs/{slug}/"
    rows = "".join(f"<tr><td><b>{e(a)}</b></td><td>{e(b)}</td><td>{e(c)}{(' <a href=\"' + e(s) + '\" rel=\"nofollow noopener\" target=\"_blank\">Source</a>') if s else ''}</td></tr>"
                   for a, b, c, s in p["rows"])
    ch = changes(p["keys"], p["region"])
    ch_html = ("<h2>Recent changes</h2><ul>" + "".join(
        f'<li><b>{e(x["date"])}: {e(x["program"])}.</b> {e(x["change"])} <a href="{e(x["source"])}" rel="nofollow noopener" target="_blank">Source</a></li>' for x in ch)
        + '</ul><p><a href="/rebate-tracker/">See every rebate change</a>.</p>') if ch else ""
    rankings = f"/installers/{p['rank_region']}/"
    rank_link = (f'<a href="/installers/">top-rated installers by city</a>')
    others = [(s, o["name"]) for s, o in PROGRAMS.items() if s != slug]
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="{p['hub']}">{e(p['hub'].strip('/').split('/')[-1].upper())}</a></li><li aria-current="page">{e(p['name'])}</li></ol></nav>
<header class="hero"><div class="wrap"><h1>{e(p['h1'])}</h1>
<p>Every amount links to the official program. Last checked {CHECKED_H}.</p><p class="meta">By {e(AUTHOR['name'])}</p></div></header>
<section class="body"><div class="wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> {e(p['short'])}</p></div>
<h2>{e(p['name'])}: amounts in 2026</h2>
<div class="tw"><table><tr><th>Upgrade</th><th>Amount</th><th>Rules</th></tr>{rows}</table></div>
<p class="small">Amounts last checked {CHECKED_H} against each program's official page (linked in each row).</p>
<h2>How to apply</h2><ol>{"".join(f"<li>{e(x)}</li>" for x in p['steps'])}</ol>
{ch_html}
<h2>Find your city and an installer</h2>
<p>See the exact rebates for your city on the <a href="{p['hub']}">{e(p['hub'].strip('/').split('/')[-1].upper())} rebates page</a>, then compare {rank_link}, ranked by Google reviews. No one pays to be listed.</p>
<h2>Common questions</h2>
{"".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in p['faq'])}
<p><b>Related:</b> {" · ".join(f'<a href="{u}">{e(t)}</a>' for u, t in p['related'])}</p>
<p><b>Other program guides:</b> {" · ".join(f'<a href="/programs/{s}/">{e(n)}</a>' for s, n in others)}</p>
<p class="small">Something out of date? Email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a> and we'll check it within a week.</p>
</div></section>"""
    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": p["title"], "description": p["short"],
         "datePublished": "2026-09-29", "dateModified": CHECKED, "author": AUTHOR,
         "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE}, "mainEntityOfPage": BASE + path},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p["faq"]]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": p["hub"].strip("/").split("/")[-1].upper(), "item": BASE + p["hub"]},
            {"@type": "ListItem", "position": 3, "name": p["name"]}]},
    ]
    nav = "on" if p["region"] in ("ON",) else p["hub"].strip("/").split("/")[-1]
    out = shell(p["title"] + " | HomePowerRebate", p["desc"], path, nav, body, ld)
    out = out.replace("</style>", ".tw{overflow-x:auto;-webkit-overflow-scrolling:touch}.tw table{min-width:520px}</style>", 1)
    return path, out


def main():
    for slug, p in PROGRAMS.items():
        path, out = page(slug, p)
        f = ROOT / path.strip("/") / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(out, encoding="utf-8")
        print("Wrote", path)
    # Link each hub to its program guides (inside the HUB-TOP block's section, as its own marker block).
    by_hub = {}
    for slug, p in PROGRAMS.items():
        by_hub.setdefault(p["hub"], []).append((slug, p["name"]))
    # The federal tax-credit guide belongs on every US state hub.
    for hub in ("/us/ny/", "/us/ma/", "/us/ca/", "/us/vt/", "/us/pa/", "/us/co/"):
        by_hub.setdefault(hub, []).append(("federal-tax-credits-2026", "2026 tax credits"))
    S, E = "<!-- PROGRAM-LINKS-START -->", "<!-- PROGRAM-LINKS-END -->"
    for hub, items in by_hub.items():
        f = ROOT / hub.strip("/") / "index.html"
        s = f.read_text(encoding="utf-8")
        blk = (f'{S}<p style="max-width:880px;margin:12px auto;padding:0 20px;"><b>Program guides:</b> '
               + " · ".join(f'<a href="/programs/{sl}/">{e(n)}</a>' for sl, n in items) + f"</p>{E}")
        if S in s:
            s = re.sub(re.escape(S) + ".*?" + re.escape(E), lambda m: blk, s, count=1, flags=re.S)
        else:
            anchor = "<!-- HUB-CHANGES-END -->" if "<!-- HUB-CHANGES-END -->" in s else "<!-- HUB-TOP-END -->"
            if anchor not in s:
                continue
            s = s.replace(anchor, anchor + "\n" + blk, 1)
        f.write_text(s, encoding="utf-8")
        print("Linked", hub)


if __name__ == "__main__":
    main()
