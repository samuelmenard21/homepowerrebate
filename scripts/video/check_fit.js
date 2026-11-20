// Checks that the text in a bento video fits: node scripts/video/check_fit.js <spec.json> <out dir> <repo root>
// Draws each scene near its end (everything popped in), then reports tiles whose text overflows, items outside the 1080 x 1920 frame, and tiles that overlap. Saves a PNG per scene.
const fs = require('fs'), path = require('path');
const puppeteer = require(path.join(__dirname, '..', 'og', 'node_modules', 'puppeteer-core'));
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
(async () => {
  const [specFile, outDir, root] = process.argv.slice(2);
  const spec = JSON.parse(fs.readFileSync(specFile, 'utf8'));
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox', '--allow-file-access-from-files'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(root, '_partials', 'video-bento.html'), { waitUntil: 'networkidle0' });
  fs.mkdirSync(outDir, { recursive: true });
  let bad = 0;
  for (let i = 0; i < spec.scenes.length; i++) {
    const s = spec.scenes[i], t = Math.max(s.at + 0.1, s.end - 0.35);
    await page.evaluate((sp, tt) => window.render(sp, tt), spec, t);
    await new Promise(r => setTimeout(r, 80));
    const issues = await page.evaluate(() => {
      const out = [], boxes = [];
      document.querySelectorAll('.tile, .sticker').forEach(el => {
        if (el.style.display === 'none') return;
        const r = el.getBoundingClientRect(), txt = (el.textContent || '').trim().slice(0, 40);
        const inner = el.firstElementChild && el.classList.contains('tile') ? el.firstElementChild : null;
        const over = el.scrollHeight > el.clientHeight + 3 || el.scrollWidth > el.clientWidth + 3 || (inner && inner.getBoundingClientRect().height > el.clientHeight - 30);
        if (over) out.push('overflow: ' + txt);
        if (r.left < 20 || r.right > 1060 || r.top < 0 || r.bottom > 1900) out.push('off frame: ' + txt);
        boxes.push({ r, txt, tile: el.classList.contains('tile') });
      });
      for (let a = 0; a < boxes.length; a++) for (let b = a + 1; b < boxes.length; b++) {
        if (!boxes[a].tile || !boxes[b].tile) continue;
        const A = boxes[a].r, B = boxes[b].r;
        if (A.left < B.right - 8 && B.left < A.right - 8 && A.top < B.bottom - 8 && B.top < A.bottom - 8) out.push('overlap: ' + boxes[a].txt + ' / ' + boxes[b].txt);
      }
      return out;
    });
    await page.screenshot({ path: path.join(outDir, 'scene_' + String(i).padStart(2, '0') + '.png') });
    if (issues.length) { bad += issues.length; console.log('scene ' + i + ' (' + s.at + 's):', issues.join(' | ')); }
  }
  await browser.close();
  console.log(bad ? 'FIT PROBLEMS: ' + bad : 'all text fits');
})();
