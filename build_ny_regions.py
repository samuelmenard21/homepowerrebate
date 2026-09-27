#!/usr/bin/env python3
"""
Generate all New York utility region pages from a template.
Each region gets NY-specific blog posts for internal linking.
"""

from pathlib import Path

# NY utility regions
REGIONS = [
    {'name': 'Central Hudson', 'slug': 'central-hudson'},
    {'name': 'Con Edison', 'slug': 'con-edison'},
    {'name': 'National Grid', 'slug': 'national-grid'},
    {'name': 'PSEG', 'slug': 'pseg'},
]

# Blog posts for New York internal linking (fixes orphaned NY content)
BLOG_POSTS_NY = [
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
        'url': '/blog/6-new-york-heat-pump-programs-stack-together/',
        'category': 'Guide • NY Programs',
        'title': '6 New York Heat Pump Programs You Can Stack Together',
        'description': 'How to layer NY State, utility, and local heat pump rebates for maximum benefit.'
    },
    {
        'url': '/blog/new-york-empower-plus-guide/',
        'category': 'Guide • EmPower+',
        'title': 'EmPower+ for New York Homeowners: Free/Cheap Heat Pump Guide',
        'description': 'Income-qualified program details, eligibility, and how to apply.'
    },
    {
        'url': '/blog/new-york-dac-mapping-eligibility-guide/',
        'category': 'Guide • Eligibility',
        'title': 'Are You in an NY Disadvantaged Community? Rebate Guide',
        'description': 'Check your DAC status and unlock additional funding.'
    },
    {
        'url': '/blog/new-york-cities-ranked-fastest-heat-pump-payback/',
        'category': 'Guide • Payback',
        'title': 'New York Cities Ranked by Fastest Heat Pump Payback',
        'description': 'Where heat pumps pay back fastest in NY based on local heating costs.'
    },
    {
        'url': '/blog/energy-saving-ideas-ny-home/',
        'category': 'Guide • Quick Wins',
        'title': '11 Ways to Cut Your Energy Bill in New York (2026)',
        'description': 'Free and low-cost energy-saving actions with real NY incentives.'
    },
]

def customize_page(template, region):
    """Replace all placeholders with region-specific values."""
    html = template

    # Replace region name and slug (National Grid template)
    region_title = region['name']
    region_lower = region['slug']

    # Try multiple variations
    html = html.replace('National Grid', region_title)
    html = html.replace('national-grid', region_lower)
    html = html.replace('national_grid', region_lower.replace('-', '_'))

    # Inject blog posts before footer
    blog_html = '<section style="padding:0 28px; margin-bottom: 40px;">\n'
    blog_html += '  <div class="wrap" style="max-width:1000px; margin:0 auto;">\n'
    blog_html += f'    <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 12px; color: #111;">Learn more about New York rebates</h2>\n'
    blog_html += '    <p style="font-size: 15px; color: #666; margin-bottom: 32px;">Guides and deep-dives to help you stack NY rebates and choose the right upgrades.</p>\n'
    blog_html += '    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">\n'

    for post in BLOG_POSTS_NY:
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
    template_path = Path('us/ny/national-grid/index.html')
    template = template_path.read_text(encoding='utf-8')

    # Generate each region
    for region in REGIONS:
        region_dir = Path(f'us/ny/{region["slug"]}')
        region_dir.mkdir(parents=True, exist_ok=True)

        # Customize template
        html = customize_page(template, region)

        # Write page
        output_path = region_dir / 'index.html'
        output_path.write_text(html, encoding='utf-8')
        print(f'✓ {region["slug"]:20} → us/ny/{region["slug"]}/index.html')

if __name__ == '__main__':
    main()
