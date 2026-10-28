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
    """A one-question-at-a-time quiz (shared CSS and JS in _partials/nav-footer.html). Without JavaScript every question and its explanation show."""
    qs = []
    for n, item in enumerate(q["qs"]):
        opts = "".join(f'<button type="button" class="qz-opt">{e(o)}</button>' for o in item["options"])
        qs.append(f'<fieldset class="qz-q" data-a="{item["answer"]}"><legend>{n + 1}. {e(item["q"])}</legend><div class="qz-opts">{opts}</div>'
                  f'<p class="qz-why">{item["why"]}</p></fieldset>')
    msgs = e(json.dumps(q["messages"]), quote=True)
    return (f'<section class="hpr-quiz" id="quiz-{slug}" data-msgs="{msgs}"><span class="qz-kick">Quick quiz</span><h2>{e(q["title"])}</h2><p class="qz-intro">{e(q["intro"])}</p>{"".join(qs)}'
            f'<div class="qz-result" aria-live="polite"><div class="qz-ring"><span class="qz-score"></span></div><span class="qz-msg"></span>'
            f'<div class="qz-acts"><span class="qz-cta-wrap">{q["cta"].replace("<a ", "<a class=\"qz-cta\" ", 1)}</span><button type="button" class="qz-again">Play again</button><button type="button" class="qz-share">Share my score</button></div></div></section>')


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
            '</figure>')


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


def open_programs(upgrade, labelled=False):
    """Every open program for an upgrade across all regions: [{code, region, program, value, shown, source, checked, currency}], biggest first."""
    out = []
    for f in sorted(CAL.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for p in d["programs"]:
            if p.get("upgrade") != upgrade or p.get("status") != "active":
                continue
            v, shown = _amount(p.get("amount"))
            if (v <= 0 and not (labelled and shown)) or not shown:
                continue  # labelled=True also lists programs whose amount is a range we show but do not add up (appliances)
            out.append({"code": d["code"], "region": d["name"], "country": d["country"], "program": p["name"], "value": v, "shown": shown,
                        "source": p.get("source_url", ""), "checked": p.get("verified_on", ""), "currency": d["currency"]})
    return sorted(out, key=lambda r: (r["country"] != "ca", r["region"], -r["value"]))


def region_quiz(code, upgrades=None):
    """A quiz for a region built from its calculator programs (so every answer is a verified, dated amount). None when the region has too few.
    upgrades limits it to programs for those upgrade ids (a region's heat pump page asks about heat pump programs)."""
    import zlib
    d = json.loads((CAL / f"{code}.json").read_text(encoding="utf-8"))
    cur = "CA$" if d["currency"] == "CAD" else "$"
    rows = []
    for p in d["programs"]:
        if upgrades and p.get("upgrade") not in upgrades:
            continue
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
            "cta": f'<a href="/calculator/{code}/">Estimate my rebates</a>'}


# ---- general quizzes (no province or state named; they teach how the device works) and city quizzes (2026-10-28) ----
QZ = ROOT / "data" / "quizzes"


def general_quiz(name, slug=None):
    """A device-knowledge quiz from data/quizzes/<name>.json. The file lists the right answer first; the order is shuffled by a hash of the question so the
    answer is not always the first button. Never names a province or state."""
    import zlib
    q = json.loads((QZ / f"{name}.json").read_text(encoding="utf-8"))
    qs = []
    for item in q["qs"]:
        opts = sorted(item["options"], key=lambda o: zlib.crc32((item["q"] + o).encode()))
        qs.append({**item, "options": opts, "answer": opts.index(item["options"][item["answer"]])})
    return quiz(slug or f"{name}-basics", {**q, "qs": qs})


_LOOKUP = json.loads((ROOT / "city-rebate-lookup.json").read_text(encoding="utf-8"))
_CLIMATE = json.loads((ROOT / "city-climate-data.json").read_text(encoding="utf-8"))
_SOLAR = json.loads((ROOT / "city-solar-data.json").read_text(encoding="utf-8"))
_CAT = {"heat-pump": "heat_pump", "solar": "solar", "battery": "battery", "water-heater": "water_heater", "insulation": "insulation",
        "windows-doors": "windows", "ev-charger": "ev_charger", "smart-thermostats": "thermostat", "hrv": "hrv"}
_COLD = {"heat-pump", "insulation", "windows-doors", "water-heater", "smart-thermostats", "hub"}
_NAME = {"heat-pump": "heat pump", "solar": "solar", "battery": "battery", "water-heater": "water heater", "insulation": "insulation",
         "windows-doors": "windows and doors", "ev-charger": "EV charger", "smart-thermostats": "smart thermostat", "hub": "home energy"}


def _shuffled(correct, wrong, seed):
    import zlib
    opts = sorted([correct, *wrong], key=lambda o: zlib.crc32((seed + o).encode()))
    return opts, opts.index(correct)


def city_quiz(code, city, service="hub", country="ca"):
    """Quiz about one city, built only from our own city data: its utility, weather sample, solar hours, the biggest 'up to' amount we list for the
    upgrade, and (where we hold it) the renter share. None when fewer than three questions can be made."""
    import re
    import zlib
    key = f"{code}|{city.replace('-', ' ')}"
    row = _LOOKUP.get(key)
    if not row:
        return None
    name = row["city"]
    us = country == "us"
    qs = []

    def say(*variants):
        """One of several phrasings of a question, picked by the city and page, so sibling city pages do not repeat the same sentence."""
        return variants[zlib.crc32((key + service + variants[0]).encode()) % len(variants)]

    def add(q, correct, wrong, why):
        opts, a = _shuffled(correct, wrong, key + q)
        num = lambda o: float(re.sub(r"[^\d.\-]", "", o))
        if all(re.match(r"^[\$\-]?\d", o) for o in opts):  # numbers read best in order
            opts = sorted(opts, key=num)
            a = opts.index(correct)
        qs.append({"q": q, "options": opts, "answer": a, "why": why})

    others = []  # other utilities from the same country only (a Vermont quiz never offers a BC utility), same province or state first
    import regions
    same = {r["code"] for r in regions.REGIONS if r["country"] == next((x["country"] for x in regions.REGIONS if x["code"] == code), "")}
    for first in (True, False):
        for k, v in _LOOKUP.items():
            u = v["utility"]
            if u != row["utility"] and "(" not in u and u not in others and v["region"].lower() in same and (v["region"] == row["region"]) == first:
                others.append(u)
    if len(others) >= 2:
        add(say(f"Which utility's programs apply to our {name} rebate guide?", f"Rebates in {name} often depend on the utility. Which one do we use for {name}?", f"Whose programs should a {name} homeowner check first?"), row["utility"], others[:2],
            f"{e(row['utility'])} is the utility we use for {e(name)}. Rebates often depend on who supplies your power or gas, so check yours first.")
    sh = [(1, 2), (-2, -1), (-1, 1), (1, 3), (-3, -1)][zlib.crc32((key + service).encode()) % 5]  # where the wrong numbers sit, so the right one is not always in the middle
    cl = _CLIMATE.get(key)
    if service in _COLD and cl:
        v = cl["avg_january_low_c"]
        def t(x):
            return f"{round(x * 9 / 5 + 32)} °F" if us else f"{round(x)} °C"
        step = 9 if us else 5
        add(say(f"On average, how low does the temperature fall in {name} in January?", f"What is a typical January night low in {name}?", f"In January, {name} nights usually bottom out near:"), t(v), [t(v + sh[0] * step), t(v + sh[1] * step)],
            f"Our weather sample for {e(name)} ({cl['sample_years']}) shows an average January low of {t(v)}. Cold-climate heat pumps are tested at low temperatures, so check the rating at your coldest days, not just the average.")
        if service == "heat-pump" and cl.get("coldest_recorded_c") is not None:
            c = cl["coldest_recorded_c"]
            add(say(f"What was the coldest reading in our {cl['sample_years']} weather sample for {name}?", f"How cold did {name} get at its worst between {cl['sample_years'].replace('-', ' and ')}?", f"The coldest spell in {name} in {cl['sample_years']} reached:"), t(c), [t(c + sh[0] * 2 * step), t(c + sh[1] * 2 * step)],
                f"The lowest temperature in the sample for {e(name)} was {t(c)}. A right-sized heat pump is chosen for your coldest design day, not the average.")
    so = _SOLAR.get(key)
    if service in ("solar", "battery", "hub") and so:
        h = so["approx_peak_sun_hours"]
        wrong = [f"{max(h + sh[0], 0.5):.1f}", f"{max(h + sh[1], 0.9):.1f}"]
        add(say(f"About how many peak sun hours a day does {name} get on average?", f"A solar panel in {name} sees about how many full-sun hours a day?", f"Daily peak sun hours in {name} average about:"), f"{h:.1f}", wrong,
            f"Our {so['sample_years']} sunshine sample for {e(name)} averages about {h:.1f} peak sun hours a day. Fewer hours means less solar power per panel, so the size of the system matters.")
    cat = _CAT.get(service, "heat_pump" if service == "hub" else None)
    txt = row.get("categories", {}).get(cat, "") if cat else ""
    nums = [int(n.replace(",", "")) for n in re.findall(r"[Uu]p to \$([\d,]+)", txt)]
    if nums and max(nums) > 0:
        top = max(nums)
        wrong = [x for x in dict.fromkeys(sorted(set(nums) - {top}) + [top * 2, max(top // 2, 100), top * 3]) if x != top][:2]
        what = _NAME.get(service, "heat pump") if service != "hub" else "heat pump"
        add(say(f"We list {what} rebates for {name}. What is the biggest 'up to' amount?", f"What is the largest 'up to' {what} figure on our {name} summary?", f"Across the {what} programs we list for {name}, the top 'up to' amount is:"), f"${top:,}", [f"${x:,}" for x in wrong],
            f"Our summary for {e(name)}: {e(txt)}. The amount you get depends on your home, income and utility, so use the calculator.")
    cen = ROOT / "data" / f"{code}-housing-census2021.json"
    if cen.exists():
        c = json.loads(cen.read_text(encoding="utf-8")).get(city)
        if isinstance(c, dict) and c.get("renter") and c.get("households"):
            v = round(100 * c["renter"] / c["households"])
            wrong = [f"{min(max(v + sh[0] * 12, 3), 95)}%", f"{min(max(v + sh[1] * 12, 3), 95)}%"]
            if len({f"{v}%", *wrong}) == 3:
                add(say(f"About what share of homes in {name} are rented?", f"Out of 100 homes in {name}, about how many are rented?", f"Renters make up what share of {name} households?"), f"{v}%", wrong,
                    f"The 2021 Census counts {c['renter']:,.0f} renter households out of {c['households']:,.0f} in {e(name)}. Many rebates go to owners, and some programs have separate rules for landlords and tenants.")
    if len(qs) < (3 if service == "hub" else 2):
        return None
    what = _NAME.get(service, "home energy")
    cta = f'<a href="/calculator/{code}/">Estimate my rebates</a>' if (CAL / f"{code}.json").exists() else '<a href="/get-quotes/">See my rebates</a>'
    return {"title": f"Quick quiz: {what} in {name}", "intro": f"Questions about {name}, from the data behind this page. Tap an answer to see why.", "qs": qs[:5],
            "messages": ["Worth another look at the page above.", f"Nice. You know {name} well.", f"Perfect score. You know {name}."], "cta": cta}


# ---- photo for any article (2026-10-24): one free-licence photo per topic, chosen by words in the slug and title ----
_PHOTOS = json.loads((ROOT / "data" / "learn-photos.json").read_text(encoding="utf-8"))
_TOPIC = [(r"ev-|-ev\b|charger|electric vehicle", "ev-charger"), (r"solar|net-meter|roof", "solar-roof"), (r"thermostat|smart-home", "thermostat"),
          (r"insulation|attic|air-seal|weatheri|draft|window|door", "rebate-plans"), (r"water-heater|appliance|induction|stove|dryer|cook|kitchen", "kitchen"),
          (r"installer|quote|contractor|hire|vet|scam|audit|advisor|assessment", "hiring-roof"),
          (r"income|renter|condo|strata|apartment|landlord|low-income|assistance|bill|heating-rebate|harp|supplement|crisis", "living-room"),
          (r"heat-pump|furnace|cold|hvac|cooling|ductless|mini-split|geothermal", "heat-pump-house")]
_FALLBACK = ["modern-home", "duplex-home", "living-room", "heat-pump-house"]


def photo_for(slug, title=""):
    """(file, alt, credit, url) for a blog post: first topic whose words appear in the slug or title, else a stable pick by hash of the slug."""
    import re
    import zlib
    text = f"{slug} {title}".lower().replace(" ", "-")
    for pat, f in _TOPIC:
        if re.search(pat, text):
            break
    else:
        f = _FALLBACK[zlib.crc32(slug.encode()) % len(_FALLBACK)]
    p = _PHOTOS[f]
    return f, p["alt"], p["credit"], p["url"]


def post_figure(slug, title=""):
    f, alt, credit, url = photo_for(slug, title)
    return (f'<figure class="learn-photo"><img src="/assets/learn/{f}-1200.webp" width="1200" height="800" alt="{e(alt)}" fetchpriority="high">'
            '</figure>')
