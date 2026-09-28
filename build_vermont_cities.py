#!/usr/bin/env python3
"""
Inject Vermont blog/guide links into each existing VT city hub.

INJECT-ONLY: this script never copies one city's hub over another. An earlier
version used us/vt/burlington/index.html as a template and find-replaced the
city name, which overwrote Barre/Montpelier/Rutland/South Burlington with
Burlington Electric Department content (restored 2026-09-28).

The block is wrapped in <!-- VT-BLOG-LINKS-START/END --> markers and is
idempotent: re-running replaces the marked block. An older unmarked copy of the
same section (heading "Learn more about Vermont rebates") is replaced too, so
it never duplicates.
"""

import re
from pathlib import Path

CITIES = ['barre', 'burlington', 'montpelier', 'rutland', 'south-burlington']

BLOG_POSTS_VT = [
    ('/guides/which-rebate-first/', 'Guide • Foundations',
     'Which Rebate Should I Claim First? Priority Guide 2026',
     'The strategic order to claim rebates and maximize your total savings.'),
    ('/guides/rebate-stacking-explained/', 'Guide • Stacking',
     'What Is Rebate Stacking? How to Combine Multiple Rebates',
     'Layer federal, state, utility, and local rebates for maximum benefit.'),
    ('/blog/vermont-virtual-power-plant-battery-rebates/', 'Guide • VPP',
     "Vermont's Home Batteries Just Became Its Biggest Power Plant",
     'How battery incentives and virtual power plant programs are transforming Vermont energy.'),
]

START, END = '<!-- VT-BLOG-LINKS-START -->', '<!-- VT-BLOG-LINKS-END -->'
MARKED = re.compile(re.escape(START) + r'.*?' + re.escape(END) + r'\n?', re.S)
UNMARKED = re.compile(
    r'<section style="padding:0 28px; margin-bottom: 40px;">\n  <div class="wrap"[^>]*>\n'
    r'    <h2[^>]*>Learn more about Vermont rebates</h2>.*?</section>\n\n?', re.S)


def block():
    cards = ''.join(
        f'''      <a href="{u}" style="display: block; border: 1px solid #d9d0c1; border-radius: 10px; padding: 16px; text-decoration: none; color: inherit;">
        <p style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: #d4751c; margin-bottom: 6px;">{cat}</p>
        <h3 style="font-size: 14px; font-weight: 600; margin-bottom: 8px; color: #0a2a2e;">{t}</h3>
        <p style="font-size: 13px; color: #666; margin: 0;">{d}</p>
      </a>
''' for u, cat, t, d in BLOG_POSTS_VT)
    return (f'{START}\n<section style="padding:0 28px; margin-bottom: 40px;">\n'
            '  <div class="wrap" style="max-width:1000px; margin:0 auto;">\n'
            '    <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 12px; color: #111;">Learn more about Vermont rebates</h2>\n'
            '    <p style="font-size: 15px; color: #666; margin-bottom: 32px;">Guides and deep-dives to help you understand Vermont\'s home energy programs.</p>\n'
            '    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">\n'
            f'{cards}    </div>\n'
            '    <p style="text-align: center; margin-top: 32px;">\n'
            '      <a href="/blog/" style="color: #d4751c; text-decoration: none; font-weight: 600; font-size: 14px;">View all guides and articles →</a>\n'
            '    </p>\n  </div>\n</section>\n'
            f'{END}\n')


def inject(html):
    b = block()
    if START in html:
        return MARKED.sub(lambda m: b, html, count=1)
    m = UNMARKED.search(html)
    if m:
        html = html[:m.start()] + b + html[m.end():]
        return UNMARKED.sub('', html)  # drop any extra unmarked copies
    i = html.find('<footer')
    if i == -1:
        raise SystemExit('no <footer> found')
    return html[:i] + b + '\n' + html[i:]


def main():
    for slug in CITIES:
        p = Path(f'us/vt/{slug}/index.html')
        if not p.exists():
            print(f'skip {slug}: hub missing (this script never creates hubs)')
            continue
        old = p.read_text(encoding='utf-8')
        new = inject(old)
        if new != old:
            p.write_text(new, encoding='utf-8')
        print(f'{"updated" if new != old else "unchanged"}  {p}')


if __name__ == '__main__':
    main()
