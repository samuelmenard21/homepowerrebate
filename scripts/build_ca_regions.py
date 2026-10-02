#!/usr/bin/env python3
"""California region pages (/us/ca/<region>/) built only from data/verified-facts + data/calc/ca.json.

The old pages were one Bay Area template copied to every region: it called Los Angeles "PG&E and SMUD territory" and quoted a SMUD amount that
disagrees with SMUD's own page. Utility territory is stated only where a verified fact says it (Sacramento = SMUD, Los Angeles = LADWP,
Glendale, Burbank, Pasadena = their own utilities, Long Beach and Santa Monica = SCE). Elsewhere the page says which programs we could verify
and which we could not."""
import html
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell, AUTHOR, BASE  # noqa: E402
from build_calculator import load_facts, money, CSS  # noqa: E402
from build_hub_tops import status_pill  # noqa: E402

e = html.escape
FACTS = load_facts()
SPEC = json.loads((ROOT / "data" / "calc" / "ca.json").read_text())
PROGS = {p["id"]: p for p in SPEC["programs"]}
STATEWIDE = ["tech-hp", "heehra-hp", "sgip"]
UTIL_NAME = {"smud": "SMUD", "ladwp": "LADWP", "gwp": "Glendale Water & Power", "bwp": "Burbank Water & Power", "pwp": "Pasadena Water & Power", "sce": "Southern California Edison"}
REGIONS = {
    "sacramento": {"name": "Sacramento", "utils": ["smud"], "intro": "Sacramento is served by SMUD, which runs its own rebates.",
                   "cities": ["sacramento", "folsom", "rancho-cordova", "roseville"]},
    "los-angeles": {"name": "Los Angeles", "utils": ["ladwp", "gwp", "bwp", "pwp", "sce"],
                    "intro": "Los Angeles is served by LADWP. Nearby Glendale, Burbank and Pasadena run their own utilities, and Long Beach and Santa Monica are served by Southern California Edison.",
                    "cities": ["los-angeles", "glendale", "burbank", "pasadena", "long-beach", "santa-monica"]},
    "roseville": {"name": "Roseville", "utils": [], "path": "/us/ca/sacramento/roseville/", "dir": "us/ca/sacramento/roseville", "parent": ("Sacramento area", "/us/ca/sacramento/"),
                  "cities": ["roseville"],
                  "short": ("Roseville is served by its own city electric utility, Roseville Electric, not by SMUD, so SMUD's rebates do not apply here. The City's rebate pages for heat pumps and water heaters are marked archived on its website, "
                            "so we could not confirm a current Roseville Electric rebate and show no amounts. Statewide heat pump help (TECH Clean California and the federal HEEHRA program) is fully reserved and taking waitlist requests only."),
                  "lead": "Roseville has its own electric utility. Here is what we could and could not confirm.",
                  "unconfirmed": ("<h2>What we could not confirm</h2><p>The City of Roseville's electric rebates. Its pages for the <a href='https://www.roseville.ca.us/government/departments/electric_utility/rebates_and_energy_savings/heat_pump_water_heater_archived' rel='nofollow noopener' target='_blank'>heat pump water heater</a> "
                                  "and <a href='https://www.roseville.ca.us/government/departments/electric_utility/rebates_and_energy_savings/h_v_a_c_heat_pump_rebate_archived' rel='nofollow noopener' target='_blank'>heat pump HVAC</a> rebates are marked archived (read October 1, 2026). "
                                  "Ask Roseville Electric whether any rebate is open before you buy, and tell us at <a href='mailto:hello@homepowerrebate.com'>hello@homepowerrebate.com</a> if you find a current one.</p>")},
    "berkeley": {"name": "Berkeley", "utils": [], "path": "/us/ca/bay-area/berkeley/", "dir": "us/ca/bay-area/berkeley", "parent": ("Bay Area", "/us/ca/bay-area/"), "cities": ["berkeley"]},
    "fremont": {"name": "Fremont", "utils": [], "path": "/us/ca/bay-area/fremont/", "dir": "us/ca/bay-area/fremont", "parent": ("Bay Area", "/us/ca/bay-area/"), "cities": ["fremont"]},
    "oakland": {"name": "Oakland", "utils": [], "path": "/us/ca/bay-area/oakland/", "dir": "us/ca/bay-area/oakland", "parent": ("Bay Area", "/us/ca/bay-area/"), "cities": ["oakland"]},
    "san-francisco": {"name": "San Francisco", "utils": [], "path": "/us/ca/bay-area/san-francisco/", "dir": "us/ca/bay-area/san-francisco", "parent": ("Bay Area", "/us/ca/bay-area/"), "cities": ["san-francisco"]},
    "san-jose": {"name": "San Jose", "utils": [], "path": "/us/ca/bay-area/san-jose/", "dir": "us/ca/bay-area/san-jose", "parent": ("Bay Area", "/us/ca/bay-area/"), "cities": ["san-jose"]},
    "bay-area": {"name": "Bay Area", "utils": [], "intro": "", "cities": ["berkeley", "fremont", "oakland", "san-francisco", "san-jose"]},
    "inland-empire": {"name": "Inland Empire", "utils": [], "intro": "", "cities": ["riverside", "san-bernardino", "moreno-valley", "ontario"]},
    "bakersfield": {"name": "Bakersfield", "utils": [], "intro": "", "cities": ["bakersfield"]},
    "fresno": {"name": "Fresno", "utils": [], "intro": "", "cities": ["fresno"]},
    "san-diego": {"name": "San Diego", "utils": [], "intro": "", "cities": ["san-diego", "chula-vista", "escondido"]},
}
CITY_LABEL = {"roseville": "Roseville (its own utility, not SMUD)", "san-jose": "San Jose", "san-francisco": "San Francisco", "rancho-cordova": "Rancho Cordova", "moreno-valley": "Moreno Valley", "san-bernardino": "San Bernardino",
              "long-beach": "Long Beach", "santa-monica": "Santa Monica", "los-angeles": "Los Angeles", "san-diego": "San Diego", "chula-vista": "Chula Vista"}


def row(p):
    fx = FACTS[p["fact"]]
    return (f"<tr><td><b>{e(p['name'])}</b></td><td>{e(money(p))}{status_pill(fx['status'])}</td>"
            f"<td>{e(p['rules'])} <a href='{e(fx['source_url'])}' rel='nofollow noopener' target='_blank'>Source</a> <span class='small'>(checked {e(fx['verified_on'])})</span></td></tr>")


def table(ids):
    return "<div class='tw'><table><tr><th>Program</th><th>Amount</th><th>Rules</th></tr>" + "".join(row(PROGS[i]) for i in ids) + "</table></div>"


def util_programs(u):
    return [p["id"] for p in SPEC["programs"] if (p.get("when") or {}).get("utility") == [u] and FACTS[p["fact"]]["status"] in ("active", "upcoming")]


def page(slug, r):
    path = r.get("path", f"/us/ca/{slug}/")
    name = r["name"]
    latest = max(FACTS[p["fact"]]["verified_on"] for p in SPEC["programs"])
    when = date.fromisoformat(latest).strftime("%B %-d, %Y")
    secs = []
    for u in r["utils"]:
        ids = util_programs(u)
        if ids:
            secs.append(f"<h2>{e(UTIL_NAME[u])} rebates</h2>{table(ids)}<p><a href='/calculator/ca/?utility={u}'>Estimate your {e(UTIL_NAME[u])} rebates</a></p>")
    if r.get("short"):
        short, lead = r["short"], r["lead"]
        secs.append(r["unconfirmed"])
    elif r["utils"]:
        short = (f"{r['intro']} Your utility sets which rebates you can claim, so find it below. Statewide help for heat pumps (TECH Clean California and the federal HEEHRA program) is fully reserved "
                 "and taking waitlist requests only.")
        lead = "Rebates depend on your electric utility. Here is what each one pays, with a source for every amount."
    else:
        short = (f"We have not verified a current home rebate from the utilities that serve {name} (PG&E, Southern California Edison, SDG&E and others) on a program page, so we show no utility amounts here. "
                 "Statewide heat pump help (TECH Clean California and the federal HEEHRA program) is fully reserved and taking waitlist requests only. The federal 25C and 25D tax credits ended for 2026 installs.")
        lead = "California's statewide programs are full. Here is exactly where each stands, and what we could not confirm."
        secs.append("<h2>What we could not confirm</h2><p>Utility rebates from PG&amp;E, Southern California Edison and SDG&amp;E. Quoted amounts on other sites do not match a program page we could read, so we leave them out. "
                    "Ask your utility before you buy, and tell us at <a href='mailto:hello@homepowerrebate.com'>hello@homepowerrebate.com</a> if you find a current one.</p>")
    state = table(STATEWIDE)
    cities = "".join(f"<li><a href='/us/ca/{slug}/{c}/'>{e(CITY_LABEL.get(c, c.replace('-', ' ').title()))}</a></li>" if (ROOT / "us" / "ca" / slug / c / "index.html").exists() and not r.get("path") else
                     f"<li>{e(CITY_LABEL.get(c, c.replace('-', ' ').title()))}</li>" for c in r["cities"])
    inst = "".join(f"<li><a href='/installers/ca/{c}/heat-pump/'>Heat pump installers in {e(CITY_LABEL.get(c, c.replace('-', ' ').title()))}</a></li>" for c in r["cities"]
                   if (ROOT / "installers" / "ca" / c / "heat-pump" / "index.html").exists())
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/us/ca/">California</a></li>{f'<li><a href="{r["parent"][1]}">{r["parent"][0]}</a></li>' if r.get("parent") else ""}<li aria-current="page">{e(name)}</li></ol></nav>
<header class="hero"><div class="wrap"><h1>{e(name)} Home Energy Rebates 2026: What Is Open</h1><p>{e(lead)}</p><p class="meta">By {e(AUTHOR['name'])} · Checked {e(when)}</p></div></header>
<section class="body"><div class="wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> {e(short)}</p></div>
{"".join(secs)}
<h2>Statewide programs</h2>{state}
<p>The federal 25C and 25D tax credits ended for spending after December 31, 2025, so we do not count them.</p>
<h2>Check your own numbers</h2><p><a href="/calculator/ca/">California rebate calculator</a> · <a href="/get-quotes/?province=ca">Get my plan and top-rated installers</a></p>
{"" if r.get("path") else "<h2>Cities in this area</h2><ul>" + cities + "</ul>"}
{"<h2>Top-rated installers</h2><ul>" + inst + "</ul>" if inst else ""}
<p class="small">Installers are ranked by Google reviews only. Nobody pays to be listed.</p>
</div></section>"""
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": f"{name} Home Energy Rebates 2026", "author": AUTHOR, "dateModified": latest, "mainEntityOfPage": BASE + path,
           "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE}}]
    title = f"{name} Home Energy Rebates 2026: What Is Open | HomePowerRebate"
    desc = f"What home energy rebates are open in {name}, California: utility programs, statewide waitlists and what has ended, with a source for every amount."
    out = shell(title, desc, path, "ca", body, ld)
    return out.replace("</style>", ".tw{overflow-x:auto}.tw table{min-width:520px}" + CSS + "</style>", 1)


def main():
    for slug, r in REGIONS.items():
        f = ROOT / r.get("dir", f"us/ca/{slug}") / "index.html"
        f.write_text(page(slug, r), encoding="utf-8")
        print("Wrote", f.relative_to(ROOT))


if __name__ == "__main__":
    main()
