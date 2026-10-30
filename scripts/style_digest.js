// Computed-style digest of sample pages, to prove a CSS refactor changes nothing:
//   node scripts/style_digest.js capture http://localhost:8888 out.json /path1/ /path2/ ...
//   node scripts/style_digest.js compare before.json after.json
// Each element gets a hash of ALL its computed properties at 390 and 1280 px; compare lists pages with differing elements.
// Needs puppeteer-core (scripts/og/node_modules) and Chrome.
const fs = require('fs'), path = require('path');
// PUPPETEER_CORE=/path/to/node_modules/puppeteer-core overrides the default (scripts/og/node_modules, which is a link in git)
const puppeteer = require(process.env.PUPPETEER_CORE || path.join(__dirname, 'og', 'node_modules', 'puppeteer-core'));
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const DIGEST = () => {
  const h = s => { let x = 5381; for (let i = 0; i < s.length; i++) x = ((x << 5) + x + s.charCodeAt(i)) | 0; return (x >>> 0).toString(36); };
  const out = [];
  document.querySelectorAll('body *').forEach((e, i) => {
    if (e.closest('script,style,noscript,[hidden]')) return;
    const c = getComputedStyle(e); const props = [];
    for (let k = 0; k < c.length; k++) { const p = c[k]; if (/^(transition|animation|-webkit-)/.test(p)) continue; props.push(p + ':' + c.getPropertyValue(p)); }
    const s = props.sort().join(';') + ';'; // custom properties list in no fixed order, so sort
    if (window.__dbg && i === 0) out.push('PROPS ' + s);
    out.push(i + ':' + e.tagName + '.' + String(e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className).slice(0, 40) + '=' + h(s));
  });
  return out;
};
(async () => {
  const [mode, a, b, ...paths] = process.argv.slice(2);
  if (mode === 'compare') {
    const A = JSON.parse(fs.readFileSync(a)), B = JSON.parse(fs.readFileSync(b)); let bad = 0;
    for (const k of Object.keys(A)) {
      const x = A[k], y = B[k] || []; const d = []; const n = Math.max(x.length, y.length);
      for (let i = 0; i < n; i++) if (x[i] !== y[i]) d.push(x[i] + '  ->  ' + y[i]);
      if (d.length) { bad++; const who = {}; d.forEach(z => { const m = z.split('  ->  ')[0].replace(/^\d+:/, '').replace(/=.*/, ''); who[m] = (who[m] || 0) + 1; }); console.log('DIFF', k, d.length, 'elements:', JSON.stringify(who).slice(0, 400)); }
    }
    console.log(bad ? bad + ' page views differ' : 'all ' + Object.keys(A).length + ' page views identical'); process.exit(bad ? 1 : 0);
  }
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const res = {};
  for (const w of [390, 1280]) {
    const page = await browser.newPage(); await page.setViewport({ width: w, height: 900 });
    await page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
    await page.setRequestInterception(true);
    page.on('request', r => (/fonts\.g|assets\/fonts|google-analytics|googletagmanager|youtube/.test(r.url()) ? r.abort() : r.continue()));
    for (const p of paths) {
      try { await page.goto(a + p, { waitUntil: 'load', timeout: 20000 }); } catch (e) { console.error('slow load, measuring anyway:', p); } await page.addStyleTag({ content: '*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}html{overflow-y:scroll!important}' }); await new Promise(r => setTimeout(r, 1500));
      if (process.env.DBG) await page.evaluate(() => { window.__dbg = 1; });
      res[p + '@' + w] = await page.evaluate(DIGEST); console.error('ok', p, w);
    }
    await page.close();
  }
  await browser.close(); fs.writeFileSync(b, JSON.stringify(res)); console.log('captured', Object.keys(res).length, 'page views');
})();
