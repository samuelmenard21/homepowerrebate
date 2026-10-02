#!/usr/bin/env python3
"""Keep _redirects and the page folders in step with data/ca/pages: a category with a prose file is a live page (its redirect is removed); a category without one
redirects to the city hub and its folder is deleted. Run after adding or removing a data/ca/pages/<city>/<category>.json file."""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from ca_cities import CITIES  # noqa: E402
from build_ca_pages import LABEL  # noqa: E402

lines = (ROOT / "_redirects").read_text().split("\n")
out = []
for l in lines:
    m = re.match(r"(/us/ca/[a-z-]+/[a-z-]+)/([a-z-]+)/?\s", l)
    drop = False
    if m:
        city = m.group(1).rsplit("/", 1)[1]
        cat = m.group(2)
        if city in CITIES and (ROOT / "data/ca/pages" / city / f"{cat}.json").exists():
            drop = True
    if not drop:
        out.append(l)
have = set(out)
added = 0
for slug, c in CITIES.items():
    pdir = ROOT / "data/ca/pages" / slug
    if not pdir.exists():
        continue
    hub = f"/us/ca/{c['area']}/{slug}/"
    for cat in LABEL:
        if (pdir / f"{cat}.json").exists():
            continue
        shutil.rmtree(ROOT / "us/ca" / c["area"] / slug / cat, ignore_errors=True)
        for suf in ("/", ""):
            r = f"{hub}{cat}{suf}  {hub}  301"
            if r not in have and not any(x.startswith(f"{hub}{cat}{suf} ") for x in out):
                out.append(r)
                have.add(r)
                added += 1
(ROOT / "_redirects").write_text("\n".join(out).rstrip("\n") + "\n")
print("redirect lines added", added, "removed", len(lines) - len(out) + added)
