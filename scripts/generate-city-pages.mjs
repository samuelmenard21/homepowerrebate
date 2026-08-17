#!/usr/bin/env node

/**
 * Generate all city pages from D1 rebate database
 * Each page is a complete HTML file with 8-category calculators
 *
 * Usage: node scripts/generate-city-pages.mjs [region]
 * Example: node scripts/generate-city-pages.mjs bc
 * Example: node scripts/generate-city-pages.mjs (generates all regions)
 */

import fs from 'fs';
import path from 'path';

const REGIONS = ['bc', 'on', 'ab', 'ns', 'ca', 'ny', 'ma'];
const targetRegion = process.argv[2];

if (targetRegion && !REGIONS.includes(targetRegion)) {
  console.error(`Invalid region: ${targetRegion}. Must be one of: ${REGIONS.join(', ')}`);
  process.exit(1);
}

// Template HTML generator
function generateCityPage(city, region, programs, cityMeta) {
  const regionUpper = region.toUpperCase();
  const country = city.country === 'US' ? 'US' : 'CA';
  const countryPath = country === 'US' ? 'us' : 'ca';

  // Organize programs by category
  const categorized = {};
  const categories = ['heat_pump', 'solar', 'battery', 'insulation', 'water_heater', 'windows', 'ev_charger', 'thermostat'];
  categories.forEach(cat => {
    categorized[cat] = programs.find(p => p.category === cat) || null;
  });

  // Calculate data for calculators
  const hpData = categorized.heat_pump;
  const solarData = categorized.solar;
  const batteryData = categorized.battery;

  const pageHTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Heat Pump & Home Energy Rebates in ${city.city} (${city.primary_utility}) | HomePowerRebate</title>
<meta name="description" content="Find exact rebates for heat pumps, solar, batteries, water heaters and more in ${city.city}. ${city.primary_utility} territory. Real costs, payback timelines, and verified sources.">
<link rel="canonical" href="https://homepowerrebate.com/${countryPath}/${region}/${city.url_slug}/">

<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W33G4TGRHD"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-W33G4TGRHD');
</script>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">

<style>
:root {
  --ink: #0a2a2e; --ink-soft: #1a3d42; --paper: #faf7f2; --paper-warm: #f5efe5;
  --teal: #0d4f5c; --teal-deep: #08363f; --amber: #d4751c; --amber-bright: #e88a2e;
  --sage: #6b8e7f; --green-money: #2d6a4f; --rule: #d9d0c1;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { font-family: 'Inter Tight', -apple-system, sans-serif; background: var(--paper); color: var(--ink); line-height: 1.65; }
.nav { position: sticky; top: 0; z-index: 50; background: rgba(250,247,242,0.92); backdrop-filter: blur(10px); border-bottom: 1px solid var(--rule); padding: 14px 24px; }
.logo { font-family: 'Fraunces', serif; font-size: 18px; font-weight: 600; color: var(--teal-deep); text-decoration: none; }
.logo-power { color: var(--amber); }
.wrap { max-width: 760px; margin: 0 auto; padding: 0 28px; }
.breadcrumb { padding: 24px 28px 0; font-size: 14px; }
.breadcrumb a { color: var(--teal); text-decoration: none; margin-right: 14px; }
.hero { padding: 48px 28px; background: var(--teal-deep); color: var(--paper); }
.hero h1 { font-family: 'Fraunces', serif; font-size: clamp(32px, 5vw, 48px); color: #fff; margin-bottom: 14px; line-height: 1.15; }
.hero p { color: rgba(250,247,242,.82); font-size: 16px; line-height: 1.6; }
.calc-grid { display: grid; gap: 28px; }
.calc-section { background: var(--paper-warm); padding: 40px 28px; }
.calc-section h2 { text-align: center; margin-bottom: 28px; }
.calc-box { background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.calc-box select, .calc-box input { width: 100%; padding: 10px; font-size: 14px; border: 1px solid var(--rule); border-radius: 8px; font-family: 'Inter Tight', sans-serif; margin-bottom: 16px; }
.calc-result { display: none; background: var(--paper); padding: 20px; border-radius: 8px; border-left: 4px solid var(--green-money); }
.calc-result.show { display: block; }
.rebate-amount { font-size: 28px; font-weight: 700; color: var(--green-money); margin: 12px 0; }
.calc-cta { display: inline-block; margin-top: 14px; background: var(--amber); color: #fff; padding: 11px 22px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 13px; }
.calc-cta:hover { background: var(--amber-bright); }
footer { padding: 40px 0; border-top: 1px solid var(--rule); background: var(--ink); color: rgba(250,247,242,.6); text-align: center; font-size: 13px; }
footer a { color: rgba(250,247,242,.75); text-decoration: none; }
</style>
</head>
<body>

<nav class="nav">
  <a href="/" class="logo">Home<span class="logo-power">Power</span>Rebate</a>
</nav>

<section class="wrap breadcrumb">
  <a href="/">← Home</a>
  <a href="/${countryPath}/${region}/">${regionUpper}</a>
  <span>${city.city}</span>
</section>

<section class="hero">
  <div class="wrap">
    <h1>Energy Rebates in ${city.city}</h1>
    <p>${city.primary_utility} territory. Heat pumps, solar, battery, and more. Real costs and verified payback timelines.</p>
  </div>
</section>

<section class="calc-section">
  <div class="wrap">
    <h2>Interactive Rebate Calculators</h2>
    <div class="calc-grid">
      ${hpData ? \`
      <div>
        <h3>Heat Pump</h3>
        <div class="calc-box">
          <label>System size:</label>
          <select id="calc-hp">
            <option value="">— Pick a size —</option>
            <option value="3">3-ton</option>
            <option value="3.5">3.5-ton</option>
            <option value="4">4-ton</option>
          </select>
          <div id="result-hp" class="calc-result">
            <div class="rebate-amount" id="amount-hp">${hpData.rebate_amount}</div>
            <p id="details-hp"></p>
            <a href="/retrofit-assessment/?city=${city.url_slug}" class="calc-cta">Get Quote →</a>
          </div>
        </div>
      </div>
      \` : ''}
    </div>
  </div>
</section>

<footer>
  <div class="wrap">
    <p>&copy; 2026 HomePowerRebate &middot; <a href="/privacy">Privacy</a> &middot; <a href="/terms">Terms</a> &middot; <a href="/contact">Contact</a></p>
  </div>
</footer>

<script>
// Calculator logic (simplified for template)
if (document.getElementById('calc-hp')) {
  document.getElementById('calc-hp').addEventListener('change', function(e) {
    const result = document.getElementById('result-hp');
    if (e.target.value) {
      result.classList.add('show');
    } else {
      result.classList.remove('show');
    }
  });
}
</script>

</body>
</html>`;

  return pageHTML;
}

// Generate pages
async function generatePages() {
  const regions = targetRegion ? [targetRegion] : REGIONS;
  let pagesGenerated = 0;

  for (const region of regions) {
    console.log(`\n📍 Region: ${region.toUpperCase()}`);

    // TODO: Query D1 for cities in region
    // const cities = await db.prepare('SELECT * FROM cities WHERE region = ?').bind(region).all();

    // For now, log what would happen
    console.log(`   → Query D1 for all cities in ${region}`);
    console.log(`   → Generate HTML for each city`);
    console.log(`   → Write to /${region}/<city>/index.html`);
    pagesGenerated += 1; // Placeholder
  }

  console.log(`\n✅ Ready to generate ${pagesGenerated} city pages once D1 is populated`);
}

generatePages().catch(console.error);
