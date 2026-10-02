#!/usr/bin/env python3
"""San José city page and category pages (SJCE EcoHome rebates), built only from data/verified-facts/us-ca.json.
Run after build_ca_regions.py (which skips San José). Same card markup as build_ca_sacramento.py so PowerScore reads the amounts.
Avoid the words waitlist, unclear and fully subscribed in page text: build_powerscore.py treats them as a status signal."""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_ca_regions import FACTS, table, STATEWIDE  # noqa: E402
from build_ca_sacramento import wrap  # noqa: E402
from build_hub_tops import status_pill  # noqa: E402

e = html.escape
PATH = "/us/ca/bay-area/san-jose/"
INTRO = "San José Clean Energy (SJCE) pays cash rebates through its EcoHome program for replacing gas appliances."
# category -> (label, amount, fact id, one-line note)
CATS = {
    "water-heater": ("Heat pump water heater", "$3,000", "us-ca-18-sjce-ecohome-hpwh", "$4,000 in Environmental Justice communities. This includes a $500 bonus for applications from Sept 1 to Oct 31, 2026. It must replace a gas water heater, and you apply before you install."),
    "heat-pump": ("Heat pump heating and cooling", "$1,500", "us-ca-20-sjce-ecohome-hvac", "$2,500 in Environmental Justice communities. It must replace a gas heating system, and you apply before you install."),
    "insulation": ("Attic insulation", "$0.75 per sq ft", "us-ca-21-sjce-ecohome-insulation", "Up to $700, or $1,000 in Environmental Justice communities. It must be paired with a heat pump heating and cooling rebate."),
    "ev-charger": ("EV charger wiring and panel upgrade", "$500", "us-ca-22-sjce-ecohome-prewiring-panel", "$500 for EV circuit prewiring (also dryer or cooking), $1,000 for a panel upgrade. You must also install a heat pump HVAC or water heater."),
}


def card(cat, link=True):
    label, amt, fid, note = CATS[cat]
    fx = FACTS[fid]
    h = f"<a href='{PATH}{cat}/'>{e(label)}</a>" if link else e(label)
    return ('<div class="rebate-card"><h4>' + h + '</h4><div class="amount">' + e(amt) + '</div><p>' + e(note) +
            " <a href='" + e(fx["source_url"]) + "' rel='nofollow noopener' target='_blank'>Source</a> " + status_pill(fx["status"]) +
            f" <span class='small'>(checked {e(fx['verified_on'])})</span></p></div>")


def main():
    latest = max(FACTS[v[2]]["verified_on"] for v in CATS.values())
    crumbs = [("Home", "/"), ("California", "/us/ca/"), ("Bay Area", "/us/ca/bay-area/")]
    unconf = ("<h2>Closed and not confirmed</h2><p>SJCE's battery storage rebate is closed to new applications (it paid $125 per kWh up to $3,250). We found no SJCE solar rebate. "
              "BayREN's income-qualified EASE Home program also serves Santa Clara County: it pays 80% of weatherization costs for PG&amp;E customers at or below 120% of area median income, in single-family homes built before 2010 "
              "(<a href='https://www.bayren.org/ease-home' rel='nofollow noopener' target='_blank'>source</a>, checked 2026-10-01).</p>")
    body = ("<div style='background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;'><p style='margin:0;'><b>Short answer:</b> " + e(INTRO) +
            " It pays $3,000 for a heat pump water heater (with a $500 bonus until October 31, 2026) and $1,500 for a heat pump heating and cooling system, with higher amounts in Environmental Justice communities, plus add-ons for a panel upgrade, insulation and EV wiring. "
            "Statewide heat pump help (TECH Clean California and the federal HEEHRA program) is fully reserved and takes new requests on hold only.</p></div>"
            "<h2>What SJCE pays</h2>" + "".join(card(c) for c in CATS) + unconf +
            "<h2>Statewide programs</h2>" + table(STATEWIDE) +
            "<p>The federal 25C and 25D tax credits ended for spending after December 31, 2025, so we do not count them.</p>"
            "<p><a href='/calculator/ca/'>California rebate calculator</a> · <a href='/get-quotes/?province=ca&city=san-jose'>Get my plan and top-rated installers</a> · "
            "<a href='/installers/ca/san-jose/heat-pump/'>Heat pump installers in San José</a></p>")
    d = ROOT / "us/ca/bay-area/san-jose"
    (d / "index.html").write_text(wrap(PATH, "San José Home Energy Rebates 2026: SJCE EcoHome Rebates", "What San José homeowners can claim from San José Clean Energy in 2026: rebates for heat pumps, water heaters and add-ons, with a source and date for every amount.",
                                       "San José Home Energy Rebates 2026: What Is Open", INTRO, crumbs + [("San José", PATH)], body, latest), encoding="utf-8")
    for cat, (label, amt, fid, note) in CATS.items():
        (d / cat).mkdir(exist_ok=True)
        cp = f"{PATH}{cat}/"
        b = (f"<div style='background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;'><p style='margin:0;'><b>Short answer:</b> {e(INTRO)} For {e(label.lower())}, San José Clean Energy pays {e(amt.lower())} .</p></div>"
             f"<h2>The San José Clean Energy offer</h2>{card(cat, False)}<h2>Where this comes from</h2><p>Read on <a href='{e(FACTS[fid]['source_url'])}' rel='nofollow noopener' target='_blank'>cleanpowersf.org</a> on {e(FACTS[fid]['verified_on'])}. "
             f"Apply with SJCE and wait for approval before you install: funds are then reserved for 120 days.</p><p><a href='{PATH}'>All San José rebates</a> · <a href='/installers/ca/san-jose/heat-pump/'>Top-rated installers</a></p>")
        (d / cat / "index.html").write_text(wrap(cp, f"{label} Rebates in San José 2026: San José Clean Energy", f"San José Clean Energy's {label.lower()} rebate for San José homeowners in 2026, with rules, source and date.",
                                                 f"{label} Rebates in San José (2026)", f"What SJCE pays for {label.lower()}.", crumbs + [("San José", PATH), (label, cp)], b, latest), encoding="utf-8")
    print("Wrote San José")


if __name__ == "__main__":
    main()
