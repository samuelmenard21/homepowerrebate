#!/usr/bin/env python3
"""Rebuild the region hubs and run every post-step in the right order.

The hub builders write long " | HomePowerRebate" titles and leave some official
links as nofollow; the restamp copies og:image:alt from the title. Running the
builders alone therefore leaves the hubs wrong. Use this script instead:

    python3 scripts/build_hubs.py            # hub pipeline + post-steps
    python3 scripts/build_hubs.py --powerscore   # also rebuild PowerScore first

It stops at the first failing step.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

POWERSCORE = ["build_powerscore.py", "build_powerscore_page.py"]
HUB = [
    "build_hub_tops.py",
    "build_hub_showcase.py",
    "build_hub_tidy.py",
    "apply_canonical_nav_footer.py",
    "apply_canonical_nav_footer.py",
]
# the post-steps are the shared list in post_steps.py (one list for every generator), then the hub layout check
sys.path.insert(0, str(ROOT / "scripts"))
from post_steps import STEPS as POST_STEPS  # noqa: E402
POST = [s.split()[0] + ".py" + "".join(" " + a for a in s.split()[1:]) for s in POST_STEPS] + ["check_hub_layout.py"]


def main():
    steps = (POWERSCORE if "--powerscore" in sys.argv else []) + HUB + POST
    for i, script in enumerate(steps, 1):
        print(f"[{i}/{len(steps)}] {script}", flush=True)
        name, *args = script.split()
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / name), *args], cwd=ROOT)
        if r.returncode:
            sys.exit(f"FAILED: {script} (exit {r.returncode})")
    print("Hubs rebuilt. Next: check_internal_links.py, generate_sitemap.py.")


if __name__ == "__main__":
    main()
