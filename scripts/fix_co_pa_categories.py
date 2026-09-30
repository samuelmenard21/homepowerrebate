#!/usr/bin/env python3
"""Second pass on Colorado and Pennsylvania category pages, checked against primary sources on 2026-09-29:
- Xcel Colorado EV charger page: up to $500 ($800 DIC standard, $2,300 income-qualified); EV Accelerate At Home closed Jul 14, 2026.
- Xcel Solar*Rewards 2026 page: only IQ/DIC products, $1 per watt up to 10 kW AC; everyone else gets net metering only.
- Xcel 2026 rebate sheet (program page): insulation 30% of cost, up to $500 attic, $350 wall, $400 air sealing.
- PPL portal and PECO pages (see /programs/ pages): current per-item amounts. Old Phase IV amounts (Penelec, Duquesne) expired May 31, 2026.
- Federal 25D battery/solar credit ended for spending after Dec 31, 2025.
Each fix swaps the card amount, the lead paragraph (also used in the FAQ and structured data) and the same text on the city hub card."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FED = "the 30% federal tax credit ended for systems paid for after December 31, 2025"

FIXES = []
for c in ("denver", "aurora", "boulder"):
    FIXES += [
        ("us/co", c, "ev-charger", "Up to $500",
         "Xcel Energy pays up to $500 toward a Level 2 charger and the wiring for a 240-volt circuit. Income-qualified customers can get up to $2,300, and homes in a Disproportionately Impacted Community can get a standard rebate up to $800. You enroll in Xcel's Optimize Your Charge program first. EV Accelerate At Home closed to new Colorado applicants on July 14, 2026. Rebates are first come, first served.", "open"),
        ("us/co", c, "solar", "No cash rebate",
         "For most homes, Xcel's 2026 Solar*Rewards residential program has no upfront rebate. You get net metering credit for the extra power you send to the grid. Income-qualified homes and homes in a Disproportionately Impacted Community can get $1 per watt of installed solar, up to 10 kW. Also, " + FED + ".", "limited"),
        ("us/co", c, "insulation", "Up to $500 attic",
         "Xcel Energy pays 30% of the cost of insulation and air sealing: up to $500 for attic insulation, $350 for wall insulation and $400 for air sealing. Homes heated with Xcel natural gas get 1.5 times the standard rebate. Check Xcel's 2026 rebate sheet before you book the work.", "open"),
    ]
PPL = ("PPL Electric pays $225 or $325 for an air source heat pump, $225 for a ductless mini-split and $500 for a ground source heat pump. "
       "Which amount you get depends on your offer, and PPL's Check Best Offers tool shows it. PPL says equipment installed on or before May 31, 2026 is no longer eligible, so check the portal for your install date.")
PECO_HP = ("PECO pays $200 or $300 for an air source heat pump and $150 or $300 for a ductless mini-split, depending on the efficiency rating. "
           "The higher amount needs 17.1 SEER2 or better. Apply within 90 days of buying or installing. Income-qualified homes may get more through PECO's income-eligible programs, so ask PECO.")
FIXES += [
    ("us/pa", "allentown", "heat-pump", "$225 to $500", PPL, "open"),
    ("us/pa", "philadelphia", "heat-pump", "$200 to $300", PECO_HP, "open"),
    ("us/pa", "philadelphia", "water-heater", "$350",
     "PECO pays $350 for an ENERGY STAR certified heat pump water heater in a home with PECO electric service. Apply within 90 days of buying or installing.", "open"),
    ("us/pa", "erie", "heat-pump", "Confirm status",
     "Penelec's Act 129 heat pump rebate of up to $500 covered purchases through May 31, 2026. We could not confirm the amounts for the program that started in June 2026, so check Penelec's rebate portal before you buy.", "limited"),
    ("us/pa", "pittsburgh", "heat-pump", "Confirm status",
     "Duquesne Light's earlier $200 heat pump rebate closed to new purchases on May 31, 2026. We could not confirm the amounts for the new program that started in June 2026. Call Duquesne Light at 1-888-998-9478 to check.", "limited"),
    ("us/pa", "pittsburgh", "insulation", "Confirm status",
     "Duquesne Light's earlier insulation adder closed to new purchases on May 31, 2026. We could not confirm the amounts for the new program that started in June 2026. Call Duquesne Light at 1-888-998-9478 to check.", "limited"),
]
for c in ("allentown", "erie", "philadelphia", "pittsburgh"):
    FIXES.append(("us/pa", c, "battery", "No rebate found",
                  "We found no battery storage rebate from the local utility or the state, and " + FED + ".", "limited"))

CARD = re.compile(r'(<div class="rebate-card[^"]*">\s*<span class="program-status status-)\w+("[^>]*>)\w+(</span>)')


def swap_page(f, old_amt, new_amt, old_lead, new_lead, status):
    t = f.read_text(encoding="utf-8")
    o = t
    if old_lead:
        t = t.replace(old_lead, new_lead)
        t = t.replace(old_lead.replace('"', '\\"'), new_lead)
    if old_amt and old_amt != new_amt:
        t = t.replace(f'<div class="amount-badge">{old_amt}</div>', f'<div class="amount-badge">{new_amt}</div>')
        t = t.replace(f'<div class="amount">{old_amt}</div>', f'<div class="amount">{new_amt}</div>')
        t = t.replace(f'<div class="finder-amount">{old_amt}</div>', f'<div class="finder-amount">{new_amt}</div>')
        t = t.replace(old_amt, new_amt)
    if t != o:
        f.write_text(t, encoding="utf-8")
    return t != o


EXTRA = [
    ("Xcel Energy's Solar Rewards program pays $300 per kW, capped at $1,500 per home. The federal 30% solar tax credit expired after December 31, 2025 and no longer applies to 2026 installs.",
     "For most homes there is no upfront solar rebate from Xcel in 2026, only net metering credit. Income-qualified and Disproportionately Impacted Community homes can get $1 per watt up to 10 kW. The federal 30% solar tax credit expired after December 31, 2025 and no longer applies to 2026 installs."),
    ("The standard Xcel Solar Rewards payout is $300 per kW, capped at $1,500. Income-qualified households can get significantly more through Xcel's IQDIC track - up to $1 per watt, or roughly $5,000 on a typical 5kW system.",
     "For most homes there is no upfront Xcel solar rebate in 2026, only net metering credit. Income-qualified households can get $1 per watt through Xcel's IQ and DIC track, or roughly $5,000 on a typical 5 kW system."),
    ("The standard Xcel Solar Rewards payout is $300 per kW, capped at $1,500. Income-qualified households can get significantly more through Xcel's IQDIC track \u2014 up to $1 per watt, or roughly $5,000 on a typical 5kW system.",
     "For most homes there is no upfront Xcel solar rebate in 2026, only net metering credit. Income-qualified households can get $1 per watt through Xcel's IQ and DIC track, or roughly $5,000 on a typical 5 kW system."),
    ("standard $300/kW rate", "standard net-metering-only terms"),
    ("The standard Xcel Solar Rewards payout applies: $300 per kW installed, capped at $1,500.", "There is no upfront Xcel solar rebate for most homes in 2026, only net metering credit."),
    ("The standard Xcel Solar Rewards payout applies here: $300 per kW installed, capped at $1,500.", "There is no upfront Xcel solar rebate for most homes in 2026, only net metering credit."),
]


def main():
    for c in ("denver", "aurora", "boulder"):
        f = ROOT / "us/co" / c / "solar" / "index.html"
        t = f.read_text(encoding="utf-8")
        for a, b in EXTRA:
            t = t.replace(a, b)
        f.write_text(t, encoding="utf-8")
    for region, city, cat, new_amt, new_lead, status in FIXES:
        f = ROOT / region / city / cat / "index.html"
        h = f.read_text(encoding="utf-8")
        am = re.search(r'<div class="amount">(.*?)</div>', h, re.S)
        lead = re.search(r'<div class="amount">.*?</div>\s*</div>\s*<p>(.*?)</p>', h, re.S)
        if not am or not lead:
            print("SKIP (no card)", f)
            continue
        old_amt = re.sub(r"\s+", " ", am.group(1)).strip()
        raw_lead = lead.group(1)
        old_lead = re.sub(r"^.*?&mdash; ", "", raw_lead, count=1) if "&mdash;" in raw_lead[:80] else raw_lead
        old_lead = re.sub(r"^<strong>.*?</strong>\s*", "", old_lead)
        if raw_lead.startswith("<strong>") and "&mdash;" in raw_lead[:120]:
            old_lead = raw_lead.split("&mdash; ", 1)[1]
        changed = swap_page(f, old_amt, new_amt, old_lead, new_lead, status)
        # status colour on the main card
        t = f.read_text(encoding="utf-8")
        t2 = CARD.sub(lambda m: m.group(1) + status + m.group(2) + status + m.group(3), t, count=1)
        if t2 != t:
            f.write_text(t2, encoding="utf-8")
        # same text on the city hub card
        hub = ROOT / region / city / "index.html"
        ht = hub.read_text(encoding="utf-8")
        hn = ht.replace(old_lead, new_lead) if old_lead else ht
        if old_amt != new_amt:
            hn = hn.replace(f'<div class="amount">{old_amt}</div>', f'<div class="amount">{new_amt}</div>').replace(f'<div class="finder-amount">{old_amt}</div>', f'<div class="finder-amount">{new_amt}</div>')
        if hn != ht:
            hub.write_text(hn, encoding="utf-8")
        print(("ok  " if changed else "same"), region, city, cat, "|", old_amt, "->", new_amt, "| hub" if hn != ht else "")


if __name__ == "__main__":
    main()
