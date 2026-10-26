#!/usr/bin/env python3
"""Put a "your project" search bar on region hubs and city pages (2026-10-23), like the one that opens /get-quotes/.
Region hubs (ca|us/<region>/index.html): inside the hero, before the button row, with a city list from data/regions.json.
City hubs and city category pages: a slim bar under the hero with the city already chosen; the reader picks a project.
It is a plain GET form to /get-quotes/ (province, city, project), so it works without JavaScript; the finder reads those parameters.
Wrapped in HUB-SEARCH-START/END markers. Styles are .hub-search in _partials/nav-footer.html. A post-step.
Usage: python3 scripts/add_hub_search.py"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import regions  # noqa: E402

S, E = "<!-- HUB-SEARCH-START -->", "<!-- HUB-SEARCH-END -->"
OLD = re.compile(r"\n?" + re.escape(S) + r"[\s\S]*?" + re.escape(E))
e = html.escape
# one photo per upgrade for the hero of city category pages (free-licence Unsplash set in assets/learn)
NO_BAR = {("bc", "solar")}  # near-duplicate guard: these city pages sit at the 90% limit, so they carry no shared search bar
PHOTO = {"heat-pump": "heat-pump-house", "solar": "solar-roof", "battery": "modern-home", "insulation": "rebate-plans", "windows": "duplex-home", "windows-doors": "duplex-home", "water-heater": "duplex-home", "index": "modern-home"}
PROJECTS = [("", "All projects"), ("heat-pump", "Heat pump"), ("solar", "Solar panels"), ("battery", "Home battery"), ("insulation", "Insulation")]


def proj_select():
    return '<select name="project" aria-label="Your project">' + "".join(f'<option value="{v}">{e(n)}</option>' for v, n in PROJECTS) + "</select>"


def region_bar(code):
    r = regions.BY_CODE[code]
    opts = "".join(f'<option value="{h.strip("/").split("/")[-1]}">{e(n)}</option>' for h, n in r["cities"])
    return (f'{S}<form class="hub-search" action="/get-quotes/" method="get"><input type="hidden" name="province" value="{code}">'
            f'<div class="hub-search-f"><select name="city" aria-label="Your city" required><option value="">Pick your city</option>{opts}</select></div>'
            f'<div class="hub-search-f">{proj_select()}</div><button type="submit">See my rebates</button></form>{E}')


def city_bar(code, slug, name):
    return (f'{S}<div class="hub-search-wrap"><form class="hub-search is-city" action="/get-quotes/" method="get"><input type="hidden" name="province" value="{code}">'
            f'<input type="hidden" name="city" value="{slug}"><div class="hub-search-f"><span class="hub-search-city">{e(name)}</span></div>'
            f'<div class="hub-search-f">{proj_select()}</div><button type="submit">See my rebates</button></form></div>{E}')


def country_bar(codes):
    """Province or state, then project: for /ca/, /us/ and /installers/. The finder opens with that region chosen and its Refine drawer open."""
    import regions as R
    groups = []
    for label, rs in R.grouped():
        rs = [r for r in rs if r["code"] in codes]
        if rs:
            groups.append(f'<optgroup label="{label}">' + "".join(f'<option value="{r["code"]}">{e(r["name"])}</option>' for r in rs) + "</optgroup>")
    return (f'{S}<div class="hub-search-wrap"><form class="hub-search" action="/get-quotes/" method="get"><div class="hub-search-f"><select name="province" aria-label="Your province or state" required>'
            f'<option value="">Pick your province or state</option>{"".join(groups)}</select></div><div class="hub-search-f">{proj_select()}</div><button type="submit">See my rebates</button></form></div>{E}')


def country_pages():
    n = 0
    jobs = [(ROOT / "ca" / "index.html", {r["code"] for r in regions.REGIONS if r["country"] == "ca"}),
            (ROOT / "us" / "index.html", {r["code"] for r in regions.REGIONS if r["country"] == "us"}),
            ]  # /installers/ has its own front (build_installers_front.py)
    for f, codes in jobs:
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8")
        t2 = OLD.sub("", t)
        m = re.search(r'<section class="hero([^"]*)"([\s\S]*?)</section>', t2)
        if not m:
            continue
        head = f'<section class="hero{m.group(1) if "hero-photo" in m.group(1) else m.group(1) + " hero-photo"}"'
        t2 = t2[:m.start()] + head + m.group(2) + "</section>\n" + country_bar(codes) + t2[m.end():]
        if t2 != t:
            f.write_text(t2, encoding="utf-8")
            n += 1
    return n


def calculator_heroes():
    """Photo hero on the calculators (the calculator itself is untouched)."""
    n = 0
    for f in sorted(ROOT.glob("calculator/*/index.html")) + [ROOT / "energy-advisors" / "index.html", ROOT / "energy-auditors" / "index.html"]:
        if f.parent.name in ("embed", "data", "widget") or not f.exists():
            continue
        t = f.read_text(encoding="utf-8")
        t2 = re.sub(r'<(section|header) class="hero(?: hero-photo)?"', r'<\1 class="hero hero-photo"', t, count=1)
        if t2 != t:
            f.write_text(t2, encoding="utf-8")
            n += 1
    return n


def main():
    n = country_pages() + calculator_heroes()
    names = {}
    for code, r in regions.BY_CODE.items():
        for h, nm in r["cities"]:
            names[(code, h.strip("/").split("/")[-1])] = nm
    for code in regions.BY_CODE:
        hub = ROOT / regions.HUB_URL_BY_CODE[code].strip("/") / "index.html"
        if not hub.exists():
            continue
        t = hub.read_text(encoding="utf-8")
        t2 = OLD.sub("", t)
        i = t2.find('<div class="cta-row">')
        if 'hub-hero' not in t2 or i < 0:
            continue
        t2 = t2[:i] + region_bar(code) + t2[i:]
        if t2 != t:
            hub.write_text(t2, encoding="utf-8")
            n += 1
        base = hub.parent
        for f in sorted(base.glob("*/index.html")) + sorted(base.glob("*/*/index.html")):
            slug = f.parts[-2] if f.parent.parent == base else f.parts[-3]
            if (code, slug) not in names or f.parts[-2] == "fr":
                continue
            t = f.read_text(encoding="utf-8")
            t2 = OLD.sub("", t)
            m = re.search(r'<(section|header) class="hero([^"]*)"([\s\S]*?)</\1>', t2)
            if not m:
                continue
            cat = f.parts[-2] if f.parent.parent != base else "index"
            img = PHOTO.get(cat, "modern-home")
            tag = m.group(1)
            hero = f'<{tag} class="hero{m.group(2).replace(" hero-photo", "").split(" hero-img-")[0]} hero-photo hero-img-{img}"{m.group(3)}</{tag}>'
            bar = "" if (code, cat) in NO_BAR else "\n" + city_bar(code, slug, names[(code, slug)])
            t2 = t2[:m.start()] + hero + bar + t2[m.end():]
            if t2 != t:
                f.write_text(t2, encoding="utf-8")
                n += 1
    print(f"hub search bars: {n} pages updated")


if __name__ == "__main__":
    main()
