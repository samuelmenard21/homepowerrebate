#!/usr/bin/env python3
"""Free website and Google profile review for ranked installers (2026-11-04): the "give first" note that starts a relationship.

Why: installers do not answer link or badge requests. A short, honest review of their own site and Google listing, with 3 fixes they
can make today, is something worth replying to. This builds the reviews and one plain note per company; it SENDS NOTHING.

What it checks (one fetch of the homepage, like a visitor; stdlib only):
  site:    https, phone-friendly viewport, title and H1 say heat pump + a city, meta description, click-to-call (tel:) link,
           a quote or booking way in, a heat pump page, rebate help mentioned, structured data, page weight and load time.
  Google:  from the ranking data we already hold (rating, review count, our rank in the city, reviews against the city median
           and against the next company up). Things we cannot see (photos, categories, hours, services, replies to reviews) go in a
           checklist labelled "check yourself"; the review never claims what it cannot read.
Output: data/installer-reviews/<region>-<city>-<slug>.json, one line per company in data/installer-reviews/index.md, and a draft
note in data/installer-reviews/notes/<same>.txt. Usage: python3 scripts/installer_review.py [--cities 25] [--per-city 1] [--service heat-pump]"""
import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_installer_rankings as br  # noqa: E402

OUT = ROOT / "data" / "installer-reviews"
UA = "Mozilla/5.0 (compatible; HomePowerRebate-review/1.0; +https://homepowerrebate.com/installers/how-we-rank/)"


def fetch(url):
    t = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=12) as r:
            body = r.read(1_500_000).decode("utf-8", "ignore")
            return r.geturl(), body, time.time() - t, None
    except Exception as e:  # unreachable, blocked, bad certificate...
        return url, "", None, str(e)[:120]


def strip(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style).*?</\1>", " ", h)))


def site_checks(url, body, secs, city, service):
    low = body.lower()
    text = strip(body).lower()
    title = (re.search(r"(?is)<title[^>]*>(.*?)</title>", body) or [None, ""])[1].strip()
    h1s = re.findall(r"(?is)<h1[^>]*>(.*?)</h1>", body)
    h1 = strip(h1s[0]).strip() if h1s else ""
    word = {"heat-pump": "heat pump", "insulation": "insulation"}.get(service, service)
    c = city.lower()
    meta = re.search(r'(?is)<meta[^>]+name=["\']description["\'][^>]*content=["\']([^"\']{20,})', body)
    has_city = c in title.lower() or c in h1.lower()
    has_word = word in title.lower() or word in h1.lower()
    # ordered by what matters most to a homeowner on a phone; the first three misses become the fixes
    return [
        ("One-tap call link (tel:) on the homepage", "href=\"tel:" in low or "href='tel:" in low, "Make your phone number a tap-to-call link on the homepage. Most local searches happen on a phone, and a number people have to copy loses calls."),
        ("A quote or booking way in", bool(re.search(r"(free )?(quote|estimate|book (online|now|an? )|schedule)", text)), "Add a clear 'Get a quote' or 'Book a visit' button near the top of the homepage."),
        ("Works on a phone (viewport tag)", "name=\"viewport\"" in low or "name='viewport'" in low, "Add a mobile viewport tag so the homepage fits a phone screen."),
        ("Secure site (https)", url.startswith("https://"), "Move the site to https so browsers do not show a 'not secure' warning."),
        (f"A {word} page or section", bool(re.search(rf'href=["\'][^"\']*{word.replace(" ", "[-_ ]?")}', low)) or low.count(word) >= 3, f"Give {word} its own page with the models you install, a price range and the areas you serve."),
        ("Mentions rebates on the homepage", bool(re.search(r"rebate|incentive|grant", text)), "Say on the homepage which rebates you help customers claim; homeowners search for exactly that."),
        (f"Homepage title or heading names {city}", has_city, f"Name {city} in the homepage title or main heading, so searchers see you serve their city."),
        (f"Homepage title or heading says '{word}'", has_word, f"Say '{word}' in the homepage title or main heading so it is clear what you install."),
        ("Has a meta description", bool(meta), "Write a 150-character search description with your city and what you install."),
        ("Structured data (schema)", "application/ld+json" in low, "Add LocalBusiness structured data so search and AI answers can read your name, phone and service area."),
        ("Homepage loads in under 3 seconds (from our test)", secs is not None and secs < 3, "Compress large images; slow pages lose phone visitors."),
    ]


def build():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cities", type=int, default=25)
    ap.add_argument("--per-city", type=int, default=1)
    ap.add_argument("--service", default="heat-pump")
    a = ap.parse_args()
    rows = [r for r in br.load_rows() if r["service"] == a.service]
    by = {}
    for r in rows:
        by.setdefault((r["region"], r["city"]), []).append(r)
    hubs = br.city_hubs()
    top = sorted(((k, v) for k, v in by.items() if len(v) >= br.MIN_INSTALLERS), key=lambda kv: -sum(x["reviews"] for x in kv[1]))[: a.cities]
    (OUT / "notes").mkdir(parents=True, exist_ok=True)
    lines = ["# Installer reviews (drafts, nothing sent)", "", "| City | Company | Rank | Site checks passed | Top 3 fixes |", "|---|---|---|---|---|"]
    n = 0
    for (region, city), inst in top:
        ranked = sorted(inst, key=br.score, reverse=True)
        hub = br.find_hub(hubs, region, city)
        label = hub["label"] if hub else city
        med = median(x["reviews"] for x in ranked)
        for rank, r in enumerate(ranked[: a.per_city], 1):
            site = r["website"].split("?")[0] if r["website"] else ""
            checks, err = [], None
            if site:
                url, body, secs, err = fetch(site)
                if not err:
                    checks = site_checks(url, body, secs, label, a.service)
            above = ranked[rank - 2] if rank > 1 else None
            google = {"rating": r["rating"], "reviews": r["reviews"], "rank_in_city": rank, "companies_in_city": len(ranked),
                      "city_median_reviews": med, "reviews_to_pass_next": (above["reviews"] - r["reviews"] + 1) if above else 0,
                      "has_phone": bool(r["phone"]), "has_website": bool(site)}
            passed = sum(1 for c in checks if c[1])
            fixes = [c[2] for c in checks if not c[1]][:3]
            if not site:
                fixes = ["Add a website link to your Google listing so searchers can see your work and request a quote."]
            elif err:
                lines.append(f"| {label} | {r['name']} | {rank}/{len(ranked)} | not checked | our fetch was refused or failed; check by hand before writing |")
                print(f"{label}: {r['name']} not checked ({err})")
                continue
            slug = f"{region}-{br.slugify(label)}-{br.slugify(r['name'])}"[:90]
            rec = {"company": r["name"], "region": region, "city": label, "service": a.service, "website": site, "google": google,
                   "checks": [{"check": c[0], "pass": c[1], "fix": c[2]} for c in checks], "passed": passed, "of": len(checks), "fixes": fixes,
                   "check_yourself": ["Photos of finished installs (add recent ones)", "Business categories include the service you sell and no wrong ones",
                                      "Services list and service area filled in", "You reply to reviews, good and bad", "Phone number and hours match your website"],
                   "page": f"https://homepowerrebate.com/installers/{region}/{hub['slug'] if hub else br.slugify(city)}/{a.service}/"}
            (OUT / f"{slug}.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            cat = f"{rank}{'st' if rank == 1 else 'nd' if rank == 2 else 'rd' if rank == 3 else 'th'}"
            note = (f"Hi {r['name']} team,\n\nWe rank {a.service.replace('-', ' ')} installers in {label} by Google reviews, and you are {cat} of {len(ranked)} "
                    f"({r['rating']:.1f} stars, {r['reviews']:,} reviews; the middle company has {med:,.0f}). "
                    + (f"I looked at your homepage the way a homeowner on a phone would and it passes {passed} of {len(checks)} basic checks. " if checks else "")
                    + ("The one thing I would fix first:\n" if len(fixes) == 1 else f"The {len(fixes)} things I would fix first:\n") + "".join(f"  {i}. {f}\n" for i, f in enumerate(fixes, 1))
                    + "\nNothing to buy and nothing to sign. If it helps, reply and I will send the full list of checks. - Sam, HomePowerRebate\n")
            (OUT / "notes" / f"{slug}.txt").write_text(note, encoding="utf-8")
            lines.append(f"| {label} | {r['name']} | {rank}/{len(ranked)} | {passed}/{len(checks) or '-'} | {'; '.join(fixes)[:160]} |")
            n += 1
            print(f"{label}: {r['name']} {passed}/{len(checks)}")
    (OUT / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{n} reviews written to {OUT}")


if __name__ == "__main__":
    build()
