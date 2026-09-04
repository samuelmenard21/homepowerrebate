-- Adds opt-in testimonial capture to the outcomes table.
-- quote_text: free-text "how's it working out" quote (max 600 chars, enforced app-side)
-- share_consent: 1 only if the homeowner explicitly checked "you can quote me publicly"
-- display_name: only populated when share_consent = 1

ALTER TABLE outcomes ADD COLUMN quote_text TEXT DEFAULT '';
ALTER TABLE outcomes ADD COLUMN share_consent INTEGER DEFAULT 0;
ALTER TABLE outcomes ADD COLUMN display_name TEXT DEFAULT '';
