#!/usr/bin/env python3
"""Merge the researched community lists (data/city-areas-parts/*.json, one per region group) into data/city-areas.json.

Each entry names the page it was read from (source_url). Only "inside" names are published: the research agents could not
confirm adjacency for most "nearby" towns, and the ranking pages already link the closest cities by distance. Entries with fewer
than MIN_INSIDE names are dropped (a thin list says little). DROP removes names a reviewer found weak (a caption mention, a retail
centre, a hill). Run build_installer_rankings.py and post_steps.py afterwards."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTS = ROOT / "data" / "city-areas-parts"
MIN_INSIDE = 3
PLACE = {"bc/langley": "the Township of Langley"}   # the cited page covers the Township, not the City of Langley
DROP = {"ny/albany": {"Helderberg"}, "ca/roseville": {"Fountains at Roseville"}, "ca/folsom": {"Carpenter Hill"},
        "ca/rancho-cordova": {"Barrel District", "Villages of Zinfandel"}}


def main():
    out, dropped = {}, []
    for f in sorted(PARTS.glob("*.json")):
        if f.name.startswith("_"):
            continue
        for key, v in json.loads(f.read_text(encoding="utf-8")).items():
            inside = [n for n in v.get("inside", []) if n not in DROP.get(key, set())]
            if len(inside) < MIN_INSIDE or not v.get("source_url"):
                dropped.append(key)
                continue
            e = {"inside": inside, "source": v["source"], "source_url": v["source_url"]}
            if key in PLACE:
                e["place"] = PLACE[key]
            if v.get("lead"):
                e["lead"] = v["lead"]
            out[key] = e
    (ROOT / "data" / "city-areas.json").write_text(json.dumps(dict(sorted(out.items())), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(out)} cities with a sourced community list; left out (too few names): {', '.join(dropped) or 'none'}")


if __name__ == "__main__":
    main()
