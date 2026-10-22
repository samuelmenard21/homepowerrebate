#!/usr/bin/env python3
"""Partner kit for the federal heat pump rebate launch, 2026-10-22: for installers, energy advisors, realtors, credit unions, community groups.
Three pages, one source (the federal-* facts in data/verified-facts/federal.json and the open heat pump programs in calculator/data/<code>.json):
  /embed/federal-heat-pump-rebate/                      noindex, framed by partners: what Ottawa has said, the launch alert, a link to the "Do I qualify?" tool.
  /partners/federal-heat-pump-rebate/sheet/             noindex, printable one-pager the partner brands with their own name and contact line, plus the open
                                                        heat pump rebates for the province they pick. Branding is typed in the browser and kept in the link
                                                        (?name=&phone=&email=&site=&prov=); nothing is sent to us or stored.
  /partners/federal-heat-pump-rebate/                   indexable how-to page: copy-paste embed code, sheet link builder, email blurb, attribution.
Attribution: the embed and the kit link carry ?p=<partner>, and signups are stored with page "...?src=partner-<p>" so federal_alert_report.py shows which
partner sends signups. Everything states only what Ottawa has published; the page is re-read when Ottawa publishes rules (see build_federal_qualify.py).
When launch details are published: update the SAID / NOT_YET lists here and in build_federal_qualify.py, rerun both, then scripts/post_steps.py.
Usage: python3 scripts/build_federal_partner_kit.py && python3 scripts/post_steps.py"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_rebate_sheets as sheets  # noqa: E402
import page_kit as kit  # noqa: E402

e = html.escape
BASE = "https://homepowerrebate.com"
KIT = "/partners/federal-heat-pump-rebate/"
SHEET = KIT + "sheet/"
EMBED = "/embed/federal-heat-pump-rebate/"
QUALIFY = "/programs/national-heat-pump-rebate/do-i-qualify/"
GUIDE = "/programs/national-heat-pump-rebate/"
RELEASE = "https://www.canada.ca/en/environment-climate-change/news/2026/10/prime-minister-carney-announces-landmark-investment-to-retrofit-one-million-homes-cutting-energy-costs-and-emissions.html"
CHECKED = "October 9, 2026"   # when federal-0 to federal-3 were last read (verified_on)
PROVS = [("bc", "British Columbia"), ("on", "Ontario"), ("ab", "Alberta"), ("sk", "Saskatchewan"), ("mb", "Manitoba"), ("qc", "Quebec"), ("nb", "New Brunswick"),
         ("ns", "Nova Scotia"), ("pe", "Prince Edward Island"), ("nl", "Newfoundland and Labrador"), ("yt", "Yukon"), ("nt", "Northwest Territories")]

SAID = ["Up to $10,000 for households below the median income, and $2,000 for other eligible homeowners.",
        "Applications are expected to open in early 2027. They are not open yet.",
        "One rebate per person, and the heat pump must be on the Eligible Products List.",
        "It can be combined with provincial programs. Each program has its own rules."]
NOT_YET = ["The income line that decides $10,000 or $2,000", "Which home types and heating fuels qualify, including natural gas", "The exact launch date, and whether purchases made before launch count"]
STEPS = "Ottawa's plan, as reported by CBC from the government document: apply in an online portal, get approval within 24 hours, buy and install an approved heat pump, upload receipts, payment within five days. No energy audit before or after."


def province_data():
    out = {}
    for code, name in PROVS:
        f = ROOT / "calculator" / "data" / f"{code}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        items = []
        for p in d["programs"]:
            if p.get("upgrade") != "heat-pump" or p.get("status") != "active" or p["id"].startswith("fed-"):
                continue
            amt = sheets.amount_text(p.get("amount") or {}, d.get("currency", "CAD"))
            if not amt:
                continue
            items.append({"n": p["name"], "a": amt, "r": (p.get("rules") or "").split(". ")[0].rstrip(".") + ".", "s": p.get("source_url", "")})
        out[code] = {"name": name, "v": d.get("verified_on", ""), "items": items}
    return out


# ------------------------------------------------------------------ embed (standalone page, framed on partner sites)
def embed_page():
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Federal heat pump rebate</title><meta name="robots" content="noindex, follow"><link rel="canonical" href="{BASE}{GUIDE}">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Inter+Tight:wght@400;600;700&display=swap" rel="stylesheet">
<style>
body{{margin:0;padding:10px;font-family:'Inter Tight',system-ui,sans-serif;color:#0a2a2e;background:transparent}}
.fe{{max-width:560px;margin:0 auto;padding:18px;background:#faf7f2;border:1px solid #d9d0c1;border-radius:14px}}
.fe-badge{{display:inline-block;padding:3px 10px;font-size:12px;font-weight:700;color:#7a4a00;background:#ffe8c2;border-radius:999px}}
.fe h1{{margin:8px 0 6px;font:600 24px/1.15 'Fraunces',Georgia,serif}}
.fe p{{margin:0 0 10px;font-size:15px;line-height:1.5}}
.fe ul{{margin:0 0 12px;padding-left:20px;font-size:15px;line-height:1.5}}.fe li{{margin:0 0 4px}}
.fe b.amt{{font-family:'Fraunces',Georgia,serif;color:#2d6a4f}}
.fe form{{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 6px}}
.fe input[type=email]{{flex:1 1 200px;min-width:0;min-height:44px;padding:0 12px;font:inherit;font-size:16px;border:1px solid #b9ae9c;border-radius:8px}}
.fe button{{min-height:44px;padding:0 18px;font:inherit;font-weight:700;color:#fff;background:#a4540a;border:0;border-radius:8px;cursor:pointer}}
.fe .hp{{position:absolute;left:-9999px}}.fe .msg{{font-weight:700;margin:6px 0}}
.fe a{{color:#0d4f5c;font-weight:600}}.fe .by{{margin:12px 0 0;font-size:13px;text-align:center}}
</style></head><body>
<div class="fe"><span class="fe-badge">Opens early 2027</span>
<h1>Ottawa's new heat pump rebate</h1>
<p><b class="amt">Up to $10,000</b> for households below the median income. <b class="amt">$2,000</b> for other eligible homeowners.</p>
<ul>{"".join(f"<li>{e(t)}</li>" for t in SAID[1:])}</ul>
<p><a id="q" href="{BASE}{QUALIFY}" target="_blank" rel="noopener">Check what Ottawa has said about your home</a></p>
<form id="f"><label for="em" style="position:absolute;left:-9999px">Email</label><input id="em" type="email" required autocomplete="email" placeholder="Your email"><input class="hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true"><button type="submit">Email me when it opens</button></form>
<p class="msg" id="m" hidden></p>
<p style="font-size:13px;color:#4a5d60;margin:0">One email the day applications open and one when Ottawa says who gets $10,000. No spam. Unsubscribe anytime.</p>
<p class="by"><a href="{BASE}{GUIDE}" target="_blank" rel="noopener">Federal heat pump rebate guide by HomePowerRebate</a></p></div>
<script>
(function () {{
  var p = (new URLSearchParams(location.search).get('p') || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 30), src = p ? 'partner-' + p : 'embed';
  document.getElementById('q').href += '?src=' + src;
  var f = document.getElementById('f'), m = document.getElementById('m');
  f.addEventListener('submit', function (ev) {{
    ev.preventDefault(); var b = f.querySelector('button'); b.disabled = true;
    fetch('https://leads.homepowerrebate.com/alert', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({{ list: 'federal-hp', email: document.getElementById('em').value, province: '', city: '', page: '{EMBED}?src=' + src, website: f.querySelector('.hp').value }}) }})
      .then(function (r) {{ if (!r.ok) throw 0; f.hidden = true; m.hidden = false; m.textContent = "You're on the list! Check your inbox for a short note from us."; }})
      .catch(function () {{ b.disabled = false; m.hidden = false; m.textContent = 'That did not go through. Please try again.'; }});
  }});
  function h() {{ parent.postMessage({{ hprFedHeight: document.documentElement.scrollHeight }}, '*'); }}
  new ResizeObserver(h).observe(document.body); h();
}})();
</script></body></html>"""


# ------------------------------------------------------------------ co-branded sheet
SHEET_CSS = """<style>
.ps{max-width:860px;margin:0 auto;padding:24px 16px 56px;color:var(--ink)}
.ps-tools{display:grid;gap:10px;margin:0 0 18px;padding:16px;background:var(--paper-warm);border:1px solid var(--card-rule);border-radius:12px}
.ps-tools label{display:block;margin:0 0 3px;font-weight:700;font-size:14px}
.ps-tools input,.ps-tools select{width:100%;box-sizing:border-box;min-height:44px;padding:0 10px;font:inherit;font-size:16px;border:1px solid #b9ae9c;border-radius:8px;background:#fff}
.ps-tools button{min-height:46px;padding:0 20px;border:0;border-radius:10px;background:var(--teal-deep);color:#fff;font:inherit;font-weight:700;cursor:pointer}
@media(min-width:640px){.ps-tools{grid-template-columns:1fr 1fr}.ps-tools .wide{grid-column:1/-1}}
.ps-sheet{background:#fff;border:1px solid var(--card-rule);border-radius:14px;padding:26px 24px}
.ps-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;border-bottom:3px solid var(--amber);padding-bottom:12px;margin-bottom:14px}
.ps .ps-head h2{font-family:'Fraunces',Georgia,serif;font-size:27px;line-height:1.15;margin:0;color:var(--ink);text-transform:none;letter-spacing:0}
.ps-head p{margin:4px 0 0;font-size:14px;color:var(--ink-soft)}
.ps-by{text-align:right;font-size:13.5px;line-height:1.4;min-width:150px}.ps-by b{display:block;font-size:16px}
.ps h2{font-size:15px;margin:16px 0 6px;color:var(--teal-deep);text-transform:uppercase;letter-spacing:.04em}
.ps-amts{display:grid;gap:10px;margin:10px 0}
@media(min-width:560px){.ps-amts{grid-template-columns:1fr 1fr}}
.ps-amt{padding:12px 14px;background:#fff7ea;border-left:4px solid var(--amber);border-radius:6px}
.ps-amt b{display:block;font-family:'Fraunces',Georgia,serif;font-size:26px;color:var(--green-money)}
.ps ul{margin:6px 0;padding-left:20px;font-size:14.5px;line-height:1.5}
.ps table{width:100%;border-collapse:collapse;font-size:14px}.ps td{border-top:1px solid var(--card-rule);padding:7px 6px;vertical-align:top}
.ps td.amt{font-weight:700;white-space:nowrap;width:1%}.ps .rule{display:block;color:var(--ink-soft);font-size:12.5px;margin-top:2px}
.ps-small{font-size:12px;color:var(--ink-soft)}
@media(max-width:560px){.ps-head{flex-direction:column}.ps-by{text-align:left}}
@media print{
  body{background:#fff!important}
  .nav,.site-footer,footer,.ps-tools,.hpr-breadcrumb,.skip-link,#sticky-cta,.sticky-cta,.fed-alert,.fed-bar,[class*="newsletter"]{display:none!important}
  .ps{padding:0;max-width:none}.ps-sheet{border:0;padding:0}
  .ps ul{font-size:12px}.ps table{font-size:11.5px}.ps td{padding:4px 5px}.ps h2{font-size:12.5px;margin:10px 0 3px}.ps .ps-head h2{font-size:22px}.ps-amt b{font-size:22px}
  a{color:inherit;text-decoration:none}@page{margin:12mm}
}
</style>"""


def sheet_article(pdata):
    opts = "".join(f'<option value="{c}">{e(n)}</option>' for c, n in PROVS if c in pdata)
    data = json.dumps(pdata, ensure_ascii=False).replace("</", "<\\/")
    said = "".join(f"<li>{e(t)}</li>" for t in SAID)
    notyet = "".join(f"<li>{e(t)}</li>" for t in NOT_YET)
    return f"""<div class="ps">
<form class="ps-tools" id="ps-form" onsubmit="return false">
<div class="wide"><b>Make it yours.</b> Type your business details and pick a province. They stay in your browser and in this page's link, so you can bookmark it. Then print or save as a PDF.</div>
<div><label for="ps-name">Your business or name</label><input id="ps-name" autocomplete="organization" maxlength="60"></div>
<div><label for="ps-phone">Phone</label><input id="ps-phone" autocomplete="tel" maxlength="30"></div>
<div><label for="ps-email">Email</label><input id="ps-email" autocomplete="email" maxlength="60"></div>
<div><label for="ps-site">Website</label><input id="ps-site" maxlength="60" placeholder="yourbusiness.ca"></div>
<div class="wide"><label for="ps-prov">Province for the "open today" list</label><select id="ps-prov"><option value="">Choose a province</option>{opts}</select></div>
<div class="wide"><button type="button" onclick="window.print()">Print or save as PDF</button></div>
</form>
<article class="ps-sheet">
<div class="ps-head"><div><h2>The federal heat pump rebate: what we know</h2><p>Information checked {CHECKED}. Applications are not open yet.</p></div>
<div class="ps-by" id="ps-by" hidden><span class="ps-small">Prepared for you by</span><b id="o-name"></b><span id="o-phone"></span><br><span id="o-email"></span><br><span id="o-site"></span></div></div>
<div class="ps-amts"><div class="ps-amt"><b>Up to $10,000</b>Households below the median income</div><div class="ps-amt"><b>$2,000</b>Other eligible homeowners</div></div>
<h2>What Ottawa has said</h2><ul>{said}</ul>
<p class="ps-small">{e(STEPS)}</p>
<h2>What Ottawa has not said yet</h2><ul>{notyet}</ul>
<h2 id="o-prov-h">Open today for a heat pump</h2>
<div id="o-prov"><p class="ps-small">Pick a province above to list the heat pump rebates that are open today there.</p></div>
<h2>What to do now</h2><ul><li>Find out what heats your home today and what your heat pump options are.</li><li>If your system fails before launch, keep every invoice. Ottawa has not said whether earlier purchases count, so do not count on the rebate.</li><li>Get the launch alert and check your home at homepowerrebate.com{QUALIFY}</li></ul>
<p class="ps-small">Independent information from HomePowerRebate (homepowerrebate.com{GUIDE}). This is not from the Government of Canada: check canada.ca for official news. Amounts are the most a program pays; your amount depends on your home, utility and income.</p>
<p class="ps-small" id="o-foot" hidden></p>
</article></div>
<script>
(function () {{
  var D = {data}, q = new URLSearchParams(location.search), ids = {{ name: 'ps-name', phone: 'ps-phone', email: 'ps-email', site: 'ps-site', prov: 'ps-prov' }};
  Object.keys(ids).forEach(function (k) {{ var el = document.getElementById(ids[k]); if (q.get(k)) el.value = q.get(k).slice(0, 60); el.addEventListener('input', draw); el.addEventListener('change', draw); }});
  function v(k) {{ return document.getElementById(ids[k]).value.trim(); }}
  function t(id, s) {{ var el = document.getElementById(id); el.textContent = s; el.style.display = s ? '' : 'none'; }}
  function draw() {{
    t('o-name', v('name')); t('o-phone', v('phone')); t('o-email', v('email')); t('o-site', v('site'));
    var any = v('name') || v('phone') || v('email') || v('site');
    document.getElementById('ps-by').hidden = !any;
    var foot = document.getElementById('o-foot'); foot.hidden = !v('name'); foot.textContent = v('name') ? 'Prepared for you by ' + v('name') + [v('phone'), v('email'), v('site')].filter(Boolean).map(function (s) {{ return ' | ' + s; }}).join('') + '.' : '';
    var box = document.getElementById('o-prov'), P = D[v('prov')];
    box.textContent = '';
    if (!P) {{ var n = document.createElement('p'); n.className = 'ps-small'; n.textContent = 'Pick a province above to list the heat pump rebates that are open today there.'; box.appendChild(n); }}
    else {{
      document.getElementById('o-prov-h').textContent = 'Open today for a heat pump in ' + P.name;
      var tb = document.createElement('table');
      P.items.forEach(function (it) {{
        var tr = tb.insertRow(), a = tr.insertCell(), b = tr.insertCell(); b.className = 'amt'; b.textContent = it.a;
        a.appendChild(document.createTextNode(it.n)); var r = document.createElement('span'); r.className = 'rule'; r.textContent = it.r; a.appendChild(r);
      }});
      box.appendChild(tb);
      var n2 = document.createElement('p'); n2.className = 'ps-small'; n2.textContent = 'Rules checked ' + P.v + '. Your utility and income decide which apply. The full list with sources is at homepowerrebate.com/calculator/' + v('prov') + '/.'; box.appendChild(n2);
    }}
    var u = new URLSearchParams(); Object.keys(ids).forEach(function (k) {{ if (v(k)) u.set(k, v(k)); }});
    try {{ history.replaceState(null, '', location.pathname + (u.toString() ? '?' + u.toString() : '')); }} catch (e) {{}}
  }}
  draw();
}})();
</script>"""


# ------------------------------------------------------------------ kit page
def kit_article():
    snippet = (f'<iframe src="{BASE}{EMBED}?p=YOUR-NAME" title="Federal heat pump rebate" width="100%" height="560" '
               'style="max-width:580px;border:0;" loading="lazy"></iframe>\n'
               f'<p><a href="{BASE}{GUIDE}">Federal heat pump rebate guide by HomePowerRebate</a></p>')
    blurb = ("Ottawa has announced a new heat pump rebate: up to $10,000 for households below the median income and $2,000 for other eligible homeowners, "
             "with applications expected to open in early 2027. The income line, home types and fuels that qualify have not been published yet. "
             f"If you are thinking about a heat pump, you can check what Ottawa has said about your home and get one email the day applications open at {BASE}{QUALIFY}?src=partner-YOUR-NAME")
    return f"""<p>Ottawa announced a new heat pump rebate on October 8, 2026. Your customers, members and clients will ask about it. This kit gives you something accurate to hand them, with your name on it, and it changes by itself when Ottawa publishes the rules. Everything is free to use.</p>
<h2 id="embed">1. Add the rebate card to your website</h2>
<p>A small card that says what Ottawa has published, links to our "Do I qualify?" tool and lets visitors sign up for the launch email. Paste this into an HTML block. Replace <code>YOUR-NAME</code> with your business name in letters, numbers and dashes.</p>
<p><label for="k-p"><b>Your business name</b></label><br><input id="k-p" style="min-height:44px;font:inherit;font-size:16px;padding:8px 12px;border:1px solid #b9ae9c;border-radius:8px;width:min(320px,100%);margin:6px 0 10px" placeholder="Smith Heating" maxlength="40"></p>
<pre id="k-code" style="background:#0a2a2e;color:#fff;padding:14px;border-radius:8px;overflow-x:auto;white-space:pre-wrap;">{e(snippet)}</pre>
<p><button type="button" id="k-copy" style="min-height:44px;font:inherit;font-weight:700;padding:10px 20px;color:#fff;background:#a4540a;border:0;border-radius:8px;cursor:pointer">Copy code</button> <span id="k-done" role="status"></span></p>
<h3>Preview</h3>
<iframe id="k-prev" src="{EMBED}" title="Federal heat pump rebate preview" width="100%" height="560" style="max-width:580px;border:1px solid #d9d0c1;border-radius:12px;" loading="lazy"></iframe>
<h2 id="sheet">2. Print a one-page sheet with your name on it</h2>
<p>A single page you can print or save as a PDF. It shows what Ottawa has said and has not said, and lists the heat pump rebates that are open today in your province. Type your business name and contact details into the sheet. They stay in your browser; nothing is sent to us.</p>
<p><a class="btn" href="{SHEET}"><b>Make my sheet</b></a></p>
<h2 id="email">3. Send it in your newsletter or email</h2>
<p>Copy and paste this. It states only what Ottawa has published.</p>
<blockquote id="k-blurb" style="margin:0 0 12px;padding:12px 16px;background:#f5efe5;border-left:4px solid #d4751c;border-radius:6px">{e(blurb)}</blockquote>
<p><button type="button" id="k-copy2" style="min-height:44px;font:inherit;font-weight:700;padding:10px 20px;color:#fff;background:#a4540a;border:0;border-radius:8px;cursor:pointer">Copy text</button> <span id="k-done2" role="status"></span></p>
<h2 id="rules">What we ask, and what we do not</h2>
<ul><li>Keep the small credit link under the card. It is a normal link.</li>
<li>Do not tell people they qualify. Ottawa has not published who does. The card and sheet say so, and so should you.</li>
<li>We never sell or share the emails people enter. They get messages about this rebate only.</li>
<li>Being in this kit never changes where an installer ranks. Installers are ranked by Google reviews only.</li></ul>
<h2 id="track">How you see what works</h2>
<p>The name you put in the link is saved with each signup as a source, so we can tell you how many people from your card or link joined the launch list. Ask at <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a>. We count signups only. We do not track visitors on your site.</p>
<h2 id="faq">Common questions</h2>
{kit.faq({"faq": FAQ})}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Source: the Government of Canada <a href="{RELEASE}" rel="noopener" target="_blank">news release of October 8, 2026</a> and our <a href="{GUIDE}">guide</a>, last read {CHECKED}. We are an independent site, not the Government of Canada.</p>
<script>
(function () {{
  var s = document.getElementById('k-p'), c = document.getElementById('k-code'), base = c.textContent, pv = document.getElementById('k-prev'), bl = document.getElementById('k-blurb'), b0 = bl.textContent;
  function slug() {{ return s.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 30) || 'YOUR-NAME'; }}
  s.addEventListener('input', function () {{ var k = slug(); c.textContent = base.split('YOUR-NAME').join(k); bl.textContent = b0.split('YOUR-NAME').join(k); if (k !== 'YOUR-NAME') pv.src = '{EMBED}?p=' + k; }});
  function copy(el, out) {{ navigator.clipboard.writeText(el.textContent).then(function () {{ out.textContent = 'Copied.'; }}, function () {{ out.textContent = 'Select the text and copy it.'; }}); }}
  document.getElementById('k-copy').addEventListener('click', function () {{ copy(c, document.getElementById('k-done')); }});
  document.getElementById('k-copy2').addEventListener('click', function () {{ copy(bl, document.getElementById('k-done2')); }});
  window.addEventListener('message', function (ev) {{ if (ev.data && ev.data.hprFedHeight && ev.source === pv.contentWindow) pv.height = Math.min(900, ev.data.hprFedHeight + 4); }});
}})();
</script>"""


FAQ = [("Is this free?", "Yes. The card, the sheet and the email text are free to use. We ask you to keep the small credit link under the card."),
       ("Will the card update when Ottawa publishes the rules?", "Yes. The card is loaded from our site, so when we update it, every site that shows it updates. You do not change anything."),
       ("Does the sheet send my details to HomePowerRebate?", "No. What you type into the sheet stays in your browser and in the page link. Nothing is stored on our side."),
       ("Can I say my customers qualify?", "No. Ottawa has not published the income line, home types or heating fuels that qualify. The materials say so. Please say the same."),
       ("Can I use the sheet for a province that is not listed?", "The sheet lists the twelve provinces and territories where we have verified the open heat pump rebates. For another place, leave the province blank and the sheet still shows what Ottawa has said.")]


def main():
    pdata = province_data()
    out = ROOT / EMBED.strip("/")
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(embed_page(), encoding="utf-8")

    # printable sheet: noindex
    trail = [("Home", "/"), ("Partners", KIT), ("Branded sheet", SHEET)]
    title, desc = "Federal Heat Pump Rebate Sheet With Your Name On It", "A printable one-page sheet on the federal heat pump rebate, with your business name and the open provincial rebates."
    hero = {"badge": "For partners", "h1": "Federal heat pump rebate: your branded sheet", "lead": "Type your details, pick a province, and print or save as a PDF."}
    lds = kit.ld_scripts([kit.breadcrumb_ld(trail, home_slash=True)])
    kit.write_page(SHEET, title, desc, lds, navfooter.render_nav("", ""), kit.breadcrumb(trail), kit.hero(hero), None, sheet_article(pdata),
                   navfooter.render_footer("", "", "", SHEET), extra_css=SHEET_CSS)
    f = ROOT / SHEET.strip("/") / "index.html"
    t = f.read_text(encoding="utf-8").replace('<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">', '<meta name="robots" content="noindex, follow">')
    f.write_text(t, encoding="utf-8")

    # kit page: indexable
    trail = [("Home", "/"), ("Partners", KIT)]
    title = "Federal Heat Pump Rebate Kit for Installers and Advisors"
    desc = "A free rebate card for your website, a printable sheet with your name on it and ready email text about Ottawa's new heat pump rebate. States only what Ottawa has published."
    hero = {"badge": "Free partner kit", "h1": "Federal heat pump rebate kit for your business", "lead": "A card for your website, a printable sheet and email text. All accurate, all with your name on them."}
    lds = kit.ld_scripts([kit.article_ld(title, desc, "2026-10-22", KIT), kit.breadcrumb_ld(trail, home_slash=True), kit.faq_ld({"faq": FAQ})])
    kit.write_page(KIT, title, desc, lds, navfooter.render_nav("", ""), kit.breadcrumb(trail), kit.hero(hero), None, kit_article(),
                   navfooter.render_footer("", "", "", KIT))
    print("built", EMBED, SHEET, KIT)


if __name__ == "__main__":
    main()
