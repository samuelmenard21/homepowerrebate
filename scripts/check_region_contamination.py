#!/usr/bin/env python3
"""
Guardrail: catch region/utility names bleeding into the wrong province or state.

This project builds content per-region (BC, ON, AB, NS, MA, NY, CA, PA, CO, VT)
and has repeatedly shipped copy-paste bugs where one region's program/utility
name ends up on another region's page (e.g. Ontario's "Home Renovation Savings
Program" wording landed on 131 AB/MA/NS installer profiles on 2026-08-30; an
earlier session found LADWP's rate quoted on 5 non-LADWP LA-area cities).

Run this after any sitewide or multi-file scripted edit, before committing:

    python3 scripts/check_region_contamination.py

It is deliberately noisy-tolerant: known-legitimate cross-references (hub
pages, comparison pages, blog posts, an explicit "for BC" title) are allowed
via ALLOWED_PREFIXES per term. A flagged file is not automatically a bug —
open it and confirm with your own eyes, the way the Aug 30 2026 scan did.
Extend CHECKS as new regions/programs are added to the site.
"""
import subprocess
import sys

BC_INSTALLER_CITIES = [
    "abbotsford", "burnaby", "chilliwack", "coquitlam", "fort-st-john",
    "kamloops", "kelowna", "langley", "maple-ridge", "nanaimo", "penticton",
    "prince-george", "richmond", "squamish", "surrey", "vancouver", "vernon",
    "victoria",
]
BC_INSTALLER_PREFIXES = [f"./installers/profiles/{c}/" for c in BC_INSTALLER_CITIES]

# Pages that legitimately discuss multiple regions and should never be flagged.
GLOBAL_ALLOW = ["./blog/", "./guides/", "./questions/", "./ca/index.html",
                 "./us/index.html", "./index.html", "./calculator/",
                 "./installers/index.html", "./heat-pump-water-heater/index.html",
                 "./hrv-heat-recovery-ventilation/index.html", "./partners/index.html",
                 "./retrofit-assessment/index.html"]

CHECKS = [
    # ca/ab/index.html and us/ca/sacramento/index.html deliberately compare
    # themselves to BC's programs/rates (confirmed by eye, Aug 30 2026) —
    # allowed explicitly rather than broadly, so a real leak elsewhere in
    # those regions still gets caught.
    ("CleanBC", ["./ca/bc/"] + BC_INSTALLER_PREFIXES + ["./ca/ab/index.html"]),
    ("BC Hydro", ["./ca/bc/"] + BC_INSTALLER_PREFIXES + ["./ca/ab/index.html", "./us/ca/sacramento/index.html"]),
    ("FortisBC", ["./ca/bc/"] + BC_INSTALLER_PREFIXES),
    ("Home Renovation Savings Program", ["./ca/on/", "./installers/profiles/on/"]),
    ("Mass Save", ["./us/ma/", "./installers/profiles/ma/"]),
    ("CEIP", ["./ca/ab/", "./installers/profiles/ab/"]),
    ("Efficiency Nova Scotia", ["./ca/ns/", "./installers/profiles/ns/"]),
    ("HomeWarming", ["./ca/ns/", "./installers/profiles/ns/"]),
    ("LADWP", ["./us/ca/"]),
    ("SMUD", ["./us/ca/"]),
    ("SDG&E", ["./us/ca/"]),
    ("PG&E", ["./us/ca/"]),
    ("Con Edison", ["./us/ny/"]),
    ("PSEG", ["./us/ny/"]),
    ("Central Hudson", ["./us/ny/"]),
    # "National Grid" is deliberately NOT checked: it's a real utility serving
    # both MA and NY, and every page's sitewide city-picker nav lists every
    # region's cities (including "Yonkers (National Grid)"), so a plain
    # string match is 100% noise. If this needs checking later, scope the
    # match to exclude the nav's city-dropdown markup first.
]


def files_with(term):
    out = subprocess.run(
        ["grep", "-rl", term, "--include=index.html", "."],
        capture_output=True, text=True,
    ).stdout
    return set(out.strip().split("\n")) if out.strip() else set()


def main():
    any_flagged = False
    for term, allowed in CHECKS:
        allowed_all = allowed + GLOBAL_ALLOW
        files = files_with(term)
        bad = sorted(f for f in files if not any(f.startswith(p) for p in allowed_all))
        if bad:
            any_flagged = True
            print(f"--- {term}: {len(bad)} file(s) outside its expected region ---")
            for b in bad[:20]:
                print("   ", b)
            if len(bad) > 20:
                print(f"    ...and {len(bad) - 20} more")
        else:
            print(f"{term}: clean ({len(files)} files)")
    if any_flagged:
        print("\nFlagged files are not automatically bugs — open each one and confirm by")
        print("eye (comparison pages, hub pages, and blog posts legitimately mention other")
        print("regions). Add a genuinely-legitimate path to GLOBAL_ALLOW or the term's own")
        print("allowlist once confirmed, so future runs stay quiet.")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
