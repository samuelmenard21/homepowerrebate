# Phase 3: Data-Driven City Pages (Infrastructure Build)

## Status: 🚀 Ready for D1 Deployment & Page Generation

### Agents Completed ✅✅✅

**Agent 1: CA/NY/MA Research** (✅ DONE)
- ✅ 44 US cities complete (25 CA + 6 NY + 13 MA)
- ✅ 8 upgrade categories × 3+ verified sources each
- ✅ Delivered: ca-rebates.csv, ny-rebates.csv, ma-rebates.csv
- ✅ Critical findings: Federal credits expired Dec 2025, CA programs closed/waitlisted, NY + MA programs strong

**Agent 2: Canadian Data Extraction** (✅ DONE)
- ✅ 45 Canadian cities complete (18 BC + 20 ON + 5 AB + 2 NS)
- ✅ 8 upgrade categories per city
- ✅ Delivered: bc-rebates.csv, on-rebates.csv, ab-ns-rebates.csv
- ✅ All data sources verified 2026-08-17

### Infrastructure Built ✅

1. **D1 Database Schema** (`scripts/schema.sql`)
   - Tables: `cities`, `programs`, `sources`
   - Supports 8 upgrade categories per city
   - Stores rebate amounts, costs, annual savings, payback years, verified sources

2. **CSV Template** (`scripts/rebates-template.csv`)
   - Standardized format for data entry
   - Columns: region, city, country, utility, 8 categories × (rebate, cost, savings, payback)
   - Data agents will output matching this format

3. **Data Loader Script** (`scripts/load-rebates.mjs`)
   - Ingests CSV files
   - Validates data format
   - Ready for bulk D1 import

4. **Page Template** (`scripts/page-template.html`)
   - All 8 categories with interactive calculators
   - Responsive grid layout
   - Template variables for dynamic content injection
   - Calculator logic for heat pump, solar, battery, water heater
   - Info cards for insulation, windows, EV charger, thermostat

### Next Steps (When Agents Complete)

**Week 1 (Priority Order):**
1. **Receive CSVs from both agents** (6 files total)
2. **Create D1 database** in Cloudflare: `wrangler d1 create homepowerrebate-programs`
3. **Apply schema** to D1: `wrangler d1 execute homepowerrebate-programs --remote < scripts/schema.sql`
4. **Bulk load Canadian data** (fastest to test): `node scripts/load-rebates.mjs bc-rebates.csv`
5. **Test page generation** on 2-3 BC cities
6. **Generate all Canadian pages** (44 cities)
7. **Bulk load US/MA data** (CA/NY/MA CSVs)
8. **Generate all 44 US/MA pages**

**Result:** 88 city pages, all auto-generated from D1, all with working calculators, all with verified 3+ sources per data point

### Architecture

```
Research Agents (CSV) 
    ↓
CSV Files (bc-rebates.csv, on-rebates.csv, ca-rebates.csv, etc.)
    ↓
Data Loader Script (validate, transform)
    ↓
D1 Database (single source of truth: cities + programs + sources)
    ↓
Page Generator (queries D1, fills template, outputs HTML)
    ↓
88 Static City Pages (live at /ca/bc/vancouver/, /us/ca/los-angeles/, etc.)
```

### Key Features

- **Single source of truth:** All rebate data in D1, no duplicates
- **Auto-update:** Change one rebate in DB, all pages auto-update
- **Scalable:** New state/province = research → CSV → load → done
- **Verified sources:** 3+ sources per data point, stored in DB, linked on pages
- **Responsive:** Works on mobile, tablet, desktop
- **SEO:** H1 tags, canonical URLs, GA4, schema.org metadata

### Deliverables (Final)

- ✅ Database schema
- ✅ Page template (all 8 categories)
- ✅ Data loader pipeline
- ⏳ Research CSVs (agents working)
- ⏳ D1 database (created after CSVs arrive)
- ⏳ 88 generated city pages
- ⏳ Source citations on each page

### Timeline

- **Today:** Infrastructure + agents launched
- **Next 2-4 hours:** Agents research and extract data
- **Day 2:** Load data, test generation, create all pages
- **Day 3:** Verify, deploy, monitor

---

**What You Don't Have to Do:**
- ✅ No manual page building
- ✅ No copy-paste of rebate numbers
- ✅ No repetitive data entry
- ✅ No calculator code per page

**What The System Does:**
- ✅ Research with verified sources
- ✅ Data validation
- ✅ Bulk loading to DB
- ✅ Auto-generation of HTML
- ✅ Responsive design
- ✅ SEO optimization
