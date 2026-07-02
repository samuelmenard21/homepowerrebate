#!/usr/bin/env python3
"""
Generate all BC city pages from the Kelowna template.
Each city gets a custom page with its own saved form hidden input.
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
    }
]

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
