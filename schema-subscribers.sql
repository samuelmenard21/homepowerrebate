-- HomePowerRebate: results-drip subscribers table
-- Powers the "email my breakdown" capture on the homepage assessment widget.
-- Apply with: wrangler d1 execute homepowerrebate-outcomes --remote --file=schema-subscribers.sql

CREATE TABLE IF NOT EXISTS subscribers (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,

  -- calculator context, captured at signup, refreshed on repeat visits
  city TEXT,
  province TEXT NOT NULL DEFAULT 'BC',
  heating TEXT,
  income TEXT,
  estimate TEXT,
  source TEXT,

  -- drip state — step is which email is NEXT due (1 = local comparison, 2 = lock-in nudge, 3 = done)
  step INTEGER NOT NULL DEFAULT 1,
  next_send_at TEXT,
  unsubscribed INTEGER NOT NULL DEFAULT 0,

  created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_subscribers_email ON subscribers(email);
CREATE INDEX IF NOT EXISTS idx_subscribers_due ON subscribers(unsubscribed, step, next_send_at);
