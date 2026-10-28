#!/usr/bin/env python3
"""Learn hubs: /learn/<slug>/ for each upgrade (2026-10-23), from hand-written data/learn-hubs/<slug>.json plus live data.
Fields: slug, upgrade (calculator upgrade id), title, desc, h1, badge_noun, lead, intro (html), checks [html], faq [[q,a]], refs [[text,url]] (extra to the program pages),
keywords (blog-index titles that match), services (learn article tags), updated, published.
Everything numeric comes from the calculators (learn_kit.open_programs): the open programs for the upgrade in every region, each with its official page and the date we checked.
Usage: python3 scripts/build_learn_hubs.py   (git add -f data/learn-hubs)"""
import html
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import learn_kit as lk  # noqa: E402
import page_kit as kit  # noqa: E402
import regions  # noqa: E402

e = html.escape
HUB_STYLE = ('<style>.learn-hero-photo{background:linear-gradient(180deg,rgba(8,54,63,.8),rgba(8,54,63,.94)),url(/assets/learn/{img}-1200.webp) center/cover no-repeat!important}'
             '.learn-facts{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:0 0 28px}.learn-fact{padding:20px 22px;border-radius:20px;background:#fff;border:1px solid var(--card-rule)}'
             '.learn-fact b{display:block;font-family:Fraunces,Georgia,serif;font-size:clamp(30px,3.2vw,44px);line-height:1;color:var(--teal-deep)}.learn-fact span{display:block;margin-top:8px;font-size:16px;color:var(--muted)}'
             '@media(max-width:760px){.learn-facts{grid-template-columns:1fr}}</style>')


def table(rows):
    body = "".join(
        f'<tr><td><a href="{regions.HUB_URL_BY_CODE[r["code"]]}">{e(r["region"])}</a></td><td>{e(r["program"])}</td><td>{e(r["shown"])} ({r["currency"]})</td>'
        f'<td><a href="{e(r["source"])}" target="_blank" rel="noopener">Official page</a>, checked {date.fromisoformat(r["checked"]).strftime("%b %-d, %Y")}</td></tr>' for r in rows if r["checked"])
    return f'<div class="table-wrap"><table><thead><tr><th>Where</th><th>Program</th><th>Pays</th><th>Source</th></tr></thead><tbody>{body}</tbody></table></div>'


def blog_strip(keywords, skip=()):
    idx = json.loads((ROOT / "data" / "blog-index.json").read_text(encoding="utf-8"))
    hits = [p for s in idx["sections"] for p in s["posts"] if any(k in (p["title"] + " " + p["desc"]).lower() for k in keywords) and p["slug"] not in skip][:6]
    return lk.strip([(e(p["title"]), f"/blog/{p['slug']}/") for p in hits]) if hits else ""


def build(d):
    slug, up = d["slug"], d["upgrade"]
    path = f"/learn/{slug}/"
    progs = lk.open_programs(up, labelled=bool(d.get("labelled")))
    assert progs, f"no open programs for {up}"
    top = max(progs, key=lambda r: r["value"] * (0.73 if r["currency"] == "CAD" else 1))
    top_shown = top["shown"].replace("up to ", "").replace("Up to ", "")  # roughly comparable in US dollars
    nreg = len({r["code"] for r in progs})
    latest = max(r["checked"] for r in progs if r["checked"])
    nice = date.fromisoformat(latest).strftime("%B %-d, %Y")
    arts = lk.pick(d["services"][0], n=3, key=path)
    cards = "".join(lk.card(s, a) for s, a in arts)
    facts = (f'<div class="learn-facts"><div class="learn-fact"><b>{nreg}</b><span>provinces and states with an open {e(d["noun"])} rebate we track</span></div>'
             f'<div class="learn-fact"><b>{e(top["shown"].replace("up to ", ""))}</b><span>the biggest single amount: {e(top["program"])}, {e(top["region"])} ({top["currency"]})</span></div>'
             f'<div class="learn-fact"><b>{len(progs)}</b><span>open programs, each with its official page and the date we checked it</span></div></div>')
    quiz = lk.general_quiz(slug)  # ten questions about the device itself, no province or state named
    checks = "".join(f"<li>{c}</li>" for c in d["checks"])
    refs = list(d["refs"])
    for r in progs[:6]:
        if r["source"] and all(r["source"] != u for _, u in refs):
            refs.append((f"{r['region']}: {r['program']}", r["source"]))
    refs_html = ", ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a>' for t, u in refs)
    article = f"""<p class="byline">By <a href="/about">Sam Menard</a> · Rebate amounts checked {nice}</p>
{quiz}
{facts}
{d["intro"]}
<h2>What to check before you buy</h2>
<ul>{checks}</ul>
{d.get("extra", "")}
<h2>Open {e(d["noun"])} rebates, region by region</h2>
<p>Each row is an open program today. Amounts are the most a program pays, and many depend on your home, your income or your utility, so use the calculator for your own number.</p>
{table(progs)}
<p><a class="cta" href="/get-quotes/">See my rebates &rarr;</a></p>
<h2>Start with these guides</h2>
<div class="learn-grid">{cards}</div>
{blog_strip(d["keywords"], skip={s for s, _ in arts})}
<h2>Common questions</h2>
{kit.faq(d)}
<p style="font-size:14px;">Sources, read {nice}: {refs_html}.</p>"""
    w = kit.quality_gate(article, d, path, loose_refs=True, min_words=700)
    trail = [("Home", "/"), ("Learn", "/learn/"), (d["h1"], path)]
    lds = kit.ld_scripts([kit.article_ld(d["h1"], d["desc"], latest, path, published=d["published"]), kit.breadcrumb_ld(trail), kit.faq_ld(d)])
    crumb = kit.breadcrumb([("Home", "/"), ("Learn", "/learn/"), (e(d["h1"]), path)])
    hero = kit.hero({"badge": f"{nreg} regions with an open rebate", "h1": d["h1"], "lead": d["lead"]}).replace('class="hero"', 'class="hero learn-hero-photo"')
    kit.write_page(path, d["title"], d["desc"], lds, navfooter.render_nav("on", ""), crumb, hero, None, article,
                   navfooter.render_footer("on", "", "", path), extra_css=HUB_STYLE.replace("{img}", d["image"]))
    return path, w


def index(items):
    path = "/learn/"
    cards = "".join(
        f'<a class="learn-card" href="/learn/{d["slug"]}/"><div class="learn-tile t-{d["tone"]}"><img src="/assets/learn/{d["image"]}-640.webp" width="640" height="427" alt="{e(d["image_alt"])}" loading="lazy">'
        f'<span class="learn-kick">Learn</span><span class="learn-big">{e(d["tile"])}</span></div><h3>{e(d["h1"])}</h3><span class="learn-more">Read more →</span></a>' for d in items)
    article = (f'<p>Plain guides to each home energy upgrade, with every open rebate we track and the date we checked it. Pick an upgrade, then see the rebates for your city.</p>'
               f'<div class="learn-grid">{cards}</div><p><a class="cta" href="/get-quotes/">See my rebates &rarr;</a></p><h2>Quick reads and quizzes</h2>'
               f'<div class="learn-grid">{"".join(lk.card(s, a) for s, a in lk.pick("heat-pump", n=3, key=path))}</div>')
    d = {"badge": "Five upgrades, one place", "h1": "Learn about home energy upgrades", "lead": "Heat pumps, solar, batteries, insulation and water heating. What each one is, what to check, and what it pays where you live."}
    lds = kit.ld_scripts([kit.breadcrumb_ld([("Home", "/"), ("Learn", path)])])
    kit.write_page(path, "Learn About Home Energy Upgrades | HomePowerRebate", "Plain guides to heat pumps, solar, batteries, insulation and water heating, with every open rebate we track.", lds,
                   navfooter.render_nav("on", ""), kit.breadcrumb([("Home", "/"), ("Learn", path)]), kit.hero(d), None, article, navfooter.render_footer("on", "", "", path))
    return path


if __name__ == "__main__":
    items = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "data" / "learn-hubs").glob("*.json"))]
    for d in items:
        print("built", *build(d), "words")
    print("built", index(items))
