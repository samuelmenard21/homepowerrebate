#!/usr/bin/env python3
"""Build data/rebate-sources.json: every official page a rebate figure or claim on the site depends on, for the monthly source check.
Sources: source_url of every fact in data/verified-facts, the refs of every hand-written page in data/ca/pages, and EXTRA below (pages read for context that no fact points at).
The monthly-rebate-check task re-opens each url, compares it with what the site says, and records the result. Re-run this after adding facts or pages, then `git add -f data/rebate-sources.json`."""
import json
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
REG = defaultdict(lambda: {"used_by": set(), "facts": [], "titles": set(), "last_read": ""})
EXTRA = [
    # (url, region, what to check)
    ("https://www.ladwp.com/residential-services/programs-and-rebates-residential", "CA-LADWP", "Program list: new or removed residential programs"),
    ("https://www.ladwp.com/residential-services/programs-and-rebates-residential/electric-vehicles/residential-ev-charger-rebate-program", "CA-LADWP", "EV charger rebate, meter rebate and EV rate discount"),
    ("https://www.ladwp.com/residential-services/programs-and-rebates-residential?page=1", "CA-LADWP", "Second page of the program list (EPM, feed-in tariff)"),
    ("https://www.ladbs.org/", "CA-LADWP", "Los Angeles Building and Safety permit rules"),
    ("https://pwp.cityofpasadena.net/savemoney/", "CA-PWP", "PWP program catalog: new or removed rebates"),
    ("https://pwp.cityofpasadena.net/low-income/", "CA-PWP", "Bill Payment Assistance eligibility"),
    ("https://pwp.cityofpasadena.net/netsurpluscompensation/", "CA-PWP", "Net surplus compensation rules"),
    ("https://pwp.cityofpasadena.net/solar-power-in-pasadena/", "CA-PWP", "Solar program page and PowerClerk steps"),
    ("https://pwp.cityofpasadena.net/appliancerebates/", "CA-PWP", "Appliance rebate list (amounts need login)"),
    ("https://www.cityofpasadena.net/planning/permit-center/apply-for-permit/", "CA-PWP", "Pasadena Permit Center"),
    ("https://www.glendaleca.gov/business/doing-business-with-the-city/getting-a-permit", "CA-GWP", "Glendale permit portal and fee schedule"),
    ("https://www.burbankwaterandpower.com/residential-rebates", "CA-BWP", "Thermostat, refrigerator, insulation, pool rebates"),
    ("https://www.burbankwaterandpower.com/electrify-your-home", "CA-BWP", "Electrification rebates and low-income amounts"),
    ("https://www.burbankwaterandpower.com/residential-ev-charging-stations-rebate", "CA-BWP", "EV charger and panel rebates"),
    ("https://www.sce.com/save-money/rebates-financial-assistance/rebates-sce-marketplace", "CA-SCE", "Marketplace: thermostat credit, Golden State coupons, Home Performance Plus"),
    ("https://www.sce.com/clean-energy-efficiency/electric-vehicles/rebates-rates", "CA-SCE", "Charge Ready Home, Charge Smart, EV rates"),
    ("https://www.lbutilities.org/Gas/Natural-Gas-Efficiency/Gas-Utility-Rebates", "CA-LongBeach", "Long Beach Utilities gas rebates (yearly window)"),
    ("https://www.santamonica.gov/green-building-incentives-and-installation-resources", "CA-SantaMonica", "City incentive status list (GO ZERO, HEEHRA, TECH, SGIP)"),
    ("https://www.santamonica.gov/process-explainers/how-to-electrify-your-home", "CA-SantaMonica", "City electrification guidance and QuitCarbon partnership"),
    ("https://www.smud.org/Rebates-and-Savings-Tips/Rebates-for-My-Home", "CA-SMUD", "Appliance, thermostat and induction rebates"),
    ("https://www.smud.org/en/Rebates-and-Savings-Tips/Rebates-for-My-Home/Heating-and-Cooling-Rebates", "CA-SMUD", "Heat pump amounts and published install costs"),
    ("https://www.smud.org/en/Rebates-and-Savings-Tips/Rebates-for-My-Home/Home-Appliances-and-Electronics-Rebates", "CA-SMUD", "Heat pump water heater amounts by tank size, install costs"),
    ("https://www.smud.org/Rebates-and-Savings-Tips/Improve-Home-Efficiency", "CA-SMUD", "Home Performance Program packages and eligibility"),
    ("https://www.smud.org/Going-Green/Battery-storage", "CA-SMUD", "Battery enrollment incentive and tiers (changed Sept 23, 2026)"),
    ("https://www.smud.org/Going-Green/Electric-Vehicles/Charge-at-Home-application-page", "CA-SMUD", "Charge@Home amounts"),
    ("https://www.smud.org/Going-Green/Electric-Vehicles/Charge-at-Home-application-page/Charge-at-Home-Terms-and-Conditions", "CA-SMUD", "Charge@Home terms and charger specs"),
    ("https://www.folsom.ca.us/government/community-development/building-services/instant-solar-permitting", "CA-Folsom", "Instant solar permit process and fee waivers"),
    ("https://www.cityofranchocordova.org/departments/community-development/building-and-safety/forms-and-downloads", "CA-RanchoCordova", "SolarAPP+ permitting"),
    ("https://www.cleanpowersf.org/waterheater", "CA-SF", "CleanPowerSF credits"),
    ("https://sanjosecleanenergy.org/ecohome-rebate/", "CA-SanJose", "EcoHome rebate amounts and bonus window (blocks some fetchers; use a browser)"),
    ("https://www.bayren.org/ease-home", "CA-BayArea", "BayREN EASE Home"),
    ("https://www.bayren.org/find-incentives", "CA-BayArea", "BayREN incentive index and county programs"),
    ("https://avaenergy.org/go-electric/savings-incentives/", "CA-Ava", "Ava incentive finder (needs household inputs; amounts not on the page)"),
    ("https://www.sdge.com/rebates", "CA-SDGE", "SDG&E retail coupons and whether Golden State Rebates ended"),
    ("https://www.sdge.com/residential/savings-center/tips/home-electrification", "CA-SDGE", "SDG&E electrification page"),
    ("https://homerenovationsavings.ca/without-assessment/smart-thermostat", "ON", "Ontario thermostat rebate amount, brands, Peak Perks"),
    ("https://www.novascotia.ca/programs-and-services/heating-assistance-rebate-program-harp", "NS", "HARP amount and 2026-27 intake"),
    ("https://www.switchison.org/", "CA", "State incentive lookup"),
    ("https://techcleanca.com/incentives/single-family-incentives/", "CA", "TECH Clean California funding status"),
]


def host(u):
    return urlparse(u).netloc


for f in sorted((ROOT / "data" / "verified-facts").glob("*.json")):
    for x in json.loads(f.read_text())["facts"]:
        u = x.get("source_url")
        if u:
            r = REG[u]
            r["facts"].append(x["id"])
            r["last_read"] = max(r["last_read"], x.get("verified_on", ""))
            r["titles"].add(x.get("program", ""))
            r["region"] = f.stem
for f in sorted((ROOT / "data" / "ca" / "pages").glob("*/*.json")):
    d = json.loads(f.read_text())
    for t, u in d.get("refs", []):
        r = REG[u]
        r["used_by"].add(f"/us/ca/{f.parent.name}/" + ("" if f.stem == "index" else f.stem + "/"))
        r["titles"].add(t)
        r.setdefault("region", "ca-pages")
for u, region, what in EXTRA:
    r = REG[u]
    r["region"] = region
    r["what"] = what
    r["titles"].add(what)
out = []
for u, r in sorted(REG.items(), key=lambda kv: (kv[1].get("region", ""), kv[0])):
    out.append({"url": u, "host": host(u), "region": r.get("region", ""), "check": r.get("what") or "; ".join(sorted(t for t in r["titles"] if t))[:200],
                "facts": sorted(set(r["facts"])), "used_by_pages": sorted(r["used_by"]), "last_read": r["last_read"]})
(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data" / "rebate-sources.json").write_text(json.dumps({"generated": "see git log", "count": len(out), "sources": out}, indent=1, ensure_ascii=False))
print(len(out), "sources,", len({o["host"] for o in out}), "hosts")
