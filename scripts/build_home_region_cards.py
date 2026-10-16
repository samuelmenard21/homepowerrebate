#!/usr/bin/env python3
"""llms.txt "Regions covered" section, rebuilt from data/regions.json (name, home_blurb, cities, hub path) on every run.
The homepage region cards, meta region lists and city counts are rebuilt by build_home_hero.py (sync_regions).
Both run from scripts/sync_regions.py, the one command to run after adding a region or a city."""
import html as _h
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import regions  # noqa: E402
from build_get_quotes import city_slugs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FEDERAL = ("- Canada (federal) — National Heat Pump Rebate announced Oct 8, 2026: up to $10,000 below the median income, $2,000 otherwise, "
           "launch expected early 2027, eligibility rules not yet published. /programs/national-heat-pump-rebate/ and guides at "
           "/blog/should-you-wait-federal-heat-pump-rebate/, /blog/federal-heat-pump-rebate-stacking-by-province/")


def line(r):
    names = ", ".join(c[1] for c in r["cities"])
    n = len(city_slugs(r["code"]))
    return f'- {r["name"]} — {_h.unescape(r.get("home_blurb") or "")} {n} {"city" if n == 1 else "cities"}, including {names}. /{r["path"]}/'


def main():
    lp = ROOT / "llms.txt"
    t = lp.read_text()
    ca = [line(r) for r in regions.REGIONS if r["country"] == "ca"] + [FEDERAL]
    us = [line(r) for r in regions.REGIONS if r["country"] == "us"]
    sec = (f"## Regions covered ({len(regions.REGIONS)})\n\n**Canada**\n" + "\n".join(ca)
           + "\n\n**United States**\n" + "\n".join(us) + "\n\n")
    a = t.index("## Regions covered")
    b = t.index("Note: as of 2026, the federal 25C/25D", a)
    new = t[:a] + sec + t[b:]
    if new != t:
        lp.write_text(new)
    print("llms.txt regions:", len(regions.REGIONS))


if __name__ == "__main__":
    main()
