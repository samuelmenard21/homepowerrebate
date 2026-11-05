# Heat pump: a plan for every city (2026-11-04)

Built from `scripts/build_city_strategy.py`. The full table, one row per city with its wave, tier, list size, open rebate, search demand,
reachable installers and plays, is `data/reports/city-strategy/city-strategy-2026-11-04.csv` (summary in the `.md` beside it). Rerun the script
after any data change; edit the `WAVE1` and `WAVE2_EXTRA` lists in it to move a city.

## What the data can and cannot tell us
- **Search demand is known for only 7 cities** (Hamilton 543 impressions in 90 days, Kitchener 267, Chula Vista 152, Cambridge ON 95, Peterborough 67, St. Albert 35, plus Greater Sudbury's suburb queries). It comes from the top local queries only. Everything else is a bet.
- **The open rebate figure is the highest "up to" amount** (about $12,000 in Ontario, $13,000 in BC). It is the same in most cities, so it separates provinces, not cities. Alberta shows none, which is a real gap in rebates, not in searches.
- **Reachability** counts how many of a city's top 5 companies have a public email. It decides how fast we can build relationships.
- One result is hand-checked: the Burlington, ON results page for "heat pump installers near me" (ads, AI Overview, map pack, then installers' own city pages).

## The waves
- **Wave 1 (10 cities): where we can already see demand.** Hamilton, Kitchener, Cambridge ON, Peterborough, Burlington ON, Greater Sudbury, Chula Vista, St. Albert, Newton MA, Cambridge MA. The two Massachusetts cities are here because "Mass Save approved contractor <city>" queries appear and we now list Mass Save's network by county.
- **Wave 2 (30 cities): large lists, reachable installers, a real rebate.** 24 chosen by rule (mostly BC for the registered-contractor angle, the GTA, New York) plus six big metros added by judgement: Toronto, Vancouver BC, Boston, Calgary, Edmonton, Denver.
- **Wave 3 (69):** full list and a rebate, no demand seen yet. Template and awards only.
- **Wave 4 (31):** thin list or no open rebate. Template only; revisit when data changes.

## What we do in a wave-1 city
1. **Page** (done everywhere): search-match title and answer box, communities, nearby cities, "People also ask" answers, rebate in the description.
2. **People:** a personal website and Google review note to the top 3 companies (10 notes are written for the #1 companies in 25 cities; wave 1 needs the other two in each city). Nothing is sent without Sam's approval of the list and wording. No link or badge request in the first note.
3. **Proof:** a local-news pitch from the city ratings page with that city's own numbers.
4. **Awards:** winner notice in December (see `docs/seo/awards-2026-plan.md`).
5. **Watch:** the Monday check reports impressions, position and click-through for the city page, plus `installer_click` and `quote_start` events.

## Cadence
- **Week of Nov 9:** wave-1 notes drafted and approved; reporter list approved.
- **Nov 16 to 30:** send wave-1 notes at about 25 a week, one to one; read replies; refresh Google ratings (the files are from September).
- **Dec 1:** awards kickoff run; first read of wave-1 pages against the baseline (gate below).
- **Dec 8:** awards launch. Wave 2 notes start.
- **January:** waves 3 and 4 get the template and awards only; second-wave categories (water heaters, EV chargers).

## Gate (Dec 1)
If wave-1 city pages gained 2 or more positions or doubled their click-through compared with the solar and battery pages that were not changed, run wave 2 at full speed. If not, stop and look at the actual results pages for 3 of the 10 cities before doing more.

## Advisors and auditors (next build)
Their lists overlap across a province or state, so only 3 advisor pages and 7 auditor pages are indexable. Run them by province or state, not city: one award per province or state, referrer outreach (calculator embed and printable sheet), and the same weekly check. Per city we only track whether an advisor page exists (column `advisor_page`).
