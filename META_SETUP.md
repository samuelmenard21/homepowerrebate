# Meta (Instagram & Facebook) Automation Setup Guide

**Goal:** Deploy hands-off Meta automation that posts 3-4 items per day automatically  
**Timeline:** 40 minutes setup + testing  
**Result:** 300+ clicks/month from Meta → HomePowerRebate

---

## Phase 1: Meta Business Account Setup (15 minutes)

### 1. Create Meta Business Account

1. Go to [Facebook.com](https://facebook.com)
2. Log in or create an account
3. Go to [business.facebook.com](https://business.facebook.com)
4. Click **"Create Account"** (if you don't have one)
5. Enter business name: `HomePowerRebate`
6. Enter your email: `samuelmenard@gmail.com`
7. Complete setup

**Expected:** You have a Meta Business Account

### 2. Connect Your Instagram Account

1. In Meta Business Suite, go to **Settings** → **Instagram Accounts**
2. Click **Add Instagram Account**
3. Choose **Use Existing Account** (if you already have an Instagram profile for the site)
4. Or create a new one: **HomePowerRebate** or similar
5. Link it to your business account

**Make sure it's a Business Account** (not Personal):
- Go to your Instagram profile
- Settings → Account Type and Tools → Switch to Professional Account
- Choose "Business" as the type

**Expected:** Instagram Business Account linked to Meta Business

### 3. Connect Your Facebook Page

1. In Meta Business Suite, go to **Settings** → **Facebook Pages**
2. Click **Add Page**
3. Choose **Use Existing Page** or create a new one: `HomePowerRebate`
4. Link it to your business account

**Expected:** Facebook Page linked and ready

---

## Phase 2: Get Your Account IDs (5 minutes)

### 4. Find Instagram Business Account ID

1. Go to Meta Business Suite → **Settings** → **Instagram Accounts**
2. Select your Instagram account
3. You'll see the **Account ID** (looks like: `123456789`)
4. Copy this ID and save it

**Save as:** `INSTAGRAM_BUSINESS_ACCOUNT_ID = "123456789"`

### 5. Find Facebook Page ID (Optional but Recommended)

1. Go to Meta Business Suite → **Settings** → **Facebook Pages**
2. Select your Facebook page
3. You'll see the **Page ID** (looks like: `987654321`)
4. Copy this ID and save it

**Save as:** `FACEBOOK_PAGE_ID = "987654321"`

**Expected:** You have both account IDs saved

---

## Phase 3: Generate Meta API Credentials (15 minutes)

### 6. Create a Meta App

1. Go to [Facebook Developers](https://developers.facebook.com)
2. Click **My Apps** → **Create App**
3. Choose app type: **Business** (not Consumer)
4. App name: `HomePowerRebate Worker`
5. App purpose: `Automate social media posting`
6. Create app

### 7. Add Instagram and Facebook Permissions

1. In your app dashboard, go to **Products**
2. Click **+ Add Product**
3. Search for and add:
   - **Instagram Graph API**
   - **Facebook Graph API**

### 8. Generate Access Token

1. Go to **Tools** → **Graph API Explorer**
2. In the top dropdown, select your app name
3. Make sure it says "Get User Access Token" or "Get Page Access Token"
4. Click **Generate Access Token**
5. Select these permissions:
   - ✅ `instagram_business_content_publish`
   - ✅ `instagram_business_manage_messages`
   - ✅ `pages_manage_posts` (for Facebook)
   - ✅ `pages_read_engagement`
6. Click **Generate**

**You'll get a long token** — Copy it immediately (you can only see it once!)

**Save as:** `META_ACCESS_TOKEN = "your_token_here"`

### 9. Test Your Credentials

Test Instagram:
```bash
curl -X GET "https://graph.instagram.com/v18.0/me?fields=username,name" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected response:**
```json
{
  "username": "homepowerrebate",
  "name": "HomePowerRebate",
  "id": "123456789"
}
```

---

## Phase 4: Deploy Meta Worker (10 minutes)

### 10. Deploy to Cloudflare

Navigate to the worker directory:
```bash
cd /Users/sammenard/Downloads/Powerrebate/meta-worker
```

Install dependencies:
```bash
npm install
```

Login to Cloudflare:
```bash
npx wrangler login
```

Deploy:
```bash
npx wrangler deploy
```

**Expected:** Terminal outputs a worker URL like `meta-automation.yoursubdomain.workers.dev`

### 11. Set Environment Secrets

**Add your Meta API token:**
```bash
npx wrangler secret put META_ACCESS_TOKEN
```
Paste your token from Step 8

**Add your Instagram Business Account ID:**
```bash
npx wrangler secret put INSTAGRAM_BUSINESS_ACCOUNT_ID
```
Paste your account ID (e.g., `123456789`)

**Add your Facebook Page ID (optional):**
```bash
npx wrangler secret put FACEBOOK_PAGE_ID
```
Paste your page ID (e.g., `987654321`)

**Verify secrets are set:**
```bash
npx wrangler secret list
```

**Expected:** All three secrets show in the list

### 12. Test Worker Manually

Trigger the worker once:
```bash
curl -X POST https://meta-automation.yoursubdomain.workers.dev/test
```

**Expected response:**
```json
{
  "success": true,
  "post_id": "98765432100",
  "type": "blog",
  "platforms": ["instagram", "facebook"]
}
```

**Check your Instagram and Facebook** — A new post should appear!

---

## Phase 5: Enable Scheduling (5 minutes)

### 13. Activate Scheduled Triggers

The worker is configured to run automatically 4 times daily. To verify:

1. Go to Cloudflare Dashboard → **Workers & Pages** → **meta-automation**
2. Under **Triggers** → **Cron Triggers**
3. Verify the cron is set: `0 6,12,18,22 * * *`
4. Status should show **Enabled**

**What this does:**
- 6 AM PT: Posts to Instagram + Facebook
- 12 PM PT: Posts to Instagram + Facebook
- 6 PM PT: Posts to Instagram + Facebook
- 10 PM PT: Posts to Instagram + Facebook
- **Total: 4 posts/day = 28 posts/week**

### 14. Monitor Worker Execution

Check that posts are posting automatically:

1. Cloudflare Dashboard → **Logs**
2. Watch for messages like: `[Meta] Post created successfully: 123456789`

**Expected:** Logs appear every 6 hours with successful posts

---

## Phase 6: Analytics Setup (5 minutes)

### 15. Connect Instagram Analytics

1. Go to your Instagram Business Account
2. Go to **Insights** tab
3. Enable **Instagram Insights** (syncs with Meta Business Suite)

### 16. Connect Facebook Analytics

1. Go to your Facebook Page
2. Go to **Insights** tab
3. Track **Post Performance** → Clicks, Reach, Engagement

### 17. Add UTM Tracking to GA4

All posts include UTM params: `?source=meta&medium=instagram&campaign=[type]` or `?source=meta&medium=facebook&campaign=[type]`

In Google Analytics:

1. Go to **Admin** → **Reporting** → **Acquisition**
2. Create a custom report for `source=meta`
3. Segment by `medium=instagram` or `medium=facebook`
4. Track clicks/month, conversion rate

**Expected:** GA4 dashboard shows Meta traffic separately from Pinterest

---

## Phase 7: Manual Testing (5 minutes)

### 18. Test First 3 Posts Manually

Before letting automation run, create 3 test posts manually:

1. Go to your Instagram Business Account
2. Create a post:
   - Upload a test image (1080×1350px for feed posts)
   - Write a caption: `[TEST] BC Heat Pump Rebates`
   - Add link to bio or use "Link Stickers"
   - Post

Repeat 2 more times with different post types (tips, city guide).

**Expected:** 3 test posts appear on Instagram without errors

---

## Phase 8: Go Live (Ongoing)

### 19. Monitor Weekly

**Every Monday:**
- Check Cloudflare logs for errors
- Review GA4 for traffic (UTM params)
- Check Instagram/Facebook Insights for performance
- Adjust posting times if needed

### 20. Optimize Monthly

**First month:** Let automation run as-is (establish baseline)

**Month 2:** Based on analytics:
- If certain post types outperform: increase that %
- If Instagram outperforms Facebook: focus on Instagram
- If certain times perform better: adjust cron schedule
- Consider adding new blog posts or city guides

---

## Success Metrics

**Week 1:**
- ✅ 4 posts posted (all types working)
- ✅ No API errors in logs
- ✅ Each post gets 10-30 likes/comments

**Week 2-4:**
- ✅ 28 posts posted (7 per week)
- ✅ 100-200 clicks to site (from GA4)
- ✅ Growing engagement on each post

**Month 2:**
- ✅ 100+ posts total
- ✅ 200-300 clicks/month to site
- ✅ ~5-10 installer leads from Meta traffic

**Month 3+:**
- ✅ 300+ clicks/month (target)
- ✅ Consistent 50-75 clicks per week
- ✅ 8-15 installer leads/month from Meta

---

## Troubleshooting

### "Post failed: 401 Unauthorized"
- **Cause:** Access token expired or invalid
- **Fix:** Regenerate token, update secret: `npx wrangler secret put META_ACCESS_TOKEN`

### "No posts appearing on Instagram"
- **Cause:** Account ID incorrect or permissions missing
- **Fix:** Verify Instagram Business Account ID exactly matches (case-sensitive)

### "Worker not running on schedule"
- **Cause:** Cron trigger disabled
- **Fix:** Go to Cloudflare Dashboard → Workers → Triggers → Enable cron

### "Only Instagram posts, Facebook failing"
- **Cause:** Facebook Page ID missing or permissions issue
- **Fix:** Facebook posting is optional; if you want it, verify Page ID: `npx wrangler secret put FACEBOOK_PAGE_ID`

### "Post image not loading"
- **Cause:** Image URL broken or inaccessible
- **Fix:** Verify image URLs are public and exist on your server

---

## Quick Reference

**Worker Commands**
```bash
# Deploy worker
npx wrangler deploy

# Set secrets
npx wrangler secret put META_ACCESS_TOKEN
npx wrangler secret put INSTAGRAM_BUSINESS_ACCOUNT_ID
npx wrangler secret put FACEBOOK_PAGE_ID

# View logs
npx wrangler logs

# Test manually
curl -X POST https://meta-automation.yoursubdomain.workers.dev/test

# List secrets
npx wrangler secret list
```

**Account IDs to Save**
```
INSTAGRAM_BUSINESS_ACCOUNT_ID = your_ig_id
FACEBOOK_PAGE_ID = your_fb_page_id
META_ACCESS_TOKEN = your_token
```

---

## Next Steps

1. ✅ Complete Phase 1-8 above
2. 📊 Monitor analytics for 2 weeks
3. 🔄 Optimize based on top-performing posts
4. 📈 Expand with new content as needed
5. 🎯 Scale from 300 clicks/month to 500+ by Q4 2026

---

**Questions?** Refer to:
- Meta API docs: https://developers.facebook.com/docs/instagram-api
- Cloudflare Workers docs: https://developers.cloudflare.com/workers/
- Pinterest Worker (reference): See `../pinterest-worker/README.md`
