# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Homeowners in Canada (BC, Ontario, Alberta, Nova Scotia, Newfoundland and Labrador) and the US (California, Massachusetts, New York, Pennsylvania, Colorado, Vermont, Michigan, New Jersey, Illinois, Washington, Minnesota) who are thinking about a heat pump, solar, battery, insulation, windows, water heater, EV charger or smart thermostat. They are not experts, often on a phone, and they arrive unsure what they qualify for and wary of being sold to. Their job: find out what money is really open for their home, then find someone trustworthy to do the work.

## Product Purpose
HomePowerRebate shows every home energy rebate open in a homeowner's city, each with its status, the official source and the date it was last checked, and ranks the top-rated local installers by Google reviews. Success: a visitor picks their city and sees their real numbers; Canadians also sign up to hear when the National Heat Pump Rebate opens (early 2027), which is the company's top metric until launch.

## Positioning
Independent and sourced. Every amount comes from a verified facts file with a status (open, starts soon, paused, closed) and a source link, and is re-read monthly. Closed programs are shown as closed. Installer rankings use Google reviews only; nobody pays to be listed and money never affects rankings. Free for homeowners and, for now, for installers.

## Operating Context
Static HTML on Cloudflare Pages, generated at scale (2,000+ pages) by Python generators; shared nav, footer and CSS come from partials and are restamped. The homepage's city finder sends people to `/get-quotes/`. Regions and cities come only from `data/regions.json`; amounts only from `data/verified-facts/*.json`.

## Capabilities and Constraints
- Plain HTML, CSS and vanilla JS; no frameworks or build tools.
- New .js/.json files 403 at Cloudflare unless allow-listed; inline what a page needs.
- Never state an amount that is not in a facts file; never show a closed program as open.
- Glossary (`_partials/glossary.json`) fixes button labels: "See my rebates" goes to the rebate finder; "Request my quotes" is only for installer forms. We never ask for energy bills.
- Federal heat pump rebate: no income line, retroactivity or start date until an official page says so.

## Brand Commitments
Name HomePowerRebate, with "Power" in amber in the wordmark. Voice: Grade-6, warm, honest ("we tell you when the math doesn't work"), never salesy. Founder byline: Sam Menard (/about). Visual system in DESIGN.md ("The Honest Ledger").

## Evidence on Hand
Verified facts per region (`data/verified-facts/*.json`), PowerScore city scores (`data/powerscore*.json`), the rebate change feed (`rebate-tracker/changes.json`), Google-review installer rankings (`installers/json`). No testimonials, customer counts or savings case studies exist; do not invent them.

## Product Principles
1. The amount and its status come first; the source is always one tap away.
2. Show what's closed, not just what's open. Honesty is the product.
3. One region list, one facts store, one shared component; never patch a single page.
4. Canada and the US are equal citizens: no region is the default or the afterthought.

## Accessibility & Inclusion
Grade-6 copy; 13px minimum text; 44px tap targets; status in words, never colour alone; designed at 390px first.
