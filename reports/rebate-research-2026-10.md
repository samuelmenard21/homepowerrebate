# Rebate research pass, run 2026-09-29 (for the October digest)

Scope: (1) all 23 tracker sources re-fetched; (2) BC compared against xolar.ca/rebates (page dated Sept 22, 2026); (3) spot checks of Ontario, Alberta, California, Nova Scotia.

## Tracker sources
All 23 source URLs still load (mass.gov returns 403 to bots only). No entry needed a status change.
Re-confirmed on the official page today: Calgary CEIP "closed until winter 2026/2027"; TECH Clean California single-family reserved statewide since Nov 14, 2025; California HEEHRA single-family fully reserved since Feb 24, 2026 ($8,000 / $4,000 amounts unchanged; multifamily still open, up to $14,000 per unit; Phase II has no launch date); Ontario Home Renovation Savings amounts match our pages.

## Possible gaps (unverified leads)
- None for BC. xolar's BC list: solar up to $5,000, battery up to $1,500 ($5,000 with Peak Saver), PST exemption, Nanaimo Renewable Energy Systems Rebate expired Jan 1, 2026. All are already on our site or are correctly absent.
- xolar note: since April 1, 2026 battery-only systems without Peak Saver are not eligible. Our verified facts (data/verified-facts/bc-pages.json) already say battery-only is allowed only with Peak Saver.
- Nanaimo Renewable Energy Systems Rebate (expired Jan 1, 2026): could be added to the tracker as "ended", but only after checking the City of Nanaimo's own page.
- California multifamily HEEHRA (up to $14,000 per unit) is still open; our tracker only lists the paused single-family program.

## Possible drift
- None found.

## Could not check (page content did not load)
- Efficiency Nova Scotia program pages (Moderate Income Rebate, Programs index): fetch returned no page text (likely script-rendered). Needs a manual look.
- Nova Scotia HARP 2026-27 opening date and amount: the province's page returned 404; still "confirm with the Province" in the tracker.
- BC Hydro home-renovation page URL used in the tracker returned 404 to the fetch tool (200 to curl); heat pump bonus end date (Oct 31, 2026) not re-read from the official page this pass.
- Lethbridge / St. Albert CEIP status: the overview page shows no status; needs each city's page.

## Low-confidence
- None.
