#!/usr/bin/env python3
"""Los Angeles-area city and category pages, built only from data/verified-facts (us-ca.json, us-ca-la-munis.json).
Each city is served by a different utility, so each has its own offers. Categories with no verified offer are not built; their URLs redirect to the city page.
Cards use the rebate-card/.amount markup that build_powerscore.py reads. Avoid the words waitlist, unclear and fully subscribed in page text."""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_ca_regions import FACTS, table, STATEWIDE  # noqa: E402
from build_ca_sacramento import wrap  # noqa: E402
from build_hub_tops import status_pill  # noqa: E402

e = html.escape
L = "us-ca-la-munis-"
ALL_CATS = ["appliances", "battery", "ev-charger", "heat-pump", "hrv", "insulation", "smart-thermostats", "solar", "water-heater", "windows-doors"]
# city -> dict(name, utility, intro, cats{cat: (label, amount, note, [fact ids])}, none{cat: note})
CITIES = {
    "los-angeles": dict(name="Los Angeles", intro="Los Angeles homes are served by the Los Angeles Department of Water and Power (LADWP), which runs its own rebates.", cats={
        "heat-pump": ("Heat pump heating and cooling", "Up to $2,500 per ton", "For installs from November 1, 2025. Apply after the install, within 12 months.", ["us-ca-11-ladwp-consumer-rebate-program"]),
        "water-heater": ("Heat pump water heater", "Up to $2,500", "Apply after the install, within 12 months.", ["us-ca-11-ladwp-consumer-rebate-program"]),
        "windows-doors": ("ENERGY STAR windows", "$2.00 per sq ft", "LADWP does rebate windows. Apply after the install, within 12 months.", ["us-ca-11-ladwp-consumer-rebate-program"]),
        "battery": ("Home battery", "No general rebate", "LADWP has no general battery rebate. Households at or below 80% of area median income can get help for solar and storage through the state's SGIP equity program, which LADWP runs.", ["us-ca-12-ladwp-sgip-rsse"]),
    }),
    "glendale": dict(name="Glendale", intro="Glendale has its own utility, Glendale Water and Power (GWP), which runs its own rebates.", cats={
        "heat-pump": ("Heat pump heating and cooling", "$1,000 per ton, up to $5,000", "That is for replacing a gas furnace. Replacing an existing heat pump pays $500 per ton, up to $2,500, as a bill credit. A $1,000 panel upgrade rebate is added when it is paired with a heat pump or water heater install.", [L + "7-gwp-heat-pump-hvac-replacing-gas-furnace-gas-elect", L + "8-gwp-heat-pump-hvac-replacing-an-existing-heat-pump", L + "10-gwp-panel-upgrade"]),
        "water-heater": ("Heat pump water heater", "$4,000", "A limited-time rebate. It must replace a gas water heater, and needs gas capping and electrical permits.", [L + "9-gwp-heat-pump-water-heater"]),
        "appliances": ("Appliances", "Up to $400 each", "A heat pump dryer or an electric range replacing gas pays $400. A refrigerator or freezer pays $200 and a dishwasher $50. Apply within 12 months.", [L + "11-gwp-appliances"]),
    }),
    "burbank": dict(name="Burbank", intro="Burbank has its own utility, Burbank Water and Power (BWP), which runs its own rebates.", cats={
        "heat-pump": ("Heat pump heating and cooling", "$1,000 per ton, up to $2,500", "Up to $5,000 for low-income customers. It must replace natural gas heating. It covers equipment and panel, not labour.", [L + "12-bwp-heat-pump-hvac-mini-split-replacing-gas"]),
        "water-heater": ("Heat pump water heater", "$1,500", "It must replace a gas water heater.", [L + "13-bwp-electrification-other"]),
        "ev-charger": ("EV charger", "Up to $500", "A smart charger pays $500 and a standard charger $200, with a panel upgrade up to $750. You must be on a time-of-use rate. Renters can apply.", [L + "14-bwp-ev-charger-rebate"]),
        "smart-thermostats": ("Smart thermostat", "Up to $75", "A rebate for an eligible smart thermostat.", [L + "15-bwp-efficiency-rebates"]),
        "appliances": ("Electric appliances", "Up to $500", "An electric range pays $500. A heat pump dryer or induction cooktop pays $200, with higher amounts for low-income customers. They must replace gas.", [L + "13-bwp-electrification-other"]),
    }),
    "pasadena": dict(name="Pasadena", intro="Pasadena has its own utility, Pasadena Water and Power (PWP), which runs its own rebates.", cats={
        "heat-pump": ("Heat pump heating and cooling", "$170 per ton", "A 3-ton system earns $510, plus $20 per ton if you buy it in Pasadena. Apply within 180 days of purchase.", [L + "0-pwp-heat-pump-rebate"]),
        "water-heater": ("Heat pump water heater", "$500", "Add $20 if you buy it in Pasadena. Apply within 180 days.", [L + "1-pwp-heat-pump-water-heater-rebate"]),
        "ev-charger": ("EV charger", "Up to $600", "$600 for a Wi-Fi connected Level 2 charger and $200 for a standard one. Up to 2 per address, with a permit and professional install.", [L + "2-pwp-ev-charger-rebate"]),
        "smart-thermostats": ("Smart thermostat", "$50", "Add $10 if you buy it in Pasadena.", [L + "3-pwp-smart-thermostat-rebate"]),
        "insulation": ("Ceiling insulation", "$0.10 per sq ft", "Add $0.05 per sq ft with a qualified local contractor. It must reach R-30 or higher.", [L + "4-pwp-ceiling-insulation-rebate"]),
        "solar": ("Solar panels", "$0.60 per watt", "$1.00 per watt for income-qualified households, for new or expanded rooftop systems. This is a pilot program.", [L + "5-pwp-solar-and-battery-rebate-pilot"]),
        "battery": ("Home battery", "Up to $550 per kWh", "Tiered incentives through the same pilot program as solar.", [L + "5-pwp-solar-and-battery-rebate-pilot"]),
    }),
    "long-beach": dict(name="Long Beach", intro="Long Beach is served by Southern California Edison for electricity. Its gas comes from the city's own utility, not SoCalGas.", cats={
        "ev-charger": ("EV charger panel upgrade", "Up to $4,200", "Income-qualified households only (below 80% of area median income, or on an assistance program). You must install a Level 2 charger within 180 days.", [L + "16-sce-charge-ready-home"]),
        "smart-thermostats": ("Smart thermostat", "$75 bill credit", "For enrolling an eligible smart thermostat in SCE's demand response program.", [L + "17-sce-smart-energy-program"]),
    }),
    "santa-monica": dict(name="Santa Monica", intro="Santa Monica is served by Southern California Edison.", cats={
        "ev-charger": ("EV charger panel upgrade", "Up to $4,200", "Income-qualified households only (below 80% of area median income, or on an assistance program). You must install a Level 2 charger within 180 days.", [L + "16-sce-charge-ready-home"]),
        "smart-thermostats": ("Smart thermostat", "$75 bill credit", "For enrolling an eligible smart thermostat in SCE's demand response program.", [L + "17-sce-smart-energy-program"]),
    }),
}


def sources(ids):
    seen, out = set(), []
    for i in ids:
        u = FACTS[i]["source_url"]
        if u not in seen:
            seen.add(u)
            out.append(f"<a href='{e(u)}' rel='nofollow noopener' target='_blank'>Source</a>")
    return " ".join(out)


def card(slug, cat, link=True):
    label, amt, note, ids = CITIES[slug]["cats"][cat]
    fx = FACTS[ids[0]]
    base = f"/us/ca/los-angeles/{slug}/"
    h = f"<a href='{base}{cat}/'>{e(label)}</a>" if link else e(label)
    none = "none" if amt.startswith("No ") else ""
    return (f'<div class="rebate-card {none}"><h4>{h}</h4><div class="amount {none}">{e(amt)}</div><p>{e(note)} {sources(ids)} {status_pill(fx["status"])} '
            f"<span class='small'>(checked {e(max(FACTS[i]['verified_on'] for i in ids))})</span></p></div>")


SD_INTRO = "San Diego homes are served by San Diego Gas and Electric (SDG&E)."
for _s, _n in (("san-diego", "San Diego"), ("chula-vista", "Chula Vista"), ("escondido", "Escondido")):
    CITIES[_s] = dict(name=_n, area="san-diego", area_name="San Diego area", intro=SD_INTRO if _s == "san-diego" else f"{_n} is in SDG&E's service area (San Diego Gas and Electric).", cats={}, facts=["us-ca-24-sdge-retail-coupons"])


def main():
    for slug, c in CITIES.items():
        if (ROOT / "data/ca/pages" / slug).exists():
            continue  # hand-written pages, built by build_ca_pages.py
        area = c.get("area", "los-angeles")
        name, base = c["name"], f"/us/ca/{area}/{slug}/"
        d = ROOT / "us/ca" / area / slug
        latest = max(FACTS[i]["verified_on"] for i in (c.get("facts") or [i for v in c["cats"].values() for i in v[3]]))
        crumbs = [("Home", "/"), ("California", "/us/ca/"), (c.get("area_name", "Los Angeles area"), f"/us/ca/{area}/")]
        amts = [v[1] for k, v in c["cats"].items() if not v[1].startswith("No ")]
        lead = (f"We verified {len(c['cats'])} home rebate areas for {name}, listed below with a source for each. " if c["cats"]
                else f"We could not verify an open home rebate from SDG&E for {name}, so we show no utility amount. ")
        if c["cats"]:
            offers = f"<h2>What is offered in {e(name)}</h2>" + "".join(card(slug, k) for k in c["cats"])
        else:
            offers = ("<h2>What SDG&amp;E lists</h2><p>SDG&amp;E's rebates page lists retail coupons: $75 for an ENERGY STAR smart thermostat, $40 for an Amazon smart thermostat, $500 for a heat pump water heater that replaces an electric water heater, and $15 for a room air conditioner. "
                      "The same page says the program's retail rebate offerings have ended, and it does not honour rebates after purchase, so we do not count these as open. "
                      f"<a href='{e(FACTS['us-ca-24-sdge-retail-coupons']['source_url'])}' rel='nofollow noopener' target='_blank'>Source</a> <span class='small'>(read 2026-10-01)</span></p>")
        body = ("<div style='background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;'><p style='margin:0;'><b>Short answer:</b> " + e(c["intro"]) + " " + e(lead) +
                "Statewide heat pump help (TECH Clean California and the federal HEEHRA program) is fully reserved and takes new requests on hold only.</p></div>" + offers +
                "<h2>What we could not confirm</h2><p>Anything not listed above, such as other categories or amounts quoted on other sites. We show no figure we could not read on the utility's own page. "
                "Tell us at <a href='mailto:hello@homepowerrebate.com'>hello@homepowerrebate.com</a> if you find a current one.</p>"
                "<h2>Statewide programs</h2>" + table(STATEWIDE) +
                "<p>The federal 25C and 25D tax credits ended for spending after December 31, 2025, so we do not count them.</p>"
                f"<p><a href='/calculator/ca/'>California rebate calculator</a> · <a href='/get-quotes/?province=ca&city={slug}'>Get my plan and top-rated installers</a> · <a href='/installers/ca/{slug}/heat-pump/'>Heat pump installers in {e(name)}</a></p>")
        (d / "index.html").write_text(wrap(base, f"{name} Home Energy Rebates 2026: What Is Open", f"What {name}, California homeowners can claim in 2026 from their utility, with a source and date for every amount.",
                                           f"{name} Home Energy Rebates 2026: What Is Open", c["intro"], crumbs + [(name, base)], body, latest), encoding="utf-8")
        for cat in ALL_CATS:
            cd = d / cat
            if cat not in c["cats"]:
                if cd.exists():
                    for f in cd.rglob("*"):
                        if f.is_file():
                            f.unlink()
                    for sub in sorted(cd.rglob("*"), reverse=True):
                        sub.rmdir()
                    cd.rmdir()
                continue
            label, amt, note, ids = c["cats"][cat]
            cd.mkdir(exist_ok=True)
            cp = f"{base}{cat}/"
            b = (f"<div style='background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;'><p style='margin:0;'><b>Short answer:</b> {e(c['intro'])} For {e(label.lower())}: {e(amt.lower())}.</p></div>"
                 f"<h2>The offer</h2>{card(slug, cat, False)}<p><a href='{base}'>All {e(name)} rebates</a> · <a href='/installers/ca/{slug}/heat-pump/'>Top-rated installers</a></p>")
            (cd / "index.html").write_text(wrap(cp, f"{label} Rebates in {name} 2026", f"What {name}, California homeowners can claim for {label.lower()} in 2026, with rules, source and date.",
                                                f"{label} Rebates in {name} (2026)", c["intro"], crumbs + [(name, base), (label, cp)], b, latest), encoding="utf-8")
        print("Wrote", slug, sorted(c["cats"]))


if __name__ == "__main__":
    main()
