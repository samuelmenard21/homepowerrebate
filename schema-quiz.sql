-- HomePowerRebate: aggregate quiz answer counts (one row per quiz section id and question number).
-- Counts only: how many answered right and how many wrong. No IP, cookie, email or person is stored.
-- Apply with: wrangler d1 execute homepowerrebate-outcomes --remote --file=schema-quiz.sql
CREATE TABLE IF NOT EXISTS quiz_stats (
  quiz TEXT NOT NULL,
  q INTEGER NOT NULL,
  right_n INTEGER NOT NULL DEFAULT 0,
  wrong_n INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (quiz, q)
);
