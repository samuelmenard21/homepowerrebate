#!/usr/bin/env python3
"""Homepage hero: headline, one simple find-your-city card (province, city) that opens the single get-my-plan page, then the short answer.
Replaces the old inline assessment widget. Block lives between HOME-HERO-START/END in index.html. City lists come from installer folders."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_get_quotes import REG, OV, city_slugs  # noqa: E402

S, E = "<!-- HOME-HERO-START -->", "<!-- HOME-HERO-END -->"


import html as _html  # noqa: E402
import regions  # noqa: E402

GRID_S, GRID_E = "<!-- REGION-GRID-START -->", "<!-- REGION-GRID-END -->"
CHIP = ("font-size:12px; color:var(--teal); border:1px solid var(--rule); border-radius:999px; padding:4px 10px; text-decoration:none;")
CARD = ("display:block; background:var(--paper); border:1px solid var(--rule); border-radius:16px; padding:26px; text-decoration:none; "
        "transition:all .2s; box-shadow:var(--shadow);")


def _short(r):
    return "BC" if r["code"] == "bc" else r["name"]


def _series(names):
    return ", ".join(names[:-1]) + ", and " + names[-1]


def region_grid():
    """The homepage "Choose your region" cards: one per region in data/regions.json (name, home_blurb, city count, first cities)."""
    cards = []
    for r in regions.REGIONS:
        n = len(city_slugs(r["code"]))
        country = "Canada" if r["country"] == "ca" else "United States"
        chips = "".join(f'<a href="{h}" onclick="event.stopPropagation()" style="{CHIP}">{_html.escape(t)}</a>\n        ' for h, t in r["cities"][:4])
        cards.append(f'''    <div style="{CARD}">
      <div class="is-1f3bab59">{country} &middot; {n} {"city" if n == 1 else "cities"}</div>
      <h3 class="is-ab1b25e3"><a href="/{r["path"]}/" class="is-48711be5">{_html.escape(r["name"])}</a></h3>
      <p class="is-26757191">{_html.escape(r.get("home_blurb") or "")}</p>
      <div class="is-f1e97509">
        {chips}</div>
    </div>''')
    return GRID_S + '\n  <div class="region-grid is-c0839a60">\n' + "\n".join(cards) + "\n  </div>\n" + GRID_E


def sync_regions(s):
    """Everything on the homepage that names regions or counts cities, rebuilt from data/regions.json (idempotent):
    meta and JSON-LD region lists, areaServed, the page count, and the region cards."""
    names = [r["name"] for r in regions.REGIONS]
    canada = [r for r in regions.REGIONS if r["country"] == "ca"]
    us = [r for r in regions.REGIONS if r["country"] == "us"]
    alt = "|".join(re.escape(x) for x in sorted(set(names + ["BC", "British Columbia"]), key=len, reverse=True))
    run = re.compile(rf"(?:BC|British Columbia), (?:(?:{alt}), )+(?:and )?(?:{alt})(?![A-Za-z])")
    s = run.sub(lambda m: _series([("British Columbia" if m.group(0).startswith("British") and r["code"] == "bc" else _short(r)) for r in canada + us]), s)
    # areaServed: every run of AdministrativeArea objects, rewritten in the style it was written in
    area = re.compile(r'(\{ ?"@type": "AdministrativeArea", "name": "[^"]+" ?\})((?:,\s*\{ ?"@type": "AdministrativeArea", "name": "[^"]+" ?\})+)')

    def redo(m):
        first = m.group(1)
        sep = re.match(r",\s*", m.group(2)).group(0)
        tpl = first.replace(re.search(r'"name": "([^"]+)"', first).group(1), "{}")
        return sep.join(tpl.replace("{}", f'{r["name"]}, {"Canada" if r["country"] == "ca" else "United States"}') for r in canada + us)
    s = area.sub(redo, s)
    total = sum(len(city_slugs(r["code"])) for r in regions.REGIONS)
    s = re.sub(r"Covers \d+ city and utility-territory pages", f"Covers {total} city and utility-territory pages", s)
    if GRID_S in s:
        s = s[:s.index(GRID_S)] + region_grid() + s[s.index(GRID_E) + len(GRID_E):]
    else:
        a = s.index('<div class="region-grid is-c0839a60">')
        depth, end = 0, None
        for m in re.finditer(r"<div\b|</div>", s[a:]):
            depth += -1 if m.group(0) == "</div>" else 1
            if depth == 0:
                end = a + m.end()
                break
        s = s[:a] + region_grid() + s[end:]
    return s


def main():
    f = ROOT / "index.html"
    s = f.read_text(encoding="utf-8")
    data = []
    for code, name, prov, _ in REG:
        cities = city_slugs(code)
        data.append({"c": code, "n": name, "k": [[c, OV.get(c, c.replace("-", " ").title())] for c in cities]})
    if S in s:
        a = s.index('<div class="quick-answer">', s.index(S))
        qa = s[a:s.index('<div class="hero-trust-line">', a)]
    else:
        a = s.index('<div class="quick-answer">')
        b = s.index("<!-- INLINE ASSESSMENT WIDGET -->")
        qa = s[a:b].strip() + "\n"
    qa = re.sub(r'<p class="hero-sub">.*?</p>', "", qa, flags=re.S)
    new = f"""{S}
<style>
#hero-find{{max-width:640px;margin:20px auto 8px;background:var(--paper);color:var(--ink);border-radius:16px;padding:22px 22px 20px;text-align:left;box-shadow:0 20px 48px rgba(0,0,0,.18)}}
#hero-find .hf-row{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
#hero-find label{{display:block;font-size:13px;font-weight:600;margin-bottom:5px;color:var(--ink-soft)}}
#hero-find select{{width:100%;min-height:48px;padding:10px 12px;border:1.5px solid var(--rule);border-radius:9px;font-family:'Inter Tight',sans-serif;font-size:16px;background:#fff;color:var(--ink)}}
#hero-find button{{width:100%;margin-top:14px;min-height:50px;border:0;border-radius:999px;background:var(--amber);color:#fff;font-family:'Inter Tight',sans-serif;font-weight:700;font-size:16px;cursor:pointer}}
.hero-fed{{display:inline-flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:4px 10px;max-width:640px;margin:0 auto 18px;padding:9px 16px;border-radius:999px;background:rgba(232,138,46,.16);border:1px solid rgba(232,138,46,.55);color:inherit;font-size:15px;line-height:1.4;text-decoration:none}}
.hero-fed b{{padding:2px 9px;border-radius:999px;background:var(--amber-bright);color:var(--ink);font-size:12px;letter-spacing:.04em;text-transform:uppercase}}
.hero-fed span{{font-weight:700;text-decoration:underline;text-underline-offset:3px}}
.hero-fed:hover{{background:rgba(232,138,46,.26)}}
@media(max-width:600px){{.hero-fed{{border-radius:14px;font-size:14px}}}}
#hero-find .hf-note{{font-size:13px;color:var(--ink-soft);margin:10px 0 0;text-align:center}}
@media(max-width:600px){{#hero-find .hf-row{{grid-template-columns:1fr}}#hero-find{{order:2}}}}
@media(max-width:600px){{.hero-trust-line{{flex-direction:column;align-items:center;gap:4px;flex-wrap:wrap}}.hero-trust-line span.dot{{display:none}}.hero-trust-line span{{white-space:normal}}}}
</style>
<section class="hero">
  <div class="hero-eyebrow"><span class="hero-eyebrow-dot"></span>Canada &amp; US &middot; {sum(len(r["k"]) for r in data)} cities &middot; Checked monthly</div>
  <a class="hero-fed" href="#federal-alert"><b>New in Canada</b> Ottawa's heat pump rebate: up to $10,000, opening early 2027. <span>Get the launch email &darr;</span></a>
  <h1 class="hero-h1">Find every home energy rebate <em>for your city.</em></h1>
  <p class="hero-sub">See what you could get back and who to call. Free, no sales calls.</p>
  <form id="hero-find" action="/get-quotes/" method="get">
    <div class="hf-row">
      <div><label for="hf-prov">Province or state</label><select id="hf-prov" name="province" required><option value="">Choose one</option></select></div>
      <div><label for="hf-city">City</label><select id="hf-city" name="city" required><option value="">Choose your city</option></select></div>
    </div>
    <button type="submit">Show my rebates and installers &rarr;</button>
    <p class="hf-note">Takes 20 seconds. No email needed to see the numbers.</p>
  </form>
  {qa.strip()}
  <div class="hero-trust-line"><span>Checked against official program pages</span><span class="dot"></span><span>Installers ranked by Google reviews</span><span class="dot"></span><span>Nobody pays to be listed</span></div>
</section>
<script>(function(){{var D=window.HPR_CITIES={json.dumps(data, separators=(",", ":"))};var p=document.getElementById("hf-prov"),c=document.getElementById("hf-city");
D.forEach(function(r){{var o=document.createElement("option");o.value=r.c;o.textContent=r.n;p.appendChild(o)}});
p.addEventListener("change",function(){{c.textContent="";var h=document.createElement("option");h.value="";h.textContent="Choose your city";c.appendChild(h);
var r=D.filter(function(x){{return x.c===p.value}})[0];if(r)r.k.forEach(function(k){{var o=document.createElement("option");o.value=k[0];o.textContent=k[1];c.appendChild(o)}})}});}})();</script>
{E}"""
    if S in s:
        s = re.sub(re.escape(S) + ".*?" + re.escape(E), lambda m: new, s, count=1, flags=re.S)
    else:
        a = s.index('<section class="hero">')
        b = s.index("</section>", s.index("Takes 20 seconds", a)) + len("</section>")
        s = s[:a] + new + s[b:]
        # drop the old inline-widget script (it references elements that no longer exist)
        i = s.index("var provinceSelect = $('hpr-province');")
        a = s.rfind("<script>", 0, i)
        b = s.index("</script>", i) + len("</script>")
        s = s[:a] + s[b:]
    s = sync_regions(s)
    f.write_text(s, encoding="utf-8")
    print("Homepage hero rebuilt")


if __name__ == "__main__":
    main()
