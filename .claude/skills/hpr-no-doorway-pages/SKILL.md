---
name: hpr-no-doorway-pages
description: Mandatory check before publishing ANY new city page, category subpage, or blog-city-variant on HomePowerRebate. Prevents doorway/near-duplicate pages — city pages that are byte-identical except for a find-replaced city name — which Google can penalize and which this site has shipped three separate times (Aug 2026 smart-thermostats, Aug 2026 CA windows-doors, Sep 2026 audit found 236 pages across 10 regions still doing this).
---

# HPR No-Doorway-Pages Checklist

## Why this exists

On 2026-09-03, an SEO audit found 236 category subpages across AB, BC, ON, CA (5 metro clusters), CO, MA, VT, and NY were byte-identical to their sibling city pages except for the city name — some clusters had up to 14 cities sharing one templated page. This happened because city-page generation (often via agents working in batch) defaulted to "write once, swap the city name" instead of pulling real per-city data. It had already happened twice before this session (BC smart-thermostats, CA windows-doors) and was fixed both times — but the pattern kept recurring in new categories/regions because nothing enforced it going forward. This is the fix: a mandatory pre-publish gate.

Search engines treat this pattern as doorway pages — many URLs funneling to functionally identical content — and can suppress or deindex the whole cluster, not just the offending pages. It also means real homeowners get generic content with no actual local value.

## The rule

**No two sibling city pages in the same category may be identical once the city name is normalized out.** Every page needs at least one genuinely city-specific element:

- Real per-city rebate dollar figures pulled from `city-rebate-lookup.json` (not the region average, not invented).
- The city's actual utility/program name where it varies (e.g. BC Hydro vs. FortisBC, or the specific municipal utility for a US city) — check `installers/json/{city}.json` or the city's own hub page for what's already been researched.
- At least one locally-distinct note: local climate/heating-degree-days framing, a housing-stock fact, a program quirk specific to that city's utility territory, or content already researched for that city's hub page (`ca/{province}/{city}/index.html` or `us/{state}/{city}/index.html`) — reuse real researched content, never invent one.

A shared intro paragraph or shared boilerplate (nav, footer, generic "how rebates work" explainer) is fine — the whole point is that the sections carrying the SEO/informational value can't be templated.

## Before publishing any new city page or category subpage batch

- [ ] Run `python3 scripts/check_duplicate_content.py --category <the-category-you're-adding>` (or with no `--category` flag to check everything) **before** committing.
- [ ] If it reports a new duplicate group involving pages you just added, fix it before pushing — don't ship it and plan to fix later. Every prior instance of this bug was shipped, then caught in a later audit, then required a separate cleanup pass. Catching it pre-publish is strictly cheaper.
- [ ] If you're generating a batch across many cities (agent-driven or scripted), do not let the generation pull from one shared paragraph bank with find-replace as the only variation. Pull real numbers from `city-rebate-lookup.json` per city and write the local-specific note per city, not once for the cluster.
- [ ] Apply the `no-ai-slop` skill standard to any new prose — this project bans invented "local flavor" filler as much as it bans templated duplication; the fix is real specifics, not padded language that merely looks distinct.

## Standing audit

Run `python3 scripts/check_duplicate_content.py` periodically (monthly is reasonable, or after any large content batch) even when you don't think you introduced a duplicate — it catches regressions from agents that skipped this checklist. `--fail-on-duplicates` exits 1 for wiring into a pre-push hook or CI if that's ever set up.

## Related

[[hpr-new-city-checklist]] covers the sibling problem of a new city missing rebate DATA entirely (email fallback). This skill covers the new city having data but templated CONTENT.
