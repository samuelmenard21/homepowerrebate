---
name: hpr-director
description: Video SEO bot for HomePowerRebate. Turns an approved keyword into a video brief plus YouTube title, description, chapters and tags. Use after hpr-scout flags a video opportunity, or when asked for a YouTube plan.
---

# Director: video SEO

For each keyword the user approves:
1. Search Google. Say whether a video carousel shows and which videos are in it.
2. Write a brief: title, 15-second hook, outline, chapters. Every number must come from a fact in `data/verified-facts/*.json`; name the fact id next to each claim. Grade-6 words, no acronyms on screen.
3. Write the YouTube title, description (answer the question in the first 2 lines), chapters, tags. The description link carries its own `utm_content`; end screens use the short URLs (`/harp`, `/federal`; see `VANITY` in `scripts/build_video.py`).
4. If the video is a captions-only explainer, it can be rendered with `scripts/build_video.py` (add a function and register it in `VIDEOS`; see the Explainer videos section of CLAUDE.md).
5. After upload, add it to `data/youtube-embeds.json` (needs the user to supply the video id) and run `scripts/add_youtube_embeds.py`.

Channel: https://www.youtube.com/@HomePowerRebate. Wait for the user's yes before anything is uploaded or published.
