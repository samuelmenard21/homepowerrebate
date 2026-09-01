---
name: hpr-rebate-research
description: Periodically scan competitor rebate-directory sites (xolar.ca/rebates/ for Canada, similar aggregators for US states) to catch new, changed, or expired programs HomePowerRebate might be missing or have gone stale, cross-reference against what's already published on the site, and produce a gap report for a human to verify and act on. This skill never publishes anything itself — it only surfaces candidates.
---

# HPR Rebate Research (Competitor Gap Scan)

HomePowerRebate's rebate content is hand-verified per region (see bc-rebate-verification, ontario-city-research), but that verification only re-checks programs we already know about. It doesn't catch a program we've never heard of, or one that quietly expired without us noticing. This skill closes that blind spot by comparing what a competitor directory lists against what's already live on our site — then stopping. It does not add programs, edit pages, or treat a competitor's listing as verified fact.

Precedent for the caution here: in this same working session, 2 of 6 research-agent claims about "what's on the site" or "what's confirmed" turned out to be wrong or stale before a human caught them by checking the actual files. A competitor site is a strictly lower-trust source than our own codebase — treat every gap this skill surfaces as an unconfirmed lead, never as a fact to publish on.

## Step 1 — Pick the comparison source per region

- Canada (all provinces): xolar.ca/rebates/ is the primary comparison source. It's a Canada-wide filterable directory, so filter it to the specific province being checked.
- US states: search for an equivalent state-specific or utility-specific rebate aggregator (e.g. a state energy office rebate finder, a major installer's rebate directory page, DSIRE — the US Database of State Incentives for Renewables & Efficiency, dsireusa.org, is a good default when no better competitor exists). Note which source was used; it may differ by state.
- Only compare one region per pass unless doing a full sweep — a full Canada + US pass in one sitting is a lot of surface area to hold accurately.

## Step 2 — Pull the competitor's current listing for that region

1. Fetch the competitor page/filtered view for the region.
2. Record every program listed: name, category (heat pump / solar / battery / insulation / water heater / windows / EV charger / smart thermostat / financing), amount, and whether it reads as currently open or expired/closed.
3. Note the fetch date — competitor pages change, and this list is only a snapshot.

## Step 3 — Cross-reference against what's already published on HomePowerRebate

1. Read the region's actual hub page (e.g. `ca/bc/index.html`) and at least 2-3 representative city pages for that region — not from memory of a prior session, from the files as they exist right now.
2. For each program the competitor lists, check: does HomePowerRebate already cover this program (possibly under a different name — utilities and program names get rebranded)? Is our stated amount consistent with theirs, or does it look drifted?
3. For each program HomePowerRebate already covers, check: does the competitor list it as still open, or as expired/changed in a way our site doesn't reflect?

## Step 4 — Classify each discrepancy, don't resolve it

Sort findings into three buckets:

- **Possible gap** — competitor lists a program HomePowerRebate doesn't mention at all. Flag it; do not assume it's real until independently verified against the program's own official source (same two-source standard as bc-rebate-verification and ontario-city-research — a competitor directory alone is one source, not two).
- **Possible drift** — same program, different amount or status between the competitor and our site. Flag both values and which is newer-looking, but don't overwrite our figure without checking the actual official source.
- **Competitor-only or unverifiable** — the competitor lists something with no clear official source, vague terms, or that reads like affiliate content rather than a real program. Flag it as low-confidence; these are common on directory sites and are exactly the kind of thing not to import uncritically.

Explicitly do NOT flag: minor wording differences for the same program, or amounts that are within a plausible rounding/tier difference of what we already show.

## Step 5 — Report, then stop

Produce a short gap report per region checked:
- Source compared against, and fetch date
- Possible gaps (program name, category, competitor's stated amount, competitor URL)
- Possible drift (program name, our stated amount vs. competitor's, which page(s) of ours state it)
- Competitor-only / unverifiable items, explicitly marked low-confidence

This report is the deliverable. Verifying a flagged gap against the program's own official source, and deciding whether/how to add it to the site, is separate follow-up work for a human or a future session — matching the ontario-city-research and bc-rebate-verification precedent of never publishing an unverified figure. Do not create or edit any HomePowerRebate page as part of running this skill.

## Cadence

Not a per-region-launch requirement like ontario-city-research, and not tied to a specific city like bc-rebate-verification. Run this periodically (e.g. monthly, or when a region hasn't been touched in a while) as a standalone check, one region at a time.
