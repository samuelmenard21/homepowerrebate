#!/usr/bin/env python3
"""YouTube embeds, 2026-10-23: the 30 second video next to the page it explains, with a watch-on-YouTube and subscribe box. Config in
data/youtube-embeds.json (video id, name, length, upload date, pages). Privacy-friendly embed (youtube-nocookie, lazy), plus VideoObject JSON-LD
(name, description, thumbnail, embed URL, upload date, duration) so the page can show the video in search. Marker-wrapped (YT-EMBED-START/END),
idempotent, a post-step. Styles (.yt-embed) live once in _partials/nav-footer.html.
Usage: python3 scripts/add_youtube_embeds.py   (git add -f data/youtube-embeds.json)"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S, E = "<!-- YT-EMBED-START -->", "<!-- YT-EMBED-END -->"
SITE = "https://homepowerrebate.com"


def upload_date(d):
    """Google wants a time zone on uploadDate; a bare date is flagged."""
    return d if "T" in d else d + "T12:00:00-07:00"


def block(cfg, v, path, heading=None):
    v = {**v, "heading": heading or v["heading"]}
    sub = cfg["channel"] + "?sub_confirmation=1&utm_source=homepowerrebate&utm_medium=embed&utm_campaign=" + v["id"]
    watch = f"https://www.youtube.com/shorts/{v['id']}"
    ld = {"@context": "https://schema.org", "@type": "VideoObject", "name": v["name"], "description": v["description"],
          "thumbnailUrl": [f"https://i.ytimg.com/vi/{v['id']}/hqdefault.jpg"], "uploadDate": upload_date(v["uploaded"]), "duration": v["duration"],
          "embedUrl": f"https://www.youtube-nocookie.com/embed/{v['id']}", "contentUrl": watch, "inLanguage": "en",
          "publisher": {"@id": f"{SITE}/#org"}}
    tr = ""
    if v.get("transcript"):
        tr = ('<details class="yt-transcript"><summary>Read what the video says</summary>'
              + "".join(f"<p>{html.escape(line)}</p>" for line in v["transcript"]) + "</details>")
    return (f'{S}<section class="yt-embed" aria-label="{html.escape(v["heading"])}">'
            f'<div class="yt-frame"><iframe src="https://www.youtube-nocookie.com/embed/{v["id"]}?rel=0" title="{html.escape(v["name"])}" loading="lazy" '
            'allow="accelerometer; encrypted-media; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>'
            f'<div class="yt-text"><p class="yt-h">{html.escape(v["heading"])}</p><p>{html.escape(v["description"])}</p>'
            f'<p class="yt-links"><a href="{watch}" rel="noopener">Watch on YouTube</a> <a href="{sub}" rel="noopener">Subscribe</a></p>{tr}</div>'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script></section>{E}')


def main():
    cfg = json.loads((ROOT / "data" / "youtube-embeds.json").read_text(encoding="utf-8"))
    changed = 0
    for v in cfg["videos"]:
        for pg in v["pages"]:
            f = ROOT / pg["path"].strip("/") / "index.html"
            if not f.exists():
                print("missing page:", pg["path"])
                continue
            s = f.read_text(encoding="utf-8")
            s2 = re.sub(re.escape(S) + ".*?" + re.escape(E) + r"\n?", "", s, flags=re.S)
            a = s2.find("<article")
            end = s2.rfind("</article>")
            if a < 0 or end < 0:
                print("no article:", pg["path"])
                continue
            if pg["where"] == "top":
                at = s2.find("<h2", a)
                at = at if 0 < at < end else end
            else:
                at = end
            s2 = s2[:at] + block(cfg, v, pg["path"], pg.get("heading")) + "\n" + s2[at:]
            if s2 != s:
                f.write_text(s2, encoding="utf-8")
                changed += 1
    print("pages changed", changed)


if __name__ == "__main__":
    main()
