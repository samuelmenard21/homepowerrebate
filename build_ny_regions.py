#!/usr/bin/env python3
"""
Inject NY-specific guide links into each existing New York utility hub.

INJECT-ONLY. An earlier version of this script copied us/ny/national-grid/index.html
over every other utility hub (find-replacing the utility name), which clobbered the
bespoke Con Edison, PSEG Long Island and Central Hudson hubs on 2026-09-26. This
version never replaces page content: it only adds/updates a marked guides block
inside each hub's OWN file, and is safe to re-run.
"""

from pathlib import Path

REGIONS = [
    {'name': 'Central Hudson', 'slug': 'central-hudson'},
    {'name': 'Con Edison', 'slug': 'con-edison'},
    {'name': 'National Grid', 'slug': 'national-grid'},
    {'name': 'PSEG Long Island', 'slug': 'pseg'},
]

BLOG_POSTS_NY = [
    {'url': '/guides/which-rebate-first/', 'category': 'Guide • Foundations',
     'title': 'Which Rebate Should I Claim First? Priority Guide 2026',
     'description': 'The order to claim rebates so you keep the most money.'},
    {'url': '/guides/rebate-stacking-explained/', 'category': 'Guide • Stacking',
     'title': 'What Is Rebate Stacking? How to Combine Multiple Rebates',
     'description': 'Which rebates can be combined, and which ones cancel each other out.'},
    {'url': '/blog/6-new-york-heat-pump-programs-stack-together/', 'category': 'Guide • NY Programs',
     'title': 'New York Heat Pump Programs: What Stacks and What Doesn\'t',
     'description': 'How NYS Clean Heat, EmPower+, Comfort Home and local programs fit together.'},
    {'url': '/blog/new-york-empower-plus-guide/', 'category': 'Guide • EmPower+',
     'title': 'EmPower+ for New York Homeowners',
     'description': 'Income-qualified program details, eligibility, and how to apply.'},
    {'url': '/blog/new-york-dac-mapping-eligibility-guide/', 'category': 'Guide • Eligibility',
     'title': 'Are You in an NY Disadvantaged Community? Rebate Guide',
     'description': 'Check your DAC status and see which rebates pay more there.'},
    {'url': '/blog/new-york-cities-ranked-fastest-heat-pump-payback/', 'category': 'Guide • Payback',
     'title': 'New York Cities Ranked by Heat Pump Payback',
     'description': 'Where heat pumps pay back fastest in NY based on local heating costs.'},
    {'url': '/blog/energy-saving-ideas-ny-home/', 'category': 'Guide • Quick Wins',
     'title': '11 Ways to Cut Your Energy Bill in New York (2026)',
     'description': 'Free and low-cost energy-saving actions with real NY incentives.'},
]

START = '<!-- ny-guides:start -->'
END = '<!-- ny-guides:end -->'


def build_blog_section():
    h = START + '\n<section style="padding:0 28px; margin-bottom: 40px;">\n'
    h += '  <div class="wrap" style="max-width:1000px; margin:0 auto;">\n'
    h += '    <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 12px; color: #111;">Learn more about New York rebates</h2>\n'
    h += '    <p style="font-size: 15px; color: #666; margin-bottom: 32px;">Guides to help you combine NY rebates and choose the right upgrades.</p>\n'
    h += '    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">\n'
    for post in BLOG_POSTS_NY:
        h += f'''      <a href="{post['url']}" style="display: block; border: 1px solid #d9d0c1; border-radius: 10px; padding: 16px; text-decoration: none; color: inherit;">
        <p style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: #d4751c; margin-bottom: 6px;">{post['category']}</p>
        <h3 style="font-size: 14px; font-weight: 600; margin-bottom: 8px; color: #0a2a2e;">{post['title']}</h3>
        <p style="font-size: 13px; color: #666; margin: 0;">{post['description']}</p>
      </a>
'''
    h += '    </div>\n    <p style="text-align: center; margin-top: 32px;">\n'
    h += '      <a href="/blog/" style="color: #d4751c; text-decoration: none; font-weight: 600; font-size: 14px;">View all guides and articles →</a>\n'
    h += '    </p>\n  </div>\n</section>\n' + END + '\n'
    return h


def strip_legacy(html):
    """Remove unmarked copies of the block left by the old clobbering version."""
    marker = '<section style="padding:0 28px; margin-bottom: 40px;">\n  <div class="wrap" style="max-width:1000px; margin:0 auto;">\n    <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 12px; color: #111;">Learn more about New York rebates</h2>'
    while marker in html:
        i = html.index(marker)
        j = html.index('</section>', i) + len('</section>')
        html = html[:i] + html[j:].lstrip('\n')
    return html


def inject(html, block):
    if START in html:
        pre, rest = html.split(START, 1)
        post = rest.split(END, 1)[1].lstrip('\n')
        return pre + block + post
    html = strip_legacy(html)
    i = html.find('<footer')
    return html if i < 0 else html[:i] + block + '\n' + html[i:]


def main():
    block = build_blog_section()
    for region in REGIONS:
        path = Path(f'us/ny/{region["slug"]}/index.html')
        if not path.exists():
            print(f'skip (missing) {path}')
            continue
        html = path.read_text(encoding='utf-8')
        new = inject(html, block)
        if new != html:
            path.write_text(new, encoding='utf-8')
            print(f'injected {path}')
        else:
            print(f'unchanged {path}')


if __name__ == '__main__':
    main()
