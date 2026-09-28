#!/usr/bin/env python3
"""NY-only: rewrite the rebate body of New York city + utility hubs with verified facts.

Source of truth: data/verified-facts/ny.json (checked 2026-09-26).
Replaces ONLY: <title>, meta description, og:title/og:description, FAQPage + Article
JSON-LD, the old inline breadcrumb row, and the main rebate body (hero .. end of
<article class="article"> on city hubs; hero .. newsletter on utility hubs).
Everything else on the page (nav, rebate finder, category links, footer) is kept.
Idempotent: the body is wrapped in <!-- ny-verified:start/end --> markers.

Usage: python3 scripts/ny_verified_hubs.py
"""
import json, re, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = '2026-09-26'
CHECKED = 'September 26, 2026'
MANUAL = 'https://cleanheat.ny.gov/assets/pdf/NYS%20Clean%20Heat%20Program%20Manual%202025_v2.pdf'
EMPOWER = 'https://www.nyserda.ny.gov/All-Programs/EmPower-New-York-Program'
COMFORT = 'https://www.nyserda.ny.gov/All-Programs/Comfort-Home-Program'
DACMAP = 'https://www.nyserda.ny.gov/ny/Disadvantaged-Communities'
IRS25C = 'https://www.irs.gov/credits-deductions/energy-efficient-home-improvement-credit'

# ---- utility programs (all numbers from data/verified-facts/ny.json) ----
U = {
 'con-edison': dict(
   name='Con Edison', short='Con Edison', program='NYS Clean Heat (run by Con Edison)',
   src=('Con Edison air-source heat pump incentives', 'https://www.coned.com/en/save-money/rebates-incentives-tax-credits/rebates-incentives-tax-credits-for-residential-customers/electric-heating-and-cooling-technology-for-renters-homeowners/save-on-a-central-air-source-heat-pump'),
   headline='up to $10,000 ($11,000 in a Disadvantaged Community)',
   rows=[('Whole-home air-source heat pump, standard tier', '$7,000', '$8,000'),
         ('Whole-home air-source heat pump, weatherized tier', '$10,000', '$11,000'),
         ('Partial system (heat pump covers part of the home)', '$2,500', '$4,500'),
         ('Apartment, whole-home', '$3,500&ndash;$5,000', '$4,000&ndash;$5,500'),
         ('Ground-source (geothermal), whole 1&ndash;4 unit building', '$30,000', '$40,000'),
         ('Heat pump water heater', '$1,000', '$1,000')],
   note='Con Edison takes the incentive off your contractor&rsquo;s invoice, so you never wait for a cheque. Your home must pass a &ldquo;service adequate&rdquo; check first.',
   ev=('Con Edison has no rebate for buying a home charger. Its <a href="/us/ny/con-edison/new-york-city/ev-charger/">SmartCharge New York</a> program pays about $400 a year on average for charging off-peak. PowerReady stopped taking new Level 2 applications on April 22, 2026.'),
   clean_heat=True),
 'national-grid': dict(
   name='National Grid', short='National Grid', program='NYS Clean Heat (run by National Grid)',
   src=('NYS Clean Heat Program Manual v2 (Mar 5, 2026), Table 8', MANUAL),
   headline='up to $10,000 ($12,000 in a Disadvantaged Community)',
   rows=[('Whole-home cold-climate air-source heat pump', '$6,000', '$8,000'),
         ('Whole-home air-source + removing the old system', '$10,000', '$12,000'),
         ('Partial load (heat pump covers part of the home)', '$4,000', '$4,000'),
         ('Ground-source (geothermal) retrofit', '$20,000', '$25,000'),
         ('Heat pump water heater', '$1,250', '$1,250')],
   note='Apartments and homes under 1,000 sq ft get about half these amounts. Your participating contractor applies for you.',
   ev='', clean_heat=True),
 'rge': dict(
   name='RG&amp;E', short='RG&amp;E', program='NYS Clean Heat (run by RG&amp;E)',
   src=('NYS Clean Heat Program Manual v2 (Mar 5, 2026), Table 12', MANUAL),
   headline='up to $10,000',
   rows=[('Whole-home cold-climate air-source heat pump', '$6,000', '$6,000'),
         ('Whole-home air-source + removing the old system', '$10,000', '$10,000'),
         ('Partial load (heat pump covers part of the home)', '$3,000', '$3,000'),
         ('Ground-source (geothermal) retrofit', '$17,000', '$18,000'),
         ('Heat pump water heater', '$1,250', '$1,250')],
   note='Apartments and homes under 1,000 sq ft get less. Your participating contractor applies for you.',
   ev='', clean_heat=True),
 'central-hudson': dict(
   name='Central Hudson', short='Central Hudson', program='NYS Clean Heat (run by Central Hudson)',
   src=('NYS Clean Heat Program Manual v2 (Mar 5, 2026), Table 3', MANUAL),
   headline='up to $8,000',
   rows=[('Whole-home cold-climate air-source heat pump', '$5,000', '&mdash;'),
         ('Whole-home air-source + removing the old system', '$8,000', '&mdash;'),
         ('Partial load (heat pump covers part of the home)', '$3,000', '&mdash;'),
         ('Ground-source (geothermal) retrofit', '$18,000', '&mdash;'),
         ('Heat pump water heater', '$1,250', '&mdash;')],
   note='These are single-family amounts. Apartments and homes under 1,000 sq ft get less ($3,000 / $5,000 / $1,000). Central Hudson&rsquo;s table does not list a separate DAC column.',
   ev='', clean_heat=True),
 'pseg': dict(
   name='PSEG Long Island', short='PSEG Long Island', program='PSEG Long Island heat pump rebates',
   src=('PSEG Long Island heat pump rebates', 'https://www.psegliny.com/en/saveenergyandmoney/homeefficiency/HomeComfort/HeatPumps/Rebates'),
   headline='$4,000 (or $5,000&ndash;$7,500 if you qualify on income or live in a DAC)',
   rows=[('Whole-home heat pump, market rate', '$4,000', '$5,000'),
         ('Whole-home heat pump, moderate income (under 80% AMI)', '$5,000', '$5,000'),
         ('Whole-home heat pump, low income (under 60% AMI)', '$7,500', '$7,500')],
   note='PSEG Long Island is not part of NYS Clean Heat. The heat pump must be on the NEEP cold-climate list, sized for the whole home, installed by a participating contractor, and pre-approved before work starts.',
   ev='', clean_heat=False),
}

# ---- cities: utility key, url, plain local facts (kept conservative and true) ----
C = {
 'con-edison/new-york-city': dict(u='con-edison', city='New York City', short='NYC', slug='new-york-city',
   local='Con Edison supplies electricity across all five boroughs. For gas, Con Edison serves Manhattan, the Bronx and parts of Queens, while National Grid serves Brooklyn, Staten Island and the rest of Queens. That matters because the biggest Clean Heat amounts go to homes that fully replace oil, gas or electric-resistance heat. Many row houses and small multifamily buildings here have old steam or oil systems, which is exactly where a whole-home heat pump pays off most.',
   q='Con Edison heat pump rebate in NYC'),
 'con-edison/yonkers': dict(u='con-edison', city='Yonkers', short='Yonkers', slug='yonkers',
   local='Yonkers is in Westchester County, where Con Edison supplies both electricity and gas. Much of the housing is older two- and three-family homes, and Con Edison&rsquo;s program covers 1&ndash;4 family buildings, so an owner-occupied two-family can qualify.',
   q='Con Edison heat pump rebate in Yonkers'),
 'con-edison/new-rochelle': dict(u='con-edison', city='New Rochelle', short='New Rochelle', slug='new-rochelle',
   local='New Rochelle is a Westchester County city on Long Island Sound, served by Con Edison for electricity and gas. Plenty of homes here still burn heating oil, and oil-to-heat-pump switches are where the whole-home tier makes the most sense.',
   q='Con Edison heat pump rebate in New Rochelle'),
 'con-edison/mount-vernon': dict(u='con-edison', city='Mount Vernon', short='Mount Vernon', slug='mount-vernon',
   local='Mount Vernon borders the Bronx in southern Westchester and is served by Con Edison. Parts of the city are mapped as Disadvantaged Communities, so check your address &mdash; DAC status raises the Con Edison amount and the cost cap (85% instead of 70%).',
   q='Con Edison heat pump rebate in Mount Vernon'),
 'con-edison/white-plains': dict(u='con-edison', city='White Plains', short='White Plains', slug='white-plains',
   local='White Plains is the Westchester County seat and is served by Con Edison. Its mix of single-family homes and condos means both the single-family and apartment amounts below can apply, depending on your building.',
   q='Con Edison heat pump rebate in White Plains'),
 'national-grid/buffalo': dict(u='national-grid', city='Buffalo', short='Buffalo', slug='buffalo',
   local='National Grid supplies electricity in Buffalo, while most homes get gas from National Fuel Gas. Lake-effect winters are long and cold, so pick a heat pump on the cold-climate list and get the attic insulated and air-sealed first &mdash; many of Buffalo&rsquo;s older wood-frame homes leak a lot of heat.',
   q='heat pump rebate in Buffalo', title='Buffalo Heat Pump &amp; Insulation Rebates 2026',
   extra='<h2>Insulation rebates in Buffalo</h2><p>For insulation and air sealing, Buffalo homeowners have three real options: NYSERDA <strong>Comfort Home</strong> ($2,500 or $3,000 per package, +$2,000 for windows), <strong>EmPower+</strong> if your income qualifies (free or 50% covered), and National Grid&rsquo;s own efficiency offers &mdash; see our <a href="/us/ny/national-grid/buffalo/insulation/">Buffalo insulation page</a>. The federal 25C insulation tax credit ended December 31, 2025, so it no longer applies.</p>'),
 'national-grid/syracuse': dict(u='national-grid', city='Syracuse', short='Syracuse', slug='syracuse',
   local='National Grid supplies both electricity and gas in Syracuse. It is one of the snowiest cities in the US, so a cold-climate heat pump with a backup plan for the coldest nights is the usual design.',
   q='heat pump rebates in Syracuse'),
 'national-grid/albany': dict(u='national-grid', city='Albany', short='Albany', slug='albany',
   local='National Grid supplies electricity and gas in Albany. Many homes are older row houses and two-family homes, so the apartment amounts can apply to each unit of a two-family building.',
   q='heat pump rebates in Albany'),
 'national-grid/rochester': dict(u='rge', city='Rochester', short='Rochester', slug='rochester',
   local='Important: the City of Rochester is served by <strong>RG&amp;E (Rochester Gas and Electric)</strong>, not National Grid. RG&amp;E runs NYS Clean Heat here, so the amounts in the table are RG&amp;E&rsquo;s. (This page sits in our National Grid section only for historical reasons.) A few outlying towns in Monroe County are on National Grid, so check the name on your electric bill.',
   q='heat pump rebate in Rochester'),
 'central-hudson/poughkeepsie': dict(u='central-hudson', city='Poughkeepsie', short='Poughkeepsie', slug='poughkeepsie',
   local='Central Hudson supplies electricity and gas in Poughkeepsie and across the mid-Hudson Valley. Many homes here heat with oil or propane, and replacing those with a whole-home heat pump is what unlocks Central Hudson&rsquo;s larger $8,000 tier.',
   q='Central Hudson heat pump rebate in Poughkeepsie'),
 'pseg/brookhaven': dict(u='pseg', city='Brookhaven', short='Brookhaven', slug='brookhaven',
   local='Brookhaven is Long Island&rsquo;s largest town, in Suffolk County. PSEG Long Island supplies electricity (for LIPA) and National Grid supplies gas where there are gas lines &mdash; but many homes in eastern Brookhaven heat with oil, which is where a heat pump saves the most.',
   q='PSEG Long Island heat pump rebate in Brookhaven'),
 'pseg/islip': dict(u='pseg', city='Islip', short='Islip', slug='islip',
   local='Islip is a Suffolk County town served by PSEG Long Island for electricity and National Grid for gas. Its many 1950s&ndash;70s ranch and Cape homes are a good fit for ducted or ductless whole-home heat pumps.',
   q='PSEG Long Island heat pump rebate in Islip'),
}

UTILITY_HUBS = {
 'con-edison': dict(u='con-edison', title='Con Edison Heat Pump Rebates 2026: NYC &amp; Westchester',
   cities=['new-york-city', 'yonkers', 'mount-vernon', 'new-rochelle', 'white-plains'], area='New York City and Westchester County'),
 'national-grid': dict(u='national-grid', title='National Grid NY Heat Pump Rebates 2026 (Upstate)',
   cities=['buffalo', 'syracuse', 'albany', 'rochester'], area='upstate New York (Buffalo, Syracuse, Albany)'),
 'central-hudson': dict(u='central-hudson', title='Central Hudson Heat Pump Rebates 2026',
   cities=['poughkeepsie', 'kingston', 'newburgh', 'beacon', 'saugerties'], area='the mid-Hudson Valley'),
 'pseg': dict(u='pseg', title='PSEG Long Island Heat Pump Rebates 2026',
   cities=['brookhaven', 'islip', 'babylon', 'huntington', 'smithtown', 'oyster-bay', 'southampton'], area='Long Island (Nassau and Suffolk) and the Rockaways'),
}
CITY_NAMES = {'new-york-city': 'New York City', 'yonkers': 'Yonkers', 'mount-vernon': 'Mount Vernon', 'new-rochelle': 'New Rochelle',
  'white-plains': 'White Plains', 'buffalo': 'Buffalo', 'syracuse': 'Syracuse', 'albany': 'Albany', 'rochester': 'Rochester (RG&amp;E)',
  'poughkeepsie': 'Poughkeepsie', 'kingston': 'Kingston', 'newburgh': 'Newburgh', 'beacon': 'Beacon', 'saugerties': 'Saugerties',
  'brookhaven': 'Brookhaven', 'islip': 'Islip', 'babylon': 'Babylon', 'huntington': 'Huntington', 'smithtown': 'Smithtown',
  'oyster-bay': 'Oyster Bay', 'southampton': 'Southampton'}

STYLE = '''<style>
.nyv{max-width:860px;margin:0 auto;padding:8px 20px 32px;color:var(--ink);font-size:17px;line-height:1.65}
.nyv h2{font-family:'Fraunces',Georgia,serif;font-size:26px;line-height:1.25;margin:36px 0 12px;color:var(--ink)}
.nyv .short{background:#fff;border-left:4px solid var(--amber);border-radius:10px;padding:16px 18px;margin:18px 0}
.nyv table{width:100%;border-collapse:collapse;font-size:15px;margin:12px 0;background:#fff}
.nyv th,.nyv td{border:1px solid var(--rule,#d9d0c1);padding:9px 10px;text-align:left;vertical-align:top}
.nyv th{background:var(--paper-warm)}
.nyv .tbl{overflow-x:auto}
.nyv .src{font-size:14px;color:var(--ink-soft);margin-top:28px}
.nyv .cta-box{background:var(--teal-deep);color:#fff;border-radius:12px;padding:20px;margin:28px 0}
.nyv .cta-box a{color:#fff;font-weight:700}
.nyv details{background:#fff;border:1px solid var(--rule,#d9d0c1);border-radius:10px;padding:12px 14px;margin:8px 0}
.nyv summary{font-weight:600;cursor:pointer}
</style>'''


def exists(url):
    return (ROOT / url.strip('/') / 'index.html').exists()


def rate_table(u):
    d = U[u]
    rows = ''.join(f'<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>' for a, b, c in d['rows'])
    return (f'<div class="tbl"><table><thead><tr><th>What you install</th><th>Standard</th><th>In a Disadvantaged Community</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div><p style="font-size:15px">{d["note"]}</p>')


def not_stack(u):
    d = U[u]
    first = ('<li><strong>&ldquo;Utility rebate + NYS Clean Heat&rdquo; is one rebate, not two.</strong> '
             f'NYS Clean Heat is the program {d["short"]} runs. Don&rsquo;t believe any quote that adds them together.</li>'
             if d['clean_heat'] else
             '<li><strong>NYS Clean Heat does not apply on Long Island.</strong> PSEG Long Island runs its own heat pump rebates for LIPA instead.</li>')
    return ('<ul>' + first +
            '<li><strong>There is no separate &ldquo;federal HEAR&rdquo; cheque you apply for.</strong> New York delivers the federal Home Energy Rebates '
            '(HEAR and HOMES) to income-eligible households through <a href="/blog/new-york-empower-plus-guide/">EmPower+</a> and NYSERDA&rsquo;s Appliance Upgrade Program.</li>'
            f'<li><strong>The federal 25C and 25D tax credits are gone.</strong> They ended for anything installed after December 31, 2025.</li>'
            '<li><strong>Rebates are capped.</strong> ' + ('NYS Clean Heat pays at most 70% of the project cost (85% in a DAC), so a rebate can never be bigger than your bill.' if d['clean_heat'] else 'Rebates only cover part of the cost &mdash; nobody gets paid to install a heat pump.') + '</li></ul>')


def empower_block():
    return ('<p><strong>EmPower+</strong> (NYSERDA) is for lower-income owners <em>and renters</em> of 1&ndash;4 family homes. '
            'Low-income households can get upgrades at no cost, up to $12,000 upstate or $14,000 downstate. Moderate-income households get 50% of the cost covered, '
            'up to $6,000 upstate or $7,000 downstate. Heat pumps can add more on top. Income limits depend on your county and household size.</p>'
            '<p><strong>Comfort Home</strong> (NYSERDA) pays $2,500 or $3,000 toward an air-sealing and insulation package, plus $2,000 more if you add windows. '
            'It works through Comfort Home contractors in participating counties, so check that yours is covered.</p>')


def installer_links(slug):
    out = []
    for svc, label in (('heat-pump', 'heat pump'), ('solar', 'solar')):
        url = f'/installers/ny/{slug}/{svc}/'
        if exists(url):
            out.append(f'<a href="{url}">top-rated {label} installers in {CITY_NAMES.get(slug, slug).replace(" (RG&amp;E)", "")}</a>')
    return out


def cta(slug=None):
    links = installer_links(slug) if slug else []
    extra = (' See the ' + ' and '.join(links) + ', ranked by Google reviews.') if links else ''
    return ('<div class="cta-box"><strong>Next step:</strong> compare top-rated local installers, ranked by Google reviews &mdash; free for homeowners.'
            f'{extra} <a href="/us/ny/">See your city&rsquo;s rebates &rarr;</a></div>')


def sources(u):
    d = U[u]
    s = [d['src'], ('NYSERDA EmPower+', EMPOWER), ('NYSERDA Comfort Home', COMFORT), ('NYS Disadvantaged Communities map', DACMAP), ('IRS: 25C credit', IRS25C)]
    if u != 'pseg' and d['src'][1] != MANUAL:
        s.insert(1, ('NYS Clean Heat Program Manual v2', MANUAL))
    return '<p class="src">Sources, checked ' + CHECKED + ': ' + ', '.join(f'<a href="{b}" rel="noopener">{a}</a>' for a, b in s) + '.</p>'


def faqs_city(c):
    d = U[c['u']]; city = c['city']
    return [
      (f'How much is the heat pump rebate in {city}?',
       f'{html.unescape(d["program"])} pays {html.unescape(re.sub("<[^>]+>", "", d["headline"]))} for a whole-home heat pump in {city}. The exact amount depends on your home size, whether you remove your old heating system, and whether you live in a Disadvantaged Community. Your contractor applies for you.'),
      ('Can I add NYS Clean Heat on top of my utility rebate?' if d['clean_heat'] else 'Can Long Island homes get NYS Clean Heat?',
       (f'No. NYS Clean Heat is the rebate {html.unescape(d["short"])} pays, so there is only one heat pump rebate from your utility. Income-eligible households may get more through EmPower+.' if d['clean_heat'] else
        'No. PSEG Long Island is not part of NYS Clean Heat. It runs its own heat pump rebates: $4,000 at market rate, $5,000 for moderate income or DAC homes, and $7,500 for low income.')),
      ('Is the federal tax credit still available for heat pumps?',
       'No. The federal 25C home-improvement credit and 25D clean-energy credit ended for anything installed after December 31, 2025.'),
      ('Who qualifies for EmPower+?',
       'Lower-income owners and renters of 1-4 family homes. Low-income households can get free upgrades up to $12,000 upstate or $14,000 downstate; moderate-income households get 50% covered up to $6,000 upstate or $7,000 downstate.'),
    ]


def faq_html(faqs):
    return '<h2>Common questions</h2>' + ''.join(f'<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>' for q, a in faqs)


def faq_ld(faqs):
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]}


def article_ld(headline, desc, url):
    return {'@context': 'https://schema.org', '@type': 'Article', 'headline': headline, 'description': desc,
            'datePublished': '2026-08-17', 'dateModified': TODAY,
            'author': {'@type': 'Person', 'name': 'Sam Menard', 'url': 'https://homepowerrebate.com/about'},
            'publisher': {'@type': 'Organization', 'name': 'HomePowerRebate'}, 'mainEntityOfPage': url}


def city_body(key, c, header=False):
    u = c['u']; d = U[u]; city = c['city']
    cat = f'/us/ny/{key}/'
    cats = [(f'{cat}heat-pump/', 'Heat pumps'), (f'{cat}insulation/', 'Insulation'), (f'{cat}water-heater/', 'Water heaters'),
            (f'{cat}solar/', 'Solar'), (f'{cat}battery/', 'Batteries'), (f'{cat}ev-charger/', 'EV chargers'), (f'{cat}smart-thermostats/', 'Smart thermostats')]
    catlinks = ' &middot; '.join(f'<a href="{a}">{b}</a>' for a, b in cats if exists(a))
    ev = f'<h2>EV chargers in {city}</h2><p>{d["ev"]}</p>' if d['ev'] else ''
    short = (f'<div class="short"><strong>Short answer:</strong> In {city}, the main heat pump rebate is {d["program"]}: '
             f'{d["headline"]} for a whole-home system, taken off your contractor&rsquo;s bill. It is one rebate &mdash; not several that add up. '
             'Lower-income households can get much more through EmPower+, and the federal tax credits ended on December 31, 2025.</div>')
    intro = f'What {city} homeowners can really get in 2026, checked against {d["short"]} and NYSERDA on {CHECKED}.'
    h1 = f'{city} Heat Pump Rebates 2026: {d["short"]}'
    hero = (f'<header>\n  <h1>{h1}</h1>\n  <p class="subheading">{intro}</p>\n</header>' if header else
            f'<section class="hero">\n  <div class="wrap">\n    <h1>{h1}</h1>\n    <p>{intro}</p>\n  </div>\n</section>')
    tail = '\n<div class="container">' if header else ''
    return hero + f'''
{STYLE}
<article class="nyv">
{short}
<h2>How much is the {c["q"]}?</h2>
<p>Amounts for a single-family home. You get one line from this table, not several.</p>
{rate_table(u)}
<h2>What makes {city} different</h2>
<p>{c["local"]}</p>
{c.get("extra", "")}
<h2>What does <em>not</em> stack</h2>
{not_stack(u)}
<h2>Income-qualified help: EmPower+ and Comfort Home</h2>
{empower_block()}
<h2>Are you in a Disadvantaged Community?</h2>
<p>If your home is in a NYS Disadvantaged Community, some amounts go up and the Clean Heat cap rises from 70% to 85% of cost. Enter your address on the <a href="{DACMAP}" rel="noopener">state DAC map</a>, or read our <a href="/blog/new-york-dac-mapping-eligibility-guide/">DAC guide</a>.</p>
{ev}
<h2>What to do next</h2>
<ol>
<li>Check the name on your electric bill &mdash; it decides which rebate you get.</li>
<li>If your income may qualify, apply to <a href="/blog/new-york-empower-plus-guide/">EmPower+</a> before you sign anything.</li>
<li>Get 2&ndash;3 quotes from participating contractors. Ask each one which rebate tier your home fits and to show it on the quote.</li>
<li>Insulate and air-seal first if your home is drafty &mdash; it lets you buy a smaller heat pump.</li>
</ol>
<p>More for {city}: {catlinks}</p>
{cta(c["slug"])}
{faq_html(faqs_city(c))}
{sources(u)}
</article>''' + tail


def hub_body(slug, h):
    u = h['u']; d = U[u]
    cities = ' &middot; '.join(f'<a href="/us/ny/{slug}/{c}/">{CITY_NAMES[c]}</a>' for c in h['cities'] if exists(f'/us/ny/{slug}/{c}/'))
    extra = ''
    if slug == 'national-grid':
        extra = ('<p><strong>Rochester note:</strong> the City of Rochester is served by RG&amp;E, not National Grid. RG&amp;E&rsquo;s Clean Heat amounts are a little different '
                 '(up to $10,000 for a whole-home switch). See our <a href="/us/ny/national-grid/rochester/">Rochester page</a>.</p>')
    ev = f'<h2>EV chargers</h2><p>{d["ev"]}</p>' if d['ev'] else ''
    faqs = [
      (f'How much is the {html.unescape(d["short"])} heat pump rebate?',
       f'{html.unescape(d["program"])} pays {html.unescape(re.sub("<[^>]+>", "", d["headline"]))} for a whole-home heat pump. Partial systems and apartments get less.'),
      faqs_city({'u': u, 'city': h['area']})[1],
      faqs_city({'u': u, 'city': ''})[2],
      faqs_city({'u': u, 'city': ''})[3],
    ]
    body = f'''<section class="hero">
  <div class="wrap">
    <h1>{h["title"]}</h1>
    <p>Heat pump rebates for homeowners in {h["area"]}, checked against {d["short"]} and NYSERDA on {CHECKED}.</p>
  </div>
</section>
{STYLE}
<article class="nyv">
<div class="short"><strong>Short answer:</strong> {d["program"]} pays {d["headline"]} for a whole-home heat pump. It is one rebate, taken off your contractor&rsquo;s bill. Lower-income households can get more through EmPower+. The federal 25C/25D tax credits ended December 31, 2025.</div>
<h2>Pick your city</h2>
<p>{cities}</p>
{extra}
<h2>{d["short"]} heat pump rebate amounts (2026)</h2>
{rate_table(u)}
<h2>What does <em>not</em> stack</h2>
{not_stack(u)}
<h2>Income-qualified help</h2>
{empower_block()}
{ev}
{cta()}
{faq_html(faqs)}
{sources(u)}
</article>'''
    return body, faqs


def set_head(t, title, desc, faqs, art):
    t = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', t, 1, re.S)
    t = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{desc}">', t, 1)
    t = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{title}">', t, 1)
    t = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{desc}">', t, 1)
    # drop old FAQPage / Article blocks, add fresh ones
    def keep(m):
        s = m.group(0)
        return '' if re.search(r'"@type"\s*:\s*"(FAQPage|Article)"', s) else s
    t = re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>\s*', keep, t)
    ld = ('<script type="application/ld+json">\n' + json.dumps(faqs, ensure_ascii=False, indent=1) + '\n</script>\n'
          '<script type="application/ld+json">\n' + json.dumps(art, ensure_ascii=False, indent=1) + '\n</script>\n')
    return t.replace('</head>', ld + '</head>', 1)


def put_body(t, body, end_pat):
    body = '<!-- ny-verified:start -->\n' + body + '\n<!-- ny-verified:end -->'
    if '<!-- ny-verified:start -->' in t:
        a = t.index('<!-- ny-verified:start -->'); b = t.index('<!-- ny-verified:end -->') + len('<!-- ny-verified:end -->')
        return t[:a] + body + t[b:]
    a = t.index('<section class="hero">')
    m = re.compile(end_pat).search(t, a)
    return t[:a] + body + t[m.start():]


def drop_old_crumb(t):
    return re.sub(r'<section class="wrap" style="padding:24px 28px 0;">\s*<div style="font-size:14px; line-height:2.2;">[\s\S]*?</section>\s*', '', t, 1)


def main():
    changed = 0
    for key, c in C.items():
        p = ROOT / 'us/ny' / key / 'index.html'
        t = p.read_text(encoding='utf-8')
        d = U[c['u']]
        title = c.get('title') or f'{c["short"]} Heat Pump Rebates 2026: {d["short"]} Amounts'
        if len(html.unescape(title)) > 60:
            title = f'{c["short"]} Heat Pump Rebates 2026'
        desc = html.unescape(f'{c["city"]} heat pump rebates in 2026: {d["program"]} pays {re.sub("<[^>]+>", "", d["headline"])}. What stacks, what ended, and EmPower+.')
        if len(desc) > 160:
            desc = html.unescape(f'{c["city"]} heat pump rebates 2026: {d["short"]} pays {re.sub("<[^>]+>", "", d["headline"])}. What stacks and what ended.')
        desc = html.escape(desc[:160], quote=True)
        url = f'https://homepowerrebate.com/us/ny/{key}/'
        if '<!-- ny-verified:start -->' in t:
            header = '<!-- ny-verified:start -->\n<header>' in t
        else:
            header = '<article class="article">' not in t
        body = city_body(key, c, header)
        faqs = faq_ld(faqs_city(c))
        if '<!-- ny-verified:start -->' not in t:
            t = drop_old_crumb(t)
            if not header:
                a = t.index('<section class="hero">'); b = t.index('</article>', a) + len('</article>')
            else:
                a = t.index('<header>'); b = t.index('<section>\n<h2>Category Deep Dives</h2>', a)
            t = t[:a] + '<!-- ny-verified:start -->\n<!-- ny-verified:end -->\n' + t[b:]
        t = put_body(t, body, None)
        t = set_head(t, title, desc, faqs, article_ld(html.unescape(title), html.unescape(desc), url))
        p.write_text(t, encoding='utf-8'); changed += 1
    for slug, h in UTILITY_HUBS.items():
        p = ROOT / 'us/ny' / slug / 'index.html'
        t = p.read_text(encoding='utf-8')
        body, faqs = hub_body(slug, h)
        if '<!-- ny-verified:start -->' not in t:
            a = t.index('<section class="hero">')
            b = t.index('<section style="background: linear-gradient(135deg, rgba(13, 79, 92, 0.95)', a)
            t = t[:a] + '<!-- ny-verified:start -->\n<!-- ny-verified:end -->\n\n' + t[b:]
        t = put_body(t, body, None)
        title = h['title']
        d = U[h['u']]
        desc = html.escape(html.unescape(f'{d["program"]} pays {re.sub("<[^>]+>", "", d["headline"])} for a whole-home heat pump. What stacks, what ended, and EmPower+ help.')[:160], quote=True)
        t = set_head(t, title, desc, faq_ld(faqs), article_ld(html.unescape(title), html.unescape(desc), f'https://homepowerrebate.com/us/ny/{slug}/'))
        p.write_text(t, encoding='utf-8'); changed += 1
    print('pages written:', changed)


if __name__ == '__main__':
    main()
