# Installer photo Worker

Shows each installer's Google photo on its profile page (`/installers/profiles/...`) without storing anything from Google.
Google's Places policies allow storing place IDs only, so the pages carry a place ID and this Worker asks Google for the
photo each time a visitor scrolls to it. Pages always show an initials tile underneath, so nothing breaks if the Worker
is down, over its cap, or a business has no photo.

Per photo view: one Place Details request asking only for `photos` (Essentials IDs Only SKU, no charge) and one Place
Photo request (Place Details Photos SKU: 1,000 free a month, then $7 per 1,000; checked 2026-10-11). `MONTHLY_CAP`
counts Place Photo requests and stops at 1,000, so it never costs anything unless you raise it. Crawlers get no photo.

## Set up (once)
1. Google Cloud Console (same project as the roof check is fine): enable **Places API (New)**, create an API key
   restricted to Places API (New). Under the API's Quotas set a daily limit (about 100 a day for Place Photo).
2. Find the place IDs (free; run in your own terminal, never paste the key into chat):
   `python3 scripts/lookup_installer_place_ids.py` (it asks for the key; typing is hidden)
   then `git add -f data/installer-place-ids.json`.
3. `cd photo-worker && npx wrangler kv namespace create USAGE` and paste the id into wrangler.toml.
4. `npx wrangler secret put GOOGLE_API_KEY` (paste the key at the prompt) and `npx wrangler deploy`.
5. Put `https://photos.homepowerrebate.com` in `data/profile-photos/config.json` as `worker_url` (and the Google logo
   path as `google_logo`, see below), then `python3 scripts/add_profile_photos.py` and the restamp.

## Attribution (required by Google)
Under every photo: the author's name linked to their profile, a link to the photo on Google Maps, and, because there
is no Google map on the page, the Google logo. Use the official logo from Google's attribution assets
(https://developers.google.com/static/maps/documentation/images/Google_Maps_Attribution_Assets.zip), saved under
`/assets/` and named in `google_logo`. Until then the caption shows the words "Google Maps".
