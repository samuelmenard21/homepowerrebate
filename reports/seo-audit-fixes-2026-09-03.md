# SEO Audit & Fixes — September 3, 2026

Full-site audit of HomePowerRebate (2,571 HTML files across CA/US city pages, category subpages, blog posts, and hub pages). Findings and fixes below, organized by category. Commit: `02f91efb`.

## 1. Technical / Crawlability

### Sitemap — verified complete, no fix needed
- `sitemap.xml` lists 2,565 URLs. Cross-checked every real HTML file in the repo against sitemap entries. The only 6 files not in the sitemap are legitimately excluded: `404.html`, dev/build templates (`ONTARIO_CITY_PAGE_TEMPLATE.html`, `CITY_PAGE_TEMPLATE_OPTIMIZED.html`, `scripts/page-template.html`), `_partials/nav-footer.html` (an include fragment, not a page), and `og-image.html` (an image-render helper). No gap. This has been a recurring bug in the past (see `hpr_sitemap_gap_fixed` memory) — confirmed not regressed.
- Regenerated `sitemap.xml` anyway via `scripts/generate_sitemap.py` to pick up anything from recent content batches. Included in this commit.

### Broken internal links — found and fixed
Ran a full href-vs-filesystem check across all 2,571 files (164,513 hrefs checked). Fixed every real broken link found:

- **`_partials/nav-footer.html`** and the **164 pages it's baked into** (not fetched via JS — copy-pasted) contained a dead link: `/us/ny/national-grid/yonkers/` labeled "Yonkers (National Grid)". No such page exists; the real Yonkers page is `/us/ny/con-edison/yonkers/`, already listed correctly right next to it. Removed the erroneous duplicate entry sitewide (164 files + the partial source).
- **`blog-bc-hydro-vs-fortisbc-rebates.html`** — 14 broken links using a stale URL pattern (`/ca/bc/{city}-heat-pump-guide`) instead of the current one (`/ca/bc/{city}/heat-pump/`). Fixed for Vancouver, Burnaby, Surrey, Victoria, Nanaimo, Kelowna, Kamloops, Abbotsford, Chilliwack, Penticton, Squamish, Vernon, Fort St. John, Prince George.
- **`blog-island-vs-mainland-bc-heat-pump.html`** — same stale pattern, 4 links fixed (Nanaimo, Victoria, Vancouver, Burnaby).
- **`blog-kelowna-vs-kamloops-solar.html`** — same stale pattern, 2 links fixed (Kelowna, Kamloops).
- **`blog-heat-pump-vs-ac-cost-rebates.html`** — `/ca/bc/fortis-rebates` didn't exist; repointed to `/ca/bc/` (the BC hub, which covers FortisBC).
- **Installer profile links in VT/CO city category pages** — slug-generation mismatches where the link used "-and-" and the real directory used a plain dash (e.g. link `jim-manley-plumbing-and-heating` vs real dir `jim-manley-plumbing-heating`). Fixed 6 via fuzzy-matched correct target: `us/vt/rutland/heat-pump/index.html` (Jim Manley, Bernie's, Rutland Heating & Air), `us/vt/barre/heat-pump/index.html` (Rowell, J A Gould). 5 more had no matching profile page at all (the installer was never given a profile, or in one case — SERVPRO of Barre/Montpelier — isn't actually an HVAC installer) and were unlinked (kept as plain text with their outbound "Visit site" link intact) rather than pointed at a guessed URL: `us/vt/barre/heat-pump/index.html` (SERVPRO), `us/vt/burlington/solar/index.html` (Green Mountain Solar, Lakeside Electric), `us/vt/burlington/heat-pump/index.html` (Air Systems Inc, Benoure Plumbing).
- Re-ran the full link check after fixes: **zero broken internal links remain** (excluding intentionally-unrendered template placeholder files like `scripts/page-template.html`, which use `{{...}}` tokens, and one JS template literal in `calculator/index.html` that isn't an actual href).

### 25C federal tax credit — checked, no bug found
Searched all 25C mentions sitewide (52 files, mostly `hrv/index.html` city pages). Every body-copy mention correctly states the credit "expired December 31, 2025." The only 25C references without an "expired" qualifier are `<p class="src">` citation lines naming it as a historical data source — not a claim that it's active. No fix needed; this was checked because it's a known past bug class.

## 2. On-Page Structure

- **`<title>` and meta description**: full regex scan across all city/blog/hub pages. Only 3 files missing either tag: `installers/solar-carousel.html`, `installers/unified-carousel.html`, `installers/installer-carousel.html`. Confirmed these are HTML *fragments* injected into other pages (not standalone URLs — not in sitemap, not directly navigable). No fix needed.
- **Image alt text**: spot-checked all `<img>` tags across `ca/` and `us/` city pages (53 images sampled). Zero missing or empty `alt` attributes.
- **FAQPage schema**: 1,156 of 1,169 city-page `index.html` files carry FAQPage schema (~99%) — consistent with the existing `hpr_schema_standards` baseline. No regression found.

## 3. Doorway / Near-Duplicate Content — SIGNIFICANT FINDING, NOT FIXED (see manual actions)

Ran a real duplicate-content check: normalized every category-subpage body (city name stripped/replaced with `[CITY]` token) and hashed it, grouped by category across sibling cities in the same metro cluster.

**Result: 33 groups of pages are byte-identical except for the city name.** Verified with a manual diff (e.g. `us/co/aurora/water-heater/index.html` vs `us/co/denver/water-heater/index.html` — 279 lines each, diff shows literally zero differences beyond "Aurora"→"Denver"). This affects:
- VT metro cluster (Rutland, South Burlington, Montpelier, Barre) — water-heater, ev-charger, windows-doors, insulation, smart-thermostats, battery
- CO Front Range cluster (Aurora, Denver, Boulder) — same categories
- CA Bay Area, Inland Empire, San Diego, LA, Sacramento clusters — solar, ev-charger, windows-doors, insulation, battery
- BC — a 12-city windows cluster (Coquitlam, Nanaimo, Richmond, Kelowna, Victoria, Langley, Penticton, Squamish, Kamloops, Surrey, Burnaby, Vernon)

This is the same doorway-page issue that has been found and fixed twice before on this site (per project memory). It was **not fixed in this pass** — genuine differentiation requires real, city-specific researched content (local utility names, real rebate amounts, real housing-stock commentary) for each of ~100+ affected pages, which is a content-research project, not a mechanical bug fix, and fabricating that content would violate the site's no-fabrication standard. Full list of affected file groups is in the script output; flagged as the top item in the manual-actions report.

## 4. AEO / AI Overview Readiness

Not deeply re-audited this pass beyond the FAQPage schema check above (already near-universal) — the concise 40–100 word direct-answer-under-H2 pattern was previously implemented per `hpr_content_listicle_strategy` and `hpr_schema_standards` memory and wasn't spot-checked for regression here due to time; recommend as a follow-up pass if a dedicated AEO audit is wanted.

## Files touched (all committed and pushed to `origin/main`)
- `_partials/nav-footer.html` + 164 pages sharing its baked-in nav
- `blog-bc-hydro-vs-fortisbc-rebates.html`
- `blog-heat-pump-vs-ac-cost-rebates.html`
- `blog-island-vs-mainland-bc-heat-pump.html`
- `blog-kelowna-vs-kamloops-solar.html`
- `us/vt/barre/heat-pump/index.html`
- `us/vt/burlington/heat-pump/index.html`
- `us/vt/burlington/solar/index.html`
- `us/vt/rutland/heat-pump/index.html`
- `sitemap.xml` (regenerated)
