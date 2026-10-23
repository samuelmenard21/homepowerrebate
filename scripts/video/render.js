// Renders the scenes of one explainer video as 1080 x 1920 PNGs: node scripts/video/render.js <job.json> <repo root>
// job.json: { "scenes": [ { out, kicker, headline, sub, foot, theme, big, index, total } ] }. Needs puppeteer-core (scripts/og/node_modules) and Google Chrome.
const fs = require('fs'), path = require('path');
const puppeteer = require(path.join(__dirname, '..', 'og', 'node_modules', 'puppeteer-core'));
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
(async () => {
  const [job, root] = process.argv.slice(2);
  const j = JSON.parse(fs.readFileSync(job, 'utf8'));
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(root, '_partials', 'video-scene.html'), { waitUntil: 'networkidle0' });
  for (const s of j.scenes) {
    await page.evaluate(d => window.setScene(d), s);
    await new Promise(r => setTimeout(r, 150));
    await page.screenshot({ path: s.out, type: 'png' });
  }
  await browser.close();
})();
