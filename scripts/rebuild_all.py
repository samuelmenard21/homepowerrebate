#!/usr/bin/env python3
"""Rebuild every generated page in place: every generator in each mode (the same list check_generator_sync.py uses),
the hub steps when a region hub base page was rebuilt, then the post-steps. After a clean run, check_generator_sync.py
reports nothing to change.

  python3 scripts/rebuild_all.py            # everything
  python3 scripts/rebuild_all.py build_bc_pages "build_bc_pages --hubs"   # only these runs (then hub and post-steps)
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_hubs import HUB as HUB_STEPS  # noqa: E402
from check_generator_sync import generators  # noqa: E402
from post_steps import run as run_post_steps  # noqa: E402


def main():
    runs = sys.argv[1:] or generators()
    failed = []
    for g in runs:
        name, *args = g.split()
        r = subprocess.run([sys.executable, f"scripts/{name}.py", *args], cwd=ROOT, capture_output=True, text=True)
        print(("FAILED " if r.returncode else "ok     ") + g, flush=True)
        if r.returncode:
            failed.append(g)
            print("   ", (r.stderr or r.stdout).strip()[-400:])
    if any(" --state" in g for g in runs):
        for step in HUB_STEPS:
            subprocess.run([sys.executable, f"scripts/{step}"], cwd=ROOT, capture_output=True, text=True)
    bad = run_post_steps(cwd=ROOT)
    print(f"{len(runs)} runs, {len(failed)} failed; post-steps " + ("ok" if not bad else "failed: " + ", ".join(bad)))
    return 1 if failed or bad else 0


if __name__ == "__main__":
    sys.exit(main())
