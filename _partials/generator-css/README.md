# Frozen page CSS for the shared `shell()` generators

`scripts/build_furnace_pages.py` `shell()` is used by about 17 generators (calculators, program pages, furnace, battery, technology, rebate tracker, strata, search, survey and others). It used to import `CSS` from `build_installer_rankings.py`, so every ranking-page redesign silently changed what those generators would emit, while their live pages kept the older copy. Re-running a generator then changed a page's design and dropped its registered template variant.

These files are the exact CSS those pages were built with, frozen (2026-10-11):

- `2026-10-09.css`: default (calculators, program pages, furnace, technology, rebate tracker, thermostat hub, strata, CA regions)
- `2026-09-29.css`: battery guides, insulation hub, installer survey, search, net metering post, NS heat pump water heater
- `2026-09-28.css`: solar quote checker

A generator picks one with `shell(..., css=page_css("2026-09-29"))`. Never edit these files in place: the restamp matches pages to `_partials/templates/variants.json` by a hash of this CSS. To change the design of these pages, change their template family CSS (`_partials/templates/*.css`) instead. `python3 scripts/check_generator_sync.py` re-runs every shell generator in a scratch worktree and fails if any page would change.
