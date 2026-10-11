# What to send installers

Updated 2026-10-11. The old paid-partner pitches are in `archive/old-installer-model/`; don't send them.

Don't mention price or "free" at all in installer copy. Nothing costs anything, so there's no need to say it, and we never promise anything about the future.

## The two ways installers can link to us

1. **Top-rated installer badge:** https://homepowerrebate.com/installers/badge/
   They pick their province or state, city and service, then copy the code. To skip the picking, link straight to their badge with `?r=<region>&c=<city-slug>&s=<service>`, e.g. https://homepowerrebate.com/installers/badge/?r=bc&c=kelowna&s=heat-pump (the `badge_page` column in `data/outreach-rankings.csv` has this link for every installer after the next full `build_installer_rankings.py` run). Only companies listed on that ranking can use its badge.
2. **Rebate calculator for their website:** https://homepowerrebate.com/calculator/widget/
   An iframe they paste in. We ask them to keep the "Rebate calculator by HomePowerRebate" link under it.

## Message

> Hi [Name], your company is one of the top-rated [heat pump] installers in [City] on HomePowerRebate. The ranking comes from your Google reviews: [ranking page link].
>
> If you'd like to show it, your badge is here: homepowerrebate.com/installers/badge/. Pick your city, copy the code and paste it into your site. Showing it doesn't change your rank.
>
> You can also add our rebate calculator to your site so customers can see which rebates they qualify for: homepowerrebate.com/calculator/widget/
>
> Sam, HomePowerRebate
