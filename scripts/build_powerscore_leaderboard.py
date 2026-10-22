#!/usr/bin/env python3
"""/powerscore/leaderboard/: the national leaderboard, 2026-10-22. Ranks every city in powerscore-data.json by the dollars its open rebates
could pay (US dollars, Canadian amounts converted at the data file's rate, so Canada and the US sit on one list), then shows the champion
for each upgrade and for each province and state. Ties share a rank and are shown as ties, never broken by name. Nothing is typed in by
hand: every figure and city link comes from powerscore-data.json (built by build_powerscore.py from the verified facts).
Usage: python3 scripts/build_powerscore_leaderboard.py && python3 scripts/post_steps.py"""
import html
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import page_kit as kit  # noqa: E402

e = html.escape
PATH = "/powerscore/leaderboard/"
TOP_N = 25


def usd(v):
    return "$" + format(round(v), ",")


def ranked(rows):
    """rows: (value, payload) high to low -> (rank, value, payload) with ties sharing the lowest rank number."""
    rows = sorted(rows, key=lambda r: -r[0])
    return [(1 + sum(1 for x in rows if x[0] > v), v, p) for v, p in rows]


def main():
    d = json.loads((ROOT / "powerscore-data.json").read_text())
    cats = d["category_labels"]
    cities = []
    for rk, region in d["regions"].items():
        for slug, c in region["cities"].items():
            cities.append({"rk": rk, "region": region["label"], "country": region["country"], "slug": slug, **c})
    n = len(cities)
    fx = d["cad_to_usd"]
    gen = d["generated"]

    # ---- 1. overall
    rk_all = ranked([(c["potential_usd"], c) for c in cities])
    top = [r for r in rk_all if r[0] <= TOP_N]
    cut = top[-1][1] if top else 0
    rows = "".join(f'<tr><td>{"T-" if sum(1 for x in rk_all if x[0] == rank) > 1 else ""}{rank}</td><td><a href="{c["url"]}">{e(c["label"])}</a></td><td>{e(c["region"])}</td>'
                   f'<td>{usd(v)}</td><td>{c["open_count"]} of {len(cats)}</td></tr>' for rank, v, c in top)
    tied_out = sum(1 for r in rk_all if r[1] == cut) - sum(1 for r in top if r[1] == cut)
    overall = (f'<div style="overflow-x:auto;"><table class="compare-table"><thead><tr><th>Rank</th><th>City</th><th>Province or state</th><th>Most open rebates could pay</th><th>Upgrades open</th></tr></thead><tbody>{rows}</tbody></table></div>'
               + (f"<p>{tied_out} more cities are tied at {usd(cut)}.</p>" if tied_out > 0 else ""))

    # ---- 2. champions by upgrade
    champ = ""
    for cat, label in cats.items():
        rows_c = [(c["categories"][cat]["usd_value"], c) for c in cities if c["categories"].get(cat, {}).get("status") == "open" and c["categories"][cat]["usd_value"] > 0]
        if not rows_c:
            continue
        rr = ranked(rows_c)
        best = rr[0][1]
        winners = [p for r, v, p in rr if v == best]
        shown = ", ".join(f'<a href="{c["url"]}">{e(c["label"])}</a>' for c in winners[:4]) + (f" and {len(winners) - 4} more" if len(winners) > 4 else "")
        nxt = [(v, p) for r, v, p in rr if v < best][:3]
        nx = "; ".join(f'<a href="{p["url"]}">{e(p["label"])}</a> {usd(v)}' for v, p in nxt)
        champ += f"<li><strong>{e(label)}:</strong> {shown} at {usd(best)} ({len(rows_c)} of {n} cities have an open program)." + (f" Next: {nx}." if nx else "") + "</li>"

    # ---- 3. champion in each province and state
    reg_rows = []
    for rk, region in d["regions"].items():
        cs = [c for c in cities if c["rk"] == rk]
        best = max(c["potential_usd"] for c in cs)
        w = [c for c in cs if c["potential_usd"] == best]
        reg_rows.append((best, region["label"], region["country"], w, len(cs)))
    reg_rows.sort(key=lambda r: (-r[0], r[1]))
    reg_html = "".join(f'<tr><td>{e(lab)}</td><td>{e(cty)}</td><td>' + ", ".join(f'<a href="{c["url"]}">{e(c["label"])}</a>' for c in w[:3]) + (f" and {len(w) - 3} more" if len(w) > 3 else "")
                       + f"</td><td>{usd(best)}</td><td>{nc}</td></tr>" for best, lab, cty, w, nc in reg_rows)
    regions = f'<div style="overflow-x:auto;"><table class="compare-table"><thead><tr><th>Province or state</th><th>Country</th><th>Best city</th><th>Most open rebates could pay</th><th>Cities scored</th></tr></thead><tbody>{reg_html}</tbody></table></div>'

    # ---- 4. Canada and the United States
    sides = {}
    for cty in ("Canada", "United States"):
        cs = [c for c in cities if c["country"] == cty]
        sides[cty] = (len(cs), statistics.median(c["potential_usd"] for c in cs), max(cs, key=lambda c: c["potential_usd"]))
    (nc, mc, bc), (nu, mu, bu) = sides["Canada"], sides["United States"]
    cmp_ = (f"<p>We score {nc} Canadian and {nu} US cities. The middle Canadian city has up to {usd(mc)} in open rebates and the middle US city up to {usd(mu)}. "
            f'The Canadian city with the most is <a href="{bc["url"]}">{e(bc["label"])}</a> ({usd(bc["potential_usd"])}); the US city with the most is <a href="{bu["url"]}">{e(bu["label"])}</a> ({usd(bu["potential_usd"])}).</p>')

    leader = rk_all[0][2]
    t1 = [p for r, v, p in rk_all if r == 1]
    top_line = ", ".join(e(c["label"]) for c in t1[:3])
    article = f"""<h2 id="top">The 25 best cities for open home energy rebates</h2>
<p>Each city's total adds the biggest open program for every upgrade we track: heat pump, insulation, solar, battery, water heater, thermostat, EV charger, and windows and doors. It is the most a household could collect if it did everything and qualified for the top tier of every program, so use it to compare places, not to budget. Right now {top_line} {"leads" if len(t1) == 1 else "lead"} the list at {usd(leader["potential_usd"])}.</p>
{overall}
<h2 id="upgrade">Best city for each upgrade</h2>
<p>These are the cities with the biggest open rebate for each upgrade. Cities with the same amount share the top spot, and we show them as a tie.</p>
<ul>{champ}</ul>
<h2 id="region">Best city in each province and state</h2>
<p>The same total, with the winner in each of the {len(d["regions"])} regions we cover. A city can lead its own province and still sit far down the national list, because programs are set by provinces, states and utilities more than by cities.</p>
{regions}
<h2 id="country">Canada and the United States</h2>
{cmp_}
<p>Canadian amounts are converted to US dollars at {fx} so both countries share one list.</p>
<h2 id="read">How to read this leaderboard</h2>
<p>Only programs that are open today count. A program that is closed, paused or about to start adds nothing, so a city can drop when a program closes and climb when a new one opens. The biggest amounts are often for lower-income households, such as the CleanBC and Yukon income-qualified heat pump programs, so your own number can be much smaller. Where two cities share a utility and a province, they usually tie. For the score that also weighs how many upgrades are covered, see <a href="/powerscore/">PowerScore</a>, and for two cities side by side, the head-to-head comparisons linked from the same page.</p>
<p>What moved since last month? See the <a href="/data-release/">monthly data release</a>.</p>
<p>Want your own number? Use the <a href="/calculator/">rebate calculator</a> or <a href="/get-quotes/">see my rebates</a>.</p>
<h2 id="faq">Common questions</h2>
{kit.faq({"faq": FAQ})}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Data generated {e(gen)} from the program amounts we verify on official pages. Details are in the <a href="/powerscore/">PowerScore method</a>.</p>"""
    hero = {"badge": f"{n} cities ranked", "h1": "The Best Places for Home Energy Rebates in Canada and the US",
            "lead": f"We add up every open rebate in {n} cities across {len(d['regions'])} provinces and states, in one currency, and rank them. See who leads overall, for each upgrade and in each province or state."}
    title = "Best Places for Home Energy Rebates: National Leaderboard"
    desc = f"Ranking of {n} Canadian and US cities by the most their open home energy rebates could pay, with the best city for each upgrade and each province or state."
    trail = [("Home", "/"), ("PowerScore", "/powerscore/"), ("Leaderboard", PATH)]
    lds = kit.ld_scripts([kit.article_ld(title, desc, gen, PATH), kit.breadcrumb_ld(trail, home_slash=True), kit.faq_ld({"faq": FAQ})])
    kit.write_page(PATH, title, desc, lds, navfooter.render_nav("", ""), kit.breadcrumb(trail), kit.hero(hero), None, article,
                   navfooter.render_footer("", "", "", PATH), extra_css=CSS)
    print("built", PATH, "cities", n)


FAQ = [("Which city has the best home energy rebates?", "It depends on the measure. By the most open rebates could pay in total, the leaderboard above shows the leaders today. By upgrade, each category has its own winner."),
       ("How is the leaderboard different from PowerScore?", "PowerScore is a 0 to 100 score that weighs how many upgrades are covered. The leaderboard ranks cities by dollars alone, so it answers a simpler question: where is the most money on the table."),
       ("Why are Canadian cities converted to US dollars?", "So both countries sit on one list. Canadian amounts use an approximate exchange rate, so treat a small gap as a tie."),
       ("Can I get the full amount shown for my city?", "Probably not. The total adds the biggest open program for every upgrade, and many of the biggest amounts are for lower-income households. Run the calculator for your own numbers.")]

CSS = """<style>
.compare-table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--card-rule);margin:16px 0;font-size:15px}
.compare-table th,.compare-table td{padding:10px 12px;text-align:left;border-bottom:1px solid var(--card-rule);vertical-align:top}
.compare-table th{background:#f5efe5;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-soft)}
.compare-table tr:last-child td{border-bottom:0}
</style>"""

if __name__ == "__main__":
    main()
