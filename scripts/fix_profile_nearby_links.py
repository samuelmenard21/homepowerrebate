#!/usr/bin/env python3
"""Point profile-to-profile links at the profile page that actually exists.

Older BC/ON profiles live at /installers/profiles/<city>/<slug>/, newer ones at /installers/profiles/<region>/<city>/<slug>/.
A link to the missing spelling is rewritten to the existing one. Run after add_missing_installer_profiles.py.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROF = ROOT / "installers" / "profiles"
pat = re.compile(r'href="/installers/profiles/([a-z0-9-]+(?:/[a-z0-9-]+){1,2})/"')


def norm(slug):
    return re.sub(r"-and(?=-|$)", "", slug)


_idx = {}


def sibling(rel):
    """Existing profile in the same folder whose slug matches ignoring '&'/'and' spelling."""
    d, _, slug = rel.rpartition("/")
    if d not in _idx:
        base = PROF / d
        _idx[d] = {norm(x.name): x.name for x in base.iterdir() if (x / "index.html").exists()} if base.is_dir() else {}
    hit = _idx[d].get(norm(slug))
    return f"{d}/{hit}" if hit else None


def exists(rel):
    return (PROF / rel / "index.html").exists()


def main():
    changed = 0
    for f in PROF.rglob("index.html"):
        h = f.read_text(encoding="utf-8")

        def fix(m):
            rel = m.group(1)
            if exists(rel):
                return m.group(0)
            parts = rel.split("/")
            alt = "/".join(parts[1:]) if len(parts) == 3 else None
            for cand in (rel, alt):
                if cand:
                    if exists(cand):
                        return f'href="/installers/profiles/{cand}/"'
                    sib = sibling(cand)
                    if sib:
                        return f'href="/installers/profiles/{sib}/"'
            return m.group(0)

        n = pat.sub(fix, h)
        if n != h:
            f.write_text(n, encoding="utf-8")
            changed += 1
    print(f"fixed links in {changed} profile pages")


if __name__ == "__main__":
    main()
