#!/usr/bin/env python3
"""Replace the auto-generated hero stat strip on the 10 NY 'alt template'
pages (con-edison/pseg/central-hudson) with figures pulled from the page's
own rebate-grid instead of powerscore-data.json.

Why: these pages score "closed"/$0 in powerscore-data.json for heat-pump
because that dataset only tracks a single utility program, but the pages
themselves feature a much bigger *stacked* total (utility + NYS Clean Heat +
federal HEAR, etc.) as their real headline number. Using the powerscore
figures produced a misleadingly small strip (e.g. $4,000 insulation instead
of $28,000 stacked heat pump). Source of truth for these 10 pages is their
own already-written rebate-card content.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = "hero-stat-strip"

FILES = [
    "us/ny/con-edison/mount-vernon/index.html",
    "us/ny/con-edison/white-plains/index.html",
    "us/ny/pseg/huntington/index.html",
    "us/ny/pseg/oyster-bay/index.html",
    "us/ny/pseg/smithtown/index.html",
    "us/ny/pseg/southampton/index.html",
    "us/ny/central-hudson/beacon/index.html",
    "us/ny/central-hudson/kingston/index.html",
    "us/ny/central-hudson/newburgh/index.html",
    "us/ny/central-hudson/saugerties/index.html",
]

CARD_RE = re.compile(
    r'<h3>(.*?)</h3>\s*<div class="rebate-amount">(.*?)</div>', re.DOTALL
)

STRIP_RE = re.compile(
    r'<div class="hero-stat-strip".*?</div>\n(?:.*?</div>\n)*?</div>\n', re.DOTALL
)
# The div block itself has no nested divs other than the 3 stat cards; match
# just the outer wrapper non-greedily by counting to its own closing </div>.
OUTER_STRIP_RE = re.compile(
    r'<div class="hero-stat-strip"[^>]*>.*?\n</div>\n', re.DOTALL
)


def top_amounts(text, n=3):
    cards = CARD_RE.findall(text)
    has_stacked = any("Stacked Total" in label for label, _ in cards)
    picked = []
    for label, amount in cards:
        if "Flagged incomplete" in amount:
            continue
        if has_stacked and "(Single Program)" in label:
            continue
        nums = [int(x.replace(",", "")) for x in re.findall(r"\$([\d,]+)", amount)]
        if not nums or max(nums) == 0:
            continue
        clean_label = re.sub(r"\s*\((Stacked Total|Single Program)\)", "", label).strip()
        clean_label = re.sub(r"\s*Rebate$", "", clean_label).strip()
        picked.append((clean_label, max(nums)))
    picked.sort(key=lambda x: x[1], reverse=True)
    # de-dupe by label, keep highest
    seen = {}
    for label, val in picked:
        if label not in seen or val > seen[label]:
            seen[label] = val
    ordered = sorted(seen.items(), key=lambda x: x[1], reverse=True)
    return ordered[:n]


def fmt(v):
    return f"${v:,.0f}"


def strip_html(cats):
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
        f"{cards}\n</div>\n"
    )


def main():
    for rel in FILES:
        path = ROOT / rel
        text = path.read_text()
        cats = top_amounts(text)
        if len(cats) < 2:
            print(f"SKIP (not enough data): {rel}")
            continue
        new_strip = strip_html(cats)
        new_text, count = OUTER_STRIP_RE.subn(new_strip, text, count=1)
        if count != 1:
            print(f"WARN: could not find existing strip in {rel}")
            continue
        path.write_text(new_text)
        print(f"Fixed {rel}: {cats}")


if __name__ == "__main__":
    main()
