# Meta Automation Worker for HomePowerRebate

**Fully automated Instagram & Facebook posting — 3-4 posts per day, zero manual work.**

This Cloudflare Worker automatically posts content from your HomePowerRebate site to Instagram and Facebook on a schedule, targeting high-intent keywords and driving traffic back to your site.

## Files

- **`index.js`** — Main worker logic (post creation, API calls)
- **`wrangler.toml`** — Cloudflare configuration (cron schedule, environment variables)
- **`package.json`** — Dependencies (wrangler CLI)

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Deploy to Cloudflare
```bash
npx wrangler login
npx wrangler deploy
```

### 3. Add Your Meta Credentials
```bash
npx wrangler secret put META_ACCESS_TOKEN
# Paste your access token

npx wrangler secret put INSTAGRAM_BUSINESS_ACCOUNT_ID
# Enter your Instagram Business Account ID

npx wrangler secret put FACEBOOK_PAGE_ID
# (Optional) Enter your Facebook Page ID for cross-posting
```

### 4. Verify Secrets
```bash
npx wrangler secret list
```

### 5. Test
```bash
curl -X POST https://meta-automation.yoursubdomain.workers.dev/test
```

**Expected:** A new post appears on your Instagram and Facebook!

## How It Works

**Posting Schedule (Cron)**
- 6 AM PT: Post content (random type)
- 12 PM PT: Post content
- 6 PM PT: Post content
- 10 PM PT: Post content
- **Total: 4 posts/day = 28/week**

**Post Types (Auto-selected)**
- **40%** Blog posts (with featured image + link)
- **35%** Tips/hacks (carousel-style insights)
- **25%** City guides (local rebate breakdowns)

**Content Sources**
- Blog posts from `/blog/` directory
- City pages from `/ca/bc/*/` directory
- Automatically updated as you add new content

**Platforms**
- **Instagram:** Posts with image + caption + link
- **Facebook:** Reposts with image + message + link

## Configuration

### Update Posting Schedule

Edit `wrangler.toml`:

```toml
[[triggers.crons]]
cron = "0 6,12,18,22 * * *"  # Change hours here (24-hour format)
```

Examples:
- 4 times daily: `0 6,12,18,22 * * *`
- 2 times daily: `0 8,18 * * *`
- Once daily: `0 8 * * *`

### Update Post Distribution

Edit `index.js`:

```javascript
const POST_TYPES = {
  BLOG: 0.50,      // 50% blog posts
  TIPS: 0.30,      // 30% tips
  CITY: 0.20       // 20% city guides
};
```

### Add More Content Sources

Edit `CONTENT_SOURCES` in `index.js`:

```javascript
blogs: [
  { path: "/blog/new-post.html", type: "blog", title: "Your New Post Title" },
  // ... more blogs
]
```

## Monitoring

### View Logs
```bash
npx wrangler logs
```

### Check Successful Posts
Look for messages like:
```
[Meta] Post created successfully: 123456789
[Meta] Execution at 2026-07-25T18:00:00.000Z
```

### Verify in GA4
All posts include UTM params: `?source=meta&medium=instagram&campaign=[type]`

Check Google Analytics for:
- Sessions from source=meta
- Medium=instagram or medium=facebook
- Landing pages
- Conversion rate

## Troubleshooting

### Worker not posting?
1. Check logs: `npx wrangler logs`
2. Verify secrets: `npx wrangler secret list`
3. Test manually: `curl -X POST https://meta-automation.yoursubdomain.workers.dev/test`

### "401 Unauthorized"
- Token expired → Regenerate in Meta App Dashboard
- Update: `npx wrangler secret put META_ACCESS_TOKEN`

### Account ID wrong?
- Verify exact Instagram Business Account ID
- Update: `npx wrangler secret put INSTAGRAM_BUSINESS_ACCOUNT_ID`

### Only Instagram posting, Facebook failing?
- Facebook posting is non-critical (fails gracefully)
- Check Facebook Page ID if you want to fix it
- Update: `npx wrangler secret put FACEBOOK_PAGE_ID`

## Full Documentation

See:
- **Strategy & Planning:** `../meta-strategy.md` (coming soon)
- **Setup Guide:** `../META_SETUP.md` (coming soon)
- **Pinterest Worker:** `../pinterest-worker/README.md` (reference implementation)

## Next Steps

1. ✅ Deploy worker (this directory)
2. ✅ Set API credentials
3. ✅ Test first post
4. 📊 Monitor logs for 24 hours
5. 📈 Check GA4 after 1 week for traffic data
6. 🔄 Optimize based on performance

---

**Questions?** Open the full setup guide (coming soon) or check the strategy document.
