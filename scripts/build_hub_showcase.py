#!/usr/bin/env python3
"""Hub redesign layer: a stat strip under each region hub's hero, then a city finder, upgrade tiles and one
"Explore more" row after the program links. Data comes from powerscore-data.json (amounts read from our own city pages).

Marker-wrapped (HUB-STATS, HUB-SHOWCASE), so re-runs replace the blocks. It also removes the separate link boxes
that build_internal_boosts.py used to stack at the bottom of hubs; their links live in "Explore more" now.
  python3 scripts/build_hub_showcase.py   (after build_powerscore.py)
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "powerscore-data.json").read_text())
LABELS = D["category_labels"]
CATS = list(LABELS)
ICON = {"heat-pump": "🔥", "insulation": "🌡️", "solar": "☀️", "battery": "🔋", "water-heater": "💧",
        "smart-thermostats": "🎛️", "ev-charger": "🚗", "windows-doors": "🪟"}
e = html.escape

HUBS = ["ca/bc", "ca/on", "ca/ab", "ca/ns", "us/ma", "us/ny", "us/ca", "us/pa", "us/co", "us/vt", "us/nj"]
PROGRAMS = {"ca/bc": [("bc-hydro-rebates", "BC Hydro rebates"), ("cleanbc-rebates", "CleanBC rebates"), ("bc-hydro-peak-saver", "Peak Saver")],
            "ca/on": [("home-renovation-savings", "Home Renovation Savings")], "ca/ab": [("alberta-energy-rebates", "Alberta rebates guide")],
            "ca/ns": [("efficiency-nova-scotia", "Efficiency Nova Scotia")], "us/ma": [("mass-save", "Mass Save")],
            "us/ny": [("nys-clean-heat", "NYS Clean Heat")], "us/pa": [("peco-rebates", "PECO rebates"), ("ppl-electric-rebates", "PPL Electric rebates")],
            "us/co": [("xcel-energy-colorado-rebates", "Xcel Energy rebates")], "us/ca": [], "us/vt": [], "us/nj": [("pseg-rebates", "PSE&G rebates"), ("jcpl-rebates", "JCP&L rebates"), ("atlantic-city-electric-rebates", "Atlantic City Electric rebates")]}
VERIFIED = {"ca/bc", "ca/on", "ca/ab", "ca/ns", "us/ma", "us/ny", "us/ca", "us/vt", "us/nj"}


def money(v, country):
    return ("CA$" if country == "Canada" else "$") + f"{v:,.0f}"


def cat_page(url, cat):
    for d in (cat, "windows" if cat == "windows-doors" else cat):
        if (ROOT / url.strip("/") / d / "index.html").exists():
            return f"{url}{d}/"
    return url


def stats_block(reg, rs, country):
    cities = len(rs)
    avg = sum(r["overall"] for r in rs) / cities
    best = None
    for r in rs:
        for c in CATS:
            v = r["categories"][c].get("usd_value") or 0
            if v and (best is None or v > best[0]):
                best = (v, c, r["categories"][c]["dollar_value"])
    open_cats = sum(1 for c in CATS if any(r["categories"][c]["status"] == "open" for r in rs))
    big = f'{money(best[2], country)}<small>{e(LABELS[best[1]])}</small>' if best else "—"
    if reg in VERIFIED:
        items = [(f"{cities}", "cities covered"), (f"{avg:.0f}", "average PowerScore"), (big, "biggest single rebate"), (f"{open_cats} of 8", "upgrade types with an open rebate")]
    else:
        n_prog = len(PROGRAMS.get(reg, []))
        items = [(f"{cities}", "cities covered"), (f"{n_prog}" if n_prog else "0", "utility program guides"),
                 ("Being checked", "city-page amounts vs official pages")]
    cells = "".join(f'<div class="hs-stat"><b>{v}</b><span>{l}</span></div>' for v, l in items)
    return f'<!-- HUB-STATS-START --><div class="hs-wrap"><div class="hs-stats">{cells}</div></div><!-- HUB-STATS-END -->'


def showcase_block(reg, rs, country, label):
    order = sorted(rs, key=lambda r: -r["overall"])
    cards = []
    short = reg.split("/")[1]
    for i, r in enumerate(order):
        open_vals = [v["dollar_value"] for v in r["categories"].values() if v["status"] == "open" and v.get("dollar_value")]
        pot = sum(open_vals)
        slug = r["slug"].split("/")[-1]
        n_inst = sum(len(re.findall(r'<li class="rank', p.read_text(encoding="utf-8", errors="ignore")))
                     for p in (ROOT / "installers" / short / slug).glob("*/index.html")) if (ROOT / "installers" / short / slug).is_dir() else 0
        l1 = f"Open rebates worth up to {money(pot, country)}" if pot else "Local programs only"
        l2 = f"{len(open_vals)} of 8 upgrades open" + (f" · {n_inst} installers ranked" if n_inst else "")
        deg = max(0, min(100, r["overall"])) * 3.6
        cards.append(f'<a class="hs-city" href="{r["url"]}" data-name="{e(r["label"]).lower()}" data-score="{r["overall"]}" data-order="{i}">'
                     f'<span class="hs-ring" style="--d:{deg:.0f}deg"><b>{r["overall"]:.0f}</b></span>'
                     f'<span class="hs-cn"><b>{e(r["label"])}</b><small>{l1}</small><small>{l2}</small></span></a>')
    tiles = []
    for c in CATS:
        best = max(rs, key=lambda r: r["categories"][c].get("usd_value") or 0)
        v = best["categories"][c]
        n_open = sum(1 for r in rs if r["categories"][c]["status"] == "open")
        if v.get("dollar_value"):
            body = f'up to <b>{money(v["dollar_value"], country)}</b><small>best in {e(best["label"])} · open in {n_open} of {len(rs)} cities</small>'
            href = cat_page(best["url"], c)
        else:
            if (ROOT / reg / c / "index.html").exists():
                body = '<b>No amount listed</b><small>see what is and is not open</small>'
                href = f"/{reg}/{c}/"
            else:
                body = f'<b>No amount listed</b><small>see city pages for local programs</small>'
                href = best["url"]
        tiles.append(f'<a class="hs-tile" href="{href}"><span class="hs-ti">{ICON[c]}</span><span class="hs-tt"><em>{e(LABELS[c])}</em>{body}</span></a>')
    links = [(f"/programs/{s}/", n) for s, n in PROGRAMS.get(reg, [])]
    if reg.startswith("ca/"):
        links.append(("/blog/greener-homes-grant-explained/", "Greener Homes Grant: what replaced it"))
    if reg in ("ca/bc", "ca/on", "us/ca"):
        links.append(("/blog/net-metering-vs-net-billing/", "Net metering vs net billing"))
    if reg.startswith("us/"):
        links.append(("/programs/federal-tax-credits-2026/", "2026 federal tax credits"))
    links += [("/insulation-rebates/", "Insulation rebates by region"), ("/rebate-tracker/", "What ended and what's new"),
              ("/installers/", "Top-rated installers"), ("/powerscore/", "PowerScore rankings")]
    chips = "".join(f'<a class="hs-chip" href="{u}">{e(t)}</a>' for u, t in links)
    warn = "" if reg in VERIFIED else '<p class="hs-note">Heads up: we have not yet checked every program in this region against its official page, so treat the amounts as a guide.</p>'
    more = f'<button type="button" class="hs-more" id="hs-more">Show all {len(rs)} cities</button>' if len(rs) > 12 else ""
    return f'''<!-- HUB-SHOWCASE-START --><section class="hs-wrap hs-sec" id="find-city" aria-label="{e(label)} at a glance">
<h2 class="hs-h">Find your city in {e(label)}</h2>
<p class="hs-sub">Each ring is the city's PowerScore out of 100. Tap a city for its full rebate guide and top-rated installers.</p>
<div class="hs-ctl"><input type="search" id="hs-q" placeholder="Search {len(rs)} cities" aria-label="Search cities in {e(label)}"><button type="button" class="hs-sort on" data-s="score">Top score</button><button type="button" class="hs-sort" data-s="az">A to Z</button></div>
<div class="hs-grid" id="hs-grid">{"".join(cards)}</div>{more}
<h2 class="hs-h" style="margin-top:34px;">Biggest rebates by upgrade</h2>
<p class="hs-sub">The largest amount found in {e(label)} for each type of upgrade, and where.</p>
<div class="hs-tiles">{"".join(tiles)}</div>{warn}
<h2 class="hs-h" style="margin-top:34px;">Explore more</h2>
<div class="hs-chips">{chips}</div>
</section><!-- HUB-SHOWCASE-END -->'''


REMOVE = ["NET-METERING-LINK", "GREENER-LINK", "INSULATION-HUB-LINK", "BCH-REBATES-LINK"]


def find_hero_end(t):
    m = re.search(r'<(header|section)[^>]*class="hero[^"]*"[^>]*>', t)
    if not m:
        return -1
    tag = m.group(1)
    close = t.find(f"</{tag}>", m.end())
    return -1 if close < 0 else close + len(f"</{tag}>")


def main():
    by = {}
    for r in D["leaderboard_overall"]:
        by.setdefault(r["region"], []).append(r)
    for reg in HUBS:
        f = ROOT / reg / "index.html"
        rs = by.get(reg, [])
        if not f.exists() or not rs:
            continue
        t = f.read_text(encoding="utf-8")
        country, label = rs[0]["country"], rs[0]["region_label"]
        for k in REMOVE:
            t = re.sub(rf"<!-- {k}-START -->.*?<!-- {k}-END -->\n?", "", t, flags=re.S)
        for name, blk in (("HUB-STATS", stats_block(reg, rs, country)), ("HUB-SHOWCASE", showcase_block(reg, rs, country, label))):
            S, E = f"<!-- {name}-START -->", f"<!-- {name}-END -->"
            t = re.sub(re.escape(S) + ".*?" + re.escape(E) + "\n?", "", t, flags=re.S)
            if name == "HUB-STATS":
                i = find_hero_end(t)
            else:
                m = t.find("<!-- PROGRAM-LINKS-END -->")
                i = m + len("<!-- PROGRAM-LINKS-END -->") if m >= 0 else -1
                if i < 0:  # California's body is rebuilt by build_hub_tops, so anchor after the changes box
                    m = t.find("<!-- HUB-CHANGES-END -->")
                    i = m + len("<!-- HUB-CHANGES-END -->") if m >= 0 else -1
            if i < 0:
                print("no anchor for", name, reg)
                continue
            t = t[:i] + "\n" + blk + "\n" + t[i:]
        f.write_text(t, encoding="utf-8")
        print("Hub", reg, len(rs), "cities")


if __name__ == "__main__":
    main()
