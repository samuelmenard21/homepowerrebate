#!/usr/bin/env python3
"""Program alerts, 2026-10-23: a small "get one email when this changes" box at the top of each program status page (the 13 heating bill help pages,
the Nova Scotia HARP program page and its payment-dates post). People come back to these pages to see whether something moved; this gives them a
one-time promise instead. One list per program in data/alert-programs.json (the lead router accepts exactly those ids at POST /alert), signups
stored in table `alerts` like the federal list, one confirmation email, unsubscribe link, CASL-safe (they asked for this one alert).
Marker-wrapped (PROG-ALERT-START/END), idempotent, a post-step. The submit handler and styles live once in _partials/nav-footer.html.
Announcements are sent by hand when a program opens, closes or changes (list: npx wrangler d1 execute homepowerrebate-outcomes --remote --command
"SELECT email FROM alerts WHERE list='heating-pa' AND unsubscribed=0").
Usage: python3 scripts/add_program_alerts.py  (then deploy the worker once: lead-router.js reads the same JSON)"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S, E = "<!-- PROG-ALERT-START -->", "<!-- PROG-ALERT-END -->"
ANCHOR = re.compile(r'(<article class="article"[^>]*>\s*(?:<div class="wrap">)?)')


def block(list_id, prog):
    name = html.escape(prog["name"])
    return (f'{S}<section class="prog-alert" data-list="{list_id}" data-region="{prog["region"]}" aria-label="Email alert for {name}">'
            f'<div class="prog-alert-text"><p class="prog-alert-h">Get one email when this changes</p>'
            f'<p>We will write once when {name} opens, closes or changes. Nothing else.</p></div>'
            '<form class="prog-alert-form"><label for="prog-alert-email">Email</label>'
            '<input id="prog-alert-email" type="email" name="email" required autocomplete="email" placeholder="Your email">'
            '<input class="prog-alert-hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">'
            '<button type="submit">Email me</button></form>'
            '<p class="prog-alert-done" role="status" hidden></p>'
            f'<p class="prog-alert-note">No spam. Unsubscribe anytime. We are an independent site, not the program.</p></section>{E}')


def main():
    progs = json.loads((ROOT / "data" / "alert-programs.json").read_text(encoding="utf-8"))["programs"]
    changed = 0
    for list_id, prog in progs.items():
        for path in [prog["page"]] + prog.get("extra_pages", []):
            f = ROOT / path.strip("/") / "index.html"
            if not f.exists():
                print("missing page:", path)
                continue
            s = f.read_text(encoding="utf-8")
            s2 = re.sub(r"\n?" + re.escape(S) + ".*?" + re.escape(E) + r"\n?", "", s, flags=re.S)
            m = ANCHOR.search(s2)
            if not m:
                print("no article anchor:", path)
                continue
            s2 = s2[:m.end()] + "\n" + block(list_id, prog) + "\n" + s2[m.end():]
            if s2 != s:
                f.write_text(s2, encoding="utf-8")
                changed += 1
    print("pages changed", changed)


if __name__ == "__main__":
    main()
