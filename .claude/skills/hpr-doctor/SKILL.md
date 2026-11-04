---
name: hpr-doctor
description: Weekly site-health bot for HomePowerRebate. Grades speed, mobile, sitemap, broken links and redirects, then reports the 5 fixes that matter most. Report only, changes nothing. Use for "site health", "audit", "what should I fix first".
---

# Doctor: site health (report only)

Run, in this order, and read the output (do not fix anything):
- Speed/mobile on the top 10 pages by Search Console clicks (`hpr-seo-reports`; use the `web-perf` skill / Lighthouse at 390 px). Homepage, a hub, a city page, a ranking page, a profile page at minimum.
- Sitemap: confirm https://homepowerrebate.com/sitemap.xml loads and every indexable page is listed (profiles are noindex and excluded on purpose).
- Links and redirects: `python3 scripts/check_internal_links.py`; `python3 scripts/compact_redirects.py --check` (2,000 static rule limit); look for redirect chains.
- Repo guards: `check_consistency.py`, `check_facts.py`, `check_hub_layout.py`, `check_stylesheet_combos.py`, `check_generator_sync.py` (slow; run last).
- Search Console: indexing errors, the Generative AI report, pages dropping in clicks.

Output: a grade (A-F), then exactly 5 fixes in priority order, one line each with the file/script that owns the fix. Don't pad. Remember: fixes go in generators/data, never by hand-editing pages.
