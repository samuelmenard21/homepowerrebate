/**
 * HomePowerRebate Lead Router (v2 — adds /waitlist endpoint)
 *
 * Routes:
 *   POST /submit    — Full lead from a city page; routes to one matched installer.
 *   POST /waitlist  — Out-of-area waitlist signup from /ca/bc or /;
 *                     captures city + email (+ optional postal),
 *                     sends a confirmation, logs to sheet.
 *
 * Deploy: wrangler deploy
 * Endpoint: https://leads.homepowerrebate.com
 *
 * Required environment variables (set with `wrangler secret put`):
 *   RESEND_API_KEY      - for sending emails (resend.com free tier: 100/day)
 *   GSHEET_WEBHOOK_URL  - Google Apps Script webhook for logging leads/waitlist.
 *                         Both routes POST here; the Apps Script reads the
 *                         `record_type` field ("lead" | "waitlist") to route to
 *                         the right tab.
 *   OPS_EMAIL           - your operations inbox (lead audit copies + waitlist alerts)
 *
 * Required wrangler.toml config:
 *   [vars]
 *   ENVIRONMENT = "production"
 */

import CITY_REBATE_LOOKUP from './city-rebate-lookup.json';

// ===========================================================================
// INSTALLER ROUTING TABLE
// ---------------------------------------------------------------------------
// One preferred installer per city. Update emails here when partnerships
// change. The 'cc' field is optional — if your installer has multiple inboxes
// (e.g. owner + ops), add them as a comma-separated string.
// ===========================================================================

// ===========================================================================
// INSTALLER ROUTING TABLE
// ---------------------------------------------------------------------------
// Nested by service, then by city. Each service ('solar-battery', 'heat-pump')
// has its own installer per city — they're different trades and usually
// different companies. Update emails here when partnerships change. The
// 'cc' field is optional — if your installer has multiple inboxes (e.g.
// owner + ops), add them as a comma-separated string.
//
// If a city has no installer yet for a given service, leave the entry out
// entirely — handleLeadSubmit() will fall back to routing that lead to
// OPS_EMAIL only, so you never lose a lead even before you've signed a
// partner for that trade.
// ===========================================================================

const INSTALLER_ROUTING = {
  'solar-battery': {
    kelowna: {
      name: 'Kelowna Solar Partners',
      email: 'leads@kelowna-installer.example.com',
      cc: '',
      phone: '(250) 555-0100',
      region: 'Central Okanagan'
    },
    kamloops: {
      name: 'Thompson Energy Co.',
      email: 'leads@kamloops-installer.example.com',
      cc: '',
      phone: '(250) 555-0300',
      region: 'Thompson Region'
    },
    victoria: {
      name: 'Island Solar Group',
      email: 'leads@victoria-installer.example.com',
      cc: '',
      phone: '(250) 555-0200',
      region: 'Vancouver Island South'
    },
    nanaimo: {
      name: 'Mid-Island Power',
      email: 'leads@nanaimo-installer.example.com',
      cc: '',
      phone: '(250) 555-0400',
      region: 'Central Vancouver Island'
    },
    vancouver: {
      name: 'Metro Solar Pros',
      email: 'leads@vancouver-installer.example.com',
      cc: '',
      phone: '(604) 555-0100',
      region: 'Metro Vancouver'
    },
    surrey: {
      name: 'Surrey Solar Partners',
      email: 'leads@surrey-installer.example.com',
      cc: '',
      phone: '(604) 555-0500',
      region: 'Metro Vancouver South'
    },
    abbotsford: {
      name: 'Fraser Valley Solar Co.',
      email: 'leads@abbotsford-installer.example.com',
      cc: '',
      phone: '(604) 555-0600',
      region: 'Fraser Valley'
    },
    chilliwack: {
      name: 'Fraser Valley Solar Co.',
      email: 'leads@chilliwack-installer.example.com',
      cc: '',
      phone: '(604) 555-0700',
      region: 'Fraser Valley East'
    },
    vernon: {
      name: 'North Okanagan Solar',
      email: 'leads@vernon-installer.example.com',
      cc: '',
      phone: '(250) 555-0800',
      region: 'North Okanagan'
    },
    'prince-george': {
      name: 'Northern BC Solar',
      email: 'leads@pg-installer.example.com',
      cc: '',
      phone: '(250) 555-0900',
      region: 'Northern BC'
    },
    squamish: {
      name: 'Sea-to-Sky Solar',
      email: 'leads@squamish-installer.example.com',
      cc: '',
      phone: '(604) 555-1000',
      region: 'Sea-to-Sky'
    }
  },

  'heat-pump': {
    // TODO: replace placeholder emails once you've signed HVAC installer
    // partners per city. Until then, leads still route safely to OPS_EMAIL
    // via the fallback in handleLeadSubmit() — you just won't auto-notify
    // an installer for that city yet.
    kelowna: {
      name: 'TBD — Kelowna HVAC Partner',
      email: 'leads@kelowna-hvac.example.com',
      cc: '',
      phone: '(250) 555-0100',
      region: 'Central Okanagan'
    }
    // Add kamloops, victoria, nanaimo, vancouver, surrey, abbotsford,
    // chilliwack, vernon, prince-george, squamish here as you sign each one.
  }
};

// ===========================================================================
// CORS headers
// ===========================================================================

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': 'https://homepowerrebate.com',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400'
};

// Outcomes comparison feature: valid categories (matches the site's 8-category
// standard) and the minimum sample size before a city/province average is
// shown, so a handful of self-reports (or one bad-faith submission) can't
// skew a displayed stat. Below the threshold, callers fall back to the next
// wider tier (city -> province -> national).
const OUTCOME_CATEGORIES = [
  'heat-pump', 'solar', 'battery', 'insulation',
  'water-heater', 'windows', 'ev-charger', 'thermostat'
];
const MIN_SAMPLE = 5;

// Open submissions (no booking/lead required — anyone who did the work can
// share it, same as a salary-sharing site) means plausibility bounds are the
// main defense against joke/bot entries skewing an average. Ranges are
// deliberately wide (installed cost before rebates, CAD/USD both live here).
const PLAUSIBLE_COST_RANGE = {
  'heat-pump': [2000, 35000],
  'solar': [3000, 60000],
  'battery': [3000, 40000],
  'insulation': [500, 25000],
  'water-heater': [500, 15000],
  'windows': [1000, 40000],
  'ev-charger': [300, 8000],
  'thermostat': [50, 1500]
};
const MAX_SUBMISSIONS_PER_EMAIL_PER_DAY = 3;

// For local testing, uncomment:
// CORS_HEADERS['Access-Control-Allow-Origin'] = '*';

// Resend audience for the newsletter / list-building (not secret — the API key is).
const RESEND_AUDIENCE_ID = 'c8b63b68-01ad-4727-a62e-2484dbe25ae9';

// ===========================================================================
// MAIN HANDLER — path-based router
// ===========================================================================

export default {
  async fetch(request, env, ctx) {
    return handleFetch(request, env, ctx);
  },
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runDripQueue(env));
  }
};

async function handleFetch(request, env, ctx) {
    // CORS preflight (applies to every route)
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    const url = new URL(request.url);
    const path = url.pathname.replace(/\/$/, ''); // strip trailing slash

    // GET routes (read-only, no lead capture) — everything else stays POST-only.
    if (path === '/outcomes/compare') {
      return request.method === 'GET'
        ? handleOutcomeCompare(request, env)
        : jsonResponse({ error: 'Method not allowed' }, 405);
    }
    if (path === '/unsubscribe') {
      return request.method === 'GET'
        ? handleUnsubscribe(request, env)
        : jsonResponse({ error: 'Method not allowed' }, 405);
    }

    if (request.method !== 'POST') {
      return jsonResponse({ error: 'Method not allowed' }, 405);
    }

    if (path === '/submit') return handleLeadSubmit(request, env);
    if (path === '/waitlist') return handleWaitlistSubmit(request, env);
    if (path === '/newsletter') return handleNewsletter(request, env);
    if (path === '/estimate-lead') return handleEstimateLead(request, env);
    if (path === '/outcomes/submit') return handleOutcomeSubmit(request, env);

    return jsonResponse({ error: `Unknown route: ${path}` }, 404);
}

// ===========================================================================
// ROUTE 1 — /submit (full lead from a city page)
// ===========================================================================
// Unchanged from v1. One trusted installer per city; the lead is fanned out
// to their inbox, the ops inbox, and the master Google Sheet.

async function handleLeadSubmit(request, env) {
  let payload;
  try {
    payload = await request.json();
  } catch (e) {
    return jsonResponse({ error: 'Invalid JSON' }, 400);
  }

  // ---- Validation ----
  const required = ['firstname', 'lastname', 'email', 'phone', 'postal', 'city'];
  const missing = required.filter(f => !payload[f]);
  if (missing.length) {
    return jsonResponse({ error: `Missing fields: ${missing.join(', ')}` }, 400);
  }

  // Honeypot check
  if (payload.website) {
    return jsonResponse({ success: true }, 200);
  }

  // Email format
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email)) {
    return jsonResponse({ error: 'Invalid email' }, 400);
  }

  // Postal code format (Canadian)
  if (!/^[A-Za-z][0-9][A-Za-z][ -]?[0-9][A-Za-z][0-9]$/.test(payload.postal)) {
    return jsonResponse({ error: 'Invalid postal code' }, 400);
  }

  // ---- Look up installer (service-aware) ----
  // payload.service is set by each page's hidden form field: 'solar-battery'
  // (default, for backward compatibility with existing city pages that don't
  // send it yet) or 'heat-pump'. If no installer is configured yet for this
  // city+service combo, we don't reject the lead — we still capture it and
  // notify ops, so nothing is lost while you're signing installer partners.
  const city = String(payload.city || '').toLowerCase().trim();
  const service = String(payload.service || 'solar-battery').toLowerCase().trim();

  const serviceTable = INSTALLER_ROUTING[service];
  if (!serviceTable) {
    return jsonResponse({ error: `Unknown service: ${service}` }, 400);
  }

  const installer = serviceTable[city];
  // A routing-table entry with a placeholder .example.com email isn't a real,
  // signed partner — treat it the same as "no installer configured" so a
  // lead never gets fanned out to an address that can't receive mail. Only
  // send to an installer once its email is a real domain.
  const hasInstaller = !!installer && !/example\.com$/i.test(installer.email || '');

  const leadId = crypto.randomUUID();
  const timestamp = new Date().toISOString();

  // ---- Build lead record ----
  const lead = {
    record_type: 'lead',
    lead_id: leadId,
    timestamp,
    city,
    service,
    installer_assigned: hasInstaller ? installer.name : 'UNASSIGNED — needs manual follow-up',
    installer_email: hasInstaller ? installer.email : '',
    firstname: cleanString(payload.firstname),
    lastname: cleanString(payload.lastname),
    email: cleanString(payload.email),
    phone: cleanString(payload.phone),
    postal: cleanString(payload.postal),
    // The retrofit-assessment checklist sends flat fields, not a calc_result
    // object — that mismatch previously meant every field below silently
    // fell back to 'unknown' no matter what the homeowner selected.
    utility: cleanString(payload.utility || 'unknown'),
    current_heat: cleanString(payload.current_heating || 'unknown'),
    water_heating: cleanString(payload.water_heating || 'unknown'),
    year_built: cleanString(payload.year_built || 'unknown'),
    income_tier: cleanString(payload.income_tier || 'unknown'),
    // The single most important field: what the homeowner actually wants.
    // Previously captured by the frontend and then silently dropped.
    upgrades: Array.isArray(payload.upgrades) ? payload.upgrades.join(', ') : cleanString(payload.upgrades || ''),
    notes: cleanString(payload.notes || ''),
    estimated_value: cleanString(payload.estimated_rebates || 'unknown'),
    total_cost: cleanString(payload.total_cost || 'unknown'),
    net_cost: cleanString(payload.net_cost || 'unknown'),
    ten_year_savings: cleanString(payload.ten_year_savings || 'unknown'),
    page_url: cleanString(payload.page_url || payload.page || ''),
    referrer: cleanString(payload.referrer || 'direct'),
    status: 'new'
  };

  // ---- Fan out to email, sheet, and ops inbox in parallel ----
  // If there's no installer configured yet, skip sendInstallerEmail entirely
  // (there's no inbox to send to) — ops still gets notified so a human picks
  // it up, and the lead is still logged to the sheet.
  const tasks = [
    sendLeadConfirmation(lead, hasInstaller ? installer : null, env),
    sendOpsEmail(lead, env),
    logToSheet(lead, env),
    startResultsDrip({
      email: lead.email, city: lead.city, province: 'BC',
      heating: lead.current_heat, income: lead.income_tier,
      estimate: lead.estimated_value, source: 'retrofit-assessment'
    }, env)
  ];
  if (hasInstaller) {
    tasks.unshift(sendInstallerEmail(lead, installer, env));
  }

  const results = await Promise.allSettled(tasks);
  const taskNames = hasInstaller
    ? ['installer', 'confirmation', 'ops', 'sheet', 'drip']
    : ['confirmation', 'ops', 'sheet', 'drip'];

  const failures = results
    .map((r, i) => ({ r, name: taskNames[i] }))
    .filter(x => x.r.status === 'rejected');

  if (failures.length) {
    console.error('Lead routing partial failure:', failures.map(f => `${f.name}: ${f.r.reason}`));
  }

  return jsonResponse({
    success: true,
    lead_id: leadId,
    installer_name: hasInstaller ? installer.name : null,
    installer_phone: hasInstaller ? installer.phone : null
  }, 200);
}

// ===========================================================================
// ROUTE 2 — /waitlist (out-of-area signup from /ca/bc and homepage)
// ===========================================================================
// Lighter capture: email + city_name (free text) + optional postal.
// No installer routing (by definition — we don't have one yet for this area).
// Sends a confirmation email so the homeowner has something tangible,
// notifies ops, and logs to the same Google Sheet (different tab via record_type).

async function handleWaitlistSubmit(request, env) {
  let payload;
  try {
    payload = await request.json();
  } catch (e) {
    return jsonResponse({ error: 'Invalid JSON' }, 400);
  }

  // Honeypot
  if (payload.website) {
    return jsonResponse({ success: true }, 200);
  }

  // ---- Required: email + city_name. Postal is optional. ----
  const requiredW = ['email', 'city_name'];
  const missingW = requiredW.filter(f => !payload[f]);
  if (missingW.length) {
    return jsonResponse({ error: `Missing fields: ${missingW.join(', ')}` }, 400);
  }

  // Email format
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email)) {
    return jsonResponse({ error: 'Invalid email' }, 400);
  }

  // Optional postal — validate only if provided
  if (payload.postal && !/^[A-Za-z][0-9][A-Za-z][ -]?[0-9][A-Za-z][0-9]$/.test(payload.postal)) {
    return jsonResponse({ error: 'Invalid postal code' }, 400);
  }

  // Soft length cap on city_name (max 80 chars, matches the form's maxlength)
  const cityName = cleanString(payload.city_name);
  if (cityName.length < 2) {
    return jsonResponse({ error: 'Please enter a valid city name' }, 400);
  }

  const waitlistId = crypto.randomUUID();
  const timestamp = new Date().toISOString();

  // ---- Build waitlist record ----
  const waitlist = {
    record_type: 'waitlist',
    waitlist_id: waitlistId,
    timestamp,
    list: cleanString(payload.list || 'general'),  // 'bc-waitlist' | 'homepage-waitlist' | 'general'
    city_name: cityName,
    postal: cleanString(payload.postal || ''),
    email: cleanString(payload.email),
    page_url: cleanString(payload.page_url || ''),
    referrer: cleanString(payload.referrer || 'direct'),
    status: 'new'
  };

  // ---- Fan out: confirmation to homeowner, ops alert, sheet log ----
  const results = await Promise.allSettled([
    sendWaitlistConfirmation(waitlist, env),
    sendOpsWaitlistAlert(waitlist, env),
    logToSheet(waitlist, env)
  ]);

  const failures = results
    .map((r, i) => ({ r, name: ['confirmation', 'ops', 'sheet'][i] }))
    .filter(x => x.r.status === 'rejected');

  if (failures.length) {
    console.error('Waitlist routing partial failure:', failures.map(f => `${f.name}: ${f.r.reason}`));
  }

  return jsonResponse({
    success: true,
    waitlist_id: waitlistId
  }, 200);
}

// ===========================================================================
// ROUTE 3 — /newsletter (list-building: email + estimate context)
// ===========================================================================
// Lightweight top-of-funnel capture from the homepage/city assessment widget.
// Adds the contact to the Resend audience AND logs to the Google Sheet
// (record_type: 'subscriber') with the estimate context so you can spot
// high-intent subscribers by city. No installer routing — these are
// subscribers, not yet referrals (no phone number).

async function handleNewsletter(request, env) {
  let p;
  try { p = await request.json(); } catch (e) { return jsonResponse({ error: 'Invalid JSON' }, 400); }

  if (p.website) return jsonResponse({ success: true }, 200); // honeypot
  if (!p.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p.email)) {
    return jsonResponse({ error: 'Invalid email' }, 400);
  }

  const record = {
    record_type: 'subscriber',
    timestamp: new Date().toISOString(),
    email: cleanString(p.email),
    city: cleanString(p.city || ''),
    heating: cleanString(p.heating || ''),
    income: cleanString(p.income || ''),
    estimate: cleanString(String(p.estimate || '')),
    source: cleanString(p.source || p.page || ''),
    status: 'new'
  };

  const tasks = [logToSheet(record, env)];
  // Only add to the newsletter audience if they didn't opt out (CASL).
  if (p.newsletter !== false) tasks.unshift(addToResendAudience(record.email, env));
  // Results drip: sends the recap immediately, then a local-comparison and a
  // lock-in-your-numbers email on a delay via the daily cron (see runDripQueue).
  tasks.push(startResultsDrip(record, env));
  const results = await Promise.allSettled(tasks);
  const failures = results.filter(r => r.status === 'rejected');
  if (failures.length) {
    console.error('Newsletter signup partial failure:', failures.map(f => f.reason?.message || f.reason));
  }

  return jsonResponse({ success: true }, 200);
}

// ===========================================================================
// RESULTS DRIP — recap on signup, local comparison at +2d, lock-in at +5d
// ===========================================================================
// Table: subscribers (OUTCOMES_DB, see schema-subscribers.sql). New signups
// get the recap email synchronously and start the drip; repeat signups (e.g.
// re-running the calculator) just refresh their saved context and don't
// restart or resend anything.

const DRIP_DAY_MS = 24 * 60 * 60 * 1000;

async function startResultsDrip(p, env) {
  if (!env.OUTCOMES_DB || !p.email) return;
  if (p.newsletter === false) return; // respect CASL opt-out on any entry point

  const province = String(p.province || 'BC').toUpperCase();
  const existing = await env.OUTCOMES_DB.prepare('SELECT id FROM subscribers WHERE email = ?').bind(p.email).first();

  if (existing) {
    await env.OUTCOMES_DB.prepare(
      `UPDATE subscribers SET city = ?, province = ?, heating = ?, income = ?, estimate = ?, source = ? WHERE id = ?`
    ).bind(p.city, province, p.heating, p.income, p.estimate, p.source, existing.id).run();
    return;
  }

  const id = crypto.randomUUID();
  const now = new Date();
  const nextSendAt = new Date(now.getTime() + 2 * DRIP_DAY_MS).toISOString();

  await env.OUTCOMES_DB.prepare(
    `INSERT INTO subscribers (id, email, city, province, heating, income, estimate, source, step, next_send_at, unsubscribed, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 0, ?)`
  ).bind(id, p.email, p.city, province, p.heating, p.income, p.estimate, p.source, nextSendAt, now.toISOString()).run();

  await sendResultsRecapEmail({ id, email: p.email, city: p.city, province, heating: p.heating, estimate: p.estimate }, env);
}

// Called daily by the Worker's cron trigger (see wrangler.toml [triggers]).
// Sends whichever drip email is due, then either advances to the next step
// or marks the subscriber done (step = 3).
async function runDripQueue(env) {
  if (!env.OUTCOMES_DB || !env.RESEND_API_KEY) return;

  const nowIso = new Date().toISOString();
  const due = await env.OUTCOMES_DB.prepare(
    `SELECT * FROM subscribers WHERE unsubscribed = 0 AND step IN (1, 2) AND next_send_at IS NOT NULL AND next_send_at <= ? LIMIT 200`
  ).bind(nowIso).all();

  for (const sub of due.results || []) {
    try {
      if (sub.step === 1) {
        await sendLocalComparisonEmail(sub, env);
        const nextSendAt = new Date(Date.now() + 3 * DRIP_DAY_MS).toISOString();
        await env.OUTCOMES_DB.prepare('UPDATE subscribers SET step = 2, next_send_at = ? WHERE id = ?').bind(nextSendAt, sub.id).run();
      } else if (sub.step === 2) {
        await sendLockInEmail(sub, env);
        await env.OUTCOMES_DB.prepare('UPDATE subscribers SET step = 3, next_send_at = NULL WHERE id = ?').bind(sub.id).run();
      }
    } catch (err) {
      console.error(`Drip send failed for subscriber ${sub.id} (step ${sub.step}):`, err.message || err);
    }
  }
}

async function handleUnsubscribe(request, env) {
  const id = new URL(request.url).searchParams.get('id');
  if (id && env.OUTCOMES_DB) {
    await env.OUTCOMES_DB.prepare('UPDATE subscribers SET unsubscribed = 1, next_send_at = NULL WHERE id = ?').bind(id).run();
  }
  return new Response(
    `<!doctype html><html><head><title>Unsubscribed</title><meta name="viewport" content="width=device-width, initial-scale=1"></head>
     <body style="font-family:-apple-system,sans-serif;max-width:480px;margin:80px auto;text-align:center;color:#08363f;padding:0 20px;">
       <h1 style="font-size:22px;">You're unsubscribed</h1>
       <p>No more emails from this sequence. If that was a mistake, just resubmit the calculator on <a href="https://homepowerrebate.com">homepowerrebate.com</a>.</p>
     </body></html>`,
    { status: 200, headers: { 'Content-Type': 'text/html; charset=utf-8', ...CORS_HEADERS } }
  );
}

function dripEmailFooter(sub) {
  const unsubUrl = `https://leads.homepowerrebate.com/unsubscribe?id=${sub.id}`;
  return `
    <p style="margin:24px 0 0;font-size:12px;color:#6b7d80;text-align:center;">
      HomePowerRebate &middot; Independent installer matching service<br>
      <a href="https://homepowerrebate.com" style="color:#6b7d80;">homepowerrebate.com</a> &middot; <a href="${unsubUrl}" style="color:#6b7d80;">Unsubscribe</a>
    </p>`;
}

// Province-specific "learn more" links + the program name used in copy.
// Every entry points at a real, published guide — never invent a link here.
const PROVINCE_CONTEXT = {
  BC: {
    programName: 'CleanBC',
    links: [
      { href: 'https://homepowerrebate.com/blog/heat-pump-rebate-guide-bc-2026/', label: 'Full BC Heat Pump Rebate Guide' },
      { href: 'https://homepowerrebate.com/blog/heat-pumps-explained-bc/', label: 'Heat Pumps Explained' }
    ]
  },
  ON: {
    programName: 'Home Renovation Savings Program',
    links: [
      { href: 'https://homepowerrebate.com/blog/ontario-home-renovation-savings-program-explained/', label: 'How the Ontario Program Works' },
      { href: 'https://homepowerrebate.com/blog/ontario-home-energy-rebates-2026-listicle/', label: 'All 9 Ontario Rebate Categories' }
    ]
  },
  AB: {
    programName: 'Alberta',
    links: [
      { href: 'https://homepowerrebate.com/blog/alberta-16-applications-one-grant/', label: 'Alberta Rebate Programs Explained' }
    ]
  },
  NS: {
    programName: 'Nova Scotia',
    links: [
      { href: 'https://homepowerrebate.com/blog/nova-scotia-heat-pump-rebate-disappeared/', label: 'Nova Scotia Heat Pump Rebate Guide' }
    ]
  },
  MA: {
    programName: 'Mass Save',
    links: [
      { href: 'https://homepowerrebate.com/blog/mass-save-home-energy-assessment-explained/', label: 'Mass Save Home Energy Assessment Guide' }
    ]
  }
};

function provinceContext(sub) {
  return PROVINCE_CONTEXT[String(sub.province || 'BC').toUpperCase()] || PROVINCE_CONTEXT.BC;
}

// Looks up the city's published heat-pump rebate range so the recap email can
// show a real number even when the triggering form (e.g. the homepage
// quick-capture widget) never collected sub.estimate. Keyed on the same
// province/city pairing used across the site's city pages.
function normalizeCityKey(s) {
  return String(s || '').toLowerCase().replace(/[.,]/g, '').replace(/\s+/g, ' ').trim();
}

function cityRebateLookup(sub) {
  const key = `${normalizeCityKey(sub.province || 'BC')}|${normalizeCityKey(sub.city)}`;
  return CITY_REBATE_LOOKUP[key] || null;
}

function learnMoreBlock(sub) {
  const ctx = provinceContext(sub);
  const links = [...ctx.links, { href: 'https://homepowerrebate.com/blog/canada-provinces-ranked-home-energy-rebates/', label: 'How Every Province Compares' }];
  return `
    <div style="margin:20px 0 0;padding-top:16px;border-top:1px solid #d9d0c1;">
      <p style="margin:0 0 8px;font-size:12px;color:#6b7d80;text-transform:uppercase;letter-spacing:0.04em;">Worth reading next</p>
      ${links.map(l => `<a href="${l.href}" style="display:block;font-size:14px;color:#08363f;text-decoration:underline;margin-bottom:4px;">${escapeHtml(l.label)} →</a>`).join('')}
    </div>`;
}

function getQuotesUrl(sub) {
  return `https://homepowerrebate.com/get-quotes/?city=${encodeURIComponent(sub.city || '')}&province=${encodeURIComponent(String(sub.province || 'BC').toUpperCase())}`;
}

async function sendResultsRecapEmail(sub, env) {
  if (!env.RESEND_API_KEY) return Promise.resolve();
  const ctx = provinceContext(sub);

  // The quick-capture widget only submits city + email, so sub.estimate is
  // often blank/'unknown'. Fall back to the city's real published heat-pump
  // rebate range rather than showing a placeholder.
  const cityData = cityRebateLookup(sub);
  const rawEstimate = String(sub.estimate || '').trim();
  const estimate = (rawEstimate && rawEstimate.toLowerCase() !== 'unknown')
    ? rawEstimate
    : (cityData ? cityData.heat_pump_rebate : '');

  const rawHeating = String(sub.heating || '').trim();
  const heatingRow = (rawHeating && rawHeating.toLowerCase() !== 'unknown')
    ? `<tr><td style="padding:8px 0;color:#1a3d42;">Current heating:</td><td style="padding:8px 0;font-weight:600;">${escapeHtml(capitalize(rawHeating))}</td></tr>`
    : '';

  const html = `
    <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:560px;margin:0 auto;padding:20px;color:#0a2a2e;">
      <div style="background:#08363f;color:#faf7f2;padding:28px 24px;border-radius:14px 14px 0 0;">
        <div style="font-family:Georgia,serif;font-size:14px;color:#e88a2e;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:10px;">Your results</div>
        <h1 style="margin:0;font-family:Georgia,serif;font-size:26px;font-weight:500;line-height:1.2;">Here's the breakdown you asked for.</h1>
      </div>
      <div style="background:#faf7f2;padding:28px 24px;border-radius:0 0 14px 14px;border:1px solid #d9d0c1;border-top:none;">
        <div style="background:white;border:1px solid #d9d0c1;border-radius:10px;padding:16px;margin-bottom:16px;">
          <table style="width:100%;border-collapse:collapse;font-size:14px;">
            <tr><td style="padding:8px 0;color:#1a3d42;font-weight:600;width:50%;">Estimated ${escapeHtml(ctx.programName)} rebates:</td><td style="padding:8px 0;color:#2d6a4f;font-weight:700;font-size:18px;">${escapeHtml(estimate || 'see your assessment')}</td></tr>
            <tr><td style="padding:8px 0;color:#1a3d42;">City:</td><td style="padding:8px 0;font-weight:600;">${escapeHtml(capitalize(sub.city || ''))}</td></tr>
            ${heatingRow}
          </table>
        </div>
        <p style="font-size:15px;line-height:1.6;margin:0 0 12px;">Keep this for reference — in a couple days we'll send you what homeowners near you actually paid, so you can sanity-check any quote against real numbers, not just estimates.</p>
        <p style="font-size:15px;line-height:1.6;margin:0;"><a href="${getQuotesUrl(sub)}" style="display:inline-block;padding:12px 20px;background:#d4751c;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">Get matched with an installer →</a></p>
        ${learnMoreBlock(sub)}
        ${dripEmailFooter(sub)}
      </div>
    </div>`;

  return resendEmail(env.RESEND_API_KEY, {
    from: 'HomePowerRebate <hello@homepowerrebate.com>',
    to: sub.email,
    subject: `Your ${sub.city ? capitalize(sub.city) + ' ' : ''}rebate breakdown`,
    html
  });
}

async function sendLocalComparisonEmail(sub, env) {
  if (!env.RESEND_API_KEY) return Promise.resolve();
  const province = String(sub.province || 'BC').toUpperCase();

  let comparisonHtml = `<p style="font-size:15px;line-height:1.6;margin:0 0 16px;">We're still building up verified cost data in your area — but homeowners who've had work done are starting to share what they actually paid. <a href="https://homepowerrebate.com/share-your-cost/">Add yours</a> and we'll send you the local average as soon as we have enough submissions.</p>`;

  if (env.OUTCOMES_DB) {
    try {
      const comparison = await computeComparison(env, 'heat-pump', String(sub.city || '').toLowerCase(), province, null);
      const shownTier = comparison.tiers.find(t => t.shown);
      if (shownTier) {
        const scopeLabel = shownTier.scope === 'city' ? capitalize(sub.city || '') : shownTier.scope === 'province' ? `${province}-wide` : 'Nationally';
        comparisonHtml = `
          <div style="background:white;border:1px solid #d9d0c1;border-radius:10px;padding:16px;margin-bottom:16px;">
            <p style="margin:0 0 6px;font-size:13px;color:#6b7d80;text-transform:uppercase;letter-spacing:0.04em;">${escapeHtml(scopeLabel)} average, based on ${shownTier.sample_size} verified homeowner${shownTier.sample_size === 1 ? '' : 's'}</p>
            <p style="margin:0;font-size:24px;font-weight:700;color:#2d6a4f;">$${shownTier.avg_net_cost.toLocaleString()} <span style="font-size:14px;font-weight:400;color:#1a3d42;">net cost after rebates</span></p>
          </div>
          <p style="font-size:15px;line-height:1.6;margin:0 0 16px;">Use this as a sanity check against any quote you get — if a number comes in wildly higher, ask why before you sign. Based on homeowner-submitted data on <a href="https://homepowerrebate.com/share-your-cost/">homepowerrebate.com/share-your-cost</a>, not official program figures.</p>`;
      }
    } catch (err) {
      console.error('Local comparison lookup failed:', err.message || err);
    }
  }

  const html = `
    <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:560px;margin:0 auto;padding:20px;color:#0a2a2e;">
      <div style="background:#08363f;color:#faf7f2;padding:28px 24px;border-radius:14px 14px 0 0;">
        <div style="font-family:Georgia,serif;font-size:14px;color:#e88a2e;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:10px;">Real numbers</div>
        <h1 style="margin:0;font-family:Georgia,serif;font-size:24px;font-weight:500;line-height:1.2;">What homeowners near you actually paid.</h1>
      </div>
      <div style="background:#faf7f2;padding:28px 24px;border-radius:0 0 14px 14px;border:1px solid #d9d0c1;border-top:none;">
        ${comparisonHtml}
        <p style="font-size:15px;line-height:1.6;margin:0;"><a href="${getQuotesUrl(sub)}" style="display:inline-block;padding:12px 20px;background:#d4751c;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">Get matched with an installer →</a></p>
        ${learnMoreBlock(sub)}
        ${dripEmailFooter(sub)}
      </div>
    </div>`;

  return resendEmail(env.RESEND_API_KEY, {
    from: 'HomePowerRebate <hello@homepowerrebate.com>',
    to: sub.email,
    subject: `What ${sub.city ? capitalize(sub.city) + ' ' : province + ' '}homeowners actually paid`,
    html
  });
}

async function sendLockInEmail(sub, env) {
  if (!env.RESEND_API_KEY) return Promise.resolve();
  const ctx = provinceContext(sub);

  const html = `
    <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:560px;margin:0 auto;padding:20px;color:#0a2a2e;">
      <div style="background:#08363f;color:#faf7f2;padding:28px 24px;border-radius:14px 14px 0 0;">
        <div style="font-family:Georgia,serif;font-size:14px;color:#e88a2e;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:10px;">Worth knowing</div>
        <h1 style="margin:0;font-family:Georgia,serif;font-size:24px;font-weight:500;line-height:1.2;">Rebate amounts and rules change without notice.</h1>
      </div>
      <div style="background:#faf7f2;padding:28px 24px;border-radius:0 0 14px 14px;border:1px solid #d9d0c1;border-top:none;">
        <p style="font-size:15px;line-height:1.6;margin:0 0 16px;">${escapeHtml(ctx.programName)}, utility, and municipal programs update their numbers and eligibility rules more often than most homeowners expect. The estimate we sent you was accurate when you ran it — the way to lock in real numbers is to get an actual quote from a local installer while today's programs are still active.</p>
        <p style="font-size:15px;line-height:1.6;margin:0 0 16px;">No obligation, and it costs nothing to ask — you'll see exactly what applies to your home before you decide anything.</p>
        <p style="font-size:15px;line-height:1.6;margin:0;"><a href="${getQuotesUrl(sub)}" style="display:inline-block;padding:12px 20px;background:#d4751c;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">Get a real quote →</a></p>
        ${learnMoreBlock(sub)}
        ${dripEmailFooter(sub)}
      </div>
    </div>`;

  return resendEmail(env.RESEND_API_KEY, {
    from: 'HomePowerRebate <hello@homepowerrebate.com>',
    to: sub.email,
    subject: `Before you wait any longer on ${sub.city ? capitalize(sub.city) : 'your'} rebates`,
    html
  });
}

// ===========================================================================
// ROUTE 4 — /estimate-lead (a referral: adds name + phone to an estimate)
// ===========================================================================
// The second tier of the assessment widget. Once a subscriber adds their
// name + phone, they become an installer-ready referral: routed to the
// matched heat-pump installer (or ops if none/placeholder), logged to the
// Sheet as a 'lead', and kept on the Resend list.

async function handleEstimateLead(request, env) {
  let p;
  try { p = await request.json(); } catch (e) { return jsonResponse({ error: 'Invalid JSON' }, 400); }

  if (p.website) return jsonResponse({ success: true }, 200); // honeypot

  const required = ['email', 'firstname', 'phone', 'city'];
  const missing = required.filter(f => !p[f]);
  if (missing.length) return jsonResponse({ error: `Missing fields: ${missing.join(', ')}` }, 400);
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p.email)) return jsonResponse({ error: 'Invalid email' }, 400);

  const city = String(p.city || '').toLowerCase().trim();
  const service = 'heat-pump';

  // Use homeowner-selected installer (from form) OR fall back to routing table
  const selectedName = String(p.installer_name || '').trim();
  const selectedEmail = String(p.installer_email || '').trim();
  const selectedPhone = String(p.installer_phone || '').trim();

  let installer = null;
  let isReal = false;

  // Prefer homeowner selection if provided
  if (selectedName && selectedEmail) {
    installer = {
      name: selectedName,
      email: selectedEmail,
      phone: selectedPhone,
      cc: ''
    };
    isReal = selectedEmail && !/example\.com$/i.test(selectedEmail);
  } else {
    // Fall back to routing table (old behavior for direct submits)
    installer = (INSTALLER_ROUTING[service] || {})[city];
    isReal = installer && !/example\.com$/i.test(installer.email);
  }

  const lead = {
    record_type: 'lead',
    lead_id: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    city,
    province: cleanString(p.province || 'BC').toUpperCase(),
    service,
    installer_assigned: installer ? installer.name : 'UNASSIGNED — needs manual follow-up',
    installer_email: isReal ? installer.email : '',
    firstname: cleanString(p.firstname),
    lastname: cleanString(p.lastname || ''),
    email: cleanString(p.email),
    phone: cleanString(p.phone),
    postal: cleanString(p.postal || ''),
    current_heat: cleanString(p.heating || p.current_heating || 'unknown'),
    income_band: cleanString(p.income || p.income_tier || 'unknown'),
    income_tier: cleanString(p.income_tier || p.income || 'unknown'),
    utility: cleanString(p.utility || 'unknown'),
    water_heating: cleanString(p.water_heating || 'unknown'),
    year_built: cleanString(p.year_built || 'unknown'),
    upgrades: Array.isArray(p.upgrades) ? p.upgrades.join(', ') : cleanString(p.upgrades || ''),
    notes: cleanString(p.notes || ''),
    estimated_value: cleanString(String(p.estimate || p.estimated_rebates || 'unknown')),
    total_cost: cleanString(p.total_cost || 'unknown'),
    net_cost: cleanString(p.net_cost || 'unknown'),
    ten_year_savings: cleanString(p.ten_year_savings || 'unknown'),
    page_url: cleanString(p.page_url || p.source || p.page || ''),
    referrer: cleanString(p.referrer || 'estimate-widget'),
    status: 'new'
  };

  const tasks = [
    sendOpsEstimateLead(lead, env),
    logToSheet(lead, env),
    startResultsDrip({
      email: lead.email, city: lead.city, province: lead.province,
      heating: lead.current_heat, income: lead.income_tier,
      estimate: lead.estimated_value, source: lead.page_url || 'get-quotes',
      newsletter: p.newsletter
    }, env)
  ];
  // Only add to the newsletter audience if they didn't opt out (CASL).
  if (p.newsletter !== false) tasks.push(addToResendAudience(lead.email, env));
  if (isReal) tasks.unshift(sendEstimateInstallerEmail(lead, installer, env));

  const results = await Promise.allSettled(tasks);
  const failures = results.filter(r => r.status === 'rejected');
  if (failures.length) {
    console.error('Estimate-lead routing partial failure:', failures.map(f => f.reason?.message || f.reason));
  }

  return jsonResponse({
    success: true,
    lead_id: lead.lead_id,
    installer_name: installer ? installer.name : null,
    installer_phone: installer ? installer.phone : null
  }, 200);
}

// ===========================================================================
// ROUTE 5 — /outcomes/submit (verified-outcomes: "give to get" comparison)
// ===========================================================================
// A homeowner reports what they actually paid, post-install. In exchange,
// the response includes their own comparison stats immediately — that's
// the incentive to submit (no email round-trip required to see it).
// Full postal code and address are never stored — only the FSA (first 3
// characters), city, and province, which is enough to build a comparison
// without being personally identifying.

async function handleOutcomeSubmit(request, env) {
  let p;
  try { p = await request.json(); } catch (e) { return jsonResponse({ error: 'Invalid JSON' }, 400); }

  if (p.website) return jsonResponse({ success: true }, 200); // honeypot

  const required = ['email', 'category', 'postal', 'city', 'province', 'install_month', 'total_cost'];
  const missing = required.filter(f => p[f] === undefined || p[f] === null || p[f] === '');
  if (missing.length) return jsonResponse({ error: `Missing fields: ${missing.join(', ')}` }, 400);

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p.email)) {
    return jsonResponse({ error: 'Invalid email' }, 400);
  }

  const category = String(p.category).toLowerCase().trim();
  if (!OUTCOME_CATEGORIES.includes(category)) {
    return jsonResponse({ error: `Unknown category: ${category}` }, 400);
  }

  const postalFsa = extractFsa(p.postal, p.province);
  if (!postalFsa) return jsonResponse({ error: 'Invalid postal/zip code' }, 400);

  if (!/^\d{4}-\d{2}$/.test(String(p.install_month))) {
    return jsonResponse({ error: 'install_month must be YYYY-MM' }, 400);
  }

  const totalCost = Number(p.total_cost);
  const rebatesReceived = Number(p.rebates_received || 0);
  if (!Number.isFinite(totalCost) || totalCost <= 0) {
    return jsonResponse({ error: 'total_cost must be a positive number' }, 400);
  }
  if (!Number.isFinite(rebatesReceived) || rebatesReceived < 0) {
    return jsonResponse({ error: 'rebates_received must be a non-negative number' }, 400);
  }

  // Plausibility bounds — this endpoint is open to anyone (no booking or
  // lead required), so this is the main defense against joke/bot entries.
  const [minCost, maxCost] = PLAUSIBLE_COST_RANGE[category];
  if (totalCost < minCost || totalCost > maxCost) {
    return jsonResponse({ error: `total_cost for ${category} should be between $${minCost} and $${maxCost}` }, 400);
  }
  if (rebatesReceived > totalCost) {
    return jsonResponse({ error: 'rebates_received cannot exceed total_cost' }, 400);
  }

  const netCost = Math.max(0, totalCost - rebatesReceived);
  const city = cleanString(p.city).toLowerCase();
  const province = cleanString(p.province).toUpperCase();
  const billBefore = p.monthly_bill_before != null ? Number(p.monthly_bill_before) : null;
  const billAfter = p.monthly_bill_after != null ? Number(p.monthly_bill_after) : null;

  const id = crypto.randomUUID();
  const createdAt = new Date().toISOString();

  if (!env.OUTCOMES_DB) {
    return jsonResponse({ error: 'Outcomes database not configured' }, 500);
  }

  // Rate limit: same email can't flood a category/city with fake submissions.
  const email = cleanString(p.email).toLowerCase();
  const since = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  const recentCount = await env.OUTCOMES_DB.prepare(
    `SELECT COUNT(*) AS n FROM outcomes WHERE email = ? AND created_at >= ?`
  ).bind(email, since).first();
  if ((recentCount?.n || 0) >= MAX_SUBMISSIONS_PER_EMAIL_PER_DAY) {
    return jsonResponse({ error: 'Too many submissions from this email in the last 24 hours' }, 429);
  }

  try {
    const otherCategories = Array.isArray(p.other_categories)
      ? p.other_categories.map(c => String(c).toLowerCase().trim()).filter(c => OUTCOME_CATEGORIES.includes(c) && c !== category)
      : [];

    await env.OUTCOMES_DB.prepare(
      `INSERT INTO outcomes
        (id, created_at, category, postal_fsa, city, province, install_month,
         total_cost, rebates_received, net_cost, monthly_bill_before, monthly_bill_after,
         installer_name, other_categories, verified, email, status)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'new')`
    ).bind(
      id, createdAt, category, postalFsa, city, province, String(p.install_month),
      totalCost, rebatesReceived, netCost,
      Number.isFinite(billBefore) ? billBefore : null,
      Number.isFinite(billAfter) ? billAfter : null,
      cleanString(p.installer_name || ''),
      otherCategories.join(','),
      email
    ).run();
  } catch (e) {
    console.error('Outcome insert failed:', e);
    return jsonResponse({ error: 'Failed to save outcome' }, 500);
  }

  // Give-to-get: return this homeowner's comparison immediately.
  const comparison = await computeComparison(env, category, city, province, netCost);

  // Fire-and-forget: log to sheet + notify ops so submissions are visible
  // alongside leads/waitlist without adding latency to the response.
  const record = {
    record_type: 'outcome',
    outcome_id: id,
    timestamp: createdAt,
    category, city, province,
    postal_fsa: postalFsa,
    install_month: String(p.install_month),
    total_cost: totalCost,
    rebates_received: rebatesReceived,
    net_cost: netCost,
    installer_name: cleanString(p.installer_name || ''),
    email,
    status: 'new'
  };
  Promise.allSettled([logToSheet(record, env), sendOpsOutcomeAlert(record, env)]);

  return jsonResponse({ success: true, outcome_id: id, comparison }, 200);
}

// ===========================================================================
// ROUTE 6 — /outcomes/compare (GET: read-only comparison lookup)
// ===========================================================================
// Lets a page (e.g. a blog post or city hub) show live comparison stats
// without requiring a fresh submission — used for the "see how others in
// BC compare" widgets. Same tiering/threshold logic as the submit response.

async function handleOutcomeCompare(request, env) {
  const url = new URL(request.url);
  const category = String(url.searchParams.get('category') || '').toLowerCase().trim();
  const city = String(url.searchParams.get('city') || '').toLowerCase().trim();
  const province = String(url.searchParams.get('province') || '').toUpperCase().trim();
  const valueParam = url.searchParams.get('value');
  const value = valueParam != null ? Number(valueParam) : null;

  if (!OUTCOME_CATEGORIES.includes(category)) {
    return jsonResponse({ error: `Unknown or missing category` }, 400);
  }
  if (!env.OUTCOMES_DB) {
    return jsonResponse({ error: 'Outcomes database not configured' }, 500);
  }

  const comparison = await computeComparison(env, category, city, province, Number.isFinite(value) ? value : null);
  return jsonResponse({ success: true, comparison }, 200);
}

// ===========================================================================
// OUTCOMES: shared aggregation logic (city -> province -> national tiers)
// ===========================================================================

async function computeComparison(env, category, city, province, netCostForPercentile) {
  const tiers = [];

  if (city) tiers.push(await tierStats(env, 'city', category, 'city = ?', [city]));
  if (province) tiers.push(await tierStats(env, 'province', category, 'province = ?', [province]));
  tiers.push(await tierStats(env, 'national', category, '1 = 1', []));

  // Percentile against the narrowest tier that meets MIN_SAMPLE, falling
  // back wider if the neighbourhood-level sample is too thin to be useful.
  let percentile = null;
  if (netCostForPercentile != null) {
    for (const tier of tiers) {
      if (tier.n < MIN_SAMPLE) continue;
      const scope = tier.scope;
      const where = scope === 'city' ? 'city = ?' : scope === 'province' ? 'province = ?' : '1 = 1';
      const binds = scope === 'city' ? [city] : scope === 'province' ? [province] : [];
      const row = await env.OUTCOMES_DB.prepare(
        `SELECT COUNT(*) AS below FROM outcomes WHERE category = ? AND ${where} AND net_cost <= ?`
      ).bind(category, ...binds, netCostForPercentile).first();
      percentile = {
        scope,
        // "you paid less than X% of homeowners" — cheaper is better, so this
        // is the share of the comparison group at or above your cost.
        cheaper_than_pct: Math.round((1 - (row.below / tier.n)) * 100)
      };
      break;
    }
  }

  return {
    category,
    tiers: tiers.map(t => ({
      scope: t.scope,
      sample_size: t.n,
      shown: t.n >= MIN_SAMPLE,
      avg_net_cost: t.n > 0 ? Math.round(t.avgNet) : null
    })),
    percentile
  };
}

async function tierStats(env, scope, category, whereClause, binds) {
  const row = await env.OUTCOMES_DB.prepare(
    `SELECT COUNT(*) AS n, AVG(net_cost) AS avg_net FROM outcomes WHERE category = ? AND ${whereClause}`
  ).bind(category, ...binds).first();
  return { scope, n: row?.n || 0, avgNet: row?.avg_net || 0 };
}

// Derive a privacy-safe area code from a full postal/zip code. Canadian FSA
// (first 3 chars, e.g. "V6B") or US ZIP3 (first 3 digits, e.g. "021") —
// never store the full code.
function extractFsa(postal, province) {
  const raw = String(postal || '').toUpperCase().replace(/\s/g, '');
  if (String(province).toUpperCase() === 'MA') {
    return /^\d{5}$/.test(raw) ? raw.slice(0, 3) : null;
  }
  return /^[A-Z]\d[A-Z]\d[A-Z]\d$/.test(raw) ? raw.slice(0, 3) : null;
}

async function sendOpsOutcomeAlert(record, env) {
  if (!env.OPS_EMAIL) return Promise.resolve();
  return resendEmail(env.RESEND_API_KEY, {
    from: 'HomePowerRebate <ops@homepowerrebate.com>',
    to: env.OPS_EMAIL,
    subject: `[Outcome] ${record.category} in ${capitalize(record.city)}, ${record.province} — net $${record.net_cost}`,
    html: `
      <p>New verified-outcomes submission.</p>
      <ul>
        <li><strong>Category:</strong> ${escapeHtml(record.category)}</li>
        <li><strong>Location:</strong> ${escapeHtml(capitalize(record.city))}, ${escapeHtml(record.province)} (${escapeHtml(record.postal_fsa)})</li>
        <li><strong>Install month:</strong> ${escapeHtml(record.install_month)}</li>
        <li><strong>Total cost:</strong> $${record.total_cost}</li>
        <li><strong>Rebates received:</strong> $${record.rebates_received}</li>
        <li><strong>Net cost:</strong> $${record.net_cost}</li>
        <li><strong>Installer:</strong> ${escapeHtml(record.installer_name || '(not provided)')}</li>
        <li><strong>Email:</strong> ${escapeHtml(record.email)}</li>
      </ul>`
  });
}

// ===========================================================================
// EMAIL: compact installer + ops notifications for estimate leads
// ===========================================================================

async function sendEstimateInstallerEmail(lead, installer, env) {
  const fn = escapeHtml(lead.firstname), ln = escapeHtml(lead.lastname), ph = escapeHtml(lead.phone),
        em = escapeHtml(lead.email), ct = escapeHtml(capitalize(lead.city)), ch = escapeHtml(lead.current_heat),
        ev = escapeHtml(lead.estimated_value), instName = escapeHtml(installer.name.split(' ')[0] || 'there');

  const notesBlock = lead.notes
    ? `<div style="background:#fef9e6;border-left:4px solid #d4751c;border-radius:0 8px 8px 0;padding:16px 18px;margin:20px 0;">
        <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#a15d10;margin-bottom:6px;">In their own words</div>
        <div style="font-size:15px;color:#08363f;">${escapeHtml(lead.notes)}</div>
      </div>`
    : '';

  return resendEmail(env.RESEND_API_KEY, {
    from: 'HomePowerRebate <leads@homepowerrebate.com>',
    to: installer.email,
    cc: installer.cc || undefined,
    bcc: env.OPS_EMAIL || undefined,
    reply_to: lead.email,
    subject: `${fn} in ${ct} wants a quote — sent via HomePowerRebate`,
    html: `
      <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:580px;margin:0 auto;padding:0;color:#0a2a2e;">
        <div style="background:#08363f;padding:28px 28px 24px;border-radius:14px 14px 0 0;">
          <div style="font-size:13px;color:#e88a2e;letter-spacing:.06em;text-transform:uppercase;font-weight:700;margin-bottom:10px;">New lead from HomePowerRebate.com</div>
          <div style="font-size:22px;color:#fff;font-weight:600;line-height:1.3;">Hi ${instName} — a ${ct} homeowner wants your help.</div>
        </div>

        <div style="background:#faf7f2;padding:28px;border-radius:0 0 14px 14px;border:1px solid #d9d0c1;border-top:none;">
          <p style="font-size:15px;line-height:1.6;color:#1a3d42;margin:0 0 20px;">
            ${fn} used HomePowerRebate's free rebate assessment tool, saw what they qualify for, and chose <strong>${escapeHtml(installer.name)}</strong> as one of the installers they'd like a quote from. Here's what they're looking for:
          </p>

          <div style="background:#fff;border:1px solid #d9d0c1;border-radius:10px;padding:20px;margin-bottom:20px;">
            <table style="width:100%;border-collapse:collapse;font-size:14px;">
              <tr><td style="padding:6px 0;color:#6b7d80;width:130px;">Name</td><td style="padding:6px 0;font-weight:600;color:#08363f;">${fn} ${ln}</td></tr>
              <tr><td style="padding:6px 0;color:#6b7d80;">Phone</td><td style="padding:6px 0;font-weight:600;"><a href="tel:${ph}" style="color:#08363f;">${ph}</a></td></tr>
              <tr><td style="padding:6px 0;color:#6b7d80;">Email</td><td style="padding:6px 0;font-weight:600;"><a href="mailto:${em}" style="color:#08363f;">${em}</a></td></tr>
              <tr><td style="padding:6px 0;color:#6b7d80;">City</td><td style="padding:6px 0;font-weight:600;color:#08363f;">${ct}, BC</td></tr>
              <tr><td style="padding:6px 0;color:#6b7d80;">Current heating</td><td style="padding:6px 0;font-weight:600;color:#08363f;">${ch}</td></tr>
              <tr><td style="padding:6px 0;color:#6b7d80;">Interested in</td><td style="padding:6px 0;font-weight:600;color:#08363f;">${escapeHtml(lead.upgrades || 'not specified')}</td></tr>
              <tr><td style="padding:6px 0;color:#6b7d80;">Rebate estimate shown</td><td style="padding:6px 0;font-weight:700;color:#2d6a4f;">up to ${ev}</td></tr>
            </table>
          </div>

          ${notesBlock}

          <div style="background:#0a2a2e;color:#faf7f2;padding:20px;border-radius:10px;text-align:center;margin-top:8px;">
            <p style="margin:0 0 4px;font-size:13px;opacity:.75;">They're expecting to hear from you</p>
            <p style="margin:0 0 14px;font-size:16px;font-weight:600;">Please reach out within 1 business day.</p>
            <a href="tel:${ph}" style="display:inline-block;background:#d4751c;color:#fff;padding:12px 26px;border-radius:999px;text-decoration:none;font-weight:600;">Call ${ph}</a>
            <p style="margin:14px 0 0;font-size:12px;opacity:.65;">Prefer email? Just hit reply — it goes straight to ${em}, not to us.</p>
          </div>

          <p style="font-size:13px;color:#6b7d80;text-align:center;margin:22px 0 0;">
            Note: this homeowner may have also requested quotes from a couple of other local installers — that's by design, so they can compare.
          </p>

          <div style="border-top:1px solid #d9d0c1;margin-top:24px;padding-top:18px;text-align:center;">
            <p style="margin:0;font-size:13px;color:#6b7d80;">
              Questions about this lead or the partnership? I'm easy to reach.<br>
              <strong style="color:#08363f;">Sam Menard</strong> · HomePowerRebate.com<br>
              <a href="mailto:samuelmenard@gmail.com" style="color:#08363f;">samuelmenard@gmail.com</a>
            </p>
          </div>
        </div>
      </div>`
  });
}

async function sendOpsEstimateLead(lead, env) {
  if (!env.OPS_EMAIL) return Promise.resolve();
  const fn = escapeHtml(lead.firstname), ln = escapeHtml(lead.lastname), ph = escapeHtml(lead.phone),
        em = escapeHtml(lead.email), ct = escapeHtml(lead.city), ch = escapeHtml(lead.current_heat),
        ib = escapeHtml(lead.income_band), ev = escapeHtml(lead.estimated_value), src = escapeHtml(lead.page_url),
        assigned = escapeHtml(lead.installer_assigned);
  const warn = lead.installer_email ? '' :
    `<p style="background:#fef3e6;border:1px solid #e8b87a;padding:10px 14px;border-radius:8px;"><strong>⚠️ No live heat-pump installer for ${ct} yet.</strong> Follow up manually / forward to a partner.</p>`;
  return resendEmail(env.RESEND_API_KEY, {
    from: 'HomePowerRebate <ops@homepowerrebate.com>',
    to: env.OPS_EMAIL,
    subject: `[Referral] ${capitalize(lead.city)} — ${lead.firstname} (${lead.estimated_value})`,
    html: `${warn}
      <p>New estimate referral (routed to <strong>${assigned}</strong>).</p>
      <ul>
        <li><strong>Name:</strong> ${fn} ${ln}</li>
        <li><strong>Phone:</strong> ${ph}</li>
        <li><strong>Email:</strong> ${em}</li>
        <li><strong>City:</strong> ${ct}</li>
        <li><strong>Heating:</strong> ${ch}</li>
        <li><strong>Income band:</strong> ${ib}</li>
        <li><strong>Upgrades wanted:</strong> ${escapeHtml(lead.upgrades || 'none specified')}</li>
        <li><strong>Estimate:</strong> ${ev}</li>
        ${lead.notes ? `<li><strong>Notes from homeowner:</strong> ${escapeHtml(lead.notes)}</li>` : ''}
        <li><strong>Source:</strong> ${src}</li>
      </ul>`
  });
}

// ===========================================================================
// RESEND: add a contact to the newsletter audience
// ===========================================================================

async function addToResendAudience(email, env) {
  if (!env.RESEND_API_KEY) return Promise.resolve();
  const res = await fetch(`https://api.resend.com/audiences/${RESEND_AUDIENCE_ID}/contacts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${env.RESEND_API_KEY}` },
    body: JSON.stringify({ email, unsubscribed: false })
  });
  // "already exists" is fine — don't throw.
  return res.ok ? res.json() : Promise.resolve();
}

// ===========================================================================
// EMAIL: send formatted lead to installer (unchanged)
// ===========================================================================

async function sendInstallerEmail(lead, installer, env) {
  const instName = escapeHtml((installer.name || '').split(' ')[0] || 'there');
  const subject = `${escapeHtml(lead.firstname)} in ${capitalize(lead.city)} wants a quote — sent via HomePowerRebate`;

  const html = `
    <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:600px;margin:0 auto;padding:20px;color:#0a2a2e;">
      <div style="background:#08363f;color:white;padding:24px 20px 20px;border-radius:12px 12px 0 0;">
        <div style="font-size:13px;color:#e88a2e;letter-spacing:.06em;text-transform:uppercase;font-weight:700;margin-bottom:8px;">New lead from HomePowerRebate.com</div>
        <h1 style="margin:0;font-size:22px;font-weight:600;">Hi ${instName} — a ${capitalize(lead.city)} homeowner wants your help.</h1>
      </div>

      <div style="background:#faf7f2;padding:24px;border-radius:0 0 12px 12px;border:1px solid #d9d0c1;border-top:none;">
        <p style="font-size:15px;line-height:1.6;color:#1a3d42;margin:0 0 20px;">
          ${escapeHtml(lead.firstname)} used HomePowerRebate's free rebate assessment tool and chose <strong>${escapeHtml(installer.name || '')}</strong> as one of the installers they'd like a quote from. Here's what they're looking for:
        </p>
        <h2 style="margin:0 0 12px;font-size:18px;color:#08363f;">Customer details</h2>
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:6px 0;color:#1a3d42;width:140px;">Name</td><td style="padding:6px 0;font-weight:600;">${lead.firstname} ${lead.lastname}</td></tr>
          <tr><td style="padding:6px 0;color:#1a3d42;">Email</td><td style="padding:6px 0;font-weight:600;"><a href="mailto:${lead.email}">${lead.email}</a></td></tr>
          <tr><td style="padding:6px 0;color:#1a3d42;">Phone</td><td style="padding:6px 0;font-weight:600;"><a href="tel:${lead.phone}">${lead.phone}</a></td></tr>
          <tr><td style="padding:6px 0;color:#1a3d42;">Postal code</td><td style="padding:6px 0;font-weight:600;">${lead.postal}</td></tr>
          <tr><td style="padding:6px 0;color:#1a3d42;">City</td><td style="padding:6px 0;font-weight:600;">${capitalize(lead.city)}, BC</td></tr>
        </table>

        <h2 style="margin:24px 0 12px;font-size:18px;color:#08363f;">What they want</h2>
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:6px 0;color:#1a3d42;width:140px;">Upgrades selected</td><td style="padding:6px 0;font-weight:600;">${lead.upgrades || 'none specified'}</td></tr>
          <tr><td style="padding:6px 0;color:#1a3d42;">Power company</td><td style="padding:6px 0;font-weight:600;">${formatUtility(lead.utility)}</td></tr>
          <tr><td style="padding:6px 0;color:#1a3d42;">Current heating</td><td style="padding:6px 0;font-weight:600;">${lead.current_heat}</td></tr>
          <tr><td style="padding:6px 0;color:#1a3d42;">Current water heating</td><td style="padding:6px 0;font-weight:600;">${lead.water_heating}</td></tr>
          <tr><td style="padding:6px 0;color:#1a3d42;">Home built</td><td style="padding:6px 0;font-weight:600;">${lead.year_built}</td></tr>
          <tr><td style="padding:6px 0;color:#1a3d42;">Income tier</td><td style="padding:6px 0;font-weight:600;">${lead.income_tier}</td></tr>
        </table>

        ${lead.notes ? `<div style="background:#fef9e6;border-left:4px solid #d4751c;padding:14px 16px;border-radius:6px;margin-top:16px;"><strong style="color:#08363f;">In their own words:</strong><br>${escapeHtml(lead.notes)}</div>` : ''}

        <h2 style="margin:24px 0 12px;font-size:18px;color:#08363f;">Estimate shown to homeowner</h2>
        <div style="background:white;border:1px solid #d9d0c1;border-radius:10px;padding:16px;">
          <div style="font-size:14px;color:#1a3d42;">CleanBC rebates on selection:</div>
          <div style="font-size:28px;color:#2d6a4f;font-weight:600;margin:4px 0;">${lead.estimated_value}</div>
          <div style="font-size:14px;color:#1a3d42;">System cost: <strong>${lead.total_cost}</strong> &middot; After rebates: <strong>${lead.net_cost}</strong> &middot; 10-year savings: <strong>${lead.ten_year_savings}</strong></div>
        </div>

        <div style="background:#0a2a2e;color:#faf7f2;padding:20px;border-radius:10px;margin-top:24px;text-align:center;">
          <p style="margin:0 0 8px;font-size:14px;opacity:0.7;">Action required</p>
          <p style="margin:0;font-size:16px;font-weight:600;">Call this homeowner within 1 business day.</p>
          <a href="tel:${lead.phone}" style="display:inline-block;margin-top:14px;background:#d4751c;color:white;padding:12px 24px;border-radius:999px;text-decoration:none;font-weight:600;">Call ${lead.phone}</a>
          <p style="margin:14px 0 0;font-size:12px;opacity:.65;">Prefer email? Just hit reply — it goes straight to ${lead.email}, not to us.</p>
        </div>

        <p style="font-size:13px;color:#6b7d80;text-align:center;margin:22px 0 0;">
          Note: this homeowner may have also requested quotes from a couple of other local installers — that's by design, so they can compare.
        </p>

        <p style="margin:16px 0 0;font-size:12px;color:#1a3d42;">
          Submitted: ${new Date(lead.timestamp).toLocaleString('en-CA', { timeZone: 'America/Vancouver' })}
        </p>

        <div style="border-top:1px solid #d9d0c1;margin-top:24px;padding-top:18px;text-align:center;">
          <p style="margin:0;font-size:13px;color:#6b7d80;">
            Questions about this lead or the partnership? I'm easy to reach.<br>
            <strong style="color:#08363f;">Sam Menard</strong> &middot; HomePowerRebate.com<br>
            <a href="mailto:samuelmenard@gmail.com" style="color:#08363f;">samuelmenard@gmail.com</a>
          </p>
        </div>
      </div>
    </div>
  `;

  return resendEmail(env.RESEND_API_KEY, {
    from: 'HomePowerRebate Leads <leads@homepowerrebate.com>',
    to: installer.email,
    cc: installer.cc || undefined,
    bcc: env.OPS_EMAIL || undefined,
    reply_to: lead.email,
    subject,
    html
  });
}

// ===========================================================================
// EMAIL: send ops audit copy for lead (unchanged)
// ===========================================================================

async function sendOpsEmail(lead, env) {
  if (!env.OPS_EMAIL) return Promise.resolve();

  const unassignedWarning = lead.installer_email
    ? ''
    : `<p style="background:#fef3e6;border:1px solid #e8b87a;padding:10px 14px;border-radius:8px;"><strong>⚠️ No installer configured yet for ${lead.city} / ${lead.service}.</strong> This lead was NOT sent to an installer automatically — follow up manually.</p>`;

  return resendEmail(env.RESEND_API_KEY, {
    from: 'HomePowerRebate <ops@homepowerrebate.com>',
    to: env.OPS_EMAIL,
    subject: `[Lead] ${lead.city} (${lead.service}) - ${lead.firstname} ${lead.lastname} (${lead.estimated_value})`,
    html: `
      ${unassignedWarning}
      <p>New lead routed to <strong>${lead.installer_assigned}</strong>.</p>
      <ul>
        <li><strong>Lead ID:</strong> ${lead.lead_id}</li>
        <li><strong>City:</strong> ${lead.city}</li>
        <li><strong>Service:</strong> ${lead.service}</li>
        <li><strong>Name:</strong> ${lead.firstname} ${lead.lastname}</li>
        <li><strong>Email:</strong> ${lead.email}</li>
        <li><strong>Phone:</strong> ${lead.phone}</li>
        <li><strong>Postal:</strong> ${lead.postal}</li>
        <li><strong>Utility:</strong> ${lead.utility}</li>
        <li><strong>Upgrades wanted:</strong> ${lead.upgrades || 'none specified'}</li>
        <li><strong>Current heat:</strong> ${lead.current_heat}</li>
        <li><strong>Water heating:</strong> ${lead.water_heating}</li>
        <li><strong>Home built:</strong> ${lead.year_built}</li>
        <li><strong>Income tier:</strong> ${lead.income_tier}</li>
        <li><strong>Rebates estimate:</strong> ${lead.estimated_value} &middot; System cost: ${lead.total_cost} &middot; After rebates: ${lead.net_cost}</li>
        ${lead.notes ? `<li><strong>Notes from homeowner:</strong> ${escapeHtml(lead.notes)}</li>` : ''}
        <li><strong>Source:</strong> ${lead.page_url}</li>
      </ul>
    `
  });
}

// ===========================================================================
// EMAIL: confirmation to homeowner for waitlist signup (NEW)
// ===========================================================================
// Warm, brief, no other CTAs. Reaffirms the promise: we won't contact you
// until there's an actual approved installer for your area.

async function sendWaitlistConfirmation(waitlist, env) {
  const html = `
    <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:560px;margin:0 auto;padding:20px;color:#0a2a2e;">
      <div style="background:#08363f;color:#faf7f2;padding:28px 24px;border-radius:14px 14px 0 0;">
        <div style="font-family:Georgia,serif;font-size:14px;color:#e88a2e;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:10px;">You&rsquo;re on the list</div>
        <h1 style="margin:0;font-family:Georgia,serif;font-size:26px;font-weight:500;line-height:1.2;">We&rsquo;ll email you when we&rsquo;re live in your area.</h1>
      </div>

      <div style="background:#faf7f2;padding:28px 24px;border-radius:0 0 14px 14px;border:1px solid #d9d0c1;border-top:none;">
        <p style="font-size:16px;line-height:1.6;margin:0 0 16px;">
          Thanks for joining the HomePowerRebate waitlist. We&rsquo;ve got you down for <strong>${waitlist.city_name}</strong>${waitlist.postal ? ` (${waitlist.postal})` : ''}.
        </p>
        <p style="font-size:16px;line-height:1.6;margin:0 0 16px;">
          Here&rsquo;s our promise: <strong>we won&rsquo;t contact you again until we have an approved local installer ready to serve your area.</strong> No sales calls. No newsletters. No spam.
        </p>
        <p style="font-size:16px;line-height:1.6;margin:0 0 16px;">
          When we expand to your city, you&rsquo;ll get one email with the link to your local page, a short note about who your matched installer is, and that&rsquo;s it.
        </p>
        <p style="font-size:16px;line-height:1.6;margin:0 0 20px;">
          In the meantime, if you have questions, just hit reply &mdash; this email comes from a real inbox we read.
        </p>

        <div style="background:white;border:1px solid #d9d0c1;border-radius:10px;padding:16px;margin-top:20px;">
          <p style="margin:0;font-size:14px;color:#1a3d42;">
            <strong style="color:#08363f;">Already in one of our 11 cities?</strong><br>
            We currently serve Abbotsford, Chilliwack, Kamloops, Kelowna, Nanaimo, Prince George, Squamish, Surrey, Vancouver, Vernon, and Victoria. If your home is in one of those, you can skip the wait &mdash; <a href="https://homepowerrebate.com/ca/bc" style="color:#08363f;border-bottom:1px solid #d4751c;text-decoration:none;font-weight:600;">pick your city here</a>.
          </p>
        </div>

        <p style="margin:24px 0 0;font-size:12px;color:#6b7d80;text-align:center;">
          HomePowerRebate &middot; Independent installer matching service<br>
          Not affiliated with BC Hydro &middot; <a href="https://homepowerrebate.com" style="color:#6b7d80;">homepowerrebate.com</a>
        </p>
      </div>
    </div>
  `;

  return resendEmail(env.RESEND_API_KEY, {
    from: 'HomePowerRebate <hello@homepowerrebate.com>',
    to: waitlist.email,
    subject: `You're on the HomePowerRebate waitlist`,
    html
  });
}

// ===========================================================================
// EMAIL: confirmation to homeowner after lead submission (NEW)
// ===========================================================================
// Warm confirmation that we got their info and an installer will contact them soon.

async function sendLeadConfirmation(lead, installer, env) {
  if (!env.RESEND_API_KEY) return Promise.resolve();

  const installerLine = installer
    ? `<p style="font-size:16px;line-height:1.6;margin:0 0 16px;">We've matched you with <strong>${installer.name}</strong>, and they'll reach out within 1 business day at <strong>${lead.phone}</strong> or <strong>${lead.email}</strong>.</p>`
    : `<p style="font-size:16px;line-height:1.6;margin:0 0 16px;background:#fef3e6;padding:16px;border-radius:8px;border-left:4px solid #e8b87a;"><strong>Note:</strong> We're still building our installer network in ${lead.city}. Your information is safe with us, and we'll route you to a qualified installer as soon as we expand to your area.</p>`;

  const html = `
    <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:560px;margin:0 auto;padding:20px;color:#0a2a2e;">
      <div style="background:#08363f;color:#faf7f2;padding:28px 24px;border-radius:14px 14px 0 0;">
        <div style="font-family:Georgia,serif;font-size:14px;color:#e88a2e;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:10px;">We got it</div>
        <h1 style="margin:0;font-family:Georgia,serif;font-size:26px;font-weight:500;line-height:1.2;">Your retrofit assessment is submitted.</h1>
      </div>

      <div style="background:#faf7f2;padding:28px 24px;border-radius:0 0 14px 14px;border:1px solid #d9d0c1;border-top:none;">
        <p style="font-size:16px;line-height:1.6;margin:0 0 16px;">
          Thanks for taking the HomePowerRebate assessment. We've logged your information for <strong>${capitalize(lead.city)}</strong>.
        </p>

        ${installerLine}

        <h2 style="font-size:18px;color:#08363f;margin:24px 0 12px;"><strong>Your assessment summary</strong></h2>
        <div style="background:white;border:1px solid #d9d0c1;border-radius:10px;padding:16px;margin-bottom:16px;">
          <table style="width:100%;border-collapse:collapse;font-size:14px;">
            <tr><td style="padding:8px 0;color:#1a3d42;font-weight:600;width:45%;">CleanBC rebates on selection:</td><td style="padding:8px 0;color:#2d6a4f;font-weight:700;font-size:18px;">${lead.estimated_value}</td></tr>
            <tr><td style="padding:8px 0;color:#1a3d42;">System cost / after rebates:</td><td style="padding:8px 0;font-weight:600;">${lead.total_cost} / ${lead.net_cost}</td></tr>
            <tr><td style="padding:8px 0;color:#1a3d42;">Upgrades selected:</td><td style="padding:8px 0;font-weight:600;">${lead.upgrades || 'none specified'}</td></tr>
            <tr><td style="padding:8px 0;color:#1a3d42;">Current heating:</td><td style="padding:8px 0;font-weight:600;">${capitalize(String(lead.current_heat || 'unknown'))}</td></tr>
            <tr><td style="padding:8px 0;color:#1a3d42;">Utility:</td><td style="padding:8px 0;font-weight:600;">${formatUtility(lead.utility)}</td></tr>
          </table>
        </div>

        <div style="background:white;border-left:4px solid #2d6a4f;padding:16px;margin:24px 0;border-radius:6px;">
          <p style="margin:0;font-size:15px;color:#08363f;"><strong>What happens next:</strong></p>
          <ol style="margin:8px 0 0;padding-left:20px;font-size:15px;color:#1a3d42;">
            <li>Installer reviews your assessment (today)</li>
            <li>Calls or emails you with personalized quotes (within 1 business day)</li>
            <li>You compare and decide (no pressure — we don't get paid if you don't)</li>
          </ol>
        </div>

        <h2 style="font-size:16px;color:#08363f;margin:24px 0 12px;"><strong>Learn more before they call</strong></h2>
        <p style="font-size:15px;line-height:1.6;margin:0 0 12px;">
          <a href="https://homepowerrebate.com/blog/heat-pumps-explained-bc" style="display:inline-block;margin-bottom:8px;padding:10px 16px;background:#d4751c;color:#fff;border-radius:6px;text-decoration:none;font-weight:600;">Heat Pumps Explained →</a><br>
          <a href="https://homepowerrebate.com/blog/bc-approved-home-battery-rebate" style="display:inline-block;margin-bottom:8px;padding:10px 16px;background:#d4751c;color:#fff;border-radius:6px;text-decoration:none;font-weight:600;">Choosing a Battery →</a><br>
          <a href="https://homepowerrebate.com/blog" style="display:inline-block;margin-bottom:8px;padding:10px 16px;background:#d4751c;color:#fff;border-radius:6px;text-decoration:none;font-weight:600;">All Guides & Articles →</a>
        </p>

        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:16px;margin-top:20px;">
          <p style="margin:0 0 8px;font-size:14px;color:#166534;">
            <strong>Questions before they call?</strong> Just reply to this email. We read everything.
          </p>
          <p style="margin:0;font-size:14px;color:#166534;">
            <strong>Watch your email and phone</strong> for contact from <strong>${installer ? installer.name : 'your matched installer'}</strong>. Add leads@homepowerrebate.com to your contacts so we don't land in spam.
          </p>
        </div>

        <p style="margin:24px 0 0;font-size:12px;color:#6b7d80;text-align:center;">
          HomePowerRebate &middot; Independent installer matching service<br>
          Not affiliated with BC Hydro &middot; <a href="https://homepowerrebate.com" style="color:#6b7d80;">homepowerrebate.com</a>
        </p>
      </div>
    </div>
  `;

  return resendEmail(env.RESEND_API_KEY, {
    from: 'HomePowerRebate Leads <leads@homepowerrebate.com>',
    to: lead.email,
    subject: `Your HomePowerRebate assessment is submitted — ${capitalize(lead.city)} installer standing by`,
    html
  });
}

// ===========================================================================
// EMAIL: ops alert for waitlist signup (NEW)
// ===========================================================================
// Lighter than the lead alert. Lets you spot demand patterns by city.

async function sendOpsWaitlistAlert(waitlist, env) {
  if (!env.OPS_EMAIL) return Promise.resolve();

  return resendEmail(env.RESEND_API_KEY, {
    from: 'HomePowerRebate <ops@homepowerrebate.com>',
    to: env.OPS_EMAIL,
    subject: `[Waitlist] ${waitlist.city_name}${waitlist.postal ? ' / ' + waitlist.postal : ''}`,
    html: `
      <p>New waitlist signup.</p>
      <ul>
        <li><strong>Waitlist ID:</strong> ${waitlist.waitlist_id}</li>
        <li><strong>City entered:</strong> ${waitlist.city_name}</li>
        <li><strong>Postal:</strong> ${waitlist.postal || '(not provided)'}</li>
        <li><strong>Email:</strong> ${waitlist.email}</li>
        <li><strong>List:</strong> ${waitlist.list}</li>
        <li><strong>Source page:</strong> ${waitlist.page_url}</li>
        <li><strong>Referrer:</strong> ${waitlist.referrer}</li>
        <li><strong>Submitted:</strong> ${new Date(waitlist.timestamp).toLocaleString('en-CA', { timeZone: 'America/Vancouver' })}</li>
      </ul>
      <p style="font-size:12px;color:#666;">Watch for clusters by city &mdash; these are demand signals for partnership expansion.</p>
    `
  });
}

// ===========================================================================
// SHEET: log to Google Sheet via Apps Script webhook (unchanged signature)
// ===========================================================================
// Both leads and waitlist entries POST to the same webhook. The payload's
// `record_type` field tells the Apps Script which tab to write to.

async function logToSheet(record, env) {
  if (!env.GSHEET_WEBHOOK_URL) return Promise.resolve();

  return fetch(env.GSHEET_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(record)
  });
}

// ===========================================================================
// HELPERS (unchanged)
// ===========================================================================

async function resendEmail(apiKey, params) {
  if (!apiKey) throw new Error('RESEND_API_KEY not configured');

  const body = {
    from: params.from,
    to: params.to,
    subject: params.subject,
    html: params.html
  };
  if (params.cc) body.cc = params.cc;
  if (params.bcc) body.bcc = params.bcc;
  if (params.reply_to) body.reply_to = params.reply_to;

  const response = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`
    },
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Resend failed: ${response.status} ${text}`);
  }
  return response.json();
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS_HEADERS }
  });
}

function cleanString(s) {
  return String(s || '').trim().replace(/[\r\n\t]/g, ' ').slice(0, 500);
}

// Escape user-supplied values before putting them in notification email HTML.
function escapeHtml(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function formatUtility(u) {
  return ({
    bchydro: 'BC Hydro',
    fortisbc: 'FortisBC',
    newwest: 'New Westminster Electric',
    other: 'Unsure / Other'
  })[u] || u;
}

function formatHomeType(h) {
  return ({
    detached: 'Detached house',
    duplex: 'Duplex / townhouse / row home',
    strata: 'Condo / apartment',
    mobile: 'Mobile home'
  })[h] || h;
}

function formatBill(b) {
  return ({
    '100': 'Under $100',
    '150': '$100 to $200',
    '250': '$200 to $300',
    '400': 'Over $300'
  })[String(b)] || `$${b}`;
}
