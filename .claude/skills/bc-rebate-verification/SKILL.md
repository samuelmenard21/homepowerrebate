---
name: bc-rebate-verification
description: Re-verify BC HomePowerRebate content (all 18 cities) against live official sources — BC Hydro, FortisBC, CleanBC/BetterHomes BC, and each city's local top-up or financing program. Use for a periodic accuracy audit, or whenever a rate/amount is suspected stale, not for building a new city (BC coverage is already complete).
---

# BC Rebate Verification

BC's 18 city pages all share the same provincial/utility rebate stack (CleanBC, BC Hydro, FortisBC) baked into every page via the same template — which means a single stale figure in the shared data propagates to all 18 pages at once. This skill exists to catch that kind of drift, and to spot-check the smaller number of city-specific local programs (top-ups, financing) layered on top.

Precedent: on 2026-08-09, re-verifying Toronto against live sources (Ontario, a much younger build) found a loan-rate figure had already drifted within about 24 hours of publishing. BC's content is older and has had more time to drift — treat this as more likely to find something, not less.

## Step 1 — Verify the shared provincial/utility stack (highest leverage — affects all 18 pages at once)

Fetch each of these and compare against what's currently published on the BC city page template:

1. **CleanBC heat pump rebate** (income-tiered: standard $4,000, up to $16,000, income-qualified electrical add-on up to ~$21,000) — verify via betterhomesbc.ca.
2. **BC Hydro home solar/self-generation rebate** ($5,000) and **home battery rebate** ($1,500–$5,000, Peak Saver enrollment terms) — verify via bchydro.com.
3. **BC Hydro EV charger rebate** (up to $550) — verify via bchydro.com.
4. **Insulation/windows/doors rebates** (up to $5,500 / up to $2,000) and **heat pump water heater** ($1,000–$3,000) — verify via betterhomesbc.ca.
5. **FortisBC heat pump/water heater rebates** (up to $12,000 total, dual-fuel add-on) — verify via fortisbc.com.
6. **ECAP / income-qualified free programs** (free energy kit, free heat pump install, income thresholds e.g. ~$57,200 for family of four) — verify via bchydro.com's income-based savings page.
7. Confirm whether the "Greener Homes grant/loan are both closed as of late 2025" claim (used on every city page) is still accurate, or whether anything has reopened or changed.

**Cross-validate every figure against at least two independent sources** before recording it as confirmed — the primary official page (BC Hydro/FortisBC/BetterHomes BC) plus at least one of: a targeted search surfacing multiple independent citations of the same number, a second official page (e.g. a government press release, a program-specific sub-page vs. the general overview page), or a reputable third-party summary that itself cites the primary source. This matters more than it sounds: several BC Hydro/BetterHomes BC pages render key figures via an interactive calculator rather than static text, so a single fetch can come back empty or misleading even when the page is live — don't treat an empty or partial fetch result as "unable to confirm, therefore unchanged." If a figure looks surprising, different from what's published, or expressed in a different unit (e.g. a per-kW/kWh formula vs. a flat dollar cap), that's specifically the signal to pull a second source before concluding anything drifted or stayed the same.

Record each figure as confirmed-unchanged (with both sources noted), or flag exactly what changed with the old value, new value, and source URL(s).

## Step 2 — Spot-check city-specific local programs

Not every city needs a full re-check every time, but any city with a distinguishing local claim should be verified when touched:

- Vancouver, Coquitlam, Langley, Maple Ridge, Richmond: the "$2,000 local heat pump top-up" claim — confirm each city's own program page still offers this.
- Nanaimo: "$15,000 interest-free financing" claim.
- Penticton: "own Home Energy Loan Program" claim.
- Fort St. John, Prince George: "northern fuel-switching top-ups" claim.
- Any other city-specific note (free navigator services, RetrofitAssist mentions, etc.).

## Step 3 — Validate links resolve

For every official source URL cited (BC Hydro, FortisBC, BetterHomes BC, and each city's municipal page), fetch and confirm it's live and still describes the program being cited — not just that it returns 200.

## Step 4 — Report and fix

Produce a short diff: what was checked, what's confirmed unchanged, and what drifted (old → new, with source). Fix drifted figures across every page that repeats them — since the shared rebate-grid content is duplicated per-city (not templated from a single source file), a shared-stack fix means editing all 18 city pages plus any blog posts or the BC province hub that also state the figure.

## Note on scope

This is a bigger sweep than the Ontario skill — BC has 18 cities vs. Ontario's current 2, and more accumulated time since launch. Don't try to do a full Step 1 + Step 2 + Step 3 pass in one sitting if time-constrained; Step 1 (the shared stack) is the highest-leverage check and can be done alone as a lighter periodic audit.
