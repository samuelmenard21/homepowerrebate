#!/usr/bin/env python3
"""Keep _redirects inside Cloudflare Pages' limits (2,000 static + 100 dynamic rules).

Over the limit, Pages silently ignores most of the file (found 2026-10-16: 2,645 static rules,
only ~175 worked live, 110 merged pages returned 404 in Search Console).

What it does, in place:
  1. Drops `<path>.html` rules when `<path>` or `<path>/` already has a rule (old .html forms).
  2. Collapses per-city rules that differ only in the city segment into one `:city` rule,
     when the destination is identical (or uses the same city) and no page on disk matches the pattern.
  3. Removes exact duplicate sources (first rule wins, as on Pages).
Then fails if the result is still over the limits.

  python3 scripts/compact_redirects.py           # rewrite _redirects
  python3 scripts/compact_redirects.py --check   # only report counts, exit 1 if over the limit
"""
import re
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILE = ROOT / "_redirects"
MAX_STATIC, MAX_DYNAMIC = 2000, 100
MIN_GROUP = 3
TARGET_STATIC = 1700  # leave room for new rules between runs


def is_dynamic(src):
    return "*" in src or ":" in src


def counts(rules):
    d = sum(1 for r in rules if is_dynamic(r[0]))
    return len(rules) - d, d


def parse(lines):
    out = []
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or s.startswith("#"):
            out.append(("comment", line))
            continue
        parts = s.split()
        out.append(("rule", (parts[0], parts[1], parts[2] if len(parts) > 2 else "301")))
    return out


def page_exists(pattern_parts):
    """True if any folder on disk matches a path with one ':city' segment."""
    base = ROOT
    for p in pattern_parts:
        if p == ":city":
            return any((d / Path(*pattern_parts[pattern_parts.index(p) + 1:])).exists()
                       for d in base.iterdir() if d.is_dir()) if base.exists() else False
        base = base / p
    return base.exists()


def main():
    items = parse(FILE.read_text().splitlines())
    rules = [x for k, x in items if k == "rule"]
    before = counts(rules)

    # 3. duplicate sources
    seen = set()
    keep = set()
    for idx, (k, x) in enumerate(items):
        if k == "rule":
            if x[0] in seen:
                continue
            seen.add(x[0])
            keep.add(idx)
    # 1. .html variants
    srcs = {x[0] for k, x in items if k == "rule"}
    for idx in list(keep):
        src = items[idx][1][0]
        if src.endswith(".html") and not src.endswith("/index.html"):
            b = src[:-5]
            if b in srcs or b + "/" in srcs:
                keep.discard(idx)
        elif src.endswith("/index.html"):
            b = src[:-10]
            if b in srcs or b.rstrip("/") in srcs:
                keep.discard(idx)

    # 2. collapse city segment
    groups = defaultdict(list)
    for idx in keep:
        src, dst, code = items[idx][1]
        if is_dynamic(src):
            continue
        parts = src.strip("/").split("/")
        slash = src.endswith("/")
        for pos in range(1, len(parts)):
            city = parts[pos]
            pat = parts[:pos] + [":city"] + parts[pos + 1:]
            d = dst.replace(f"/{city}/", "/:city/") if f"/{city}/" in dst else dst
            groups[("/".join(pat), slash, d, code)].append((idx, city))
    used = set()
    new_rules = []
    static_now = sum(1 for i in keep if not is_dynamic(items[i][1][0]))
    dyn_now = sum(1 for i in keep if is_dynamic(items[i][1][0]))
    for (pat, slash, d, code), members in sorted(groups.items(), key=lambda g: -len(g[1])):
        members = [m for m in members if m[0] not in used]
        if static_now <= TARGET_STATIC or dyn_now >= MAX_DYNAMIC - 10:
            break
        if len(members) < MIN_GROUP or ":city" not in pat:
            continue
        pparts = pat.split("/")
        if page_exists(pparts):
            continue
        # the pattern must not match a source that redirects somewhere else
        rx = re.compile("^/" + re.escape(pat).replace(re.escape(":city"), "[^/]+") + ("/" if slash else "") + "$")
        clash = any(rx.match(items[i][1][0]) and i not in {m[0] for m in members}
                    for i in keep if not is_dynamic(items[i][1][0]))
        if clash:
            continue
        for m in members:
            used.add(m[0])
        static_now -= len(members)
        dyn_now += 1
        new_rules.append(("/" + pat + ("/" if slash else ""), d, code, members[0][0]))
    keep -= used

    first_at = defaultdict(list)
    for src, d, code, at in new_rules:
        first_at[at].append(f"{src} {d} {code}")
    out = []
    for idx, (k, x) in enumerate(items):
        if k == "comment":
            out.append(x)
        if idx in first_at:
            out.extend(first_at[idx])
        if k == "rule" and idx in keep:
            out.append(" ".join(x))
    # Pages expects static rules before dynamic ones; move every dynamic rule to the end.
    dyn = [l for l in out if l.strip() and not l.strip().startswith("#") and is_dynamic(l.split()[0])]
    out = [l for l in out if l not in dyn]
    out += ["", "# Dynamic rules (splats and :city placeholders) must come after all static rules on Cloudflare Pages."] + dyn
    final = [tuple(l.split()) for l in out if l.strip() and not l.strip().startswith("#")]
    st, dy = counts(final)
    print(f"before: {before[0]} static, {before[1]} dynamic; after: {st} static, {dy} dynamic")
    ok = st <= MAX_STATIC and dy <= MAX_DYNAMIC
    if "--check" in sys.argv:
        st0, dy0 = before
        sys.exit(0 if st0 <= MAX_STATIC and dy0 <= MAX_DYNAMIC else 1)
    if not ok:
        sys.exit("still over Cloudflare Pages limits; not written")
    FILE.write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
