#!/usr/bin/env python3
"""
Generate a one-page HTML audit report per installer from audit_results.json.

Usage:
    .venv/bin/python generate_report.py --results reports/audit_results.json --out reports/html
"""
import argparse
import json
import re
from pathlib import Path

GRADE_COLOR = {
    "A": "#1a7f37",
    "B": "#4a8f3c",
    "C": "#b8860b",
    "D": "#c0392b",
    "F": "#8b1a1a",
}

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Website Audit — {name}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    margin: 0; padding: 0; background: #f4f5f7; color: #1c1e21;
  }}
  .page {{
    max-width: 780px; margin: 0 auto; background: #fff; padding: 40px 48px;
  }}
  .header {{
    display: flex; justify-content: space-between; align-items: flex-start;
    border-bottom: 3px solid #111; padding-bottom: 20px; margin-bottom: 24px;
  }}
  .brand {{ font-size: 13px; letter-spacing: 0.08em; text-transform: uppercase; color: #666; font-weight: 600; }}
  h1 {{ font-size: 22px; margin: 4px 0 2px; }}
  .sub {{ color: #555; font-size: 14px; }}
  .score-box {{
    text-align: center; min-width: 120px;
  }}
  .score-num {{ font-size: 46px; font-weight: 800; line-height: 1; color: {grade_color}; }}
  .grade-letter {{
    display: inline-block; margin-top: 4px; font-size: 15px; font-weight: 700;
    color: #fff; background: {grade_color}; border-radius: 6px; padding: 2px 10px;
  }}
  .score-label {{ font-size: 11px; color: #888; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.06em; }}

  .meta-row {{ display: flex; gap: 24px; margin-bottom: 28px; font-size: 13px; color: #444; flex-wrap: wrap; }}
  .meta-item strong {{ display: block; color: #111; font-size: 15px; }}

  .breakdown {{ margin-bottom: 28px; }}
  .bd-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }}
  .bd-label {{ flex: 0 0 260px; font-size: 13px; color: #333; }}
  .bd-bar-track {{ flex: 1; background: #eee; border-radius: 4px; height: 10px; overflow: hidden; }}
  .bd-bar-fill {{ height: 100%; border-radius: 4px; background: #111; }}
  .bd-pts {{ flex: 0 0 55px; font-size: 12px; color: #666; text-align: right; }}

  h2 {{ font-size: 15px; text-transform: uppercase; letter-spacing: 0.05em; color: #111; margin: 28px 0 12px; border-left: 4px solid #111; padding-left: 10px; }}

  .rec-list {{ list-style: none; padding: 0; margin: 0; }}
  .rec-list li {{
    padding: 12px 14px; margin-bottom: 8px; background: #fbfaf7; border-left: 3px solid #b8860b;
    font-size: 14px; line-height: 1.45; border-radius: 4px;
  }}

  .growth-list {{ list-style: none; padding: 0; margin: 0; }}
  .growth-list li {{
    padding: 12px 14px; margin-bottom: 8px; background: #f4f9f6; border-left: 3px solid #1a7f37;
    font-size: 14px; line-height: 1.45; border-radius: 4px;
  }}

  .cta {{
    margin-top: 34px; padding: 22px 24px; background: #111; color: #fff; border-radius: 8px;
  }}
  .cta h3 {{ margin: 0 0 8px; font-size: 16px; }}
  .cta p {{ margin: 0 0 14px; font-size: 13.5px; color: #d7d7d7; line-height: 1.5; }}

  .footer {{ margin-top: 28px; font-size: 11px; color: #999; text-align: center; }}
</style>
</head>
<body>
<div class="page">

  <div class="header">
    <div>
      <div class="brand">A Free Website &amp; Local Search Audit, Brought to You by HomePowerRebate</div>
      <h1>{name}</h1>
      <div class="sub">{location}</div>
    </div>
    <div class="score-box">
      <div class="score-num">{score_display}</div>
      <div class="grade-letter">Grade {grade}</div>
      <div class="score-label">out of 100</div>
    </div>
  </div>

  <div class="meta-row">
    <div class="meta-item"><strong>{rating}&#9733; ({reviews} reviews)</strong>Google rating</div>
    <div class="meta-item"><strong>{load_time}</strong>Page load time</div>
    <div class="meta-item"><strong>{ssl_status}</strong>Secure connection</div>
    <div class="meta-item"><strong>{schema_status}</strong>AI/schema readiness</div>
  </div>

  <h2>Score breakdown</h2>
  <div class="breakdown">
    {breakdown_html}
  </div>

  <h2>What's costing you leads right now</h2>
  <ul class="rec-list">
    {rec_html}
  </ul>

  <h2>How to get ahead of other {specialty} companies nearby</h2>
  <ul class="growth-list">
    {growth_html}
  </ul>

  <div class="cta">
    <h3>Want to see what an A-grade version of this site looks like?</h3>
    <p>HomePowerRebate sends homeowners looking for rebates to installers we trust — and we build local-search-optimized sites for HVAC and solar companies too, the kind that show up in Google's map pack and get cited when homeowners ask AI assistants "who should I call for a heat pump install near me." Happy to send over an example built for a business like yours, or hop on a quick 15-minute call to walk through this audit.</p>
  </div>

  <div class="footer">Audit prepared by HomePowerRebate &middot; {audited_at} &middot; homepowerrebate.com</div>

</div>
</body>
</html>
"""


def build_growth_ideas(result):
    """
    Forward-looking plays a competitor probably isn't doing yet —
    distinct from the fix-it list, which just closes gaps.
    """
    ideas = []
    tech = result.get("technical", {})
    reviews = result.get("reviews") or 0
    internal_links = tech.get("internal_link_count", 0)

    if not tech.get("has_local_business_schema"):
        ideas.append(
            "As of mid-2026, 87% of independent HVAC and plumbing contractors have zero visibility when homeowners ask ChatGPT or Google AI Overviews a question — while AI Overviews now show up on over 80% of local service searches. Adding FAQ + LocalBusiness schema is the fastest way to become one of the few local businesses AI tools actually cite."
        )
    if internal_links < 15:
        ideas.append(
            "Build dedicated pages per city + service combo (e.g. 'Heat Pump Installation in [City]') instead of one homepage — this is how bigger competitors quietly out-rank local ones on Google, and it compounds every page you add."
        )
    if reviews < 100:
        ideas.append(
            "Set up an automated review-request text/email sent right after each job — the installers with 100+ reviews are winning the map pack almost entirely on review volume, not skill."
        )
    ideas.append(
        "Post before/after job photos to Google Business Profile weekly — GBP rewards active profiles with more map-pack visibility, and most local contractors post once and forget it."
    )
    ideas.append(
        "Get listed as a certified installer on rebate/incentive resource sites (like HomePowerRebate) — homeowners actively researching a heat pump or solar rebate are higher-intent leads than a generic Google search, and most installers aren't showing up in this channel yet."
    )
    ideas.append(
        "Apply for Google Local Services Ads (the \"Google Verified\" badge) — it places you above the regular map pack on a pay-per-lead basis, averaging around $51/lead with a 44% book rate, and most independent installers haven't gone through the verification process to qualify yet."
    )
    ideas.append(
        "Add missed-call text-back so a lead who calls after hours gets an instant reply instead of silence — HVAC contractors lose an estimated $45,000–$120,000 a year to unanswered calls, and 85% of those callers never leave a voicemail or call back. This alone recovers jobs you're currently losing for free."
    )
    ideas.append(
        "Show 0%-down financing options clearly on the homepage — a lot of rebate-driven traffic is homeowners who want the upgrade but are price-checking whether they can afford it now, and financing visibility converts that hesitation into a booked call."
    )
    ideas.append(
        "Offer a seasonal maintenance plan (spring AC tune-up, fall furnace check) — it turns a one-time install into recurring revenue and keeps you top-of-mind before a competitor's ad does."
    )
    if reviews >= 50:
        ideas.append(
            "You already have strong reviews — turn a few into short video testimonials for the homepage. Video builds more trust than star ratings alone and almost nobody in this space bothers to shoot it."
        )
    return ideas[:6]


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def render_report(result):
    grade = result.get("grade", "F")
    score = result.get("score")
    color = GRADE_COLOR.get(grade, "#8b1a1a")

    if result.get("error") and score is None:
        score_display = "N/A"
    else:
        score_display = str(score)

    breakdown_rows = []
    for label, pts, maxpts in result.get("breakdown", []):
        pct = int(100 * pts / maxpts) if maxpts else 0
        breakdown_rows.append(
            f'<div class="bd-row"><div class="bd-label">{label}</div>'
            f'<div class="bd-bar-track"><div class="bd-bar-fill" style="width:{pct}%"></div></div>'
            f'<div class="bd-pts">{pts}/{maxpts}</div></div>'
        )
    breakdown_html = "\n".join(breakdown_rows) if breakdown_rows else "<p style='font-size:13px;color:#888'>Site could not be fully analyzed.</p>"

    recs = result.get("recommendations", [])
    rec_html = "\n".join(f"<li>{r}</li>" for r in recs) if recs else "<li>No major issues found — nice work.</li>"

    growth_ideas = build_growth_ideas(result)
    growth_html = "\n".join(f"<li>{g}</li>" for g in growth_ideas)

    tech = result.get("technical", {})
    load_time = f"{result['load_time_sec']}s" if result.get("load_time_sec") is not None else "—"
    ssl_status = "Yes" if result.get("has_ssl") else "No"
    schema_status = "Present" if tech.get("has_schema") else "Missing"

    html = TEMPLATE.format(
        name=result.get("name", "Installer"),
        location=result.get("location", ""),
        score_display=score_display,
        grade=grade,
        grade_color=color,
        rating=result.get("rating", "—"),
        reviews=result.get("reviews", "—"),
        load_time=load_time,
        ssl_status=ssl_status,
        schema_status=schema_status,
        breakdown_html=breakdown_html,
        rec_html=rec_html,
        growth_html=growth_html,
        specialty=result.get("specialty") or "local service",
        audited_at=result.get("audited_at", ""),
    )
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", default="reports/html")
    args = ap.parse_args()

    results = json.loads(Path(args.results).read_text())
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for result in results:
        html = render_report(result)
        fname = slugify(result.get("name", "installer")) + ".html"
        (out_dir / fname).write_text(html)
        print(f"Wrote {out_dir / fname}")


if __name__ == "__main__":
    main()
