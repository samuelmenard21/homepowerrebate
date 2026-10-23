#!/usr/bin/env python3
"""Shared page components for the article-layout pages (city category pages, city hubs, province/state topic pages,
program pages). One place for the head, breadcrumb, hero, rebate grid, FAQ, sources line, structured data, quality gate
and page wrapper, so a design or markup change is made once. Builders pass data; they never carry their own HTML shell.

The restamp (apply_canonical_nav_footer.py) and the post-steps (post_steps.py) finish every page the same way.
"""
import html
import json
import re
from datetime import date
from pathlib import Path

import apply_canonical_nav_footer as navfooter
from status_pills import STATUS as _STATUS  # one status vocabulary site-wide

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://homepowerrebate.com"
AUTHOR = {"@type": "Person", "@id": f"{BASE}/about#sam-menard", "name": "Sam Menard", "url": f"{BASE}/about"}


def load_facts():
    """Every verified fact by id, from data/verified-facts/*.json (the one source for amounts, status and dates)."""
    facts = {}
    for f in sorted((ROOT / "data" / "verified-facts").glob("*.json")):
        for x in json.loads(f.read_text())["facts"]:
            facts[x["id"]] = x
    return facts


FACTS = load_facts()
# The article family's CSS as the restamp leaves it, read from a built article page: its family stylesheet link plus any
# inline <style> blocks, minus the font faces (the restamp adds those as the FONT-PRELOAD block) and dead blocks.
TEMPLATE = (ROOT / "ca/on/kitchener/heat-pump/index.html").read_text(encoding="utf-8")
_TPL_HEAD = re.sub(r"<!-- FONT-PRELOAD-START -->.*?<!-- FONT-PRELOAD-END -->", "", TEMPLATE, flags=re.S).split("</head>")[0]
CSS = "".join([navfooter.tpl_link(v).rstrip("\n") for v in navfooter.TPL_LINK_RE.findall(_TPL_HEAD) if v in navfooter.TEMPLATE_VARIANTS and v not in navfooter.DEAD_VARIANTS]
              + [m.group(0) for m in navfooter.STYLE_RE.finditer(_TPL_HEAD) if not navfooter.dead_css(m.group(2))])
PILL = {k: (cls, label) for k, (label, _tone, cls) in _STATUS.items()}
e = html.escape
GA = """<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-W33G4TGRHD');</script>"""
FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">"""


# Who-it-is-for chips on a rebate card (2026-10-23). Each chip appears only when the verified fact's own eligibility text says so (never inferred).
CHIP_RULES = [("Income-qualified", r"income[- ]qualified|income limit|low[- ]income|income below|household income"),
              ("Single-family homes", r"single[- ]family|single detached"),
              ("Replaces electric heat", r"replace electric heat|replacing electric heat|replaces electric heat"),
              ("Registered installer", r"hpcn|registered (?:contractor|installer)|program[- ]registered|licensed and trained")]


def chips(c):
    txt = " ".join(FACTS[i].get("eligibility", "") for i in c.get("facts", []) if i in FACTS).lower()
    got = [label for label, pat in CHIP_RULES if re.search(pat, txt)]
    return '<div class="rebate-chips">' + "".join(f"<span>{e(x)}</span>" for x in got) + "</div>" if got else ""


def card(c):
    cls, label = PILL[c.get("status", "active")]
    return (f'<div class="rebate-card"><span class="program-status {cls}">{label}</span><h3>{(f"<a href='{c['href']}'>" + e(c["title"]) + "</a>") if c.get("href") else e(c["title"])}</h3><div class="amount">{e(c["amount"])}</div>'
            f'<p style="font-size:14px;margin:8px 0 0;">{c["note"]}</p>{chips(c)}</div>')


def words(h):
    return len(re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).split())


def fact_ids(d):
    """Every fact a page names (cards and page-level), checked against the facts files."""
    fids = [i for cd in d["cards"] for i in cd.get("facts", [])] + d.get("facts", [])
    for i in fids:
        assert i in FACTS, f"unknown fact {i}"
    return fids


def checked(fids):
    """(ISO date, 'October 3, 2026') of the newest verified_on among the facts."""
    iso = max(FACTS[i]["verified_on"] for i in fids)
    return iso, date.fromisoformat(iso).strftime("%B %-d, %Y")


def cards(d):
    return "".join(card(x) for x in d["cards"])


def _first_sentence(s, n=170):
    s = re.sub(r"\s+", " ", s).strip()
    m = re.match(r"(.{20,%d}?[.;])(\s|$)" % n, s)
    return (m.group(1) if m else (s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "...")).rstrip(";")


def glance(d):
    """Who qualifies / How much / How to apply, read from the first card's verified fact (program pages, 2026-10-23). Rendered only when at least two parts have data."""
    if not d["cards"] or not d["cards"][0].get("facts"):
        return ""
    c = d["cards"][0]
    f = FACTS[c["facts"][0]]
    parts = []
    if c.get("amount") and not re.search(r"not confirmed|unverified|check", c["amount"], re.I):
        parts.append(("How much", e(c["amount"])))
    if f.get("eligibility"):
        parts.append(("Who qualifies", e(_first_sentence(f["eligibility"]))))
    link = f'<a href="{e(f["source_url"])}" target="_blank" rel="noopener">Official program page</a>' if f.get("source_url") else ""
    when = date.fromisoformat(f["verified_on"]).strftime("%B %-d, %Y") if f.get("verified_on") else ""
    how = " ".join(x for x in [e(f.get("dates", "")).rstrip("."), ] if x)
    parts.append(("How to apply", " ".join(x for x in [how + "." if how else "", link, f"Checked {when}." if when else ""] if x)))
    if len(parts) < 3:  # "How to apply" is always there, so at least one of amount and eligibility must be too
        return ""
    cells = "".join(f'<div class="glance-cell"><b>{h}</b><span>{b}</span></div>' for h, b in parts)
    return f'<div class="glance" aria-label="Program at a glance">{cells}</div>\n'


def claim(d):
    steps = "".join(f"<li>{s}</li>\n" for s in d.get("claim_steps", []))
    return f"<h2>{d['claim_heading']}</h2>\n<ol>\n{steps}</ol>" if steps else ""


def faq(d):
    return "".join(f'<div class="faq-item"><h3>{e(q)}</h3><p>{a}</p></div>\n' for q, a in d["faq"])


def sources(d):
    return " ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a>' + ("," if i < len(d["refs"]) - 1 else "") for i, (t, u) in enumerate(d["refs"]))


def sections(d):
    return "".join(f"<h2>{h}</h2>{b}" for h, b in d["sections"])


def callout(calc_url, calc_label, quotes_url, city_name, near_you=False):
    """The calculator box; with no quotes_url it asks the reader to pick their city in the calculator instead."""
    if quotes_url is None:
        return (f'<div class="callout"><strong>Want a number for your home?</strong> Run our <a href="{calc_url}" style="color:var(--teal,#0d4f5c); font-weight:600;">'
                f'{calc_label} rebate calculator</a> and pick {e(city_name)} to see what your utility pays.</div>')
    return (f'<div class="callout"><strong>Want a number for your home?</strong> Run our <a href="{calc_url}" style="color:var(--teal,#0d4f5c); font-weight:600;">'
            f'{calc_label} rebate calculator</a>, or <a href="{quotes_url}" style="color:var(--teal,#0d4f5c); font-weight:600;">get a plan emailed with the top-rated '
            f'installers {"near you" if near_you else "in " + e(city_name)}</a>.</div>')


def quality_gate(article, d, path, extra=(), loose_refs=False, min_words=750):
    """The shared gate: 750 words (or the page's min_words), 4 FAQs, 3 outside references, at most one em dash, no PowerScore
    status words. extra: (regex or callable, message) pairs for a region's own bans. loose_refs: count every outside link
    (topic pages), not only deep links. Raises SystemExit with every problem."""
    w = words(article)
    ext = {m for m in re.findall(r'href="(https?://[^"]+)"', article)}
    problems = []
    if w < d.get("min_words", min_words):
        problems.append(f"{w} words (<{d.get('min_words', min_words)})")
    if len(d["faq"]) < 4:
        problems.append("fewer than 4 FAQ items")
    if len([u for u in ext if "homepowerrebate" not in u and (loose_refs or not re.search(r"(maps\.google|^https?://[^/]*$)", u))]) < 3:
        problems.append("fewer than 3 external references")
    dashes = article.count("—") + article.count("&mdash;")
    if dashes > 1:
        problems.append(f"{dashes} em dashes")
    if re.search(r"waitlist|unclear|fully subscribed", article, re.I):
        problems.append("contains a PowerScore status keyword")
    for test, msg in extra:
        if (test(article) if callable(test) else re.search(test, article)):
            problems.append(msg)
    if problems:
        raise SystemExit(f"{path}: " + "; ".join(problems))
    return w


def faq_ld(d):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", html.unescape(a))}} for q, a in d["faq"]]}


def article_ld(title, desc, iso, path, published=None):
    """published: the first publish date when it differs from the last update (blog articles)."""
    return {"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc, "author": AUTHOR, "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
            "datePublished": published or iso, "dateModified": iso, "mainEntityOfPage": BASE + path}


def breadcrumb_ld(trail, home_slash=False):
    """trail: [(name, path)] from Home to this page. home_slash: the Home item is BASE + "/" (New Jersey's pages)."""
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + p if (p != "/" or home_slash) else BASE} for i, (n, p) in enumerate(trail)]}


def ld_scripts(items):
    return "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in items)


def breadcrumb(trail):
    """Visible breadcrumb; trail: [(name, path)], the last item is the current page."""
    *links, (cur, _) = trail
    return ('<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol>' + "".join(f'<li><a href="{p}">{n}</a></li>' for n, p in links)
            + f'<li aria-current="page">{cur}</li></ol></nav>')


def hero(d, tag="section"):
    return f"<{tag} class=\"hero\"><div class=\"wrap\"><div class=\"amount-badge\">{e(d['badge'])}</div><h1>{e(d['h1'])}</h1><p>{d['lead']}</p></div></{tag}>"


def head(title, desc, path, lds, extra_head="", extra_css=""):
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
{GA}
<meta name="description" content="{e(desc)}"><meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large"><link rel="canonical" href="{BASE}{path}">{extra_head}
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{BASE}{path}"><meta property="og:type" content="article">
<meta property="og:image" content="{BASE}/og-image.jpg">
{FONTS}
{CSS}{chr(10) + extra_css if extra_css else ""}
{lds}</head><body>"""


def write_page(path, title, desc, lds, nav, crumb, hero_html, top, article, footer, extra_head="", extra_css=""):
    """Assemble and write /path/index.html. nav and footer come from navfooter.render_nav/render_footer; top is the
    link row under the hero (may be empty; None leaves the row out, as on topic pages)."""
    row = "" if top is None else f"""<section class="wrap" style="padding:24px 28px 0;"><div style="font-size:14px; line-height:2.2;">
{top}</div></section>
"""
    page = f"""{head(title, desc, path, lds, extra_head, extra_css)}
{nav}
{crumb}
{hero_html}
{row}<article class="article"><div class="wrap">
{article}
</div></article>
{footer}
</body></html>
"""
    out = ROOT / path.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")


# ---- "Page updated" dates that change only when the content does ----
_DATES_FILE = ROOT / "data" / "page-dates.json"
_DATES = None


def stable_date(key, content, fallback=None):
    """ISO date a generated page's content last changed. key: the page path; content: the generated HTML with the date left
    out. Unchanged content keeps its stored date; changed content gets today's date; a page seen for the first time keeps
    `fallback` (the date it shows now) when given. Call save_dates() once after a build."""
    global _DATES
    if _DATES is None:
        _DATES = json.loads(_DATES_FILE.read_text()) if _DATES_FILE.exists() else {}
    import hashlib
    # cache-busting versions (site.css?v=..., og images) change with unrelated edits: leave them out of the fingerprint
    h = "v2:" + hashlib.sha1(re.sub(r"\?v=[0-9a-f]+", "", content).encode()).hexdigest()[:16]
    old = _DATES.get(key)
    if old and old["hash"] == h:
        return old["date"]
    first = old is None or not old["hash"].startswith("v2:")  # never seen, or saved before this fingerprint
    d = fallback if (first and fallback) else date.today().isoformat()
    _DATES[key] = {"hash": h, "date": d}
    return d


def save_dates():
    if _DATES is not None:
        _DATES_FILE.write_text(json.dumps(dict(sorted(_DATES.items())), indent=0) + "\n", encoding="utf-8")
