#!/usr/bin/env python3
"""Stamp company-supplied notes (data/installer-owner-notes.json) into installer profiles.

Each note goes right after the profile's intro paragraph, inside OWNER-NOTES markers, so re-runs
replace it. Re-run after generate_installer_profiles.py or add_missing_installer_profiles.py --refresh.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
START, END = "<!-- OWNER-NOTES-START -->", "<!-- OWNER-NOTES-END -->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.S)
INTRO_RE = re.compile(r'(<p class="ip-intro">.*?</p>\n)', re.S)


def block(note):
    body = " ".join(note["lines"])
    return f'{START}\n  <p class="ip-intro">{body} <em>(Added at the company\'s request.)</em></p>\n{END}\n'


def main():
    notes = json.loads((ROOT / "data" / "installer-owner-notes.json").read_text(encoding="utf-8"))["notes"]
    for note in notes:
        page = ROOT / note["profile"] / "index.html"
        if not page.exists():
            print(f"MISSING {note['profile']}")
            continue
        html = BLOCK_RE.sub("", page.read_text(encoding="utf-8"))
        new, n = INTRO_RE.subn(lambda m: m.group(1) + block(note), html, count=1)
        if not n:
            print(f"NO INTRO {note['profile']}")
            continue
        page.write_text(new, encoding="utf-8")
        print(f"stamped {note['profile']}")


if __name__ == "__main__":
    main()
