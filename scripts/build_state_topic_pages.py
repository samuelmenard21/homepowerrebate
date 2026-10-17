#!/usr/bin/env python3
"""State/province topic pages, e.g. /us/ma/battery/ or /ca/ab/ev-charger/, from hand-written data/state-topics/<region>-<topic>.json.
One honest page per state answers state-level searches better than near-identical city copies (those city URLs redirect here).
Cards name verified facts; each card's status pill comes from its first fact. Same quality gate as build_ca_pages.py (750 words).
Usage: python3 scripts/build_state_topic_pages.py [name ...]"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_ca_pages as ca  # noqa: E402
import page_kit as kit  # noqa: E402  (shared page components)

e = html.escape
FACTS = ca.FACTS


def build(name):
    d = json.loads((ROOT / "data/state-topics" / f"{name}.json").read_text())
    path, nav, region = d["path"], d["nav"], d["region"]
    hub_name, hub = d["hub_name"], d["hub"]
    fids = kit.fact_ids(d)
    for cd in d["cards"]:
        if cd.get("facts") and "status" not in cd:
            cd["status"] = FACTS[cd["facts"][0]]["status"]
    iso, when = kit.checked(fids)
    links = "".join(f'<li><a href="{u}">{e(t)}</a>: {b}</li>\n' for t, u, b in d["links"])
    steps = "".join(f"<li>{s}</li>\n" for s in d["claim_steps"])
    calc = d.get("calc") or f"/calculator/{region}/"
    calc_label = d.get("calc_label") or f"{hub_name} rebate calculator"
    article = f"""<h2>{d['cards_heading']}</h2>
{d['cards_intro']}
<div class="rebate-grid">
{kit.cards(d)}
</div>
{d.get('after_cards', '')}
{kit.sections(d)}
<h2>{d['claim_heading']}</h2>
<ol>
{steps}</ol>
<h2>More for {e(hub_name)} homes</h2>
<ul>
<li><a href="{hub}">{e(hub_name)} home rebates: every program in one place</a></li>
{links}</ul>
<div class="callout"><strong>Want a number for your home?</strong> Run our <a href="{calc}" style="color:var(--teal,#0d4f5c); font-weight:600;">{e(calc_label)}</a>, or <a href="/get-quotes/" style="color:var(--teal,#0d4f5c); font-weight:600;">get a plan emailed with the top-rated installers near you</a>.</div>
<h2>Common questions</h2>
{kit.faq(d)}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read {when}: {kit.sources(d)}.</p>"""
    w = kit.quality_gate(article, d, path, loose_refs=True)
    trail = [("Home", "/"), (hub_name, hub), (d["short"], path)]
    lds = kit.ld_scripts([kit.article_ld(d["title"], d["desc"], iso, path), kit.breadcrumb_ld(trail, home_slash=True), kit.faq_ld(d)])
    crumb = kit.breadcrumb([("Home", "/"), (e(hub_name), hub), (e(d["short"]), path)])
    kit.write_page(path, d["title"], d["desc"], lds, navfooter.render_nav(nav, ""), crumb, kit.hero(d), None, article,
                   navfooter.render_footer(nav, "", "", path), d.get("alternates", ""))
    return path, w


if __name__ == "__main__":
    only = set(sys.argv[1:])
    for f in sorted((ROOT / "data/state-topics").glob("*.json")):
        if only and f.stem not in only:
            continue
        p, w = build(f.stem)
        print("built", p, w, "words")
