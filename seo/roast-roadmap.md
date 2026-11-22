# SEO Roast Roadmap: homepowerrebate.com (2026-11-22)

Verdict: Nothing blocks crawling or indexing. The problem is whether Google chooses to show the site, not whether it can see it.

Method: `seo-roast` six-point procedure, run against production and the repo on 2026-11-22. Not run (no tool access): backlink and domain-rating comparison (point 4), URL Inspection per money page, and a viewport layout test (3a).

| # | Tier | Issue | Revenue impact | Fix | Owner | Status |
|---|---|---|---|---|---|---|
| 1 | COMPOUNDING | Impressions flip between about 2,000 a day and under 160 (Nov 15 to 16 off, Nov 17 to 19 on) | Organic signups swing with it; the cause is outside the site's code | Hold new pages; re-check with `gsc_onoff_check.py` after Nov 22 | Sam | open |
| 2 | REVENUE | `/programs/national-heat-pump-rebate/do-i-qualify/` has 4 contextual inbound links; the pillar has 501 | The page that turns Ottawa's published rules into a signup gets little traffic | Link it from the 48 Canadian heat pump pages and the federal articles via `add_federal_links.py` | agent | next |
| 3 | REVENUE | `/installers/heat-pump/` (the page meant to rank for "heat pump installers near me") has 63 inbound links | Smaller than the other money pages (get-quotes 1,100, calculators 445) | Add it to the "Related pages" box on city heat pump pages through `link_discovered.py` | agent | next |
| 4 | REVENUE | 4 pages have no contextual inbound link, 36 have fewer than 3 | Pages that cannot be found by crawl or by visitors | See the weak list in `seo/internal-links-report.md` | agent | next |
| 5 | COMPOUNDING | Clean editorial links to the site are unmeasured here | Ranking on competitive terms | Pull referring domains in Ahrefs or Search Console links report monthly | Sam | open |

## Passed (no action)
- robots.txt blocks only five old template files and lists the sitemap. OAI-SearchBot, PerplexityBot, Claude-SearchBot, GPTBot, ClaudeBot, Googlebot and Bingbot all get 200.
- Missing pages return 404 at the top level and nested (`/ca/bc/nope`, `/ca/bc/kelowna/nope`).
- Locales: 6 French pages (Quebec and New Brunswick hubs, Montreal, Quebec City, Moncton) have reciprocal hreflang with x-default. This is under the 3-locale limit and fully translated.
- Rebate amounts (`$1,000`, `$10,000`, `$13,000`...) are in the raw HTML for GPTBot, OAI-SearchBot, PerplexityBot and ClaudeBot.
- Counts agree: 23 regions in `data/regions.json`, the homepage and `llms.txt`; 161 cities on the homepage.
- `www` and `http` all reach the bare https host in one hop (fixed in Cloudflare 2026-11-22).
- Share cards fixed on 47 pages (PR 266).

## Fluff (ignore until rows above ship)
- `/bc.html` and `/ca/bc/kelowna.html` return 404, not a redirect. They are not in the sitemap and no page links to them.
- Five old template files at the site root are disallowed in robots.txt and still deploy; they could be deleted.
