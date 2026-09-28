#!/usr/bin/env python3
"""NY-only, one-off + idempotent: correct us/ny/index.html against data/verified-facts/ny.json."""
import json, re
from pathlib import Path

P = Path(__file__).resolve().parent.parent / 'us/ny/index.html'
t = P.read_text(encoding='utf-8')
MANUAL = 'https://cleanheat.ny.gov/assets/pdf/NYS%20Clean%20Heat%20Program%20Manual%202025_v2.pdf'


def sub(old, new, count=1):
    global t
    if old in t:
        t = t.replace(old, new, count)
    elif new not in t:
        raise SystemExit('anchor missing: ' + old[:80])


# ---- head ----
t = re.sub(r'<title>.*?</title>', '<title>NY State Energy Rebates 2026: Heat Pumps &amp; More</title>', t, count=1, flags=re.S)
DESC = 'New York energy rebates for 2026: NYS Clean Heat pays up to $10,000-$12,000 for a heat pump, PSEG LI $4,000-$7,500, plus EmPower+ for lower incomes.'
t = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{DESC}">', t, count=1)
t = re.sub(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="NY State Energy Rebates 2026: Heat Pumps &amp; More">', t, count=1)
t = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{DESC}">', t, count=1)

FAQ = [
 ('What energy rebates can I get in New York State in 2026?',
  'The biggest is the heat pump rebate from your electric utility. Con Edison, National Grid, NYSEG, RG&E, Central Hudson and Orange & Rockland run it as NYS Clean Heat, paying about $8,000 to $12,000 for a whole-home switch. PSEG Long Island pays $4,000 to $7,500. Lower-income households can also get free or half-price upgrades through EmPower+, and NYSERDA Comfort Home pays $2,500 to $3,000 toward insulation.'),
 ('Can I stack NYS Clean Heat with my utility rebate?',
  'No. NYS Clean Heat is the heat pump rebate your utility pays, so it is one rebate, not two. You can combine it with EmPower+ help if your income qualifies.'),
 ('Is there a federal HEAR rebate I can apply for in New York?',
  'Not as a separate cheque. New York delivers the federal Home Energy Rebates to income-eligible households through EmPower+ and NYSERDA\'s Appliance Upgrade Program.'),
 ('Are the federal 25C and 25D tax credits still available?',
  'No. They ended for anything installed after December 31, 2025.'),
 ('Who can use EmPower+?',
  'Lower-income owners and renters of 1-4 family homes anywhere in New York State. Low-income households can get free upgrades up to $12,000 upstate or $14,000 downstate; moderate-income households get 50% covered up to $6,000 upstate or $7,000 downstate.'),
]
faq_ld = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
    {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQ]}
art_ld = {'@context': 'https://schema.org', '@type': 'Article', 'headline': 'New York State Energy Rebates 2026: Heat Pumps and More',
          'description': DESC, 'datePublished': '2026-08-17', 'dateModified': '2026-09-26',
          'author': {'@type': 'Person', 'name': 'Sam Menard', 'url': 'https://homepowerrebate.com/about'},
          'publisher': {'@type': 'Organization', 'name': 'HomePowerRebate'}, 'mainEntityOfPage': 'https://homepowerrebate.com/us/ny/'}
t = re.sub(r'<script type="application/ld\+json">\s*\{\s*"@context": "https://schema.org",\s*"@type": "(FAQPage|Article)"[\s\S]*?</script>\s*', '', t)
t = t.replace('</head>', '<script type="application/ld+json">\n' + json.dumps(faq_ld, indent=1) + '\n</script>\n'
              '<script type="application/ld+json">\n' + json.dumps(art_ld, indent=1) + '\n</script>\n</head>', 1)

# ---- hero + stack box ----
HERO = '''<section class="hero">
  <div class="wrap">
    <h1>New York State Energy Rebates 2026</h1>
    <p>Heat pump, insulation, water heater, solar and EV rebates for New York homeowners &mdash; checked against NYSERDA and each utility on September 26, 2026.</p>
    <a href="#cities" class="cta">See your city&rsquo;s rebates</a>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="alert-box">
      <strong>Short answer:</strong> In New York, your electric utility decides your heat pump rebate. Con Edison, National Grid, NYSEG, RG&amp;E, Central Hudson and O&amp;R run <strong>NYS Clean Heat</strong>, which pays about <strong>$8,000&ndash;$12,000</strong> for a whole-home switch. PSEG Long Island pays <strong>$4,000&ndash;$7,500</strong>. Clean Heat <em>is</em> the utility rebate &mdash; it doesn&rsquo;t stack on top of it. Lower-income households can get far more through EmPower+. The federal 25C/25D tax credits ended December 31, 2025.
    </div>
  </div>
</section>
'''
a = t.index('<section class="hero">')
b = t.index('<section class="section" style="background: var(--paper-warm);">', a)
if 'New York State Energy Rebates 2026</h1>' not in t[a:b]:
    t = t[:a] + HERO + '\n' + t[b:]

sub('<h2 style="text-align: center; margin-bottom: 32px;">See Your Rebate Stack</h2>',
    '<h2 style="text-align: center; margin-bottom: 32px;">How much is the heat pump rebate for your utility?</h2>')
sub('<div style="font-size: 14px; color: var(--ink-soft); line-height: 1.6;" id="ny-rebate-info">\n          Utility + state + federal stacking available.',
    '<div style="font-size: 14px; color: var(--ink-soft); line-height: 1.6;" id="ny-rebate-info">\n          Pick a utility.')
sub('<div style="font-size: 13px; color: var(--ink-soft); margin-bottom: 4px;">Total Rebate Stack:</div>',
    '<div style="font-size: 13px; color: var(--ink-soft); margin-bottom: 4px;">Whole-home heat pump rebate (single-family):</div>')
sub('id="ny-rebate-amount">$14,000–$28,000+</div>', 'id="ny-rebate-amount">&mdash;</div>')
sub('          Includes: Utility rebate + NYS Clean Heat + Federal HEAR (authorized through 2030, subject to change)',
    '          One rebate from your utility. Capped at 70% of cost (85% in a Disadvantaged Community) for NYS Clean Heat. Income-eligible homes can add EmPower+.')
sub('↑ Select your utility to see your stacking total', '↑ Select your utility to see its heat pump rebate')

JS_OLD_START = 'const nyUtilityData = {'
i = t.index(JS_OLD_START); j = t.index('};', i) + 2
t = t[:i] + '''const nyUtilityData = {
  coned: { rebate: 'Up to $10,000', info: 'NYS Clean Heat via Con Edison: $7,000 standard or $10,000 weatherized tier ($8,000 / $11,000 in a Disadvantaged Community). Taken off your contractor invoice.', link: '/us/ny/con-edison/' },
  ng: { rebate: 'Up to $10,000', info: 'NYS Clean Heat via National Grid: $6,000 whole-home, $10,000 if you remove the old system ($8,000 / $12,000 in a Disadvantaged Community). Buffalo, Syracuse, Albany.', link: '/us/ny/national-grid/' },
  nyseg: { rebate: 'Up to $10,000', info: 'NYS Clean Heat via NYSEG or RG&E (Rochester): $6,000 whole-home, $10,000 if you remove the old system. NYSEG DAC homes get up to $11,000.', link: '/us/ny/national-grid/rochester/' },
  ch: { rebate: 'Up to $8,000', info: 'NYS Clean Heat via Central Hudson: $5,000 whole-home, $8,000 if you remove the old system.', link: '/us/ny/central-hudson/' },
  or: { rebate: 'Up to $9,000', info: 'NYS Clean Heat via Orange & Rockland: $5,000 whole-home, $9,000 if you remove the old system ($6,000 / $10,000 in a Disadvantaged Community).', link: '/us/ny/' },
  pseg: { rebate: '$4,000–$7,500', info: 'PSEG Long Island (not part of NYS Clean Heat): $4,000 market rate, $5,000 moderate income or DAC, $7,500 low income.', link: '/us/ny/pseg/' }
};''' + t[j:]

sub('<h2>7 New York Utility Territories</h2>', '<h2 id="cities">Pick your utility and city</h2>')
sub('<p>Your rebate amount depends on which utility you\'re served by. Pick your territory to see your options.</p>',
    '<p>Your rebate depends on the utility named on your electric bill. Note: the City of Rochester is served by RG&amp;E, not National Grid &mdash; its page is listed under National Grid but shows RG&amp;E&rsquo;s amounts.</p>')
sub('Upstate NY &middot; 6 cities</span></a>', 'Buffalo, Syracuse, Albany + Rochester (RG&amp;E) &middot; 4 cities</span></a>')

# ---- rebate finder corrections ----
sub('Con Edison, PSEG Long Island, National Grid, and Central Hudson each run their own program with their own dollar amounts. Filter by category, or scroll to your utility\'s group below. Figures shown are the utility-only rebate; add NYS Clean Heat and federal HEAR on top where eligible (see the stacking box above).',
    'Con Edison, PSEG Long Island, National Grid and Central Hudson each run their own program with their own dollar amounts. Filter by category, or scroll to your utility&rsquo;s group below. The heat pump figures <em>are</em> the NYS Clean Heat amounts (PSEG Long Island runs its own) &mdash; don&rsquo;t add Clean Heat on top.')
sub('''<div class="finder-amount">$2,000&ndash;$10,000</div>
          <p>Income-tiered utility rebate. EmPower+ covers 100% of cost (up to $14,000) for qualifying low-income NYC households.</p>''',
    '''<div class="finder-amount">Up to $10,000</div>
          <p>NYS Clean Heat via Con Edison: $7,000 standard, $10,000 weatherized tier; $8,000/$11,000 in a Disadvantaged Community. Lower-income households can also use EmPower+.</p>''')
sub('<p>Combined with NY-Sun and federal solar tax credit; varies by system size.</p>',
    '<p>NY-Sun Affordable Solar pays $0.80/W to income-eligible homes in Con Edison territory. The federal 25D solar credit ended December 31, 2025.</p>')
sub('''<div class="finder-amount">Up to $4,000</div>
          <p>Bundled with the insulation / building-envelope tier above.</p>''',
    '''<div class="finder-amount">Via Comfort Home</div>
          <p>No standalone Con Edison window rebate confirmed. NYSERDA Comfort Home adds $2,000 for windows on top of a seal-and-insulate package.</p>''')
sub('''<div class="finder-amount">Up to $400</div>
          <p>Level 2 home charger incentive; some installs qualify for $0 if panel capacity requires no upgrade credit.</p>''',
    '''<div class="finder-amount">~$400/yr reward</div>
          <p>No rebate on the charger itself. SmartCharge New York pays about $400 a year on average for off-peak charging.</p>''')
sub('<h4>Home EV charger rebate</h4>\n          <div class="finder-amount">~$400/yr reward</div>', '<h4>SmartCharge New York</h4>\n          <div class="finder-amount">~$400/yr reward</div>')
sub('<p>Income-tiered; most Long Island households qualify for the full $7,500.</p>',
    '<p>$4,000 market rate; $5,000 for moderate income (under 80% AMI) or DAC homes; $7,500 for low income (under 60% AMI).</p>')
sub('<p>PSEG does not currently rebate rooftop solar directly &mdash; NY-Sun incentives and the federal tax credit still apply, so it\'s a savings play rather than a rebate one here.</p>',
    '<p>PSEG does not rebate rooftop solar directly. NY-Sun Affordable Solar pays $0.40/W to income-eligible Long Island homes; the federal 25D credit ended December 31, 2025.</p>')
sub('''<div class="finder-amount">$1,500&ndash;$6,000</div>
          <p>Tiered by coverage and income; a partial heat pump can qualify at the lower end.</p>''',
    '''<div class="finder-amount">Up to $10,000</div>
          <p>NYS Clean Heat via National Grid: $4,000 partial, $6,000 whole-home, $10,000 with removal of the old system ($12,000 in a DAC).</p>''')
sub('<p>Stacks with NY-Sun and the federal solar tax credit.</p>',
    '<p>Check NY-Sun&rsquo;s current upstate block with your installer. The federal 25D solar credit ended December 31, 2025.</p>')
sub('<p>National Grid\'s EV charger incentive is the thinnest of the four utilities &mdash; most Buffalo/Rochester/Syracuse homeowners see little to no rebate here.</p>',
    '<p>National Grid&rsquo;s EV charger incentive is small &mdash; most Buffalo, Syracuse and Albany homeowners see little to no rebate here.</p>')
sub('<p>The largest heat-pump-only utility rebate of the four, before Clean Heat and HEAR are stacked on top.</p>',
    '<p>NYS Clean Heat via Central Hudson: $5,000 whole-home, $8,000 with removal of the old system.</p>')
sub('<p>Together with the heat pump rebate, the two largest utility rebates in Central Hudson territory ($8,000 + $1,250 = $9,250 combined).</p>',
    '<p>NYS Clean Heat pays $1,250 per heat pump water heater in Central Hudson territory.</p>')
sub('Every one of the 21 cities we cover has its own page with the full stack (utility + NYS Clean Heat + federal HEAR) worked out for that address.',
    'Every one of the 21 cities we cover has its own page with the verified amounts for that utility.')

# ---- stacking advantage + FAQ ----
a = t.index('<section class="section">\n  <div class="wrap">\n    <h2>The Stacking Advantage') if 'The Stacking Advantage' in t else -1
if a >= 0:
    b = t.index('<section class="section">\n  <div class="wrap">\n    <h2>Read More</h2>', a)
    rows = [('Con Edison (NYC, Westchester)', 'NYS Clean Heat', '$7,000&ndash;$10,000', '$8,000&ndash;$11,000'),
            ('National Grid (Buffalo, Syracuse, Albany)', 'NYS Clean Heat', '$6,000&ndash;$10,000', '$8,000&ndash;$12,000'),
            ('NYSEG', 'NYS Clean Heat', '$6,000&ndash;$10,000', '$7,000&ndash;$11,000'),
            ('RG&amp;E (Rochester)', 'NYS Clean Heat', '$6,000&ndash;$10,000', '$6,000&ndash;$10,000'),
            ('Central Hudson (Hudson Valley)', 'NYS Clean Heat', '$5,000&ndash;$8,000', 'not listed separately'),
            ('Orange &amp; Rockland', 'NYS Clean Heat', '$5,000&ndash;$9,000', '$6,000&ndash;$10,000'),
            ('PSEG Long Island', 'PSEG LI rebates', '$4,000 (up to $7,500 by income)', '$5,000')]
    tr = ''.join(f'<tr><td>{a1}</td><td>{b1}</td><td>{c1}</td><td>{d1}</td></tr>' for a1, b1, c1, d1 in rows)
    faq_html = ''.join(f'<div class="faq-item"><div class="faq-q">{q}</div><div class="faq-a">{a2.replace("&", "&amp;")}</div></div>' for q, a2 in FAQ)
    NEW = f'''<section class="section">
  <div class="wrap">
    <h2>NY heat pump rebates by utility (2026)</h2>
    <p>Single-family, whole-home cold-climate heat pump. The higher number is for removing your old oil, gas or propane system. Apartments and homes under 1,000 sq ft get less.</p>
    <div style="overflow-x:auto;"><table style="width:100%; border-collapse:collapse; font-size:15px; background:#fff;">
      <thead><tr style="background:var(--paper-warm);"><th style="text-align:left; padding:8px; border:1px solid var(--rule);">Utility</th><th style="text-align:left; padding:8px; border:1px solid var(--rule);">Program</th><th style="text-align:left; padding:8px; border:1px solid var(--rule);">Standard</th><th style="text-align:left; padding:8px; border:1px solid var(--rule);">Disadvantaged Community</th></tr></thead>
      <tbody>{tr.replace('<td>', '<td style="padding:8px; border:1px solid var(--rule);">')}</tbody>
    </table></div>
    <h2 style="margin-top:36px;">What stacks in New York &mdash; and what doesn&rsquo;t</h2>
    <ul>
      <li><strong>Stacks:</strong> your utility heat pump rebate + EmPower+ (if your income qualifies) + NYSERDA Comfort Home for insulation + a separate heat pump water heater rebate ($1,000&ndash;$1,250).</li>
      <li><strong>Doesn&rsquo;t stack:</strong> &ldquo;utility rebate + NYS Clean Heat&rdquo; &mdash; they are the same money.</li>
      <li><strong>No separate federal HEAR cheque:</strong> New York routes the federal Home Energy Rebates through <a href="/blog/new-york-empower-plus-guide/">EmPower+</a> and NYSERDA&rsquo;s Appliance Upgrade Program for income-eligible households.</li>
      <li><strong>Ended:</strong> the federal 25C and 25D tax credits, for anything installed after December 31, 2025.</li>
      <li><strong>Capped:</strong> NYS Clean Heat pays at most 70% of the project cost (85% in a Disadvantaged Community). Nobody gets paid to install a heat pump.</li>
    </ul>
    <h2 style="margin-top:36px;">What to do next</h2>
    <ol>
      <li>Find your utility on your electric bill, then open your city page above.</li>
      <li>Check the <a href="https://www.nyserda.ny.gov/ny/Disadvantaged-Communities" rel="noopener">Disadvantaged Community map</a> &mdash; it can raise your rebate.</li>
      <li>If money is tight, apply to <a href="/blog/new-york-empower-plus-guide/">EmPower+</a> first.</li>
      <li>Compare top-rated local installers, ranked by Google reviews &mdash; free for homeowners. Ask each one to show the rebate on the quote.</li>
    </ol>
  </div>
</section>

<section class="faq-section">
  <div class="wrap">
    <h2>Quick Questions</h2>
    {faq_html}
    <div class="faq-item"><div class="faq-q">Is my contractor&rsquo;s rebate quote a scam?</div><div class="faq-a">It can be, if the promised rebate is doing most of the work to make an inflated price look reasonable. <a href="/blog/is-my-contractors-rebate-quote-a-scam/">Check the real rebate cap before you sign &rarr;</a></div></div>
    <p style="font-size:14px; color:var(--ink-soft); margin-top:24px;">Sources, checked September 26, 2026: <a href="{MANUAL}" rel="noopener">NYS Clean Heat Program Manual v2</a>, <a href="https://www.coned.com/en/save-money/rebates-incentives-tax-credits/rebates-incentives-tax-credits-for-residential-customers/electric-heating-and-cooling-technology-for-renters-homeowners/save-on-a-central-air-source-heat-pump" rel="noopener">Con Edison</a>, <a href="https://www.psegliny.com/en/saveenergyandmoney/homeefficiency/HomeComfort/HeatPumps/Rebates" rel="noopener">PSEG Long Island</a>, <a href="https://www.nyserda.ny.gov/All-Programs/EmPower-New-York-Program" rel="noopener">NYSERDA EmPower+</a>, <a href="https://www.nyserda.ny.gov/All-Programs/Comfort-Home-Program" rel="noopener">NYSERDA Comfort Home</a>, <a href="https://www.nyserda.ny.gov/All-Programs/NY-Sun/Contractors/Dashboards-and-incentives" rel="noopener">NY-Sun</a>, <a href="https://www.irs.gov/credits-deductions/energy-efficient-home-improvement-credit" rel="noopener">IRS 25C</a>.</p>
  </div>
</section>

'''
    t = t[:a] + NEW + t[b:]

sub('<p>New York comparison: Heat pump 4–6 year payback vs. solar 12–18 years.</p>', '<p>Which upgrade to do first in New York, and why it depends on your utility.</p>')
sub('<p>NYC & Westchester: Complete rebate stacking breakdown.</p>', '<p>NYC &amp; Westchester: verified Con Edison heat pump amounts.</p>')
P.write_text(t, encoding='utf-8')
print('ok')
