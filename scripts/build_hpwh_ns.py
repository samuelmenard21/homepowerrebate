#!/usr/bin/env python3
"""/heat-pump-water-heater/nova-scotia/: rebate, running-cost savings and fit for Nova Scotia homes.

Search Console (Sep 2026) shows ~180 impressions/2 weeks across "heat pump water heater nova scotia",
"...rebate cape breton", "...cost", "replace electric water heater with heat pump nova scotia", at
positions 21-40, with no page targeting them. Every number below has a source.
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell, AUTHOR  # noqa: E402

e = html.escape
BASE = "https://homepowerrebate.com"
PATH = "/heat-pump-water-heater/nova-scotia/"
CHECKED = "2026-09-29"

RATE = 0.19128          # NS Power standard residential energy rate, $/kWh, from May 1, 2026
RATE_SRC = "https://www.nspower.ca/your-home/residential-rates/standard-residential-service-rate"
REBATE = 800
REBATE_SRC = "https://www.efficiencyns.ca/programs-rebates/instant-rebates"
HEA_SRC = "https://assets.ctfassets.net/hro74sf4x6k2/3WUCMiBurFYsS5L8O0Dg0K/e980fabca778e3ed2e7c2a0b4ff8e56a/Home-Energy-Assessment-Rebate-Guide-Aug-2026.pdf"
NYSERDA_SRC = "https://www.nyserda.ny.gov/Featured-Stories/All-About-Heat-Pump-Water-Heaters"

FAQ = [
    ("Is there a heat pump water heater rebate in Nova Scotia?",
     f"Yes. Efficiency Nova Scotia gives ${REBATE} off an ENERGY STAR heat pump water heater, instantly at participating stores. "
     "If you didn't take it at the store, you can claim it through a Home Energy Assessment instead."),
    ("Does the rebate work in Cape Breton?",
     "Yes. It's a province-wide Efficiency Nova Scotia rebate, so Cape Breton homes get the same $800 as Halifax."),
    ("How much will I save replacing an electric water heater with a heat pump in Nova Scotia?",
     "At NS Power's rate of about 19.1 cents per kWh, a home whose electric tank uses 3,500 kWh a year spends about $670 a year on hot water. "
     "A heat pump water heater using about a third of the power would cost about $220, saving roughly $450 a year. Your use may be higher or lower."),
    ("Will a heat pump water heater work in my basement?",
     "Usually, if the space stays between about 4°C and 32°C (40°F to 90°F) and has at least 1,000 cubic feet of air around it. "
     "It cools and dries the air it uses, which many damp Nova Scotia basements welcome."),
]


def body():
    kwh = 3500
    now = kwh * RATE
    hp = kwh / 3 * RATE
    faq_html = "".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in FAQ)
    return f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/ca/ns/">Nova Scotia</a></li><li aria-current="page">Heat pump water heaters</li></ol></nav>
<header class="hero"><div class="wrap"><h1>Heat Pump Water Heaters in Nova Scotia: $800 Rebate and Real Savings</h1>
<p>What you get back, what you'll save on your NS Power bill, and whether your basement suits one. Checked {CHECKED}.</p><p class="meta">By {e(AUTHOR['name'])}</p></div></header>
<section class="body"><div class="wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> Efficiency Nova Scotia takes <b>${REBATE}</b> off an ENERGY STAR heat pump water heater, instantly at participating stores, anywhere in the province including Cape Breton. If you now heat water with an electric tank, it uses roughly a third of the power. At NS Power's rate that's about <b>${now - hp:,.0f} a year</b> saved for a typical home.</p></div>

<h2>The rebate</h2>
<div class="tw"><table><tr><th>Offer</th><th>Amount</th><th>Rules</th></tr>
<tr><td><b>Instant rebate at the store</b></td><td>${REBATE}</td><td>ENERGY STAR model at a participating retailer. <a href="{REBATE_SRC}" rel="nofollow noopener" target="_blank">Source</a></td></tr>
<tr><td><b>Through a Home Energy Assessment</b></td><td>${REBATE}</td><td>Only if you didn't take the instant rebate. UEF at least 2.00 (under 56 gallons) or 2.20 (56+ gallons). Counts toward the $5,000 assessment cap. <a href="{HEA_SRC}" rel="nofollow noopener" target="_blank">Source</a></td></tr>
</table></div>
<p>You get one or the other, not both. The instant rebate is simplest if you're only replacing the water heater. If you're also doing insulation or a heat pump, the <a href="/programs/efficiency-nova-scotia/">Home Energy Assessment</a> bundles everything.</p>

<h2>What you'll save on your power bill</h2>
<p>NS Power charges <b>{RATE * 100:.3f}¢ per kWh</b> (standard residential rate from May 1, 2026, <a href="{RATE_SRC}" rel="nofollow noopener" target="_blank">source</a>). Heat pump water heaters deliver around three times the efficiency of a standard electric tank (<a href="{NYSERDA_SRC}" rel="nofollow noopener" target="_blank">NYSERDA</a>). Enter your household's hot water use to see your numbers:</p>
<div class="calc" style="background:#fff;border:1px solid #d9d0c1;border-radius:12px;padding:18px 20px;margin:10px 0 18px;">
<label for="kwh"><b>Electric tank use (kWh a year)</b></label>
<input id="kwh" type="number" inputmode="numeric" value="{kwh}" min="500" max="10000" step="100" style="display:block;width:100%;max-width:220px;padding:10px;margin:6px 0 4px;font:inherit;font-size:16px;border:1px solid #d9d0c1;border-radius:8px;">
<p class="small" style="margin:0 0 12px;">Not sure? 3,000 to 4,000 kWh is common for a family; more people and long showers push it higher.</p>
<p style="margin:4px 0;">Electric tank today: <b id="c-now">${now:,.0f}</b> a year</p>
<p style="margin:4px 0;">Heat pump water heater: <b id="c-hp">${hp:,.0f}</b> a year</p>
<p style="margin:4px 0;font-size:18px;">You save about <b id="c-save" style="color:#2d6a4f;">${now - hp:,.0f}</b> a year</p>
<p class="small" style="margin:8px 0 0;">Estimate only. Uses one-third of the tank's power; real results vary with the model, where it's installed and how much hot water you use.</p>
</div>
<script>(function(){{const R={RATE},i=document.getElementById('kwh'),f=v=>'$'+Math.round(v).toLocaleString();
function u(){{const k=Math.max(0,+i.value||0);document.getElementById('c-now').textContent=f(k*R);document.getElementById('c-hp').textContent=f(k/3*R);document.getElementById('c-save').textContent=f(k*R-k/3*R);}}
i.addEventListener('input',u);}})();</script>

<h2>Oil or propane hot water?</h2>
<p>If your hot water comes from an oil boiler or propane, the savings depend on your fuel price, and switching also means adding an electric circuit. Ask your installer for both running costs side by side. Homes that mainly heat with oil or propane may also qualify for Efficiency Nova Scotia's <a href="/programs/efficiency-nova-scotia/">Moderate Income Rebate</a>.</p>

<h2>Will it work in your home?</h2>
<ul>
<li><b>Space:</b> the room should stay between about 4°C and 32°C all year, with at least 1,000 cubic feet of air around the unit (<a href="{NYSERDA_SRC}" rel="nofollow noopener" target="_blank">NYSERDA</a>). An unfinished basement usually works.</li>
<li><b>It cools and dries the room.</b> That helps a damp basement. In a small closet it can struggle; ask about ducted or louvred-door options.</li>
<li><b>Noise:</b> it has a fan and compressor, about like a fridge. Avoid putting it next to a bedroom wall.</li>
<li><b>Drain:</b> it makes condensate, so it needs a floor drain or a small pump.</li>
<li><b>Size:</b> heat pump models recover more slowly than electric tanks. Families often go one size up (for example, 50 gallons becomes 65).</li>
</ul>

<h2>Before you buy</h2>
<ol>
<li>Confirm the model is ENERGY STAR and on Efficiency Nova Scotia's list, and that the store applies the ${REBATE} at checkout.</li>
<li>Check your electrical panel has room for a dedicated circuit (most models use 240 V).</li>
<li>Ask the installer where the condensate will drain and how the old tank is disposed of.</li>
</ol>

<h2>Common questions</h2>
{faq_html}
<p><b>Related:</b> <a href="/programs/efficiency-nova-scotia/">Efficiency Nova Scotia rebates</a> · <a href="/ca/ns/halifax/">Halifax rebates</a> · <a href="/ca/ns/cape-breton/">Cape Breton rebates</a> · <a href="/heat-pump-water-heater/">How heat pump water heaters work</a></p>
<p class="small">Something out of date? Email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a> and we'll check it within a week.</p>
</div></section>"""


def main():
    title = "Heat Pump Water Heater Nova Scotia: $800 Rebate, Savings, Cost (2026)"
    desc = ("Nova Scotia heat pump water heaters in 2026: $800 Efficiency NS rebate (Cape Breton too), yearly savings at NS Power's "
            "19.1¢/kWh rate, and whether your basement suits one. Savings calculator included.")
    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": title, "datePublished": CHECKED, "dateModified": CHECKED,
         "author": AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE}, "mainEntityOfPage": BASE + PATH},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Nova Scotia", "item": BASE + "/ca/ns/"},
            {"@type": "ListItem", "position": 3, "name": "Heat pump water heaters"}]},
    ]
    out = shell(title + " | HomePowerRebate", desc, PATH, "ns", body(), ld)
    out = out.replace("</style>", ".tw{overflow-x:auto;-webkit-overflow-scrolling:touch}.tw table{min-width:520px}</style>", 1)
    f = ROOT / PATH.strip("/") / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(out, encoding="utf-8")
    print("Wrote", PATH)
    link_pages()


def link_pages():
    """Marker-wrapped link from the NS water-heater pages and the general guide to this page."""
    import re
    from apply_canonical_nav_footer import content_insert_point
    S, E_ = "<!-- NS-HPWH-LINK-START -->", "<!-- NS-HPWH-LINK-END -->"
    blk = (f'{S}<section style="max-width:880px;margin:24px auto;padding:0 20px;"><p style="background:#f5efe5;border-radius:8px;padding:14px 18px;">'
           f'<b>In Nova Scotia?</b> See the <a href="{PATH}">$800 heat pump water heater rebate and what you\'ll save at NS Power rates</a>.</p></section>{E_}')
    for rel in ["ca/ns/halifax/water-heater", "ca/ns/cape-breton/water-heater", "heat-pump-water-heater"]:
        f = ROOT / rel / "index.html"
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8")
        if S in t:
            t = re.sub(re.escape(S) + ".*?" + re.escape(E_), lambda m: blk, t, count=1, flags=re.S)
        else:
            i = content_insert_point(t)
            if i < 0:
                continue
            t = t[:i] + blk + "\n" + t[i:]
        f.write_text(t, encoding="utf-8")
        print("Linked", rel)


if __name__ == "__main__":
    main()
