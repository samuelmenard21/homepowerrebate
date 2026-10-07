#!/usr/bin/env python3
"""Homepage PowerScore spotlight, generated from powerscore-data.json (same file the /powerscore/ page reads).
Replaces the block between POWERSCORE-SPOTLIGHT-START/END in index.html. Run after build_powerscore.py."""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S, E = "<!-- POWERSCORE-SPOTLIGHT-START -->", "<!-- POWERSCORE-SPOTLIGHT-END -->"
OLD = "<!-- POWERSCORE SPOTLIGHT -->"
NAMES = {"ca/bc": "BC", "ca/on": "ON", "ca/ab": "AB", "ca/ns": "NS", "us/ma": "MA", "us/ny": "NY", "us/ca": "CA", "us/pa": "PA", "us/co": "CO", "us/vt": "VT", "us/mi": "MI"}


def card(c, first):
    lab = f"{html.escape(c['label'])}, {NAMES[c['region']]}"
    score = round(c["overall"])
    sub = f"{html.escape(c['region_label'])}'s top city"
    if first:
        return (f'<a href="{c["url"]}" class="ps-card ps-first"><span class="ps-tag">#1 overall</span><b class="ps-num">{score}</b>'
                f'<span class="ps-lab">PowerScore</span><b class="ps-city">{lab}</b><span class="ps-sub">{sub}</span></a>')
    return (f'<a href="{c["url"]}" class="ps-card"><b class="ps-num">{score}</b><span class="ps-lab">PowerScore</span>'
            f'<b class="ps-city">{lab}</b><span class="ps-sub">{sub}</span></a>')


def main():
    d = json.loads((ROOT / "powerscore-data.json").read_text())
    best = {}
    for c in d["leaderboard_overall"]:
        if c["region"] not in best or c["overall"] > best[c["region"]]["overall"]:
            best[c["region"]] = c
    ranked = sorted(best.values(), key=lambda c: -c["overall"])
    cards = "".join(card(c, i == 0) for i, c in enumerate(ranked))
    n = d["stats"]["total_cities"]
    block = f"""{S}
<style>.ps-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:32px}}
.ps-card{{display:flex;flex-direction:column;gap:2px;text-decoration:none;color:#111;background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:22px;position:relative}}
.ps-first{{background:linear-gradient(135deg,#0d4f5c,#08363f);border:0;color:#fff}}
.ps-num{{font-family:'Fraunces',serif;font-size:38px;line-height:1.1}}.ps-lab{{font-size:12px;opacity:.65;margin-bottom:8px}}
.ps-city{{font-size:16px}}.ps-sub{{font-size:13px;opacity:.75}}.ps-tag{{position:absolute;top:12px;right:16px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;opacity:.7}}</style>
<div style="padding:56px 28px 60px;max-width:1100px;margin:0 auto;">
  <div style="text-align:center;margin-bottom:40px;">
    <p style="font-size:13px;text-transform:uppercase;letter-spacing:.08em;font-weight:700;color:#d4751c;margin:0 0 10px;">PowerScore</p>
    <h2 style="font-family:'Fraunces',serif;font-size:clamp(28px,5vw,42px);font-weight:500;line-height:1.2;color:#111;margin:0 0 16px;">How does your city stack up?</h2>
    <p style="font-size:16px;color:#666;margin:0 auto;max-width:640px;">We scored {n} cities, 0 to 100, on how much rebate money is open today: dollar value, program status and how many programs stack. Here is the top city in each of our {len(ranked)} regions.</p>
  </div>
  <div class="ps-grid">{cards}</div>
  <div style="text-align:center;"><a href="/powerscore/" style="display:inline-block;background:#0d4f5c;color:white;padding:14px 32px;border-radius:999px;text-decoration:none;font-weight:700;font-size:15px;">See the full leaderboard &rarr;</a></div>
</div>
{E}"""
    f = ROOT / "index.html"
    s = f.read_text(encoding="utf-8")
    if S in s:
        s = re.sub(re.escape(S) + ".*?" + re.escape(E), lambda m: block, s, count=1, flags=re.S)
    else:
        a = s.index(OLD)
        end = s.index("</div>\n</div>\n", s.index("See the full leaderboard", a)) + len("</div>\n</div>\n")
        s = s[:a] + block + "\n" + s[end:]
    f.write_text(s, encoding="utf-8")
    print("Homepage spotlight:", ", ".join(f"{c['label']} {round(c['overall'])}" for c in ranked))


if __name__ == "__main__":
    main()
