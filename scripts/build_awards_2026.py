#!/usr/bin/env python3
"""HomePowerRebate Top-Rated Installer Awards 2026: pick the winners and build the pages (2026-11-04).

Rules (docs/seo/awards-2026-plan.md): three equal winners per city and category, the three highest scores on the city ranking (the same published
score: Google rating weighted by review count) among companies that are eligible. A city needs at least MIN_COMPANIES ranked companies, and a winner
needs MIN_REVIEWS reviews, a MIN_RATING rating, a working phone or website, and must not be blocked or suppressed. If a company fails a test the next
one up takes its place. Winners are listed alphabetically, never as 1st, 2nd, 3rd.
Output: data/awards/2026.json (winners, scores, who was skipped and why, contact flags for the notices),
        /installers/awards/2026/ and one page per category (heat-pump, battery, solar).
LIVE stays False until launch: pages are noindex and out of the sitemap, with a visible draft notice. Ratings in the CSVs are from
September 2026; refresh them (Places lookup) before announcing and rerun this script.
Usage: python3 scripts/build_awards_2026.py, then python3 scripts/post_steps.py"""
import html
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_installer_rankings as br  # noqa: E402
import page_kit as kit  # noqa: E402
import regions as regions_mod  # noqa: E402

LIVE = False
YEAR = "2026"
MIN_COMPANIES, MIN_REVIEWS, MIN_RATING, WINNERS = 8, 50, 4.5, 3
CATS = {"heat-pump": ("Heat pumps", "heat pump installers"), "battery": ("Home batteries", "home battery installers"), "solar": ("Solar", "solar installers")}
SINGULAR = {"heat-pump": "Heat pump", "battery": "Home battery", "solar": "Solar"}
MAIN_OUTREACH = Path("/Users/sammenard/Downloads/Powerrebate/outreach")
e = html.escape
BASE = "/installers/awards/2026/"


def suppressed_emails():
    f = MAIN_OUTREACH / "suppress.txt"
    return {l.strip().lower() for l in f.read_text().splitlines() if l.strip()} if f.exists() else set()


def site_ok():
    ok = {}
    f = MAIN_OUTREACH / "website-audits.jsonl"
    if f.exists():
        for line in f.read_text().splitlines():
            d = json.loads(line)
            ok[(d["name"], d["city"])] = d.get("status") == "ok"
    return ok


def pick():
    rows = [r for r in br.load_rows() if r["service"] in CATS]
    sup, sites, hubs = suppressed_emails(), site_ok(), br.city_hubs()
    groups = defaultdict(list)
    for r in rows:
        groups[(r["service"], r["region"], r["city"])].append(r)
    out = {sv: [] for sv in CATS}
    audit = []
    data_date = max((r["updated"] for r in rows if r["updated"]), default="")
    for (sv, region, city), inst in sorted(groups.items()):
        if len(inst) < MIN_COMPANIES:
            continue
        hub = br.find_hub(hubs, region, city)
        slug = hub["slug"] if hub else br.slugify(city)
        label = hub["label"] if hub else city
        ranked = sorted(inst, key=lambda r: (-br.score(r), -r["reviews"]))
        elig, skipped = [], []
        for r in ranked:
            why = ("fewer than %d reviews" % MIN_REVIEWS if r["reviews"] < MIN_REVIEWS else "rating under %.1f" % MIN_RATING if r["rating"] < MIN_RATING
                   else "on the suppression list" if (r["email"] or "").strip().lower() in sup
                   else "no working phone or website" if not (r["phone"] or sites.get((r["name"], r["city"])))
                   else "")
            (skipped if why else elig).append((r, why))
        if len(elig) < WINNERS:
            audit.append({"service": sv, "region": region, "city": label, "result": "no award", "reason": f"only {len(elig)} eligible companies"})
            continue
        top = [r for r, _ in elig[:WINNERS]]
        raw_top = ranked[:WINNERS]
        replaced = [{"name": r["name"], "reason": w} for r, w in skipped if any(r is x for x in raw_top)]
        nxt = elig[WINNERS][0] if len(elig) > WINNERS else None
        gap = round(br.score(top[-1]) - br.score(nxt), 3) if nxt else None
        out[sv].append({
            "region": region, "city": label, "slug": slug, "ranking_url": f"/installers/{region}/{slug}/{sv}/", "companies": len(inst), "eligible": len(elig),
            "third_vs_fourth_gap": gap, "replaced": replaced,
            "winners": sorted(({"name": br.display_name(r["name"]), "rating": r["rating"], "reviews": r["reviews"], "score": round(br.score(r), 3),
                                "profile": br.profile_url(region, r["city"], r["name"]) or "", "has_email": "@" in (r["email"] or ""), "email": (r["email"] or "").strip(),
                                "website": r["website"]} for r in top), key=lambda w: w["name"].lower())})
    special = {}
    for sv in CATS:
        best = {}
        for r in rows:
            if r["service"] != sv or r["rating"] < MIN_RATING:
                continue
            if r["region"] not in best or r["reviews"] > best[r["region"]]["reviews"]:
                best[r["region"]] = r
        special[sv] = {rg: {"name": br.display_name(r["name"]), "city": r["city"], "reviews": r["reviews"], "rating": r["rating"]} for rg, r in best.items()}
    return out, special, audit, data_date


def region_groups(cities):
    names = {r["code"]: r for r in regions_mod.REGIONS}
    by = defaultdict(list)
    for c in cities:
        by[c["region"]].append(c)
    order = sorted(by, key=lambda k: (names[k]["country"] != "ca", names[k]["name"]))
    return [(names[k], sorted(by[k], key=lambda c: c["city"])) for k in order]


def winner_li(w):
    name = f'<a href="{w["profile"]}">{e(w["name"])}</a>' if w["profile"] else e(w["name"])
    return f'<li>{name} <span class="muted">{w["rating"]:.1f}★ · {w["reviews"]:,} reviews</span></li>'


def write(path, title, desc, h1, badge, lead, crumbs, body, faqs):
    trail = [("Home", "/")] + [(n, u or path) for n, u in crumbs]
    ld = [kit.breadcrumb_ld(trail), {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}]
    faq = "<h2>Questions about the awards</h2>" + "".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in faqs)
    hero = f'<section class="hero"><div class="wrap"><div class="amount-badge">{e(badge)}</div><h1>{e(h1)}</h1><p>{lead}</p></div></section>'
    kit.write_page(path, title, desc, kit.ld_scripts(ld), navfooter.render_nav("ca", ""), kit.breadcrumb(trail), hero, None, body + faq,
                   navfooter.render_footer("ca", "", "", path))
    if not LIVE:
        f = ROOT / path.strip("/") / "index.html"
        s = f.read_text(encoding="utf-8")
        s = s.replace('content="index, follow, max-snippet:-1, max-image-preview:large"', 'content="noindex, nofollow"', 1)
        f.write_text(s, encoding="utf-8")


def main():
    out, special, audit, data_date = pick()
    total_w = sum(len(c["winners"]) for v in out.values() for c in v)
    (ROOT / "data" / "awards").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "awards" / "2026.json").write_text(json.dumps({
        "year": YEAR, "live": LIVE, "ratings_collected": data_date, "rules": {"companies_per_city": MIN_COMPANIES, "winners_per_city": WINNERS, "min_reviews": MIN_REVIEWS,
                                                                      "min_rating": MIN_RATING}, "winners": out, "most_reviewed_by_region": special, "no_award": audit},
        indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        from datetime import date
        when = date.fromisoformat(data_date).strftime("%B %Y")
    except ValueError:
        when = data_date or "September 2026"
    draft = ("" if LIVE else f'<div class="callout"><p><strong>Draft, not published.</strong> Ratings were collected in {e(when)} and will be refreshed before the winners are announced. '
             'Do not share this page.</p></div>')
    rules = (f"<p>Each city page ranks local installers by their Google rating, weighted by how many reviews they have, so a company with hundreds of good reviews ranks above one with a handful. "
             f"The award goes to the <b>top {WINNERS}</b> in each city and category. Three equal winners, listed in alphabetical order, because the scores at the top are often very close and one company should not be called the best on a tiny difference.</p>"
             f"<ul><li>The city has at least {MIN_COMPANIES} ranked companies.</li><li>A winner has at least {MIN_REVIEWS} Google reviews and a rating of {MIN_RATING:.1f} or better.</li>"
             f"<li>Its phone number or website still works, and it has not asked to be removed or to stop hearing from us.</li>"
             f"<li>If a company does not meet a test, the next one on the ranking takes its place.</li><li>Nobody pays, applies or is asked to buy anything. Money never changes a ranking.</li></ul>"
             f"<p>Ratings and review counts are from Google Maps, collected {e(when)}.</p>")
    cats_html = ""
    for sv, (label, plural) in CATS.items():
        cs = out[sv]
        cats_html += (f'<div style="display:flex;gap:18px;align-items:center;margin:16px 0"><img src="/assets/awards/shield-{sv}-{YEAR}.svg" width="120" height="124" alt="Award Winner {YEAR} badge for {e(label.lower())}">'
                      f'<div><h3 style="margin:0"><a href="{BASE}{sv}/">{e(label)}: {sum(len(c["winners"]) for c in cs)} winners in {len(cs)} cities</a></h3>'
                      f'<p style="margin:4px 0 0">See the winners in your city and why they were picked.</p></div></div>')
    sp_rows = ""
    names = {r["code"]: r for r in regions_mod.REGIONS}
    for rg in sorted({rg for sv in special.values() for rg in sv}, key=lambda k: (names[k]["country"] != "ca", names[k]["name"])):
        cells = "".join(f'<td>{e(special[sv][rg]["name"])}<br><span class="muted">{e(special[sv][rg]["city"])}, {special[sv][rg]["reviews"]:,} reviews</span></td>' if rg in special[sv] else "<td>n/a</td>" for sv in CATS)
        sp_rows += f"<tr><td>{e(names[rg]['name'])}</td>{cells}</tr>"
    sp = ('<h2>Most reviewed in each province and state</h2><p>A simple count, not a score: the company with the most Google reviews, among those rated '
          f'{MIN_RATING:.1f} or better.</p><div class="table-wrap"><table class="hub-table"><thead><tr><th>Region</th>' + "".join(f"<th>{e(v[0])}</th>" for v in CATS.values())
          + f"</tr></thead><tbody>{sp_rows}</tbody></table></div>")
    faqs = [("How are the winners chosen?", f"The top {WINNERS} companies on each city's ranking in each category, using the same score as the city pages (Google rating weighted by review count), among companies with at least {MIN_REVIEWS} reviews and a {MIN_RATING:.1f} rating or better."),
            ("Can a company pay to win or to rank higher?", "No. Nobody pays to enter, to win or to rank higher, and nobody has to apply. There is nothing to buy."),
            ("Why three winners and not one?", "Because the scores at the top are often very close. A tiny gap in a rating is not a good reason to name one company the best, so the top three are all winners, listed in alphabetical order."),
            ("I think my company's rating or listing is wrong. What can I do?", "Email hello@homepowerrebate.com. Ratings and review counts come from Google Maps, so a fix to your Google listing shows up in the next refresh. If you do not want to be listed, we remove you the same day."),
            ("Why is my city missing?", f"A city needs at least {MIN_COMPANIES} ranked companies in a category before we name winners, and at least {WINNERS} of them must meet the review and rating tests.")]
    write(BASE, f"Top-Rated Installer Awards {YEAR}: Winners by City", f"Award winners for heat pump, home battery and solar installers in cities across Canada and the US, chosen from Google reviews. Nobody pays to win.",
          f"Top-Rated Installer Awards {YEAR}", f"{total_w:,} winners", "The best-reviewed local installers in each city, chosen from Google reviews. Nobody pays to enter, win or rank higher.",
          [("Installers", "/installers/"), ("Awards " + YEAR, None)],
          draft + f'<div class="callout"><p><strong>Short answer:</strong> {total_w:,} companies won in {sum(len(v) for v in out.values())} city and category lists. '
          f"Each winner ranked in the top {WINNERS} for its city, with {MIN_REVIEWS}+ reviews and a {MIN_RATING:.1f}+ rating. Nobody paid.</p></div><h2>The winners, by category</h2>{cats_html}"
          f"<h2>How we picked them</h2>{rules}{sp}", faqs)
    for sv, (label, plural) in CATS.items():
        cs = out[sv]
        close = sum(1 for c in cs if c["third_vs_fourth_gap"] is not None and c["third_vs_fourth_gap"] < 0.02)
        repl = sum(1 for c in cs if c["replaced"])
        body = draft + (f'<div style="display:flex;gap:18px;align-items:center;flex-wrap:wrap"><img src="/assets/awards/shield-{sv}-{YEAR}.svg" width="150" height="155" alt="Award Winner {YEAR} badge for {e(label.lower())}">'
                        f'<div class="callout" style="flex:1;min-width:260px"><p><strong>Short answer:</strong> {sum(len(c["winners"]) for c in cs):,} {e(plural)} won in {len(cs)} cities. '
                        f"In each city the top {WINNERS} on the ranking won, listed alphabetically.</p></div></div>")
        body += (f"<h2>Why these companies</h2>{rules}<p>For {e(label.lower())}: {len(cs)} cities had enough ranked companies and enough that met the tests. "
                 f"In {close} of them the third and fourth place were within 0.02 of each other, which is why we do not rank the winners against each other. "
                 f"In {repl} cities a company that would have placed in the top {WINNERS} was skipped because it failed a test, and the next one took its place.</p>")
        body += f"<h2>Winners by city</h2>"
        for rg, cl in region_groups(cs):
            body += f'<h3 id="{rg["code"]}">{e(rg["name"])} ({len(cl)} cities)</h3><div class="table-wrap"><table class="hub-table"><thead><tr><th>City</th><th>Award winners (alphabetical)</th></tr></thead><tbody>'
            for c in cl:
                body += (f'<tr><td><a href="{c["ranking_url"]}"><b>{e(c["city"])}</b></a><br><span class="muted">{c["companies"]} companies ranked</span></td>'
                         f'<td><ul style="margin:0;padding-left:18px">{"".join(winner_li(w) for w in c["winners"])}</ul></td></tr>')
            body += "</tbody></table></div>"
        write(f"{BASE}{sv}/", f"{SINGULAR[sv]} Installer Award Winners {YEAR}: By City", f"The top-rated {plural} in {len(cs)} cities, chosen from Google reviews for the {YEAR} awards. Nobody pays to win.",
              f"{SINGULAR[sv]} installer award winners", f"{sum(len(c['winners']) for c in cs):,} winners", f"The top {WINNERS} {plural} in {len(cs)} cities, chosen from Google reviews.",
              [("Installers", "/installers/"), ("Awards " + YEAR, BASE), (label, None)], body, faqs[:4])
    for sv, cs in out.items():
        print(sv, len(cs), "cities,", sum(len(c["winners"]) for c in cs), "winners,", sum(1 for c in cs if c["replaced"]), "cities with a skipped company")
    print(len(audit), "city lists with no award;", "ratings collected", data_date, "; LIVE =", LIVE)


if __name__ == "__main__":
    main()
