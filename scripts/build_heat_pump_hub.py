#!/usr/bin/env python3
"""City-based heat pump installer hubs (2026-11-03): /installers/heat-pump/ and /installers/heat-pump/<region>/.

Why: Search Console showed "heat pump installers near me" landing on random city pages. There was no page for the head
term. These hubs list every city we rank (one row per city: how many companies, the top-rated one, the open heat pump
rebate), grouped by country and region, and link straight to each city's ranking. No postal code box: the choice is the city.

Every number comes from the same data as the ranking pages (installers/*-installers-real.csv through
build_installer_rankings.load_rows, powerscore-data.json for the open rebate), so a hub cannot disagree with a city page.
Regions with fewer than MIN_CITIES cities are covered on the national hub only (they would be thin pages).
Run after build_installer_rankings.py, then post_steps.py. git add -f is not needed (output is HTML)."""
import html
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_installer_rankings as br  # noqa: E402
import page_kit as kit  # noqa: E402
import regions as regions_mod  # noqa: E402

e = html.escape
SERVICE = "heat-pump"
MIN_CITIES = 4
NAT = "/installers/heat-pump/"
OUTSIDE = [("https://www.energy.gov/energysaver/heat-pump-systems", "U.S. Department of Energy: heat pump systems"),
           ("https://www.energystar.gov/products/heat_pumps_air_source", "ENERGY STAR: air-source heat pumps")]


def city_rows():
    """One dict per indexed heat pump ranking page, in region order."""
    hubs = br.city_hubs()
    rk = {m["url"]: m for m in json.loads((ROOT / "installers" / "rankings.json").read_text(encoding="utf-8"))
          if m["service"] == SERVICE and m.get("indexed", True)}
    groups = defaultdict(list)
    for r in br.load_rows():
        if r["service"] == SERVICE:
            groups[(r["region"], r["city"])].append(r)
    out = []
    for (region, city), inst in groups.items():
        hub = br.find_hub(hubs, region, city)
        url = f"/installers/{region}/{hub['slug'] if hub else br.slugify(city)}/{SERVICE}/"
        if url not in rk:
            continue
        ranked = sorted(inst, key=br.score, reverse=True)
        top = ranked[0]
        ps = br.PS_CITIES.get(hub["url"]) if hub else None
        d = ((ps or {}).get("categories") or {}).get("heat-pump") or {}
        rebate = d.get("dollar_value") if d.get("status") == "open" and d.get("dollar_value") else None
        out.append({"region": region, "city": hub["label"] if hub else city, "url": url, "n": len(ranked),
                    "reviews": sum(r["reviews"] for r in ranked), "top": br.display_name(top["name"]), "rating": top["rating"],
                    "top_reviews": top["reviews"], "avg": sum(r["rating"] * r["reviews"] for r in ranked) / max(sum(r["reviews"] for r in ranked), 1), "rebate": rebate, "hub_url": hub["url"] if hub else "",
                    "registered": rk[url].get("rebate_registered", 0)})
    return sorted(out, key=lambda c: (c["region"], c["city"]))


def table(cities):
    rows = "".join(
        f'<tr><td><a href="{c["url"]}"><b>Heat pump installers in {e(c["city"])}</b></a></td><td>{c["n"]}</td>'
        f'<td>{e(c["top"])} <span class="muted">({c["rating"]:.1f}★, {c["top_reviews"]:,} reviews)</span></td>'
        f'<td>{"up to $" + format(round(c["rebate"]), ",") if c["rebate"] else "check the city page"}</td></tr>' for c in cities)
    return ('<div class="table-wrap"><table class="hub-table"><thead><tr><th>City</th><th>Companies ranked</th><th>Top-rated company</th>'
            f'<th>Open heat pump rebate</th></tr></thead><tbody>{rows}</tbody></table></div>')


def faq(scope, n_cities, n_companies, n_reviews, region_name=None):
    where = region_name or "Canada and the United States"
    return [
        (f"How do you pick the top-rated heat pump installers in {where}?",
         f"We rank companies by their Google rating, weighted by how many reviews they have, so a company with hundreds of good reviews ranks above one with a handful. "
         f"The {n_companies:,} companies on {scope} have {n_reviews:,} Google reviews between them. Nobody pays to be listed or to rank higher."),
        ("Is heat pump installation free to compare?",
         "Yes. Comparing installers is free for homeowners, and the listed companies pay nothing to appear. Each city page also shows the heat pump rebates open in that city, so you can see what could come off the price before you call."),
        ("Why can't I search by my postal code or ZIP code?",
         "We rank installers city by city, because rebates, climate and rules change by city. Pick the closest city in the table. Each city page also lists nearby cities with their own rankings."),
        ("What should I check before I hire a heat pump installer?",
         "Ask for the exact model and its cold-climate rating, a written heat-loss calculation, whether the company is registered for the rebate you want, and a quote you can compare line by line. Each city page has a checklist and a cost range."),
    ]


def page(path, title, desc, h1, badge, lead, crumbs, body_html, faqs, extra_ld=()):
    trail = [("Home", "/")] + [(n, u or path) for n, u in crumbs]
    ld = [kit.breadcrumb_ld(trail),
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
              {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]},
          *extra_ld]
    faq_html = "<h2>Questions about heat pump installers</h2>" + "".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in faqs)
    refs = "<h2>Further reading</h2><ul>" + "".join(
        f'<li><a href="{u}" rel="noopener" target="_blank">{e(t)}</a></li>' for u, t in OUTSIDE) + \
        '<li><a href="/installers/how-we-rank/">How we rank installers</a></li>' \
        '<li><a href="/installers/heat-pump/city-ratings/">Which cities have the best-reviewed installers</a></li>' \
        '<li><a href="/programs/national-heat-pump-rebate/">Canada\'s national heat pump rebate (opens early 2027)</a></li></ul>'
    nav = navfooter.render_nav("ca", "")
    footer = navfooter.render_footer("ca", "", "", path)
    hero = (f'<section class="hero"><div class="wrap"><div class="amount-badge">{e(badge)}</div><h1>{e(h1)}</h1><p>{lead}</p></div></section>')
    kit.write_page(path, title, desc, kit.ld_scripts(ld), nav, kit.breadcrumb(trail), hero, None,
                   body_html + faq_html + refs, footer)


def main():
    cities = city_rows()
    by_region = defaultdict(list)
    for c in cities:
        by_region[c["region"]].append(c)
    n_c, n_i = len(cities), sum(c["n"] for c in cities)
    n_r = sum(c["reviews"] for c in cities)
    names = {r["code"]: r for r in regions_mod.REGIONS}

    def region_label(code):
        return names[code]["name"]

    # ---- national hub ----
    parts = [f'<div class="callout"><p><strong>Short answer:</strong> pick your city below. Each row opens a ranking of the top-rated heat pump installers there, '
             f'with typical cost, open rebates and what to ask before you hire. We cover {n_c} cities and {n_i:,} companies, ranked by {n_r:,} Google reviews.</p></div>']
    for country, label in (("ca", "Canada"), ("us", "United States")):
        codes = sorted((c for c in by_region if names[c]["country"] == country), key=region_label)
        if not codes:
            continue
        parts.append(f"<h2>Heat pump installers in {label}</h2>")
        for code in codes:
            cs = by_region[code]
            link = f' <a class="small" href="{NAT}{code}/">All {e(region_label(code))} cities</a>' if len(cs) >= MIN_CITIES else ""
            parts.append(f'<h3 id="{code}">{e(region_label(code))} ({len(cs)} cities){link}</h3>{table(cs)}')
    page(NAT, f"Heat Pump Installers Near You: Top-Rated in {n_c} Cities",
         f"Find top-rated heat pump installers in {n_c} cities across Canada and the US, ranked by {n_r:,} Google reviews. Compare costs and open rebates for your city.",
         "Heat Pump Installers Near You", f"{n_c} cities",
         f"Pick your city to compare the top-rated heat pump installers there. {n_i:,} companies, ranked by Google reviews. Not paid for.",
         [("Installers", "/installers/"), ("Heat pump installers", None)], "".join(parts),
         faq("this page", n_c, n_i, n_r))

    # ---- one hub per region with enough cities ----
    made = 1
    for code, cs in sorted(by_region.items()):
        if len(cs) < MIN_CITIES:
            continue
        name = region_label(code)
        n_ci, n_co, n_rv = len(cs), sum(c["n"] for c in cs), sum(c["reviews"] for c in cs)
        best = max(cs, key=lambda c: (c["top_reviews"], c["rating"]))
        biggest = max(cs, key=lambda c: c["n"])
        with_reb = [c for c in cs if c["rebate"]]
        top_reb = max(with_reb, key=lambda c: c["rebate"]) if with_reb else None
        reg = sum(c["registered"] for c in cs)
        short = (f'<p><strong>Short answer:</strong> we rank {n_co:,} heat pump installers in {n_ci} {e(name)} cities. '
                 f'{e(biggest["city"])} has the longest list ({biggest["n"]} companies). The company with the most Google reviews at the top of its city is '
                 f'{e(best["top"])} in {e(best["city"])} ({best["top_reviews"]:,} reviews, {best["rating"]:.1f}★).'
                 + (f' The biggest open heat pump rebate we list is up to ${round(top_reb["rebate"]):,} in {e(top_reb["city"])}.' if top_reb else "")
                 + "</p>")
        reg_note = (f'<p>{reg} of the ranked companies are on an official contractor list for a heat pump rebate program. '
                    'These are marked on each city page; most rebates require one.</p>') if reg else ""
        hub_url = f"/ca/{code}/" if names[code]["country"] == "ca" else f"/us/{code}/"
        body = (f'<div class="callout">{short}</div>{reg_note}<h2>{e(name)} cities, with the top-rated company in each</h2>{table(cs)}'
                f'<p>Want the rebates first? See <a href="{hub_url}">heat pump and other rebates in {e(name)}</a>, then come back to compare companies.</p>'
                f'<p><a href="{NAT}">Heat pump installers in all {n_c} cities</a></p>')
        page(f"{NAT}{code}/", f"Heat Pump Installers in {name}: Top-Rated by City"[:80],
             f"Top-rated heat pump installers in {n_ci} {name} cities, ranked by {n_rv:,} Google reviews. See the best company in each city plus open rebates.",
             f"Heat Pump Installers in {name}", f"{n_ci} cities",
             f"{n_co:,} companies in {n_ci} cities, ranked by Google reviews. Pick your city to compare.",
             [("Installers", "/installers/"), ("Heat pump installers", NAT), (name, None)], body,
             faq(f"these {name} pages", n_ci, n_co, n_rv, name))
        made += 1
    kit.save_dates() if hasattr(kit, "save_dates") else None
    print(f"{made} heat pump hub pages written ({n_c} cities, {n_i:,} companies).")


if __name__ == "__main__":
    main()
