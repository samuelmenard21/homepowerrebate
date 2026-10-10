#!/usr/bin/env python3
"""Installer ranking pages (installers/<region>/<city>/<service>/): make each card click through to the company's profile.
- the whole card is a link (stretched name link), the name links to the profile, and a "View profile" button replaces the small "Profile" link
- the email shows as an "Email" button, never the address as text
Works on existing pages (so it does not undo later head/style fixes); build_installer_rankings.py writes the same markup for new pages. Idempotent.
Usage: python3 scripts/fix_ranking_cards.py"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_installer_rankings import slugify  # noqa: E402

CSS = """.rank{position:relative}
.rank.has-prof{cursor:pointer}
.rank.has-prof .nm>a::after{content:"";position:absolute;inset:0;border-radius:14px;z-index:1}
.rank.has-prof .nm>a:focus-visible::after{outline:3px solid var(--amber);outline-offset:2px}
.rank .act a,.rank .nm .badge,.rank .nm .bf,.rank .nm .reg{position:relative;z-index:2}
.rank .btn-prof{display:inline-flex;align-items:center;min-height:44px;padding:0 18px;border:2px solid var(--teal-deep);border-radius:999px;color:var(--teal-deep)!important;font-weight:700;font-size:15px;text-decoration:none!important;background:#fff}
.rank .btn-prof:hover{background:var(--teal-deep);color:#fff!important}"""
ANCHOR = ".rank .em{overflow-wrap:anywhere}"
LI = re.compile(r'<li class="(rank[^"]*)"([^>]*)>(.*?)</li>', re.S)


def fix_card(m, region, city_slug):
    cls, attrs, body = m.group(1), m.group(2), m.group(3)
    nm = re.search(r'<div class="nm">(.*?)</div>', body, re.S)
    if not nm:
        return m.group(0)
    inner = nm.group(1)
    name_html = re.split(r"<span ", inner, maxsplit=1)[0]
    name_text = re.sub(r"<[^>]+>", "", name_html)
    import html as _h
    name_plain = _h.unescape(name_text)
    prof = re.search(r'href="(/installers/profiles/[^"]+/)"', body)
    prof_url = prof.group(1) if prof else ""
    if not prof_url:
        for rel in (f"installers/profiles/{city_slug}/{slugify(name_plain)}", f"installers/profiles/{region}/{city_slug}/{slugify(name_plain)}"):
            if (ROOT / rel / "index.html").exists():
                prof_url = "/" + rel + "/"
                break
    if prof_url and "<a " not in name_html:
        body = body.replace(f'<div class="nm">{name_html}', f'<div class="nm"><a href="{prof_url}">{name_html}</a>', 1)
    if prof_url:
        body = re.sub(r'<a class="lnk" href="(/installers/profiles/[^"]+/)">Profile</a>', r'<a class="btn-prof" href="\1">View profile</a>', body)
        if "btn-prof" not in body:
            body = re.sub(r'(<div class="act">.*)(</div>\s*)$', lambda x: x.group(1) + f'<a class="btn-prof" href="{prof_url}">View profile</a>' + x.group(2), body, count=1, flags=re.S)
        if "has-prof" not in cls:
            cls += " has-prof"
    body = re.sub(r'<a class="lnk em" href="(mailto:[^"]+)">Email [^<]*</a>',
                  lambda x: f'<a class="lnk em" href="{x.group(1)}" aria-label="Email {_h.escape(name_plain)}">Email</a>', body)
    return f'<li class="{cls}"{attrs}>{body}</li>'


def patch(t, region, city_slug):
    t = LI.sub(lambda m: fix_card(m, region, city_slug), t)
    if ".rank.has-prof" not in t and ANCHOR in t:
        t = t.replace(ANCHOR, ANCHOR + "\n" + CSS, 1)
    return t


if __name__ == "__main__":
    n = 0
    for p in sorted((ROOT / "installers").glob("*/*/*/index.html")):
        rel = p.relative_to(ROOT / "installers").parts
        if rel[0] in ("profiles", "json"):
            continue
        t = p.read_text(encoding="utf-8")
        if '<li class="rank' not in t:
            continue
        u = patch(t, rel[0], rel[1])
        if u != t:
            p.write_text(u, encoding="utf-8")
            n += 1
    print("patched", n, "ranking pages")
