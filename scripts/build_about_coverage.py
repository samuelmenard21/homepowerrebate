#!/usr/bin/env python3
"""Stamp the region and city counts on /about from data/regions.json, so they cannot go stale.

Writes two marker-wrapped blocks in about.html:
- ABOUT-COVERAGE: the "Today we cover N cities in M provinces and states" paragraph with links to each hub.
- ABOUT-LD: the Organization, Person and AboutPage JSON-LD (areaServed comes from the region list).
City counts use build_get_quotes.city_slugs, the same count the homepage hero shows. Idempotent; a post-step.

Usage: python3 scripts/build_about_coverage.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import regions  # noqa: E402
from build_get_quotes import city_slugs  # noqa: E402

SITE = "https://homepowerrebate.com"
PAGE = ROOT / "about.html"
COUNTRY = {"ca": ("Canada", "Canada", "provinces"), "us": ("the US", "United States", "states")}


def counts():
    total = sum(len(city_slugs(r["code"])) for r in regions.REGIONS)
    by = {c: [r for r in regions.REGIONS if r["country"] == c] for c in COUNTRY}
    return total, by


def coverage_html(total, by):
    lines = [f'<p>Today we cover {total} cities in {len(regions.REGIONS)} provinces and states. '
             "We add a new place only when we can read its programs on the official pages.</p>", "<ul>"]
    for c, (label, _, kind) in COUNTRY.items():
        links = ", ".join(f'<a href="{regions.HUB_URL_BY_CODE[r["code"]]}">{r["name"]}</a>' for r in by[c])
        lines.append(f"  <li><strong>{label} ({len(by[c])} {kind}):</strong> {links}</li>")
    lines.append("</ul>")
    return "\n    ".join(lines)


def ld(total, by):
    area = [{"@type": "AdministrativeArea", "name": f'{r["name"]}, {COUNTRY[c][1]}'} for c in COUNTRY for r in by[c]]
    org = {"@type": "Organization", "@id": f"{SITE}/#org", "name": "HomePowerRebate", "url": f"{SITE}/",
           "description": (f"Independent guide to home energy rebates in {total} cities across Canada and the United States. Every amount links to the "
                           "official program and is re-checked monthly. Installers are ranked by Google reviews; nobody pays to be listed."),
           "founder": {"@id": f"{SITE}/about#sam-menard"}, "foundingLocation": "Ontario, Canada", "areaServed": area}
    person = {"@type": "Person", "@id": f"{SITE}/about#sam-menard", "name": "Sam Menard", "jobTitle": "Founder", "worksFor": {"@id": f"{SITE}/#org"},
              "alumniOf": {"@type": "CollegeOrUniversity", "name": "Wilfrid Laurier University"},
              "knowsAbout": ["home-energy rebates", "heat pump rebates", "residential solar and battery rebates", "utility incentive programs"],
              "description": ("Sam Menard is a business and analytics professional who built HomePowerRebate as an independent, plain-English guide "
                              "to home-energy rebate programs across Canada and the US."),
              "sameAs": ["https://ca.linkedin.com/in/sammenard"]}
    page = {"@type": "AboutPage", "url": f"{SITE}/about", "name": "About HomePowerRebate", "about": {"@id": f"{SITE}/#org"}, "mainEntity": {"@id": f"{SITE}/about#sam-menard"}}
    return ('<script type="application/ld+json">\n'
            + json.dumps({"@context": "https://schema.org", "@graph": [org, person, page]}, indent=1, ensure_ascii=False) + "\n</script>")


def stamp(html, name, body):
    pat = re.compile(rf"<!-- {name}-START -->.*?<!-- {name}-END -->", re.S)
    if not pat.search(html):
        sys.exit(f"about.html has no {name} markers")
    return pat.sub(lambda _: f"<!-- {name}-START -->\n{body}\n<!-- {name}-END -->", html)


def main():
    total, by = counts()
    html = PAGE.read_text()
    new = stamp(html, "ABOUT-COVERAGE", "    " + coverage_html(total, by) + "\n   ")
    new = stamp(new, "ABOUT-LD", ld(total, by))
    if new != html:
        PAGE.write_text(new)
    print(f"about: {total} cities, {len(regions.REGIONS)} regions" + ("" if new != html else " (no change)"))


if __name__ == "__main__":
    main()
