#!/usr/bin/env python3
"""
Generate all Ontario city pages from a template.
Each city gets a custom page with region-specific blog posts for internal linking.
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
    }
]

def customize_page(template, city):
    """Replace all placeholders in the template with city-specific values."""
    html = template

    # Replace city name and slug (both directions for URLs, titles, etc.)
    city_title = city['name']
    city_lower = city['slug']

    # Replace in title, description, URLs
    html = html.replace('Kitchener', city_title)
    html = html.replace('kitchener', city_lower)
    html = html.replace('kitchener', city_lower)
    html = html.replace('Waterloo Region', city['region'])

    # Inject Ontario-specific blog posts before footer
    blog_html = '<section style="padding:0 28px; margin-bottom: 40px;">\n'
    blog_html += '  <div class="wrap" style="max-width:1000px; margin:0 auto;">\n'
    blog_html += '    <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 12px; color: #111;">Learn more about Ontario rebates</h2>\n'
    blog_html += '    <p style="font-size: 15px; color: #666; margin-bottom: 32px;">Guides and deep-dives to help you make the right choice.</p>\n'
    blog_html += '    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">\n'

    for post in BLOG_POSTS_ONTARIO:
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
    html = html.replace('<footer class="footer">', blog_html + '\n<footer class="footer">')

    return html

def main():
    # Read template
    template_path = Path('ca/on/kitchener/index.html')
    template = template_path.read_text(encoding='utf-8')

    # Generate each city
    for city in CITIES:
        city_dir = Path(f'ca/on/{city["slug"]}')
        city_dir.mkdir(parents=True, exist_ok=True)

        # Customize template
        html = customize_page(template, city)

        # Write page
        output_path = city_dir / 'index.html'
        output_path.write_text(html, encoding='utf-8')
        print(f'✓ {city["slug"]:20} → ca/on/{city["slug"]}/index.html')

if __name__ == '__main__':
    main()
