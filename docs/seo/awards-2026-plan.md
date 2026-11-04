# HomePowerRebate Top-Rated Installer Awards 2026 (plan, written 2026-11-04)

Why: installers do not answer link or badge requests, but they do share an honest award. It gives us a real reason to write to every company, earns links without asking for them, and gives local news a story per city.

## Rules (publish them on the awards page; keep them simple and never pay-to-play)
- Winner = the company ranked first on our city ranking for that service (rating weighted by review count). Finalists = the next two. Nobody pays, applies or is asked to buy anything.
- Only cities with at least 8 ranked companies; winners need at least 50 Google reviews and a 4.5 rating or better. Companies on `data/installer-blocklist.json` or `outreach/suppress.txt` are never named or contacted.
- Data date shown on every page. Refresh the Google ratings before announcing: the current files are from September 2026, and an award built on stale numbers invites a dispute.
- Extra awards from the same data, no new claims: most-reviewed company in each province or state, largest review count in each country.
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
