#!/usr/bin/env python3
"""
Generate all Massachusetts city pages from a template.
Each city gets MA-specific blog posts for internal linking.
"""

from pathlib import Path

# Massachusetts cities
CITIES = [
    {'name': 'Boston', 'slug': 'boston'},
    {'name': 'Brockton', 'slug': 'brockton'},
    {'name': 'Cambridge', 'slug': 'cambridge'},
    {'name': 'Cape Cod', 'slug': 'cape-cod'},
    {'name': 'Fall River', 'slug': 'fall-river'},
    {'name': 'Lawrence', 'slug': 'lawrence'},
    {'name': 'Lowell', 'slug': 'lowell'},
    {'name': 'Lynn', 'slug': 'lynn'},
    {'name': 'New Bedford', 'slug': 'new-bedford'},
    {'name': 'Newton', 'slug': 'newton'},
    {'name': 'Quincy', 'slug': 'quincy'},
    {'name': 'Salem', 'slug': 'salem'},
    {'name': 'Somerville', 'slug': 'somerville'},
    {'name': 'Springfield', 'slug': 'springfield'},
    {'name': 'Worcester', 'slug': 'worcester'},
]

# Blog posts for Massachusetts internal linking
BLOG_POSTS_MA = [
    {
        'url': '/guides/which-rebate-first/',
        'category': 'Guide • Foundations',
        'title': 'Which Rebate Should I Claim First? Priority Guide 2026',
        'description': 'The strategic order to claim rebates and maximize your total savings.'
    },
    {
        'url': '/guides/rebate-stacking-explained/',
        'category': 'Guide • Stacking',
        'title': 'What Is Rebate Stacking? How to Combine Multiple Rebates',
        'description': 'Layer federal, state, utility, and local rebates for maximum benefit.'
    },
    {
        'url': '/blog/41-towns-locked-out-mass-save/',
        'category': 'Guide • MassSave',
        'title': '41 Massachusetts Towns Locked Out of MassSave: What to Do',
        'description': 'Which towns are excluded, why, and alternative rebate programs available.'
    },
    {
        'url': '/blog/smart-thermostat-buying-guide-ma/',
        'category': 'Guide • Thermostats',
        'title': 'Smart Thermostat Buying Guide for Massachusetts (2026)',
        'description': 'Comparing Nest, Ecobee, Honeywell, and more with MA rebate info.'
    },
]

SECTION_MARK = 'Learn more about Massachusetts rebates'


def customize_page(html, city):
    """Inject the MA guides section into a city's OWN existing page.

    Never copies another city's page over this one (a Boston-template
    find/replace clobbered all 14 bespoke hubs in Aug 2026). Idempotent:
    does nothing if the section is already present.
    """
    if SECTION_MARK in html:
        return html

    # Inject blog posts before footer
    blog_html = '<section style="padding:0 28px; margin-bottom: 40px;">\n'
    blog_html += '  <div class="wrap" style="max-width:1000px; margin:0 auto;">\n'
    blog_html += f'    <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 12px; color: #111;">Learn more about Massachusetts rebates</h2>\n'
    blog_html += '    <p style="font-size: 15px; color: #666; margin-bottom: 32px;">Guides and deep-dives to help you navigate MA programs like MassSave.</p>\n'
    blog_html += '    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">\n'

    for post in BLOG_POSTS_MA:
        blog_html += f'''      <a href="{post['url']}" style="display: block; border: 1px solid #d9d0c1; border-radius: 10px; padding: 16px; text-decoration: none; color: inherit;">
        <p style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: #d4751c; margin-bottom: 6px;">{post['category']}</p>
        <h3 style="font-size: 14px; font-weight: 600; margin-bottom: 8px; color: #0a2a2e;">{post['title']}</h3>
        <p style="font-size: 13px; color: #666; margin: 0;">{post['description']}</p>
      </a>
'''

    blog_html += '    </div>\n'
    blog_html += '    <p style="text-align: center; margin-top: 32px;">\n'
    blog_html += '      <a href="/blog/" style="color: #d4751c; text-decoration: none; font-weight: 600; font-size: 14px;">View all guides and articles →</a>\n'
    blog_html += '    </p>\n'
    blog_html += '  </div>\n'
    blog_html += '</section>\n'

    # Insert before footer
    html = html.replace('<footer class="footer">', blog_html + '\n<footer class="footer">', 1)

    return html

def main():
    for city in CITIES:
        output_path = Path(f'us/ma/{city["slug"]}/index.html')
        if not output_path.exists():
            print(f'skip {city["slug"]}: no existing page (this script never creates pages)')
            continue
        html = output_path.read_text(encoding='utf-8')
        new = customize_page(html, city)
        if new != html:
            output_path.write_text(new, encoding='utf-8')
            print(f'✓ injected guides → {output_path}')
        else:
            print(f'= unchanged {output_path}')

if __name__ == '__main__':
    main()
