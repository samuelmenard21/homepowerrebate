#!/usr/bin/env python3
"""/insulation-rebates/: insulation rebates by province and state, with a BC attic calculator and links to every city page.

Search Console (Sep 2026): "insulation rebates" 119 impressions at position ~100, "attic insulation" + "home attic insulation" ~130 at
position ~85, with no page built for the national query. Every amount comes from data/verified-facts/*.json (checked against the
program's own page); Ontario amounts are copied as published there.
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell, AUTHOR  # noqa: E402

e = html.escape
BASE = "https://homepowerrebate.com"
PATH = "/insulation-rebates/"
CHECKED = "2026-09-29"
REGION = {"bc": "British Columbia", "on": "Ontario", "ab": "Alberta", "ns": "Nova Scotia", "ma": "Massachusetts", "ny": "New York",
          "ca": "California", "co": "Colorado", "pa": "Pennsylvania"}
HUB = {"bc": "/ca/bc/", "on": "/ca/on/", "ab": "/ca/ab/", "ns": "/ca/ns/", "ma": "/us/ma/", "ny": "/us/ny/", "ca": "/us/ca/", "co": "/us/co/", "pa": "/us/pa/"}

# (region, program, amount, rules, guide link or None, source)
ROWS = [
    ("BC", "BC Hydro insulation rebate", "Attic: $0.02 per sq ft for each R-value added, up to $900. Basement, crawlspace, wall cavity or wall sheathing: $0.09 per sq ft per R, up to $1,200 each. Other: $0.07, up to $1,000. Up to $5,500 in all.",
     "Electrically heated homes. HPCN contractor, so DIY doesn't count. Apply within 6 months of the invoice. At least R-12 added for an attic.",
     "/programs/bc-hydro-rebates/", "https://www.bchydro.com/powersmart/residential/rebates-programs/home-renovation/renovating-insulation.html"),
    ("BC", "FortisBC insulation rebate", "Same formula as BC Hydro: attic up to $900, walls and basement up to $1,200, other up to $1,000.",
     "FortisBC gas customers, and some FortisBC or municipal electric customers.", None,
     "https://www.fortisbc.com/rebates-and-energy-savings/rebates-and-offers"),
    ("BC", "ECAP (BC Hydro and FortisBC)", "Free home energy evaluation and free upgrades.", "Income-qualified customers.", "/programs/cleanbc-rebates/",
     "https://www.fortisbc.com/rebates/detail/free-home-energy-evaluation-and-upgrades"),
    ("Ontario", "Home Renovation Savings, no assessment", "Attic insulation up to $1,250.", "No assessment needed. Ontario raised it from $1,000.",
     "/programs/home-renovation-savings/", "https://homerenovationsavings.ca/"),
    ("Ontario", "Home Renovation Savings, with assessment", "Attic to R-50: $1,500, $1,200 or $900 depending on your starting R-value. Exterior wall $3,600, $2,100 or $1,200. Basement wall $1,500 or $900. Total insulation up to $7,700.",
     "Home energy assessment before and after the work.", "/programs/home-renovation-savings/", "https://homerenovationsavings.ca/with-assessment"),
    ("Nova Scotia", "Efficiency NS Home Energy Assessment rebates", "Attic to R-50 up to $750. Exterior walls up to $1,500. Basement walls up to $1,200. Crawlspace up to $960. Air sealing $200.",
     "Through a Home Energy Assessment. Pro-rated by the share of the area you insulate; row-house end units 75% and middle units 50% for walls.",
     "/programs/efficiency-nova-scotia/", "https://assets.ctfassets.net/hro74sf4x6k2/3WUCMiBurFYsS5L8O0Dg0K/e980fabca778e3ed2e7c2a0b4ff8e56a/Home-Energy-Assessment-Rebate-Guide-Aug-2026.pdf"),
    ("Nova Scotia", "HomeWarming", "Free insulation, draft-proofing and more, plus a free assessment.",
     "Lower-income homeowners; the primary residence. Expect a wait (about 4 to 6 weeks to hear back).", "/programs/efficiency-nova-scotia/",
     "https://www.efficiencyns.ca/programs-rebates/homewarming"),
    ("Alberta", "Calgary Home Upgrades Program", "Free upgrades including insulation and air sealing.", "Income-qualified Calgarians; there is a waitlist.", "/programs/alberta-energy-rebates/",
     "https://www.homeupgradesprogram.ca/calgary"),
    ("Massachusetts", "Mass Save weatherization", "75% to 100% off insulation, air sealing and weather stripping.", "100% generally for income-qualified homes or certain 1 to 4 unit buildings; 75% otherwise. Start with the free home energy assessment.",
     "/programs/mass-save/", "https://goclean.masscec.com/homeowners/weatherization/"),
    ("New York", "NYSERDA Comfort Home", "Seal-and-insulate packages: $2,500 (Good) or $3,000 (Better), plus $2,000 for windows.", "Through Comfort Home contractors in participating counties. Confirm your county is covered.",
     "/programs/nys-clean-heat/", "https://www.nyserda.ny.gov/All-Programs/Comfort-Home-Program"),
    ("California", "SMUD Seal and Insulate", "Up to $3,000 for air sealing, attic insulation and ducts.", "SMUD customers, through a Home Performance Program contractor.", None,
     "https://www.smud.org/Rebates-and-Savings-Tips/Improve-Home-Efficiency/Seal-and-Insulate"),
    ("California", "Pasadena Water and Power ceiling insulation", "$0.10 per sq ft, plus $0.05 with a qualified local contractor or Pasadena purchase.", "Must reach R-30 or more. Pasadena Water and Power customers.", None,
     "https://pwp.cityofpasadena.net/ceilinginsulationrebate/"),
]

FAQ = [
    ("How much is the insulation rebate?",
     "It depends where you live. In BC an attic rebate is $0.02 per sq ft for each R-value added, up to $900. In Ontario it is up to $1,250 "
     "without an assessment. In Nova Scotia an attic to R-50 gets up to $750. Massachusetts pays 75% to 100% of insulation and air sealing."),
    ("Do I need an energy assessment first?",
     "In Ontario the bigger rebates need a home energy assessment before and after the work. In Nova Scotia the rebates go through a Home "
     "Energy Assessment. In Massachusetts the free assessment is the first step. BC Hydro's rebate does not need one."),
    ("Can I install the insulation myself and still get a rebate?",
     "Usually not. BC Hydro requires a Home Performance Contractor Network member, so DIY work does not qualify. Check the rules before you buy materials."),
    ("Does the US federal tax credit still cover insulation?",
     "No. The 25C credit ended for anything installed after December 31, 2025. State and utility programs still pay, as listed on this page."),
]


def cities():
    out = {}
    for p in sorted((ROOT / "installers").glob("*/*/insulation/index.html")):
        reg, city = p.parts[-4], p.parts[-3]
        if reg not in REGION:
            continue
        label = re.sub(r"\s+", " ", city.replace("-", " ").title())
        rebate = ROOT / {"ca": "us/ca", "co": "us/co", "ma": "us/ma", "ny": "us/ny", "pa": "us/pa"}.get(reg, f"ca/{reg}") / city / "insulation" / "index.html"
        out.setdefault(reg, []).append((label, f"/installers/{reg}/{city}/insulation/", rebate.exists()))
    return out


def body():
    rows = "".join(f'<tr><td><b>{e(r)}</b></td><td>{e(p)}'
                   + (f'<br><a href="{g}">Guide</a> · ' if g else "<br>") + f'<a href="{e(s)}" rel="nofollow noopener" target="_blank">Official source</a></td>'
                   f'<td>{e(a)}</td><td>{e(ru)}</td></tr>' for r, p, a, ru, g, s in ROWS for r in [r])
    table = f'<div class="tw"><table><tr><th>Where</th><th>Program</th><th>What it pays</th><th>Rules</th></tr>{rows}</table></div>'
    cl = ""
    for reg, items in cities().items():
        links = " · ".join(f'<a href="{u}">{e(l)}</a>' for l, u, _ in items)
        cl += f'<p><b><a href="{HUB[reg]}">{e(REGION[reg])}</a>:</b> {links}</p>'
    faq_html = "".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in FAQ)
    return f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">Insulation rebates</li></ol></nav>
<header class="hero"><div class="wrap"><h1>Insulation Rebates by Province and State (2026)</h1>
<p>What each program pays for attic, wall and basement insulation, who qualifies, and the rules that catch people out. Amounts checked {CHECKED}.</p><p class="meta">By {e(AUTHOR['name'])}</p></div></header>
<section class="body"><div class="wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> insulation rebates run from <b>$750 for an attic in Nova Scotia</b> to <b>up to $7,700 in Ontario</b> and <b>75% to 100% of the cost in Massachusetts</b>. Most programs want a certified contractor or an energy assessment first, and the US federal insulation tax credit ended after December 31, 2025. Find your region below.</p></div>

<h2>Insulation rebates at a glance</h2>
{table}

<h2>BC attic rebate calculator</h2>
<p>BC Hydro pays $0.02 per square foot for each R-value point you add, up to $900, for electrically heated homes. Enter your attic size and the R-value you'll add:</p>
<div style="background:#fff;border:1px solid #d9d0c1;border-radius:12px;padding:18px 20px;margin:10px 0 18px;">
<label for="in-a"><b>Attic floor area (sq ft)</b></label><input id="in-a" type="number" inputmode="numeric" value="1000" min="0" step="50" style="display:block;width:100%;max-width:220px;padding:10px;margin:6px 0 12px;font:inherit;font-size:16px;border:1px solid #d9d0c1;border-radius:8px;">
<label for="in-r"><b>R-value you are adding</b></label><input id="in-r" type="number" inputmode="numeric" value="30" min="0" step="1" style="display:block;width:100%;max-width:220px;padding:10px;margin:6px 0 12px;font:inherit;font-size:16px;border:1px solid #d9d0c1;border-radius:8px;">
<p style="margin:4px 0;font-size:18px;">Estimated BC Hydro rebate: <b id="in-o" style="color:#2d6a4f;">$600</b> <span id="in-n" class="small"></span></p>
<p class="small" style="margin:8px 0 0;">Estimate only. The program needs at least R-12 added, a Home Performance Contractor Network member, and an electrically heated home.</p></div>
<script>(function(){{const a=document.getElementById('in-a'),r=document.getElementById('in-r'),o=document.getElementById('in-o'),n=document.getElementById('in-n');
function u(){{const A=+a.value||0,R=+r.value||0;if(R<12){{o.textContent='$0';n.textContent='(BC Hydro needs at least R-12 added)';return;}}
const v=A*R*0.02;o.textContent='$'+Math.round(Math.min(v,900)).toLocaleString();n.textContent=v>900?'(capped at $900)':'';}}
a.addEventListener('input',u);r.addEventListener('input',u);u();}})();</script>

<h2>Rules that catch people out</h2>
<ul>
<li><b>Assessment first.</b> Ontario's bigger rebates, Nova Scotia's rebates and Massachusetts weatherization all start with a home energy assessment. Book it before any work.</li>
<li><b>Certified contractor.</b> BC Hydro requires an HPCN member and does not pay for DIY. New York's Comfort Home works through its own contractors.</li>
<li><b>Deadlines.</b> BC Hydro wants your application within 6 months of the invoice.</li>
<li><b>Air seal first.</b> Insulation without air sealing loses much of its value. See the <a href="/blog/attic-insulation-guide/">attic insulation guide</a> for R-values, order of work and DIY safety checks.</li>
<li><b>Doing a heat pump too?</b> Insulate first: a tighter home needs a smaller heat pump. Read <a href="/blog/why-insulation-first-energy-retrofit/">why insulation comes first</a>.</li>
</ul>

<h2>Find your city: rebates and top-rated insulation installers</h2>
<p>Each link goes to the city's top-rated insulation installers, ranked by Google reviews, with that city's rebates.</p>
{cl}

<h2>Common questions</h2>
{faq_html}
<p class="small">Something out of date? Email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a> and we'll check it within a week.</p>
</div></section>"""


def main():
    title = "Insulation Rebates 2026: Amounts by Province and State"
    desc = ("Insulation rebates by region: BC Hydro attic $0.02 per sq ft (max $900), Ontario up to $7,700, Nova Scotia, Mass Save 75-100%, "
            "NY, California. Rules, calculator and top-rated installers by city.")
    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": title, "datePublished": CHECKED, "dateModified": CHECKED,
         "author": AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE}, "mainEntityOfPage": BASE + PATH},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Insulation rebates"}]},
    ]
    out = shell(title + " | HomePowerRebate", desc, PATH, "bc", body(), ld)
    out = out.replace("</style>", ".tw{overflow-x:auto;-webkit-overflow-scrolling:touch}.tw table{min-width:760px}</style>", 1)
    f = ROOT / PATH.strip("/") / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(out, encoding="utf-8")
    print("Wrote", PATH)


if __name__ == "__main__":
    main()
