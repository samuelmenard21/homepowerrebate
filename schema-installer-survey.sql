-- 2026 installer survey answers (/installers/survey/ -> Worker /installer-survey).
CREATE TABLE IF NOT EXISTS installer_survey (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  company TEXT NOT NULL,
  email TEXT NOT NULL,
  region TEXT NOT NULL,
  city TEXT,
  services TEXT,
  quote_ok INTEGER DEFAULT 0,
  mark_ok INTEGER DEFAULT 0,
  answers TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_survey_region ON installer_survey(region);
