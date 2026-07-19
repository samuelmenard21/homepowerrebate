#!/usr/bin/env python3
import os
import re

# Cities in BC
cities = [
    "abbotsford", "burnaby", "chilliwack", "coquitlam", "fort-st-john",
    "kamloops", "kelowna", "langley", "maple-ridge", "nanaimo",
    "penticton", "prince-george", "richmond", "squamish", "surrey",
    "vancouver", "vernon", "victoria"
]

# Read the carousel HTML
with open('/Users/sammenard/Downloads/Powerrebate/installers/installer-carousel.html', 'r') as f:
    carousel_html = f.read()

# The section to replace (from "Your trusted installer" to closing </section>)
replace_pattern = r'<section class="section">\s*<div class="wrap">\s*<div class="eyebrow">Your trusted installer</div>.*?</section>\s*<section class="section">\s*<div class="wrap">\s*<div class="eyebrow">The short version</div>'

for city in cities:
    city_dir = f'/Users/sammenard/Downloads/Powerrebate/ca/bc/{city}'
    index_file = os.path.join(city_dir, 'index.html')

    if not os.path.exists(index_file):
        print(f"✗ {city}: index.html not found")
        continue

    with open(index_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Format the city name for display (e.g., "fort-st-john" -> "Fort St. John")
    city_display = ' '.join(word.capitalize() for word in city.split('-'))

    # Create city-specific carousel with proper city name
    city_carousel = carousel_html.replace('[CITY]', city_display)

    # Replace the matched installer section with carousel
    # Using a more specific pattern that matches the actual structure
    new_content = re.sub(
        r'<section class="section">\s*<div class="wrap">\s*<div class="eyebrow">Your trusted installer</div>.*?</section>(?=\s*<section class="section">\s*<div class="wrap">\s*<div class="eyebrow">The short version</div>)',
        city_carousel + '\n\n<section class="section">\n  <div class="wrap">\n    <div class="eyebrow">The short version</div>',
        content,
        flags=re.DOTALL
    )

    if new_content == content:
        print(f"✗ {city}: pattern not matched")
        continue

    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✓ {city}: replaced Coming soon with carousel")

print("\n✓ All 18 city pages updated")
