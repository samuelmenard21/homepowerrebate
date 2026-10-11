#!/usr/bin/env python3
"""Answer-first titles and descriptions for pages that rank in the top 10 but earn almost no clicks (the Nova Scotia fix, applied where it fits).
Edits title, meta description, og/twitter tags and JSON-LD names in place, so later site-wide layers stay intact; generated pages also carry the same text in their data files.
Usage: python3 scripts/update_answer_first_heads.py"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEADS = {}
PAGES = {
    "blog/mass-save-rejection-guide": (
        "Mass Save Rejected Your Rebate? Fix and Resubmit (2026)",
        "Mass Save rejected your heat pump rebate? A common cause is the 2026 R-410A refrigerant rule. Here is how to check it, fix it and resubmit."),
    "blog/mass-save-rebate-delayed-what-to-do": (
        "Mass Save Rebate Delayed? Check Status After 12 Weeks",
        "Mass Save says 8 to 12 weeks. How to check your rebate status, why delays happen, and who to call after 12 weeks: Mass Save, the DPU, the Attorney General."),
    "blog/new-york-empower-plus-guide": (
        "EmPower+ NY 2026: Income Limits, Amounts, How to Apply",
        "EmPower+ gives lower-income New Yorkers free home upgrades: up to $12,000 upstate or $14,000 downstate, or 50% off. Income limits and how to apply."),
    "blog/ontario-heat-pump-rebate-rejection-mistakes": (
        "Ontario Heat Pump Rebate Rejected? 6 Mistakes to Avoid",
        "Skipping pre-approval, an unlisted unit or the wrong fuel tier can cost you thousands. Six Ontario heat pump rebate mistakes and how to avoid them."),
    "blog/massachusetts-towns-not-eligible-mass-save": (
        "41 Massachusetts Towns Not Eligible for Mass Save (List)",
        "41 Massachusetts towns have their own electric utility and can't use Mass Save rebates. Check if yours is one, and see what you can get instead."),
    "blog/smud-rebate-breakdown": (
        "SMUD Rebates 2026: Heat Pump $1,000 to $3,000 and More",
        "Every SMUD home rebate in 2026: heat pump $1,000 to $3,000, water heater $3,000 to $4,000, EV charger up to $850, battery $300 per kWh. Read Oct 2, 2026."),
    "us/vt/rutland": (
        "Rutland VT Home Energy Rebates 2026: Efficiency Vermont",
        "Rutland, Vermont rebates for 2026: heat pump discounts, weatherization up to $3,000 ($7,000 if income-eligible), battery and EV rebates. 69% of homes burn oil."),
}
LEAD_EDITS = {
    "blog/mass-save-rejection-guide": ("There's a good chance this comes down to one specific, fixable rule most contractors forget to mention. Here's how to fix it.",
                                       "The most common fixable cause is the 2026 R-410A refrigerant rule that most contractors forget to mention. Check it first, then fix it and resubmit."),
    "blog/mass-save-rebate-delayed-what-to-do": ("You did everything right.",
                                                 "Short answer: Mass Save says 8 to 12 weeks, and if it has been longer you can check your status and escalate. You did everything right."),
}


EXTRA = {
    "blog/ontario-heat-pump-rebate-rejection-mistakes": [
        ("6 Mistakes That Get Your Ontario Heat Pump Rebate Rejected", "Ontario Heat Pump Rebate Rejected? 6 Mistakes to Avoid"),
        ("how to avoid them. Six real ways", "how to avoid them. These are six real ways"),
    ],
}


def main():
    for rel, (title, desc) in PAGES.items():
        p = ROOT / rel / "index.html"
        s = p.read_text(encoding="utf-8")
        old_t = html.unescape(re.search(r"<title>(.*?)</title>", s, re.S).group(1))
        old_d = html.unescape(re.search(r'name="description" content="([^"]*)', s).group(1))
        for old, new in ((old_t, title), (old_d, desc)):
            for a in {old, html.escape(old, quote=True), html.escape(old, quote=False), old.replace("&", "\\u0026")}:
                s = s.replace(a, new if "&" not in a or "&amp;" not in a else html.escape(new, quote=False))
        # exact-string safety: both title and description must now be present
        assert title in html.unescape(s) and desc in html.unescape(s), rel
        for a, b in EXTRA.get(rel, []):
            s = s.replace(a, b)
        if rel in LEAD_EDITS:
            a, b = LEAD_EDITS[rel]
            s = s.replace(a, b, 1)
        p.write_text(s, encoding="utf-8")
        print("updated", rel)


if __name__ == "__main__":
    main()
