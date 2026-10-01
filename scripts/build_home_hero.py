#!/usr/bin/env python3
"""Homepage hero: headline, one simple find-your-city card (province, city) that opens the single get-my-plan page, then the short answer.
Replaces the old inline assessment widget. Block lives between HOME-HERO-START/END in index.html. City lists come from installer folders."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_get_quotes import REG, OV  # noqa: E402

S, E = "<!-- HOME-HERO-START -->", "<!-- HOME-HERO-END -->"


def main():
    f = ROOT / "index.html"
    s = f.read_text(encoding="utf-8")
    data = []
    for code, name, prov, _ in REG:
        base = ROOT / "installers" / code
        cities = sorted(p.name for p in base.iterdir() if p.is_dir()) if base.exists() else []
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
#hero-find .hf-note{{font-size:13px;color:var(--ink-soft);margin:10px 0 0;text-align:center}}
@media(max-width:600px){{#hero-find .hf-row{{grid-template-columns:1fr}}#hero-find{{order:2}}}}
</style>
<section class="hero">
  <div class="hero-eyebrow"><span class="hero-eyebrow-dot"></span>Canada &amp; US &middot; 123 cities &middot; Checked monthly</div>
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
<script>(function(){{var D={json.dumps(data, separators=(",", ":"))};var p=document.getElementById("hf-prov"),c=document.getElementById("hf-city");
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
    f.write_text(s, encoding="utf-8")
    print("Homepage hero rebuilt")


if __name__ == "__main__":
    main()
