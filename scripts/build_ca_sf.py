#!/usr/bin/env python3
"""San Francisco city page and category pages (CleanPowerSF bill credits), built only from data/verified-facts/us-ca.json.
Run after build_ca_regions.py (which skips San Francisco). Same card markup as build_ca_sacramento.py so PowerScore reads the amounts.
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
PATH = "/us/ca/bay-area/san-francisco/"
INTRO = "San Francisco's electricity comes from CleanPowerSF, which pays rebates as monthly bill credits, not as a cheque."
# category -> (label, amount, fact id, one-line note)
CATS = {
    "water-heater": ("Heat pump water heater", "Up to $1,200", "us-ca-15-cleanpowersf-hpwh-credit", "$50 off your bill each month for 24 months. You must enrol the new water heater in a load-shifting program, and the install needs a San Francisco permit."),
    "heat-pump": ("Heat pump heating", "Up to $1,200", "us-ca-16-cleanpowersf-hp-heating-credit", "$50 off your bill each month for 24 months, for installs from April 14, 2026. You must be on the EV2-A or E-ELEC electric rate."),
    "appliances": ("Electric cooking, dryer and gas meter", "Up to $300", "us-ca-17-cleanpowersf-cooking-dryer-meter", "$150 for electric cooking, $300 for an electric dryer and $300 for removing your gas meter."),
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
    unconf = ("<h2>What we could not confirm</h2><p>BayREN and state programs help with weatherization and sign-ups, but pay no fixed cash amount we could verify for San Francisco. "
              "Rebates for batteries, EV chargers, insulation and solar are not listed on CleanPowerSF's pages, so we show no amounts for them. "
              "Tell us at <a href='mailto:hello@homepowerrebate.com'>hello@homepowerrebate.com</a> if you find a current one.</p>")
    body = ("<div style='background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;'><p style='margin:0;'><b>Short answer:</b> " + e(INTRO) +
            " It pays up to $1,200 for a heat pump water heater and up to $1,200 for heat pump heating, plus smaller credits for electric cooking, a dryer and gas meter removal. "
            "Statewide heat pump help (TECH Clean California and the federal HEEHRA program) is fully reserved and takes new requests on hold only.</p></div>"
            "<h2>What CleanPowerSF pays</h2>" + "".join(card(c) for c in CATS) + unconf +
            "<h2>Statewide programs</h2>" + table(STATEWIDE) +
            "<p>The federal 25C and 25D tax credits ended for spending after December 31, 2025, so we do not count them.</p>"
            "<p><a href='/calculator/ca/'>California rebate calculator</a> · <a href='/get-quotes/?province=ca&city=san-francisco'>Get my plan and top-rated installers</a> · "
            "<a href='/installers/ca/san-francisco/heat-pump/'>Heat pump installers in San Francisco</a></p>")
    d = ROOT / "us/ca/bay-area/san-francisco"
    (d / "index.html").write_text(wrap(PATH, "San Francisco Home Energy Rebates 2026: CleanPowerSF Credits", "What San Francisco homeowners can claim from CleanPowerSF in 2026: bill credits for heat pumps and water heaters, with a source and date for every amount.",
                                       "San Francisco Home Energy Rebates 2026: What Is Open", INTRO, crumbs + [("San Francisco", PATH)], body, latest), encoding="utf-8")
    for cat, (label, amt, fid, note) in CATS.items():
        (d / cat).mkdir(exist_ok=True)
        cp = f"{PATH}{cat}/"
        b = (f"<div style='background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;'><p style='margin:0;'><b>Short answer:</b> {e(INTRO)} For {e(label.lower())}, CleanPowerSF pays {e(amt.lower())} as bill credits.</p></div>"
             f"<h2>The CleanPowerSF offer</h2>{card(cat, False)}<h2>Where this comes from</h2><p>Read on <a href='{e(FACTS[fid]['source_url'])}' rel='nofollow noopener' target='_blank'>cleanpowersf.org</a> on {e(FACTS[fid]['verified_on'])}. "
             f"Apply online with CleanPowerSF after your install is done and permitted.</p><p><a href='{PATH}'>All San Francisco rebates</a> · <a href='/installers/ca/san-francisco/heat-pump/'>Top-rated installers</a></p>")
        (d / cat / "index.html").write_text(wrap(cp, f"{label} Rebates in San Francisco 2026: CleanPowerSF", f"CleanPowerSF's {label.lower()} credit for San Francisco homeowners in 2026, with rules, source and date.",
                                                 f"{label} Rebates in San Francisco (2026)", f"What CleanPowerSF pays for {label.lower()}.", crumbs + [("San Francisco", PATH), (label, cp)], b, latest), encoding="utf-8")
    print("Wrote San Francisco")


if __name__ == "__main__":
    main()
