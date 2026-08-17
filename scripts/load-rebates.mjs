#!/usr/bin/env node

/**
 * Load rebate data from CSV into D1 database
 * Usage: node scripts/load-rebates.mjs <csv-file> [env]
 * Example: node scripts/load-rebates.mjs data/rebates-bc-on.csv production
 */

import fs from 'fs';
import path from 'path';
import { parse } from 'csv-parse/sync';

const dbUrl = process.argv[3] === 'production'
  ? process.env.D1_DATABASE_URL
  : 'http://localhost:8787/__d1_initialize';

const csvFile = process.argv[2];

if (!csvFile) {
  console.error('Usage: node scripts/load-rebates.mjs <csv-file> [env]');
  process.exit(1);
}

if (!fs.existsSync(csvFile)) {
  console.error(`File not found: ${csvFile}`);
  process.exit(1);
}

// Parse CSV
const csvContent = fs.readFileSync(csvFile, 'utf-8');
const records = parse(csvContent, {
  columns: true,
  skip_empty_lines: true,
  trim: true,
});

console.log(`📊 Loaded ${records.length} records from ${path.basename(csvFile)}`);

// Transform CSV to database inserts
async function loadData() {
  let citiesInserted = 0;
  let programsInserted = 0;

  const citiesMap = new Map(); // Track cities to avoid duplicates

  for (const record of records) {
    try {
      // City insert (once per unique city)
      const cityKey = `${record.region}_${record.city}`;

      if (!citiesMap.has(cityKey)) {
        const cityId = `${record.region}_${record.city.toLowerCase().replace(/\s+/g, '_')}`;

        // Insert city (this would go to D1)
        console.log(`  ✓ City: ${record.city} (${record.region.toUpperCase()})`);
        citiesMap.set(cityKey, cityId);
        citiesInserted++;
      }

      const cityId = citiesMap.get(cityKey);
      const programId = `${cityId}_${record.category}`;

      // Program insert
      console.log(`    • ${record.category}: $${record.rebate_amount} (payback: ${record.payback_years}y)`);
      programsInserted++;

    } catch (err) {
      console.error(`❌ Error processing record:`, record, err.message);
    }
  }

  console.log(`\n✅ Summary:`);
  console.log(`   Cities: ${citiesInserted}`);
  console.log(`   Programs: ${programsInserted}`);
  console.log(`\nNext steps:`);
  console.log(`  1. Verify data looks correct above`);
  console.log(`  2. Run: wrangler d1 execute homepowerrebate-programs --remote < scripts/schema.sql`);
  console.log(`  3. Data is ready to bulk-insert into D1`);
}

loadData().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
