---
name: hpr-seo-reports
description: Run SEO/GSC reports for HomePowerRebate using the already-connected Search Console project. Use whenever the user asks for an SEO report, keyword opportunity check, technical crawl, or ranking data for homepowerrebate.com.
---

# HomePowerRebate SEO Reports

The global `seo` CLI skill covers general usage. This file only captures the
project-specific setup so it's never rediscovered from scratch.

## The property gotcha (already solved, don't redo this)

Google Search Console has two separate property types for the same site:
- **Domain property** (`sc-domain:homepowerrebate.com`) — DNS-verified, covers
  all subdomains/protocols.
- **URL-prefix property** (`https://homepowerrebate.com/`) — verified
  separately, covers only that exact prefix.

`seo start`'s default guess picked the domain property, but the account
(`samuelmenard@gmail.com`) is only a verified Owner on the **URL-prefix**
property. Every report call against the domain property fails with "Google
Search Console denied access" even though auth/scopes are fine — it's a
per-property permission check, not an auth problem. Confirmed via `seo sites`,
which lists the real owned properties.

**The project is already configured correctly** as of 2026-09-01:

```
seo report --project homepowerrebate-com
```

If a future session hits the same "denied access" error again (e.g. after a
`seo start` rerun resets it), fix it the same way:

```bash
seo sites                                    # confirms the real owned property
seo projects add --id homepowerrebate-com \
  --site "https://homepowerrebate.com/" \
  --url "https://homepowerrebate.com" \
  --default
```

## Useful commands for this project

- `seo report --project homepowerrebate-com` — main report: performance,
  content opportunities, technical fixes with search value, priorities.
- `seo crawl --project homepowerrebate-com` — technical crawl. Note: capped
  at 500 pages by default; the site has 2,000+ pages (968 rebate pages, 896
  installer profiles, 127 blog posts, plus hub/index pages), so one crawl
  won't cover everything. Re-run periodically or investigate specific
  sections separately if a report flags an issue the crawl didn't localize.
- `seo cannibal --project homepowerrebate-com --days 90 --limit 25` — finds
  queries split across competing URLs (the site's programmatic city/category
  page structure makes this a real risk worth checking periodically).
- `seo second-page --project homepowerrebate-com --days 90` — pages ranking
  10-20, close to page one.
- `seo refresh-priorities --project homepowerrebate-com --days 90 --verify-content --limit 25` —
  turns a report into a ranked, content-verified action queue.
- `seo technical-watch --project homepowerrebate-com --limit 50` — saves a
  crawl/index baseline so future reports can flag technical drift.

## First real findings (2026-09-01, for context — re-check before trusting as current)

- "mysa vs ecobee" ranks position 14.3, 141 impressions, on
  `/blog/smart-thermostat-comparison-nest-ecobee-honeywell-mysa/` — a real
  striking-distance opportunity.
- Possible cannibalization on "insulation rebates" (3 competing URLs) —
  needs `seo cannibal` to confirm whether it's real duplication or distinct
  intents that just look similar.
- A `jsonld_invalid` finding from the main report wasn't localized by the
  500-page-capped crawl — if it resurfaces, it may predate this session's
  extensive JSON-LD validation pass across blog/rebate/installer pages, or
  live outside the crawled 500. Re-verify before assuming it's still real.
