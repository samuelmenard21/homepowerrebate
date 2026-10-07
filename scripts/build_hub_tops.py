#!/usr/bin/env python3
"""Hub pages: head-term titles, a short answer, an open-programs table and a "What changed recently"
box on every province/state hub. California's body is rebuilt entirely (its old finder had stale,
wrong numbers).

Every amount comes from data/verified-facts/*.json; changes come from rebate-tracker/changes.json.
Blocks are marker-wrapped (HUB-TOP, HUB-CHANGES) so re-runs replace them. Run after the monthly
rebate check:  python3 scripts/build_hub_tops.py
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import AUTHOR  # noqa: E402

e = html.escape
TRACK = json.loads((ROOT / "rebate-tracker" / "changes.json").read_text())
CHECKED = TRACK["checked"]
CHECKED_H = date.fromisoformat(CHECKED).strftime("%B %-d, %Y")
BASE = "https://homepowerrebate.com"
TOP_S, TOP_E = "<!-- HUB-TOP-START -->", "<!-- HUB-TOP-END -->"
CH_S, CH_E = "<!-- HUB-CHANGES-START -->", "<!-- HUB-CHANGES-END -->"
BODY_S, BODY_E = "<!-- HUB-BODY-START -->", "<!-- HUB-BODY-END -->"

HUBS = {
    "ca/bc": {"code": "BC", "name": "BC",
              "title": "BC Hydro Rebates 2026: Heat Pump, Solar, Battery & Insulation",
              "desc": "Every BC Hydro, CleanBC and FortisBC rebate in 2026: heat pumps up to $4,000 (or $13,000 income-qualified), solar and battery up to $10,000, free smart thermostats. Checked monthly.",
              "h1": "BC Hydro and CleanBC Rebates 2026", "eyebrow": "BC Hydro · CleanBC · FortisBC",
              "short": "BC Hydro pays up to $4,000 for a heat pump that replaces electric heat, up to $10,000 for solar plus a battery, and free Mysa or Sinopé thermostats for baseboard homes. CleanBC pays income-qualified homes up to $13,000 to switch from gas, oil or propane to a heat pump. FortisBC customers have their own rebates instead.",
              "rows": [
                  ("Heat pump (replacing electric heat)", "BC Hydro", "Up to $4,000 whole home, $1,500 partial", "HPCN-registered installer. Extra bonus up to $1,000 for installs finished by Oct 31, 2026.", "https://www.bchydro.com/powersmart/residential/rebates-programs/home-renovation/renovating-heating-system.html"),
                  ("Heat pump (from gas, oil or propane)", "CleanBC, income-qualified", "$13,000 / $7,000 / $3,500 by income level", "Plus a $3,000 northern top-up for levels 1 and 2.", "https://betterhomesbc.ca/wp-content/uploads/2026/07/RebateEligibilityRequirements_ESP_6July2026.pdf"),
                  ("Solar panels", "BC Hydro", "$1,000 per kW, up to $5,000", "Max 50% of cost. Approval before you install.", "https://app.bchydro.com/accounts-billing/electrical-connections/customer-generation/solar-battery-rebates.html"),
                  ("Home battery", "BC Hydro", "Up to $5,000 with Peak Saver ($1,500 without)", "Must be on the qualified list. Tesla batteries get $0.", "https://app.bchydro.com/accounts-billing/electrical-connections/customer-generation/solar-battery-rebates.html"),
                  ("Smart thermostats", "BC Hydro", "Free (up to 5), from October 2026", "Baseboard-heated homes, enrolled in Peak Saver.", "https://news.gov.bc.ca/releases/2026ECS0037-000794"),
                  ("FortisBC customers", "FortisBC", "Insulation, windows, heat pump water heater, thermostat", "FortisBC customers can't use BC Hydro rebates.", "https://www.fortisbc.com/rebates-and-energy-savings/rebates-and-offers"),
              ],
              "snippet_re": r'<p class="snippet-answer">.*?</p>'},
    "ca/on": {"code": "ON", "name": "Ontario",
              "title": "Home Renovation Savings 2026: Ontario Rebates by City",
              "desc": "Ontario's Home Renovation Savings Program in 2026: heat pumps up to $12,000, solar and battery up to $10,000, insulation up to $7,700, $125 smart thermostats. Every city, checked monthly.",
              "h1": "Ontario Home Renovation Savings Rebates 2026", "eyebrow": "Home Renovation Savings Program",
              "short": "Ontario's Home Renovation Savings Program pays $1,250 per ton, up to $7,500, for an air-source heat pump in an electric, oil, propane or wood home ($500 per ton, up to $2,000, on Enbridge gas), and up to $12,000 for ground-source, up to $5,000 each for solar and a battery, up to $7,700 for insulation with an energy assessment, and $125 for a smart thermostat. Income-qualified homes can get free upgrades, and Toronto adds a home energy loan of up to $125,000.",
              "rows": [
                  ("Heat pump", "Home Renovation Savings", "$1,250 per ton, up to $7,500 (air-source); ground-source $2,000 per ton, up to $12,000", "Electric, oil, propane or wood heat. Pre-approval and a participating contractor are required.", "https://homerenovationsavings.ca/heat-pumps"),
                  ("Heat pump (Enbridge gas customers)", "Home Renovation Savings", "$500 per ton, up to $2,000", "Active Enbridge Gas account.", "https://homerenovationsavings.ca/heat-pumps"),
                  ("Solar and battery", "Home Renovation Savings", "Up to $5,000 each, $10,000 combined", "Max 50% of cost. No net-metering agreement with your utility.", "https://www.homerenovationsavings.ca/without-assessment/solar"),
                  ("Insulation", "Home Renovation Savings", "Up to $7,700 with an assessment; attic up to $1,250 without", "Pre- and post-work assessment for the bigger amount.", "https://homerenovationsavings.ca/with-assessment"),
                  ("Smart thermostat", "Home Renovation Savings", "$125", "First thermostat rebate only. Claim within 60 days.", "https://homerenovationsavings.ca/without-assessment/smart-thermostat"),
                  ("Free upgrades", "Energy Affordability Program", "Free", "Income-qualified owners and renters.", "https://saveonenergy.ca/For-Your-Home/Energy-Affordability-Program"),
                  ("Toronto only", "Home Energy Loan Program (HELP)", "Loan up to $125,000", "Capped at 10% of your home's assessed value; up to 20 years.", "https://www.toronto.ca/services-payments/water-environment/environmental-grants-incentives/home-energy-loan-program-help/"),
              ],
              "snippet_re": r'<p class="snippet-answer">.*?</p>'},
    "us/ca": {"code": "CA", "name": "California",
              "title": "California Heat Pump & Solar Rebates 2026: What's Open",
              "desc": "Which California home energy rebates are still open in 2026? SMUD, Glendale, Burbank and Pasadena rebates, SGIP batteries and free income-qualified upgrades. TECH and HEEHRA are waitlisted. Checked monthly.",
              "h1": "California Home Energy Rebates 2026: What's Still Open", "eyebrow": "SMUD · City utilities · SCE · SGIP",
              "short": "Most statewide California rebates are closed or waitlisted in 2026: TECH Clean California and the HEEHRA heat pump rebate are fully reserved, and the federal tax credits ended on December 31, 2025. Your best money now depends on your utility: SMUD pays up to $3,000 for a heat pump and $6,000 for a battery, and city utilities in Glendale, Burbank and Pasadena have their own rebates. PG&E, SCE and SDG&E customers mostly have income-qualified programs.",
              "rows": [
                  ("Heat pump", "SMUD (Sacramento)", "Up to $3,000, plus up to $2,000 Go Electric bonus", "Participating contractor. Bonus for switching from gas.", "https://www.smud.org/Rebates-and-Savings-Tips/Rebates-for-My-Home"),
                  ("Heat pump water heater", "SMUD", "Up to $4,000", "NEEA Tier III or IV models.", "https://www.smud.org/Rebates-and-Savings-Tips/Rebates-for-My-Home"),
                  ("Home battery", "SMUD", "$300 per kWh, up to $6,000", "Solar and Storage Rate; enroll within 90 days.", "https://www.smud.org/Going-Green/Battery-Storage"),
                  ("Heat pump (replacing gas)", "Glendale Water & Power", "$1,000 per ton, up to $5,000", "Until funds run out.", "https://www.glendaleca.gov/government/departments/glendale-water-and-power/residential-customers/residential-programs/smart-home-rebate-program"),
                  ("Heat pump (replacing gas)", "Burbank Water & Power", "$1,000 per ton, up to $2,500", "BWP residential.", "https://www.burbankwaterandpower.com/electrify-your-home"),
                  ("Solar and battery", "Pasadena Water & Power (pilot)", "$0.60 per watt; battery up to $550 per kWh", "Limited funds.", "https://pwp.cityofpasadena.net/launch-solar-and-battery-rebate-pilot-program-for-residential-and-commercial-customers/"),
                  ("Home battery", "SGIP (statewide)", "Depends on tier", "Mainly income-qualified, medical baseline or high fire-threat areas.", "https://www.cpuc.ca.gov/industries-and-topics/electrical-energy/demand-side-management/self-generation-incentive-program"),
                  ("Free upgrades", "SCE Energy Savings Assistance", "No cost", "Income-qualified SCE customers.", "https://www.sce.com/save-money/income-qualified-programs/energy-savings-assistance-program"),
                  ("Panel upgrade for EV charging", "SCE Charge Ready Home", "Up to $4,200", "SCE customers.", "https://evhome.sce.com/"),
              ]},
    # Other hubs: "What changed" box only.
    "ca/ab": {"code": "AB", "name": "Alberta"}, "ca/ns": {"code": "NS", "name": "Nova Scotia"},
    "us/ny": {"code": "NY", "name": "New York"}, "us/ma": {"code": "MA", "name": "Massachusetts"},
    "us/pa": {"code": "PA", "name": "Pennsylvania"}, "us/co": {"code": "CO", "name": "Colorado"}, "us/vt": {"code": "VT", "name": "Vermont"}, "us/il": {"code": "IL", "name": "Illinois"},
}
FED = {"ca": "CA-FED", "us": "US"}


def load_data_hubs():
    """Regions added by data alone: data/hub-tops/<code>.json (short answer + rows) plus data/verified-facts/<code>.json for sources.
    Adding a region = add those two files; the hub gets the same short-answer and open-programs block as every other hub."""
    for f in sorted((ROOT / "data" / "hub-tops").glob("*.json")):
        spec = json.loads(f.read_text())
        facts = {x["program"]: x for x in json.loads((ROOT / "data" / "verified-facts" / f.name).read_text())["facts"]}
        rows = [(r["upgrade"], r["program"], r["amount"], r["rules"], facts[r["fact"]]["source_url"]) for r in spec["rows"]]
        status = [facts[r["fact"]]["status"] for r in spec["rows"]]
        verified = max(facts[r["fact"]]["verified_on"] for r in spec["rows"])
        key = next(k for k, v in HUBS.items() if v["code"] == spec["code"])
        HUBS[key].update(name=spec["name"], short=spec["short"], rows=rows, top_only=True, eyebrow=spec["eyebrow"],
                         row_status=status, verified=verified, row_pages=[r.get("page") for r in spec["rows"]])


load_data_hubs()


def fmt(d):
    parts = d.split("-")
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    return f"{months[int(parts[1]) - 1]} {parts[0]}" if len(parts) >= 2 else parts[0]


def changes_box(key, cfg):
    codes = {cfg["code"], FED[key.split("/")[0]]}
    items = sorted([x for x in TRACK["entries"] if x["region"] in codes], key=lambda x: x["date"], reverse=True)[:5]
    if not items:
        return ""
    lis = "".join(
        f'<li><b>{e(fmt(x["date"]))}: {e(x["program"])}</b> ({e(x["status"])}). {e(x["change"])} '
        f'<a href="{e(x["source"])}" rel="nofollow noopener" target="_blank">Source</a></li>' for x in items)
    return (f'{CH_S}<section style="max-width:880px;margin:24px auto;padding:0 20px;"><div style="background:#fff;border:1px solid #d9d0c1;'
            f'border-left:4px solid #d4751c;border-radius:10px;padding:18px 20px;"><h2 style="font-family:Fraunces,Georgia,serif;font-size:22px;margin:0 0 4px;">'
            f'What changed recently in {e(cfg["name"])}</h2><p style="margin:0 0 10px;font-size:14px;color:#6b8e7f;">Checked {CHECKED_H}. '
            f'<a href="/rebate-tracker/">See every change</a>.</p><ul style="margin:0 0 0 18px;line-height:1.6;font-size:15px;">{lis}</ul></div></section>{CH_E}')


def unify_hero(s, cfg):
    """Every hub gets the same hero: eyebrow, h1, one-line sub, and the same two buttons."""
    m = re.search(r'<(header|section) class="hero[^"]*"[^>]*>.*?</\1>', s, re.S)
    if not m:
        return s
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", m.group(0), re.S).group(1)
    sub = re.search(r'<p[^>]*class="sub"[^>]*>(.*?)</p>', m.group(0), re.S) or re.search(r"<p[^>]*>(.*?)</p>", m.group(0), re.S)
    hero = (f'<header class="hero hub-hero"><div class="wrap"><div class="eyebrow">{e(cfg["eyebrow"])}</div><h1>{h1}</h1>'
            f'<p class="sub">{sub.group(1) if sub else ""}</p><div class="cta-row"><a href="#find-city" class="btn">Find your city →</a>'
            f'<a href="/programs/" class="btn btn-secondary">See all programs</a></div></div></header>')
    return s[:m.start()] + hero + s[m.end():]


STATUS_PILL = {  # status -> (label, background, text colour); the label is always a word, never colour alone
    "active": ("Open", "#e3f1e8", "#1f5a3d"), "upcoming": ("Starts soon", "#fdeccf", "#8a4a06"),
    "waitlist": ("Waitlist", "#fdeccf", "#8a4a06"), "paused": ("Paused", "#f3dcdc", "#8a2b2b"),
    "closed": ("Closed", "#f3dcdc", "#8a2b2b"), "check": ("Confirm status", "#e8e8e8", "#444"), "info": ("Note", "#e8e8e8", "#444"),
}


def status_pill(st):
    label, bg, fg = STATUS_PILL[st]
    return (f'<span class="rb-status rb-{st}" style="display:inline-block;margin-left:6px;padding:1px 8px;border-radius:99px;'
            f'font-size:12px;font-weight:600;background:{bg};color:{fg};white-space:nowrap;">{label}</span>')


def top_block(cfg):
    sts = cfg.get("row_status") or ["active"] * len(cfg["rows"])
    pages = cfg.get("row_pages") or [None] * len(cfg["rows"])
    rows = "".join(f'<tr><td><b>{e(w)}</b></td><td>{f'<a href="{e(pg)}">{e(p)}</a>' if pg else e(p)}</td><td>{e(a)}{status_pill(st)}</td><td>{e(n)} <a href="{e(s)}" rel="nofollow noopener" target="_blank">Source</a></td></tr>'
                   for (w, p, a, n, s), st, pg in zip(cfg["rows"], sts, pages))
    vdate = fmt(cfg["verified"]) if cfg.get("verified") else CHECKED_H
    return (f'{TOP_S}<section style="max-width:880px;margin:24px auto;padding:0 20px;">'
            f'<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;font-size:17px;line-height:1.6;"><b>Short answer:</b> {e(cfg["short"])}</p>'
            f'<p style="margin:10px 0 0;font-size:13px;color:#6b8e7f;">Last verified {vdate} · By <a href="/about">{e(AUTHOR["name"])}</a> · Every amount links to the official program.</p></div>'
            f'<h2 style="font-family:Fraunces,Georgia,serif;font-size:24px;margin:26px 0 10px;">Rebates open in {e(cfg["name"])} right now</h2>'
            f'<div style="overflow-x:auto;-webkit-overflow-scrolling:touch;"><table style="width:100%;min-width:620px;border-collapse:collapse;font-size:15px;">'
            f'<tr style="background:#f5efe5;text-align:left;"><th style="padding:10px;">Upgrade</th><th style="padding:10px;">Program</th><th style="padding:10px;">Amount</th><th style="padding:10px;">Rules</th></tr>'
            + rows.replace("<td>", '<td style="padding:10px;border-bottom:1px solid #d9d0c1;vertical-align:top;">')
            + f'</table></div></section>{TOP_E}')


def ca_body(cfg):
    cities = json.loads((ROOT / "powerscore-data.json").read_text())["regions"]["us/ca"]["cities"].values()
    grid = "".join(f'<a href="{c["url"]}" style="display:block;padding:12px 14px;background:#fff;border:1px solid #d9d0c1;border-radius:8px;text-decoration:none;color:#0a2a2e;font-weight:600;">{e(c["label"])}</a>'
                   for c in sorted(cities, key=lambda c: c["label"]))
    faq = [
        ("Can I still get the federal tax credit for a heat pump or solar in California?",
         "No, not for 2026 installs. The federal 25C and 25D credits ended for systems installed after December 31, 2025."),
        ("Is TECH Clean California still open?",
         "Not for new single-family requests. TECH's heat pump incentives were fully reserved on November 14, 2025, and new requests go on a waitlist."),
        ("What about the HEEHRA heat pump rebate?",
         "HEEHRA, the income-qualified rebate that paid up to $8,000, was fully reserved statewide on February 24, 2026. New requests are waitlisted."),
        ("Which utility am I on?",
         "Look at the top of your electric bill. Most of the state is PG&E, SCE or SDG&E. Sacramento is SMUD, and Los Angeles, Glendale, Burbank and Pasadena have their own city utilities with their own rebates."),
        ("Is solar still worth it under net billing?",
         "Since April 15, 2023, new solar customers of PG&E, SCE and SDG&E are paid much less for power they send to the grid. Savings now depend on using your own solar power, which is why many quotes include a battery. Check any quote with our solar quote checker."),
    ]
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
    return (f'{BODY_S}<header class="hero" style="padding:44px 20px 36px;background:#08363f;color:#faf7f2;text-align:center;"><div class="wrap">'
            f'<div style="font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#e88a2e;margin-bottom:10px;">{e(cfg["eyebrow"])}</div>'
            f'<h1 style="font-family:Fraunces,Georgia,serif;font-size:clamp(28px,5vw,42px);color:#fff;margin:0 0 12px;">{e(cfg["h1"])}</h1>'
            f'<p style="max-width:640px;margin:0 auto;color:rgba(250,247,242,.85);">What each utility still pays, what closed, and what to do instead. Updated {CHECKED_H}.</p></div></header>'
            + top_block(cfg) + changes_box("us/ca", cfg) +
            f'<section style="max-width:880px;margin:24px auto;padding:0 20px;"><h2 style="font-family:Fraunces,Georgia,serif;font-size:24px;">If you\'re on PG&amp;E, SCE or SDG&amp;E</h2>'
            f'<p>Upfront rebates are thin right now. Your best options: income-qualified free upgrades (SCE Energy Savings Assistance, and PG&amp;E\'s and SDG&amp;E\'s own programs), SGIP for a battery if you qualify, and joining the TECH or HEEHRA waitlist in case funds return. '
            f'Before you sign, make sure a quote isn\'t counting on a rebate or tax credit that has closed.</p>'
            f'<h2 style="font-family:Fraunces,Georgia,serif;font-size:24px;margin-top:28px;">California cities</h2>'
            f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px;">{grid}</div>'
            f'<h2 style="font-family:Fraunces,Georgia,serif;font-size:24px;margin-top:28px;">Common questions</h2>'
            + "".join(f"<h3 style=\"font-size:18px;margin:18px 0 6px;\">{e(q)}</h3><p>{e(a)}</p>" for q, a in faq)
            + '<p><b>Related:</b> <a href="/rebate-tracker/">Rebate tracker</a> · <a href="/solar-quote-checker/">Solar quote checker</a> · <a href="/batteries/">Home battery guides</a> · <a href="/installers/">Top-rated installers by city</a></p></section>'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>{BODY_E}')


def set_head(s, cfg, url):
    t = e(cfg["title"]) + " | HomePowerRebate"
    s = re.sub(r"<title>.*?</title>", f"<title>{t}</title>", s, count=1, flags=re.S)
    for pat, val in [(r'(<meta name="description" content=")[^"]*(")', cfg["desc"]), (r'(<meta property="og:description" content=")[^"]*(")', cfg["desc"]),
                     (r'(<meta property="og:title" content=")[^"]*(")', cfg["title"]), (r'(<meta name="twitter:title" content=")[^"]*(")', cfg["title"]),
                     (r'(<meta name="twitter:description" content=")[^"]*(")', cfg["desc"])]:
        s = re.sub(pat, lambda m: m.group(1) + e(val) + m.group(2), s, count=1)
    art = {"@context": "https://schema.org", "@type": "Article", "headline": cfg["title"], "description": cfg["short"],
           "dateModified": CHECKED, "author": AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE},
           "mainEntityOfPage": url}
    blk = f'<!-- HUB-LD-START --><script type="application/ld+json">{json.dumps(art, ensure_ascii=False)}</script><!-- HUB-LD-END -->'
    if "<!-- HUB-LD-START -->" in s:
        s = re.sub(r"<!-- HUB-LD-START -->.*?<!-- HUB-LD-END -->", lambda m: blk, s, count=1, flags=re.S)
    else:
        s = s.replace("</head>", blk + "\n</head>", 1)
    return s


def replace_or_insert(s, start, end, block, after_re):
    if start in s:
        return re.sub(re.escape(start) + ".*?" + re.escape(end), lambda m: block, s, count=1, flags=re.S)
    m = re.search(after_re, s, re.S)
    if not m:
        raise SystemExit(f"anchor not found: {after_re}")
    return s[:m.end()] + "\n" + block + s[m.end():]


def main():
    for key, cfg in HUBS.items():
        f = ROOT / key / "index.html"
        s = f.read_text(encoding="utf-8")
        url = f"{BASE}/{key}/"
        if key == "us/ca":
            s = set_head(s, cfg, url)
            # Drop the old head FAQ (it claimed federal credits still stack); the new body carries its own.
            s = re.sub(r'<script type="application/ld\+json">\s*\{\s*"@context": "https://schema.org",\s*"@type": "FAQPage".*?</script>\s*',
                       lambda m: "" if "Which region am I in?" in m.group(0) else m.group(0), s, flags=re.S)
            body = ca_body(cfg)
            if BODY_S in s:
                s = re.sub(re.escape(BODY_S) + ".*?" + re.escape(BODY_E), lambda m: body, s, count=1, flags=re.S)
            else:
                a = s.index("<!-- ============================ /NAV ============================== -->") + len("<!-- ============================ /NAV ============================== -->")
                b = s.index("<!-- FURNACE-LINK-START -->")
                s = s[:a] + "\n" + body + "\n" + s[b:]
        elif cfg.get("top_only"):
            anchor = re.escape("<!-- HUB-STATS-END -->") if "<!-- HUB-STATS-END -->" in s else r"<header class=\"hero\">.*?</header>"
            s = replace_or_insert(s, TOP_S, TOP_E, top_block(cfg), anchor)
            box = changes_box(key, cfg)
            if box:
                s = replace_or_insert(s, CH_S, CH_E, box, re.escape(TOP_E))
        elif "rows" in cfg:
            s = set_head(s, cfg, url)
            s = re.sub(r"(<header class=\"hero\">.*?<h1>).*?(</h1>)", lambda m: m.group(1) + e(cfg["h1"]) + m.group(2), s, count=1, flags=re.S)
            s = re.sub(r'(<header class="hero">\s*<div class="wrap">\s*<div class="eyebrow">).*?(</div>)', lambda m: m.group(1) + e(cfg["eyebrow"]) + m.group(2), s, count=1, flags=re.S)
            s = re.sub(cfg["snippet_re"], "", s, count=1, flags=re.S)
            for old, new in [("browse vetted local installers", "compare top-rated local installers"),
                             ("Browse vetted local installers", "Compare top-rated local installers"),
                             ("Browse vetted local heat pump installers", "Compare top-rated local heat pump installers"),
                             ("you see every vetted installer in your city", "you see the top-rated installers in your city")]:
                s = s.replace(old, new)
            s = replace_or_insert(s, TOP_S, TOP_E, top_block(cfg), r"<header class=\"hero\">.*?</header>")
            box = changes_box(key, cfg)
            if box:
                s = replace_or_insert(s, CH_S, CH_E, box, re.escape(TOP_E))
        else:
            box = changes_box(key, cfg)
            if box:
                s = replace_or_insert(s, CH_S, CH_E, box, r"<h1\b.*?</h1>.*?</(?:section|header)>")
        if cfg.get("eyebrow"):
            s = unify_hero(s, cfg)
        f.write_text(s, encoding="utf-8")
        print("updated", key)


if __name__ == "__main__":
    main()
