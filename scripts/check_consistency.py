#!/usr/bin/env python3
"""Site-wide consistency check against _partials/glossary.json.

Rules: retired or misleading terms (glossary 'terms'), button labels per destination ('cta_labels'), one h1 per page,
no h2 -> h4 jump inside main (unless aria-level="3"). Counts are compared with _partials/consistency-baseline.json and
the check fails when any rule's count goes up, so new pages cannot add inconsistencies while old ones are fixed over time.

  python3 scripts/check_consistency.py                     # summary; exit 1 if any count rose above the baseline
  python3 scripts/check_consistency.py --list RULE [N]     # pages and snippets for one rule
  python3 scripts/check_consistency.py --update-baseline   # record current counts (only after fixing, so counts go down)
  python3 scripts/check_consistency.py --fix [--fix-only]  # apply the glossary's 'fixes' first (a post-step after generators)
"""
import html
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY = json.loads((ROOT / "_partials" / "glossary.json").read_text(encoding="utf-8"))
BASELINE_PATH = ROOT / "_partials" / "consistency-baseline.json"
sys.path.insert(0, str(ROOT / "scripts"))
from build_public import is_public, tracked_files  # noqa: E402  (only pages that ship are checked)
STRIP = re.compile(r"<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->", re.S | re.I)
A_RE = re.compile(r'<a\b([^>]*)href="([^"]*)"([^>]*)>(.*?)</a>', re.S | re.I)


def pages():
    for f in sorted(tracked_files()):
        if f.suffix != ".html" or not is_public(f) or f.as_posix().startswith("calculator/embed/") or not (ROOT / f).is_file():
            continue
        yield f.as_posix(), (ROOT / f).read_text(encoding="utf-8", errors="ignore")


def allowed_label(label: str, allowed) -> bool:
    return any(re.fullmatch(a[3:], label) if a.startswith("re:") else a == label for a in allowed)


def apply_fixes() -> int:
    """Exact-string replacements from the glossary's 'fixes' list (a post-step: generators that still emit an old
    phrase are corrected on every run). Returns the number of pages changed."""
    changed = 0
    for rel, raw in pages():
        new = raw
        for fx in GLOSSARY.get("fixes", []):
            new = re.sub(fx["find"], fx["replace"], new) if fx.get("regex") else new.replace(fx["find"], fx["replace"])
        if new != raw:
            (ROOT / rel).write_text(new, encoding="utf-8")
            changed += 1
    return changed


def text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def check(rel: str, raw: str):
    """Yield (rule, snippet) for every finding on one page."""
    if 'name="robots" content="noindex' in raw and "/profiles/" in rel:
        return
    t = STRIP.sub(" ", raw)
    visible = text(t)
    for term in GLOSSARY["terms"]:
        hay = t if term.get("html") else visible
        for m in re.finditer(term["pattern"], hay):
            s = hay[max(0, m.start() - 60):m.end() + 40]
            yield "term:" + term["id"], text(s) if term.get("html") else s
    for pre_attrs, href, post_attrs, inner in A_RE.findall(t):
        attrs = pre_attrs + post_attrs
        label = text(inner)
        arrow = label.endswith(("→", "»")) or label.endswith("->")
        buttonish = arrow or re.search(r'class="[^"]*\b(btn|cta|button)', attrs)
        if not buttonish:
            continue
        for dest, allowed in GLOSSARY["cta_labels"].items():
            if dest.startswith("_") or not href.startswith(dest):
                continue
            core = re.sub(r"\s*(→|»|->)$", "", label).strip()
            if core and not allowed_label(core, allowed):
                yield "cta:" + dest, core
    pills = GLOSSARY.get("pill_labels", {})
    ok_pills = set(pills.get("allowed", [])) | set(pills.get("allowed_fr", []))
    for lab in re.findall(r'<span class="(?:program-status|rb-status)[^"]*">([^<]*)<', t):
        if ok_pills and html.unescape(lab).strip() not in ok_pills:
            yield "pill:label", lab.strip()
    if len(re.findall(r"<h1\b", t, re.I)) != 1 and "<html" in t[:400].lower():
        yield "heading:h1-count", str(len(re.findall(r"<h1\b", t, re.I)))
    main = re.search(r"<main\b.*?</main>", t, re.S | re.I)
    body = main.group(0) if main else t
    last = 0
    for m in re.finditer(r"<h([1-6])\b([^>]*)>(.*?)</h\1>", body, re.S | re.I):
        lvl = int(m.group(1))
        al = re.search(r'aria-level="(\d)"', m.group(2))
        lvl = int(al.group(1)) if al else lvl
        if last and lvl > last + 1:
            yield "heading:skip", f"h{last} -> h{lvl} {text(m.group(3))[:60]}"
        last = lvl


def main():
    args = sys.argv[1:]
    if "--fix" in args:
        print(f"glossary fixes applied to {apply_fixes()} pages")
        if "--fix-only" in args:
            return
    counts, where = Counter(), defaultdict(list)
    for rel, raw in pages():
        for rule, snip in check(rel, raw):
            counts[rule] += 1
            where[rule].append((rel, snip))
    if "--list" in args:
        rule = args[args.index("--list") + 1]
        n = int(args[args.index("--list") + 2]) if len(args) > args.index("--list") + 2 else 40
        by = Counter(s for _, s in where[rule])
        for s, c in by.most_common(n):
            ex = next(r for r, x in where[rule] if x == s)
            print(f"{c:5d}  {s[:150]}   e.g. {ex}")
        return
    base = json.loads(BASELINE_PATH.read_text()) if BASELINE_PATH.exists() else {}
    if "--update-baseline" in args:
        rose = {r: c for r, c in counts.items() if c > base.get(r, c)}
        if rose and "--allow-increase" not in args:
            sys.exit(f"refusing: counts rose {rose}; fix them or pass --allow-increase")
        BASELINE_PATH.write_text(json.dumps(dict(sorted(counts.items())), indent=2) + "\n", encoding="utf-8")
        print("baseline updated:", dict(sorted(counts.items())))
        return
    bad = 0
    for rule in sorted(set(counts) | set(base)):
        c, b = counts.get(rule, 0), base.get(rule)
        state = "NEW " if b is None and c else "UP  " if b is not None and c > b else "down" if b is not None and c < b else "ok  "
        bad += state in ("NEW ", "UP  ")
        print(f"{state} {rule:28s} {c:6d}" + (f"  (baseline {b})" if b is not None else ""))
    if bad:
        print("\nA rule's count rose. See: python3 scripts/check_consistency.py --list <rule>")
    elif any(counts.get(r, 0) < b for r, b in base.items()):
        print("\nCounts went down: run --update-baseline to lock in the improvement.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
