#!/usr/bin/env python3
"""/heat-pump-rebate-alert/: a short page made for sharing (Facebook groups, Reddit, texts, installer emails), 2026-10-17.
One job: get people on the "email me the day Ottawa's heat pump rebate opens" list. The sign-up box itself is the shared
FED-ALERT component, placed at <!-- FED-ALERT-HERE --> by add_federal_alert.py (a post-step), with its share row open.
noindex, follow: the full guide (/programs/national-heat-pump-rebate/) is the page that should rank; this one would only
compete with it. Links shared from here carry ?src=, so the weekly report (federal_alert_report.py) shows what works.
Copy is Grade 6 and states only what data/verified-facts/federal.json says (federal-0 amounts and date, federal-3 stacking,
the $1,400 savings line in federal-0's eligibility). Never add retroactivity, an income line or a date before Ottawa does.
Usage: python3 scripts/build_alert_page.py, then python3 scripts/post_steps.py and python3 scripts/build_og_cards.py --only heat-pump-rebate-alert"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import page_kit as kit  # noqa: E402

PATH = "/heat-pump-rebate-alert/"
TITLE = "Up to $10,000 for a Heat Pump: Get an Email the Day It Opens"
DESC = "Ottawa's new heat pump rebate opens in early 2027: up to $10,000 below the median income, $2,000 for other homeowners. Get one email the day applications open."
OTTAWA = "https://www.canada.ca/en/environment-climate-change/campaigns/one-million-home-energy-retrofits.html"
RELEASE = "https://www.canada.ca/en/environment-climate-change/news/2026/10/prime-minister-carney-announces-landmark-investment-to-retrofit-one-million-homes-cutting-energy-costs-and-emissions.html"
PROVINCES = [("British Columbia", "/ca/bc/heat-pump/"), ("Ontario", "/ca/on/heat-pump/"), ("Alberta", "/ca/ab/heat-pump/"),
             ("Nova Scotia", "/ca/ns/heat-pump/"), ("Manitoba", "/ca/mb/heat-pump/"), ("Quebec", "/ca/qc/heat-pump/"),
             ("Newfoundland and Labrador", "/programs/newfoundland-oil-to-electric-rebate/")]

HERO = {"badge": "Opens early 2027", "h1": "Up to $10,000 for a heat pump. Be first in line.",
        "lead": "Ottawa is bringing in a new heat pump rebate in early 2027. Put in your email and we'll tell you the day it opens."}

ARTICLE = f"""<!-- FED-ALERT-HERE -->
<h2 id="what-is-it">What is this rebate?</h2>
<p>On October 8, 2026, the Government of Canada <a href="{RELEASE}" rel="noopener" target="_blank">announced</a> a $2 billion rebate for electric heat pumps. Households below the median income can get up to $10,000. Other eligible homeowners can get $2,000. Ottawa says you can add it on top of provincial rebates.</p>
<h2 id="why-now">Why sign up now?</h2>
<p>Applications are not open yet. Ottawa expects to open them in early 2027. When they open, we'll email you that day, so you can apply right away instead of finding out weeks later.</p>
<p>It can be worth a lot even after the rebate. Ottawa says homes that switch from oil, propane or electric baseboard heat save over $1,400 a year on average.</p>
<h2 id="what-you-get">What will you email me?</h2>
<ul><li>A quick hello now, so you know it worked.</li><li>One email the day applications open.</li><li>One email when Ottawa says who gets $10,000.</li></ul>
<p>That's it. No spam, and you can unsubscribe anytime. We don't sell your email.</p>
<h2 id="who-we-are">Who are we?</h2>
<p>HomePowerRebate is an independent site, not the Government of Canada. We track home energy rebates across Canada and link every amount to the official program. Ottawa also has <a href="{OTTAWA}" rel="noopener" target="_blank">its own sign-up</a>, and you can use both.</p>
<p><a href="/programs/national-heat-pump-rebate/do-i-qualify/"><b>Check what Ottawa has said about your home &rarr;</b></a></p>
<p><a href="/programs/national-heat-pump-rebate/"><b>Read everything we know so far about the federal rebate &rarr;</b></a></p>
<h2 id="while-you-wait">While you wait: what your province pays today</h2>
<ul>{"".join(f'<li><a href="{u}">{n}</a></li>' for n, u in PROVINCES)}</ul>"""


def main():
    trail = [("Home", "/"), ("Federal heat pump rebate alert", PATH)]
    lds = kit.ld_scripts([kit.breadcrumb_ld(trail)])
    kit.write_page(PATH, TITLE, DESC, lds, navfooter.render_nav("", ""), kit.breadcrumb(trail), kit.hero(HERO), None, ARTICLE,
                   navfooter.render_footer("", "", "", PATH))
    f = ROOT / PATH.strip("/") / "index.html"
    t = f.read_text(encoding="utf-8")
    t = t.replace('<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">',
                  '<meta name="robots" content="noindex, follow, max-image-preview:large">')
    t = t.replace('<meta property="og:type" content="article">', '<meta property="og:type" content="website">')
    f.write_text(t, encoding="utf-8")
    print("built", PATH)


if __name__ == "__main__":
    main()
