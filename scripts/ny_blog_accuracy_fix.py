#!/usr/bin/env python3
"""NY-only, idempotent: correct the NY blog posts against data/verified-facts/ny.json (2026-09-26)."""
import json, re, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EMPOWER = 'https://www.nyserda.ny.gov/All-Programs/EmPower-New-York-Program'
MANUAL = 'https://cleanheat.ny.gov/assets/pdf/NYS%20Clean%20Heat%20Program%20Manual%202025_v2.pdf'
HERFAQ = 'https://www.nyserda.ny.gov/-/media/Project/Nyserda/Files/Programs/IRA/IRA-HER-HEAR-FAQ.pdf'
COMFORT = 'https://www.nyserda.ny.gov/All-Programs/Comfort-Home-Program'
IRS = 'https://www.irs.gov/credits-deductions/energy-efficient-home-improvement-credit'
AUTHOR = {'@type': 'Person', 'name': 'Sam Menard', 'url': 'https://homepowerrebate.com/about'}

STACK_BOX = ('<div class="callout" style="border-left:4px solid var(--amber); background:#fff; padding:16px 18px; border-radius:10px; margin:18px 0;">'
  '<strong>Updated September 26, 2026 &mdash; what really stacks in New York:</strong> NYS Clean Heat <em>is</em> the heat pump rebate your utility pays '
  '(Con Edison up to $10,000, National Grid up to $10,000&ndash;$12,000, NYSEG/RG&amp;E up to $10,000, Central Hudson up to $8,000), so it never adds on top of a separate &ldquo;utility rebate&rdquo;. '
  'PSEG Long Island runs its own ($4,000&ndash;$7,500). There is no separate federal HEAR cheque: New York delivers the federal Home Energy Rebates through '
  '<a href="/blog/new-york-empower-plus-guide/">EmPower+</a> for income-eligible households. The federal 25C/25D tax credits ended December 31, 2025. '
  f'Sources: <a href="{MANUAL}" rel="noopener">Clean Heat manual</a>, <a href="{EMPOWER}" rel="noopener">EmPower+</a>, <a href="{IRS}" rel="noopener">IRS</a>.</div>')


def set_meta(t, title, desc):
    t = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', t, count=1, flags=re.S)
    t = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{desc}">', t, count=1)
    t = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{title}">', t, count=1)
    t = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{desc}">', t, count=1)
    return t


def set_ld(t, objs):
    t = re.sub(r'<script type="application/ld\+json">\s*\{\s*"@context": "https://schema.org",\s*"@type": "(FAQPage|Article|BlogPosting)"[\s\S]*?</script>\s*', '', t)
    add = ''.join('<script type="application/ld+json">\n' + json.dumps(o, ensure_ascii=False, indent=1) + '\n</script>\n' for o in objs)
    return t.replace('</head>', add + '</head>', 1)


def drop_old_crumb(t):
    return re.sub(r'<section class="wrap" style="padding:24px 28px 0;">\s*<div style="font-size:14px; line-height:2.2;">[\s\S]*?</section>\s*', '', t, count=1)


def empower():
    p = ROOT / 'blog/new-york-empower-plus-guide/index.html'
    t = p.read_text(encoding='utf-8')
    title = 'EmPower+ NY 2026: Income Limits, Amounts, How to Apply'
    desc = 'EmPower+ gives lower-income New Yorkers free upgrades up to $12,000 upstate or $14,000 downstate, or 50% off up to $6,000/$7,000. Owners and renters, statewide.'
    t = set_meta(t, title, desc)
    t = drop_old_crumb(t)
    faqs = [
      ('Who qualifies for EmPower+?', 'Income-eligible owners and renters of 1-4 family homes anywhere in New York State. Income limits depend on your county and household size; NYSERDA publishes the current limits.'),
      ('How much does EmPower+ pay?', 'Low-income households get upgrades at no cost, up to $12,000 upstate or $14,000 downstate per project. Moderate-income households get 50% of the cost covered, up to $6,000 upstate or $7,000 downstate. Heat pumps can qualify for more through linked funding.'),
      ('Is EmPower+ only for Con Edison customers?', 'No. EmPower+ is run by NYSERDA and is open statewide, including National Grid, NYSEG, RG&E, Central Hudson, O&R and PSEG Long Island areas.'),
      ('Can I combine EmPower+ with the Con Edison or NYS Clean Heat rebate?', 'Often, yes - EmPower+ and your utility\'s heat pump rebate are separate programs, and NYSERDA coordinates with utility programs. Your EmPower+ contractor will tell you how the funding is split on your project.'),
      ('Is there a separate federal HEAR rebate?', 'Not for most households. New York delivers the federal Home Energy Rebates (HEAR and HOMES) through EmPower+ and NYSERDA\'s Appliance Upgrade Program, so applying to EmPower+ is how you get it.'),
    ]
    faq_html = ''.join(f'<h3>{html.escape(q)}</h3><p>{html.escape(a)}</p>' for q, a in faqs)
    body = f'''<section class="hero">
  <div class="wrap">
    <h1>EmPower+ New York 2026: Free or Half-Price Home Upgrades</h1>
    <p>By <a href="/about">Sam Menard</a> &middot; Updated September 26, 2026</p>
  </div>
</section>

<article class="article">
  <div class="wrap">
    <div class="callout" style="border-left:4px solid var(--amber); background:#fff; padding:16px 18px; border-radius:10px; margin:18px 0;"><strong>Short answer:</strong> EmPower+ is NYSERDA&rsquo;s program for lower-income New Yorkers, open statewide to owners <em>and renters</em> of 1&ndash;4 family homes. Low-income households get upgrades at no cost, up to <strong>$12,000 upstate or $14,000 downstate</strong>. Moderate-income households get <strong>50% covered, up to $6,000 upstate or $7,000 downstate</strong>. It&rsquo;s also how New York delivers the federal HEAR/HOMES rebates.</div>

    <h2>Who qualifies for EmPower+?</h2>
    <p>EmPower+ is for households that meet NYSERDA&rsquo;s income limits, which depend on your county and how many people live with you. It covers owners and renters of one- to four-family homes, anywhere in the state &mdash; NYC, Westchester, Long Island, the Hudson Valley and upstate. If someone in your home already gets help like SNAP or HEAP, ask NYSERDA whether that fast-tracks your application.</p>

    <h2>How much does EmPower+ pay?</h2>
    <div style="overflow-x:auto;"><table style="width:100%; border-collapse:collapse; background:#fff; font-size:15px;">
      <thead><tr style="background:var(--paper-warm);"><th style="padding:8px; border:1px solid var(--rule); text-align:left;">Household</th><th style="padding:8px; border:1px solid var(--rule); text-align:left;">Upstate</th><th style="padding:8px; border:1px solid var(--rule); text-align:left;">Downstate</th></tr></thead>
      <tbody>
        <tr><td style="padding:8px; border:1px solid var(--rule);">Low income</td><td style="padding:8px; border:1px solid var(--rule);">No cost, up to $12,000</td><td style="padding:8px; border:1px solid var(--rule);">No cost, up to $14,000</td></tr>
        <tr><td style="padding:8px; border:1px solid var(--rule);">Moderate income</td><td style="padding:8px; border:1px solid var(--rule);">50% of cost, up to $6,000</td><td style="padding:8px; border:1px solid var(--rule);">50% of cost, up to $7,000</td></tr>
      </tbody>
    </table></div>
    <p>These caps are per project and cover efficiency work like insulation and air sealing. NYSERDA also lists extra funding for heat pumps (for example $10,000 toward an air-source or ground-source heat pump through its Sustainable Futures funding) and $5,000 toward a heat pump water heater through HEAR &mdash; your contractor will confirm what your home qualifies for.</p>

    <h2>How EmPower+ fits with other New York rebates</h2>
    <ul>
      <li><strong>Utility heat pump rebate (NYS Clean Heat or PSEG Long Island):</strong> a separate program from your electric company. Clean Heat pays up to about $8,000&ndash;$12,000 depending on your utility; PSEG Long Island pays $4,000&ndash;$7,500.</li>
      <li><strong>Federal HEAR and HOMES:</strong> delivered through EmPower+ and the Appliance Upgrade Program, not a separate application.</li>
      <li><strong>Federal 25C and 25D tax credits:</strong> ended December 31, 2025.</li>
      <li><strong>Comfort Home:</strong> NYSERDA&rsquo;s insulation packages ($2,500&ndash;$3,000, +$2,000 for windows) for households that don&rsquo;t qualify for EmPower+.</li>
    </ul>

    <h2>How to apply</h2>
    <ol>
      <li>Check the income limits for your county on <a href="{EMPOWER}" rel="noopener">NYSERDA&rsquo;s EmPower+ page</a>.</li>
      <li>Apply online or by phone (1-866-NYSERDA). Renters will need their landlord&rsquo;s OK for the work.</li>
      <li>A participating contractor does a free home energy assessment and lists the upgrades.</li>
      <li>The work is done; NYSERDA pays the contractor directly for the covered share.</li>
    </ol>

    <h2>Common questions</h2>
    {faq_html}

    <h2>What to do next</h2>
    <p>Not sure you qualify? Look up your utility&rsquo;s heat pump rebate first on your <a href="/us/ny/">city page</a>, then check EmPower+. When you&rsquo;re ready, compare top-rated local installers, ranked by Google reviews &mdash; free for homeowners. Related: <a href="/blog/new-york-dac-mapping-eligibility-guide/">DAC eligibility guide</a>, <a href="/us/ny/con-edison/new-york-city/">NYC rebates</a>, <a href="/us/ny/national-grid/buffalo/">Buffalo rebates</a>.</p>
    <p style="font-size:14px; color:var(--ink-soft);">Sources, checked September 26, 2026: <a href="{EMPOWER}" rel="noopener">NYSERDA EmPower+</a>, <a href="{HERFAQ}" rel="noopener">NYSERDA HER/HEAR FAQ</a>, <a href="{MANUAL}" rel="noopener">NYS Clean Heat Program Manual v2</a>, <a href="{COMFORT}" rel="noopener">NYSERDA Comfort Home</a>, <a href="{IRS}" rel="noopener">IRS 25C</a>.</p>
  </div>
</article>'''
    a = t.index('<section class="hero">'); b = t.index('</article>', a) + len('</article>')
    t = t[:a] + body + t[b:]
    t = set_ld(t, [
      {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a2}} for q, a2 in faqs]},
      {'@context': 'https://schema.org', '@type': 'Article', 'headline': title, 'description': desc, 'datePublished': '2026-08-17', 'dateModified': '2026-09-26',
       'author': AUTHOR, 'publisher': {'@type': 'Organization', 'name': 'HomePowerRebate'}, 'mainEntityOfPage': 'https://homepowerrebate.com/blog/new-york-empower-plus-guide/'}])
    p.write_text(t, encoding='utf-8')


# sentence-level corrections for the other NY posts
REPL = {
 'blog/6-new-york-heat-pump-programs-stack-together/index.html': [
   ('Stack Con Edison, National Grid, NYS Clean Heat, federal HEAR, DAC bonus, and EmPower+ programs', 'How NYS Clean Heat, PSEG Long Island, EmPower+, Comfort Home and DAC status really fit together'),
   ('Federal HEAR Tax Credit (IRA Section 30C)', 'Federal tax credits (ended)'),
   ('The federal government is paying 30% of your heat pump cost, up to $3,200', 'The federal 25C credit (30% up to $2,000 for heat pumps) ended December 31, 2025 and no longer applies'),
   ('File your tax return and claim the federal 30% credit', 'Keep your invoices, but note the federal 25C credit ended December 31, 2025'),
   ('<p><strong><a href="https://www.energy.gov/articles/inflation-reduction-act-clean-energy-tax-credits">30% Federal Tax Credit (Energy.gov)</a>:</strong> Up to $3,200 for a heat pump installed between 2022 and 2032. Stacks with everything.</p>',
    '<p><strong>Federal tax credit (25C): ended.</strong> It no longer applies to heat pumps installed after December 31, 2025 (<a href="' + IRS + '" rel="noopener">IRS</a>).</p>'),
   ('<li>Claim the <strong>federal 30% tax credit</strong> on your 2026 tax return (Form 5695).</li>',
    '<li>Don&rsquo;t plan on a federal tax credit &mdash; 25C ended December 31, 2025.</li>'),
   ('• Federal HEAR Tax Credit (30%): $4,000', '• Federal tax credit: $0 (25C ended Dec 31, 2025)'),
 ],
 'blog/heat-pump-or-solar-new-york/index.html': [
   ('State rebates $2K–$4K + federal ITC (30% of cost) = $6K–$9K total', 'NY-Sun incentive (varies by region and income) + NY State solar tax credit; the federal 25D credit ended Dec 31, 2025'),
   ('Federal HEAR stays active through 2030 (unlike most states)', 'Federal HEAR money reaches NY households only through EmPower+'),
   ('Federal HEAR active through 2030', 'Federal HEAR via EmPower+ only'),
   ('Con Edison $2K–$10K + state Clean Heat $6K–$10K + federal HEAR $4K–$8K + DAC bonus $0–$2K = <strong>$14K–$28K+</strong>',
    'Con Edison&rsquo;s NYS Clean Heat rebate: <strong>$7,000&ndash;$10,000</strong> for a single-family whole-home switch ($8,000&ndash;$11,000 in a Disadvantaged Community). EmPower+ can add more for income-eligible homes.'),
   ('Federal HEAR via EmPower+ only. Most states lost HEAR after 2025. New York homeowners stack three sources. That\'s rare and valuable.',
    'Con Edison&rsquo;s Clean Heat rebate is one of the larger utility heat pump rebates in the country, and income-eligible homes can add EmPower+.'),
   ('<td>$14K–$28K+</td>\n          <td>$2K–$8K</td>', '<td>$7K–$11K</td>\n          <td>$7K–$15K</td>'),
   (' A homeowner in Massachusetts gets state + HEAR = $10K–$14K. A New Yorker in NYC gets Con Ed + state + HEAR + DAC = $14K–$28K+. That\'s double the rebate. That\'s why heat pump payback is 4–6 years in NYC vs. 6–8 years in Boston.',
    ' Payback depends heavily on what fuel you replace &mdash; oil and propane homes save the most. Ask your installer for a bill estimate using your actual rates.'),
   ("New York's stacking (HEAR + state + utility) makes heat pumps uniquely attractive compared to other states", 'New York&rsquo;s utility heat pump rebates (NYS Clean Heat, up to about $8,000&ndash;$12,000) make heat pumps attractive, especially for oil and propane homes'),
 ],
 'blog/new-york-cities-ranked-fastest-heat-pump-payback/index.html': [
   ('Payback times include utility rebates + state rebates + federal tax credit', 'Note: payback figures on this page were estimated before the federal 25C credit ended on Dec 31, 2025, and may double-count utility and Clean Heat rebates; treat them as rough and ask for a bill estimate'),
   ('30% up to $3,200', 'ended Dec 31, 2025'),
 ],
 'blog/new-york-dac-mapping-eligibility-guide/index.html': [
   ("you can qualify for significantly higher rebates through New York's Clean Heat and HEAR/HOMES programs &mdash; sometimes up to $14,000 per measure for income-qualified households",
    'your utility&rsquo;s NYS Clean Heat amount goes up (for example Con Edison $11,000 instead of $10,000, National Grid $12,000 instead of $10,000) and the cost cap rises from 70% to 85%'),
 ],
}


def others():
    for rel, pairs in REPL.items():
        p = ROOT / rel; t = p.read_text(encoding='utf-8'); o = t
        for a, b in pairs:
            t = t.replace(a, b)
        if 'what really stacks in New York:' not in t and rel != 'blog/new-york-dac-mapping-eligibility-guide/index.html':
            i = t.find('<article'); j = t.find('>', i) + 1 if i >= 0 else -1
            if j > 0:
                w = t.find('<div class="wrap">', j)
                k = t.find('>', w) + 1 if 0 <= w < j + 200 else j
                t = t[:k] + '\n' + STACK_BOX + t[k:]
        t = re.sub(r'"dateModified":\s*"[^"]*"', '"dateModified": "2026-09-26"', t)
        if t != o:
            p.write_text(t, encoding='utf-8'); print('fixed', rel)


if __name__ == '__main__':
    empower()
    others()
