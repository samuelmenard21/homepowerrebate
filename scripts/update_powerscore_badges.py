#!/usr/bin/env python3
"""Keep the PowerScore numbers printed on city hub pages and stacking-calculator pages in step with powerscore-data.json.

City hubs carry "PowerScore: 89.7/100 - #1 of 18 in British Columbia"; stacking pages carry the score in a hero stat.
Run after every scripts/build_powerscore.py:   python3 scripts/update_powerscore_badges.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "powerscore-data.json").read_text())
rows = D["leaderboard_overall"]


def fmt(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


by_region = {}
for r in rows:
    by_region.setdefault(r["region"], []).append(r)
info = {}
for reg, rs in by_region.items():
    scores = [round(x["overall"], 1) for x in rs]
    for x in rs:
        sc = round(x["overall"], 1)
        info[x["url"]] = (x["overall"], 1 + sum(1 for y in scores if y > sc), len(rs), x["region_label"], scores.count(sc) > 1)

BADGE = re.compile(r"PowerScore: [0-9.]+/100 &mdash; (?:tied for )?#[0-9]+ of [0-9]+ in [A-Za-z ]+")
STAT = re.compile(r'(<div class="num">)\d+(</div><div class="lbl">PowerScore</div>)')


def main():
    n_b = n_s = 0
    for url, (ov, rank, size, label, tied) in info.items():
        f = ROOT / url.strip("/") / "index.html"
        if f.exists():
            t = f.read_text(encoding="utf-8")
            txt = f"PowerScore: {fmt(ov)}/100 &mdash; {'tied for ' if tied else ''}#{rank} of {size} in {label}"
            new = BADGE.sub(txt, t)
            if new != t:
                f.write_text(new, encoding="utf-8")
                n_b += 1
        sf = ROOT / "stacking-calculator" / url.strip("/") / "index.html"
        if sf.exists():
            t = sf.read_text(encoding="utf-8")
            new = STAT.sub(lambda m: f"{m.group(1)}{ov:.0f}{m.group(2)}", t)
            if new != t:
                sf.write_text(new, encoding="utf-8")
                n_s += 1
    print(f"Updated {n_b} city hub badges and {n_s} stacking-calculator scores.")


if __name__ == "__main__":
    main()
