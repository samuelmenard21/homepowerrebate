// Renders every frame of a bento / kinetic type video: node scripts/video/render_frames.js <spec.json> <out dir> <fps> <repo root>
// spec.json: { scenes: [ { at, end, theme, foot, items: [...] } ] } (see _partials/video-bento.html). Writes frame_00000.jpg ...
const fs = require('fs'), path = require('path');
const puppeteer = require(path.join(__dirname, '..', 'og', 'node_modules', 'puppeteer-core'));
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
(async () => {
  const [specFile, outDir, fpsArg, root] = process.argv.slice(2);
  const spec = JSON.parse(fs.readFileSync(specFile, 'utf8')), fps = Number(fpsArg);
  const total = spec.scenes[spec.scenes.length - 1].end;
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(root, '_partials', 'video-bento.html'), { waitUntil: 'networkidle0' });
  fs.mkdirSync(outDir, { recursive: true });
  const n = Math.round(total * fps);
  for (let i = 0; i < n; i++) {
    await page.evaluate((s, t) => window.render(s, t), spec, Math.min(total - 0.001, i / fps));
    await page.screenshot({ path: path.join(outDir, 'frame_' + String(i).padStart(5, '0') + '.jpg'), type: 'jpeg', quality: 90 });
  }
  await browser.close();
  console.log('frames', n);
})();
