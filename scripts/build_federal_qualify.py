#!/usr/bin/env python3
"""/programs/national-heat-pump-rebate/do-i-qualify/: "Do I qualify?" for the National Heat Pump Rebate (first built 2026-10-22, rewritten 2026-11-20).
Ottawa's campaign page (read in full 2026-11-19) now publishes the income table, eligible fuels, who may apply and the dates, so the tool gives a
real answer: tier ($10,000 or $2,000) from province, household size and after-tax income, plus fuel, ownership and timing. The thresholds are read
from federal-6 in data/verified-facts/federal.json, so a change there changes the tool. Ottawa says parameters may still change: the page says so.
Usage: python3 scripts/build_federal_qualify.py && python3 scripts/post_steps.py"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import page_kit as kit  # noqa: E402

e = html.escape
PATH = "/programs/national-heat-pump-rebate/do-i-qualify/"
GUIDE = "/programs/national-heat-pump-rebate/"
TITLE = "Federal Heat Pump Rebate Income Limits by Province (2026)"
DESC = "Ottawa's income limit for the $10,000 federal heat pump rebate, by province and household size. Check your income, fuel and home in one minute."
RELEASE = "https://www.canada.ca/en/environment-climate-change/news/2026/10/prime-minister-carney-announces-landmark-investment-to-retrofit-one-million-homes-cutting-energy-costs-and-emissions.html"
CAMPAIGN = "https://www.canada.ca/en/environment-climate-change/campaigns/one-million-home-energy-retrofits.html"
PM = "https://www.pm.gc.ca/en/news/news-releases/2026/10/08/prime-minister-carney-announces-landmark-investment-retrofit-one"
CBC = "https://www.cbc.ca/news/canada/canada-heat-pump-retrofit-faq-9.7374613"
GHAP = "https://natural-resources.canada.ca/energy-efficiency/home-energy-efficiency/canada-greener-homes-initiative/canada-greener-homes-affordability-program"
FACTS = ["federal-0-national-heat-pump-rebate", "federal-1-launch-and-retroactivity", "federal-2-how-it-works", "federal-3-stacking", "federal-4-greener-homes-affordability", "federal-6-income-thresholds", "federal-7-eligible-homes-fuels-products"]

PROVS = [("bc", "British Columbia"), ("on", "Ontario"), ("ab", "Alberta"), ("sk", "Saskatchewan"), ("mb", "Manitoba"), ("qc", "Quebec"),
         ("nb", "New Brunswick"), ("ns", "Nova Scotia"), ("pe", "Prince Edward Island"), ("nl", "Newfoundland and Labrador"),
         ("yt", "Yukon"), ("nt", "Northwest Territories"), ("nu", "Nunavut")]
GHAP_PROVS = {"bc", "mb", "ns", "pe", "qc"}   # federal-4: provinces accepting applications on the NRCan page


def prov_links():
    out = {}
    for c, n in PROVS:
        hp = ROOT / "ca" / c / "heat-pump" / "index.html"
        hub = ROOT / "ca" / c / "index.html"
        calc = ROOT / "calculator" / c / "index.html"
        out[c] = {"name": n, "hp": f"/ca/{c}/heat-pump/" if hp.exists() else (f"/ca/{c}/" if hub.exists() else ""),
                  "calc": f"/calculator/{c}/" if calc.exists() else "", "ghap": c in GHAP_PROVS}
    return out


def thresholds():
    """{province name: [1, 2, 3, 4, 5+ person after-tax income lines]} from fact federal-6."""
    t = {x["id"]: x for x in json.loads((ROOT / "data/verified-facts/federal.json").read_text())["facts"]}["federal-6-income-thresholds"]["eligibility"]
    body = t.split("5 or more people: ", 1)[1]
    rows = re.findall(r"([A-Z][A-Za-z ]+?) ([\d,]+) / ([\d,]+) / ([\d,]+) / ([\d,]+) / ([\d,]+)", body)
    assert len(rows) == 13, len(rows)
    return {r[0].strip(): [int(c.replace(",", "")) for c in r[1:]] for r in rows}


# fuel and ownership answers (federal-7); status: said | partial | notyet
RULES = {
    "fuel": {
        "oil": ["said", "Oil heat qualifies. Ottawa says homes that switch from oil, propane or electric resistance heat save more than $1,400 a year on average.", "federal-7"],
        "propane": ["said", "Propane heat qualifies. Ottawa says homes that switch from oil, propane or electric resistance heat save more than $1,400 a year on average.", "federal-7"],
        "electric": ["said", "Electric heat qualifies, including electric furnaces and baseboards. Ottawa says these homes save more than $1,400 a year on average.", "federal-7"],
        "gas": ["said", "Natural gas heat qualifies. Ottawa also warns that switching from gas may not lower your bills, depending on your region and system, so run the numbers first.", "federal-7"],
        "wood": ["said", "Wood heat qualifies. Ottawa lists electricity, natural gas, oil, propane, diesel, coal and wood.", "federal-7"],
        "hp": ["partial", "Ottawa does not say that an existing heat pump rules you out. It does say you get no rebate if federal money already paid for a heat pump at your address. Ask the program before you buy.", "federal-7"],
    },
    "own": {
        "own": ["said", "You can apply if you live in Canada and own the home. It does not have to be your main home, so a rental property you own counts. You get one rebate per household, even with several properties.", "federal-7"],
        "condo": ["partial", "You can apply if you own the home. Ottawa's page does not list condos or apartments separately, so ask the program, and ask your condo board about outdoor units.", "federal-7"],
        "rent": ["said", "You must own the home, so a tenant cannot apply for a heat pump in a rented home. Ottawa says rented or leased heat pumps may be eligible after launch, with details later. If you own a rental property, you can apply for it.", "federal-7"],
    },
    "state": {
        "broken": ["said", "Emergency installs count. You do not have to show your old system failed or remove it. Installs from November 1, 2026 can apply once the portal opens in early 2027, so keep every receipt and submit within 6 months.", "federal-1"],
        "ending": ["said", "Planned installs count too. Installs from November 1, 2026 can apply once the portal opens. If your system still works, our guide weighs the cost of waiting against what is open today.", "federal-1"],
        "fine": ["said", "You do not need a broken system. Planned installs count, and installs from November 1, 2026 can apply once the portal opens. If yours works, our guide weighs the cost of waiting.", "federal-1"],
    },
}

NOT_YET = ["Changes: Ottawa says the rules are still being finalized and can change, and uses the rules in force on your install date",
           "Anything installed before November 1, 2026 (the page does not mention it)",
           "Rented or leased heat pumps (may be eligible after launch, details later)",
           "The exact portal date (early 2027)",
           "How each provincial program stacks (Ottawa says it can be combined with provincial programs; each has its own rules)"]
SAID = [("$10,000 if your after-tax household income is at or below your province's line for your household size, $2,000 above it.", "federal-6"),
        ("You must live in Canada and own the home. A rental property you own counts. One rebate per household.", "federal-7"),
        ("Natural gas, oil, propane, electricity, diesel, coal and wood heat can all qualify.", "federal-7"),
        ("The heat pump must be on the eligible product list (by AHRI number), bought from and installed by an HVAC contractor, and heat the whole home.", "federal-7"),
        ("The portal opens in early 2027 and the program closes in March 2034. Installs from November 1, 2026 can apply once it opens.", "federal-1"),
        ("Send receipts within 6 months. No audit is needed before or after the install.", "federal-2"),
        ("The Canada Revenue Agency checks your income with your Social Insurance Number when you apply.", "federal-2"),
        ("It can be combined with provincial programs. Each program has its own stacking rules.", "federal-3")]

CSS = """<style>
.dq-form{display:grid;gap:14px;margin:18px 0;padding:20px;border:1px solid var(--card-rule);border-radius:var(--radius-card);background:#f6f0e6}
.dq-form label{display:block;margin:0 0 4px;font-weight:700;color:var(--ink)}
.dq-form small{display:block;margin-top:4px;color:var(--muted)}
.dq-form select,.dq-form input{width:100%;min-height:48px;padding:0 12px;font:inherit;font-size:16px;color:var(--ink);background:#fff;border:1px solid #b9ae9c;border-radius:8px}
.dq-form button{min-height:48px;padding:0 22px;font:inherit;font-weight:700;color:#fff;background:#a4540a;border:0;border-radius:8px;cursor:pointer}
.dq-form button:hover{background:#8a4607}
@media(min-width:720px){.dq-form{grid-template-columns:1fr 1fr}.dq-form .dq-wide{grid-column:1/-1}}
.dq-tablewrap{margin:16px 0;overflow-x:auto;border:1px solid var(--card-rule);border-radius:12px;background:#fff}
.dq-table{width:100%;min-width:560px;border-collapse:collapse;font-size:15px}
.dq-table th,.dq-table td{padding:10px 12px;text-align:right;border-bottom:1px solid var(--card-rule);white-space:nowrap}
.dq-table th[scope=row],.dq-table thead th:first-child{text-align:left;white-space:normal;position:sticky;left:0;background:#fff}
.dq-table thead th{background:#f6f0e6;font-size:14px}
.dq-table tr:last-child th,.dq-table tr:last-child td{border-bottom:0}
.dq-out{margin:22px 0}
.dq-out[hidden]{display:none}
.dq-verdict{padding:18px 20px;border-radius:var(--radius-card);color:var(--paper);background:linear-gradient(165deg,#0f5361,#08363f)}
.dq-verdict h2,.tpl-article .dq-verdict h2{margin:0 0 6px;color:var(--paper) !important;font-size:24px}
.dq-verdict p,.tpl-article .dq-verdict p{margin:0;color:var(--paper) !important;max-width:none}
.dq-verdict h2::before,.dq-verdict h2::after{display:none}
.dq-list{list-style:none;margin:16px 0;padding:0;display:grid;gap:10px}
.dq-list li{margin:0;padding:14px 16px;border:1px solid var(--card-rule);border-radius:12px;background:#fff}
.dq-chip{display:inline-block;margin:0 8px 6px 0;padding:2px 10px;font-size:13px;font-weight:700;border-radius:999px}
.dq-chip.said{color:#1b4332;background:#d8f3dc}.dq-chip.partial{color:#7a4a00;background:#ffe8c2}.dq-chip.notyet{color:#5b2a1f;background:#f6d7cf}
.dq-list p{margin:4px 0 0;max-width:none}
.dq-do a{font-weight:700}
</style>"""


def build():
    pl = prov_links()
    said = "".join(f"<li>{e(t)}</li>" for t, _ in SAID)
    notyet = "".join(f"<li>{e(t)}</li>" for t in NOT_YET)
    opts = "".join(f'<option value="{c}">{e(n)}</option>' for c, n in PROVS)
    data = json.dumps({"rules": RULES, "provs": pl, "thr": thresholds(), "notyet": NOT_YET,
                       "pages": {"gas": "/blog/heat-pump-natural-gas-home-federal-rebate/", "rent": "/blog/federal-heat-pump-rebate-renters-condos-landlords/",
                                 "wait": "/blog/should-you-wait-federal-heat-pump-rebate/", "stack": "/blog/federal-heat-pump-rebate-stacking-by-province/"}}, ensure_ascii=False).replace("</", "<\\/")
    th = thresholds()
    limits_table = ('<div class="dq-tablewrap" tabindex="0" role="region" aria-label="Income limits by province and household size"><table class="dq-table"><thead><tr><th scope="col">Province or territory</th>'
                    + "".join(f'<th scope="col">{h}</th>' for h in ("1 person", "2 people", "3 people", "4 people", "5 or more")) + "</tr></thead><tbody>"
                    + "".join(f'<tr><th scope="row">{e(n)}</th>' + "".join(f"<td>${v:,}</td>" for v in vals) + "</tr>" for n, vals in th.items()) + "</tbody></table></div>")
    article = f"""<p>Ottawa now says who gets the National Heat Pump Rebate who gets the National Heat Pump Rebate: <b>$10,000</b> if your after-tax household income is at or below your province's line for your household size, <b>$2,000</b> if it is above. Gas, oil, propane, electric and wood homes can all apply, and so can a rental property you own. Answer the questions below to see your tier. The portal opens in early 2027, and Ottawa says the rules can still change, so check the date we last read its page.</p>
<h2 id="check">Check your home</h2>
<form class="dq-form" id="dq-form">
<div><label for="dq-prov">Where is your home?</label><select id="dq-prov" required><option value="">Choose your province</option>{opts}</select></div>
<div><label for="dq-size">How many people live in the home?</label><select id="dq-size" required><option value="">Choose one</option><option value="0">1 person</option><option value="1">2 people</option><option value="2">3 people</option><option value="3">4 people</option><option value="4">5 or more people</option></select></div>
<div><label for="dq-inc">Your household's after-tax income, 2025</label><input id="dq-inc" type="number" inputmode="numeric" min="0" step="1" placeholder="For example 85000" required><small>Line 23600 minus line 43500 on your 2025 tax return, plus a partner's. We do not save or send it.</small></div>
<div><label for="dq-fuel">What heats your home now?</label><select id="dq-fuel" required><option value="">Choose one</option><option value="oil">Oil</option><option value="propane">Propane</option><option value="electric">Electric baseboards or electric furnace</option><option value="gas">Natural gas</option><option value="wood">Wood</option><option value="hp">I already have a heat pump</option></select></div>
<div><label for="dq-own">Do you own the home?</label><select id="dq-own" required><option value="">Choose one</option><option value="own">I own a house, semi, row home or mobile home</option><option value="condo">I own a condo or apartment</option><option value="rent">I rent</option></select></div>
<div><label for="dq-state">How is your heating system?</label><select id="dq-state" required><option value="">Choose one</option><option value="broken">It is broken or failing now</option><option value="ending">It is old and I am planning to replace it</option><option value="fine">It works fine</option></select></div>
<div class="dq-wide"><button type="submit">Check my rebate tier</button></div>
</form>
<div class="dq-out" id="dq-out" hidden aria-live="polite"></div>
<!-- FED-ALERT-HERE -->
<h2 id="limits">Income limits by province and household size</h2>
<p>Ottawa's table shows median after-tax household income in 2025 dollars (Statistics Canada 2021, adjusted for inflation). If your after-tax household income is equal to or less than the number for your province or territory and household size, the rebate is up to $10,000. Above it, $2,000. Add line 23600 minus line 43500 of your 2025 return, plus a spouse's or common-law partner's.</p>
{limits_table}
<p>Source: <a href="{CAMPAIGN}" rel="noopener" target="_blank">Government of Canada, National Heat Pump Rebate</a>. Saskatchewan's number for 5 or more people is lower than for 4 people as Ottawa posted it. The rules can still change.</p>
<h2 id="said">What Ottawa has said</h2>
<ul>{said}</ul>
<p>These points come from the Government of Canada's <a href="{CAMPAIGN}" rel="noopener" target="_blank">campaign page</a>, which we re-read in full on November 19, 2026, and the <a href="{RELEASE}" rel="noopener" target="_blank">October 8 news release</a>. The approval and payment timings in the release (24 hours and five days) are not repeated on the campaign page.</p>
<h2 id="not-said">What can still change or is not settled</h2>
<ul>{notyet}</ul>
<p>Ottawa says the program is still being finalized. We re-read its page often and update this one with the date, and we email the people on our launch list the day applications open.</p>
<h2 id="free-upgrades">A different federal program may already be open</h2>
<p>The Canada Greener Homes Affordability Program is separate. It gives free insulation and heat pump upgrades to homeowners and tenants with low to median incomes, and you apply through your province, not through Ottawa. NRCan's page lists British Columbia, Manitoba, Nova Scotia, Prince Edward Island and Quebec as taking applications (page updated August 31, 2026). Read the <a href="{GHAP}" rel="noopener" target="_blank">program page</a> for the steps in your province.</p>
<h2 id="faq">Common questions</h2>
{kit.faq({"faq": FAQ})}
<p style="font-size:14px;">By <a href="/author/sam-menard/">Sam Menard</a>. Sources, last read November 19, 2026: <a href="{RELEASE}" rel="noopener" target="_blank">Government of Canada news release</a>, <a href="{CAMPAIGN}" rel="noopener" target="_blank">campaign page</a>, <a href="{PM}" rel="noopener" target="_blank">Prime Minister's release</a>, <a href="{CBC}" rel="noopener" target="_blank">CBC</a>, <a href="{GHAP}" rel="noopener" target="_blank">NRCan</a>. We are an independent site, not the Government of Canada.</p>
<script>
(function () {{
  var D = {data}, form = document.getElementById('dq-form'), out = document.getElementById('dq-out');
  var CHIP = {{ said: 'Ottawa has said', partial: 'Ask first', notyet: 'Not published yet' }};
  function li(status, head, text, extra) {{ return '<li><span class="dq-chip ' + status + '">' + CHIP[status] + '</span><b>' + head + '</b><p>' + text + (extra || '') + '</p></li>'; }}
  form.addEventListener('submit', function (e) {{
    e.preventDefault();
    var p = document.getElementById('dq-prov').value, z = +document.getElementById('dq-size').value, inc = +document.getElementById('dq-inc').value,
        f = document.getElementById('dq-fuel').value, o = document.getElementById('dq-own').value, s = document.getElementById('dq-state').value, P = D.provs[p];
    var line = D.thr[P.name][z], high = inc <= line, R = D.rules, fmt = function (n) {{ return '$' + n.toLocaleString('en-CA'); }};
    var html = '<div class="dq-verdict"><h2>' + (high ? 'You are likely in the $10,000 tier' : 'You are likely in the $2,000 tier') + '</h2><p>' +
      (high ? 'Your income of ' + fmt(inc) + ' is at or below the ' + P.name + ' line of ' + fmt(line) + ' for your household size.' : 'Your income of ' + fmt(inc) + ' is above the ' + P.name + ' line of ' + fmt(line) + ' for your household size.') +
      ' The $10,000 is a maximum: the amount also depends on your equipment cost. Ottawa says its rules can still change.</p></div><ul class="dq-list">';
    html += li('said', 'Your amount', (high ? 'Up to $10,000' : '$2,000') + '. The Canada Revenue Agency checks your income with your Social Insurance Number when you apply. Your income is line 23600 minus line 43500 on your 2025 return, plus a partner\\'s. If your income is close to the line, check the table on <a href="{GUIDE}">our federal rebate guide</a>.');
    html += li(R.fuel[f][0], 'Your heating', R.fuel[f][1], f === 'gas' ? ' <a href="' + D.pages.gas + '">Read the gas home guide</a>.' : '');
    html += li(R.own[o][0], 'Who owns the home', R.own[o][1], o === 'rent' ? ' <a href="' + D.pages.rent + '">Read the guide for renters, condos and landlords</a>.' : '');
    html += li(R.state[s][0], 'Timing', R.state[s][1], (s === 'ending' || s === 'fine') ? ' <a href="' + D.pages.wait + '">Should you wait?</a>' : '');
    html += li('said', 'Stacking with ' + P.name + ' programs', 'Ottawa says the federal rebate can be combined with provincial programs. Each provincial program has its own rules.', ' <a href="' + D.pages.stack + '">See stacking by province</a>.');
    html += '</ul><h3>What you can do now in ' + P.name + '</h3><ul class="dq-do">';
    html += '<li>Check the eligible product list by AHRI number before you accept a quote, and ask for a written heat load calculation.</li>';
    if (P.hp) html += '<li><a href="' + P.hp + '">Rebates open today for a heat pump in ' + P.name + '</a></li>';
    if (P.calc) html += '<li><a href="' + P.calc + '">Add up every open rebate in ' + P.name + ' with the calculator</a></li>';
    if (P.ghap) html += '<li>' + P.name + ' is on NRCan\\'s list for the free Greener Homes Affordability upgrades (low to median income). <a href="{GHAP}" rel="noopener" target="_blank">Check the program page</a>.</li>';
    html += '<li>Join the launch alert below. We email you the day applications open.</li></ul>';
    out.innerHTML = html; out.hidden = false; out.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    if (window.gtag) window.gtag('event', 'fed_qualify_check', {{ page_path: location.pathname, province: p, fuel: f, tier: high ? '10000' : '2000' }});
  }});
}})();
</script>"""
    return article


FAQ = [("Do I qualify for the federal heat pump rebate?", "You qualify if you live in Canada, own the home (a rental property you own counts), and install a heat pump from the eligible product list through an HVAC contractor. Natural gas, oil, propane, electric, diesel, coal and wood homes can all apply."),
       ("How much is the rebate?", "$10,000 if your after-tax household income is at or below your province's line for your household size, and $2,000 if it is above. The amount also depends on your equipment cost."),
       ("How is my income checked?", "When you apply, you give your Social Insurance Number and the Canada Revenue Agency checks your household's after-tax income: line 23600 minus line 43500 on your 2025 return, plus a partner's."),
       ("When can I apply?", "The portal opens in early 2027. Join the alert on this page and we will email you the day applications open."),
       ("Can I get the rebate if I buy a heat pump now?", "Ottawa says installs from November 1, 2026 can apply once the portal opens. It says nothing about earlier installs. Keep your invoices and send receipts within 6 months."),
       ("Can I combine it with provincial rebates?", "Ottawa says it can be combined with provincial programs. Each program has its own rules, so check yours.")]


def main():
    article = build()
    trail = [("Home", "/"), ("Programs", "/programs/"), ("National Heat Pump Rebate", GUIDE), ("Do I qualify?", PATH)]
    lds = kit.ld_scripts([kit.article_ld(TITLE, DESC, "2026-11-20", PATH, published="2026-10-22"), kit.breadcrumb_ld(trail, home_slash=True), kit.faq_ld({"faq": FAQ})])
    hero = {"badge": "$10,000 or $2,000", "h1": "Federal Heat Pump Rebate Income Limits: Do I Qualify?",
            "lead": "Enter your province, household size and income to see your tier, then check your fuel, ownership and install date."}
    kit.write_page(PATH, TITLE, DESC, lds, navfooter.render_nav("", ""), kit.breadcrumb(trail), kit.hero(hero), None, article,
                   navfooter.render_footer("", "", "", PATH), extra_css=CSS)
    print("built", PATH)


if __name__ == "__main__":
    main()
