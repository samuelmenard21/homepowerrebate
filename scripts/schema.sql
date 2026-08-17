-- Rebate Programs Database Schema
-- Centralized source of truth for all rebate data across regions

CREATE TABLE IF NOT EXISTS cities (
  id TEXT PRIMARY KEY,
  region TEXT NOT NULL,  -- 'bc', 'on', 'ab', 'ns', 'ca', 'ny', 'ma'
  city TEXT NOT NULL,
  country TEXT NOT NULL,  -- 'CA' or 'US'
  primary_utility TEXT,
  secondary_utility TEXT,
  heating_degree_days INTEGER,
  avg_gas_price_per_unit REAL,
  avg_elec_price_per_kwh REAL,
  climate_region TEXT,  -- 'cold', 'moderate', 'mild', 'coastal'
  population INTEGER,
  url_slug TEXT,
  notes TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS programs (
  id TEXT PRIMARY KEY,
  city_id TEXT NOT NULL,
  category TEXT NOT NULL,  -- 'heat_pump', 'solar', 'battery', 'insulation', 'water_heater', 'windows', 'ev_charger', 'thermostat'
  rebate_amount TEXT,  -- "$10,000", "$2,500-$5,000", "Up to $8,000"
  rebate_description TEXT,
  system_size_1 TEXT,  -- e.g., "3-ton"
  system_cost_1 REAL,
  rebate_1 REAL,
  system_size_2 TEXT,  -- e.g., "3.5-ton"
  system_cost_2 REAL,
  rebate_2 REAL,
  system_size_3 TEXT,  -- e.g., "4-ton"
  system_cost_3 REAL,
  rebate_3 REAL,
  annual_savings REAL,
  payback_years REAL,
  eligibility_notes TEXT,
  income_qualified BOOLEAN,
  stacking_allowed BOOLEAN,
  verified_date TEXT,
  source_1 TEXT,
  source_1_url TEXT,
  source_2 TEXT,
  source_2_url TEXT,
  source_3 TEXT,
  source_3_url TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (city_id) REFERENCES cities(id)
);

CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  program_id TEXT NOT NULL,
  source_name TEXT,
  source_url TEXT,
  verified_date TEXT,
  FOREIGN KEY (program_id) REFERENCES programs(id)
);

CREATE INDEX IF NOT EXISTS idx_programs_city ON programs(city_id);
CREATE INDEX IF NOT EXISTS idx_programs_category ON programs(category);
CREATE INDEX IF NOT EXISTS idx_cities_region ON cities(region);
