-- Migration: add other_categories to existing outcomes table (safe to re-run).
-- Apply with: wrangler d1 execute homepowerrebate-outcomes --remote --file=schema-outcomes-add-other-categories.sql
ALTER TABLE outcomes ADD COLUMN other_categories TEXT;
