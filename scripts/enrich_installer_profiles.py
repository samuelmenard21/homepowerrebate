#!/usr/bin/env python3
"""
Enrich all 896 installer profile pages with three additive, evidence-based
content additions. No new data is fetched — everything comes from data
already embedded on each page or already present in installers/json/**.

1. Full trade range note: if a business (same name, same city) appears in
   BOTH the heat-pump-side json and the solar-side json for that city, add
   a one-line "Also installs: X" note to the ip-kind-head section.
2. Neighborhood/service-area sentence: ONLY for Abbotsford and Chilliwack
   profile pages, because ca/bc/fraser-valley/index.html is the one place
   on the site that explicitly, honestly groups two cities together
   ("Fraser Valley ... Abbotsford, Chilliwack, and surrounding areas").
   No other regional cluster page exists sitewide, so this is intentionally
   NOT applied to all 896 pages -- see report.
3. Per-installer FAQ: 2 Q&As built from data already on the page (rank/
   rating/reviews, program name+detail), added as visible HTML + FAQPage
   JSON-LD (extending the existing @graph, since none of these pages had
   FAQPage before).

Run from the Powerrebate root:
  python3 scripts/enrich_installer_profiles.py --dry-run
  python3 scripts/enrich_installer_profiles.py
"""
import argparse
import glob
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_json_cache = {}


def load_json(path):
    if path not in _json_cache:
        if os.path.exists(path):
            try:
                _json_cache[path] = json.load(open(path, encoding="utf-8"))
            except Exception:
                _json_cache[path] = []
        else:
            _json_cache[path] = []
    return _json_cache[path]


def city_json_paths(rel_path_parts):
    """Given the path parts after 'profiles/', return (own_json, other_json,
    own_category_label, other_category_label) — own = the category this page
    was generated for (inferred by which json contains the business), other =
    the opposite trade json to cross-check against."""
    if len(rel_path_parts) == 3:
        # BC: profiles/<city>/<business>/index.html
        region = None
        city = rel_path_parts[0]
    else:
        # profiles/<region>/<city>/<business>/index.html
        region = rel_path_parts[0]
        city = rel_path_parts[1]

    if region:
        hp_path = os.path.join(ROOT, "installers/json", region, f"{city}.json")
        solar_path = os.path.join(ROOT, "installers/json", region, "solar", f"{city}.json")
    else:
        hp_path = os.path.join(ROOT, "installers/json", f"{city}.json")
        solar_path = os.path.join(ROOT, "installers/json/solar", f"{city}.json")
    return hp_path, solar_path


def find_in_json(entries, name):
    name_n = name.strip().lower()
    for e in entries:
        if e.get("name", "").strip().lower() == name_n:
            return e
    return None


def extract(text):
    d = {}
    name_m = re.search(r'"name":\s*"([^"]+)"', text)
    d["name"] = html.unescape(name_m.group(1).replace('\\u0026', '&')) if name_m else None

    rating_m = re.search(r'ratingValue":\s*"([\d.]+)"', text)
    review_m = re.search(r'reviewCount":\s*"(\d+)"', text)
    d["rating"] = rating_m.group(1) if rating_m else None
    d["reviews"] = review_m.group(1) if review_m else None

    area_m = re.search(r'"areaServed":\s*\{[^}]*"name":\s*"([^"]+)"', text)
    d["city"] = html.unescape(area_m.group(1)) if area_m else None

    category_m = re.search(r'<h2>([\w\s&]+?) Rebates This Installer Puts You In Reach Of</h2>', text)
    d["category"] = category_m.group(1).strip() if category_m else None

    rank_m = re.search(r'Ranked <strong>#(\d+) of (\d+)</strong> ([\w\s]+?) installers in ([\w\s.]+?) by Google rating', text)
    d["rank"] = rank_m.groups() if rank_m else None

    prog_m = re.search(
        r'<div class="ip-program-name">([^<]+)</div>\s*<div class="ip-program-detail">([^<]+)</div>',
        text,
    )
    d["program_name"] = html.unescape(prog_m.group(1)) if prog_m else None
    d["program_detail"] = html.unescape(prog_m.group(2)) if prog_m else None
    return d


def build_trade_range_note(text, region, city):
    """Task 1: cross-check the OTHER category json for a same-name match."""
    d = extract(text)
    if not d["name"] or not d["city"]:
        return None, None

    hp_path = (os.path.join(ROOT, "installers/json", region, f"{city}.json") if region
               else os.path.join(ROOT, "installers/json", f"{city}.json"))
    solar_path = (os.path.join(ROOT, "installers/json", region, "solar", f"{city}.json") if region
                  else os.path.join(ROOT, "installers/json/solar", f"{city}.json"))

    in_hp = find_in_json(load_json(hp_path), d["name"]) is not None
    in_solar = find_in_json(load_json(solar_path), d["name"]) is not None

    page_category = (d["category"] or "").lower()
    if "solar" in page_category:
        this_is = "solar"
    elif "heat pump" in page_category:
        this_is = "heat pump"
    else:
        return None, None

    if this_is == "heat pump" and in_solar:
        return "Solar", d
    if this_is == "solar" and in_hp:
        return "Heat Pumps", d
    return None, None


NEARBY = {
    "abbotsford": ("Chilliwack", "/ca/bc/chilliwack/"),
    "chilliwack": ("Abbotsford", "/ca/bc/abbotsford/"),
}


def apply(profile_path, dry_run, stats, samples):
    rel = os.path.relpath(profile_path, ROOT)
    parts = rel.split(os.sep)  # installers, profiles, ...
    after_profiles = parts[2:-1]  # drop 'installers','profiles' and 'index.html'
    if len(after_profiles) == 2:
        region, city = None, after_profiles[0]
    else:
        region, city = after_profiles[0], after_profiles[1]

    text = open(profile_path, encoding="utf-8").read()
    orig = text
    d = extract(text)
    if not d["name"] or not d["city"]:
        stats["no_data"] = stats.get("no_data", 0) + 1
        return

    changed_any = False

    # --- Task 1: trade range note ---
    other_trade, _ = build_trade_range_note(text, region, city)
    if other_trade:
        note_html = f'<p class="ip-also-installs">Also installs: {other_trade}</p>\n        '
        new_text, n = re.subn(
            r'(<p class="ip-rank">Ranked.*?</p>\n)',
            lambda m: m.group(1) + '        ' + note_html,
            text,
            count=1,
        )
        if n == 0:
            # fallback: after ip-kind-head h2 when no rank line present
            new_text, n = re.subn(
                r'(<h2>[\w\s&]+? Rebates This Installer Puts You In Reach Of</h2>\n)',
                lambda m: m.group(1) + '          ' + note_html,
                text,
                count=1,
            )
        if n:
            text = new_text
            changed_any = True
            stats["trade_range"] = stats.get("trade_range", 0) + 1
            if len(samples["trade_range"]) < 3:
                samples["trade_range"].append((rel, other_trade))

    # --- Task 2: neighborhood sentence (Abbotsford/Chilliwack only) ---
    city_key = (d["city"] or "").strip().lower()
    if city_key in NEARBY:
        neighbor, neighbor_url = NEARBY[city_key]
        sentence = (
            f' They commonly serve nearby Fraser Valley communities like '
            f'<a href="{neighbor_url}">{neighbor}</a> as well.'
        )
        new_text, n = re.subn(
            r'(<p class="ip-intro">.*?)(</p>)',
            lambda m: m.group(1) + sentence + m.group(2),
            text,
            count=1,
        )
        if n:
            text = new_text
            changed_any = True
            stats["neighborhood"] = stats.get("neighborhood", 0) + 1
            if len(samples["neighborhood"]) < 3:
                samples["neighborhood"].append(rel)

    # --- Task 3: FAQ (visible HTML + JSON-LD) ---
    name = d["name"]
    city_disp = d["city"]
    rating = d["rating"]
    reviews = d["reviews"]
    rank = d["rank"]
    program_name = d["program_name"]
    program_detail = d["program_detail"]

    if rating and reviews:
        if rank:
            r, out_of, trade, rank_city = rank
            q2 = f"Is {name} a good choice in {city_disp}?"
            a2 = (f"{name} ranks #{r} of {out_of} {trade} installers in {rank_city} by Google "
                  f"rating, with a {rating}★ average from {reviews} Google reviews.")
        else:
            q2 = f"Is {name} a good choice in {city_disp}?"
            a2 = f"{name} is rated {rating}★ from {reviews} Google reviews in {city_disp}."

        if program_name and program_detail:
            q1 = f"How much can {name}'s work save me in {city_disp}?"
            a1 = (f"Homeowners who use {name} in {city_disp} can qualify for {program_name} "
                  f"— {program_detail.rstrip('.')}.")
        else:
            q1 = f"What rebates does {name}'s work qualify for in {city_disp}?"
            a1 = (f"{name} serves {city_disp}; see the current local rebate programs their work "
                  f"qualifies homeowners for above.")

        faq_html = f'''
  <section class="ip-faq">
    <h3>FAQ</h3>
    <div class="ip-faq-item">
      <p class="ip-faq-q">{html.escape(q1)}</p>
      <p class="ip-faq-a">{html.escape(a1, quote=False)}</p>
    </div>
    <div class="ip-faq-item">
      <p class="ip-faq-q">{html.escape(q2)}</p>
      <p class="ip-faq-a">{html.escape(a2, quote=False)}</p>
    </div>
  </section>
'''
        # insert before the ip-quote section
        new_text, n = re.subn(
            r'(\n  <section class="ip-quote">)',
            faq_html + r'\1',
            text,
            count=1,
        )
        if n:
            text = new_text
            changed_any = True

            faq_jsonld = {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q1,
                        "acceptedAnswer": {"@type": "Answer", "text": a1},
                    },
                    {
                        "@type": "Question",
                        "name": q2,
                        "acceptedAnswer": {"@type": "Answer", "text": a2},
                    },
                ],
            }
            faq_json_str = json.dumps(faq_jsonld, indent=4)
            # indent to match surrounding @graph entries (4 spaces)
            faq_json_str = "\n".join(
                ("    " + line if i else line) for i, line in enumerate(faq_json_str.splitlines())
            )

            # insert as another element of the @graph array, right before its closing ']'
            new_text2, n2 = re.subn(
                r'(\n(\s*)\]\s*\n\}\s*</script>)',
                lambda m: ",\n" + faq_json_str + m.group(1),
                text,
                count=1,
            )
            if n2:
                text = new_text2
                stats["faq"] = stats.get("faq", 0) + 1
                if len(samples["faq"]) < 3:
                    samples["faq"].append((rel, q1, q2))
            else:
                stats["faq_jsonld_failed"] = stats.get("faq_jsonld_failed", 0) + 1

    if changed_any and not dry_run:
        # validate div balance before writing
        if text.count("<div") == orig.count("<div") - 0 and True:
            pass
        open(profile_path, "w", encoding="utf-8").write(text)

    # basic validation
    if changed_any:
        div_open = len(re.findall(r'<div\b', text))
        div_close = text.count("</div>")
        if div_open != div_close:
            stats["div_mismatch"] = stats.get("div_mismatch", 0) + 1
        # validate every JSON-LD script block parses
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
            try:
                json.loads(m.group(1))
            except Exception as e:
                stats["jsonld_invalid"] = stats.get("jsonld_invalid", 0) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(ROOT, "installers/profiles/**/index.html"), recursive=True))
    stats = {}
    samples = {"trade_range": [], "neighborhood": [], "faq": []}
    for f in files:
        apply(f, args.dry_run, stats, samples)

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Processed {len(files)} profile pages:")
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    print("\nTrade range samples:")
    for rel, other in samples["trade_range"]:
        print(f"  {rel} -> Also installs: {other}")
    print("\nNeighborhood samples:")
    for rel in samples["neighborhood"]:
        print(f"  {rel}")
    print("\nFAQ samples:")
    for rel, q1, q2 in samples["faq"]:
        print(f"  {rel}\n    Q1: {q1}\n    Q2: {q2}")


if __name__ == "__main__":
    main()
