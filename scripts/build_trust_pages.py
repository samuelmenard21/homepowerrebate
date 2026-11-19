#!/usr/bin/env python3
"""Trust pages (2026-11-19): /author/sam-menard/ and /how-we-check-rebate-facts/.

The author page reads data/author.json (only facts Sam has confirmed; empty `credentials` are not shown). The method page
describes how data/verified-facts/*.json works (status, verified_on, source_url) and its counts are computed from those
files, so they cannot drift. Usage: python3 scripts/build_trust_pages.py && python3 scripts/post_steps.py
"""
import html
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import page_kit as kit  # noqa: E402
from status_pills import STATUS  # noqa: E402

e = html.escape
METHOD = "/how-we-check-rebate-facts/"
TODAY = "2026-11-19"


def author_page():
    a = json.loads((ROOT / "data/author.json").read_text())
    path = a["path"]
    bg = "".join(f"<p>{e(x)}</p>" for x in a["background"])
    cred = ""
    if a["credentials"]:
        cred = "<h2 id=\"credentials\">Credentials</h2><ul>" + "".join(f"<li>{e(c)}</li>" for c in a["credentials"]) + "</ul>"
    article = f"""<p>I am Sam Menard, the person who runs HomePowerRebate and writes its pages. This page says who I am, what I do here and how to tell me when something is wrong.</p>
<h2 id="background">My background</h2>
{bg}
{cred}
<h2 id="role">What I do on this site</h2>
<ul><li>I decide which programs and cities we cover. We add a place only when its programs can be read on an official page.</li>
<li>I write the guides and set the rules for how pages are built. The numbers come from our <a href="{METHOD}">fact files</a>, not from memory.</li>
<li>I do not sell installation, and nobody can pay to be ranked higher. Installers are ranked by Google reviews. See <a href="/installers/how-we-rank/">how we rank installers</a>.</li></ul>
<h2 id="limits">What I am not</h2>
<p>I am not a utility, a government office or an installer, and I do not give engineering advice. For sizing, safety and wiring, talk to a licensed installer or a registered energy advisor. Every rebate amount links to the official page it came from, so you can check it yourself before you spend money.</p>
<h2 id="how">How I check the numbers</h2>
<p>Each rebate amount has a status, a source link and the date we last read the official page. If we cannot read a program on an official page, we say so instead of guessing. The full process is on <a href="{METHOD}">How we check rebate facts</a>.</p>
<h2 id="corrections">Corrections</h2>
<p>If a number is wrong or out of date, email <a href="mailto:{e(a['email'])}">{e(a['email'])}</a> with the page and the official link. I fix the facts file, rebuild the page and show the new check date. Programs change often, so please tell me.</p>
<p><a href="/about">About HomePowerRebate</a> &middot; <a href="{METHOD}">How we check rebate facts</a></p>"""
    title = "Sam Menard: Who Runs HomePowerRebate"
    desc = "Who writes HomePowerRebate, his background, what he does on the site, what he does not do, and how to send a correction."
    person = {"@context": "https://schema.org", "@type": "ProfilePage", "mainEntity": {**kit.AUTHOR, "jobTitle": a["job_title"], "worksFor": {"@type": "Organization", "name": "HomePowerRebate", "url": kit.BASE},
              "description": " ".join(a["background"][:2]), "email": a["email"]}}
    trail = [("Home", "/"), ("About", "/about"), ("Sam Menard", path)]
    lds = kit.ld_scripts([person, kit.breadcrumb_ld(trail)])
    hero = {"badge": "Author", "h1": "Sam Menard", "lead": "Founder of HomePowerRebate. I write the guides and check the rebate numbers."}
    kit.write_page(path, title, desc, lds, navfooter.render_nav("", ""), kit.breadcrumb(trail), kit.hero(hero), None, article,
                   navfooter.render_footer("", "", "", path))


def method_page():
    facts = kit.load_facts()
    n = len(facts)
    st = Counter(f["status"] for f in facts.values())
    srcs = len({f.get("source_url") for f in facts.values() if f.get("source_url")})
    files = len(list((ROOT / "data/verified-facts").glob("*.json")))
    dated = [f["verified_on"] for f in facts.values() if f.get("verified_on")]
    oldest, newest = min(dated), max(dated)
    ex = facts["federal-0-national-heat-pump-rebate"]
    rows = "".join(f"<tr><td>{e(STATUS[s][0])}</td><td>{st[s]}</td><td>{e(MEANING[s])}</td></tr>" for s in STATUS if st.get(s))
    article = f"""<p>Every rebate amount on HomePowerRebate comes from a record in a plain data file. The record holds the amount, the status, the date we read it and the official page it came from. A page shows what the record says. If the record changes, the page changes.</p>
<h2 id="record">What is in each record</h2>
<table class="compare-table"><thead><tr><th>Field</th><th>What it holds</th><th>Example (the federal heat pump rebate)</th></tr></thead><tbody>
<tr><td>amount</td><td>What the program pays, as the official page says it</td><td>{e(ex['amount'])}</td></tr>
<tr><td>status</td><td>Open, starts soon, on hold, paused, check first, closed or info</td><td>{e(STATUS[ex['status']][0])}</td></tr>
<tr><td>verified_on</td><td>The day we last read the official page</td><td>{e(ex['verified_on'])}</td></tr>
<tr><td>source_url</td><td>The official page we read</td><td><a href="{e(ex['source_url'])}" rel="noopener">{e(ex['source_url'].split('/')[2])}</a></td></tr></tbody></table>
<h2 id="steps">The five steps</h2>
<ol><li><b>Find the official page.</b> We use the utility, the province, the state or the government. We do not copy an amount from another website, or from one of our own city pages.</li>
<li><b>Read it in full.</b> Amount, who qualifies, what must be installed, who must install it, the dates and the limits.</li>
<li><b>Write the record.</b> Amount, status, date read and source link go in the fact file. If we could not read the page, the status is "Check first" and no amount is shown as sure.</li>
<li><b>Build the pages from the record.</b> Rebate cards, tables and the <a href="/calculator/">calculators</a> read the same file, so two pages cannot show two different amounts.</li>
<li><b>Read it again every month.</b> When a program closes or changes, we change its status or amount in the record, and every page that uses it updates with a new date.</li></ol>
<h2 id="count">The record today</h2>
<p>{n} records from {srcs} official pages, in {files} files, one per province, state or topic. The oldest check is {e(oldest)} and the newest is {e(newest)}.</p>
<table class="compare-table"><thead><tr><th>Status</th><th>Records</th><th>What it means</th></tr></thead><tbody>{rows}</tbody></table>
<h2 id="not">What we do not do</h2>
<ul><li>We do not show a rebate we could not read on an official page.</li>
<li>We do not let money change a ranking. Installers are ranked by Google reviews. See <a href="/installers/how-we-rank/">how we rank installers</a>.</li>
<li>We do not promise a rebate. Programs run out of money, change rules and close. Always confirm on the official page before you sign.</li>
<li>We do not guess a closing date. If the program page gives none, we say none is published.</li></ul>
<h2 id="wrong">If you find a mistake</h2>
<p>Email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a> with the page and the official link. We correct the record first, then the pages. Pages are written by <a href="/author/sam-menard/">Sam Menard</a>.</p>
<h2 id="faq">Common questions</h2>
{kit.faq({"faq": FAQ})}"""
    title = "How We Check Rebate Facts: Sources, Dates, Status"
    desc = f"How every HomePowerRebate amount is read from an official page, dated and kept up to date. {n} records, {srcs} official pages, checked monthly."
    trail = [("Home", "/"), ("About", "/about"), ("How we check rebate facts", METHOD)]
    lds = kit.ld_scripts([kit.article_ld(title, desc, TODAY, METHOD), kit.breadcrumb_ld(trail), kit.faq_ld({"faq": FAQ})])
    hero = {"badge": f"{n} sourced records", "h1": "How We Check Rebate Facts",
            "lead": "Every amount has an official source, a status and the date we read it. Here is how that works."}
    kit.write_page(METHOD, title, desc, lds, navfooter.render_nav("", ""), kit.breadcrumb(trail), kit.hero(hero), None, article,
                   navfooter.render_footer("", "", "", METHOD), extra_css=CSS)


MEANING = {"active": "Open now; the official page says people can apply", "upcoming": "Announced, not open yet",
           "waitlist": "Full or on hold; the official page says so", "paused": "Stopped for now",
           "check": "We could not confirm it; no amount is shown as sure", "closed": "Ended; we keep it so you do not chase it",
           "info": "Helpful program information, not a home rebate"}
FAQ = [("Where do your rebate amounts come from?", "From the program's own official page: the utility, province, state or government. Each record links to that page."),
       ("How often do you check?", "Every source is read again each month. A program that closes or changes gets a new status or amount and a new check date."),
       ("What does 'Check first' mean?", "We could not confirm the program on an official page, so we do not show an amount as sure. Confirm with the program before you buy."),
       ("Can an installer pay to be listed higher?", "No. Installers are ranked by Google reviews and money never changes a ranking."),
       ("Who do I tell about a mistake?", "Email hello@homepowerrebate.com with the page and the official link.")]
CSS = """<style>
.compare-table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--card-rule);margin:12px 0;font-size:14.5px}
.compare-table th,.compare-table td{padding:9px 11px;text-align:left;border-bottom:1px solid var(--card-rule);vertical-align:top}
.compare-table th{background:#f5efe5;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink-soft)}
</style>"""

if __name__ == "__main__":
    author_page()
    method_page()
    kit.save_dates() if hasattr(kit, "save_dates") else None
    print("built", METHOD, "and /author/sam-menard/")
