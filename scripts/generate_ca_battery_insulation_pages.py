#!/usr/bin/env python3
"""
Build the missing /battery/ and /insulation/ CA city pages (found the same
way the /solar/ gap was found: a directory listing showed Bay Area has no
/battery/, and LA/San Diego/Inland Empire have no /insulation/ — 22 pages
total). Same approach as generate_ca_solar_pages.py: real 2026 research,
no copy-pasted Sacramento dollar figures, exact verbatim block swaps (not
fragile regex) to avoid the dangling-div bug caught during the solar pass.

Real facts this content is built on (WebSearch, 2026-08-30):
  - Federal 25C tax credit (30% up to $1,200/yr, covered insulation/air
    sealing) ended Dec 31, 2025 — same OBBBA law that killed the 25D solar
    credit.
  - California's HEEHRA (state implementation of federal HEAR, income-
    qualified point-of-sale rebates up to $14,000 total / $1,600 insulation
    cap) was fully reserved statewide as of Feb 24, 2026 — CLOSED to new
    applicants, not "available now."
  - Each major IOU (PG&E/SCE/SDG&E) runs its own ongoing, separate, real
    Energy Savings Assistance (ESA) Program: free weatherization/insulation
    for income-qualified households — this is NOT the exhausted HEAR funding.
  - CA's HOMES program (whole-home retrofit, up to $8,000) was not yet live
    as of May 2026 — still rolling out via the CEC.
  - SGIP (battery incentive, $2,700-$13,500 for a 13.5kWh battery, income/
    fire-zone tiered) is IOU-customer-only — municipal utility customers
    (LADWP, Glendale/Pasadena/Burbank Water & Power) are excluded from the
    standard program. This is why battery pages are only being built for
    Bay Area (PG&E) and Inland Empire (SCE) — both all-IOU groups; the LA
    cluster's municipal-utility cities were correctly left off this list.

Run from the Powerrebate root:
  python3 scripts/generate_ca_battery_insulation_pages.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (city_slug, group, display_name, utility_kind, utility_name, utility_url)
BATTERY_CITIES = [
    ("berkeley", "bay-area", "Berkeley", "iou", "PG&E", "https://www.pge.com/en/save-energy-and-money/rebates-and-incentives.html"),
    ("fremont", "bay-area", "Fremont", "iou", "PG&E", "https://www.pge.com/en/save-energy-and-money/rebates-and-incentives.html"),
    ("oakland", "bay-area", "Oakland", "iou", "PG&E", "https://www.pge.com/en/save-energy-and-money/rebates-and-incentives.html"),
    ("san-francisco", "bay-area", "San Francisco", "iou", "PG&E", "https://www.pge.com/en/save-energy-and-money/rebates-and-incentives.html"),
    ("san-jose", "bay-area", "San Jose", "iou", "PG&E", "https://www.pge.com/en/save-energy-and-money/rebates-and-incentives.html"),
    ("moreno-valley", "inland-empire", "Moreno Valley", "iou", "SCE", "https://www.sce.com/residential/rebates-savings"),
    ("ontario", "inland-empire", "Ontario", "iou", "SCE", "https://www.sce.com/residential/rebates-savings"),
    ("riverside", "inland-empire", "Riverside", "iou", "SCE", "https://www.sce.com/residential/rebates-savings"),
    ("san-bernardino", "inland-empire", "San Bernardino", "iou", "SCE", "https://www.sce.com/residential/rebates-savings"),
]

INSULATION_CITIES = [
    ("burbank", "los-angeles", "Burbank", "muni", "Burbank Water & Power", "https://www.burbankwaterandpower.com/save-money-energy/rebates-incentives"),
    ("glendale", "los-angeles", "Glendale", "muni", "Glendale Water & Power", "https://www.glendaleca.gov/government/departments/glendale-water-power/save-money-and-energy/rebate-programs"),
    ("long-beach", "los-angeles", "Long Beach", "iou", "SCE", "https://www.sce.com/residential/rebates-savings"),
    ("los-angeles", "los-angeles", "Los Angeles", "muni", "LADWP", "https://www.ladwp.com/residential-account/save-money-and-energy/rebates-and-incentives"),
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

CATEGORY_LABEL = {"battery": "Home Battery", "insulation": "Insulation"}


def battery_content(display_name, utility_kind, utility_name, utility_url):
    hero_badge = "No flat rebate — SGIP pays $2,700–$13,500 based on income & fire risk"
    how_much = f"""<p>There's no flat dollar figure for a home battery in {display_name} the way a heat pump rebate works &mdash; instead, California's <strong>Self-Generation Incentive Program (SGIP)</strong> pays a per-kWh incentive that varies by your household income and whether you're in a high fire-threat zone. For a typical 13.5kWh battery (about $12,000&ndash;$15,000 installed):</p>
    <ul>
      <li><strong>General market:</strong> a base SGIP incentive applies to any {utility_name} residential customer, no income requirement.</li>
      <li><strong>Equity tier (lower income):</strong> a meaningfully higher per-kWh rate.</li>
      <li><strong>Equity Resiliency (high fire-threat zone or medical baseline):</strong> the highest tier, sometimes covering most or all of the battery cost &mdash; this is where the $2,700&ndash;$13,500 range comes from.</li>
    </ul>
    <p>Note: the federal 30% tax credit for standalone home batteries (Section 25D) also ended for anything placed in service in 2026 or later &mdash; don't expect an installer's quote to include it.</p>
    <p>Why pair a battery with solar at all in {display_name}? Because {utility_name}'s NEM 3.0 net billing only pays you $0.04&ndash;$0.08/kWh for power you export &mdash; a fraction of retail. A battery lets you store your own solar and use it yourself at night instead of selling it cheap and buying it back expensive.</p>
    <p class="src" style="font-size:11px; color:var(--sage); font-weight:600; text-transform:uppercase; letter-spacing:.04em;">Source: CPUC Self-Generation Incentive Program, {utility_name}</p>"""
    faq = f"There's no flat rebate — California's SGIP pays a per-kWh incentive that varies by income and fire-threat zone, from a base general-market rate up to $2,700-$13,500 for a typical 13.5kWh battery at the highest equity tiers. The federal 30% tax credit for batteries ended for systems placed in service in 2026 or later."
    return hero_badge, how_much, faq


def insulation_content(display_name, utility_kind, utility_name, utility_url):
    hero_badge = "Federal credit ended — check your utility's free weatherization program"
    if utility_kind == "iou":
        how_much = f"""<p>Insulation incentives changed a lot heading into 2026 &mdash; here's what's actually true right now in {display_name}:</p>
    <ul>
      <li><strong>Federal 25C tax credit: ended.</strong> The Energy Efficient Home Improvement Credit (30% of insulation/air-sealing costs, up to $1,200/year) was terminated early by the OBBBA law, effective for anything installed after December 31, 2025.</li>
      <li><strong>HEAR / HEEHRA (income-qualified, up to $14,000 total, $1,600 insulation cap): fully reserved.</strong> California's implementation of the federal HEAR program hit its funding cap statewide on February 24, 2026, and is closed to new applicants. Check back in case a new funding round opens.</li>
      <li><strong>{utility_name}'s Energy Savings Assistance (ESA) Program: still running.</strong> This is separate from the exhausted HEAR funding &mdash; if your household is income-qualified (at or below 200% of the federal poverty guideline), {utility_name} provides free attic insulation and air sealing directly, no HEAR application needed.</li>
      <li><strong>CA HOMES program: not live yet.</strong> A separate whole-home retrofit incentive (up to $8,000 for a 35%+ modeled energy reduction) was still rolling out through the California Energy Commission as of mid-2026 &mdash; not something you can apply for yet.</li>
    </ul>
    <p class="src" style="font-size:11px; color:var(--sage); font-weight:600; text-transform:uppercase; letter-spacing:.04em;">Source: {utility_name} ESA Program, CPUC/CEC HEAR &amp; HOMES program status</p>"""
        faq = f"The federal 25C tax credit ended Dec 31, 2025. California's income-qualified HEAR/HEEHRA rebate (up to $1,600 for insulation) hit its funding cap statewide on Feb 24, 2026 and is closed. What's still real: {utility_name}'s Energy Savings Assistance Program provides free insulation and air sealing for income-qualified households (a separate, ongoing program), and CA's HOMES whole-home retrofit incentive is expected but not yet live."
    else:
        how_much = f"""<p>{display_name} is served by {utility_name}, a municipal utility separate from the big investor-owned utilities &mdash; so statewide programs tied to PG&amp;E/SCE/SDG&amp;E ratepayer funding (like the ESA weatherization program) may not apply here the same way. We haven't independently verified a current insulation-specific program for {utility_name}, so check directly: <a href="{utility_url}" target="_blank" rel="noopener">{utility_name}'s rebates &amp; incentives page &rarr;</a>.</p>
    <p>What's confirmed true regardless of your local utility:</p>
    <ul>
      <li><strong>Federal 25C tax credit: ended.</strong> The 30% insulation/air-sealing tax credit (up to $1,200/year) was terminated early by the OBBBA law, effective for anything installed after December 31, 2025.</li>
      <li><strong>HEAR / HEEHRA: fully reserved.</strong> California's income-qualified HEAR rebate (up to $1,600 for insulation) hit its statewide funding cap on February 24, 2026, and is closed to new applicants.</li>
      <li><strong>CA HOMES program: not live yet.</strong> A separate whole-home retrofit incentive was still rolling out through the California Energy Commission as of mid-2026.</li>
    </ul>
    <p class="src" style="font-size:11px; color:var(--sage); font-weight:600; text-transform:uppercase; letter-spacing:.04em;">Source: {utility_name} (program details unverified &mdash; confirm directly), CPUC/CEC HEAR &amp; HOMES program status</p>"""
        faq = f"We haven't verified a current {utility_name}-specific insulation program — check their site directly. What's confirmed statewide: the federal 25C tax credit ended Dec 31, 2025, and California's income-qualified HEAR rebate (up to $1,600 for insulation) hit its funding cap on Feb 24, 2026 and is closed to new applicants."
    return hero_badge, how_much, faq


CONTENT_FN = {"battery": battery_content, "insulation": insulation_content}


def build_page(category, city_slug, group, display_name, utility_kind, utility_name, utility_url):
    template_path = os.path.join(ROOT, f"us/ca/sacramento/sacramento/{category}/index.html")
    base = open(template_path, encoding="utf-8").read()
    label = CATEGORY_LABEL[category]

    hero_badge, how_much_you_get, faq_answer = CONTENT_FN[category](display_name, utility_kind, utility_name, utility_url)

    out = base

    # Sacramento's actual headline dollar figures per category (to find/replace)
    sac_amount = {"battery": "$5,400", "insulation": "$1,600"}[category]
    sac_faq_text_battery = "$5,400 — A 13.5kWh battery costs about $12,000 installed. SMUD's storage enrollment bonus can add up to $10,000 more (below)."

    # --- title / meta ---
    out = out.replace(
        f"<title>{label} Rebates in Sacramento 2026 | HomePowerRebate</title>",
        f"<title>{label} in {display_name} 2026: What Actually Saves You Money | HomePowerRebate</title>",
    )
    out = re.sub(
        r'<meta name="description" content="[^"]*">',
        f'<meta name="description" content="{label} for {display_name} homeowners in 2026: no flat {utility_name} rebate. Here\'s exactly what\'s real, sourced, and current instead.">',
        out, count=1,
    )
    out = out.replace(f"https://homepowerrebate.com/us/ca/sacramento/sacramento/{category}/", f"https://homepowerrebate.com/us/ca/{group}/{city_slug}/{category}/")
    out = re.sub(
        r'<meta property="og:title" content="[^"]*">',
        f'<meta property="og:title" content="{label} in {display_name} 2026: What Actually Saves You Money">',
        out, count=1,
    )
    out = re.sub(
        r'<meta property="og:description" content="[^"]*">',
        f'<meta property="og:description" content="No flat {utility_name} {label.lower()} rebate in 2026 — here\'s what actually saves you money instead.">',
        out, count=1,
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
    out = out.replace(f'https://homepowerrebate.com/us/ca/sacramento/sacramento/{category}', f'https://homepowerrebate.com/us/ca/{group}/{city_slug}/{category}')

    # --- Article schema ---
    out = re.sub(
        r'"headline": "[^"]*",',
        f'"headline": "{label} in {display_name} 2026: What Actually Saves You Money",',
        out, count=1,
    )
    out = re.sub(
        r'"description": "Everything Sacramento homeowners need to know about[^"]*",',
        f'"description": "Everything {display_name} homeowners need to know about {label.lower()} economics in 2026.",',
        out, count=1,
    )

    # --- FAQ schema: swap both the question name AND the answer text ---
    sac_faq_answer_json = {
        "battery": '"$5,400 \\u2014 A 13.5kWh battery costs about $12,000 installed. SMUD\'s storage enrollment bonus can add up to $10,000 more (below)."',
        "insulation": '"$1,600 \\u2014 Attic, wall or crawlspace insulation. Makes your heat pump smaller and cheaper to run."',
    }[category]
    old_q = f'"name": "How much is the {label} rebate in Sacramento?"'
    assert old_q in out, f"template drifted for {category} — FAQ question not found verbatim"
    out = out.replace(old_q, f'"name": "How much is the {label.lower()} rebate in {display_name}?"')
    old_answer_line = f'"text": {sac_faq_answer_json}'
    assert old_answer_line in out, f"template drifted for {category} — FAQ answer not found verbatim"
    out = out.replace(old_answer_line, f'"text": {json.dumps(faq_answer)}')

    out = re.sub(
        r'"name": "Where do I find ' + re.escape(label.lower()) + r' installers in Sacramento\?"',
        f'"name": "Where do I find {label.lower()} installers in {display_name}?"',
        out,
    )
    installer_faq_text = f"Browse real, currently-reviewed installers near {display_name} on our installer directory, or run our free assessment for a shortlist matched to your project."
    out = re.sub(
        r'"text": "Browse real, currently-reviewed installers near Sacramento[^"]*"',
        f'"text": {json.dumps(installer_faq_text)}',
        out,
    )

    # --- hero ---
    out = re.sub(r'<div class="amount-badge">[^<]*</div>', f'<div class="amount-badge">{hero_badge}</div>', out, count=1)
    out = re.sub(r'<h1>[^<]*</h1>', f'<h1>{label} in {display_name}: What Actually Saves You Money</h1>', out, count=1)
    out = re.sub(
        r"<p>Here's exactly how the [a-z ]+ rebate works in Sacramento[^<]*</p>",
        f"<p>{utility_name} doesn't offer a flat {label.lower()} rebate &mdash; here's what actually determines your real savings in {display_name}, plus local installers to call.</p>",
        out,
    )

    # --- category nav row + back link ---
    out = out.replace(
        f'<a href="/us/ca/sacramento/sacramento">&larr; Back to Sacramento rebate hub</a>',
        f'<a href="/us/ca/{group}/{city_slug}">&larr; Back to {display_name} rebate hub</a>',
    )
    out = re.sub(r'/us/ca/sacramento/sacramento/(heat-pump|battery|water-heater|insulation|ev-charger|smart-thermostats|solar)/', f'/us/ca/{group}/{city_slug}/\\1/', out)
    out = re.sub(r'in Sacramento</a>', f'in {display_name}</a>', out)

    existing_categories = {
        d for d in os.listdir(os.path.join(ROOT, "us/ca", group, city_slug))
        if os.path.isdir(os.path.join(ROOT, "us/ca", group, city_slug, d))
    }
    for cat in ["heat-pump", "battery", "water-heater", "insulation", "ev-charger", "smart-thermostats", "solar"]:
        if cat != category and cat not in existing_categories:
            out = re.sub(
                rf'\s*<span style="margin-right:14px;"><a href="/us/ca/{re.escape(group)}/{re.escape(city_slug)}/{cat}/">[^<]*</a></span>',
                '',
                out,
            )

    # --- Replace "How much you get" block: from that h2 through the src line ---
    out = re.sub(
        r'<h2>How much you get</h2>\s*<p><strong>.*?</p>\s*<p class="src"[^>]*>Source: SMUD</p>',
        f'<h2>How much you get</h2>\n    {how_much_you_get}',
        out, count=1, flags=re.S,
    )

    # --- installer section heading + intro, then strip Sacramento's hardcoded card list exactly ---
    out = out.replace(
        f'<h2>{label} installers in Sacramento</h2>\n    <p>Real companies serving Sacramento, pulled from their current Google reviews. We\'re not paid to list anyone here.</p>',
        f'<h2>{label} installers in {display_name}</h2>\n    <p>Browse real, currently-reviewed {label.lower()} installers in {display_name} on our <a href="/installers/">installer directory</a>.</p>',
    )
    sac_installer_block_with_cards = '''<div class="installer-card">
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
    sac_installer_block_link_only = '<p><a href="/installers/">Browse HVAC, solar, and electrical installers near Sacramento &rarr;</a></p>'

    if sac_installer_block_with_cards in out:
        out = out.replace(
            sac_installer_block_with_cards,
            f'<p style="margin-top: 8px;"><a href="/installers/">Browse all {display_name} installers &rarr;</a></p>',
        )
    elif sac_installer_block_link_only in out:
        out = out.replace(
            sac_installer_block_link_only,
            f'<p><a href="/installers/">Browse HVAC, solar, and electrical installers near {display_name} &rarr;</a></p>',
        )
    else:
        raise AssertionError(f"template drifted for {category} — neither known installer block found verbatim")

    out = out.replace('?city=sacramento', f'?city={city_slug}')

    # --- visible FAQ text ---
    out = re.sub(
        r'<h3>How much is the ' + re.escape(label) + r' rebate in Sacramento\?</h3>\s*<p>.*?</p>',
        f'<h3>How much is the {label.lower()} rebate in {display_name}?</h3>\n      <p>{faq_answer}</p>',
        out, count=1, flags=re.S,
    )
    out = re.sub(
        r'<h3>Where do I find ' + re.escape(label.lower()) + r' installers in Sacramento\?</h3>\s*<p>.*?</p>',
        f'<h3>Where do I find {label.lower()} installers in {display_name}?</h3>\n      <p>{installer_faq_text}</p>',
        out, count=1, flags=re.S,
    )

    # --- Next steps line ---
    out = re.sub(
        r'<p><a href="/us/ca/sacramento/sacramento">View all Sacramento rebate programs &rarr;</a> or check the official <a href="[^"]*" target="_blank" rel="noopener">[^<]*&rarr; &rarr;</a> for the current source of truth\.</p>',
        f'<p><a href="/us/ca/{group}/{city_slug}">View all {display_name} rebate programs &rarr;</a> or check the official <a href="{utility_url}" target="_blank" rel="noopener">{utility_name} rebates &amp; incentives &rarr;</a> for the current source of truth.</p>',
        out, count=1,
    )

    # --- newsletter hidden fields ---
    out = out.replace('id="newsletter-city" value="Sacramento"', f'id="newsletter-city" value="{display_name}"')
    out = re.sub(
        r'id="newsletter-page" value="/us/ca/sacramento/sacramento/[a-z-]+/"',
        f'id="newsletter-page" value="/us/ca/{group}/{city_slug}/{category}/"',
        out,
    )

    out = out.replace('href="/us/ca/sacramento/" class="city-current">Sacramento<', 'href="/us/ca/sacramento/">Sacramento<')

    return out


def run(category, cities):
    written = []
    for city_slug, group, display_name, utility_kind, utility_name, utility_url in cities:
        out_dir = os.path.join(ROOT, "us/ca", group, city_slug, category)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.html")
        html = build_page(category, city_slug, group, display_name, utility_kind, utility_name, utility_url)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        written.append(out_path)
        print(f"✓ {group}/{city_slug}/{category}/ ({utility_kind}, {utility_name})")
    return written


if __name__ == "__main__":
    all_written = []
    all_written += run("battery", BATTERY_CITIES)
    all_written += run("insulation", INSULATION_CITIES)
    print(f"\nWrote {len(all_written)} pages total")
