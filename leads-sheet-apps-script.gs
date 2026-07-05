/**
 * HomePowerRebate — Google Sheet lead logger + notifier
 * =====================================================
 * Receives POSTs from the Cloudflare Worker (lead-router.js) and:
 *   1. Writes each record to the right tab (Leads / Subscribers / Waitlist),
 *      auto-creating tabs and columns as needed.
 *   2. Adds a `status` column (defaults to "new") so the sheet doubles as
 *      your CRM: new → contacted → matched → quoted → won / lost.
 *   3. EMAILS YOU on every new record so you can respond fast.
 *      This uses MailApp (your own Google account) — it does NOT depend on
 *      Resend or a verified domain, so it's the reliable notification path.
 *
 * ---- SETUP (5 min) -------------------------------------------------------
 * 1. Open your Google Sheet → Extensions → Apps Script.
 * 2. Delete whatever's there and paste ALL of this file.
 * 3. Set NOTIFY_EMAIL below to your inbox.
 * 4. Deploy → New deployment → type "Web app":
 *      - Execute as:  Me
 *      - Who has access:  Anyone
 *    Copy the Web app URL.
 * 5. Point the Worker at it:
 *      wrangler secret put GSHEET_WEBHOOK_URL   → paste the URL
 *    (If GSHEET_WEBHOOK_URL is already set to this script, just deploy a
 *     NEW VERSION of the same deployment so the URL stays the same.)
 * 6. wrangler deploy   (to publish the /newsletter + /estimate-lead routes)
 *
 * Test it: submit the estimate widget on the live site, then check the
 * sheet + your inbox.
 * -------------------------------------------------------------------------
 */

// ====== CONFIG — edit these ======
var NOTIFY_EMAIL = 'samuelmenard@gmail.com';   // where lead alerts go
var NOTIFY_ON = ['lead', 'subscriber', 'waitlist']; // record types that email you
// ==================================

var TAB_FOR = {
  lead: 'Leads',
  subscriber: 'Subscribers',
  waitlist: 'Waitlist'
};

function doPost(e) {
  try {
    var record = JSON.parse(e.postData.contents);
    var type = String(record.record_type || 'other');
    var tabName = TAB_FOR[type] || 'Other';

    // Ensure every record has a status for the CRM workflow.
    if (!record.status) record.status = 'new';
    // Server-side received time (in case the client clock is off).
    record.received_at = new Date().toISOString();

    writeRow(tabName, record);

    if (NOTIFY_ON.indexOf(type) !== -1) {
      sendNotification(type, record);
    }

    return json({ success: true });
  } catch (err) {
    // Log the error to the Executions view and still return 200 so the
    // Worker's Promise.allSettled doesn't treat it as a hard failure.
    console.error('doPost error: ' + err + ' | body: ' + (e && e.postData ? e.postData.contents : '(none)'));
    return json({ success: false, error: String(err) });
  }
}

/**
 * Append a record to a tab. Headers are built dynamically: any new field on
 * an incoming record becomes a new column, so /submit leads, /estimate-lead
 * referrals, subscribers and waitlist rows all coexist without hardcoding.
 * `status` and `received_at` are pinned as the first columns for scanning.
 */
function writeRow(tabName, record) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(tabName);
  if (!sheet) {
    sheet = ss.insertSheet(tabName);
    sheet.appendRow(['received_at', 'status']);
    sheet.setFrozenRows(1);
  }

  var headers = sheet.getRange(1, 1, 1, Math.max(1, sheet.getLastColumn())).getValues()[0];

  // Add any missing columns for keys we haven't seen before.
  var keys = Object.keys(record);
  for (var i = 0; i < keys.length; i++) {
    if (headers.indexOf(keys[i]) === -1) {
      headers.push(keys[i]);
      sheet.getRange(1, headers.length).setValue(keys[i]);
    }
  }

  // Build the row in header order.
  var row = [];
  for (var c = 0; c < headers.length; c++) {
    var key = headers[c];
    row.push(record[key] !== undefined ? record[key] : '');
  }
  sheet.appendRow(row);
}

/** Email you a readable alert for each new record. */
function sendNotification(type, record) {
  var subject, body;

  if (type === 'lead') {
    // A phone referral — actionable, respond fast.
    subject = '[LEAD ☎] ' + cap(record.city) + ' — ' + (record.firstname || '') +
              ' (' + (record.estimated_value || record.estimate || '?') + ')';
    body =
      'NEW REFERRAL (has phone — call them)\n\n' +
      'Name:      ' + (record.firstname || '') + ' ' + (record.lastname || '') + '\n' +
      'Phone:     ' + (record.phone || '') + '\n' +
      'Email:     ' + (record.email || '') + '\n' +
      'City:      ' + (record.city || '') + '\n' +
      'Heating:   ' + (record.current_heat || record.heating || '') + '\n' +
      'Income:    ' + (record.income_band || record.income || '') + '\n' +
      'Estimate:  ' + (record.estimated_value || record.estimate || '') + '\n' +
      'Assigned:  ' + (record.installer_assigned || '(none yet — you handle it)') + '\n' +
      'Source:    ' + (record.source || record.page_url || '') + '\n\n' +
      'Row logged to the "Leads" tab.';
  } else if (type === 'subscriber') {
    // Email-only — list building, not urgent, but you asked to see everything.
    subject = '[subscriber] ' + cap(record.city) + ' — ' + (record.email || '');
    body =
      'New newsletter subscriber (no phone yet — nurture).\n\n' +
      'Email:     ' + (record.email || '') + '\n' +
      'City:      ' + (record.city || '') + '\n' +
      'Heating:   ' + (record.heating || '') + '\n' +
      'Income:    ' + (record.income || '') + '\n' +
      'Estimate:  ' + (record.estimate || '') + '\n' +
      'Source:    ' + (record.source || '') + '\n';
  } else {
    // waitlist / other
    subject = '[' + type + '] ' + (record.city_name || record.city || '') + ' — ' + (record.email || '');
    body = 'New ' + type + ' entry:\n\n' + JSON.stringify(record, null, 2);
  }

  MailApp.sendEmail(NOTIFY_EMAIL, subject, body);
}

function cap(s) {
  s = String(s || '');
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : '(unknown)';
}

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/** Optional: run once from the editor to confirm email + tabs work. */
function testNotification() {
  var demo = {
    record_type: 'lead', city: 'kelowna', firstname: 'Test', lastname: 'Homeowner',
    phone: '250-555-0123', email: 'test@example.com', current_heat: 'furnace',
    income_band: 'tier1', estimated_value: '31500', installer_assigned: 'UNASSIGNED',
    source: 'city-kelowna', status: 'new'
  };
  writeRow('Leads', demo);
  sendNotification('lead', demo);
}
