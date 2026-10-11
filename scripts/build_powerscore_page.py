#!/usr/bin/env python3
"""Generate /powerscore/index.html from powerscore-data.json.

Reads the computed PowerScore data (see scripts/build_powerscore.py) and renders the page:
hero with the region gap and a city search (shareable ?city= scorecard), key findings, a strip
chart of every region and city, a region x upgrade heatmap, best places per upgrade (ties grouped),
the full sortable ranking with per-city breakdowns, method, reliability notes and a press box.
The shared nav and footer are restamped afterwards by apply_canonical_nav_footer.py.
"""
import html
import re
import json
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import regions
ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "powerscore-data.json").read_text())

CAT_LABELS = DATA["category_labels"]
CATEGORIES = list(CAT_LABELS.keys())
CAT_EMOJI = {
    "heat-pump": "&#128293;",
    "insulation": "&#127777;&#65039;",
    "solar": "&#9728;&#65039;",
    "battery": "&#128267;",
    "water-heater": "&#128167;",
    "smart-thermostats": "&#127777;&#65039;",
    "ev-charger": "&#128663;",
    "windows-doors": "&#129003;",
}

rows = DATA["leaderboard_overall"]
total_cities = DATA["stats"]["total_cities"]
total_regions = DATA["stats"]["total_regions"]


def esc(s):
    return html.escape(str(s), quote=True)


# ---------- Est. Annual Energy Cost (display-only, does NOT affect scoring) ----------
# Region/utility-level combined electricity + heating-fuel cost estimate for a
# 2,500 sq ft home. Sourced from BC Hydro, FortisBC, Enbridge Gas, ATCO Gas,
# Nova Scotia Power, PG&E/SCE/SDG&E/SMUD, Con Edison/PSEG/National Grid,
# Eversource/National Grid MA, PECO/UGI/Peoples Gas, Xcel Energy, Colorado
# Springs Utilities, Green Mountain Power, Burlington Electric Department,
# plus EIA and Statistics Canada usage data. Region-level, not a per-city bill.
# Keyed by (region_key, slug_prefix) where slug_prefix is the first path
# segment of the city slug (used for CA utility territory / NY utility
# territory sub-splits); "" matches when the slug has no sub-prefix.
ENERGY_COST = {
    ("ca/bc", ""): {"display": "$2,150", "range": False},
    ("ca/on", ""): {"display": "$2,750", "range": False},
    ("ca/ab", ""): {"display": "$3,700", "range": False},
    ("ca/ns", ""): {"display": "$3,350&ndash;$5,500", "range": True},
    ("us/ca", "bay-area"): {"display": "$2,875", "range": False},
    ("us/ca", "los-angeles"): {"display": "$2,875", "range": False},
    ("us/ca", "inland-empire"): {"display": "$2,875*", "range": False},
    ("us/ca", "san-diego"): {"display": "$3,400+", "range": False},
    ("us/ca", "sacramento"): {"display": "$2,300", "range": False},
    ("us/ca", ""): {"display": "$2,875*", "range": False},
    ("us/ny", "con-edison"): {"display": "$4,250", "range": False},
    ("us/ny", "pseg"): {"display": "$3,000", "range": False},
    ("us/ny", "national-grid"): {"display": "$3,050", "range": False},
    ("us/ny", "central-hudson"): {"display": "$3,050*", "range": False},
    ("us/ma", ""): {"display": "$3,600&ndash;$5,000", "range": True},
    ("us/pa", "philadelphia"): {"display": "$3,300", "range": False},
    ("us/pa", "pittsburgh"): {"display": "$3,900", "range": False},
    ("us/pa", "allentown"): {"display": "$3,400", "range": False},
    ("us/pa", "erie"): {"display": "$3,200*", "range": False},
    ("us/pa", ""): {"display": "$3,450*", "range": False},
    ("us/co", "denver"): {"display": "$2,200*", "range": False},
    ("us/co", "aurora"): {"display": "$2,200*", "range": False},
    ("us/co", "boulder"): {"display": "$2,200*", "range": False},
    ("us/co", "fort-collins"): {"display": "$1,950*", "range": False},
    ("us/co", "colorado-springs"): {"display": "$2,000*", "range": False},
    ("us/co", ""): {"display": "$2,050*", "range": False},
    ("us/vt", ""): {"display": "$4,900", "range": False},
}


def energy_cost_for(r):
    # slug is either "city" (flat, e.g. PA) or "utility-prefix/city" (CA, NY).
    # Try the full slug (flat-city override, e.g. PA per-city rates), then
    # the utility prefix (CA/NY sub-territory), then the region-wide default.
    prefix = r["slug"].split("/")[0] if "/" in r["slug"] else ""
    key = (r["region"], r["slug"])
    if key not in ENERGY_COST:
        key = (r["region"], prefix)
    if key not in ENERGY_COST:
        key = (r["region"], "")
    info = ENERGY_COST.get(key)
    if not info:
        return "&mdash;"
    return info["display"]


def score_band(score):
    if score >= 75:
        return "band-great"
    if score >= 50:
        return "band-good"
    if score >= 25:
        return "band-fair"
    return "band-low"


def gauge_style(score):
    pct = max(0, min(100, score))
    deg = pct * 3.6
    return f"--score-deg:{deg}deg;"



# ---------- data reliability ----------
VERIFIED_FILES = regions.FACTS_FILES


def region_verified(reg):
    files = VERIFIED_FILES.get(reg, [])
    return any((ROOT / "data" / "verified-facts" / f"{f}.json").exists() for f in files)


def region_stats():
    by = {}
    for r in rows:
        by.setdefault(r["region"], []).append(r)
    out = {}
    for reg, rs in by.items():
        cells = [r["categories"][c] for r in rs for c in CATEGORIES]
        quant = sum(1 for v in cells if v.get("dollar_value")) / len(cells)
        vecs = {}
        for r in rs:
            vecs.setdefault(tuple(round(r["categories"][c]["score"], 1) for c in CATEGORIES), []).append(r)
        alike = max(len(v) for v in vecs.values())
        ver = region_verified(reg)
        if not ver:
            read, level = "Unverified: treat as a rough guide until we check each program against its official page.", "low"
        elif alike / len(rs) >= 0.6:
            read, level = "Province-wide programs decide most scores, so many cities tie. Local programs are what separate them.", "mid"
        elif len(rs) < 6:
            read, level = "Only a few cities covered, so comparisons are limited.", "mid"
        else:
            read, level = "Good for comparing cities inside this region.", "high"
        out[reg] = {"label": rs[0]["region_label"], "n": len(rs), "verified": ver, "quant": quant, "alike": alike, "read": read, "level": level}
    return out


REGION_STATS = region_stats()


def conf_tag(reg):
    st = REGION_STATS.get(reg)
    if st and st["level"] == "low":
        return '<span class="conf low" title="This region\'s numbers have not been checked against official program pages yet">unverified data</span>'
    return ""


def render_reliability():
    body = "".join(
        f'<tr><td><b>{esc(st["label"])}</b></td><td>{st["n"]}</td>'
        f'<td>{"Yes" if st["verified"] else "<span class=conf-no>Not yet</span>"}</td>'
        f'<td>{st["quant"]*100:.0f}%</td><td>{st["alike"]} of {st["n"]}</td>'
        f'<td><span class="lvl {st["level"]}">{esc(st["read"])}</span></td></tr>'
        for reg, st in sorted(REGION_STATS.items(), key=lambda kv: kv[0]))
    return body


reliability_rows_html = render_reliability()
unverified = ", ".join(st["label"] for st in REGION_STATS.values() if not st["verified"]) or "none"

# ---------- shared helpers ----------
def comp_ranks():
    """Competition ranking: cities with the same score share a rank (T-6), instead of an arbitrary order."""
    scores = [round(r["overall"], 1) for r in rows]
    out = []
    for sc in scores:
        rank = 1 + sum(1 for x in scores if x > sc)
        out.append((rank, scores.count(sc) > 1))
    return out


RANKS = comp_ranks()
SHORT_LABELS = {
    "heat-pump": "Heat pump", "insulation": "Insulation", "solar": "Solar", "battery": "Battery",
    "water-heater": "Water heater", "smart-thermostats": "Thermostat", "ev-charger": "EV charger",
    "windows-doors": "Windows",
}


def money(amount, country):
    return f'{"CA$" if country == "Canada" else "US$"}{amount:,.0f}'


def band_word(score):
    return "excellent" if score >= 75 else "solid" if score >= 50 else "limited" if score >= 25 else "thin"


def by_region():
    by = {}
    for r in rows:
        by.setdefault(r["region"], []).append(r)
    return dict(sorted(by.items(), key=lambda kv: -sum(x["overall"] for x in kv[1]) / len(kv[1])))


BY_REGION = by_region()
REGION_AVG = {reg: sum(x["overall"] for x in rs) / len(rs) for reg, rs in BY_REGION.items()}
TOP_REG, BOT_REG = next(iter(BY_REGION)), list(BY_REGION)[-1]
TOP_LABEL, BOT_LABEL = BY_REGION[TOP_REG][0]["region_label"], BY_REGION[BOT_REG][0]["region_label"]
GAP_RATIO = REGION_AVG[TOP_REG] / max(REGION_AVG[BOT_REG], 1)
CA_AVG = sum(r["overall"] for r in rows if r["country"] == "Canada") / max(1, sum(1 for r in rows if r["country"] == "Canada"))
US_AVG = sum(r["overall"] for r in rows if r["country"] != "Canada") / max(1, sum(1 for r in rows if r["country"] != "Canada"))
# the largest region whose cities all land within a few points of each other
TIGHT_REG = min((reg for reg, rs in BY_REGION.items() if len(rs) >= 10),
                key=lambda reg: max(x["overall"] for x in BY_REGION[reg]) - min(x["overall"] for x in BY_REGION[reg]))
TIGHT = BY_REGION[TIGHT_REG]


def score_bar(score, cls=""):
    return f'<span class="ps-bar {cls}"><i style="width:{max(2, min(100, score)):.0f}%"></i></span>'


# ---------- hero gap card ----------
def render_gap():
    regs = list(BY_REGION.items())
    pick = regs[:3] + regs[-3:]
    out = []
    for i, (reg, rs) in enumerate(pick):
        avg = REGION_AVG[reg]
        if i == 3:
            out.append('<li class="ps-gap-sep" aria-hidden="true"><span></span></li>')
        out.append(f'<li><span class="ps-gap-name">{esc(rs[0]["region_label"])}</span>'
                   f'<span class="ps-gap-track"><i class="{"hi" if i < 3 else "lo"}" style="width:{avg:.0f}%"></i></span>'
                   f'<b>{avg:.0f}</b></li>')
    return "\n".join(out)


# ---------- key findings ----------
def render_findings():
    tight_lo = min(x["overall"] for x in TIGHT)
    tight_hi = max(x["overall"] for x in TIGHT)
    cards = [
        ("The gap", f"{GAP_RATIO:.1f}&times;",
         f"{esc(TOP_LABEL)} cities average a PowerScore of {REGION_AVG[TOP_REG]:.0f}. {esc(BOT_LABEL)} cities average {REGION_AVG[BOT_REG]:.0f}. "
         "Same upgrades, very different help."),
        ("Canada vs the US", f"{CA_AVG:.0f} vs {US_AVG:.0f}",
         "Canadian cities average higher scores than US cities. Big province-wide programs cover every city at once, "
         "while many US rebates depend on your utility."),
        ("Province beats postcode", f"{tight_hi - tight_lo:.1f} points",
         f"All {len(TIGHT)} {esc(TIGHT[0]['region_label'])} cities score between {tight_lo:.0f} and {tight_hi:.0f}. "
         f"Across all {total_cities} cities there are only {distinct_scores} different scores. Where you live is mostly about your province or state."),
    ]
    return "\n".join(
        f'<article class="ps-find"><p class="ps-find-k">{k}</p><p class="ps-find-n">{n}</p><p class="ps-find-t">{t}</p></article>'
        for k, n, t in cards)


# ---------- every region, every city (strip chart) ----------
def render_strip():
    out = []
    for reg, rs in BY_REGION.items():
        avg = REGION_AVG[reg]
        lo, hi = min(x["overall"] for x in rs), max(x["overall"] for x in rs)
        best = max(rs, key=lambda x: x["overall"])
        dots = "".join(f'<i class="ps-dot" style="left:{x["overall"]:.1f}%" title="{esc(x["label"])}: {x["overall"]:.0f}"></i>' for x in rs)
        flag = "CA" if rs[0]["country"] == "Canada" else "US"
        out.append(f'''<button type="button" class="ps-strip-row" data-region="{esc(reg)}" aria-label="{esc(rs[0]["region_label"])}: average {avg:.0f}, {len(rs)} cities. Show these cities in the full ranking.">
  <span class="ps-strip-name"><b>{esc(rs[0]["region_label"])}</b><small>{flag} &middot; {len(rs)} {"city" if len(rs) == 1 else "cities"} &middot; best: {esc(best["label"])}</small>{conf_tag(reg)}</span>
  <span class="ps-strip-track"><span class="ps-range" style="left:{lo:.1f}%;width:{max(.6, hi - lo):.1f}%"></span>{dots}<span class="ps-avg" style="left:{avg:.1f}%"></span></span>
  <span class="ps-strip-num">{avg:.0f}</span>
</button>''')
    return "\n".join(out)


# ---------- heatmap: region average per category ----------
def heat_cell(score):
    s = max(0, min(100, score))
    return f'<td style="--h:{s:.0f}%" class="{"dk" if s >= 55 else ""}" title="{s:.0f} out of 100">{s:.0f}</td>'


def render_heatmap():
    head = "".join(f'<th scope="col">{esc(SHORT_LABELS[c])}</th>' for c in CATEGORIES)
    body = []
    for reg, rs in BY_REGION.items():
        cells = "".join(heat_cell(sum(x["categories"][c]["score"] for x in rs) / len(rs)) for c in CATEGORIES)
        body.append(f'<tr><th scope="row">{esc(rs[0]["region_label"])}</th>{cells}<td class="ps-heat-all">{REGION_AVG[reg]:.0f}</td></tr>')
    return f'<thead><tr><th scope="col"><span class="sr">Region</span></th>{head}<th scope="col">Overall</th></tr></thead><tbody>{"".join(body)}</tbody>'


# ---------- best places for each upgrade (ties grouped by region) ----------
def category_groups(cat, limit=5):
    groups = []
    for r in DATA["leaderboard_by_category"][cat]:
        if r["score"] <= 0:
            continue
        key = (r["region"], round(r["score"], 1), r["dollar_value"])
        if groups and groups[-1]["key"] == key:
            groups[-1]["cities"].append(r)
        else:
            if len(groups) == limit:
                break
            groups.append({"key": key, "cities": [r]})
    return groups


def render_champions():
    cards = []
    for cat in CATEGORIES:
        groups = category_groups(cat)
        if not groups:
            continue
        top = groups[0]["cities"][0]
        n0 = len(groups[0]["cities"])
        lead_name = esc(top["label"]) if n0 == 1 else esc(top["region_label"])
        lead_who = f'{esc(top["region_label"])}, score {top["score"]:.0f}' if n0 == 1 else f'{n0} cities tie at {top["score"]:.0f}'
        items = []
        for g in groups:
            c0 = g["cities"][0]
            ctry = DATA["regions"][c0["region"]]["country"]
            names = (", ".join(esc(x["label"]) for x in g["cities"]) if len(g["cities"]) <= 2
                     else f'{esc(g["cities"][0]["label"])} and {len(g["cities"]) - 1} more')
            amt = money(c0["dollar_value"], ctry) if c0["dollar_value"] else ""
            items.append(f'<li><span class="ps-ch-who"><a href="{esc(c0["url"])}">{names}</a><small>{esc(c0["region_label"])}{" &middot; " + amt if amt else ""}</small></span>'
                         f'{score_bar(c0["score"])}<b>{c0["score"]:.0f}</b></li>')
        cards.append(f'''<article class="ps-ch">
  <header><h3>{esc(SHORT_LABELS[cat])}</h3><p class="ps-ch-amt">{lead_name}</p><p class="ps-ch-lead">{lead_who}</p></header>
  <ol>{"".join(items)}</ol>
</article>''')
    return "\n".join(cards)


# ---------- full ranking ----------
def mini_profile(r):
    return '<span class="ps-prof" aria-hidden="true">' + "".join(
        f'<i style="height:{max(6, r["categories"][c]["score"]):.0f}%" title="{esc(SHORT_LABELS[c])}: {r["categories"][c]["score"]:.0f}"></i>'
        for c in CATEGORIES) + "</span>"


def render_rows():
    out = []
    for i, r in enumerate(rows):
        rank, tied = RANKS[i]
        key = f'{r["region"]}/{r["slug"]}'
        data_cat = " ".join(f'data-c-{c}="{r["categories"][c]["score"]:.1f}"' for c in CATEGORIES)
        out.append(f'''<tr id="city-{esc(key).replace("/", "-")}" data-key="{esc(key)}" data-overall="{r["overall"]}" data-potential="{r.get("potential_usd", 0)}" data-region="{esc(r["region"])}" data-name="{esc(r["label"]).lower()}" data-order="{i}" {data_cat}>
  <td class="ps-rk">{"T-" if tied else ""}{rank}</td>
  <td class="ps-city"><a href="{esc(r["url"])}">{esc(r["label"])}</a><small>{esc(r["region_label"])}</small>{conf_tag(r["region"])}</td>
  <td class="ps-sc"><b>{r["overall"]:.0f}</b>{score_bar(r["overall"])}</td>
  <td class="ps-pf">{mini_profile(r)}</td>
  <td class="ps-pot">US${r.get("potential_usd", 0):,.0f}<small>{r.get("open_count", 0)} of 8 open</small></td>
  <td class="ps-more"><button type="button" class="ps-open" aria-expanded="false" aria-label="Show the {esc(r["label"])} breakdown">Details</button></td>
</tr>''')
    return "\n".join(out)


# ---------- comparisons and further reading ----------
COMPARE_PICKS = ["vancouver-vs-toronto", "toronto-vs-boston", "vancouver-vs-boston", "toronto-vs-new-york-city",
                 "new-york-city-vs-los-angeles", "calgary-vs-vancouver", "halifax-vs-toronto", "ottawa-vs-victoria",
                 "edmonton-vs-toronto", "boston-vs-new-york-city"]


def render_compare_links():
    links = []
    for slug in COMPARE_PICKS:
        if (ROOT / "powerscore" / "compare" / slug / "index.html").exists():
            a, b = slug.split("-vs-")
            nice = lambda s: " ".join(w.capitalize() for w in s.split("-"))
            links.append(f'<a href="/powerscore/compare/{slug}/">{nice(a)} vs {nice(b)}</a>')
    return "".join(links)


# ---------- data for the page script ----------
def page_rows_json():
    out = []
    for i, r in enumerate(rows):
        rank, tied = RANKS[i]
        rs = BY_REGION[r["region"]]
        reg_rank = 1 + sum(1 for x in rs if round(x["overall"], 1) > round(r["overall"], 1))
        reg_tied = sum(1 for x in rs if round(x["overall"], 1) == round(r["overall"], 1)) > 1
        ec = energy_cost_for(r)
        out.append({
            "k": f'{r["region"]}/{r["slug"]}', "n": r["label"], "r": r["region_label"], "rg": r["region"],
            "cur": "CA$" if r["country"] == "Canada" else "US$", "s": round(r["overall"], 1), "u": r["url"],
            "rk": rank, "t": tied, "rr": reg_rank, "rt": reg_tied, "rn": len(rs), "p": r.get("potential_usd", 0), "o": r.get("open_count", 0),
            "e": "" if ec == "&mdash;" else html.unescape(ec),
            "c": [[round(r["categories"][c]["score"]), r["categories"][c]["dollar_value"], r["categories"][c]["status"][0]] for c in CATEGORIES],
        })
    return json.dumps(out, separators=(",", ":"))


# ---------- JSON-LD ----------
def render_jsonld():
    dataset = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "HomePowerRebate PowerScore City Rebate Rankings",
        "description": "A calculated 0-100 score for every city HomePowerRebate covers, ranking how much home-energy rebate money is available, how many programs stack, and whether funding is open, based on published rebate amounts.",
        "url": "https://homepowerrebate.com/powerscore/",
        "creator": {"@type": "Organization", "name": "HomePowerRebate"},
        "variableMeasured": ["Overall PowerScore"] + [CAT_LABELS[c] + " PowerScore" for c in CATEGORIES],
        "temporalCoverage": "2026",
        "dateModified": DATA["generated"],
    }
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "PowerScore: See How Your City's Home Energy Rebates Rank",
        "description": f"We scored all {total_cities} cities HomePowerRebate covers across {total_regions} regions on rebate dollar value, program status, and stackability to build a 0-100 PowerScore leaderboard.",
        "author": {"@type": "Person", "name": "Sam Menard", "url": "https://homepowerrebate.com/about/"},
        "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
        "mainEntityOfPage": "https://homepowerrebate.com/powerscore/",
        "datePublished": "2026-08-23",
        "dateModified": DATA["generated"],
    }
    return (
        '<script type="application/ld+json">' + json.dumps(dataset) + "</script>\n"
        '<script type="application/ld+json">' + json.dumps(article) + "</script>"
    )


distinct_scores = len({round(r['overall'], 1) for r in rows})
data_date = DATA['generated']
cad = DATA.get('cad_to_usd', 0.73)
_ys = DATA.get("yardstick_usd", {})
yardstick_rows_html = "".join(f'<tr><td>{esc(CAT_LABELS[c])}</td><td>US${_ys.get(c, 0):,.0f} (about CA${_ys.get(c, 0) / cad:,.0f})</td></tr>' for c in CATEGORIES)
sort_options_html = '<option value="overall">PowerScore</option><option value="potential">Open rebate money</option>' + "".join(f'<option value="{c}">{esc(SHORT_LABELS[c])} score</option>' for c in CATEGORIES)
region_options_html = '<option value="all">All regions</option>' + "".join(f'<option value="{esc(reg)}">{esc(rs[0]["region_label"])}</option>' for reg, rs in sorted(BY_REGION.items(), key=lambda kv: kv[1][0]["region_label"]))
profile_key_html = "".join(f"<li>{esc(SHORT_LABELS[c])}</li>" for c in CATEGORIES)
jsonld_html = render_jsonld()
date_nice = __import__("datetime").date.fromisoformat(data_date).strftime("%B %-d, %Y")


PS_CSS = r""":root{--ink:#0a2a2e;--ink-soft:#1a3d42;--paper:#faf7f2;--paper-warm:#f5efe5;--teal:#0d4f5c;--teal-deep:#08363f;--amber:#d4751c;--amber-bright:#e88a2e;--green-money:#2d6a4f;--red-flag:#b04545;--rule:#e2d9ca;--sage:#6b8e7f;--muted:#4a5f62}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:'Inter Tight',sans-serif;line-height:1.6}
.ps{--gut:clamp(16px,3.2vw,56px)}
.ps .ps-wrap{max-width:1200px;margin:0 auto;padding:0 var(--gut)}
.ps .sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.ps h1,.ps h2,.ps h3{font-family:'Fraunces',Georgia,serif;color:var(--teal-deep);margin:0}
.ps .ps-sec{padding:clamp(48px,6vw,88px) 0}
.ps .ps-sec.warm{background:var(--paper-warm)}
.ps .ps-sec.white{background:#fff}
.ps .ps-kicker{margin:0 0 10px;font-size:13px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--amber)}
.ps .ps-h2{font-size:clamp(28px,3.2vw,44px);font-weight:600;line-height:1.08;letter-spacing:-.02em;max-width:22ch;text-wrap:balance}
.ps .ps-sec p.ps-intro{margin:14px 0 0;max-width:62ch;font-size:clamp(16px,1.3vw,18px);line-height:1.6;color:var(--muted)}
.ps .ps-head{margin-bottom:clamp(24px,3vw,40px)}

/* hero */
.ps .ps-hero{position:relative;overflow:hidden;color:#fff;padding:clamp(40px,6vw,96px) 0 clamp(40px,5vw,80px);
 background:radial-gradient(110% 130% at 100% 0%,rgba(232,138,46,.22) 0%,rgba(232,138,46,0) 50%),radial-gradient(90% 120% at 0% 100%,rgba(107,142,127,.28) 0%,rgba(107,142,127,0) 55%),var(--teal-deep)}
.ps .ps-hero-grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr);gap:clamp(28px,5vw,72px);align-items:center}
.ps .ps-hero .ps-kicker{color:#f5b566}
.ps .ps-hero h1{color:#fff;font-size:clamp(36px,5.4vw,76px);font-weight:600;line-height:1.02;letter-spacing:-.028em;max-width:15ch;text-wrap:balance}
.ps .ps-hero h1 em{font-style:normal;color:var(--amber-bright)}
.ps .ps-hero p.ps-lead{margin:20px 0 0;max-width:54ch;font-size:clamp(17px,1.5vw,20px);line-height:1.55;color:rgba(250,247,242,.88)}
.ps .ps-find-box{position:relative;margin-top:clamp(24px,3vw,36px);max-width:560px}
.ps .ps-find-box label{display:block;font-size:14px;font-weight:700;color:#f5b566;margin-bottom:8px}
.ps .ps-search{width:100%;min-height:60px;padding:0 20px 0 52px;border:0;border-radius:16px;font:inherit;font-size:18px;color:var(--ink);background:#fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22' fill='none' stroke='%230d4f5c' stroke-width='2.4' stroke-linecap='round'%3E%3Ccircle cx='9.5' cy='9.5' r='7'/%3E%3Cpath d='m15 15 5.5 5.5'/%3E%3C/svg%3E") no-repeat 18px 50%;box-shadow:0 20px 44px -18px rgba(0,0,0,.5)}
.ps .ps-search:focus{outline:3px solid var(--amber-bright);outline-offset:2px}
.ps .ps-list{position:absolute;z-index:20;left:0;right:0;top:calc(100% + 6px);margin:0;padding:6px;list-style:none;background:#fff;border-radius:14px;box-shadow:0 24px 48px -12px rgba(0,0,0,.35);max-height:340px;overflow:auto}
.ps .ps-list[hidden]{display:none}
.ps .ps-list li{display:flex;justify-content:space-between;gap:12px;padding:11px 14px;border-radius:10px;cursor:pointer;color:var(--ink);font-size:16px}
.ps .ps-list li small{color:var(--muted);font-size:14px}
.ps .ps-list li[aria-selected="true"],.ps .ps-list li:hover{background:var(--paper-warm)}
.ps .ps-list li b{font-family:'Fraunces',serif;color:var(--teal-deep)}
.ps .ps-hint{margin:10px 0 0;font-size:14px;color:rgba(250,247,242,.7)}
.ps .ps-hint button{font:inherit;color:#fff;background:none;border:0;padding:0;text-decoration:underline;text-underline-offset:3px;cursor:pointer}
.ps .ps-gap{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);border-radius:22px;padding:clamp(20px,2.4vw,30px)}
.ps .ps-gap h2{color:#fff;font-size:clamp(20px,1.8vw,24px);font-weight:600;line-height:1.2}
.ps .ps-gap p.ps-gap-sub{margin:6px 0 18px;font-size:14px;color:rgba(250,247,242,.72)}
.ps .ps-gap ol{list-style:none;margin:0;padding:0;display:grid;gap:10px}
.ps .ps-gap li{display:grid;grid-template-columns:minmax(0,9.5em) 1fr 2.2em;align-items:center;gap:12px;font-size:15px}
.ps .ps-gap-name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:rgba(250,247,242,.92)}
.ps .ps-gap-track{height:12px;border-radius:12px;background:rgba(255,255,255,.1);overflow:hidden}
.ps .ps-gap-track i{display:block;height:100%;border-radius:12px}
.ps .ps-gap-track i.hi{background:var(--amber-bright)}.ps .ps-gap-track i.lo{background:#8fb1a4}
.ps .ps-gap li b{font-family:'Fraunces',serif;font-size:20px;text-align:right}
.ps .ps-gap li.ps-gap-sep{display:block;height:14px}
.ps .ps-gap li.ps-gap-sep span{display:block;margin:6px 0 0;border-top:1px dashed rgba(255,255,255,.28)}
.ps .ps-gap-foot{margin:16px 0 0;font-size:13px;color:rgba(250,247,242,.6)}
.ps .ps-gap-foot a{color:#fff}

/* scorecard */
.ps .ps-card-sec{padding:clamp(28px,4vw,48px) 0 0}
.ps #your-score,.ps #ranking,.ps #regions{scroll-margin-top:88px}
.ps .ps-card-sec[hidden]{display:none}
.ps .ps-card{position:relative;display:grid;grid-template-columns:auto minmax(0,1fr);gap:clamp(20px,3vw,44px);background:#fff;border:1px solid var(--rule);border-radius:24px;padding:clamp(20px,3vw,40px);box-shadow:0 30px 60px -36px rgba(10,42,46,.4)}
.ps .ps-card-close{position:absolute;top:14px;right:14px;width:40px;height:40px;border-radius:50%;border:1px solid var(--rule);background:#fff;font-size:22px;line-height:1;color:var(--muted);cursor:pointer}
.ps .ps-card-left{display:flex;flex-direction:column;align-items:center;text-align:center;min-width:200px}
.ps .ps-ring{position:relative;width:176px;height:176px}
.ps .ps-ring svg{display:block;transform:rotate(-90deg)}
.ps .ps-ring .num{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.ps .ps-ring .num b{font-family:'Fraunces',serif;font-size:56px;font-weight:600;line-height:1;color:var(--teal-deep)}
.ps .ps-ring .num small{font-size:14px;font-weight:600;color:var(--muted)}
.ps .ps-band{margin-top:12px;display:inline-block;padding:5px 12px;border-radius:999px;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.06em}
.ps .ps-band.excellent{background:#e3f0e8;color:var(--green-money)}.ps .ps-band.solid{background:#e2eef0;color:var(--teal)}.ps .ps-band.limited{background:#fbeedd;color:#9a520f}.ps .ps-band.thin{background:#f8e5e2;color:var(--red-flag)}
.ps .ps-card h2{font-size:clamp(28px,3vw,40px);font-weight:600;line-height:1.05;padding-right:44px}
.ps .ps-card p.ps-card-reg{margin:4px 0 0;font-size:15px;color:var(--muted)}
.ps .ps-facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:20px 0}
.ps .ps-facts div{background:var(--paper);border-radius:14px;padding:12px 14px}
.ps .ps-facts b{display:block;font-family:'Fraunces',serif;font-size:clamp(20px,2vw,26px);line-height:1.1;color:var(--teal-deep)}
.ps .ps-facts span{font-size:13px;color:var(--muted)}
.ps .ps-cats{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:4px 28px}
.ps .ps-cats li{display:grid;grid-template-columns:7.5em 1fr 2em;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #efe8db;font-size:15px}
.ps .ps-cats li .lab{font-weight:600}
.ps .ps-cats li .amt{grid-column:2/4;font-size:13px;color:var(--muted);margin-top:-6px}
.ps .ps-cats li b{text-align:right;font-family:'Fraunces',serif;font-size:17px}
.ps .ps-cats .st{display:inline-block;margin-left:6px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;padding:1px 7px;border-radius:999px}
.ps .ps-cats .st.l{background:#fbeedd;color:#9a520f}.ps .ps-cats .st.c{background:#f8e5e2;color:var(--red-flag)}
.ps .ps-card-actions{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:20px}
.ps .ps-btn{display:inline-flex;align-items:center;min-height:48px;padding:0 22px;border-radius:999px;background:var(--amber);color:#fff;font-weight:700;font-size:16px;text-decoration:none;border:0;cursor:pointer;font-family:inherit}
.ps .ps-btn:hover{background:var(--amber-bright)}
.ps .ps-btn.ghost{background:transparent;color:var(--teal-deep);border:1.5px solid var(--rule)}
.ps .ps-btn.ghost:hover{border-color:var(--teal)}
.ps .ps-note{margin:12px 0 0;font-size:13px;color:var(--muted)}

/* bars */
.ps .ps-bar{display:block;height:8px;border-radius:8px;background:#ece4d6;overflow:hidden}
.ps .ps-bar i{display:block;height:100%;border-radius:8px;background:var(--teal)}

/* findings */
.ps .ps-finds{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:clamp(12px,1.6vw,20px)}
.ps .ps-find{background:#fff;border:1px solid var(--rule);border-radius:20px;padding:clamp(20px,2.2vw,28px)}
.ps .ps-sec p.ps-find-k{margin:0;font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--sage)}
.ps .ps-sec p.ps-find-n{margin:8px 0 10px;font-family:'Fraunces',serif;font-size:clamp(34px,3.6vw,52px);font-weight:600;line-height:1;letter-spacing:-.02em;color:var(--amber)}
.ps .ps-sec p.ps-find-t{margin:0;font-size:16px;line-height:1.55;color:var(--ink-soft)}

/* strip chart */
.ps .ps-strip{display:grid;gap:2px}
.ps .ps-strip-axis{display:grid;grid-template-columns:240px 1fr 48px;gap:18px;font-size:12px;color:var(--muted);padding:0 12px 6px}
.ps .ps-strip-axis span:nth-child(2){display:flex;justify-content:space-between}
.ps .ps-strip-row{display:grid;grid-template-columns:240px 1fr 48px;gap:18px;align-items:center;width:100%;padding:10px 12px;border:0;border-radius:14px;background:transparent;font:inherit;color:inherit;text-align:left;cursor:pointer}
.ps .ps-strip-row:hover,.ps .ps-strip-row:focus-visible{background:var(--paper-warm)}
.ps .ps-strip-name b{display:block;font-size:16px;color:var(--teal-deep)}
.ps .ps-strip-name small{font-size:13px;color:var(--muted)}
.ps .ps-strip-track{position:relative;height:28px;border-radius:8px;background:repeating-linear-gradient(90deg,#ece4d6 0 1px,transparent 1px 25%) ,#f6f1e8}
.ps .ps-range{position:absolute;top:50%;height:6px;margin-top:-3px;border-radius:6px;background:rgba(13,79,92,.18)}
.ps .ps-dot{position:absolute;top:50%;width:12px;height:12px;margin:-6px 0 0 -6px;border-radius:50%;background:rgba(13,79,92,.45);border:1.5px solid #fff}
.ps .ps-avg{position:absolute;top:2px;bottom:2px;width:4px;margin-left:-2px;border-radius:4px;background:var(--amber)}
.ps .ps-strip-num{font-family:'Fraunces',serif;font-size:24px;font-weight:600;color:var(--teal-deep);text-align:right}
.ps .ps-legend{display:flex;flex-wrap:wrap;gap:8px 20px;margin:16px 12px 0;font-size:14px;color:var(--muted)}
.ps .ps-legend span{display:inline-flex;align-items:center;gap:8px}
.ps .ps-legend .k-dot{width:12px;height:12px;border-radius:50%;background:rgba(13,79,92,.45)}
.ps .ps-legend .k-avg{width:4px;height:16px;border-radius:4px;background:var(--amber)}
.ps .ps-legend .k-rng{width:22px;height:6px;border-radius:6px;background:rgba(13,79,92,.18)}
.ps .conf{display:inline-block;margin-top:4px;font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;padding:2px 7px;border-radius:999px;background:#fdf2f0;color:var(--red-flag);border:1px solid #efc9c4}

/* heatmap */
.ps .ps-heat-wrap{overflow-x:auto;border-radius:18px;border:1px solid var(--rule);background:#fff}
.ps .ps-heat{width:100%;border-collapse:separate;border-spacing:3px;font-size:15px;min-width:760px}
.ps .ps-heat th{font-weight:600;font-size:13px;color:var(--muted);padding:10px 6px;text-align:center;vertical-align:bottom;line-height:1.25}
.ps .ps-heat tbody th{vertical-align:middle;text-align:left;font-size:15px;color:var(--teal-deep);white-space:nowrap;padding:0 12px;position:sticky;left:0;background:#fff;z-index:1}
.ps .ps-heat td{text-align:center;padding:12px 4px;border-radius:8px;font-variant-numeric:tabular-nums;font-weight:600;color:var(--ink);background:color-mix(in srgb,var(--teal) var(--h),#f6f1e8)}
.ps .ps-heat td.dk{color:#fff}
.ps .ps-heat td.ps-heat-all{background:var(--paper-warm);font-family:'Fraunces',serif;font-size:18px;color:var(--teal-deep)}
.ps .ps-heat-key{display:flex;align-items:center;gap:10px;margin:14px 0 0;font-size:13px;color:var(--muted)}
.ps .ps-heat-key i{display:block;width:160px;height:10px;border-radius:10px;background:linear-gradient(90deg,#f6f1e8,var(--teal))}

/* champions */
.ps .ps-chs{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:clamp(12px,1.6vw,18px)}
.ps .ps-ch{background:#fff;border:1px solid var(--rule);border-radius:20px;padding:20px 20px 12px}
.ps .ps-ch h3{font-family:'Inter Tight',sans-serif;font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--sage)}
.ps .ps-sec p.ps-ch-amt{margin:6px 0 0;font-family:'Fraunces',serif;font-size:26px;font-weight:600;line-height:1.1;color:var(--amber)}
.ps .ps-sec p.ps-ch-lead{margin:2px 0 12px;font-size:14px;color:var(--muted)}
.ps .ps-ch ol{list-style:none;margin:0;padding:0;counter-reset:c}
.ps .ps-ch li{display:grid;grid-template-columns:minmax(0,1fr) 64px 2em;gap:10px;align-items:center;padding:9px 0;border-top:1px solid #efe8db;font-size:15px}
.ps .ps-ch-who a{display:block;font-weight:600;color:var(--teal-deep);text-decoration:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ps .ps-ch-who a:hover{text-decoration:underline}
.ps .ps-ch-who small{display:block;font-size:13px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ps .ps-ch li b{text-align:right;font-family:'Fraunces',serif;font-size:17px;color:var(--teal-deep)}

/* ranking table */
.ps .ps-controls{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr) minmax(0,1fr);gap:10px;margin-bottom:12px}
.ps .ps-controls input,.ps .ps-controls select{width:100%;min-height:50px;padding:0 14px;border:1px solid var(--rule);border-radius:12px;font:inherit;font-size:16px;background:#fff;color:var(--ink)}
.ps .ps-count{font-size:14px;color:var(--muted);margin:0 0 10px}
.ps .ps-table-wrap{border:1px solid var(--rule);border-radius:18px;background:#fff;overflow:hidden}
.ps .ps-table{width:100%;border-collapse:collapse;font-size:15px}
.ps .ps-table thead th{text-align:left;font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);padding:14px 16px;background:var(--paper);border-bottom:1px solid var(--rule)}
.ps .ps-table td{padding:12px 16px;border-bottom:1px solid #efe8db;vertical-align:middle}
.ps .ps-table tbody tr.hide{display:none}
.ps .ps-table tbody tr.on td{background:#fffaf2}
.ps .ps-rk{width:56px;font-weight:700;color:var(--sage);font-variant-numeric:tabular-nums}
.ps .ps-city a{font-weight:700;color:var(--teal-deep);text-decoration:none;font-size:16px}
.ps .ps-city a:hover{text-decoration:underline}
.ps .ps-city small{display:block;font-size:13px;color:var(--muted)}
.ps .ps-sc{width:190px}
.ps .ps-sc{white-space:nowrap}
.ps .ps-sc b{display:inline-block;width:2em;font-family:'Fraunces',serif;font-size:20px;color:var(--teal-deep);vertical-align:middle}
.ps .ps-sc .ps-bar{display:inline-block;width:110px;vertical-align:middle}
.ps .ps-prof{display:inline-flex;align-items:flex-end;gap:3px;height:28px;vertical-align:middle}
.ps .ps-prof i{display:block;width:7px;border-radius:2px 2px 0 0;background:var(--teal)}
.ps .ps-prof i:nth-child(odd){background:#3f7c87}
.ps .ps-pot{font-weight:700;color:var(--green-money);white-space:nowrap}
.ps .ps-pot small{display:block;font-weight:500;font-size:13px;color:var(--muted)}
.ps .ps-more{width:100px;text-align:right}
.ps .ps-open{font:inherit;font-size:14px;font-weight:600;color:var(--teal);background:none;border:1px solid var(--rule);border-radius:999px;padding:7px 14px;cursor:pointer}
.ps .ps-open[aria-expanded="true"]{background:var(--teal-deep);border-color:var(--teal-deep);color:#fff}
.ps .ps-table tr.ps-detail td{background:var(--paper);padding:18px}
.ps .ps-table tr.ps-detail .ps-card{box-shadow:none}
.ps .ps-profile-key{display:flex;flex-wrap:wrap;gap:4px 14px;margin:12px 4px 0;padding:0;list-style:none;font-size:13px;color:var(--muted)}
.ps .ps-profile-key li:first-child::before{content:"Bars, left to right: ";font-weight:600}
.ps .ps-more-btn{display:block;margin:20px auto 0}

/* method */
.ps .ps-method{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:clamp(24px,4vw,56px);align-items:start}
.ps .ps-formula{display:flex;height:56px;border-radius:14px;overflow:hidden;margin:20px 0 18px;font-weight:700;font-size:15px;color:#fff}
.ps .ps-formula span{display:flex;align-items:center;justify-content:center}
.ps .ps-formula .f1{flex:60;background:var(--teal-deep)}.ps .ps-formula .f2{flex:25;background:var(--teal)}.ps .ps-formula .f3{flex:15;background:var(--amber)}
.ps .ps-parts{list-style:none;margin:0;padding:0;display:grid;gap:14px}
.ps .ps-parts li{font-size:16px;line-height:1.55;color:var(--ink-soft);padding-left:18px;border-left:4px solid var(--teal-deep)}
.ps .ps-parts li:nth-child(2){border-color:var(--teal)}.ps .ps-parts li:nth-child(3){border-color:var(--amber)}
.ps .ps-sec p.ps-body{margin:14px 0 0;font-size:16px;line-height:1.6;color:var(--ink-soft)}
.ps details.ps-fold{background:#fff;border:1px solid var(--rule);border-radius:16px;padding:0 20px;margin-bottom:12px}
.ps details.ps-fold summary{cursor:pointer;padding:16px 0;font-weight:700;font-size:16px;color:var(--teal-deep);list-style:none;display:flex;justify-content:space-between;gap:12px}
.ps details.ps-fold summary::-webkit-details-marker{display:none}
.ps details.ps-fold summary::after{content:"+";font-size:22px;line-height:1;color:var(--amber)}
.ps details.ps-fold[open] summary::after{content:"\2013"}
.ps details.ps-fold .in{padding:0 0 18px}
.ps details.ps-fold ul{margin:0 0 14px 18px;padding:0}
.ps details.ps-fold li{margin-bottom:8px;font-size:15px;color:var(--ink-soft)}
.ps details.ps-fold p{font-size:15px;color:var(--ink-soft)}
.ps .ps-mini{width:100%;border-collapse:collapse;font-size:14px}
.ps .ps-mini th,.ps .ps-mini td{text-align:left;padding:8px 10px;border-bottom:1px solid #efe8db;vertical-align:top}
.ps .ps-mini th{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.ps .ps-scroll{overflow-x:auto}
.ps .lvl.low{color:var(--red-flag);font-weight:600}.ps .lvl.mid{color:#8a5a00}.ps .lvl.high{color:var(--green-money);font-weight:600}
.ps .conf-no{color:var(--red-flag);font-weight:700}

/* media + comparisons */
.ps .ps-press{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);gap:clamp(16px,2vw,24px)}
.ps .ps-press-box{border-radius:22px;padding:clamp(22px,2.6vw,34px);background:var(--teal-deep);color:#fff}
.ps .ps-press-box h2{color:#fff;font-size:clamp(24px,2.4vw,32px);font-weight:600}
.ps .ps-sec .ps-press-box p{margin:12px 0 0;font-size:16px;line-height:1.6;color:rgba(250,247,242,.86)}
.ps .ps-press-box a{color:#f5b566}
.ps .ps-cite{margin:16px 0 0;padding:14px 16px;border-radius:12px;background:rgba(255,255,255,.08);font-size:15px;line-height:1.5;color:#fff}
.ps .ps-links{border-radius:22px;padding:clamp(22px,2.6vw,34px);background:#fff;border:1px solid var(--rule)}
.ps .ps-links h2{font-size:clamp(22px,2vw,26px);font-weight:600}
.ps .ps-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.ps .ps-chips a{display:inline-flex;align-items:center;min-height:40px;padding:0 14px;border-radius:999px;border:1px solid var(--rule);font-size:14px;font-weight:600;color:var(--teal-deep);text-decoration:none}
.ps .ps-chips a:hover{border-color:var(--amber);color:var(--amber)}

@media (max-width:980px){
 .ps .ps-hero-grid,.ps .ps-method,.ps .ps-press{grid-template-columns:1fr}
 .ps .ps-finds{grid-template-columns:1fr}
 .ps .ps-controls{grid-template-columns:1fr 1fr}.ps .ps-controls input{grid-column:1/-1}
}
@media (max-width:760px){
 .ps .ps-card{grid-template-columns:1fr}
 .ps .ps-card-left{flex-direction:row;gap:16px;text-align:left;min-width:0}
 .ps .ps-ring{width:120px;height:120px}.ps .ps-ring svg{width:120px;height:120px}.ps .ps-ring .num b{font-size:40px}
 .ps .ps-cats{grid-template-columns:1fr}
 .ps .ps-facts{grid-template-columns:1fr 1fr;gap:8px}.ps .ps-facts div{padding:10px}.ps .ps-facts div:nth-child(3){grid-column:1/-1}
 .ps .ps-strip-axis{display:none}
 .ps .ps-heat{min-width:600px;font-size:13px;border-spacing:2px}.ps .ps-heat td{padding:9px 2px}.ps .ps-heat th{font-size:12px;padding:8px 2px}.ps .ps-heat tbody th{font-size:13px;padding:0 8px}.ps .ps-heat td.ps-heat-all{font-size:15px}
 .ps .ps-strip-row{grid-template-columns:1fr 2.4em;gap:6px 12px;padding:10px 6px}
 .ps .ps-strip-name{grid-column:1;grid-row:1}.ps .ps-strip-num{grid-column:2;grid-row:1/3;align-self:center}
 .ps .ps-strip-track{grid-column:1;grid-row:2;height:22px}
 .ps .ps-table thead{display:none}
 .ps .ps-table,.ps .ps-table tbody{display:block}
 .ps .ps-table tbody tr:not(.ps-detail){display:grid;grid-template-columns:34px minmax(0,1fr) auto auto;gap:6px 10px;align-items:center;padding:12px 12px;border-bottom:1px solid #efe8db}
 .ps .ps-table tbody tr.hide{display:none}
 .ps .ps-table tr.ps-detail{display:block}.ps .ps-table tr.ps-detail td{display:block}
 .ps .ps-table td{border:0;padding:0}
 .ps .ps-rk{grid-column:1;grid-row:1/3;width:auto;font-size:14px}
 .ps .ps-city{grid-column:2/4;grid-row:1}
 .ps .ps-sc{grid-column:4;grid-row:1;width:auto;text-align:right}.ps .ps-sc .ps-bar{display:none}
 .ps .ps-pf{grid-column:2;grid-row:2}
 .ps .ps-pot{grid-column:3;grid-row:2;text-align:right;font-size:14px}.ps .ps-pot small{display:none}
 .ps .ps-more{grid-column:4;grid-row:2;width:auto}
 .ps .ps-open{padding:5px 11px;font-size:13px}
 .ps .ps-table tbody tr.on{background:#fffaf2}.ps .ps-table tbody tr.on td{background:none}
 .ps .ps-table tr.ps-detail td{padding:10px}
}
@media (max-width:420px){
 .ps .ps-gap li{grid-template-columns:minmax(0,7.5em) 1fr 2em;gap:8px;font-size:14px}
 .ps .ps-facts b{font-size:18px}
}
"""


PS_JS = r"""(function(){
var D=window.PS_ROWS,CATS=window.PS_CATS,BY={};D.forEach(function(r){BY[r.k]=r;});
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function band(s){return s>=75?'excellent':s>=50?'solid':s>=25?'limited':'thin';}
function fmt(n){return Math.round(n).toLocaleString('en-US');}
function card(r,inTable){
 var C=2*Math.PI*78,off=C*(1-Math.min(100,r.s)/100),cats='';
 r.c.forEach(function(v,i){
  var st=v[2]==='l'?'<span class="st l">Limited</span>':v[2]==='c'?'<span class="st c">Closed</span>':'';
  var amt=v[1]>0?'up to '+r.cur+fmt(v[1]):'No open rebate found';
  cats+='<li><span class="lab">'+CATS[i]+st+'</span><span class="ps-bar"><i style="width:'+Math.max(2,v[0])+'%"></i></span><b>'+v[0]+'</b><span class="amt">'+amt+'</span></li>';
 });
 return '<div class="ps-card">'+(inTable?'':'<button type="button" class="ps-card-close" aria-label="Close">&times;</button>')+
  '<div class="ps-card-left"><div class="ps-ring"><svg width="176" height="176" viewBox="0 0 176 176"><circle cx="88" cy="88" r="78" fill="none" stroke="#ece4d6" stroke-width="14"/><circle cx="88" cy="88" r="78" fill="none" stroke="#d4751c" stroke-width="14" stroke-linecap="round" stroke-dasharray="'+C.toFixed(1)+'" stroke-dashoffset="'+off.toFixed(1)+'"/></svg><div class="num"><b>'+Math.round(r.s)+'</b><small>out of 100</small></div></div>'+
  '<div><span class="ps-band '+band(r.s)+'">'+band(r.s)+'</span></div></div>'+
  '<div><h2>'+esc(r.n)+'</h2><p class="ps-card-reg">'+esc(r.r)+'</p>'+
  '<div class="ps-facts"><div><b>'+(r.t?'T-':'#')+r.rk+'</b><span>of '+D.length+' cities</span></div><div><b>'+(r.rt?'T-':'#')+r.rr+'</b><span>of '+r.rn+' in '+esc(r.r)+'</span></div><div><b>US$'+fmt(r.p)+'</b><span>top open rebates, '+r.o+' of 8 upgrades</span></div></div>'+
  '<ul class="ps-cats">'+cats+'</ul>'+
  '<div class="ps-card-actions"><a class="ps-btn" href="'+esc(r.u)+'">See '+esc(r.n)+' rebates</a>'+(inTable?'':'<button type="button" class="ps-btn ghost ps-copy">Copy link to this score</button>')+'</div>'+
  '<p class="ps-note">Open rebate money adds the top open rebate in each upgrade. Most homes will not qualify for all of them.'+(r.e?' Typical yearly energy bill in this area (estimate, not part of the score): '+esc(r.e)+'.':'')+'</p></div></div>';
}
var sec=document.getElementById('your-score'),slot=document.getElementById('ps-card-slot');
function show(key,scroll){var r=BY[key];if(!r)return;slot.innerHTML=card(r,false);sec.hidden=false;
 try{history.replaceState(null,'','?city='+encodeURIComponent(key)+'#your-score');}catch(e){}
 if(scroll)sec.scrollIntoView({behavior:'smooth',block:'start'});
 if(window.gtag)gtag('event','powerscore_lookup',{city:key});}
slot.addEventListener('click',function(e){
 if(e.target.closest('.ps-card-close')){sec.hidden=true;try{history.replaceState(null,'',location.pathname);}catch(x){}}
 var b=e.target.closest('.ps-copy');if(b){var u=location.href;(navigator.clipboard?navigator.clipboard.writeText(u):Promise.reject()).then(function(){b.textContent='Link copied';},function(){b.textContent=u;});}
});
/* search box */
var inp=document.getElementById('ps-search'),list=document.getElementById('ps-list'),act=-1,hits=[];
function norm(s){return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9 ]/g,'');}
function render(){var q=norm(inp.value.trim());if(!q){list.hidden=true;inp.setAttribute('aria-expanded','false');return;}
 hits=D.filter(function(r){return norm(r.n+' '+r.r).indexOf(q)>-1;}).sort(function(a,b){return (norm(a.n).indexOf(q)===0?0:1)-(norm(b.n).indexOf(q)===0?0:1);}).slice(0,8);
 act=hits.length?0:-1;
 list.innerHTML=hits.length?hits.map(function(r,i){return '<li role="option" id="ps-opt-'+i+'" data-k="'+esc(r.k)+'" aria-selected="'+(i===act)+'"><span>'+esc(r.n)+' <small>'+esc(r.r)+'</small></span><b>'+Math.round(r.s)+'</b></li>';}).join(''):'<li aria-disabled="true"><span>No match yet. We cover '+D.length+' cities.</span></li>';
 list.hidden=false;inp.setAttribute('aria-expanded','true');}
function pick(k){inp.value=BY[k].n+', '+BY[k].r;list.hidden=true;inp.setAttribute('aria-expanded','false');show(k,true);}
inp.addEventListener('input',render);
inp.addEventListener('keydown',function(e){
 if(list.hidden)return;
 if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();act=(act+(e.key==='ArrowDown'?1:-1)+hits.length)%hits.length;
  [].forEach.call(list.children,function(li,i){li.setAttribute('aria-selected',i===act);});inp.setAttribute('aria-activedescendant','ps-opt-'+act);}
 else if(e.key==='Enter'){e.preventDefault();if(hits[act])pick(hits[act].k);}
 else if(e.key==='Escape'){list.hidden=true;}
});
list.addEventListener('mousedown',function(e){var li=e.target.closest('li[data-k]');if(li){e.preventDefault();pick(li.dataset.k);}});
inp.addEventListener('blur',function(){setTimeout(function(){list.hidden=true;},120);});
[].forEach.call(document.querySelectorAll('[data-try]'),function(b){b.addEventListener('click',function(){pick(b.dataset.try);});});
/* full ranking */
var tbody=document.querySelector('#ps-table tbody'),rowsEl=[].slice.call(tbody.querySelectorAll('tr[data-key]')),
 st={region:'all',q:'',sort:'overall',all:false},LIMIT=20,count=document.getElementById('ps-count'),more=document.getElementById('ps-more'),
 regSel=document.getElementById('ps-region');
function closeDetails(){[].forEach.call(tbody.querySelectorAll('tr.ps-detail'),function(d){d.remove();});
 [].forEach.call(tbody.querySelectorAll('.ps-open[aria-expanded="true"]'),function(b){b.setAttribute('aria-expanded','false');b.textContent='Details';b.closest('tr').classList.remove('on');});}
function apply(){closeDetails();
 var vis=rowsEl.filter(function(r){return (st.region==='all'||r.dataset.region===st.region)&&(!st.q||r.dataset.name.indexOf(st.q)>-1);});
 var k=st.sort==='overall'?'data-overall':st.sort==='potential'?'data-potential':'data-c-'+st.sort;
 vis.sort(function(a,b){return (parseFloat(b.getAttribute(k))-parseFloat(a.getAttribute(k)))||(a.dataset.order-b.dataset.order);});
 var lim=(st.all||st.q||st.region!=='all')?vis.length:LIMIT;
 rowsEl.forEach(function(r){r.classList.add('hide');});
 vis.forEach(function(r,i){tbody.appendChild(r);r.classList.toggle('hide',i>=lim);});
 count.textContent='Showing '+Math.min(lim,vis.length)+' of '+vis.length+' cities.';
 more.style.display=vis.length>lim?'':'none';}
tbody.addEventListener('click',function(e){var b=e.target.closest('.ps-open');if(!b)return;var tr=b.closest('tr'),open=b.getAttribute('aria-expanded')==='true';
 closeDetails();if(open)return;
 var d=document.createElement('tr');d.className='ps-detail';d.innerHTML='<td colspan="6">'+card(BY[tr.dataset.key],true)+'</td>';tr.after(d);
 b.setAttribute('aria-expanded','true');b.textContent='Close';tr.classList.add('on');});
document.getElementById('ps-filter').addEventListener('input',function(e){st.q=e.target.value.trim().toLowerCase();apply();});
regSel.addEventListener('change',function(){st.region=regSel.value;apply();});
document.getElementById('ps-sort').addEventListener('change',function(e){st.sort=e.target.value;apply();});
more.addEventListener('click',function(){st.all=true;apply();});
[].forEach.call(document.querySelectorAll('.ps-strip-row'),function(b){b.addEventListener('click',function(){
 st.region=b.dataset.region;regSel.value=st.region;apply();document.getElementById('ranking').scrollIntoView({behavior:'smooth',block:'start'});});});
apply();
var q=new URLSearchParams(location.search).get('city');if(q&&BY[q])show(q,true);
})();
"""

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PowerScore: City Rebate Rankings 2026 | HomePowerRebate</title>

<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-W33G4TGRHD');
</script>

<meta name="description" content="We scored {total_cities} cities in {total_regions} provinces and states on home energy rebates, 0 to 100. {esc(TOP_LABEL)} cities average {REGION_AVG[TOP_REG]:.0f}; {esc(BOT_LABEL)} averages {REGION_AVG[BOT_REG]:.0f}. Find your city's score.">
<link rel="canonical" href="https://homepowerrebate.com/powerscore/">
<meta property="og:title" content="PowerScore: City Rebate Rankings 2026 | HomePowerRebate">
<meta property="og:description" content="Where you live decides how much rebate help you get. {total_cities} cities scored 0 to 100. Find yours.">
<meta property="og:type" content="article">
<meta property="og:image" content="https://homepowerrebate.com/og-image.svg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:type" content="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">

{jsonld_html}

<style>
{PS_CSS}
</style>
</head>
<body>
'''

MAIN = f'''
<div class="ps">
<header class="ps-hero">
  <div class="ps-wrap ps-hero-grid">
    <div>
      <p class="ps-kicker">PowerScore &middot; updated {date_nice}</p>
      <h1>Where you live decides your <em>rebate</em>.</h1>
      <p class="ps-lead">We scored every city we cover on the same 0 to 100 scale: how much rebate money there is, whether it is open today, and how many programs stack. The best region scores {GAP_RATIO:.1f} times higher than the lowest.</p>
      <div class="ps-find-box" role="search">
        <label for="ps-search">Find your city's score</label>
        <input id="ps-search" class="ps-search" type="text" placeholder="Type your city" autocomplete="off" role="combobox" aria-expanded="false" aria-controls="ps-list" aria-autocomplete="list">
        <ul id="ps-list" class="ps-list" role="listbox" hidden></ul>
        <p class="ps-hint">Try <button type="button" data-try="{esc(rows[0]["region"])}/{esc(rows[0]["slug"])}">{esc(rows[0]["label"])}</button>, <button type="button" data-try="{esc(TIGHT[0]["region"])}/{esc(TIGHT[0]["slug"])}">{esc(TIGHT[0]["label"])}</button> or <button type="button" data-try="{esc(BY_REGION[BOT_REG][0]["region"])}/{esc(BY_REGION[BOT_REG][0]["slug"])}">{esc(BY_REGION[BOT_REG][0]["label"])}</button>.</p>
      </div>
    </div>
    <aside class="ps-gap" aria-labelledby="ps-gap-h">
      <h2 id="ps-gap-h">The rebate gap</h2>
      <p class="ps-gap-sub">Average PowerScore, top 3 and bottom 3 of {total_regions} regions</p>
      <ol>
{render_gap()}
      </ol>
      <p class="ps-gap-foot"><a href="#regions">See all {total_regions} regions</a></p>
    </aside>
  </div>
</header>

<section class="ps-card-sec" id="your-score" hidden>
  <div class="ps-wrap" id="ps-card-slot" aria-live="polite"></div>
</section>
<script>(function(){{var s=document.getElementById('your-score');if(new URLSearchParams(location.search).get('city'))s.hidden=false;}})();</script>

<section class="ps-sec">
  <div class="ps-wrap">
    <div class="ps-head">
      <p class="ps-kicker">What the numbers show</p>
      <h2 class="ps-h2">Three things we learned scoring {total_cities} cities</h2>
    </div>
    <div class="ps-finds">
{render_findings()}
    </div>
  </div>
</section>

<section class="ps-sec white" id="regions">
  <div class="ps-wrap">
    <div class="ps-head">
      <p class="ps-kicker">Every region, every city</p>
      <h2 class="ps-h2">Your province or state sets the bar</h2>
      <p class="ps-intro">Each dot is one city. Most dots in a region sit on top of each other, because the biggest rebates come from province-wide or state-wide programs. Tap a region to see its cities in the full ranking.</p>
    </div>
    <div class="ps-strip">
      <div class="ps-strip-axis" aria-hidden="true"><span></span><span><i>0</i><i>25</i><i>50</i><i>75</i><i>100</i></span><span>Avg</span></div>
{render_strip()}
    </div>
    <div class="ps-legend"><span><i class="k-dot"></i>One city</span><span><i class="k-avg"></i>Region average</span><span><i class="k-rng"></i>Lowest to highest city</span></div>
  </div>
</section>

<section class="ps-sec">
  <div class="ps-wrap">
    <div class="ps-head">
      <p class="ps-kicker">Strengths and gaps</p>
      <h2 class="ps-h2">What each region does best</h2>
      <p class="ps-intro">Average score for each upgrade, out of 100. Darker means more rebate help. Scroll sideways on a phone.</p>
    </div>
    <div class="ps-heat-wrap"><table class="ps-heat">{render_heatmap()}</table></div>
    <p class="ps-heat-key">0 <i></i> 100</p>
  </div>
</section>

<section class="ps-sec warm">
  <div class="ps-wrap">
    <div class="ps-head">
      <p class="ps-kicker">Upgrade by upgrade</p>
      <h2 class="ps-h2">The best places for each upgrade</h2>
      <p class="ps-intro">The top five spots for each upgrade. Cities that tie with the same programs are grouped together. Amounts are the largest single rebate we list, in local dollars.</p>
    </div>
    <div class="ps-chs">
{render_champions()}
    </div>
  </div>
</section>

<section class="ps-sec white">
  <div class="ps-wrap">
    <div class="ps-head">
      <p class="ps-kicker">Full ranking</p>
      <h2 class="ps-h2" id="ranking">All {total_cities} cities, ranked</h2>
      <p class="ps-intro">Cities with the same score share a rank (shown as T-). Tap Details for the upgrade-by-upgrade breakdown.</p>
    </div>
    <div class="ps-controls">
      <input type="search" id="ps-filter" placeholder="Filter by city name" aria-label="Filter the ranking by city name">
      <select id="ps-region" aria-label="Show one region">{region_options_html}</select>
      <select id="ps-sort" aria-label="Sort the ranking by">{sort_options_html}</select>
    </div>
    <p class="ps-count" id="ps-count" aria-live="polite"></p>
    <div class="ps-table-wrap">
      <table class="ps-table" id="ps-table">
        <thead><tr><th>Rank</th><th>City</th><th>PowerScore</th><th>By upgrade</th><th>Open rebates</th><th><span class="sr">Details</span></th></tr></thead>
        <tbody>
{render_rows()}
        </tbody>
      </table>
    </div>
    <ul class="ps-profile-key">{profile_key_html}</ul>
    <button type="button" id="ps-more" class="ps-btn ghost ps-more-btn">Show all {total_cities} cities</button>
  </div>
</section>

<section class="ps-sec" id="method">
  <div class="ps-wrap ps-method">
    <div>
      <p class="ps-kicker">Method</p>
      <h2 class="ps-h2">How PowerScore works</h2>
      <p class="ps-body">Each city gets a score from 0 to 100 for each of 8 upgrades. The overall PowerScore is the plain average of those 8. Every number comes from the rebate amounts on our own city pages, which we check against official program pages.</p>
      <div class="ps-formula" aria-hidden="true"><span class="f1">60% money</span><span class="f2">25% open</span><span class="f3">15%</span></div>
      <ul class="ps-parts">
        <li><b>60% Money.</b> The top rebate for that upgrade, in US dollars, compared with a common yardstick: what the best-funded tenth of cities offer. Matching the yardstick earns full marks.</li>
        <li><b>25% Open today.</b> Open programs get full credit. Funding limited or unclear programs get half. Closed or missing programs get zero.</li>
        <li><b>15% Stacking.</b> How many separate programs apply (federal, provincial or state, utility, city). More layers score higher, up to four.</li>
      </ul>
    </div>
    <div>
      <details class="ps-fold" id="reliability">
        <summary>How reliable is this ranking?</summary>
        <div class="in">
          <ul>
            <li><b>One yardstick for every city.</b> A city's money score compares its top rebate with what the best-funded tenth of cities offer, not with the best city in its own province or state.</li>
            <li><b>Currency is approximate.</b> Canadian amounts are converted at {cad} US dollars per Canadian dollar, only to put both countries on one scale.</li>
            <li><b>Open rebate money is not a promise.</b> It adds the top open rebate in each upgrade. Most homes will not qualify for all of them, and some programs cannot be combined.</li>
            <li><b>Ties are real.</b> Only {distinct_scores} different overall scores exist across {total_cities} cities, because most rebate programs cover a whole province or state.</li>
            <li><b>Not every region has been verified.</b> Regions marked "Not yet" ({unverified}) have not had each program checked against its official page.</li>
            <li><b>Data last rebuilt {date_nice}.</b> Amounts change. The <a href="/rebate-tracker/">rebate tracker</a> lists what has ended or moved.</li>
          </ul>
          <div class="ps-scroll"><table class="ps-mini">
            <thead><tr><th>Region</th><th>Cities</th><th>Facts verified</th><th>Cells with a $ amount</th><th>Cities scoring alike</th><th>How to read it</th></tr></thead>
            <tbody>{reliability_rows_html}</tbody>
          </table></div>
        </div>
      </details>
      <details class="ps-fold">
        <summary>Full-score yardstick for each upgrade</summary>
        <div class="in"><table class="ps-mini"><thead><tr><th>Upgrade</th><th>Earns a full money score at</th></tr></thead><tbody>{yardstick_rows_html}</tbody></table></div>
      </details>
      <details class="ps-fold">
        <summary>About the energy bill estimate</summary>
        <div class="in"><p>The city breakdown shows an estimated yearly electricity and heating fuel cost for a 2,500 sq ft home, based on utility rate schedules and typical regional usage. It is not a quoted bill and plays no part in the PowerScore. Nova Scotia and Massachusetts show a range because many homes there heat with oil, which costs more. Figures marked with an asterisk (*) use a neighbouring utility's rates where we could not find a local one.</p></div>
      </details>
    </div>
  </div>
</section>

<section class="ps-sec white">
  <div class="ps-wrap ps-press">
    <div class="ps-press-box">
      <p class="ps-kicker" style="color:#f5b566">For reporters and researchers</p>
      <h2>Using PowerScore in a story?</h2>
      <p>PowerScore is an independent ranking of home energy rebates across {total_cities} cities in Canada and the US, rebuilt each time our city pages change. Please link to this page when you cite it.</p>
      <p class="ps-cite">HomePowerRebate PowerScore, data as of {date_nice}. homepowerrebate.com/powerscore</p>
      <p>Questions about the data or the method? Email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a>. Read <a href="/blog/powerscore-how-we-rank-every-city/">how we rank every city</a>.</p>
    </div>
    <div class="ps-links">
      <h2>Head to head</h2>
      <p class="ps-body">Side-by-side comparisons of two cities, upgrade by upgrade.</p>
      <div class="ps-chips">{render_compare_links()}</div>
    </div>
  </div>
</section>
</div>
'''

page += f'''
<!-- ============================== NAV (canonical, from _partials/nav-footer.html) ============================== -->
<nav class="nav">
  <div class="nav-inner" style="display:flex; justify-content:space-between; align-items:center;">
    <a href="/" class="logo">
      <span class="logo-mark"></span>
      <span>Home<span class="logo-power">Power</span>Rebate</span>
    </a>
    <div style="display:flex; align-items:center; gap:16px;" class="nav-desktop-only">
      <a href="/installers/" style="color:var(--ink-soft); font-weight:600; font-size:15px; text-decoration:none;">Find an Installer</a>
      <a href="/get-quotes/" style="color:var(--ink-soft); font-weight:600; font-size:15px; text-decoration:none;">Get my plan</a>
      <a href="/blog/" style="color:var(--ink-soft); font-weight:600; font-size:15px; text-decoration:none;">Blog</a>
    </div>
    <div style="display:none; align-items:center; gap:12px;" class="nav-mobile-only">
      <a href="/installers/" style="color:var(--ink-soft); font-weight:600; font-size:14px; text-decoration:none;">Installers</a>
      <a href="/get-quotes/" style="color:var(--ink-soft); font-weight:600; font-size:14px; text-decoration:none;">Get my plan</a>
    </div>
    <button onclick="toggleCityDropdown()" class="nav-pick" style="border:none; cursor:pointer;">
      Pick your city
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
    </button>
  </div>

  <div id="city-dropdown-modal" style="display:none; position:absolute; top:56px; right:20px; background:#fff; border:1px solid var(--rule); border-radius:12px; box-shadow:0 8px 24px rgba(10,42,46,0.12); z-index:49; max-width:300px; max-height:70vh; overflow-y:auto;">
    <div style="padding:16px 16px 0;">
      <div style="display:flex; gap:6px; margin-bottom:12px;">
        <button type="button" onclick="showProvinceCities('on')" id="province-tab-on" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:var(--teal-deep); color:#fff; font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Ontario</button>
        <button type="button" onclick="showProvinceCities('bc')" id="province-tab-bc" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">British Columbia</button>
        <button type="button" onclick="showProvinceCities('ca')" id="province-tab-ca" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">California (US)</button>
      </div>
      <div style="display:flex; gap:6px; margin-bottom:12px;">
        <button type="button" onclick="showProvinceCities('ab')" id="province-tab-ab" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Alberta</button>
        <button type="button" onclick="showProvinceCities('ns')" id="province-tab-ns" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Nova Scotia</button>
      </div>
      <div style="display:flex; gap:6px; margin-bottom:12px;">
        <button type="button" onclick="showProvinceCities('ma')" id="province-tab-ma" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Massachusetts</button>
        <button type="button" onclick="showProvinceCities('ny')" id="province-tab-ny" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">New York</button>
      </div>
      <div style="display:flex; gap:6px; margin-bottom:12px;">
        <button type="button" onclick="showProvinceCities('pa')" id="province-tab-pa" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Pennsylvania</button>
        <button type="button" onclick="showProvinceCities('co')" id="province-tab-co" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Colorado</button>
        <button type="button" onclick="showProvinceCities('vt')" id="province-tab-vt" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Vermont</button>
        <button type="button" onclick="showProvinceCities('il')" id="province-tab-il" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Illinois</button>
      </div>
      <div style="display:flex; gap:6px; margin-bottom:12px;">
        <button type="button" onclick="showProvinceCities('wa')" id="province-tab-wa" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Washington</button>
        <span style="flex:1;"></span>
      </div>
    </div>
    <div style="padding:0 16px 16px;">
    <div id="province-cities-on" style="display:grid; gap:8px;">
      <a href="/ca/on/toronto/">Toronto</a><a href="/ca/on/ottawa/">Ottawa</a><a href="/ca/on/mississauga/">Mississauga</a><a href="/ca/on/brampton/">Brampton</a><a href="/ca/on/hamilton/">Hamilton</a><a href="/ca/on/markham/">Markham</a><a href="/ca/on/vaughan/">Vaughan</a><a href="/ca/on/richmond-hill/">Richmond Hill</a><a href="/ca/on/barrie/">Barrie</a><a href="/ca/on/london/">London</a><a href="/ca/on/kitchener/">Kitchener</a><a href="/ca/on/windsor/">Windsor</a><a href="/ca/on/oakville/">Oakville</a><a href="/ca/on/oshawa/">Oshawa</a><a href="/ca/on/whitby/">Whitby</a><a href="/ca/on/burlington/">Burlington</a><a href="/ca/on/cambridge/">Cambridge</a><a href="/ca/on/greater-sudbury/">Greater Sudbury</a>
    </div>
    <div id="province-cities-bc" style="display:none; gap:8px;">
      <a href="/ca/bc/abbotsford/">Abbotsford</a><a href="/ca/bc/burnaby/">Burnaby</a><a href="/ca/bc/chilliwack/">Chilliwack</a><a href="/ca/bc/coquitlam/">Coquitlam</a><a href="/ca/bc/fort-st-john/">Fort St. John</a><a href="/ca/bc/kamloops/">Kamloops</a><a href="/ca/bc/kelowna/">Kelowna</a><a href="/ca/bc/langley/">Langley</a><a href="/ca/bc/maple-ridge/">Maple Ridge</a><a href="/ca/bc/nanaimo/">Nanaimo</a><a href="/ca/bc/penticton/">Penticton</a><a href="/ca/bc/prince-george/">Prince George</a><a href="/ca/bc/richmond/">Richmond</a><a href="/ca/bc/squamish/">Squamish</a><a href="/ca/bc/surrey/">Surrey</a><a href="/ca/bc/vancouver/">Vancouver</a><a href="/ca/bc/vernon/">Vernon</a><a href="/ca/bc/victoria/">Victoria</a>
    </div>
    <div id="province-cities-ab" style="display:none; gap:8px;">
      <a href="/ca/ab/calgary/">Calgary</a><a href="/ca/ab/edmonton/">Edmonton</a><a href="/ca/ab/red-deer/">Red Deer</a><a href="/ca/ab/lethbridge/">Lethbridge</a><a href="/ca/ab/st-albert/">St. Albert</a>
    </div>
    <div id="province-cities-ns" style="display:none; gap:8px;">
      <a href="/ca/ns/halifax/">Halifax</a>
    </div>
    <div id="province-cities-ma" style="display:none; gap:8px;">
      <a href="/us/ma/boston/">Boston</a><a href="/us/ma/worcester/">Worcester</a><a href="/us/ma/springfield/">Springfield</a><a href="/us/ma/cambridge/">Cambridge</a><a href="/us/ma/lowell/">Lowell</a><a href="/us/ma/brockton/">Brockton</a><a href="/us/ma/new-bedford/">New Bedford</a><a href="/us/ma/quincy/">Quincy</a><a href="/us/ma/lynn/">Lynn</a><a href="/us/ma/fall-river/">Fall River</a><a href="/us/ma/newton/">Newton</a><a href="/us/ma/somerville/">Somerville</a>
    </div>
    <div id="province-cities-ca" style="display:none; gap:8px;">
      <a href="/us/ca/los-angeles/">Los Angeles</a><a href="/us/ca/sacramento/">Sacramento</a><a href="/us/ca/bay-area/">Bay Area</a><a href="/us/ca/san-diego/">San Diego</a><a href="/us/ca/inland-empire/">Inland Empire</a>
    </div>
    <div id="province-cities-ny" style="display:none; gap:8px;">
      <a href="/us/ny/con-edison/new-york-city/">New York City</a><a href="/us/ny/con-edison/yonkers/">Yonkers</a><a href="/us/ny/con-edison/mount-vernon/">Mount Vernon</a><a href="/us/ny/con-edison/new-rochelle/">New Rochelle</a><a href="/us/ny/con-edison/white-plains/">White Plains</a><a href="/us/ny/pseg/brookhaven/">Brookhaven</a><a href="/us/ny/pseg/islip/">Islip</a><a href="/us/ny/pseg/babylon/">Babylon</a><a href="/us/ny/pseg/huntington/">Huntington</a><a href="/us/ny/pseg/smithtown/">Smithtown</a><a href="/us/ny/pseg/oyster-bay/">Oyster Bay</a><a href="/us/ny/pseg/southampton/">Southampton</a><a href="/us/ny/central-hudson/poughkeepsie/">Poughkeepsie</a><a href="/us/ny/central-hudson/newburgh/">Newburgh</a><a href="/us/ny/central-hudson/kingston/">Kingston</a><a href="/us/ny/central-hudson/beacon/">Beacon</a><a href="/us/ny/central-hudson/saugerties/">Saugerties</a><a href="/us/ny/national-grid/albany/">Albany</a><a href="/us/ny/national-grid/buffalo/">Buffalo</a><a href="/us/ny/national-grid/rochester/">Rochester</a><a href="/us/ny/national-grid/syracuse/">Syracuse</a>
    </div>
    <div id="province-cities-pa" style="display:none; gap:8px;">
      <a href="/us/pa/philadelphia/">Philadelphia</a><a href="/us/pa/pittsburgh/">Pittsburgh</a><a href="/us/pa/allentown/">Allentown</a><a href="/us/pa/erie/">Erie</a>
    </div>
    <div id="province-cities-co" style="display:none; gap:8px;">
      <a href="/us/co/denver/">Denver</a><a href="/us/co/colorado-springs/">Colorado Springs</a><a href="/us/co/aurora/">Aurora</a><a href="/us/co/fort-collins/">Fort Collins</a><a href="/us/co/boulder/">Boulder</a>
    </div>
    <div id="province-cities-vt" style="display:none; gap:8px;">
      <a href="/us/vt/burlington/">Burlington</a><a href="/us/vt/south-burlington/">South Burlington</a><a href="/us/vt/rutland/">Rutland</a><a href="/us/vt/barre/">Barre</a><a href="/us/vt/montpelier/">Montpelier</a>
    </div>
    <div id="province-cities-il" style="display:none; gap:8px;">
      <a href="/us/il/chicago/">Chicago</a><a href="/us/il/aurora/">Aurora</a><a href="/us/il/naperville/">Naperville</a><a href="/us/il/peoria/">Peoria</a>
    </div>
    </div>
  </div>
</nav>
<!-- ============================== /NAV ============================== -->
'''
page += MAIN
page += f'''
<!-- ============================ FOOTER ============================= -->
<section style="background: linear-gradient(135deg, rgba(13, 79, 92, 0.95), rgba(8, 54, 63, 0.98)); padding: 56px 24px; margin: 0;">
  <div class="wrap" style="text-align: center; color: #fff; max-width: 600px;">
    <div style="font-size: 13px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: rgba(212, 117, 28, 0.9); margin-bottom: 14px;">From Sam</div>
    <h2 style="font-family: 'Fraunces', Georgia, serif; font-size: 32px; line-height: 1.2; margin-bottom: 14px; color: #fff;">Get my weekly email</h2>
    <p style="font-size: 15px; color: rgba(250, 247, 242, 0.85); margin-bottom: 24px;">Every Friday: what I'm learning about rebates across every province and state we cover, heat pump reality checks, solar economics, and the installers I trust. Real stuff, no marketing.</p>
    <form id="newsletter-form" style="display: flex; flex-direction: column; gap: 10px;">
      <input type="email" id="newsletter-email" placeholder="your@email.com" required style="padding: 12px 14px; border: none; border-radius: 6px; font-family: 'Inter Tight', sans-serif; font-size: 14px; background: #fff; color: var(--ink);">
      <input type="hidden" id="newsletter-city" value="">
      <input type="hidden" id="newsletter-page" value="/powerscore/">
      <button type="submit" style="padding: 12px 24px; background: #d4751c; color: #fff; border: none; border-radius: 6px; font-weight: 600; font-size: 14px; cursor: pointer; font-family: 'Inter Tight', sans-serif;">Subscribe</button>
      <p style="font-size: 11px; color: rgba(250, 247, 242, 0.6); margin-top: 6px;">No spam, ever. Unsubscribe anytime.</p>
    </form>
    <div id="newsletter-response" style="display: none; margin-top: 12px; padding: 12px; background: rgba(45, 106, 79, 0.2); border-radius: 6px; border: 1px solid rgba(45, 106, 79, 0.4); font-size: 13px;"></div>
  </div>
</section>

<footer class="footer">
  <div class="footer-inner">
    <div class="footer-top">
      <div>
        <div class="footer-brand">Home<span class="logo-power">Power</span>Rebate</div>
        <p class="footer-tagline">Helping homeowners understand rebates and choose trusted installers. Real numbers. Your choice.</p>
      </div>
      <div>
        <div class="footer-col-title">Canada</div>
        <ul class="footer-col-links">
          <li><a href="/ca/">All Provinces</a></li>
          <li><a href="/ca/bc/">British Columbia</a></li>
          <li><a href="/ca/on/">Ontario</a></li>
          <li><a href="/ca/ab/">Alberta</a></li>
          <li><a href="/ca/ns/">Nova Scotia</a></li>
        </ul>
      </div>
      <div>
        <div class="footer-col-title">United States</div>
        <ul class="footer-col-links">
          <li><a href="/us/">All States</a></li>
          <li><a href="/us/ca/">California</a></li>
          <li><a href="/us/ny/">New York</a></li>
          <li><a href="/us/ma/">Massachusetts</a></li>
        </ul>
      </div>
      <div>
        <div class="footer-col-title">Guides &amp; Tools</div>
        <ul class="footer-col-links">
          <li><a href="/powerscore/">PowerScore Rankings</a></li>
          <li><a href="/installers/">Find an Installer</a></li>
          <li><a href="/get-quotes/">Get my plan</a></li>
          <li><a href="/share-your-cost/">Share Your Cost</a></li>
          <li><a href="/blog/">Full Blog</a></li>
          <li><a href="/questions/">Rebate Questions</a></li>
          <li><a href="/ca/">Canada by Province</a></li>
          <li><a href="/us/">US by State</a></li>
        </ul>
      </div>
      <div>
        <div class="footer-col-title">Company</div>
        <ul class="footer-col-links">
          <li><a href="/about/">About</a></li>
          <li><a href="/installers/badge/">For Installers</a></li>
          <li><a href="/privacy/">Privacy</a></li>
          <li><a href="/terms/">Terms</a></li>
          <li><a href="/contact/">Contact</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <div>&copy; 2026 HomePowerRebate &middot; Independent guide. By <a href="/about/" style="color:inherit;">Sam Menard</a>. <a href="https://www.facebook.com/profile.php?id=61592376033225" style="color:inherit; text-decoration:none;">Follow on Facebook</a></div>
      <div>Made in Canada 🇨🇦</div>
    </div>
  </div>
</footer>
<!-- =========================== /FOOTER ============================= -->

<script>
function toggleCityDropdown() {{
  const modal = document.getElementById('city-dropdown-modal');
  if (modal) modal.style.display = modal.style.display === 'none' ? 'block' : 'none';
}}
function showProvinceCities(prov) {{
  const regions = ['on', 'bc', 'ab', 'ns', 'ma', 'ca', 'ny', 'pa', 'co', 'vt', 'il'];
  regions.forEach(function(r) {{
    const panel = document.getElementById('province-cities-' + r);
    const tab = document.getElementById('province-tab-' + r);
    if (!panel || !tab) return;
    panel.style.display = (prov === r) ? 'grid' : 'none';
    tab.style.background = (prov === r) ? 'var(--teal-deep)' : '#fff';
    tab.style.color = (prov === r) ? '#fff' : 'var(--ink)';
  }});
}}
document.getElementById('newsletter-form')?.addEventListener('submit', async (e) => {{
  e.preventDefault();
  const email = document.getElementById('newsletter-email').value;
  const city = document.getElementById('newsletter-city').value;
  const page = document.getElementById('newsletter-page').value;
  const responseEl = document.getElementById('newsletter-response');
  const button = document.querySelector('#newsletter-form button');
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = 'Subscribing...';
  try {{
    const response = await fetch('https://leads.homepowerrebate.com/newsletter', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ email, city, page }})
    }});
    if (!response.ok) throw new Error('Subscription failed');
    responseEl.textContent = "You're in! Check your inbox for a welcome email.";
    responseEl.style.display = 'block';
    document.getElementById('newsletter-form').style.display = 'none';
  }} catch (error) {{
    responseEl.textContent = 'Something went wrong — please try again or email us directly.';
    responseEl.style.display = 'block';
    responseEl.style.background = 'rgba(163, 64, 47, 0.2)';
    responseEl.style.borderColor = 'rgba(163, 64, 47, 0.4)';
    button.disabled = false;
    button.textContent = originalText;
  }}
}});

/* ---- PowerScore page-specific JS ---- */
window.PS_ROWS = {page_rows_json()};
window.PS_CATS = {json.dumps([SHORT_LABELS[c] for c in CATEGORIES])};
{PS_JS}
</script>

</body>
</html>
'''

out_path = ROOT / "powerscore" / "index.html"
page = re.sub(r"const regions = \[[^\]]*\];", "const regions = " + regions.codes_js() + ";", page)
out_path.write_text(page)
print(f"Wrote {out_path} ({len(page):,} bytes)")
