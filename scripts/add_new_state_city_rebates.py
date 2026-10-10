#!/usr/bin/env python3
"""Add city rebate summaries for NJ, IL, WA, MN and MI to city-rebate-lookup.json (used by the lead-router emails).

Every amount comes from data/verified-facts/<state>.json (read 2026-10-06/07). A category with no verified amount is left out, so the
email never shows a number we cannot source. Amounts a fact marks "check" say they are being re-confirmed. Idempotent: rewrites only these keys.
Run, then redeploy the lead router (wrangler deploy).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "city-rebate-lookup.json"

SOLAR_NJ = "NJ Successor Solar Incentive: $77 per MWh (about 7.7 cents per kWh) in credits, plus net metering and a property tax exemption for the value the system adds"
SOLAR_IL = "Illinois Shines pays for the solar credits your system makes ($70.37 or $80.77 per credit for systems up to 10 kW, plus $20 more per credit if you own it)"
SOLAR_WA = "No cash rebate; 100% of state and local sales tax is exempt on the equipment and installation"
SOLAR_MN = "Xcel Solar*Rewards: $0.03 per kWh produced for 10 years (amount being re-confirmed)"

PSEG = {
    "utility": "PSE&G",
    "heat_pump": "Up to $10,000 ($12,000 income-qualified) for a cold-climate heat pump that replaces your fossil-fuel heat (PSE&G Clean Heat); $300 to $600 instant rebate on a standard air source heat pump",
    "solar": SOLAR_NJ,
    "battery": "Up to $5,000 instant rebate on a home battery (PSE&G GridSmart Battery Program)",
    "water_heater": "$450 or $750 (PSE&G heat pump water heater)",
    "insulation": "Free assessment and no-cost products, plus wall, ceiling and attic insulation upgrades (PSE&G Home Weatherization)",
    "thermostat": "$60 to $100, or free (PSE&G smart thermostat)",
    "ev_charger": "Up to $1,500 per charger plus up to $5,000 toward utility work (PSE&G)",
}
JCPL = {
    "utility": "JCP&L (confirm on your bill)",
    "heat_pump": "Up to $10,000 ($12,000 moderate-income) for a cold-climate heat pump that replaces fossil-fuel heat (JCP&L Clean Comfort); up to $1,000 for an air source heat pump",
    "solar": SOLAR_NJ,
    "insulation": "Up to $7,500 (JCP&L Whole Home Energy Solutions); free upgrades up to $14,000 for income-qualified households",
}
ACE = {
    "utility": "Atlantic City Electric (confirm on your bill)",
    "heat_pump": "$500 to $2,000 for a heat pump; up to $10,000 or 50% of project cost for a cold-climate heat pump that replaces fossil-fuel heat",
    "solar": SOLAR_NJ,
    "insulation": "Free for households at or below 250% of the federal poverty level (NJ Comfort Partners)",
    "thermostat": "Up to $100 for enrolling a smart thermostat (Energy Wise Rewards)",
}
COMED = {
    "utility": "ComEd",
    "heat_pump": "Instant discount of about $900 to $2,000 on a ducted air source heat pump, $500 to $1,000 on a ductless mini-split, up to $6,000 for geothermal (ComEd)",
    "solar": SOLAR_IL,
    "water_heater": "Up to $750 (ComEd heat pump water heater)",
    "thermostat": "$75 (ComEd)",
}
WA_PSE = {
    "utility": "Puget Sound Energy",
    "heat_pump": "$1,500 ($2,400 income-qualified) to replace electric resistance heat or an old heat pump; $4,000 for income-qualified gas customers",
    "solar": SOLAR_WA,
    "battery": "Up to $1,000 when you enroll, plus up to $500 a year (PSE flex batteries)",
    "water_heater": "$1,000 ($1,100 income-qualified)",
    "insulation": "Up to $3,500 attic, $5,000 walls, $5,000 floor",
    "windows": "Up to $100 per window ($200 income-qualified)",
    "thermostat": "$75 ($175 income-qualified)",
    "ev_charger": "Up to $300 ($600 plus $2,000 install if income-qualified)",
}

CITIES = {
    "nj|newark": ("Newark", "NJ", PSEG),
    "nj|jersey city": ("Jersey City", "NJ", PSEG),
    "nj|toms river": ("Toms River", "NJ", JCPL),
    "nj|atlantic city": ("Atlantic City", "NJ", ACE),
    "il|chicago": ("Chicago", "IL", {**COMED, "insulation": "Gas customers: up to $1,200 per project (Peoples Gas) or up to $3,000 by measure (Nicor Gas), depending on your gas company"}),
    "il|aurora": ("Aurora", "IL", {**COMED, "insulation": "Nicor Gas: air sealing $500 per home, attic insulation $400 (gas customers)"}),
    "il|naperville": ("Naperville", "IL", {
        "utility": "Naperville Electric",
        "heat_pump": "$900, $1,400 or $1,800 by efficiency (Naperville Electric)",
        "solar": SOLAR_IL,
        "thermostat": "$75 (Naperville Electric)",
        "insulation": "Nicor Gas: air sealing $500 per home, attic insulation $400 (gas customers); Naperville Electric's own insulation incentive is closed for 2026"}),
    "il|peoria": ("Peoria", "IL", {
        "utility": "Ameren Illinois",
        "heat_pump": "Check current amounts with Ameren Illinois (we could not confirm them)",
        "solar": SOLAR_IL,
        "insulation": "Free for income-qualified households, up to $20,000 (Illinois Home Weatherization Assistance Program)"}),
    "wa|bellevue": ("Bellevue", "WA", WA_PSE),
    "wa|seattle": ("Seattle", "WA", {
        "utility": "Seattle City Light",
        "heat_pump": "$300 to $600 instant discount from a contractor; $2,000 (free if income-eligible) to switch from oil to electric",
        "solar": SOLAR_WA,
        "water_heater": "$750",
        "thermostat": "$50"}),
    "wa|spokane": ("Spokane", "WA", {
        "utility": "Avista",
        "heat_pump": "$300 to $600 per outdoor system",
        "solar": SOLAR_WA,
        "water_heater": "$500",
        "insulation": "$1.75 per square foot (attic, floor and wall); free upgrades for income-qualifying customers",
        "windows": "Up to $225 per window; $600 per door"}),
    "wa|tacoma": ("Tacoma", "WA", {
        "utility": "Tacoma Power",
        "heat_pump": "Up to $2,000 rebate, or a loan up to $20,000",
        "solar": SOLAR_WA,
        "water_heater": "$500",
        "insulation": "Up to $2,250 rebate ($750 each for crawlspace, wall and attic)",
        "windows": "$50 to $100 per window; $200 to $400 per sliding door",
        "thermostat": "$75",
        "ev_charger": "Up to $600"}),
    "wa|vancouver": ("Vancouver", "WA", {
        "utility": "Clark Public Utilities",
        "heat_pump": "$500 to $1,250 central; $900 ductless",
        "solar": SOLAR_WA,
        "water_heater": "$1,500",
        "insulation": "$0.75 to $1.20 per square foot",
        "windows": "$6 to $10 per square foot",
        "thermostat": "$140"}),
}
XCEL_MPLS = {
    "heat_pump": "CenterPoint Energy $1,100 for a ducted heat pump replacing a gas furnace; Xcel Energy $1,500 to $2,000 for a cold-climate heat pump (amount being re-confirmed)",
    "solar": SOLAR_MN,
    "water_heater": "Xcel Energy $400 ($500 for a smart model) for a heat pump water heater",
    "insulation": "Xcel Energy 40% of project cost, up to $3,000; CenterPoint Energy up to $3,000 combined",
    "windows": "$50 per ENERGY STAR window (CenterPoint Energy)",
    "thermostat": "$50 (CenterPoint Energy and Xcel Energy; Xcel amount being re-confirmed)",
}
CITIES.update({
    "mn|minneapolis": ("Minneapolis", "MN", {"utility": "Xcel Energy and CenterPoint Energy", **XCEL_MPLS,
        "insulation": XCEL_MPLS["insulation"] + "; Minneapolis Green Cost Share up to $5,000 ($14,000 in a Green Zone)"}),
    "mn|saint paul": ("Saint Paul", "MN", {"utility": "Xcel Energy and CenterPoint Energy", **XCEL_MPLS}),
    "mn|rochester": ("Rochester", "MN", {
        "utility": "Rochester Public Utilities",
        "heat_pump": "$1,500 for a ducted heat pump; $800 to $2,200 to replace electric heat; $200 per ton for geothermal",
        "water_heater": "$400", "thermostat": "Up to $100"}),
    "mn|duluth": ("Duluth", "MN", {
        "utility": "Minnesota Power",
        "heat_pump": "$400 or $1,000 for an air source heat pump; $800 to $1,000 per ton for geothermal",
        "water_heater": "$300", "thermostat": "$50"}),
    "mi|detroit": ("Detroit", "MI", {
        "utility": "DTE Energy",
        "heat_pump": "$150 to $1,200 (DTE Energy)",
        "water_heater": "Instant discount on an ENERGY STAR heat pump water heater (amount not stated)",
        "insulation": "Up to $600 for attic insulation, plus a $250 bonus",
        "thermostat": "$50"}),
    "mi|grand rapids": ("Grand Rapids", "MI", {
        "utility": "Consumers Energy",
        "heat_pump": "$200 to $350 (Consumers Energy)",
        "insulation": "Up to $475",
        "thermostat": "$50 to $100 (Consumers' pages disagree; being re-checked)"}),
    "mi|ann arbor": ("Ann Arbor", "MI", {
        "utility": "DTE Energy and the City's A2Zero program",
        "heat_pump": "A2Zero $4,000 ($5,500 income-qualified) for a cold-climate heat pump; DTE Energy $150 to $1,200",
        "insulation": "DTE Energy up to $600 for attic insulation, plus a $250 bonus",
        "thermostat": "$50 (DTE Energy)"}),
    "mi|lansing": ("Lansing", "MI", {
        "utility": "Lansing Board of Water & Light",
        "heat_pump": "$4,000 to $5,000 for a central heat pump replacing a gas furnace and AC (Lansing BWL)",
        "thermostat": "$50"}),
})


def main():
    d = json.loads(FILE.read_text(encoding="utf-8"))
    for key, (city, region, data) in CITIES.items():
        data = dict(data)
        utility = data.pop("utility")
        d[key] = {"city": city, "region": region, "utility": utility, "categories": data, "heat_pump_rebate": data.get("heat_pump", "")}
    FILE.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(CITIES)} cities written; {len(d)} total")


if __name__ == "__main__":
    main()
