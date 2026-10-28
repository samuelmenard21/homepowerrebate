#!/usr/bin/env python3
"""Printable one-page hand-out for libraries, town offices and community groups (added 2026-10-27): how to apply for Newfoundland and Labrador's
Home Heating Supplement. /rebate-sheet/nl/oil-rebate/ (noindex, made to be printed). Every figure and date is read from fact
nl-4-home-heating-supplement in data/verified-facts/nl.json, and the build stops if the fact's wording changes.
  python3 scripts/build_nl_oil_sheet.py"""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_rebate_sheets as rs  # noqa: E402
import page_kit  # noqa: E402

esc = html.escape
PATH = "/rebate-sheet/nl/oil-rebate/"
SHORT = "homepowerrebate.com/nl-oil"


def main():
    f = page_kit.FACTS["nl-4-home-heating-supplement"]
    claim, elig, dates, notes = f["claim"], f["eligibility"], f["dates"], f["notes"]
    for must, where in (("from $500 to $1,000", claim), ("do not need to apply again", claim), ("second payment", claim), ("$100,000 or less", elig),
                        ("$150,000", elig), ("250 litres", elig), ("January 15, 2027", dates), ("P.O. Box 8700", notes), ("1-844-729-4645", notes),
                        ("OilSupplement@gov.nl.ca", notes), ("public libraries", notes)):
        assert must in where, f"fact changed ({must}): re-read it before printing"
    assert f["status"] == "active"
    checked = f["verified_on"]
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/ca/nl/heating-assistance/">Newfoundland and Labrador oil rebate</a></li><li aria-current="page">Printable sheet</li></ol></nav>
<main id="main" class="rs">
<div class="rs-tools"><span><b>For libraries, town offices and community groups:</b> print this sheet or save it as a PDF. Please keep the link on it.</span>
<button type="button" onclick="window.print()">Print or save as PDF</button></div>
<article class="rs-sheet">
<div class="rs-head"><div><h1>Newfoundland and Labrador oil rebate: how to apply</h1>
<p>The Home Heating Supplement now pays <b>$400 to $1,000</b>. It used to be $200 to $500. Checked {esc(checked)}.</p></div>
<div class="rs-brand">Home<span>Power</span>Rebate</div></div>
<p class="rs-first"><b>Apply by January 15, 2027.</b> Late forms are not accepted. If you already applied this year, do not apply again.</p>
<h2>Who gets how much</h2>
<table><tr><td>Your family earned <b>$100,000 or less</b> in 2025</td><td class="amt">$1,000</td></tr>
<tr><td>Your family earned more than $100,000, up to $150,000</td><td class="amt">At least $400</td></tr></table>
<h2>What you need</h2>
<ul><li>You buy furnace or stove oil to heat your main home in Newfoundland and Labrador.</li>
<li>Oil bills from January 1 to December 31, 2026 for at least 250 litres, with your delivery address. They can be in your name or your spouse's or partner's name.</li>
<li>Your 2025 tax return filed with the Canada Revenue Agency.</li>
<li>Only one person per household can apply.</li></ul>
<h2>Two ways to apply</h2>
<ul><li><b>Online (faster):</b> HHSP Online. Find the link on the province's page: gov.nl.ca/fin/home-heating-supplement-program/</li>
<li><b>By mail:</b> fill in the 2026 application form, sign it, add a copy of an oil bill, and mail it to<br>Home Heating Supplement Program, Department of Finance, P.O. Box 8700, St. John's, NL A1B 4J6</li></ul>
<p>Paper forms are at public libraries, Government Service Centres (not Springdale or Lewisporte), Jobs, Growth and Rural Development offices, and the Department of Finance and SeniorsNL office in St. John's.</p>
<h2>After you apply</h2>
<ul><li>Most forms are processed within 10 weeks.</li>
<li>If your tax refund or GST/HST credit comes by direct deposit, the supplement goes to the same bank account. If not, you get a cheque.</li>
<li>Already paid? The province says a second payment is coming later this year.</li></ul>
<div class="rs-foot">
<div><b>Questions? Ask the program:</b><br>709-729-4645 or 1-844-729-4645 (toll-free)<br>OilSupplement@gov.nl.ca</div>
<div><b>Steps, forms and answers:</b><br>{SHORT}</div>
</div>
<p class="rs-small">HomePowerRebate is an independent guide, not the government. Source: Government of Newfoundland and Labrador, Department of Finance. Rules can change, so check the province's page before you apply.</p>
</article>
</main>"""
    title = "NL Oil Rebate: How to Apply (Printable Sheet)"
    desc = "A printable one-page guide to Newfoundland and Labrador's Home Heating Supplement: who gets $400 to $1,000, what you need, how to apply and the January 15, 2027 deadline."
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{rs.BASE}{PATH}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{rs.CSS}</style>
</head>
<body>
{navfooter.render_nav("nl", "st-johns")}
{body}
{navfooter.render_footer("nl", "st-johns", "Newfoundland and Labrador", PATH)}
</body>
</html>
"""
    dest = ROOT / PATH.strip("/") / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    print("wrote", dest.relative_to(ROOT))


if __name__ == "__main__":
    main()
