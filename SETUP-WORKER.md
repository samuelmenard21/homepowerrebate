# Worker & Lead Capture Setup

This guide walks you through deploying the lead-router Worker and setting up automatic lead logging.

## Phase 1: Google Sheet + Apps Script Webhook

### 1a. Create the sheet structure
Your Google Sheet should have tabs named:
- **Leads** — full leads from city pages
- **Waitlist** — out-of-area signups
- **Errors** (auto-created by the script)

### 1b. Add the Apps Script webhook
1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1MQAx_i-e4DqEf1E9eXCWjE-nFWD08YR9P2OHfTKi-8M/edit
2. Click **Tools** → **Script Editor** (opens a new tab with Apps Script)
3. Delete the default `function myFunction() {}` code
4. Paste the entire contents of `apps-script-template.gs` (from this repo)
5. Click **Save** (top left)
6. Click **Run** to execute the script once (it will prompt for permissions)
7. Once it completes, click **Deploy** → **New deployment** → Choose type: **Web app**
   - Execute as: (your Google account)
   - Who has access: **Anyone**
8. Click **Deploy**
9. **Copy the deployment URL** — it looks like:
   ```
   https://script.google.com/macros/d/[VERY_LONG_ID]/userweb
   ```
   Save this — you'll need it in the next step.

## Phase 2: Resend Account (Email)

### 2a. Sign up for Resend
1. Go to https://resend.com and sign up (free tier: 100 emails/day)
2. Verify your email
3. Go to **API Tokens** in the dashboard
4. Click **Create Token** → name it `homepowerrebate-prod`
5. **Copy the token** (looks like `re_abc123xyz...`)
   Save this — you'll need it for the Worker secrets.

## Phase 3: Cloudflare Worker Deployment

### 3a. Install Wrangler (CLI tool)
Open your terminal and run:
```bash
npm install -g wrangler
```

If you already have it, update:
```bash
npm install -g wrangler@latest
```

### 3b. Authenticate with Cloudflare
```bash
wrangler login
```
This opens your browser to authorize the CLI with your Cloudflare account.

### 3c. Deploy the Worker
Navigate to your homepowerrebate directory and run:
```bash
cd /Users/sammenard/Downloads/Powerrebate
wrangler deploy
```

The Worker deploys to `leads.homepowerrebate.com`.

### 3d. Set the secrets
Secrets are environment variables that the Worker needs. Set them one at a time:

**Resend API key:**
```bash
wrangler secret put RESEND_API_KEY
# When prompted, paste the token you copied from Resend
```

**Google Sheet webhook URL:**
```bash
wrangler secret put GSHEET_WEBHOOK_URL
# When prompted, paste the Apps Script deployment URL from step 1b
```

**Operations email (for lead alerts):**
```bash
wrangler secret put OPS_EMAIL
# When prompted, type: hello@homepowerrebate.com
# (or your own email for testing)
```

## Phase 4: Test the setup

### 4a. Test the `/waitlist` endpoint (simplest)
```bash
curl -X POST https://leads.homepowerrebate.com/waitlist \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "city_name": "Test City",
    "postal": "V1V1V1",
    "list": "general"
  }'
```

Expected response:
```json
{
  "success": true,
  "waitlist_id": "[uuid]"
}
```

### 4b. Check your email
You should receive a confirmation email from Resend within ~5 seconds. If you don't:
- Check spam folder
- Check the Worker logs: `wrangler tail`

### 4c. Check your Google Sheet
In the **Waitlist** tab, you should see a new row with the test signup.

### 4d. Test the `/submit` endpoint (full lead)
```bash
curl -X POST https://leads.homepowerrebate.com/submit \
  -H "Content-Type: application/json" \
  -d '{
    "firstname": "Test",
    "lastname": "User",
    "email": "test@example.com",
    "phone": "(250) 555-0123",
    "postal": "V1V1V1",
    "city": "kelowna",
    "service": "solar-battery",
    "calc_result": {
      "utility": "bchydro",
      "home_type": "detached",
      "has_solar": "no",
      "monthly_bill": "150",
      "estimated_value": "$20,000",
      "payback": "7-11 yr"
    },
    "page_url": "https://homepowerrebate.com/ca/bc/kelowna"
  }'
```

Expected: success, lead logged to **Leads** sheet, installer email sent.

## Troubleshooting

**"GSHEET_WEBHOOK_URL not configured"**
→ You missed setting the secret. Run: `wrangler secret put GSHEET_WEBHOOK_URL`

**"Resend failed: 401"**
→ Your RESEND_API_KEY is wrong or expired. Check it in the Resend dashboard and re-set it.

**No email arrives**
→ Check Resend dashboard for bounce/block reasons. Make sure you're not in the free tier cap (100/day).

**Webhook 404 from Apps Script**
→ Your GSHEET_WEBHOOK_URL is malformed or the script isn't deployed. Check the Apps Script deployment URL (step 1b).

**"Method not allowed 405"**
→ You're using GET instead of POST. Make sure your request is `POST`.

## Monitoring

View live Worker logs:
```bash
wrangler tail
```

This streams all requests + errors in real-time. Useful for debugging form submissions.

## Next steps

Once this is working:
1. Submit your sitemap in Google Search Console
2. Start driving traffic (blog, social, webinars)
3. Monitor leads in your Google Sheet
4. Reach out to installers with proof-of-concept data
