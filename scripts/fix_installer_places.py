#!/usr/bin/env python3
"""Google Maps Platform terms: ratings and reviews from Places may be shown on a page with attribution, but must not power LocalBusiness, AggregateRating or Review markup.
Existing installer pages: drop the LocalBusiness JSON-LD from profile pages (name, address and phone come from Places) and make the attribution to Google Maps explicit.
The generators now write this directly; this script cleans pages generated earlier. Safe to re-run."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LD = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)
n = {"ld": 0, "attr": 0}
for f in subprocess.run(["git", "ls-files", "installers/*.html"], cwd=ROOT, capture_output=True, text=True).stdout.split():
    p = ROOT / f
    if not p.exists():
        continue
    s = o = p.read_text(encoding="utf-8", errors="ignore")
    if f.startswith("installers/profiles/"):
        def fix(m):
            try:
                d = json.loads(m.group(2))
            except Exception:
                return m.group(0)
            g = d.get("@graph")
            if isinstance(g, list):
                keep = [x for x in g if x.get("@type") not in ("LocalBusiness", "Review", "AggregateRating")]
                if len(keep) != len(g):
                    d["@graph"] = keep
                    n["ld"] += 1
                    return m.group(1) + json.dumps(d, ensure_ascii=False, indent=1) + m.group(3)
            return m.group(0)
        s = LD.sub(fix, s)
        s = re.sub(r"with a current Google rating of ([\d.]+)★ from (\d[\d,]*) reviews\.", r"with a current Google Maps rating of \1★ from \2 reviews (source: Google Maps).", s)
        s = re.sub(r'(<span class="ip-vet-detail">[\d.]+★ from \d[\d,]* reviews)(</span>)', r"\1 on Google Maps\2", s)
    s = s.replace('<p class="meta">Ratings collected ', '<p class="meta">Ratings and review counts from Google Maps, collected ')
    if s != o:
        p.write_text(s, encoding="utf-8")
        n["attr"] += 1
print(n)
