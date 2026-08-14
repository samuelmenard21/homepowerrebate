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
};

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
    logToSheet(lead, env)
  ];
  if (hasInstaller) {
    tasks.unshift(sendInstallerEmail(lead, installer, env));
  }

  const results = await Promise.allSettled(tasks);
  const taskNames = hasInstaller ? ['installer', 'ops', 'sheet'] : ['ops', 'sheet'];

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
  await Promise.allSettled(tasks);

  return jsonResponse({ success: true }, 200);
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
    service,
    installer_assigned: installer ? installer.name : 'UNASSIGNED — needs manual follow-up',
    installer_email: isReal ? installer.email : '',
    firstname: cleanString(p.firstname),
    lastname: cleanString(p.lastname || ''),
    email: cleanString(p.email),
    phone: cleanString(p.phone),
    postal: cleanString(p.postal || ''),
    current_heat: cleanString(p.heating || 'unknown'),
    income_band: cleanString(p.income || 'unknown'),
    estimated_value: cleanString(String(p.estimate || 'unknown')),
    page_url: cleanString(p.source || p.page || ''),
    referrer: cleanString(p.referrer || 'estimate-widget'),
    status: 'new'
  };

  const tasks = [
    sendOpsEstimateLead(lead, env),
    logToSheet(lead, env)
  ];
  // Only add to the newsletter audience if they didn't opt out (CASL).
  if (p.newsletter !== false) tasks.push(addToResendAudience(lead.email, env));
  if (isReal) tasks.unshift(sendEstimateInstallerEmail(lead, installer, env));

  await Promise.allSettled(tasks);

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
    await env.OUTCOMES_DB.prepare(
      `INSERT INTO outcomes
        (id, created_at, category, postal_fsa, city, province, install_month,
         total_cost, rebates_received, net_cost, monthly_bill_before, monthly_bill_after,
         installer_name, verified, email, status)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'new')`
    ).bind(
      id, createdAt, category, postalFsa, city, province, String(p.install_month),
      totalCost, rebatesReceived, netCost,
      Number.isFinite(billBefore) ? billBefore : null,
      Number.isFinite(billAfter) ? billAfter : null,
      cleanString(p.installer_name || ''),
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
        ev = escapeHtml(lead.estimated_value), src = escapeHtml(lead.page_url);
  return resendEmail(env.RESEND_API_KEY, {
    from: 'HomePowerRebate Leads <leads@homepowerrebate.com>',
    to: installer.email,
    cc: installer.cc || undefined,
    reply_to: lead.email,
    subject: `New heat pump lead: ${lead.firstname} in ${capitalize(lead.city)}`,
    html: `
      <div style="font-family:-apple-system,sans-serif;max-width:560px;margin:0 auto;padding:20px;color:#0a2a2e;">
        <h2 style="color:#08363f;">New HomePowerRebate referral</h2>
        <p>A homeowner asked to be matched after seeing their rebate estimate.</p>
        <ul>
          <li><strong>Name:</strong> ${fn} ${ln}</li>
          <li><strong>Phone:</strong> <a href="tel:${ph}">${ph}</a></li>
          <li><strong>Email:</strong> <a href="mailto:${em}">${em}</a></li>
          <li><strong>City:</strong> ${ct}, BC</li>
          <li><strong>Current heating:</strong> ${ch}</li>
          <li><strong>Estimate shown:</strong> up to ${ev}</li>
        </ul>
        <p style="background:#0a2a2e;color:#faf7f2;padding:16px;border-radius:10px;text-align:center;">
          Call this homeowner within 1 business day.<br>
          <a href="tel:${ph}" style="display:inline-block;margin-top:10px;background:#d4751c;color:#fff;padding:10px 22px;border-radius:999px;text-decoration:none;font-weight:600;">Call ${ph}</a>
        </p>
        <p style="font-size:12px;color:#1a3d42;">Source: ${src} · ${new Date(lead.timestamp).toLocaleString('en-CA', { timeZone: 'America/Vancouver' })}</p>
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
        <li><strong>Estimate:</strong> ${ev}</li>
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
  const subject = `New lead: ${lead.firstname} ${lead.lastname} in ${capitalize(lead.city)}`;

  const html = `
    <div style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:600px;margin:0 auto;padding:20px;color:#0a2a2e;">
      <div style="background:#d4751c;color:white;padding:20px;border-radius:12px 12px 0 0;">
        <h1 style="margin:0;font-size:22px;">New HomePowerRebate Lead</h1>
        <p style="margin:6px 0 0;opacity:0.9;font-size:14px;">Lead ID: ${lead.lead_id}</p>
      </div>

      <div style="background:#faf7f2;padding:24px;border-radius:0 0 12px 12px;border:1px solid #d9d0c1;border-top:none;">
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
        </div>

        <p style="margin:24px 0 0;font-size:12px;color:#1a3d42;">
          Source page: ${lead.page_url}<br>
          Referrer: ${lead.referrer}<br>
          Submitted: ${new Date(lead.timestamp).toLocaleString('en-CA', { timeZone: 'America/Vancouver' })}
        </p>
      </div>
    </div>
  `;

  return resendEmail(env.RESEND_API_KEY, {
    from: 'HomePowerRebate Leads <leads@homepowerrebate.com>',
    to: installer.email,
    cc: installer.cc || undefined,
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
