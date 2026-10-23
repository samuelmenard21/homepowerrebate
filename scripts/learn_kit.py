#!/usr/bin/env python3
"""Shared markup for the LEARN components (2026-10-23): editorial cards, "how to read these results" tips, listicle, key takeaways, quiz.
Styles and the quiz script live in _partials/nav-footer.html (SHARED CSS / SHARED JS); nothing here is inline CSS.
Articles come from data/learn/<slug>.json (see build_learn_articles.py)."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
e = html.escape


def articles():
    """Every learn article's data, by slug."""
    return {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "data" / "learn").glob("*.json"))}


def card(slug, d):
    c = d["card"]
    cls = " is-num" if c.get("style") == "num" else ""
    im = c.get("image")
    photo = ""
    if im:
        cls += " has-img"
        photo = (f'<img src="/assets/learn/{im["file"]}-640.webp" srcset="/assets/learn/{im["file"]}-640.webp 640w, /assets/learn/{im["file"]}-1200.webp 1200w" '
                 f'sizes="(min-width:760px) 360px, 90vw" width="640" height="427" alt="{e(im["alt"])}" loading="lazy">')
    return (f'<a class="learn-card{cls}" href="/blog/{slug}/"><div class="learn-tile t-{c["tone"]}">{photo}<span class="learn-kick">{e(c["kicker"])}</span>'
            f'<span class="learn-big">{e(c["tile"])}</span></div><h3>{e(d["h1"])}</h3>'
            f'<div class="learn-meta">Sam Menard · {e(d["read"])}</div>'
            f'<div class="learn-chips">{"".join(f"<span>{e(t)}</span>" for t in c["chips"])}</div>'
            f'<span class="learn-more">Read more →</span></a>')


def pick(service, n=3, key=""):
    """The n articles that best fit a service (heat-pump, solar...); topped up with general ones. With several candidates the order
    rotates by a hash of key (the page path), so neighbouring pages do not all show the same row."""
    import zlib
    arts = articles()
    spin = lambda ss: sorted(ss, key=lambda s: zlib.crc32((key + s).encode()))
    fit = spin([s for s, d in arts.items() if service in d["services"]])
    rest = spin([s for s in arts if s not in fit])
    return [(s, arts[s]) for s in (fit + rest)[:n]]


def not_ready_row(service, key="", heading="Not ready to talk to a contractor yet?", sub="Short reads and quick quizzes. Learn the rules first, then call."):
    cards = "".join(card(s, d) for s, d in pick(service, key=key))
    return (f'<section class="learn-row"><h2>{e(heading)}</h2>'
            f'<p class="learn-sub">{e(sub)}</p><div class="learn-grid">{cards}</div></section>')


def tips(unit):
    """Three-step reading guide for a ranking page; unit = "installer", "advisor"..."""
    items = [("Open the profile.", f"How a {unit} describes its own work tells you a lot. Look for jobs like yours."),
             ("Read the Google reviews.", "Stars and counts come from Google Maps. Click through and read what past customers wrote, good and bad."),
             ("Check for program badges.", "A green registered-contractor badge means the company is on the program's own list, which some rebates require."),
             ("Compare three.", f"Do not stop at the first good {unit}. Three quotes show you the real range in price, equipment and plan.")]
    return ('<section class="learn-tips"><h2>How to read these results</h2><ol>'
            + "".join(f"<li><b>{e(a)}</b>{e(b)}</li>" for a, b in items) + "</ol></section>")


def takeaways(d):
    return '<div class="learn-key"><h2>Key takeaways</h2><ul>' + "".join(f"<li>{t}</li>" for t in d["takeaways"]) + "</ul></div>"


def listicle(d):
    out = ['<ol class="learn-list">']
    for i, (h, body) in enumerate(d["items"], 1):
        out.append(f'<li><h3><span class="learn-num">{i}</span><span>{h}</span></h3>{body}</li>')
    out.append("</ol>")
    return "".join(out)


def quiz(slug, q):
    qs = []
    for n, item in enumerate(q["qs"]):
        opts = "".join(f'<button type="button" class="qz-opt">{e(o)}</button>' for o in item["options"])
        qs.append(f'<fieldset class="qz-q" data-a="{item["answer"]}"><legend>{n + 1}. {e(item["q"])}</legend><div class="qz-opts">{opts}</div>'
                  f'<p class="qz-why">{item["why"]}</p></fieldset>')
    msgs = e(json.dumps(q["messages"]), quote=True)
    return (f'<section class="hpr-quiz" id="quiz-{slug}" data-msgs="{msgs}"><h2>{e(q["title"])}</h2><p>{e(q["intro"])}</p>{"".join(qs)}'
            f'<div class="qz-result" aria-live="polite"><b class="qz-score"></b><span class="qz-msg"></span> {q["cta"]}</div></section>')


def strip(links):
    """Paper-strip list for "Keep reading": links = [(text, url)] or [(text, url, kind)]."""
    kinds = {s: "Listicle and quiz" for s in articles()}
    lis = ""
    for l in links:
        kind = kinds.get(l[1].strip("/").split("/")[-1], "Guide")
        lis += f'<li><span><small>{e(kind)}</small><a href="{l[1]}">{l[0]}</a></span></li>'
    return f'<ul class="learn-strip">{lis}</ul>'


def figure(d):
    """The article's lead photo with its credit (cards use the same file)."""
    im = d["card"].get("image")
    if not im:
        return ""
    return (f'<figure class="learn-photo"><img src="/assets/learn/{im["file"]}-1200.webp" width="1200" height="800" alt="{e(im["alt"])}" fetchpriority="high">'
            f'<figcaption>Photo: <a href="{e(im["url"])}" target="_blank" rel="noopener">{e(im["credit"])}</a></figcaption></figure>')


# ---- open rebates by upgrade, read from the calculators (which read the verified facts) ----
CAL = ROOT / "calculator" / "data"


def _amount(a):
    """(sort value, display text) for a calculator amount: a maximum, a per-unit rate with a cap, or a labelled amount."""
    if not a:
        return 0, ""
    if a.get("label"):
        return a.get("max", 0) or a.get("per", {}).get("cap", 0) or 0, a["label"]
    if a.get("max"):
        return a["max"], f"up to ${a['max']:,}"
    per = a.get("per")
    if per:
        if per.get("cap"):
            return per["cap"], f"up to ${per['cap']:,}"
        return per.get("rate", 0), f"${per['rate']:,} per {per.get('unit', 'unit')}"
    return 0, ""


def open_programs(upgrade):
    """Every open program for an upgrade across all regions: [{code, region, program, value, shown, source, checked, currency}], biggest first."""
    out = []
    for f in sorted(CAL.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for p in d["programs"]:
            if p.get("upgrade") != upgrade or p.get("status") != "active":
                continue
            v, shown = _amount(p.get("amount"))
            if v <= 0 or not shown:
                continue
            out.append({"code": d["code"], "region": d["name"], "country": d["country"], "program": p["name"], "value": v, "shown": shown,
                        "source": p.get("source_url", ""), "checked": p.get("verified_on", ""), "currency": d["currency"]})
    return sorted(out, key=lambda r: (r["country"] != "ca", r["region"], -r["value"]))


def region_quiz(code):
    """A quiz for a region built from its calculator programs (so every answer is a verified, dated amount). None when the region has too few."""
    import zlib
    d = json.loads((CAL / f"{code}.json").read_text(encoding="utf-8"))
    cur = "CA$" if d["currency"] == "CAD" else "$"
    rows = []
    for p in d["programs"]:
        v, shown = _amount(p.get("amount"))
        if p.get("status") == "active" and v > 0 and shown.startswith("up to"):
            rows.append((p["name"], v, shown, p.get("verified_on", ""), p.get("source_url", "")))
    seen, uniq = set(), []
    for r in rows:
        if r[1] not in seen:
            seen.add(r[1])
            uniq.append(r)
    if len(uniq) < 3:
        return None
    uniq = sorted(uniq, key=lambda r: zlib.crc32((code + r[0]).encode()))[:5]
    values = [r[1] for r in uniq]
    qs = []
    for i, (name, v, shown, checked, src) in enumerate(uniq):
        others = [x for x in values if x != v]
        opts = sorted({v, *others[:2]})
        while len(opts) < 3:
            opts.append(max(opts) * 2)
            opts = sorted(set(opts))
        labels = [f"{cur}{x:,}" for x in opts]
        when = checked and __import__("datetime").date.fromisoformat(checked).strftime("%B %-d, %Y")
        qs.append({"q": f"The most this program can pay: {name}. How much?", "options": labels, "answer": opts.index(v),
                   "why": f"{e(name)} pays {e(shown)}. " + (f'<a href="{e(src)}" target="_blank" rel="noopener">Official page</a>, checked {when}.' if src else f"Checked {when}.")})
    return {"title": f"Quick quiz: {d['name']} rebates", "intro": "A few questions from the programs we track. Tap an answer to see why.", "qs": qs,
            "messages": ["Worth another look at the programs above.", "Nice. You know the programs well.", "Perfect score. You know your rebates."],
            "cta": f'<a href="/calculator/{code}/">Estimate your rebates</a>'}
