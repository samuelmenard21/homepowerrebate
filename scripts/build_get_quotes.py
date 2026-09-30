#!/usr/bin/env python3
"""Rebuild the main content and script of /get-quotes/ (between GQ-START and GQ-END). Nav and footer stay stamped by the shared partial.
Region and city lists come from the installer folders on disk, so a new city appears here on the next build."""
import glob
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S, E = "<!-- GQ-START -->", "<!-- GQ-END -->"
REG = [("bc", "British Columbia", "BC", ""), ("on", "Ontario", "ON", "on"), ("ab", "Alberta", "AB", "ab"), ("ns", "Nova Scotia", "NS", "ns"),
       ("ma", "Massachusetts", "MA", "ma"), ("ny", "New York", "NY", "ny"), ("ca", "California", "CA", "ca"), ("pa", "Pennsylvania", "PA", "pa"),
       ("co", "Colorado", "CO", "co"), ("vt", "Vermont", "VT", "vt")]
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
var UPG=[["heat-pump","Heat pump"],["solar","Solar"],["battery","Battery"],["insulation","Insulation"],["water-heater","Heat pump water heater"],["thermostat","Smart thermostat"],["ev","EV charger"]];
var chipBox=$("gq-chips");
UPG.forEach(function(u){var l=document.createElement("label");l.className="gq-chip";var c=document.createElement("input");c.type="checkbox";c.value=u[0];
 c.addEventListener("change",function(){l.classList.toggle("on",c.checked);show()});l.appendChild(c);l.appendChild(document.createTextNode(u[1]));chipBox.appendChild(l)});
var rs=$("gq-region"),cs=$("gq-city");
D.forEach(function(r){var o=document.createElement("option");o.value=r.code;o.textContent=r.name;rs.appendChild(o)});
function fillCities(){cs.textContent="";var ph=document.createElement("option");ph.value="";ph.textContent="Choose your city";cs.appendChild(ph);
 var r=D.filter(function(x){return x.code===rs.value})[0];if(!r)return;r.cities.forEach(function(c){var o=document.createElement("option");o.value=c[0];o.textContent=c[1];cs.appendChild(o)})}
rs.addEventListener("change",function(){fillCities();show()});cs.addEventListener("change",show);
var prov=(P.get("province")||"").toLowerCase();if(prov&&D.some(function(r){return r.code===prov})){rs.value=prov;fillCities();var cc=(P.get("city")||"").toLowerCase().replace(/\s+/g,"-");cs.value=cc;if(cs.value!==cc)cs.value=""}
var picks=[];var shown=[];
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
  if(t!==token)return;var box=$("gq-list");box.textContent="";picks=[];shown=[];
  res.forEach(function(g){
   var h=document.createElement("h4");h.style.margin="14px 0 0";h.textContent=(g.s==="solar"?"Solar":"Heat pump")+" installers";box.appendChild(h);
   var top=g.a.slice(0,3);
   if(!top.length){var p=document.createElement("p");p.className="gq-meta";p.textContent="We have not listed installers for this yet.";box.appendChild(p)}
   top.forEach(function(i){shown.push(i);
    var d=document.createElement("div");d.className="gq-inst";var l=document.createElement("div");
    var n=document.createElement("h4");n.textContent=i.name;l.appendChild(n);
    var m=document.createElement("div");m.className="gq-meta";m.textContent=stars(i);l.appendChild(m);
    var k=document.createElement("div");k.className="gq-links";
    if(i.phone){var a=document.createElement("a");a.href="tel:"+i.phone.replace(/[^0-9+]/g,"");a.textContent=i.phone;k.appendChild(a)}
    if(i.website){var w=document.createElement("a");w.href=i.website;w.rel="nofollow noopener";w.target="_blank";w.textContent="Website";k.appendChild(w)}
    if(i.gmaps_url){var g2=document.createElement("a");g2.href=i.gmaps_url;g2.rel="nofollow noopener";g2.target="_blank";g2.textContent="Google reviews";k.appendChild(g2)}
    l.appendChild(k);d.appendChild(l);
    if(i.email){var pk=document.createElement("label");pk.className="gq-pick";var cb=document.createElement("input");cb.type="checkbox";
     cb.addEventListener("change",function(){var ix=picks.indexOf(i);if(cb.checked&&ix<0)picks.push(i);if(!cb.checked&&ix>=0)picks.splice(ix,1);$("gq-send").disabled=!picks.length});
     pk.appendChild(cb);pk.appendChild(document.createTextNode("Ask for a quote"));d.appendChild(pk)}
    box.appendChild(d)});
   var more=document.createElement("p");var ma=document.createElement("a");ma.href="/installers/"+r.instDir+"/"+city+"/"+g.s+"/";ma.textContent="See every "+(g.s==="solar"?"solar":"heat pump")+" installer in "+label+" →";more.appendChild(ma);box.appendChild(more)});
  var others=plan.filter(function(p){return p==="battery"||p==="insulation"});
  others.forEach(function(s){var p=document.createElement("p");var a=document.createElement("a");a.href="/installers/"+r.instDir+"/"+city+"/"+s+"/";a.textContent="See "+s+" installers in "+label+" →";p.appendChild(a);box.appendChild(p)});
  $("gq-send").disabled=true;$("gq-contact").style.display=shown.some(function(i){return i.email})?"block":"none";
 });
}
$("gq-form").addEventListener("submit",function(e){
 e.preventDefault();var r=D.filter(function(x){return x.code===rs.value})[0];var msg=$("gq-msg");
 if($("gq-web").value)return;if(!picks.length)return;
 var plan=[].map.call(document.querySelectorAll("#gq-chips input:checked"),function(c){return c.value});
 var shared={firstname:$("gq-fn").value,lastname:$("gq-ln").value,email:$("gq-em").value,phone:$("gq-ph").value,postal:$("gq-po").value,city:cs.value,province:r.prov,notes:"",upgrades:plan,page_url:location.href,referrer:document.referrer||"direct",website:""};
 var b=$("gq-send");b.disabled=true;b.textContent="Sending...";
 Promise.all(picks.map(function(i){return fetch("https://leads.homepowerrebate.com/estimate-lead",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(Object.assign({},shared,{installer_name:i.name||"",installer_email:i.email||"",installer_phone:i.phone||""}))}).then(function(x){return x.json()}).then(function(x){return!!x.success}).catch(function(){return false})})).then(function(rs2){
  var n=rs2.filter(Boolean).length;b.textContent="Send my details";b.disabled=false;
  msg.className="gq-msg show "+(n?"ok":"err");
  msg.textContent=n?"Sent to "+n+" installer"+(n>1?"s":"")+". Expect a call or email within 1 business day. Only the installers you ticked got your details.":"That did not go through. Check your postal or ZIP code and try again.";
  if(n)$("gq-form").reset();
 });
});
show();
})();
"""


def main():
    data = []
    for code, name, prov, jdir in REG:
        base = ROOT / "installers" / code
        cities = sorted(p.name for p in base.iterdir() if p.is_dir()) if base.exists() else []
        hub = {"bc": "/ca/bc/", "on": "/ca/on/", "ab": "/ca/ab/", "ns": "/ca/ns/", "ma": "/us/ma/", "ny": "/us/ny/", "ca": "/us/ca/", "pa": "/us/pa/", "co": "/us/co/", "vt": "/us/vt/"}[code]
        cp = {}
        for c in cities:
            hits = glob.glob(str(ROOT / hub.strip("/") / "**" / c / "index.html"), recursive=True)
            if hits:
                cp[c] = "/" + os.path.relpath(os.path.dirname(hits[0]), ROOT) + "/"
        data.append({"code": code, "name": name, "prov": prov, "jsonDir": jdir, "instDir": code, "hub": hub, "cityPage": cp,
                     "cities": [[c, OV.get(c, c.replace("-", " ").title())] for c in cities]})
    js = JS.replace("__DATA__", json.dumps(data, separators=(",", ":")))
    body = f"""{S}
<style>{CSS}</style>
<section class="hero"><div class="wrap"><h1>Your rebates and top-rated installers, in one place</h1>
<p>Pick your city and see what you could get back, plus the best-reviewed local installers. No sign-up needed. Nobody pays to be listed.</p></div></section>
<section class="section"><div class="gq">
<div class="gq-card"><div class="gq-row"><div class="gq-f"><label for="gq-region">Province or state</label><select id="gq-region"><option value="">Choose one</option></select></div>
<div class="gq-f"><label for="gq-city">City</label><select id="gq-city"><option value="">Choose your city</option></select></div></div>
<div class="gq-f"><label>What are you planning? (optional)</label><div class="gq-chips" id="gq-chips"></div></div></div>
<div id="gq-out" style="display:none">
<div class="gq-card"><h2 class="gq-h" id="gq-r-title">Rebates</h2><p class="gq-sub">Every amount comes from the program's own page. We only add up programs that are open today.</p>
<a class="gq-cta" id="gq-calc" href="/calculator/">Estimate my rebates</a><a class="gq-alt" id="gq-guide" href="/">City rebate guide</a></div>
<div class="gq-card"><h2 class="gq-h" id="gq-i-title">Top-rated installers</h2><p class="gq-sub">Ranked by Google reviews. <a href="/installers/how-we-rank/">How we rank</a>.</p><div id="gq-list"></div></div>
<div class="gq-card" id="gq-contact" style="display:none"><details><summary>Want an installer to contact you?</summary>
<p class="gq-sub" style="margin-top:10px">Tick "Ask for a quote" next to the installers you want, then send your details. Only those installers get them. We never sell your details.</p>
<form id="gq-form"><div class="gq-row"><div class="gq-f"><label for="gq-fn">First name</label><input id="gq-fn" required autocomplete="given-name"></div><div class="gq-f"><label for="gq-ln">Last name</label><input id="gq-ln" required autocomplete="family-name"></div></div>
<div class="gq-row"><div class="gq-f full"><label for="gq-em">Email</label><input id="gq-em" type="email" required autocomplete="email"></div></div>
<div class="gq-row"><div class="gq-f"><label for="gq-ph">Phone</label><input id="gq-ph" type="tel" required autocomplete="tel"></div><div class="gq-f"><label for="gq-po">Postal or ZIP code</label><input id="gq-po" required autocomplete="postal-code"></div></div>
<input id="gq-web" style="position:absolute;left:-9999px" tabindex="-1" autocomplete="off" aria-hidden="true">
<button class="gq-cta" id="gq-send" type="submit" disabled>Send my details</button><div class="gq-msg" id="gq-msg"></div></form></details></div>
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
