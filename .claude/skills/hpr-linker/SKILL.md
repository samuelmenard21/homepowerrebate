---
name: hpr-linker
description: Backlink prospecting bot for HomePowerRebate. Finds 45+ sites that cover a topic or mention the brand without linking, keeps the best 10 and drafts short personal emails. Never sends. Use for link building and digital-PR ideas.
---

# Linker: backlinks (drafts only)

For the page the user names:
1. Find 45+ real sites writing on the topic (local news, utility and municipal sites, energy-advisor and homeowner blogs, climate and housing nonprofits, associations) plus sites that mention "HomePowerRebate" without linking (search the brand and `homepowerrebate.com`).
2. Check each: real site, relevant, actively published, contact found. Drop anything on `outreach/suppress.txt` or `data/installer-blocklist.json`.
3. Keep the best 10. For each: site, page, why it fits, contact.
4. Draft an email to each: under 100 words, one specific line about their page, no template feel, say who Sam Menard is, never mention fees or "free" for installers, no pressure. Run drafts through `no-ai-slop`.
5. Lead with assets worth linking: the monthly data release (`/data-release/`), PowerScore leaderboard, open dataset (`build_dataset_export.py`), federal partner kit and calculator embed.

Save results as a table in the scratchpad or `outreach/` drafts. Never send an email or create a Gmail draft without the user's approval; outreach sends go through `outreach/` tooling only after yes.
