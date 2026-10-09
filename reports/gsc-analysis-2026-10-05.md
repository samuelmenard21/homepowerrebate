# GSC Content Gap Analysis — 2026-09-26 to 2026-10-02

Live data via `seo gsc-query --project=homepowerrebate` (the same route `scripts/gsc_weekly_report.py` uses). Window ends 3 days back because Search Console lags.

An earlier version of this report said credentials were missing. That was wrong. The task file names a credentials path that doesn't exist, and I didn't look for the working setup. This version replaces it.

## Summary
- Total queries analyzed: 427 unique (522 query-page rows), 1,879 impressions, 5 clicks in 7 days
- Tier 1 (10+ impressions, 0 clicks): 35 queries
- Tier 2 (20+ impressions, 1-3 clicks): 2 queries
- Tier 3 (5-9 impressions, 0 clicks): 53 queries
- **Biggest finding:** 796 of 1,879 impressions (42%) come from one cluster, Nova Scotia heating rebate (HARP), all landing on `/ca/ns/`, with 2 clicks.

## Top 10 Abandoned Queries (Highest Opportunity)
| Query | Impressions | Clicks | Avg Position | CTR | Category | Status |
| --- | --- | --- | --- | --- | --- | --- |
| heat rebate 2026 | 121 | 0 | 10.6 | 0% | How-to/educational (NS) | Optimize /ca/ns/ + new post |
| heating rebate 2026 | 83 | 0 | 10.6 | 0% | How-to/educational (NS) | Optimize + new post |
| ns heating rebate 2026 | 80 | 0 | 3.7 | 0% | City-specific (NS) | Optimize (position 3.7, no clicks: title/meta problem) |
| ns heating rebate 2026 payment dates | 55 | 0 | 10.0 | 0% | How-to (NS) | New post |
| power rebate 2026 | 49 | 1 | 6.1 | 2% | Generic rebate (NS) | Optimize |
| ns heating rebate 2026 2027 | 39 | 0 | 7.0 | 0% | How-to (NS) | New post |
| ns power rebate 2026 | 33 | 0 | 10.3 | 0% | City-specific (NS) | Optimize |
| harp rebate ns | 32 | 0 | 10.5 | 0% | How-to (NS) | Optimize + new post |
| mysa vs ecobee | 29 | 0 | 5.8 | 0% | Brand comparison | Optimize (position 5.8, no clicks) |
| ns heating rebate check status | 27 | 0 | 10.3 | 0% | How-to (NS) | New post |

## Recommended New Blog Posts (Top 5)
1. **"Nova Scotia Heating Rebate 2026-27: Payment Dates and How to Check Your Status"** — "ns heating rebate 2026 payment dates" (55), "ns heating rebate check status" (27), "check status of heating rebate" (12), "heating rebate status" (11), "heat rebate status" (5), "heat rebate 2026 payment dates" (20)
   - Impressions: about 130/week for status/dates queries alone, roughly 550/month
   - Relevance: pure rebate intent, and the 2026-27 application window opened Oct 1, so demand is at its seasonal peak.
   - Angle: dedicated page with the answer in the first 50 words, a dates table, a status-check walkthrough, an FAQ. Source dates from the official provincial page (external citation standard). Re-verify amounts and dates before publishing (rate-drift lesson).
2. **"What Is HARP? Nova Scotia's Home Heating Assistance Rebate Explained"** — "harp rebate ns" (32), "harp heating rebate" (20), "harp rebate status" (18), "apply for harp" (17), "nova scotia harp" (16), plus about 25 more variants
   - Impressions: about 150/week, roughly 650/month
   - Angle: plain-language explainer (grade-6 rule), eligibility, how to apply, and a link into the NS heat pump and water heater rebates. Possible to combine with post 1; I'd keep them separate because "status" and "what is" are different intents.
3. **"Free Thermostat Programs in Ottawa"** — "free thermostat ottawa" (19 + 11 across two pages, positions 40 and 88)
   - Impressions: 30/week. It is split across two weak pages, so one focused page would consolidate it. Verify the program is still live before writing.
4. **"Ontario New Furnace Rebates 2026"** — "new furnace rebates ontario" (8), "ontario new furnace rebate" (8), "ontario gas furnace rebate" (6), "markham furnace rebate" (9), all positions 30-45 on `/furnace-rebates/ontario/`
   - Impressions: about 31/week. The page exists but ranks poorly. Likely an optimization first, new post only if the page can't carry it.
5. **"Calgary Resilient Roofing Rebate Program"** — "calgary resilient roofing rebate" (7), "resilient roofing rebate program calgary" (7), "calgary roofing rebate" (5), positions 21-23
   - Impressions: 19/week. Outside the 8-category standard, so check fit with the 8-category rule before committing.

## Recommended Content Optimizations (Top 3)
1. **/ca/ns/** — 796 impressions on the HARP cluster, 2 clicks. The title is already "Nova Scotia Heating Rebate 2026-27: Status, $400 & Dates", so it was recently retitled and the CTR may still be catching up. Check back in 2 weeks before rewriting again.
   - "ns heating rebate 2026" ranks 3.7 with 0 clicks out of 80 impressions. That is unusual for position 3.7 and worth inspecting the live snippet in Google.
   - Add H2s that match the exact phrases: "payment dates", "check your status", "2026-27", "power rebate".
   - If new posts 1 and 2 are published, link them from this page so queries split by intent.
2. **/blog/smart-thermostat-comparison-nest-ecobee-honeywell-mysa/** — "mysa vs ecobee" 29 impressions at position 5.8 with 0 clicks, "mysa vs nest" 10 at 7.8
   - Add keywords: "mysa vs ecobee", "mysa vs nest" in H2s with a one-line verdict each. At these positions, a title/meta rewrite is the lever.
3. **/blog/heat-pump-brands-comparison-mitsubishi-daikin-bosch/** — "bosch vs mitsubishi heat pump" 15 impressions at position 20.9
   - Add the exact phrase to title/H1 and put a direct verdict in the first 50 words. Estimated CTR lift is small until it reaches page 1.

## City Page Updates Needed
- **/ca/bc/penticton/**: "solar panels penticton" (11, pos 36), "energy audits penticton bc" (6, pos 75), "energy rebates penticton bc" (6, pos 36). Add exact-phrase H2s for solar and energy audits.
- **/us/ny/**: "utility rebates 2026" (11, pos 8.4, 0 clicks). Rewrite title/meta with 2026 and the lead rebate.
- **/ca/ab/**: "power rebates 2026" (7, pos 8.4). Same fix.
- **/ca/bc/chilliwack/**: "hvac rebates" (6) at position 1.8 with 0 clicks. Check the snippet; this should convert.
- **/ca/on/vaughan/**: "heat pump rebate vaughan" (6 + 6, pos 17 and 32), split across two pages. Consider consolidating.
- **/us/vt/barre/solar**: "vt solar rebates" (11, pos 10.7). Add a Vermont-level section or link to the state page.
- **/us/pa/philadelphia/insulation/** and **/us/pa/erie/**: "insulation rebates new york and pennsylvania" (8 + 6). A multi-state phrase; low priority.

## Notes
- Data from: 2026-09-26 to 2026-10-02 (7 days, final data state), 427 unique queries.
- Installer-name and phone-number queries (e.g. "(250) 572-0209 kdb hvac", "vivion energy") were excluded as branded lookups, not content gaps.
- Cross-referencing: `/ca/ns/` title and meta were read. Other pages were matched by URL only, so confirm "optimize" vs "new post" before writing.
- Tier 2 is thin (2 queries) because the site gets very few clicks overall. Most opportunity sits in Tier 1.
- Next review: 2026-10-12
