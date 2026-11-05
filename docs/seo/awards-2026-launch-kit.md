# Awards 2026: launch kit (drafts, nothing sent)

Launch order (see awards-2026-plan.md): refresh ratings, notify winners (private), wait for the notice window, flip `LIVE = True` in `scripts/build_awards_2026.py`, run it, then `add_award_badges.py`, `add_award_links.py`, `python3 scripts/post_steps.py`, sitemap, merge.

What goes live with `LIVE = True`
- Winners pages (`/installers/awards/2026/...`), indexable.
- Profile-page badge block with the "Add this badge to your website" snippet (`add_award_badges.py`).
- "The 2026 Best Installers in <city>" box on each city's installer ranking pages and city hub (`add_award_links.py`).
- Still to do at launch by hand: a homepage link (`build_home.py`), footer link (`_partials/nav-footer.html`), a winners-chip on ranking cards.

## 1. Winner notice (send ~3 weeks before launch; run through no-ai-slop first; no mention of price)
Subject: You're one of the top 3 {category} installers in {city}

Hi {first name or team},

Good news. Based on Google reviews, {company} is one of the top 3 {category} installers in {city} for 2026. We rank every {city} company the same way, by rating and number of reviews, and yours came out on top.

The 2026 winners go public on {launch date}. Until then please keep it quiet.

On that day your profile page will carry a 2026 Award Winner badge: {profile url}
If you'd like to show it on your own website, there's a snippet to paste under "Add this badge to your website" on that page. It links visitors back to your profile. Once it's up, reply and tell us where, so we can say thanks.

Congratulations,
Sam, HomePowerRebate.com

Track replies in a sheet (company, date sent, replied, badge live). Suppressed addresses are already excluded from winners.

## 2. Reminder (launch day, only to winners without a link-back)
Short: "Your 2026 badge is live: {profile url}. Paste the snippet on your site when you can."

## 3. Local press line (after winners are notified; reporter list is in data/link-targets)
Subject: Who are the top-rated heat pump installers in {city}? 2026 list

{City} homeowners can now see the three top-rated heat pump installers in town, ranked by Google reviews, at {winners url}. Every {city} company on our list is ranked the same way and money never affects the order. Happy to share the data for {city} or for your region.

## 4. Link-back tracking
Weekly check: search the winners' websites for `homepowerrebate.com/installers/profiles/`; log how many link back; note in the sheet. Search Console Links export (from Sam) gives the baseline.
