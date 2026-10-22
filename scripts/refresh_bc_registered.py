#!/usr/bin/env python3
"""Refresh the BC "registered contractor" matches from the official Better Homes BC list, 2026-10-22.
Better Homes BC publishes the whole list of program registered contractors (members of the Home Performance Contractor Network) as a
public JSON feed behind https://betterhomesbc.ca/get-support/contractors/ (1,303 companies on 2026-10-22, each with the programs it is
registered for: CleanBC Energy Savings Program (ESP) and the BC Hydro Home Renovation Rebate (HRR), and the upgrade types). The rules say a
program registered contractor is required for all ESP upgrades and for HRR heat pump and insulation upgrades, so a homeowner who hires an
unregistered contractor loses the rebate. This script
  1. downloads the list once (data/bc-registered-contractors.json, compact),
  2. matches every BC company on our heat pump and insulation rankings to it, high confidence only (same website domain, same email, or same
     phone AND a similar name), never on a name alone,
  3. rewrites the BC heat-pump and insulation matches in data/rebate-registered.json (BC solar and NY matches are left alone).
build_installer_rankings.py and generate_installer_profiles.py already show a "✓" badge from that file.
Usage: python3 scripts/refresh_bc_registered.py [--offline] && python3 scripts/build_installer_rankings.py && python3 scripts/build_installer_profiles.py && python3 scripts/post_steps.py
(git add -f data/bc-registered-contractors.json data/rebate-registered.json: data/ is gitignored.)"""
import csv
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
FEED = "https://betterhomesbc.ca/wp-json/custom/v1/contractors"
PAGE = "https://betterhomesbc.ca/get-support/contractors/"
RAW = ROOT / "data" / "bc-registered-contractors.json"
REG = ROOT / "data" / "rebate-registered.json"
BC_CITIES = {"Abbotsford", "Burnaby", "Chilliwack", "Coquitlam", "Fort St. John", "Kamloops", "Kelowna", "Langley", "Maple Ridge", "Nanaimo", "Penticton",
             "Prince George", "Richmond", "Squamish", "Surrey", "Vancouver", "Vernon", "Victoria"}
SERVICES = {"heat-pump": "Heat pumps", "insulation": "Insulation"}
GENERIC_MAIL = {"gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "shaw.ca", "telus.net", "icloud.com", "live.com", "me.com", "aol.com", "msn.com", "yahoo.ca", "hotmail.ca"}
STOP = {"ltd", "inc", "the", "and", "co", "corp", "company", "services", "service", "bc", "of", "ltd.", "inc."}


def digits(s):
    d = re.sub(r"\D", "", s or "")
    return d[-10:] if len(d) >= 10 else ""


def domain(u):
    u = (u or "").strip()
    if not u:
        return ""
    return urlparse(u if "://" in u else "http://" + u).netloc.lower().replace("www.", "")


def tokens(s):
    return {t for t in re.sub(r"[^a-z0-9 ]", " ", (s or "").lower().replace("&", " and ")).split() if t not in STOP and len(t) > 1}


def similar(a, b):
    ta, tb = tokens(a), tokens(b)
    return len(ta & tb) / len(ta | tb) if ta and tb else 0.0


def download():
    req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0 (HomePowerRebate list check; hello@homepowerrebate.com)"})
    raw = json.load(urllib.request.urlopen(req, timeout=60))
    out = []
    for c in raw:
        out.append({"name": c.get("company_name") or c.get("title"), "city": c.get("head_office_location") or "", "site": c.get("company_website") or "", "email": c.get("email") or "",
                    "phone": c.get("phone") or "", "programs": sorted(t["slug"] for t in (c.get("program_designations") or [])), "types": sorted(t["name"] for t in (c.get("types") or [])),
                    "url": c.get("post_url") or ""})
    RAW.write_text(json.dumps({"checked": date.today().isoformat(), "source": PAGE, "contractors": out}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return out


def main():
    data = json.loads(RAW.read_text(encoding="utf-8"))["contractors"] if "--offline" in sys.argv and RAW.exists() else download()
    today = date.today().isoformat()
    by_phone, by_site, by_mail, by_name = {}, {}, {}, {}
    for c in data:
        if digits(c["phone"]):
            by_phone.setdefault(digits(c["phone"]), []).append(c)
        if tokens(c["name"]):
            by_name.setdefault(frozenset(tokens(c["name"])), []).append(c)
        if domain(c["site"]):
            by_site.setdefault(domain(c["site"]), []).append(c)
        m = c["email"].lower().strip()
        if m and m.split("@")[-1] not in GENERIC_MAIL:
            by_mail.setdefault(m.split("@")[-1], []).append(c)
        if m:
            by_mail.setdefault(m, []).append(c)
    reg = json.loads(REG.read_text(encoding="utf-8"))
    keep = [m for m in reg["matches"] if not (m["region"] == "bc" and m["service"] in SERVICES)]
    programs = {k: v for k, v in reg["programs"].items() if not k.startswith("bc_reg_")}
    why = ("Better Homes BC lists this company as a program registered contractor (a Home Performance Contractor Network member). "
           "A registered contractor is required for all CleanBC Energy Savings Program upgrades and for BC Hydro Home Renovation Rebate heat pump and insulation upgrades.")
    new = []
    for service, utype in SERVICES.items():
        f = ROOT / "installers" / f"{service}-installers-real.csv"
        for r in csv.DictReader(open(f, encoding="utf-8")):
            if r["City"] not in BC_CITIES:
                continue
            cands, why_m = [], ""
            d, p, e = domain(r["Website"]), digits(r["Phone"]), (r["Email"] or "").lower().strip()
            for c in by_site.get(d, []) if d else []:
                if similar(r["Business Name"], c["name"]) >= 0.2:
                    cands, why_m = [c], "website domain and name match on the official list"
            if not cands and e:
                for c in by_mail.get(e, []) + (by_mail.get(e.split("@")[-1], []) if e.split("@")[-1] not in GENERIC_MAIL else []):
                    if similar(r["Business Name"], c["name"]) >= 0.2 or c["email"].lower() == e:
                        cands, why_m = [c], "email match on the official list"
                        break
            if not cands and p:
                for c in by_phone.get(p, []):
                    if similar(r["Business Name"], c["name"]) >= 0.34:
                        cands, why_m = [c], "phone number and name match on the official list"
            if not cands:  # same company name (all words equal) and the same city, for companies with no site or phone on the list
                for c in by_name.get(frozenset(tokens(r["Business Name"])), []):
                    if c["city"].strip().lower() and (c["city"].strip().lower() in r["City"].lower() or r["City"].lower() in c["city"].strip().lower()):
                        cands, why_m = [c], "exact company name and city match on the official list"
                        break
            if not cands:
                continue
            c = cands[0]
            if utype not in c["types"]:
                continue
            ps = set(c["programs"])
            key = "both" if {"esp", "hrr"} <= ps else ("esp" if "esp" in ps else "hrr")
            pk = f"bc_reg_{'hp' if service == 'heat-pump' else 'ins'}_{key}"
            label = {"both": "ESP and HRR", "esp": "ESP only", "hrr": "HRR only"}[key]
            programs[pk] = {"name": f"Better Homes BC program registered contractor ({label})", "short": f"Registered contractor ({label})", "region": "bc", "service": service,
                            "why": why + f" Registered for: {label}.", "source_url": PAGE, "checked": today}
            new.append({"region": "bc", "service": service, "business": r["Business Name"].strip(), "program": pk, "official_name": c["name"], "evidence": why_m, "confidence": "high"})
    old_hp = {m["business"] for m in reg["matches"] if m["region"] == "bc" and m["service"] == "heat-pump"}
    now_hp = {m["business"] for m in new if m["service"] == "heat-pump"}
    reg["matches"] = keep + new
    reg["programs"] = programs
    reg["checked"] = today
    REG.write_text(json.dumps(reg, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"official list: {len(data)} companies. BC matches written: {len(new)} ({sum(1 for m in new if m['service'] == 'heat-pump')} heat pump, {sum(1 for m in new if m['service'] == 'insulation')} insulation).")
    print(f"previously matched heat pump companies now missing: {sorted(old_hp - now_hp)}")


if __name__ == "__main__":
    main()
