#!/usr/bin/env python3
"""The post-steps to run after any page generator, in one place (2026-10-16).

check_generator_sync.py runs this same list, so what you run by hand and what the sync check expects cannot drift apart.
Order matters:
- the restamp first, so a freshly generated page has its footer markers before anything is placed relative to them
  (build_internal_boosts used to run first and skipped fresh pages, so its boxes vanished after every rebuild);
- marker-based injectors next (internal link boxes, deadline notes, the federal callout then its email alert box, breadcrumb JSON-LD: the visible-trail version
  before the URL-path version, because each skips pages that already have a BreadcrumbList);
- SEO and link fixes, then the restamp twice (the second pass matches a fresh <style> block to its template file).
Every step is idempotent: running the whole list twice changes nothing the second time.

  python3 scripts/post_steps.py            # run all steps
  python3 scripts/post_steps.py --list     # print the order
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STEPS = ["apply_canonical_nav_footer", "build_internal_boosts", "build_installer_rankings --links-only", "add_deadline_notes", "add_federal_links", "add_federal_alert", "add_heat_pump_links", "add_breadcrumb_jsonld", "add_breadcrumb_ld",
         "fix_seo_meta", "add_aeo_markup", "link_orphans", "link_discovered", "fix_redirected_links", "follow_official_sources",
         "apply_canonical_nav_footer", "apply_canonical_nav_footer"]


def run(cwd: Path = ROOT, quiet: bool = True) -> list:
    """Run every step in cwd; returns the names of steps that failed."""
    failed = []
    for step in STEPS:
        name, *args = step.split()
        r = subprocess.run([sys.executable, f"scripts/{name}.py", *args], cwd=cwd, capture_output=quiet, text=True)
        if r.returncode:
            failed.append(step)
            if quiet:
                print(f"{step} FAILED:", (r.stderr or "").strip()[-600:])
    return failed


if __name__ == "__main__":
    if "--list" in sys.argv:
        print("\n".join(STEPS))
        sys.exit(0)
    bad = run(quiet="--verbose" not in sys.argv)
    print("post-steps done" + (f"; failed: {', '.join(bad)}" if bad else ""))
    sys.exit(1 if bad else 0)
