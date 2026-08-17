# Phase 3 Deployment: D1 Database & Page Generation

## Prerequisites
- Cloudflare account with D1 access
- `wrangler` CLI installed and authenticated
- All CSV files consolidated: `scripts/all-rebates-consolidated.csv` ✅

## Deployment Steps

### Step 1: Create D1 Database
```bash
wrangler d1 create homepowerrebate-programs
```

This will output a database ID. Copy it and update `wrangler.toml`:
```toml
[[d1_databases]]
binding = "PROGRAMS_DB"
database_name = "homepowerrebate-programs"
database_id = "YOUR_ID_HERE"  # Paste the ID from Step 1
```

### Step 2: Apply Schema
```bash
wrangler d1 execute homepowerrebate-programs --remote --file scripts/schema.sql
```

### Step 3: Load Rebate Data into D1

**Option A: Using SQL INSERT (Recommended)**
```bash
# Convert CSV to SQL INSERT statements
node scripts/csv-to-sql.mjs scripts/all-rebates-consolidated.csv > scripts/load-data.sql

# Execute the SQL
wrangler d1 execute homepowerrebate-programs --remote --file scripts/load-data.sql
```

**Option B: Manual SQL (for testing first 5 rows)**
```sql
INSERT INTO cities (id, region, city, country, primary_utility, heating_degree_days, climate_region)
VALUES
  ('bc_abbotsford', 'bc', 'Abbotsford', 'CA', 'BC Hydro', 4200, 'Temperate Maritime'),
  ('bc_burnaby', 'bc', 'Burnaby', 'CA', 'BC Hydro', 3600, 'Temperate Maritime'),
  ... (89 total rows);

INSERT INTO programs (id, city_id, category, rebate_amount, system_size_1, system_cost_1, rebate_1, ...)
VALUES
  ... (712 total data points);
```

### Step 4: Verify Data Loaded
```bash
wrangler d1 execute homepowerrebate-programs --remote --command "SELECT COUNT(*) as city_count FROM cities;"
wrangler d1 execute homepowerrebate-programs --remote --command "SELECT COUNT(*) as program_count FROM programs;"
```

Expected output:
- `city_count`: 89
- `program_count`: ~712 (8 categories × 89 cities)

### Step 5: Generate City Pages
```bash
node scripts/generate-city-pages.mjs
```

This will:
- Query D1 for all 89 cities
- Render each city with all 8 calculators
- Output to `/us/ca/los-angeles/los-angeles/index.html` format
- Include all SEO/AEO optimizations

### Step 6: Deploy to Cloudflare
```bash
wrangler deploy
git add -A && git commit -m "Deploy Phase 3: 89 city pages with D1 backend"
git push origin main
```

## File Structure (After Generation)

```
/us/ca/los-angeles/los-angeles/index.html          (25 CA city pages)
/us/ca/sacramento/sacramento/index.html
... (6 regional hub pages)

/us/ny/con-edison/new-york-city/index.html         (6 NY city pages)
/us/ny/national-grid/buffalo/index.html
... (2 utility hub pages)

/us/ma/boston/index.html                           (13 MA city pages)
... (1 state hub page)

/ca/bc/vancouver/index.html                        (18 BC city pages)
... (1 regional hub page)

/ca/on/toronto/index.html                          (20 ON city pages)
... (1 regional hub page)

/ca/ab/calgary/index.html                          (5 AB city pages)
... (1 regional hub page)

/ca/ns/halifax/index.html                          (2 NS city pages)
... (1 regional hub page)
```

## Data Integrity Checks

After deployment, run these checks:

```bash
# Check all cities rendered
find . -name "index.html" -path "*/ca/*" -o -path "*/us/*" | wc -l
# Expected: ~100+ (89 cities + regional hubs)

# Verify H1 tags present (SEO)
grep -r "<h1>" us/ ca/ | wc -l
# Expected: ~89 (one per city page)

# Verify GA4 tracking
grep -r "G-W33G4TGRHD" us/ ca/ | wc -l
# Expected: ~89 (on every page)

# Verify canonical URLs
grep -r "rel=\"canonical\"" us/ ca/ | wc -l
# Expected: ~89

# Verify source citations (3+ per city)
grep -r "source_1_url\|source_2_url\|source_3_url" us/ ca/ | wc -l
# Expected: ~270+ (3 sources × 89 cities)
```

## Rollback (If Needed)

```bash
# Drop D1 database (WARNING: destructive)
wrangler d1 delete homepowerrebate-programs

# Revert git
git revert HEAD

# No pages will be generated until you re-deploy
```

## Next Steps: NY Expansion

To add more New York cities (e.g., Ithaca, Poughkeepsie, Glens Falls):

1. **Research** the cities (3+ sources per category, 8 categories)
2. **Add rows** to `scripts/ny-rebates.csv`
3. **Consolidate** again: `./scripts/consolidate-rebates.sh`
4. **Reload** into D1: `wrangler d1 execute homepowerrebate-programs --remote --file scripts/load-data.sql`
5. **Generate** new pages: `node scripts/generate-city-pages.mjs`
6. **Deploy**: `git add -A && git commit && git push origin main`

Total time for expansion: ~2-3 hours research + 5 minutes automated generation/deployment = **2.5-3.5 hours per new state/province**.

## Database Schema Reference

```sql
-- Cities table (89 rows)
id: bc_abbotsford
region: bc
city: Abbotsford
country: CA
primary_utility: BC Hydro
heating_degree_days: 4200
climate_region: Temperate Maritime

-- Programs table (~712 rows)
id: bc_abbotsford_heat_pump
city_id: bc_abbotsford
category: heat_pump
rebate_amount: $4,000-$16,000
system_size_1: 3-ton
system_cost_1: $12,000
rebate_1: $4,000
...
verified_date: 2026-08-17
source_1_url: https://www.bchydro.com/...
```

---

**Status:** Ready for production deployment ✅  
**Last verified:** 2026-08-17  
**Total cities:** 89  
**Total data points:** ~712  
**All sources:** 3+ per city verified  
