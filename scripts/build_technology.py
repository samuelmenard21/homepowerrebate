#!/usr/bin/env python3
"""Technology hub: /technology/ and its explainers.

Rules: a product is called "available" only if the maker's own page says so; anything read from news or a search summary is labelled
"reported". Each item shows the date we read the source. Rebate tables come from data/calc + data/verified-facts, so statuses stay in sync.
Re-read every source before changing a claim (SOURCES below carries the read date)."""
import html
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell, AUTHOR, BASE  # noqa: E402
from build_calculator import load_facts, money  # noqa: E402

e = html.escape
READ = "2026-09-30"
READ_H = date.fromisoformat(READ).strftime("%B %-d, %Y")

POSTS = [
 {"slug": "plug-in-heat-pump-water-heaters", "title": "Plug-In Heat Pump Water Heaters: Can You Skip the Electrician?",
  "desc": "120-volt heat pump water heaters plug into a normal outlet. What they are, who they suit, what they cost and which rebates apply, with sources.",
  "kicker": "Water heating", "summary": "A normal outlet, not a new 240-volt circuit, can now run a heat pump water heater. Here is who that helps."},
 {"slug": "cold-climate-heat-pumps-2026", "title": "Cold-Climate Heat Pumps in 2026: What \"Rated to -15°C\" Really Means",
  "desc": "What the cold-climate rating on a heat pump means, how to read two temperatures on a spec sheet, and where the rating decides your rebate.",
  "kicker": "Heating", "summary": "Two numbers on every spec sheet decide whether a heat pump keeps your house warm in a cold snap."},
 {"slug": "quilt-heat-pump-canada", "title": "Quilt Heat Pumps Arrive in Canada: What We Know and What We Don't",
  "desc": "Quilt, a US ductless heat pump maker, launched in Canada in December 2025. Where it is sold, who installs it, its cold-weather ratings and the open questions on price and rebates.",
  "kicker": "Heating", "summary": "A design-led ductless heat pump is now sold in five provinces. Here is what is confirmed and what is not."},
]
COMING = ["Sodium-ion vs lithium home batteries: what to wait for", "Can your EV power your house? Which cars, what it costs, why it is stuck",
          "Solar panels: what 26.9% efficiency means and when you can buy it"]


def pill(label, kind):
    col = {"ok": ("#e3f1e8", "#1f5a3d"), "rep": ("#fdeccf", "#8a4a06"), "lab": ("#e8e8e8", "#444")}[kind]
    return f'<span style="display:inline-block;padding:1px 9px;border-radius:99px;font-size:12px;font-weight:600;background:{col[0]};color:{col[1]}">{e(label)}</span>'


def hpwh_table():
    facts = load_facts()
    rows = []
    for f in sorted((ROOT / "data" / "calc").glob("*.json")):
        sp = json.loads(f.read_text())
        seen = set()
        for p in sp["programs"]:
            fx = facts[p["fact"]]
            if p["upgrade"] != "water-heater" or fx["status"] not in ("active", "upcoming") or p["fact"] in seen:
                continue
            seen.add(p["fact"])
            note = " Starts October 1, 2026." if fx["status"] == "upcoming" else ""
            rows.append(f"<tr><td>{e(sp['name'])}</td><td><b>{e(p['name'])}</b></td><td>{e(money(p))}</td>"
                        f"<td><a href='{e(fx['source_url'])}' rel='nofollow noopener' target='_blank'>Source</a> <span class='small'>(checked {e(fx['verified_on'])}){note}</span></td></tr>")
    return "<div class='tw'><table><tr><th>Where</th><th>Program</th><th>Amount</th><th>Source</th></tr>" + "".join(rows) + "</table></div>"


def post_water():
    return f"""<p class="meta">By {e(AUTHOR['name'])} · Sources read {READ_H}</p>
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> Yes, for many homes. A 120-volt plug-in heat pump water heater needs a standard outlet instead of a new 240-volt circuit, which is often the costly part of switching from gas or an old electric tank. The catch is size and space: they may recover more slowly than a 240-volt model, and they need room and air around them.</p></div>
<h2>What is new</h2>
<p>Heat pump water heaters have been sold for years, but most needed a 240-volt circuit like an electric dryer. Two makers now list 120-volt plug-in models. {pill('Available: maker page read', 'ok')}</p>
<table><tr><th>Maker and model</th><th>What the maker states</th></tr>
<tr><td>A. O. Smith Voltex 120V Plug-In (HPTV-50)</td><td>50-gallon tank (66 and 80 gallons also listed). 120 volts on a 15-amp shared circuit. UEF 3. First hour rating 52 gallons. 45 dBA. 10-year limited tank and parts warranty. ENERGY STAR certified. The maker says it saves up to $118 a year compared with a gas water heater.</td></tr>
<tr><td>Rheem ProTerra Plug-in</td><td>Rheem lists plug-in 120-volt models, with a dedicated-circuit version and a shared-circuit version. {pill('Reported: spec sheet not re-read', 'rep')} Check the exact sizes and ratings on Rheem's page before you buy.</td></tr></table>
<p class="small">Sources: <a href="https://www.hotwater.com/products/HPTV-50-SG210.html" rel="nofollow noopener" target="_blank">A. O. Smith product page</a>, read {READ_H}. <a href="https://files.rheem.com/blobazrheem/wp-content/uploads/sites/2/Plug-in-Heat-Pump-Spec-Sheet.pdf" rel="nofollow noopener" target="_blank">Rheem spec sheet</a>, listed but not read in full.</p>
<h2>Who it suits</h2>
<ul><li><b>You have a gas water heater and no spare 240-volt circuit.</b> A plug-in unit can avoid new wiring. Ask your installer to check your panel and outlet anyway.</li>
<li><b>Small to medium households.</b> A 50-gallon tank with a 52-gallon first hour rating suits a household that does not run many showers and laundry loads back to back.</li>
<li><b>A basement, garage or utility room with space.</b> Heat pump water heaters cool the air around them and make some noise (45 dBA for the A. O. Smith model, about a quiet room).</li></ul>
<h2>Who should look at a 240-volt model instead</h2>
<p>Big households and homes with heavy hot water use. A 240-volt model recovers faster. If you already have a 240-volt circuit from an old electric tank, you give up nothing by using it.</p>
<h2>What it costs</h2>
<p>We could not find a manufacturer price. One retailer lists the 50-gallon A. O. Smith model at about $3,345, before installation. {pill('Reported: one retailer listing', 'rep')} Installed cost depends on your home, so get at least two quotes for the same size and model.</p>
<h2>Does a rebate apply?</h2>
<p>Often, but each program sets its own rules. Many require an ENERGY STAR model, and some keep their own qualified-products list, so check that the exact model is on it before you buy. These are the open programs we track for heat pump water heaters:</p>
{hpwh_table()}
<p>Want the number for your home? <a href="/calculator/">Use the rebate calculator</a>, then <a href="/get-quotes/">see top-rated installers in your city</a>.</p>
<h2>What we could not confirm</h2>
<p>Rheem's full specifications, and a manufacturer price for either brand. We will update this page when we have read them.</p>"""


def post_hp():
    return f"""<p class="meta">By {e(AUTHOR['name'])} · Sources read {READ_H}</p>
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> Every cold-climate heat pump has two temperatures on its spec sheet: the coldest it will run, and the coldest it still gives full heating power. The second number matters more. Your rebate may also depend on it.</p></div>
<h2>Two numbers, two meanings</h2>
<p>Carrier's own page is a good example. It says its Infinity 21 Ultimate Cold Climate heat pump (27VNA1) operates "down to -23°F" and keeps "100% capacity at 5°F". {pill('Available: maker page read', 'ok')}</p>
<table><tr><th></th><th>In °F</th><th>In °C</th><th>What it means</th></tr>
<tr><td>Coldest it will run</td><td>-23°F</td><td>about -31°C</td><td>It keeps heating below this point only in a reduced way, or stops.</td></tr>
<tr><td>Coldest at full capacity</td><td>5°F</td><td>-15°C</td><td>Down to here it delivers all the heat it is rated for.</td></tr></table>
<p>So "rated to -15°C" usually points to the full-power number. Below it, the heat pump still helps, but a backup heat source may do some of the work. A different Carrier model (27VNA3) is listed as running down to -15°F, about -26°C. The same brand can have very different ratings, so read the exact model.</p>
<p class="small">Source: <a href="https://www.carrier.com/us/en/residential/hvac-resources/heat-pumps/cold-climate-heat-pump/" rel="nofollow noopener" target="_blank">Carrier cold climate heat pump page</a>, read {READ_H}. Carrier also states that it completed the U.S. Department of Energy's Cold Climate Heat Pump Challenge.</p>
<h2>What is new in 2026</h2>
<p>Trade press reports that Carrier, Lennox, Bosch and Trane had cold-climate models on the market by the end of 2025, and that Daikin and Rheem were expected to follow in 2026. {pill('Reported: trade press, not confirmed with each maker', 'rep')} TCL also showed new cold-climate systems at the AHR Expo 2026 trade show. We have only read Carrier's page so far, so treat the others as leads to check, not as facts.</p>
<p class="small">Sources: <a href="https://propmodo.com/?p=173682" rel="nofollow noopener" target="_blank">Propmodo</a>, <a href="https://us.tcl.com/blogs/press-releases/tcl-expands-u-s-hvac-portfolio-at-ahr-expo-2026" rel="nofollow noopener" target="_blank">TCL press release</a>.</p>
<h2>Where the rating decides your rebate</h2>
<table><tr><th>Where</th><th>What the program asks</th></tr>
<tr><td>BC Hydro</td><td>The whole-home rebate (up to $4,000) needs the heat pump to meet 100% of your heating at -5°C, plus an eligible model and a Home Performance Contractor Network installer. <a href="/programs/bc-hydro-rebates/">Details</a></td></tr>
<tr><td>Ontario Home Renovation Savings</td><td>Pays $1,250 per ton, up to $7,500, for a cold-climate air-source heat pump when you heat with electricity, oil, propane or wood. <a href="/calculator/on/">Ontario calculator</a></td></tr>
<tr><td>Mass Save</td><td>Needs an ENERGY STAR cold-climate model from a Heat Pump Installer Network contractor. <a href="/calculator/ma/">Massachusetts calculator</a></td></tr></table>
<h2>How to read a spec sheet</h2>
<ol><li>Find the temperature where the unit keeps 100% capacity, and compare it with your area's coldest design day.</li>
<li>Check the exact model number against your rebate program's list.</li>
<li>Ask your installer how the unit was sized for your home. A well-sized smaller unit often beats an oversized bigger one.</li></ol>
<p>Comparing brands? Read <a href="/blog/heat-pump-brands-comparison-mitsubishi-daikin-bosch/">Bosch vs Mitsubishi vs Daikin</a>. Ready to price one? <a href="/get-quotes/">See top-rated installers in your city</a>.</p>
<h2>What we could not confirm</h2>
<p>Model lists and ratings for Lennox, Bosch, Trane, Daikin and Rheem's 2026 launches. Prices for any brand.</p>"""


def post_quilt():
    return f"""<p class="meta">By {e(AUTHOR['name'])} · Sources read {READ_H}</p>
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> Quilt is a ductless heat pump with a modern design, and it is now sold in Ontario, British Columbia, Nova Scotia, New Brunswick and Manitoba. It is installed only through Quilt's own partners. We could not find a price, and we do not yet know whether leased or rented systems qualify for rebates.</p></div>
<h2>What it is</h2>
<p>Quilt makes ductless (mini-split) heat pumps with one outdoor unit and two or three indoor units, controlled by a dial and an app. {pill('Available: maker page read', 'ok')}</p>
<table><tr><th>What Quilt states</th><th>Detail</th></tr>
<tr><td>Efficiency</td><td>SEER2 25 (2 indoor units) or 25.3 (3 units). HSPF2 12 (Region IV). ENERGY STAR Cold Climate certified.</td></tr>
<tr><td>Cold weather (Canada page)</td><td>100% of heating capacity down to -5°F (-21°C), and 90% at -13°F (-25°C).</td></tr>
<tr><td>Capacity at 47°F</td><td>18,000 BTU/h (2 units) or 27,000 BTU/h (3 units).</td></tr>
<tr><td>Noise</td><td>Indoor units 27 to 48 dBA. Outdoor units 50 to 52 dBA.</td></tr>
<tr><td>Refrigerant</td><td>R32.</td></tr></table>
<p class="small">Sources: <a href="https://www.quilt.com/canada" rel="nofollow noopener" target="_blank">Quilt Canada page</a> and <a href="https://www.quilt.com/tech-specs" rel="nofollow noopener" target="_blank">Quilt tech specs</a>, read {READ_H}.</p>
<h2>Where you can get it</h2>
<p>Quilt's Canada page lists Ontario, British Columbia, Nova Scotia, New Brunswick and Manitoba, and names two installers: Go Lime in Toronto and Wilsons in Halifax. A law-firm write-up dates the Canadian launch to December 11, 2025, and says it is Quilt's first market outside the US. {pill('Available: maker page read', 'ok')}</p>
<p class="small">Source: <a href="https://www.goodmans.ca/insights/post/goodmans-tech-blog/quilt-brings-next-gen-heat-pumps-to-canada" rel="nofollow noopener" target="_blank">Goodmans</a>, read {READ_H}.</p>
<h2>About Go Lime</h2>
<p>Go Lime is a Greater Toronto Area home-services company. News coverage says it offers leases and rentals for water heaters and HVAC equipment through a program called GoFlex, and that it is Quilt's installation and service partner in Canada. {pill('Reported: news, not Go Lime\'s own site', 'rep')} We have not read Go Lime's own pages, so check its current terms before you sign anything.</p>
<h2>Does a rebate apply?</h2>
<p>Possibly, but we cannot say yet. Rebate programs look at the model, the installer and sometimes who owns the equipment:</p>
<ul><li><b>BC Hydro</b> needs an eligible model on its list and an installer in its Home Performance Contractor Network. <a href="/programs/bc-hydro-rebates/">Details</a></li>
<li><b>Ontario Home Renovation Savings</b> pays per ton for a cold-climate heat pump for homeowners. <a href="/calculator/on/">Ontario calculator</a></li>
<li><b>Nova Scotia</b> pays per ton through a Home Energy Assessment, and only for models on Efficiency Nova Scotia's list. <a href="/calculator/ns/">Nova Scotia calculator</a></li></ul>
<p>Ask Quilt or your installer three things in writing: is this exact model on my program's list, is the installer registered with the program, and does a lease or rental still qualify for the rebate.</p>
<h2>What we could not confirm</h2>
<ul><li>Canadian pricing. Quilt says it gives a price after a free consultation.</li><li>Whether leased or rented systems get rebates.</li><li>Whether the model is on BC Hydro's, Ontario's or Nova Scotia's qualified lists.</li><li>How many Google reviews Go Lime and Wilsons have. Our installer rankings use Google reviews only, and neither company is in our lists yet.</li></ul>
<p>Comparing options? Read <a href="/technology/cold-climate-heat-pumps-2026/">what the cold-climate rating means</a>, then <a href="/get-quotes/">see top-rated installers in your city</a>.</p>"""


def page(post, body):
    path = f"/technology/{post['slug']}/"
    full = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/technology/">Technology</a></li><li aria-current="page">{e(post['kicker'])}</li></ol></nav>
<header class="hero"><div class="wrap"><h1>{e(post['title'])}</h1></div></header>
<section class="body"><div class="wrap">{body}</div></section>"""
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": post["title"], "description": post["desc"], "author": AUTHOR,
           "dateModified": READ, "mainEntityOfPage": BASE + path, "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE}},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Technology", "item": BASE + "/technology/"},
              {"@type": "ListItem", "position": 3, "name": post["title"]}]}]
    return path, shell(post["title"] + " | HomePowerRebate", post["desc"], path, "bc", full, ld)


def hub():
    cards = "".join(f'<li style="margin:0 0 16px;"><a href="/technology/{p["slug"]}/"><b>{e(p["title"])}</b></a><br><span class="small">{e(p["kicker"])} · checked {READ_H}</span><br>{e(p["summary"])}</li>' for p in POSTS)
    coming = "".join(f"<li>{e(t)}</li>" for t in COMING)
    body = f"""<header class="hero"><div class="wrap"><h1>Home Energy Technology: What Is New and What Is Real</h1><p>Short explainers on new heat pumps, water heaters, batteries and solar, with a source for every claim and a note on which rebates apply.</p></div></header>
<section class="body"><div class="wrap"><h2>Latest</h2><ul style="list-style:none;padding:0;">{cards}</ul>
<h2>How we label things</h2><ul><li>{pill('Available: maker page read', 'ok')} The maker's own page says it is for sale, and we read it on the date shown.</li>
<li>{pill('Reported', 'rep')} We found it in news or a search summary but have not confirmed it with the maker.</li>
<li>{pill('Lab result', 'lab')} Announced in a lab or pilot. You cannot buy it yet.</li></ul>
<h2>Coming next</h2><ul>{coming}</ul>
<p>Monthly email: <a href="#newsletter-form">get the update in your inbox</a>.</p></div></section>"""
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Home Energy Technology", "url": BASE + "/technology/", "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE}}]
    return "/technology/", shell("Home Energy Technology: New Heat Pumps, Batteries and Solar | HomePowerRebate",
                                 "What is new in home heat pumps, water heaters, batteries and solar, with sources, dates and the rebates that apply.", "/technology/", "bc", body, ld)


def main():
    outs = [hub(), page(POSTS[0], post_water()), page(POSTS[1], post_hp()), page(POSTS[2], post_quilt())]
    for path, html_ in outs:
        f = ROOT / path.strip("/") / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html_, encoding="utf-8")
        print("Wrote", path)


if __name__ == "__main__":
    main()
