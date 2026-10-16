#!/usr/bin/env python3
"""Link weakly linked pages from the pages a reader would come from (added 2026-10-16).

Search Console listed 776 pages as "Discovered - currently not indexed". Most were already two clicks
from the homepage; 76 had 0 to 2 content links or no path from the homepage at all. Each parent page
below gets one marker-wrapped "Related pages" box. Link text is the target page's own h1, so it stays
current. Marker-wrapped, so re-runs replace the block. Run with the post-steps after any generator.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from apply_canonical_nav_footer import content_insert_point  # noqa: E402

MARK = "DISCOVERED-LINKS"
BOX = ('<section style="max-width:880px;margin:24px auto;padding:0 20px;"><p style="background:#f5efe5;'
       'border-radius:8px;padding:14px 18px;margin:0;"><b>{}</b> {}</p></section>')

BC_CITIES = ["abbotsford", "burnaby", "chilliwack", "coquitlam", "fort-st-john", "kamloops", "kelowna", "langley",
             "maple-ridge", "nanaimo", "penticton", "prince-george", "richmond", "squamish", "surrey", "vancouver",
             "vernon", "victoria"]

# parent page -> (label, [target paths])
JOBS = {}


def add(parent, label, *targets):
    JOBS.setdefault(parent, (label, []))[1].extend(targets)


for c in BC_CITIES:
    add(f"/ca/bc/{c}/", "More for your home:",
        f"/blog/energy-saving-ideas-bc-home-{c}/",
        f"/blog/free-heat-pump-bc-income-qualified-{c}/",
        f"/blog/window-doors-replacement-rebates-bc-guide-{c}/")
add("/ca/bc/kamloops/", "More for your home:", "/questions/kamloops-solar/")
add("/ca/bc/kelowna/", "More for your home:", "/questions/kelowna-heat_pump/", "/questions/kelowna-solar/")
add("/ca/bc/", "BC guides:", "/blog/heat-pump-or-solar-bc/", "/blog/rebate-rejected-bc/",
    "/questions/heat-pump-rebate-income-limits/", "/blog/energy-saving-ideas-ca-home/")
add("/ca/bc/heat-pump/", "Heat pump guides:", "/blog/trane-carrier-heat-pumps-bc/",
    "/technology/cold-climate-heat-pumps-2026/", "/technology/quilt-heat-pump-canada/",
    "/technology/plug-in-heat-pump-water-heaters/")
for c in ["philadelphia", "pittsburgh", "allentown", "erie"]:
    add(f"/us/pa/{c}/", "Pennsylvania-wide pages:", "/us/pa/appliances/", "/us/pa/windows/", "/us/pa/ev-charger/")
add("/us/pa/", "Pennsylvania-wide pages:", "/us/pa/appliances/", "/us/pa/windows/", "/us/pa/ev-charger/")
for c in ["denver", "aurora", "boulder", "colorado-springs", "fort-collins"]:
    add(f"/us/co/{c}/", "Colorado-wide pages:", "/us/co/water-heater/")
add("/us/co/", "Colorado-wide pages:", "/us/co/water-heater/")
add("/us/co/boulder/", "Colorado-wide pages:", "/us/co/boulder/insulation/")
add("/us/ca/", "California guides:", "/blog/insulation-buying-guide-ca/")
add("/us/ca/san-diego/", "San Diego guides:", "/blog/heat-pump-or-solar-san-diego/")
add("/us/ca/los-angeles/burbank/", "More for Burbank homes:", "/us/ca/los-angeles/burbank/appliances/")
add("/us/ma/", "Massachusetts guides:", "/blog/heat-pump-or-solar-massachusetts/")
add("/us/ma/lawrence/", "More for Lawrence homes:", "/us/ma/lawrence/insulation/")
add("/us/ny/pseg/brookhaven/", "More for Brookhaven homes:", "/us/ny/pseg/brookhaven/water-heater/")
add("/us/ny/central-hudson/beacon/", "Local installers:", "/installers/ny/beacon/heat-pump/")
add("/us/ny/central-hudson/newburgh/", "Local installers:", "/installers/ny/newburgh/heat-pump/")
add("/us/ny/con-edison/mount-vernon/", "Local installers:", "/installers/ny/mount-vernon/heat-pump/")
add("/programs/", "Compare utilities:", "/programs/utility-comparison/")
add("/rebate-tracker/", "Past months:", "/rebate-tracker/2026-09/")
add("/blog/", "Before you hire:", "/blog/not-all-installers-trustworthy/", "/blog/solar-snow-coverage/")
add("/calculator/", "For installers:", "/calculator/widget/")


def file_of(path):
    return ROOT / path.strip("/") / "index.html"


def title(path):
    s = file_of(path).read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S) or re.search(r"<title>(.*?)</title>", s, re.S)
    t = re.sub(r"<[^>]+>", "", m.group(1)) if m else path
    return html.escape(html.unescape(" ".join(t.split())), quote=False)


def main():
    changed = 0
    for parent, (label, targets) in JOBS.items():
        pf = file_of(parent)
        if not pf.exists():
            print("skip, no parent:", parent)
            continue
        s = pf.read_text(encoding="utf-8")
        seen, links = set(), []
        for t in targets:
            if t in seen or not file_of(t).exists():
                continue
            seen.add(t)
            links.append(f'<a href="{t}">{title(t)}</a>')
        if not links:
            continue
        block = f"<!-- {MARK}-START -->{BOX.format(label, ' · '.join(links))}<!-- {MARK}-END -->"
        a, b = f"<!-- {MARK}-START -->", f"<!-- {MARK}-END -->"
        if a in s:
            new = s[:s.index(a)] + block + s[s.index(b) + len(b):]
        else:
            i = content_insert_point(s)
            new = s[:i] + block + s[i:]
        if new != s:
            pf.write_text(new, encoding="utf-8")
            changed += 1
    print(f"{changed} pages updated")


if __name__ == "__main__":
    main()
