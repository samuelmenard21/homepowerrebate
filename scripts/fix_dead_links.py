#!/usr/bin/env python3
"""Fix external links that return 404/410 (list from `check_links.py --external`, rechecked with a browser UA).

  python3 scripts/fix_dead_links.py dead.json [--dry-run]
dead.json: [[url, status, pages, example_page], ...]
Rules, in order:
  1. URL in REPLACE            -> point at the working page.
  2. anchor text is "Website" (installer's own site is gone) -> drop the link and its separator.
  3. anything else             -> unwrap: keep the sentence, drop the dead link.
Pages are generated from data that no longer lives in this repo, so this edits the HTML directly and logs
every change to reports/dead-links-fixed.csv. Re-running check_links.py --external afterwards should be clean.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"dist", "scripts", ".claude", "node_modules", "reports", "data", "_partials"}
REPLACE = {
    "https://www.chargepoint.com/products/home/flex/": "https://www.chargepoint.com/drivers/home/",
    "https://www.torontohydro.com/for-home/peaksaver": "https://www.saveonenergy.ca/en/For-Your-Home/Peaksaver-PLUS",
    "https://www.energyaid.net/norcal": "https://www.energyaid.net/",
    "https://www.energyaid.net/bay-area": "https://www.energyaid.net/",
    "https://www.energyaid.net/central-valley": "https://www.energyaid.net/",
    "https://gridalternatives.org/regions/san-diego": "https://www.gridalternatives.org/regions",
    "https://gridalternatives.org/regions/greater-sacramento": "https://www.gridalternatives.org/regions",
    "https://cleanbc.gov.bc.ca/programs/": "https://www.cleanbc.gov.bc.ca/",
    "https://www.aeso.ca/grid/current-supply-demand/": "https://www.aeso.ca/grid/",
    "https://www.epcor.com/products-services/power/outages": "https://www.epcor.com/",
    "https://energy.atco.com/en-ca": "https://energy.atco.com/",
    "https://www.burbankwaterandpower.com/save-money-energy/rebates-incentives": "https://www.burbankwaterandpower.com/",
}


def apply_fixes(t, replace, remove, log=None, rel=""):
    """Apply link fixes to one page's HTML; returns new text. Shared with build_public.py."""
    for u, new_u in replace.items():
        if f'href="{u}"' in t:
            t = t.replace(f'href="{u}"', f'href="{new_u}"')
            if log is not None:
                log.append([rel, u, "replaced"])
    for u in remove:
        if u not in t:
            continue
        pat = re.compile(r'(\s*(?:&middot;|·)\s*)?<a\b[^>]*href="' + re.escape(u) + r'"[^>]*>(.*?)</a>', re.S)

        def sub(m):
            raw = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if raw.lower() in ("website", "visit website", "visit site") or raw.endswith("&rarr;") or raw.endswith("→"):
                return ""
            return (m.group(1) or "") + m.group(2)
        t = pat.sub(sub, t)
    return t


def main():
    dry = "--dry-run" in sys.argv
    dead = {u: pages for u, code, pages, _ in json.load(open(sys.argv[1])) if code in (404, 410)}
    dead = {u: n for u, n in dead.items() if "fonts.g" not in u}
    files = [p for p in ROOT.rglob("*.html") if not (set(p.relative_to(ROOT).parts) & SKIP)]
    log = [["page", "url", "action"]]
    for f in files:
        t = f.read_text(encoding="utf-8", errors="ignore")
        if not any(u in t for u in dead):
            continue
        new = t
        for u in dead:
            if u not in new:
                continue
            rel = str(f.relative_to(ROOT))
            if u in REPLACE:
                new = new.replace(f'href="{u}"', f'href="{REPLACE[u]}"')
                log.append([rel, u, "replaced"])
                continue
            pat = re.compile(r'(\s*(?:&middot;|·)\s*)?<a\b[^>]*href="' + re.escape(u) + r'"[^>]*>(.*?)</a>', re.S)

            def sub(m):
                raw = re.sub(r"<[^>]+>", "", m.group(2)).strip()
                txt = raw.lower()
                if txt in ("website", "visit website", "visit site") or raw.endswith("&rarr;") or raw.endswith("→"):
                    log.append([rel, u, "removed dead website/arrow link"])
                    return ""
                log.append([rel, u, "unwrapped"])
                return m.group(2) if not m.group(1) else m.group(1) + m.group(2)
            new = pat.sub(sub, new)
        if new != t and not dry:
            f.write_text(new, encoding="utf-8")
    out = ROOT / "reports" / "dead-links-fixed.csv"
    if not dry:
        out.parent.mkdir(exist_ok=True)
        csv.writer(out.open("w", newline="", encoding="utf-8")).writerows(log)
    from collections import Counter
    print(Counter(l[2] for l in log[1:]), "(dry run)" if dry else "")


if __name__ == "__main__":
    main()
