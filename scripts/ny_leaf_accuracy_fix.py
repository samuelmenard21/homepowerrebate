#!/usr/bin/env python3
"""NY-only, idempotent sentence fixes on us/ny/** leaf pages (verified 2026-09-26).

- Removes 'federal HEAR on top of Clean Heat' claims (NY routes HEAR/HOMES through EmPower+).
- Removes 'utility rebate + NYS Clean Heat' double counting (Clean Heat IS the utility rebate).
- Removes 'federal tax credits remain available' (25C/25D ended Dec 31, 2025).
- PSEG Long Island is not part of NYS Clean Heat.
- Retires 'matched with vetted contractors' wording.
See data/verified-facts/ny.json.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EMP = '<a href="/blog/new-york-empower-plus-guide/">EmPower+</a>'


def emp(city):
    return (f'Lower-income {city} households should also check EmPower+, which is how New York delivers the federal '
            'Home Energy Rebates &mdash; there is no separate HEAR cheque to apply for.')


FIXED = [
 ('Check the NYSERDA incentive and whether your household qualifies for the federal HEAR rebate, which can add several thousand dollars more for lower- and moderate-income Buffalo homeowners.', emp('Buffalo')),
 ('Check the NYSERDA incentive and whether your household qualifies for the federal HEAR rebate, which can add several thousand dollars more for lower- and moderate-income Syracuse homeowners.', emp('Syracuse')),
 ('Homeowners in Beacon may qualify for the federal HEAR rebate, for lower-income households, on top of the Clean Heat incentive.', emp('Beacon')),
 ('Income-qualified households in Poughkeepsie can pair the federal HEAR rebate with the Clean Heat incentive above — note the federal 25C tax credit expired December 31, 2025, so that credit is no longer part of the math.',
  'Income-qualified Poughkeepsie households can get extra help through EmPower+, which is how New York delivers the federal Home Energy Rebates. The federal 25C tax credit expired December 31, 2025, so it is no longer part of the math.'),
 ('Layer on New York State\'s Clean Heat financing, and if your household qualifies by income, add the federal HEAR rebate plus a Disadvantaged Community bonus where the address qualifies.',
  'The Con Edison amount already is the NYS Clean Heat rebate, so don\'t add Clean Heat on top. If your address is in a Disadvantaged Community the amount goes up, and income-qualified households can also use EmPower+.'),
 ('Lower- and moderate-income Albany households can add the federal HEAR rebate on top, often worth several thousand dollars more, so ask your contractor to run that eligibility check.', emp('Albany')),
 ('Lower-income Kingston households can layer the federal HEAR rebate on top of the Clean Heat incentive above — the federal 25C tax credit is gone (it expired December 31, 2025), so HEAR and Clean Heat are the two pieces left to combine.',
  'Lower-income Kingston households can get extra help through EmPower+, which is how New York delivers the federal Home Energy Rebates. The federal 25C tax credit is gone (it expired December 31, 2025).'),
 ('Mount Vernon households that qualify by income can layer on the federal HEAR rebate and a Disadvantaged Community (DAC) bonus alongside New York State\'s Clean Heat financing — worth asking your contractor to check your address against the DAC map before assuming you don\'t qualify.',
  'Parts of Mount Vernon are Disadvantaged Communities, where Con Edison\'s Clean Heat amount is higher — ask your contractor to check your address against the DAC map. Income-qualified households can also use EmPower+.'),
 ('National Grid utility rebate ($1,500&ndash;$4,000) + NYS Clean Heat ($6,000&ndash;$10,000, income-qualified) + federal HEAR ($4,000&ndash;$8,000, income-qualified).',
  'One rebate: NYS Clean Heat, paid through your utility &mdash; $4,000 to $14,000 for a whole-home switch depending on utility, tier and income. Income-qualified households can add EmPower+.'),
 ('New Rochelle homeowners can build on the $10,000 Con Edison base with New York State\'s Clean Heat financing, and income-qualified households may also add the federal HEAR rebate and a Disadvantaged Community bonus.',
  'The Con Edison amount already is the NYS Clean Heat rebate, so there\'s nothing to add on top of it. Income-qualified New Rochelle households can also use EmPower+.'),
 ('New York State Clean Heat financing stacks with the Con Edison incentive, and income-qualified New York City households in Disadvantaged Community-designated areas can add a DAC bonus and the federal HEAR rebate.',
  'The Con Edison incentive is the NYS Clean Heat rebate, so it doesn\'t stack with itself. Homes in Disadvantaged Communities get a higher amount, and income-qualified New York City households can also use EmPower+.'),
 ('Pair the Con Edison incentive with New York State\'s Clean Heat financing; income-qualified Yonkers households can add the federal HEAR rebate and a DAC bonus on top.',
  'The Con Edison incentive is the NYS Clean Heat rebate. Yonkers homes in a Disadvantaged Community get a higher amount, and income-qualified households can also use EmPower+.'),
 ('Rochester homeowners who qualify by income can stack the federal HEAR rebate, which can meaningfully increase the total, and it\'s worth checking that eligibility before signing a contract.',
  'Rochester is served by RG&amp;E, which runs NYS Clean Heat here. Income-qualified households can also get help through EmPower+ &mdash; check before signing a contract.'),
 ('Saugerties households that qualify by income can add the federal HEAR rebate to the Clean Heat incentive above; the federal 25C tax credit expired December 31, 2025, so it\'s no longer in the mix.',
  'Saugerties households that qualify by income can get extra help through EmPower+; the federal 25C tax credit expired December 31, 2025, so it\'s no longer in the mix.'),
 ('The federal 25C tax credit is off the table now (it ended December 31, 2025), but income-qualified Newburgh households can still add the federal HEAR rebate on top of Clean Heat.',
  'The federal 25C tax credit is off the table now (it ended December 31, 2025), but income-qualified Newburgh households can still get extra help through EmPower+.'),
 (' &middot; National Grid / NYS Clean Heat / Federal HEAR', ' &middot; NYS Clean Heat'),
 ('There is no residential solar rebate in PSEG territory, but federal tax credits and other financing options remain available.',
  'PSEG Long Island has no rooftop solar rebate. Income-eligible homes can get NY-Sun Affordable Solar ($0.40/W on Long Island); the federal 25D solar credit ended December 31, 2025, but the NY State solar tax credit still applies.'),
 ('With PSEG ($4,000–$7,500), state Clean Heat ($6,000–$10,000 if income-qualified), and other rebates, you might keep $11,000–$18,000 in total incentives.',
  'PSEG Long Island pays $4,000 for a whole-home heat pump ($5,000 for moderate income or DAC homes, $7,500 for low income). Long Island is not part of NYS Clean Heat, so there is no second state rebate to add.'),
 ('paying back in 10–13 years even without the federal tax credit.', 'though payback depends on your roof and usage, and the federal 25D solar credit ended December 31, 2025.'),
 # --- Babylon (PSEG LI): $4,000 is the market-rate amount; LI battery incentive requires solar pairing ---
 ('Most Babylon households qualify for the full $7,500.', 'Most households get the $4,000 market-rate amount; $5,000 is for moderate-income or DAC homes and $7,500 for low-income homes.'),
 ('Most Babylon households qualify for the full heat pump rebate.', 'Most households get the $4,000 market-rate amount.'),
 (', with roughly $800/year savings and ~18-year payback on unrebated portion.', '.'),
 ('PSEG offers $200 per kWh through NYSERDA, which works out to roughly $2,700 for a typical 13.5&nbsp;kWh system against a $12,000 installed cost.',
  'On Long Island, NYSERDA&rsquo;s home battery incentive is only for batteries paired with rooftop solar; ask your installer for the current per-kWh amount.'),
 ('PSEG offers $200/kWh through NYSERDA, which works out to roughly $2,700 for a typical 13.5 kWh system.',
  'On Long Island, NYSERDA&rsquo;s home battery incentive is only for batteries paired with rooftop solar; ask your installer for the current per-kWh amount.'),
 ('<p>$200/kWh through NYSERDA. Typical 13.5 kWh system costs ~$12,000. Also provides backup during outages.</p>',
  '<p>NYSERDA incentive, only when paired with rooftop solar on Long Island. Also provides backup during outages.</p>'),
 ('<div class="amount">$2,700</div>', '<div class="amount">Solar-paired only</div>'),
 ('<h4>Home Battery Storage ($200/kWh)</h4>', '<h4>Home Battery Storage (with solar)</h4>'),
 ('<span>~$2,700 for 13.5 kWh system</span>', '<span>Check NYSERDA&rsquo;s current rate</span>'),
 ('font-weight:700; color:#fff;">$7,500</div><div style="font-size:12px; color:rgba(250,247,242,.7); margin-top:4px;">Heat Pump rebate</div>',
  'font-weight:700; color:#fff;">$4,000</div><div style="font-size:12px; color:rgba(250,247,242,.7); margin-top:4px;">Heat Pump rebate (up to $7,500 by income)</div>'),
 ('font-weight:700; color:#fff;">$2,700</div><div style="font-size:12px; color:rgba(250,247,242,.7); margin-top:4px;">Battery Storage rebate</div>',
  'font-weight:700; color:#fff;">$1,200</div><div style="font-size:12px; color:rgba(250,247,242,.7); margin-top:4px;">Heat pump water heater rebate</div>'),
 ('In 2026, a Babylon homeowner can claim $4,000 to $7,500 on a heat pump (tiered by income), $2,700 on a home battery, and $1,200 on a heat pump water heater.',
  'In 2026, a Babylon homeowner can get $4,000 on a whole-home heat pump from PSEG Long Island ($5,000&ndash;$7,500 for moderate- and low-income homes) and up to $1,200 on a heat pump water heater.'),
 ('A typical Babylon household replacing a gas furnace keeps <strong>$7,500 on the heat pump</strong>, plus potentially $2,700 on a battery and $1,200 on a water heater if doing those too — a non-solar stack clearing <strong>$11,400</strong>.',
  'A typical market-rate Babylon household replacing a gas furnace gets <strong>$4,000 on the heat pump</strong>, plus up to $1,200 on a heat pump water heater &mdash; <strong>$5,200</strong> in total. Moderate- and low-income homes get more.'),
 ('PSEG does not rebate solar here, so rooftop is a savings play, not a rebate one.', 'PSEG does not rebate solar here; income-eligible homes can get NY-Sun Affordable Solar ($0.40/W on Long Island).'),
 ('Pays around $200/kWh of installed battery capacity for National Grid upstate electric customers', 'Has been listed at around $200/kWh of installed battery capacity for upstate electric customers (confirm the current block with NYSERDA)'),
 ('to get matched with vetted contractors.','to compare top-rated local installers, ranked by Google reviews &mdash; free for homeowners.'),
]

changed = 0
for p in sorted((ROOT / 'us/ny').rglob('index.html')):
    t = p.read_text(encoding='utf-8'); o = t
    for a, b in FIXED:
        t = t.replace(a, b)
        # JSON-LD copies use raw characters instead of entities
        ja = a.replace('&ndash;', '–').replace('&mdash;', '—').replace('&amp;', '&')
        jb = b.replace('&ndash;', '–').replace('&mdash;', '—').replace('&amp;', '&')
        if ja != a:
            t = t.replace(ja, jb)
    if t != o:
        p.write_text(t, encoding='utf-8'); changed += 1
print('changed', changed)
