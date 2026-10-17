#!/usr/bin/env python3
"""Do the shared-shell generators still reproduce the live pages?

Every generator that builds pages with build_furnace_pages.shell() or the build_ca_pages city shell (in each mode) is re-run in a scratch git worktree (HEAD plus
this checkout's uncommitted and git-ignored data files), followed by the nav/footer restamp. Any page that would
change is listed, and a page whose CSS no longer matches its registered template variant is flagged STYLE (its
design would change). Exit status 1 if anything would change. Nothing in this checkout is touched.

Usage: python3 scripts/check_generator_sync.py [generator ...]   (default: every shell generator)
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as nf  # noqa: E402
# needs arguments or is not a page builder
SKIP = {"build_monthly_rebate_report", "page_kit", "city_pages", "capture_build"}
from post_steps import run as run_post_steps  # noqa: E402  (one list, shared with scripts/post_steps.py)
from build_hubs import HUB as HUB_STEPS  # noqa: E402
# (the restamp converts a fresh generator <style> block to its template file on its second pass, after adding font fallbacks)
TPL_RE = re.compile(r'/assets/tpl/([\w-]+)\.css')
EXTRA = ["build_ca_sacramento", "build_ca_sf", "build_ca_sj", "build_ca_la"]


def git(*a, cwd=ROOT, check=True):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=check).stdout


def generators():
    """Every page generator to re-run, as command strings: the furnace-shell generators, plus every builder on the
    shared city-page shell (build_ca_pages) once per mode it supports (cities, --hubs, --state/--state-hub)."""
    gens = {"build_furnace_pages"}
    for p in (ROOT / "scripts").glob("build_*.py"):
        if re.search(r"^from build_furnace_pages import .*\bshell\b", p.read_text(encoding="utf-8"), re.M):
            gens.add(p.stem)
    runs = sorted((gens | set(EXTRA)) - SKIP)
    for p in sorted((ROOT / "scripts").glob("*.py")):
        t = p.read_text(encoding="utf-8")
        wrapper = bool(re.search(r"^\s*city_pages\.main\(", t, re.M))  # a region wrapper on the shared engine (always has --hubs)
        if p.stem in SKIP or p.stem in gens or not (wrapper or ((p.stem == "build_ca_pages" or re.search(r"^import build_ca_pages\b", t, re.M)) and "<!DOCTYPE" in t)):
            continue
        runs.append(p.stem)
        runs += [f"{p.stem} {flag}" for flag in ("--hubs", "--state", "--state-hub") if f'"{flag}"' in t or (wrapper and flag == "--hubs")]
    return runs


def main():
    gens = sys.argv[1:] or generators()
    tmp = Path(tempfile.mkdtemp(prefix="hpr-gensync-"))
    wt = tmp / "wt"
    git("worktree", "add", "-q", "--detach", str(wt), "HEAD")
    try:
        # overlay this checkout: uncommitted tracked changes, untracked files, and ignored generator inputs
        changed = [l[3:] for l in git("status", "--porcelain", "--untracked-files=all").splitlines()]
        ignored = [f for f in git("ls-files", "-o", "-i", "--exclude-standard").splitlines()
                   if f.startswith(("data/", "installers/")) and ".wrangler" not in f and "credentials" not in f]
        for f in changed + ignored:
            f = f.split(" -> ")[-1].strip('"')
            src, dst = ROOT / f, wt / f
            if src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            elif not src.exists() and dst.exists():
                dst.unlink()
        git("add", "-A", cwd=wt)
        git("-c", "user.name=sync", "-c", "user.email=sync@localhost", "commit", "-q", "--no-verify", "--allow-empty",
            "-m", "baseline", cwd=wt)
        owner = {}
        for g in gens:
            name, *args = g.split()
            r = subprocess.run([sys.executable, f"scripts/{name}.py", *args], cwd=wt, capture_output=True, text=True)
            if r.returncode:
                print(f"{g}: FAILED\n{r.stderr.strip()[-400:]}")
            for line in git("status", "--porcelain", cwd=wt).splitlines():
                owner.setdefault(line[3:], g)
        # the same post-steps the pipeline runs after any generator (scripts/post_steps.py)
        if any(" --state" in g for g in gens):  # a region hub base page needs the hub blocks before the post-steps
            for step in HUB_STEPS:
                subprocess.run([sys.executable, f"scripts/{step}"], cwd=wt, capture_output=True, text=True)
        run_post_steps(cwd=wt)
        diffs = [l[3:] for l in git("status", "--porcelain", cwd=wt).splitlines()]
        bad = 0
        for f in sorted(diffs):
            if not f.endswith(".html"):
                continue
            s = (wt / f).read_text(encoding="utf-8", errors="replace")
            was = git("show", f"HEAD:{f}", cwd=wt, check=False)
            # STYLE: the page would lose its live template variant (inline CSS left, or linked to another variant)
            style = bool(re.search(r"<style[^>]*>\s*:root\{--ink", s)) or TPL_RE.findall(s) != TPL_RE.findall(was)
            d = git("diff", "-U0", "--", f, cwd=wt)
            n = sum(1 for l in d.splitlines() if l[:1] in "+-" and l[:3] not in ("+++", "---"))
            lost = sorted(nf.visible_words(was) - nf.visible_words(s))
            tag = "STYLE" if style else "LOST " if lost else "text "
            print(f"{tag} {n:5d} lines  {f}  ({owner.get(f, 'restamp')})" + (f"  lost: {' '.join(lost[:12])}" if lost else ""))
            bad += 1
        if os.environ.get("DIFF"):
            Path(os.environ["DIFF"]).write_text(git("diff", "-U0", cwd=wt), encoding="utf-8")
        print(f"\n{len(gens)} generators re-run; {bad} pages would change.")
        return 1 if bad else 0
    finally:
        if os.environ.get("KEEP"):
            print(f"kept {wt}")
        else:
            git("worktree", "remove", "--force", str(wt), check=False)
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
