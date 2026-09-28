#!/usr/bin/env python3
"""NY-only, idempotent upgrade of top-traffic NYC leaf pages (GSC top pages, Sep 2026).
Facts: data/verified-facts/ny.json (checked 2026-09-26)."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SMART = 'https://www.coned.com/en/save-money/rebates-incentives-tax-credits/rebates-incentives-tax-credits-for-residential-customers/electric-vehicle-rewards'
POWERREADY = 'https://www.coned.com/en/our-energy-future/electric-vehicles/power-ready-program'
IRS30C = 'https://www.irs.gov/credits-deductions/alternative-fuel-vehicle-refueling-property-credit'
AUTHOR = {'@type': 'Person', 'name': 'Sam Menard', 'url': 'https://homepowerrebate.com/about'}


def set_meta(t, title, desc):
    t = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', t, count=1, flags=re.S)
    for pat, val in ((r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{desc}">'),
                     (r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{title}">'),
                     (r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{desc}">')):
        t = re.sub(pat, val, t, count=1)
    return t


def replace_ld(t, typ, obj):
    blocks = re.findall(r'<script type="application/ld\+json">[\s\S]*?</script>', t)
    new = '<script type="application/ld+json">\n' + json.dumps(obj, ensure_ascii=False, indent=1) + '\n</script>'
    for b in blocks:
        if re.search(r'"@type"\s*:\s*"' + typ + '"', b):
            return t.replace(b, new, 1)
    return t.replace('</head>', new + '\n</head>', 1)


def drop_old_crumb(t):
    return re.sub(r'<section class="wrap" style="padding:24px 28px 0;">\s*<div style="font-size:14px; line-height:2.2;">[\s\S]*?</section>\s*', '', t, count=1)


def faq_block(faqs):
    return ''.join(f'    <div class="faq-item">\n      <h3>{q}</h3>\n      <p>{a}</p>\n    </div>\n' for q, a in faqs)


def strip_tags(s):
    import html as h
    return h.unescape(re.sub(r'<[^>]+>', '', s))


# ---------------- EV charger (NYC) ----------------
def ev():
    p = ROOT / 'us/ny/con-edison/new-york-city/ev-charger/index.html'
    t = p.read_text(encoding='utf-8')
    title = 'Con Edison EV Charger Rebate 2026: What NYC Gets'
    desc = 'Con Edison has no rebate on the charger itself. SmartCharge New York pays about $400/yr for off-peak charging. PowerReady L2 closed April 22, 2026.'
    t = set_meta(t, title, desc)
    t = drop_old_crumb(t)
    t = t.replace('<h1>EV Charger Rebates in New York City</h1>', '<h1>Con Edison EV Charger Rebates in NYC (2026)</h1>')
    t = t.replace("<p>Here's exactly how the ev charger rebate works in New York City (Con Edison territory), plus local installers to call.</p>",
                  '<p>What Con Edison actually pays New York City EV drivers in 2026, checked September 26, 2026.</p>')
    faqs = [
     ('Does Con Edison give a rebate for a home EV charger?',
      'No. Con Edison does not pay money toward buying a home Level 2 charger. Its <a href="' + SMART + '" rel="noopener">SmartCharge New York</a> program pays you for charging at off-peak times instead &mdash; about $400 a year on average.'),
     ('How much does SmartCharge New York pay?',
      '10 cents per kWh for charging off-peak (midnight to 8 a.m.), a $25 bonus after your first 3 months, and summer bonuses for not charging on weekdays from 2 to 6 p.m. between June 1 and September 30. Con Edison says participants earn about $400 a year on average.'),
     ('Who can join SmartCharge New York?',
      'Anyone who charges a compatible EV or charger in New York City or Westchester County. You do not have to be a Con Edison customer, but drivers on a residential or small-business time-of-use rate (SC1 or SC2) cannot earn the incentives.'),
     ('Is PowerReady still open for home chargers?',
      'No. Con Edison stopped taking new Level 2 applications for PowerReady on April 22, 2026, and it was built for site make-ready work, not single-family garages.'),
     ('Can I still get the federal EV charger tax credit?',
      'Only for a charger placed in service by June 30, 2026. The federal 30C credit (30% up to $1,000) ended after that date.'),
    ]
    ev_body = '''    <div class="callout" style="border-left:4px solid var(--amber);"><strong>Short answer:</strong> Con Edison has <strong>no rebate on the charger itself</strong>. What it pays is <strong>SmartCharge New York</strong>: 10&cent;/kWh for off-peak charging plus bonuses, about <strong>$400 a year</strong> on average. PowerReady closed to new Level 2 applications on April 22, 2026, and the federal 30C charger credit ended June 30, 2026.</div>

    <h2>Does Con Edison have an EV charger rebate?</h2>
    <p>Not for buying the charger. Con Edison rewards <em>how</em> you charge, not what you buy. That still adds up: a driver who plugs in overnight can earn back the cost of a basic Level 2 charger in a year or two.</p>
    <div style="overflow-x:auto;"><table style="width:100%; border-collapse:collapse; font-size:15px; background:#fff; margin:12px 0;">
      <thead><tr style="background:var(--paper-warm);"><th style="text-align:left; padding:8px; border:1px solid var(--rule);">Program</th><th style="text-align:left; padding:8px; border:1px solid var(--rule);">What it pays</th><th style="text-align:left; padding:8px; border:1px solid var(--rule);">Status (Sept 2026)</th></tr></thead>
      <tbody>
        <tr><td style="padding:8px; border:1px solid var(--rule);">SmartCharge New York</td><td style="padding:8px; border:1px solid var(--rule);">10&cent;/kWh off-peak (midnight&ndash;8 a.m.), $25 after 3 months, summer bonuses for avoiding weekday 2&ndash;6 p.m. charging; ~$400/yr average</td><td style="padding:8px; border:1px solid var(--rule);">Open</td></tr>
        <tr><td style="padding:8px; border:1px solid var(--rule);">Con Edison PowerReady (Level 2)</td><td style="padding:8px; border:1px solid var(--rule);">Make-ready wiring costs at charging sites</td><td style="padding:8px; border:1px solid var(--rule);">Closed to new L2 applications April 22, 2026</td></tr>
        <tr><td style="padding:8px; border:1px solid var(--rule);">Federal 30C tax credit</td><td style="padding:8px; border:1px solid var(--rule);">30% of a home charger, up to $1,000</td><td style="padding:8px; border:1px solid var(--rule);">Ended for chargers placed in service after June 30, 2026</td></tr>
      </tbody>
    </table></div>

    <h2>How to earn SmartCharge rewards</h2>
    <ol>
      <li>Check that your car or charger is on Con Edison&rsquo;s compatible list.</li>
      <li>Stay off the residential time-of-use rate (SC1/SC2 TOU) &mdash; those customers can&rsquo;t earn SmartCharge incentives. Compare both options before you switch rates.</li>
      <li>Sign up through Con Edison&rsquo;s SmartCharge portal and connect your EV or charger.</li>
      <li>Schedule charging for midnight to 8 a.m., and skip weekday 2&ndash;6 p.m. charging in summer.</li>
    </ol>
    <p class="source-note">Sources, checked September 26, 2026: <a href="''' + SMART + '''" target="_blank" rel="noopener">Con Edison SmartCharge New York</a>, <a href="''' + POWERREADY + '''" target="_blank" rel="noopener">Con Edison PowerReady</a>, <a href="''' + IRS30C + '''" target="_blank" rel="noopener">IRS 30C credit</a>.</p>
'''
    a = t.index('    <h2>How much you get</h2>') if '    <h2>How much you get</h2>' in t else None
    if a is not None:
        b = t.index('    <h2>Buying a home charger as an NYC homeowner</h2>', a)
        t = t[:a] + ev_body + '\n' + t[b:]
    # installers + CTA
    t = t.replace('''    <h2>EV Charger installers in New York City</h2>
    <p>We don't have verified local installer data for New York City in this category yet. <a href="/installers/">Browse the full installer directory &rarr;</a> for HVAC, solar, and electrical installers near New York City.</p>''',
      '''    <h2>Who installs EV chargers in New York City?</h2>
    <p>A licensed electrician does the work, and in NYC the job usually needs a Department of Buildings electrical permit. Compare top-rated local installers, ranked by Google reviews &mdash; free for homeowners. <a href="/installers/">Browse the installer directory &rarr;</a> or <a href="/us/ny/con-edison/new-york-city/">see all NYC rebates &rarr;</a></p>''')
    # FAQ visible
    a = t.index('    <h2>Common questions</h2>')
    b = t.index('    <h2>Other Con Edison Cities</h2>', a)
    t = t[:a] + '    <h2>Common questions</h2>\n' + faq_block(faqs) + '\n' + t[b:]
    t = t.replace("""    <p>Con Edison is the local electric utility for New York City. The EV charger rebate above is a state-wide program, so which utility bills you doesn't change what you qualify for, but Con Edison is who to ask about time-of-use or EV-specific electricity rates, since charging overnight on the right rate plan can meaningfully change your running cost. Some utilities also run their own home-charger incentive on top of the state one, worth a quick call to Con Edison to check.</p>""",
      """    <p>Con Edison supplies electricity across all five boroughs, so SmartCharge New York is the program that applies to NYC drivers. Your choice is between SmartCharge rewards and a time-of-use rate &mdash; you can&rsquo;t earn SmartCharge incentives on the residential TOU rate, so compare both with your real driving before switching. Thinking about a heat pump too? See <a href="/us/ny/con-edison/new-york-city/heat-pump/">NYC heat pump rebates</a> and the <a href="/us/ny/con-edison/">Con Edison hub</a>.</p>""")
    t = replace_ld(t, 'FAQPage', {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': strip_tags(a)}} for q, a in faqs]})
    t = replace_ld(t, 'Article', {'@context': 'https://schema.org', '@type': 'Article', 'headline': title, 'description': desc,
        'datePublished': '2026-08-22', 'dateModified': '2026-09-26', 'author': AUTHOR,
        'publisher': {'@type': 'Organization', 'name': 'HomePowerRebate'},
        'mainEntityOfPage': 'https://homepowerrebate.com/us/ny/con-edison/new-york-city/ev-charger/'})
    p.write_text(t, encoding='utf-8')


if __name__ == '__main__':
    ev()
    print('ok')
