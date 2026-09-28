#!/usr/bin/env python3
"""Build /solar-quote-checker/ — paste your solar quote(s), get price-per-watt, verified rebates,
estimated production and payback, and red flags.

Why: homeowner research (Sept 2026) showed people distrust solar quotes ("a six-year payback pitch
in 2026 is very often last year's math"). No site lets them check a real quote against real data.

Data:
  - Sun hours per city: city-solar-data.json (5-year satellite radiation averages).
  - US price band: LBNL Tracking the Sun 2024 edition, 20th-80th percentile for residential
    systems installed in 2023 = $3.2-$5.5/W. No equivalent Canadian survey, so Canadian quotes are
    compared to each other only.
  - Rebates: only ones in data/verified-facts/*.json. Anything else says "check".
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell, CHECKED, ISO, AUTHOR  # noqa: E402
from build_installer_rankings import BASE  # noqa: E402

PATH = "/solar-quote-checker/"

# Verified solar incentives by region (see data/verified-facts). kind "per_kw_capped": $/kW, cap, max share of cost.
REBATES = {
    "BC": {"kind": "per_kw_capped", "per_kw": 1000, "cap": 5000, "share": 0.5,
           "name": "BC Hydro solar rebate", "note": "BC Hydro customers only. FortisBC customers (e.g. Kelowna) aren't eligible."},
    "ON": {"kind": "per_kw_capped", "per_kw": 1000, "cap": 5000, "share": 0.5,
           "name": "Home Renovation Savings solar rebate", "note": "You can't also sign a net-metering agreement with your utility if you take this rebate."},
    "MA": {"kind": "flat", "amount": 1000, "name": "Massachusetts state solar tax credit (max $1,000)",
           "note": "The federal 30% credit ended for systems installed after Dec 31, 2025."},
    "NY": {"kind": "none", "name": "NY-Sun incentive", "note": "NY-Sun pays by the watt in blocks that change. Check the current block on NYSERDA's site. The federal 30% credit ended Dec 31, 2025."},
    "CA": {"kind": "none", "name": "No upfront solar rebate", "note": "California pays much less for power you send to the grid (net billing), so savings depend on how much you use yourself. The federal 30% credit ended Dec 31, 2025."},
    "AB": {"kind": "none", "name": "No provincial or utility solar rebate", "note": "CEIP financing may be open in your town."},
    "NS": {"kind": "none", "name": "No current solar rebate", "note": "SolarHomes closed to homeowners April 17, 2025."},
    "CO": {"kind": "none", "name": "No verified rebate on file", "note": "Check your utility. The federal 30% credit ended Dec 31, 2025."},
    "PA": {"kind": "none", "name": "No verified rebate on file", "note": "Check your utility. The federal 30% credit ended Dec 31, 2025."},
    "VT": {"kind": "none", "name": "No verified rebate on file", "note": "Check Efficiency Vermont and your utility. The federal 30% credit ended Dec 31, 2025."},
}
US = {"MA", "NY", "CA", "CO", "PA", "VT"}
REGION_NAMES = {"BC": "British Columbia", "ON": "Ontario", "AB": "Alberta", "NS": "Nova Scotia", "MA": "Massachusetts",
                "NY": "New York", "CA": "California", "CO": "Colorado", "PA": "Pennsylvania", "VT": "Vermont"}

FAQ = [
    ("What is a fair price per watt for solar?", "In the US, the middle 60% of home systems installed in 2023 cost $3.20 to $5.50 per watt before incentives (Lawrence Berkeley National Lab). Bigger systems usually cost less per watt. In Canada there's no official survey, so compare two or three quotes for the same size system."),
    ("How do I work out price per watt?", "Divide the total price before rebates by the system size in watts. A $24,000 quote for an 8 kW (8,000 watt) system is $3.00 per watt."),
    ("Can I still get the 30% federal solar tax credit?", "No, not if you own the system. The federal residential clean energy credit (25D) ended for systems installed after December 31, 2025. A quote that still subtracts 30% is using old math."),
    ("How long should solar take to pay back?", "It depends on your electricity rate, your sun, and your price. Many 2026 paybacks land around 10 years or more. Be careful with any quote promising under 6 years. Ask to see the math."),
    ("Should I lease or buy solar?", "Buying usually saves more over 25 years. With a lease or PPA you don't own the panels, you may face yearly price increases, and it can complicate selling your home. Read the transfer terms before you sign."),
]


def cities():
    solar = json.loads((ROOT / "city-solar-data.json").read_text())
    ranks = {(r["region"], r["city"].lower()): r["url"] for r in json.loads((ROOT / "installers" / "rankings.json").read_text())
             if r["service"] == "solar"}
    out = []
    for key, c in sorted(solar.items(), key=lambda kv: (kv[1]["region"], kv[1]["city"])):
        reg = c["region"]
        out.append({"k": key, "city": c["city"], "region": reg, "sun": c["approx_peak_sun_hours"],
                    "rank": ranks.get((reg.lower(), c["city"].lower()), "")})
    return out


JS = r"""
const C = window.SQC_CITIES, R = window.SQC_REBATES, US = new Set(window.SQC_US);
const $ = id => document.getElementById(id);
const money = n => '$' + Math.round(n).toLocaleString();
const sel = $('sq-city');
let last = '';
C.forEach((c, i) => { if (c.region !== last) { const g = document.createElement('optgroup'); g.label = window.SQC_NAMES[c.region]; sel.appendChild(g); last = c.region; }
  const o = document.createElement('option'); o.value = i; o.textContent = c.city; sel.lastChild.appendChild(o); });
function addQuote() {
  const n = document.querySelectorAll('.sq-quote').length; if (n >= 3) return;
  const d = document.createElement('div'); d.className = 'sq-quote';
  d.innerHTML = `<b>Quote ${n + 1}</b><label>System size (kW)<input type="number" step="0.1" min="1" class="q-kw" placeholder="e.g. 8"></label>
  <label>Total price before rebates ($)<input type="number" step="100" min="1000" class="q-price" placeholder="e.g. 24000"></label>
  <label class="chk"><input type="checkbox" class="q-batt"> Price includes a battery</label>`;
  $('sq-quotes').appendChild(d); if (n >= 2) $('sq-add').style.display = 'none';
}
function rebate(reg, kw, price) {
  const r = R[reg];
  if (r.kind === 'per_kw_capped') return Math.min(kw * r.per_kw, r.cap, price * r.share);
  if (r.kind === 'flat') return r.amount;
  return 0;
}
function check() {
  const c = C[sel.value], rate = parseFloat($('sq-rate').value), reg = c.region, isUS = US.has(reg);
  const qs = [...document.querySelectorAll('.sq-quote')].map((d, i) => ({ i: i + 1,
    kw: parseFloat(d.querySelector('.q-kw').value), price: parseFloat(d.querySelector('.q-price').value), batt: d.querySelector('.q-batt').checked }))
    .filter(q => q.kw > 0 && q.price > 0);
  const out = $('sq-result');
  if (!qs.length) { out.innerHTML = '<p class="warn">Enter a system size and price for at least one quote.</p>'; return; }
  const flags = [];
  let rows = '';
  qs.forEach(q => {
    const ppw = q.price / (q.kw * 1000);
    const kwh = q.kw * c.sun * 365 * 0.80;
    const reb = rebate(reg, q.kw, q.price);
    const net = q.price - reb;
    const save = rate > 0 ? kwh * rate : 0;
    const pay = save > 0 ? net / save : 0;
    let verdict = '';
    if (q.batt) verdict = 'Includes a battery, so price per watt will look high. Ask for the solar-only price.';
    else if (isUS) verdict = ppw < 3.2 ? 'Below the typical US range. Good price, but check equipment and warranty.' :
      ppw <= 5.5 ? 'Within the typical US range ($3.20–$5.50/W).' : 'Above the typical US range. Ask why, or get another quote.';
    rows += `<tr><td>Quote ${q.i}</td><td>${q.kw} kW</td><td><b>$${ppw.toFixed(2)}/W</b></td><td>${money(reb)}</td><td>${money(net)}</td>
      <td>${Math.round(kwh).toLocaleString()} kWh</td><td>${save ? money(save) : '—'}</td><td>${pay ? pay.toFixed(1) + ' yrs' : '—'}</td></tr>
      ${verdict ? `<tr><td colspan="8" class="verdict">${verdict}</td></tr>` : ''}`;
  });
  const plain = qs.filter(q => !q.batt).map(q => q.price / (q.kw * 1000));
  if (plain.length > 1) { const lo = Math.min(...plain), hi = Math.max(...plain);
    if (hi / lo > 1.25) flags.push(`Your quotes differ by ${Math.round((hi / lo - 1) * 100)}% per watt. Ask the higher bidder what you're getting for the extra money.`); }
  if ($('f-credit').checked) flags.push(isUS ? '<b>The 30% federal tax credit is gone for owned systems</b> installed after Dec 31, 2025. If the quote subtracts it, the real cost is higher than shown.'
    : '<b>There\'s no federal solar grant in Canada in 2026.</b> The Canada Greener Homes Grant and Loan are closed. If a quote subtracts one, the real cost is higher than shown.');
  if ($('f-pay').checked) flags.push('<b>A very short payback promise</b> is often last year\'s math. Compare it with the estimate above, which uses your own electricity rate.');
  if ($('f-lease').checked) flags.push('<b>Lease or PPA:</b> you don\'t own the panels. Check yearly price increases (escalators) and what happens if you sell your home.');
  if ($('f-today').checked) flags.push('<b>"Sign today" pressure</b> is a red flag. Rebates don\'t vanish overnight; a good installer will give you time to compare.');
  if ($('f-roof').checked) flags.push('<b>Roof age:</b> if your roof needs replacing within about 10 years, do it first. Removing and reinstalling panels later costs thousands.');
  const r = R[reg];
  out.innerHTML = `<h3>Your results for ${c.city}</h3>
  <div class="tbl"><table><thead><tr><th></th><th>Size</th><th>Price/watt</th><th>Rebate</th><th>After rebate</th><th>Yearly output*</th><th>Yearly savings</th><th>Payback</th></tr></thead><tbody>${rows}</tbody></table></div>
  <p><b>Rebate used:</b> ${r.name}. ${r.note}</p>
  ${!isUS ? '<p>There\'s no official price survey for Canada, so we don\'t grade Canadian prices against US numbers. Compare your quotes to each other for the same size system.</p>' : ''}
  ${flags.length ? '<div class="flags"><b>Things to check</b><ul>' + flags.map(f => '<li>' + f + '</li>').join('') + '</ul></div>' : ''}
  <p class="small">*Output estimate: size × ${c.sun} sun-hours a day (5-year average for ${c.city}) × 365 × 80% for real-world losses. Savings assume every kWh offsets power you'd buy at your rate; if your utility pays less for exported power, savings will be lower.</p>
  ${c.rank ? `<p><a class="cta" href="${c.rank}">Compare top-rated solar installers in ${c.city} &rarr;</a></p>` : `<p><a class="cta" href="/installers/">Find top-rated solar installers &rarr;</a></p>`}`;
  out.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
$('sq-add').addEventListener('click', addQuote);
$('sq-go').addEventListener('click', check);
addQuote();
"""

CSS = """
.sq-card{background:#fff;border:1px solid #d9d0c1;border-radius:12px;padding:20px;margin:20px 0;}
.sq-card label{display:block;font-weight:600;font-size:15px;margin:10px 0 4px;}
.sq-card input[type=number],.sq-card select{width:100%;padding:11px;border:1px solid #d9d0c1;border-radius:8px;font:inherit;font-size:16px;box-sizing:border-box;}
.sq-card label.chk{font-weight:400;display:flex;gap:8px;align-items:center;}
.sq-quote{border-top:1px dashed #d9d0c1;padding-top:12px;margin-top:12px;}
.sq-btn{background:#d4751c;color:#fff;border:0;border-radius:8px;padding:14px 22px;font:inherit;font-weight:700;font-size:16px;cursor:pointer;margin-top:14px;}
.sq-btn.alt{background:#f5efe5;color:#0a2a2e;border:1px solid #d9d0c1;}
.tbl{overflow-x:auto;}table{width:100%;border-collapse:collapse;font-size:14px;margin:12px 0;}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #d9d0c1;}th{background:#f5efe5;white-space:nowrap;}
td.verdict{font-size:14px;color:#1a3d42;background:#faf7f2;}
.flags{background:#fff4e8;border-left:4px solid #d4751c;border-radius:8px;padding:14px 16px;margin:14px 0;}
.small{font-size:13px;color:#1a3d42;}.warn{color:#b3261e;font-weight:600;}
a.cta{display:inline-block;background:#0d4f5c;color:#fff;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:700;}
"""


def build():
    data = cities()
    e = html.escape
    faq = "".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in FAQ)
    flags = [("f-credit", "It subtracts a federal tax credit or grant"), ("f-pay", "It promises payback in under 6 years"),
             ("f-lease", "It's a lease or PPA (you don't buy the panels)"), ("f-today", "They want you to sign today"),
             ("f-roof", "My roof is over 15 years old")]
    flag_html = "".join(f'<label class="chk"><input type="checkbox" id="{i}"> {e(t)}</label>' for i, t in flags)
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">Solar quote checker</li></ol></nav>
<header class="hero"><div class="wrap"><h1>Solar Quote Checker: Is Your Quote Fair?</h1>
<p>Enter up to three quotes. See the price per watt, the rebates you really qualify for, and an honest payback. Free, no sign-up.</p></div></header>
<section class="body"><div class="wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> Divide the price by the system size in watts. In the US, most home systems cost $3.20 to $5.50 per watt before incentives. In 2026 the 30% federal tax credit is gone for systems you buy, so any quote still subtracting it is using old math.</p></div>
<div class="sq-card">
<label for="sq-city">Your city</label><select id="sq-city"></select>
<label for="sq-rate">Your electricity rate ($ per kWh) <span style="font-weight:400">— on your bill. Include delivery charges.</span></label>
<input type="number" id="sq-rate" step="0.01" min="0" placeholder="e.g. 0.14">
<div id="sq-quotes"></div>
<button type="button" class="sq-btn alt" id="sq-add">+ Add another quote</button>
<p style="font-weight:700;margin:18px 0 4px;">Does any quote do this? (tick all that apply)</p>
{flag_html}
<button type="button" class="sq-btn" id="sq-go">Check my quote</button>
</div>
<div id="sq-result" aria-live="polite"></div>
<h2>How to read a solar quote</h2>
<ul><li><b>Price per watt</b> is the fairest way to compare quotes of different sizes.</li>
<li><b>Same equipment?</b> Compare panel brand, inverter type (string or microinverters) and warranty length.</li>
<li><b>Who owns it?</b> If it's a lease or PPA, the installer owns the panels.</li>
<li><b>Rebates:</b> ask who applies for them, and get pre-approval where it's required.</li></ul>
<h2>Common questions</h2>
{faq}
<p class="small" style="margin-top:28px;"><b>Sources, checked {CHECKED}:</b> <a href="https://emp.lbl.gov/tracking-the-sun" rel="noopener">Lawrence Berkeley National Lab, Tracking the Sun (2024 edition)</a> ·
<a href="https://app.bchydro.com/accounts-billing/electrical-connections/customer-generation/solar-battery-rebates.html" rel="noopener">BC Hydro solar rebate</a> ·
<a href="https://www.homerenovationsavings.ca/without-assessment/solar" rel="noopener">Ontario Home Renovation Savings: solar</a> ·
<a href="https://www.irs.gov/credits-deductions/residential-clean-energy-credit" rel="noopener">IRS residential clean energy credit</a>. Sun hours are 5-year satellite averages for each city.</p>
<p><b>Related:</b> <a href="/blog/why-solar-quotes-vary-so-much/">Why solar quotes vary so much</a> · <a href="/blog/red-flags-choosing-solar-installer/">Red flags when choosing an installer</a> · <a href="/installers/">Top-rated installers by city</a></p>
</div></section>
<script>window.SQC_CITIES={json.dumps(data)};window.SQC_REBATES={json.dumps(REBATES)};window.SQC_US={json.dumps(sorted(US))};window.SQC_NAMES={json.dumps(REGION_NAMES)};</script>
<script>{JS}</script>"""
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": "Solar Quote Checker", "url": BASE + PATH,
         "applicationCategory": "FinanceApplication", "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
         "description": "Check a home solar quote: price per watt, verified rebates, estimated output and payback, and red flags.", "dateModified": ISO, "author": AUTHOR},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
    ]
    page = shell("Solar Quote Checker: Is Your Quote Fair? (2026) | HomePowerRebate",
                 "Check your solar quote free: price per watt vs real market data, rebates you actually qualify for, honest payback, and red flags like the ended 30% tax credit.",
                 PATH, "on", body, ld)
    page = page.replace("</style>", CSS + "</style>", 1)
    f = ROOT / PATH.strip("/") / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(page, encoding="utf-8")
    print(f"Wrote {PATH} with {len(data)} cities.")


INBOUND = ["blog/why-solar-quotes-vary-so-much/index.html", "blog/red-flags-choosing-solar-installer/index.html"]
LS, LE = "<!-- SQC-LINK-START -->", "<!-- SQC-LINK-END -->"


def link_inbound():
    block = (f'{LS}<p style="max-width:760px;margin:24px auto;padding:14px 18px;background:#f5efe5;border-radius:8px;">'
             f'<b>Got a quote already?</b> <a href="{PATH}">Check it with our free solar quote checker</a>: price per watt, '
             f'the rebates you really qualify for, and an honest payback.</p>{LE}')
    for rel in INBOUND:
        f = ROOT / rel
        s = f.read_text(encoding="utf-8")
        if LS in s:
            s = s[:s.index(LS)] + block + s[s.index(LE) + len(LE):]
        else:
            i = s.index("<h2")
            s = s[:i] + block + "\n" + s[i:]
        f.write_text(s, encoding="utf-8")


if __name__ == "__main__":
    build()
    link_inbound()
