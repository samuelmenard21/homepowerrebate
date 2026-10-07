#!/usr/bin/env python3
"""Region hub cleanup: drop the legacy city list (the city finder above already links every city) and fold the long
legacy sections (rebate finder, FAQ, guides) into closed <details> so the page is short. Content stays in the HTML.
Run after build_hub_showcase.py; safe to re-run.   python3 scripts/build_hub_tidy.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUBS = ["ca/bc", "ca/on", "ca/ab", "ca/ns", "us/ma", "us/ny", "us/ca", "us/pa", "us/co", "us/vt", "us/mi"]
CITY_H = re.compile(r"Cities We Cover|Where HomePowerRebate operates", re.I)
FOLD = [(re.compile(r"rebate finder|rebate program", re.I), "Open the full rebate list"),
        (re.compile(r"common questions|quick questions|what you should know", re.I), "Read the questions and answers"),
        (re.compile(r"before you sign|read more", re.I), "See the guides"),
        (re.compile(r"by utility \(", re.I), "Read the utility-by-utility breakdown")]


def strip(x):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x)).strip()


ART_FOLD = re.compile(r"common questions|quick questions|^sources|rebate finder|more .* (guides|rebates)|status by city|what closed|scams|read more", re.I)
CITY_ART = re.compile(r"cities( we cover)?$", re.I)


def tidy_article(t, have):
    """Hubs that are one flat <article> of h2 blocks: fold the long ones, drop city lists the finder covers."""
    m = re.search(r'<article class="article">(.*?)</article>', t, re.S)
    if not m:
        return t
    body = m.group(1)
    parts = re.split(r"(?=<h2[ >])", body)
    out = [parts[0]]
    for p in parts[1:]:
        h2 = re.match(r"<h2[^>]*>(.*?)</h2>", p, re.S)
        title = strip(h2.group(1))
        rest = p[h2.end():]
        if "hub-fold" in rest:
            out.append(p)
            continue
        if CITY_ART.search(title):
            links = set(re.findall(r'href="(/(?:ca|us)/[a-z-]+/[a-z-]+/)"', rest))
            if links and links <= have:
                continue
        if ART_FOLD.search(title) and len(rest) > 1200:
            label = "Read the questions and answers" if re.search(r"questions", title, re.I) else "Open this section"
            p = p[:h2.end()] + f'\n<details class="hub-fold"><summary>{label}</summary>' + rest + "</details>\n"
        out.append(p)
    return t[:m.start(1)] + "".join(out) + t[m.end(1):]


TOC_SKIP = re.compile(r"not sure|weekly email|sources|newsletter|installers", re.I)


TOC_LABELS = [(r"rebate finder|rebate program|by category|by utility", "Rebate finder"), (r"question|faq|what you should know", "FAQ"),
              (r"before you sign|read more|guides|scams", "Guides"), (r"cities", "Cities"), (r"stack", "Rebate stack"),
              (r"utility|serves you", "Your utility"), (r"statewide|federal|covers|program", "Programs"), (r"what to do next|next", "Next steps"),
              (r"heat pump|furnace", "Heat pumps"), (r"status", "Status by city"), (r"closed", "What closed")]


def toc_label(title):
    for rx, label in TOC_LABELS:
        if re.search(rx, title, re.I):
            return label
    t = re.sub(r"[.?:]+$", "", title)
    return t if len(t) <= 26 else t[:26].rsplit(" ", 1)[0] + "…"


def toc_ids(mid):
    """Give every h2 an id (slug of its text) so the table of contents can link to it."""
    seen = set(re.findall(r'\bid="([^"]+)"', mid))

    def add(m):
        if re.search(r'\bid="', m.group(1)):
            return m.group(0)
        slug = re.sub(r"[^a-z0-9]+", "-", strip(m.group(2)).lower()).strip("-")[:40] or "section"
        while slug in seen:
            slug += "-x"
        seen.add(slug)
        return f'<h2{m.group(1)} id="{slug}">{m.group(2)}</h2>'
    return re.sub(r"<h2([^>]*)>(.*?)</h2>", add, mid, flags=re.S)


def tidy(t):
    a = t.find("<!-- HUB-SHOWCASE-END -->")
    b = t.find("<!-- CANONICAL-FOOTER-START")
    if a < 0 or b < 0:
        return t
    a += len("<!-- HUB-SHOWCASE-END -->")
    head, mid, tail = t[:a], t[a:b], t[b:]
    showcase = t[t.find("<!-- HUB-SHOWCASE-START -->"):a]
    have = set(re.findall(r'href="(/[^"]+)"', showcase))
    out, pos = [], 0
    for m in re.finditer(r"<section\b[^>]*>.*?</section>", mid, re.S):
        out.append(mid[pos:m.start()])
        s = m.group(0)
        pos = m.end()
        h2 = re.search(r"<h2[^>]*>(.*?)</h2>", s, re.S)
        title = strip(h2.group(1)) if h2 else ""
        if h2 and CITY_H.search(title):
            links = set(re.findall(r'href="(/(?:ca|us)/[a-z-]+/[a-z-]+/)"', s))
            for u in sorted(links - have):  # region pages the finder lacks move into "Explore more"
                nm = u.strip("/").split("/")[-1].replace("-", " ").title() + " guide"
                chip = f'<a class="hs-chip" href="{u}">{nm}</a>'
                k = head.rfind('<div class="hs-chips">')
                if k >= 0:
                    e2 = head.find("</div>", k)
                    head = head[:e2] + chip + head[e2:]
                    have.add(u)
            if links <= have:
                continue  # every city is now reachable from the finder
        if h2 and "hub-fold" not in s and len(s) > 2000:
            label = next((l for rx, l in FOLD if rx.search(title) or (rx.pattern.startswith("rebate finder") and 'id="rebate-finder"' in s[:200])), None)
            if label:
                ins = h2.end()
                lede = re.match(r'\s*<p class="lede">.*?</p>', s[ins:], re.S)
                if lede:
                    ins += lede.end()
                close = s.rfind("</div>", 0, s.rfind("</section>"))
                if close > ins:
                    s = s[:ins] + f'\n<details class="hub-fold"><summary>{label}</summary>' + s[ins:close] + "</details>\n" + s[close:]
        out.append(s)
    out.append(mid[pos:])
    mid = "".join(out).replace('href="#cities"', 'href="#find-city"')
    mid = re.sub(r"<!-- HUB-TOC-START -->.*?<!-- HUB-TOC-END -->\s*", "", mid, flags=re.S)
    mid = re.sub(r'<nav class="toc"[^>]*>.*?</nav>\s*', "", mid, flags=re.S)
    mid = toc_ids(mid)
    links = ['<a href="#find-city">Find your city</a>']
    for m in re.finditer(r'<h2[^>]*\bid="([^"]+)"[^>]*>(.*?)</h2>', mid, re.S):
        title = strip(m.group(2))
        if TOC_SKIP.search(title) or len(links) >= 7:
            continue
        label = toc_label(title)
        if any(f">{label}<" in l for l in links):
            continue
        links.append(f'<a href="#{m.group(1)}">{label}</a>')
    toc = ('<!-- HUB-TOC-START --><nav class="toc" aria-label="On this page"><span class="toc-lbl">On this page:</span>'
           + "".join(links) + "</nav><!-- HUB-TOC-END -->")
    mid = "\n" + toc + mid
    r = (head + mid + tail).replace('href="#cities" class="btn"', 'href="#find-city" class="btn"')
    if "<article" in mid:
        r = tidy_article(r, have)
    return r


def clean_head(t):
    """Drop the per-hub city-picker script (the shared nav picks the region from the URL) and the old Home / All States strip."""
    t = re.sub(r"\s*<script>\s*document\.addEventListener\('DOMContentLoaded', function \(\) \{ showProvinceCities\('[a-z]+'\); \}\);\s*</script>", "", t, count=1)
    t = re.sub(r'\s*<section class="wrap"[^>]*>\s*<div[^>]*>\s*<span[^>]*><a href="/">&larr; Home</a></span>\s*<span[^>]*><a href="/(?:us|ca)/">All [A-Za-z ]+</a></span>\s*</div>\s*</section>', "", t, count=1)
    return t


def main():
    for reg in HUBS:
        f = ROOT / reg / "index.html"
        t = clean_head(f.read_text(encoding="utf-8"))
        n = tidy(t)
        f.write_text(n, encoding="utf-8")
        print(reg, len(t), "->", len(n))


if __name__ == "__main__":
    main()
