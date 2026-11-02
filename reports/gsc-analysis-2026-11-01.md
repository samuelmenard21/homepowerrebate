# GSC Content Gap Analysis — 2026-10-23 to 2026-10-29

Live data via `seo gsc-query --project=homepowerrebate` (7-day window, ends 3 days back). Run on Sunday 2026-11-01. Compared against `gsc-analysis-2026-10-27.md`.

## Summary
- Total queries analyzed: 1,974 unique (2,572 query-page rows), 11,207 impressions, 34 clicks (last week: 1,613 queries, 8,609 impressions, 29 clicks)
- Tier 1 gaps (10+ impressions, 0 clicks): 206 queries
- Tier 2 gaps (20+ impressions, 1-3 clicks, CTR under 5%): 10 queries
- Tier 3 (5-10 impressions, 0 clicks): 297 queries
- **Nova Scotia cluster still dominates:** status post 1,890 impressions, 14 clicks, avg position 5.7; HARP program page 907 impressions, 3 clicks, position 9.1. Together about 25% of all impressions. Clicks are low for position 4-7 (see below).
- **New cluster: Newfoundland and Labrador heating/oil rebate.** `/ca/nl/heating-assistance/` has 786 impressions and 2 clicks at position 9.2. Queries: "oil rebate nl 2026" 93, "home heating rebate 2026" 99, "home heating rebate nl 2026" 68, "home heating supplement program" 74 combined, "oil rebate nl" 33. The page was rewritten on 2026-10-27, so it is inside its window.
- Impressions up 30% week over week; clicks +5. Growth is mostly NS/NL (seasonal "heating rebate" interest) plus installer pages at positions 40-90, which is noise.

## Change ledger status (LEDGER.md)
All rows were changed 2026-10-23 to 2026-10-27, so none is near its 2027-01 check date. Not due for judging. Early read only, exact page and query:

| Page | Query | Last week | This week | Note |
| --- | --- | --- | --- | --- |
| /ca/bc/penticton/ | energy rebates penticton bc | pos 64.3 / 100 impr, lands on Kelowna | 72 impr, pos 55.3 on Kelowna; Penticton page has 14 impr at pos 12.9 | Penticton page now shows for the query at pos 12.9 (small sample). Not due. |
| /ca/on/ottawa/smart-thermostats/ | free thermostat ottawa | pos 47.6 / 120 | 93 impr, pos 41.5; Ottawa page 31 impr at pos 36.6 | Slightly better, 0 clicks. Not due. |
| NS status post | heating rebate status cluster | pos 5.4-11 | status post now avg 5.7 on 1,890 impr | Top-20 pass shows in position, clicks still thin. Not due. |
| /ca/qc/heat-pump/ and /fr/ | logivert, programme logivert | ~60-90 | pos 88-91, 0 clicks | No movement yet (indexing lag). Not due. |
| /furnace-rebates/alberta/ | air conditioner rebate alberta | pos 30.1 / 77 | 71 impr, pos 24.2, still lands on /ca/ab/ (64) | Improving. Not due. |
| /ca/nl/heating-assistance/ | oil rebate nl 2026 and friends | new | 786 impr, pos 9.2, 2 clicks | Added to ledger this run (baseline). |

Recommendation for ledger pages: leave all alone.

## Top 10 Abandoned Queries (Highest Opportunity)
Aggregated across pages. Installer-name and phone-number queries excluded (e.g. Climate Masters West Babylon, 78 impressions).

| Query | Impressions | Clicks | Avg Position | CTR | Category | Status |
| --- | --- | --- | --- | --- | --- | --- |
| heat rebate 2026 | 221 | 0 | 8.2 | 0% | How-to (NS) | Not due (NS pass 10-27) |
| heating rebate check status | 174 | 0 | 5.8 | 0% | How-to (NS) | Not due |
| heat rebate status | 151 | 0 | 4.2 | 0% | How-to (NS) | Not due |
| harp nova scotia | 131 | 0 | 7.3 | 0% | Program (NS) | Not due |
| ns heating rebate 2026 payment dates | 112 | 0 | 6.4 | 0% | How-to (NS) | Not due |
| home heating rebate 2026 | 99 | 0 | 8.3 | 0% | Program (NL) | Not due (NL pass 10-27) |
| free thermostat ottawa | 93 | 0 | 41.5 | 0% | City-specific (ON) | Not due |
| energy rebates penticton bc | 72 | 0 | 55.3 | 0% | City-specific (BC) | Not due |
| air conditioner rebate alberta | 71 | 0 | 24.2 | 0% | Region (AB) | Not due |
| mass save heat pump rebates massachusetts | 66 | 0 | 77.5 | 0% | Region (MA) | Monitor (pos 77) |

Next tier outside the ledger: "ontario thermostat rebate 2026" 64 (pos 7.8, ledger page), "bosch vs mitsubishi heat pump" 60 (pos 3.8, 0 clicks), "thermostat rebate" 57, "mysa vs ecobee" 30 (pos 2.5, 0 clicks), "bc hydro air fryer rebate" 183 impr with 1 click (pos 8.1).

## Recommended New Blog Posts (Top 5)
No strong new-post gaps this week. Nearly every top query already has an owner page. Candidates, all lower confidence:

1. **Air fryer rebate stands alone as a query** — "bc hydro air fryer rebate" (183 impr, 1 click, pos 8.1; plus "bc hydro rebate air fryer" 18)
   - Relevance: Seasonal and specific ($25 until March 5, 2027, per the post). Already answered in `/blog/bc-hydro-product-rebates-appliances/`, so this is an optimization, not a new post.
2. **"Mysa vs Ecobee" snippet** — "mysa vs ecobee" 30 impr at pos 2.5, 0 clicks. Covered by `/blog/smart-thermostat-comparison-nest-ecobee-honeywell-mysa/`. Position is already top 3, so zero clicks is odd; check the SERP title before editing.
3. **Hamilton and Kitchener heat pump installers** — "heat pump hamilton" 63, "heat pump installation hamilton" 55, "heat pump kitchener" 56. Installer pages exist; they sit at pos 45-56. Not a content gap, an authority gap. No new post.
4. **Tesla Powerwall 3 rebates by state** — "tesla powerwall state rebates usa homeowners 2025" 16 at pos 8.4, "powerwall 3 rebate hawaii" 10. `/batteries/tesla-powerwall-3/` has 196 impr at pos 29. Possible US battery listicle; verify US state data first. Low volume.
5. **Logivert (Quebec)** — cluster still at position 70-90. A new post will not fix that; wait for the check date.

## Recommended Content Optimizations (Top 3)
1. **/blog/bc-hydro-product-rebates-appliances/** — 360 impr, 1 click, pos 13.4. The air fryer answer is in the top paragraph, but the title ("BC Hydro Rebates 2026: Appliances, Free Thermostats, AC...") does not say air fryer. Not in the ledger. Option: add "air fryer" to the title or meta description only. Estimated CTR lift: 1% to 3% on the air fryer queries.
2. **/blog/heat-pump-brands-comparison-mitsubishi-daikin-bosch/** — "bosch vs mitsubishi heat pump" 60 impr, pos 3.8, 0 clicks. Title already starts "Bosch vs Mitsubishi Heat Pump (2026)". Check the live SERP snippet; if the meta does not answer which one wins, rewrite it answer-first. Not in the ledger.
3. **/ca/on/heating-assistance/** — 167 impr, 0 clicks, pos 32. Not in the ledger. Low priority until it breaks the top 20.

## City Page Updates Needed
- Penticton and Ottawa: no change, inside window.
- Hamilton, Kitchener, Vaughan ("vaughan heat pump" 29, pos 44.6): installer and city pages rank 45-56. No on-page fix visible from this data; inbound links are the lever (see monthly links run).
- Chula Vista, CA ("heat pump installation near me" 60, pos 40): installer page appearing for a generic query. Ignore.

## Internal Linking
Internal linking: skipped (not due). Latest report is `internal-links-2026-10-27.md` (5 days old). Next due the first Monday of the month after 4 weeks have passed (2026-11-24 or the 2026-12-07 run).

## Notes
- Data from 2026-10-23 to 2026-10-29. Next review: Monday 2026-11-09 (week of 11-02 baseline for ledger rows will land in that run).
- Ledger row added this run: `/ca/nl/heating-assistance/` (changed 2026-10-27, check 2027-01-25).
- Git log shows no new SEO edits to blog or city pages beyond those already in the ledger since 10-27 (the other 10-27 commits were NL features, LinkedIn, video, installer data and a federal rebate fact update).

## This week's list
Page changes (max two):
1. `/blog/bc-hydro-product-rebates-appliances/` — add "air fryer" to the meta description (and title if it fits under the length limit). Outside any window; real query with 183 impressions.
2. `/blog/heat-pump-brands-comparison-mitsubishi-daikin-bosch/` — only if the live snippet fails to say which brand wins; check the SERP first.

New pages (max two): none recommended. No gap lacks an owner page.

Backlog: Powerwall state-rebate listicle, Ontario heating-assistance page (wait for ranking to reach top 20), Mass Save MA page (pos 77).
