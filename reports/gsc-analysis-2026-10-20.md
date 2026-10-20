# GSC Content Gap Analysis — 2026-10-11 to 2026-10-17

Live data via `seo gsc-query --project=homepowerrebate` (7-day window, ends 3 days back for Search Console lag). Compared against `gsc-analysis-2026-10-05.md`.

## Summary
- Total queries analyzed: 1,341 unique (1,618 query-page rows), 6,985 impressions, 25 clicks in 7 days (last week: 427 queries, 1,879 impressions, 5 clicks)
- Tier 1 gaps (10+ impressions, 0 clicks): 122 queries
- Tier 2 gaps (20+ impressions, 1-3 clicks, CTR under 5%): 6 queries
- Tier 3 (5-9 impressions, 0 clicks): 157 queries
- **Biggest finding:** the Nova Scotia heating rebate cluster is now about 2,700 of 6,985 impressions (about 39%), with roughly 10 clicks. The status/payment-date post we shipped after last week's report (`/blog/nova-scotia-heating-rebate-2026-27-payment-dates-status/`) already earns 1,902 impressions, ranks at positions 3-8 for its main queries, and still converts under 1%. The problem is now click-through, not coverage.
- Impressions grew about 3.7x week over week. Most of the growth is the NS cluster plus installer-directory pages.

## Top 10 Abandoned Queries (Highest Opportunity)
| Query | Impressions | Clicks | Avg Position | CTR | Category | Status |
| --- | --- | --- | --- | --- | --- | --- |
| ns heating rebate check status | 643 | 2 | 5.4 | 0.3% | How-to (NS) | Optimize title/snippet |
| heating rebate status | 183 | 0 | 7.7 | 0% | How-to (NS) | Optimize |
| check status of heating rebate | 201 | 1 | 5.2 | 0.5% | How-to (NS) | Optimize |
| ns heating rebate 2026 | 159 | 1 | 10.4 | 0.6% | City-specific (NS) | Optimize |
| heating rebate check status | 120 | 0 | 6.5 | 0% | How-to (NS) | Optimize |
| heat rebate status | 115 | 0 | 4.9 | 0% | How-to (NS) | Optimize (position 4.9, no clicks) |
| heat rebate 2026 | 90 | 0 | 12.6 | 0% | How-to (NS) | Optimize |
| energy rebates penticton bc | 78 | 0 | 60.1 | 0% | City-specific (BC) | Optimize city page (lands on Kelowna, not Penticton) |
| free thermostat ottawa | 73 | 0 | 54.7 | 0% | City-specific (ON) | Optimize / new post |
| bosch vs mitsubishi heat pump | 72 | 0 | 3.3 | 0% | Brand comparison | Optimize title (position 3.3, zero clicks) |

Other notable: "air conditioner rebate alberta" (69, pos 25.9), "heat pump rebate" on `/us/pa/` (49, pos 50.8), "bc hydro rebates" (48, pos 35), "mysa vs ecobee" (45, pos 4.2), "mysa vs nest" (29, pos 4.8), "bc hydro air fryer rebate" (38, pos 7.7).

Excluded as branded/installer lookups: Climate Masters (West Babylon), Walker Brothers (Lynn MA), Hunter & Sons (Lowell MA), Nation Furnace (Langley), and similar name/address queries.

## Recommended New Blog Posts (Top 5)
Last week's top two (NS status/dates, HARP explainer) now exist, so none repeat here.

1. **"Penticton Energy Rebates 2026: FortisBC, City of Penticton and BC Hydro"** — "energy rebates penticton bc" (78)
   - Impressions: 78/week, about 330/month
   - Relevance: pure city-rebate intent in a BC city we cover. The query surfaces `/ca/bc/kelowna/` at position 60 even though `/ca/bc/penticton/` exists, so Google isn't matching our own Penticton page to it. Penticton has its own electric utility, which makes a standalone guide a real differentiator.
   - Angle: a hub-style post answering "which utility, which rebates" first, linking into the Penticton page and the existing Penticton heat pump, windows and insulation posts. Counts as an optimization first (see below); write the post only if the page can't rank.
2. **"Air Conditioner Rebates in Alberta 2026"** — "air conditioner rebate alberta" (69, pos 25.9)
   - Impressions: about 300/month
   - Relevance: `/ca/ab/` says honestly that Alberta has no provincial rebate. A post on what does exist (CEIP financing, city programs, federal options) answers a question the hub page buries.
   - Angle: "Is there an AC rebate in Alberta?" answered in the first 50 words, then the real options and a cost-versus-heat-pump comparison. Verify current program status before publishing.
3. **"Free Thermostat Ottawa: Is the Program Still Running?"** — "free thermostat ottawa" (73, pos 54.7)
   - Impressions: about 315/month, up from 30/week last report. Growing.
   - Relevance: high intent; page `/ca/on/ottawa/smart-thermostats/` exists but sits at position 55.
   - Angle: verify the program is live first (rate-drift lesson), then publish one focused answer page and consolidate the split pages.
4. **"BC Hydro Air Fryer Rebate: What Qualifies in 2026"** — "bc hydro air fryer rebate" (38, pos 7.7)
   - Impressions: about 165/month
   - Relevance: the appliance rebate post exists but doesn't name air fryers. Check whether air fryers are actually eligible before writing; if not, a short "what is and isn't covered" section may be enough.
   - Angle: eligibility list with a yes/no answer up top.
5. **"Heat Pump Rebates in Pennsylvania 2026"** — "heat pump rebate" (49) on `/us/pa/`, "ppl rebates" (24) on `/us/pa/allentown/`
   - Impressions: about 315/month combined
   - Relevance: US expansion page ranking at position 51. PPL utility rebates are a concrete, citable hook.
   - Angle: PPL territory rebates plus federal credits, tied to the Allentown and statewide pages. Needs verified program data before writing.

## Recommended Content Optimizations (Top 3)
1. **`/blog/nova-scotia-heating-rebate-2026-27-payment-dates-status/` and `/programs/nova-scotia-heating-assistance-rebate-harp/`** — about 2,300 combined impressions, 2 clicks per top query
   - Add keywords: "check status," "heating rebate status," "heat rebate 2026," "HARP status" in the H1, first paragraph and an FAQ block
   - The post title is "When Will My NS Heating Rebate Arrive?" while the dominant queries are "check status." The programs page title already says "Check Your NS Heating Rebate Status" but ranks lower for those terms. Two of our own pages may be splitting the same intent; pick one canonical page for "check status" and link the other to it.
   - Missing sections: a status-check answer in the first line (link to the official tool), a "why it says pending" table
   - Estimated CTR lift: 0.5% to 3-5% at positions 4-7, which would be roughly 50-100 extra clicks per week
2. **`/blog/heat-pump-brands-comparison-mitsubishi-daikin-bosch/`** — "bosch vs mitsubishi heat pump" 72 impressions at position 3.3, 0 clicks
   - Title "Bosch vs Mitsubishi Heat Pump (2026)" matches the query already, so the snippet needs a reason to click: lead the meta description with a verdict (which wins for cold climates, price gap) and consider a short comparison table near the top.
   - Estimated CTR lift: 0% to 8-10% (5-7 extra clicks per week)
3. **`/blog/smart-thermostat-comparison-nest-ecobee-honeywell-mysa/`** — "mysa vs ecobee" 45 and "mysa vs nest" 29, positions 4-5, 0 clicks
   - Add a "Mysa vs Nest" subsection (the phrase appears once on the page, "Mysa vs Ecobee" 15 times) and a verdict-first meta description.
   - Estimated CTR lift: 0% to 6-8%

## City Page Updates Needed
- **Penticton**: "energy rebates penticton bc" (78) lands on Kelowna. Add "energy rebates" to the Penticton H1/title (current: "Penticton Home Energy Rebates 2026: FortisBC Rebates"), add internal links from the Kelowna page and BC hub, and check why Kelowna outranks it. Also "rebates for window replacement kelowna" (20) shows Kelowna windows demand.
- **Ontario installer pages**: Hamilton heat pump (326 impressions combined across "heat pump installation hamilton" 64, "heat pump hamilton" 41), Kitchener (162), Cambridge (67). All at position 40-60 with zero clicks. Add city-specific rebate and cost sections so they rank above generic directory listings.
- **BC hub `/ca/bc/`**: "bc hydro rebates" (48), "bc hydro rebates for heat pumps" (21), "energy rebates bc" (19) at positions 33-40. Add a BC Hydro rebate summary near the top.
- **`/furnace-rebates/bc/`**: "bc hydro furnace rebate" (24, pos 47.8). Confirm the page says BC Hydro doesn't offer furnace rebates (CleanBC/FortisBC do) so it answers the query directly.
- **`/smart-thermostats/`**: "thermostat rebate" (23), "smart thermostat rebate" (22), "bc hydro smart thermostat rebate" (22), positions 38-44. Two URL variants (with and without trailing slash) show up in the data; confirm canonical tags.

## Notes
- Data from: 2026-10-11 to 2026-10-17 (7 days), query+page, 1,618 rows.
- The "bosch vs mitsubishi" and Mysa pages already include the exact phrases; the gap is click-through, not coverage.
- A few Tier 1 queries over 10 impressions are page-level duplicates of the NS cluster; counts above aggregate across pages.
- Next review: Monday 2026-10-27.
