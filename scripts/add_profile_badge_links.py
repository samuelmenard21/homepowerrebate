#!/usr/bin/env python3
"""Installer profiles: a "Is this your company?" card linking to the badge page with that company's ranking picked.

A profile gets one card per ranking page it is listed on (found from the profile links on each ranking page) that has
a badge (the rankings in the badge page's picker). The link opens /installers/badge/?r=<region>&c=<city>&s=<service>.
The card sits just above the footer note inside PROFILE-BADGE markers, so re-runs replace it. Re-run after
generate_installer_profiles.py or build_installer_rankings.py.
Usage: python3 scripts/add_profile_badge_links.py"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCK_RE = re.compile(r"<!-- PROFILE-BADGE-START -->.*?<!-- PROFILE-BADGE-END -->\n?", re.S)
ANCHOR = '  <p class="ip-footer-note">'


def rankings():
    s = (ROOT / "installers/badge/index.html").read_text(encoding="utf-8")
    m = re.search(r"var R=(\[.*?\]),BASE=", s) or re.search(r"const B=(\[.*?\]);", s)
    data = json.loads(m.group(1))
    out = {}
    for r in data:
        for c in r.get("c", []):
            for x in c["s"]:
                out[x["u"]] = (c["n"], x["l"])
    return out


def card(u, city, label):
    _, region, c, svc = u.strip("/").split("/")
    href = f"/installers/badge/?r={region}&amp;c={c}&amp;s={svc}"
    return (f'<a href="{href}" class="ip-program"><div class="ip-program-name">Is this your company? Get your badge</div>'
            f'<div class="ip-program-detail">You&#39;re on our top-rated {html.escape(label)} installers in {html.escape(city)} list. '
            f'Add the badge to your website. Showing it doesn&#39;t change your rank.</div>'
            f'<span class="ip-program-arrow">&rarr;</span></a>')


def main():
    ranks = rankings()
    listed = {}
    for u in ranks:
        f = ROOT / u.strip("/") / "index.html"
        if not f.exists():
            continue
        for p in dict.fromkeys(re.findall(r'href="(/installers/profiles/[^"]+/)"', f.read_text(encoding="utf-8"))):
            listed.setdefault(p, []).append(u)
    changed = added = 0
    for f in sorted((ROOT / "installers/profiles").glob("*/*/*/index.html")):
        s = f.read_text(encoding="utf-8")
        p = "/" + str(f.parent.relative_to(ROOT)) + "/"
        new = BLOCK_RE.sub("", s)
        us = listed.get(p, [])
        if us and ANCHOR in new:
            block = ('<!-- PROFILE-BADGE-START -->\n  <aside class="ip-programs" aria-label="For this company">'
                     + "".join(card(u, *ranks[u]) for u in us) + "</aside>\n<!-- PROFILE-BADGE-END -->\n")
            new = new.replace(ANCHOR, block + ANCHOR, 1)
            added += 1
        if new != s:
            f.write_text(new, encoding="utf-8")
            changed += 1
    print(f"{added} profiles with a badge card, {changed} files changed")


if __name__ == "__main__":
    main()
