#!/usr/bin/env python3
"""
Build powerscore-data.json — computes a 0-100 "PowerScore" per city, per category
(and an overall average), by parsing dollar amounts, program counts, and status
already published on the site's own city hub + category pages. No new numbers are
invented; everything comes from existing .rebate-card / .amount markup.

Formula per category, per city:
  score = 0.60 * dollar_score + 0.25 * status_score + 0.15 * stack_score

  dollar_score = 100 * (city_max_amount / region_max_amount_for_that_category)
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

ROOT = Path(__file__).resolve().parent.parent

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

REGIONS = {
    "ca/bc": ("Canada", "British Columbia"),
    "ca/on": ("Canada", "Ontario"),
    "ca/ab": ("Canada", "Alberta"),
    "ca/ns": ("Canada", "Nova Scotia"),
    "us/ma": ("United States", "Massachusetts"),
    "us/ny": ("United States", "New York"),
    "us/ca": ("United States", "California"),
    "us/pa": ("United States", "Pennsylvania"),
}

STATUS_KEYWORDS_CLOSED = ["program closed", "no longer accepting", "fully subscribed", "rebate-card none", "class=\"amount none\""]
STATUS_KEYWORDS_LIMITED = ["funding limited", "limited funding", "waitlist", "unclear", "may be paused", "subject to available funding"]

AMOUNT_RE = re.compile(r"\$([\d,]+(?:\.\d+)?)")
CARD_RE = re.compile(r'<div class="rebate-card([^"]*)">(.*?)</div>\s*</div>', re.DOTALL)
CARD_SPLIT_RE = re.compile(r'<div class="rebate-card')


def find_category_dir(city_dir: Path, category: str):
    for alias in CATEGORY_ALIASES.get(category, [category]):
        d = city_dir / alias
        if d.is_dir() and (d / "index.html").exists():
            return d
    return None


def extract_amounts(html: str):
    """Return list of dollar amounts (floats) found in .amount divs."""
    amounts = []
    # grab each `<div class="amount...">...</div>` block
    for m in re.finditer(r'<div class="amount[^"]*">(.*?)</div>', html, re.DOTALL):
        text = m.group(1)
        nums = AMOUNT_RE.findall(text)
        for n in nums:
            try:
                amounts.append(float(n.replace(",", "")))
            except ValueError:
                pass
    return amounts


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
        heading_m = re.search(r"<h4>(.*?)</h4>", body, re.DOTALL)
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


def main():
    raw = {}  # region_key -> city_slug -> category -> {amounts, programs, status}
    city_meta = {}  # region_key -> city_slug -> {label, path}

    for region_key, (country, region_label) in REGIONS.items():
        region_path = ROOT / region_key
        if not region_path.exists():
            continue
        leaves = find_city_leaves(region_path)
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
                amounts, programs, status = [], 0, "closed"
                if cat_dir:
                    cat_html = (cat_dir / "index.html").read_text(errors="ignore")
                    amounts = extract_amounts(cat_html)
                    programs = count_program_cards(cat_html)
                    status = detect_status(cat_html, bool(amounts))
                if not amounts:
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
                    "programs": max(programs, 1 if amounts else 0),
                    "status": status,
                }

    # compute region maxes per category
    region_max = {}
    for region_key, cities in raw.items():
        region_max[region_key] = {}
        for cat in CATEGORIES:
            mx = 0.0
            for slug, cats in cities.items():
                amts = cats[cat]["amounts"]
                if amts:
                    mx = max(mx, max(amts))
            region_max[region_key][cat] = mx or 1.0

    STATUS_SCORE = {"open": 100, "limited": 50, "closed": 0}

    output = {"generated": "2026-08-23", "regions": {}}

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
                dollar_score = 100.0 * (dollar_val / region_max[region_key][cat])
                dollar_score = min(dollar_score, 100.0)
                status_score = STATUS_SCORE.get(info["status"], 0)
                stack_score = min(100, 25 * info["programs"])
                score = 0.60 * dollar_score + 0.25 * status_score + 0.15 * stack_score
                cat_scores[cat] = {
                    "score": round(score, 1),
                    "dollar_value": dollar_val,
                    "status": info["status"],
                    "programs": info["programs"],
                }
            overall = round(sum(c["score"] for c in cat_scores.values()) / len(CATEGORIES), 1)
            meta = city_meta[region_key][slug]
            region_out["cities"][slug] = {
                "label": meta["label"],
                "url": meta["url"],
                "overall": overall,
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
