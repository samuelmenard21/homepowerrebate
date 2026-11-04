#!/usr/bin/env python3
"""/us/ma/heat-pump-installer-network/: what Mass Save's Heat Pump Installer Network list is, by county (2026-11-04).
Built from data/ma-hpin-contractors.json (scripts/refresh_ma_hpin.py) and fact ma-38. It says only what Mass Save's list says: who is on it,
the counties served, how many offer the instant rebate. It does NOT say a rebate requires network membership (not verified).
Usage: python3 scripts/build_ma_hpin_page.py, then post_steps.py"""
import html
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_heat_pump_hub as hub  # noqa: E402
import build_installer_rankings as br  # noqa: E402

e = html.escape
PATH = "/us/ma/heat-pump-installer-network/"


def main():
    d = json.loads((ROOT / "data" / "ma-hpin-contractors.json").read_text(encoding="utf-8"))
    cs = d["contractors"]
    res = [c for c in cs if "Residential" in c["property_types"]]
    rev = date.fromisoformat(d["checked"]).strftime("%B %-d, %Y")
    ranked = {r["city"]: r for r in hub.city_rows() if r["region"] == "ma"}
    counties = {}
    for city, county in br.MA_COUNTY.items():
        counties.setdefault(county, []).append(city)
    rows = ""
    for county in sorted({c for x in res for c in x["counties"]}, key=lambda k: -sum(1 for x in res if k in x["counties"])):
        serving = [x for x in res if county in x["counties"]]
        inst = sum(1 for x in serving if x["instant_rebate"] == "Yes")
        links = ", ".join(f'<a href="{ranked[c]["url"]}">{e(c)}</a>' for c in sorted(counties.get(county, [])) if c in ranked) or "none yet"
        rows += f"<tr><td>{e(county)}</td><td>{len(serving):,}</td><td>{inst:,}</td><td>{links}</td></tr>"
    table = ('<div class="table-wrap"><table class="hub-table"><thead><tr><th>County</th><th>Residential contractors that serve it</th><th>Offer the instant rebate</th>'
             f'<th>Cities where we rank installers</th></tr></thead><tbody>{rows}</tbody></table></div>')
    eq = {}
    for x in res:
        for q in x["equipment"]:
            eq[q] = eq.get(q, 0) + 1
    eq_li = "".join(f"<li>{e(k)}: {v:,} contractors</li>" for k, v in sorted(eq.items(), key=lambda kv: -kv[1]))
    n_inst = sum(1 for x in res if x["instant_rebate"] == "Yes")
    body = (f'<div class="callout"><p><strong>Short answer:</strong> Mass Save lists {len(cs):,} contractors in its Heat Pump Installer Network ({len(res):,} that serve homes), in a list revised {rev}. '
            f'Mass Save says they have shown proof of EPA certification and Massachusetts insurance and completed heat pump installation training. '
            f'It does not endorse their work, and neither do we: the list does not rank anyone.</p></div>'
            f'<h2>What the list tells you, and what it does not</h2>'
            f'<p>It tells you who has joined the network, which counties each contractor serves, what equipment they install and whether they offer the instant rebate ({n_inst:,} of the {len(res):,} home contractors do). '
            f'It does not tell you how good a contractor is, what they charge, or whether a particular rebate requires membership. We have not verified that last point, so ask Mass Save which contractors qualify for the rebate you want before you sign.</p>'
            f'<h2>Contractors by county</h2>{table}'
            f'<p>A contractor can serve several counties, so the counts add up to more than the total. Each city page lists the network contractors with an office in that city, and marks the ones on our review-ranked list with a ✓.</p>'
            f'<h2>Equipment the home contractors install</h2><ul>{eq_li}</ul>'
            f'<h2>How to pick one</h2><p>Start with the contractors in your county that install the equipment you want. Then compare Google reviews and written quotes, as on our '
            f'<a href="/installers/heat-pump/ma/">Massachusetts heat pump installer rankings</a>. Ask each one for a written heat-loss calculation and an itemized quote.</p>'
            f'<p class="small">Source: Mass Save Heat Pump Installer Network contractor list, revised {rev}. {e(d["disclaimer"])}</p>')
    faqs = [("What is the Mass Save Heat Pump Installer Network?",
             f"It is a list of contractors that Mass Save publishes. Mass Save says they have provided proof of EPA certification and insurance in Massachusetts and have completed heat pump installation training. The list we read has {len(cs):,} contractors and was revised {rev}."),
            ("Does Mass Save approve or endorse these contractors?", "No. Mass Save says its sponsors do not endorse or warrant the performance of installed or serviced equipment and make no representations about the contractors' services."),
            ("Do I have to use a network contractor to get a Mass Save heat pump rebate?",
             "We have not verified that, so we do not say yes or no. Ask Mass Save which contractors qualify for the rebate you want before you sign a contract."),
            ("How do I find a network contractor near me?", "Find your county in the table above and open the city page for the closest city we rank. You can also check Mass Save's own list, which shows each contractor's counties, equipment and languages.")]
    hub.page(PATH, "Mass Save Heat Pump Installer Network: By County",
             f"Mass Save lists {len(cs):,} contractors in its Heat Pump Installer Network. See who serves your county, who offers the instant rebate, and how to compare them.",
             "Mass Save Heat Pump Installer Network", f"{len(cs):,} contractors",
             f"Mass Save's own list of heat pump contractors, by county. Revised {rev}. Not a ranking.",
             [("Massachusetts", "/us/ma/"), ("Heat pump installer network", None)], body, faqs)
    print("MA HPIN page written")


if __name__ == "__main__":
    main()
