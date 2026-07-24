#!/usr/bin/env python3
"""
Apply the branded city picker to the 7 non-city pages that have varied headers:
  - about-us.html          (nav with nav-links)
  - ca/bc/index.html       (nav with Blog link + BC Overview tag)
  - 5 blog/*.html pages     (NO header nav at all — thin bar is their only header)

Run after apply_branded_city_nav.py, from the Powerrebate root.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

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
DROPDOWN_LINKS = "\n".join(
    f'        <a href="/ca/bc/{slug}" style="{LINK_STYLE}">{name}</a>'
    for slug, name in CITIES
)

PICKER = f'''    <div style="position:relative;">
      <button type="button" onclick="var m=this.nextElementSibling; m.style.display=(m.style.display==='grid'?'none':'grid');" style="display:flex; align-items:center; gap:8px; background:var(--teal-deep); color:var(--paper); padding:10px 18px; border-radius:999px; border:none; cursor:pointer; font-family:'Inter Tight',sans-serif; font-weight:600; font-size:14px;">
        Pick your city
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
      </button>
      <div style="display:none; position:absolute; top:calc(100% + 10px); right:0; grid-template-columns:1fr 1fr; gap:8px; padding:16px; background:#fff; border:1px solid var(--rule); border-radius:12px; box-shadow:0 8px 24px rgba(10,42,46,0.12); z-index:60; width:min(340px,86vw); max-height:70vh; overflow-y:auto;">
{DROPDOWN_LINKS}
      </div>
    </div>'''

# Standalone branded header for blog pages (they have no header nav at all).
BLOG_HEADER = f'''<nav class="nav" style="position:sticky; top:0; z-index:50; background:rgba(250,247,242,0.92); backdrop-filter:blur(10px); border-bottom:1px solid var(--rule); padding:14px 24px; display:flex; align-items:center; justify-content:space-between; gap:16px;">
  <a href="/" class="logo" style="font-family:'Fraunces',serif; font-size:18px; font-weight:600; color:var(--teal-deep); text-decoration:none;">Home<span class="logo-power" style="color:var(--amber);">Power</span>Rebate</a>
{PICKER}
</nav>
'''

THIN_BAR_RE = re.compile(
    r'<!-- CITY PICKER STICKY HEADER -->.*?</select>\s*</div>\s*</div>\s*',
    re.DOTALL,
)

# about-us: logo + nav-links, add picker on the right, make nav a flex row.
ABOUT_OLD = '''<nav class="nav">
  <a href="/" class="logo">Home<span class="logo-power">Power</span>Rebate</a>
  <div class="nav-links">
    <a href="/about-us">About</a>
    <a href="/how-we-vet-installers">Vetting</a>
  </div>
</nav>'''
ABOUT_NEW = f'''<nav class="nav" style="display:flex; align-items:center; justify-content:space-between; gap:16px;">
  <a href="/" class="logo">Home<span class="logo-power">Power</span>Rebate</a>
  <div style="display:flex; align-items:center; gap:20px;">
    <div class="nav-links">
      <a href="/about-us">About</a>
      <a href="/how-we-vet-installers">Vetting</a>
    </div>
{PICKER}
  </div>
</nav>'''

# ca/bc overview: add picker into its existing right-side flex group.
OVERVIEW_OLD = '''  <div style="display:flex; align-items:center; gap:20px;">
    <a href="/blog" style="color:var(--ink-soft); font-weight:600; font-size:15px; text-decoration:none;">Blog</a>
    <span class="nav-tag">BC Overview</span>
  </div>'''
OVERVIEW_NEW = f'''  <div style="display:flex; align-items:center; gap:20px;">
    <a href="/blog" style="color:var(--ink-soft); font-weight:600; font-size:15px; text-decoration:none;">Blog</a>
    <span class="nav-tag">BC Overview</span>
{PICKER}
  </div>'''


def patch(path: Path, kind: str) -> bool:
    html = path.read_text(encoding="utf-8")
    original = html
    html, _ = THIN_BAR_RE.subn(BLOG_HEADER if kind == "blog" else "", html)

    if kind == "about" and ABOUT_OLD in html:
        html = html.replace(ABOUT_OLD, ABOUT_NEW, 1)
    elif kind == "overview" and OVERVIEW_OLD in html:
        html = html.replace(OVERVIEW_OLD, OVERVIEW_NEW, 1)

    if html != original:
        path.write_text(html, encoding="utf-8")
        return True
    return False


if __name__ == "__main__":
    targets = [
        (ROOT / "about-us.html", "about"),
        (ROOT / "ca/bc/index.html", "overview"),
    ]
    targets += [(p, "blog") for p in sorted((ROOT / "blog").glob("*.html"))
                if "CITY PICKER STICKY HEADER" in p.read_text(encoding="utf-8")]

    print(f"Patching {len(targets)} straggler pages...\n")
    for path, kind in targets:
        ok = patch(path, kind)
        rel = path.relative_to(ROOT)
        print(f"  {'✓' if ok else '⚠️ '} {rel} ({kind})")
