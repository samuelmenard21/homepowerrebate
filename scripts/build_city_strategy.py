#!/usr/bin/env python3
"""One strategy row per city (2026-11-04): which plays to run where, from data we already hold.

Inputs: installers/rankings.json and the ranking CSVs (list sizes, ratings, emails), powerscore-data.json (open heat pump rebate),
data/reports/city-strategy/gsc-pages-*.json (Search Console impressions per ranking page; partial: top local queries only),
data/city-areas.json (sourced communities), data/rebate-registered.json (official contractor lists), energy advisor and auditor rankings.
Writes data/reports/city-strategy/city-strategy-<date>.csv and .md. Tiers:
  A  Win now: real search demand already, or a large list plus a big open rebate plus reachable installers.
  B  Build: a full list and a rebate, no demand yet. Template plus outreach and awards.
  C  Hold: thin list or no open rebate. Template only; revisit when data changes.
Usage: python3 scripts/build_city_strategy.py"""
import csv
import glob
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_heat_pump_hub as hub  # noqa: E402
import build_installer_rankings as br  # noqa: E402

OUT = ROOT / "data" / "reports" / "city-strategy"
# Wave 1 = cities with search demand we can see (Search Console, 90 days), the Burlington results page the owner checked by hand, and the Massachusetts
# cities where "Mass Save approved contractor <city>" queries appear. Edit this list, not the rules below, to move a city.
WAVE1 = {("on", "Hamilton"), ("on", "Kitchener"), ("on", "Cambridge"), ("on", "Peterborough"), ("on", "Burlington"), ("on", "Greater Sudbury"),
         ("ca", "Chula Vista"), ("ab", "St. Albert"), ("ma", "Newton"), ("ma", "Cambridge")}
# Big metros pulled into wave 2 by judgement: the rules rank by rebate and reachability, and Alberta has no open heat pump rebate, which would
# bury Calgary and Edmonton although "heat pump installers <city>" searches do not depend on a rebate.
WAVE2_EXTRA = {("on", "Toronto"), ("bc", "Vancouver"), ("ma", "Boston"), ("ab", "Calgary"), ("ab", "Edmonton"), ("co", "Denver")}
REGISTERED_REGIONS = {"bc": "Better Homes BC registered contractors", "ma": "Mass Save Heat Pump Installer Network", "ny": "NYS Clean Heat contractors"}


def main():
    cities = hub.city_rows()
    gsc = {}
    for f in sorted(glob.glob(str(OUT / "gsc-pages-*.json"))):
        gsc = json.loads(Path(f).read_text(encoding="utf-8"))["pages"]
    areas = json.loads((ROOT / "data" / "city-areas.json").read_text(encoding="utf-8")) if (ROOT / "data" / "city-areas.json").exists() else {}
    rows_all = br.load_rows()
    by = defaultdict(list)
    for r in rows_all:
        by[(r["region"], r["service"], r["city"])].append(r)
    rk = json.loads((ROOT / "installers" / "rankings.json").read_text(encoding="utf-8"))
    adv = {}
    for m in rk:
        if m["service"] in ("energy-advisor", "energy-auditor"):
            adv[(m["region"], m["city"])] = m
    out = []
    for c in cities:
        key = (c["region"], "heat-pump", None)
        inst = [r for (rg, sv, ct), v in by.items() if rg == c["region"] and sv == "heat-pump" and ct.lower() == c["city"].lower() for r in v]
        ranked = sorted(inst, key=br.score, reverse=True)
        top5 = ranked[:5]
        emails_top5 = sum(1 for r in top5 if "@" in (r.get("email") or ""))
        emails_all = sum(1 for r in ranked if "@" in (r.get("email") or ""))
        g = gsc.get(c["url"], {})
        slug = c["url"].split("/")[3]
        has_areas = f"{c['region']}/{slug}" in areas
        a = adv.get((c["region"], c["city"]))
        demand = g.get("impressions", 0)
        score = (min(demand, 300) / 3) + min(c["n"], 15) * 3 + (min(c["rebate"] or 0, 12000) / 400) + emails_top5 * 4 + (8 if c["n"] >= 8 else 0)
        if demand >= 20 or (c["n"] >= 12 and (c["rebate"] or 0) >= 5000 and emails_top5 >= 3):
            tier = "A"
        elif c["n"] >= 8 and (c["rebate"] or 0) > 0:
            tier = "B"
        else:
            tier = "C"
        wave = 1 if (c["region"], c["city"]) in WAVE1 else (2 if (c["region"], c["city"]) in WAVE2_EXTRA or (tier == "A" and emails_top5 >= 4 and c["n"] >= 12) else (3 if tier in ("A", "B") else 4))
        plays = []
        if tier == "A":
            plays += ["personal review notes to top 3 companies", "local news pitch (ratings page + city numbers)", "check title test and rank weekly", "awards: first-wave winner"]
        if tier in ("A", "B"):
            plays += ["badge and awards notice after replies", "internal links from rebate pages (done)"]
        if c["region"] in REGISTERED_REGIONS:
            plays.append("lead with " + REGISTERED_REGIONS[c["region"]])
        if not has_areas:
            plays.append("find a sourced community list (official city page)")
        if c["n"] < 8:
            plays.append("award at region level only (fewer than 8 companies)")
        out.append({"region": c["region"], "city": c["city"], "wave": wave, "tier": tier, "score": round(score), "companies": c["n"], "reviews": c["reviews"],
                    "top_company": c["top"], "top_rating": c["rating"], "top_reviews": c["top_reviews"], "open_rebate_usd": round(c["rebate"] or 0),
                    "gsc_impressions_90d": demand, "gsc_position": g.get("avg_position", ""), "top5_with_email": emails_top5, "all_with_email": emails_all,
                    "community_list": "yes" if has_areas else "no",
                    "advisor_page": (f"{a['service']} ({a['count']} companies, {'indexable' if a.get('indexed', True) else 'noindex'})" if a else "none"),
                    "plays": "; ".join(plays), "url": c["url"]})
    out.sort(key=lambda r: (r["wave"], -r["score"]))
    stamp = date.today().isoformat()
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / f"city-strategy-{stamp}.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    t = defaultdict(list)
    for r in out:
        t[r["tier"]].append(r)
    wv = defaultdict(list)
    for r in out:
        wv[r["wave"]].append(r)
    names = {r["code"]: r["abbr"] for r in __import__("regions").REGIONS}
    lines = [f"# City strategy ({stamp})", "", f"{len(out)} cities: A {len(t['A'])}, B {len(t['B'])}, C {len(t['C'])}. Demand numbers are partial (top local queries only).", ""]
    for tier, label in (("A", "Win now"), ("B", "Build"), ("C", "Hold")):
        lines += [f"## Tier {tier}: {label} ({len(t[tier])})", "", "| City | Companies | Open rebate | Search impressions (90d) | Top 5 reachable | Advisor page |", "|---|---|---|---|---|---|"]
        for r in t[tier][:40 if tier != "C" else 12]:
            lines.append(f"| {r['city']}, {names.get(r['region'], r['region'].upper())} | {r['companies']} | ${r['open_rebate_usd']:,} | {r['gsc_impressions_90d']} | {r['top5_with_email']}/5 | {r['advisor_page']} |")
        lines.append("")
    (OUT / f"city-strategy-{stamp}.md").write_text("\n".join(lines), encoding="utf-8")
    print("tiers", {k: len(v) for k, v in t.items()}, "waves", {k: len(v) for k, v in sorted(wv.items())})
    for r in t["A"][:25]:
        print(r["tier"], r["city"], r["region"], "n", r["companies"], "reb", r["open_rebate_usd"], "gsc", r["gsc_impressions_90d"], "emails", r["top5_with_email"])


if __name__ == "__main__":
    main()
