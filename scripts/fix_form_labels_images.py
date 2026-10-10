#!/usr/bin/env python3
"""Idempotent accessibility fixes applied to built pages (run after generators):
- visible form controls without a label get an aria-label (placeholders are not labels)
- carousel placeholder images get width/height/lazy/async so they do not shift layout or load early
Honeypot fields (aria-hidden) are left alone."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = ("scripts/", "_partials/", "data/", "drafts/")

REPL = [
    ('<input type="text" id="ip-name" placeholder="First name" required>',
     '<input type="text" id="ip-name" placeholder="First name" aria-label="First name" autocomplete="given-name" required>'),
    ('<input type="email" id="ip-email" placeholder="your@email.com" required>',
     '<input type="email" id="ip-email" placeholder="your@email.com" aria-label="Email address" autocomplete="email" inputmode="email" required>'),
    ('<input type="tel" id="ip-phone" placeholder="Phone number" required>',
     '<input type="tel" id="ip-phone" placeholder="Phone number" aria-label="Phone number" autocomplete="tel" inputmode="tel" required>'),
    ('<input type="email" id="newsletter-email" placeholder="your@email.com" required style=',
     '<input type="email" id="newsletter-email" placeholder="your@email.com" required aria-label="Your email address" autocomplete="email" style='),
    ('<input type="text" name="website" id="il-hp" style="position:absolute; left:-9999px;" tabindex="-1" autocomplete="off">',
     '<input type="text" name="website" id="il-hp" style="position:absolute; left:-9999px;" tabindex="-1" autocomplete="off" aria-hidden="true">'),
    ('<input type="text" id="il-name" name="firstname" placeholder="Your Name" required>',
     '<input type="text" id="il-name" name="firstname" placeholder="Your Name" aria-label="Your name" autocomplete="given-name" required>'),
    ('<input type="email" id="il-email" name="email" placeholder="Your Email Address" required>',
     '<input type="email" id="il-email" name="email" placeholder="Your Email Address" aria-label="Your email address" autocomplete="email" required>'),
    ('<input type="tel" id="il-phone" name="phone" placeholder="Your Phone Number" required>',
     '<input type="tel" id="il-phone" name="phone" placeholder="Your Phone Number" aria-label="Your phone number" autocomplete="tel" required>'),
    ('<select id="il-city" name="city" required>', '<select id="il-city" name="city" aria-label="Your city" required>'),
]
JUMP = re.compile(r'<select id="directory-jump-select"(?![^>]*aria-label)')
SELECT = re.compile(r'<select id="res_([a-z_-]+)_category"(?![^>]*aria-label)')
IMG = re.compile(r'<img class="unified-carousel-installer-image" src=""(?![^>]*\bwidth=)')


def fix(s):
    for a, b in REPL:
        s = s.replace(a, b)
    s = JUMP.sub('<select id="directory-jump-select" aria-label="Jump to a region or city"', s)
    s = SELECT.sub(lambda m: f'<select id="res_{m.group(1)}_category" aria-label="Filter what homeowners paid by category"', s)
    s = IMG.sub('<img class="unified-carousel-installer-image" src="" width="400" height="200" loading="lazy" decoding="async"', s)
    return s


def main():
    files = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "*.html"], text=True).split()
    n = 0
    for f in files:
        if f.startswith(SKIP):
            continue
        p = ROOT / f
        s = p.read_text(encoding="utf-8", errors="ignore")
        t = fix(s)
        if t != s:
            p.write_text(t, encoding="utf-8")
            n += 1
    print(f"fixed {n} pages")


if __name__ == "__main__":
    main()
