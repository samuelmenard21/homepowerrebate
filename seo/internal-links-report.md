# Internal link report (2026-11-22)

Command: `python3 scripts/count_inbound_links.py`. Counts distinct pages that link to each indexable page from the body, excluding the shared nav and footer and noindex pages. Raw counts per page are in `seo/internal-link-graph.json`.

Indexable pages: 936. Fewer than 3 inbound links: 36. Zero: 4.

## Money pages
| Page | Inbound |
|---|---|
| /get-quotes/ | 1,100 |
| /programs/national-heat-pump-rebate/ | 501 |
| /calculator/widget/ | 445 |
| /ca/on/ | 346 |
| /powerscore/ | 276 |
| /blog/ | 276 |
| /ca/bc/ | 200 |
| /us/ma/ | 174 |
| /installers/heat-pump/ | 63 |
| /programs/national-heat-pump-rebate/do-i-qualify/ | 4 |

## Zero inbound
`/installers/installer-carousel`, `/installers/solar-carousel`, `/installers/unified-carousel` (old template files, not real pages) and `/terms` (linked only from the footer, which this count excludes).

## One inbound
`/ca/ab/red-deer/smart-thermostats/`, `/ca/bc/fraser-valley/`, `/ca/nb/moncton/fr/`, `/ca/qc/montreal/fr/`, `/ca/qc/quebec-city/fr/`, `/programs/utility-comparison/`, `/questions/kamloops-solar/`, `/rebate-tracker/2026-09/`, `/solar-battery`

## Two inbound
Mostly older blog posts, `/about`, `/eguana`, `/ca/nb/fr/`, `/data-release/2026-10/` and a few question pages. The full list is the output of the command above.

## Next step
Fix through `scripts/link_discovered.py` and `scripts/add_federal_links.py`, never by editing pages. Anchors 3 to 7 words, 5 or more distinct anchors per target, no exact anchor over 3 times.
