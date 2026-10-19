#!/usr/bin/env python3
"""Take an installer off the site for good, in one command.

  python3 scripts/remove_installer.py --email owner@example.ca --reason "asked to be removed"
  python3 scripts/remove_installer.py --name "Acme Heating" --city "Kelowna" --reason "..."
  python3 scripts/remove_installer.py --email a@x.ca --reason "..." --no-build   # queue several, then:
  python3 scripts/remove_installer.py --build                                       # rebuild once

What it does:
  1. Adds the company to data/installer-blocklist.json (rankings and the Google
     Places scraper skip it from now on) and logs it in data/installer-cleanup-log.csv.
  2. Drops its rows from installers/*-installers-real.csv and installers/json/**.json.
  3. Deletes its profile pages, 301s each to the ranking page it was on (or the
     city hub), and removes it from other profiles' "Other installers" lists and
     the installer directory.
  4. Unless --no-build: rebuilds rankings, the affected regions' city pages and
     hubs, the rebate finder, compacts redirects, runs the post-steps and checks
     that nothing blocked is still listed.
"""
import argparse
import csv
import io
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import installer_blocklist as bl  # noqa: E402

PENDING = ROOT / "data" / "installer-removals-pending.json"  # regions waiting for --build


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
        subprocess.run([sys.executable, *cmd], cwd=ROOT, check=True)
    run("scripts/build_installer_rankings.py")
    for code in sorted(regions):
        b = ROOT / "scripts" / f"build_{code}_pages.py"
        if b.exists():
            run(str(b.relative_to(ROOT)))
            run(str(b.relative_to(ROOT)), "--hubs")
    run("scripts/build_get_quotes.py")
    run("scripts/compact_redirects.py")
    run("scripts/post_steps.py")
    if subprocess.run([sys.executable, "scripts/installer_blocklist.py"], cwd=ROOT).returncode:
        sys.exit("A blocked installer is still listed; see above.")
    PENDING.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--email")
    ap.add_argument("--name")
    ap.add_argument("--city")
    ap.add_argument("--reason")
    ap.add_argument("--no-build", action="store_true", help="queue the removal; run --build after the last one")
    ap.add_argument("--build", action="store_true", help="rebuild for every queued removal")
    a = ap.parse_args()
    pending = set(json.loads(PENDING.read_text())) if PENDING.exists() else set()

    if a.build and not (a.email or a.name):
        build(pending or {"bc"})
        return
    if not (a.email or a.name) or not a.reason:
        ap.error("give --email or --name (with --city), and --reason")

    email = (a.email or "").strip().lower()
    rows = find_rows(email, a.name, a.city)
    if not rows:
        sys.exit("No installer row matches; nothing removed.")
    name = rows[0][1]["Business Name"].strip()
    cities = sorted({r["City"].strip() for _, r in rows})
    redirect_to = ranking_url(rows)

    entries = json.loads(bl.FILE.read_text()) if bl.FILE.exists() else []
    for c in cities:
        r = next(r for _, r in rows if r["City"].strip() == c)
        entries.append({"name": name, "city": c, "email": email or r.get("Email", "").strip().lower(),
                        "website": r.get("Website", "").strip(), "cid": bl._cid(r.get("Google Maps URL")),
                        "reason": a.reason, "date": date.today().isoformat()})
    bl.FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    bl._KEYS = None

    with open(ROOT / "data" / "installer-cleanup-log.csv", "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        for fp in sorted({fp.name for fp, _ in rows}):
            for c in cities:
                w.writerow([fp, name, c, "removed and blocked", f"{a.reason} ({date.today().isoformat()})"])

    n_csv, n_json = strip_csvs(), strip_json()
    gone = remove_profiles(name, cities, redirect_to)
    print(f"{name}: blocked; {n_csv} CSV rows, {n_json} JSON entries, {len(gone)} profiles removed ({', '.join(gone) or 'none'}) -> {redirect_to}")

    regions = {(re.match(r"([a-z]{2})-", fp.name) or [None, "bc"])[1] for fp, _ in rows}
    pending |= regions
    if a.no_build:
        PENDING.write_text(json.dumps(sorted(pending)) + "\n")
        print("Queued. Run: python3 scripts/remove_installer.py --build")
    else:
        build(pending)


if __name__ == "__main__":
    main()
