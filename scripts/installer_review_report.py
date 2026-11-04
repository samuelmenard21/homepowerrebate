#!/usr/bin/env python3
"""One-page HTML review for one company (the full report a note offers), from data/installer-reviews/<slug>.json. Local file, never published.
Usage: python3 scripts/installer_review_report.py "Calgary Air" [--out DIR]"""
import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
e = html.escape


def render(d):
    g = d["google"]
    rows = "".join(f'<tr><td>{"✓" if c["pass"] else "✗"}</td><td>{e(c["check"])}</td><td>{"" if c["pass"] else e(c["fix"])}</td></tr>' for c in d["checks"])
    ck = "".join(f"<li>{e(x)}</li>" for x in d["check_yourself"])
    return f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Website and Google review: {e(d['company'])}</title>
<style>body{{font:16px/1.55 'Inter Tight',system-ui,sans-serif;color:#0a2a2e;background:#faf7f2;margin:0}}main{{max-width:760px;margin:0 auto;padding:28px 20px 60px}}
h1{{font-family:Georgia,serif;font-size:28px;margin:0 0 4px}}.logo b{{color:#d4751c}}.card{{background:#fff;border:1px solid #d9d0c1;border-radius:12px;padding:16px 20px;margin:16px 0}}
.kpi{{display:flex;gap:12px;flex-wrap:wrap}}.kpi div{{flex:1;min-width:130px;background:#f5efe5;border-radius:10px;padding:10px 14px}}.kpi b{{display:block;font-size:24px;font-family:Georgia,serif}}
table{{border-collapse:collapse;width:100%;font-size:15px}}td{{border-top:1px solid #e6dfd2;padding:8px 6px;vertical-align:top}}td:first-child{{width:28px;font-weight:700}}.small{{font-size:13px;color:#4a5d60}}</style>
<main><div class="logo">Home<b>Power</b>Rebate</div><h1>{e(d['company'])}</h1><p class="small">Website and Google listing review, {e(d['city'])} {e(d['service'].replace('-', ' '))} installers. Prepared for the company; not published.</p>
<div class="card"><h2>Your Google listing, in context</h2><div class="kpi"><div><b>{g['rating']:.1f}★</b>rating</div><div><b>{g['reviews']:,}</b>Google reviews</div>
<div><b>{g['rank_in_city']} of {g['companies_in_city']}</b>on our {e(d['city'])} list</div><div><b>{g['city_median_reviews']:,.0f}</b>reviews for the middle company</div></div>
<p class="small">Ratings and review counts are from Google Maps. We rank by rating weighted by review count. We can only see public numbers, so photos, categories, hours and replies are on your own checklist below.</p></div>
<div class="card"><h2>Your homepage: {d['passed']} of {d['of']} basic checks</h2><p class="small">We read the homepage once, the way a visitor on a phone would. Other pages may cover what a check marks missing.</p><table>{rows}</table></div>
<div class="card"><h2>Check these on your Google listing yourself</h2><ul>{ck}</ul></div>
<p class="small">Questions or want to talk it through? Reply to the email. Sam Menard, HomePowerRebate.</p></main>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    for f in (ROOT / "data" / "installer-reviews").glob("*.json"):
        if f.name == "emails.json":
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if a.name.lower() in d["company"].lower():
            out = Path(a.out) / f"review-{f.stem}.html"
            out.write_text(render(d), encoding="utf-8")
            print(out)
            return
    raise SystemExit("not found")


if __name__ == "__main__":
    main()
