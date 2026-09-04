# SEO Manual Actions Needed — September 3, 2026

Items from the September 3 audit that need the user's input, an external data source not available in this environment, or a judgment call. Nothing below was fabricated — nothing is claimed as done that wasn't verified directly.

## 1. Highest priority: doorway/near-duplicate content across ~100+ pages (real finding, unresolved)

The audit found 33 groups of category subpages (water-heater, solar, ev-charger, windows-doors, insulation, smart-thermostats, battery, windows) that are **byte-identical to their sibling city pages except for the city name** — confirmed by direct diff, not estimated. Affected clusters: VT (Rutland/South Burlington/Montpelier/Barre), CO Front Range (Aurora/Denver/Boulder), several CA metro clusters (Bay Area, Inland Empire, San Diego, LA, Sacramento), and a 12-city BC windows cluster.

This is the same class of issue fixed twice before on this site. Full details and file lists are in `seo-audit-fixes-2026-09-03.md` §3. It was **not fixed** in this pass because real fixes require genuine city-specific content (actual local utility names, real housing-stock notes, real rebate specifics) for each page — not template text. Recommend: treat as its own content project, city cluster by city cluster, similar to the BC verification skill pattern already in use.

## 2. Semrush export — not available in this environment
No Semrush export file exists in the repo, and there's no way to pull one from this environment. If you want competitive-gap or backlink data folded into future audits, export from Semrush (Organic Research → Positions, or Backlink Analytics) and drop the CSV in the repo (e.g. `reports/semrush-export-<date>.csv`).

## 3. Google Business Profile data — not available
No GBP export or API connection exists in this repo. If there's a Business Profile for HomePowerRebate (or for the installer directory's own listing), export insights/reviews data manually if you want it factored into local-SEO recommendations.

## 4. Lighthouse / Core Web Vitals — not run, no fabricated scores
This environment has no way to run Lighthouse against the live production site. I did not fabricate performance scores. If you want real Core Web Vitals data:
- Run Lighthouse manually in Chrome DevTools against a few representative page types (homepage, a city page, a blog post), or
- Pull the real field data already sitting in Search Console's Core Web Vitals report, or
- Use the `web-perf` skill available in this environment, which can drive a real Chrome instance against a URL you approve — say so if you want that run now.

## 5. GSC / indexation data — both scheduled reports are blocked (pre-existing, not caused by this audit)
`reports/gsc-analysis-2026-08-27.md` and `reports/gsc-analysis-2026-07-27.md` both report **BLOCKED — no GSC data source available** — two consecutive blocked runs. No credentials file (`~/.homepowerrebate-gsc-credentials.json`), no `gsc-export.csv`, and no `seo` skill provider installed (that requires interactive human approval once). This audit inherited that same blocker — indexation status, query-level impressions, and click data could not be verified for this report. Recommend picking one of the three unblock paths already documented in those reports (OAuth/service-account credentials file is the lowest-maintenance long-term fix).

## 6. AEO direct-answer pattern — not re-audited this pass
FAQPage schema coverage was verified (~99%, healthy), but the deeper AEO checks (concise 40–100 word direct answers under key H2s, table presence) from `hpr_content_listicle_strategy` weren't re-verified for regression in this pass due to scope. Worth a dedicated follow-up if AI Overview visibility is a current priority.

## 7. Judgment call already made, flagging for visibility
The `/ca/bc/fortis-rebates` broken link (from `blog-heat-pump-vs-ac-cost-rebates.html`) was repointed to `/ca/bc/` (the BC provincial hub, which covers FortisBC programs) rather than to a specific FortisBC-only page, since no such page exists. If a dedicated FortisBC page is wanted, that's a new-page project, not a fix.
