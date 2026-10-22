#!/usr/bin/env python3
"""/heating-assistance/: one page listing every heating and energy bill assistance program we have verified, 2026-10-22.
Built from data/state-topics/*-heating-assistance.json (the 13 pages) and the facts each names, so status, dates and amounts
can never differ from the pages it links to. Programs we could not read on an official page are listed as "not yet", never guessed.
Usage: python3 scripts/build_heating_assistance_hub.py && python3 scripts/post_steps.py"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import page_kit as kit  # noqa: E402
from status_pills import STATUS  # noqa: E402

e = html.escape
PATH = "/heating-assistance/"
ORDER = {"active": 0, "upcoming": 1, "check": 2, "info": 3, "waitlist": 4, "paused": 5, "closed": 6}
NOT_YET = [("New York (HEAP)", "The state's HEAP page returned a blank page when we tried to read it."),
           ("Minnesota (Energy Assistance Program)", "The state site showed a bot check, so we could not read it."),
           ("Saskatchewan and the other provinces", "We have not found and read an official program page yet."),
           ("BC Climate Action Tax Credit", "It has ended; see the BC page.")]


def main():
    facts = kit.load_facts()
    rows = []
    for f in sorted((ROOT / "data/state-topics").glob("*-heating-assistance.json")):
        d = json.loads(f.read_text())
        fact = facts[d["facts"][0]]
        country = "Canada" if d["path"].startswith("/ca/") else "United States"
        rows.append({"region": d["hub_name"], "country": country, "path": d["path"], "program": fact["program"], "status": fact["status"],
                     "amount": fact.get("amount") or d["cards"][0]["amount"], "dates": fact.get("dates", ""), "badge": d["badge"]})
    rows.sort(key=lambda r: (ORDER[r["status"]], r["country"] != "Canada", r["region"]))
    n_open = sum(1 for r in rows if r["status"] == "active")

    def tbl(rs):
        return ('<div style="overflow-x:auto;"><table class="compare-table"><thead><tr><th>Region</th><th>Program</th><th>Status</th><th>What it pays</th><th>Dates</th></tr></thead><tbody>'
                + "".join(f'<tr><td><a href="{r["path"]}">{e(r["region"])}</a></td><td>{e(r["program"])}</td><td>{e(STATUS[r["status"]][0])}</td><td>{e(r["amount"])}</td><td>{e(r["dates"])}</td></tr>' for r in rs)
                + "</tbody></table></div>")

    ca = [r for r in rows if r["country"] == "Canada"]
    us = [r for r in rows if r["country"] == "United States"]
    nyl = "".join(f"<li><b>{e(a)}:</b> {e(b)}</li>" for a, b in NOT_YET)
    article = f"""<p>If your heating bill is hard to pay, there is probably a program for it. In the United States most states run the Low Income Home Energy Assistance Program, called LIHEAP. In Canada each province runs its own help. This page lists every program we have checked on an official page, with the status and dates. {n_open} are open today. Click a region for the full rules and how to apply.</p>
<h2 id="us">United States</h2>
<p>LIHEAP is paid for by the federal government and run by each state, so the dates, income limits and amounts differ. Most states open in the fall and close in spring or when the money runs out.</p>
{tbl(us)}
<h2 id="canada">Canada</h2>
<p>Canadian programs are provincial or utility programs. Some pay a one-time amount, some give a credit on your bill, and some help seniors.</p>
{tbl(ca)}
<h2 id="how">How to apply for any of them</h2>
<ul><li>Check the income rule for your household size on the official page we link from each region.</li>
<li>Gather proof of income, a recent bill and ID for everyone in the home.</li>
<li>Apply early. Many programs run until the money is gone.</li>
<li>If your heat is about to be shut off, call the agency and say so first. Many have emergency help.</li>
<li>Never pay anyone for a grant. Illinois warns that LIHEAP does not charge a fee, and the same goes for the other programs here.</li></ul>
<h2 id="not-yet">Not on this page yet</h2>
<p>We list a program only after reading it on an official page. These are missing, and why:</p>
<ul>{nyl}</ul>
<h2 id="lower">Help is for this winter. Rebates cut the bill for good.</h2>
<p>Bill help covers a gap. Insulation, a heat pump or a smart thermostat lowers what you use every year, and some programs give them free to lower-income households. See the <a href="/calculator/">rebate calculator</a> for your province or state, or the <a href="/programs/national-heat-pump-rebate/do-i-qualify/">federal heat pump rebate checker</a> in Canada.</p>
<h2 id="faq">Common questions</h2>
{kit.faq({"faq": FAQ})}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Each program was read on its official page on October 21, 2026; the region pages list the sources.</p>"""
    title = "Heating Bill Help 2026-27: LIHEAP and Programs by State and Province"
    desc = f"Every heating and energy bill assistance program we have checked, with status, dates and amounts: {n_open} open now. LIHEAP by state and help in Canada."
    hero = {"badge": f"{n_open} programs open now", "h1": "Heating Bill Help for 2026-27, by State and Province",
            "lead": "Where to get help paying the winter heating bill, what each program pays, and when it opens. Every program is checked on an official page."}
    trail = [("Home", "/"), ("Heating bill help", PATH)]
    lds = kit.ld_scripts([kit.article_ld(title, desc, "2026-10-22", PATH), kit.breadcrumb_ld(trail, home_slash=True), kit.faq_ld({"faq": FAQ})])
    kit.write_page(PATH, title, desc, lds, navfooter.render_nav("", ""), kit.breadcrumb(trail), kit.hero(hero), None, article, navfooter.render_footer("", "", "", PATH), extra_css=CSS)
    print("built", PATH, len(rows), "programs")


FAQ = [("What is LIHEAP?", "The Low Income Home Energy Assistance Program is a federal program that helps lower-income households in the United States pay heating and cooling bills. Each state runs its own version."),
       ("Do I have to be on welfare to get help?", "Not in most programs. Pennsylvania, for example, says you do not need to be on public assistance. Check the rules for your state or province."),
       ("When should I apply?", "As soon as your program opens. Several run until funding is gone, and New Jersey processes applications first come, first served."),
       ("Is there help in Canada?", "Yes. Examples are the BC Hydro Customer Crisis Fund, Ontario's Electricity Support Program, the Yukon Pioneer Utility Grant and Newfoundland and Labrador's Home Heating Supplement."),
       ("Does the federal government help pay heating bills in Canada?", "Not through a program we have verified. The federal heat pump rebate and the Greener Homes Affordability upgrades lower future bills; they do not pay a current one.")]

CSS = """<style>
.compare-table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--card-rule);margin:12px 0;font-size:14.5px}
.compare-table th,.compare-table td{padding:9px 11px;text-align:left;border-bottom:1px solid var(--card-rule);vertical-align:top}
.compare-table th{background:#f5efe5;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-soft)}
</style>"""

if __name__ == "__main__":
    main()
