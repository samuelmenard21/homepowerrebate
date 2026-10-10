#!/usr/bin/env python3
"""Responsive layout for installer profile pages (installers/profiles/**/index.html).
The old layout was a fixed 760px column with a 72ch cap on every paragraph, and the Google photo link is often dead (a huge empty box).
Adds one marker-wrapped CSS block after the profile's own styles and makes a failed photo remove itself. Idempotent; generate_installer_profiles.py imports RESPONSIVE_CSS so regenerated pages match.
Usage: python3 scripts/fix_profile_layout.py"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
START, END = "/* IP-RESPONSIVE-START */", "/* IP-RESPONSIVE-END */"
RESPONSIVE_CSS = f"""
{START}
.ip-wrap {{ max-width:1040px; padding:32px clamp(16px,4vw,32px) 80px; }}
.ip-wrap p, .ip-wrap li {{ max-width:none; }}
.ip-hero {{ align-items:flex-end; }}
.ip-photo {{ width:100%; max-height:340px; aspect-ratio:16/6; object-fit:cover; }}
.ip-intro, .ip-reviewsum {{ max-width:72ch; }}
.ip-programs {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr)); gap:12px; }}
.ip-nearby-list {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr)); gap:8px; }}
.ip-vetting, .ip-quote {{ overflow-wrap:anywhere; }}
@media (min-width:900px) {{
  .ip-quote {{ display:grid; grid-template-columns:1fr 380px; column-gap:40px; align-items:start; }}
  .ip-quote > h2, .ip-quote > p {{ grid-column:1; }}
  .ip-quote > form {{ grid-column:2; grid-row:1 / span 3; }}
}}
@media (max-width:560px) {{
  .ip-hero {{ flex-direction:column; align-items:flex-start; gap:8px; }}
  .ip-rating {{ text-align:left; }}
  .ip-actions .ip-btn {{ flex:1 1 100%; text-align:center; }}
  .ip-program {{ flex-wrap:wrap; }}
  .ip-quote {{ padding:24px 18px; }}
  .ip-quote-form {{ max-width:none; }}
}}
{END}"""
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
ANCHOR = ".ip-quote-done { display:none; color:var(--amber-bright); font-weight:700; }"


def patch(t):
    if START in t:
        t = BLOCK_RE.sub(lambda m: RESPONSIVE_CSS.strip(), t, count=1)
    elif ANCHOR in t:
        t = t.replace(ANCHOR, ANCHOR + RESPONSIVE_CSS, 1)
    t = re.sub(r'(<img [^>]*class="ip-photo"(?![^>]*onerror)[^>]*?)(>)', r'\1 onerror="this.remove()"\2', t)
    return t


if __name__ == "__main__":
    n = 0
    for p in sorted((ROOT / "installers/profiles").rglob("index.html")):
        t = p.read_text(encoding="utf-8")
        u = patch(t)
        if u != t:
            p.write_text(u, encoding="utf-8")
            n += 1
    print("patched", n, "profile pages")
