#!/usr/bin/env python3
"""
Generate all BC city pages from the Kelowna template.
Each city gets a custom page with its own saved form hidden input.
Also injects region-specific blog posts to improve internal linking.

Related builders:
- build_ontario_cities.py — Generates all Ontario city pages
- build_california_cities.py — Generates all California region pages
"""

import os
import re
from pathlib import Path

# City data: name, slug, region, phone, 10-yr value, payback, coords
CITIES = [
    {
        'name': 'Abbotsford',
        'slug': 'abbotsford',
        'region': 'Fraser Valley',
        'phone': '(604) 555-0600',
        'value': '$20,000',
        'payback': '8-11 yr payback',
        'lat': '49.0504',
        'lon': '-122.3045'
    },
    {
        'name': 'Chilliwack',
        'slug': 'chilliwack',
        'region': 'Fraser Valley East',
        'phone': '(604) 555-0700',
        'value': '$20,000',
        'payback': '8-11 yr payback',
        'lat': '49.1667',
        'lon': '-122.0830'
    },
    {
        'name': 'Kamloops',
        'slug': 'kamloops',
        'region': 'Thompson Region',
        'phone': '(250) 555-0300',
        'value': '$22,000',
        'payback': '6-9 yr payback',
        'lat': '50.0753',
        'lon': '-120.3368'
    },
    {
        'name': 'Kelowna',
        'slug': 'kelowna',
        'region': 'Central Okanagan',
        'phone': '(250) 555-0100',
        'value': '$20,000',
        'payback': '7-11 yr payback',
        'lat': '49.8880',
        'lon': '-119.4960'
    },
    {
        'name': 'Nanaimo',
        'slug': 'nanaimo',
        'region': 'Central Vancouver Island',
        'phone': '(250) 555-0400',
        'value': '$19,500',
        'payback': '8-11 yr payback',
        'lat': '49.1604',
        'lon': '-123.9459'
    },
    {
        'name': 'Prince George',
        'slug': 'prince-george',
        'region': 'Northern BC',
        'phone': '(250) 555-0900',
        'value': '$20,500',
        'payback': '7-10 yr payback',
        'lat': '53.9167',
        'lon': '-122.7482'
    },
    {
        'name': 'Squamish',
        'slug': 'squamish',
        'region': 'Sea-to-Sky',
        'phone': '(604) 555-1000',
        'value': '$19,000',
        'payback': '8-11 yr payback',
        'lat': '49.7454',
        'lon': '-123.1606'
    },
    {
        'name': 'Surrey',
        'slug': 'surrey',
        'region': 'Metro Vancouver South',
        'phone': '(604) 555-0500',
        'value': '$18,500',
        'payback': '9-12 yr payback',
        'lat': '49.1926',
        'lon': '-122.8010'
    },
    {
        'name': 'Vancouver',
        'slug': 'vancouver',
        'region': 'Metro Vancouver',
        'phone': '(604) 555-0100',
        'value': '$18,500',
        'payback': '9-12 yr payback',
        'lat': '49.2827',
        'lon': '-123.1207'
    },
    {
        'name': 'Vernon',
        'slug': 'vernon',
        'region': 'North Okanagan',
        'phone': '(250) 555-0800',
        'value': '$21,000',
        'payback': '6-10 yr payback',
        'lat': '50.2685',
        'lon': '-119.2723'
    },
    {
        'name': 'Victoria',
        'slug': 'victoria',
        'region': 'Vancouver Island South',
        'phone': '(250) 555-0200',
        'value': '$19,000',
        'payback': '8-11 yr payback',
        'lat': '48.4281',
        'lon': '-123.3656'
    },
    {
        'name': 'Burnaby',
        'slug': 'burnaby',
        'region': 'Metro Vancouver',
        'phone': '(604) 555-0550',
        'value': '$18,500',
        'payback': '9-12 yr payback',
        'lat': '49.2504',
        'lon': '-122.9945'
    },
    {
        'name': 'Penticton',
        'slug': 'penticton',
        'region': 'South Okanagan',
        'phone': '(250) 555-0850',
        'value': '$22,500',
        'payback': '6-9 yr payback',
        'lat': '49.5008',
        'lon': '-119.5886'
    },
    {
        'name': 'Fort St. John',
        'slug': 'fort-st-john',
        'region': 'Northeast BC',
        'phone': '(250) 555-1100',
        'value': '$21,000',
        'payback': '7-10 yr payback',
        'lat': '56.2507',
        'lon': '-120.8425'
    }
]

# Blog posts to inject for regional internal linking (fixes orphaned blog posts)
BLOG_POSTS_BY_REGION = {
    'BC': [
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
            'url': '/blog/heat-pump-or-solar-bc/',
            'category': 'Guide • Decision',
            'title': 'Heat Pump or Solar First? (BC Edition)',
            'description': 'The smart order to maximize your BC rebates and your home\'s comfort.'
        },
        {
            'url': '/blog/bc-hydro-schedule-2289-battery-payback/',
            'category': 'Guide • Battery',
            'title': 'BC Hydro Schedule 2289: What It Means for Battery Savings',
            'description': 'How the rate change affects your battery payback and Peak Saver value.'
        },
        {
            'url': '/blog/cleanbc-rebate-changes-july-2026/',
            'category': 'Update • Programs',
            'title': 'CleanBC Rebate Changes July 6, 2026',
            'description': 'What changed, who it affects, and what to do before the cutoff.'
        },
        {
            'url': '/blog/trane-carrier-heat-pumps-bc/',
            'category': 'Article • Comparison',
            'title': 'Trane & Carrier Heat Pumps in BC: Why They\'re Rare and Whether to Wait',
            'description': 'Cold-climate rated options and when they might be worth the premium.'
        }
    ]
}

def get_blog_posts_html(city_region):
    """Generate HTML for region-specific blog posts."""
    posts = BLOG_POSTS_BY_REGION.get(city_region, [])
    if not posts:
        return ''

    html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-top: 20px;">\n'
    for post in posts:
        html += f'''      <a href="{post['url']}" style="display: block; border: 1px solid #d9d0c1; border-radius: 10px; padding: 16px; text-decoration: none; color: inherit;">
        <p style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: #d4751c; margin-bottom: 6px;">{post['category']}</p>
        <h3 style="font-size: 14px; font-weight: 600; margin-bottom: 8px; color: #0a2a2e;">{post['title']}</h3>
        <p style="font-size: 13px; color: #666; margin: 0;">{post['description']}</p>
      </a>
'''
    html += '    </div>'
    return html

def customize_page(template, city):
    """Replace all placeholders in the template with city-specific values."""
    html = template

    # Capitalize variants
    city_title = city['name']  # Kelowna
    city_lower = city['slug']  # kelowna

    # Case-sensitive replacements (for structured data, URLs, geo tags)
    html = html.replace('Kelowna', city_title)
    html = html.replace('kelowna', city_lower)
    html = html.replace('"Central Okanagan"', f'"{city["region"]}"')
    html = html.replace("'Central Okanagan'", f"'{city['region']}'")

    # Coordinates (geo.position uses semicolon, ICBM uses comma)
    html = html.replace('49.8880;-119.4960', f'{city["lat"]};{city["lon"]}')
    html = html.replace('49.8880, -119.4960', f'{city["lat"]}, {city["lon"]}')

    # Phone number (all instances across multiple forms + schema)
    html = html.replace('(250) 555-0100', city['phone'])
    html = html.replace('+1-250-555-0100', f'+1-{city["phone"].replace(" ", "-").replace("(", "").replace(")", "")}')

    # Value and payback (in FAQ schema)
    html = html.replace('$20,000', city['value'])
    html = html.replace('7-11 yr payback', city['payback'])

    # Inject region-specific blog posts (for internal linking)
    blog_html = get_blog_posts_html('BC')  # All BC cities use BC-specific posts
    html = html.replace(
        '    </div>\n\n    <p style="text-align: center; margin-top: 32px;">',
        '    </div>\n' + blog_html + '\n\n    <p style="text-align: center; margin-top: 32px;">'
    )

    return html

def main():
    # Read template
    template_path = Path('ca/bc/kelowna/index.html')
    template = template_path.read_text(encoding='utf-8')

    # Generate each city
    for city in CITIES:
        city_dir = Path(f'ca/bc/{city["slug"]}')
        city_dir.mkdir(parents=True, exist_ok=True)

        # Customize template
        html = customize_page(template, city)

        # Write page
        output_path = city_dir / 'index.html'
        output_path.write_text(html, encoding='utf-8')
        print(f'✓ {city["slug"]:15} → ca/bc/{city["slug"]}/index.html')

if __name__ == '__main__':
    main()
