#!/usr/bin/env python3
"""
Installer site audit tool.

Takes an installer record (name, website, rating, reviews, phone, location)
and produces a scored audit report (JSON + a one-page HTML report).

Usage:
    .venv/bin/python audit.py --json ../../installers/json/maple-ridge.json --out reports
    .venv/bin/python audit.py --json ../../installers/json/maple-ridge.json --limit 5 --out reports
"""
import argparse
import json
import re
import ssl
import socket
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

TIMEOUT = 12
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SiteAuditBot/1.0)"}


def safe_get(url, timeout=TIMEOUT):
    try:
        start = time.time()
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        elapsed = time.time() - start
        return resp, elapsed, None
    except Exception as e:
        return None, None, str(e)


def check_ssl(url):
    parsed = urlparse(url)
    if parsed.scheme != "https":
        # try https version
        try:
            host = parsed.netloc or parsed.path
            ctx = ssl.create_default_context()
            with socket.create_connection((host, 443), timeout=5) as sock:
                with ctx.wrap_socket(sock, server_hostname=host):
                    return True
        except Exception:
            return False
    return True


def analyze_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    findings = {}

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    findings["title"] = title
    findings["title_len"] = len(title)
    findings["has_title"] = bool(title)

    meta_desc = soup.find("meta", attrs={"name": "description"})
    findings["meta_description"] = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else ""
    findings["has_meta_description"] = bool(findings["meta_description"])

    viewport = soup.find("meta", attrs={"name": "viewport"})
    findings["has_viewport"] = bool(viewport)

    h1s = soup.find_all("h1")
    findings["h1_count"] = len(h1s)
    findings["has_single_h1"] = len(h1s) == 1

    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    schema_types = []
    for s in scripts:
        try:
            data = json.loads(s.string or "{}")
            items = data if isinstance(data, list) else [data]
            for item in items:
                t = item.get("@type")
                if t:
                    schema_types.append(t)
        except Exception:
            pass
    findings["schema_types"] = schema_types
    findings["has_schema"] = len(schema_types) > 0
    findings["has_local_business_schema"] = any(
        "LocalBusiness" in t or "HVACBusiness" in t or "Organization" in t for t in schema_types
    )

    text = soup.get_text(" ", strip=True)
    findings["word_count"] = len(text.split())

    body_lower = text.lower()
    findings["mentions_phone"] = bool(re.search(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", body_lower))

    # city-service page signal: look for internal links containing city/service-like slugs
    links = [a.get("href", "") for a in soup.find_all("a", href=True)]
    findings["internal_link_count"] = sum(1 for l in links if l.startswith("/") or base_url in l)

    return findings


def check_robots_sitemap(base_url):
    parsed = urlparse(base_url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    robots_resp, _, _ = safe_get(root + "/robots.txt", timeout=6)
    sitemap_resp, _, _ = safe_get(root + "/sitemap.xml", timeout=6)
    has_robots = bool(robots_resp and robots_resp.status_code == 200)
    has_sitemap = bool(sitemap_resp and sitemap_resp.status_code == 200)
    return has_robots, has_sitemap


def score_site(technical, gbp, load_time, has_ssl, has_robots, has_sitemap):
    """
    Weighted 0-100 score. GBP/local signals weighted highest since that's
    what drives calls for a local contractor.
    """
    score = 0
    breakdown = []

    # GBP / reputation (40 pts)
    rating = gbp.get("rating") or 0
    reviews = gbp.get("reviews") or 0
    gbp_pts = 0
    if rating >= 4.5:
        gbp_pts += 15
    elif rating >= 4.0:
        gbp_pts += 10
    elif rating > 0:
        gbp_pts += 5
    if reviews >= 100:
        gbp_pts += 15
    elif reviews >= 30:
        gbp_pts += 10
    elif reviews >= 5:
        gbp_pts += 5
    gbp_pts += 10 if gbp.get("recommended") else 0
    score += gbp_pts
    breakdown.append(("Google reputation (rating/reviews)", gbp_pts, 40))

    # Technical/on-site SEO (35 pts)
    tech_pts = 0
    tech_pts += 5 if has_ssl else 0
    tech_pts += 5 if technical.get("has_viewport") else 0
    tech_pts += 5 if technical.get("has_title") and 10 <= technical.get("title_len", 0) <= 65 else 0
    tech_pts += 5 if technical.get("has_meta_description") else 0
    tech_pts += 5 if technical.get("has_single_h1") else 0
    tech_pts += 5 if load_time is not None and load_time < 2.5 else (2 if load_time is not None and load_time < 5 else 0)
    tech_pts += 5 if technical.get("word_count", 0) >= 300 else 0
    score += tech_pts
    breakdown.append(("On-site technical SEO", tech_pts, 35))

    # Structured data / AEO readiness (15 pts)
    schema_pts = 0
    schema_pts += 8 if technical.get("has_schema") else 0
    schema_pts += 7 if technical.get("has_local_business_schema") else 0
    score += schema_pts
    breakdown.append(("Schema markup / AI-search readiness", schema_pts, 15))

    # Crawlability (10 pts)
    crawl_pts = (5 if has_robots else 0) + (5 if has_sitemap else 0)
    score += crawl_pts
    breakdown.append(("Crawlability (robots.txt / sitemap)", crawl_pts, 10))

    return score, breakdown


def grade_for(score):
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 65:
        return "C"
    if score >= 50:
        return "D"
    return "F"


def build_recommendations(technical, gbp, has_ssl, has_robots, has_sitemap, load_time):
    recs = []
    if not has_ssl:
        recs.append("Site isn't fully secured with SSL (https) — this can hurt rankings and scares off mobile visitors.")
    if not technical.get("has_viewport"):
        recs.append("No mobile viewport tag found — the site likely doesn't resize properly on phones, where most local searches happen.")
    if not technical.get("has_meta_description"):
        recs.append("Missing meta description — Google is writing your search snippet for you instead of you controlling the pitch.")
    if not technical.get("has_single_h1"):
        recs.append("Page headings aren't structured cleanly (missing or multiple H1 tags) — this confuses both Google and AI search tools.")
    if not technical.get("has_schema"):
        recs.append("No structured data (schema markup) — this is exactly what AI tools like ChatGPT and Google AI Overviews read to decide who to recommend. You're invisible to AI search right now.")
    elif not technical.get("has_local_business_schema"):
        recs.append("Has some schema markup but no LocalBusiness schema — missing an easy win for local + AI search.")
    if technical.get("word_count", 0) < 300:
        recs.append("Homepage is thin on content — not enough for Google to understand what you do and where you serve.")
    if load_time and load_time > 3:
        recs.append(f"Site took {load_time:.1f}s to load — slow sites lose mobile visitors before the page even finishes loading.")
    if not has_sitemap:
        recs.append("No sitemap.xml found — makes it harder for Google to fully index your service pages.")
    reviews = gbp.get("reviews") or 0
    if reviews < 30:
        recs.append("Under 30 Google reviews — most homeowners compare review counts before calling, this is limiting trust at a glance.")
    if technical.get("internal_link_count", 0) < 5:
        recs.append("Very few internal links/pages — likely a single-page site with no dedicated pages per service or city, which limits how many searches you can rank for.")
    if not technical.get("mentions_phone"):
        recs.append("Phone number isn't clearly visible on the page text — make sure it matches exactly what's on your Google Business Profile (mismatched name/address/phone across listings quietly hurts local ranking).")
    return recs[:6]  # cap at 6 for a clean one-pager


def audit_installer(installer):
    website = (installer.get("website") or "").strip()
    result = {
        "name": installer.get("name"),
        "location": installer.get("location"),
        "phone": installer.get("phone"),
        "website": website,
        "rating": installer.get("rating"),
        "reviews": installer.get("reviews"),
        "recommended": installer.get("recommended"),
        "specialty": installer.get("specialty"),
        "audited_at": datetime.utcnow().isoformat() + "Z",
    }

    if not website:
        result["error"] = "No website on file"
        result["score"] = None
        return result

    resp, load_time, err = safe_get(website)
    if err or resp is None:
        result["error"] = f"Site unreachable: {err}"
        result["score"] = 0
        result["grade"] = "F"
        result["recommendations"] = ["Website did not load during audit — verify it's still live. An unreachable site loses every visitor who clicks through from Google."]
        return result

    has_ssl = check_ssl(website)
    has_robots, has_sitemap = check_robots_sitemap(resp.url)
    technical = analyze_html(resp.text, resp.url)

    score, breakdown = score_site(
        technical,
        {"rating": installer.get("rating"), "reviews": installer.get("reviews"), "recommended": installer.get("recommended")},
        load_time,
        has_ssl,
        has_robots,
        has_sitemap,
    )
    recs = build_recommendations(technical, installer, has_ssl, has_robots, has_sitemap, load_time)

    result.update({
        "score": score,
        "grade": grade_for(score),
        "breakdown": breakdown,
        "load_time_sec": round(load_time, 2) if load_time else None,
        "has_ssl": has_ssl,
        "has_robots": has_robots,
        "has_sitemap": has_sitemap,
        "technical": technical,
        "recommendations": recs,
    })
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, help="Path to region installer JSON file")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--out", default="reports")
    args = ap.parse_args()

    installers = json.loads(Path(args.json).read_text())[: args.limit]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for installer in installers:
        print(f"Auditing: {installer.get('name')} ({installer.get('website')})")
        res = audit_installer(installer)
        results.append(res)
        print(f"  -> score={res.get('score')} grade={res.get('grade')}")

    out_file = out_dir / "audit_results.json"
    out_file.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nSaved {len(results)} results to {out_file}")


if __name__ == "__main__":
    main()
