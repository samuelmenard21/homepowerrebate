---
name: ontario-city-research
description: Research a new Ontario city before building its rebate hub page — confirm the correct local distribution company (LDC), find any city-specific loan/rebate programs, and validate every official source link actually resolves before it's cited on the page. Use whenever adding a new Ontario city to HomePowerRebate (e.g. "add Ottawa", "build out Mississauga").
---

# Ontario City Research

Ontario has 60+ local distribution companies (LDCs) instead of BC's 2 utilities (BC Hydro + FortisBC), and municipal programs vary city by city (Toronto has HELP, Ottawa has Better Homes Ottawa, others may have nothing). Getting the utility wrong or citing a dead link is a worse trust problem than a missing page — this skill exists to catch both before a city page ships.

Run this **before** drafting any content for a new Ontario city, not after.

## Step 1 — Identify the correct LDC

1. Web-search `"<city name>" electricity utility distribution company Ontario` and `"<city name>" hydro`.
2. Confirm the LDC's official name (e.g. "Toronto Hydro", "Alectra Utilities", "Hydro One", "Elexicon Energy") and that it actually serves the specific city/municipality being built — LDC service territories don't always match municipal boundaries exactly, so verify the specific city, not just the general region.
3. Note whether the city is on Enbridge Gas for natural gas (most of Ontario is, but confirm — don't assume).
4. Record: LDC name + official URL, gas utility + official URL.

## Step 2 — Find city-specific programs

1. Web-search `"<city name>" home energy loan program` and `"<city name>" heat pump rebate` and `site:<city>.ca energy retrofit`.
2. Look specifically for: municipal financing/loan programs (like Toronto's HELP), local top-up rebates, or city-run energy coaching services.
3. If nothing city-specific exists, that's a valid finding — don't invent a program. Say explicitly on the page that the city follows the standard provincial HRSP stack with no local top-up, same pattern used for BC cities without a local top-up.

## Step 3 — Validate every link before it goes on the page, with at least two independent sources per material figure

For each official source URL you're about to cite (LDC rebate page, municipal program page, HRSP category page):

1. Fetch the URL and confirm it returns a live page (not a 404, redirect to a generic homepage, or "page moved" notice).
2. Confirm the page content actually describes the program you're about to cite — a URL that resolves but now describes a *different* or *discontinued* program is worse than an obvious 404, since it reads as verified when it isn't.
3. If a source has moved, find the current URL rather than leaving the stale one — don't cite from memory or a prior session's data without re-checking, since these programs change.
4. **Cross-validate every dollar figure, rate, or eligibility rule against a second, independent source** before publishing it — the primary official page plus at least one of: a search that surfaces multiple independent citations of the same figure, a second official page (e.g. a press release or program-overview page), or a reputable third-party summary that itself cites the primary source. A single WebFetch of one page is not enough confidence on its own, especially for pages that render dynamically (calculators, JS-gated content) where a fetch can silently return incomplete or misleading content — if the first source's figure looks surprising or doesn't match what's already published, that's a signal to check a second source, not a reason to skip it.

## Step 4 — Flag anything unconfirmed

If a rebate amount, deadline, or program detail can't be verified against a live official source in this pass, do not present it as fact on the page. Say explicitly what couldn't be confirmed (see the precedent: the Nov 30, 2026 HRSP expiry date from an earlier secondary source could not be confirmed on the official site, so the Toronto page states that explicitly rather than asserting the date). This matters more for Ontario than it did for BC, since Ontario's LDC fragmentation means there's no single canonical utility to cross-check against.

## Output

Before drafting the city's hub page, produce a short research summary:
- LDC name + URL (verified live)
- Gas utility (Enbridge Gas, confirmed) + URL
- Any city-specific loan/rebate program found, with verified live URL — or explicit confirmation that none exists
- Any detail that could not be verified and should be flagged on the page rather than stated as fact

This summary is what gets translated into the city's "Local context" and "Provincial & utility programs" sections — don't draft those sections from assumption or pattern-matching against Toronto's structure alone.
