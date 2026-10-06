#!/usr/bin/env python3
"""Builds /roof-check/: an address-based solar estimate from the Google Solar API (through roof-check-worker) combined with verified rebate rules.
Rules come from data/roof-check/regions.json; every program names verified facts, and the page shows each fact's source and date.
Until data/roof-check/config.json has a worker_url the page says it is not live yet and is noindex. Usage: python3 scripts/build_roof_check.py"""
import html
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import build_ca_pages as ca  # noqa: E402

e = html.escape
FACTS = ca.FACTS
cfg = json.loads((ROOT / "data/roof-check/config.json").read_text())
reg = json.loads((ROOT / "data/roof-check/regions.json").read_text())


def src(ids):
    out = []
    for i in ids:
        f = FACTS[i]
        out.append({"t": f["program"], "u": f["source_url"], "d": f["verified_on"], "s": f["status"]})
    return out


data = {"assume": reg["assumptions"], "unverified": reg["unverified"], "federal": {k: {"text": v["text"], "src": src(v["facts"])} for k, v in reg["federal"].items()}, "regions": {}}
for code, r in reg["regions"].items():
    data["regions"][code] = {"name": r["name"], "page": r["page"], "sizeToUsage": r.get("size_to_usage", False),
                             "programs": [dict({k: v for k, v in p.items() if k != "facts"}, src=src(p["facts"])) for p in r["programs"]]}
live = bool(cfg["worker_url"])
checked = max(FACTS[i]["verified_on"] for r in reg["regions"].values() for p in r["programs"] for i in p["facts"])
title = "Solar Roof Check: Your Roof and the Rebates You Can Claim"
desc = "Type your address to see how many panels fit your roof, how much power they make and which verified solar rebates apply in your province or state."
robots = "noindex, follow" if cfg.get("noindex", True) else "index, follow, max-snippet:-1, max-image-preview:large"
worker = cfg["worker_url"].rstrip("/")
faq = [("Where do the roof numbers come from?", "From Google's Solar API, which models your roof from aerial imagery: how many panels fit, how much sun each roof section gets and the yearly output of different layouts. Coverage is not complete, and imagery can be a few years old."),
       ("Is my address stored?", "We do not save your address or your results. The address goes to Google to find your roof. To stop abuse we keep a running count of lookups and a visitor's IP address for up to an hour, nothing more."),
       ("Why does Ontario ask for my electricity use?", "Ontario's solar rebate does not allow a system under a net metering agreement, so the system must be sized to the electricity you use at home. Without your use we can only show the biggest system your roof could hold, which may be larger than the program allows."),
       ("Is this a quote?", "No. It is an estimate from satellite data and published program rules. A licensed installer has to measure your roof, check shade and your electrical panel, and design the system."),
       ("Why does it sometimes say there is no data?", "Google does not have roof data for every address, especially in some smaller communities. In that case the rebate rules for your region are still on our rebate calculator.")]
faq_html = "".join(f'<div class="faq-item"><h3>{e(q)}</h3><p>{e(a)}</p></div>' for q, a in faq)
faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
path = "/roof-check/"
js = r"""
(function(){
var D=__DATA__, W="__WORKER__";
var $=function(i){return document.getElementById(i)};
function esc(s){var d=document.createElement('div');d.textContent=String(s==null?'':s);return d.innerHTML}
function money(n){return '$'+Math.round(n).toLocaleString('en-US')}
function num(n){return Math.round(n).toLocaleString('en-US')}
function srcHtml(ss){return (ss||[]).map(function(s){var dt=new Date(s.d+'T12:00:00');return '<a href="'+esc(s.u)+'" target="_blank" rel="noopener">'+esc(s.t)+'</a> ('+esc(s.s)+', verified '+dt.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})+')'}).join('; ')}
function show(h){$('rc-out').innerHTML=h;$('rc-out').scrollIntoView({behavior:'smooth',block:'start'})}
function msg(t){show('<div class="rc-card"><p>'+t+'</p></div>')}
var form=$('rc-form');
var qs=new URLSearchParams(location.search);if(qs.get('country')==='CA'||qs.get('country')==='US')$('rc-country').value=qs.get('country');
if(!W){form.style.display='none';return}
form.addEventListener('submit',function(ev){
  ev.preventDefault();
  var addr=$('rc-addr').value.trim(),country=$('rc-country').value,use=parseFloat($('rc-use').value)||0;
  if(addr.length<8){msg('Please enter a full street address.');return}
  $('rc-go').disabled=true;$('rc-go').textContent='Checking your roof...';
  fetch(W+'/check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({address:addr,country:country})})
   .then(function(r){return r.json().then(function(j){return {s:r.status,j:j}})})
   .then(function(x){render(x.s,x.j,use,country)})
   .catch(function(){msg('Something went wrong reaching the roof service. Please try again in a minute.')})
   .then(function(){$('rc-go').disabled=false;$('rc-go').textContent='Check my roof'});
});
function regionFor(j,country){return D.regions[country+'-'+j.region]||null}
function render(status,j,use,country){
  if(status!==200){
    var m={cap:'We have reached this month\'s limit on roof lookups. The limit keeps this tool free. Please try again next month, or use our <a href="/calculator/">rebate calculator</a>.',
      slow_down:'You have checked several addresses in the past hour. Please try again later.',
      need_street_address:'Please enter a full street address with a house number.',
      not_found_address:'We could not find that address. Check the spelling and the country.',
      bad_address:'Please enter a full street address.',
      no_data:'Google has no roof data for that address. The rebate rules for your area are in our <a href="/calculator/">rebate calculator</a>.',
      upstream:'The roof service is busy. Please try again in a minute.'};
    msg(m[j.error]||'Something went wrong. Please try again.');return}
  var r=regionFor(j,country),f=D.assume.ac_factor,cs=j.configs||[];
  if(!cs.length){msg('Google found the building but no panel layouts for it.');return}
  var pick=cs[cs.length-1],sized=false;
  if(use>0){for(var i=0;i<cs.length;i++){if(cs[i].dcKwh*f>=use){pick=cs[i];sized=true;break}}}
  var kw=pick.panels*j.panelWatts/1000,ac=pick.dcKwh*f,full=cs[cs.length-1];
  var h='<div class="rc-card"><h2>Your roof</h2><p class="rc-addr">'+esc(j.address)+'</p><div class="rc-grid">'+
   '<div><b>'+num(j.maxPanels)+'</b><span>panels fit (about '+(Math.round(j.maxPanels*j.panelWatts/100)/10)+' kW)</span></div>'+
   '<div><b>'+num(j.maxSunshineHours)+'</b><span>best sun hours a year on the sunniest spot</span></div>'+
   (j.roofAreaM2?'<div><b>'+num(j.roofAreaM2)+' m&sup2;</b><span>roof area Google measured</span></div>':'')+'</div>'+
   '<p class="rc-small">Imagery quality: '+esc(j.imageryQuality||'unknown')+(j.imageryDate?', imagery date '+esc(j.imageryDate.year+'-'+String(j.imageryDate.month).padStart(2,'0')):'')+'.</p></div>';
  h+='<div class="rc-card"><h2>A system for you</h2><p>'+(sized?'Sized to cover your yearly use of '+num(use)+' kWh:':(use>0?'Your roof cannot cover all of your '+num(use)+' kWh, so this is the largest layout Google found:':'The largest layout Google found (enter your yearly use to size it to your home):'))+'</p><div class="rc-grid">'+
   '<div><b>'+pick.panels+'</b><span>panels</span></div><div><b>'+(Math.round(kw*10)/10)+' kW</b><span>system size (DC)</span></div><div><b>'+num(ac)+' kWh</b><span>a year after losses (estimate)</span></div>'+
   (use>0?'<div><b>'+Math.min(100,Math.round(100*ac/use))+'%</b><span>of your yearly use</span></div>':'')+'</div>'+
   '<p class="rc-small">'+esc(D.assume.ac_note)+'</p></div>';
  h+='<div class="rc-card"><h2>Rebates for '+esc(r?r.name:(j.region||'your area'))+'</h2>';
  if(r){
    if(r.sizeToUsage&&!(use>0))h+='<p class="rc-warn">'+esc(r.name)+'\'s program needs the system sized to your own electricity use. Enter your yearly kWh to see a realistic number.</p>';
    r.programs.forEach(function(p){
      var line='';
      if(p.kind==='per_kw'){if(r.sizeToUsage&&!(use>0)){line=''}else{var amt=Math.min(p.rate*kw,p.cap);line='Up to <b>'+money(amt)+'</b> for a '+(Math.round(kw*10)/10)+' kW system'}}
      else if(p.kind==='per_kwh'){line='About <b>'+money(p.rate*ac)+' a year</b> at $'+p.rate.toFixed(2)+' per kWh on about '+num(ac)+' kWh'}
      else if(p.kind==='pct_cap'){line='Up to <b>'+money(p.cap)+'</b> ('+p.pct+'% of your system cost)'}
      else if(p.kind==='per_kw_cond'){line='<b>'+money(p.rate*Math.min(kw,p.maxkw))+'</b> only if you are income-qualified or in an eligible community'}
      h+='<div class="rc-prog"><h3>'+esc(p.name)+'</h3>'+(line?'<p class="rc-amt">'+line+'</p>':'')+'<p>'+esc(p.note)+'</p><p class="rc-small">Source: '+srcHtml(p.src)+'</p></div>';
    });
    h+='<p><a href="'+esc(r.page)+'">More about solar rebates in '+esc(r.name)+' &rarr;</a></p>';
  }else{
    h+='<p>'+esc(D.unverified.replace('{region}',j.region||'your area'))+'</p>';
  }
  var fd=D.federal[country];if(fd)h+='<p class="rc-small">'+esc(fd.text)+' Source: '+srcHtml(fd.src)+'</p>';
  h+='</div>';
  h+='<div class="rc-card"><p><b>Next:</b> <a href="/get-quotes/">get a plan emailed with the top-rated solar installers near you</a>. Installers are ranked by Google reviews only, and nobody pays to be listed. This estimate is not a quote.</p></div>';
  h+='<p class="rc-attr">Source: Includes solar data from Google. Google Maps.</p>';
  show(h);
}
})();
"""
js = js.replace("__DATA__", json.dumps(data, ensure_ascii=False)).replace("__WORKER__", worker)
css = """<style>
.rc-wrap{max-width:860px;margin:0 auto;padding:28px 20px 60px}.rc-form{background:#fff;border:1px solid #e5dccb;border-radius:14px;padding:22px;display:grid;gap:14px}
.rc-form label{font-weight:600;font-size:14px;display:block;margin-bottom:4px}.rc-form input,.rc-form select{width:100%;padding:12px;border:1px solid #cfc6b4;border-radius:8px;font:inherit;box-sizing:border-box}
.rc-row{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:620px){.rc-row{grid-template-columns:1fr}}
.rc-form button{background:var(--amber,#d4751c);color:#fff;border:0;border-radius:999px;padding:14px 26px;font:inherit;font-weight:700;cursor:pointer}.rc-form button:disabled{opacity:.6}
.rc-card{background:#fff;border:1px solid #e5dccb;border-radius:14px;padding:20px;margin-top:16px}.rc-card h2{margin-top:0}
.rc-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:12px 0}.rc-grid div{background:#f5efe5;border-radius:10px;padding:12px}.rc-grid b{display:block;font-size:24px;color:var(--teal-deep,#08363f)}.rc-grid span{font-size:13px}
.rc-small{font-size:13px;color:#555}.rc-warn{background:#fff3e0;border-left:4px solid #d4751c;padding:10px 12px}.rc-prog{border-top:1px solid #eee;padding-top:10px;margin-top:10px}.rc-amt{font-size:18px}.rc-attr{font-size:12px;color:#5E5E5E;margin-top:14px}
.rc-off{background:#fff3e0;border-radius:10px;padding:14px;margin-bottom:16px}
</style>"""
notlive = '' if live else '<div class="rc-off"><b>Not live yet.</b> This tool is being set up and will switch on once its roof-data connection is ready.</div>'
page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-W33G4TGRHD');</script>
<meta name="description" content="{e(desc)}"><meta name="robots" content="{robots}"><link rel="canonical" href="{ca.BASE}{path}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{ca.BASE}{path}"><meta property="og:type" content="website"><meta property="og:image" content="{ca.BASE}/og-image.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
{ca.CSS}
{css}
<script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script></head><body>
{navfooter.render_nav("on", "")}
<section class="hero"><div class="wrap"><div class="amount-badge">Free, from your address</div><h1>Solar Roof Check</h1><p>Type your address. We find your roof, estimate the panels and yearly power, then apply the solar rebates we have verified for your province or state.</p></div></section>
<main class="rc-wrap">
{notlive}
<form id="rc-form" class="rc-form" autocomplete="on"><div class="rc-row"><div><label for="rc-country">Country</label><select id="rc-country"><option value="US">United States</option><option value="CA">Canada</option></select></div>
<div><label for="rc-use">Yearly electricity use in kWh (optional)</label><input id="rc-use" type="number" min="0" step="100" placeholder="e.g. 9000" inputmode="numeric"></div></div>
<div><label for="rc-addr">Street address</label><input id="rc-addr" type="text" maxlength="200" placeholder="123 Main St, Salem, MA" required></div>
<button id="rc-go" type="submit">Check my roof</button>
<p class="rc-small" style="margin:0">Your use is on your electricity bill (monthly kWh times 12). Rebate amounts last verified {date.fromisoformat(checked).strftime("%B %-d, %Y")}. Roof data: Google Solar API.</p></form>
<div id="rc-out" aria-live="polite"></div>
<h2>How this works</h2>
<p>Google models your roof from aerial imagery. We take its panel count and yearly output, then apply published program rules for your province or state. Each rebate shows its source and the date we last read it. Where we have not verified a program, we say so and show no number.</p>
<h2>Common questions</h2>
{faq_html}
<p style="font-size:14px;">By <a href="/about">Sam Menard</a>. See also the <a href="/calculator/">rebate calculator</a> and <a href="/solar-quote-checker/">solar quote checker</a>.</p>
</main>
{navfooter.render_footer("on", "", "", path)}
<script>{js}</script>
</body></html>
"""
out = ROOT / "roof-check" / "index.html"
out.parent.mkdir(exist_ok=True)
out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
print("built", path, "live" if live else "not live (noindex)")
