#!/usr/bin/env python3
"""
Inject the "Learn more about Ontario rebates" internal-link section into EXISTING
Ontario city hub pages (ca/on/<slug>/index.html).

WARNING (2026-09-26): an earlier version of this script copied ca/on/kitchener/index.html
over every city and find-replaced the city name. That wiped each city's hand-researched
content (e.g. Better Homes Ottawa) and left Kitchener / Enova Power / RetrofitWR facts on
every page (doorway pages). It now only replaces/inserts the blog-link section, is
idempotent, and never creates or re-templates a page.
"""

import os
import re
from pathlib import Path

# Ontario city data
CITIES = [
    {'name': 'Barrie', 'slug': 'barrie', 'region': 'Central Ontario'},
    {'name': 'Brampton', 'slug': 'brampton', 'region': 'Greater Toronto Area'},
    {'name': 'Burlington', 'slug': 'burlington', 'region': 'Golden Horseshoe'},
    {'name': 'Cambridge', 'slug': 'cambridge', 'region': 'Waterloo Region'},
    {'name': 'Durham', 'slug': 'durham', 'region': 'Durham Region'},
    {'name': 'Greater Sudbury', 'slug': 'greater-sudbury', 'region': 'Northeastern Ontario'},
    {'name': 'Guelph', 'slug': 'guelph', 'region': 'Waterloo Region'},
    {'name': 'Hamilton', 'slug': 'hamilton', 'region': 'Golden Horseshoe'},
    {'name': 'Kingston', 'slug': 'kingston', 'region': 'Eastern Ontario'},
    {'name': 'Kitchener', 'slug': 'kitchener', 'region': 'Waterloo Region'},
    {'name': 'London', 'slug': 'london', 'region': 'Southwestern Ontario'},
    {'name': 'Markham', 'slug': 'markham', 'region': 'Greater Toronto Area'},
    {'name': 'Mississauga', 'slug': 'mississauga', 'region': 'Greater Toronto Area'},
    {'name': 'Niagara Falls', 'slug': 'niagara-falls', 'region': 'Niagara Region'},
    {'name': 'Oakville', 'slug': 'oakville', 'region': 'Golden Horseshoe'},
    {'name': 'Oshawa', 'slug': 'oshawa', 'region': 'Durham Region'},
    {'name': 'Ottawa', 'slug': 'ottawa', 'region': 'Eastern Ontario'},
    {'name': 'Peterborough', 'slug': 'peterborough', 'region': 'Central Ontario'},
    {'name': 'Pickering', 'slug': 'pickering', 'region': 'Durham Region'},
    {'name': 'St. Catharines', 'slug': 'st-catharines', 'region': 'Niagara Region'},
    {'name': 'Thunder Bay', 'slug': 'thunder-bay', 'region': 'Northwestern Ontario'},
    {'name': 'Timmins', 'slug': 'timmins', 'region': 'Northeastern Ontario'},
    {'name': 'Toronto', 'slug': 'toronto', 'region': 'Greater Toronto Area'},
    {'name': 'Vaughan', 'slug': 'vaughan', 'region': 'Greater Toronto Area'},
    {'name': 'Waterloo', 'slug': 'waterloo', 'region': 'Waterloo Region'},
    {'name': 'Windsor', 'slug': 'windsor', 'region': 'Southwestern Ontario'},
    {'name': 'Winnipeg', 'slug': 'winnipeg', 'region': 'Manitoba'},
]

# Blog posts for Ontario internal linking
BLOG_POSTS_ONTARIO = [
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
        'description': 'Layer federal, provincial, utility, and local rebates for maximum benefit.'
    },
    {
        'url': '/blog/heat-pump-or-solar-ontario/',
        'category': 'Guide • Decision',
        'title': 'Heat Pump or Solar First? (Ontario Edition)',
        'description': 'The optimal order to stack Ontario rebates and maximize your savings.'
    },
    {
        'url': '/blog/ontario-heat-pump-rebate-tiers-explained/',
        'category': 'Guide • Heat Pumps',
        'title': 'Ontario Heat Pump Rebates & Income Tiers Explained',
        'description': 'Income-based rebates, income verification, and eligibility for heating upgrades.'
    },
    {
        'url': '/blog/ontario-solar-rebate-vs-net-metering/',
        'category': 'Guide • Solar',
        'title': 'Ontario Solar: Net Metering vs. Battery Storage',
        'description': 'When you don\'t need a battery in Ontario, and when you do.'
    },
    {
        'url': '/blog/rebate-rejected-ontario/',
        'category': 'Guide • Troubleshooting',
        'title': 'Why Your Ontario Rebate Got Rejected: Fixes & Prevention',
        'description': 'Common mistakes and how to avoid them.'
    },
    {
        'url': '/blog/ontario-loan-closed/',
        'category': 'Update • Programs',
        'title': 'Ontario: Federal Loan Closed. Here\'s What\'s Open in 2026',
        'description': 'What changed with the federal home energy loan and your alternatives.'
    }
]

SECTION_RE = re.compile(
    r'<section style="padding:0 28px; margin-bottom: 40px;">\s*<div class="wrap"[^>]*>\s*'
    r'<h2[^>]*>Learn more about Ontario rebates</h2>.*?</section>\n*', re.S)


def blog_section():
    h = '<section style="padding:0 28px; margin-bottom: 40px;">\n'
    h += '  <div class="wrap" style="max-width:1000px; margin:0 auto;">\n'
    h += '    <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 12px; color: #111;">Learn more about Ontario rebates</h2>\n'
    h += '    <p style="font-size: 15px; color: #666; margin-bottom: 32px;">Guides and deep-dives to help you make the right choice.</p>\n'
    h += '    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">\n'
    for post in BLOG_POSTS_ONTARIO:
        h += ('      <a href="%s" style="display: block; border: 1px solid #d9d0c1; border-radius: 10px; padding: 16px; text-decoration: none; color: inherit;">\n'
              '        <p style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: #d4751c; margin-bottom: 6px;">%s</p>\n'
              '        <h3 style="font-size: 14px; font-weight: 600; margin-bottom: 8px; color: #0a2a2e;">%s</h3>\n'
              '        <p style="font-size: 13px; color: #666; margin: 0;">%s</p>\n'
              '      </a>\n') % (post['url'], post['category'], post['title'], post['description'])
    h += '    </div>\n'
    h += '    <p style="text-align: center; margin-top: 32px;">\n'
    h += '      <a href="/blog/" style="color: #d4751c; text-decoration: none; font-weight: 600; font-size: 14px;">View all guides and articles →</a>\n'
    h += '    </p>\n'
    h += '  </div>\n'
    h += '</section>\n\n'
    return h


def inject(html):
    """Remove any existing blog-link section(s) and insert one fresh copy before the footer."""
    html = SECTION_RE.sub('', html)
    return html.replace('<footer class="footer">', blog_section() + '<footer class="footer">', 1)


def main():
    for city in CITIES:
        path = Path(f'ca/on/{city["slug"]}/index.html')
        if not path.exists():
            print(f'- skip {city["slug"]}: page does not exist (this script never creates pages)')
            continue
        html = path.read_text(encoding='utf-8')
        new = inject(html)
        if new != html:
            path.write_text(new, encoding='utf-8')
            print(f'refreshed {city["slug"]}')


if __name__ == '__main__':
    main()
