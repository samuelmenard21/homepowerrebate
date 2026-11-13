-- Exact rate-limit counters for the lead router's form routes (strictLimitOk in lead-router.js).
-- k is a hash of "ip:<address>:<minute or day>" or "to:<email>:<day>": no IP or email address is stored.
-- Rows are removed by the daily cron once `expires` (Unix seconds) has passed.
-- Apply: npx wrangler d1 execute homepowerrebate-outcomes --remote --file schema-ratelimit.sql
CREATE TABLE IF NOT EXISTS rate_limits (
  k TEXT PRIMARY KEY,
  n INTEGER NOT NULL DEFAULT 0,
  expires INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS rate_limits_expires ON rate_limits (expires);
