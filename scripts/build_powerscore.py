#!/usr/bin/env python3
"""
Build powerscore-data.json — computes a 0-100 "PowerScore" per city, per category
(and an overall average), by parsing dollar amounts, program counts, and status
already published on the site's own city hub + category pages. No new numbers are
invented; everything comes from existing .rebate-card / .amount markup.

Formula per category, per city:
  score = 0.60 * dollar_score + 0.25 * status_score + 0.15 * stack_score

  dollar_score = 100 * min(1, usd_amount / yardstick_for_that_category)
  yardstick    = 90th percentile of city top amounts for the category across ALL regions, in USD
                 (a city scores 100 by matching what the best-funded tenth of cities offer)
  usd_amount   = amount, with Canadian dollars converted at CAD_TO_USD (an approximation)
  status_score = 100 (Open) / 50 (Funding Limited / Unclear) / 0 (Closed)
  stack_score  = min(100, 25 * distinct_program_count)   # 1=25,2=50,3=75,4+=100

Overall PowerScore for a city = average of its 8 category scores.

Regions walked: ca/bc, ca/on, ca/ab, ca/ns, us/ma, us/ny, us/ca
Categories: heat-pump, insulation, solar, battery, water-heater,
            smart-thermostats, ev-charger, windows-doors (bc uses "windows")
"""
import json
import re
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import regions
ROOT = Path(__file__).resolve().parent.parent

# Approximate exchange rate used only to put Canadian and US rebate amounts on one scale.
CAD_TO_USD = 0.73

# Rebates paid per ton of capacity (ENS heat pump: $300-$600/ton), not as a flat amount.
PER_TON = {("ca/ns", "heat-pump")}

CATEGORIES = [
    "heat-pump", "insulation", "solar", "battery",
    "water-heater", "smart-thermostats", "ev-charger", "windows-doors",
]
CATEGORY_LABELS = {
    "heat-pump": "Heat Pump",
    "insulation": "Insulation",
    "solar": "Solar",
    "battery": "Battery Storage",
    "water-heater": "Water Heater",
    "smart-thermostats": "Smart Thermostat",
    "ev-charger": "EV Charger",
    "windows-doors": "Windows & Doors",
}
# some regions used an older folder name
CATEGORY_ALIASES = {
    "windows-doors": ["windows-doors", "windows"],
}

REGIONS = dict(regions.COUNTRY_NAME_BY_PATH)

STATUS_KEYWORDS_CLOSED = ["program closed", "no longer accepting", "fully subscribed", "rebate-card none", "class=\"amount none\""]
STATUS_KEYWORDS_LIMITED = ["funding limited", "limited funding", "waitlist", "unclear", "may be paused", "subject to available funding"]

AMOUNT_RE = re.compile(r"\$([\d,]+(?:\.\d+)?)")
CARD_RE = re.compile(r'<div class="rebate-card([^"]*)">(.*?)</div>\s*</div>', re.DOTALL)
CARD_SPLIT_RE = re.compile(r'<div class="rebate-card')


def _load_redirects():
    out = {}
    f = ROOT / "_redirects"
    for line in (f.read_text().splitlines() if f.exists() else []):
        parts = line.split()
        if len(parts) >= 2 and not line.startswith("#"):
            out[parts[0]] = parts[1]
    return out


REDIRECTS = _load_redirects()


def find_category_dir(city_dir: Path, category: str):
    for alias in CATEGORY_ALIASES.get(category, [category]):
        d = city_dir / alias
        if d.is_dir() and (d / "index.html").exists():
            return d
    # A city without its own page for this category 301s to a province or state topic page
    # (e.g. /us/pa/pittsburgh/solar/ -> /us/pa/solar/); score what the visitor lands on.
    # A redirect to the city hub or a sibling category is left to the hub fallback.
    rel = "/" + str(city_dir.relative_to(ROOT)) + "/"
    region = "/".join(city_dir.relative_to(ROOT).parts[:2])
    for alias in CATEGORY_ALIASES.get(category, [category]):
        target = REDIRECTS.get(f"{rel}{alias}/")
        if target and re.fullmatch(rf"/{region}/{re.escape(alias)}/", target):
            d = ROOT / target.strip("/")
            if (d / "index.html").exists():
                return d
    return None


# Loans and on-bill financing are not rebates: a card headed as one, or a clause of an amount that names one
# ("Up to $2,000 plus 0% loans up to $20,000"), adds nothing to the dollar score.
FINANCING_RE = re.compile(r"financ|loan|on-bill|repay|lends|interest|% apr|clean energy improvement|\bceip\b|\bpace\b", re.I)
NOT_A_HOME_REBATE_RE = re.compile(r'program-status status-closed"|program-status status-[a-z]+">Info<|not for (houses|homeowners|single homes)', re.I)
CLAUSE_SPLIT_RE = re.compile(r"\s*(?:\+|\bplus\b|,\s|;|\.\s)\s*", re.I)
# An uncapped share of the cost ("75% to 100% off", "80% of weatherization"). It scores as that share of the dollar
# yardstick, so no project cost is assumed; tax credits and shares of a maximum are not this kind of offer.
PERCENT_OFFER_RE = re.compile(r"(\d{1,3})%(?:\s*(?:to|-|–|&ndash;)\s*(\d{1,3})%)?\s*(?:off\b|of (?:the )?(?:cost|weatherization|project))", re.I)


def amount_texts(html: str):
    """Yield the text of each .amount div that can count as a home rebate, with loan and financing clauses removed."""
    # grab each `<div class="amount...">...</div>` block
    for m in re.finditer(r'<div class="amount[^"]*">(.*?)</div>', html, re.DOTALL):
        card_start = html.rfind('<div class="rebate-card', 0, m.start())
        if card_start != -1 and m.start() - card_start > 1500:  # an amount outside any card
            card_start = -1
        p_end = html.find("</p>", m.end(), m.end() + 800)
        card = html[card_start:(p_end + 4 if p_end != -1 else m.end())] if card_start != -1 else ""
        heads = re.findall(r"<h4\b[^>]*>(.*?)</h4>", html[card_start:m.start()] if card_start != -1 else "", re.DOTALL)
        if heads and FINANCING_RE.search(re.sub(r"<[^>]+>", "", heads[-1])):
            continue
        if NOT_A_HOME_REBATE_RE.search(card):  # closed or expired, an info card (a fee or a rate), or not for houses
            continue
        clauses = CLAUSE_SPLIT_RE.split(re.sub(r"<[^>]+>", " ", m.group(1)).replace("&nbsp;", " "))
        yield " ".join(c for c in clauses if not FINANCING_RE.search(c)).strip()


def extract_amounts(html: str):
    """Return list of dollar amounts (floats) found in .amount divs, leaving out loans and financing."""
    amounts = []
    for text in amount_texts(html):
        if re.search(r"per (credit|srec|rec)\b", text, re.I):
            continue  # a market price per certificate (Illinois Shines), not a rebate
        for n in AMOUNT_RE.findall(text):
            try:
                v = float(n.replace(",", ""))
                if v >= 1:  # "$0.03 per kWh" production payments are rates, not rebate amounts
                    amounts.append(v)
            except ValueError:
                pass
    return amounts


def extract_percent_offers(html: str):
    """Return (highest percent, the amount text) for each uncapped percent-of-cost offer (no dollar figure in it)."""
    offers = []
    for text in amount_texts(html):
        m = PERCENT_OFFER_RE.search(text)
        if m and "$" not in text and "credit" not in text.lower():
            offers.append((min(100, int(m.group(2) or m.group(1))), text))
    return offers


def percent_words(offers):
    """'75% off' for one offer, '75% to 100% off' when a page lists several (standard and income-qualified)."""
    lo = min(min(int(n) for n in re.findall(r"(\d{1,3})%", t)) for _, t in offers)
    hi = max(p for p, _ in offers)
    return f"{hi}% off" if lo >= hi else f"{lo}% to {hi}% off"


def count_program_cards(html: str):
    """Count distinct rebate-card blocks that are not marked 'none'."""
    chunks = html.split('<div class="rebate-card')
    count = 0
    for chunk in chunks[1:]:
        head = chunk[:40]
        if head.strip().startswith('none') or head.strip().startswith(' none'):
            continue
        count += 1
    return max(count, 0)


def split_cards(html: str):
    """Split a page's markup into individual `rebate-card` chunks (opening div tag
    through the next rebate-card / end of grid), each with its class attribute."""
    cards = []
    for m in re.finditer(r'<div class="rebate-card([^"]*)">', html):
        classes = m.group(1)
        start = m.end()
        nxt = html.find('<div class="rebate-card', start)
        end = nxt if nxt != -1 else min(start + 1200, len(html))
        cards.append((classes, html[start:end]))
    return cards


def detect_status(html: str, has_amount: bool):
    low = html.lower()
    # Pages built with status pills (program-status status-open / status-closed ...) list live and ended
    # programs together; a closed card must not turn the whole category closed.
    pills = re.findall(r'program-status status-([a-z]+)', low)
    if pills:
        if "open" in pills and has_amount:
            return "open"
        if any(p in ("limited", "check", "upcoming", "waitlist", "paused") for p in pills):
            return "limited"
        return "closed"
    if 'status status-closed' in low or '"status-closed"' in low:
        return "closed"
    if 'status status-limited' in low or '"status-limited"' in low:
        return "limited"
    if 'class="rebate-card none"' in low or 'class="amount none"' in low:
        return "closed"
    for kw in STATUS_KEYWORDS_CLOSED:
        if kw in low:
            return "closed"
    for kw in STATUS_KEYWORDS_LIMITED:
        if kw in low:
            return "limited"
    if not has_amount:
        return "closed"
    return "open"


CATEGORY_KEYWORDS = {
    "heat-pump": ["heat pump"],
    "insulation": ["insulation", "attic", "crawlspace", "exterior wall"],
    "solar": ["solar"],
    "battery": ["battery"],
    "water-heater": ["water heater"],
    "smart-thermostats": ["thermostat"],
    "ev-charger": ["ev charger", "ev charging", "electric vehicle"],
    "windows-doors": ["window", "door"],
}


def extract_city_from_hub(hub_html: str, category: str):
    """Fallback: pull the category's summary card straight from the city hub page,
    matched by heading keyword, when no dedicated category subpage exists or the
    subpage is prose-only (no .amount markup, e.g. some BC category pages)."""
    keywords = CATEGORY_KEYWORDS[category]
    amounts_total = []
    programs = 0
    status = "closed"
    found = False
    for classes, body in split_cards(hub_html):
        heading_m = re.search(r"<h4\b[^>]*>(.*?)</h4>", body, re.DOTALL)
        if not heading_m:
            continue
        heading = re.sub(r"<[^>]+>", "", heading_m.group(1)).lower()
        if category == "heat-pump" and "water heater" in heading:
            continue
        if category == "water-heater" and "heat pump water heater" not in heading and "water heater" not in heading:
            continue
        if not any(k in heading for k in keywords):
            continue
        found = True
        is_none = "none" in classes
        amounts = extract_amounts(body)
        amounts_total.extend(amounts)
        if not is_none:
            programs += 1
        card_status = detect_status(body, bool(amounts) and not is_none)
        if card_status == "open" and not is_none:
            status = "open" if status != "limited" else status
        elif card_status == "limited":
            status = "limited"
        elif is_none:
            pass  # leave status as-is unless nothing else found
    if not found:
        return None
    if status == "closed" and amounts_total:
        status = "open"
    return {
        "amounts": amounts_total,
        "programs": programs,
        "status": status,
    }


def find_city_leaves(region_path: Path):
    """Recursively find directories that represent an actual city/leaf page:
    contains index.html and at least one category subdirectory."""
    leaves = []
    for d in sorted(p for p in region_path.rglob("*") if p.is_dir()):
        if not (d / "index.html").exists():
            continue
        subdirs = {p.name for p in d.iterdir() if p.is_dir()}
        if subdirs & set(sum(CATEGORY_ALIASES.values(), CATEGORIES)):
            leaves.append(d)
    return leaves


def city_dirs(region_key: str):
    """The cities the rest of the site lists (homepage hero, get-quotes, installer finder): city_slugs() in build_get_quotes.py,
    which reads installer folders plus data/regions.json. Each city's page is found under the region hub; where a metro hub
    and its main city share a slug (us/ca/los-angeles/los-angeles), the deeper city folder wins."""
    from build_get_quotes import city_slugs
    region_path = ROOT / region_key
    out = []
    for slug in city_slugs(regions.CODE_BY_PATH[region_key]):
        hits = [h for h in region_path.rglob(f"{slug}/index.html") if h.parent != region_path]
        if hits:
            out.append(max(hits, key=lambda h: len(h.parts)).parent)
    return sorted(out)


def main():
    raw = {}  # region_key -> city_slug -> category -> {amounts, programs, status}
    city_meta = {}  # region_key -> city_slug -> {label, path}

    for region_key, (country, region_label) in REGIONS.items():
        region_path = ROOT / region_key
        if not region_path.exists():
            continue
        leaves = city_dirs(region_key)
        raw[region_key] = {}
        city_meta[region_key] = {}
        for city_dir in leaves:
            hub_file = city_dir / "index.html"
            hub_html = hub_file.read_text(errors="ignore")
            rel = city_dir.relative_to(ROOT)
            slug = "/".join(rel.parts[2:]) if len(rel.parts) > 2 else city_dir.name
            # human label: prefer the dir name (clean, short); h1/title text on these
            # pages is a full SEO sentence, not a city name.
            label = city_dir.name.replace("-", " ").title()
            label = (label.replace("St ", "St. ").replace("Ny ", "NY ")
                     .replace("Bc ", "BC ").replace("Ev ", "EV "))
            city_meta[region_key][slug] = {
                "label": label,
                "url": "/" + str(rel) + "/",
            }
            raw[region_key][slug] = {}
            for cat in CATEGORIES:
                cat_dir = find_category_dir(city_dir, cat)
                amounts, percents, programs, status = [], [], 0, "closed"
                if cat_dir:
                    cat_html = (cat_dir / "index.html").read_text(errors="ignore")
                    amounts = extract_amounts(cat_html)
                    percents = extract_percent_offers(cat_html)
                    programs = count_program_cards(cat_html)
                    status = detect_status(cat_html, any(a > 0 for a in amounts) or bool(percents))
                if not amounts and not percents:
                    # dedicated subpage missing or written in prose (no .amount divs,
                    # e.g. BC category pages) — fall back to the hub page's summary card
                    fallback = extract_city_from_hub(hub_html, cat)
                    if fallback and fallback["amounts"]:
                        amounts = fallback["amounts"]
                        programs = max(programs, fallback["programs"])
                        status = fallback["status"] if status == "closed" else status
                    elif fallback and not cat_dir:
                        programs = fallback["programs"]
                        status = fallback["status"]
                raw[region_key][slug][cat] = {
                    "amounts": amounts,
                    "percents": percents,
                    "programs": max(programs, 1 if amounts or percents else 0),
                    "status": status,
                }

    # Common yardstick per category: 90th percentile of city top amounts (USD) across every region.
    def usd_of(country, v):
        return v * (CAD_TO_USD if country == "Canada" else 1.0)

    yardstick = {}
    for cat in CATEGORIES:
        vals = []
        for region_key, cities in raw.items():
            country = REGIONS[region_key][0]
            for slug, cats in cities.items():
                amts = cats[cat]["amounts"]
                if amts:
                    vals.append(usd_of(country, max(amts)))
        vals.sort()
        if not vals:
            yardstick[cat] = 1.0
        elif len(vals) < 10:
            yardstick[cat] = vals[-1]
        else:
            yardstick[cat] = vals[min(len(vals) - 1, int(0.9 * len(vals)))]

    STATUS_SCORE = {"open": 100, "limited": 50, "closed": 0}

    output = {"generated": __import__("datetime").date.today().isoformat(), "regions": {},
              "yardstick_usd": {c: round(v, 2) for c, v in yardstick.items()}, "cad_to_usd": CAD_TO_USD}

    all_city_rows = []

    for region_key, (country, region_label) in REGIONS.items():
        if region_key not in raw:
            continue
        region_out = {"label": region_label, "country": country, "cities": {}}
        for slug, cats in raw[region_key].items():
            cat_scores = {}
            for cat in CATEGORIES:
                info = cats[cat]
                dollar_val = max(info["amounts"]) if info["amounts"] else 0.0
                usd_val = usd_of(country, dollar_val)
                dollar_score = min(100.0, 100.0 * (usd_val / yardstick[cat]))
                pct = max(info["percents"], default=None)
                if pct and pct[0] > dollar_score:
                    # an uncapped percent off beats every flat amount here: score the share, show its words, add no dollars
                    dollar_score, dollar_val, usd_val = float(pct[0]), 0.0, 0.0
                status_score = STATUS_SCORE.get(info["status"], 0)
                stack_score = min(100, 25 * info["programs"])
                score = 0.60 * dollar_score + 0.25 * status_score + 0.15 * stack_score
                cat_scores[cat] = {
                    **({"unit": "per ton"} if (region_key, cat) in PER_TON else {}),
                    **({"percent_off": pct[0], "percent_text": percent_words(info["percents"])} if pct and dollar_val == 0 and dollar_score == pct[0] else {}),
                    "score": round(score, 1),
                    "dollar_value": dollar_val,
                    "usd_value": round(usd_val, 2),
                    "status": info["status"],
                    "programs": info["programs"],
                }
            open_cats = [c for c in cat_scores.values() if c["status"] == "open" and c["usd_value"] > 0]
            potential = round(sum(c["usd_value"] for c in open_cats))
            overall = round(sum(c["score"] for c in cat_scores.values()) / len(CATEGORIES), 1)
            meta = city_meta[region_key][slug]
            region_out["cities"][slug] = {
                "label": meta["label"],
                "url": meta["url"],
                "overall": overall,
                "potential_usd": potential,
                "open_count": len(open_cats),
                "categories": cat_scores,
            }
            all_city_rows.append({
                "region": region_key,
                "region_label": region_label,
                "country": country,
                "slug": slug,
                "label": meta["label"],
                "url": meta["url"],
                "overall": overall,
                "potential_usd": potential,
                "open_count": len(open_cats),
                "categories": cat_scores,
            })
        output["regions"][region_key] = region_out

    # rankings
    all_city_rows.sort(key=lambda r: r["overall"], reverse=True)
    output["leaderboard_overall"] = all_city_rows

    for cat in CATEGORIES:
        rows = sorted(all_city_rows, key=lambda r: r["categories"][cat]["score"], reverse=True)
        output.setdefault("leaderboard_by_category", {})[cat] = [
            {
                "region": r["region"], "region_label": r["region_label"], "country": r["country"],
                "slug": r["slug"], "label": r["label"], "url": r["url"],
                "score": r["categories"][cat]["score"], "dollar_value": r["categories"][cat]["dollar_value"],
                **({"percent_text": r["categories"][cat]["percent_text"]} if r["categories"][cat].get("percent_text") else {}),
                "status": r["categories"][cat]["status"], "programs": r["categories"][cat]["programs"],
            }
            for r in rows
        ]

    output["category_labels"] = CATEGORY_LABELS
    output["stats"] = {
        "total_cities": len(all_city_rows),
        "total_regions": len(output["regions"]),
        "categories": len(CATEGORIES),
    }

    out_path = ROOT / "powerscore-data.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"Wrote {out_path} — {len(all_city_rows)} cities across {len(output['regions'])} regions")
    print("\nTop 10 overall:")
    for r in all_city_rows[:10]:
        print(f"  {r['overall']:5.1f}  {r['label']:25s} ({r['region_label']})")


if __name__ == "__main__":
    main()
