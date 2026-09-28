#!/usr/bin/env python3
"""Build /installers/survey/: the 2026 installer survey (noindex).

Answers POST to https://leads.homepowerrebate.com/installer-survey (Worker), which stores them in
D1 (installer_survey table), logs to the Sheet and emails ops. Results feed the public installer report.

Pricing is asked as a total price for a defined typical job (solar: price per watt), in ranges, so
answers are comparable across companies and quick to give.
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell  # noqa: E402

PATH = "/installers/survey/"
ENDPOINT = "https://leads.homepowerrebate.com/installer-survey"
e = html.escape

REGIONS = [("bc", "British Columbia", "CAD"), ("on", "Ontario", "CAD"), ("ab", "Alberta", "CAD"), ("ns", "Nova Scotia", "CAD"),
           ("ma", "Massachusetts", "USD"), ("ny", "New York", "USD"), ("ca", "California", "USD"), ("co", "Colorado", "USD"),
           ("pa", "Pennsylvania", "USD"), ("vt", "Vermont", "USD"), ("other", "Somewhere else", "")]

# Rebate programs homeowners use, by region (options only; "other" is always offered).
REBATES = {
    "bc": ["BC Hydro heat pump rebate", "CleanBC income-qualified rebates", "BC Hydro solar or battery rebate", "FortisBC rebates", "City top-ups"],
    "on": ["Home Renovation Savings (with assessment)", "Home Renovation Savings (no assessment)", "Energy Affordability Program", "City loan (e.g. Toronto HELP)"],
    "ab": ["CEIP financing", "Calgary Home Upgrades", "City or utility rebate"],
    "ns": ["Home Energy Assessment rebates", "Moderate Income Rebate", "Free upgrades (Efficiency Nova Scotia)"],
    "ma": ["Mass Save heat pump rebate", "Mass Save 0% HEAT Loan", "Mass Save income-eligible", "MA solar tax credit", "ConnectedSolutions"],
    "ny": ["NYS Clean Heat", "EmPower+", "NY-Sun", "Comfort Home"],
    "ca": ["TECH Clean California", "Energy Savings Assistance", "SMUD or city utility rebates", "SGIP (batteries)"],
    "co": ["Xcel Energy rebates", "City or utility rebate", "State income-qualified program"],
    "pa": ["Utility rebate (PECO, PPL, Duquesne...)", "State income-qualified program"],
    "vt": ["Efficiency Vermont", "Utility rebate (e.g. Green Mountain Power)"],
}

SERVICES = [("heat-pump", "Heat pumps"), ("solar", "Solar"), ("battery", "Home batteries"), ("insulation", "Insulation")]

# One defined job per trade, so every answer describes the same thing.
PRICE_Q = {
    "heat-pump": [
        ("price_hp_ducted", "Whole-home cold-climate heat pump, ducted, replacing a furnace or AC in a typical 2,000 sq ft house",
         ["Under 10,000", "10,000–15,000", "15,000–20,000", "20,000–25,000", "25,000–30,000", "Over 30,000"]),
        ("price_hp_minisplit", "One ductless mini-split (single zone), installed",
         ["Under 3,000", "3,000–5,000", "5,000–7,000", "7,000–10,000", "Over 10,000"]),
    ],
    "solar": [
        ("price_solar_watt", "Price per watt, before rebates, for a typical 6–10 kW rooftop system",
         ["Under 2.50", "2.50–3.00", "3.00–3.50", "3.50–4.00", "4.00–5.00", "Over 5.00"]),
    ],
    "battery": [
        ("price_battery", "One battery of about 13.5 kWh (Powerwall-size), installed with an existing solar system",
         ["Under 10,000", "10,000–13,000", "13,000–16,000", "16,000–20,000", "Over 20,000"]),
    ],
    "insulation": [
        ("price_attic", "Attic top-up to about R-50/R-60 for a 1,000 sq ft attic, including air sealing",
         ["Under 1,500", "1,500–2,500", "2,500–3,500", "3,500–5,000", "Over 5,000"]),
    ],
}

ALSO_ASK = ["Heat pump", "Central AC only", "New furnace", "Solar", "Home battery", "Backup generator", "Insulation or air sealing",
            "Windows or doors", "EV charger", "Electrical panel upgrade", "Heat pump water heater"]
BLOCKERS = ["Upfront price", "Confused by rebates", "Rebates take too long to pay", "Waiting for an install date",
            "Home isn't a good fit", "Can't get financing", "Condo, strata or landlord rules"]


def radios(name, opts, required=False):
    req = " required" if required else ""
    return '<div class="sv-opts">' + "".join(
        f'<label class="sv-pick"><input type="radio" name="{name}" value="{e(o)}"{req}> {e(o)}</label>' for o in opts) + "</div>"


def checks(name, opts, cls=""):
    return f'<div class="sv-opts {cls}">' + "".join(
        f'<label class="sv-pick"><input type="checkbox" name="{name}" value="{e(v)}"> {e(t)}</label>' for v, t in opts) + "</div>"


def build():
    price_html = ""
    for svc, label in SERVICES:
        qs = "".join(
            f'<fieldset><legend>{e(q)}</legend>{radios(k, opts + ["We don’t do this job"])}</fieldset>' for k, q, opts in PRICE_Q[svc])
        price_html += f'<div class="sv-svc" data-svc="{svc}" hidden><h3>{e(label)}</h3>{qs}</div>'

    rebate_html = "".join(
        f'<div class="sv-reb" data-region="{r}" hidden>{checks("rebates", [(x, x) for x in opts])}</div>' for r, opts in REBATES.items())

    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/installers/">Installers</a></li><li aria-current="page">2026 installer survey</li></ol></nav>
<header class="hero"><div class="wrap"><h1>2026 Home Energy Installer Survey</h1>
<p>Five minutes. Real answers from installers on prices, wait times and rebates, so homeowners know what to expect before they call you.</p></div></header>
<section class="body"><div class="wrap">
<div class="sv-give"><h2 style="margin-top:0">What you get for taking part</h2><ul>
<li><b>A "Survey contributor" mark</b> next to your company on our top-rated rankings. It shows you share real information with homeowners. It never changes your rank.</li>
<li><b>Credit in the 2026 Installer Report</b>, with your company name and a link to your website, if we quote your answer. You choose below.</li>
<li><b>Your free top-rated badge</b>, if you're ranked. <a href="/installers/badge/">Get it here</a>.</li>
</ul><p class="small">We only publish totals and ranges by region. Your prices are never shown next to your name.</p></div>

<form id="sv" class="qf" novalidate>
<h2 style="margin-top:0">About your company</h2>
<div class="qf-row"><label>Company name<input name="company" required autocomplete="organization"></label>
<label>Your name<input name="name" autocomplete="name"></label></div>
<div class="qf-row"><label>Email<input type="email" name="email" required autocomplete="email"></label>
<label>Website<input name="company_site" placeholder="https://" autocomplete="url"></label></div>
<div class="qf-row"><label>Where do you work?<select name="region" id="sv-region" required><option value="">Choose one</option>
{"".join(f'<option value="{r}" data-cur="{c}">{e(n)}</option>' for r, n, c in REGIONS)}</select></label>
<label>Main city<input name="city" required></label></div>
<fieldset><legend>What do you install?</legend>{checks("services", SERVICES, "qf-grid")}</fieldset>

<h2>1. Prices for a typical job</h2>
<p>Pick the range your typical customer pays for each job, before rebates, including installation. <span id="sv-cur"></span></p>
<p class="sv-hint" id="sv-pick-first">Choose what you install above to see these questions.</p>
{price_html}
<fieldset><legend>Compared to a year ago, your prices are:</legend>{radios("price_trend", ["Down more than 5%", "About the same", "Up 5–10%", "Up more than 10%"])}</fieldset>

<h2>2. Wait times</h2>
<fieldset><legend>If a homeowner signed today, when could you start a typical job?</legend>{radios("lead_time", ["Within a week", "1–2 weeks", "2–4 weeks", "1–2 months", "More than 2 months"])}</fieldset>

<h2>3. Rebates</h2>
<fieldset><legend>About how many of your jobs use at least one rebate or incentive?</legend>{radios("rebate_share", ["Almost none", "Under 25%", "25–50%", "50–75%", "Over 75%"])}</fieldset>
<fieldset><legend>Which rebates do your customers use most? Pick up to 3.</legend>
<p class="sv-hint" id="sv-reb-first">Choose where you work above to see the programs.</p>{rebate_html}
<label>Another program<input name="rebate_other"></label></fieldset>
<label>Which rebate causes the most delays or paperwork headaches, and why?<textarea name="rebate_pain" rows="2" maxlength="400"></textarea></label>

<h2>4. What homeowners ask for</h2>
<fieldset><legend>When homeowners call you, what else do they ask about? Pick all that apply.</legend>{checks("also_ask", [(x, x) for x in ALSO_ASK], "qf-grid")}</fieldset>
<fieldset><legend>What's the most common reason a homeowner doesn't go ahead?</legend>{radios("blocker", BLOCKERS)}</fieldset>
<label>What's one thing you wish every homeowner knew before calling you?<textarea name="wish" rows="3" maxlength="500"></textarea></label>

<h2>5. Credit</h2>
<label class="qf-pick"><input type="checkbox" name="quote_ok" value="yes" checked> You can quote my answers with my company name and a link to our website.</label>
<label class="qf-pick"><input type="checkbox" name="mark_ok" value="yes" checked> Show a "Survey contributor" mark on our ranking.</label>
<input type="text" name="website" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px" aria-hidden="true">
<button type="submit" class="qf-btn">Send my answers</button>
<div id="qf-msg" role="status"></div>
</form>
<div id="sv-ok" class="qf-ok" hidden><p><b>Thank you!</b> Your answers are in. If you're ranked, your contributor mark will appear at the next monthly update.</p></div>
<p class="small">Questions? Email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a>. We use your answers only for the report and never sell your details.</p>
</div></section>
<script>
(function(){{
var f=document.getElementById('sv'),reg=document.getElementById('sv-region');
function sync(){{
  var picked=[].map.call(f.querySelectorAll('input[name=services]:checked'),function(x){{return x.value}});
  document.querySelectorAll('.sv-svc').forEach(function(d){{d.hidden=picked.indexOf(d.dataset.svc)<0}});
  document.getElementById('sv-pick-first').hidden=picked.length>0;
  var r=reg.value;document.querySelectorAll('.sv-reb').forEach(function(d){{d.hidden=d.dataset.region!==r}});
  document.getElementById('sv-reb-first').hidden=!!r;
  var o=reg.options[reg.selectedIndex],c=o&&o.dataset.cur;document.getElementById('sv-cur').textContent=c?'Prices in '+c+'.':'';
}}
f.addEventListener('change',function(ev){{
  if(ev.target.name==='rebates'){{var on=f.querySelectorAll('.sv-reb:not([hidden]) input[name=rebates]:checked');if(on.length>3)ev.target.checked=false;}}
  sync();}});
f.addEventListener('submit',function(ev){{
  ev.preventDefault();var msg=document.getElementById('qf-msg');msg.textContent='';
  if(!f.checkValidity()){{msg.textContent='Please fill in your company, email, region and city.';f.reportValidity();return;}}
  var d={{}};new FormData(f).forEach(function(v,k){{if(k==='rebates'||k==='services'||k==='also_ask'){{(d[k]=d[k]||[]).push(v)}}else d[k]=v}});
  d.rebates=(d.rebates||[]).filter(function(v){{return [].some.call(f.querySelectorAll('.sv-reb:not([hidden]) input:checked'),function(x){{return x.value===v}})}});
  d.page_url=location.href;var b=f.querySelector('button');b.disabled=true;b.textContent='Sending...';
  fetch('{ENDPOINT}',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(d)}})
  .then(function(r){{return r.json().then(function(j){{if(!r.ok)throw new Error(j.error||'Error');}})}})
  .then(function(){{f.hidden=true;document.getElementById('sv-ok').hidden=false;window.scrollTo(0,0);if(window.gtag)gtag('event','installer_survey_submit',{{region:d.region}});}})
  .catch(function(err){{msg.textContent='Sorry, that didn\\'t send ('+err.message+'). Please try again or email hello@homepowerrebate.com.';b.disabled=false;b.textContent='Send my answers';}});
}});
sync();
}})();
</script>"""
    css = """.sv-give{background:#f5efe5;border-left:4px solid #2d6a4f;border-radius:10px;padding:18px 20px;margin-bottom:8px}
.sv-opts{display:flex;flex-direction:column}.sv-opts.qf-grid{display:grid}
.sv-pick{display:flex;gap:10px;align-items:center;min-height:44px;font-weight:500}.sv-pick,.qf-pick{flex-direction:row!important}.sv-pick input,.qf-pick input{width:20px!important;height:20px;flex:none;display:inline-block!important;margin:0!important;padding:0!important}
.sv-svc h3{font-size:19px;margin:18px 0 0}.sv-hint{font-style:italic;color:#6b8e7f!important}
#sv h2{font-size:22px;margin:30px 0 8px}
.qf{background:#fff;border:2px solid #0d4f5c;border-radius:14px;padding:22px 20px;margin:28px 0}
.qf fieldset{border:0;margin:14px 0}.qf legend{font-weight:700;margin-bottom:8px}
.qf-pick{display:flex;gap:10px;align-items:center;min-height:44px;font-weight:500}.qf-pick input{width:20px;height:20px;flex:none}
.qf-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:0 12px}
.qf-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.qf label:not(.qf-pick):not(.sv-pick){display:block;font-weight:600;font-size:15px;margin:10px 0 0}
.qf input:not([type=checkbox]):not([type=radio]),.qf select,.qf textarea{display:block;width:100%;margin-top:4px;padding:11px;border:1px solid #d9d0c1;border-radius:8px;font:inherit;font-size:16px}
.qf-btn{margin-top:16px;background:#d4751c;color:#fff;border:0;border-radius:8px;padding:14px 22px;font:inherit;font-weight:700;font-size:16px;cursor:pointer;min-height:48px}
.qf-ok{background:#eef6f0;border-radius:8px;padding:14px}#qf-msg{margin-top:10px;font-weight:600;color:#8a2a1c}
.small{font-size:13.5px!important;color:#6b8e7f!important}"""
    page = shell("2026 Home Energy Installer Survey | HomePowerRebate",
                 "A five-minute survey for heat pump, solar, battery and insulation installers: prices, wait times and rebates.",
                 PATH, "on", body, [])
    page = page.replace('content="index, follow, max-snippet:-1, max-image-preview:large"', 'content="noindex, follow"', 1)
    page = page.replace("</style>", css + "</style>", 1)
    out = ROOT / PATH.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"Wrote {PATH}")


if __name__ == "__main__":
    build()
