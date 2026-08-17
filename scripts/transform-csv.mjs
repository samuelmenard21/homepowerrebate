#!/usr/bin/env node

/**
 * Transform agent-generated CSV to template format
 * Converts detailed agent CSV → normalized template CSV for D1 loading
 *
 * Usage: node scripts/transform-csv.mjs <input-csv> <region> <country>
 * Example: node scripts/transform-csv.mjs ca-ny-rebates.csv us US
 */

import fs from 'fs';
import { parse } from 'csv-parse/sync';
import { stringify } from 'csv-stringify/sync';

const input = process.argv[2];
const region = process.argv[3];
const country = process.argv[4];

if (!input || !region || !country) {
  console.error('Usage: node scripts/transform-csv.mjs <input-csv> <region> <country>');
  console.error('Example: node scripts/transform-csv.mjs ca-ny-rebates.csv us US');
  process.exit(1);
}

const csv = fs.readFileSync(input, 'utf-8');
const records = parse(csv, { columns: true, trim: true });

// Transform to template format
const transformed = records.map(row => ({
  region: region,
  city: row.City,
  country: country,
  utility_primary: row.Utility,
  heating_degree_days: row.HDD || '',
  heat_pump_rebate: extractRebateAmount(row.Heat_Pump_HVAC_Rebate),
  heat_pump_system_size: '4-ton',
  heat_pump_cost: extractNumber(row.Heat_Pump_Typical_Cost),
  heat_pump_annual_savings: extractNumber(row.Heat_Pump_Annual_Savings_Dollars),
  heat_pump_payback_years: extractNumber(row.Heat_Pump_Payback_Years),
  solar_rebate: extractRebateAmount(row.Solar_Rebate),
  solar_kw: '5kW',
  solar_cost: extractNumber(row.Solar_Typical_Cost_5KW),
  solar_annual_savings: extractNumber(row.Solar_Annual_Savings),
  solar_payback_years: extractNumber(row.Solar_Payback_Years),
  battery_rebate: extractRebateAmount(row.Battery_Rebate),
  battery_kwh: '13.5',
  battery_cost: extractNumber(row.Battery_Typical_Cost),
  water_heater_rebate: extractRebateAmount(row.Heat_Pump_Water_Heater_Rebate),
  insulation_rebate: extractRebateAmount(row.Home_Insulation_Rebate),
  windows_rebate: extractRebateAmount(row.Windows_Rebate),
  ev_charger_rebate: extractRebateAmount(row.EV_Charger_Rebate),
  thermostat_rebate: extractRebateAmount(row.Smart_Thermostat_Rebate),
  notes: row.Heat_Pump_Rebate_Note || `${row.State} - ${row.Utility}`,
  source_utility: row.Primary_Source_1 || '',
  source_state: row.Primary_Source_2 || '',
  source_city: row.Primary_Source_3 || '',
  verified_date: new Date().toISOString().split('T')[0]
}));

// Helpers
function extractRebateAmount(str) {
  if (!str || str === '$0' || str.includes('SGIP')) return '$0';
  // Extract first dollar amount
  const match = str.match(/\$[\d,]+/);
  return match ? match[0] : '$0';
}

function extractNumber(str) {
  if (!str) return '';
  const match = str.match(/[\d,]+/);
  return match ? match[0].replace(/,/g, '') : '';
}

// Output
const output = input.replace('.csv', '-transformed.csv');
const outputCsv = stringify(transformed, { header: true });
fs.writeFileSync(output, outputCsv);

console.log(`✅ Transformed: ${input} → ${output}`);
console.log(`📊 Records: ${transformed.length}`);
console.log(`\nNext step: Load into D1`);
console.log(`  wrangler d1 execute homepowerrebate-programs --remote --file ${output}`);
