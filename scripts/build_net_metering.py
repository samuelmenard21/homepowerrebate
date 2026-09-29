#!/usr/bin/env python3
"""/blog/net-metering-vs-net-billing/: what the two mean, where each applies, and what it does to solar savings.

Google Trends (Sep 2026, Canada): "net metering vs net billing", "net metering explained" (breakout), "bc hydro net metering
changes" (+150%). Only facts in data/verified-facts/*.json are used for regions; everything else is definition or labelled example.
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
PATH = "/blog/net-metering-vs-net-billing/"
CHECKED = "2026-09-29"
BC_SRC = "https://www.bchydro.com/toolbar/about/strategies-plans-regulatory/rate-design/self-generation-rate-updates.html"
CA_SRC = "https://www.cpuc.ca.gov/nbt"
ON_SRC = "https://www.homerenovationsavings.ca/without-assessment/solar"

FAQ = [
    ("What is the difference between net metering and net billing?",
     "With net metering, each kWh you send to the grid cancels out a kWh you use later, at the same price. With net billing, "
     "the power you send out is credited at a set export rate, and that rate is often lower than what you pay to buy power."),
    ("Is net metering still available in BC?",
     "Not for new customers. BC Hydro closed net metering to new customers on July 1, 2026. New solar owners are on the "
     "self-generation rate, which pays 10 cents per kWh for power sent to the grid. Existing net metering customers stay on it "
     "until 10 years from their net metering start date."),
    ("What is net billing in California?",
     "PG&E, SCE and SDG&E customers who applied for new solar after April 14, 2023 are on the Net Billing Tariff. Exports are "
     "credited at hourly values that are far below the retail price. SMUD and LADWP set their own rules."),
    ("Does net billing make solar a bad idea?",
     "Not always, but it changes how to size it. Under net billing, power you use yourself is worth more than power you export, "
     "so systems sized to your daytime use, or paired with a battery, tend to do better than oversized ones."),
]


def body():
    faq_html = "".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in FAQ)
    return f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/blog/">Blog</a></li><li aria-current="page">Net metering vs net billing</li></ol></nav>
<header class="hero"><div class="wrap"><h1>Net Metering vs Net Billing: What It Means for Your Solar Savings</h1>
<p>The difference in plain words, where each one applies in BC, California and Ontario, and how it changes the size of solar system to buy. Checked {CHECKED}.</p><p class="meta">By {e(AUTHOR['name'])}</p></div></header>
<section class="body"><div class="wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> with <b>net metering</b>, power you send to the grid is credited kWh for kWh at the same price you pay. With <b>net billing</b>, exports are credited at a set rate, usually lower than the price you pay. BC Hydro ended net metering for new customers on July 1, 2026 and now pays 10 cents per kWh for exports. California moved most new solar customers to net billing in April 2023.</p></div>

<h2>How each one works</h2>
<div class="tw"><table><tr><th></th><th>Net metering</th><th>Net billing</th></tr>
<tr><td><b>Credit for power you export</b></td><td>Same as the price you pay to buy power</td><td>A set export rate, often lower than the retail price</td></tr>
<tr><td><b>Is midday solar surplus worth much?</b></td><td>Yes, you get full value later</td><td>Less, so use it yourself when you can</td></tr>
<tr><td><b>Best system size</b></td><td>Can be sized to cover your whole year</td><td>Sized closer to what you use in daylight</td></tr>
<tr><td><b>Does a battery help?</b></td><td>Mostly for outages</td><td>Yes: it stores surplus so you use it instead of exporting it</td></tr></table></div>

<h2>What the difference is worth: try your numbers</h2>
<p>Enter what you expect to export in a year, what you pay per kWh to buy power, and the export credit. This is an illustration with numbers you supply, not a quote.</p>
<div style="background:#fff;border:1px solid #d9d0c1;border-radius:12px;padding:18px 20px;margin:10px 0 18px;">
<label for="nm-x"><b>Exported per year (kWh)</b></label><input id="nm-x" type="number" inputmode="numeric" value="3000" min="0" step="100" style="display:block;width:100%;max-width:220px;padding:10px;margin:6px 0 12px;font:inherit;font-size:16px;border:1px solid #d9d0c1;border-radius:8px;">
<label for="nm-r"><b>Price you pay to buy power (cents per kWh)</b></label><input id="nm-r" type="number" inputmode="decimal" value="15" min="0" step="0.5" style="display:block;width:100%;max-width:220px;padding:10px;margin:6px 0 12px;font:inherit;font-size:16px;border:1px solid #d9d0c1;border-radius:8px;">
<label for="nm-e"><b>Export credit (cents per kWh)</b></label><input id="nm-e" type="number" inputmode="decimal" value="10" min="0" step="0.5" style="display:block;width:100%;max-width:220px;padding:10px;margin:6px 0 12px;font:inherit;font-size:16px;border:1px solid #d9d0c1;border-radius:8px;">
<p style="margin:4px 0;">Value under net metering: <b id="nm-a">$450</b> a year</p>
<p style="margin:4px 0;">Value under net billing: <b id="nm-b">$300</b> a year</p>
<p style="margin:4px 0;font-size:18px;">Difference: <b id="nm-d" style="color:#8a2a1c;">$150</b> a year</p>
<p class="small" style="margin:8px 0 0;">The starting numbers are examples. Use your own bill for the price you pay; 10 cents is BC Hydro's export rate.</p></div>
<script>(function(){{const g=id=>document.getElementById(id),f=v=>'$'+Math.round(v).toLocaleString();
function u(){{const x=+g('nm-x').value||0,r=(+g('nm-r').value||0)/100,c=(+g('nm-e').value||0)/100;g('nm-a').textContent=f(x*r);g('nm-b').textContent=f(x*c);g('nm-d').textContent=f(x*r-x*c);}}
['nm-x','nm-r','nm-e'].forEach(i=>g(i).addEventListener('input',u));}})();</script>

<h2>Where it applies</h2>
<h3>British Columbia</h3>
<p>BC Hydro's net metering rate (RS 1289) closed to new customers on <b>July 1, 2026</b>. New solar owners are on the self-generation rate (RS 2289), which pays <b>10 cents per kWh</b> for power you export, credited each billing cycle. Existing net metering customers stay on it until 10 years from their net metering start date, then move to RS 2289. (<a href="{BC_SRC}" rel="nofollow noopener" target="_blank">BC Hydro source</a>.) Our <a href="/blog/bc-net-metering-ended-self-generation-rate-2026/">BC net metering guide</a> covers what to do if you're planning solar now, and the <a href="/programs/bc-hydro-rebates/">BC Hydro rebates</a> page lists the solar and battery rebates.</p>
<h3>California</h3>
<p>PG&amp;E, SCE and SDG&amp;E customers who applied for new solar after April 14, 2023 are on the <b>Net Billing Tariff</b>. Exports are credited at hourly avoided-cost values, far below the retail price. SMUD and LADWP are not regulated by the state commission and set their own rules (SMUD has a Solar and Storage Rate). (<a href="{CA_SRC}" rel="nofollow noopener" target="_blank">CPUC source</a>.) See <a href="/us/ca/">California rebates</a> and <a href="/blog/smud-rebate-breakdown/">SMUD's programs</a>.</p>
<h3>Ontario</h3>
<p>In Ontario the Home Renovation Savings solar rebate cannot be taken together with a net metering agreement with your local utility. Check with your utility before you sign a solar contract. (<a href="{ON_SRC}" rel="nofollow noopener" target="_blank">Program page</a>.) Our <a href="/blog/ontario-solar-rebate-vs-net-metering/">Ontario solar rebate vs net metering</a> guide walks through the choice.</p>
<h3>Anywhere else</h3>
<p>We haven't verified the export rules for every province and state yet. Ask your utility two questions before you buy: <em>what do you credit me for power I send to the grid?</em> and <em>does that rate change after some number of years?</em></p>

<h2>What this means for the size of system you buy</h2>
<ul>
<li><b>Size for your own use first.</b> When exports earn less than you pay, each kWh you use yourself is worth more than one you export.</li>
<li><b>Look at a battery.</b> It shifts midday surplus to the evening. BC Hydro and Ontario both have battery rebates; see the <a href="/programs/bc-hydro-rebates/">BC Hydro</a> and <a href="/programs/home-renovation-savings/">Ontario</a> pages.</li>
<li><b>Ask each installer to show the numbers both ways.</b> A quote that assumes full retail credit for every exported kWh may be too optimistic under net billing.</li>
<li><b>Compare installers by reviews.</b> See top-rated <a href="/installers/">solar installers in your city</a>.</li>
</ul>

<h2>Common questions</h2>
{faq_html}
<p class="small">Something out of date? Email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a> and we'll check it within a week.</p>
</div></section>"""


def main():
    title = "Net Metering vs Net Billing: What It Means for Solar (2026)"
    desc = ("Net metering credits exports at the retail price; net billing pays a set, usually lower rate. How each works, BC Hydro's "
            "10¢/kWh export rate since July 2026, California's Net Billing Tariff, and how to size solar.")
    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": title, "datePublished": CHECKED, "dateModified": CHECKED,
         "author": AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE}, "mainEntityOfPage": BASE + PATH},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Blog", "item": BASE + "/blog/"},
            {"@type": "ListItem", "position": 3, "name": "Net metering vs net billing"}]},
    ]
    out = shell(title + " | HomePowerRebate", desc, PATH, "bc", body(), ld)
    out = out.replace("</style>", ".tw{overflow-x:auto;-webkit-overflow-scrolling:touch}.tw table{min-width:520px}</style>", 1)
    f = ROOT / PATH.strip("/") / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(out, encoding="utf-8")
    print("Wrote", PATH)


if __name__ == "__main__":
    main()
