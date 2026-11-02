#!/usr/bin/env python3
"""The national quiz (learn_kit.national_quiz) on the PowerScore leaderboard and the federal heat pump pages (added 2026-11-01).
It sits just above the LEARN row, between NATIONAL-QUIZ markers so a re-run replaces it. Questions come from powerscore-data.json and the federal facts,
so they follow those files. A post-step (post_steps.py), idempotent."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import learn_kit as lk  # noqa: E402

PAGES = {"powerscore/leaderboard": "national-leaderboard", "programs/national-heat-pump-rebate": "national-federal",
         "programs/national-heat-pump-rebate/do-i-qualify": "national-qualify"}
S, E = "<!-- NATIONAL-QUIZ-START -->", "<!-- NATIONAL-QUIZ-END -->"
OLD = re.compile(re.escape(S) + r".*?" + re.escape(E) + r"\n?", re.S)


def main():
    q = lk.national_quiz()
    n = 0
    for rel, slug in PAGES.items():
        f = ROOT / rel / "index.html"
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8")
        t2 = OLD.sub("", t)
        i = t2.find("<!-- LEARN-START -->")
        if i < 0:
            i = navfooter.content_insert_point(t2)  # pages without a LEARN row: just above the shared footer block
        if not q or i < 0:
            if t2 != t:
                f.write_text(t2, encoding="utf-8")
            continue
        t2 = t2[:i] + f'{S}\n<div class="learn-wrap">{lk.quiz(slug, q)}</div>\n{E}\n' + t2[i:]
        if t2 != t:
            f.write_text(t2, encoding="utf-8")
            n += 1
    print(f"national quiz: {n} pages updated")


if __name__ == "__main__":
    main()
