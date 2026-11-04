# Winning "heat pump installation near me" (written 2026-11-03)

## What Search Console shows (90 days to 2026-10-30, property `https://homepowerrebate.com/`)

Use the URL-prefix property in SEO tools; `sc-domain:` is denied for this account.

- 198 local-intent queries, 2,788 impressions, **1 click**. Almost every impression sits at position 30 to 90.
- The demand has one shape: `heat pump installation <place>` and `heat pump installers <place>`. Places are often suburbs we never name: Waterdown, Binbrook, Ancaster, Stoney Creek, Flamborough, Kilbride, Skead. The Hamilton ranking page collects about 400 impressions from them and mentions none of those names.
- "heat pump installation near me" (104 impressions) and "heat pump installers near me" (61) land on random city pages (Chula Vista, Kitchener, St. Albert). No page is built for a visitor in any city. There is no `/installers/heat-pump/` hub.
- Our title is "Best Heat Pump Installers in Hamilton, ON (2026)". Searchers type "installation". The word is not in the title or H1.
- Two pages compete for the same query: rebate hubs (`/us/ma/springfield/`) beat the installer page for "heat pump installation rebates springfield ma".
- "heat pump installers" sits at position 8.7 with 34 impressions and 0 clicks. Page one without clicks is a snippet problem.
- Length is not the problem (Vancouver 5,900 words, Hamilton 3,800). Match to the query and authority are.
- Profile pages are noindex but still appear in the index (Burlington, Oakville, Nanaimo, Sudbury profiles). They are stale and will fall out.

## Honest target

Baseline is near zero, so "10x clicks" is cheap and not the goal. Goals:

1. Top 5 for `heat pump installers <city>` and `heat pump installation <city>` in the 25 biggest heat pump cities by 2027-02-01.
2. 100 clicks a month from the 140 heat pump ranking pages by 2027-02-01 (baseline about 0.3 a month).
3. A page that wins the unlocated "near me" query.

## The plan, in order

### Phase 1: fix match and snippet (week 1, 25 highest-impression pages first)

1. **Title and H1 in the searcher's words.** "Heat Pump Installation in Hamilton: 12 Top-Rated Installers" (under 60 characters, no year suffix drift). Keep "Top-Rated" and the review count in the description. Change one generator field in `build_installer_rankings.py`; do not touch pages by hand.
2. **Areas-served section on every city page, from real data.** List the suburbs and neighbouring towns that appear in the installers' own Google addresses and service areas, and name what is distinct (Hamilton: Ancaster, Dundas, Waterdown, Stoney Creek, Binbrook, Glanbrook). Never invent a suburb or write "also serves" without a source. This is one section inside the city page, not new suburb pages (doorway risk, see `hpr-no-doorway-pages`).
3. **Answer box under the H1** that matches the query: how many installers, the top-rated name and review count, typical install cost range from a source, and whether rebates require a registered contractor. This is what lifts CTR at position 8 and feeds AI answers.
4. **Cannibalisation rule.** For installer and installation queries the ranking page is canonical. Rebate hubs get a prominent "Find heat pump installers in <city>" module with that anchor text. Check with the `cannibalisation` report after two weeks.

### Phase 2: win "near me" (weeks 2 to 3)

5. **Build `/installers/heat-pump/`** (hub, indexable): postal code or ZIP box that routes to the right city page, province and state picker, the 140 city links grouped by region, and the "how we rank" explanation. Title: "Heat Pump Installers Near Me: Top-Rated in Your City". It is the only page that should target the unlocated head term.
6. **Browser location button** on the hub and on city pages: asks permission, maps the visitor to the nearest city we cover (computed in the browser from a city centre list we own). Do not store Google Places coordinates; Places terms limit caching them. Installer ordering stays review-based, never distance-based, so money and geography never change rankings.
7. **Cities with no ranking page** but search demand (the suburb list from phase 1) get a line on the nearest city page, not their own page.

### Phase 3: be the page worth ranking (weeks 3 to 6)

8. Add what lead-gen competitors do not have, all sourced: the **registered-contractor flag** (done for BC; extend to NY, ON and MA only where an official list exists), the rebate this contractor type must hold, an "ask for these 6 things in a heat pump quote" checklist, a cold-climate model note tied to the BC Hydro qualified list, and permit or inspection notes per region only where an official page says it.
9. **Reviews data without markup.** Keep ratings visible with Google attribution and no AggregateRating markup (see CLAUDE.md, Google Places policy).
10. **Internal links.** Every heat pump rebate page, calculator result and blog post that names a city links to that city's installer page with "heat pump installation in <city>". Add the hub to the footer and the homepage.

### Phase 4: authority (weeks 2 to 8, runs alongside)

11. **Badge links.** Installers on a heat pump ranking already get the badge; make badge outreach in the top 25 cities the priority of `installer-outreach-daily`, and point the badge at the city's heat pump page.
12. **Link bait that is ours:** one data post, "Which cities have the best-reviewed heat pump installers", from the ranking data (review counts and ratings are ours to rank, not to republish). Pitch it to local news in the top 10 cities.
13. **Federal rebate tie-in.** The national rebate launch (early 2027) will spike "heat pump" searches; the hub and city pages should already rank and carry the alert box when it does.

## Measurement (use what already exists)

- Weekly: `local-search-demand` and `quick-wins` reports (URL-prefix property), plus `rank-tracking` on 40 saved keywords (`heat pump installation <city>`, `heat pump installers <city>`, `heat pump installers near me`) across 10 cities. Extend the `ns-title-ctr-check` pattern: change titles on 10 pages first, leave 10 matched pages alone as controls, compare CTR after 3 weeks.
- Success gates: phase 1 pages gain 2 or more positions or 2x CTR vs controls by 2026-12-01; if not, stop and diagnose before phase 2.

## Then other categories

Same template, same order, once heat pump phase 1 shows lift (check 2026-12-01): solar (Denver pages sit at 60 to 88 with about 250 impressions), battery, insulation, energy auditor/advisor, water heater. Query pattern is identical: `<service> installation/installers <city>`. Do the title and areas-served change in the shared ranking generator, the category hubs (`/installers/solar/` etc.) as copies of the heat pump hub.

## Risks

- Titles that over-promise ("near me") on city pages: keep "near me" only on the hub.
- Areas-served lists drifting into doorway text: each must name a source and differ per city; run `check_duplicate_content.py` before shipping.
- Changing the shared generator touches 424 ranking pages: run `check_generator_sync.py` and review the diff list.

## What the live results show (Burlington, ON, "heat pump installers near me", seen 2026-11-03 by the site owner)

Order on the page: 4 ads, an AI Overview ("Top-rated heat pump installers in and around Burlington include..." naming HAMCO, 4.8 stars, 797 reviews), the map pack (3 businesses plus a sponsored one), then organic results, then "People also ask", more ads, "People also search for".
- First organic results are the installers' own city pages (HAMCO "Burlington Heat Pump Installation Pros", Cozy World "Heat Pump Installation in Burlington, ON"). No directory or comparison site is on the first screen.
- Winning snippets lead with a dollar amount ("up to $7,500") or "free quote".
- People also ask: average cost of a heat pump installation; most reliable heat pump in Canada; labour cost; cost for a 1,500 sq ft house.
- People also search for: "heat pump installers near Oakville, ON", "residential heat pump installers near me", "best heat pump installers near me".

What we did with it (2026-11-03): FAQ answers worded like those four questions on every heat pump page (answers use only the sourced price range and say plainly when no verified figure exists); the open rebate amount in the meta description; nearby-city links already answer "near Oakville". Still to do: get cited in the AI Overview (it quotes review counts, which our ranked lists carry), and test whether a "Best ..." title lifts clicks against the current one.
