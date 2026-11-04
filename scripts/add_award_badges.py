#!/usr/bin/env python3
"""Put the "2026 Award Winner" badge on each winner's profile page (2026-11-04). A post-step; idempotent.

Reads data/awards/2026.json (scripts/build_awards_2026.py). The block sits between AWARD-WINNER-START/END, before the profile photo, and shows
one shield per category the company won in that city, with a line saying how it was chosen and a link to the winners page.
It does NOTHING until the awards JSON has "live": true (set LIVE = True in build_awards_2026.py at launch), so winners are not announced early.
--preview applies it anyway (for a look, then git checkout the pages); --only <text> limits it to profile URLs containing the text; --remove strips every block.
Usage: python3 scripts/add_award_badges.py [--preview] [--only on/hamilton] [--remove]"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S, E_ = "<!-- AWARD-WINNER-START -->", "<!-- AWARD-WINNER-END -->"
LABEL = {"heat-pump": "heat pump", "battery": "home battery", "solar": "solar"}
BLOCK_RE = re.compile(re.escape(S) + r".*?" + re.escape(E_) + r"\n?", re.S)
ANCHORS = [r"<!-- PROFILE-PHOTO-START -->", r'<aside class="ip-programs"', r'<section class="ip-kind">']


def block(items, year, prof):
    badges = "".join(f'<a href="/installers/awards/{year}/{i["sv"]}/#{i["slug"]}"><img src="/assets/awards/shield-{i["sv"]}-{year}.svg" width="84" height="87" alt="Award Winner {year}: {LABEL[i["sv"]]} installers in {i["city"]}"></a>' for i in items)
    lines = "".join(f'<p style="margin:4px 0 0">One of the top 3 {LABEL[i["sv"]]} installers in {i["city"]}, picked from {i["companies"]} companies ranked by Google reviews. '
                    f'<a href="/installers/awards/{year}/{i["sv"]}/#{i["slug"]}">See all the {i["city"]} winners</a>.</p>' for i in items)
    first = items[0]
    code = (f'<a href="https://homepowerrebate.com{{prof}}" rel="noopener"><img src="https://homepowerrebate.com/assets/awards/shield-{first["sv"]}-{year}.svg" '
            f'width="120" alt="HomePowerRebate.com {year} Award Winner: {LABEL[first["sv"]]} installers in {first["city"]}"></a>')
    code = code.replace("{prof}", prof)
    esc = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    snippet = (f'<details style="margin-top:8px"><summary style="cursor:pointer;font-weight:600">Add this badge to your website</summary>'
               f'<p style="margin:6px 0">Paste this where you want the badge. It links visitors to this page.</p>'
               f'<textarea readonly rows="4" style="width:100%;font:12px monospace" onclick="this.select()">{esc}</textarea></details>')
    return (f'{S}<section aria-label="Award winner {year}" style="display:flex;gap:16px;align-items:center;margin:18px 0;padding:16px 18px;background:#f5efe5;'
            f'border:1px solid #d9d0c1;border-radius:14px;flex-wrap:wrap"><div style="display:flex;gap:8px">{badges}</div>'
            f'<div style="flex:1;min-width:220px"><b style="font-family:Fraunces,Georgia,serif;font-size:20px">{year} Award Winner</b>{lines}{snippet}</div></section>{E_}\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--remove", action="store_true")
    a = ap.parse_args()
    d = json.loads((ROOT / "data" / "awards" / "2026.json").read_text(encoding="utf-8"))
    year = d["year"]
    if a.remove:
        n = 0
        for f in (ROOT / "installers" / "profiles").rglob("index.html"):
            s = f.read_text(encoding="utf-8")
            t = BLOCK_RE.sub("", s)
            if t != s:
                f.write_text(t, encoding="utf-8")
                n += 1
        print(n, "badge blocks removed")
        return
    if not d.get("live") and not a.preview:
        print("awards are not live: nothing to do (use --preview to look at it)")
        return
    by = defaultdict(list)
    for sv, cities in d["winners"].items():
        for c in cities:
            for w in c["winners"]:
                if w["profile"] and a.only in w["profile"]:
                    by[w["profile"]].append({"sv": sv, "city": c["city"], "slug": c["slug"], "companies": c["companies"]})
    done = missing = 0
    for prof, items in by.items():
        f = ROOT / prof.strip("/") / "index.html"
        if not f.exists():
            missing += 1
            continue
        s = f.read_text(encoding="utf-8")
        blk = block(sorted(items, key=lambda i: i["sv"]), year, prof)
        if S in s:
            new = BLOCK_RE.sub(lambda m: blk, s, count=1)
        else:
            pos = next((m.start() for pat in ANCHORS for m in [re.search(pat, s)] if m), -1)
            if pos < 0:
                missing += 1
                continue
            new = s[:pos] + blk + s[pos:]
        if new != s:
            f.write_text(new, encoding="utf-8")
            done += 1
    print(f"{done} profile pages updated, {missing} without a page or anchor ({len(by)} winning companies)")


if __name__ == "__main__":
    main()
