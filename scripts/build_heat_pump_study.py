#!/usr/bin/env python3
"""/installers/heat-pump/city-ratings/: a data page built to be linked to (2026-11-04). Which cities have the best-reviewed heat pump
installers, from the same Google Maps ratings and review counts the ranking pages show (installers/*-installers-real.csv).
Everything is computed here; no sentence states a number that is not in the data. Cities with fewer than MIN_COMPANIES companies are left
out of the rankings (small samples). Rerun after build_installer_rankings.py, then post_steps.py.
Usage: python3 scripts/build_heat_pump_study.py"""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_heat_pump_hub as hub  # noqa: E402
import page_kit as kit  # noqa: E402
import regions as regions_mod  # noqa: E402

e = html.escape
PATH = "/installers/heat-pump/city-ratings/"
MIN_COMPANIES = 8


def main():
    cities = hub.city_rows()
    names = {r["code"]: r for r in regions_mod.REGIONS}
    big = [c for c in cities if c["n"] >= MIN_COMPANIES]
    n_c, n_i, n_r = len(cities), sum(c["n"] for c in cities), sum(c["reviews"] for c in cities)
    overall = sum(c["avg"] * c["reviews"] for c in cities) / n_r
    country = {}
    for c in cities:
        k = names[c["region"]]["country"]
        d = country.setdefault(k, [0, 0, 0.0, 0])
        d[0] += c["n"]; d[1] += c["reviews"]; d[2] += c["avg"] * c["reviews"]; d[3] += 1
    label = lambda c: f'{c["city"]}, {names[c["region"]]["abbr"]}'
    by_avg = sorted(big, key=lambda c: (-round(c["avg"], 2), -c["reviews"]))[:15]
    by_per = sorted(big, key=lambda c: -c["reviews"] / c["n"])[:10]
    by_n = sorted(cities, key=lambda c: -c["n"])[:10]

    def tbl(rows, cols):
        head = "".join(f"<th>{h}</th>" for h, _ in cols)
        body = "".join("<tr>" + "".join(f"<td>{f(c)}</td>" for _, f in cols) + "</tr>" for c in rows)
        return f'<div class="table-wrap"><table class="hub-table"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'

    link = lambda c: f'<a href="{c["url"]}">{e(label(c))}</a>'
    t1 = tbl(by_avg, [("City", link), ("Average rating", lambda c: f'{c["avg"]:.2f}★'), ("Companies", lambda c: str(c["n"])), ("Google reviews", lambda c: f'{c["reviews"]:,}')])
    t2 = tbl(by_per, [("City", link), ("Reviews per company", lambda c: f'{c["reviews"] / c["n"]:,.0f}'), ("Companies", lambda c: str(c["n"]))])
    t3 = tbl(by_n, [("City", link), ("Companies ranked", lambda c: str(c["n"])), ("Google reviews", lambda c: f'{c["reviews"]:,}')])
    ca, us = country.get("ca"), country.get("us")
    cmp_p = ""
    if ca and us:
        cmp_p = (f"<p>Canadian cities in our data ({ca[3]} cities, {ca[0]:,} companies) average {ca[2] / ca[1]:.2f} stars with {ca[1] / ca[0]:,.0f} Google reviews per company. "
                 f"US cities ({us[3]} cities, {us[0]:,} companies) average {us[2] / us[1]:.2f} stars with {us[1] / us[0]:,.0f} reviews per company.</p>")
    best = by_avg[0]
    body = (f'<div class="callout"><p><strong>Short answer:</strong> across {n_c} cities and {n_i:,} heat pump installers, the average rating is {overall:.2f} stars '
            f'(weighted by review count). Among cities with at least {MIN_COMPANIES} companies, {e(label(best))} has the highest average, {best["avg"]:.2f} stars across {best["reviews"]:,} reviews.</p></div>'
            f'<h2>Cities with the highest average rating</h2><p>Only cities with at least {MIN_COMPANIES} ranked companies are included, so one or two businesses cannot decide a city\'s place. '
            f'The average is weighted by review count.</p>{t1}'
            f'<h2>Cities where installers have the most reviews</h2><p>More reviews per company means homeowners have more to read before they call.</p>{t2}'
            f'<h2>Cities with the longest installer lists</h2>{t3}<h2>Canada and the United States</h2>{cmp_p}'
            f'<h2>How we made this</h2><p>We collected the Google Maps rating and review count for heat pump installers in each city, then ranked them with a score that weights the rating by the number of reviews. '
            f'This page uses the same numbers as each city\'s ranking. Ratings come from Google reviewers: they tell you what customers said, not how well a system was designed, and a company with few reviews may still be excellent. '
            f'We found the companies through Google Maps searches for each city, so a business without a Google listing is not here, and the averages describe the companies Google surfaced, not every installer in a city. Nobody pays to be listed or to rank higher. '
            f'See <a href="/installers/how-we-rank/">how we rank</a>. Ratings and review counts are from Google Maps.</p>'
            f'<p>Find your city: <a href="/installers/heat-pump/">heat pump installers in all {n_c} cities</a>.</p>')
    faqs = [("Which city has the best-reviewed heat pump installers?",
             f"Among cities with at least {MIN_COMPANIES} companies in our data, {label(best)} has the highest review-weighted average rating: {best['avg']:.2f} stars across {best['reviews']:,} Google reviews."),
            ("Does a high average rating mean every installer there is good?",
             "No. The average describes the group, not each company. Read each company's reviews, check that it is registered for the rebate you want, and compare at least two quotes."),
            ("Where do these ratings come from?",
             "From Google Maps: each company's rating and review count, collected in September 2026 and refreshed on our schedule. We do not change them.")]
    hub.page(PATH, f"Heat Pump Installer Ratings by City ({n_c} Cities)",
             f"Which cities have the best-reviewed heat pump installers? We compared Google ratings for {n_i:,} companies in {n_c} cities across Canada and the US.",
             "Heat Pump Installer Ratings by City", f"{n_c} cities",
             f"{n_i:,} companies, {n_r:,} Google reviews, {n_c} cities. Which cities have the best-reviewed installers?",
             [("Installers", "/installers/"), ("Heat pump installers", hub.NAT), ("Ratings by city", None)], body, faqs)
    print("study page written")


if __name__ == "__main__":
    main()
