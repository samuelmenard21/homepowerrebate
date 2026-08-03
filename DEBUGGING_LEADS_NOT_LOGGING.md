# Debugging: Leads Not Appearing in Google Sheet

## Problem
Forms submit successfully (homeowners see "✓ Sent" and installer modal), but lead data doesn't appear in the Google Sheet.

## Root Causes to Check

### 1. Missing or Incorrect Environment Variable (MOST LIKELY)
The Worker tries to POST to `env.GSHEET_WEBHOOK_URL`, but if this isn't set or is wrong, logging silently fails.

**Check this first:**
```bash
# SSH into Cloudflare or use the Wrangler CLI to check secrets
wrangler secret list

# You should see:
# GSHEET_WEBHOOK_URL ••••••••••••••••••
# RESEND_API_KEY     ••••••••••••••••••
# OPS_EMAIL          ••••••••••••••••••
```

If `GSHEET_WEBHOOK_URL` is missing or shows wrong value:
```bash
# Set the correct URL (from Google Apps Script)
wrangler secret put GSHEET_WEBHOOK_URL
# Then paste the webhook URL when prompted
```

### 2. Google Apps Script Webhook Not Working
The webhook might be set but returning an error.

**Test it manually:**
```bash
# Use curl to POST test data to the webhook
curl -X POST https://YOUR_GSHEET_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{
    "record_type": "lead",
    "lead_id": "test-123",
    "timestamp": "'$(date -Iseconds)'",
    "email": "test@example.com",
    "firstname": "Test",
    "city": "vancouver"
  }'

# Response should be 200 OK, not an error
```

### 3. Google Sheet Permissions
The Apps Script may not have write access to the Google Sheet.

**Check this in Google Apps Script:**
1. Go to the Apps Script editor
2. Look at the Google Sheet ID being written to (in leads-sheet-apps-script.gs)
3. Make sure the Sheet is accessible to the service account or user running the script

### 4. Wrong Google Apps Script Deployment
The webhook URL might point to an old or undeployed version.

**Verify the URL format:**
- Should look like: `https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/usercontent`
- Make sure `YOUR_DEPLOYMENT_ID` is the active (latest) deployment

---

## How to Get the Correct Webhook URL

1. Open Google Apps Script editor (the `leads-sheet-apps-script.gs` file)
2. Click **Deploy** → **New deployment**
3. Select type: **Web app**
4. Set:
   - Execute as: (your Google account)
   - Who has access: **Anyone**
5. Click **Deploy**
6. Copy the URL shown in the dialog (looks like: `https://script.google.com/macros/s/ABC123XYZ/usercontent`)
7. Set it as a secret:
   ```bash
   wrangler secret put GSHEET_WEBHOOK_URL
   # Paste the URL when prompted
   ```

---

## Testing the Full Flow

1. **Submit a test lead** from a city page form
2. **Check console** (your browser DevTools) for any POST errors
3. **Check Cloudflare Worker logs:**
   ```bash
   wrangler tail
   # Watch for any errors in the logToSheet call
   ```
4. **Check Google Sheet immediately** (within 5 seconds of form submit)
5. **Check ops email inbox** (OPS_EMAIL should get a copy)

---

## Expected Behavior (When Working)

1. Homeowner submits form
2. Worker receives POST at `/estimate-lead`
3. Worker sends email to selected installer (via Resend)
4. Worker sends audit copy to OPS_EMAIL (via Resend)
5. Worker POSTs to Google Apps Script webhook
6. Apps Script writes record to Google Sheet (Leads tab)
7. Homeowner sees "✓ Perfect! You're matched with [Installer]"

If any step fails, check the logs and env vars above.

---

## Quick Checklist

- [ ] `GSHEET_WEBHOOK_URL` is set in Cloudflare (check with `wrangler secret list`)
- [ ] Webhook URL is a valid Google Apps Script endpoint
- [ ] Webhook URL works when tested with curl
- [ ] Google Sheet is accessible and has write permissions
- [ ] OPS_EMAIL emails are being received (proves some posting works)
- [ ] Google Apps Script is deployed (latest version)

---

## If Still Broken

1. Test the webhook directly with curl (see above)
2. Check Google Apps Script execution logs:
   - Go to Apps Script editor
   - Click **Executions** to see any runtime errors
3. Add console.log to the Apps Script to debug what it's receiving
4. Check Cloudflare Worker logs for POST failures
