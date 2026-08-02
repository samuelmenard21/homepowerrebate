# Pinterest Automation Setup Guide

**Goal:** Deploy hands-off Pinterest automation that posts 3-4 pins/day automatically  
**Timeline:** 30 minutes setup + testing  
**Result:** 500+ clicks/month from Pinterest → HomePowerRebate

---

## Phase 1: Pinterest Account Setup (10 minutes)

### 1. Create Pinterest Business Account

1. Go to [Pinterest.com](https://pinterest.com)
2. Click **"Sign up"** → Choose **"Create a business account"**
3. Email: `samuelmenard@gmail.com`
4. Business name: `HomePowerRebate`
5. Verify email and set password
6. Add your website: `https://homepowerrebate.com`

**Expected:** You now have a verified Pinterest Business account

### 2. Create 7 Pinterest Boards

From your Pinterest dashboard, create these boards (boards are where pins live):

**Primary Boards:**
- Board 1: `bc-heat-pump-rebates-2026` (Private initially, publish later)
- Board 2: `bc-solar-panel-rebates`
- Board 3: `bc-home-energy-rebates-2026` (Hub board)
- Board 4: `homeowner-tips-hacks`

**Secondary Boards:**
- Board 5: `bc-thermostat-rebates`
- Board 6: `battery-storage-peak-saver`
- Board 7: `best-hvac-brands`

**Board Settings:**
- Set each board to **Private** while testing (publish after first 10 successful pins)
- Add board descriptions (see `pinterest-strategy.md` for exact text)

**Expected:** 7 boards ready to receive pins

### 3. Copy Board IDs

You'll need board IDs for the worker config. For each board:

1. Open the board
2. URL looks like: `https://pinterest.com/homepowerrebate/bc-heat-pump-rebates-2026/`
3. The board ID is the slug: `bc-heat-pump-rebates-2026`

**Save these:**
```
PINTEREST_BOARD_ID_HEAT_PUMP = "bc-heat-pump-rebates-2026"
PINTEREST_BOARD_ID_SOLAR = "bc-solar-panel-rebates"
PINTEREST_BOARD_ID_HUB = "bc-home-energy-rebates-2026"
PINTEREST_BOARD_ID_TIPS = "homeowner-tips-hacks"
```

**Expected:** You have all 7 board IDs

---

## Phase 2: Pinterest API Credentials (10 minutes)

### 4. Generate API Access Token

1. Go to [Pinterest Developers](https://developers.pinterest.com)
2. Click **"Sign in with Pinterest"** (use your business account)
3. In the left menu: **Apps & Credentials**
4. Click **"Create an App"**
   - App name: `HomePowerRebate Worker`
   - App type: `Web`
5. Accept terms → **Create**
6. You'll see a **"Generate OAuth token"** section
7. Click **"Generate token"**
   - Scopes needed:
     - `pins:read`
     - `pins:write`
     - `boards:read`
   - Click **"Generate"**

**You'll get an access token** (looks like: `abc123def456xyz789...`)

⚠️ **SAVE THIS TOKEN IMMEDIATELY** — you can't see it again!

**Expected:** You have a Pinterest API access token

### 5. Test API Token

Before deploying the worker, verify your token works:

```bash
curl -X GET "https://api.pinterest.com/v5/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected response:**
```json
{
  "id": "123456789",
  "username": "homepowerrebate",
  "first_name": "Home",
  "last_name": "Power"
}
```

If you get an error, regenerate the token and ensure scopes are correct.

---

## Phase 3: Cloudflare Worker Deployment (10 minutes)

### 6. Deploy Worker to Cloudflare

You need to be logged into Cloudflare and have Pages/Workers enabled on your account.

1. Open terminal and navigate to the worker directory:
```bash
cd /Users/sammenard/Downloads/Powerrebate/pinterest-worker
```

2. Install dependencies:
```bash
npm install wrangler
```

3. Login to Cloudflare:
```bash
npx wrangler login
```
(Opens browser → authorize with your Cloudflare account)

4. Deploy the worker:
```bash
npx wrangler deploy
```

**Expected:** Terminal outputs a worker URL like `pinterest-automation.yoursubdomain.workers.dev`

### 7. Set Environment Variables

**Add your Pinterest API token to Cloudflare secrets:**

```bash
npx wrangler secret put PINTEREST_ACCESS_TOKEN
```
(Paste your access token when prompted, press Enter)

**Add configuration variables:**

```bash
npx wrangler secret put PINTEREST_BOARD_ID
```
(Enter: `bc-heat-pump-rebates-2026`)

**Verify secrets are set:**
```bash
npx wrangler secret list
```

**Expected:** Both secrets show in the list

### 8. Test Worker Manually

Trigger the worker once to verify it works:

```bash
curl -X POST https://pinterest-automation.yoursubdomain.workers.dev/test
```

**Expected response:**
```json
{
  "success": true,
  "pin_id": "98765432100",
  "type": "blog"
}
```

Check your Pinterest account — a new pin should appear on the board!

---

## Phase 4: Enable Scheduling (5 minutes)

### 9. Activate Scheduled Triggers

The worker is configured to run on a cron schedule (4 times daily). To enable it:

1. Go to Cloudflare Dashboard → **Workers & Pages** → **pinterest-automation**
2. Under **Triggers** → **Cron Triggers**
3. Verify the cron is set: `0 6,12,18,22 * * *`
4. Status should show **Enabled**

**What this does:**
- 6 AM PT: Posts 1 pin (blog or tips)
- 12 PM PT: Posts 1 pin (tips or city guide)
- 6 PM PT: Posts 1 pin (blog or city guide)
- 10 PM PT: Posts 1 pin (tips or city guide)
- **Total: 4 pins/day = 28 pins/week = ~100 pins/month**

**Expected:** Cron trigger is green/enabled

### 10. Monitor Worker Execution

Check that pins are posting automatically:

1. Cloudflare Dashboard → **Logs**
2. Watch for messages like: `[Pinterest] Pin posted successfully: 123456789`
3. Each log shows the pin type (blog/tips/city)

**Expected:** Logs appear every 6 hours with successful pin posts

---

## Phase 5: Analytics Setup (5 minutes)

### 11. Connect Pinterest Analytics

1. Go to your Pinterest Business Account → **Analytics** tab
2. Enable **Pinterest Analytics** (sync to your account)
3. Create a custom report for:
   - Impressions per board
   - Outbound clicks (traffic to your site)
   - Top-performing pins

### 12. Add UTM Tracking to GA4

All pins include UTM params: `?source=pinterest&medium=pin&campaign=[topic]`

In Google Analytics:

1. Go to **Admin** → **Reporting** → **Acquisition**
2. Create a custom report for `source=pinterest`
3. Segment by `medium=pin`
4. Track clicks/month, conversion rate

**Expected:** GA4 dashboard shows Pinterest traffic separately

---

## Phase 6: Manual Testing (5 minutes)

### 13. Test First 5 Pins Manually

Before letting the automation run wild, create 5 test pins manually:

1. Go to your Pinterest Business Account
2. Click **Create** → **Create pin**
3. Upload test image (1000×1500px)
4. Add title: `[TEST] BC Heat Pump Rebates 2026`
5. Add description: `Test pin from automation setup`
6. Link: `https://homepowerrebate.com/blog/bc-hydro-peak-saver-battery-rebate-5000-vs-1500.html?source=pinterest&medium=pin&campaign=peak-saver`
7. Select board: `bc-heat-pump-rebates-2026`
8. Click **Publish**

Repeat 4 more times with different pin types (blog, tips, city guides).

**Expected:** 5 test pins appear on your boards without errors

---

## Phase 7: Go Live (Ongoing)

### 14. Publish Boards

Once you've verified 5+ successful pins:

1. Go to each board → **Board settings**
2. Change from **Private** to **Public**
3. Repeat for all 7 boards

### 15. Monitor Weekly

**Every Monday:**
- Check Cloudflare logs for errors
- Review GA4 for traffic (UTM params)
- Check Pinterest Analytics for top-performing pins
- Adjust posting times if needed

**Every 2 weeks:**
- Review highest-CTR pin types
- Consider adding more city guides if performing well
- Check for any API errors or token expiration

### 16. Optimize Monthly

**First month:** Let automation run as-is (establish baseline)

**Month 2:** Based on analytics:
- If blog pins underperform: increase tips/city guides
- If certain topics perform better: adjust content rotation
- If certain times perform better: adjust cron schedule

---

## Troubleshooting

### "Pin posting failed: 401 Unauthorized"
- **Cause:** Access token expired or invalid
- **Fix:** Regenerate token, update secret: `npx wrangler secret put PINTEREST_ACCESS_TOKEN`

### "No pins appearing on board"
- **Cause:** Board ID incorrect or doesn't exist
- **Fix:** Verify board ID exactly matches board slug (case-sensitive)

### "Worker not running on schedule"
- **Cause:** Cron trigger disabled
- **Fix:** Go to Cloudflare Dashboard → Workers → Triggers → Enable cron

### "Pin image not loading"
- **Cause:** Image URL broken or inaccessible
- **Fix:** Verify image URLs are public (not behind auth)

### "Only 1-2 pins per day posting instead of 4"
- **Cause:** Worker timing out before 4 pins complete
- **Fix:** Adjust cron times to space out further (e.g., 6am, 11am, 4pm, 9pm)

---

## Success Metrics

**Week 1:** 
- ✅ 4 pins posted (all types working)
- ✅ No API errors in logs
- ✅ Each pin gets 5-20 impressions

**Week 2-4:**
- ✅ 28 pins posted (7 per week)
- ✅ 50-100 clicks to site (from GA4)
- ✅ Boards have 28+ pins, engagement growing

**Month 2:**
- ✅ 100+ pins total
- ✅ 200-300 clicks/month to site
- ✅ ~1-3 installer leads from Pinterest traffic

**Month 3+:**
- ✅ 500+ clicks/month (target)
- ✅ Consistent 30-40+ clicks per week
- ✅ 5-10 installer leads/month from Pinterest

---

## Next Steps

1. ✅ Complete Phase 1-7 above
2. 📊 Monitor analytics for 2 weeks
3. 🔄 Optimize based on top-performing pins
4. 📈 Expand to new topics/boards based on data
5. 🎯 Scale from 500 clicks/month to 1K+ by Q4 2026

---

## Quick Reference: Board IDs

```
bc-heat-pump-rebates-2026
bc-solar-panel-rebates
bc-home-energy-rebates-2026
homeowner-tips-hacks
bc-thermostat-rebates
battery-storage-peak-saver
best-hvac-brands
```

## Quick Reference: Worker Commands

```bash
# Deploy worker
npx wrangler deploy

# Set secrets
npx wrangler secret put PINTEREST_ACCESS_TOKEN
npx wrangler secret put PINTEREST_BOARD_ID

# View logs
npx wrangler logs

# Trigger manually
curl -X POST https://pinterest-automation.yoursubdomain.workers.dev/test

# List scheduled triggers
npx wrangler triggers list
```

---

**Questions?** Refer to:
- Pinterest API docs: https://developers.pinterest.com/docs/api/overview/
- Cloudflare Workers docs: https://developers.cloudflare.com/workers/
- Strategy details: See `pinterest-strategy.md`
