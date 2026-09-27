#!/usr/bin/env python3
"""
Generate all California city/region pages from a template.
Each page gets region-specific blog posts for internal linking.
"""

from pathlib import Path

# California region data
REGIONS = [
    {'name': 'Bay Area', 'slug': 'bay-area', 'desc': 'San Francisco, Oakland, San Jose'},
    {'name': 'Inland Empire', 'slug': 'inland-empire', 'desc': 'Riverside, San Bernardino'},
    {'name': 'Sacramento', 'slug': 'sacramento', 'desc': 'Sacramento Valley'},
    {'name': 'Bakersfield', 'slug': 'bakersfield', 'desc': 'Kern County'},
    {'name': 'Fresno', 'slug': 'fresno', 'desc': 'San Joaquin Valley'},
    {'name': 'Los Angeles', 'slug': 'los-angeles', 'desc': 'Los Angeles County'},
    {'name': 'San Diego', 'slug': 'san-diego', 'desc': 'San Diego County'},
]

# Blog posts for California internal linking
BLOG_POSTS_CALIFORNIA = [
    {
        'url': '/blog/california-rebates-outside-utilities/',
        'category': 'Guide • Program',
        'title': 'California Rebates If You\'re Not on a Major Utility',
        'description': 'Help for customers of smaller utilities and community choice aggregators.'
    },
    {
        'url': '/blog/top-5-california-cities-heat-pump-rebate/',
        'category': 'Guide • Rankings',
        'title': 'Top California Cities by Heat Pump Rebate',
        'description': 'Which California metros have the best heat pump incentives and payback.'
    },
]

# Region-specific blog posts
REGION_BLOG_POSTS = {
    'bay-area': [
        {
            'url': '/blog/heat-pump-or-solar-bay-area/',
            'category': 'Guide • Decision',
            'title': 'Heat Pump or Solar First? Bay Area Decision Guide',
            'description': 'Maximize your Bay Area rebates by choosing the right order.'
        },
    ],
    'inland-empire': [
        {
            'url': '/blog/heat-pump-or-solar-inland-empire/',
            'category': 'Guide • Decision',
            'title': 'Heat Pump or Solar First? Inland Empire Decision Guide',
            'description': 'Maximize your Inland Empire rebates by choosing the right order.'
        },
    ],
}

def customize_page(template, region):
    """Replace all placeholders with region-specific values."""
    html = template

    # Replace region name and slug
    # Bay Area template uses "Bay Area" and "bay-area"
    region_title = region['name']
    region_lower = region['slug']

    # Try multiple template variations
    html = html.replace('Bay Area', region_title)
    html = html.replace('bay-area', region_lower)
    html = html.replace('bay_area', region_lower.replace('-', '_'))

    # Add region-specific blog posts if they exist
    all_posts = BLOG_POSTS_CALIFORNIA.copy()
    if region_lower in REGION_BLOG_POSTS:
        all_posts = REGION_BLOG_POSTS[region_lower] + all_posts

    # Inject blog posts before footer
    blog_html = '<section style="padding:0 28px; margin-bottom: 40px;">\n'
    blog_html += '  <div class="wrap" style="max-width:1000px; margin:0 auto;">\n'
    blog_html += f'    <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 12px; color: #111;">Learn more about {region_title} rebates</h2>\n'
    blog_html += '    <p style="font-size: 15px; color: #666; margin-bottom: 32px;">Guides and deep-dives to help you decide on solar, heat pumps, and more.</p>\n'
    blog_html += '    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">\n'

    for post in all_posts:
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
    template_path = Path('us/ca/bay-area/index.html')
    template = template_path.read_text(encoding='utf-8')

    # Generate each region
    for region in REGIONS:
        region_dir = Path(f'us/ca/{region["slug"]}')
        region_dir.mkdir(parents=True, exist_ok=True)

        # Customize template
        html = customize_page(template, region)

        # Write page
        output_path = region_dir / 'index.html'
        output_path.write_text(html, encoding='utf-8')
        print(f'✓ {region["slug"]:20} → us/ca/{region["slug"]}/index.html')

if __name__ == '__main__':
    main()
