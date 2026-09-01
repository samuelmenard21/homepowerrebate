#!/usr/bin/env python3
"""
Add Water Heater category pages to all 20 NY city pages — the only category
(of insulation/solar/battery/ev-charger/smart-thermostats/windows-doors/
water-heater) missing sitewide for NY, found 2026-08-31 while researching a
water-heater buying guide and noticing NY had no rebate data to ground it in.

Builds each new page from that city's existing insulation/index.html as a
structural template (nav, footer, city-picker dropdown, breadcrumb pattern
all already correct there), swapping in water-heater-specific content. Then
adds a "water-heater" link into the sibling-category nav row on all 6
existing category pages per city, and a "Learn more about Water Heater" link
on each city's hub index.html — so the new pages aren't orphans.

Real 2026 rebate figures per utility (WebSearch-verified 2026-08-31):
  Con Edison:     $1,300 instant rebate, ENERGY STAR HPWH up to 120 gal,
                  purchase by Dec 31 2026, Lowe's/Home Depot or contractor.
                  https://www.coned.com/en/save-money/rebates-incentives-tax-credits/rebates-incentives-tax-credits-for-residential-customers/electric-heating-and-cooling-technology-for-renters-homeowners/swap-your-water-heater-and-save
  PSEG Long Island: up to $1,200, ENERGY STAR HPWH, one per account/5 yrs.
                  https://www.psegliny.com/en/saveenergyandmoney/homeefficiency/HomeComfort/HeatPumps/Rebates
  National Grid:  up to $1,250 instant rebate via retail partners, plus
                  additional NYS Clean Heat Program incentives.
                  https://www.nationalgridus.com/Upstate-NY-Home/Energy-Saving-Programs/Electric-Heat-Pump-Water-Heaters
  Central Hudson: $1,000-$1,250 (sources vary — Central Hudson's own site
                  and NYS Clean Heat materials disagree by $250; used range).
                  https://www.cenhud.com/en/my-energy/save-energy-money/residential-incentives/electric-heat-pump-water-heaters/

Run from the Powerrebate root:
  python3 scripts/generate_ny_water_heater_pages.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UTILITY_DATA = {
    "con-edison": {
        "amount": "$1,300",
        "headline_amount": "Up to $1,300",
        "desc": "Con Edison's instant rebate covers ENERGY STAR-certified heat pump water heaters up to 120 gallons, redeemed at Lowe's or Home Depot, or through a participating contractor.",
        "faq": "Con Edison offers a $1,300 instant rebate on ENERGY STAR-certified heat pump water heaters (up to 120 gallons). Purchase must happen by December 31, 2026, and the rebate is redeemed at checkout through a participating Lowe's, Home Depot, or contractor — there's no separate mail-in claim.",
        "source_name": "Con Edison heat pump water heater program",
        "source_url": "https://www.coned.com/en/save-money/rebates-incentives-tax-credits/rebates-incentives-tax-credits-for-residential-customers/electric-heating-and-cooling-technology-for-renters-homeowners/swap-your-water-heater-and-save",
    },
    "pseg": {
        "amount": "$1,200",
        "headline_amount": "Up to $1,200",
        "desc": "PSEG Long Island pays up to $1,200 for an ENERGY STAR-certified electric heat pump water heater, limited to one per account every 5 years.",
        "faq": "PSEG Long Island offers up to $1,200 for ENERGY STAR-certified electric heat pump water heaters installed in 2026, limited to one per residential account every 5 years. Income-qualified customers may see enhanced rebates plus New York State financing.",
        "source_name": "PSEG Long Island heat pump rebates",
        "source_url": "https://www.psegliny.com/en/saveenergyandmoney/homeefficiency/HomeComfort/HeatPumps/Rebates",
    },
    "national-grid": {
        "amount": "$1,250",
        "headline_amount": "Up to $1,250",
        "desc": "National Grid's instant rebate applies at checkout for a qualifying heat pump water heater at participating retailers, on top of additional NYS Clean Heat Program incentives.",
        "faq": "National Grid offers up to $1,250 in instant savings on a heat pump water heater, redeemed via a coupon code at checkout through participating Lowe's and Home Depot locations. Customers can also access additional incentives through the NYS Clean Heat Program.",
        "source_name": "National Grid electric heat pump water heaters",
        "source_url": "https://www.nationalgridus.com/Upstate-NY-Home/Energy-Saving-Programs/Electric-Heat-Pump-Water-Heaters",
    },
    "central-hudson": {
        "amount": "$1,000-$1,250",
        "headline_amount": "$1,000-$1,250",
        "desc": "Central Hudson's rebate for an energy-efficient heat pump water heater is listed at $1,000 on its own site, though NYS Clean Heat materials cite $1,250 — confirm your exact figure before budgeting.",
        "faq": "Central Hudson's own site lists a $1,000 rebate for an energy-efficient heat pump water heater, while separate NYS Clean Heat Program materials cite $1,250 for the same equipment category. Confirm the current figure on Central Hudson's residential incentives page before you buy.",
        "source_name": "Central Hudson electric heat pump water heaters",
        "source_url": "https://www.cenhud.com/en/my-energy/save-energy-money/residential-incentives/electric-heat-pump-water-heaters/",
    },
}

CITIES = {
    "con-edison": ["new-york-city", "yonkers", "mount-vernon", "new-rochelle", "white-plains"],
    "pseg": ["brookhaven", "islip", "babylon", "huntington", "smithtown", "oyster-bay", "southampton"],
    "national-grid": ["albany", "buffalo", "rochester", "syracuse"],
    "central-hudson": ["poughkeepsie", "newburgh", "kingston", "beacon", "saugerties"],
}

DISPLAY_NAMES = {
    "new-york-city": "New York City", "yonkers": "Yonkers", "mount-vernon": "Mount Vernon",
    "new-rochelle": "New Rochelle", "white-plains": "White Plains", "brookhaven": "Brookhaven",
    "islip": "Islip", "babylon": "Babylon", "huntington": "Huntington", "smithtown": "Smithtown",
    "oyster-bay": "Oyster Bay", "southampton": "Southampton", "albany": "Albany", "buffalo": "Buffalo",
    "rochester": "Rochester", "syracuse": "Syracuse", "poughkeepsie": "Poughkeepsie",
    "newburgh": "Newburgh", "kingston": "Kingston", "beacon": "Beacon", "saugerties": "Saugerties",
}

OTHER_CATEGORIES = [
    ("insulation", "Insulation & Air Sealing"),
    ("solar", "Solar"),
    ("battery", "Battery Storage"),
    ("ev-charger", "EV Charger"),
    ("windows-doors", "Windows & Doors"),
    ("smart-thermostats", "Smart Thermostats"),
]


def build_water_heater_page(template_text, utility, city_slug, display_name):
    data = UTILITY_DATA[utility]
    other_city_slugs = [c for c in CITIES[utility] if c != city_slug]

    text = template_text

    # <title>
    text = re.sub(
        r"<title>Insulation & Air Sealing Rebates in [^<]+</title>",
        f"<title>Water Heater Rebates in {display_name} 2026 | HomePowerRebate</title>",
        text,
    )
    # meta description / canonical / og tags
    text = text.replace(
        f"Insulation & Air Sealing rebates for {display_name} homeowners in 2026: Up to $4,000. Eligibility, sources, and local installers.",
        f"Water Heater rebates for {display_name} homeowners in 2026: {data['amount']}. Eligibility, sources, and local installers.",
    )
    text = text.replace(
        f"/us/ny/{utility}/{city_slug}/insulation/", f"/us/ny/{utility}/{city_slug}/water-heater/"
    )
    text = text.replace(
        f"Insulation & Air Sealing Rebates in {display_name} 2026",
        f"Water Heater Rebates in {display_name} 2026",
    )

    # Breadcrumb JSON-LD name/item
    text = text.replace(
        '"name": "Insulation & Air Sealing",', '"name": "Water Heater",'
    )

    # Article JSON-LD headline/description
    text = text.replace(
        f'"headline": "Insulation & Air Sealing Rebates in {display_name} 2026",',
        f'"headline": "Water Heater Rebates in {display_name} 2026",',
    )
    text = text.replace(
        '"description": "Everything New York City homeowners need to know about insulation & air sealing rebates.",',
        f'"description": "Everything {display_name} homeowners need to know about water heater rebates.",',
    ) if city_slug == "new-york-city" else text
    text = re.sub(
        r'"description": "Everything [^"]+ homeowners need to know about insulation & air sealing rebates\.",',
        f'"description": "Everything {display_name} homeowners need to know about water heater rebates.",',
        text,
    )

    # FAQPage JSON-LD block — replace wholesale
    old_faq_re = re.compile(
        r'<script type="application/ld\+json">\n\{\n "@context": "https://schema\.org",\n "@type": "FAQPage",.*?\n</script>',
        re.S,
    )
    new_faq = (
        '<script type="application/ld+json">\n'
        '{\n'
        ' "@context": "https://schema.org",\n'
        ' "@type": "FAQPage",\n'
        ' "mainEntity": [\n'
        '  {\n'
        '   "@type": "Question",\n'
        f'   "name": "How much is the Water Heater rebate in {display_name}?",\n'
        '   "acceptedAnswer": {\n'
        '    "@type": "Answer",\n'
        f'    "text": {repr(data["faq"]).replace(chr(39), chr(34), 1)[1:-1] if False else __import__("json").dumps(data["faq"])[1:-1]}\n'
        '   }\n'
        '  },\n'
        '  {\n'
        '   "@type": "Question",\n'
        f'   "name": "Where do I find water heater installers in {display_name}?",\n'
        '   "acceptedAnswer": {\n'
        '    "@type": "Answer",\n'
        f'    "text": "Browse real, currently-reviewed installers near {display_name} on our installer directory, or run our free assessment for a shortlist matched to your project."\n'
        '   }\n'
        '  }\n'
        ' ]\n'
        '}\n'
        '</script>'
    )
    text = old_faq_re.sub(lambda m: new_faq, text)

    # Hero amount badge + h1 + intro
    text = text.replace(">Up to $4,000</div>", f">{data['headline_amount']}</div>")
    text = re.sub(
        r"<h1>Insulation & Air Sealing Rebates in [^<]+</h1>",
        f"<h1>Water Heater Rebates in {display_name}</h1>",
        text,
    )
    text = re.sub(
        r"<p>Here&#39;s exactly how the insulation &amp; air sealing rebate works in [^,]+, plus local installers to call\.</p>",
        f"<p>Here's exactly how the water heater rebate works in {display_name} ({utility.replace('-', ' ').title()} territory), plus local installers to call.</p>",
        text,
    )
    # some pages may not have the &#39;/&amp; entities depending on how they were saved — fallback plain replace
    text = re.sub(
        r"<p>Here's exactly how the insulation & air sealing rebate works in [^,]+, plus local installers to call\.</p>",
        f"<p>Here's exactly how the water heater rebate works in {display_name} ({utility.replace('-', ' ').title()} territory), plus local installers to call.</p>",
        text,
    )

    # Sibling nav row: point everything to the OTHER categories, remove self-link, add insulation link instead of self
    nav_links = "\n".join(
        f'      <span style="margin-right:14px;"><a href="/us/ny/{utility}/{city_slug}/{slug}/">{label} in {display_name}</a></span>'
        for slug, label in OTHER_CATEGORIES
    )
    text = re.sub(
        r'<section class="wrap" style="padding:24px 28px 0;">\n  <div style="font-size:14px; line-height:2\.2;">\n.*?\n  </div>\n</section>',
        f'<section class="wrap" style="padding:24px 28px 0;">\n  <div style="font-size:14px; line-height:2.2;">\n      <span style="margin-right:14px;"><a href="/us/ny/{utility}/{city_slug}">&larr; Back to {display_name} rebate hub</a></span>\n{nav_links}\n  </div>\n</section>',
        text,
        flags=re.S,
    )

    # "How much you get" body block
    text = re.sub(
        r'<h2>How much you get</h2>\n\s*<p>Con Edison\'s "Get up to \$4,000.*?</h2>',
        (
            "<h2>How much you get</h2>\n"
            f"    <p>{data['desc']}</p>\n"
            f'    <p class="source-note">Source: <a href="{data["source_url"]}" target="_blank" rel="noopener">{data["source_name"]}</a></p>\n\n'
            "    \n\n"
            f"    <h2>Water Heater installers in {display_name}</h2>"
        ),
        text,
        flags=re.S,
    )
    # fallback simpler pattern in case the above didn't match exactly (varies per source file)
    text = re.sub(
        r'<h2>How much you get</h2>.*?<h2>Insulation & Air Sealing installers in [^<]+</h2>',
        (
            "<h2>How much you get</h2>\n"
            f"    <p>{data['desc']}</p>\n"
            f'    <p class="source-note">Source: <a href="{data["source_url"]}" target="_blank" rel="noopener">{data["source_name"]}</a></p>\n\n'
            f"    <h2>Water Heater installers in {display_name}</h2>"
        ),
        text,
        flags=re.S,
    )
    text = text.replace(
        f"We don't have verified local installer data for {display_name} in this category yet.",
        f"We don't have verified local installer data for {display_name} in this category yet.",
    )

    # Common questions section body
    text = re.sub(
        r'<h2>Common questions</h2>\n\s*<div class="faq-item">\n\s*<h3>How much is the Insulation & Air Sealing rebate in [^<]+</h3>\n\s*<p>.*?</div>\n\s*<div class="faq-item">\n\s*<h3>Is that Insulation & Air Sealing figure confirmed\?</h3>\n\s*<p>.*?</p>\n\s*</div>\n\s*<div class="faq-item">\n\s*<h3>Where do I find insulation & air sealing installers in [^<]+</h3>',
        (
            '<h2>Common questions</h2>\n'
            '    <div class="faq-item">\n'
            f'      <h3>How much is the Water Heater rebate in {display_name}?</h3>\n'
            f'      <p>{data["faq"]}</p>\n'
            '    </div>\n'
            '    <div class="faq-item">\n'
            f'      <h3>Where do I find water heater installers in {display_name}?</h3>'
        ),
        text,
        flags=re.S,
    )

    # "Other <utility> Cities" block — rebuild links to point at water-heater
    def other_cities_repl(m):
        links = "\n".join(
            f'      <a href="/us/ny/{utility}/{c}/water-heater/" style="margin-right:14px; display:inline-block;">{DISPLAY_NAMES[c]}</a>'
            for c in other_city_slugs
        )
        return f'<h2>Other {utility.replace("-", " ").title()} Cities</h2>\n    <p style="font-size:14px;">\n{links}\n    </p>'

    text = re.sub(
        rf'<h2>Other {re.escape(utility.replace("-", " ").title())} Cities</h2>\n\s*<p style="font-size:14px;">\n.*?\n\s*</p>',
        other_cities_repl,
        text,
        flags=re.S,
    )

    # "Next steps"
    text = re.sub(
        r'<h2>Next steps</h2>\n\s*<p><a href="/us/ny/[^"]+">View all [^<]+ rebate programs &rarr;</a>',
        f'<h2>Next steps</h2>\n    <p><a href="/us/ny/{utility}/{city_slug}">View all {display_name} rebate programs &rarr;</a>',
        text,
    )

    # newsletter hidden page field
    text = text.replace(
        f'value="/us/ny/{utility}/{city_slug}/insulation/"',
        f'value="/us/ny/{utility}/{city_slug}/water-heater/"',
    )

    return text


def add_sibling_links(page_path, utility, city_slug, display_name):
    """Insert a Water Heater link into the cross-nav row of an existing category page."""
    text = open(page_path, encoding="utf-8").read()
    if "water-heater" in text.split("</nav>", 1)[-1].split("<article", 1)[0] if "<article" in text else False:
        pass
    marker = f'<span style="margin-right:14px;"><a href="/us/ny/{utility}/{city_slug}/smart-thermostats/">Smart Thermostats in {display_name}</a></span>'
    new_link = f'\n      <span style="margin-right:14px;"><a href="/us/ny/{utility}/{city_slug}/water-heater/">Water Heater in {display_name}</a></span>'
    if marker in text and "Water Heater in" not in text:
        text = text.replace(marker, marker + new_link)
        open(page_path, "w", encoding="utf-8").write(text)
        return True
    return False


def add_hub_link(hub_path, utility, city_slug, display_name):
    text = open(hub_path, encoding="utf-8").read()
    if "Learn more about Water Heater" in text:
        return False
    marker = f'<li><a href="/us/ny/{utility}/{city_slug}/windows-doors/">Learn more about Windows & Doors in {display_name} &rarr;</a></li>'
    new_link = f'\n<li><a href="/us/ny/{utility}/{city_slug}/water-heater/">Learn more about Water Heater in {display_name} &rarr;</a></li>'
    if marker in text:
        text = text.replace(marker, marker + new_link)
        open(hub_path, "w", encoding="utf-8").write(text)
        return True
    return False


def main():
    created, sibling_updates, hub_updates, skipped = 0, 0, 0, []

    for utility, cities in CITIES.items():
        for city_slug in cities:
            display_name = DISPLAY_NAMES[city_slug]
            base_dir = os.path.join(ROOT, "us/ny", utility, city_slug)
            template_path = os.path.join(base_dir, "insulation", "index.html")
            if not os.path.exists(template_path):
                skipped.append(f"{city_slug}: no insulation template found")
                continue

            template_text = open(template_path, encoding="utf-8").read()
            new_page = build_water_heater_page(template_text, utility, city_slug, display_name)

            out_dir = os.path.join(base_dir, "water-heater")
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, "index.html")
            open(out_path, "w", encoding="utf-8").write(new_page)
            created += 1
            print(f"  CREATED {os.path.relpath(out_path, ROOT)}")

            for cat_slug, _ in OTHER_CATEGORIES:
                sib_path = os.path.join(base_dir, cat_slug, "index.html")
                if os.path.exists(sib_path) and add_sibling_links(sib_path, utility, city_slug, display_name):
                    sibling_updates += 1

            hub_path = os.path.join(base_dir, "index.html")
            if os.path.exists(hub_path) and add_hub_link(hub_path, utility, city_slug, display_name):
                hub_updates += 1

    print(f"\ncreated={created} sibling_nav_updates={sibling_updates} hub_updates={hub_updates}")
    if skipped:
        print("skipped:")
        for s in skipped:
            print(f"  {s}")


if __name__ == "__main__":
    main()
