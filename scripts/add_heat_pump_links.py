#!/usr/bin/env python3
"""Link the new heat pump and deadline pages from pages that already get search traffic (Nova Scotia HARP, hubs, homepage, Ontario thermostat post).
A new page that only sits in the sitemap ranks slowly. Each block sits right after the page's hero between HP-LINKS-START/END, so re-runs replace it.
Usage: python3 scripts/add_heat_pump_links.py"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S, E = "<!-- HP-LINKS-START -->", "<!-- HP-LINKS-END -->"
BOX = 'style="max-width:880px;margin:18px auto;padding:14px 20px;background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;font-size:15px;line-height:1.6;"'
A = lambda u, t: f'<a href="{u}">{t}</a>'
JOBS = {
    "programs/nova-scotia-heating-assistance-rebate-harp/index.html":
        "<b>Replacing your heating system?</b> " + A("/ca/ns/heat-pump/", "Nova Scotia heat pump rebates: $300 to $600 a ton") + " &middot; " + A("/programs/national-heat-pump-rebate/", "the new federal heat pump rebate (early 2027)") + " &middot; " + A("/ca/ns/", "all Nova Scotia rebates"),
    "ca/index.html":
        "<b>Heat pump rebates by province:</b> " + " &middot; ".join([A("/ca/bc/heat-pump/", "BC"), A("/ca/on/heat-pump/", "Ontario"), A("/ca/ab/heat-pump/", "Alberta"), A("/ca/ns/heat-pump/", "Nova Scotia"), A("/ca/qc/heat-pump/", "Quebec") + " (" + A("/fr/qc/thermopompe/", "en fran&ccedil;ais") + ")"]) + ". " + A("/programs/national-heat-pump-rebate/", "Federal rebate guide"),
    "index.html":
        "<b>New in Canada:</b> heat pump rebate guides for " + " &middot; ".join([A("/ca/bc/heat-pump/", "BC"), A("/ca/on/heat-pump/", "Ontario"), A("/ca/ab/heat-pump/", "Alberta"), A("/ca/ns/heat-pump/", "Nova Scotia"), A("/ca/qc/heat-pump/", "Quebec")]) + ", plus " + A("/programs/national-heat-pump-rebate/", "Ottawa's new heat pump rebate") + " and " + A("/blog/ma-ny-year-end-rebate-deadlines-2026/", "Massachusetts and New York year-end deadlines") + ".",
    "blog/ontario-smart-thermostats-100-rebate-compared/index.html":
        "<b>Also in Ontario:</b> " + A("/blog/ontario-home-renovation-savings-deadlines-2026/", "Home Renovation Savings deadlines (Nov 30 and Dec 31, 2026)") + " &middot; " + A("/ca/on/heat-pump/", "Ontario heat pump rebates"),
    "us/ma/index.html":
        "<b>Before year end:</b> " + A("/blog/ma-ny-year-end-rebate-deadlines-2026/", "Massachusetts and New York rebate deadlines for 2026") + " (EV charger rebates end Nov 1 to Dec 31).",
    "us/ny/index.html":
        "<b>Before year end:</b> " + A("/blog/ma-ny-year-end-rebate-deadlines-2026/", "Massachusetts and New York rebate deadlines for 2026") + " (heat pump water heater offers end Nov 30 and Dec 31).",
}
HERO = re.compile(r'(<section class="hero[\s\S]*?</section>|<header class="[^"]*hub-hero[\s\S]*?</header>)')


def main():
    n = 0
    for rel, html in JOBS.items():
        p = ROOT / rel
        t = p.read_text(encoding="utf-8")
        t = re.sub(re.escape(S) + r"[\s\S]*?" + re.escape(E) + r"\n?", "", t)
        m = HERO.search(t)
        if not m:
            print("no hero in", rel)
            continue
        t = t[:m.end()] + "\n" + S + f"<section {BOX}>{html}</section>" + E + "\n" + t[m.end():]
        p.write_text(t, encoding="utf-8")
        n += 1
    print("linked", n, "pages")


if __name__ == "__main__":
    main()
