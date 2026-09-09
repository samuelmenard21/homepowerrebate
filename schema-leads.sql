-- HomePowerRebate: lead follow-up tracking table
-- Powers two automated touches per lead:
--   1. Installer reminder at +24h ("has this homeowner heard from you yet")
--   2. Homeowner follow-up at +2 business days ("did they reach out?"),
--      sent exactly once, with alternate-installer fallback on "no".
-- Apply with: wrangler d1 execute homepowerrebate-outcomes --remote --file=schema-leads.sql

CREATE TABLE IF NOT EXISTS leads (
  id TEXT PRIMARY KEY,               -- same as lead_id used in email records
  email TEXT NOT NULL,
  firstname TEXT,
  phone TEXT,
  city TEXT NOT NULL,
  province TEXT NOT NULL DEFAULT 'BC',
  service TEXT NOT NULL DEFAULT 'heat-pump',

  installer_name TEXT,
  installer_email TEXT,
  installer_phone TEXT,

  created_at TEXT NOT NULL,

  -- installer-facing: one reminder at +24h if they haven't been nudged yet
  installer_reminder_send_at TEXT,
  installer_reminder_sent_at TEXT,

  -- homeowner-facing: one follow-up at +2 business days, never repeated
  followup_send_at TEXT,
  followup_sent_at TEXT,
  response TEXT,                     -- 'heard_back' | 'no_response' | NULL
  responded_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_leads_followup_due ON leads(followup_send_at, followup_sent_at);
CREATE INDEX IF NOT EXISTS idx_leads_installer_reminder_due ON leads(installer_reminder_send_at, installer_reminder_sent_at);
