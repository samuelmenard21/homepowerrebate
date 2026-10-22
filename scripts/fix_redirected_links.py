#!/usr/bin/env python3
"""Rewrite internal links that point at URLs _redirects sends elsewhere, so visitors and Googlebot skip the extra hop.
Also swaps the retired /retrofit-assessment/ page for /get-quotes/ (anchor labels included). Safe to re-run; run after any generator that may link to removed pages."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
red = {}
for line in (ROOT / "_redirects").read_text().splitlines():
    p = line.split()
    if len(p) >= 2 and not line.startswith("#") and p[1].startswith("/"):
        red[p[0].rstrip("/") or "/"] = p[1]


def target(path):
    seen = 0
    while path.rstrip("/") in red and seen < 5:
        path = red[path.rstrip("/")]
        seen += 1
    return path


files = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True).stdout.split()
changed = links = 0
for f in files:
    if f.startswith(("_partials/", "calculator/embed/", "embed/")):
        continue
    p = ROOT / f
    if not p.exists():
        continue
    s = p.read_text(encoding="utf-8", errors="ignore")
    o = s
    s = re.sub(r'(href="/retrofit-assessment/"[^>]*>)(Assessment|Retrofit Assessment)(<)', lambda m: m.group(1).replace("/retrofit-assessment/", "/get-quotes/") + "See my rebates" + m.group(3), s)
    # one name per action (2026-10-14): /get-quotes/ shows rebates and top-rated installers for a city; it is not an
    # assessment, gives estimates rather than exact amounts, and does not send quote requests (installer ranking forms do)
    s = re.sub(r'(<a\b[^>]*href="/get-quotes/[^"]*"[^>]*>)\s*(?:Start your assessment|Run your free assessment|Get quotes|Get Quotes)\s*(&rarr;|→)?\s*(</a>)',
               lambda m: m.group(1) + "See my rebates" + (" " + m.group(2) if m.group(2) else "") + m.group(3), s)
    s = re.sub(r'(<a\b[^>]*href="/get-quotes/[^"]*"[^>]*>)\s*Get your exact rebate amount\s*(&rarr;|→)?\s*(</a>)',
               lambda m: m.group(1) + "Estimate my rebates" + (" " + m.group(2) if m.group(2) else "") + m.group(3), s)
    s = re.sub(r"Get an exact number:(</strong>)? Fill out our free assessment tool to see your", lambda m: "Get your number:" + (m.group(1) or "") + " Pick your city in our free rebate finder to see your", s)
    s = s.replace("local context, and a free assessment tool.", "local context, and a free rebate finder.").replace("in our free assessment tool for an estimate", "in our free rebate finder for an estimate")

    def sub(m):
        global links
        h = m.group(1)
        base, sep, rest = re.match(r"([^?#]*)([?#].*)?$", h).group(1), "", (re.match(r"([^?#]*)([?#].*)?$", h).group(2) or "")
        k = base.rstrip("/") or "/"
        if k in red:
            links += 1
            return f'href="{target(base)}{rest}"'
        return m.group(0)
    s = re.sub(r'href="(/[^"]*)"', sub, s)
    if s != o:
        p.write_text(s, encoding="utf-8")
        changed += 1
print("files changed", changed, "links rewritten", links)

# glossary wording fixes (_partials/glossary.json 'fixes'): generators that still emit a retired phrase are corrected here,
# since this script already runs after every generator
sys.path.insert(0, str(ROOT / "scripts"))
from check_consistency import apply_fixes  # noqa: E402
print("glossary fixes applied to", apply_fixes(), "pages")
