"""Offer data for the California city pages built by build_ca_pages.py. Every amount is the wording of a fact in data/verified-facts.
Add a category to a city only when a fact backs it (offer) or data/ca/coverage.json records that we read the utility's page and it does not list one."""
L = "us-ca-la-munis-"
S = "us-ca-"
SD_INTRO = "San Diego homes are served by San Diego Gas and Electric (SDG&E)."
# offer = (amount, note, [fact ids], example or None)
CITIES = {
    "los-angeles": dict(area="los-angeles", area_name="Los Angeles area", name="Los Angeles", utility="ladwp", utility_name="LADWP",
        intro="Los Angeles homes are served by the Los Angeles Department of Water and Power (LADWP), which runs its own rebates.", offers={
        "heat-pump": ("Up to $2,500 per ton", "For installs from November 1, 2025. Apply after the install, within 12 months.", [S + "11-ladwp-consumer-rebate-program"], None),
        "water-heater": ("Up to $2,500", "Apply after the install, within 12 months.", [S + "11-ladwp-consumer-rebate-program"], None),
        "windows-doors": ("$2.00 per sq ft", "LADWP does rebate ENERGY STAR windows. Apply after the install, within 12 months.", [S + "11-ladwp-consumer-rebate-program"], "Replacing 150 sq ft of window glass earns 150 x $2.00 = $300."),
        "battery": ("No general rebate", "LADWP has no general battery rebate. Households at or below 80% of area median income can get help for solar and storage through the state's SGIP equity program, which LADWP runs.", [S + "12-ladwp-sgip-rsse"], None)}),
    "glendale": dict(area="los-angeles", area_name="Los Angeles area", name="Glendale", utility="gwp", utility_name="Glendale Water and Power",
        intro="Glendale has its own utility, Glendale Water and Power (GWP), which runs its own rebates.", offers={
        "heat-pump": ("$1,000 per ton, up to $5,000", "That is for replacing a gas furnace. Replacing an existing heat pump pays $500 per ton, up to $2,500, as a bill credit. A $1,000 panel upgrade rebate is added when it is paired with a heat pump or water heater install.", [L + "7-gwp-heat-pump-hvac-replacing-gas-furnace-gas-elect", L + "8-gwp-heat-pump-hvac-replacing-an-existing-heat-pump", L + "10-gwp-panel-upgrade"], "A 3-ton system replacing a gas furnace earns 3 x $1,000 = $3,000. The $5,000 cap is reached at 5 tons."),
        "water-heater": ("$4,000", "A limited-time rebate. It must replace a gas water heater, and needs gas capping and electrical permits.", [L + "9-gwp-heat-pump-water-heater"], None),
        "appliances": ("Up to $400 each", "A heat pump dryer or an electric range replacing gas pays $400. A refrigerator or freezer pays $200 and a dishwasher $50. Apply within 12 months.", [L + "11-gwp-appliances"], None)}),
    "burbank": dict(area="los-angeles", area_name="Los Angeles area", name="Burbank", utility="bwp", utility_name="Burbank Water and Power",
        intro="Burbank has its own utility, Burbank Water and Power (BWP), which runs its own rebates.", offers={
        "heat-pump": ("$1,000 per ton, up to $2,500", "Up to $5,000 for low-income customers. It must replace natural gas heating. It covers equipment and panel, not labour.", [L + "12-bwp-heat-pump-hvac-mini-split-replacing-gas"], "A 3-ton system would earn $3,000 at $1,000 per ton, so the $2,500 cap applies."),
        "water-heater": ("$1,500", "It must replace a gas water heater.", [L + "13-bwp-electrification-other"], None),
        "ev-charger": ("Up to $500", "A smart charger pays $500 and a standard charger $200, with a panel upgrade up to $750. You must be on a time-of-use rate. Renters can apply.", [L + "14-bwp-ev-charger-rebate"], None),
        "smart-thermostats": ("Up to $75", "A rebate for an eligible smart thermostat.", [L + "15-bwp-efficiency-rebates"], None),
        "appliances": ("$200", "A heat pump dryer or induction cooktop pays $200, with higher amounts for low-income customers. They must replace gas.", [L + "13-bwp-electrification-other"], None),
        "insulation": ("Set on application", "BWP lists attic and wall insulation rebates, with the amount set on the application. We could not read a fixed per-square-foot figure.", [L + "15-bwp-efficiency-rebates"], None)}),
    "pasadena": dict(area="los-angeles", area_name="Los Angeles area", name="Pasadena", utility="pwp", utility_name="Pasadena Water and Power",
        intro="Pasadena has its own utility, Pasadena Water and Power (PWP), which runs its own rebates.", offers={
        "heat-pump": ("$170 per ton", "Add $20 per ton if you buy it in Pasadena. Apply within 180 days of purchase.", [L + "0-pwp-heat-pump-rebate"], "A 3-ton system earns 3 x $170 = $510."),
        "water-heater": ("$500", "Add $20 if you buy it in Pasadena. Apply within 180 days.", [L + "1-pwp-heat-pump-water-heater-rebate"], None),
        "ev-charger": ("Up to $600", "$600 for a Wi-Fi connected Level 2 charger and $200 for a standard one. Up to 2 per address, with a permit and professional install.", [L + "2-pwp-ev-charger-rebate"], None),
        "smart-thermostats": ("$50", "Add $10 if you buy it in Pasadena.", [L + "3-pwp-smart-thermostat-rebate"], None),
        "insulation": ("$0.10 per sq ft", "Add $0.05 per sq ft with a qualified local contractor. It must reach R-30 or higher.", [L + "4-pwp-ceiling-insulation-rebate"], "Insulating 1,500 sq ft of ceiling earns 1,500 x $0.10 = $150, or $225 with the $0.05 local contractor add-on."),
        "solar": ("$0.60 per watt", "$1.00 per watt for income-qualified households, for new or expanded rooftop systems. This is a pilot program.", [L + "5-pwp-solar-and-battery-rebate-pilot"], "A 6,000-watt system earns 6,000 x $0.60 = $3,600."),
        "battery": ("Up to $550 per kWh", "Tiered incentives through the same pilot program as solar.", [L + "5-pwp-solar-and-battery-rebate-pilot"], None),
        "appliances": ("Amounts shown after login", "PWP lists rebates for ENERGY STAR refrigerators, dishwashers, ceiling fans and room air conditioners, but shows the amounts only after you log in, so we do not quote them.", [L + "6-pwp-appliance-rebates"], None)}),
    "long-beach": dict(area="los-angeles", area_name="Los Angeles area", name="Long Beach", utility="sce", utility_name="Southern California Edison",
        intro="Long Beach is served by Southern California Edison for electricity. Its gas comes from the city's own utility, not SoCalGas.", offers={
        "ev-charger": ("Up to $4,200", "Income-qualified households only (below 80% of area median income, or on an assistance program). You must install a Level 2 charger within 180 days.", [L + "16-sce-charge-ready-home"], None),
        "smart-thermostats": ("$75 bill credit", "For enrolling an eligible smart thermostat in SCE's demand response program.", [L + "17-sce-smart-energy-program"], None)}),
    "santa-monica": dict(area="los-angeles", area_name="Los Angeles area", name="Santa Monica", utility="sce", utility_name="Southern California Edison",
        intro="Santa Monica is served by Southern California Edison.", offers={
        "ev-charger": ("Up to $4,200", "Income-qualified households only (below 80% of area median income, or on an assistance program). You must install a Level 2 charger within 180 days.", [L + "16-sce-charge-ready-home"], None),
        "smart-thermostats": ("$75 bill credit", "For enrolling an eligible smart thermostat in SCE's demand response program.", [L + "17-sce-smart-energy-program"], None)}),
}
SMUD = {
    "heat-pump": ("Up to $3,000", "A two-stage or variable-stage heat pump from a participating contractor. A Go Electric bonus adds up to $500 per eligible circuit or panel, up to $2,000, when you replace a gas furnace or gas water heater.", [S + "4-smud-heat-pump-hvac-rebate", S + "7-smud-go-electric-bonus"], None),
    "water-heater": ("Up to $4,000", "NEEA Tier III or IV models.", [S + "5-smud-heat-pump-water-heater-rebate"], None),
    "insulation": ("Up to $3,000", "Air sealing, attic insulation and ducts through a Home Performance Program contractor.", [S + "6-smud-seal-insulate"], None),
    "battery": ("$300 per kWh, up to $6,000", "A one-time enrollment incentive for approved batteries on SMUD's Solar and Storage Rate (projects submitted from September 23, 2026). There is no separate $5,400 SMUD battery rebate.", [S + "10-smud-my-energy-optimizer-partner-battery-enrollmen"], "A 13.5 kWh battery earns 13.5 x $300 = $4,050."),
    "ev-charger": ("Up to $600", "For a charger and/or circuit.", [S + "8-smud-charge-home"], None),
    "smart-thermostats": ("$50", "An instant rebate at the SMUD Energy Store.", [S + "9-smud-smart-thermostat-induction"], None),
    "appliances": ("$750", "Induction cooking: $750 when replacing gas and $100 when replacing electric.", [S + "9-smud-smart-thermostat-induction"], None),
}
for slug, n, intro in (("sacramento", "Sacramento", "Sacramento is SMUD's home city, so SMUD's rebates apply."), ("rancho-cordova", "Rancho Cordova", "Rancho Cordova is in SMUD's service area, so SMUD's rebates apply."),
                       ("folsom", "Folsom", "SMUD serves part of Folsom, so check your electric bill before you count on these amounts.")):
    CITIES[slug] = dict(area="sacramento", area_name="Sacramento area", name=n, utility="smud", utility_name="SMUD", intro=intro, offers=SMUD)
SDGE = {
    "water-heater": ("$500 (coupon)", "SDG&E's rebates page lists $500 for a heat pump water heater that replaces an electric water heater, as a retail coupon. The same page says the program's retail offerings have ended, so we do not count it as open.", [S + "24-sdge-retail-coupons"], None),
    "smart-thermostats": ("$75 (coupon)", "SDG&E's rebates page lists $75 for an ENERGY STAR smart thermostat ($40 for an Amazon model), as a retail coupon. The same page says the retail offerings have ended, so we do not count it as open.", [S + "24-sdge-retail-coupons"], None),
}
for slug, n, intro in (("san-diego", "San Diego", SD_INTRO), ("chula-vista", "Chula Vista", "Chula Vista is in SDG&E's service area (San Diego Gas and Electric)."),
                       ("escondido", "Escondido", "Escondido is in SDG&E's service area (San Diego Gas and Electric).")):
    CITIES[slug] = dict(area="san-diego", area_name="San Diego area", name=n, utility="sdge", utility_name="SDG&E", intro=intro, offers=SDGE)
CITIES["san-francisco"] = dict(area="bay-area", area_name="Bay Area", name="San Francisco", utility="cleanpowersf", utility_name="CleanPowerSF",
    intro="San Francisco's electricity comes from CleanPowerSF, which pays rebates as monthly bill credits, not as a cheque.", offers={
    "water-heater": ("Up to $1,200", "$50 off your bill each month for 24 months. You must enrol the new water heater in a load-shifting program, and the install needs a San Francisco permit. CARE and FERA customers get 12 more months.", [S + "15-cleanpowersf-hpwh-credit"], "24 months x $50 = $1,200."),
    "heat-pump": ("Up to $1,200", "$50 off your bill each month for 24 months, for installs from April 14, 2026. You must be on the EV2-A or E-ELEC electric rate.", [S + "16-cleanpowersf-hp-heating-credit"], "24 months x $50 = $1,200."),
    "appliances": ("Up to $300", "$150 for electric cooking, $300 for an electric dryer and $300 for removing your gas meter.", [S + "17-cleanpowersf-cooking-dryer-meter"], None)})
CITIES["san-jose"] = dict(area="bay-area", area_name="Bay Area", name="San Jose", utility="sjce", utility_name="San Jose Clean Energy (SJCE)",
    intro="San Jose Clean Energy (SJCE) pays cash rebates through its EcoHome program for replacing gas appliances.", offers={
    "water-heater": ("$3,000", "$4,000 in Environmental Justice communities. This includes a $500 bonus for applications from Sept 1 to Oct 31, 2026. It must replace a gas water heater, and you apply before you install.", [S + "18-sjce-ecohome-hpwh"], None),
    "heat-pump": ("$1,500", "$2,500 in Environmental Justice communities. It must replace a gas heating system, and you apply before you install.", [S + "20-sjce-ecohome-hvac"], None),
    "insulation": ("$0.75 per sq ft", "Up to $700, or $1,000 in Environmental Justice communities. It must be paired with a heat pump heating and cooling rebate.", [S + "21-sjce-ecohome-insulation"], "Insulating a 1,000 sq ft attic earns 1,000 x $0.75 = $750, but the $700 cap applies."),
    "ev-charger": ("$500", "$500 for EV circuit prewiring and $1,000 for a panel upgrade. You must also install a heat pump HVAC or water heater.", [S + "22-sjce-ecohome-prewiring-panel"], None),
    "appliances": ("$500", "$500 for dryer or cooking circuit prewiring, when you also install a heat pump HVAC or water heater.", [S + "22-sjce-ecohome-prewiring-panel"], None),
    "battery": ("Closed", "SJCE's battery rebate ($125 per kWh up to $3,250) is closed to new applications.", [S + "23-sjce-ecohome-battery"], None)})

for slug, n in (("oakland", "Oakland"), ("berkeley", "Berkeley"), ("fremont", "Fremont")):
    CITIES[slug] = dict(area="bay-area", area_name="Bay Area", name=n, utility="ava", utility_name="Ava Community Energy",
                        intro=f"{n}'s electricity supplier is Ava Community Energy.", offers={})

for slug, n in (("riverside", "Riverside"), ("san-bernardino", "San Bernardino"), ("moreno-valley", "Moreno Valley"), ("ontario", "Ontario")):
    CITIES[slug] = dict(area="inland-empire", area_name="Inland Empire", name=n, utility="rpu" if slug == "riverside" else "sce",
                        utility_name="Riverside Public Utilities" if slug == "riverside" else "Southern California Edison", intro=f"{n} home energy programs.", offers={})

CITIES["fresno"] = dict(area="fresno", area_name="Fresno", name="Fresno", utility="pge", utility_name="PG&E", hub="/us/ca/fresno/", intro="Fresno's electricity and gas come from PG&E.", offers={})
CITIES["bakersfield"] = dict(area="bakersfield", area_name="Bakersfield", name="Bakersfield", utility="pge", utility_name="PG&E", hub="/us/ca/bakersfield/", intro="Bakersfield's electricity comes from PG&E and its gas from SoCalGas.", offers={})
CITIES["roseville"] = dict(area="sacramento", area_name="Sacramento area", name="Roseville", utility="reu", utility_name="Roseville Electric Utility",
                           intro="Roseville has its own city-owned electric utility, Roseville Electric Utility, not SMUD.", offers={})
