-- HomePowerRebate: monthly newsletter + welcome email state (2026-10-24)
-- Apply once with: npx wrangler d1 execute homepowerrebate-outcomes --remote --file=schema-newsletter.sql
-- (ALTER TABLE fails with "duplicate column" if it was already applied: that is safe to ignore.)

-- When the welcome email last went out (a repeat signup within 24 hours sends nothing) and the id (YYYY-MM) of the last monthly issue sent to this person.
ALTER TABLE subscribers ADD COLUMN welcome_sent_at TEXT;
ALTER TABLE subscribers ADD COLUMN last_issue TEXT;

-- One row per monthly issue: how many went out, how many failed, when it finished. The Monday summary reads it.
CREATE TABLE IF NOT EXISTS newsletter_runs (
  issue TEXT PRIMARY KEY,
  sent INTEGER NOT NULL DEFAULT 0,
  failed INTEGER NOT NULL DEFAULT 0,
  started_at TEXT NOT NULL,
  finished_at TEXT
);
