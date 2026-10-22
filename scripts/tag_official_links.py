#!/usr/bin/env python3
"""Tag outbound links to official program pages so utilities can see the homeowners we send them, 2026-10-22.
For every external link to an official program source (same host list as follow_official_sources.py) this adds
  - data-official="1", read by the shared script in _partials/nav-footer.html, which sends one GA4 event, "official_click", with the
    link's host and path and the page it was clicked on (so Google Analytics shows sends per program and per city page), and
  - utm_source=homepowerrebate&utm_medium=referral&utm_campaign=program-link on the URL, so the program's own analytics show the visit
    as referral traffic from us. Documents (.pdf, .xlsx, ...) are left untouched.
Idempotent: a link that already has data-official is skipped. Run as a post-step (scripts/post_steps.py) after follow_official_sources.
Never tag links to installers, aggregators or manufacturers."""
import ast
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
UTM = "utm_source=homepowerrebate&amp;utm_medium=referral&amp;utm_campaign=program-link"
DOCS = (".pdf", ".xlsx", ".xls", ".docx", ".doc", ".zip", ".csv", ".png", ".jpg")


def host_lists():
    tree = ast.parse((ROOT / "scripts" / "follow_official_sources.py").read_text(encoding="utf-8"))
    got = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and n.targets[0].id in ("OFFICIAL_SUFFIX", "OFFICIAL_HOSTS"):
            got[n.targets[0].id] = ast.literal_eval(n.value)
    return got["OFFICIAL_SUFFIX"], got["OFFICIAL_HOSTS"]


SUFFIX, HOSTS = host_lists()


def official(host):
    host = host.lower().removeprefix("www.")
    return any(host == h or host.endswith("." + h) for h in HOSTS) or host.endswith(SUFFIX)


def tag(m):
    t = m.group(0)
    if "data-official" in t:
        return t
    hm = re.search(r'href="(https?://[^"#]+)(#[^"]*)?"', t)
    if not hm:
        return t
    url, frag = hm.group(1), hm.group(2) or ""
    host = urlparse(url.replace("&amp;", "&")).netloc
    if "homepowerrebate.com" in host or not official(host) or urlparse(url.replace("&amp;", "&")).path.lower().endswith(DOCS):
        return t
    new = url if "utm_source=" in url else url + ("&amp;" if "?" in url else "?") + UTM
    t = t.replace(hm.group(0), f'href="{new}{frag}"', 1)
    return t[:-1] + ' data-official="1">'


def main():
    changed = links = 0
    for f in subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True).stdout.split():
        if f.startswith(("_partials/", "scripts/", "embed/", "calculator/embed/")) or not (ROOT / f).exists():
            continue
        p = ROOT / f
        s = p.read_text(encoding="utf-8", errors="ignore")
        n = re.sub(r"<a [^>]*>", tag, s)
        if n != s:
            links += n.count('data-official="1"') - s.count('data-official="1"')
            p.write_text(n, encoding="utf-8")
            changed += 1
    print("pages changed", changed, "links tagged", links)


if __name__ == "__main__":
    main()
