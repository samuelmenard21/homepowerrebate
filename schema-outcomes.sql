-- HomePowerRebate: verified outcomes table (Phase 1)
-- Powers the "compare against neighbours / province / national" feature.
-- Apply with: wrangler d1 execute homepowerrebate-outcomes --remote --file=schema-outcomes.sql

CREATE TABLE IF NOT EXISTS outcomes (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,

  -- what was installed
  category TEXT NOT NULL,        -- heat-pump | solar | battery | insulation | water-heater | windows | ev-charger | thermostat

  -- where (FSA only — first 3 chars of postal code — never store full postal/address)
  postal_fsa TEXT NOT NULL,
  city TEXT NOT NULL,
  province TEXT NOT NULL,        -- BC | ON | AB | NS | MA

  -- when
  install_month TEXT NOT NULL,   -- 'YYYY-MM'

  -- money (whole CAD/USD dollars, no cents)
  total_cost REAL NOT NULL,      -- pre-rebate installed cost
  rebates_received REAL NOT NULL DEFAULT 0,
  net_cost REAL NOT NULL,        -- total_cost - rebates_received, computed at insert

  -- optional bill comparison (nullable — second-step, higher friction)
  monthly_bill_before REAL,
  monthly_bill_after REAL,

  -- optional installer link (also feeds installer outcome-verification later)
  installer_name TEXT,

  -- trust signal, not shown until verification tier ships (Phase 3)
  verified INTEGER NOT NULL DEFAULT 0,

  -- contact, never exposed in aggregate queries — used only for dedupe/verification follow-up
  email TEXT NOT NULL,

  status TEXT NOT NULL DEFAULT 'new'  -- new | flagged | verified
);

CREATE INDEX IF NOT EXISTS idx_outcomes_category_city ON outcomes(category, city);
CREATE INDEX IF NOT EXISTS idx_outcomes_category_province ON outcomes(category, province);
CREATE INDEX IF NOT EXISTS idx_outcomes_category ON outcomes(category);
