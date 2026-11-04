# HomePowerRebate Top-Rated Installer Awards 2026 (plan, written 2026-11-04)

Why: installers do not answer link or badge requests, but they do share an honest award. It gives us a real reason to write to every company, earns links without asking for them, and gives local news a story per city.

## Rules (publish them on the awards page; keep them simple and never pay-to-play)
- **Three winners per city and category, equal.** The three companies with the highest score on the city ranking each get the "Award Winner 2026" seal. They are listed alphabetically on the awards page, because in 42% of heat pump cities the top two scores are within 0.02 of each other (checked 2026-11-04) and naming one "best" would be fragile. Nobody pays, applies or is asked to buy anything.
- **Score:** the same published score the city rankings use (Google rating weighted by review count). Ties go to the company with more reviews.
- **Eligibility:** the city has at least 8 ranked companies; each winner has at least 50 Google reviews and a 4.5 rating or better; its website or phone still works; it is not on `data/installer-blocklist.json` or in `outreach/suppress.txt`. If a company fails a test, the next one up takes its place.
- **Where:** heat pumps (about 125 cities), home batteries (43) and solar (28) in December; insulation (9 cities) and the other categories later. Cities under 8 companies get no city award.
- **Extra single awards from counts, not scores:** most-reviewed company in each province or state.
- Data date shown on every page. Refresh the Google ratings before announcing: the current files are from October 9, 2026, and an award built on stale numbers invites a dispute.
- A company can ask to be removed, and we do it the same day.

## Logo and assets (done 2026-11-04)
`python3 scripts/build_awards_logo.py` writes `assets/awards/` (emblem, lockup, a Hamilton winner seal). City winner seals use `city_seal(year, "CITY · SERVICE")`. Still to make in December: share cards (1200 x 630) per city from `build_og_cards.py`, a press-kit page, PNG exports from a browser.

## Timeline (December 2026)
- Dec 1: kickoff (scheduled task): refresh ratings, rebuild rankings, pick winners with the rules above, review the list by hand, write `data/awards/2026.json`.
- Dec 3 to 5: private notice to each winner, written by hand, one to one, with their seal, their city page, the rules, and an embargo until the announcement. No ask. Only for companies we have an email for; others by contact form.
- Dec 8: public launch. `/installers/awards/2026/` (winners by country, region, city), seals on every winning city page, a press release, local-news pitches for the top 10 cities (from `docs/seo/heat-pump-link-pitches.md`, approved by Sam before sending), social posts, a short video of the logo and winners.
- Dec 9 to 20: congratulate each winner who replies; offer the seal as an image and a snippet that links to their page. The link request happens only after they reply, never in the first note.
- Early January: recap report (replies, seals displayed, links earned, press pickups, search clicks) for the next year.

## Federal rebate tie-in (idea 1, from 2026-11-04)
Do not list anyone as "ready for the federal rebate" until Ottawa publishes who can apply and how. Until then: ask winners and repliers one question in their first reply, "will you help customers apply for the national rebate when it opens?", record yes or no in `data/installer-federal-interest.json`, and at launch publish the list from the yeses plus the official rules. The homeowner side already exists (alert list, do-I-qualify tool, partner kit).

## Winners picked (2026-11-04, draft)
`python3 scripts/build_awards_2026.py` picks the winners with the rules above and writes `data/awards/2026.json` plus draft pages under `/installers/awards/2026/` (hub, heat-pump, battery, solar). `LIVE = False` keeps the pages noindex and nofollow, and they are NOT committed: generated pages stay out of the repo until launch day so the winner list does not go public early. At launch: refresh ratings, rerun the script with `LIVE = True`, run the restamp, post-steps and sitemap, then merge. Result on the October 9 data: heat pumps 372 winners in 124 cities, home batteries 123 in 41, solar 81 in 27 (576 in all); no award in 4 city lists with too few eligible companies. Badges: `assets/awards/shield-<category>-2026.svg` and `shield(category, year, city)` in `scripts/build_awards_logo.py` for city seals.
