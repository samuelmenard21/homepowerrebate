#!/usr/bin/env python3
"""Register every remaining inline <style> block on the site as a template variant, so the restamp serves it as a
cached /assets/tpl/<variant>.css file in the same place (same rules, same cascade position: nothing renders differently).

A block used by pages of one family is named <family>-<hash8>; a block shared across families (the breadcrumb rules,
an old copy of the header CSS) is common-<hash8>. Families come from apply_canonical_nav_footer.page_family().
Left inline on purpose: the font preload block (it must be in the HTML), EXTRACTED-INLINE blocks (homepage and
installer index, managed by externalize_inline_styles.py), template placeholders, and blocks with relative url()s.
Usage: python3 scripts/adopt_all_styles.py [--dry-run]"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as nf  # noqa: E402

TPL = ROOT / "_partials" / "templates"
STYLE_RE = re.compile(r'<style(?: id="[\w-]+")?>([\s\S]*?)</style>')
FONT_BLOCK = re.compile(r"<!-- FONT-PRELOAD-START -->.*?<!-- FONT-PRELOAD-END -->", re.S)


def eligible(css):
    if "EXTRACTED-INLINE-START" in css or "{{" in css or "{%" in css:
        return False
    for u in re.findall(r"url\(\s*['\"]?([^'\")]+)", css):
        if not re.match(r"(https?:|data:|/|#)", u):
            return False
    return bool(css.strip())


def main():
    dry = "--dry-run" in sys.argv
    reg_path = TPL / "variants.json"
    reg = json.loads(reg_path.read_text())
    known = {v["hash"] for v in reg.values()}
    found = {}  # hash -> [css, set(families), pages]
    for f in subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "*.html"], text=True).split():
        if f.startswith(("_partials/", "scripts/", "data/", "drafts/")):
            continue
        s = (ROOT / f).read_text(encoding="utf-8", errors="ignore")
        if "CANONICAL-NAV-START" not in s:
            continue
        s2 = FONT_BLOCK.sub("", s)
        fam = nf.page_family(s, nf.TPL_LINK_RE.findall(s))
        for css in STYLE_RE.findall(s2):
            h = nf._norm_hash(css)
            if h in known or not eligible(css):
                continue
            e = found.setdefault(h, [css, set(), 0])
            e[1].add(fam)
            e[2] += 1
    added = 0
    for h, (css, fams, n) in sorted(found.items(), key=lambda kv: -kv[1][2]):
        fam = next(iter(fams)) if len(fams) == 1 else "common"
        name = f"{fam}-{h[:8]}"
        added += 1
        if not dry:
            (TPL / "base" / f"{name}.css").write_text(css, encoding="utf-8")
            reg[name] = {"family": fam, "hash": h, "pages": n}
    if not dry:
        reg_path.write_text(json.dumps(reg, indent=1, sort_keys=True) + "\n")
    print(f"{'would add' if dry else 'added'} {added} variants")


if __name__ == "__main__":
    main()
