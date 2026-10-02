#!/usr/bin/env python3
"""Let links to official program sources pass credit: remove rel="nofollow" from external links to government, utility and program-administrator pages.
Google's guidance is to use nofollow for paid, user-generated or untrusted links; editorial citations of primary sources should be normal links (keep noopener).
Competitors, aggregators, installers and manufacturers stay nofollow. Generators still write nofollow, so run this after them (see CLAUDE.md)."""
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
OFFICIAL_SUFFIX = (".gov", ".gov.bc.ca", ".gc.ca", ".ca.gov", ".ny.gov", ".mass.gov", ".state.pa.us", ".state.vt.us", ".state.co.us")
OFFICIAL_HOSTS = {
    "bchydro.com", "fortisbc.com", "betterhomesbc.ca", "homerenovationsavings.ca", "saveonenergy.ca", "novascotia.ca", "efficiencyns.ca", "efficiencynovascotia.ca", "nsuarb.ca",
    "natural-resources.canada.ca", "calgary.ca", "ceip.abmunis.ca", "energy.ca.gov", "cpuc.ca.gov", "techcleanca.com", "switchison.org", "smud.org", "ladwp.com", "sce.com", "pge.com",
    "sdge.com", "peco.com", "ppl.clearesult.com", "pplelectric.com", "xcelenergy.com", "masssave.com", "masscec.com", "goclean.masscec.com", "ma-eeac.org", "nyserda.ny.gov",
    "cleanheat.ny.gov", "efficiencyvermont.com", "energystar.gov", "irs.gov", "emp.lbl.gov", "climateinstitute.ca", "homeperformance.ca", "cityofpasadena.net", "glendaleca.gov",
    "burbankwaterandpower.com", "burbankca.gov", "sanjosecleanenergy.org", "cleanpowersf.org", "sfpuc.gov", "bayren.org", "avaenergy.org", "lbutilities.org", "longbeach.gov",
    "santamonica.gov", "folsom.ca.us", "cityofranchocordova.org", "ladbs.org", "cleanpoweralliance.org", "socalgas.com", "sdcommunitypower.org", "xcelnew.my.salesforce.com", "assets.ctfassets.net", "coned.com", "psegliny.com", "nationalgridus.com", "cenhud.com", "nyseg.com", "nationalgrid.com", "eversource.com", "unitil.com", "efficiencyvt.com", "ci.pittsburgh.pa.us", "phila.gov", "denvergov.org", "coloradoenergy.org",
}


def official(host):
    host = host.lower().removeprefix("www.")
    return any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS) or host.endswith(OFFICIAL_SUFFIX)


def fix_tag(m):
    tag = m.group(0)
    hm = re.search(r"href=[\"']https?://([^/\"']+)", tag)
    if not hm or "homepowerrebate.com" in hm.group(1) or "nofollow" not in tag or not official(hm.group(1)):
        return tag
    new = re.sub(r"rel=([\"'])([^\"']*)\1", lambda r: "rel=" + r.group(1) + " ".join(x for x in r.group(2).split() if x != "nofollow") + r.group(1), tag)
    return new.replace(' rel=""', "").replace(" rel=''", "")


changed = links = 0
for f in subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True).stdout.split():
    if f.startswith(("_partials/", "scripts/")) or not (ROOT / f).exists():
        continue
    p = ROOT / f
    s = p.read_text(encoding="utf-8", errors="ignore")
    n = re.sub(r"<a [^>]*>", fix_tag, s)
    if n != s:
        links += sum(1 for a, b in zip(re.findall(r"<a [^>]*>", s), re.findall(r"<a [^>]*>", n)) if a != b)
        p.write_text(n, encoding="utf-8")
        changed += 1
print("pages changed", changed, "links now followed", links)
