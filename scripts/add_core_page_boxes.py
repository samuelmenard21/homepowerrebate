#!/usr/bin/env python3
"""Rebate calculator box and 'last checked' line on the pages listed in data/core-pages.json (post-step, 2026-11-08).

- CORE-CALC: a short box with a link to the region's calculator, placed above the shared footer (content_insert_point).
- CORE-VERIFIED: one line right after the page's first </h1>; the date is the OLDEST verified_on among the page's facts in
  data/verified-facts/*.json, so it never claims a newer check than we made. Skipped when the page already shows "Last verified" or "Checked <date>".
Both sit between START/END markers and are replaced on every run, so re-runs never duplicate them. Facts decide the date; change it there.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402

CALC = ("<!-- CORE-CALC-START -->", "<!-- CORE-CALC-END -->")
VER = ("<!-- CORE-VERIFIED-START -->", "<!-- CORE-VERIFIED-END -->")


def strip(t, marks):
    return re.sub(r"\n?" + re.escape(marks[0]) + r"[\s\S]*?" + re.escape(marks[1]) + r"\n?", "", t)


def fact_dates():
    out = {}
    for f in (ROOT / "data" / "verified-facts").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        for x in d.get("facts", []) if isinstance(d, dict) else d:
            out[x["id"]] = x.get("verified_on")
    return out


def calc_box(calc, where):
    return (f'<section class="core-calc" style="max-width:880px;margin:28px auto;padding:0 20px;"><div style="background:#f5efe5;border-left:4px solid #0d4f5c;'
            f'border-radius:8px;padding:16px 20px;color:#0a2a2e;font-size:16px;line-height:1.5;"><p style="margin:0 0 6px;font-weight:700;">'
            f'What could you get back in {html.escape(where)}?</p><p style="margin:0 0 10px;">Answer a few questions. See the rebates open to your home, '
            f'with a link to the official page for each one.</p><p style="margin:0;"><a href="{calc}" style="display:inline-block;background:#d4751c;color:#fff;'
            f'font-weight:700;padding:10px 18px;border-radius:6px;text-decoration:none;">Estimate my rebates</a></p></div></section>')


def ver_line(d):
    return (f'<p class="core-verified" style="max-width:880px;margin:10px auto 0;padding:0 20px;color:inherit;opacity:.85;font-size:14px;">'
            f'We last checked the official program pages on {d.strftime("%B %-d, %Y")}.</p>')


def main():
    cfg = json.loads((ROOT / "data" / "core-pages.json").read_text(encoding="utf-8"))["pages"]
    dates = fact_dates()
    changed = 0
    for p in cfg:
        f = ROOT / p["page"].strip("/") / "index.html"
        if not f.exists():
            print("missing page", p["page"])
            continue
        t0 = f.read_text(encoding="utf-8")
        t = strip(strip(t0, CALC), VER)
        if p.get("verified") and not re.search(r"Last verified|Checked [A-Z][a-z]+ \d", re.sub(r"<[^>]+>", " ", t)):
            ds = [dates[i] for i in p["verified"] if dates.get(i)]
            missing = [i for i in p["verified"] if i not in dates]
            if missing:
                print("unknown fact id", missing)
            elif ds:
                m = re.search(r"</h1>", t)
                if m:
                    t = t[:m.end()] + "\n" + VER[0] + ver_line(date.fromisoformat(min(ds))) + VER[1] + "\n" + t[m.end():]
        if p.get("calc") and not re.search(r'href="' + re.escape(p["calc"]) + r'"', t):
            i = navfooter.content_insert_point(t)
            if i >= 0:
                t = t[:i] + "\n" + CALC[0] + calc_box(p["calc"], p.get("where", "your area")) + CALC[1] + "\n" + t[i:]
        if t != t0:
            f.write_text(t, encoding="utf-8")
            changed += 1
    print(f"Core page boxes: {len(cfg)} pages listed, {changed} files changed.")


if __name__ == "__main__":
    main()
