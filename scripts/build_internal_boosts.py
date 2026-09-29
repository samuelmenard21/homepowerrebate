#!/usr/bin/env python3
"""Add contextual internal links to pages that rank 9-30 in Search Console but had few inbound links.

Sep 2026 GSC: the SMUD rebate post (EV charger queries, pos 29-30) had 2 inbound links; the Nova Scotia
heat pump water heater pages (pos 21-40) had 4-8. Links go on the pages a searcher would actually be on.
Marker-wrapped, so re-runs replace rather than duplicate. Run after any city rebuild.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from apply_canonical_nav_footer import content_insert_point  # noqa: E402

SMUD = "/blog/smud-rebate-breakdown/"
NS_GUIDE = "/blog/water-heater-buying-guide-ns/"
NS_CALC = "/heat-pump-water-heater/nova-scotia/"

BOX = ('<section style="max-width:880px;margin:24px auto;padding:0 20px;"><p style="background:#f5efe5;border-radius:8px;'
       'padding:14px 18px;margin:0;">{}</p></section>')

# (marker, html, [pages])
SMUD_CITIES = ["sacramento/sacramento", "sacramento/folsom", "sacramento/rancho-cordova"]
JOBS = [
    ("SMUD-LINK", f'<b>On SMUD power?</b> See <a href="{SMUD}">every SMUD rebate: EV charger up to $600, heat pump up to $3,000, water heater and battery</a>.',
     ["us/ca/sacramento/index.html"] + [f"us/ca/{c}/{s}/index.html" for c in SMUD_CITIES for s in ("", "ev-charger", "heat-pump", "water-heater", "battery")]),
    ("SMUD-LINK", f'<b>Sacramento-area homes on SMUD:</b> the <a href="{SMUD}">SMUD EV charger rebate (Charge@Home, up to $600) and other SMUD rebates</a>.',
     ["us/ca/index.html"]),
    ("NS-GUIDE-LINK", f'<b>Replacing an electric tank?</b> Read the <a href="{NS_GUIDE}">Nova Scotia heat pump water heater cost, sizing and rebate guide</a>, or <a href="{NS_CALC}">work out your savings at NS Power rates</a>.',
     ["ca/ns/index.html", "ca/ns/halifax/index.html", "ca/ns/cape-breton/index.html",
      "ca/ns/halifax/water-heater/index.html", "ca/ns/cape-breton/water-heater/index.html", "heat-pump-water-heater/index.html"]),
    ("NS-GUIDE-LINK", f'<b>Sizing, cost and basements:</b> the <a href="{NS_GUIDE}">Nova Scotia heat pump water heater buying guide</a> covers what size to buy and whether it suits a cold basement.',
     ["heat-pump-water-heater/nova-scotia/index.html"]),
    ("NS-CALC-LINK", f'<b>Do the math:</b> the <a href="{NS_CALC}">Nova Scotia heat pump water heater savings calculator</a> uses NS Power\'s current rate.',
     ["blog/water-heater-buying-guide-ns/index.html"]),
]


def main():
    n = 0
    for marker, html, pages in JOBS:
        S, E = f"<!-- {marker}-START -->", f"<!-- {marker}-END -->"
        blk = S + BOX.format(html) + E
        for rel in pages:
            f = ROOT / rel
            if not f.exists():
                continue
            t = f.read_text(encoding="utf-8")
            if S in t:
                new = re.sub(re.escape(S) + ".*?" + re.escape(E), lambda m: blk, t, count=1, flags=re.S)
            else:
                i = content_insert_point(t)
                if i < 0:
                    print("no insert point:", rel)
                    continue
                new = t[:i] + blk + "\n" + t[i:]
            if new != t:
                f.write_text(new, encoding="utf-8")
                n += 1
    print(f"{n} pages updated")


if __name__ == "__main__":
    main()
