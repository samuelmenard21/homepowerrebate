// Renders share cards for scripts/build_og_cards.py: node scripts/og/render.js <job.json> <repo root>
// Needs puppeteer-core (npm install --prefix scripts/og puppeteer-core) and Google Chrome.
const fs = require('fs'), path = require('path');
const puppeteer = require('puppeteer-core');
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
(async () => {
  const [job, root] = process.argv.slice(2);
  const cards = JSON.parse(fs.readFileSync(job, 'utf8'));
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 630, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(root, '_partials', 'og-card.html'), { waitUntil: 'networkidle0' });
  let n = 0;
  for (const c of cards) {
    await page.evaluate(d => window.setCard(d), c);
    const out = path.join(root, c.out);
    fs.mkdirSync(path.dirname(out), { recursive: true });
    await page.screenshot({ path: out.replace(/\.jpg$/, '.png'), type: 'png' });
    if (++n % 250 === 0) console.log(n + ' / ' + cards.length);
  }
  await browser.close();
})();
