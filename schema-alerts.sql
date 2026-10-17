-- HomePowerRebate: program-launch alert lists (one row per email per list)
-- First list: 'federal-hp' (tell me the day the National Heat Pump Rebate portal opens).
-- Separate from `subscribers` on purpose: these people asked for one alert only, so they get
-- no results drip and are NOT added to the Resend newsletter audience (CASL: consent is for this alert).
-- Apply with: wrangler d1 execute homepowerrebate-outcomes --remote --file=schema-alerts.sql
-- Launch-day list: SELECT email, province FROM alerts WHERE list = 'federal-hp' AND unsubscribed = 0;

CREATE TABLE IF NOT EXISTS alerts (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  list TEXT NOT NULL,
  province TEXT,
  city TEXT,
  page TEXT,
  unsubscribed INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_email_list ON alerts(email, list);
CREATE INDEX IF NOT EXISTS idx_alerts_list ON alerts(list, unsubscribed, province);

-- How often the alert box was seen (at least half on screen), one counter per day, list and page (page includes ?src=
-- when the visitor arrived from a shared or installer link). No IP, cookie or person is stored.
-- Weekly report: python3 scripts/federal_alert_report.py
CREATE TABLE IF NOT EXISTS alert_views (
  day TEXT NOT NULL,
  list TEXT NOT NULL,
  page TEXT NOT NULL,
  views INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day, list, page)
);
