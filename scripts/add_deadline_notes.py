#!/usr/bin/env python3
"""Put a "Deadline coming up" note on each page a row in data/rebate-deadlines.json points to.

The note sits between DEADLINE-NOTE-START/END markers: on hubs right after the HUB-TOP block, elsewhere right after the hero.
Every run removes old notes first, so a passed deadline or a closed program disappears on the next run.
The page script also hides an item once its date has passed, in case the rebuild is late.
Re-run after build_rebate_deadlines.py and after any generator rewrites these pages.
"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_rebate_deadlines import open_rows, fmt  # noqa: E402
import apply_canonical_nav_footer as navfooter  # noqa: E402

S, E = "<!-- DEADLINE-NOTE-START -->", "<!-- DEADLINE-NOTE-END -->"
e = html.escape


def note(rows):
    items = "".join(f'<li class="dn-i" data-deadline="{r["date"]}" style="margin:6px 0;"><b>{e(fmt(r["date"]))}:</b> {e(r["what"])} '
                    f'<a href="{e(r["source"])}" rel="noopener">Official source</a></li>' for r in rows)
    return (f'<section class="dn" style="max-width:880px;margin:24px auto;padding:0 20px;"><div style="background:#fdeccf;border-left:4px solid #d4751c;'
            f'border-radius:8px;padding:14px 18px;color:#5a3306;font-size:15px;line-height:1.5;"><p style="margin:0;font-weight:700;">Deadline coming up</p>'
            f'<ul style="margin:6px 0 0;padding:0 0 0 18px;">{items}</ul><p style="margin:8px 0 0;"><a href="/rebate-deadlines/">All upcoming deadlines</a></p></div></section>'
            '<script>(function(){var n=new Date();document.querySelectorAll(".dn-i").forEach(function(i){if(new Date(i.dataset.deadline+"T23:59:59")<n)i.remove()});'
            'document.querySelectorAll(".dn").forEach(function(s){if(!s.querySelector(".dn-i"))s.remove()})})();</script>')


def strip(t):
    return re.sub(re.escape(S) + r"[\s\S]*?" + re.escape(E) + r"\n?", "", t)


def put(t, block):
    t = strip(t)
    m = re.search(r"<!-- HUB-TOP-END -->", t) or re.search(r'<(section|header) class="hero[^"]*"[\s\S]*?</\1>', t)
    i = m.end() if m else navfooter.content_insert_point(t)
    return t[:i] + "\n" + S + block + E + "\n" + t[i:]


def main():
    by_page = {}
    for r in open_rows():
        by_page.setdefault(r["page"], []).append(r)
    changed = 0
    for f in ROOT.glob("**/index.html"):
        rel = "/" + str(f.parent.relative_to(ROOT)).replace("\\", "/") + "/"
        if rel.startswith(("/.claude/", "/dist/", "/node_modules/")):
            continue
        t = f.read_text(encoding="utf-8")
        rows = by_page.get(rel.replace("//", "/"))
        new = put(t, note(rows)) if rows else (strip(t) if S in t else t)
        if new != t:
            f.write_text(new, encoding="utf-8")
            changed += 1
    print(f"Deadline notes: {len(by_page)} pages listed, {changed} files changed.")


if __name__ == "__main__":
    main()
