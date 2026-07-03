#!/usr/bin/env python3
"""
Generate all blog posts + the /blog hub from a shared template.
Body content is written per-post below; the shell (head, nav, footer, CSS)
is shared so every post stays on-brand automatically.
"""

import re
from pathlib import Path

SHELL_CSS = """
:root {
  --ink: #0a2a2e; --ink-soft: #1a3d42; --paper: #faf7f2; --paper-warm: #f5efe5;
  --teal: #0d4f5c; --teal-deep: #08363f; --amber: #d4751c; --amber-bright: #e88a2e;
  --sage: #6b8e7f; --green-money: #2d6a4f; --red-warning: #b04545; --rule: #d9d0c1;
  --shadow: 0 1px 2px rgba(10,42,46,0.04), 0 8px 24px rgba(10,42,46,0.06);
  --shadow-lg: 0 4px 12px rgba(10,42,46,0.08), 0 24px 48px rgba(10,42,46,0.12);
}
* { margin:0; padding:0; box-sizing:border-box; }
html { scroll-behavior:smooth; }
body { font-family:'Inter Tight', -apple-system, BlinkMacSystemFont, sans-serif; color:var(--ink); background:var(--paper); line-height:1.65; -webkit-font-smoothing:antialiased; }
.wrap { max-width:760px; margin:0 auto; padding:0 24px; }
.wrap-wide { max-width:1000px; margin:0 auto; padding:0 24px; }
h1, h2, h3 { font-family:'Fraunces', Georgia, serif; font-weight:500; line-height:1.2; letter-spacing:-0.01em; }
.logo { font-family:'Fraunces', Georgia, serif; font-size:22px; font-weight:600; color:var(--ink); text-decoration:none; letter-spacing:-0.01em; }
.logo-power { color:var(--amber); font-weight:700; }
.btn { display:inline-block; background:var(--amber); color:#fff; padding:14px 28px; border-radius:999px; text-decoration:none; font-weight:600; font-size:16px; transition:background .15s, transform .15s; border:none; cursor:pointer; }
.btn:hover { background:var(--amber-bright); transform:translateY(-1px); }
.btn-secondary { background:#fff; color:var(--ink); border:1.5px solid var(--rule); }
.btn-secondary:hover { background:var(--paper-warm); }
nav { display:flex; align-items:center; justify-content:space-between; padding:20px 24px; max-width:1000px; margin:0 auto; }
.nav-tag { font-size:13px; color:var(--sage); font-weight:600; letter-spacing:.04em; text-transform:uppercase; }
.post-header { background:var(--teal-deep); color:var(--paper); padding:56px 0 48px; }
.post-header .wrap { max-width:760px; }
.post-eyebrow { font-size:13px; color:var(--amber-bright); font-weight:700; letter-spacing:.08em; text-transform:uppercase; margin-bottom:16px; }
.post-header h1 { font-size:clamp(28px,5vw,42px); color:#fff; margin-bottom:16px; }
.post-meta { font-size:14px; color:rgba(250,247,242,0.65); }
article { padding:48px 0 64px; }
article p { font-size:17px; color:var(--ink-soft); margin-bottom:20px; }
article h2 { font-size:26px; margin:36px 0 14px; color:var(--ink); }
article h3 { font-size:20px; margin:28px 0 10px; color:var(--ink); }
article ul, article ol { margin:0 0 20px 22px; }
article li { font-size:16.5px; color:var(--ink-soft); margin-bottom:8px; }
article strong { color:var(--ink); }
article a { color:var(--teal-deep); font-weight:600; text-decoration:underline; text-decoration-color:var(--amber); text-underline-offset:2px; }
.callout { background:var(--paper-warm); border:1px solid var(--rule); border-left:4px solid var(--amber); border-radius:8px; padding:20px 24px; margin:28px 0; }
.callout p { margin-bottom:0; font-size:15.5px; }
.callout strong { color:var(--amber); }
.post-cta { background:var(--amber); color:#fff; border-radius:16px; padding:36px 32px; margin-top:40px; text-align:center; }
.post-cta h3 { color:#fff; margin-bottom:10px; font-size:22px; }
.post-cta p { color:rgba(255,255,255,0.9); margin-bottom:20px; font-size:15.5px; }
.post-cta .btn { background:var(--ink); }
.post-cta .btn:hover { background:var(--teal-deep); }
.related { border-top:1px solid var(--rule); margin-top:48px; padding-top:32px; }
.related h4 { font-size:14px; text-transform:uppercase; letter-spacing:.05em; color:var(--sage); margin-bottom:16px; }
.related a { display:block; color:var(--ink); font-weight:600; text-decoration:none; padding:10px 0; border-bottom:1px solid var(--rule); }
.related a:hover { color:var(--amber); }
/* Blog hub grid */
.hub-hero { background:var(--teal-deep); color:var(--paper); padding:64px 0 56px; }
.hub-hero .eyebrow { font-size:14px; color:var(--amber-bright); font-weight:600; letter-spacing:.08em; text-transform:uppercase; margin-bottom:18px; }
.hub-hero h1 { font-size:clamp(34px,6vw,52px); color:#fff; margin-bottom:18px; }
.hub-hero .sub { font-size:clamp(16px,2.2vw,19px); color:rgba(250,247,242,.82); max-width:640px; }
.post-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(280px,1fr)); gap:22px; margin-top:36px; }
.post-card { background:#fff; border:1px solid var(--rule); border-radius:16px; padding:26px; transition:all .2s; text-decoration:none; color:var(--ink); display:block; }
.post-card:hover { border-color:var(--amber); box-shadow:var(--shadow-lg); transform:translateY(-2px); }
.post-card .tag { font-size:11px; font-weight:700; letter-spacing:.05em; text-transform:uppercase; color:var(--amber); margin-bottom:10px; display:block; }
.post-card h3 { font-size:19px; margin-bottom:8px; line-height:1.3; }
.post-card p { font-size:14px; color:var(--ink-soft); }
footer { padding:40px 0 60px; border-top:1px solid var(--rule); margin-top:40px; }
footer .wrap-wide { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; }
footer p { font-size:13px; color:var(--sage); }
@media (max-width:720px) { .post-header { padding:40px 0 36px; } article { padding:36px 0 48px; } .post-grid { grid-template-columns:1fr; } }
"""

def shell(title, description, slug, eyebrow, published, body_html, related):
    related_html = "".join(f'<a href="/blog/{r["slug"]}">{r["title"]} &rarr;</a>' for r in related)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | HomePowerRebate Blog</title>
<meta name="description" content="{description}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="https://homepowerrebate.com/blog/{slug}">
<meta name="google-site-verification" content="Yyio4MZpG_tVGKuE9hbSKTYb0Yo9LFWoNF_3_UxVkGE" />

<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://homepowerrebate.com/blog/{slug}">
<meta property="og:locale" content="en_CA">
<meta property="article:published_time" content="{published}T09:00:00-07:00">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "description": "{description}",
  "datePublished": "{published}",
  "dateModified": "{published}",
  "author": {{ "@type": "Organization", "name": "HomePowerRebate", "url": "https://homepowerrebate.com" }},
  "publisher": {{ "@type": "Organization", "name": "HomePowerRebate", "url": "https://homepowerrebate.com" }},
  "mainEntityOfPage": "https://homepowerrebate.com/blog/{slug}"
}}
</script>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "https://homepowerrebate.com" }},
    {{ "@type": "ListItem", "position": 2, "name": "Blog", "item": "https://homepowerrebate.com/blog" }},
    {{ "@type": "ListItem", "position": 3, "name": "{title}", "item": "https://homepowerrebate.com/blog/{slug}" }}
  ]
}}
</script>

<style>{SHELL_CSS}</style>
</head>
<body>

<nav>
  <a href="/" class="logo">Home<span class="logo-power">Power</span>Rebate</a>
  <span class="nav-tag"><a href="/blog" style="color:inherit; text-decoration:none;">Blog</a></span>
</nav>

<header class="post-header">
  <div class="wrap">
    <div class="post-eyebrow">{eyebrow}</div>
    <h1>{title}</h1>
    <div class="post-meta">Published {published} &middot; HomePowerRebate</div>
  </div>
</header>

<article>
  <div class="wrap">
    {body_html}

    <div class="related">
      <h4>Keep reading</h4>
      {related_html}
    </div>
  </div>
</article>

<footer>
  <div class="wrap-wide">
    <a href="/" class="logo">Home<span class="logo-power">Power</span>Rebate</a>
    <p>&copy; 2026 HomePowerRebate. Independent installer matching service, not affiliated with BC Hydro.</p>
  </div>
</footer>

</body>
</html>
"""

def cta(heading, sub, href, label):
    return f"""
    <div class="post-cta">
      <h3>{heading}</h3>
      <p>{sub}</p>
      <a href="{href}" class="btn">{label} &rarr;</a>
    </div>
    """

POSTS = []

# ---------------------------------------------------------------------------
POSTS.append({
    'slug': 'is-bc-hydro-solar-rebate-worth-it',
    'title': 'Is the BC Hydro Solar Rebate Actually Worth It? We Ran the Numbers',
    'description': 'A skeptical, honest look at solar payback periods in BC with the BC Hydro rebate factored in — including when it does NOT make sense.',
    'eyebrow': 'Straight talk',
    'published': '2026-06-15',
    'body': """
    <p>"Solar payback is 15 years, isn't that a scam?" We see this question a lot, usually from someone who got a quote that didn't add up, or read a scary comment on Reddit. Fair question. Let's actually run the math instead of just saying "trust us."</p>

    <h2>The real math, city by city</h2>
    <p>Payback time depends on three things: how much sun your city gets, what you pay per kWh, and how big your rebate is. In BC, with the Power Smart 2.0 rebate factored in, typical payback runs <strong>6 to 12 years</strong> depending on where you live — not 15 to 20, which is the number you'd get <em>without</em> any rebate.</p>
    <ul>
      <li><strong>Kamloops, Vernon:</strong> best sun in the province, 6&ndash;9 year payback</li>
      <li><strong>Kelowna, Prince George, Fraser Valley:</strong> 7&ndash;11 years</li>
      <li><strong>Vancouver, Surrey, coastal cities:</strong> 9&ndash;12 years, more cloud cover, more expensive real estate driving up install cost per sq ft of roof</li>
    </ul>

    <h2>What actually makes payback longer than advertised</h2>
    <p>When people get burned, it's usually one of these three things, not the technology itself:</p>
    <ol>
      <li><strong>An unapproved battery.</strong> Install a Tesla Powerwall in BC and you lose the entire $5,000 battery rebate. That alone can add 3&ndash;4 years to your payback.</li>
      <li><strong>Skipping Peak Saver enrollment.</strong> This is a free, reversible program that adds roughly $3,000 over 10 years. Not enrolling leaves real money on the table for no reason.</li>
      <li><strong>An oversized system.</strong> Some installers size systems bigger than your roof or usage needs to hit a bigger sale. Bigger isn't always better — it just means a bigger loan.</li>
    </ol>

    <div class="callout">
      <p><strong>When solar does NOT make sense:</strong> if you're planning to sell your home in the next 2&ndash;3 years, if your roof needs replacement soon (do that first), or if you get heavy shade for most of the day. We'd rather tell you this now than have an installer tell you otherwise later.</p>
    </div>

    <h2>The honest bottom line</h2>
    <p>With the BC Hydro rebate, Peak Saver rewards, and lower monthly bills stacked together, most BC homeowners see $18,000&ndash;$22,000 in total value over 10 years on a system that costs $25,000&ndash;$40,000 installed. That's real, it's math you can check yourself, and it's very different from a system with no rebate attached.</p>
    """,
    'cta': cta("See your own numbers", "Answer 4 quick questions and get your city's real payback estimate — no email required.", "/ca/bc", "Check my savings"),
    'related': ['tesla-powerwall-mistake', 'how-much-does-battery-save-during-outage']
})

# ---------------------------------------------------------------------------
POSTS.append({
    'slug': 'tesla-powerwall-mistake',
    'title': "Why Your Neighbor's Tesla Powerwall Got Zero Rebate",
    'description': "Tesla Powerwall isn't on BC Hydro's approved battery list. Here's what that actually costs you, and which batteries qualify for the full $5,000 rebate.",
    'eyebrow': 'Common mistake',
    'published': '2026-06-18',
    'body': """
    <p>This is the single most expensive mistake we see BC homeowners make. Someone hears "Powerwall" — it's the battery everyone's heard of — and assumes it's the safe, obvious choice. In BC, it's the choice that costs you $5,000.</p>

    <h2>Why isn't Tesla on the list?</h2>
    <p>BC Hydro maintains an approved product list for the Power Smart 2.0 rebate. Tesla has simply never gotten its Powerwall certified for the BC program. It's not a quality judgment — Powerwall is a fine product — it's a paperwork and certification issue between Tesla and BC Hydro that, as of today, hasn't been resolved.</p>
    <p>The result: <strong>install a Powerwall in BC and your battery rebate is $0</strong>, full stop. Not reduced. Zero.</p>

    <h2>What's actually approved</h2>
    <p>Several battery systems are fully approved and qualify for the full $5,000 rebate when enrolled in Peak Saver:</p>
    <ul>
      <li><strong>Eguana Evolve</strong> &mdash; Canadian-engineered, built for cold-climate performance including Northern BC winters</li>
      <li>Enphase IQ</li>
      <li>LG Home</li>
      <li>SolarEdge Home</li>
      <li>Panasonic EverVolt</li>
      <li>Generac PWRcell</li>
    </ul>
    <p>All of these do the same fundamental job as a Powerwall &mdash; backup power during an outage, paired with solar to charge the battery &mdash; and all of them qualify for the same rebate a Powerwall doesn't.</p>

    <h2>How to check before you sign anything</h2>
    <p>Before you agree to any battery installation in BC, ask your installer one direct question: <em>"Is this battery on BC Hydro's current Power Smart 2.0 approved list?"</em> A legitimate installer will answer immediately. If they hesitate or change the subject, that's your signal to get a second opinion.</p>

    <div class="callout">
      <p><strong>Already have a quote with a Powerwall in it?</strong> Ask for the same system with an approved battery instead. The install cost is usually similar &mdash; the $5,000 difference is purely the missed rebate.</p>
    </div>
    """,
    'cta': cta("Get matched with an approved-battery installer", "We only route homeowners to installers using BC Hydro-approved battery systems.", "/ca/bc", "Find my city"),
    'related': ['is-bc-hydro-solar-rebate-worth-it', 'red-flags-choosing-solar-installer']
})

# ---------------------------------------------------------------------------
POSTS.append({
    'slug': 'bc-hydro-rebate-deadlines-2026',
    'title': 'BC Hydro Rebate Deadlines in 2026: What Changes and When',
    'description': 'HPCN installer certification becomes mandatory June 1, 2026. Rate schedules change July 1, 2026. Here is what BC homeowners need to know before those dates.',
    'eyebrow': 'Time-sensitive',
    'published': '2026-05-20',
    'body': """
    <p>Two real deadlines are coming up on the BC Hydro Power Smart 2.0 program, and both affect what your installation actually costs. Neither is marketing hype &mdash; these are documented program changes. Here's what they mean in plain language.</p>

    <h2>June 1, 2026: HPCN certification becomes mandatory</h2>
    <p>Starting this date, your installer must be certified through BC Hydro's Home Performance Contractor Network (HPCN) for your project to qualify for the rebate. Before this date, some installers were operating under looser requirements.</p>
    <p><strong>What this means for you:</strong> if you're getting quotes right now, confirm your installer is HPCN certified &mdash; or actively completing certification. An uncertified installer after June 1 means no rebate, no matter how good the install is.</p>

    <h2>July 1, 2026: Rate schedule 1289 transitions to 2289</h2>
    <p>BC Hydro is changing its residential rate structure. This affects how your monthly bill is calculated and, by extension, how fast your solar + battery system pays for itself. If you're on the fence, installing before this date locks in your project under the current, well-understood rate structure.</p>

    <h2>Should you rush your decision?</h2>
    <p>No &mdash; but you also shouldn't drag your feet without a reason. If you were already planning to move forward this year, there's no upside to waiting past June 1 for HPCN reasons, since a certified installer costs you nothing extra. If you're still deciding, focus on getting your quote and installer lined up now so the actual install lands comfortably before either date.</p>

    <div class="callout">
      <p><strong>The bigger picture:</strong> Power Smart 2.0 is a 3-year, $1.1 billion program. These aren't signs it's ending &mdash; they're normal maturity steps as BC Hydro tightens quality control on installers.</p>
    </div>
    """,
    'cta': cta("Lock in your installer now", "Get matched with an HPCN-certified installer in your city before the June 1 deadline.", "/ca/bc", "Find my city"),
    'related': ['tesla-powerwall-mistake', 'red-flags-choosing-solar-installer']
})

# ---------------------------------------------------------------------------
POSTS.append({
    'slug': 'why-solar-quotes-vary-so-much',
    'title': 'I Got 3 Solar Quotes in Kelowna — Here’s Why They Were $8,000 Apart',
    'description': 'Solar and battery quotes for the same BC home can vary by thousands of dollars. Here is exactly what drives the difference, so you know what a fair quote looks like.',
    'eyebrow': 'Buyer’s guide',
    'published': '2026-06-22',
    'body': """
    <p>If you've gotten more than one solar quote in BC, you've probably seen this: three installers, the same roof, the same house &mdash; and quotes that differ by five or eight thousand dollars. That's not necessarily someone trying to rip you off. Here's what actually drives the gap.</p>

    <h2>1. Panel and battery brand</h2>
    <p>Not all approved equipment costs the same. A Tier 1 panel brand with a strong warranty costs more than a budget panel &mdash; both might be perfectly fine, but the price difference is real and legitimate.</p>

    <h2>2. Battery choice</h2>
    <p>Battery systems range widely in price. An Eguana Evolve, an LG Home, and a Generac PWRcell all qualify for the same BC Hydro rebate, but they don't cost the same to buy or install. This alone can account for a few thousand dollars of quote variance.</p>

    <h2>3. Roof complexity</h2>
    <p>A simple south-facing roof with no obstructions installs faster and cheaper than a roof with multiple angles, skylights, or a steep pitch. Installers pricing the same roof should be quoting similar labour &mdash; if one quote is dramatically cheaper here, ask why.</p>

    <h2>4. System size</h2>
    <p>This is the one to watch closely. Some installers size a system larger than your actual usage or roof space justifies &mdash; more panels, bigger sale, bigger commission. Compare quotes by <em>size and rebate-eligible cost</em>, not just the bottom-line number.</p>

    <h2>5. Permit and inspection fees</h2>
    <p>These are usually similar city to city but occasionally get bundled differently &mdash; some installers include them up front, others add them later. Ask explicitly what's included.</p>

    <div class="callout">
      <p><strong>What a fair comparison looks like:</strong> same system size (kW), same battery capacity (kWh), both quotes confirming BC Hydro-approved equipment, both installers HPCN certified. Once those four things match, the price difference tells you something real.</p>
    </div>

    <h2>Why we only send you one quote</h2>
    <p>This is exactly why HomePowerRebate matches you with a single vetted installer instead of running a bidding war between five companies. You get one straightforward quote from someone who already knows the approved equipment list and the local permitting process &mdash; not a race to the bottom that usually ends in a smaller, worse system.</p>
    """,
    'cta': cta("Skip the bidding war", "Get matched with one trusted, HPCN-certified installer in your city.", "/ca/bc", "Find my city"),
    'related': ['red-flags-choosing-solar-installer', 'is-bc-hydro-solar-rebate-worth-it']
})

# ---------------------------------------------------------------------------
POSTS.append({
    'slug': 'heat-pumps-cold-climate-bc-winter',
    'title': 'Do Heat Pumps Actually Work in a BC Winter?',
    'description': 'The most common heat pump objection in BC is cold-weather performance. Here is how cold-climate heat pumps (ccASHP) actually handle a BC winter, with real numbers.',
    'eyebrow': 'Common question',
    'published': '2026-06-10',
    'body': """
    <p>"Won't I freeze if it hits -15&deg;C?" is the question we hear more than any other about heat pumps in BC. It's a fair worry &mdash; older heat pump technology genuinely struggled in cold climates. That's no longer true, but the reputation stuck around.</p>

    <h2>Old heat pumps vs. cold-climate heat pumps</h2>
    <p>The heat pumps that gave the technology a bad reputation years ago lost most of their heating capacity below freezing, sometimes requiring backup electric heat to kick in constantly. Modern <strong>cold-climate air source heat pumps (ccASHP)</strong> are a different category of equipment, engineered specifically to maintain heating output well below 0&deg;C.</p>

    <h2>What "cold-climate rated" actually means</h2>
    <p>BC Hydro's rebate program only covers heat pumps on its qualified product list, and that list requires cold-climate rating. In practice, that means the unit is tested and rated to maintain a meaningful percentage of its heating capacity down to around -15&deg;C to -25&deg;C, depending on the specific model.</p>
    <p>For context: even in Prince George and other Northern BC cities, where winter lows regularly hit -15&deg;C to -20&deg;C, properly sized ccASHP units are installed and performing as the primary heat source &mdash; not just a summer AC unit that happens to also heat.</p>

    <h2>What actually matters for winter performance</h2>
    <ul>
      <li><strong>Correct sizing.</strong> A heat pump sized for your specific home's heat loss, not a generic estimate, is the single biggest factor in cold-weather comfort.</li>
      <li><strong>Cold-climate rating.</strong> Confirm the specific model is BC Hydro qualified &mdash; not just "a heat pump," but one certified for this climate.</li>
      <li><strong>Backup heat strategy.</strong> Many BC installs keep existing baseboard or furnace heat as backup for the coldest handful of days per year. This is normal and doesn't mean the heat pump "doesn't work."</li>
    </ul>

    <div class="callout">
      <p><strong>The BC Hydro rebate</strong> covers up to $4,000 for a whole-home heat pump (80%+ of your home's conditioned space) or up to $1,500 for partial coverage &mdash; but only for cold-climate rated units, which is one more reason to confirm the specific model before signing anything.</p>
    </div>
    """,
    'cta': cta("See your heat pump rebate", "Check your city's heat pump rebate and get matched with a certified installer.", "/programs", "See all programs"),
    'related': ['bc-hydro-rebate-deadlines-2026', 'stack-bc-hydro-greener-homes']
})

# ---------------------------------------------------------------------------
POSTS.append({
    'slug': 'bc-hydro-peak-saver-explained',
    'title': "The BC Hydro Peak Saver Program Explained (What They Don't Advertise)",
    'description': 'Peak Saver sounds like BC Hydro controlling your battery. Here is exactly what it does, what it pays, and how to override it whenever you want.',
    'eyebrow': 'Program explainer',
    'published': '2026-06-05',
    'body': """
    <p>"Wait, BC Hydro can control my battery?" is a completely reasonable reaction the first time someone hears about Peak Saver. It sounds invasive. In practice, it's a lot more limited &mdash; and a lot more profitable for you &mdash; than that first impression suggests.</p>

    <h2>What Peak Saver actually does</h2>
    <p>When you enroll your home battery in Peak Saver, BC Hydro can briefly draw power from your battery during periods of very high demand across the grid &mdash; think a cold winter evening when everyone's heating and cooking at once. This is called a demand-response event. In exchange, they pay you.</p>

    <h2>What it pays</h2>
    <ul>
      <li><strong>Up to $500</strong> one-time enrollment incentive</li>
      <li><strong>Up to $250 per winter season</strong>, ongoing</li>
      <li><strong>~$3,000 total</strong> over a typical 10-year horizon</li>
    </ul>
    <p>This is on top of &mdash; not instead of &mdash; your solar and battery rebate.</p>

    <h2>Can you actually override it?</h2>
    <p>Yes. Enrollment does not mean you lose control of your own battery. You can override a demand-response event at any time, for any reason &mdash; if you need your battery reserved for an approaching storm, or you're just not comfortable with an event that day, you say no and keep your power.</p>

    <h2>Why this matters for the grid, not just your wallet</h2>
    <p>Demand-response programs like Peak Saver are part of how BC Hydro avoids building new power plants just to cover a few peak-demand hours per year. Every enrolled home battery is a small buffer that reduces strain during exactly the moments the grid is under the most pressure &mdash; which is also, not coincidentally, the moments you'd most want backup power yourself.</p>

    <div class="callout">
      <p><strong>Bottom line:</strong> Peak Saver is a free, reversible, opt-out-anytime program that adds roughly $3,000 of value over a decade. Skipping it because it "sounds weird" leaves real money on the table for no real downside.</p>
    </div>
    """,
    'cta': cta("Enroll when you install", "Your matched installer walks you through Peak Saver enrollment as part of your solar + battery install.", "/ca/bc", "Find my city"),
    'related': ['is-bc-hydro-solar-rebate-worth-it', 'how-much-does-battery-save-during-outage']
})

# ---------------------------------------------------------------------------
POSTS.append({
    'slug': 'how-much-does-battery-save-during-outage',
    'title': 'How Much Does a Home Battery Actually Save You During a Power Outage?',
    'description': 'A realistic breakdown of what a home battery keeps running during a BC power outage, and how that compares to the cost of a bad storm without one.',
    'eyebrow': 'Real numbers',
    'published': '2026-06-25',
    'body': """
    <p>Every major BC windstorm brings the same search spike: "home battery backup power outage." Fair &mdash; nothing focuses the mind like sitting in the dark. Here's a realistic, non-hyped answer to what a battery actually keeps running, and for how long.</p>

    <h2>What a typical home battery can power</h2>
    <p>Most residential batteries installed in BC (10&ndash;13 kWh capacity) are sized to run your home's essential circuits &mdash; not your entire house at full draw, but the things that matter during an outage:</p>
    <ul>
      <li>Fridge and freezer (protects hundreds of dollars in food)</li>
      <li>Lights</li>
      <li>Your furnace or heat pump's electronic controls and blower</li>
      <li>Wifi router and a few outlets for phones, laptops, medical devices</li>
    </ul>
    <p>Depending on system size and what's running, that's typically <strong>8 to 24+ hours</strong> of backup &mdash; and if it's paired with solar, that window extends every sunny day the outage continues.</p>

    <h2>What it costs to be without one</h2>
    <p>The real cost of a multi-day outage isn't dramatic &mdash; it's a few hundred dollars in spoiled groceries, a hotel night if your heat is out and it's freezing, and for some households, a genuine safety issue if someone depends on powered medical equipment. None of that shows up on a spreadsheet until it happens to you.</p>

    <h2>How this connects to the rebate</h2>
    <p>The BC Hydro rebate exists specifically to encourage this kind of resilience at the household level &mdash; up to $5,000 toward a battery, plus Peak Saver rewards for keeping it enrolled in the grid's demand-response program. The rebate is the financial case; outage protection is the actual reason most BC homeowners pull the trigger.</p>

    <div class="callout">
      <p><strong>Sizing tip:</strong> talk to your installer about which circuits actually need backup. A smaller, correctly-scoped system covering your essentials is usually a better value than an oversized system trying to run everything.</p>
    </div>
    """,
    'cta': cta("See your battery rebate", "Up to $5,000 from BC Hydro when your battery is Peak Saver enrolled.", "/ca/bc", "Find my city"),
    'related': ['bc-hydro-peak-saver-explained', 'tesla-powerwall-mistake']
})

# ---------------------------------------------------------------------------
POSTS.append({
    'slug': 'fortisbc-vs-bc-hydro-rebates',
    'title': 'FortisBC vs. BC Hydro: Why Your Rebate Options Are Completely Different',
    'description': 'Not sure which utility you have? Here is how to check, and why it completely changes which BC home energy rebates you qualify for.',
    'eyebrow': 'Clear this up first',
    'published': '2026-06-12',
    'body': """
    <p>This sounds basic, but it trips up more people than you'd expect: BC has two major utilities, BC Hydro and FortisBC, and they run separate rebate programs. If you're reading about a rebate that doesn't seem to apply to you, this is usually why.</p>

    <h2>How to check which one you have</h2>
    <p>Look at your power bill &mdash; the company name at the top tells you. Most of the province is BC Hydro. FortisBC primarily serves the Southern Interior (Kelowna area electricity in some pockets, though most of Kelowna is BC Hydro), parts of the Kootenays, and it's also BC's main natural gas provider almost everywhere.</p>

    <h2>BC Hydro: Power Smart 2.0</h2>
    <p>This is the program HomePowerRebate specializes in &mdash; up to $10,000 for solar + battery, up to $4,000 for heat pumps, plus Peak Saver rewards. It's a $1.1 billion, 3-year commitment and it's the most generous solar/battery rebate currently available in BC.</p>

    <h2>FortisBC: different programs, different focus</h2>
    <p>FortisBC's home energy programs lean toward efficiency upgrades &mdash; free home energy evaluations, insulation, and heat pump incentives &mdash; rather than a dedicated solar + battery rebate on the same scale as Power Smart 2.0. If you're a FortisBC customer specifically looking at solar, your rebate math will look different, and it's worth checking FortisBC's own program details directly.</p>

    <div class="callout">
      <p><strong>The one thing to get right first:</strong> confirm your utility before you get quotes. An installer who doesn't ask this question, or gives you BC Hydro-specific rebate numbers without checking, is skipping a step that changes your entire budget.</p>
    </div>

    <h2>See everything side by side</h2>
    <p>We built a full comparison of every BC and federal home energy program &mdash; BC Hydro, FortisBC, and Canada Greener Homes &mdash; so you can see exactly what applies to your situation in one place.</p>
    """,
    'cta': cta("Compare every BC program", "See BC Hydro, FortisBC, and federal rebates side by side.", "/programs", "See all programs"),
    'related': ['stack-bc-hydro-greener-homes', 'is-bc-hydro-solar-rebate-worth-it']
})

# ---------------------------------------------------------------------------
POSTS.append({
    'slug': 'stack-bc-hydro-greener-homes',
    'title': 'Can You Stack the BC Hydro Rebate With Canada Greener Homes? A Real Example',
    'description': 'BC homeowners can often combine BC Hydro Power Smart 2.0 with the federal Canada Greener Homes program. Here is a real, itemized example.',
    'eyebrow': 'Worked example',
    'published': '2026-06-28',
    'body': """
    <p>"Can I combine the BC Hydro rebate with the federal one?" is a question with a genuinely useful answer: often, yes &mdash; because they cover different things. Here's a real, itemized example instead of a vague "it depends."</p>

    <h2>Why they can stack</h2>
    <p>BC Hydro's Power Smart 2.0 program covers solar panels, home batteries, and (separately) heat pumps for BC Hydro customers specifically. The federal Canada Greener Homes Initiative covers a broader set of retrofits &mdash; insulation, windows and doors, air sealing, and heat pumps &mdash; for any Canadian homeowner, regardless of utility. Where the categories don't overlap, you can typically claim both.</p>

    <h2>A worked example: Metro Vancouver home</h2>
    <table style="width:100%; border-collapse:collapse; margin:20px 0;">
      <tr style="border-bottom:1px solid var(--rule);"><td style="padding:10px 0;">BC Hydro solar rebate</td><td style="padding:10px 0; text-align:right; font-weight:700; color:var(--green-money);">+$5,000</td></tr>
      <tr style="border-bottom:1px solid var(--rule);"><td style="padding:10px 0;">BC Hydro battery rebate</td><td style="padding:10px 0; text-align:right; font-weight:700; color:var(--green-money);">+$5,000</td></tr>
      <tr style="border-bottom:1px solid var(--rule);"><td style="padding:10px 0;">Canada Greener Homes &mdash; window upgrade</td><td style="padding:10px 0; text-align:right; font-weight:700; color:var(--green-money);">+$2,000</td></tr>
      <tr><td style="padding:10px 0; font-weight:700;">Total rebates claimed</td><td style="padding:10px 0; text-align:right; font-weight:700; font-size:18px; color:var(--green-money);">$12,000</td></tr>
    </table>

    <h2>Watch for this: heat pumps overlap</h2>
    <p>Heat pumps are the one category where both programs offer a rebate, and you generally cannot claim the full amount from both for the same unit. Confirm the specific stacking rule with each program before assuming you'll get both checks &mdash; this is the one place people get their expectations wrong.</p>

    <h2>The practical order of operations</h2>
    <ol>
      <li>Confirm your utility (BC Hydro or FortisBC) &mdash; this determines your provincial options</li>
      <li>Get your solar + battery quote and BC Hydro rebate locked in first</li>
      <li>Separately look at Canada Greener Homes for insulation, windows, or air sealing if you're doing a broader retrofit</li>
      <li>Apply for each program according to its own paperwork &mdash; they don't share an application</li>
    </ol>

    <div class="callout">
      <p><strong>Always confirm current stacking rules directly with each program before starting work</strong> &mdash; rebate rules do get updated, and this is the kind of detail worth double-checking rather than assuming.</p>
    </div>
    """,
    'cta': cta("See every program in one place", "Full comparison of BC Hydro, FortisBC, and federal home energy rebates.", "/programs", "See all programs"),
    'related': ['fortisbc-vs-bc-hydro-rebates', 'bc-hydro-rebate-deadlines-2026']
})

# ---------------------------------------------------------------------------
POSTS.append({
    'slug': 'red-flags-choosing-solar-installer',
    'title': 'Red Flags When Choosing a Solar Installer in BC',
    'description': 'The most common complaints BC homeowners have about solar installers, and how to spot the warning signs before you sign a contract.',
    'eyebrow': 'Buyer protection',
    'published': '2026-06-30',
    'body': """
    <p>Trust is the number one hesitation we hear from BC homeowners considering solar &mdash; not "does it work," but "will I get taken advantage of." Fair worry. Here are the patterns worth watching for before you sign anything.</p>

    <h2>1. Pressure to sign today</h2>
    <p>"This price is only good if you sign right now" is a sales tactic, not a real constraint. Legitimate installers can hold a quote for a reasonable period. If someone's pushing same-day signatures, slow down.</p>

    <h2>2. Vague or shifting rebate promises</h2>
    <p>An installer should be able to tell you exactly which BC Hydro rebate categories your specific system qualifies for &mdash; solar amount, battery amount, whether it's HPCN-certified work &mdash; not a rounded-up "up to $10,000, probably" without specifics tied to your equipment.</p>

    <h2>3. No mention of the approved equipment list</h2>
    <p>If a battery brand isn't on BC Hydro's approved list, your rebate on that component is zero. An installer who doesn't proactively confirm this &mdash; especially if they're recommending a well-known brand like Tesla &mdash; is either uninformed or hoping you won't check.</p>

    <h2>4. No HPCN certification, or certification they can't show you</h2>
    <p>As of June 1, 2026, HPCN certification is mandatory for the rebate to apply. Ask directly, and ask for proof if you're not sure.</p>

    <h2>5. A single quote with no comparison basis</h2>
    <p>You don't need five competing bids, but you should understand what a reasonable price range looks like for your system size before signing. If a quote is dramatically higher or lower than what similar homes in your area are paying, ask why specifically.</p>

    <h2>6. Reluctance to explain sizing</h2>
    <p>Your installer should be able to explain, in plain terms, why they're proposing a system of a specific size &mdash; based on your roof, your usage, and your goals. "This is what everyone gets" is not an answer.</p>

    <div class="callout">
      <p><strong>Why we only work with one vetted installer per city:</strong> instead of asking you to screen five companies yourself, we do that vetting up front &mdash; HPCN certification, approved equipment, transparent pricing &mdash; so you're not the one running background checks on a $30,000 decision.</p>
    </div>
    """,
    'cta': cta("Skip the guesswork", "Get matched with one pre-vetted, HPCN-certified installer in your city.", "/ca/bc", "Find my city"),
    'related': ['why-solar-quotes-vary-so-much', 'tesla-powerwall-mistake']
})


# ---------------------------------------------------------------------------
POSTS.append({
    'slug': 'heat-pump-bc-winter-actually-works',
    'title': 'Heat Pumps Work in BC Winter at -25°C: Data, Not Fear',
    'description': 'Modern cold-climate heat pumps extract heat even at -25°C and work reliably in BC winters. Here's the data.',
    'eyebrow': 'Cold climate guide',
    'published': '2026-07-03',
    'body': """<p>Every BC homeowner asks: "Will a heat pump actually heat my house at -20°C?" Yes, modern cold-climate heat pumps work reliably in BC winters.</p>
    <h2>How it works in extreme cold</h2>
    <p>A heat pump extracts heat from outside air and moves it inside. Modern units use enhanced vapor injection compressors and advanced inverters to work at -25°C or lower with 80%+ efficiency. Mitsubishi Hyper-Heat, Fujitsu XLTH, Daikin Fit, and Bosch IDS 2.0 all qualify for BC Hydro rebates and work reliably in BC.</p>
    <h2>The payback</h2>
    <p>Cost: $8,000–$12,000. BC Hydro rebate: $4,000 (whole-home) or $1,500 (partial). Annual savings: $1,000–$2,000 depending on fuel. Payback: 4–6 years, often free if income-qualified ($16,000 rebate instead of $4,000).</p>
    <div class="callout"><p><strong>Bottom line:</strong> BC winters don't break modern heat pumps. The engineering is solid.</p></div>""",
    'cta': cta("Check your heat pump savings", "See what a heat pump retrofit costs and returns in your city.", "/ca/bc", "Find my city"),
    'related': ['solar-heat-pump-water-heater-stacking-real-numbers', 'is-bc-hydro-solar-rebate-worth-it']
})

# ---------------------------------------------------------------------------
POSTS.append({
    'slug': 'peak-saver-14-day-window-3500-mistake',
    'title': 'The $3,500 Mistake: Peak Saver Enrollment and the 14-Day Window',
    'description': 'If you install a battery but miss Peak Saver enrollment within 14 days, your rebate shrinks from $5,000 to $1,500. Here's how to avoid it.',
    'eyebrow': 'Critical deadline',
    'published': '2026-07-03',
    'body': """<p>Your battery is installed. You got a $5,000 rebate. Done, right? Wrong. If you don't enroll in Peak Saver within 14 days of interconnection approval, your rebate shrinks to $1,500. That's a $3,500 mistake happening constantly.</p>
    <h2>What changed April 1, 2026</h2>
    <p>Before: install battery, claim $5,000. After: $5,000 only if enrolled in Peak Saver within 14 days, else $1,500. Same battery. Different payout. One deadline.</p>
    <h2>The 14-day clock</h2>
    <p>Timeline: installer installs → submits to BC Hydro → BC Hydro approves (5–10 days) → 14-day clock starts. You must enroll by day 14 or lose $3,500. BC Hydro won't waive it.</p>
    <h2>Make sure it doesn't happen</h2>
    <ul><li>Before signing: Ask installer "Will you enroll my battery in Peak Saver?" Get it in writing.</li>
    <li>After approval: Installer contacts you immediately. Day 1, not day 10.</li>
    <li>If no contact by day 3: Call them. Don't wait.</li></ul>
    <div class="callout"><p><strong>Why this matters:</strong> an installer who doesn't mention Peak Saver or leaves it to you is signaling they don't manage critical details.</p></div>""",
    'cta': cta("Get matched with a detail-oriented installer", "We work with installers who handle Peak Saver so you don't lose $3,500 by accident.", "/ca/bc", "Find my city"),
    'related': ['is-bc-hydro-solar-rebate-worth-it', 'tesla-powerwall-mistake']
})

# ---------------------------------------------------------------------------
POSTS.append({
    'slug': 'solar-heat-pump-water-heater-stacking-real-numbers',
    'title': 'Stack $18,000 in BC Energy Rebates: Solar + Heat Pump + Water Heater',
    'description': 'BC homeowners can stack rebates from BC Hydro, CleanBC, and federal programs. Here's how one project returns $19,000.',
    'eyebrow': 'Full home retrofit',
    'published': '2026-07-03',
    'body': """<p>Most BC homeowners don't know you can stack rebates. They see solar ($5,000) and maybe heat pump ($4,000) but don't realize you can claim both, plus water heater, plus multi-upgrade bonuses. Total: $15,000–$22,000 in one year.</p>
    <h2>The stacking rule</h2>
    <p>BC Hydro, CleanBC, and federal programs stack—you can claim from multiple programs for different upgrades in the same project. Solar + battery + heat pump + water heater all in one year. All on one house.</p>
    <h2>Real example: Metro Vancouver homeowner</h2>
    <p>Solar (8 kW): $5,000 | Battery (5 kWh): $5,000 | Heat pump: $4,000 | Water heater: $1,000 | Multi-upgrade bonus: $2,000 | <strong>Total: $17,000</strong></p>
    <h2>Income-qualified: $35,000+</h2>
    <p>If you qualify (household income under $95k–$185k depending on family size), CleanBC income-qualified rebates 2x the amounts. Heat pump alone jumps from $4k to $16k. Same project, different income bracket = $28,000–$35,000 back.</p>
    <div class="callout"><p><strong>The gotcha:</strong> installers often specialize in solar OR heat pumps, not both. They quote solar ($5k) and miss stacking heat pump ($4k) and water heater ($1k) opportunities. You need someone who sees the whole home.</p></div>""",
    'cta': cta("See your stacking potential", "Each BC city has different climate and costs. Get your specific numbers.", "/ca/bc", "Check my city"),
    'related': ['peak-saver-14-day-window-3500-mistake', 'fortisbc-vs-bc-hydro-rebates']
})

# ---------------------------------------------------------------------------

def slugify_title_map():
    return {p['slug']: p['title'] for p in POSTS}

def main():
    title_map = slugify_title_map()
    blog_dir = Path('blog')
    blog_dir.mkdir(exist_ok=True)

    for post in POSTS:
        related = [{'slug': s, 'title': title_map[s]} for s in post['related']]
        html = shell(
            title=post['title'],
            description=post['description'],
            slug=post['slug'],
            eyebrow=post['eyebrow'],
            published=post['published'],
            body_html=post['body'] + post['cta'],
            related=related
        )
        post_dir = blog_dir / post['slug']
        post_dir.mkdir(exist_ok=True)
        (post_dir / 'index.html').write_text(html, encoding='utf-8')
        print(f'✓ {post["slug"]:38} → blog/{post["slug"]}/index.html')

    # Build the /blog hub
    cards = ""
    for post in POSTS:
        cards += f"""
        <a href="/blog/{post['slug']}" class="post-card">
          <span class="tag">{post['eyebrow']}</span>
          <h3>{post['title']}</h3>
          <p>{post['description'][:110]}{'…' if len(post['description']) > 110 else ''}</p>
        </a>"""

    hub_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BC Home Energy Blog | HomePowerRebate</title>
<meta name="description" content="Honest, no-hype guides on BC Hydro rebates, solar, batteries, and heat pumps for BC homeowners.">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="https://homepowerrebate.com/blog">
<meta name="google-site-verification" content="Yyio4MZpG_tVGKuE9hbSKTYb0Yo9LFWoNF_3_UxVkGE" />

<meta property="og:title" content="BC Home Energy Blog | HomePowerRebate">
<meta property="og:description" content="Honest, no-hype guides on BC Hydro rebates, solar, batteries, and heat pumps.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://homepowerrebate.com/blog">
<meta property="og:locale" content="en_CA">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">

<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "https://homepowerrebate.com" }},
    {{ "@type": "ListItem", "position": 2, "name": "Blog", "item": "https://homepowerrebate.com/blog" }}
  ]
}}
</script>

<style>{SHELL_CSS}</style>
</head>
<body>

<nav>
  <a href="/" class="logo">Home<span class="logo-power">Power</span>Rebate</a>
  <span class="nav-tag">Blog</span>
</nav>

<header class="hub-hero">
  <div class="wrap-wide">
    <div class="eyebrow">Honest, no-hype guides</div>
    <h1>Straight answers about BC home energy rebates.</h1>
    <p class="sub">No sales pitch. Real numbers, common mistakes, and what to watch for before you sign anything.</p>
  </div>
</header>

<section style="padding:56px 0;">
  <div class="wrap-wide">
    <div class="post-grid">
      {cards}
    </div>
  </div>
</section>

<footer>
  <div class="wrap-wide">
    <a href="/" class="logo">Home<span class="logo-power">Power</span>Rebate</a>
    <p>&copy; 2026 HomePowerRebate. Independent installer matching service, not affiliated with BC Hydro.</p>
  </div>
</footer>

</body>
</html>
"""
    (blog_dir / 'index.html').write_text(hub_html, encoding='utf-8')
    print(f'✓ {"blog hub":38} → blog/index.html')

if __name__ == '__main__':
    main()
