/**
 * HomePowerRebate Lead Logger
 *
 * Paste this into Google Apps Script (Apps Script editor in your Sheet).
 * It creates a webhook that accepts POST requests from the lead-router Worker
 * and logs leads + waitlist signups to separate sheets.
 *
 * Setup:
 * 1. Open your Google Sheet
 * 2. Tools → Script Editor
 * 3. Paste this entire script
 * 4. Run → Deploy → New deployment → type: Web app → Execute as: [your account]
 *    → Who has access: Anyone
 * 5. Copy the deployment URL (it looks like: https://script.google.com/macros/d/[ID]/userweb)
 * 6. Set GSHEET_WEBHOOK_URL to that URL in the Cloudflare Worker secrets
 */

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const recordType = payload.record_type; // "lead" or "waitlist"

    // Get or create the appropriate sheet
    const sheet = SpreadsheetApp.getActiveSpreadsheet();
    let targetSheet;

    if (recordType === 'lead') {
      targetSheet = getOrCreateSheet(sheet, 'Leads');
      appendLeadRow(targetSheet, payload);
    } else if (recordType === 'waitlist') {
      targetSheet = getOrCreateSheet(sheet, 'Waitlist');
      appendWaitlistRow(targetSheet, payload);
    } else {
      return ContentService
        .createTextOutput(JSON.stringify({ error: 'Unknown record_type' }))
        .setMimeType(ContentService.MimeType.JSON);
    }

    return ContentService
      .createTextOutput(JSON.stringify({ success: true, record_type: recordType }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    // Log errors to a separate sheet for debugging
    const sheet = SpreadsheetApp.getActiveSpreadsheet();
    const errorSheet = getOrCreateSheet(sheet, 'Errors');
    errorSheet.appendRow([
      new Date().toISOString(),
      error.toString(),
      e.postData.contents.slice(0, 500)
    ]);

    return ContentService
      .createTextOutput(JSON.stringify({ error: error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function getOrCreateSheet(spreadsheet, sheetName) {
  let sheet = spreadsheet.getSheetByName(sheetName);
  if (!sheet) {
    sheet = spreadsheet.insertSheet(sheetName);

    // Add headers
    if (sheetName === 'Leads') {
      sheet.appendRow([
        'Timestamp', 'Lead ID', 'City', 'Service', 'First Name', 'Last Name',
        'Email', 'Phone', 'Postal', 'Installer', 'Utility', 'Home Type',
        'Has Solar', 'Monthly Bill', 'Estimated Value', 'Payback', 'Status'
      ]);
    } else if (sheetName === 'Waitlist') {
      sheet.appendRow([
        'Timestamp', 'Waitlist ID', 'City Name', 'Postal', 'Email', 'List', 'Status'
      ]);
    } else if (sheetName === 'Errors') {
      sheet.appendRow([
        'Timestamp', 'Error', 'Raw Payload (first 500 chars)'
      ]);
    }
  }
  return sheet;
}

function appendLeadRow(sheet, lead) {
  sheet.appendRow([
    lead.timestamp,
    lead.lead_id,
    lead.city,
    lead.service,
    lead.firstname,
    lead.lastname,
    lead.email,
    lead.phone,
    lead.postal,
    lead.installer_assigned,
    lead.utility,
    lead.home_type,
    lead.has_solar,
    lead.monthly_bill,
    lead.estimated_value,
    lead.payback,
    lead.status
  ]);
}

function appendWaitlistRow(sheet, waitlist) {
  sheet.appendRow([
    waitlist.timestamp,
    waitlist.waitlist_id,
    waitlist.city_name,
    waitlist.postal,
    waitlist.email,
    waitlist.list,
    waitlist.status
  ]);
}
