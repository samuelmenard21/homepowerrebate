#!/usr/bin/env python3
"""/home-battery-rebates/: the national home battery rebate hub, 2026-10-22 (Google Trends: "home energy storage" +160%).
Different from /batteries/ (product guides): this page answers "what will someone pay me for a home battery, where". Built from
  - the open battery programs in calculator/data/<code>.json (amount, first rule, source, checked date; amounts in the region's currency),
  - powerscore-data.json (the cities with the biggest open battery rebate, in US dollars so Canada and the US compare),
  - the existing battery pages we link to (state pages, Ontario city pages, product guides).
Nothing is typed in by hand except the explanations, which state only what those programs' rules say.
Usage: python3 scripts/build_battery_rebate_hub.py && python3 scripts/post_steps.py"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_rebate_sheets as sheets  # noqa: E402
import page_kit as kit  # noqa: E402
from status_pills import STATUS  # noqa: E402

e = html.escape
PATH = "/home-battery-rebates/"
PAGES = {"co": "/us/co/battery/", "ma": "/us/ma/battery/", "nj": "/us/nj/battery/", "ny": "/us/ny/battery/", "pa": "/us/pa/battery/", "vt": "/us/vt/battery/", "wa": "/us/wa/battery/", "on": "/ca/on/", "bc": "/ca/bc/", "ca": "/us/ca/"}


def programs():
    rows = []
    for f in sorted((ROOT / "calculator/data").glob("*.json")):
        d = json.loads(f.read_text())
        for p in d["programs"]:
            if p.get("upgrade") != "battery" or p.get("status") not in ("active", "upcoming", "check"):
                continue
            amt = sheets.amount_text(p.get("amount") or {}, d.get("currency", "USD")) or ((p.get("amount") or {}).get("label") or "")
            cur = d.get("currency", "USD")
            rows.append({"code": d["code"], "region": d["name"], "cur": cur, "name": p["name"], "amount": amt, "max": (p.get("amount") or {}).get("max", 0) * (0.73 if cur == "CAD" else 1),
                         "rule": (p.get("rules") or "").split(". ")[0].rstrip(".") + ".", "status": p["status"], "src": p.get("source_url", ""), "v": p.get("verified_on", "")})
    rows.sort(key=lambda r: (r["status"] != "active", -r["max"], r["region"]))
    return rows


def main():
    ps = programs()
    n_open = sum(1 for r in ps if r["status"] == "active")
    tr = "".join(f'<tr><td><a href="{PAGES.get(r["code"], "/calculator/" + r["code"] + "/")}">{e(r["region"])}</a></td><td>{e(r["name"])} <a href="{e(r["src"])}" rel="noopener" target="_blank">Source</a></td>'
                 f'<td>{e(r["amount"] + (" CAD" if r["cur"] == "CAD" and r["amount"].startswith("Up to $") else ""))}</td><td>{e(STATUS[r["status"]][0])}</td><td>{e(r["rule"])}</td><td>{e(r["v"])}</td></tr>' for r in ps)
    d = json.loads((ROOT / "powerscore-data.json").read_text())
    cities = [c for c in d["leaderboard_by_category"]["battery"] if c.get("status") == "open" and c.get("dollar_value", 0) > 0]
    # powerscore leaderboard rows carry the city's own-currency value; use the per-city usd value from the regions block
    usd = {}
    for rk, reg in d["regions"].items():
        for slug, c in reg["cities"].items():
            v = c["categories"].get("battery", {})
            if v.get("status") == "open" and v.get("usd_value", 0) > 0:
                usd[(rk, slug)] = (v["usd_value"], c["label"], c["url"], reg["label"])
    best = sorted(usd.values(), key=lambda x: (-x[0], x[1]))
    top_v = best[0][0]
    tied = [b for b in best if b[0] == top_v]
    nxt = [b for b in best if b[0] < top_v][:8]
    n_cities = len(best)
    top_line = ", ".join(f'<a href="{b[2]}">{e(b[1])}</a>' for b in tied[:4]) + (f" and {len(tied) - 4} more" if len(tied) > 4 else "")
    nx = "".join(f'<li><a href="{b[2]}">{e(b[1])}</a>, {e(b[3])}: ${round(b[0]):,}</li>' for b in nxt)
    article = f"""<p>A home battery stores power for outages and for the hours when electricity costs most. Whether someone helps pay for one depends almost entirely on where you live. This page lists the battery programs we have checked on an official page, what each pays, and the rule that trips people up. {n_open} are open today, and we score {n_cities} cities with an open battery rebate or incentive.</p>
<h2 id="open">Battery programs open now</h2>
<p>Amounts are the most each program pays and, in Canada, are in Canadian dollars. Many pay less, or pay only if you join a program or add solar.</p>
<div style="overflow-x:auto;"><table class="compare-table"><thead><tr><th>Region</th><th>Program</th><th>Pays</th><th>Status</th><th>Main rule</th><th>Checked</th></tr></thead><tbody>{tr}</tbody></table></div>
<h2 id="kinds">Three kinds of battery help</h2>
<p><b>A rebate toward the purchase.</b> BC Hydro, Ontario's Home Renovation Savings, SMUD in California and Xcel in Colorado pay a set amount per kWh or kW, up to a cap. Ontario's pays only with a new solar system in the same project. BC Hydro's pays more when you join Peak Saver.</p>
<p><b>Payments for letting the utility use your battery.</b> Mass Save's ConnectedSolutions in Massachusetts and the Puget Sound Energy flex program in Washington pay you for sharing the battery during peak events. They reward the battery's use, so they are not a rebate on the price.</p>
<p><b>Income-qualified programs.</b> California's SGIP is aimed at income-qualified, medical baseline and high fire-threat households, and the program page says much of it is on hold, so check its status first.</p>
<h2 id="rules">Rules that catch people out</h2>
<ul><li><b>The brand can decide it.</b> BC Hydro's rebate is not for Tesla batteries. New Jersey's PSE&amp;G program lists only certain Tesla and Enphase models. Check the program's list before you buy. See our guide on <a href="/questions/is-tesla-powerwall-eligible-bc-hydro-rebate/">whether a Tesla Powerwall is eligible for the BC Hydro rebate</a>.</li>
<li><b>Order matters.</b> Several programs need approval or enrollment before or soon after install. BC Hydro's higher amount needs Peak Saver within 14 days of installation.</li>
<li><b>Solar may be required.</b> Ontario pays for a battery only with new solar.</li>
<li><b>Caps and leases.</b> Amounts are capped, often at half the cost, and leases are often excluded.</li></ul>
<h2 id="best">Where the biggest battery rebates are</h2>
<p>Using US dollars so Canada and the US compare, the biggest open battery rebate today is ${round(top_v):,}, in {top_line}. Next:</p>
<ul>{nx}</ul>
<p>The full ranking by upgrade is on the <a href="/powerscore/leaderboard/">national leaderboard</a>.</p>
<h2 id="next">Where to go next</h2>
<ul><li><a href="/batteries/">Home battery guides: specs and rebates by product</a></li><li>Pick your place: {" · ".join(f'<a href="{PAGES[c]}">{n}</a>' for c, n in [("bc", "British Columbia"), ("on", "Ontario"), ("co", "Colorado"), ("ma", "Massachusetts"), ("nj", "New Jersey"), ("ny", "New York"), ("pa", "Pennsylvania"), ("vt", "Vermont"), ("wa", "Washington"), ("ca", "California")])}</li><li><a href="/calculator/">Rebate calculator for your province or state</a></li></ul>
<h2 id="faq">Common questions</h2>
{kit.faq({"faq": FAQ})}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Each program's source link and the date we last checked it are in the table. Biggest-rebate figures come from <a href="/powerscore/">PowerScore</a>, generated {e(d["generated"])}.</p>"""
    title = "Home Battery Rebates 2026: Every Program by Region"
    desc = f"Home battery rebates and incentives in Canada and the US: {n_open} programs open now, what each pays, the rules and where the biggest rebates are."
    hero = {"badge": f"{n_open} programs open now", "h1": "Home Battery Rebates in 2026: What Each Program Pays",
            "lead": "Where a home battery gets help paying for itself, how much, and the rule that decides it. Every program is checked on an official page."}
    trail = [("Home", "/"), ("Batteries", "/batteries/"), ("Battery rebates", PATH)]
    lds = kit.ld_scripts([kit.article_ld(title, desc, "2026-10-22", PATH), kit.breadcrumb_ld(trail, home_slash=True), kit.faq_ld({"faq": FAQ})])
    kit.write_page(PATH, title, desc, lds, navfooter.render_nav("", ""), kit.breadcrumb(trail), kit.hero(hero), None, article, navfooter.render_footer("", "", "", PATH), extra_css=CSS)
    print("built", PATH, len(ps), "programs", n_cities, "cities")


FAQ = [("Is there a rebate for a home battery?", "In some places, yes. BC Hydro, Ontario, SMUD in California and Xcel in Colorado pay toward the purchase, while Massachusetts and Washington pay you for sharing the battery with the utility. The table above lists each with its rules."),
       ("Does a Tesla Powerwall qualify?", "It depends on the program. BC Hydro's rebate is not for Tesla batteries. Xcel in Colorado lists the Tesla Powerwall. New Jersey's PSE&G program lists certain Tesla and Enphase models. Check the program's own list before you buy."),
       ("Do I need solar to get a battery rebate?", "Ontario's program pays for a battery only with new solar. Other programs, such as BC Hydro's, pay for a battery on its own, with a different amount depending on whether you join Peak Saver."),
       ("Is a battery worth it without a rebate?", "That depends on your outages and your electricity rates. A rebate or a utility payment shortens the payback, but we do not give a payback figure without your own numbers."),
       ("What is the difference between a rebate and a utility payment?", "A rebate lowers what you pay up front. A program like ConnectedSolutions pays you over time for letting the utility use your battery at peak hours.")]

CSS = """<style>
.compare-table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--card-rule);margin:12px 0;font-size:14px}
.compare-table th,.compare-table td{padding:9px 11px;text-align:left;border-bottom:1px solid var(--card-rule);vertical-align:top}
.compare-table th{background:#f5efe5;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-soft)}
</style>"""

if __name__ == "__main__":
    main()
