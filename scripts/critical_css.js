// Critical CSS capture: which rules of the /assets stylesheets style something in the first screen?
//   PUPPETEER_CORE=... node scripts/critical_css.js http://localhost:8888 out.json /path1/ /path2/ ...
// Each page is measured at 390 and 1280 px; a rule is kept when one of its selectors matches an element that starts above 1.3 x the
// viewport height (hidden elements count where their nearest displayed ancestor is) (hover, focus and active states are skipped). scripts/build_critical_css.py merges the samples.
const fs = require('fs'), path = require('path');
const puppeteer = require(process.env.PUPPETEER_CORE || path.join(__dirname, 'og', 'node_modules', 'puppeteer-core'));
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const COLLECT = (vh) => {
  const SKIP = /:(hover|focus|focus-visible|focus-within|active|visited|target)\b/;
  const PSEUDO = /::?(before|after|placeholder|marker|first-line|first-letter|selection|backdrop|-webkit-[a-z-]+|-moz-[a-z-]+)/g;
  const seen = new Map();
  const above = (sel) => {
    let q;
    try { q = document.querySelectorAll(sel); } catch (e) { return true; }
    for (const el of q) {
      // hidden elements (display:none, or inside a hidden parent) count where their nearest displayed ancestor sits, and elements
      // parked off-screen above or left (skip link) count too: the rules that hide or park them are needed for the first paint
      let ref = el;
      while (ref.parentElement && getComputedStyle(ref).display === 'none') ref = ref.parentElement;
      const r = ref.getBoundingClientRect();
      if (r.top > vh * 1.3) continue;
      return true;
    }
    return false;
  };
  const ruleMatches = (rule) => /hero-img-/.test(rule.selectorText) || rule.selectorText.split(/,(?![^(]*\))/).some(s => {
    s = s.trim();
    if (SKIP.test(s)) return false;
    s = s.replace(PSEUDO, '').trim() || '*';
    return above(s);
  });
  const walk = (rules, idx, media, sheet) => {
    Array.from(rules).forEach((rule, i) => {
      const at = idx.concat(i);
      if (rule.type === 1) { if (ruleMatches(rule)) seen.set(sheet + '|' + at.join('.') + '|' + media.join('>'), { s: sheet, i: at, m: media, t: rule.cssText }); }
      else if (rule.type === 4 || rule.type === 12) { if (rule.type === 12 || matchMedia(rule.conditionText || rule.media.mediaText).matches) walk(rule.cssRules, at, media.concat((rule.type === 12 ? '@supports ' : '@media ') + (rule.conditionText || rule.media.mediaText)), sheet); }
      else if (rule.type === 5) seen.set(sheet + '|' + at.join('.') + '|ff', { s: sheet, i: at, m: [], t: rule.cssText });
      else if (rule.type === 7) seen.set(sheet + '|' + at.join('.') + '|kf', { s: sheet, i: at, m: [], t: rule.cssText, kf: rule.name });
    });
  };
  for (const sh of document.styleSheets) {
    if (!sh.href || !/\/assets\//.test(sh.href)) continue;
    const href = new URL(sh.href).pathname;
    try { walk(sh.cssRules, [], [], href); } catch (e) { /* cross-origin */ }
  }
  return Array.from(seen.values());
};
(async () => {
  const [base, out, ...paths] = process.argv.slice(2);
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const res = {};
  for (const w of [390, 1280]) {
    const vh = w === 390 ? 844 : 900;
    const page = await browser.newPage(); await page.setViewport({ width: w, height: vh });
    await page.setRequestInterception(true);
    page.on('request', r => (/fonts\.g|google-analytics|googletagmanager|youtube/.test(r.url()) ? r.abort() : r.continue()));
    for (const p of paths) {
      try { await page.goto(base + p, { waitUntil: 'load', timeout: 20000 }); } catch (e) { console.error('slow load:', p); }
      await page.addStyleTag({ content: '*,*::before,*::after{animation:none!important;transition:none!important}' });
      await new Promise(r => setTimeout(r, 1200));
      (res[p] = res[p] || []).push(...await page.evaluate(COLLECT, vh));
      console.error('ok', p, w);
    }
    await page.close();
  }
  await browser.close(); fs.writeFileSync(out, JSON.stringify(res)); console.log('captured', Object.keys(res).length, 'pages');
})();
