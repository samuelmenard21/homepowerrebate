#!/usr/bin/env python3
"""PA solar pages claimed a live "PA Sunshine Solar" rebate (up to 35%/$17,500) and a 30% federal credit. The Sunshine
program stopped taking applications in 2013 (PA DEP) and the 30% federal homeowner credit (25D) ended for spending after
Dec 31, 2025. PECO's $500 solar rebate window closed April 2026. This rewrites those claims; no amount is invented."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTE = ("Pennsylvania's Sunshine Solar rebate stopped taking applications in 2013, and the 30% federal homeowner solar tax credit "
        "ended for systems paid for after December 31, 2025, so we found no active state or federal cash rebate for home solar.")
COMMON = [
    ('<div class="amount-badge">Up to 35% / $17,500</div>', '<div class="amount-badge">No rebate found</div>'),
    ('<div class="amount">Up to 35% / $17,500</div>', '<div class="amount">No active rebate found</div>'),
    ("PA Sunshine Solar Program, <a", "PA DEP Sunshine Solar Program (closed 2013), <a"),
    ("</a>, PA Sunshine Solar Program</p>", "</a>, PA DEP Sunshine Solar Program (closed 2013)</p>"),
]
PAGES = {
    "allentown": [
        ("Allentown solar gets PA Sunshine (up to 35%/$17,500) plus PPL net metering — but PPL's 2026 credit change makes timing your install matter. Real numbers.",
         "Allentown solar has no active state or federal cash rebate we can confirm, but PPL net metering still pays. PPL's credit change makes timing matter."),
        ("Allentown solar gets PA Sunshine (up to 35%/$17,500) plus PPL net metering — but PPL's 2026 credit change makes timing your install matter.",
         "Allentown solar has no active cash rebate we can confirm, but PPL net metering still pays. Timing matters."),
        ("Yes, but it comes from the state, not PPL Electric. The PA Sunshine Solar Program rebates up to 35% of a residential system's cost, capped near $17,500, first-come first-served, stacking with the 30% federal tax credit.",
         "Not one we can confirm. " + NOTE + " PPL Electric does not run a solar panel rebate."),
        ("The rebate itself is a state program: PA Sunshine Solar rebates up to 35% of a residential system's cost, capped around $17,500 for systems up to 10kW, first-come first-served, stacking with the 30% federal tax credit. PPL Electric doesn't fund it — PPL's role is net metering, and that's where the real time pressure is for Allentown homeowners right now.",
         NOTE + " PPL Electric doesn't fund a panel rebate either. Its role is net metering, and that's where the real time pressure is for Allentown homeowners right now."),
        ("Yes, but it comes from the state, not PPL Electric. The PA Sunshine Solar Program rebates up to 35% of a residential system's cost, capped near $17,500, first-come first-served, stacking with the 30% federal tax credit.",
         "Not one we can confirm. " + NOTE),
        ("The rebate, and a deadline that matters more", "No cash rebate, and a deadline that matters more"),
    ],
    "erie": [
        ("Erie solar: PA Sunshine rebate (up to 35%/$17,500), a separate $500 Penelec solar water heating rebate, and what lake-effect cloud cover means for output.",
         "Erie solar: no active state or federal cash rebate we can confirm, a separate $500 Penelec solar water heating rebate, and what lake-effect cloud cover means for output."),
        ("Erie solar: PA Sunshine rebate (up to 35%/$17,500), a separate $500 Penelec solar water heating rebate, and what lake-effect cloud means for output.",
         "Erie solar: no active cash rebate we can confirm, a separate $500 Penelec solar water heating rebate, and what lake-effect cloud means for output."),
        ("Yes, through the state, not Penelec directly. PA Sunshine Solar rebates up to 35% of a residential system's cost, capped near $17,500, first-come first-served, and it stacks with the 30% federal tax credit.",
         "Not one we can confirm. " + NOTE),
        ("Start with the base: PA Sunshine Solar rebates up to 35% of a residential system's cost, capped around $17,500 for systems up to 10kW, first-come first-served, stacking with the 30% federal tax credit. Penelec",
         "Start with the base: " + NOTE + " Penelec"),
        ("The state rebate, plus a Penelec program most people miss", "No panel rebate, but a Penelec program most people miss"),
    ],
    "philadelphia": [
        ("Philadelphia solar stacks three rebates: PA Sunshine (up to 35%/$17,500), PECO's $500 Act 129 rebate, and the city's $0.20/watt program. Real numbers.",
         "Philadelphia solar: PECO's $500 solar rebate window closed in April 2026, and the city's $0.20 per watt program needs checking. We found no active state or federal rebate."),
        ("Philadelphia solar stacks three rebates: PA Sunshine (up to 35%/$17,500), PECO's $500 Act 129 rebate, and the city's $0.20/watt program.",
         "Philadelphia solar: PECO's $500 solar rebate window closed in April 2026, and the city's $0.20 per watt program needs checking."),
        ("Potentially three: the statewide PA Sunshine Solar Program (up to 35%, capped near $17,500, first-come first-served), PECO's own $500 Act 129 solar rebate for systems with Permission to Operate between September 2024 and April 2026, and the City of Philadelphia's $0.20/watt local rebate paid to installers on systems completed within city limits. All three stack with the 30% federal tax credit.",
         "Fewer than the old figures said. " + NOTE + " PECO's $500 Act 129 solar rebate covered systems with Permission to Operate between September 2024 and April 2026, so that window has closed. The City of Philadelphia has offered $0.20 per watt through the Philadelphia Energy Authority, but check phila.gov/solar-rebate that it is still open before you count on it."),
        ("Philadelphia is one of the few PA cities where the math genuinely involves three separate programs instead of one. The base is the statewide <strong>PA Sunshine Solar Program</strong>, up to 35% of a residential PV project's cost, capped around $17,500 for systems up to 10kW, awarded first-come first-served. On top of that, <strong>PECO</strong> pays a $500 Act 129 rebate for systems that get Permission to Operate between September 2024 and April 2026, plus up to $400 toward the second meter net metering requires.",
         "Philadelphia used to layer a few programs, and most have ended. " + NOTE + " <strong>PECO</strong> paid a $500 Act 129 rebate for systems that got Permission to Operate between September 2024 and April 2026, and that window has closed."),
        ("Finally, the <strong>City of Philadelphia's own solar rebate</strong> pays installers $0.20 per watt for systems completed inside city limits",
         "The <strong>City of Philadelphia's own solar rebate</strong> has paid installers $0.20 per watt for systems completed inside city limits"),
        ("All three stack with the 30% federal tax credit.", "Check with the Philadelphia Energy Authority that it is still open; we could not confirm a 2026 budget."),
        ("Three programs, not one", "Most old programs have ended"),
    ],
    "pittsburgh": [
        ("No Duquesne Light rebate, but Pittsburgh solar still qualifies for PA Sunshine (up to 35%/$17,500), 1:1 net metering, and SRECs. Real numbers.",
         "No Duquesne Light or state cash rebate we can confirm, but Pittsburgh solar still earns 1:1 net metering and SRECs. Real numbers."),
        ("No Duquesne Light rebate, but Pittsburgh solar still qualifies for PA Sunshine (up to 35%/$17,500), 1:1 net metering, and SRECs.",
         "No cash rebate we can confirm, but Pittsburgh solar still earns 1:1 net metering and SRECs."),
        ("No — Duquesne Light doesn't currently run a utility-branded solar hardware rebate. What Pittsburgh homeowners actually draw on is the statewide PA Sunshine Solar Program, up to 35% of project cost capped near $17,500, awarded first-come first-served.",
         "No. Duquesne Light doesn't run a solar hardware rebate. " + NOTE),
        ("Duquesne Light doesn't currently run its own solar hardware rebate — the money in Pittsburgh comes from the statewide PA Sunshine Solar Program instead, up to 35% of a residential system's cost, capped around $17,500 for systems up to 10kW, awarded first-come first-served. That stacks with the 30% federal solar tax credit.",
         "Duquesne Light doesn't run its own solar hardware rebate. " + NOTE + " The savings now come from net metering and SRECs."),
        ("Duquesne Light isn't where the rebate comes from", "No cash rebate, so the savings come from your bill"),
    ],
}


def main():
    for city, table in PAGES.items():
        f = ROOT / "us/pa" / city / "solar" / "index.html"
        t = f.read_text(encoding="utf-8")
        for a, b in COMMON + table:
            t = t.replace(a, b)
        f.write_text(t, encoding="utf-8")
        left = [k for k in ("17,500", "Sunshine (", "30% federal", "35%") if k in t]
        print(city, "leftover:", left)


if __name__ == "__main__":
    main()
