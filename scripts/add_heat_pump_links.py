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
    "ca/ns/index.html":
        "<b>HARP heating rebate:</b> " + A("/programs/nova-scotia-heating-assistance-rebate-harp/", "check your HARP status and payment dates") + " &middot; " + A("/blog/nova-scotia-harp-heating-assistance-rebate-explained/", "what HARP is and who qualifies") + ".",
    "ca/index.html":
        "<b>Heat pump rebates by province:</b> " + " &middot; ".join([A("/ca/bc/heat-pump/", "BC"), A("/ca/on/heat-pump/", "Ontario"), A("/ca/ab/heat-pump/", "Alberta"), A("/ca/mb/heat-pump/", "Manitoba"), A("/ca/ns/heat-pump/", "Nova Scotia"), A("/ca/qc/heat-pump/", "Quebec") + " (" + A("/fr/qc/thermopompe/", "en fran&ccedil;ais") + ")"]) + ". " + A("/programs/national-heat-pump-rebate/", "Federal rebate guide"),
    # the homepage links these itself (scripts/build_home.py, "Heat pump rebates by province" and the guides list)
    "blog/ontario-smart-thermostats-100-rebate-compared/index.html":
        "<b>Also in Ontario:</b> " + A("/blog/ontario-home-renovation-savings-deadlines-2026/", "Home Renovation Savings deadlines (Nov 30 and Dec 31, 2026)") + " &middot; " + A("/ca/on/heat-pump/", "Ontario heat pump rebates"),
    "us/ma/index.html":
        "<b>Before year end:</b> " + A("/blog/ma-ny-year-end-rebate-deadlines-2026/", "Massachusetts and New York rebate deadlines for 2026") + " (EV charger rebates end Nov 1 to Dec 31). Nearby: " + A("/us/me/heat-pump/", "Maine heat pump rebates") + " &middot; " + A("/us/ct/heat-pump/", "Connecticut heat pump rebates") + ".",
    "us/ny/index.html":
        "<b>Before year end:</b> " + A("/blog/ma-ny-year-end-rebate-deadlines-2026/", "Massachusetts and New York rebate deadlines for 2026") + " (heat pump water heater offers end Nov 30 and Dec 31).",
}
HERO = re.compile(r'(<section class="hero[\s\S]*?</section>|<header class="[^"]*hub-hero[\s\S]*?</header>)')


def main():
    n = 0
    for rel, html in JOBS.items():
        p = ROOT / rel
        t = p.read_text(encoding="utf-8")
        # homepage: a class, not inline styles (externalize_inline_styles.py owns the homepage's inline styles)
        blk = S + (f'<section class="hp-links">{html}</section>' if rel == "index.html" else f"<section {BOX}>{html}</section>") + E
        # already there: refresh it in place, so other boxes placed after the hero keep their order (2026-10-17)
        if S in t and E in t:
            new = re.sub(re.escape(S) + r"[\s\S]*?" + re.escape(E), lambda _: blk, t, count=1)
            if new != t:
                p.write_text(new, encoding="utf-8")
            n += 1
            continue
        # homepage: after the HOME-HERO block, never inside it (build_home_hero.py rewrites that block and dropped the box on 2026-10-16)
        m = re.search(re.escape("<!-- HOME-HERO-END -->"), t) if rel == "index.html" else HERO.search(t)
        if not m:
            print("no hero in", rel)
            continue
        t = t[:m.end()] + "\n" + blk + "\n" + t[m.end():]
        p.write_text(t, encoding="utf-8")
        n += 1
    print("linked", n, "pages")


if __name__ == "__main__":
    main()
