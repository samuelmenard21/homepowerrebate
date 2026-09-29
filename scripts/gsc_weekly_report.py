#!/usr/bin/env python3
"""Weekly Search Console report -> reports/gsc-YYYY-MM-DD.md (private, not published).

  python3 scripts/gsc_weekly_report.py [--days 28]

Sections: totals by week, striking-distance queries (pos 8-30), CTR underperformers
(page 1 but low click rate), top pages, and sitemap URLs with zero impressions.
Search Console data lags ~2 days, so the window ends 3 days ago.
"""
import datetime as dt
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = "homepowerrebate"


def gsc(dims, start, end, limit=5000):
    out = subprocess.run(["seo", "gsc-query", f"--project={PROJECT}", f"--dimensions={dims}", f"--start-date={start}",
                          f"--end-date={end}", f"--limit={limit}", "--json"], capture_output=True, text=True)
    d = json.loads(out.stdout)
    if "rows" not in d:
        sys.exit(f"GSC error: {out.stdout[:300]}")
    return d["rows"]


def table(head, rows):
    return "| " + " | ".join(head) + " |\n|" + "---|" * len(head) + "\n" + "\n".join("| " + " | ".join(map(str, r)) + " |" for r in rows) + "\n"


def short(u):
    return u.replace("https://homepowerrebate.com", "") or "/"


def main():
    days = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else 28
    end = dt.date.today() - dt.timedelta(days=3)
    start = end - dt.timedelta(days=days - 1)
    qp = gsc("query,page", start, end)
    daily = gsc("date", start, end, 1000)
    md = [f"# Search Console report {start} to {end}\n"]

    imp = sum(r["impressions"] for r in daily)
    clk = sum(r["clicks"] for r in daily)
    last7 = [r for r in daily if r["keys"][0] > str(end - dt.timedelta(days=7))]
    md.append(f"**Totals:** {imp:,} impressions, {clk} clicks in {days} days. Last 7 days: "
              f"{sum(r['impressions'] for r in last7)/max(len(last7),1):,.0f} impressions/day, "
              f"{sum(r['clicks'] for r in last7)/max(len(last7),1):.1f} clicks/day. Goal: 5,000 and 50.\n")

    # Ignore branded/installer-name noise: people searching a company name land on ranking pages.
    md.append("## Striking distance (position 8-30, most impressions)\nRewrite the page: direct answer in first 50 words, matching H2, FAQ entry.\n")
    sd = sorted([r for r in qp if 8 <= r["position"] <= 30 and r["impressions"] >= 5], key=lambda r: -r["impressions"])[:40]
    md.append(table(["query", "page", "impr", "pos"], [(r["keys"][0], short(r["keys"][1]), r["impressions"], f"{r['position']:.0f}") for r in sd]))

    md.append("## Page 1 but low click rate (rewrite title/meta)\n")
    lo = sorted([r for r in qp if r["position"] <= 10 and r["impressions"] >= 5 and r["ctr"] < 0.03], key=lambda r: -r["impressions"])[:25]
    md.append(table(["query", "page", "impr", "clicks", "pos"], [(r["keys"][0], short(r["keys"][1]), r["impressions"], r["clicks"], f"{r['position']:.0f}") for r in lo]))

    pages = defaultdict(lambda: [0, 0])
    for r in qp:
        pages[r["keys"][1]][0] += r["impressions"]
        pages[r["keys"][1]][1] += r["clicks"]
    md.append("## Top pages\n")
    md.append(table(["page", "impr", "clicks"], [(short(p), v[0], v[1]) for p, v in sorted(pages.items(), key=lambda x: -x[1][0])[:25]]))

    sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    urls = set(re.findall(r"<loc>([^<]+)</loc>", sm))
    seen = set(pages)
    md.append(f"## Zero impressions\n{len(urls - seen)} of {len(urls)} sitemap URLs had no impressions in the window "
              f"(query-level data hides rare queries, so treat as an upper bound).\n")

    out = ROOT / "reports" / f"gsc-{dt.date.today()}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(md), encoding="utf-8")
    print("Wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
