#!/usr/bin/env python3
"""Sacramento-area city and category pages (SMUD), built only from verified facts + data/calc/ca.json.
Cards use the rebate-card/.amount markup that build_powerscore.py reads, so these cities stay in PowerScore.
Avoid the words waitlist, unclear and fully subscribed in page text: build_powerscore.py treats them as a status signal."""
import html
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell, AUTHOR, BASE  # noqa: E402
from build_calculator import CSS, money  # noqa: E402
from build_ca_regions import FACTS, PROGS, table, STATEWIDE  # noqa: E402
from build_hub_tops import status_pill  # noqa: E402

e = html.escape
CITIES = {
    "sacramento": ("Sacramento", "Sacramento is SMUD's home city, so SMUD's rebates apply."),
    "rancho-cordova": ("Rancho Cordova", "Rancho Cordova is in SMUD's service area, so SMUD's rebates apply."),
    "folsom": ("Folsom", "SMUD serves part of Folsom, so check your electric bill before you count on these amounts."),
}
# category -> (label, program ids, one-line note)
CATS = {
    "heat-pump": ("Heat pump", ["smud-hp", "smud-go-electric"], "A two-stage or variable-stage heat pump from a participating contractor. A Go Electric bonus adds up to $2,000 when you replace a gas furnace or gas water heater."),
    "water-heater": ("Heat pump water heater", ["smud-hpwh"], "NEEA Tier III or IV models."),
    "insulation": ("Insulation and air sealing", ["smud-ins"], "Air sealing, attic insulation and ducts through a Home Performance Program contractor."),
    "battery": ("Home battery", ["smud-battery"], "$300 per kWh, up to $6,000, for approved batteries on SMUD's Solar and Storage Rate. There is no separate $5,400 SMUD battery rebate."),
    "ev-charger": ("EV charger", ["smud-ev"], "Up to $600 for a charger and/or circuit."),
    "smart-thermostats": ("Smart thermostat", ["smud-tstat"], "An instant rebate at the SMUD Energy Store."),
}
RC = (".rebate-card{background:#fff;border:1px solid #d9d0c1;border-radius:12px;padding:16px;margin:0 0 12px}.rebate-card.none{background:#faf7f2}.rebate-card h4{margin:0 0 4px}"
      ".rebate-card .amount{font-weight:700;color:#2d6a4f;font-size:20px}.rebate-card .amount.none{color:#6b7d80}.rebate-card p{margin:6px 0 0;font-size:15px}")
SOLAR_NOTE = "We found no SMUD solar cash rebate on SMUD's pages. A $2,000 figure quoted on other sites is unverified, so we do not use it."
REDIRECT = ["hrv", "appliances", "windows-doors"]


def amount_text(p):
    return money(p)


def card(slug, cat, with_link=True):
    label, ids, note = CATS[cat]
    main = PROGS[ids[0]]
    fx = FACTS[main["fact"]]
    h = f"<a href='/us/ca/sacramento/{slug}/{cat}/'>{e(label)}</a>" if with_link else e(label)
    return ('<div class="rebate-card"><h4>' + h + '</h4><div class="amount">' + e(amount_text(main)) + '</div><p>' + e(note) +
            " <a href='" + e(fx["source_url"]) + "' rel='nofollow noopener' target='_blank'>Source</a> " + status_pill(fx["status"]) + "</p></div>")


def solar_card(slug, with_link=True):
    h = f"<a href='/us/ca/sacramento/{slug}/solar/'>Solar panels</a>" if with_link else "Solar panels"
    return '<div class="rebate-card none"><h4>' + h + '</h4><div class="amount none">No SMUD cash rebate</div><p>' + e(SOLAR_NOTE) + "</p></div>"


def wrap(path, title, desc, h1, lead, crumbs, body, latest):
    when = date.fromisoformat(latest).strftime("%B %-d, %Y")
    bc = "".join(f'<li><a href="{u}">{e(n)}</a></li>' for n, u in crumbs[:-1]) + f'<li aria-current="page">{e(crumbs[-1][0])}</li>'
    full = (f'<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol>{bc}</ol></nav>'
            f'<header class="hero"><div class="wrap"><h1>{e(h1)}</h1><p>{e(lead)}</p><p class="meta">By {e(AUTHOR["name"])} · Checked {e(when)}</p></div></header>'
            f'<section class="body"><div class="wrap">{body}</div></section>')
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": h1, "author": AUTHOR, "dateModified": latest, "mainEntityOfPage": BASE + path,
           "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE}}]
    out = shell(title + " | HomePowerRebate", desc, path, "ca", full, ld)
    return out.replace("</style>", ".tw{overflow-x:auto}.tw table{min-width:520px}" + RC + "</style>", 1)


def main():
    latest = max(FACTS[PROGS[i]["fact"]]["verified_on"] for _, ids, _ in CATS.values() for i in ids)
    for slug, (name, intro) in CITIES.items():
        base = ROOT / "us" / "ca" / "sacramento" / slug
        cards = "".join(card(slug, c) for c in CATS) + solar_card(slug)
        city_body = (f"<div style='background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;'><p style='margin:0;'><b>Short answer:</b> {e(intro)} SMUD pays up to $3,000 for a heat pump, "
                     "up to $4,000 for a heat pump water heater, up to $3,000 for insulation and air sealing, and up to $6,000 for a battery. Statewide heat pump help (TECH Clean California and the federal HEEHRA program) "
                     "is fully reserved and takes new requests on hold only.</p></div>"
                     f"<h2>What SMUD pays</h2>{cards}"
                     "<h2>Every SMUD program in the calculator</h2>" + table([i for i in PROGS if PROGS[i].get('when', {}).get('utility') == ['smud']]) +
                     f"<p><a href='/calculator/ca/?utility=smud&city={slug}'>Estimate your {e(name)} rebates</a> · <a href='/get-quotes/?province=ca&city={slug}'>Get my plan and top-rated installers</a> · <a href='/installers/ca/{slug}/heat-pump/'>Heat pump installers in {e(name)}</a></p>"
                     "<h2>Statewide programs</h2>" + table(STATEWIDE) +
                     "<p>The federal 25C and 25D tax credits ended for spending after December 31, 2025, so we do not count them.</p>")
        path = f"/us/ca/sacramento/{slug}/"
        (base / "index.html").write_text(wrap(path, f"{name} Home Energy Rebates 2026: SMUD Programs", f"What {name}, California homeowners can claim from SMUD in 2026, with a source and date for every amount.",
                                              f"{name} Home Energy Rebates 2026: What SMUD Pays", intro, [("Home", "/"), ("California", "/us/ca/"), ("Sacramento area", "/us/ca/sacramento/"), (name, path)], city_body, latest), encoding="utf-8")
        for cat, (label, ids, note) in CATS.items():
            d = base / cat
            d.mkdir(exist_ok=True)
            cp = f"/us/ca/sacramento/{slug}/{cat}/"
            body = (f"<div style='background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;'><p style='margin:0;'><b>Short answer:</b> {e(intro)} For {e(label.lower())}, SMUD pays {e(amount_text(PROGS[ids[0]]).lower())}.</p></div>"
                    f"<h2>The SMUD offer</h2>{card(slug, cat, False)}<h2>Rules and sources</h2>{table(ids)}"
                    f"<p><a href='{path}'>All {e(name)} rebates</a> · <a href='/calculator/ca/?utility=smud&city={slug}&plan={'ev' if cat == 'ev-charger' else 'thermostat' if cat == 'smart-thermostats' else cat}'>Estimate yours</a> · <a href='/installers/ca/{slug}/heat-pump/'>Top-rated installers</a></p>")
            (d / "index.html").write_text(wrap(cp, f"{label} Rebates in {name} 2026: SMUD", f"SMUD's {label.lower()} rebate for {name}, California homeowners in 2026, with rules, source and date.",
                                               f"{label} Rebates in {name} (2026)", f"What SMUD pays for {label.lower()} and how to claim it.",
                                               [("Home", "/"), ("California", "/us/ca/"), (name, path), (label, cp)], body, latest), encoding="utf-8")
        d = base / "solar"
        d.mkdir(exist_ok=True)
        sp = f"/us/ca/sacramento/{slug}/solar/"
        sbody = (f"<div style='background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;'><p style='margin:0;'><b>Short answer:</b> {e(intro)} We found no SMUD cash rebate for solar panels. "
                 "SMUD sets its own solar rules, including a Solar and Storage Rate, and pays an enrollment incentive for approved home batteries.</p></div>"
                 f"<h2>What we checked</h2>{solar_card(slug, False)}<h2>If you add a battery</h2>{card(slug, 'battery', False)}"
                 f"<p><a href='{path}'>All {e(name)} rebates</a> · <a href='/installers/ca/{slug}/solar/'>Top-rated solar installers</a></p>")
        (d / "index.html").write_text(wrap(sp, f"Solar Panel Rebates in {name} 2026: SMUD", f"Is there a SMUD solar rebate in {name}? What we found and what pays for a battery.",
                                           f"Solar Panel Rebates in {name} (2026)", "No cash rebate from SMUD. Here is what exists.",
                                           [("Home", "/"), ("California", "/us/ca/"), (name, path), ("Solar", sp)], sbody, latest), encoding="utf-8")
        print("Wrote", slug)


if __name__ == "__main__":
    main()
