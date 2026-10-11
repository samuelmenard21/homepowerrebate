#!/usr/bin/env python3
"""Find pages built on a template family's structure that still carry their own inline <style> copy, and register
each distinct copy as a variant of that family (see the "Page templates" note in apply_canonical_nav_footer.py).

For each variant: the block is saved verbatim to _partials/templates/base/<family>-<hash8>.css and added to
_partials/templates/variants.json. The next restamp swaps the inline block for /assets/tpl/<variant>.css (same rules,
same position) and adds the family's body class, which applies the family design.
Usage: python3 scripts/adopt_template_variants.py [--family article] [--min-pages 1] [--dry-run]"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "_partials" / "templates"
STYLE_RE = re.compile(r"<style>([\s\S]*?)</style>")

# family -> (structure every page must have, text that identifies the family's own style block)
FAMILIES = {
    "article": ((re.compile(r'<main[^>]*>.*?(<section class="hero"[^>]*>\s*<div class="wrap">.*?<article class="article"|<header class="post-header">\s*<div class="wrap">.*?<article>)', re.S),), (".hero", ".post-header")),
}


def norm_hash(css):
    return hashlib.sha1(" ".join(css.split()).encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", default="article", choices=sorted(FAMILIES))
    ap.add_argument("--min-pages", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    reg_path = TPL / "variants.json"
    reg = json.loads(reg_path.read_text()) if reg_path.exists() else {}
    known = {v["hash"] for v in reg.values()}
    tests, ident = FAMILIES[a.family]
    found = {}
    for f in subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "*.html"], text=True).split():
        if f.startswith(("_partials/", "scripts/", "data/", "drafts/")):
            continue
        s = (ROOT / f).read_text(encoding="utf-8", errors="ignore")
        if re.search(r'<body[^>]*class="[^"]*\btpl-', s) or not all(t.search(s) for t in tests):
            continue
        blocks = [b for b in STYLE_RE.findall(s) if any(i in b for i in ident) and "CANONICAL" not in b[:60] and "@font-face" not in b[:40]]
        if len(blocks) != 1:
            continue
        h = norm_hash(blocks[0])
        if h in known:
            continue
        found.setdefault(h, [blocks[0], []])[1].append(f)
    added = 0
    for h, (css, pages) in sorted(found.items(), key=lambda kv: -len(kv[1][1])):
        if len(pages) < a.min_pages:
            continue
        name = f"{a.family}-{h[:8]}"
        print(f"{name}: {len(pages)} pages, e.g. {pages[0]}")
        if not a.dry_run:
            (TPL / "base" / f"{name}.css").write_text(css, encoding="utf-8")
            reg[name] = {"family": a.family, "hash": h, "example": pages[0], "pages": len(pages)}
        added += 1
    if not a.dry_run:
        reg_path.write_text(json.dumps(reg, indent=1, sort_keys=True) + "\n")
    print(f"{'would add' if a.dry_run else 'added'} {added} variants")


if __name__ == "__main__":
    main()
