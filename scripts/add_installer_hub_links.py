#!/usr/bin/env python3
"""Link the heat pump installer hubs (/installers/heat-pump/ and /installers/heat-pump/<region>/) from the pages people read before they
hire: every region hub, every region calculator, and every heat pump blog post (2026-11-04). The ranking pages had a median of 2
links from outside /installers/. Each block sits between INSTALLER-HUB-START/END (placed right after </article>, else above the footer),
so re-runs replace it. Counts come from installers/rankings.json. A post-step; idempotent.
Usage: python3 scripts/add_installer_hub_links.py"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import regions as regions_mod  # noqa: E402

S, E = "<!-- INSTALLER-HUB-START -->", "<!-- INSTALLER-HUB-END -->"
BOX = 'style="max-width:880px;margin:24px auto;padding:16px 22px;background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;font-size:15.5px;line-height:1.6;"'
MIN_CITIES = 4  # same rule as build_heat_pump_hub.py


def block(name, code, n_cities, n_companies):
    if code and n_cities >= MIN_CITIES:
        href, text = f"/installers/heat-pump/{code}/", f"See the top-rated heat pump installers in {n_cities} {name} cities"
    else:
        href, text = "/installers/heat-pump/", "See the top-rated heat pump installers in your city"
    extra = f" ({n_companies:,} companies ranked by Google reviews)" if code and n_cities >= MIN_CITIES else " (ranked by Google reviews)"
    return f'{S}<section {BOX}><b>Ready to hire?</b> <a href="{href}">{text}</a>{extra}. Free to compare.</section>{E}'


def put(path, blk):
    t = path.read_text(encoding="utf-8")
    if S in t and E in t:
        new = re.sub(re.escape(S) + r"[\s\S]*?" + re.escape(E), lambda _: blk, t, count=1)
    else:
        m = re.search(r"</article>", t)
        i = m.end() if m else navfooter.content_insert_point(t)
        if i < 0:
            return False
        new = t[:i] + "\n" + blk + "\n" + t[i:]
    if new != t:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def main():
    rk = [m for m in json.loads((ROOT / "installers" / "rankings.json").read_text(encoding="utf-8"))
          if m["service"] == "heat-pump" and m.get("indexed", True)]
    stat = {}
    for m in rk:
        c = stat.setdefault(m["region"], [0, 0])
        c[0] += 1
        c[1] += m["count"]
    changed = 0
    for r in regions_mod.REGIONS:
        code, name = r["code"], r["name"]
        n, co = stat.get(code, [0, 0])
        blk = block(name, code, n, co)
        for rel in (f"{r['country']}/{code}/index.html", f"calculator/{code}/index.html"):
            p = ROOT / rel
            if p.exists():
                changed += put(p, blk)
    # heat pump blog posts: the region hub when the post names a region, else the national hub
    by_name = {r["name"].lower(): r for r in regions_mod.REGIONS}
    idx = json.loads((ROOT / "data" / "blog-index.json").read_text(encoding="utf-8"))
    for sec in idx["sections"]:
        for post in sec["posts"]:
            if "heat-pump" not in post["slug"] and "heat pump" not in post["title"].lower():
                continue
            p = ROOT / "blog" / post["slug"] / "index.html"
            if not p.exists():
                continue
            r = by_name.get(post.get("region", "").lower())
            blk = block(r["name"], r["code"], *stat.get(r["code"], [0, 0])) if r else block("", "", 0, 0)
            changed += put(p, blk)
    print(f"{changed} pages updated with installer hub links.")


if __name__ == "__main__":
    main()
