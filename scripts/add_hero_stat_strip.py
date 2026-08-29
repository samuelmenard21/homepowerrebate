#!/usr/bin/env python3
"""Insert a top-3-rebate dollar-amount stat strip into every city page's hero.

Standard going forward: every city page must show its biggest rebate dollar
figures above the fold, in the hero, not buried below a category grid / CTA
box. Source of truth is powerscore-data.json (the same authoritative
per-category dollar_value used to build the PowerScore leaderboard) so the
numbers here can never drift from what's shown there.

Idempotent: skips any page that already has the strip (safe to re-run when
a new city page is added).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

DATA = json.loads((ROOT / "powerscore-data.json").read_text())
CAT_LABELS = DATA["category_labels"]
rows = DATA["leaderboard_overall"]

MARKER = "hero-stat-strip"

HERO_RE = re.compile(
    r'(<section class="hero">.*?)(\n(\s*)</div>\n</section>)', re.DOTALL
)
HEADER_RE = re.compile(r"</header>")


def top_categories(r, n=3):
    cats = [
        (CAT_LABELS[k], v["dollar_value"])
        for k, v in r["categories"].items()
        if v.get("status") in ("open", "limited") and v.get("dollar_value", 0) > 0
    ]
    cats.sort(key=lambda x: x[1], reverse=True)
    return cats[:n]


def fmt(value):
    if value < 10:
        return f"${value:,.2f}/watt"
    return f"${value:,.0f}"


def hero_strip_html(cats):
    cards = "\n".join(
        f'      <div style="background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.18); '
        f'border-radius:12px; padding:16px 22px; min-width:150px;">'
        f'<div style="font-family:\'Fraunces\',serif; font-size:28px; font-weight:700; color:#fff;">{fmt(v)}</div>'
        f'<div style="font-size:12px; color:rgba(250,247,242,.7); margin-top:4px;">{label} rebate</div></div>'
        for label, v in cats
    )
    return (
        f'    <div class="{MARKER}" style="display:flex; flex-wrap:wrap; justify-content:center; gap:14px; margin-top:28px;">\n'
        f"{cards}\n    </div>"
    )


def header_strip_html(cats):
    cards = "\n".join(
        f'    <div style="background:var(--color-fg); color:var(--color-bg); border-radius:0.5rem; '
        f'padding:1rem 1.5rem; min-width:150px;">'
        f'<div style="font-family:var(--font-display); font-size:1.8rem; font-weight:700; color:var(--color-accent);">{fmt(v)}</div>'
        f'<div style="font-size:0.85rem; margin-top:0.25rem;">{label} rebate</div></div>'
        for label, v in cats
    )
    return (
        f'<div class="{MARKER}" style="max-width:900px; margin:0 auto; padding:0 2rem; '
        f'display:flex; flex-wrap:wrap; justify-content:center; gap:1rem;">\n'
        f"{cards}\n</div>"
    )


def main():
    updated, skipped, no_data, no_match = [], [], [], []
    for r in rows:
        path = ROOT / r["url"].strip("/") / "index.html"
        text = path.read_text()

        if MARKER in text:
            skipped.append(r["url"])
            continue

        cats = top_categories(r)
        if len(cats) < 2:
            no_data.append(r["url"])
            continue

        m = HERO_RE.search(text)
        if m:
            strip = hero_strip_html(cats)
            new_text = text[: m.start(2)] + "\n" + strip + text[m.start(2) :]
            path.write_text(new_text)
            updated.append(r["url"])
            continue

        m = HEADER_RE.search(text)
        if m:
            strip = header_strip_html(cats)
            new_text = text[: m.end()] + "\n" + strip + text[m.end() :]
            path.write_text(new_text)
            updated.append(r["url"])
            continue

        no_match.append(r["url"])

    print(f"Updated: {len(updated)}")
    print(f"Already had strip (skipped): {len(skipped)}")
    if no_data:
        print(f"Fewer than 2 open categories with a $ value ({len(no_data)}):")
        for u in no_data:
            print(" ", u)
    if no_match:
        print(f"No hero/header pattern matched ({len(no_match)}):")
        for u in no_match:
            print(" ", u)


if __name__ == "__main__":
    main()
