#!/usr/bin/env python3
"""Take installers off the site for good, in one command.

  python3 scripts/remove_installer.py owner@a.ca other@b.com --reason "asked to be removed" --ship

For each email it blocks the company (data/installer-blocklist.json, which the
rankings builder and the Google Places scraper skip), drops its rows, deletes
its profiles with 301s, strips it from other profiles, rebuilds once, keeps
only the files about these installers, and checks nothing blocked is listed.
--ship then commits on a new branch, opens and merges the PR, and waits until
the live site shows the removal. Run it from a fresh worktree of origin/main.
"""
import argparse
import csv
import io
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import installer_blocklist as bl  # noqa: E402

# outreach never emails these; outreach/ is gitignored, so use the main checkout's copy when run from a worktree
SUPPRESS = Path(subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                               capture_output=True, text=True).stdout.strip() or ROOT / ".git").parent / "outreach" / "suppress.txt"
BASE = "https://homepowerrebate.com"


def slugs(name):
    a = re.sub(r"[^a-z0-9]+", "-", name.lower().replace("&", "and").replace("'", "").replace("’", "")).strip("-")
    b = re.sub(r"[^a-z0-9]+", "-", re.sub(r"[&'’]", "", name.lower().strip())).strip("-")
    return {x for x in (a, b) if x}


def city_slug(city):
    return re.sub(r"[^a-z0-9]+", "-", city.lower()).strip("-")


def find_rows(email, name, city):
    """Every CSV row for this company: [(file, row)]."""
    out = []
    for f in sorted((ROOT / "installers").glob("*-installers-real.csv")):
        for r in csv.DictReader(f.open(encoding="utf-8")):
            if email and r.get("Email", "").strip().lower() == email:
                out.append((f, r))
            elif name and bl._norm(r.get("Business Name")) == bl._norm(name) and (not city or bl._norm(r.get("City")) == bl._norm(city)):
                out.append((f, r))
    return out


def strip_csvs():
    n = 0
    for f in sorted((ROOT / "installers").glob("*-installers-real.csv")):
        with f.open(encoding="utf-8", newline="") as fh:  # keep CRLF line endings as they are
            lines = fh.read().splitlines(keepends=True)
        keep = [lines[0]]
        for line in lines[1:]:
            r = next(csv.DictReader(io.StringIO(lines[0] + line)), None)
            if r and bl.is_blocked(r.get("Business Name"), r.get("City"), r.get("Email"), r.get("Website"), r.get("Google Maps URL")):
                n += 1
                continue
            keep.append(line)
        if len(keep) != len(lines):
            with f.open("w", encoding="utf-8", newline="") as fh:
                fh.write("".join(keep))
    return n


def strip_json():
    n = 0
    for f in sorted((ROOT / "installers" / "json").rglob("*.json")):
        raw = f.read_text(encoding="utf-8")
        try:
            items = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(items, list):
            continue
        city = f.stem.replace("-", " ")
        keep = [it for it in items if not (isinstance(it, dict) and bl.is_blocked(it.get("name"), city, it.get("email"), it.get("website"), it.get("gmaps_url")))]
        if len(keep) != len(items):
            n += len(items) - len(keep)
            f.write_text(json.dumps(keep, ensure_ascii=False, indent=2) + ("\n" if raw.endswith("\n") else ""), encoding="utf-8")
    return n


def remove_profiles(name, cities, redirect_to):
    """Delete profile folders for this company; return their URLs."""
    gone = []
    for c in cities:
        cs = city_slug(c)
        for s in slugs(name):
            for d in ROOT.glob(f"installers/profiles/**/{cs}/{s}"):
                if (d / "index.html").exists():
                    gone.append("/" + str(d.relative_to(ROOT)) + "/")
                    shutil.rmtree(d)
                    # stage it: post-steps list pages with `git ls-files`, which still names unstaged deletions
                    subprocess.run(["git", "-C", str(ROOT), "rm", "-rq", "--cached", "--ignore-unmatch", str(d.relative_to(ROOT))], check=False)
    # Redirects: profile -> ranking page (or city hub)
    if gone:
        red = ROOT / "_redirects"
        text = red.read_text(encoding="utf-8")
        marker = "# Dynamic rules"
        add = "".join(f"{u} {redirect_to} 301\n{u.rstrip('/')} {redirect_to} 301\n" for u in gone if u not in text)
        i = text.find(marker)
        text = text[:i] + add + "\n" + text[i:] if i >= 0 else text + add
        red.write_text(text, encoding="utf-8")
    # Sibling lists, the installer directory and data files that name the profile
    for u in gone:
        a = re.escape(u)
        pats = [re.compile(rf'<li>\s*<a href="{a}"[^>]*>.*?</a>\s*</li>\s*', re.S),
                re.compile(rf'<a href="{a}"[^>]*class="ip-nearby-item"[^>]*>.*?</a>', re.S),
                re.compile(rf'<a href="{a}"[^>]*>.*?</a>', re.S)]
        for f in list((ROOT / "installers").rglob("*.html")):
            s = f.read_text(encoding="utf-8")
            if u not in s:
                continue
            for p in pats:
                s = p.sub("", s)
            f.write_text(s, encoding="utf-8")
        rel = u.strip("/")
        for f, key in ((ROOT / "data" / "installer-place-ids.json", f"{rel}/index.html"), (ROOT / "og" / "manifest.json", f"og/{rel}.jpg")):
            if f.exists():
                d = json.loads(f.read_text(encoding="utf-8"))
                if d.pop(key, None) is not None:
                    raw = f.read_text(encoding="utf-8")
                    ind = 0 if raw.startswith("{\n\"") else (1 if raw.startswith("{\n \"") else None)
                    f.write_text(json.dumps(d, ensure_ascii=False, indent=ind, separators=None if ind is not None else (", ", ": ")) + ("\n" if raw.endswith("\n") else ""), encoding="utf-8")
        og = ROOT / "og" / f"{rel}.jpg"
        if og.exists():
            og.unlink()
            subprocess.run(["git", "-C", str(ROOT), "rm", "-q", "--cached", "--ignore-unmatch", str(og.relative_to(ROOT))], check=False)
    return gone


def ranking_url(rows):
    try:
        index = json.loads((ROOT / "installers" / "rankings.json").read_text())
    except (OSError, ValueError):
        index = None
    f, r = rows[0]
    m = re.match(r"(?:([a-z]{2})-)?(.+)-installers-real\.csv$", f.name)
    region, service = (m.group(1) or "bc"), m.group(2)
    url = f"/installers/{region}/{city_slug(r['City'])}/{service}/"
    if (ROOT / url.strip("/") / "index.html").exists():
        return url
    return f"/installers/{region}/{city_slug(r['City'])}/" if index else url


def build(regions):
    def run(*cmd):
        print("$", " ".join(cmd))
        subprocess.run([sys.executable, *cmd], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    run("scripts/build_installer_rankings.py")
    for code in sorted(regions):
        b = ROOT / "scripts" / f"build_{code}_pages.py"
        if b.exists():
            run(str(b.relative_to(ROOT)))
            run(str(b.relative_to(ROOT)), "--hubs")
    run("scripts/build_get_quotes.py")
    run("scripts/compact_redirects.py")
    run("scripts/post_steps.py")


def git(*args, **kw):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, **kw).stdout


DATA = {"_redirects", "data/installer-blocklist.json", "data/installer-cleanup-log.csv", "data/installer-place-ids.json",
        "data/outreach-rankings.csv", "data/page-dates.json", "installers/rankings.json", "installers/allowed-installer-emails.json",
        "installers/badge/index.html", "og/manifest.json"}


def keep_only_related(needles):
    """Revert any rebuilt file that never mentioned these installers (drift from other work)."""
    related = set(DATA)
    for n in needles:
        related |= {l.split(":", 1)[1] if l.startswith("HEAD:") else l for l in git("grep", "-l", "-i", "-F", n, "HEAD", "--", ".").split()}
    stray = [f for f in git("diff", "--name-only").split() if f not in related and not f.startswith("scripts/")]
    if stray:
        git("checkout", "HEAD", "--", *stray)
    return stray


def ship(names, gone):
    branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    if branch in ("main", "HEAD"):
        sys.exit("--ship needs a branch (run from a fresh worktree on a new branch).")
    title = "Remove and block " + ", ".join(names)
    git("add", "-A"); git("add", "-f", "data/installer-blocklist.json")
    git("commit", "-q", "-m", f"{title}\n\nscripts/remove_installer.py\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
    git("push", "-q", "-u", "origin", branch)
    body = f"{title}: blocked, rows dropped, profiles 301'd ({', '.join(gone)}), rankings rebuilt.\n\n\U0001F916 Generated with [Claude Code](https://claude.com/claude-code)"
    pr = subprocess.run(["gh", "pr", "create", "--title", title, "--body", body], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    subprocess.run(["gh", "pr", "merge", "--merge"], cwd=ROOT, check=True)
    print("merged", pr)
    for _ in range(10):
        codes = [subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", BASE + u], capture_output=True, text=True).stdout for u in gone]
        if codes and all(c == "301" for c in codes):
            print("live: profiles now 301")
            return pr, True
        time.sleep(120)
    print("not live after 20 minutes")
    return pr, False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("emails", nargs="+")
    ap.add_argument("--reason", required=True)
    ap.add_argument("--ship", action="store_true", help="commit, open and merge the PR, wait for the live site")
    a = ap.parse_args()

    names, gone, regions, needles = [], [], set(), []
    entries = json.loads(bl.FILE.read_text()) if bl.FILE.exists() else []
    for email in (e.strip().lower() for e in a.emails):
        rows = find_rows(email, None, None)
        if not rows:
            print(f"{email}: no installer row matches; skipped")
            continue
        name = rows[0][1]["Business Name"].strip()
        cities = sorted({r["City"].strip() for _, r in rows})
        redirect_to = ranking_url(rows)
        for c in cities:
            r = next(r for _, r in rows if r["City"].strip() == c)
            entries.append({"name": name, "city": c, "email": email, "website": r.get("Website", "").strip(),
                            "cid": bl._cid(r.get("Google Maps URL")), "reason": a.reason, "date": date.today().isoformat()})
        bl.FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        bl._KEYS = None
        with open(ROOT / "data" / "installer-cleanup-log.csv", "a", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            for fp in sorted({fp.name for fp, _ in rows}):
                for c in cities:
                    w.writerow([fp, name, c, "removed and blocked", f"{a.reason} ({date.today().isoformat()})"])
        if SUPPRESS.parent.exists():
            have = SUPPRESS.read_text().lower().split() if SUPPRESS.exists() else []
            if email not in have:
                with SUPPRESS.open("a") as f:
                    f.write(email + "\n")
        n_csv, n_json = strip_csvs(), strip_json()
        g = remove_profiles(name, cities, redirect_to)
        print(f"{name}: {n_csv} CSV rows, {n_json} JSON entries, {len(g)} profiles removed -> {redirect_to}")
        names.append(name); gone += g; needles += [name, email] + g + [u.rstrip("/").rsplit("/", 1)[-1] for u in g]
        regions |= {(re.match(r"([a-z]{2})-", fp.name) or [None, "bc"])[1] for fp, _ in rows}
    if not names:
        sys.exit("Nothing removed.")
    build(regions)
    stray = keep_only_related(needles)
    if stray:
        print(f"reverted {len(stray)} unrelated rebuilt files")
    if subprocess.run([sys.executable, "scripts/installer_blocklist.py"], cwd=ROOT).returncode:
        sys.exit("A blocked installer is still listed; see above.")
    print(git("diff", "--stat", "HEAD").strip().splitlines()[-1])
    if a.ship:
        ship(names, gone)


if __name__ == "__main__":
    main()
