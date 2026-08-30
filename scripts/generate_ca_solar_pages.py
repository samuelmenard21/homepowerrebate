#!/usr/bin/env python3
"""
Build the 18 missing /solar/ category pages for CA cities that had every
other category built but not solar (found 2026-08-30 while wiring up new
installer profile pages — links to these were pointing at a 404).

Content is deliberately NOT modeled on Sacramento's SMUD-specific "$2,000
rebate" framing — real research (WebSearch, 2026-08-30) confirmed that's
wrong for these 18 cities:
  - The federal 25D 30% solar tax credit ended for systems placed in service
    in 2026+ (OBBBA terminated it early, was supposed to run through 2032).
  - PG&E, SCE, and SDG&E have NO direct residential solar equipment rebate.
    The real economics are NEM 3.0 net billing (exports paid ~$0.04-0.08/kWh,
    a fraction of retail rate) plus a property-tax exclusion for systems
    installed before Jan 1, 2027, plus a separate SGIP battery incentive
    ($2,700-$13,500, income/fire-zone tiered) that pairs with solar but isn't
    a solar rebate itself.
  - The 4 municipal utilities in the LA cluster (LADWP, Glendale Water &
    Power, Pasadena Water & Power, Burbank Water & Power) may have their own
    smaller programs, but none were verified this pass — copy says to check
    directly rather than asserting an unconfirmed number.

Run from the Powerrebate root:
  python3 scripts/generate_ca_solar_pages.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (city_slug, group, display_name, utility_kind, utility_name, utility_url)
# utility_kind: "iou" (PG&E/SCE/SDG&E, no direct rebate, use standard block)
#               "muni" (own small utility, unverified rebate, use caution block)
CITIES = [
    ("berkeley", "bay-area", "Berkeley", "iou", "PG&E", "https://www.pge.com/en/save-energy-and-money/rebates-and-incentives.html"),
    ("fremont", "bay-area", "Fremont", "iou", "PG&E", "https://www.pge.com/en/save-energy-and-money/rebates-and-incentives.html"),
    ("oakland", "bay-area", "Oakland", "iou", "PG&E", "https://www.pge.com/en/save-energy-and-money/rebates-and-incentives.html"),
    ("san-francisco", "bay-area", "San Francisco", "iou", "PG&E", "https://www.pge.com/en/save-energy-and-money/rebates-and-incentives.html"),
    ("san-jose", "bay-area", "San Jose", "iou", "PG&E", "https://www.pge.com/en/save-energy-and-money/rebates-and-incentives.html"),
    ("burbank", "los-angeles", "Burbank", "muni", "Burbank Water & Power", "https://www.burbankwaterandpower.com/save-money-energy/rebates-incentives"),
    ("glendale", "los-angeles", "Glendale", "muni", "Glendale Water & Power", "https://www.glendaleca.gov/government/departments/glendale-water-power/save-money-and-energy/rebate-programs"),
    ("long-beach", "los-angeles", "Long Beach", "iou", "SCE", "https://www.sce.com/residential/rebates-savings"),
    ("los-angeles", "los-angeles", "Los Angeles", "muni", "LADWP", "https://www.ladwp.com/residential-account/save-money-and-energy/solar"),
    ("pasadena", "los-angeles", "Pasadena", "muni", "Pasadena Water & Power", "https://www.pasadenawaterandpower.com/save/rebates/"),
    ("santa-monica", "los-angeles", "Santa Monica", "iou", "SCE", "https://www.sce.com/residential/rebates-savings"),
    ("chula-vista", "san-diego", "Chula Vista", "iou", "SDG&E", "https://www.sdge.com/residential/savings-center/rebates-and-incentives"),
    ("escondido", "san-diego", "Escondido", "iou", "SDG&E", "https://www.sdge.com/residential/savings-center/rebates-and-incentives"),
    ("san-diego", "san-diego", "San Diego", "iou", "SDG&E", "https://www.sdge.com/residential/savings-center/rebates-and-incentives"),
    ("moreno-valley", "inland-empire", "Moreno Valley", "iou", "SCE", "https://www.sce.com/residential/rebates-savings"),
    ("ontario", "inland-empire", "Ontario", "iou", "SCE", "https://www.sce.com/residential/rebates-savings"),
    ("riverside", "inland-empire", "Riverside", "iou", "SCE", "https://www.sce.com/residential/rebates-savings"),
    ("san-bernardino", "inland-empire", "San Bernardino", "iou", "SCE", "https://www.sce.com/residential/rebates-savings"),
]

TEMPLATE_PATH = os.path.join(ROOT, "us/ca/sacramento/sacramento/solar/index.html")


def build_page(city_slug, group, display_name, utility_kind, utility_name, utility_url):
    base = open(TEMPLATE_PATH, encoding="utf-8").read()

    # --- content blocks, honest per utility_kind ---
    if utility_kind == "iou":
        headline_amount = "No flat rebate"
        hero_badge = "No direct rebate — here's what actually saves you money"
        how_much_you_get = f"""<p>{utility_name} doesn't offer a flat dollar rebate for installing solar panels in {display_name} &mdash; that changed years ago, and the federal 30% tax credit for homeowner-owned systems also ended for anything placed in service in 2026 or later (the OBBBA law terminated it early; it was originally supposed to run through 2032). If a quote from an installer includes either of these as a discount, ask them to show you exactly where it comes from.</p>
    <p>What's real in 2026:</p>
    <ul>
      <li><strong>NEM 3.0 net billing:</strong> {utility_name} pays you for the electricity your panels send back to the grid, but at the utility's "avoided cost" &mdash; roughly $0.04&ndash;$0.08/kWh &mdash; not the full retail rate you pay for the power you use. The real savings come from using your own solar power directly, not from selling it back.</li>
      <li><strong>Property tax exclusion:</strong> home solar systems installed before January 1, 2027 are excluded from the property tax reassessment that would normally apply to a home improvement this size &mdash; a real, time-limited reason not to wait if you're already planning to install.</li>
      <li><strong>SGIP battery incentive (separate from solar):</strong> if you pair solar with a home battery, California's Self-Generation Incentive Program pays $2,700&ndash;$13,500 depending on your income tier and whether you're in a high fire-threat zone &mdash; this is what actually makes exporting less necessary, since you use your own power at night instead of buying it back at retail.</li>
    </ul>
    <p class="src" style="font-size:11px; color:var(--sage); font-weight:600; text-transform:uppercase; letter-spacing:.04em;">Source: {utility_name}, CPUC NEM 3.0/Net Billing Tariff, CA Self-Generation Incentive Program</p>"""
        faq_answer = f"{utility_name} doesn't offer a flat solar rebate. Your real savings come from NEM 3.0 net billing (using your own power instead of buying it at retail), a property tax exclusion for systems installed before Jan 1, 2027, and a separate SGIP battery incentive ($2,700-$13,500) if you pair solar with storage. The federal 30% tax credit ended for systems placed in service in 2026 or later."
    else:  # muni
        headline_amount = "Check directly"
        hero_badge = f"{utility_name} runs its own program — verify current details"
        how_much_you_get = f"""<p>{display_name} is served by {utility_name}, a municipal utility separate from the big investor-owned utilities (PG&amp;E/SCE/SDG&amp;E) &mdash; which means its solar program, if any, is set locally and can differ from what you'll read about California solar rebates generally. We haven't independently verified a current dollar figure for {utility_name}'s residential solar program, so rather than guess, check directly before you budget around a specific number: <a href="{utility_url}" target="_blank" rel="noopener">{utility_name}'s rebates &amp; incentives page &rarr;</a>.</p>
    <p>What's confirmed true regardless of your local utility:</p>
    <ul>
      <li><strong>Federal 30% tax credit ended:</strong> for systems placed in service in 2026 or later, the federal homeowner solar tax credit (Section 25D) is no longer available &mdash; the OBBBA law terminated it early, cutting short what was meant to run through 2032.</li>
      <li><strong>Property tax exclusion:</strong> home solar systems installed before January 1, 2027 are excluded from the property tax reassessment a home improvement this size would normally trigger.</li>
      <li><strong>SGIP battery incentive (separate from solar):</strong> California's Self-Generation Incentive Program pays $2,700&ndash;$13,500 for a home battery, depending on income tier and fire-threat zone, if you pair it with solar.</li>
    </ul>
    <p class="src" style="font-size:11px; color:var(--sage); font-weight:600; text-transform:uppercase; letter-spacing:.04em;">Source: {utility_name} (program details unverified &mdash; confirm directly), CA Self-Generation Incentive Program</p>"""
        faq_answer = f"{utility_name} runs its own municipal program separate from PG&E/SCE/SDG&E, and we haven't independently verified a current dollar figure for it — check {utility_name}'s own rebates page for the current number. What's confirmed statewide: the federal 30% tax credit ended for systems placed in service in 2026+, a property tax exclusion applies to systems installed before Jan 1, 2027, and a separate SGIP battery incentive ($2,700-$13,500) is available if you pair solar with storage."

    out = base

    # --- title / meta ---
    out = out.replace(
        "<title>Solar Rebates in Sacramento 2026 | HomePowerRebate</title>",
        f"<title>Solar in {display_name} 2026: What Actually Saves You Money | HomePowerRebate</title>",
    )
    out = out.replace(
        'content="Solar rebates for Sacramento homeowners in 2026: $2,000. Eligibility, how to apply, and local installers."',
        f'content="Solar for {display_name} homeowners in 2026: no flat {utility_name} rebate, but real savings from NEM 3.0 net billing, a property tax exclusion, and SGIP battery incentives. Here\'s exactly how the math works."',
    )
    out = out.replace(
        f'https://homepowerrebate.com/us/ca/sacramento/sacramento/solar/',
        f'https://homepowerrebate.com/us/ca/{group}/{city_slug}/solar/',
    )
    out = out.replace(
        "<meta property=\"og:title\" content=\"Solar Rebates in Sacramento 2026\">",
        f'<meta property="og:title" content="Solar in {display_name} 2026: What Actually Saves You Money">',
    )
    out = out.replace(
        'content="How much rebate you get for solar in Sacramento: $2,000."',
        f'content="No flat {utility_name} solar rebate in 2026 — here\'s what actually saves you money instead."',
    )

    # --- breadcrumbs ---
    out = re.sub(
        r'"name": "Sacramento",\s*\n\s*"item": "https://homepowerrebate\.com/us/ca/sacramento"',
        f'"name": "{group.replace("-", " ").title()}",\n   "item": "https://homepowerrebate.com/us/ca/{group}"',
        out,
    )
    out = re.sub(
        r'"name": "Sacramento",\s*\n\s*"item": "https://homepowerrebate\.com/us/ca/sacramento/sacramento"',
        f'"name": "{display_name}",\n   "item": "https://homepowerrebate.com/us/ca/{group}/{city_slug}"',
        out,
    )
    out = out.replace(
        'https://homepowerrebate.com/us/ca/sacramento/sacramento/solar',
        f'https://homepowerrebate.com/us/ca/{group}/{city_slug}/solar',
    )

    # --- Article schema ---
    out = out.replace(
        '"headline": "Solar Rebates in Sacramento 2026",',
        f'"headline": "Solar in {display_name} 2026: What Actually Saves You Money",',
    )
    out = out.replace(
        '"description": "Everything Sacramento homeowners need to know about solar rebates.",',
        f'"description": "Everything {display_name} homeowners need to know about solar economics in 2026 &mdash; no flat rebate, but real NEM 3.0, tax, and battery incentives.",',
    )

    # --- FAQ schema ---
    out = out.replace(
        f'"name": "How much is the Solar rebate in Sacramento?",',
        f'"name": "How much is the solar rebate in {display_name}?",',
    )
    out = out.replace(
        '"text": "$2,000 \\u2014 A 6kW system runs $15,000\\u2013$18,000. Saves about $1,400/year \\u2014 roughly an 11-year payback, one of the fastest in the state."',
        f'"text": {json.dumps(faq_answer)}',
    )
    out = out.replace(
        'name": "Where do I find solar installers in Sacramento?"',
        f'name": "Where do I find solar installers in {display_name}?"',
    )
    installer_faq_text = f"Browse real, currently-reviewed installers near {display_name} on our installer directory, or run our free assessment for a shortlist matched to your project."
    out = out.replace(
        '"text": "Browse real, currently-reviewed installers near Sacramento on our installer directory, or run our free assessment for a shortlist matched to your project."',
        f'"text": {json.dumps(installer_faq_text)}',
    )

    # --- hero ---
    out = out.replace('<div class="amount-badge">$2,000</div>', f'<div class="amount-badge">{hero_badge}</div>')
    out = out.replace("<h1>Solar Rebates in Sacramento</h1>", f"<h1>Solar in {display_name}: What Actually Saves You Money</h1>")
    out = out.replace(
        "<p>Here's exactly how the solar rebate works in Sacramento, plus local installers to call.</p>",
        f"<p>{utility_name} doesn't offer a flat solar rebate &mdash; here's what actually determines your real savings in {display_name}, plus local installers to call.</p>",
    )

    # --- category nav row + back link ---
    out = out.replace(
        f'<a href="/us/ca/sacramento/sacramento">&larr; Back to Sacramento rebate hub</a>',
        f'<a href="/us/ca/{group}/{city_slug}">&larr; Back to {display_name} rebate hub</a>',
    )
    out = re.sub(r'/us/ca/sacramento/sacramento/(heat-pump|battery|water-heater|insulation|ev-charger|smart-thermostats)/', f'/us/ca/{group}/{city_slug}/\\1/', out)
    out = re.sub(r'in Sacramento</a>', f'in {display_name}</a>', out)

    # Drop nav-row links to categories that don't exist for this city yet —
    # Bay Area cities have no /battery/, LA/San Diego/Inland Empire cities
    # have no /insulation/ (a pre-existing site gap, confirmed by directory
    # listing; not something this pass is building). Linking to a 404 from a
    # brand-new page would be worse than just omitting the category.
    existing_categories = {
        d for d in os.listdir(os.path.join(ROOT, "us/ca", group, city_slug))
        if os.path.isdir(os.path.join(ROOT, "us/ca", group, city_slug, d))
    }
    for cat in ["heat-pump", "battery", "water-heater", "insulation", "ev-charger", "smart-thermostats"]:
        if cat not in existing_categories:
            out = re.sub(
                rf'\s*<span style="margin-right:14px;"><a href="/us/ca/{re.escape(group)}/{re.escape(city_slug)}/{cat}/">[^<]*</a></span>',
                '',
                out,
            )

    # --- main content: replace "How much you get" block + installers list + FAQ visible text + next steps ---
    out = re.sub(
        r'<h2>How much you get</h2>\s*<p><strong>\$2,000</strong>.*?Source: SMUD</p>',
        f'<h2>How much you get</h2>\n    {how_much_you_get}',
        out, flags=re.S,
    )
    # Replace the ENTIRE Sacramento installer section (heading through the
    # "See all X installers" line) as one exact block swap — a partial regex
    # here previously left dangling unclosed <div> tags from the hardcoded
    # Sacramento installer-card list (each card has nested divs, so a
    # non-greedy ".*?</div>" only strips down to the FIRST inner </div>, not
    # the real end of the card — caught by reading the generated output).
    sacramento_installer_block = '''<h2>Solar installers in Sacramento</h2>
    <p>Real companies serving Sacramento, pulled from their current Google reviews. We're not paid to list anyone here.</p>
    <div class="installer-card">
  <div><div class="name">Premium Solar Cleaning</div><div class="stars">&#9733; 5.0 (51 reviews)</div></div>
  <a class="site-link" href="http://premiumsolarcleaning.com/" target="_blank" rel="noopener">Visit site &rarr;</a>
</div>
    <div class="installer-card">
  <div><div class="name">Panel Pros - Solar Cleaning and Maintenance</div><div class="stars">&#9733; 5.0 (45 reviews)</div></div>
  <a class="site-link" href="http://panel-pros.com/" target="_blank" rel="noopener">Visit site &rarr;</a>
</div>
    <div class="installer-card">
  <div><div class="name">Five Star Solar</div><div class="stars">&#9733; 4.9 (358 reviews)</div></div>
  <a class="site-link" href="http://www.fivestarssolar.com/" target="_blank" rel="noopener">Visit site &rarr;</a>
</div>
    <div class="installer-card">
  <div><div class="name">EnergyAid</div><div class="stars">&#9733; 4.8 (770 reviews)</div></div>
  <a class="site-link" href="https://www.energyaid.net/norcal" target="_blank" rel="noopener">Visit site &rarr;</a>
</div>
    <p style="margin-top: 8px;"><a href="/installers/">See all Sacramento installers &rarr;</a></p>'''
    assert sacramento_installer_block in out, "template drifted — Sacramento installer block not found verbatim"
    replacement_block = f'''<h2>Solar installers in {display_name}</h2>
    <p>Browse real, currently-reviewed solar installers in {display_name} on our <a href="/installers/">installer directory</a>.</p>
    <p style="margin-top: 8px;"><a href="/installers/">Browse all {display_name} installers &rarr;</a></p>'''
    out = out.replace(sacramento_installer_block, replacement_block)
    out = out.replace('?city=sacramento', f'?city={city_slug}')
    out = out.replace(
        '<h3>How much is the Solar rebate in Sacramento?</h3>\n      <p>$2,000 — A 6kW system runs $15,000–$18,000. Saves about $1,400/year — roughly an 11-year payback, one of the fastest in the state.</p>',
        f'<h3>How much is the solar rebate in {display_name}?</h3>\n      <p>{faq_answer}</p>',
    )
    out = out.replace(
        f'<h3>Where do I find solar installers in Sacramento?</h3>\n      <p>Browse real, currently-reviewed installers near Sacramento on our installer directory, or run our free assessment for a shortlist matched to your project.</p>',
        f'<h3>Where do I find solar installers in {display_name}?</h3>\n      <p>Browse real, currently-reviewed installers near {display_name} on our installer directory, or run our free assessment for a shortlist matched to your project.</p>',
    )
    out = out.replace(
        f'<p><a href="/us/ca/sacramento/sacramento">View all Sacramento rebate programs &rarr;</a> or check the official <a href="https://www.smud.org/en/Rebates-Incentives-and-Financing" target="_blank" rel="noopener">SMUD rebates &amp; incentives &rarr; &rarr;</a> for the current source of truth.</p>',
        f'<p><a href="/us/ca/{group}/{city_slug}">View all {display_name} rebate programs &rarr;</a> or check the official <a href="{utility_url}" target="_blank" rel="noopener">{utility_name} rebates &amp; incentives &rarr;</a> for the current source of truth.</p>',
    )

    # --- newsletter hidden fields ---
    out = out.replace('id="newsletter-city" value="Sacramento"', f'id="newsletter-city" value="{display_name}"')
    out = out.replace(
        'id="newsletter-page" value="/us/ca/sacramento/sacramento/solar/"',
        f'id="newsletter-page" value="/us/ca/{group}/{city_slug}/solar/"',
    )

    # --- city-picker: highlight current city if present (Sacramento was pre-highlighted; strip that, don't add per-city highlight, not worth the complexity) ---
    out = out.replace('href="/us/ca/sacramento/" class="city-current">Sacramento<', 'href="/us/ca/sacramento/">Sacramento<')

    return out


if __name__ == "__main__":
    for city_slug, group, display_name, utility_kind, utility_name, utility_url in CITIES:
        out_dir = os.path.join(ROOT, "us/ca", group, city_slug, "solar")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.html")
        html = build_page(city_slug, group, display_name, utility_kind, utility_name, utility_url)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✓ {group}/{city_slug}/solar/ ({utility_kind}, {utility_name})")
    print(f"\nWrote {len(CITIES)} solar pages")
