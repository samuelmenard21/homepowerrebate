#!/usr/bin/env python3
"""
Generate all Vermont city pages from a template.
Each city gets VT-specific blog posts for internal linking.
"""

from pathlib import Path

# Vermont cities
CITIES = [
    {'name': 'Barre', 'slug': 'barre'},
    {'name': 'Burlington', 'slug': 'burlington'},
    {'name': 'Montpelier', 'slug': 'montpelier'},
    {'name': 'Rutland', 'slug': 'rutland'},
    {'name': 'South Burlington', 'slug': 'south-burlington'},
]

# Blog posts for Vermont internal linking
BLOG_POSTS_VT = [
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
        'url': '/blog/vermont-virtual-power-plant-battery-rebates/',
        'category': 'Guide • VPP',
        'title': 'Vermont\'s Home Batteries Just Became Its Biggest Power Plant',
        'description': 'How battery incentives and virtual power plant programs are transforming Vermont energy.'
    },
]

def customize_page(template, city):
    """Replace all placeholders with city-specific values."""
    html = template

    # Replace city name and slug (Burlington template)
    city_title = city['name']
    city_lower = city['slug']

    # Try multiple variations
    html = html.replace('Burlington', city_title)
    html = html.replace('burlington', city_lower)
    html = html.replace('burlington', city_lower)

    # Inject blog posts before footer
    blog_html = '<section style="padding:0 28px; margin-bottom: 40px;">\n'
    blog_html += '  <div class="wrap" style="max-width:1000px; margin:0 auto;">\n'
    blog_html += f'    <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 12px; color: #111;">Learn more about Vermont rebates</h2>\n'
    blog_html += '    <p style="font-size: 15px; color: #666; margin-bottom: 32px;">Guides and deep-dives to help you understand Vermont\'s innovative home energy programs.</p>\n'
    blog_html += '    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">\n'

    for post in BLOG_POSTS_VT:
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
    html = html.replace('<footer', blog_html + '\n<footer')

    return html

def main():
    # Read template
    template_path = Path('us/vt/burlington/index.html')
    template = template_path.read_text(encoding='utf-8')

    # Generate each city
    for city in CITIES:
        city_dir = Path(f'us/vt/{city["slug"]}')
        city_dir.mkdir(parents=True, exist_ok=True)

        # Customize template
        html = customize_page(template, city)

        # Write page
        output_path = city_dir / 'index.html'
        output_path.write_text(html, encoding='utf-8')
        print(f'✓ {city["slug"]:20} → us/vt/{city["slug"]}/index.html')

if __name__ == '__main__':
    main()
