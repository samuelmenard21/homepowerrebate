#!/usr/bin/env python3
"""Give sitemap URLs that nothing links to an inbound link from the index page a visitor would use. Marker-wrapped, so re-runs replace the block.
Run `python3 scripts/check_internal_links.py` and the orphan check in CLAUDE.md afterward."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from apply_canonical_nav_footer import content_insert_point  # noqa: E402

BOX = '<section style="max-width:880px;margin:24px auto;padding:0 20px;"><p style="background:#f5efe5;border-radius:8px;padding:14px 18px;margin:0;">{}</p></section>'
JOBS = [
    ("blog/index.html", "ORPHAN-LINKS", '<b>More guides:</b> <a href="/blog/heat-pump-or-solar-california/">Heat pump or solar first? The California decision guide</a> · <a href="/blog/ontario-home-renovation-savings-deadlines-2026/">Ontario Home Renovation Savings deadlines for 2026</a>.'),
    ("questions/index.html", "ORPHAN-LINKS", '<b>Popular questions:</b> <a href="/questions/kelowna-heat_pump/">Is Kelowna eligible for a heat pump rebate?</a> · <a href="/questions/victoria-heat_pump/">Is Victoria eligible for a heat pump rebate?</a>'),
    ("ca/on/index.html", "ORPHAN-LINKS", '<b>More Ontario pages:</b> <a href="/ca/on/heat-pump/">Ontario heat pump rebates for 2026</a> · <a href="/blog/ontario-home-renovation-savings-deadlines-2026/">Home Renovation Savings deadlines</a>.'),
    ("ca/ns/index.html", "ORPHAN-LINKS", '<b>More Nova Scotia pages:</b> <a href="/ca/ns/heat-pump/">Nova Scotia heat pump rebates for 2026</a>.'),
    ("ca/ab/index.html", "ORPHAN-LINKS", '<b>More Alberta pages:</b> <a href="/ca/ab/heat-pump/">Alberta heat pump rebates for 2026</a>.'),
    ("ca/index.html", "ORPHAN-LINKS", '<b>More Canada pages:</b> <a href="/ca/qc/heat-pump/">Quebec heat pump rebates for 2026</a>.'),
    ("ca/bc/index.html", "ORPHAN-LINKS", '<b>More BC pages:</b> <a href="/ca/bc/heat-pump/">BC heat pump rebates for 2026</a> · <a href="/ca/bc/fraser-valley/">Fraser Valley rebates</a> · <a href="/solar-battery">BC solar and battery rebates</a>.'),
]
for rel, marker, html in JOBS:
    p = ROOT / rel
    s = p.read_text(encoding="utf-8")
    block = f"<!-- {marker}-START -->{BOX.format(html)}<!-- {marker}-END -->"
    a, b = f"<!-- {marker}-START -->", f"<!-- {marker}-END -->"
    if a in s:
        i, j = s.index(a), s.index(b) + len(b)
        s = s[:i] + block + s[j:]
    else:
        k = content_insert_point(s)
        if k < 0:
            print("no insert point", rel)
            continue
        s = s[:k] + block + "\n" + s[k:]
    p.write_text(s, encoding="utf-8")
    print("linked", rel)
