---
name: hpr-category-page-localization
description: Inject real, verified, city-distinguishing data into HomePowerRebate's city × category leaf pages (heat-pump, solar, battery, water-heater, insulation, windows, ev-charger, smart-thermostats, hrv, appliances) so they clear thin/near-duplicate content risk. Use whenever a GSC/SEO audit flags a category-page cluster as declining, thin, or near-duplicate, before building a new category page, or when running the sitewide rollout of this playbook.
---

# Category Page Localization

## Why this exists

A 2026-09-09 Search Console investigation found impressions collapsing on
Ontario city × category leaf pages (e.g. `/ca/on/kitchener/heat-pump/`,
down 81%, sitting at avg. position ~87-90). Diffing two sibling pages after
stripping the city name found 96% identical text — only the city name and
three installer names/numbers differed. The site's existing doorway-page
checker (`scripts/check_duplicate_content.py`) reported this cluster
"clean" because it only catches byte-*identical* pages; this is thinner
than that but not caught by the existing tool. See
[[hpr-no-doorway-pages]] for the byte-identical case this doesn't cover.

This is not a hypothetical risk — it's the same "Templatized Data Void"
pattern that's already cost this site three prior doorway-page incidents
(Aug 2026 smart-thermostats, Aug 2026 CA windows-doors, Sep 2026 236-page
audit). The fix here is upstream of that: give agents real per-city data
to inject so the page never becomes a doorway page in the first place,
rather than relying only on catching it after the fact.

## The zero-research baseline fix — apply to every category, every region

`city-rebate-lookup.json` already has a verified `utility` field per city
(the local utility/LDC — e.g. "Kitchener-Wilmot Hydro", "Toronto Hydro",
"Alectra Utilities") from when each city was onboarded via
[[ontario-city-research]] or the equivalent research pass for other
regions. **This is real, already-verified, city-specific data that is
currently not mentioned on any category subpage in any region.** Every
region except BC (single shared utility, so this fix doesn't add anything
there) has multiple distinct utilities — ON alone has 18 across 27 cities.

Before doing any new research, for every category page:

1. Look up the city's `utility` field in `city-rebate-lookup.json`.
2. Name it explicitly and tie it into the page's actual content — not a
   throwaway mention, but something the reader would use: which utility
   bills them, which utility's programs stack with the provincial rebate,
   who to call if something in the rebate process depends on the utility
   (net metering, panel upgrade coordination, application status).
3. This alone moves a page off "100% identical except city name and
   installer list" — it's a real fact that varies by city and it's
   already sitting in the codebase unused.

This step requires no web research and can be scripted across every
category page in every region immediately.

## Category-specific real-data layer (do this after the baseline fix)

The baseline fix (utility name) applies uniformly. Beyond that, each
category has a different kind of real, verifiable, genuinely-varying data
point worth researching and adding — do not reuse one category's data
point on another category's pages just because it's already researched.

| Category | What to research and verify | Primary source |
|---|---|---|
| `heat-pump`, `hrv`, `insulation`, `windows`/`windows-doors` | Real winter design temperature / heating degree days for the city — genuinely varies city to city and directly supports the "will this work in my climate" question these pages already try to answer with generic text | Environment Canada climate normals (climate.weather.gc.ca), cross-checked against a second source (ASHRAE climatic data, a regional HVAC design-temp reference) — do NOT treat a single WebFetch of a dynamic government page as sufficient, per [[ontario-city-research]] Step 3's two-source rule |
| `solar`, `battery` | Real solar irradiance / peak sun hours for the city or its climate region | NRCan PVWatts / solar resource maps |
| `ev-charger` | Whether the city's utility runs an EV time-of-use rate or home-charger rebate — if none exists, say so explicitly rather than implying one might | The utility's own program pages, verified live per [[ontario-city-research]] Step 3 |
| `smart-thermostats` | Whether the city's utility runs a demand-response or free/discounted smart thermostat program (common pattern: peaksaver PLUS and similar across many Ontario LDCs) — verify per utility, don't assume it exists because a neighboring city's utility has one | The utility's own program pages, verified live |
| `water-heater`, `appliances`, `battery` (rebate-stacking angle) | Whether the city's utility offers any rebate stacking on top of the provincial program beyond what's already in `city-rebate-lookup.json`'s `categories` field for that city | The utility's own program pages |

**If genuine research turns up nothing city-specific for a category**,
that is a valid finding — say so explicitly on the page (matches the
existing pattern already used for cities with no municipal loan program)
rather than inventing a plausible-sounding local detail. If a city
consistently can't clear a reasonable bar of real distinguishing content
across its categories even after this research pass, consider rolling it
into its parent regional hub instead of shipping thin standalone leaf
pages — this was the fallback the original content-strategy note
recommended, and it's the honest move when the data genuinely isn't there.

## What NOT to change

The installer directory block on each category page is already real,
city-specific, and pulled from live-scraped Google Places data — leave it
as-is. It's the one part of the current template that already passes the
"is this genuinely about this city" test.

## Verification

After localizing a batch of pages in one category/region cluster:

```bash
python3 scripts/check_duplicate_content.py --category <cat> --near-duplicate-threshold 0.90
```

Confirm the pages you just edited no longer appear in the near-duplicate
output against their siblings. A pair that still matches above threshold
after a real localization pass means either the added content wasn't
substantive enough, or (check before assuming a bug) the match is on a
block that's legitimately identical real data (e.g. the provincial rebate
table) — in which case that's expected and not a problem; the tool doesn't
yet exclude shared-data blocks on category subpages the way it does on hub
pages (see the caveat in that script's `--near-duplicate-threshold` help
text), so use judgment on what's actually flagged, not just the score.

## Rollout sequencing

Piloted first on the exact cluster the GSC investigation flagged:
Kitchener, Vaughan, Toronto, Ottawa × heat-pump (2026-09-09). Once that
pilot is validated, this playbook is meant to be applied sitewide — every
category, every city, every region with more than one distinct utility.
That is a large batch content operation (dozens of cities × up to 10
categories × several regions); treat it as a fan-out job scoped by
category or region cluster, the same way a full-site audit-and-fix run is
scoped in the `seo` skill, rather than one continuous pass.
