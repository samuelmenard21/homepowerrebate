# Next regions: 10 US states to add and the Canada gaps

Date: 2026-11-04. Nothing was built, edited or changed. Scores are in `2026-11-04-next-regions-scores.json` (same folder).

## Short version (plain language)

- Add **Connecticut and Maine first**. We already read their rebates on 2026-10-10 and each has a heat pump page. Both are cold, heat with oil a lot, and pay big rebates.
- Next are **Oregon, Maryland, Rhode Island and New Hampshire**. Big or easy rebates, and Rhode Island is one utility.
- States like Texas, Florida, Arizona and Nevada have **small or missing rebates**. They have many people, but we would have little money to show. Build them last.
- In Canada the biggest gap is not new places. It is **7 Ontario cities, Cape Breton, Fort McMurray and Fraser Valley that have pages but are not in `data/regions.json`**, so the picker, PowerScore and coverage checks do not see them.
- Also missing: **utility pages for Hydro One, ENMAX, EPCOR and the Prairie, Quebec and Atlantic utilities**, and **more cities in Quebec, Saskatchewan, Manitoba and New Brunswick**.

## What I could not do or verify (read this first)

1. **No search-volume numbers.** The `keyword-metrics` report failed: "No connected provider can supply keyword metrics" (no DataForSEO, Semrush or Ahrefs connected). The demand score is therefore a rough judgment from state size, heating mix and our own Search Console data, not measured volume. Connect a provider and rerun before committing build days to states ranked 5 to 10.
2. **Search Console on uncovered states is thin.** Property `https://homepowerrebate.com/`, 2026-10-04 to 2026-10-31, `query-clusters` with page scope. `/us/me/` gave 125 impressions, 0 clicks, average position about 60 to 77 (queries like "maine heat pump financing", "efficiency maine heat pump rebate"). `/us/ct/` gave 0 impressions. A scope for the other 18 state names matched no pages, because we have no pages for them. The report's full output was cut to the top 10 clusters, so I could not scan the whole property for stray out-of-region queries.
3. **Program amounts are not verified by me.** For Connecticut and Maine I used our own facts files (read 2026-10-10 on the official pages). For every other state the amounts below come from **web search excerpts of official sites (utility, state energy office), not from reading the page**. Many conflict or look old. Per our rules, treat them as **unverified** until read in the browser pane. I did not read any page in the browser this run.
4. **Installer density is not counted.** I did not run Google Places (cost, and "do not store coordinates"). The installer score is a guess from population and metro count.
5. **Competition is a guess** (no SERP or domain-rating data pulled). Assumed: state energy office and utility pages hold the top spots in every state.
6. **Federal heat pump rebate (early 2027)**: its income line, home types and fuels are not published (fact `federal-*`, status `upcoming`). "Federal fit" is a guess that cold states with oil, propane or electric heat will benefit most.
7. Florida, Nevada, Indiana and New Mexico: searches returned no usable 2026 heat pump amount, so their depth score is the lowest by default, not proven zero.
8. Canada city lists in Part B (largest metro areas) are from memory, **not pulled from StatCan**.

## Part A. Next US states

Score = weighted 0 to 100: rebate depth 30, search demand 20, installer density 15, competition 10 (5 = easy), build cost 15 (5 = cheap), federal fit 10. Each criterion scored 0 to 5.

| Rank | State | Score | Depth | Demand | Installers | Comp. | Build | Fed | Evidence (and status) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Connecticut | 80 | 5 | 3 | 4 | 3 | 4 | 4 | Energize CT $1,500 per ton up to $10,000; standard $250 per ton up to $2,500; Smart-E loan from 1.99% (facts ct-0 to ct-2, read 2026-10-10). Verified. |
| 2 | Maine | 77 | 5 | 3 | 2 | 3 | 5 | 4 | Efficiency Maine $1,000 to $3,000 per outdoor unit, ducted $3,000/$6,000/$9,000, +$500 bonus, loans to $25,000 (facts me-0 to me-4, read 2026-10-10). Verified. 125 GSC impressions already. |
| 3 | Oregon | 72 | 4 | 3 | 4 | 3 | 4 | 3 | Energy Trust of Oregon: ductless $800, ducted $1,000, up to $4,000 regional, HPWH up to $1,200. Unverified (excerpt of energytrust.org sheets, Jan 1 2026). |
| 4 | Maryland | 69 | 4 | 3 | 4 | 3 | 3 | 3 | Pepco: $2,000 to $3,500 install incentive for May 15 to Nov 30 2026; Home Performance up to $15,000. BGE and Maryland HEEHRA not read. Unverified. |
| 5 | Rhode Island | 65 | 4 | 2 | 2 | 3 | 5 | 3 | RI Energy up to $625 per ton, $1,500 per ton from baseboard; state Accelerator $650 per unit; sources conflict ($350/$1,250 on a 2024 form). Unverified. One utility. |
| 6 | New Hampshire | 64 | 4 | 2 | 2 | 3 | 4 | 4 | NHSaves $250 per ton, $2,000 per ton from electric resistance (from Mar 23 2026), HPWH $900, install to Dec 31 2026. Unverified. Eversource, Liberty, Unitil, NH Electric Co-op share one site. |
| 7 | Utah | 59 | 3 | 2 | 3 | 3 | 4 | 3 | Rocky Mountain Power: $1,500, $2,000 or $2,500 depending on page. Unverified, conflicting. |
| 8 | Georgia | 58 | 2 | 3 | 4 | 3 | 4 | 2 | Georgia Power HEIP up to $1,500 heat pump, $2,500 yearly cap, valid Aug 1 2026 to Dec 31 2028. Unverified. One dominant utility. |
| 9 | Ohio | 57 | 2 | 3 | 4 | 3 | 3 | 3 | Duke $500 to $1,000; AEP and FirstEnergy numbers outdated (2020 and 2023). Unverified. |
| 10 | Texas | 57 | 2 | 4 | 5 | 2 | 2 | 2 | Austin Energy HPWH $1,000; Oncor 2026 funds spent; CenterPoint small. Unverified. Many utilities, so doorway risk. |
| 11 | Wisconsin | 56 | 2 | 3 | 3 | 3 | 3 | 4 | Focus on Energy geothermal $750 to $1,000; air-source amount not found. |
| 12 | Hawaii | 55 | 3 | 2 | 2 | 3 | 5 | 1 | Hawaii Energy HPWH up to $700, to Jun 30 2027. Water heaters only. |
| 13 | Virginia | 55 | 2 | 3 | 4 | 3 | 3 | 2 | Dominion up to $750 (dates unclear); state HEEHRA not launched. |
| 14 | North Carolina | 55 | 2 | 3 | 4 | 3 | 3 | 2 | Duke $350 to $2,500, conflicting pages. |
| 15 | Arizona | 53 | 2 | 3 | 4 | 3 | 3 | 1 | SRP $75 to $150 per ton (up to $1,125), HPWH $500; APS not read. |
| 16 | Delaware | 52 | 3 | 1 | 2 | 3 | 4 | 3 | Energize Delaware tiers (Sept 2025 sheet); Delmarva Energy Wise Rewards paused May 31 2026. |
| 17 | Florida | 49 | 1 | 4 | 5 | 2 | 2 | 1 | No amounts read. |
| 18 | Indiana | 44 | 1 | 2 | 3 | 3 | 3 | 3 | Nothing read. |
| 19 | Nevada | 40 | 1 | 2 | 3 | 3 | 3 | 1 | Nothing found. |
| 20 | New Mexico | 39 | 1 | 2 | 2 | 3 | 3 | 2 | Only a $165 dryer rebate found (PNM). |

Sources for excerpts (all search results, read date 2026-11-04, not opened as pages): energy.ri.gov and rienergy.com (RI), nhsaves.com (NH), homeenergysavings.pepco.com (MD), energytrust.org (OR), focusonenergy.com (WI), dominionenergy.com and energy.virginia.gov (VA), duke-energy.com (NC, OH, IN), georgiapower.com (GA), austinenergy.com, oncor.com, centerpointenergy.com (TX), srpnet.com (AZ), rockymountainpower.net (UT), energizedelaware.org and delmarva.com (DE), pnm.com (NM), hawaiienergy.com (HI). The HEEHRA launch lists found online came from low-quality sites that disagree; use the DOE Home Energy Rebates page and each state energy office instead.

### Recommended build order (top 10)

Rule for all: hand-written city prose, no doorway pages (skills `hpr-no-doorway-pages`, `hpr-new-city-checklist`), every amount from a facts file with `status`, `verified_on`, `source_url`. Effort is for hub, calculator, first 3 city pages and the post-steps.

| # | State | First 3 cities | Read first | Effort |
|---|---|---|---|---|
| 1 | Connecticut | Bridgeport, New Haven, Hartford | Energize CT (done), Eversource and United Illuminating pages, CT Green Bank Smart-E, heating-oil switch offers, state HEEHRA status | 5 days |
| 2 | Maine | Portland, Lewiston, Bangor | Efficiency Maine (done), Central Maine Power and Versant, Maine heat pump water heater offer, state HEEHRA, Census heating-fuel counts | 4 days |
| 3 | Oregon | Portland, Eugene, Salem | Energy Trust sheets, PGE, Pacific Power, EWEB, Oregon Rebate/HEEHRA status; rules by income | 6 days |
| 4 | Maryland | Baltimore, Rockville, Columbia | BGE EmPOWER page, Pepco, Delmarva, Maryland Energy Administration HEEHRA | 7 days (several utilities) |
| 5 | Rhode Island | Providence, Warwick, Cranston | RI Energy heat pump page, Office of Energy Resources Accelerator and HEAR | 4 days |
| 6 | New Hampshire | Manchester, Nashua, Concord | NHSaves 2026 form, Eversource, Liberty, Unitil, NH Electric Co-op; end-of-year deadline | 5 days |
| 7 | Utah | Salt Lake City, Provo, West Valley City | Wattsmart Homes page and Schedule 111, Dominion Energy Utah gas | 5 days |
| 8 | Georgia | Atlanta, Savannah, Augusta | Georgia Power HEIP preconditions, EMC co-ops, state HEEHRA | 5 days |
| 9 | Ohio | Columbus, Cleveland, Cincinnati | Duke, AEP Ohio, FirstEnergy current programs, Ohio Energy Office | 6 days |
| 10 | Texas | Austin, Houston, Dallas | Austin Energy, CenterPoint, Oncor 2027 reopening; heat pump water heater angle; build only cities with a real local program | 6 days |

Caveat: ranks 7 to 10 rest on amounts I could not confirm. If reading the official pages shows little money, swap in Wisconsin (colder, strong federal fit) or Virginia.

Notes:
- Connecticut, Maine, Rhode Island and New Hampshire are the New England neighbours of Massachusetts and Vermont, so installers, oil-to-heat-pump messaging and the NY/MA/VT patterns already in the repo transfer.
- Federal rebate fit: the rebate is most useful where homes burn oil, propane or use electric resistance heat, which favours CT, ME, NH, RI and WI. Re-score when Ottawa's rules are out (the federal program is a Canadian one in this repo; no US federal equivalent is in the facts files, so treat "fit" as heating-fuel fit only).
- Not in `data/regions.json`: `us/ct/heat-pump` and `us/me/heat-pump` exist as single pages. Adding the regions means running `sync_regions.py` and filling the lead-router city summaries.

## Part B. Canada gaps

Demand evidence is from Search Console, 2026-10-04 to 2026-10-31 (28 days), unless noted.

| # | Gap | Why it matters | Source to verify | Effort | Priority |
|---|---|---|---|---|---|
| 1 | **Pages not in `data/regions.json`:** Ontario Guelph, Kingston, Niagara Falls, Peterborough, Sault Ste. Marie, Thunder Bay, Timmins; Alberta Fort McMurray; Nova Scotia Cape Breton; BC Fraser Valley (region page) | The pages exist but PowerScore, the city picker, calculators, coverage checks and city email summaries do not list them (regions.json lists 18 ON, 5 AB, 1 NS cities). GSC: Peterborough heat pump pages 67 impressions, 34 for "peterborough heat pump installation". | `data/regions.json` against `ls ca/*`; `city-rebate-lookup.json` keys | 1 to 2 days (add, `sync_regions.py`, email summaries) | High |
| 2 | **Hydro One utility page** | Hydro One serves rural Ontario and Peterborough (fact on-33). Named as not built in CLAUDE.md. | hydroone.com rebate and EV pages (read in browser) | 1 day | High |
| 3 | **ENMAX and EPCOR utility pages** | Calgary and Edmonton, our biggest Alberta cities. Fact ab-9 (ENMAX/ATCO/EPCOR/FortisAlberta heat pump or solar) is status `check`. EPCOR has no EV incentive (ab-22). | enmax.com, epcor.com, atco.com | 2 days | High |
| 4 | **Heat pump gap in Manitoba, Saskatchewan and Quebec cities.** MB, SK and PE/NL city pages are hubs only (Winnipeg, Regina folder has only `index.html`). Only 2 cities per prairie province | These pages are thin compared with BC and ON, which have 6 to 9 category pages per city. Rebates are province-wide (Efficiency Manitoba, SaskEnergy/SaskPower, LogisVert), so build only a distinct angle per city (see CLAUDE.md "no doorway") | Efficiency Manitoba, saskpower.com, hydroquebec.com | 3 to 5 days | Medium |
| 5 | **More cities in covered provinces** (from memory, not StatCan-checked): Quebec (Gatineau, Laval, Sherbrooke, Longueuil, Trois-Rivières); Saskatchewan (Prince Albert, Moose Jaw); Manitoba (Steinbach, Thompson); New Brunswick (Saint John, Edmundston); Nova Scotia (Truro, Sydney as Cape Breton); BC (Courtenay-Comox, Campbell River, Cranbrook, Mission); Alberta (Medicine Hat, Grande Prairie, Airdrie); Ontario (St. Catharines, Brantford, Belleville, Cornwall, Chatham-Kent, Pickering, Milton) | Rebates mostly are province-wide, so city pages only pay if the city has a distinct fact (utility, municipal loan, Census angle). Check Search Console per city first: "energy rebates penticton bc" got 270 impressions at position 58, showing small cities have demand | StatCan 2021 Census table 98-10-0233-01 (WDS API, or the Census Profile in Chrome if the API is down), GSC per city | 1 day per city | Medium |
| 6 | **Saint John Energy and NB Power pages** | Saint John is the biggest NB city and has its own utility. Facts for it are unverified (CLAUDE.md). | saintjohnenergy.com, nbpower.com | 2 days | Medium |
| 7 | **French coverage.** Built: QC hub, Montréal, Quebec City, QC heat pump, NB hub, Moncton. Missing: Fredericton French, NB and QC category pages, French calculator, French federal pillar page and alert box, Laval and Gatineau | Quebec is French-first; `ca/qc/` English pages cannot capture French queries. No federal alert box on French pages yet. | `data/fr/*.json`, Hydro-Québec LogisVert (French only) | 5 days for the missing cities and the federal page | Medium |
| 8 | **Nunavut** | Not built. Only 2021 to 2022 sources found for its renewable energy rebate; no official 2026 page (CLAUDE.md). Tiny search market. | Government of Nunavut, Qulliq Energy Corporation | 2 days if an official 2026 page exists | Low |
| 9 | **Federal program pages** | Pillar, do-I-qualify tool, partner kit, alert box and six articles exist. Gaps: all stay "not confirmed" until Ottawa publishes the income line, home types and start date; French pillar missing. The alert list is the top metric until launch. | Official Government of Canada page (check weekly) | 1 day when rules drop | High (time-bound) |
| 10 | **Utility pages for Prairie, Quebec and Atlantic utilities:** Efficiency Manitoba / Manitoba Hydro, SaskPower/SaskEnergy, Hydro-Québec (LogisVert), NB Power, Maritime Electric, Newfoundland Power, plus Ontario LDCs (Toronto Hydro, Alectra, Hydro Ottawa) | Not in `/programs/` (existing: BC Hydro, FortisBC, CleanBC, Enbridge, Save on Energy, Efficiency NS, NL oil-to-electric, Alberta energy rebates). Each is a "does X have a rebate" query. | each utility's own pages | 1 to 2 days each | Medium |
| 11 | **Open caveats in facts** | `mb-8` instant rebates (check); `pe-6` biomass and `pe-7` Maritime Electric rebate (check, page did not load); `ns-13` Eco-Shift (paused); Alberta `ab-0`, `ab-2`, `ab-4`, `ab-10`, `ab-11` (paused or waitlist, so pages must not show them as open); Halifax Solar City and Efficiency NS guide PDF amounts (sites block readers); Efficiency Vermont/Mass Save style bot checks. Also unverified and left off pages: Rénoclimat "$3,750", Saskatchewan retrofit rebate, Yukon HRV/appliance/solar hot water amounts, NB oil "up to $15,000" conditions | Wrong amounts are our biggest trust risk | Read in browser pane or Chrome, update facts, rerun builders | 3 days total | High |
| 12 | **Categories merged or not built per city** | BC/ON/NS have 6 to 9 category pages per big city. Alberta cities have heat pump, EV, insulation, thermostats only (Calgary). MB, SK, QC, NB, PE, NL, YT, NT have hubs only. HRV, EV and appliance pages are single province pages by design (Ontario, BC, Alberta, NS). No gap to fix unless Search Console shows demand | GSC per category; "free thermostat ottawa" 324 impressions (position 48) shows ON thermostat pages are weak | n/a | Low |
| 13 | **Demand already visible but not won** | NS heating rebate status (about 5,500 impressions, position about 6.6, CTR 0.6%); "heat pump installation hamilton" (about 1,330 impressions, position 54, 0 clicks); smart thermostat rebate cluster (1,132 impressions, position 24); BC Hydro air fryer rebate cluster. Fixing these beats new regions on short-term clicks | GSC clusters (this report) | 1 to 3 days | High |

## Top 3 next actions

1. **Build Connecticut and Maine** (about 9 days together), starting from the facts already read on 2026-10-10. Use the same method as NL/PE/NB, add both to `data/regions.json`, then run `sync_regions.py`.
2. **Add the 10 existing-but-unlisted Canadian pages to `data/regions.json`** (7 Ontario cities, Fort McMurray, Cape Breton, Fraser Valley) and write their lead-router email summaries (1 to 2 days). This is the cheapest fix and makes real pages count in PowerScore and the picker.
3. **Connect a keyword provider (DataForSEO, Semrush or Ahrefs) and read the Oregon, Maryland, Rhode Island and New Hampshire program pages in the browser**, then rescore ranks 3 to 10 before spending the build days.
