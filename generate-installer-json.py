#!/usr/bin/env python3
import csv
import json
import os
from collections import defaultdict

# Read the CSV and group by city
installers_by_city = defaultdict(list)

with open('/Users/sammenard/Downloads/Powerrebate/installers/complete-installers.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        city = row.get('City', '').strip()
        if not city:
            continue

        installer = {
            'name': row.get('Business Name', ''),
            'location': row.get('Address', ''),
            'phone': row.get('Phone', ''),
            'website': row.get('Website', ''),
            'rating': float(row.get('Google Rating', 0)) or 0,
            'reviews': int(row.get('Review Count', 0)) or 0,
            'gmaps_url': row.get('Google Maps URL', ''),
            'recommended': row.get('HomePowerRebate Recommended', '').lower() == 'yes',
            'specialty': 'Heat Pump Installation',
            'description': 'HPCN-certified heat pump and solar installer'
        }
        installers_by_city[city].append(installer)

# Sort each city's installers: recommended first, then by rating, then by reviews
for city in installers_by_city:
    installers_by_city[city].sort(
        key=lambda x: (-x['recommended'], -x['rating'], -x['reviews'])
    )

# Create installers/json directory if it doesn't exist
os.makedirs('/Users/sammenard/Downloads/Powerrebate/installers/json', exist_ok=True)

# Write JSON files for each city
for city, installers in installers_by_city.items():
    # Create slug from city name (e.g., "Fort St. John" -> "fort-st-john")
    city_slug = city.lower().replace(' ', '-').replace('.', '')
    json_path = f'/Users/sammenard/Downloads/Powerrebate/installers/json/{city_slug}.json'

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(installers, f, indent=2)

    print(f"✓ {city}: {len(installers)} installers → {city_slug}.json")

print(f"\n✓ Generated JSON files for {len(installers_by_city)} cities")
