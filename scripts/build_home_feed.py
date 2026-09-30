#!/usr/bin/env python3
"""Homepage 'What changed' feed + calculator strip, generated from rebate-tracker/changes.json (built from verified facts).
Replaces the old generic FAQ. Block sits between HOME-FEED-START/END in index.html."""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S, E = "<!-- HOME-FEED-START -->", "<!-- HOME-FEED-END -->"
PILL = {"coming": ("Coming up", "#fdeccf", "#8a4a06"), "new": ("New", "#e3f1e8", "#1f5a3d"), "raised": ("Raised", "#e3f1e8", "#1f5a3d"),
        "changed": ("Changed", "#e8e8e8", "#444"), "cut": ("Cut", "#f3dcdc", "#8a2b2b"), "paused": ("Paused", "#fdeccf", "#8a4a06"), "ended": ("Ended", "#f3dcdc", "#8a2b2b")}
REGION = {"BC": "British Columbia", "ON": "Ontario", "AB": "Alberta", "NS": "Nova Scotia", "MA": "Massachusetts", "NY": "New York", "CA": "California",
          "PA": "Pennsylvania", "CO": "Colorado", "VT": "Vermont", "US": "United States", "CA-FED": "Canada"}
HUB = {"BC": "/ca/bc/", "ON": "/ca/on/", "AB": "/ca/ab/", "NS": "/ca/ns/", "MA": "/us/ma/", "NY": "/us/ny/", "CA": "/us/ca/", "PA": "/us/pa/", "CO": "/us/co/", "VT": "/us/vt/"}


def item(x):
    lab, bg, fg = PILL[x["status"]]
    reg = html.escape(REGION.get(x["region"], x["region"]))
    link = f'<a href="{HUB[x["region"]]}">{reg}</a>' if x["region"] in HUB else reg
    when = html.escape(x["date"])
    return (f'<li class="hf-i"><span class="hf-pill" style="background:{bg};color:{fg}">{lab}</span>'
            f'<div><b>{html.escape(x["program"])}</b> <span class="hf-m">{link} &middot; {when}</span>'
            f'<p>{html.escape(x["change"])}</p></div></li>')


def main():
    d = json.loads((ROOT / "rebate-tracker" / "changes.json").read_text())["entries"]
    coming = sorted([x for x in d if x["status"] == "coming"], key=lambda x: x["date"])
    recent = sorted([x for x in d if x["status"] != "coming"], key=lambda x: x["date"], reverse=True)[:5]
    items = "".join(item(x) for x in coming + recent)
    checked = json.loads((ROOT / "rebate-tracker" / "changes.json").read_text())["checked"]
    block = f"""{S}
<style>.hf-i{{display:flex;gap:14px;align-items:flex-start;padding:14px 0;border-top:1px solid #e5e0d6;list-style:none}}
.hf-i p{{margin:4px 0 0;font-size:15px;line-height:1.5;color:#1a3d42}}.hf-m{{font-size:13px;color:#4a5f5b;white-space:nowrap}}
.hf-pill{{flex:none;min-width:78px;text-align:center;padding:2px 10px;border-radius:99px;font-size:12px;font-weight:700}}
.hf-strip{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-top:36px}}
.hf-strip a{{display:block;text-decoration:none;background:#fff;border:1px solid #d9d0c1;border-radius:12px;padding:18px;color:#0a2a2e}}
.hf-strip b{{display:block;font-family:'Fraunces',Georgia,serif;font-size:19px;margin-bottom:4px}}
@media(max-width:600px){{.hf-i{{flex-direction:column;gap:6px}}.hf-m{{white-space:normal}}}}</style>
<section style="max-width:800px;margin:0 auto;padding:64px 24px;">
  <p style="font-size:13px;text-transform:uppercase;letter-spacing:.08em;font-weight:700;color:#d4751c;margin:0 0 8px;">What changed</p>
  <h2 style="font-family:'Fraunces',Georgia,serif;font-size:clamp(28px,4vw,36px);margin:0 0 6px;color:var(--ink);">Rebates are opening and closing</h2>
  <p style="color:#4a5f5b;margin:0 0 14px;">Every item is checked against the program's own page. Last checked {html.escape(checked)}.</p>
  <ul style="padding:0;margin:0;">{items}</ul>
  <p style="margin-top:16px;"><a href="/rebate-tracker/"><b>See every change &rarr;</b></a></p>
  <div class="hf-strip">
    <a href="/calculator/"><b>Rebate calculators</b>Pick your province or state and see what you could get back.</a>
    <a href="/powerscore/"><b>PowerScore</b>See how your city ranks on open rebate money.</a>
    <a href="/how-we-vet-installers"><b>How we rank installers</b>Google reviews only. Free for you, and nobody pays to be listed.</a>
  </div>
</section>
{E}"""
    f = ROOT / "index.html"
    s = f.read_text(encoding="utf-8")
    if S in s:
        s = re.sub(re.escape(S) + ".*?" + re.escape(E), lambda m: block, s, count=1, flags=re.S)
    else:
        a = s.index("<!-- FAQ -->")
        b = s.index("</script>", s.index('"@type": "FAQPage"', a)) + len("</script>")
        s = s[:a] + block + s[b:]
    f.write_text(s, encoding="utf-8")
    print("Home feed:", len(coming), "coming +", len(recent), "recent")


if __name__ == "__main__":
    main()
