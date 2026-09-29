#!/usr/bin/env python3
"""Build home battery product pages: /batteries/<slug>/ plus the /batteries/ hub.

Specs come only from each maker's official datasheet (linked on the page). Rebates come only from
data/verified-facts/*.json. Add a product by adding an entry to PRODUCTS.
"""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell, CHECKED, ISO, AUTHOR  # noqa: E402
from build_installer_rankings import BASE  # noqa: E402

e = html.escape

PRODUCTS = {
    "tesla-powerwall-3": {
        "name": "Tesla Powerwall 3", "short": "Powerwall 3", "maker": "Tesla",
        "datasheet": "https://energylibrary.tesla.com/docs/Public/EnergyStorage/Powerwall/3/Datasheet/en-us/Powerwall-3-Datasheet.pdf",
        "datasheet_label": "Tesla Powerwall 3 Datasheet (2025)",
        "kwh": 13.5, "kw": 11.5, "inverter": "Built in (up to 20 kW solar)", "warranty": "10 years",
        "cold": "It's rated to operate down to -20°C (-4°F). In places with colder winters, installers often put it in a garage or basement.",
        "specs": [
            ("Usable energy", "13.5 kWh per unit"),
            ("Continuous power", "Up to 11.5 kW (installer can set 5.8, 7.6, 10 or 11.5 kW)"),
            ("Starting big motors", "Up to 185 LRA (a measure of the motors it can start, like AC compressors). Tesla says one unit covers most homes' needs."),
            ("Built-in solar inverter", "Yes: up to 20 kW of panels, 6 inputs (MPPTs)"),
            ("Efficiency, solar to battery to home", "89%"),
            ("How big it can grow", "Up to 4 Powerwall 3 units, plus up to 3 Expansion packs (13.5 kWh each); 7 units total"),
            ("Operating temperature", "-20°C to 50°C (-4°F to 122°F)"),
            ("Install location", "Indoor or outdoor, wall or floor"),
            ("Size and weight", "1105 × 609 × 193 mm; 132 kg installed"),
            ("Warranty", "10 years"),
        ],
        "how": ("Powerwall 3 is a battery and a solar inverter in one box. Your panels plug straight into it, so a new solar-plus-battery "
                "system needs one less piece of equipment. It uses DC coupling: solar power can charge the battery without being converted "
                "to AC and back first."),
        "best_for": [
            "New solar and battery systems, since the inverter is built in.",
            "Homes that want whole-home backup, including central AC or a well pump, from a single unit.",
            "Homes that may add more storage later with Expansion packs.",
        ],
        "watch": [
            "It's big and heavy (132 kg). Plan where it goes before you sign.",
            "If you already have solar with its own inverter, ask your installer how it will connect.",
            "In BC, it gets no BC Hydro battery rebate (see below).",
        ],
        "region_notes": {
            "bc": ("Not eligible", "Tesla batteries have been off BC Hydro's rebate list since March 12, 2025, so Powerwall 3 gets <b>$0</b> "
                   "from the BC Hydro battery rebate. It can still earn Peak Saver bill credits if you enroll it.",
                   "https://www.bchydro.com/powersmart/ineligible-product-information.html"),
            "smud": "Tesla is on SMUD's list of eligible battery brands.",
        },
        "related": [("/blog/tesla-powerwall-bc-hydro-rebate-not-qualified-alternatives/", "Powerwall and the BC Hydro rebate: alternatives"),
                    ("/blog/tesla-powerwall-vs-eguana-evolve/", "Tesla Powerwall vs Eguana Evolve")],
    },
    "enphase-iq-battery-5p": {
        "name": "Enphase IQ Battery 5P", "short": "IQ Battery 5P", "maker": "Enphase",
        "datasheet": "https://www.solarelectricsupply.com/media/sparsh/product_attachment/IQ_Battery-5P-DSH-00010-2.0-EN-US-2023-07-26_1_.pdf",
        "datasheet_label": "Enphase IQ Battery 5P Datasheet, North America (2023)",
        "kwh": 5.0, "kw": 3.84, "inverter": "No (AC coupled, works with any solar)", "warranty": "15 years",
        "cold": "It's rated to charge down to -20°C (-4°F), and works best between 0°C and 30°C. In cold climates, a garage or basement is a better spot than an outside wall.",
        "specs": [
            ("Usable energy", "5.0 kWh per unit"),
            ("Continuous power", "3.84 kVA per unit (7.68 kVA peak for 3 seconds)"),
            ("Starting big motors", "Up to 48 A LRA per unit (much less than Powerwall 3, so big motors may need several units)"),
            ("Built-in solar inverter", "No. Six small built-in battery microinverters; it works with any solar system (AC coupled)"),
            ("Round-trip efficiency", "90% AC, 96% DC"),
            ("Chemistry", "Lithium iron phosphate (LFP)"),
            ("Operating temperature", "-20°C to 50°C charging, to 55°C discharging; best at 0°C to 30°C"),
            ("Cooling", "Passive: no fans or moving parts"),
            ("Size", "About 980 × 550 × 188 mm (38.6 × 21.7 × 7.4 in)"),
            ("Warranty", "15 years (limited)"),
        ],
        "how": ("The IQ Battery 5P is AC coupled. Each unit has its own small inverters inside, so it connects to your home's wiring rather "
                "than to your panels. That makes it easy to add to an existing solar system, even one that isn't Enphase. You stack units "
                "to get the storage and power you need: two units give 10 kWh and 7.68 kVA."),
        "best_for": [
            "Adding a battery to solar you already have.",
            "Starting small and adding units over time.",
            "Homes that want a longer warranty (15 years).",
        ],
        "watch": [
            "One unit is small (5 kWh, 3.84 kVA). Backing up central AC or a whole home usually takes 2 to 4 units.",
            "Every extra unit adds cost, so compare the price per kWh with larger single batteries.",
            "In BC, check that the exact model is on BC Hydro's qualified battery list before you sign.",
        ],
        "region_notes": {
            "bc": ("Check the list", "BC Hydro only pays rebates on batteries on its qualified battery list. Confirm the exact Enphase model "
                   "is on the current list with your installer before you sign.",
                   "https://app.bchydro.com/accounts-billing/electrical-connections/customer-generation/solar-battery-rebates.html"),
            "smud": "Enphase is on SMUD's list of eligible battery brands.",
        },
        "related": [],
    },
    "eguana-evolve": {
        "name": "Eguana Evolve", "short": "Evolve", "maker": "Eguana",
        "datasheet": "https://www.eguanatech.com/_resources/pdf/evolve-lfp-datasheet.pdf",
        "datasheet_label": "Eguana Evolve LFP Datasheet",
        "kwh": 14.0, "kw": 5.0, "pitch": "It's AC coupled, so it pairs with new or existing solar, and you can add battery modules up to 28 kWh. It needs a spot that stays above freezing. ", "inverter": "No (AC coupled, works with your solar inverter)", "warranty": "10 years (60% capacity, pro-rated)",
        "cold": "Not below freezing. The Evolve LFP is rated to operate from 0°C to 50°C (best at 15°C to 30°C), so in Canadian winters it belongs indoors, in a heated garage or basement.",
        "specs": [
            ("Storage", "14 kWh base system (lithium iron phosphate modules), expandable to 28 kWh"),
            ("Continuous power", "5.0 kVA"),
            ("Short bursts", "120% for 30 minutes, 170% for 5 seconds (needs 6+ battery modules)"),
            ("Built-in solar inverter", "No. AC coupled: it pairs with new or existing solar using your preferred inverter brand"),
            ("Round-trip efficiency", "Over 85.7%"),
            ("Chemistry", "Lithium iron phosphate (LFP), Pylontech modules"),
            ("Operating temperature", "0°C to 50°C (recommended 15°C to 30°C)"),
            ("Install location", "Wall mount, indoor or outdoor rated (Type 3R)"),
            ("Backup", "Automatic backup with solar recharging and black start"),
            ("Warranty", "10 years, 60% capacity guarantee (pro-rated); 15-year, 6,000+ cycle design life"),
            ("Made by", "Eguana Technologies, Calgary, Alberta"),
        ],
        "how": ("Eguana Evolve is an AC-coupled battery system built in Calgary. It sits beside your solar system rather than replacing its "
                "inverter, so it works with new or existing solar. The base system stores 14 kWh and can grow to 28 kWh by adding battery "
                "modules, which suits homes that want longer backup through multi-day outages."),
        "best_for": [
            "Adding a battery to solar you already have, with any inverter brand.",
            "Homes that want more storage (up to 28 kWh) for long outages.",
            "Buyers who want a Canadian-made battery.",
        ],
        "watch": [
            "It's rated down to 0°C only, so it needs a spot that stays above freezing.",
            "5 kVA of power is less than Powerwall 3 or FranklinWH, so you may not run central AC and other big loads at once.",
            "The warranty guarantees 60% capacity after 10 years, lower than some rivals.",
        ],
        "region_notes": {
            "bc": ("Check the list", "BC Hydro only pays rebates on batteries on its qualified battery list, up to $5,000 with Peak Saver. "
                   "Confirm the exact Evolve model is on the current list with your installer before you sign.",
                   "https://app.bchydro.com/accounts-billing/electrical-connections/customer-generation/solar-battery-rebates.html"),
            "smud": "Eguana is on SMUD's list of eligible battery brands. Eguana's datasheet also says it's SGIP approved in California.",
        },
        "related": [("/blog/tesla-powerwall-vs-eguana-evolve/", "Tesla Powerwall vs Eguana Evolve")],
    },
    "franklinwh-apower-2": {
        "name": "FranklinWH aPower 2", "short": "aPower 2", "maker": "FranklinWH",
        "datasheet": "https://www.franklinwh.com/document/apower-2-datasheet",
        "datasheet_label": "FranklinWH aPower 2 Datasheet (SKU APR-10K15V2-US)",
        "kwh": 15.0, "kw": 10.0, "inverter": "No (AC coupled, works with any solar)", "warranty": "15 years or 60 MWh",
        "cold": "It's rated to operate down to -20°C (-4°F). In places with colder winters, installers often put it in a garage or basement.",
        "specs": [
            ("Usable energy", "15 kWh per unit; up to 15 units (225 kWh) per aGate"),
            ("Continuous power", "Up to 10 kW / 11.5 kVA (15 kW peak for 10 seconds)"),
            ("Starting big motors", "Up to 185 A LRA"),
            ("Charging power", "Up to 8 kW"),
            ("Built-in solar inverter", "No. AC coupled, used with the FranklinWH aGate controller"),
            ("Round-trip efficiency", "90% (grid to battery to load)"),
            ("Chemistry", "Lithium iron phosphate (LFP)"),
            ("Operating temperature", "-20°C to 50°C (-4°F to 122°F); to 55°C at reduced output"),
            ("Size and weight", "1149 × 750 × 300 mm; 162 kg"),
            ("Flood resistance", "IP67 battery and inverter; rated up to 29 inches from the bottom"),
            ("Warranty", "15 years or 60 MWh throughput"),
            ("Availability", "United States and Canada"),
        ],
        "how": ("The aPower 2 is an AC-coupled battery that works with the FranklinWH aGate, a smart panel that manages your battery, solar, "
                "generator and the grid. Because it's AC coupled, it works with new or existing solar. Each unit stores 15 kWh and can run "
                "big loads like air conditioners and water heaters during an outage."),
        "best_for": [
            "Whole-home backup, including AC and water heaters, from one unit.",
            "Homes that want lots of storage: up to 15 units on one aGate.",
            "Homes that also have a backup generator, which the aGate can manage.",
        ],
        "watch": [
            "It needs the aGate controller, which adds cost and wall space.",
            "It's heavy (162 kg), so plan the location with your installer.",
            "In BC, check that the exact model is on BC Hydro's qualified battery list before you sign.",
        ],
        "region_notes": {
            "bc": ("Check the list", "BC Hydro only pays rebates on batteries on its qualified battery list, up to $5,000 with Peak Saver. "
                   "Confirm the aPower 2 is on the current list with your installer before you sign.",
                   "https://app.bchydro.com/accounts-billing/electrical-connections/customer-generation/solar-battery-rebates.html"),
            "smud": "FranklinWH is on SMUD's list of eligible battery brands.",
        },
        "related": [],
    },
}

# Verified battery incentives (data/verified-facts). (region, hub, program, amount, notes, source)
REBATES = [
    ("British Columbia", "/ca/bc/", "BC Hydro battery rebate", "$500 per kWh, up to $1,500; up to $5,000 if you join Peak Saver",
     "Max 50% of cost. Battery must be on BC Hydro's qualified list. Battery-only installs need Peak Saver.",
     "https://app.bchydro.com/accounts-billing/electrical-connections/customer-generation/solar-battery-rebates.html"),
    ("Ontario", "/ca/on/", "Home Renovation Savings", "$300 per kWh, up to $5,000",
     "Max 50% of cost. You can't also sign a net-metering agreement with your utility.",
     "https://www.homerenovationsavings.ca/without-assessment/solar"),
    ("Massachusetts", "/us/ma/", "ConnectedSolutions", "About $1,375 a year for a 5 kW battery",
     "Paid for letting your utility use the battery during summer peak events. Mass Save's 0% HEAT Loan (up to $25,000) can cover a battery enrolled in ConnectedSolutions.",
     "https://goclean.masscec.com/homeowners/battery-storage/"),
    ("California", "/us/ca/", "SMUD My Energy Optimizer Partner+", "$300 per kWh, up to $6,000",
     "SMUD customers on the Solar and Storage Rate; enroll within 90 days of permission to operate.",
     "https://www.smud.org/Going-Green/Battery-Storage"),
    ("California", "/us/ca/", "SGIP (Self-Generation Incentive Program)", "Depends on your tier",
     "Mainly for income-qualified homes, medical baseline customers and high fire-threat areas.",
     "https://www.cpuc.ca.gov/industries-and-topics/electrical-energy/demand-side-management/self-generation-incentive-program"),
    ("California", "/us/ca/", "Pasadena Water and Power pilot", "Up to $550 per kWh",
     "PWP residential customers; limited funds.",
     "https://pwp.cityofpasadena.net/launch-solar-and-battery-rebate-pilot-program-for-residential-and-commercial-customers/"),
]
NO_REBATE = ("There's no battery rebate on file for Nova Scotia, and the US federal 30% credit for batteries you own ended for systems "
             "installed after December 31, 2025.")


def rebate_table(p):
    rows = ""
    for reg, hub, prog, amt, notes, src in REBATES:
        extra = ""
        if reg == "British Columbia" and p["short"]:
            status, txt, _ = p["region_notes"]["bc"]
            extra = f'<br><b>{e(p["short"])}: {e(status)}.</b>'
            if status == "Not eligible":
                amt = "$0 for " + p["short"]
        if prog.startswith("SMUD") and p["region_notes"].get("smud"):
            extra = "<br>" + e(p["region_notes"]["smud"])
        rows += (f'<tr><td><a href="{hub}">{e(reg)}</a></td><td><a href="{e(src)}" rel="nofollow noopener" target="_blank">{e(prog)}</a></td>'
                 f'<td><b>{e(amt)}</b></td><td>{e(notes)}{extra}</td></tr>')
    return ('<div class="tw"><table><tr><th>Where</th><th>Program</th><th>Amount</th><th>Rules</th></tr>' + rows + "</table></div>"
            f"<p>{e(NO_REBATE)}</p>")


def product_page(slug, p):
    path = f"/batteries/{slug}/"
    others = [(s, o) for s, o in PRODUCTS.items() if s != slug]
    bc_status, bc_txt, bc_src = p["region_notes"]["bc"]
    two = round(p["kwh"] * 2, 1)
    short = (f"The {p['name']} stores {p['kwh']:g} kWh and delivers up to {p['kw']:g} kW of continuous power per unit. "
             + (p.get("pitch") or ("It has a solar inverter built in, so it suits new solar and battery systems. " if "tesla" in slug else
                "It's AC coupled, so it adds easily to solar you already have, and you stack units for more storage. "))
             + ("It gets no BC Hydro battery rebate. Ontario, Massachusetts and parts of California do have battery programs; "
                "check that this model is on each program's list."
                if bc_status == "Not eligible" else
                "Battery programs in BC, Ontario, Massachusetts and parts of California may cover it; "
                "each keeps its own list of eligible models, so check before you sign."))
    spec_rows = "".join(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>" for k, v in p["specs"])
    faq = [
        (f"How long will a {p['short']} power my home in an outage?",
         f"It depends on what you run. A fridge, lights, internet and a furnace fan might use about 1 kW, so one {p['kwh']:g} kWh unit "
         f"could last around {p['kwh'] * 0.9:.0f} hours with no solar (allowing for losses). Central AC or electric heat drains it much faster. "
         "With solar, the battery refills during the day."),
        (f"Does the {p['name']} work in the cold?", p["cold"]),
        (f"Can I get a rebate for the {p['name']} in BC?", bc_txt.replace("<b>", "").replace("</b>", "")),
    ]
    allp = [(slug, p)] + others
    head = "".join(f"<th>{e(o['name'])}</th>" for _, o in allp)
    rows = [("Storage per unit", lambda o: f"{o['kwh']:g} kWh"), ("Continuous power per unit", lambda o: f"{o['kw']:g} kW"),
            ("Solar inverter", lambda o: o["inverter"]), ("Warranty", lambda o: o["warranty"]),
            ("BC Hydro rebate", lambda o: o["region_notes"]["bc"][0])]
    compare = (f'<h2>{e(p["short"])} vs other home batteries</h2><div class="tw"><table><tr><th></th>{head}</tr>'
               + "".join(f"<tr><th>{e(k)}</th>" + "".join(f"<td>{e(fn(o))}</td>" for _, o in allp) + "</tr>" for k, fn in rows)
               + "</table></div><p>Full guides: " + " · ".join(f'<a href="/batteries/{s2}/">{e(o["name"])}</a>' for s2, o in others) + ".</p>")
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/batteries/">Home batteries</a></li><li aria-current="page">{e(p['name'])}</li></ol></nav>
<header class="hero"><div class="wrap"><h1>{e(p['name'])}: Specs, Backup Power and Rebates (2026)</h1>
<p>What it does, what it can back up, and which rebates it qualifies for in Canada and the US. Specs from {e(p['maker'])}'s datasheet. Last checked {CHECKED}.</p>
<p class="meta">By {AUTHOR['name']}</p></div></header>
<section class="body"><div class="wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> {e(short)}</p></div>

<h2>How it works</h2>
<p>{e(p['how'])}</p>

<h2>{e(p['name'])} specs</h2>
<div class="tw"><table>{spec_rows}</table></div>
<p class="small">Source: <a href="{e(p['datasheet'])}" rel="nofollow noopener" target="_blank">{e(p['datasheet_label'])}</a>. Specs can change between versions; ask your installer for the current datasheet.</p>

<h2>What can it back up?</h2>
<p>Two numbers matter. <b>kWh</b> is how much energy it stores (how long it lasts). <b>kW</b> is how much it can power at once (how many things run together).</p>
<ul><li>One unit stores <b>{p['kwh']:g} kWh</b>; two store <b>{two:g} kWh</b>.</li>
<li>One unit can run <b>{p['kw']:g} kW</b> at once. A fridge, lights, internet and furnace fan together use about 1 kW. Central AC can use 3 to 5 kW while running, and more for a moment when it starts.</li></ul>

<h2>Who it's best for</h2>
<ul>{"".join(f"<li>{e(x)}</li>" for x in p['best_for'])}</ul>
<h2>Watch out for</h2>
<ul>{"".join(f"<li>{e(x)}</li>" for x in p['watch'])}</ul>

<h2>{e(p['name'])} rebates by province and state</h2>
{rebate_table(p)}
<p><b>In BC:</b> {bc_txt} <a href="{e(bc_src)}" rel="nofollow noopener" target="_blank">Source</a>.</p>

{compare}

<h2>Common questions</h2>
{"".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in faq)}

<p><b>Related:</b> {" · ".join(f'<a href="{u}">{e(t)}</a>' for u, t in p['related'] + [("/batteries/", "All home battery guides"), ("/solar-quote-checker/", "Solar quote checker"), ("/installers/", "Top-rated installers by city")])}</p>
</div></section>"""
    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": f"{p['name']}: Specs, Backup Power and Rebates (2026)",
         "description": short, "datePublished": "2026-09-29", "dateModified": ISO, "author": AUTHOR,
         "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE}, "mainEntityOfPage": BASE + path,
         "about": {"@type": "Product", "name": p["name"], "brand": {"@type": "Brand", "name": p["maker"]}}},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
    ]
    title = f"{p['name']} Specs, Backup & Rebates (2026) | HomePowerRebate"
    desc = (f"{p['name']}: {p['kwh']:g} kWh, {p['kw']:g} kW per unit. How it works, what it can back up, and battery rebates in "
            "Ontario, Massachusetts, California and BC.")
    return path, shell(title, desc, path, "on", body, ld)


def hub_page():
    path = "/batteries/"
    cards = "".join(
        f'<tr><td><a href="/batteries/{s}/">{e(p["name"])}</a></td><td>{p["kwh"]:g} kWh</td><td>{p["kw"]:g} kW</td>'
        f'<td>{e(p["inverter"])}</td><td>{e(p["region_notes"]["bc"][0])}</td></tr>' for s, p in PRODUCTS.items())
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">Home batteries</li></ol></nav>
<header class="hero"><div class="wrap"><h1>Home Battery Guides: Specs and Rebates (2026)</h1>
<p>Plain-language guides to the home batteries installers quote most, with specs from each maker and rebates checked monthly.</p></div></header>
<section class="body"><div class="wrap">
<div class="tw"><table><tr><th>Battery</th><th>Storage per unit</th><th>Power per unit</th><th>Solar inverter</th><th>BC Hydro rebate</th></tr>{cards}</table></div>
<h2>Battery rebates by province and state</h2>
{rebate_table({"short": "", "region_notes": {"bc": ("Depends on the model", "", "")}})}
<p class="small">More battery guides are coming. Something out of date? Email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a>.</p>
</div></section>"""
    return path, shell("Home Battery Guides 2026: Specs & Rebates | HomePowerRebate",
                       "Compare Tesla Powerwall 3, Enphase IQ Battery 5P, Eguana Evolve and FranklinWH aPower 2: storage, power, and battery rebates by province and state.",
                       path, "on", body, [])


def main():
    css = ".tw{overflow-x:auto;-webkit-overflow-scrolling:touch}.tw table{min-width:520px}section.body h3{font-size:20px;margin:24px 0 6px}"
    pages = [product_page(s, p) for s, p in PRODUCTS.items()] + [hub_page()]
    for path, page in pages:
        page = page.replace("</style>", css + "</style>", 1)
        out = ROOT / path.strip("/") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")
        print("Wrote", path)


if __name__ == "__main__":
    main()
