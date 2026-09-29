#!/usr/bin/env python3
"""Link weakly linked city pages from their own city hub.

Pages like the stacking calculator, the appliances page and BC's city blog guides existed but
had 0-2 internal links, so Google rarely crawled them. This adds a marker-wrapped
"More for {City}" block to each city hub, listing whichever of those pages exist.
Safe to re-run: the block is replaced in place.

  python3 scripts/link_city_extras.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
START, END = "<!-- CITY-EXTRAS-START -->", "<!-- CITY-EXTRAS-END -->"
ANCHOR = "<!-- CANONICAL-FOOTER-START"


def extras(hub_url, slug, label):
    region = "/".join(hub_url.strip("/").split("/")[:2])  # e.g. ca/bc
    cands = [
        (f"/stacking-calculator/{region}/{slug}/", f"Rebate stacking calculator for {label}"),
        (f"{hub_url}appliances/", f"Appliance rebates in {label}"),
        (f"/blog/energy-saving-ideas-bc-home-{slug}/", f"Energy-saving ideas for {label} homes"),
        (f"/blog/window-doors-replacement-rebates-bc-guide-{slug}/", f"Window and door rebates in {label}"),
    ]
    return [(u, t) for u, t in cands if (ROOT / u.strip("/") / "index.html").exists()]


def main():
    data = json.loads((ROOT / "powerscore-data.json").read_text())
    n = 0
    for reg in data["regions"].values():
        for slug_path, city in reg["cities"].items():
            hub = city["url"]
            f = ROOT / hub.strip("/") / "index.html"
            if not f.exists():
                continue
            slug = hub.rstrip("/").split("/")[-1]
            links = extras(hub, slug, city["label"])
            if not links:
                continue
            block = (f'{START}<section style="max-width:1180px;margin:0 auto;padding:24px 28px;">'
                     f'<h2 style="font-family:Fraunces,Georgia,serif;font-size:22px;margin:0 0 10px;">More for {city["label"]}</h2><ul style="margin:0 0 0 20px;line-height:1.9;">'
                     + "".join(f'<li><a href="{u}">{t}</a></li>' for u, t in links) + f"</ul></section>{END}")
            s = f.read_text(encoding="utf-8")
            if START in s:
                s = re.sub(re.escape(START) + ".*?" + re.escape(END), lambda m: block, s, flags=re.S)
            elif ANCHOR in s:
                s = s.replace(ANCHOR, block + "\n" + ANCHOR, 1)
            else:
                continue
            f.write_text(s, encoding="utf-8")
            n += 1
    print(f"Linked extras from {n} city hubs")


if __name__ == "__main__":
    main()
