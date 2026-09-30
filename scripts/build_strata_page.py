#!/usr/bin/env python3
"""BC strata and condo rebate guide: /strata-condo-rebates/bc/.

Every amount comes from data/verified-facts/bc-strata.json (read from BC Hydro and betterhomesbc.ca on 2026-09-29).
Nothing about noise limits, outdoor-unit rules or templates is stated, because we have not verified those.
Re-run after the monthly check. Region pattern: /strata-condo-rebates/<region>/ so other regions can follow.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell, AUTHOR, BASE  # noqa: E402
from build_hub_tops import status_pill  # noqa: E402

e = html.escape
D = json.loads((ROOT / "data" / "verified-facts" / "bc-strata.json").read_text())
FX = D["facts"]
VERIFIED = date.fromisoformat(D["checked"]).strftime("%B %-d, %Y")
PATH = "/strata-condo-rebates/bc/"
CB = "https://betterhomesbc.ca/learn-about-programs/energy-savings-program/energy-savings-program-condo-and-apartment-rebate-requirements/"

TITLE = "BC Strata and Condo Heat Pump Rebates 2026: Owners and Strata Councils"
DESC = "What BC condo owners and strata councils can claim in 2026: BC Hydro up to $2,250 per suite plus a bonus, CleanBC up to $5,000, and building-wide retrofit rebates. Rules and deadlines."
SHORT = ("A BC condo owner can get up to $2,250 from BC Hydro for a heat pump that replaces electric heat, plus up to $1,000 more if the work is done by "
         "October 31, 2026. Income-qualified owners can get up to $5,000 from CleanBC instead. Both programs need your strata's approval first. "
         "A strata council can also claim building-wide rebates for heat pumps, windows and lighting.")

FAQ = [
    ("Do I need my strata's approval for a heat pump rebate?", "Yes. BC Hydro requires strata or co-op board approval before you request the pre-approval code. CleanBC requires the strata corporation to complete a consent form, which you submit when you register."),
    ("Can I get both the BC Hydro and CleanBC condo rebates?", "BC Hydro's page says households that qualify for the CleanBC condo and apartment rebates are not eligible for its condo rebate. Check your income level first, then pick the program that pays more."),
    ("How much can a condo owner get for a heat pump in BC?", "BC Hydro pays $1,000 for a mini-split or $750 per head for a multi-split, up to three heads, so up to $2,250. CleanBC pays up to $5,000 at Income Level 1 and $4,000 at Level 2."),
    ("What is the deadline for the BC Hydro heat pump bonus?", "Work must be finished by October 31, 2026, and the application submitted by November 30, 2026. The bonus is up to $1,000."),
    ("Can a strata council get rebates for the whole building?", "Yes. BC Hydro's Multi-Unit Residential Building Retrofit Program pays for heat pumps, in-suite heat pump water heaters and windows in buildings three storeys or higher, and adds a 30% bonus on electrical projects submitted by February 12, 2027."),
]


def pill_row(f):
    return (f"<tr><td><b>{e(f['program'])}</b></td><td>{e(f['claim'])}{status_pill(f['status'])}</td>"
            f"<td>{e(f['eligibility'])} <span class='small'>{e(f['dates'])}.</span> <a href='{e(f['source_url'])}' rel='nofollow noopener' target='_blank'>Source</a></td></tr>")


def page():
    owner = [f for f in FX if "Condo and Apartment" in f["program"]]
    strata = [f for f in FX if "Multi-Unit" in f["program"]]
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/ca/bc/">BC</a></li><li aria-current="page">Strata and condo rebates</li></ol></nav>
<header class="hero"><div class="wrap"><h1>BC Strata and Condo Heat Pump Rebates 2026</h1>
<p>What owners and strata councils can claim, who must approve it, and the deadlines. Every amount links to the program's own page. Last verified {VERIFIED}.</p><p class="meta">By {e(AUTHOR['name'])}</p></div></header>
<section class="body"><div class="wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> {e(SHORT)}</p></div>
<h2>Which program is yours?</h2>
<ul><li><b>You own one suite and your household income is under the CleanBC limits:</b> use the CleanBC condo and apartment rebate, up to $5,000 (Level 1) or $4,000 (Level 2). The suite must be at or under $754,000 assessed value. Income limits for a household of four are $94,900 (Level 1) and $118,600 (Level 2).</li>
<li><b>You own one suite and your income is higher:</b> use the BC Hydro condo and apartment rebate, up to $2,250 for a heat pump and $1,000 for a heat pump water heater.</li>
<li><b>You sit on the strata council and want to upgrade the building:</b> use BC Hydro's Multi-Unit Residential Building Retrofit Program.</li></ul>
<h2>Rebates for individual suites</h2>
<div class="tw"><table><tr><th>Program</th><th>Amount</th><th>Rules</th></tr>{"".join(pill_row(f) for f in owner)}</table></div>
<h2>Rebates for the whole building</h2>
<div class="tw"><table><tr><th>Program</th><th>Amount</th><th>Rules</th></tr>{"".join(pill_row(f) for f in strata)}</table></div>
<p class="small">Amounts last verified {VERIFIED} against BC Hydro and Better Homes BC. Rebate amounts are maximums.</p>
<h2>How to get your strata to say yes</h2>
<ol><li><b>Check your suite first.</b> BC Hydro needs the suite to be primarily heated by electricity, such as baseboards, and the building to be an apartment building, stacked townhome or multiplex of six or more units. CleanBC also needs primarily electric heat.</li>
<li><b>Ask for approval in writing before you buy anything.</b> BC Hydro wants board approval before you request a pre-approval code. For CleanBC, the strata corporation fills in the <a href="{CB}" rel="nofollow noopener" target="_blank">consent form</a> and you submit it when you register.</li>
<li><b>Hire an installer who qualifies.</b> BC Hydro requires a Home Performance Contractor Network (HPCN) member for heat pumps. See <a href="/installers/">top-rated installers by city</a>, ranked by Google reviews.</li>
<li><b>Watch the clocks.</b> A BC Hydro pre-approval code is valid for six months. The limited-time bonus needs work finished by October 31, 2026.</li>
<li><b>Check your strata's own rules.</b> Bylaws differ from building to building. We have not verified any noise limit or outdoor-unit rule, so ask your council and your installer where the outdoor unit can go.</li></ol>
<h2>Common questions</h2>
{"".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in FAQ)}
<p><b>Related:</b> <a href="/ca/bc/">BC rebate guide</a> · <a href="/calculator/bc/">BC rebate calculator (single-family homes)</a> · <a href="/programs/bc-hydro-rebates/">BC Hydro rebates</a> · <a href="/programs/cleanbc-rebates/">CleanBC rebates</a> · <a href="/rebate-tracker/">Recent rebate changes</a></p>
<p class="small">Something out of date? Email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a> and we'll check it within a week.</p>
</div></section>"""
    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": TITLE, "description": SHORT, "datePublished": "2026-09-30", "dateModified": D["checked"],
         "author": AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE}, "mainEntityOfPage": BASE + PATH},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "BC", "item": BASE + "/ca/bc/"},
            {"@type": "ListItem", "position": 3, "name": "Strata and condo rebates"}]},
    ]
    out = shell(TITLE + " | HomePowerRebate", DESC, PATH, "bc", body, ld)
    return out.replace("</style>", ".tw{overflow-x:auto;-webkit-overflow-scrolling:touch}.tw table{min-width:520px}</style>", 1)


def link_hub():
    f = ROOT / "ca" / "bc" / "index.html"
    s = f.read_text(encoding="utf-8")
    S, E = "<!-- STRATA-LINK-START -->", "<!-- STRATA-LINK-END -->"
    blk = (f'{S}<p style="max-width:880px;margin:12px auto;padding:0 20px;"><b>Live in a condo or strata?</b> '
           f'<a href="{PATH}">See the BC strata and condo rebates</a> for owners and councils.</p>{E}')
    if S in s:
        s = re.sub(re.escape(S) + ".*?" + re.escape(E), lambda m: blk, s, count=1, flags=re.S)
    else:
        anchor = next(a for a in ("<!-- PROGRAM-LINKS-END -->", "<!-- HUB-CHANGES-END -->") if a in s)
        s = s.replace(anchor, anchor + "\n" + blk, 1)
    f.write_text(s, encoding="utf-8")


if __name__ == "__main__":
    (ROOT / PATH.strip("/")).mkdir(parents=True, exist_ok=True)
    (ROOT / PATH.strip("/") / "index.html").write_text(page(), encoding="utf-8")
    link_hub()
    print("Wrote", PATH)
