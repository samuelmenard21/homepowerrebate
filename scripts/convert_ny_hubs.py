#!/usr/bin/env python3
"""One-off conversion (2026-11-04): New York utility and city hubs from ny_verified_hubs.py to the page engine.
Uses that generator's own functions, so the wording is the same, and writes the engine's JSON:
  data/ny/pages/<utility>/<city>/index.json   (21 city hubs, built by python3 scripts/build_ny_pages.py --hubs)
  data/ny/pages/<utility>/hub.json            (4 utility hubs, Region.group_hub)
After this, ny_verified_hubs.py is retired: edit the JSON, not the generator. git add -f data/ny."""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import ny_verified_hubs as g  # noqa: E402
import page_kit as kit  # noqa: E402

FACT = {"con-edison": "ny-2-con-edison-clean-heat-air-source", "national-grid": "ny-4-national-grid-clean-heat-upstate",
        "central-hudson": "ny-7-central-hudson-clean-heat", "rge": "ny-5-rg-e-clean-heat-rochester", "pseg": "ny-10-pseg-long-island-heat-pump-rebates-not-nys-clean-h"}
EMP = "ny-11-empower-nyserda"
RATE_CITY = {"rochester": "ny-5-rg-e-clean-heat-rochester"}
U = html.unescape
strip = lambda s: re.sub(r"<[^>]+>", "", s)


def refs(u):
    return [[U(a), b] for b, a in re.findall(r'<a href="([^"]+)" rel="noopener">([^<]+)</a>', g.sources(u))]


def rows(u):
    t = g.rate_table(u)
    heads = [U(strip(x)) for x in re.findall(r"<th>(.*?)</th>", t)]
    out = []
    for tr in re.findall(r"<tr><td>.*?</tr>", t):
        td = [x for x in re.findall(r"<td>(.*?)</td>", tr)]
        out.append(td)
    tail = t.split("</table></div>", 1)[1] if "</table></div>" in t else ""
    return heads, out, tail


def cards(u, fid, heads, rws):
    st = kit.FACTS[fid]["status"]
    cs = []
    for td in rws:
        title = U(strip(td[0]))
        note = " ".join([heads[1] + "."] + [f"{heads[i]}: {U(strip(td[i]))}." for i in range(2, len(td))]) if len(td) > 1 else ""
        cs.append({"title": title, "amount": U(strip(td[1])) if len(td) > 1 else "", "note": note, "facts": [fid], "status": st})
    return cs


def sections_of(art):
    """[(h2 text, html)] for every <h2> in an article fragment."""
    parts = re.split(r"(?=<h2>)", art)
    out = []
    for p in parts:
        m = re.match(r"<h2>(.*?)</h2>(.*)", p, re.S)
        if m:
            out.append((m.group(1), m.group(2).strip()))
    return out


def city(key, c):
    u = c["u"]; d = g.U[u]; c["key"] = key
    fid = RATE_CITY.get(key.split("/")[-1], FACT[u])
    body = g.city_body(key, c, False)
    art = body[body.index('<article class="nyv">') + len('<article class="nyv">'):body.rindex("</article>")]
    short = re.search(r'<div class="short">(.*?)</div>', art, re.S).group(1)
    secs = dict(sections_of(art))
    heads, rws, tail = rows(u)
    h1 = U(f'{c["city"]} Heat Pump Rebates 2026: {d["short"]}')
    title = c.get("title") or f'{c["short"]} Heat Pump Rebates 2026: {d["short"]} Amounts'
    if len(U(title)) > 60:
        title = f'{c["short"]} Heat Pump Rebates 2026'
    desc = U(f'{c["city"]} heat pump rebates in 2026: {d["program"]} pays {strip(d["headline"])}. What stacks, what ended, and EmPower+.')
    if len(desc) > 160:
        desc = U(f'{c["city"]} heat pump rebates 2026: {d["short"]} pays {strip(d["headline"])}. What stacks and what ended.')
    sec, order = [], []
    for h, b in sections_of(art):
        hu = U(strip(h))
        if hu.startswith("How much is the") or hu == "Common questions" or hu.startswith("What to do next"):
            continue
        sec.append([h, b])
    nxt = re.search(r"<h2>What to do next.*?</h2>(.*?)<p>More for", art, re.S)
    steps = re.findall(r"<li>(.*?)</li>", nxt.group(1), re.S) if nxt else []
    more = re.search(r"<p>More for .*?</p>", art, re.S)
    cta = re.search(r'<div class="cta-box">(.*?)</div>', art, re.S)
    lead = f'What {c["city"]} homeowners can really get in 2026, checked against {d["short"]} and NYSERDA on {g.CHECKED}.'
    badge = re.sub(r"\s*\(.*", "", strip(d["headline"])).strip()
    return {
        "title": U(title), "desc": desc, "h1": h1, "badge": U(badge[:1].upper() + badge[1:]) if badge.lower().startswith("up to") else "From " + U(badge), "lead": lead,
        "min_words": 600, "facts": [fid, EMP], "cards_heading": f'What you can claim in {c["city"]} in 2026',
        "cards_intro": f'<div class="callout">{short}</div>\n<p>Amounts for a single-family home. You get one line from this table, not several.</p>',
        "cards": cards(u, fid, heads, rws), "after_cards": tail, "sections": sec, "no_installers": True,
        "claim_heading": f'What to do next in {c["city"]}', "claim_steps": steps,
        "faq": faq4(c),
        "next": (more.group(0) if more else "") + (f'\n<div class="callout">{cta.group(1)}</div>' if cta else ""),
        "refs": refs(u)}


def faq4(c):
    f = [[q, a] for q, a in g.faqs_city(c)]
    if len(f) < 4:  # pages with a local FAQ had three: add the EmPower+ question every other page has
        f.append([q, a] for q, a in [g.faqs_city(dict(c, key=""))[3]])
        f[-1] = list(f[-1])[0]
    return f


def hub(slug, h):
    u = h["u"]; d = g.U[u]
    body, faqs = g.hub_body(slug, h)
    art = body[body.index('<article class="nyv">') + len('<article class="nyv">'):body.rindex("</article>")]
    short = re.search(r'<div class="short">(.*?)</div>', art, re.S).group(1)
    sec = [[hh, b] for hh, b in sections_of(art) if U(strip(hh)) != "Common questions"]
    return {"title": h["title"], "desc": U(f'{d["program"]} pays {strip(d["headline"])} for a whole-home heat pump. What stacks, what ended, and EmPower+ help.')[:160],
            "h1": h["title"], "lead": f'Heat pump rebates for homeowners in {h["area"]}, checked against {d["short"]} and NYSERDA on {g.CHECKED}.',
            "short": short, "facts": [FACT[u], EMP], "sections": sec, "faq": [[q, a] for q, a in faqs], "refs": refs(u)}


DASHES = [("&mdash;</td>", "n/a</td>"), (" &mdash; not several", ", not several"), ("HEAR cheque &mdash; New York", "HEAR cheque: New York"),
          ("DAC map</a> too &mdash; it can", "DAC map</a> too: it can"), ("Google reviews &mdash; free", "Google reviews, free")]


def clean(obj):
    """The shared quality gate allows one em dash a page: table placeholders become n/a, the four sentence dashes become punctuation."""
    t = json.dumps(obj, indent=1, ensure_ascii=False)
    for a, b in DASHES:
        t = t.replace(a, b)
    t = t.replace(": \u2014.", ": n/a.").replace(" &mdash; but ", ", but ").replace(" \u2014 but ", ", but ")
    t = t.replace(" &mdash; ", "; ").replace(" \u2014 ", "; ")  # a dash between two clauses becomes a semicolon
    return t + "\n"


def main():
    n = 0
    for key, c in g.C.items():
        out = ROOT / "data/ny/pages" / key / "index.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(clean(city(key, dict(c))), encoding="utf-8"); n += 1
    for slug, h in g.UTILITY_HUBS.items():
        out = ROOT / "data/ny/pages" / slug / "hub.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(clean(hub(slug, h)), encoding="utf-8"); n += 1
    print("wrote", n, "files")


if __name__ == "__main__":
    main()
