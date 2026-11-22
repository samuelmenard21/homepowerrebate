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

# Added 2026-11-21 after an internal-link audit (seo/internal-links-report.md): pages with fewer than 3 body links.
add("/ca/bc/", "More BC guides:", "/blog/heat-pump-winter-bc/", "/blog/heat-pumps-cold-climate-bc-winter/",
    "/blog/mitsubishi-vs-daikin-heat-pump-bc-cost/", "/blog/bc-hydro-schedule-2289-battery-payback/",
    "/blog/peak-saver-14-day-window-3500-mistake/", "/blog/smart-thermostat-peak-saver-optimization/",
    "/blog/cleanbc-income-qualified-free-heat-pump-2026/", "/questions/ev-charger-rebate-bc-2026/",
    "/ca/bc/fraser-valley/")
add("/ca/bc/vancouver/", "More for your home:", "/questions/vancouver-solar/", "/questions/vancouver-heat_pump/")
add("/ca/bc/victoria/", "More for your home:", "/questions/victoria-heat_pump/")
add("/ca/on/", "Renting in Ontario:", "/questions/renter-eligible-heat-pump-rebate/")
add("/ca/ab/red-deer/", "More for Red Deer homes:", "/ca/ab/red-deer/smart-thermostats/")
add("/ca/nb/", "En français:", "/ca/nb/fr/")
add("/ca/nb/moncton/", "En français:", "/ca/nb/moncton/fr/")
add("/ca/qc/", "En français:", "/ca/qc/fr/", "/ca/qc/heat-pump/fr/")
add("/ca/qc/montreal/", "En français:", "/ca/qc/montreal/fr/")
add("/ca/qc/quebec-city/", "En français:", "/ca/qc/quebec-city/fr/")
add("/ca/qc/heat-pump/", "En français:", "/ca/qc/heat-pump/fr/")
add("/us/ny/", "New York guides:", "/blog/new-york-dac-mapping-eligibility-guide/",
    "/blog/new-york-cities-ranked-fastest-heat-pump-payback/", "/blog/heat-pump-or-solar-new-york/",
    "/blog/6-new-york-heat-pump-programs-stack-together/", "/blog/upstate-ny-rebate-guide-buffalo-rochester-syracuse/",
    "/blog/energy-saving-ideas-ny-home/", "/programs/orange-and-rockland-rebates/")
add("/us/ca/", "More California guides:", "/blog/smud-fringe-alternatives/", "/blog/inland-empire-often-overlooked/",
    "/blog/heat-pump-or-solar-inland-empire/", "/blog/solar-battery-stack-vs-heat-pump-only/")
add("/us/ca/inland-empire/", "More for the Inland Empire:", "/blog/inland-empire-often-overlooked/",
    "/blog/heat-pump-or-solar-inland-empire/")
add("/us/ca/sacramento/", "More for Sacramento homes:", "/blog/smud-fringe-alternatives/")
add("/us/vt/", "Vermont guides:", "/blog/vermont-virtual-power-plant-battery-rebates/",
    "/blog/vermont-heat-pump-rebates-efficiency-vermont-2026/")
add("/us/ma/", "Massachusetts guides:", "/blog/heat-pump-or-solar-massachusetts/")
add("/rebate-tracker/", "Monthly data:", "/data-release/", "/data-release/2026-10/")
add("/programs/", "How we check:", "/how-we-check-rebate-facts/", "/blog/powerscore-standings-aug-2026/")
add("/blog/", "Also worth reading:", "/blog/solar-installer-red-flags-how-to-choose/",
    "/guides/heat-pump-buyers-guide/", "/hrv-heat-recovery-ventilation/")
add("/technology/", "More technology:", "/technology/quilt-heat-pump-canada/")
add("/programs/national-heat-pump-rebate/", "For partners:", "/partners/federal-heat-pump-rebate/")
add("/calculator/widget/", "For partners:", "/partners/federal-heat-pump-rebate/")
add("/questions/heat-pump-rebate-income-limits/", "Related:", "/questions/renter-eligible-heat-pump-rebate/")
add("/questions/kelowna-heat_pump/", "Related:", "/questions/kelowna-solar/")
add("/questions/kelowna-solar/", "Related:", "/questions/kelowna-heat_pump/")
add("/questions/kamloops-solar/", "Related:", "/questions/vancouver-solar/")


# Added 2026-11-22 (roast: /installers/heat-pump/ had 63 inbound links against 1,100 for the rebate finder).
# Every indexable city heat pump page links the hub with its own anchor, so no exact anchor repeats.
HUB = "/installers/heat-pump/"


def _heat_pump_city_pages():
    for f in sorted(ROOT.glob("*/**/heat-pump/index.html")):
        parts = f.relative_to(ROOT).parts[:-1]
        if parts[0] not in ("ca", "us") or len(parts) < 4:
            continue
        if re.search(r'name="robots"[^>]*noindex', f.read_text(encoding="utf-8", errors="ignore")[:8000]):
            continue
        yield "/" + "/".join(parts) + "/", parts[-2].replace("-", " ").title()


for _p, _city in _heat_pump_city_pages():
    add(_p, "Find an installer:", (HUB, f"Find a heat pump installer near {_city}"))


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
            t, anchor = t if isinstance(t, tuple) else (t, None)
            if t in seen or not file_of(t).exists():
                continue
            seen.add(t)
            links.append(f'<a href="{t}">{html.escape(anchor) if anchor else title(t)}</a>')
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
