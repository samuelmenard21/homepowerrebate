#!/usr/bin/env python3
"""/programs/national-heat-pump-rebate/do-i-qualify/: "Do I qualify?" for the National Heat Pump Rebate, 2026-10-22.
Ottawa has not published the income line, home types or fuels, so no one can honestly say yes or no. The tool does the honest
version: five questions, then for each one what Ottawa has said, what it has not, and what to do now (open provincial programs,
the free Greener Homes Affordability upgrades where the province takes part), ending in the launch alert (FED-ALERT-HERE).
Every statement comes from data/verified-facts/federal.json (federal-0 to federal-4) or its sources; the rules below carry the fact id.
When Ottawa publishes the income line, home types or fuels: change the matching rule's status and text, the NOT_YET list and the
facts, then rerun this script and scripts/post_steps.py. Never state gas-home eligibility, retroactivity or the income line before then.
Usage: python3 scripts/build_federal_qualify.py && python3 scripts/post_steps.py"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import page_kit as kit  # noqa: E402

e = html.escape
PATH = "/programs/national-heat-pump-rebate/do-i-qualify/"
GUIDE = "/programs/national-heat-pump-rebate/"
TITLE = "Federal Heat Pump Rebate: Do I Qualify? What Ottawa Has Said"
DESC = "Check your home against what Ottawa has published about the $10,000 and $2,000 heat pump rebate. What is known, what is not, and what to do now."
RELEASE = "https://www.canada.ca/en/environment-climate-change/news/2026/10/prime-minister-carney-announces-landmark-investment-to-retrofit-one-million-homes-cutting-energy-costs-and-emissions.html"
CAMPAIGN = "https://www.canada.ca/en/environment-climate-change/campaigns/one-million-home-energy-retrofits.html"
PM = "https://www.pm.gc.ca/en/news/news-releases/2026/10/08/prime-minister-carney-announces-landmark-investment-retrofit-one"
CBC = "https://www.cbc.ca/news/canada/canada-heat-pump-retrofit-faq-9.7374613"
GHAP = "https://natural-resources.canada.ca/energy-efficiency/home-energy-efficiency/canada-greener-homes-initiative/canada-greener-homes-affordability-program"
FACTS = ["federal-0-national-heat-pump-rebate", "federal-1-launch-and-retroactivity", "federal-2-how-it-works", "federal-3-stacking", "federal-4-greener-homes-affordability"]

PROVS = [("bc", "British Columbia"), ("on", "Ontario"), ("ab", "Alberta"), ("sk", "Saskatchewan"), ("mb", "Manitoba"), ("qc", "Quebec"),
         ("nb", "New Brunswick"), ("ns", "Nova Scotia"), ("pe", "Prince Edward Island"), ("nl", "Newfoundland and Labrador"),
         ("yt", "Yukon"), ("nt", "Northwest Territories")]
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


# what Ottawa has said / not said, by answer. status: said | partial | notyet
RULES = {
    "fuel": {
        "oil": ["partial", "Ottawa's own savings example is about homes like yours: it says homes that use oil, propane or electric resistance heat save more than $1,400 a year on average. It has not said which heating fuels qualify for the rebate, so this is not a yes.", "federal-0"],
        "propane": ["partial", "Ottawa's own savings example is about homes like yours: it says homes that use oil, propane or electric resistance heat save more than $1,400 a year on average. It has not said which heating fuels qualify for the rebate, so this is not a yes.", "federal-0"],
        "electric": ["partial", "Ottawa's own savings example is about homes like yours: it says homes that use oil, propane or electric resistance heat save more than $1,400 a year on average. It has not said which heating fuels qualify for the rebate, so this is not a yes.", "federal-0"],
        "gas": ["notyet", "Ottawa has not said whether homes that heat with natural gas can claim the rebate. We will not guess. Our guide to gas homes lists what is known.", "federal-0"],
        "wood": ["notyet", "Ottawa has not said which heating fuels qualify, and wood is not mentioned in what it published.", "federal-0"],
        "hp": ["notyet", "Ottawa has not said whether a home that already has a heat pump can claim. It does say there is one rebate per person.", "federal-0"],
    },
    "own": {
        "own": ["notyet", "Ottawa has not published which home types qualify, so we cannot say yes for any house, semi, row home or mobile home. It does say there is one rebate per person.", "federal-0"],
        "condo": ["notyet", "Ottawa has not published which home types qualify. Condo owners often need board approval for outdoor units, which is worth asking about now.", "federal-0"],
        "rent": ["notyet", "Ottawa has not said whether tenants, or landlords for rental units, can claim. A separate part of the plan is for building owners (mortgage insurance and financing for apartment retrofits).", "federal-5"],
    },
    "state": {
        "broken": ["said", "Ottawa says the process is built for the moment a heating system breaks or nears the end of its life: apply in an online portal, get approval within 24 hours, then buy and install a pre-approved heat pump and upload the receipts. The portal is not open yet. Ottawa says its retroactivity period starts on November 1, 2026, so a heat pump installed from that date can apply once the portal opens. It has said nothing about installs before November 1. If you must replace before then, keep every invoice and do not count on the rebate.", "federal-2"],
        "ending": ["said", "Ottawa says the process is built for homes whose heating system is breaking or near the end of its life. If yours is old but working, our guide on whether to wait weighs the cost of waiting against what is open today.", "federal-2"],
        "fine": ["partial", "Ottawa describes the rebate around systems that break or near end of life, and says 80 per cent of heating replacements happen when the system breaks (as reported by CBC from a government document). It has not said whether a working system can qualify.", "federal-2"],
    },
}

NOT_YET = ["The income line that decides $10,000 or $2,000", "Which home types qualify (houses, semis, row homes, condos, mobile homes, rentals)", "Which heating fuels qualify, including natural gas",
           "The exact launch date (Ottawa says early 2027)", "Whether anything installed before November 1, 2026 counts (Ottawa says its retroactivity period starts on that date)", "Which provincial programs allow stacking, and how (Ottawa says it can be combined with provincial programs)"]
SAID = [("Up to $10,000 for households below the median income and $2,000 for other eligible homeowners.", "federal-0"),
        ("One rebate per person.", "federal-0"),
        ("The heat pump must be on the Eligible Products List (over 100,000 options).", "federal-0"),
        ("Launch is expected in early 2027. It was announced on October 8, 2026.", "federal-0"),
        ("The retroactivity period starts on November 1, 2026: eligible heat pumps installed from that date can apply once the portal opens. Ottawa says full details will be published as of November 1, 2026.", "federal-1"),
        ("It can be combined with provincial programs. Each program has its own stacking rules, which we have not read against this one.", "federal-3"),
        ("Apply online, get approval within 24 hours, buy and install, upload receipts, payment within five days by direct deposit, and no energy audit before or after (as reported by CBC from the government document).", "federal-2")]

CSS = """<style>
.dq-form{display:grid;gap:14px;margin:18px 0;padding:20px;border:1px solid var(--card-rule);border-radius:var(--radius-card);background:#f6f0e6}
.dq-form label{display:block;margin:0 0 4px;font-weight:700;color:var(--ink)}
.dq-form select{width:100%;min-height:48px;padding:0 12px;font:inherit;font-size:16px;color:var(--ink);background:#fff;border:1px solid #b9ae9c;border-radius:8px}
.dq-form button{min-height:48px;padding:0 22px;font:inherit;font-weight:700;color:#fff;background:#a4540a;border:0;border-radius:8px;cursor:pointer}
.dq-form button:hover{background:#8a4607}
@media(min-width:720px){.dq-form{grid-template-columns:1fr 1fr}.dq-form .dq-wide{grid-column:1/-1}}
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
    data = json.dumps({"rules": RULES, "provs": pl, "notyet": NOT_YET,
                       "pages": {"gas": "/blog/heat-pump-natural-gas-home-federal-rebate/", "rent": "/blog/federal-heat-pump-rebate-renters-condos-landlords/",
                                 "wait": "/blog/should-you-wait-federal-heat-pump-rebate/", "stack": "/blog/federal-heat-pump-rebate-stacking-by-province/"}}, ensure_ascii=False).replace("</", "<\\/")
    article = f"""<p>You want to know if you can get the new federal heat pump rebate. The honest answer today is that nobody can say yes or no yet. Ottawa announced the rebate on October 8, 2026, but it has not published the income line, the home types or the heating fuels that qualify. This page tells you, for your own home, what Ottawa has said, what it has not said, and what you can do now.</p>
<h2 id="check">Check your home</h2>
<form class="dq-form" id="dq-form">
<div><label for="dq-prov">Where is your home?</label><select id="dq-prov" required><option value="">Choose your province</option>{opts}</select></div>
<div><label for="dq-fuel">What heats your home now?</label><select id="dq-fuel" required><option value="">Choose one</option><option value="oil">Oil</option><option value="propane">Propane</option><option value="electric">Electric baseboards or electric furnace</option><option value="gas">Natural gas</option><option value="wood">Wood</option><option value="hp">I already have a heat pump</option></select></div>
<div><label for="dq-own">Do you own the home?</label><select id="dq-own" required><option value="">Choose one</option><option value="own">I own a house, semi, row home or mobile home</option><option value="condo">I own a condo or apartment</option><option value="rent">I rent</option></select></div>
<div><label for="dq-state">How is your heating system?</label><select id="dq-state" required><option value="">Choose one</option><option value="broken">It is broken or failing now</option><option value="ending">It is old and I am planning to replace it</option><option value="fine">It works fine</option></select></div>
<div class="dq-wide"><button type="submit">Show what Ottawa has said about my home</button></div>
</form>
<div class="dq-out" id="dq-out" hidden aria-live="polite"></div>
<!-- FED-ALERT-HERE -->
<h2 id="said">What Ottawa has said</h2>
<ul>{said}</ul>
<p>The first four points are on the government's own pages: the <a href="{RELEASE}" rel="noopener" target="_blank">October 8 news release</a>, its <a href="{CAMPAIGN}" rel="noopener" target="_blank">campaign page</a> and the <a href="{PM}" rel="noopener" target="_blank">Prime Minister's release</a>. The application steps come from <a href="{CBC}" rel="noopener" target="_blank">CBC's reading of the government document</a>.</p>
<h2 id="not-said">What Ottawa has not said yet</h2>
<ul>{notyet}</ul>
<p>Until these are published, any site that tells you that you qualify, or that you do not, is guessing. We update this page when Ottawa publishes each one, and we email the people on our launch list the same day.</p>
<h2 id="free-upgrades">A different federal program may already be open</h2>
<p>The Canada Greener Homes Affordability Program is separate. It gives free insulation and heat pump upgrades to homeowners and tenants with low to median incomes, and you apply through your province, not through Ottawa. NRCan's page lists British Columbia, Manitoba, Nova Scotia, Prince Edward Island and Quebec as taking applications (page updated August 31, 2026). Read the <a href="{GHAP}" rel="noopener" target="_blank">program page</a> for the steps in your province.</p>
<h2 id="faq">Common questions</h2>
{kit.faq({"faq": FAQ})}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read October 9, 2026: <a href="{RELEASE}" rel="noopener" target="_blank">Government of Canada news release</a>, <a href="{CAMPAIGN}" rel="noopener" target="_blank">campaign page</a>, <a href="{PM}" rel="noopener" target="_blank">Prime Minister's release</a>, <a href="{CBC}" rel="noopener" target="_blank">CBC</a>, <a href="{GHAP}" rel="noopener" target="_blank">NRCan</a>. We are an independent site, not the Government of Canada.</p>
<script>
(function () {{
  var D = {data}, form = document.getElementById('dq-form'), out = document.getElementById('dq-out');
  var CHIP = {{ said: 'Ottawa has said', partial: 'Partly said', notyet: 'Not published yet' }};
  function li(status, head, text, extra) {{ return '<li><span class="dq-chip ' + status + '">' + CHIP[status] + '</span><b>' + head + '</b><p>' + text + (extra || '') + '</p></li>'; }}
  form.addEventListener('submit', function (e) {{
    e.preventDefault();
    var p = document.getElementById('dq-prov').value, f = document.getElementById('dq-fuel').value, o = document.getElementById('dq-own').value, s = document.getElementById('dq-state').value, P = D.provs[p], R = D.rules;
    var html = '<div class="dq-verdict"><h2>We cannot say yes or no yet, and nor can anyone else</h2><p>Ottawa has not published who qualifies. Here is what it has said about your home, and what to do now.</p></div><ul class="dq-list">';
    html += li('notyet', 'Which amount: $10,000 or $2,000', 'Ottawa says up to $10,000 for households below the median income and $2,000 for other eligible homeowners. It has not published the income line, so we cannot tell you which one you would get.');
    html += li(R.fuel[f][0], 'Your heating', R.fuel[f][1], f === 'gas' ? ' <a href="' + D.pages.gas + '">Read the gas home guide</a>.' : '');
    html += li(R.own[o][0], 'Your home and who owns it', R.own[o][1], o === 'rent' ? ' <a href="' + D.pages.rent + '">Read the guide for renters, condos and landlords</a>.' : '');
    html += li(R.state[s][0], 'Timing', R.state[s][1], (s === 'ending' || s === 'fine') ? ' <a href="' + D.pages.wait + '">Should you wait?</a>' : '');
    html += li('said', 'Stacking with ' + P.name + ' programs', 'Ottawa says the federal rebate can be combined with provincial programs. Each provincial program has its own rules, which we have not read against this one.', ' <a href="' + D.pages.stack + '">See stacking by province</a>.');
    html += '</ul><h3>What you can do now in ' + P.name + '</h3><ul class="dq-do">';
    if (P.hp) html += '<li><a href="' + P.hp + '">Rebates open today for a heat pump in ' + P.name + '</a></li>';
    if (P.calc) html += '<li><a href="' + P.calc + '">Add up every open rebate in ' + P.name + ' with the calculator</a></li>';
    if (P.ghap) html += '<li>' + P.name + ' is on NRCan\\'s list for the free Greener Homes Affordability upgrades (low to median income). <a href="{GHAP}" rel="noopener" target="_blank">Check the program page</a>.</li>';
    html += '<li>Join the launch alert below. We email you the day applications open.</li></ul>';
    out.innerHTML = html; out.hidden = false; out.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    if (window.gtag) window.gtag('event', 'fed_qualify_check', {{ page_path: location.pathname, province: p, fuel: f }});
  }});
}})();
</script>"""
    return article


FAQ = [("Do I qualify for the federal heat pump rebate?", "Ottawa has not published the income line, home types or heating fuels that qualify, so no one can say yes or no yet. This page shows what is known for your home."),
       ("How much is the rebate?", "Up to $10,000 for households below the median income and $2,000 for other eligible homeowners. Ottawa has not said where the income line falls."),
       ("When can I apply?", "Ottawa expects to launch in early 2027. Applications are not open. Join the alert on this page and we will email you the day they open."),
       ("Can I get the rebate if I buy a heat pump now?", "Ottawa says installs from November 1, 2026 can apply once the portal opens in early 2027. It has said nothing about earlier installs. Keep your invoices."),
       ("Can I combine it with provincial rebates?", "Ottawa says it can be combined with provincial programs. Each program has its own rules, so check yours.")]


def main():
    article = build()
    trail = [("Home", "/"), ("Programs", "/programs/"), ("National Heat Pump Rebate", GUIDE), ("Do I qualify?", PATH)]
    lds = kit.ld_scripts([kit.article_ld(TITLE, DESC, "2026-10-22", PATH), kit.breadcrumb_ld(trail, home_slash=True), kit.faq_ld({"faq": FAQ})])
    hero = {"badge": "Early 2027 launch", "h1": "Do I Qualify for the Federal Heat Pump Rebate?",
            "lead": "Ottawa has not said who qualifies yet. Check your home to see what it has said, what it has not, and what to do now."}
    kit.write_page(PATH, TITLE, DESC, lds, navfooter.render_nav("", ""), kit.breadcrumb(trail), kit.hero(hero), None, article,
                   navfooter.render_footer("", "", "", PATH), extra_css=CSS)
    print("built", PATH)


if __name__ == "__main__":
    main()
