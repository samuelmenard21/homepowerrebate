#!/usr/bin/env python3
"""Internal links to the 2026 awards (2026-11-04). A post-step; idempotent; does nothing until data/awards/2026.json has "live": true.
For every city with winners it puts an AWARD-LINK box on the city's installer ranking pages (all categories that exist for the city) and on the
city hub, linking to that city's winners row (/installers/awards/2026/<category>/#<city>). Also a footer-independent "winners" link on the homepage
is handled by build_home.py at launch. Usage: python3 scripts/add_award_links.py [--preview] [--remove]"""
import argparse, json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from apply_canonical_nav_footer import content_insert_point  # noqa: E402

S, E_ = "<!-- AWARD-LINK-START -->", "<!-- AWARD-LINK-END -->"
RE = re.compile(re.escape(S) + r".*?" + re.escape(E_) + r"\n?", re.S)
LABEL = {"heat-pump": "heat pump", "battery": "home battery", "solar": "solar"}


def box(city, year, cats):
    links = " &middot; ".join(f'<a href="/installers/awards/{year}/{c}/#{slug}">{LABEL[c]}</a>' for c, slug in cats)
    return (f'{S}<aside style="margin:20px 0;padding:14px 18px;background:#f5efe5;border:1px solid #d9d0c1;border-radius:12px" aria-label="{year} award winners in {city}">'
            f'<b style="font-family:Fraunces,Georgia,serif;font-size:18px">The {year} Best Installers in {city}</b>'
            f'<p style="margin:4px 0 0">Meet the top 3 in {city}: {links}. <a href="/installers/awards/{year}/">See every city</a>.</p></aside>{E_}\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--remove", action="store_true")
    a = ap.parse_args()
    d = json.loads((ROOT / "data/awards/2026.json").read_text(encoding="utf-8"))
    year = d["year"]
    pages = [p for p in ROOT.glob("installers/*/*/*/index.html")] + [p for p in ROOT.glob("ca/*/*/index.html")] + [p for p in ROOT.glob("us/*/*/index.html")]
    if a.remove:
        n = 0
        for f in pages:
            s = f.read_text(encoding="utf-8")
            t = RE.sub("", s)
            if t != s:
                f.write_text(t, encoding="utf-8"); n += 1
        print(n, "award link boxes removed"); return
    if not d.get("live") and not a.preview:
        print("awards are not live: nothing to do"); return
    regions = {r["code"]: r["path"] for r in json.loads((ROOT / "data/regions.json").read_text(encoding="utf-8"))["regions"]}
    cities = defaultdict(lambda: {"cats": [], "name": ""})
    for sv, lst in d["winners"].items():
        for c in lst:
            k = (c["region"], c["slug"]); cities[k]["name"] = c["city"]; cities[k]["cats"].append((sv, c["slug"]))
    n = 0
    for (reg, slug), v in cities.items():
        targets = [ROOT / "installers" / reg / slug / cat / "index.html" for cat in ("heat-pump", "battery", "solar", "insulation", "energy-advisor")]
        if reg in regions:
            targets.append(ROOT / regions[reg] / slug / "index.html")
        b = box(v["name"], year, sorted(v["cats"]))
        for f in targets:
            if not f.exists(): continue
            s = f.read_text(encoding="utf-8")
            if S in s:
                new = RE.sub(lambda m: b, s, count=1)
            else:
                i = content_insert_point(s)
                if i < 0: continue
                new = s[:i] + b + s[i:]
            if new != s:
                f.write_text(new, encoding="utf-8"); n += 1
    print(n, "pages updated")


if __name__ == "__main__":
    main()
