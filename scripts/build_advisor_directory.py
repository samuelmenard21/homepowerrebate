#!/usr/bin/env python3
"""
Energy advisor and auditor directory and profiles (added 2026-10-17).

  /energy-advisors/            every NRCan-licensed EnerGuide service organization (Canada), by province
  /energy-auditors/            every RESNET HERS rating company in the US states we cover, by state
  /energy-advisors/<slug>/     one profile per company (noindex, like installer profiles)
  /energy-auditors/<slug>/

Data: data/energy-advisor-directory.json (written by build_energy_advisor_list.py), data/energy-advisor-sites.json
(services each company's website mentions, from scan_advisor_websites.py) and the city lists in
installers/*energy-advisor- / *energy-auditor-installers-real.csv (the same rows the ranking pages use).

A company we matched to a Google Maps listing gets the full profile: rating, review count, address, Maps link and its
place in each city ranking. Every other company gets the basic profile: phone, website, the cities it serves and the
services its website mentions. Google data is shown with attribution and never goes into structured data.

Also writes data/energy-advisor-profiles.json ({"ca|<name lower>": "/energy-advisors/<slug>/"}), which
build_installer_rankings.py reads to link ranking cards to these profiles. Run this before the rankings.

  python3 scripts/build_advisor_directory.py
"""
import csv
import html
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import advisor_profile_page  # noqa: E402
import page_kit  # noqa: E402
import regions  # noqa: E402

e = html.escape
BASE = "https://homepowerrebate.com"
DIR = json.loads((ROOT / "data" / "energy-advisor-directory.json").read_text())
SITES = json.loads((ROOT / "data" / "energy-advisor-sites.json").read_text()) if (ROOT / "data" / "energy-advisor-sites.json").exists() else {}
MAP_OUT = ROOT / "data" / "energy-advisor-profiles.json"
GUIDE = "/energy-advisors/when-to-call-an-energy-advisor/"
# Details a company gave us by email (services, base, area), keyed by company name. Shown on its profile as plain services.
OWNER = json.loads((ROOT / "data" / "energy-advisor-owner-details.json").read_text())["companies"] if (ROOT / "data" / "energy-advisor-owner-details.json").exists() else {}
MIN_RANKED = 3
PRIOR_REVIEWS, PRIOR_RATING = 25, 4.5
NRCAN_URL = DIR["sources"]["nrcan"]
RESNET_URL = DIR["sources"]["resnet"]
TODAY = date.today()
PROV_NAMES = {"AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba", "NB": "New Brunswick", "NL": "Newfoundland and Labrador",
              "NS": "Nova Scotia", "NT": "Northwest Territories", "NU": "Nunavut", "ON": "Ontario", "PEI": "Prince Edward Island",
              "QC": "Quebec", "SK": "Saskatchewan", "YT": "Yukon"}
STATE_NAMES = {r["abbr"]: r["name"] for r in regions.REGIONS if r["country"] == "us"}
KIND = {
    "ca": {"root": "/energy-advisors/", "pro": "energy advisor", "pros": "energy advisors", "service": "energy-advisor",
           "Title": "Registered Energy Advisors", "who": "NRCan-licensed EnerGuide service organization", "src": NRCAN_URL,
           "src_name": "Natural Resources Canada: find service organizations for existing homes"},
    "us": {"root": "/energy-auditors/", "pro": "home energy auditor", "pros": "home energy auditors", "service": "energy-auditor",
           "Title": "Home Energy Auditors", "who": "RESNET HERS rating company", "src": RESNET_URL,
           "src_name": "RESNET Rating Companies 2026"},
}
PROFILE_CSS = "profile-88a4d3e4"  # the installer profiles' stylesheet: one profile template site-wide


def slugify(s):
    s = html.unescape(s).lower().replace("&", "and").replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def score(rating, reviews):
    return (reviews / (reviews + PRIOR_REVIEWS)) * rating + (PRIOR_REVIEWS / (reviews + PRIOR_REVIEWS)) * PRIOR_RATING


def city_rows():
    """{(country, region, city): [rows]} from the advisor and auditor CSVs."""
    out = defaultdict(list)
    for f in sorted((ROOT / "installers").glob("*energy-a[du]*-installers-real.csv")):
        m = re.match(r"(?:([a-z]{2})-)?energy-(advisor|auditor)-installers-real\.csv$", f.name)
        if not m:
            continue
        reg = m.group(1) or "bc"
        country = "ca" if m.group(2) == "advisor" else "us"
        for r in csv.DictReader(f.open(encoding="utf-8")):
            out[(country, reg, r["City"].strip())].append(r)
    return out


def hub_info():
    """(region, city label lower) -> (hub url, slug) from data/regions.json."""
    out = {}
    for r in regions.REGIONS:
        for url, label in r.get("cities", []):
            out[(r["code"], label.lower())] = (url, url.rstrip("/").split("/")[-1])
    return out


HUBS = hub_info()


def city_slug(reg, city):
    return HUBS.get((reg, city.lower()), (None, slugify(city)))[1]


def rankings(rows_by_city):
    """{(country, name lower): [(region, city, position, count, url)]} for cities with a ranking page."""
    out = defaultdict(list)
    for (country, reg, city), rows in rows_by_city.items():
        rated = [r for r in rows if r["Google Rating"]]
        if len(rated) < MIN_RANKED:
            continue
        rated.sort(key=lambda r: score(float(r["Google Rating"]), int(float(r["Review Count"]))), reverse=True)
        url = f"/installers/{reg}/{city_slug(reg, city)}/{KIND[country]['service']}/"
        for i, r in enumerate(rated, 1):
            out[(country, r["Business Name"].strip().lower())].append((reg, city, i, len(rated), url))
    return out


def tel(p):
    return re.sub(r"[^\d+]", "", p)


def services(c):
    s = SITES.get(c["website"]) or {}
    return s.get("services", []), s.get("checked", "")


def pro_tools(country, region_code=None, city=None):
    """The offer to advisors and auditors: calculator embed, printable city rebate sheet, badge."""
    items = ['<li><b>A rebate calculator for your website.</b> Clients answer a few questions and see the rebates they can stack. '
             f'<a href="/calculator/widget/{"?r=" + region_code if region_code else ""}">Get the embed code</a>.</li>',
             '<li><b>A one-page rebate sheet for each city</b>, with every open program, its main rule and the official source, to '
             'print or email to clients. ' + (f'<a href="/rebate-sheet/{region_code}/{city_slug(region_code, city)}/">Open the {e(city)} sheet</a>.'
                                               if city and (ROOT / "rebate-sheet" / region_code / city_slug(region_code, city) / "index.html").exists()
                                               else '<a href="/rebate-sheet/">Find your city\'s sheet</a>.') + '</li>',
             '<li><b>A top-rated badge</b> for companies ranked in a city. <a href="/installers/badge/">Get your badge</a>.</li>']
    return f'<ul>{"".join(items)}</ul>'


def who(c, kind):
    """What this company is, from where we found it: NRCan or RESNET's list, or the company itself."""
    return kind["who"] if c["sources"][0].startswith(("NRCan", "RESNET")) else "team of registered energy advisors"


def profile(c, kind, ranks, rows_by_city, path):
    """One page per company, rendered by advisor_profile_page.render (the advisor template, body class tpl-advisor)."""
    name, g = c["name"], c["google"]
    w = who(c, kind)
    regions_txt = ", ".join(PROV_NAMES.get(x, STATE_NAMES.get(x, x)) for x in c["regions"])
    ctx = {"PROV_NAMES": PROV_NAMES, "STATE_NAMES": STATE_NAMES, "HUBS": HUBS, "SITES": SITES, "OWNER": OWNER,
           "who": who, "services": services, "pro_tools": pro_tools}
    body = advisor_profile_page.render(c, kind, ranks, path, ctx)
    title = f"{name}: {kind['Title'][:-1]} | HomePowerRebate" if len(name) < 40 else f"{name} | HomePowerRebate"
    desc = (f"{name}, a {w} in {regions_txt}." + (f" {g['rating']:.1f} stars from {g['reviews']:,} Google reviews." if g and g.get('rating') else "")
            + " Phone, website, cities served and services.")
    crumbs = [("Home", "/"), (kind["Title"], kind["root"]), (name, path)]
    ld = page_kit.ld_scripts([page_kit.breadcrumb_ld(crumbs)])
    cities = sorted({(r, ci) for r, ci in c["cities"]}, key=lambda x: x[1])
    reg0 = next((r for r, _ in cities), None) or ("bc" if c["country"] == "ca" else "ma")
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
{page_kit.GA}
<meta name="description" content="{e(desc)}"><meta name="robots" content="noindex, follow"><link rel="canonical" href="{BASE}{path}">
{page_kit.FONTS}
{ld}</head>
<body class="tpl-advisor">
{navfooter.render_nav(reg0, "")}
{page_kit.breadcrumb([(n, p) for n, p in crumbs[:-1]] + [(e(name), path)])}
{body}
{navfooter.render_footer(reg0, "", "", path)}
</body></html>
"""
    return navfooter.ensure_shared_assets(page)


def directory(country, companies, ranks, rows_by_city, slugs):
    kind = KIND[country]
    path = kind["root"]
    groups = defaultdict(list)
    for c in companies:
        for r in c["regions"] or ["Other"]:
            groups[r].append(c)
    order = sorted(groups, key=lambda r: (PROV_NAMES.get(r) or STATE_NAMES.get(r) or r))
    rank_links = defaultdict(list)
    for (ctry, reg, city), rows in rows_by_city.items():
        if ctry == country and sum(1 for r in rows if r["Google Rating"]) >= MIN_RANKED:
            rank_links[reg].append((city, f"/installers/{reg}/{city_slug(reg, city)}/{kind['service']}/"))
    sections = []
    for r in order:
        rows = []
        for c in sorted(groups[r], key=lambda c: (-(score(c["google"]["rating"], c["google"]["reviews"]) if c["google"] and c["google"].get("rating") else 0), c["name"].lower())):
            g = c["google"]
            rt = f'{g["rating"]:.1f}★ ({g["reviews"]:,})' if g and g.get("rating") else "No Google rating"
            ph = c["phones"].get(r, "")
            n_cities = sum(1 for reg, _ in c["cities"] if reg == r.lower() or (country == "ca" and regions.BY_CODE.get(reg, {}).get("abbr") == r))
            rows.append(f'<tr><td><a href="{slugs[(country, c["name"].lower())]}">{e(c["name"])}</a></td><td>{e(rt)}</td>'
                        f'<td>{f"<a href=\"tel:{tel(ph)}\">{e(ph)}</a>" if ph else ""}</td><td>{n_cities or ""}</td></tr>')
        code = next((x["code"] for x in regions.REGIONS if x["abbr"] == r), None)
        rl = rank_links.get(code, [])
        rl_html = ("<p>Ranked by Google reviews: " + ", ".join(f'<a href="{u}">{e(ci)}</a>' for ci, u in sorted(rl)) + ".</p>") if rl else ""
        label = PROV_NAMES.get(r) or STATE_NAMES.get(r) or r
        note = ""
        if country == "ca" and r == "NS":
            note = ('<p>In Nova Scotia, book the Home Energy Assessment through Efficiency Nova Scotia; NRCan lists only one '
                    'organization here, for Prince Edward Island postal codes.</p>')
        sections.append(f'<h2 id="{slugify(label)}">{e(label)} <span class="small">({len(groups[r])})</span></h2>{note}{rl_html}'
                        f'<div style="overflow-x:auto"><table class="rebate-table"><thead><tr><th>Company</th><th>Google rating</th><th>Phone</th>'
                        f'<th>Our cities served</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
    n = len(companies)
    rated = sum(1 for c in companies if c["google"] and c["google"].get("rating"))
    nr = sum(1 for c in companies if c["sources"][0].startswith(("NRCan", "RESNET")))
    extra_txt = (f", plus {n - nr} advisor {'team' if n - nr == 1 else 'teams'} that told us they are registered" if n > nr else "")
    if country == "ca":
        intro = (f"<p>Many rebate programs in Canada pay only after an EnerGuide home evaluation by a registered energy advisor, "
                 f"one visit before any work and one after. Every registered advisor books through a service organization licensed by "
                 f"Natural Resources Canada. This page lists all {nr} of them, by province{extra_txt}, with the {rated} we could match to a "
                 f"rated Google Maps listing ranked first.</p>"
                 f"<p>NRCan says the two evaluations together average <b>$600 to $1,000</b>, depending on the provider and province, and "
                 f"are usually paid after the work. Service organizations never sell door to door or by unsolicited calls or emails.</p>"
                 f'<p>Not sure when to call one? Read <a href="{GUIDE}">when to call an energy advisor</a>: what an evaluation and a heat load calculation are, and which rebates ask for them first.</p>'
                 f'<p>Guides by province: <a href="/blog/bc-heat-pump-rebate-energy-advisor-heat-load-calculation/">British Columbia</a>, '
                 f'<a href="/blog/ontario-home-renovation-savings-energy-audit-first/">Ontario</a>, '
                 f'<a href="/blog/nova-scotia-home-energy-assessment-rebates-explained/">Nova Scotia</a>, '
                 f'<a href="/blog/newfoundland-air-sealing-blower-door-test-takecharge/">Newfoundland and Labrador</a>, and '
                 f'<a href="/blog/how-to-find-a-registered-energy-advisor-canada/">how to find an advisor anywhere in Canada</a>.</p>')
        h1, desc = ("Registered Energy Advisors in Canada",
                    f"All {n} NRCan-licensed EnerGuide service organizations by province, with phone numbers, Google ratings and the cities each one serves.")
    else:
        intro = (f"<p>A home energy audit shows where your home loses energy and which upgrades to do first. Many utility insulation and "
                 f"heat pump programs ask for one. This page lists all {n} HERS rating companies on RESNET's 2026 list in the states we "
                 f"cover, by state, with the {rated} we could match to a rated Google Maps listing ranked first.</p>"
                 f"<p>RESNET's list covers companies that completed HERS Ratings in 2025. Most also do energy code testing and new home "
                 f"certifications; ask whether they audit existing homes and whether your utility accepts their report.</p>"
                 f'<p>Before you pay for an audit, read <a href="/blog/free-utility-home-energy-assessment-before-private-auditor/">which utilities offer their own assessment</a>.</p>')
        h1, desc = ("Home Energy Auditors in the US",
                    f"All {n} RESNET HERS rating companies in the states we cover, with Google ratings, contacts and the cities each one serves.")
    tools = (f'<div class="callout"><p><strong>Are you a {kind["pro"]}?</strong> These are yours to use with clients:</p>{pro_tools(country)}</div>')
    article = (intro + tools + "".join(sections)
               + f'<p class="small">Sources: <a href="{kind["src"]}" rel="noopener" target="_blank">{e(kind["src_name"])}</a>, read '
                 f'@@CHECKED@@. Ratings and review counts from Google Maps. A company with no rating is still listed. '
                 f'Is your company missing or wrong? Email hello@homepowerrebate.com.</p>')
    crumbs = [("Home", "/"), (kind["Title"], path)]
    lds = page_kit.ld_scripts([page_kit.breadcrumb_ld(crumbs)])
    reg0 = "bc" if country == "ca" else "ma"
    hero = (f'<section class="hero"><div class="wrap"><div class="amount-badge">{n} companies</div><h1>{e(h1)}</h1>'
            f'<p>{"Every NRCan-licensed company" if country == "ca" else "Every company on RESNET\'s 2026 list in the states we cover"}, '
            f'with phone numbers and Google ratings. Updated @@CHECKED-MONTH@@.</p></div></section>')
    # the "read"/"Updated" date moves only when the directory's content does
    out = ROOT / path.strip("/") / "index.html"
    m = re.search(r"read ([A-Z][a-z]+ \d{1,2}, \d{4})", out.read_text(encoding="utf-8")) if out.exists() else None
    shown = datetime.strptime(m.group(1), "%B %d, %Y").date().isoformat() if m else TODAY.isoformat()
    d = date.fromisoformat(page_kit.stable_date(path, hero + article, fallback=shown))
    fill = lambda t: t.replace("@@CHECKED@@", d.strftime("%B %-d, %Y")).replace("@@CHECKED-MONTH@@", d.strftime("%B %Y"))
    page_kit.write_page(path, h1, desc, lds, navfooter.render_nav(reg0, ""), page_kit.breadcrumb(crumbs), fill(hero), None, fill(article),
                        navfooter.render_footer(reg0, "", "", path))


def main():
    rows_by_city = city_rows()
    ranks = rankings(rows_by_city)
    comps = DIR["companies"]
    slugs, used = {}, set()
    for c in comps:
        s = slugify(c["name"]) or "company"
        if s in used:
            s = f"{s}-{c['regions'][0].lower()}" if c["regions"] else s + "-2"
        used.add(s)
        slugs[(c["country"], c["name"].lower())] = KIND[c["country"]]["root"] + s + "/"
    n = 0
    for c in comps:
        path = slugs[(c["country"], c["name"].lower())]
        out = ROOT / path.strip("/") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        html_out = profile(c, KIND[c["country"]], ranks, rows_by_city, path)
        # "checked" moves only when the page's content does, so a rebuild on another day changes nothing
        m = re.search(r"checked ([A-Z][a-z]+ \d+, \d{4})", out.read_text(encoding="utf-8")) if out.exists() else None
        shown = datetime.strptime(m.group(1), "%B %d, %Y").date().isoformat() if m else TODAY.isoformat()
        iso = page_kit.stable_date(path, html_out, fallback=shown)
        out.write_text(html_out.replace("@@CHECKED@@", date.fromisoformat(iso).strftime("%B %-d, %Y")), encoding="utf-8")
        n += 1
    for country in ("ca", "us"):
        directory(country, [c for c in comps if c["country"] == country], ranks, rows_by_city, slugs)
    page_kit.save_dates()
    MAP_OUT.write_text(json.dumps({f"{k[0]}|{k[1]}": v for k, v in sorted(slugs.items())}, indent=1, ensure_ascii=False) + "\n")
    print(f"{n} profiles, 2 directory pages, {MAP_OUT.name} written.")


if __name__ == "__main__":
    main()
