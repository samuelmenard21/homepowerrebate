#!/usr/bin/env python3
"""Add Newfoundland and Labrador city rebate summaries to city-rebate-lookup.json (used by the lead-router emails).
Every amount comes from data/verified-facts/nl.json (read 2026-10-16). Categories without a verified program are left out.
Idempotent: rewrites only the nl| keys. Run, then redeploy the lead router (wrangler deploy)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "city-rebate-lookup.json"
HP = ("Oil or propane homes: up to $22,000 for a central heat pump if income-qualified, up to $9,000 otherwise (takeCHARGE Oil to Electric, "
      "paid to a participating installer). No takeCHARGE heat pump rebate for homes already on electric heat")
CATS = {
    "heat_pump": HP,
    "insulation": "75% of cost, up to $1,000 attic and $1,000 basement plus up to $500 labour each (takeCHARGE; electric heat, home built before 2014)",
    "hrv": "$225 (takeCHARGE, eligible model, HRAI certified installer)",
    "solar": "$0 (no takeCHARGE homeowner solar rebate)",
    "battery": "$0 (no current program)",
}
CITIES = {"st-johns": ("St. John's", "Newfoundland Power"), "mount-pearl": ("Mount Pearl", "Newfoundland Power"), "paradise": ("Paradise", "Newfoundland Power"),
          "corner-brook": ("Corner Brook", "Newfoundland Power (confirm on your bill)"), "labrador-city": ("Labrador City", "Newfoundland and Labrador Hydro")}


def key(name):
    """Same normalization as normalizeCityKey() in lead-router.js."""
    return " ".join(name.lower().replace(".", "").replace(",", "").split())


d = json.loads(FILE.read_text())
for k in [k for k in d if k.startswith("nl|")]:
    del d[k]
for slug, (name, util) in CITIES.items():
    d[f"nl|{key(name)}"] = {"city": name, "region": "NL", "utility": util, "categories": dict(CATS), "heat_pump_rebate": HP}
FILE.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print(len(CITIES), "NL cities in city-rebate-lookup.json")
