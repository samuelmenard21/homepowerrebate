#!/usr/bin/env python3
"""
build_powerscore_compare.py — generates static city-vs-city PowerScore comparison
pages at powerscore/compare/<city-a>-vs-<city-b>/index.html.

Design decisions (deliberate, to avoid a thin-content SEO trap):
  - We do NOT generate every possible city pair (99 cities -> ~4,850 pairs, almost
    all of them thin near-duplicates nobody searches for). Instead:
  - SAME-REGION pairs: for every region with 2+ cities, we compare each of that
    region's top-N non-#1 cities against the region's #1 city (PowerScore is
    normalized within a region, so within-region comparisons are apples-to-apples).
  - CURATED CROSS-REGION pairs: a short hand-picked list of major-metro pairs a
    homeowner would actually search for (e.g. "Vancouver vs Toronto"). Because
    PowerScore's dollar_score is normalized against each city's OWN region's max,
    cross-region scores are NOT directly comparable in the same way same-region
    scores are — every cross-region page says so explicitly, in the intro copy
    and in one FAQ answer.
  - Total pages generated: printed at the end of a run. Target range ~40-60.

Usage:
  python3 scripts/build_powerscore_compare.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "powerscore-data.json"
POWERSCORE_INDEX = ROOT / "powerscore" / "index.html"
COMPARE_DIR = ROOT / "powerscore" / "compare"
SITEMAP_PATH = ROOT / "sitemap.xml"

SAME_REGION_CAP = 6  # top-N non-#1 cities compared against each region's #1

CATEGORY_EMOJI = {
    "heat-pump": "\U0001F525",
    "insulation": "\U0001F9CA",
    "solar": "☀️",
    "battery": "\U0001F50B",
    "water-heater": "\U0001F6BF",
    "smart-thermostats": "\U0001F321️",
    "ev-charger": "\U0001F697",
    "windows-doors": "\U0001FAB5",
}

# Curated well-known cross-region metro pairs a homeowner would actually search.
# Each entry: (region_key_a, slug_a, region_key_b, slug_b)
CURATED_CROSS_REGION_PAIRS = [
    ("ca/bc", "vancouver", "ca/on", "toronto"),
    ("ca/bc", "vancouver", "us/ca", "los-angeles/los-angeles"),
    ("ca/on", "toronto", "us/ny", "con-edison/new-york-city"),
    ("ca/on", "toronto", "us/ma", "boston"),
    ("us/ny", "con-edison/new-york-city", "us/ca", "los-angeles/los-angeles"),
    ("us/ma", "boston", "us/ny", "con-edison/new-york-city"),
    ("ca/ab", "calgary", "ca/bc", "vancouver"),
    ("ca/ns", "halifax", "ca/on", "toronto"),
    ("ca/ab", "edmonton", "ca/on", "toronto"),
    ("us/ca", "bay-area/san-francisco", "ca/bc", "vancouver"),
    ("ca/on", "ottawa", "ca/bc", "victoria"),
    ("ca/bc", "vancouver", "us/ma", "boston"),
    ("ca/on", "toronto", "us/ca", "bay-area/san-francisco"),
    ("ca/ns", "halifax", "us/ma", "boston"),
]


def load_data():
    with open(DATA_PATH) as f:
        return json.load(f)


def region_city_list(region_key, region):
    """Return list of (slug, city_dict) sorted by overall desc."""
    cities = region.get("cities", {})
    items = list(cities.items())
    items.sort(key=lambda kv: -kv[1]["overall"])
    return items


def get_city(data, region_key, slug):
    region = data["regions"][region_key]
    city = region["cities"][slug]
    return {
        "region_key": region_key,
        "region_label": region["label"],
        "country": region["country"],
        "slug": slug,
        **city,
    }


def slugify_pair_component(region_key, slug):
    """Turn region_key/slug into a URL-safe city slug, e.g. us/ny/con-edison/new-york-city -> new-york-city."""
    # use the last path segment of slug for readability, but disambiguate with region prefix
    last = slug.rsplit("/", 1)[-1]
    return last


def build_pairs(data):
    pairs = []  # list of (city_a_ref, city_b_ref, same_region: bool)
    seen = set()

    def add_pair(ref_a, ref_b, same_region):
        key = tuple(sorted([f"{ref_a[0]}/{ref_a[1]}", f"{ref_b[0]}/{ref_b[1]}"]))
        if key in seen:
            return
        seen.add(key)
        pairs.append((ref_a, ref_b, same_region))

    # same-region: region #1 vs top-N challengers
    for region_key, region in data["regions"].items():
        ranked = region_city_list(region_key, region)
        if len(ranked) < 2:
            continue
        top_slug, top_city = ranked[0]
        challengers = ranked[1:1 + SAME_REGION_CAP]
        for slug, city in challengers:
            add_pair((region_key, top_slug), (region_key, slug), True)

    # curated cross-region
    for ra, sa, rb, sb in CURATED_CROSS_REGION_PAIRS:
        add_pair((ra, sa), (rb, sb), False)

    return pairs


def score_band(score):
    if score >= 75:
        return "great", "band-great"
    if score >= 50:
        return "solid", "band-great"
    if score >= 25:
        return "limited", "band-mid"
    return "thin", "band-low"


def fmt_money(v):
    if not v:
        return "$0"
    return f"${v:,.0f}"


def build_faq(city_a, city_b, same_region):
    a_label, b_label = city_a["label"], city_b["label"]
    a_overall, b_overall = city_a["overall"], city_b["overall"]
    winner = city_a if a_overall >= b_overall else city_b
    loser = city_b if winner is city_a else city_a

    faqs = []
    if a_overall == b_overall:
        faqs.append({
            "q": f"Which city has the better overall PowerScore, {a_label} or {b_label}?",
            "a": (
                f"{a_label} and {b_label} are tied on overall PowerScore, both at {a_overall}/100. "
                f"PowerScore is a 0-100 average of 8 rebate categories built from real published rebate "
                f"amounts, program status, and how many programs stack — check the category breakdown "
                f"below to see where each city is actually stronger."
            ),
        })
    else:
        faqs.append({
            "q": f"Which city has the better overall PowerScore, {a_label} or {b_label}?",
            "a": (
                f"{winner['label']} has the higher overall PowerScore at {winner['overall']}/100, "
                f"compared to {loser['label']}'s {loser['overall']}/100. PowerScore is a 0-100 average "
                f"of 8 rebate categories built from real published rebate amounts, program status, and "
                f"how many programs stack."
            ),
        })

    # best category for each city
    a_best = max(city_a["categories"].items(), key=lambda kv: kv[1]["score"])
    b_best = max(city_b["categories"].items(), key=lambda kv: kv[1]["score"])
    solar_a = city_a["categories"].get("solar", {}).get("score", 0)
    solar_b = city_b["categories"].get("solar", {}).get("score", 0)
    if solar_a == solar_b:
        solar_line = (
            f"{a_label} and {b_label} are tied on solar, both at {solar_a:.1f} out of 100."
        )
    else:
        solar_winner = a_label if solar_a >= solar_b else b_label
        solar_line = (
            f"{solar_winner} scores higher on solar, {max(solar_a, solar_b):.1f} vs "
            f"{min(solar_a, solar_b):.1f} out of 100."
        )
    faqs.append({
        "q": f"Which city has better solar rebates, {a_label} or {b_label}?",
        "a": (
            f"{solar_line} {city_a['label']}'s strongest category overall is "
            f"{a_best[0].replace('-', ' ')} at {a_best[1]['score']:.1f}, while {city_b['label']}'s strongest "
            f"is {b_best[0].replace('-', ' ')} at {b_best[1]['score']:.1f}."
        ),
    })

    if same_region:
        faqs.append({
            "q": f"Is it fair to compare {a_label} and {b_label} directly?",
            "a": (
                f"Yes — {a_label} and {b_label} are both in {city_a['region_label']}, so their PowerScores "
                f"are calculated on the same regional scale (each city's dollar value is normalized against "
                f"the strongest program found anywhere in {city_a['region_label']}), making this an apples-to-apples comparison."
            ),
        })
    else:
        faqs.append({
            "q": f"Is it fair to compare {a_label} and {b_label} directly, since they're in different regions?",
            "a": (
                f"Not entirely — {a_label} is in {city_a['region_label']} and {b_label} is in {city_b['region_label']}, "
                f"and PowerScore's dollar-value component is normalized against the strongest program in each city's "
                f"own region, not against a shared national or continental scale. Treat this comparison as directional "
                f"(which city currently has more, better-funded, more stackable rebate programs), not as a precise "
                f"apples-to-apples number the way a same-region comparison would be."
            ),
        })

    return faqs[:3]


NAV_HTML = None
FOOTER_HTML = None
ROOT_STYLE_VARS = None


def extract_shared_markup():
    global NAV_HTML, FOOTER_HTML, ROOT_STYLE_VARS
    text = POWERSCORE_INDEX.read_text()

    nav_match = re.search(
        r'(<!-- ============================== NAV.*?<!-- ============================== /NAV ============================== -->)',
        text, re.DOTALL)
    footer_match = re.search(
        r'(<footer class="footer">.*?<!-- =========================== /FOOTER ============================= -->)',
        text, re.DOTALL)
    root_match = re.search(r':root\s*{(.*?)}', text, re.DOTALL)

    if not nav_match or not footer_match or not root_match:
        raise RuntimeError("Could not extract nav/footer/root-vars from powerscore/index.html — check markup markers.")

    NAV_HTML = nav_match.group(1)
    FOOTER_HTML = footer_match.group(1)
    ROOT_STYLE_VARS = root_match.group(1)


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>

<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-W33G4TGRHD');
</script>

<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="article">
<meta property="og:image" content="https://homepowerrebate.com/og-image.svg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:type" content="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">

<script type="application/ld+json">{article_jsonld}</script>
<script type="application/ld+json">{faq_jsonld}</script>

<style>
:root {{{root_vars}}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--paper); color: var(--ink); font-family: 'Inter Tight', sans-serif; line-height: 1.6; }}
h1, h2, h3, h4 {{ font-family: 'Fraunces', serif; color: var(--teal-deep); }}
.wrap {{ max-width: 1000px; margin: 0 auto; padding: 0 28px; }}
a {{ color: var(--teal); }}
.hero {{ background: linear-gradient(135deg, var(--teal-deep), var(--teal)); color: #fff; padding: 48px 28px 40px; text-align: center; }}
.hero .eyebrow {{ font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: rgba(255,255,255,0.75); margin-bottom: 14px; }}
.hero h1 {{ color: #fff; font-size: clamp(28px, 4.5vw, 42px); line-height: 1.15; margin: 0 0 14px; }}
.hero p {{ font-size: 16px; color: rgba(255,255,255,0.85); max-width: 640px; margin: 0 auto; }}
.cross-region-notice {{ background: var(--paper-warm); border-left: 4px solid var(--amber); border-radius: 0 8px 8px 0; padding: 16px 20px; margin: 24px 0; font-size: 14px; color: var(--ink-soft); }}
.section {{ padding: 40px 28px; }}
.compare-table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid var(--rule); border-radius: 12px; overflow: hidden; margin: 20px 0; }}
.compare-table th, .compare-table td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--rule); font-size: 14px; }}
.compare-table th {{ background: var(--paper-warm); font-weight: 700; text-transform: uppercase; font-size: 12px; letter-spacing: .05em; color: var(--ink-soft); }}
.compare-table tr:last-child td {{ border-bottom: none; }}
.compare-table td.score-cell {{ font-family: 'Fraunces', serif; font-weight: 700; }}
.band-great {{ color: var(--green-money); }}
.band-mid {{ color: var(--amber); }}
.band-low {{ color: var(--red-flag); }}
.overall-row td {{ font-weight: 700; background: var(--paper-warm); }}
.city-links {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 24px 0; }}
.city-links a.btn {{ display: inline-block; background: var(--amber); color: #fff; padding: 12px 22px; border-radius: 999px; text-decoration: none; font-weight: 700; font-size: 14px; }}
.city-links a.btn:hover {{ background: var(--amber-bright); }}
.back-link {{ display: inline-block; margin: 24px 0; font-weight: 600; }}
.faq {{ margin: 32px 0; }}
.faq-item {{ background: #fff; border: 1px solid var(--rule); border-radius: 10px; padding: 18px 20px; margin-bottom: 12px; }}
.faq-item h3 {{ font-size: 16px; margin: 0 0 8px; }}
.faq-item p {{ margin: 0; font-size: 14px; color: var(--ink-soft); }}
</style>
</head>
<body>

{nav}

<header class="hero">
  <div class="wrap">
    <div class="eyebrow">PowerScore Comparison</div>
    <h1>{h1}</h1>
    <p>{lead}</p>
  </div>
</header>

<section class="section">
  <div class="wrap">
    {cross_region_notice}

    <div class="city-links">
      <a class="btn" href="{url_a}">See {label_a}'s full rebate guide &rarr;</a>
      <a class="btn" href="{url_b}">See {label_b}'s full rebate guide &rarr;</a>
    </div>

    <h2>Category-by-category PowerScore</h2>
    <div style="overflow-x:auto;">
    <table class="compare-table">
      <thead><tr><th>Category</th><th>{label_a}</th><th>{label_b}</th></tr></thead>
      <tbody>
{table_rows}
        <tr class="overall-row"><td>Overall PowerScore</td><td class="score-cell {band_a}">{overall_a}</td><td class="score-cell {band_b}">{overall_b}</td></tr>
      </tbody>
    </table>
    </div>

    <h2>Frequently asked questions</h2>
    <div class="faq">
{faq_html}
    </div>

    <a class="back-link" href="/powerscore/">&larr; Back to the full PowerScore leaderboard</a>
  </div>
</section>

{footer}

</body>
</html>
"""


def build_page(city_a, city_b, same_region, generated_date):
    label_a, label_b = city_a["label"], city_b["label"]
    overall_a, overall_b = city_a["overall"], city_b["overall"]
    band_a = score_band(overall_a)[1]
    band_b = score_band(overall_b)[1]

    slug_a = slugify_pair_component(city_a["region_key"], city_a["slug"])
    slug_b = slugify_pair_component(city_b["region_key"], city_b["slug"])
    pair_slug = f"{slug_a}-vs-{slug_b}"
    canonical = f"https://homepowerrebate.com/powerscore/compare/{pair_slug}/"

    title = f"{label_a} vs {label_b} PowerScore: Which City Has Better Rebates?"
    description = (
        f"{label_a} scores {overall_a}/100 and {label_b} scores {overall_b}/100 on HomePowerRebate's "
        f"PowerScore. Compare heat pump, solar, battery, and 5 more rebate categories side by side."
    )
    h1 = f"{label_a} vs {label_b}: PowerScore Rebate Comparison"

    if same_region:
        lead = (
            f"Both cities are in {city_a['region_label']}, so these PowerScores are on the same regional "
            f"scale &mdash; a direct, apples-to-apples comparison."
        )
        cross_region_notice = ""
    else:
        lead = (
            f"{label_a} is in {city_a['region_label']} and {label_b} is in {city_b['region_label']} &mdash; "
            f"two different regions with two different rebate systems."
        )
        cross_region_notice = (
            '<div class="cross-region-notice"><strong>Heads up:</strong> these two cities are in different '
            f"regions ({city_a['region_label']} and {city_b['region_label']}). PowerScore's dollar-value "
            "component is normalized against the strongest program in each city's own region, so this "
            "comparison is directional, not a precise apples-to-apples number the way comparing two cities "
            "in the same region would be. Use it to see which city currently has more/better-funded/more "
            "stackable programs, not as a strict ranking."
        )
        cross_region_notice += "</div>"

    rows = []
    for cat_key, cat_label in CATEGORY_LABELS.items():
        emoji = CATEGORY_EMOJI.get(cat_key, "")
        a_score = city_a["categories"].get(cat_key, {}).get("score", 0)
        b_score = city_b["categories"].get(cat_key, {}).get("score", 0)
        a_band = score_band(a_score)[1]
        b_band = score_band(b_score)[1]
        rows.append(
            f'        <tr><td>{emoji} {cat_label}</td>'
            f'<td class="score-cell {a_band}">{a_score:.1f}</td>'
            f'<td class="score-cell {b_band}">{b_score:.1f}</td></tr>'
        )
    table_rows = "\n".join(rows)

    faqs = build_faq(city_a, city_b, same_region)
    faq_html = "\n".join(
        f'      <div class="faq-item"><h3>{f["q"]}</h3><p>{f["a"]}</p></div>' for f in faqs
    )

    article_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": h1,
        "description": description,
        "author": {"@type": "Person", "name": "Sam Menard", "url": "https://homepowerrebate.com/about"},
        "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
        "mainEntityOfPage": canonical,
        "datePublished": generated_date,
        "dateModified": generated_date,
    })

    faq_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f["q"],
                "acceptedAnswer": {"@type": "Answer", "text": f["a"]},
            }
            for f in faqs
        ],
    })

    html = PAGE_TEMPLATE.format(
        title=title,
        description=description,
        canonical=canonical,
        article_jsonld=article_jsonld,
        faq_jsonld=faq_jsonld,
        root_vars=ROOT_STYLE_VARS,
        nav=NAV_HTML,
        footer=FOOTER_HTML,
        h1=h1,
        lead=lead,
        cross_region_notice=cross_region_notice,
        url_a=city_a["url"],
        url_b=city_b["url"],
        label_a=label_a,
        label_b=label_b,
        table_rows=table_rows,
        band_a=band_a,
        band_b=band_b,
        overall_a=overall_a,
        overall_b=overall_b,
        faq_html=faq_html,
    )
    return pair_slug, html, canonical


CATEGORY_LABELS = {}


def main():
    global CATEGORY_LABELS
    data = load_data()
    CATEGORY_LABELS = data["category_labels"]
    generated_date = data.get("generated")

    extract_shared_markup()

    pairs = build_pairs(data)
    print(f"Building {len(pairs)} comparison pages...")

    COMPARE_DIR.mkdir(parents=True, exist_ok=True)

    new_urls = []
    for (ra, sa), (rb, sb), same_region in pairs:
        city_a = get_city(data, ra, sa)
        city_b = get_city(data, rb, sb)
        pair_slug, html, canonical = build_page(city_a, city_b, same_region, generated_date)
        page_dir = COMPARE_DIR / pair_slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(html)
        new_urls.append(canonical)

    print(f"Wrote {len(new_urls)} pages to {COMPARE_DIR}")

    # ---- update sitemap.xml ----
    sitemap_text = SITEMAP_PATH.read_text()
    existing_urls = set(re.findall(r"<loc>(.*?)</loc>", sitemap_text))
    added = 0
    insertion_lines = []
    for url in new_urls:
        if url in existing_urls:
            continue
        insertion_lines.append(
            f"  <url><loc>{url}</loc><lastmod>{generated_date}</lastmod><changefreq>monthly</changefreq><priority>0.5</priority></url>\n"
        )
        added += 1

    if insertion_lines:
        marker = "<url><loc>https://homepowerrebate.com/powerscore/</loc>"
        idx = sitemap_text.find(marker)
        if idx == -1:
            raise RuntimeError("Could not find powerscore sitemap marker to insert after.")
        line_end = sitemap_text.find("\n", idx) + 1
        sitemap_text = sitemap_text[:line_end] + "".join(insertion_lines) + sitemap_text[line_end:]
        SITEMAP_PATH.write_text(sitemap_text)

    print(f"Added {added} new URLs to sitemap.xml")


if __name__ == "__main__":
    main()
