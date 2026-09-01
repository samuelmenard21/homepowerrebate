---
name: hpr-new-city-checklist
description: Checklist to run whenever a new city, state, or province goes live on HomePowerRebate (a city page is published, or a city is added to installers/index.html's *_CITIES arrays). Catches the specific gap where a city gets installer profiles and a hub page but no rebate data for the lead-router's homeowner emails, so those emails silently show "not specified" instead of real numbers. Use alongside the region-specific research skills (ontario-city-research, bc-rebate-verification) — this covers the email-data step those don't.
---

# HPR New-City Checklist

## Why this exists

On 2026-09-01, an audit found 35 of 110 cities in the installer directory (all of PA, CO, VT; most non-NYC New York; 7 Ontario cities) had installer profiles and directory listings but zero rebate data in the lead-router's lookup — because that lookup was never updated when those cities were added. Homeowner confirmation/recap emails for those cities either showed "not specified" or, worse, were mislabeled with another region's program name (a Toronto lead's email said "Estimated CleanBC rebates" before that bug was caught). This checklist exists so the gap doesn't reopen with the next city added.

## The two systems that must stay in sync

1. **Installer directory / city pages** — `installers/index.html`'s `*_CITIES` arrays, `ca/{province}/{city}/` or `us/{state}/{city}/` page directories, `installers/profiles/{city}/`.
2. **Lead-router email data** — `scripts/all-rebates-consolidated.csv` → generates `city-rebate-lookup.json`, consumed by `lead-router.js`'s `cityRebateLookup()`. This is what makes the "Every rebate available in {city}" breakdown and the estimate fallback show real numbers instead of "not specified" in homeowner emails.

These are separate files maintained by hand — nothing currently enforces they stay in sync automatically.

## Checklist for every new city

- [ ] Research real, currently-live rebate figures for the city's region (heat pump, solar, battery, water heater, insulation, windows, EV charger, thermostat) — follow the same verification standard as `ontario-city-research`/`bc-rebate-verification` (real official sources, cross-validate surprising figures against a second source, never fabricate a number). State/provincial programs are usually shared across all cities in that state/province — check whether an existing row for that region can be reused rather than re-researching from scratch.
- [ ] Add a row to `scripts/all-rebates-consolidated.csv` matching the existing column schema exactly (region as lowercase code, city display name, dollar ranges as free text like `"$4,000-$16,000"`).
- [ ] Regenerate `city-rebate-lookup.json` from the CSV (see the generation snippet in `lead-router.js`'s comment above `import CITY_REBATE_LOOKUP`).
- [ ] If this is a **new state/province** (not just a new city in an existing one), add a `PROVINCE_CONTEXT` entry in `lead-router.js` (program name + blog links) — otherwise emails for that region silently fall back to BC/CleanBC branding.
- [ ] Verify: `node --input-type=module --check < lead-router.js` for syntax, then check `city-rebate-lookup.json` has the new city under the key `{normalized-region}|{normalized-city}`.
- [ ] After deploying, send one real test submission for the new city and confirm the resulting email shows real numbers and correct program name — not "not specified" or another region's name.
