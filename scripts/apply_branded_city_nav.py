#!/usr/bin/env python3
"""
Roll the branded 'Pick your city' dropdown out across the site so every page
uses ONE consistent city picker (replacing the old thin top-bar select).

Self-contained: the picker uses inline styles + an inline toggle handler, so it
does not depend on any page-specific CSS class or JS function. Safe to inject
into pages with differing header markup.

Run from the Powerrebate root:
  python3 scripts/apply_branded_city_nav.py
"""

import re
import sys
from pathlib import Path

CITIES = [
    ("abbotsford", "Abbotsford"), ("burnaby", "Burnaby"), ("chilliwack", "Chilliwack"),
    ("coquitlam", "Coquitlam"), ("fort-st-john", "Fort St. John"), ("kamloops", "Kamloops"),
    ("kelowna", "Kelowna"), ("langley", "Langley"), ("maple-ridge", "Maple Ridge"),
    ("nanaimo", "Nanaimo"), ("penticton", "Penticton"), ("prince-george", "Prince George"),
    ("richmond", "Richmond"), ("squamish", "Squamish"), ("surrey", "Surrey"),
    ("vancouver", "Vancouver"), ("vernon", "Vernon"), ("victoria", "Victoria"),
]

LINK_STYLE = ("padding:10px; border-radius:8px; text-decoration:none; color:var(--ink); "
              "font-weight:500; font-size:14px; border:1px solid var(--rule); text-align:center;")

# The 18-city dropdown grid (shared).
DROPDOWN_LINKS = "\n".join(
    f'      <a href="/ca/bc/{slug}" style="{LINK_STYLE}">{name}</a>'
    for slug, name in CITIES
)

# A self-contained branded picker button + dropdown. Toggling is inline (no named
# function needed). The dropdown is absolutely positioned against the sticky nav.
PICKER = f'''    <div style="position:relative;">
      <button type="button" onclick="var m=this.nextElementSibling; m.style.display=(m.style.display==='grid'?'none':'grid');" style="display:flex; align-items:center; gap:8px; background:var(--teal-deep); color:var(--paper); padding:10px 18px; border-radius:999px; border:none; cursor:pointer; font-family:'Inter Tight',sans-serif; font-weight:600; font-size:14px;">
        Pick your city
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
      </button>
      <div style="display:none; position:absolute; top:calc(100% + 10px); right:0; grid-template-columns:1fr 1fr; gap:8px; padding:16px; background:#fff; border:1px solid var(--rule); border-radius:12px; box-shadow:0 8px 24px rgba(10,42,46,0.12); z-index:60; width:min(340px,86vw); max-height:70vh; overflow-y:auto;">
{DROPDOWN_LINKS}
      </div>
    </div>'''

# City-page nav (identical across all 18). We wrap logo + picker in a flex row.
CITY_NAV_OLD = ('<nav class="nav">\n'
                '  <a href="/" class="logo">Home<span class="logo-power">Power</span>Rebate</a>\n'
                '</nav>')

CITY_NAV_NEW = ('<nav class="nav" style="display:flex; align-items:center; justify-content:space-between; gap:16px;">\n'
                '  <a href="/" class="logo">Home<span class="logo-power">Power</span>Rebate</a>\n'
                f'{PICKER}\n'
                '</nav>')

# Regex to remove the old thin top-bar block (the <select> text is unique to it).
THIN_BAR_RE = re.compile(
    r'<!-- CITY PICKER STICKY HEADER -->.*?</select>\s*</div>\s*</div>\s*',
    re.DOTALL,
)


def patch_city_page(path: Path):
    html = path.read_text(encoding="utf-8")
    original = html

    # 1. Remove the thin top-bar block.
    html, n_bar = THIN_BAR_RE.subn("", html)

    # 2. Swap the logo-only nav for the branded flex nav with the picker.
    if CITY_NAV_OLD in html:
        html = html.replace(CITY_NAV_OLD, CITY_NAV_NEW, 1)
        n_nav = 1
    else:
        n_nav = 0

    if html != original:
        path.write_text(html, encoding="utf-8")
    return n_bar, n_nav


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    city_pages = sorted((root / "ca/bc").glob("*/index.html"))

    print(f"Patching {len(city_pages)} city pages...\n")
    ok, skipped = 0, []
    for p in city_pages:
        n_bar, n_nav = patch_city_page(p)
        city = p.parent.name
        if n_bar and n_nav:
            print(f"  ✓ {city}: thin bar removed, branded picker added")
            ok += 1
        else:
            print(f"  ⚠️  {city}: bar={n_bar} nav={n_nav} — needs manual review")
            skipped.append(city)

    print(f"\n✅ {ok} city pages updated"
          + (f"; ⚠️ review: {', '.join(skipped)}" if skipped else ""))
