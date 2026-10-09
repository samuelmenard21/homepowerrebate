#!/usr/bin/env python3
"""Link the federal National Heat Pump Rebate pages from the Canadian hubs, every Canadian city heat pump page and the blog index.
Injected blocks sit between FED-HP-START/END (hubs, city pages) or FED-POSTS-START/END (blog index) so re-runs replace them.
City and hub text is province-specific and states only facts in data/verified-facts/federal.json and the province facts. Run after any generator that rewrites those pages.
Usage: python3 scripts/add_federal_links.py"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402

S, E = "<!-- FED-HP-START -->", "<!-- FED-HP-END -->"
PS, PE = "<!-- FED-POSTS-START -->", "<!-- FED-POSTS-END -->"
P = "/programs/national-heat-pump-rebate/"
BOX = 'style="max-width:880px;margin:18px auto;padding:14px 20px;background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;font-size:15px;line-height:1.6;"'
LEAD = "Federal heat pump rebate coming in early 2027: up to $10,000 for households below the median income and $2,000 for other eligible homeowners. "
HUB = {
    "bc": ("Ottawa says the new rebate can be combined with provincial programs, which in BC means BC Hydro (up to $4,000 for a whole-home heat pump replacing electric heat) and CleanBC for income-qualified households. BC Hydro's $1,000 bonus ends with installs finished by October 31, 2026.",
           [("Should you wait?", "should-you-wait-federal-heat-pump-rebate"), ("What stacks in BC", "federal-heat-pump-rebate-stacking-by-province")]),
    "on": ("Ottawa says it can be combined with provincial programs. In Ontario that is Home Renovation Savings, which pays $1,250 per ton up to $7,500 for electric, oil, propane and wood homes and $500 per ton up to $2,000 for gas homes.",
           [("Should you wait?", "should-you-wait-federal-heat-pump-rebate"), ("Heat pump on a gas home", "heat-pump-natural-gas-home-federal-rebate")]),
    "ab": ("Alberta has no province-wide heat pump rebate that we could verify, and the earlier federal oil-to-heat-pump program closed on July 31, 2026, so the new rebate may matter most here. Cold winters mean most homes should keep backup heat.",
           [("Heat pumps in prairie cold", "heat-pumps-alberta-saskatchewan-cold-federal-rebate"), ("Gas homes", "heat-pump-natural-gas-home-federal-rebate")]),
    "ns": ("Nova Scotia already has Efficiency Nova Scotia heat pump rebates and the free HomeWarming program for lower incomes. Ottawa says the federal rebate can be combined with provincial programs, but the rules of each program still apply.",
           [("What stacks", "federal-heat-pump-rebate-stacking-by-province"), ("Renters and condos", "federal-heat-pump-rebate-renters-condos-landlords")]),
}
CITY = {
    "bc": "BC Hydro and CleanBC rebates can already be claimed, and Ottawa says the federal rebate can be combined with provincial programs.",
    "on": "Home Renovation Savings pays now, and Ottawa says the federal rebate can be combined with provincial programs.",
    "ab": "Alberta has no province-wide heat pump rebate we could verify, so the federal rebate may be the main one.",
    "ns": "Efficiency Nova Scotia pays per ton now, and Ottawa says the federal rebate can be combined with provincial programs.",
}
NAMES = {"st-albert": "St. Albert", "fort-st-john": "Fort St. John", "niagara-falls": "Niagara Falls", "sault-ste-marie": "Sault Ste. Marie"}
POSTS = [("should-you-wait-federal-heat-pump-rebate", "Should You Wait for the Federal Heat Pump Rebate?", "The rebate launches early 2027. Deadlines that are real today and a simple rule for deciding."),
         ("federal-heat-pump-rebate-stacking-by-province", "Federal + Provincial Heat Pump Rebates: What Stacks", "BC, Ontario, Nova Scotia and Alberta, with sample stacks."),
         ("heat-pump-natural-gas-home-federal-rebate", "Heat Pump on a Natural Gas Home: Is It Worth It?", "Run your own numbers, and why dual fuel can make sense."),
         ("heat-pumps-alberta-saskatchewan-cold-federal-rebate", "Heat Pumps in Alberta and Saskatchewan: Cold, Cost, Rebates", "Measured performance at -21 C and what to buy."),
         ("fair-heat-pump-quote-canada", "How to Get a Fair Heat Pump Quote in Canada", "Seven steps that work with any rebate."),
         ("federal-heat-pump-rebate-renters-condos-landlords", "Federal Heat Pump Rebate: Renters, Condos and Landlords", "What is confirmed and which programs cover tenants.")]


def put(t, block, s=S, e=E):
    t = re.sub(re.escape(s) + r"[\s\S]*?" + re.escape(e) + r"\n?", "", t)
    i = t.find("<!-- PROGRAM-LINKS-START -->")
    if i < 0:
        m = re.search(r'<section class="hero"[\s\S]*?</section>', t)
        i = m.end() if m else navfooter.content_insert_point(t)
    return t[:i] + s + block + e + "\n" + t[i:] if i >= 0 else t


def main():
    n = 0
    for code, (text, links) in HUB.items():
        f = ROOT / "ca" / code / "index.html"
        t = f.read_text(encoding="utf-8")
        ln = " &middot; ".join(f'<a href="/blog/{s}/">{html.escape(a)}</a>' for a, s in links)
        blk = f'<section {BOX}><b>{LEAD}</b>{text} <a href="{P}">Everything confirmed so far</a> &middot; {ln}</section>'
        f.write_text(put(t, blk), encoding="utf-8"); n += 1
    for f in sorted((ROOT / "ca").glob("*/*/heat-pump/index.html")):
        code, slug = f.parts[-4], f.parts[-3]
        if code not in CITY:
            continue
        city = NAMES.get(slug, slug.replace("-", " ").title())
        t = f.read_text(encoding="utf-8")
        blk = f'<p {BOX}><b>{html.escape(city)}: {LEAD}</b>{CITY[code]} <a href="{P}">Read what is confirmed</a> or <a href="/blog/should-you-wait-federal-heat-pump-rebate/">decide whether to wait</a>.</p>'
        f.write_text(put(t, blk), encoding="utf-8"); n += 1
    f = ROOT / "blog" / "index.html"
    t = f.read_text(encoding="utf-8")
    cards = "".join(f'<a href="/blog/{s}/" class="post-card"><span class="tag">Federal rebate</span><h3>{html.escape(a)}</h3><p>{html.escape(b)}</p></a>\n' for s, a, b in POSTS)
    t = re.sub(re.escape(PS) + r"[\s\S]*?" + re.escape(PE) + r"\n?", "", t)
    m = re.search(r'(<a href="/blog/[^"]+/" class="post-card">)', t)
    t = t[:m.start()] + PS + cards + PE + "\n" + t[m.start():]
    f.write_text(t, encoding="utf-8")
    print("updated", n, "hubs and city pages plus blog index")


if __name__ == "__main__":
    main()
