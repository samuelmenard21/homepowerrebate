# SEO Change Ledger

One line per real change. The weekly GSC analysis reads this first.

Rules:
- **Type** is `seo` (title, meta, structure, links) or `fact` (a factual correction such as a rate or deadline change).
- Judge a change on its check date (change date + 90 days). Until then the weekly report lists it as "not due" for judging.
- Editing early is allowed when the change is clearly better: a factual fix, or a page that does not yet answer its query plainly (grade 6 language, answer first). Log each edit as a new row.
- Leave a page alone for longer when we are confident it already answers its query clearly in plain language. Do not edit it just to edit it.
- Position and impressions are the 7-day site-wide aggregates from the weekly report, not exact page+query filters. Re-pull with an exact page and exact query filter on the check date.
- Dates come from git history in this repo.

| Change date | Page | Target query | Pos / impr at change | Type | Change | Check on |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-10-23 | /ca/bc/penticton/ | energy rebates penticton bc | 64.3 / 100 (week of 10-17) | seo | Hub retitled "Penticton Energy Rebates 2026: FortisBC and the City Loan" (commit 84fb282); query still landed on /ca/bc/kelowna/ | 2027-01-21 |
| 2026-10-23 | /ca/on/ottawa/smart-thermostats/ | free thermostat ottawa | 47.6 / 120 (week of 10-17) | seo | Retitled "Free Thermostat in Ottawa 2026: Who Gets One + $125 Rebate" (commit 84fb282); earlier retitle and expansion on 2026-10-06 (b8588c9) | 2027-01-21 |
| 2026-10-26 | /blog/nova-scotia-heating-rebate-2026-27-payment-dates-status/ | ns heating rebate check status | 5.4 / 602, 9 clicks (week of 10-17) | seo | Answer-first titles, metas and top answers across the NS status cluster, plus Ontario and BC thermostat pages | 2027-01-24 |
| 2026-10-27 | /blog/nova-scotia-heating-rebate-2026-27-payment-dates-status/ and /programs/nova-scotia-heating-assistance-rebate-harp/ | heating rebate status, harp nova scotia, check harp status | 11.0 / 184; 8.5 / 115 (week of 10-17) | seo | Top-20 pass: one owner page per query group, answer first | 2027-01-25 |
| 2026-10-26 | /blog/ontario-smart-thermostats-100-rebate-compared/ | smart thermostat rebate, ecobee rebate | 27.3 / 45; 10.0 / 42 (week of 10-17) | seo | Part of the 10-26 answer-first thermostat commit | 2027-01-24 |

| 2026-10-27 | /ca/qc/heat-pump/ and /ca/qc/heat-pump/fr/ | logivert, programme logivert, subvention logivert | ~60-90 / 418 combined (week of 10-17) | seo | Added the common misspelling "Logivert" in the intro and a new first FAQ ("Is it Logivert or LogisVert?"), English and French | 2027-01-25 |
| 2026-10-27 | /furnace-rebates/alberta/ | air conditioner rebate alberta | 30.1 / 77 (week of 10-17, landed on /ca/ab/) | seo | Retitled "Alberta Air Conditioner & Furnace Rebates 2026" (another session landed the same retitle; kept theirs); I added links from /ca/ab/, /ca/ab/heat-pump/, Calgary, Edmonton and the central air guide | 2027-01-25 |

## Open items for the next review (2026-11-02)
- Read the 11-02 week as a baseline for the rows above. Recommend edits to them only if a page clearly fails to answer its query.
- Pages in the 10-17 to 10-23 data that are NOT in this ledger and are fair game: Logivert (Quebec) pages, /us/pa/, /us/co/, Hamilton and Kitchener installer pages, /furnace-rebates/bc/, the Bosch vs Mitsubishi and Mysa comparison posts, /blog/bc-hydro-product-rebates-appliances/.
