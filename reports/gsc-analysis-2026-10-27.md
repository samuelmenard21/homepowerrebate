# GSC Content Gap Analysis — 2026-10-17 to 2026-10-23

Live data via `seo gsc-query --project=homepowerrebate` (7-day window, ends 3 days back for Search Console lag). Compared against `gsc-analysis-2026-10-20.md`.

## Summary
- Total queries analyzed: 1,613 unique (2,046 query-page rows), 8,609 impressions, 29 clicks (last week: 1,341 queries, 6,985 impressions, 25 clicks)
- Tier 1 gaps (10+ impressions, 0 clicks): 160 queries
- Tier 2 gaps (20+ impressions, 1-3 clicks, CTR under 5%): 5 queries
- Tier 3 (5-9 impressions, 0 clicks): 188 queries
- **Nova Scotia cluster:** 2,629 impressions (30.5% of all) and 16 clicks. Up from about 2 clicks on the top query last week: "ns heating rebate check status" now has 602 impressions and 9 clicks (1.5%). The status post is working but most of the cluster still shows 0 clicks at positions 4-11.
- **New cluster: Quebec Logivert.** 418 impressions, 0 clicks across `/fr/qc/`, `/ca/qc/heat-pump/`, `/ca/qc/heat-pump/fr/`, `/fr/qc/thermopompe/`. Queries: "programme logivert" 61, "subvention logivert" 51, "logivert program" 23, "hydro quebec logivert" 20, "subvention thermopompe" 18. Positions 60-90, so not yet competitive.
- Impressions up about 23% week over week; clicks flat. Most growth is installer-directory pages at positions 50-85, which is noise for decisions.

## Top 10 Abandoned Queries (Highest Opportunity)
Aggregated across pages. Branded installer lookups excluded.

| Query | Impressions | Clicks | Avg Position | CTR | Category | Status |
| --- | --- | --- | --- | --- | --- | --- |
| heating rebate status | 184 | 0 | 11.0 | 0% | How-to (NS) | Optimize |
| heating rebate check status | 130 | 0 | 6.0 | 0% | How-to (NS) | Optimize |
| free thermostat ottawa | 120 | 0 | 47.6 | 0% | City-specific (ON) | Monitor (title already updated) |
| harp nova scotia | 115 | 0 | 8.5 | 0% | Program (NS) | Optimize |
| ns heating rebate 2026 payment dates | 109 | 0 | 6.9 | 0% | How-to (NS) | Optimize |
| energy rebates penticton bc | 100 | 0 | 64.3 | 0% | City-specific (BC) | Monitor (still lands on Kelowna) |
| heat rebate 2026 | 85 | 0 | 12.1 | 0% | How-to (NS) | Optimize |
| bosch vs mitsubishi heat pump | 82 | 0 | 4.7 | 0% | Brand comparison | Optimize snippet |
| air conditioner rebate alberta | 77 | 0 | 30.1 | 0% | City/region-specific (AB) | New Post |
| check harp status | 76 | 0 | 6.1 | 0% | How-to (NS) | Optimize |

Also in the Tier 2 list: "check status of heating rebate" (339 impressions, 3 clicks, position 5.9), "heat rebate status" (122, 1 click, 4.9), "bc hydro air fryer rebate" (61, 2 clicks, 7.7).

Excluded as branded/installer lookups: Climate Masters (West Babylon NY, 102 impressions), Hunter & Sons (Lowell MA), RPR Heating and Air Conditioning reviews (Penticton).

## Recommended New Blog Posts (Top 5)
1. **"Air Conditioner Rebates in Alberta 2026: What Exists and What Doesn't"** — "air conditioner rebate alberta" (77, pos 30.1)
   - Impressions: about 330/month (69 last week, 77 now)
   - Relevance: `/ca/ab/` is honest that Alberta has little provincial money; no page answers the AC question directly.
   - Angle: answer "is there a rebate?" in the first 50 words, then city programs, financing, and heat-pump-as-AC economics. Verify current program status first.
2. **"Logivert 2026: Quebec's Heat Pump Rebate Explained"** (English, with a French sibling) — "programme logivert" 61, "subvention logivert" 51, "logivert program" 23, "hydro quebec logivert" 20
   - Impressions: about 1,800/month across the cluster
   - Relevance: pure program-name intent, zero clicks, and Quebec pages already exist. Competition on the French queries may be thin.
   - Angle: what Logivert is, who qualifies, how it stacks with federal money. Verify against the official Hydro-Québec page before publishing (rate-drift lesson). The current Quebec pages sit at positions 60-90, so a dedicated program page should beat them.
3. **"Thermostat Rebates in Ontario 2026: Which Programs Are Live"** — "smart thermostat rebate" 45 plus "ecobee rebate" 42, "thermostat rebate" 27, "ontario thermostat rebate 2026" 37, "smart thermostat rebate ontario" 23, "thermostat rebate ontario" 23
   - Impressions: about 900/month combined
   - Relevance: roughly 200 impressions a week on one page at positions 10-47 with 1 click total. The existing post is a comparison; the queries want a program-status answer.
   - Angle: treat as an optimization first (below). Write a separate post only if the comparison can't carry the "which rebates are live" intent without being rewritten.
4. **"Heat Pump Rebates in Colorado: Xcel Energy and Denver 2026"** — "xcel energy rebates colorado" 18, plus "denver solar companies" 21 and "solar companies in denver colorado" 22
   - Impressions: about 260/month
   - Relevance: Colorado pages exist but rank at position 70-85. Low priority until the state hub moves.
   - Angle: Xcel program summary with citations. Needs verified data.
5. **"PPL and PECO Heat Pump Rebates in Pennsylvania 2026"** — "heat pump rebates" 32 on `/us/pa/` (pos 36), "ppl rebates" 21, "pse rebates heat pumps" 22
   - Impressions: about 320/month
   - Relevance: US expansion page at position 36-90; PPL is a concrete, citable hook.
   - Angle: utility rebates plus federal credits. Needs verified program data.

## Recommended Content Optimizations (Top 3)
1. **`/blog/nova-scotia-heating-rebate-2026-27-payment-dates-status/` and `/programs/nova-scotia-heating-assistance-rebate-harp/`** — 2,629 impressions combined, 16 clicks
   - Add keywords: "heating rebate status," "heating rebate check status," "heat rebate 2026," "check HARP status" in H1, first paragraph, and an FAQ block
   - What changed: last week's lead query now gets clicks (9 on "ns heating rebate check status"), so the status-first approach works. The broader variants ("heating rebate status" pos 11, "harp nova scotia" pos 8.5) are the next gap.
   - Missing sections: a one-line "how to check your status" answer with the official link at the top; a "why it says pending" table; confirm the programs page and the blog post link to each other so they don't split the cluster.
   - Estimated CTR lift: 1.5% to 3-5% on positions 4-7, about 40-80 extra clicks per week.
2. **`/blog/ontario-smart-thermostats-100-rebate-compared/`** — about 380 impressions, 1 click
   - Add keywords: "thermostat rebate Ontario 2026," "ecobee rebate" (query 42 impressions at position 10), "smart thermostat rebate"
   - Missing sections: a "which rebates are live right now" table at the top; an Ecobee-specific rebate section.
   - Estimated CTR lift: 0.3% to 3%.
3. **`/blog/bc-hydro-product-rebates-appliances/`** — "bc hydro air fryer rebate" 61 impressions/2 clicks at position 7.7; "bc hydro furnace rebate" 21; "bc hydro rebates air conditioner" 19
   - The post already covers air fryers (the offer runs until March 5, 2027), so this is a snippet problem. Lead the meta description with the yes/no answer and the end date. Add short "furnace" and "air conditioner" answers so the other queries land on a direct answer.
   - Estimated CTR lift: 3% to 8% on the air fryer query.

Also worth a look: `/blog/heat-pump-brands-comparison-mitsubishi-daikin-bosch/` ("bosch vs mitsubishi heat pump" 82 impressions at 4.7, 0 clicks, second week in a row) and `/blog/smart-thermostat-comparison-nest-ecobee-honeywell-mysa/` ("mysa vs ecobee" 39 at 3.1, "mysa vs nest" 20 at 3.7, 0 clicks). Both match the query already; the fix is a verdict-first meta description.

## City Page Updates Needed
- **Penticton**: "energy rebates penticton bc" (100, pos 64) still lands on `/ca/bc/kelowna/`. The Penticton title already reads "Penticton Energy Rebates 2026: FortisBC and the City Loan". Check when that title shipped; if under 90 days, wait. If it has settled, add internal links from Kelowna and the BC hub with that exact anchor.
- **Ottawa thermostats**: "free thermostat ottawa" (120, pos 47.6) is up from 73. The title already says "Free Thermostat in Ottawa 2026". Verify the program is still live; otherwise wait for it to settle.
- **Ontario installer pages**: Hamilton heat pump (350 impressions across ~6 queries), Kitchener (202), Vaughan (35 plus "heat pump rebate vaughan" 21 at position 15). All at positions 50-80. "heat pump rebate vaughan" at 15 is the only near-term one; add a rebate-first section to `/ca/on/vaughan/heat-pump/`.
- **BC hub and furnace page**: "bc hydro rebates heat pumps" (17, pos 26.9), "bc ac rebate" (18, pos 35.4), "furnace rebates bc 2026" (18, pos 9.2) on `/furnace-rebates/bc/`. The last one is already near page one; check the title carries "2026".
- **Massachusetts**: "heat pump incentives springfield ma" (20, pos 10.3) on `/us/ma/springfield/` and "mass save heat pump rebates massachusetts" (28, pos 73).
- **Quebec**: see the Logivert cluster above. The French pages need an H1 that uses "Logivert" and "subvention thermopompe" in French.

## Notes
- Data from: 2026-10-17 to 2026-10-23 (7 days), query+page, 2,046 rows.
- Install-page queries at position 60+ (Denver solar, Hamilton heat pump) are listed for completeness but are noise for decisions; don't act on them until they reach the top 20.
- Positions for page-level claims come from the aggregated query view; confirm with an exact page+query filter before editing.
- Next review: Monday 2026-11-02.
