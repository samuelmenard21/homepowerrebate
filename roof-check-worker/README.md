# Roof check Worker

Proxy for the Google Solar API and Geocoding API behind /roof-check/. It keeps the API key out of the page, counts lookups
and stops at MONTHLY_CAP (default 8,000) so the free monthly allowance (10,000 requests per API) is not exceeded.
Nothing from Google is stored or cached (Solar API policy). Google's budget alerts do not stop spending: the hard stops are this
counter and the daily quotas you set in Google Cloud.

## Deploy (once)
1. Google Cloud Console: new project, add billing, enable "Solar API" and "Geocoding API", create an API key restricted to those two APIs,
   and under each API's Quotas set the daily limit to about 250 requests.
2. `cd roof-check-worker && npx wrangler kv namespace create USAGE` and paste the printed id into wrangler.toml.
3. `npx wrangler secret put GOOGLE_API_KEY` and paste the key at the prompt (never in chat or in a file in the repo).
4. `npx wrangler deploy`
5. Put `https://roof.homepowerrebate.com` in data/roof-check/config.json as worker_url and set noindex to false, then
   `python3 scripts/build_roof_check.py` and the usual link, sitemap and registry steps.

Attribution on the page is required by Google: "Source: Includes solar data from Google" and the words "Google Maps".
