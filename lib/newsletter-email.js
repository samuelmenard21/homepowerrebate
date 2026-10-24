// Newsletter emails (2026-10-24): the welcome email and the monthly digest. Pure functions (no network, no bindings) so they can be rendered and
// previewed in Node; lead-router.js does the sending. Layout matches the results recap email: light only, stacked rows, dark teal header.

const esc = (s) => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

const SHELL_TOP = (title) => `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light only"><meta name="supported-color-schemes" content="light only">
<style>:root{color-scheme:light only;supported-color-schemes:light only}</style><title>${esc(title)}</title></head>
<body bgcolor="#f5efe5" style="margin:0;padding:0;background:#f5efe5;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#f5efe5" style="background:#f5efe5;"><tr><td align="center" style="padding:20px 12px;">
<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:#0a2a2e;">`;

const header = (h1) => `
  <tr><td bgcolor="#08363f" style="background:#08363f;padding:26px 24px;border-radius:14px 14px 0 0;">
    <div style="font-family:Georgia,serif;font-size:18px;color:#faf7f2;">Home<span style="color:#e88a2e;font-weight:700;">Power</span>Rebate</div>
    <h1 style="margin:14px 0 0;font-family:Georgia,serif;font-size:26px;font-weight:500;line-height:1.25;color:#faf7f2;">${esc(h1)}</h1>
  </td></tr>
  <tr><td bgcolor="#faf7f2" style="background:#faf7f2;padding:24px;border:1px solid #d9d0c1;border-top:none;border-radius:0 0 14px 14px;">`;

const h2 = (t) => `<h2 style="font-family:Georgia,serif;font-size:19px;font-weight:500;color:#08363f;margin:26px 0 10px;">${esc(t)}</h2>`;
const p = (t, extra = '') => `<p style="font-size:15px;line-height:1.6;margin:0 0 14px;${extra}">${t}</p>`;

const primary = (href, label) => `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:10px;"><tr><td bgcolor="#d4751c" style="background:#d4751c;border-radius:8px;text-align:center;">
  <a href="${esc(href)}" style="display:block;padding:14px 20px;color:#ffffff;text-decoration:none;font-weight:700;font-size:16px;">${esc(label)} &rarr;</a></td></tr></table>`;
const secondary = (href, label) => `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:10px;"><tr><td bgcolor="#ffffff" style="background:#ffffff;border:2px solid #08363f;border-radius:8px;text-align:center;">
  <a href="${esc(href)}" style="display:block;padding:12px 20px;color:#08363f;text-decoration:none;font-weight:700;font-size:16px;">${esc(label)} &rarr;</a></td></tr></table>`;

function footer(unsubUrl, why) {
  return `
    <p style="margin:24px 0 0;font-size:12px;line-height:1.5;color:#6b7d80;text-align:center;">${esc(why)}<br>
      HomePowerRebate &middot; independent, not the government or a utility<br>
      <a href="https://homepowerrebate.com" style="color:#6b7d80;">homepowerrebate.com</a> &middot; <a href="${esc(unsubUrl)}" style="color:#6b7d80;">Unsubscribe</a>
    </p>
  </td></tr>
</table></td></tr></table></body></html>`;
}

const guideRow = (g) => `<tr><td bgcolor="#ffffff" style="padding:12px 16px;border-top:1px solid #ece4d6;background:#ffffff;">
    <a href="${esc(g.url)}" style="font-size:15px;font-weight:700;color:#08363f;text-decoration:underline;line-height:1.4;">${esc(g.t)}</a>
    ${g.d ? `<div style="font-size:14px;line-height:1.5;color:#1a3d42;margin-top:3px;">${esc(g.d)}</div>` : ''}</td></tr>`;
const box = (rows) => `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="background:#ffffff;border:1px solid #d9d0c1;border-radius:10px;border-collapse:separate;overflow:hidden;">${rows}</table>`;

/**
 * Welcome email: sent the moment someone subscribes. Ten guides picked for their province or state, what to expect, and two next steps.
 * welcome = data/newsletter/welcome.json; urls = { calc, installers, finder, unsub }.
 */
export function renderWelcome({ province, regionName, welcome, urls }) {
  const slugs = (province && welcome.by_region[province]) || welcome.default;
  const guides = slugs.map((s) => ({ ...welcome.posts[s], url: `https://homepowerrebate.com/blog/${s}/` })).filter((g) => g.t);
  const where = regionName ? regionName : '';
  const subject = where ? `Welcome. Your 10 best reads on ${where} rebates` : 'Welcome. Your 10 best reads on home energy rebates';
  const html = SHELL_TOP(subject) + header(where ? `You're in. Start with these 10, ${where}.` : "You're in. Start with these 10.") + `
    ${p("Hi, I'm Sam, the person behind HomePowerRebate. Thanks for signing up.")}
    ${p(`Here are ten guides to read first${where ? ` for ${esc(where)}` : ''}. Each one is sourced from the program's own page, and we tell you when the math does not work.`)}
    ${box(guides.map(guideRow).join(''))}
    ${h2('What happens next')}
    ${p('One email a month. It lists the rebates that opened, changed or are closing soon, written for where you live, and links to the pages you will actually use. Nothing else, and nobody pays to be in it.')}
    ${primary(urls.calc, where ? `See what you could get back in ${where}` : 'See what you could get back')}
    ${secondary(urls.installers, 'See top-rated installers near you')}
    ${p('Ranked by Google reviews. Nobody pays to be listed, and we never pass your email on.', 'font-size:13px;color:#5a6b6e;margin:10px 0 0;')}
    ${p('Questions? Just reply to this email. It comes straight to me.', 'margin:22px 0 0;')}` +
    footer(urls.unsub, 'You are getting this because you subscribed on homepowerrebate.com.');
  return { subject, html };
}

/**
 * Monthly digest. issue = the JSON from /embed/newsletter/latest/. sub = { province, city }; scope = 'ca' | 'us' | ''.
 * Changes for the subscriber's own province or state come first, then country-wide ones, then a few from elsewhere (the promise is "every province and state").
 */
export function renderDigest({ issue, province, scope, regionName, urls }) {
  const mine = (i) => i.r === province;
  const national = (i) => (i.r === 'CA-FED' && scope === 'ca') || (i.r === 'US' && scope === 'us') || i.r === 'ALL';
  const items = issue.items;
  const local = items.filter(mine);
  const nat = items.filter((i) => !mine(i) && national(i));
  const rest = items.filter((i) => !mine(i) && !national(i)).slice(0, local.length + nat.length >= 4 ? 2 : 4);
  const posts = [...issue.posts.filter((g) => g.r === province), ...issue.posts.filter((g) => g.r !== province)].slice(0, 4);

  const itemHtml = (i, showRegion) => `<tr><td bgcolor="#ffffff" style="padding:14px 16px;border-top:1px solid #ece4d6;background:#ffffff;">
      <div style="font-size:11px;font-weight:700;letter-spacing:0.05em;color:${i.tag === 'CLOSING SOON' ? '#b3361f' : '#a15d10'};">${esc(i.tag)}${showRegion ? ` &middot; ${esc(i.region)}` : ''}</div>
      <div style="font-size:16px;font-weight:700;color:#08363f;margin-top:3px;line-height:1.35;">${esc(i.title)}</div>
      <div style="font-size:14px;line-height:1.55;color:#1a3d42;margin-top:4px;">${esc(i.body)}</div>
      <div style="font-size:14px;margin-top:6px;"><a href="${esc(i.url)}" style="color:#08363f;font-weight:700;">See how it affects your home &rarr;</a>${i.source ? ` &nbsp; <a href="${esc(i.source)}" style="color:#5a6b6e;">Official source</a>` : ''}</div></td></tr>`;

  let body = p(esc(issue.intro));
  if (local.length) body += h2(`In ${regionName || 'your area'}`) + box(local.map((i) => itemHtml(i, false)).join(''));
  else if (regionName) body += h2(`In ${regionName}`) + p(`We have not confirmed any changes to ${esc(regionName)}'s programs this month. The amounts we sent before still stand.`);
  if (nat.length) body += h2(scope === 'ca' ? 'Across Canada' : scope === 'us' ? 'Across the United States' : 'Everywhere') + box(nat.map((i) => itemHtml(i, false)).join(''));
  if (rest.length) body += h2('Elsewhere this month') + box(rest.map((i) => itemHtml(i, true)).join(''));
  if (posts.length) body += h2('New guides') + box(posts.map((g) => guideRow({ t: g.t, d: g.d, url: g.url })).join(''));
  body += h2('Your next step') + primary(urls.calc, 'Check what you could get back') + secondary(urls.installers, 'See top-rated installers near you') +
    p(`<a href="${esc(issue.release_url)}" style="color:#08363f;">Every program change in ${esc(issue.release_month)}, with sources</a>`, 'margin:16px 0 0;font-size:14px;') +
    p('Reply to this email with a question. It comes straight to me. Sam', 'margin:14px 0 0;');

  const html = SHELL_TOP(issue.subject) + header(issue.subject) + body + footer(urls.unsub, 'You get this once a month because you subscribed on homepowerrebate.com.');
  return { subject: issue.subject, html };
}

/** Parse the issue JSON out of the /embed/newsletter/latest/ page. */
export function parseIssuePage(pageHtml) {
  const m = /<script type="application\/json" id="issue-data">([\s\S]*?)<\/script>/.exec(pageHtml);
  if (!m) return null;
  try { return JSON.parse(m[1].replace(/<\\\//g, '</')); } catch (e) { return null; }
}

/** Weekly note to the owner. s = counts gathered by the Worker. */
export function renderWeeklySummary(s) {
  const row = (k, v) => `<tr><td style="padding:6px 0;color:#1a3d42;">${esc(k)}</td><td style="padding:6px 0;font-weight:700;text-align:right;">${esc(v)}</td></tr>`;
  const list = (title, pairs) => pairs.length ? `<h3 style="margin:20px 0 6px;font-size:14px;color:#08363f;">${esc(title)}</h3><table width="100%" cellpadding="0" cellspacing="0" style="font-size:14px;">${pairs.map(([k, v]) => row(k, v)).join('')}</table>` : '';
  const html = `<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;max-width:560px;margin:0 auto;color:#0a2a2e;">
    <h2 style="font-family:Georgia,serif;font-weight:500;color:#08363f;margin:0 0 4px;">Weekly signups, ${esc(s.week_label)}</h2>
    <p style="margin:0 0 14px;font-size:14px;color:#5a6b6e;">${s.new_subscribers + s.new_federal + s.new_program === 0 ? 'No new signups this week.' : 'All new signups from the last 7 days.'}</p>
    <table width="100%" cellpadding="0" cellspacing="0" style="font-size:15px;border-top:1px solid #d9d0c1;">
      ${row('New monthly-update subscribers', `${s.new_subscribers} (list now ${s.total_subscribers})`)}
      ${row('New federal rebate alert signups', `${s.new_federal} (list now ${s.total_federal})`)}
      ${row('New program alert signups (heating help, HARP)', s.new_program)}
    </table>
    ${list('Subscribers by province or state', s.by_province)}
    ${list('Signups by page', s.by_page)}
    <h3 style="margin:20px 0 6px;font-size:14px;color:#08363f;">Monthly email</h3>
    <p style="margin:0;font-size:14px;line-height:1.55;">${esc(s.digest_line)}</p>
    <p style="margin:22px 0 0;font-size:12px;color:#6b7d80;">Leads from the quote forms still email you straight away. This note replaces the one-email-per-subscriber alerts.</p></div>`;
  return { subject: `Weekly signups: ${s.new_subscribers} new subscribers, ${s.new_federal} federal alert`, html };
}
