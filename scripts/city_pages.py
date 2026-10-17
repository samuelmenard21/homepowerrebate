#!/usr/bin/env python3
"""One engine for city category pages and city hubs in every region (/ca/bc/<city>/<category>/, /us/ma/<city>/, ...).

Prose is hand-written per page in data/<code>/pages/<city>/<category>.json. Everything else comes from data:
- the region (name, hub path, calculator label) from data/regions.json;
- the page settings from the region's "city_pages" block in data/regions.json: categories built, city names, region-wide
  pages to link, installer lists, program links in the sources line, the quote link and any extra quality bans;
- markup from scripts/page_kit.py (shared with the topic and program pages).
The region scripts (build_bc_pages.py, ...) are thin wrappers: python3 scripts/build_bc_pages.py [city ...] [--hubs].
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_installer_rankings as rank  # noqa: E402
import page_kit as kit  # noqa: E402
import regions  # noqa: E402

e = html.escape
# one label per category for every region; the order is the order of the sibling links
LABEL = {"insulation": "Insulation", "windows": "Windows & Doors", "windows-doors": "Windows & Doors", "water-heater": "Water Heater", "heat-pump": "Heat Pump",
         "solar": "Solar", "battery": "Battery Storage", "ev-charger": "EV Charger", "smart-thermostats": "Smart Thermostat", "appliances": "Appliance",
         "hrv": "HRV & Ventilation"}
_ROWS = {}


def rows_for(code):
    if code not in _ROWS:
        _ROWS[code] = [r for r in rank.load_rows() if r["region"] == code]
    return _ROWS[code]


class Region:
    def __init__(self, code):
        r = regions.BY_CODE[code]
        self.code, self.name, self.path = code, r["name"], r["path"]
        self.cfg = r["city_pages"]
        self.calc_label = self.cfg.get("calc_label", r.get("calc_label", r["name"]))
        self.labels = {k: v for k, v in LABEL.items() if k in self.cfg.get("label_keys", LABEL)}
        self.names = self.cfg["names"]

    # ---- installers ----
    def installers(self, slug, cat):
        rule = self.cfg.get("installers", {}).get(cat)
        if not rule:
            return []
        if rule["from"] == "json":
            p = ROOT / "installers/json" / f"{slug}.json"
            rows = [r for r in json.loads(p.read_text()) if r.get("rating") and r.get("reviews", 0) >= rule["min"]] if p.exists() else []
        else:
            rows = [r for r in rows_for(self.code) if r["service"] == rule["service"] and rank.slugify(r["city"]) == slug and r.get("reviews", 0) >= rule["min"]]
        rows.sort(key=lambda r: -rank.score(r))
        return rows[:5]

    def installer_html(self, slug, name, cat, intro):
        rows = self.installers(slug, cat)
        if not rows:
            return ""
        out = ""
        for r in rows:
            site = re.sub(r"[?&]utm_[^&]*", "", r.get("website") or "").rstrip("?")
            link = f'<a class="site-link" href="{e(site)}" target="_blank" rel="noopener">Visit site &rarr;</a>' if site else ""
            out += f'<div class="installer-card"><div><div class="name">{e(r["name"])}</div><div class="stars">&#9733; {r["rating"]:.1f} ({r["reviews"]:,} Google reviews)</div></div>{link}</div>\n'
        more_kinds = self.cfg.get("installers_more", ["insulation", "heat-pump", "solar", "battery"])
        kind = cat if cat in more_kinds else "heat-pump"
        idir = regions.BY_CODE[self.code].get("installers_dir", self.code)
        more = (f'<p style="margin-top:8px;"><a href="/installers/{idir}/{slug}/{kind}/">See all {e(name)} installers &rarr;</a></p>'
                if (ROOT / f"installers/{idir}/{slug}/{kind}/index.html").exists() else "")
        return f"<h2>Top-rated installers in {e(name)}</h2><p>{intro}</p>\n{out}{more}"

    # ---- links ----
    def siblings(self, slug, cat):
        if self.cfg.get("siblings_from") == "data":
            return [k for k in self.labels if k != cat and (ROOT / "data" / self.code / "pages" / slug / f"{k}.json").exists()]
        return [k for k in self.labels if k != cat and (ROOT / self.path / slug / k / "index.html").exists()]

    def region_pages(self, cat):
        rp = self.cfg.get("region_pages")
        if not rp:
            return []
        if rp.get("exists") == "data":
            return [(k, t) for k, t in rp["pages"] if k != cat and (ROOT / "data/state-topics" / f"{self.code}-{k}.json").exists()]
        return [(k, t) for k, t in rp["pages"] if k != cat and (ROOT / self.path / k / "index.html").exists()]

    def program_links(self, slug, cat, d):
        p = self.cfg["program_links"]
        if "from_page" in p:
            u, t = d.get("program_url", p["from_page"][0]), d.get("program_label", p["from_page"][1])
            return f'<a href="{u}">{e(t)} &rarr;</a>'
        links = p.get("cities", {}).get(slug, p.get("default", []))
        out = " ".join(f'<a href="{u}">{t} &rarr;</a>' for u, t in links)
        out += "".join(f' <a href="{u}">{t} &rarr;</a>' for u, t in p.get("categories", {}).get(cat, []))
        return out

    # ---- page ----
    def build(self, slug, cat):
        name = self.names[slug]
        pj = ROOT / "data" / self.code / "pages" / slug / f"{cat}.json"
        if not pj.exists():
            return None
        d = json.loads(pj.read_text())
        hub = f"/{self.path}/{slug}/"
        is_hub = cat == "index"
        path = hub if is_hub else f"{hub}{cat}/"
        fids = kit.fact_ids(d)
        if self.cfg.get("card_status_from_facts"):
            for cd in d["cards"]:
                if cd.get("facts") and "status" not in cd:
                    cd["status"] = kit.FACTS[cd["facts"][0]]["status"]
        iso, when = kit.checked(fids)
        sibs = self.siblings(slug, cat)
        rp = self.region_pages(cat)
        rpc = self.cfg.get("region_pages", {})
        sib = "".join(f'<span style="margin-right:14px;"><a href="{hub}{k}/">{self.labels[k]} Rebates in {e(name)}</a></span>\n' for k in sibs)
        sib += "".join('<span style="margin-right:14px;">' + rpc["link"].format(url=f"/{self.path}/{k}/", t=t, tl=t.lower()) + "</span>\n" for k, t in rp)
        show_guides = is_hub and (sibs or not self.cfg.get("guides_need_siblings"))
        guides = ("<h2>Every rebate guide for " + e(name) + "</h2><ul>" + "".join(f'<li><a href="{hub}{k}/">{self.labels[k]} rebates in {e(name)}</a></li>' for k in sibs)
                  + "".join("<li>" + rpc["guide"].format(url=f"/{self.path}/{k}/", t=t, tl=t.lower()) + "</li>" for k, t in rp) + "</ul>") if show_guides else ""
        inst = "" if d.get("no_installers") else self.installer_html(slug, name, cat, d.get("installers_intro", ""))
        q = self.cfg.get("quotes", "/get-quotes/?province={code}&amp;city={slug}")  # null: no quote link (the calculator box asks for the city)
        quotes = q.format(code=self.code, slug=slug) if q else None
        article = f"""<h2>{d['cards_heading']}</h2>
{d['cards_intro']}
<div class="rebate-grid">
{kit.cards(d)}
</div>
{d.get('after_cards', '')}
{kit.sections(d)}
{guides}
{inst}
{kit.claim(d)}
{kit.callout(f"/calculator/{self.code}/", self.calc_label, quotes, name)}
<h2>Common questions</h2>
{kit.faq(d)}
<h2>What to do next</h2>
{d['next']}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. Sources, last read {when}: {kit.sources(d)}. <a href="{hub}">All {e(name)} rebates &rarr;</a> {self.program_links(slug, cat, d)}</p>"""
        bans = [((lambda a, b=b: re.search(b["if"], a) and not any(u in a for u in b.get("unless", []))), b["msg"]) for b in self.cfg.get("bans", [])]
        w = kit.quality_gate(article, d, path, bans)
        trail = [("Home", "/"), (self.name, f"/{self.path}/"), (name, hub)] + ([] if is_hub else [(self.labels[cat], path)])
        lds = kit.ld_scripts([kit.article_ld(d["title"], d["desc"], iso, path), kit.breadcrumb_ld(trail), kit.faq_ld(d)])
        crumb = kit.breadcrumb([(e(n), p) for n, p in trail[:-1]] + [(e(name) if is_hub else self.labels[cat], path)])
        top = "" if is_hub else f'<span style="margin-right:14px;"><a href="{hub}">&larr; Back to {e(name)} rebate hub</a></span>' + "\n" + sib
        kit.write_page(path, d["title"], d["desc"], lds, navfooter.render_nav(self.code, slug), crumb, kit.hero(d), top, article,
                       navfooter.render_footer(self.code, slug, name, path))
        return path, w


def main(code, argv=None):
    argv = sys.argv[1:] if argv is None else argv
    reg = Region(code)
    only = {a for a in argv if not a.startswith("--")}
    cats = ["index"] if "--hubs" in argv else reg.cfg["built"]
    for slug in reg.names:
        if only and slug not in only:
            continue
        for cat in cats:
            r = reg.build(slug, cat)
            if r:
                print("built", r[0], r[1], "words")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
