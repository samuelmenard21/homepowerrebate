#!/usr/bin/env python3
"""Generate the Rebate Stacking Calculator: hub page + one static page per city.

Reads powerscore-data.json (see scripts/build_powerscore.py /
scripts/build_powerscore_page.py for the data shape and site conventions this
mirrors) and renders:

  /stacking-calculator/index.html                         -- hub + JS calculator
  /stacking-calculator/<region>/<city-slug>/index.html     -- one per city (~99)

Every dollar figure on every generated page is read directly from
powerscore-data.json's categories[cat]["dollar_value"] -- nothing is invented.
If a city has a category with no dollar value / not open, that is stated
honestly rather than papered over.

Also:
  - inserts a link to each city's stacking-calculator page on that city's
    existing hub page (ca/bc/vancouver/index.html etc.)
  - appends new <url> entries to sitemap.xml for the hub + all city pages
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "powerscore-data.json").read_text())

CAT_LABELS = DATA["category_labels"]
CATEGORIES = list(CAT_LABELS.keys())
CAT_EMOJI = {
    "heat-pump": "&#128293;",
    "insulation": "&#127777;&#65039;",
    "solar": "&#9728;&#65039;",
    "battery": "&#128267;",
    "water-heater": "&#128167;",
    "smart-thermostats": "&#127777;&#65039;",
    "ev-charger": "&#128663;",
    "windows-doors": "&#129003;",
}
TODAY = "2026-08-23"


def esc(s):
    return html.escape(str(s), quote=True)


def money(v):
    return f"${v:,.0f}"


# ---------- Flatten city list ----------
class City:
    __slots__ = ("region", "region_label", "slug", "label", "url", "overall", "categories")


cities = []
for region_key, region in DATA["regions"].items():
    for slug, c in region["cities"].items():
        city = City()
        city.region = region_key
        city.region_label = region["label"]
        city.slug = slug
        city.label = c["label"]
        city.url = c["url"]
        city.overall = c["overall"]
        city.categories = c["categories"]
        cities.append(city)

cities.sort(key=lambda c: (c.region, c.label))
print(f"Loaded {len(cities)} cities")


def available_cats(city):
    """Categories that are actually open with a real dollar value > 0."""
    out = []
    for cat in CATEGORIES:
        d = city.categories.get(cat)
        if d and d.get("status") == "open" and d.get("dollar_value"):
            out.append((cat, d["dollar_value"]))
    return sorted(out, key=lambda x: -x[1])


def missing_cats(city):
    out = []
    for cat in CATEGORIES:
        d = city.categories.get(cat)
        if not d or d.get("status") != "open" or not d.get("dollar_value"):
            out.append(cat)
    return out


# ---------- Shared NAV (verbatim from build_powerscore_page.py / site canonical partial) ----------
def nav_html(depth_prefix=""):
    return f'''<!-- ============================== NAV (canonical, from _partials/nav-footer.html) ============================== -->
<nav class="nav">
  <div class="nav-inner" style="display:flex; justify-content:space-between; align-items:center;">
    <a href="/" class="logo">
      <span class="logo-mark"></span>
      <span>Home<span class="logo-power">Power</span>Rebate</span>
    </a>
    <div style="display:flex; align-items:center; gap:16px;" class="nav-desktop-only">
      <a href="/installers" style="color:var(--ink-soft); font-weight:600; font-size:15px; text-decoration:none;">Find an Installer</a>
      <a href="/retrofit-assessment/" style="color:var(--ink-soft); font-weight:600; font-size:15px; text-decoration:none;">Assessment</a>
      <a href="/blog" style="color:var(--ink-soft); font-weight:600; font-size:15px; text-decoration:none;">Blog</a>
    </div>
    <div style="display:none; align-items:center; gap:12px;" class="nav-mobile-only">
      <a href="/installers" style="color:var(--ink-soft); font-weight:600; font-size:14px; text-decoration:none;">Installers</a>
      <a href="/retrofit-assessment/" style="color:var(--ink-soft); font-weight:600; font-size:14px; text-decoration:none;">Assessment</a>
    </div>
    <button onclick="toggleCityDropdown()" class="nav-pick" style="border:none; cursor:pointer;">
      Pick your city
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
    </button>
  </div>

  <div id="city-dropdown-modal" style="display:none; position:absolute; top:56px; right:20px; background:#fff; border:1px solid var(--rule); border-radius:12px; box-shadow:0 8px 24px rgba(10,42,46,0.12); z-index:49; max-width:300px; max-height:70vh; overflow-y:auto;">
    <div style="padding:16px 16px 0;">
      <div style="display:flex; gap:6px; margin-bottom:12px;">
        <button type="button" onclick="showProvinceCities('on')" id="province-tab-on" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:var(--teal-deep); color:#fff; font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Ontario</button>
        <button type="button" onclick="showProvinceCities('bc')" id="province-tab-bc" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">British Columbia</button>
        <button type="button" onclick="showProvinceCities('ca')" id="province-tab-ca" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">California (US)</button>
      </div>
      <div style="display:flex; gap:6px; margin-bottom:12px;">
        <button type="button" onclick="showProvinceCities('ab')" id="province-tab-ab" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Alberta</button>
        <button type="button" onclick="showProvinceCities('ns')" id="province-tab-ns" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Nova Scotia</button>
      </div>
      <div style="display:flex; gap:6px; margin-bottom:12px;">
        <button type="button" onclick="showProvinceCities('ma')" id="province-tab-ma" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Massachusetts</button>
        <button type="button" onclick="showProvinceCities('ny')" id="province-tab-ny" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">New York</button>
      </div>
      <div style="display:flex; gap:6px; margin-bottom:12px;">
        <button type="button" onclick="showProvinceCities('pa')" id="province-tab-pa" style="flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:#fff; color:var(--ink); font-weight:600; font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;">Pennsylvania</button>
      </div>
    </div>
    <div style="padding:0 16px 16px;">
    <div id="province-cities-on" style="display:grid; gap:8px;">
      <a href="/ca/on/toronto">Toronto</a><a href="/ca/on/ottawa">Ottawa</a><a href="/ca/on/mississauga">Mississauga</a><a href="/ca/on/brampton">Brampton</a><a href="/ca/on/hamilton">Hamilton</a><a href="/ca/on/markham">Markham</a><a href="/ca/on/vaughan">Vaughan</a><a href="/ca/on/richmond-hill">Richmond Hill</a><a href="/ca/on/barrie">Barrie</a><a href="/ca/on/london">London</a><a href="/ca/on/kitchener">Kitchener</a><a href="/ca/on/windsor">Windsor</a><a href="/ca/on/oakville">Oakville</a><a href="/ca/on/oshawa">Oshawa</a><a href="/ca/on/whitby">Whitby</a><a href="/ca/on/burlington">Burlington</a><a href="/ca/on/cambridge">Cambridge</a><a href="/ca/on/greater-sudbury">Greater Sudbury</a>
    </div>
    <div id="province-cities-bc" style="display:none; gap:8px;">
      <a href="/ca/bc/abbotsford">Abbotsford</a><a href="/ca/bc/burnaby">Burnaby</a><a href="/ca/bc/chilliwack">Chilliwack</a><a href="/ca/bc/coquitlam">Coquitlam</a><a href="/ca/bc/fort-st-john">Fort St. John</a><a href="/ca/bc/kamloops">Kamloops</a><a href="/ca/bc/kelowna">Kelowna</a><a href="/ca/bc/langley">Langley</a><a href="/ca/bc/maple-ridge">Maple Ridge</a><a href="/ca/bc/nanaimo">Nanaimo</a><a href="/ca/bc/penticton">Penticton</a><a href="/ca/bc/prince-george">Prince George</a><a href="/ca/bc/richmond">Richmond</a><a href="/ca/bc/squamish">Squamish</a><a href="/ca/bc/surrey">Surrey</a><a href="/ca/bc/vancouver">Vancouver</a><a href="/ca/bc/vernon">Vernon</a><a href="/ca/bc/victoria">Victoria</a>
    </div>
    <div id="province-cities-ab" style="display:none; gap:8px;">
      <a href="/ca/ab/calgary">Calgary</a><a href="/ca/ab/edmonton">Edmonton</a><a href="/ca/ab/red-deer">Red Deer</a><a href="/ca/ab/lethbridge">Lethbridge</a><a href="/ca/ab/st-albert">St. Albert</a>
    </div>
    <div id="province-cities-ns" style="display:none; gap:8px;">
      <a href="/ca/ns/halifax">Halifax</a>
    </div>
    <div id="province-cities-ma" style="display:none; gap:8px;">
      <a href="/us/ma/boston">Boston</a><a href="/us/ma/worcester">Worcester</a><a href="/us/ma/springfield">Springfield</a><a href="/us/ma/cambridge">Cambridge</a><a href="/us/ma/lowell">Lowell</a><a href="/us/ma/brockton">Brockton</a><a href="/us/ma/new-bedford">New Bedford</a><a href="/us/ma/quincy">Quincy</a><a href="/us/ma/lynn">Lynn</a><a href="/us/ma/fall-river">Fall River</a><a href="/us/ma/newton">Newton</a><a href="/us/ma/somerville">Somerville</a>
    </div>
    <div id="province-cities-ca" style="display:none; gap:8px;">
      <a href="/us/ca/los-angeles/">Los Angeles</a><a href="/us/ca/sacramento/">Sacramento</a><a href="/us/ca/bay-area/">Bay Area</a><a href="/us/ca/san-diego/">San Diego</a><a href="/us/ca/inland-empire/">Inland Empire</a>
    </div>
    <div id="province-cities-ny" style="display:none; gap:8px;">
      <a href="/us/ny/con-edison/new-york-city/">New York City</a><a href="/us/ny/con-edison/yonkers/">Yonkers</a><a href="/us/ny/con-edison/mount-vernon/">Mount Vernon</a><a href="/us/ny/con-edison/new-rochelle/">New Rochelle</a><a href="/us/ny/con-edison/white-plains/">White Plains</a><a href="/us/ny/pseg/brookhaven/">Brookhaven</a><a href="/us/ny/pseg/islip/">Islip</a><a href="/us/ny/pseg/babylon/">Babylon</a><a href="/us/ny/pseg/huntington/">Huntington</a><a href="/us/ny/pseg/smithtown/">Smithtown</a><a href="/us/ny/pseg/oyster-bay/">Oyster Bay</a><a href="/us/ny/pseg/southampton/">Southampton</a><a href="/us/ny/central-hudson/poughkeepsie/">Poughkeepsie</a><a href="/us/ny/central-hudson/newburgh/">Newburgh</a><a href="/us/ny/central-hudson/kingston/">Kingston</a><a href="/us/ny/central-hudson/beacon/">Beacon</a><a href="/us/ny/central-hudson/saugerties/">Saugerties</a><a href="/us/ny/national-grid/albany/">Albany</a><a href="/us/ny/national-grid/buffalo/">Buffalo</a><a href="/us/ny/national-grid/rochester/">Rochester</a><a href="/us/ny/national-grid/syracuse/">Syracuse</a><a href="/us/ny/national-grid/yonkers/">Yonkers (National Grid)</a>
    </div>
    <div id="province-cities-pa" style="display:none; gap:8px;">
      <a href="/us/pa/philadelphia">Philadelphia</a><a href="/us/pa/pittsburgh">Pittsburgh</a><a href="/us/pa/allentown">Allentown</a><a href="/us/pa/erie">Erie</a>
    </div>
    </div>
  </div>
</nav>
<!-- ============================== /NAV ============================== -->'''


def footer_html(page_path):
    return f'''<!-- ============================ FOOTER ============================= -->
<section style="background: linear-gradient(135deg, rgba(13, 79, 92, 0.95), rgba(8, 54, 63, 0.98)); padding: 56px 24px; margin: 0;">
  <div class="wrap" style="text-align: center; color: #fff; max-width: 600px;">
    <div style="font-size: 13px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: rgba(212, 117, 28, 0.9); margin-bottom: 14px;">From Sam</div>
    <h2 style="font-family: 'Fraunces', Georgia, serif; font-size: 32px; line-height: 1.2; margin-bottom: 14px; color: #fff;">Get my weekly email</h2>
    <p style="font-size: 15px; color: rgba(250, 247, 242, 0.85); margin-bottom: 24px;">Every Friday: what I'm learning about rebates across every province and state we cover, heat pump reality checks, solar economics, and the installers I trust. Real stuff, no marketing.</p>
    <form id="newsletter-form" style="display: flex; flex-direction: column; gap: 10px;">
      <input type="email" id="newsletter-email" placeholder="your@email.com" required style="padding: 12px 14px; border: none; border-radius: 6px; font-family: 'Inter Tight', sans-serif; font-size: 14px; background: #fff; color: var(--ink);">
      <input type="hidden" id="newsletter-city" value="">
      <input type="hidden" id="newsletter-page" value="{esc(page_path)}">
      <button type="submit" style="padding: 12px 24px; background: #d4751c; color: #fff; border: none; border-radius: 6px; font-weight: 600; font-size: 14px; cursor: pointer; font-family: 'Inter Tight', sans-serif;">Subscribe</button>
      <p style="font-size: 11px; color: rgba(250, 247, 242, 0.6); margin-top: 6px;">No spam, ever. Unsubscribe anytime.</p>
    </form>
    <div id="newsletter-response" style="display: none; margin-top: 12px; padding: 12px; background: rgba(45, 106, 79, 0.2); border-radius: 6px; border: 1px solid rgba(45, 106, 79, 0.4); font-size: 13px;"></div>
  </div>
</section>

<footer class="footer">
  <div class="footer-inner">
    <div class="footer-top">
      <div>
        <div class="footer-brand">Home<span class="logo-power">Power</span>Rebate</div>
        <p class="footer-tagline">Helping homeowners understand rebates and choose trusted installers. Real numbers. Your choice.</p>
      </div>
      <div>
        <div class="footer-col-title">Canada</div>
        <ul class="footer-col-links">
          <li><a href="/ca/">All Provinces</a></li>
          <li><a href="/ca/bc">British Columbia</a></li>
          <li><a href="/ca/on">Ontario</a></li>
          <li><a href="/ca/ab">Alberta</a></li>
          <li><a href="/ca/ns">Nova Scotia</a></li>
        </ul>
      </div>
      <div>
        <div class="footer-col-title">United States</div>
        <ul class="footer-col-links">
          <li><a href="/us/">All States</a></li>
          <li><a href="/us/ca">California</a></li>
          <li><a href="/us/ny">New York</a></li>
          <li><a href="/us/ma">Massachusetts</a></li>
        </ul>
      </div>
      <div>
        <div class="footer-col-title">Guides &amp; Tools</div>
        <ul class="footer-col-links">
          <li><a href="/powerscore/">PowerScore Rankings</a></li>
          <li><a href="/stacking-calculator/">Rebate Stacking Calculator</a></li>
          <li><a href="/installers/">Find an Installer</a></li>
          <li><a href="/retrofit-assessment/">Retrofit Assessment</a></li>
          <li><a href="/share-your-cost/">Share Your Cost</a></li>
          <li><a href="/blog">Full Blog</a></li>
          <li><a href="/questions/">Rebate Questions</a></li>
          <li><a href="/ca/">Canada by Province</a></li>
          <li><a href="/us/">US by State</a></li>
        </ul>
      </div>
      <div>
        <div class="footer-col-title">Company</div>
        <ul class="footer-col-links">
          <li><a href="/about">About</a></li>
          <li><a href="/partners/">Partners</a></li>
          <li><a href="/privacy">Privacy</a></li>
          <li><a href="/terms">Terms</a></li>
          <li><a href="/contact">Contact</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <div>&copy; 2026 HomePowerRebate &middot; Independent guide. By <a href="/about" style="color:inherit;">Sam Menard</a>. <a href="https://www.facebook.com/profile.php?id=61592376033225" style="color:inherit; text-decoration:none;">Follow on Facebook</a></div>
      <div>Made in Canada 🇨🇦</div>
    </div>
  </div>
</footer>
<!-- =========================== /FOOTER ============================= -->'''


NAV_JS = '''function toggleCityDropdown() {
  const modal = document.getElementById('city-dropdown-modal');
  if (modal) modal.style.display = modal.style.display === 'none' ? 'block' : 'none';
}
function showProvinceCities(prov) {
  const regions = ['on', 'bc', 'ab', 'ns', 'ma', 'ca', 'ny', 'pa'];
  regions.forEach(function(r) {
    const panel = document.getElementById('province-cities-' + r);
    const tab = document.getElementById('province-tab-' + r);
    if (!panel || !tab) return;
    panel.style.display = (prov === r) ? 'grid' : 'none';
    tab.style.background = (prov === r) ? 'var(--teal-deep)' : '#fff';
    tab.style.color = (prov === r) ? '#fff' : 'var(--ink)';
  });
}
document.getElementById('newsletter-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('newsletter-email').value;
  const city = document.getElementById('newsletter-city').value;
  const page = document.getElementById('newsletter-page').value;
  const responseEl = document.getElementById('newsletter-response');
  const button = document.querySelector('#newsletter-form button');
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = 'Subscribing...';
  try {
    const response = await fetch('https://leads.homepowerrebate.com/newsletter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, city, page })
    });
    if (!response.ok) throw new Error('Subscription failed');
    responseEl.textContent = "You're in! Check your inbox for a welcome email.";
    responseEl.style.display = 'block';
    document.getElementById('newsletter-form').style.display = 'none';
  } catch (error) {
    responseEl.textContent = 'Something went wrong — please try again or email us directly.';
    responseEl.style.display = 'block';
    responseEl.style.background = 'rgba(163, 64, 47, 0.2)';
    responseEl.style.borderColor = 'rgba(163, 64, 47, 0.4)';
    button.disabled = false;
    button.textContent = originalText;
  }
});'''

SHARED_CSS = ''':root {
  --ink: #0a2a2e;
  --ink-soft: #1a3d42;
  --paper: #faf7f2;
  --paper-warm: #f5efe5;
  --teal: #0d4f5c;
  --teal-deep: #08363f;
  --amber: #d4751c;
  --amber-bright: #e88a2e;
  --green-money: #2d6a4f;
  --red-flag: #b04545;
  --rule: #d9d0c1;
  --sage: #6f8f7a;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink); font-family: 'Inter Tight', sans-serif; line-height: 1.6; }
h1, h2, h3, h4 { font-family: 'Fraunces', serif; color: var(--teal-deep); }
.wrap { max-width: 1180px; margin: 0 auto; padding: 0 28px; }
a { color: var(--teal); }

.hero { background: linear-gradient(135deg, var(--teal-deep), var(--teal)); color: #fff; padding: 64px 28px 56px; text-align: center; }
.hero .eyebrow { font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: rgba(255,255,255,0.75); margin-bottom: 14px; }
.hero h1 { color: #fff; font-size: clamp(28px, 4.6vw, 46px); line-height: 1.15; margin: 0 0 16px; max-width: 820px; margin-left: auto; margin-right: auto; }
.hero p.lead { font-size: 17px; color: rgba(255,255,255,0.85); max-width: 660px; margin: 0 auto 20px; }
.hero-stats { display: flex; justify-content: center; gap: 36px; flex-wrap: wrap; margin-top: 8px; }
.hero-stat { text-align: center; }
.hero-stat .num { font-family: 'Fraunces', serif; font-size: 28px; font-weight: 700; color: var(--amber-bright); }
.hero-stat .lbl { font-size: 12px; color: rgba(255,255,255,0.7); text-transform: uppercase; letter-spacing: .05em; }

.picker-section { padding: 48px 28px; }
.picker-card { background: #fff; border: 1px solid var(--rule); border-radius: 16px; padding: 32px; box-shadow: 0 6px 24px rgba(10,42,46,0.06); }
.picker-card h2 { margin-top: 0; font-size: 24px; }
.picker-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 18px; }
.picker-row select { flex: 1; min-width: 240px; padding: 12px 14px; border-radius: 8px; border: 1px solid var(--rule); font-family: 'Inter Tight', sans-serif; font-size: 15px; background: #fff; color: var(--ink); }

.cat-checks { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; margin-bottom: 20px; }
.cat-check { display: flex; align-items: center; gap: 10px; background: var(--paper-warm); border: 1px solid var(--rule); border-radius: 10px; padding: 12px 14px; font-size: 14px; font-weight: 600; }
.cat-check input { width: 18px; height: 18px; accent-color: var(--amber); }
.cat-check .amt { margin-left: auto; color: var(--green-money); font-weight: 700; }
.cat-check.disabled { opacity: .45; }
.cat-check .amt.zero { color: var(--sage); font-weight: 500; font-size: 12px; }

.stack-total { display: flex; align-items: center; gap: 20px; padding: 22px; background: var(--teal-deep); border-radius: 12px; color: #fff; flex-wrap: wrap; }
.stack-total .amt-big { font-family: 'Fraunces', serif; font-size: 40px; font-weight: 700; color: var(--amber-bright); }
.stack-total .lbl { font-size: 13px; color: rgba(255,255,255,0.75); text-transform: uppercase; letter-spacing: .05em; }

.section { padding: 44px 0; }
.section-title { font-size: 26px; margin-bottom: 6px; }
.section-sub { color: var(--ink-soft); margin-bottom: 22px; max-width: 720px; }

.example-card { background: #fff; border: 1px solid var(--rule); border-radius: 12px; padding: 22px 24px; margin-bottom: 16px; }
.example-card h3 { margin: 0 0 8px; font-size: 18px; }
.example-card .example-total { font-family: 'Fraunces', serif; font-size: 26px; font-weight: 700; color: var(--green-money); }
.example-line { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dashed var(--rule); font-size: 14px; }
.example-line:last-of-type { border-bottom: none; }

.city-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }
.city-grid a { display: block; background: #fff; border: 1px solid var(--rule); border-radius: 10px; padding: 12px 14px; text-decoration: none; color: var(--teal-deep); font-weight: 700; font-size: 14px; }
.city-grid a:hover { border-color: var(--teal); }
.city-grid a .amt { display: block; font-size: 12px; color: var(--green-money); font-weight: 600; margin-top: 2px; }
.region-block { margin-bottom: 32px; }
.region-block h3 { font-size: 18px; margin-bottom: 12px; }

.status-pill { display: inline-block; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 999px; text-transform: uppercase; letter-spacing: .03em; }
.status-pill-open { background: #eaf3ee; color: var(--green-money); }
.status-pill-missing { background: #fdf2f0; color: var(--red-flag); }

.faq-item { background: #fff; border: 1px solid var(--rule); border-radius: 12px; padding: 18px 22px; margin-bottom: 12px; }
.faq-item h3 { font-size: 16px; margin: 0 0 6px; }
.faq-item p { margin: 0; color: var(--ink-soft); font-size: 14px; }

.methodology { background: var(--paper-warm); padding: 44px 0; }
.methodology .box { background: #fff; border: 1px solid var(--rule); border-radius: 12px; padding: 26px; }
.methodology ul { margin: 12px 0 0; padding-left: 20px; }
.methodology li { margin-bottom: 8px; }

.breadcrumb { font-size: 13px; color: var(--sage); padding: 14px 28px 0; }
.breadcrumb a { color: var(--sage); text-decoration: none; }
.breadcrumb a:hover { text-decoration: underline; }

@media (max-width: 640px) {
  .stack-total { flex-direction: column; text-align: center; }
}'''


def head(title, description, canonical, og_title=None, og_description=None):
    og_title = og_title or title
    og_description = og_description or description
    return f'''<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>

<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-W33G4TGRHD');
</script>

<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:title" content="{esc(og_title)}">
<meta property="og:description" content="{esc(og_description)}">
<meta property="og:type" content="article">
<meta property="og:image" content="https://homepowerrebate.com/og-image.svg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:type" content="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">'''


# ============================================================
# Per-city page
# ============================================================
def build_city_page(city):
    avail = available_cats(city)
    missing = missing_cats(city)
    total_all = sum(v for _, v in avail)
    url = f"/stacking-calculator/{city.region}/{city.slug}/"
    canonical = f"https://homepowerrebate.com{url}"

    title = f"Rebate Stacking Calculator for {city.label}: Combine Heat Pump, Solar & More | HomePowerRebate"
    description = (
        f"See how much {city.label} homeowners can stack by combining rebates: "
        f"heat pump, solar, insulation and 5 more categories, added up to a real total of {money(total_all)} "
        f"in available {city.label} rebates when every open program is combined."
        if total_all > 0
        else f"{city.label} rebate stacking guide: what's actually available to combine, and what isn't, category by category."
    )

    # Worked examples -------------------------------------------------
    examples = []
    hp = city.categories.get("heat-pump")
    solar = city.categories.get("solar")
    ins = city.categories.get("insulation")

    def cat_line(cat):
        d = city.categories.get(cat)
        ok = d and d.get("status") == "open" and d.get("dollar_value")
        val = d["dollar_value"] if ok else 0
        return ok, val

    hp_ok, hp_v = cat_line("heat-pump")
    solar_ok, solar_v = cat_line("solar")
    ins_ok, ins_v = cat_line("insulation")
    hpsi_total = hp_v + solar_v + ins_v
    hpsi_have = [c for c, ok in (("heat pump", hp_ok), ("solar", solar_ok), ("insulation", ins_ok)) if ok]

    if hpsi_have:
        lines = []
        if hp_ok:
            lines.append(f'<div class="example-line"><span>{esc(CAT_LABELS["heat-pump"])}</span><span>{money(hp_v)}</span></div>')
        if solar_ok:
            lines.append(f'<div class="example-line"><span>{esc(CAT_LABELS["solar"])}</span><span>{money(solar_v)}</span></div>')
        if ins_ok:
            lines.append(f'<div class="example-line"><span>{esc(CAT_LABELS["insulation"])}</span><span>{money(ins_v)}</span></div>')
        missing_note = ""
        missing_here = [n for n, ok in (("heat pump", hp_ok), ("solar", solar_ok), ("insulation", ins_ok)) if not ok]
        if missing_here:
            missing_note = f'<p style="font-size:13px; color:var(--sage); margin-top:10px;">{esc(city.label)} does not currently have an open, quantified rebate for {", ".join(missing_here)} in our data, so it is left out of this total rather than estimated.</p>'
        examples.append(f'''<div class="example-card">
  <h3>Heat pump + solar + insulation</h3>
  {"".join(lines)}
  <div class="example-line" style="border-top:2px solid var(--rule); margin-top:6px; padding-top:10px; font-weight:700;"><span>Combined total</span><span class="example-total">{money(hpsi_total)}</span></div>
  {missing_note}
</div>''')

    if len(avail) >= 2:
        top2 = avail[:2]
        top2_total = sum(v for _, v in top2)
        lines = "".join(f'<div class="example-line"><span>{esc(CAT_LABELS[c])}</span><span>{money(v)}</span></div>' for c, v in top2)
        examples.append(f'''<div class="example-card">
  <h3>The two biggest {esc(city.label)} rebates, stacked</h3>
  {lines}
  <div class="example-line" style="border-top:2px solid var(--rule); margin-top:6px; padding-top:10px; font-weight:700;"><span>Combined total</span><span class="example-total">{money(top2_total)}</span></div>
</div>''')

    if len(avail) >= 3:
        lines = "".join(f'<div class="example-line"><span>{esc(CAT_LABELS[c])}</span><span>{money(v)}</span></div>' for c, v in avail)
        examples.append(f'''<div class="example-card">
  <h3>Every open {esc(city.label)} rebate combined</h3>
  {lines}
  <div class="example-line" style="border-top:2px solid var(--rule); margin-top:6px; padding-top:10px; font-weight:700;"><span>Combined total ({len(avail)} programs)</span><span class="example-total">{money(total_all)}</span></div>
</div>''')

    if not examples:
        examples.append(f'''<div class="example-card">
  <h3>No open, quantified rebates on file for {esc(city.label)} yet</h3>
  <p style="color:var(--ink-soft); font-size:14px;">We don't currently have an open program with a published dollar amount for {esc(city.label)} in any of our 8 tracked categories. Check the full <a href="{esc(city.url)}">{esc(city.label)} rebate guide</a> for the latest, or browse a nearby city on this tool's <a href="/stacking-calculator/">hub page</a>.</p>
</div>''')

    # Category table ----------------------------------------------------
    cat_rows = []
    for cat in CATEGORIES:
        d = city.categories.get(cat, {})
        ok = d.get("status") == "open" and d.get("dollar_value")
        amt = money(d["dollar_value"]) if d.get("dollar_value") else "&mdash;"
        pill = '<span class="status-pill status-pill-open">Open</span>' if ok else '<span class="status-pill status-pill-missing">Not available</span>'
        cat_rows.append(f'<div class="example-line"><span>{CAT_EMOJI.get(cat,"")} {esc(CAT_LABELS[cat])}</span><span>{amt} &nbsp; {pill}</span></div>')

    # FAQ -----------------------------------------------------------------
    faqs = []
    if hpsi_have:
        faqs.append((
            f"How much can a {city.label} homeowner get for heat pump + solar together?",
            (f"Combining {'heat pump (' + money(hp_v) + ')' if hp_ok else 'heat pump'} and "
             f"{'solar (' + money(solar_v) + ')' if solar_ok else 'solar'} in {city.label} adds up to "
             f"{money(hp_v + solar_v)} based on the open programs we track, before adding any other category.")
        ))
    faqs.append((
        f"What's the maximum rebate stack available in {city.label}?",
        (f"Adding up every open, quantified rebate category we track for {city.label} comes to {money(total_all)} "
         f"across {len(avail)} of the 8 categories." if total_all > 0 else
         f"We don't have an open, quantified rebate on file for {city.label} in any of the 8 categories we track right now — check the full {city.label} rebate guide for the latest program status.")
    ))
    faqs.append((
        f"Are all these {city.label} rebates available at the same time?",
        f"They come from different programs (federal, provincial or state, utility, and municipal), so most homeowners can combine several in the same renovation project. Always confirm current stacking rules with each program before you apply, since eligibility and funding caps can change."
    ))
    if missing:
        missing_labels = ", ".join(CAT_LABELS[c] for c in missing[:4])
        faqs.append((
            f"Which rebate categories are NOT currently available in {city.label}?",
            f"Based on our data, {city.label} does not currently have an open rebate with a published dollar amount for: {missing_labels}{' and others' if len(missing) > 4 else ''}. This can change as programs launch or funding resets, so we recheck city pages regularly."
        ))

    faq_html = "\n".join(f'<div class="faq-item"><h3>{esc(q)}</h3><p>{esc(a)}</p></div>' for q, a in faqs)

    faq_jsonld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faqs
        ],
    }
    article_jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": f"How Much Can You Stack in {city.label}? Heat Pump + Solar + Insulation Rebates",
        "description": description,
        "author": {"@type": "Person", "name": "Sam Menard", "url": "https://homepowerrebate.com/about"},
        "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
        "mainEntityOfPage": canonical,
        "datePublished": TODAY,
        "dateModified": TODAY,
    }
    jsonld_html = (
        '<script type="application/ld+json">' + json.dumps(faq_jsonld) + "</script>\n"
        '<script type="application/ld+json">' + json.dumps(article_jsonld) + "</script>"
    )

    h1 = f"How Much Can You Stack in {esc(city.label)}? Heat Pump + Solar + Insulation Rebates"

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
{head(title, description, canonical)}

{jsonld_html}

<style>
{SHARED_CSS}
</style>
</head>
<body>

{nav_html()}

<div class="breadcrumb"><a href="/">Home</a> &rsaquo; <a href="/stacking-calculator/">Rebate Stacking Calculator</a> &rsaquo; {esc(city.label)}</div>

<header class="hero">
  <div class="wrap">
    <div class="eyebrow">Rebate Stacking Calculator &middot; {esc(city.region_label)}</div>
    <h1>{h1}</h1>
    <p class="lead">{esc(city.label)} homeowners can combine multiple rebate programs on the same project. Here's what actually stacks, with real dollar figures from our {esc(city.label)} rebate guide &mdash; nothing estimated.</p>
    <div class="hero-stats">
      <div class="hero-stat"><div class="num">{money(total_all) if total_all else "&mdash;"}</div><div class="lbl">Max combined stack</div></div>
      <div class="hero-stat"><div class="num">{len(avail)}/8</div><div class="lbl">Open categories</div></div>
      <div class="hero-stat"><div class="num">{city.overall:.0f}</div><div class="lbl">PowerScore</div></div>
    </div>
  </div>
</header>

<section class="section" style="background:#fff;">
  <div class="wrap">
    <h2 class="section-title">Worked stacking examples for {esc(city.label)}</h2>
    <p class="section-sub">These use the exact dollar figures published on the <a href="{esc(city.url)}">{esc(city.label)} rebate guide</a>. If a category isn't listed, it's because {esc(city.label)} doesn't currently have an open program with a published amount &mdash; we don't fill that in with a guess.</p>
    {"".join(examples)}
  </div>
</section>

<section class="section" style="background: var(--paper-warm);">
  <div class="wrap">
    <h2 class="section-title">Every category, {esc(city.label)}</h2>
    <p class="section-sub">The full breakdown behind the totals above.</p>
    <div class="example-card">
      {"".join(cat_rows)}
    </div>
  </div>
</section>

<section class="section" style="background:#fff;">
  <div class="wrap">
    <h2 class="section-title">FAQ for {esc(city.label)} homeowners</h2>
    {faq_html}
  </div>
</section>

<section class="methodology">
  <div class="wrap">
    <div class="box">
      <h2 style="margin-top:0; font-size:22px;">How this stack is calculated</h2>
      <p>Every dollar figure above comes straight from the {esc(city.label)} rebate guide's published program amounts &mdash; the same numbers used to compute {esc(city.label)}'s <a href="/powerscore/#city-{esc(city.region).replace('/', '-')}-{esc(city.slug)}">PowerScore of {city.overall:.0f}/100</a>. We only count a category toward the combined total when it's an open program with a real published dollar value; categories with no open program, or no published amount, are shown as unavailable rather than estimated.</p>
      <p>Want your own custom combination? Use the <a href="/stacking-calculator/">interactive calculator</a> on the hub page to check-box any mix of categories across any city we cover.</p>
    </div>
  </div>
</section>

<section class="section" style="background: var(--paper-warm);">
  <div class="wrap" style="text-align:center;">
    <h2 style="margin-top:0;">See the full {esc(city.label)} rebate guide</h2>
    <p style="max-width:520px; margin:0 auto 20px; color:var(--ink-soft);">Every program explained in plain language, income tiers, local context, and a free assessment tool.</p>
    <a href="{esc(city.url)}" style="display:inline-block; padding:14px 28px; background: var(--amber); color:#fff; border-radius:8px; text-decoration:none; font-weight:700;">Open the {esc(city.label)} guide &rarr;</a>
  </div>
</section>

{footer_html(url)}

<script>
{NAV_JS}
</script>

</body>
</html>
'''
    return url, page


# ============================================================
# Hub page
# ============================================================
def build_hub_page():
    url = "/stacking-calculator/"
    canonical = "https://homepowerrebate.com" + url
    title = "Rebate Stacking Calculator: Combine Heat Pump, Solar & More by City | HomePowerRebate"
    description = (
        f"See your total combined rebate stack for {len(cities)} cities across Canada and the US. "
        "Pick your city, check the categories you're planning (heat pump, solar, insulation, and 5 more), "
        "and get a real dollar total from published program amounts."
    )

    # Build per-city JS data payload: category -> dollar_value (or null)
    js_cities = []
    for c in cities:
        cat_map = {}
        for cat in CATEGORIES:
            d = c.categories.get(cat, {})
            cat_map[cat] = d["dollar_value"] if (d.get("status") == "open" and d.get("dollar_value")) else 0
        js_cities.append({
            "key": f"{c.region}/{c.slug}",
            "label": c.label,
            "region": c.region_label,
            "url": f"/stacking-calculator/{c.region}/{c.slug}/",
            "guideUrl": c.url,
            "cats": cat_map,
        })

    city_options = "\n".join(
        f'<option value="{esc(c.region)}/{esc(c.slug)}">{esc(c.label)}, {esc(c.region_label)}</option>' for c in cities
    )

    cat_checks = "\n".join(
        f'''<label class="cat-check" id="check-{cat}">
  <input type="checkbox" value="{cat}" onchange="recalc()">
  <span>{CAT_EMOJI[cat]} {esc(CAT_LABELS[cat])}</span>
  <span class="amt" id="amt-{cat}">&mdash;</span>
</label>''' for cat in CATEGORIES
    )

    # Region -> city grid, linking to each dedicated page
    region_order = []
    seen = set()
    for c in cities:
        if c.region not in seen:
            seen.add(c.region)
            region_order.append((c.region, c.region_label))

    region_blocks = []
    for region_key, region_label in region_order:
        region_cities = [c for c in cities if c.region == region_key]
        links = []
        for c in region_cities:
            avail = available_cats(c)
            total = sum(v for _, v in avail)
            links.append(
                f'<a href="/stacking-calculator/{esc(c.region)}/{esc(c.slug)}/">{esc(c.label)}<span class="amt">{money(total) if total else "See page"}</span></a>'
            )
        region_blocks.append(f'''<div class="region-block">
  <h3>{esc(region_label)}</h3>
  <div class="city-grid">
    {"".join(links)}
  </div>
</div>''')

    dataset_jsonld = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "HomePowerRebate Rebate Stacking Calculator",
        "description": description,
        "url": canonical,
        "creator": {"@type": "Organization", "name": "HomePowerRebate"},
        "variableMeasured": [CAT_LABELS[c] for c in CATEGORIES],
        "temporalCoverage": "2026",
    }
    article_jsonld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Rebate Stacking Calculator: How Much Can You Combine?",
        "description": description,
        "author": {"@type": "Person", "name": "Sam Menard", "url": "https://homepowerrebate.com/about"},
        "publisher": {"@type": "Organization", "name": "HomePowerRebate"},
        "mainEntityOfPage": canonical,
        "datePublished": TODAY,
        "dateModified": TODAY,
    }
    jsonld_html = (
        '<script type="application/ld+json">' + json.dumps(dataset_jsonld) + "</script>\n"
        '<script type="application/ld+json">' + json.dumps(article_jsonld) + "</script>"
    )

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
{head(title, description, canonical)}

{jsonld_html}

<style>
{SHARED_CSS}
</style>
</head>
<body>

{nav_html()}

<header class="hero">
  <div class="wrap">
    <div class="eyebrow">New &middot; Rebate Stacking Calculator</div>
    <h1>If you do heat pump + solar + insulation together, what's your real total?</h1>
    <p class="lead">Most homeowners don't do one upgrade &mdash; they do two or three in the same renovation. This tool adds up the real, published rebate amounts for any combination you pick, for any of the {len(cities)} cities we cover.</p>
    <div class="hero-stats">
      <div class="hero-stat"><div class="num">{len(cities)}</div><div class="lbl">Cities</div></div>
      <div class="hero-stat"><div class="num">8</div><div class="lbl">Stackable categories</div></div>
      <div class="hero-stat"><div class="num">{len(region_order)}</div><div class="lbl">Regions</div></div>
    </div>
  </div>
</header>

<section class="picker-section">
  <div class="wrap">
    <div class="picker-card">
      <h2>Build your stack</h2>
      <div class="picker-row">
        <select id="city-select" aria-label="Choose your city" onchange="recalc()">
          <option value="">Choose your city&hellip;</option>
          {city_options}
        </select>
      </div>
      <div class="cat-checks" id="cat-checks">
        {cat_checks}
      </div>
      <div class="stack-total">
        <div>
          <div class="lbl">Your combined stack</div>
          <div class="amt-big" id="stack-total-amt">$0</div>
        </div>
        <div style="margin-left:auto;">
          <a id="stack-cta" href="#" style="display:none; padding:12px 22px; background: var(--amber); color:#fff; border-radius:8px; text-decoration:none; font-weight:700; font-size:14px;">Full city page &rarr;</a>
        </div>
      </div>
      <p id="stack-note" style="font-size:13px; color:var(--sage); margin-top:14px;">Pick a city and check the categories you're planning. Amounts of $0 mean that city doesn't currently have an open, published rebate in that category &mdash; we never invent a number to fill the gap.</p>
    </div>
  </div>
</section>

<section class="section" style="background:#fff;">
  <div class="wrap">
    <h2 class="section-title">How rebate stacking actually works</h2>
    <p class="section-sub">Home energy rebates come from different sources &mdash; federal, provincial or state, utility, and sometimes municipal &mdash; and most are designed to be combined rather than compete with each other. A heat pump rebate from your province and a solar rebate from your utility usually aren't mutually exclusive; they're separate programs with separate budgets. The catch is that each one has its own eligibility rules, paperwork, and sometimes a cap on how much of your total project cost any single rebate can cover. This calculator uses the real published dollar amounts from every city page we maintain, so the total you see is the total that's actually on offer &mdash; not a rounded-up estimate.</p>
  </div>
</section>

<section class="section" style="background: var(--paper-warm);">
  <div class="wrap">
    <h2 class="section-title" id="cities">Every city's stacking page</h2>
    <p class="section-sub">Each city below has its own dedicated stacking guide with worked examples and a full category breakdown. The amount shown is the maximum combined total across every open, quantified category we track for that city.</p>
    {"".join(region_blocks)}
  </div>
</section>

<section class="methodology">
  <div class="wrap">
    <div class="box">
      <h2 style="margin-top:0; font-size:24px;">Where these numbers come from</h2>
      <p>Every dollar figure in this calculator is pulled directly from the rebate amounts already published on each city's HomePowerRebate guide &mdash; the same underlying data that powers our <a href="/powerscore/">PowerScore</a> rankings. Nothing is estimated, rounded up, or invented. If a city doesn't have an open program with a published amount in a given category, that category shows $0 and is explained as unavailable rather than guessed at.</p>
      <p>Rebate programs change &mdash; funding caps get hit, provinces update tiers, utilities launch or close programs. We recheck city pages regularly and rebuild this calculator's data whenever they change.</p>
    </div>
  </div>
</section>

{footer_html(url)}

<script>
{NAV_JS}

/* ---- Stacking calculator page-specific JS ---- */
const STACK_CITIES = {json.dumps(js_cities)};
const STACK_CATS = {json.dumps(CATEGORIES)};

function recalc() {{
  const sel = document.getElementById('city-select');
  const key = sel.value;
  const city = STACK_CITIES.find(c => c.key === key);
  let total = 0;

  STACK_CATS.forEach(function(cat) {{
    const wrap = document.getElementById('check-' + cat);
    const amtEl = document.getElementById('amt-' + cat);
    const input = wrap.querySelector('input');
    if (!city) {{
      amtEl.textContent = '\\u2014';
      amtEl.className = 'amt';
      wrap.classList.remove('disabled');
      return;
    }}
    const val = city.cats[cat] || 0;
    if (val > 0) {{
      amtEl.textContent = '$' + val.toLocaleString();
      amtEl.className = 'amt';
      wrap.classList.remove('disabled');
    }} else {{
      amtEl.textContent = 'Not available';
      amtEl.className = 'amt zero';
      wrap.classList.add('disabled');
      input.checked = false;
    }}
    if (input.checked) total += val;
  }});

  document.getElementById('stack-total-amt').textContent = '$' + total.toLocaleString();
  const cta = document.getElementById('stack-cta');
  if (city) {{
    cta.style.display = 'inline-block';
    cta.href = city.url;
  }} else {{
    cta.style.display = 'none';
  }}
}}

document.getElementById('cat-checks').addEventListener('change', recalc);
recalc();
</script>

</body>
</html>
'''
    return url, page


# ============================================================
# Write city pages
# ============================================================
written_paths = []
thin_cities = []

for c in cities:
    url, page = build_city_page(c)
    out_path = ROOT / ("stacking-calculator/" + "/".join(url.strip("/").split("/")[1:]))
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "index.html").write_text(page)
    written_paths.append(url)
    avail = available_cats(c)
    if len(avail) < 3:
        thin_cities.append((c.region, c.slug, c.label, len(avail)))

hub_url, hub_page = build_hub_page()
hub_dir = ROOT / "stacking-calculator"
hub_dir.mkdir(parents=True, exist_ok=True)
(hub_dir / "index.html").write_text(hub_page)
written_paths.append(hub_url)

print(f"Wrote {len(written_paths)} pages (1 hub + {len(written_paths)-1} city pages)")
print(f"Cities with <3 open categories (thin data): {len(thin_cities)}")
for r, s, l, n in thin_cities:
    print(f"  {r}/{s} ({l}): {n} open categories")

# ============================================================
# Insert link into each city's existing hub page
# ============================================================
BADGE_RE = re.compile(
    r'(<div[^>]*style="text-align:center;[^"]*"><a href="/powerscore/#city-[^"]*"[^>]*>.*?</a></div>)',
    re.DOTALL,
)
# Fallback for the alternate city-page template (e.g. some NY pages) that
# wraps the PowerScore badge in a plain <div style="text-align:center...">
# without the .wrap class.
BADGE_RE_FALLBACK = re.compile(
    r'(<div[^>]*style="text-align:center;[^"]*"[^>]*><a href="/powerscore/#city-[^"]*"[^>]*>.*?</a></div>)',
    re.DOTALL,
)

linked = 0
link_failures = []
for c in cities:
    city_file = ROOT / c.url.strip("/") / "index.html"
    if not city_file.exists():
        link_failures.append((c.url, "city hub file missing"))
        continue
    content = city_file.read_text()
    stack_url = f"/stacking-calculator/{c.region}/{c.slug}/"
    if stack_url in content:
        linked += 1
        continue  # already linked (idempotent reruns)
    m = BADGE_RE.search(content) or BADGE_RE_FALLBACK.search(content)
    if not m:
        link_failures.append((c.url, "powerscore badge div not found"))
        continue
    insertion = (
        f'\n<div class="wrap" style="text-align:center; padding:10px 28px 0;">'
        f'<a href="{stack_url}" style="display:inline-flex; align-items:center; gap:8px; background:#fff; border:1px solid var(--rule); border-radius:999px; padding:8px 18px; font-size:13px; font-weight:600; color:var(--teal-deep); text-decoration:none; box-shadow:0 1px 3px rgba(10,42,46,0.08);">'
        f'<span aria-hidden="true">&#128172;</span><span>Rebate Stacking Calculator for {esc(c.label)} &rarr;</span></a></div>'
    )
    new_content = content[: m.end()] + insertion + content[m.end():]
    city_file.write_text(new_content)
    linked += 1

print(f"Linked from {linked}/{len(cities)} city hub pages")
if link_failures:
    print("Link failures:")
    for u, reason in link_failures:
        print(f"  {u}: {reason}")

# ============================================================
# Sitemap
# ============================================================
sitemap_path = ROOT / "sitemap.xml"
sitemap = sitemap_path.read_text()

new_urls = [f"https://homepowerrebate.com{hub_url}"]
for c in cities:
    new_urls.append(f"https://homepowerrebate.com/stacking-calculator/{c.region}/{c.slug}/")

existing_urls = set(re.findall(r"<loc>(.*?)</loc>", sitemap))
entries = []
for u in new_urls:
    if u in existing_urls:
        continue
    priority = "0.8" if u.endswith("/stacking-calculator/") else "0.6"
    entries.append(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>{priority}</priority></url>")

if entries:
    block = "\n".join(entries) + "\n"
    sitemap = sitemap.replace("</urlset>", block + "</urlset>")
    sitemap_path.write_text(sitemap)

print(f"Added {len(entries)} new sitemap entries")
