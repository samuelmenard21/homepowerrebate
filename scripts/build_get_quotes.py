#!/usr/bin/env python3
"""Rebuild the main content and script of /get-quotes/ (between GQ-START and GQ-END). Nav and footer stay stamped by the shared partial.
Region and city lists come from the installer folders on disk, so a new city appears here on the next build."""
import glob
import json
import os
import re
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import regions
ROOT = Path(__file__).resolve().parent.parent
S, E = "<!-- GQ-START -->", "<!-- GQ-END -->"
REG = [(r["code"], r["name"], r["abbr"], "" if r["code"] == "bc" else r["code"]) for r in regions.REGIONS]
OV = {"st-albert": "St. Albert", "fort-st-john": "Fort St. John", "fort-mcmurray": "Fort McMurray", "sault-ste-marie": "Sault Ste. Marie"}
CSS = """
.gq{max-width:820px;margin:0 auto;padding:0 20px}
.gq-card{background:#fff;border:1px solid var(--rule);border-radius:16px;padding:24px;margin:0 0 20px}
.gq-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.gq-row>*{min-width:0}.gq-f{display:flex;flex-direction:column;gap:6px}.gq-f.full{grid-column:1/-1}
.gq-f label{font-size:13px;font-weight:700;color:var(--ink-soft)}
.gq-f input,.gq-f select{font:inherit;font-size:16px;min-height:46px;padding:9px 12px;border:1px solid var(--rule);border-radius:8px;background:var(--paper);color:var(--ink);width:100%}
.gq-chips{display:flex;flex-wrap:wrap;gap:8px}.gq-chip{display:inline-flex;align-items:center;gap:6px;min-height:44px;padding:0 14px;border:1px solid var(--rule);border-radius:99px;background:#fff;cursor:pointer;font-size:15px}
.gq-chip input{accent-color:var(--amber);width:18px;height:18px}.gq-chip.on{border-color:var(--amber);background:#fff6ea}
.gq-cta{display:inline-block;background:var(--amber);color:#fff;text-decoration:none;font-weight:700;border-radius:999px;padding:14px 24px;border:0;font:inherit;font-weight:700;cursor:pointer}
.gq-cta[disabled]{opacity:.5;cursor:not-allowed}.gq-alt{display:inline-block;margin-left:14px;font-weight:600}
.gq-inst{display:grid;grid-template-columns:1fr auto;gap:10px 16px;padding:14px 0;border-top:1px solid var(--rule);align-items:start}
.gq-inst:first-of-type{border-top:0}.gq-inst h4{margin:0;font-size:17px}.gq-meta{font-size:14px;color:var(--ink-soft)}
.gq-links{display:flex;gap:14px;flex-wrap:wrap;font-size:15px;margin-top:4px}
.gq-pick{display:flex;align-items:center;gap:8px;font-size:14px;white-space:nowrap}.gq-pick input{width:20px;height:20px;accent-color:var(--amber)}
.gq-h{font-family:'Fraunces',serif;font-size:22px;color:var(--teal-deep);margin:0 0 6px}.gq-sub{font-size:14px;color:var(--ink-soft);margin:0 0 10px}
.gq-msg{margin-top:14px;padding:14px 16px;border-radius:8px;font-size:15px;display:none}.gq-msg.show{display:block}.gq-msg.ok{background:#eaf3ee;color:#1f5a3d}.gq-msg.err{background:#fef3e6;color:#8a4a06}
.gq details summary{cursor:pointer;font-weight:700;font-size:17px}
@media(max-width:600px){.gq-row{grid-template-columns:1fr}.gq-inst{grid-template-columns:1fr}.gq-card{padding:18px}}
"""
JS = r"""
(function(){
var D=__DATA__;
var $=function(id){return document.getElementById(id)};
var P=new URLSearchParams(location.search);
var UPG=[["heat-pump","\uD83D\uDD25","Heat pump","Replaces a furnace or baseboards \u2014 heats and cools with one machine."],["solar","\u2600\uFE0F","Solar panels","Rooftop solar, typically 8\u201312 kW for a home."],["battery","\uD83D\uDD0B","Home battery","Backup power, and pairs well with solar."],["insulation","\uD83C\uDFE0","Insulation","Attic, walls, or crawlspace \u2014 often the best first upgrade."],["water-heater","\uD83D\uDCA7","Heat pump water heater","Replaces an electric or gas tank."],["windows","\uD83D\uDFEB","Windows & doors","Energy-efficient replacements."],["ev","\uD83D\uDE97","EV charger","Home Level 2 charger installation."],["thermostat","\uD83D\uDCF1","Smart thermostat","Nest, Ecobee, or similar."]];
var chipBox=$("gq-chips");
UPG.forEach(function(u){var l=document.createElement("label");l.className="check-item";var c=document.createElement("input");c.type="checkbox";c.value=u[0];
 c.addEventListener("change",show);l.appendChild(c);var sp=document.createElement("span");sp.className="check-label";var h=document.createElement("h4");h.textContent=u[1]+" "+u[2];var p=document.createElement("p");p.textContent=u[3];sp.appendChild(h);sp.appendChild(p);l.appendChild(sp);chipBox.appendChild(l)});
var rs=$("gq-region"),cs=$("gq-city");
D.forEach(function(r){var o=document.createElement("option");o.value=r.code;o.textContent=r.name;rs.appendChild(o)});
function fillCities(){cs.textContent="";var ph=document.createElement("option");ph.value="";ph.textContent="Choose your city";cs.appendChild(ph);
 var r=D.filter(function(x){return x.code===rs.value})[0];if(!r)return;r.cities.forEach(function(c){var o=document.createElement("option");o.value=c[0];o.textContent=c[1];cs.appendChild(o)})}
rs.addEventListener("change",function(){fillCities();show()});cs.addEventListener("change",show);
var prov=(P.get("province")||"").toLowerCase();if(prov&&D.some(function(r){return r.code===prov})){rs.value=prov;fillCities();var cc=(P.get("city")||"").toLowerCase().replace(/\s+/g,"-");cs.value=cc;if(cs.value!==cc)cs.value=""}
var shown=[];
function slug(n){return n.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"")}
function purl(r,city,ps){return "/installers/profiles/"+(r.jsonDir?r.jsonDir+"/":"")+city+"/"+ps+"/"}
function stars(i){return (i.rating?i.rating.toFixed(1)+" ★":"")+(i.reviews?" ("+i.reviews+" Google reviews)":"")}
function get(url){return fetch(url).then(function(r){return r.ok?r.json():[]}).catch(function(){return []})}
var token=0;
function show(){
 var out=$("gq-out");var r=D.filter(function(x){return x.code===rs.value})[0];var city=cs.value;
 var plan=[].map.call(document.querySelectorAll("#gq-chips input:checked"),function(c){return c.value});
 if(!r||!city){out.style.display="none";return}
 out.style.display="block";var label=cs.options[cs.selectedIndex].textContent;var t=++token;
 $("gq-r-title").textContent="Rebates in "+label;
 var q="?city="+encodeURIComponent(city)+(plan.length?"&plan="+plan.join(","):"");
 $("gq-calc").href="/calculator/"+r.code+"/"+q;
 $("gq-guide").href=r.cityPage[city]||r.hub;
 $("gq-i-title").textContent="Top-rated installers in "+label;
 var want=plan.filter(function(p){return p==="heat-pump"||p==="solar"});if(!want.length&&!plan.length)want=["heat-pump"];
 var base="/installers/json/"+(r.jsonDir?r.jsonDir+"/":"");
 var jobs=want.map(function(s){return get(base+(s==="solar"?"solar/":"")+city+".json").then(function(a){return{s:s,a:a}})});
 Promise.all(jobs).then(function(res){
  if(t!==token)return;var box=$("gq-list");box.textContent="";shown=[];
  res.forEach(function(g){
   var h=document.createElement("h4");h.style.margin="14px 0 0";h.textContent=(g.s==="solar"?"Solar":"Heat pump")+" installers";box.appendChild(h);
   var top=g.a.slice(0,3);
   if(!top.length){var p=document.createElement("p");p.className="gq-meta";p.textContent="We have not listed installers for this yet.";box.appendChild(p)}
   top.forEach(function(i){shown.push(i);
    var d=document.createElement("div");d.className="gq-inst";var l=document.createElement("div");
    var n=document.createElement("h4");var ps=slug(i.name);var has=(r.profiles[city]||[]).indexOf(ps)>=0;
    if(has){var na=document.createElement("a");na.href=purl(r,city,ps);na.textContent=i.name;n.appendChild(na)}else n.textContent=i.name;l.appendChild(n);i._url=has?location.origin+purl(r,city,ps):"";
    var m=document.createElement("div");m.className="gq-meta";m.textContent=stars(i);l.appendChild(m);
    var k=document.createElement("div");k.className="gq-links";
    if(i.phone){var a=document.createElement("a");a.href="tel:"+i.phone.replace(/[^0-9+]/g,"");a.textContent=i.phone;k.appendChild(a)}
    if(i.website){var w=document.createElement("a");w.href=i.website;w.rel="nofollow noopener";w.target="_blank";w.textContent="Website";k.appendChild(w)}
    if(i.gmaps_url){var g2=document.createElement("a");g2.href=i.gmaps_url;g2.rel="nofollow noopener";g2.target="_blank";g2.textContent="Google reviews";k.appendChild(g2)}
    l.appendChild(k);d.appendChild(l);
    box.appendChild(d)});
   var more=document.createElement("p");var ma=document.createElement("a");ma.href="/installers/"+r.instDir+"/"+city+"/"+g.s+"/";ma.textContent="See every "+(g.s==="solar"?"solar":"heat pump")+" installer in "+label+" →";more.appendChild(ma);box.appendChild(more)});
  var others=plan.filter(function(p){return p==="battery"||p==="insulation"});
  others.forEach(function(s){var p=document.createElement("p");var a=document.createElement("a");a.href="/installers/"+r.instDir+"/"+city+"/"+s+"/";a.textContent="See "+s+" installers in "+label+" →";p.appendChild(a);box.appendChild(p)});
  $("gq-save").style.display=shown.length?"block":"none";
 });
}
$("gq-plan").addEventListener("submit",function(e){
 e.preventDefault();if($("gq-web").value)return;var r=D.filter(function(x){return x.code===rs.value})[0];var msg=$("gq-msg");var b=$("gq-send");
 var plan=[].map.call(document.querySelectorAll("#gq-chips input:checked"),function(c){return c.value});
 b.disabled=true;b.textContent="Sending...";
 fetch("https://leads.homepowerrebate.com/newsletter",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:$("gq-em").value,city:cs.options[cs.selectedIndex].textContent,province:r.prov,upgrades:plan,plan:true,newsletter:$("gq-news").checked,source:"get-quotes",page:location.pathname})})
 .then(function(x){if(!x.ok)throw 0;msg.className="gq-msg show ok";msg.textContent="Sent. Check your inbox in a minute (and your spam folder). Your plan has your rebates, a few articles and the installer list for "+cs.options[cs.selectedIndex].textContent+".";$("gq-plan").reset()})
 .catch(function(){msg.className="gq-msg show err";msg.textContent="That did not go through. Please check your email address and try again."})
 .then(function(){b.disabled=false;b.textContent="Email me my plan"});
});
$("gq-copy").addEventListener("click",function(){var b=$("gq-copy");var u=location.origin+location.pathname+"?province="+rs.value+"&city="+cs.value;
 (navigator.clipboard?navigator.clipboard.writeText(u):Promise.reject()).then(function(){b.textContent="Link copied"},function(){b.textContent="Copy failed"});setTimeout(function(){b.textContent="Copy link to this list"},2500)});
show();
})();
"""



def city_slugs(code):
    """City slugs for a region: installer folders plus the cities listed in data/regions.json, so a region whose installers cover
    only some cities still shows all of them. California's list holds regional hubs (bay-area, inland-empire), not cities, so it uses installer folders only."""
    base = ROOT / "installers" / code
    found = {p.name for p in base.iterdir() if p.is_dir()} if base.exists() else set()
    if code != "ca":
        found |= {h.strip("/").split("/")[-1] for h, _ in regions.BY_CODE[code]["cities"]}
    return sorted(found)


def main():
    data = []
    for code, name, prov, jdir in REG:
        cities = city_slugs(code)
        hub = regions.HUB_URL_BY_CODE[code]
        cp = {}
        for c in cities:
            hits = glob.glob(str(ROOT / hub.strip("/") / "**" / c / "index.html"), recursive=True)
            if hits:
                cp[c] = "/" + os.path.relpath(os.path.dirname(hits[0]), ROOT) + "/"
        prof = {}
        for c in cities:
            d = ROOT / "installers" / "profiles" / (jdir or "") / c
            prof[c] = sorted(x.name for x in d.iterdir() if x.is_dir()) if d.exists() else []
        data.append({"code": code, "name": name, "prov": prov, "jsonDir": jdir, "instDir": code, "hub": hub, "cityPage": cp,
                     "profiles": prof, "cities": [[c, OV.get(c, c.replace("-", " ").title())] for c in cities]})
    js = JS.replace("__DATA__", json.dumps(data, separators=(",", ":")))
    body = f"""{S}
<style>{CSS}</style>
<section class="hero"><div class="wrap"><h1>Your rebates and top-rated installers, in one place</h1>
<p>Pick your city and see what you could get back, plus the best-reviewed local installers. No sign-up needed. Nobody pays to be listed.</p></div></section>
<section class="section"><div class="gq">
<div class="gq-card"><div class="gq-row"><div class="gq-f"><label for="gq-region">Province or state</label><select id="gq-region"><option value="">Choose one</option></select></div>
<div class="gq-f"><label for="gq-city">City</label><select id="gq-city"><option value="">Choose your city</option></select></div></div>
<h2 class="gq-h" style="margin-top:6px">What are you planning? <span class="gq-meta">(optional)</span></h2><div class="checklist" id="gq-chips" style="margin:0"></div></div>
<div id="gq-out" style="display:none">
<div class="gq-card"><h2 class="gq-h" id="gq-r-title">Rebates</h2><p class="gq-sub">Every amount comes from the program's own page. We only add up programs that are open today.</p>
<a class="gq-cta" id="gq-calc" href="/calculator/">Estimate my rebates</a><a class="gq-alt" id="gq-guide" href="/">City rebate guide</a></div>
<div class="gq-card"><h2 class="gq-h" id="gq-i-title">Top-rated installers</h2><p class="gq-sub">Ranked by Google reviews. <a href="/installers/how-we-rank/">How we rank</a>.</p><div id="gq-list"></div></div>
<div class="gq-card" id="gq-save" style="display:none"><h2 class="gq-h">Email me this plan</h2>
<p class="gq-sub">We will email your rebates for the services you picked, a few helpful articles, and a link to every top-rated installer in your city. You choose who to call. We never pass your details to installers.</p>
<form id="gq-plan"><div class="gq-row"><div class="gq-f full"><label for="gq-em">Email</label><input id="gq-em" type="email" required autocomplete="email" placeholder="you@example.com"></div></div>
<label class="gq-pick" style="white-space:normal;margin:0 0 12px"><input id="gq-news" type="checkbox"> Also send me the monthly update on new programs and technology</label>
<input id="gq-web" style="position:absolute;left:-9999px" tabindex="-1" autocomplete="off" aria-hidden="true">
<button class="gq-cta" id="gq-send" type="submit">Email me my plan</button><button class="gq-cta" id="gq-copy" type="button" style="margin-left:10px;background:var(--teal-deep)">Copy link</button>
<div class="gq-msg" id="gq-msg"></div></form></div>
</div></div></section>
<script>{js}</script>
{E}"""
    f = ROOT / "get-quotes" / "index.html"
    s = f.read_text(encoding="utf-8")
    if S in s:
        s = re.sub(re.escape(S) + ".*?" + re.escape(E), lambda m: body, s, count=1, flags=re.S)
    else:
        a = s.index('<section class="hero">')
        b = s.index("<!-- CANONICAL-FOOTER-START -->")
        s = s[:a] + body + "\n\n" + s[b:]
        # drop the old page script (between the shared handler include and the shared nav/footer script)
        a = s.index('<script src="/form-handlers-with-installer-select.js?v=2"></script>')
        b = s.index("/* CANONICAL-NAV-FOOTER-JS-START */")
        b = s.rfind("<script>", 0, b)
        s = s[:a] + s[b:]
    f.write_text(s, encoding="utf-8")
    print("get-quotes rebuilt:", sum(len(r["cities"]) for r in data), "cities")


if __name__ == "__main__":
    main()
