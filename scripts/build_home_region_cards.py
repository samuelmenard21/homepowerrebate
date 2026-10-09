#!/usr/bin/env python3
"""Homepage "Choose your region" grid: add a card for every region in data/regions.json that has a home_blurb and no hand-made card.
Cards go between the HOME-REGION-CARDS markers, so re-runs replace them. Add a region to data/regions.json (with home_blurb) and run this."""
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import regions

ROOT = Path(__file__).resolve().parent.parent
S, E = "<!-- HOME-REGION-CARDS-START -->", "<!-- HOME-REGION-CARDS-END -->"
STYLE = ("display:block; background:var(--paper); border:1px solid var(--rule); border-radius:16px; padding:26px; text-decoration:none; "
         "transition:all .2s; box-shadow:var(--shadow);")
p = ROOT / "index.html"
html = p.read_text()
html = re.sub(re.escape(S) + r".*?" + re.escape(E) + r"\n?", "", html, flags=re.S)
cards = []
for r in regions.REGIONS:
    if not r.get("home_blurb"):
        continue
    href = f'/{r["path"]}/'
    if f'<a href="{href}" style="display:block' in html:
        continue
    country = "Canada" if r["country"] == "ca" else "United States"
    cards.append(f'''    <a href="{href}" style="{STYLE}" onmouseover="this.style.transform='translateY(-3px)'" onmouseout="this.style.transform='translateY(0)'">
      <div style="font-size:12px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:var(--amber); margin-bottom:8px;">{country} &middot; {len(r["cities"])} cities</div>
      <h3 style="font-family:'Fraunces',serif; font-size:22px; font-weight:600; color:var(--teal-deep); margin-bottom:8px;">{r["name"]}</h3>
      <p style="font-size:14px; color:var(--ink-soft);">{r["home_blurb"]}</p>
    </a>
''')
anchor = "  </div>\n</div>\n\n<!-- REBATE BREAKDOWN"
assert anchor in html, "region grid anchor not found"
html = html.replace(anchor, S + "\n" + "\n".join(cards) + E + "\n\n" + anchor, 1)
p.write_text(html)
print(len(cards), "region cards added")

# llms.txt: one line per region with a home_blurb that is not listed yet (kept between markers so re-runs replace it)
import html as _h
lp = ROOT / "llms.txt"
t = lp.read_text()
LS, LE = "<!-- REGIONS-AUTO-START -->", "<!-- REGIONS-AUTO-END -->"
t = re.sub(re.escape(LS) + r".*?" + re.escape(LE) + r"\n?", "", t, flags=re.S)
lines = []
for r in regions.REGIONS:
    if r.get("home_blurb") and f'/{r["path"]}/' not in t:
        names = ", ".join(c[1] for c in r["cities"])
        lines.append(f'- {r["name"]} — {_h.unescape(r["home_blurb"])} {len(r["cities"])} cities: {names}. /{r["path"]}/')
if lines:
    anchor = "\nNote: as of 2026, the federal 25C/25D"
    assert anchor in t
    t = t.replace(anchor, "\n" + LS + "\n" + "\n".join(lines) + "\n" + LE + "\n" + anchor, 1)
    lp.write_text(t)
print(len(lines), "llms.txt lines")
