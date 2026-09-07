#!/usr/bin/env python3
"""
Cleanup pass after apply_canonical_nav_footer.py: ~1,185 pages already had
their own inline copy of the nav dropdown JS (toggleCityDropdown,
showProvinceCities) and/or the newsletter-form submit handler *before* the
canonical block was injected, so they ended up with two copies of the same
functions. Harmless (last declaration wins, identical code) but wasteful.

This removes any such duplicate function/handler definitions that fall
OUTSIDE the canonical `<!-- ... CANONICAL-NAV-FOOTER-JS ... -->` markers,
leaving exactly one copy per page (the canonical one).

Run from the Powerrebate root:
  python3 scripts/dedupe_nav_footer_js.py --dry-run
  python3 scripts/dedupe_nav_footer_js.py
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {".git", "node_modules", "scripts", ".claude", "_partials"}

JS_MARKER_START = "/* CANONICAL-NAV-FOOTER-JS-START */"
JS_MARKER_END = "/* CANONICAL-NAV-FOOTER-JS-END */"

FUNC_START_RE = re.compile(
    r"function\s+(toggleCityDropdown|showProvinceCities)\s*\([^)]*\)\s*\{"
)
NEWSLETTER_START_RE = re.compile(
    r"document\.getElementById\(['\"]newsletter-form['\"]\)\?\.addEventListener\(\s*['\"]submit['\"]\s*,\s*async\s*\([^)]*\)\s*=>\s*\{"
)


def find_balanced_block(content: str, open_brace_pos: int) -> int:
    """Given the index of the '{' that opens a block, return the index just
    past the matching closing '}'."""
    depth = 0
    i = open_brace_pos
    n = len(content)
    while i < n:
        c = content[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def protected_ranges(content: str):
    ranges = []
    start = 0
    while True:
        s = content.find(JS_MARKER_START, start)
        if s == -1:
            break
        e = content.find(JS_MARKER_END, s)
        if e == -1:
            break
        e += len(JS_MARKER_END)
        ranges.append((s, e))
        start = e
    return ranges


def in_protected(pos, ranges):
    return any(s <= pos < e for s, e in ranges)


def strip_duplicate_blocks(content: str):
    ranges = protected_ranges(content)
    removed = 0

    def process(pattern):
        nonlocal content, ranges, removed
        while True:
            match = None
            for m in pattern.finditer(content):
                if not in_protected(m.start(), ranges):
                    match = m
                    break
            if not match:
                break
            open_brace = content.index("{", match.start())
            end = find_balanced_block(content, open_brace)
            if end == -1:
                break  # malformed, bail rather than corrupt
            block_end = end
            # newsletter handler ends with ");" right after the closing brace
            tail_match = re.match(r"\s*\)\s*;", content[end:end + 6])
            if tail_match:
                block_end = end + tail_match.end()
            content = content[: match.start()] + content[block_end:]
            removed += 1
            ranges = protected_ranges(content)

    process(FUNC_START_RE)
    process(NEWSLETTER_START_RE)
    return content, removed


def find_pages():
    pages = []
    for p in ROOT.rglob("*.html"):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in EXCLUDE_DIRS or any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        pages.append(p)
    return sorted(pages)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total_removed = 0
    changed_files = 0
    for p in find_pages():
        content = p.read_text(errors="ignore")
        if JS_MARKER_START not in content:
            continue
        new_content, removed = strip_duplicate_blocks(content)
        if removed:
            changed_files += 1
            total_removed += removed
            if not args.dry_run:
                p.write_text(new_content)

    print(f"Removed {total_removed} duplicate block(s) across {changed_files} file(s).")


if __name__ == "__main__":
    main()
