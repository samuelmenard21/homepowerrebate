#!/usr/bin/env python3
"""Mass Save Heat Pump Installer Network contractors (HPIN), 2026-11-04.

Reads the spreadsheet Mass Save publishes ("Heat Pump Installer Network Contractors", revised date in its header) and
  1. writes data/ma-hpin-contractors.json (every contractor, its counties served, equipment, languages, instant rebate flag, office, website),
  2. matches ranked Massachusetts heat pump companies to it (high confidence only: same website domain, same phone, or same normalized
     name) and writes them into data/rebate-registered.json as program ma_hpin, so ranking cards show a "Mass Save HPIN" badge.
The spreadsheet is a public Mass Save list; masssave.com blocks automated readers, so the file is downloaded by hand and passed in.
Usage: python3 scripts/refresh_ma_hpin.py /path/to/hpin-contractors.xlsx [--source-url URL]
Rerun when Mass Save revises the list (monthly check), then build_installer_rankings.py, build_ma_hpin_page.py and post_steps.py."""
import argparse
import json
import re
import sys
import zipfile
from datetime import date
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
COLS = ["name", "property_types", "counties", "equipment", "other_tech", "languages", "diverse", "instant_rebate", "address", "city", "zip", "phone", "website", "hpln"]
PROGRAM = {"name": "Mass Save Heat Pump Installer Network", "short": "Mass Save HPIN", "region": "ma", "service": "heat-pump",
           "why": "Contractors in the Mass Save Heat Pump Installer Network have shown proof of EPA certification and Massachusetts insurance and completed heat pump installation training.",
           "required": False,   # we have not verified that a rebate requires network membership; the pages say so plainly
           "source_url": "https://www.masssave.com/", "checked": ""}


def parse(xlsx):
    z = zipfile.ZipFile(xlsx)
    ss = [unescape(re.sub(r"<[^>]+>", "", s)) for s in re.findall(r"<si>(.*?)</si>", z.read("xl/sharedStrings.xml").decode("utf-8"), re.S)]
    sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
    rows = []
    for rm in re.finditer(r"<row [^>]*>(.*?)</row>", sheet, re.S):
        cells = {}
        for cm in re.finditer(r'<c r="([A-Z]+)\d+"([^>]*?)(?:/>|>(.*?)</c>)', rm.group(1), re.S):
            col, attrs, inner = cm.group(1), cm.group(2), cm.group(3) or ""
            v = re.search(r"<v>(.*?)</v>", inner, re.S)
            if not v:
                continue
            cells[col] = ss[int(v.group(1))] if 't="s"' in attrs else unescape(v.group(1))
        if cells:
            rows.append(cells)
    head = next(i for i, r in enumerate(rows) if r.get("A", "").strip() == "Company Name")
    revised = next((re.search(r"Revised:\s*([\d-]+)", " ".join(r.values())) for r in rows[:head] if "Revised" in " ".join(r.values())), None)
    out = []
    for r in rows[head + 1:]:
        d = {k: (r.get(chr(65 + i), "") or "").strip() for i, k in enumerate(COLS)}
        if not d["name"]:
            continue
        d["counties"] = [c.strip() for c in d["counties"].split(";") if c.strip()]
        d["equipment"] = [c.strip() for c in d["equipment"].split(";") if c.strip()]
        d["other_tech"] = [c.strip() for c in d["other_tech"].split(";") if c.strip()]
        d["languages"] = [c.strip() for c in d["languages"].split(";") if c.strip()]
        d["property_types"] = d["property_types"].replace("&amp;", "&")
        d["zip"] = d["zip"].zfill(5) if d["zip"].isdigit() else d["zip"]   # Excel dropped the leading zero
        out.append(d)
    rev = revised.group(1) if revised else ""
    iso = date(int(rev.split("-")[2]), int(rev.split("-")[0]), int(rev.split("-")[1])).isoformat() if rev.count("-") == 2 else ""
    return out, iso


def norm_name(s):
    s = re.sub(r"&amp;", "and", s.lower().replace("&", " and "))
    s = re.sub(r"\b(inc|llc|ltd|corp|co|company|the|of)\b\.?", " ", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def domain(u):
    h = urlparse(u if "//" in u else "//" + u).netloc.lower() if u else ""
    return re.sub(r"^www\.", "", h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("--source-url", default="https://www.masssave.com/")
    a = ap.parse_args()
    contractors, revised = parse(a.xlsx)
    (ROOT / "data" / "ma-hpin-contractors.json").write_text(json.dumps(
        {"checked": revised or date.today().isoformat(), "source": "Mass Save Heat Pump Installer Network Contractors list (spreadsheet, revised %s)" % revised,
         "source_url": a.source_url, "intro": "The contractors that participate in the Mass Save Heat Pump Installer Network have provided proof of EPA certification and insurance in the state of Massachusetts and have completed heat pump installation training.",
         "disclaimer": "The Mass Save Sponsors do not endorse or warrant the performance of installed or serviced equipment and do not make any representations or warranties regarding the services provided by these contractors.",
         "contractors": contractors}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    # match ranked MA heat pump companies
    import build_installer_rankings as br
    by_dom, by_phone, by_name = {}, {}, {}
    for c in contractors:
        if domain(c["website"]):
            by_dom[domain(c["website"])] = c
        ph = re.sub(r"\D", "", c["phone"])[-10:]
        if len(ph) == 10:
            by_phone[ph] = c
        by_name[norm_name(c["name"])] = c
    f = ROOT / "data" / "rebate-registered.json"
    d = json.loads(f.read_text(encoding="utf-8"))
    d["matches"] = [m for m in d["matches"] if m.get("program") != "ma_hpin"]
    d["programs"]["ma_hpin"] = {**PROGRAM, "checked": revised or date.today().isoformat(), "source_url": a.source_url}
    n = 0
    for r in br.load_rows():
        if r["region"] != "ma" or r["service"] != "heat-pump":
            continue
        ph = re.sub(r"\D", "", r["phone"])[-10:]
        hit, why = None, ""
        if domain(r["website"]) and domain(r["website"]) in by_dom:
            hit, why = by_dom[domain(r["website"])], "website domain match on official list"
        elif len(ph) == 10 and ph in by_phone:
            hit, why = by_phone[ph], "phone match on official list"
        elif norm_name(r["name"]) in by_name:
            hit, why = by_name[norm_name(r["name"])], "exact name match on official list"
        if hit:
            d["matches"].append({"region": "ma", "service": "heat-pump", "business": r["name"], "program": "ma_hpin", "official_name": hit["name"], "evidence": why, "confidence": "high"})
            n += 1
    f.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(contractors)} contractors (revised {revised}); {n} ranked Massachusetts heat pump companies matched.")


if __name__ == "__main__":
    main()
