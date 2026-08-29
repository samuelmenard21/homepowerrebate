#!/usr/bin/env python3
"""Insert an 'Estimated Energy Cost' pill onto every city page's hero area.

Reads the same ENERGY_COST data used by the PowerScore leaderboard
(scripts/build_powerscore_page.py) and inserts a badge-pill, matching the
existing PowerScore-badge pill style, right after the PowerScore badge on
each of the 113 city pages. Idempotent: skips any page that already has the
pill (so re-running after adding a new city/region is safe).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_powerscore_page import ENERGY_COST, energy_cost_for  # noqa: E402

DATA = json.loads((ROOT / "powerscore-data.json").read_text())
rows = DATA["leaderboard_overall"]

MARKER = "energy-cost-pill"

BADGE_RE = re.compile(
    r'(<div class="wrap" style="text-align:center; padding:14px 28px 0;">'
    r'<a href="/powerscore/#city-[^"]+"[^>]*>.*?</a></div>)',
    re.DOTALL,
)

BADGE_RE_ALT = re.compile(
    r'(<div style="text-align:center; padding:14px 20px 0;">'
    r'<a href="/powerscore/#city-[^"]+"[^>]*>.*?</a></div>)',
    re.DOTALL,
)


def pill_html(cost_display, url_fragment):
    return (
        f'<div class="wrap {MARKER}" style="text-align:center; padding:10px 28px 0;">'
        f'<a href="/powerscore/#{url_fragment}" style="display:inline-flex; align-items:center; gap:8px; '
        f'background:#fff; border:1px solid var(--rule); border-radius:999px; padding:8px 18px; '
        f'font-size:13px; font-weight:600; color:var(--teal-deep); text-decoration:none; '
        f'box-shadow:0 1px 3px rgba(10,42,46,0.08);">'
        f'<span aria-hidden="true">&#128268;</span>'
        f'<span>Estimated Annual Energy Cost: {cost_display}</span></a></div>'
    )


def pill_html_alt(cost_display, url_fragment):
    return (
        f'<div class="{MARKER}" style="text-align:center; padding:10px 20px 0;">'
        f'<a href="/powerscore/#{url_fragment}" style="display:inline-flex; align-items:center; gap:8px; '
        f'background:var(--color-bg); border:1px solid var(--color-border); border-radius:999px; '
        f'padding:8px 18px; font-size:13px; font-weight:600; color:var(--color-fg); text-decoration:none;">'
        f'<span aria-hidden="true">&#128268;</span>'
        f'<span>Estimated Annual Energy Cost: {cost_display}</span></a></div>'
    )


def main():
    updated, skipped, missing_cost = [], [], []
    for r in rows:
        cost = energy_cost_for(r)
        if cost == "&mdash;":
            missing_cost.append(r["url"])
            continue

        path = ROOT / r["url"].strip("/") / "index.html"
        text = path.read_text()

        if MARKER in text:
            skipped.append(r["url"])
            continue

        m = BADGE_RE.search(text)
        make_pill = pill_html
        if not m:
            m = BADGE_RE_ALT.search(text)
            make_pill = pill_html_alt
        if not m:
            missing_cost.append(r["url"] + " (no badge match)")
            continue

        frag = f"city-{r['region'].replace('/', '-')}-{r['slug'].replace('/', '-')}"
        new_text = text[: m.end()] + "\n" + make_pill(cost, frag) + text[m.end() :]
        path.write_text(new_text)
        updated.append(r["url"])

    print(f"Updated: {len(updated)}")
    print(f"Already had pill (skipped): {len(skipped)}")
    if missing_cost:
        print(f"No cost / no badge match ({len(missing_cost)}):")
        for u in missing_cost:
            print(" ", u)


if __name__ == "__main__":
    main()
