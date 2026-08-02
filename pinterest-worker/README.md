# Pinterest Automation Worker for HomePowerRebate

**Fully automated Pinterest posting — 3-4 pins per day, zero manual work.**

This Cloudflare Worker runs on a schedule and automatically posts pins from your HomePowerRebate content to Pinterest, targeting high-intent keywords and driving 500+ clicks/month to your site.

## Files

- **`index.js`** — Main worker logic (pin creation, API calls, analytics logging)
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

### 3. Add Your Pinterest API Token
```bash
npx wrangler secret put PINTEREST_ACCESS_TOKEN
# Paste your token from Pinterest Developers
```

### 4. Set Board ID
```bash
npx wrangler secret put PINTEREST_BOARD_ID
# Enter your primary board ID: bc-heat-pump-rebates-2026
```

### 5. Test
```bash
curl -X POST https://pinterest-automation.yoursubdomain.workers.dev/test
```

**Expected:** A new pin appears on your Pinterest board!

## How It Works

**Posting Schedule (Cron)**
- 6 AM PT: Post pin (random type)
- 12 PM PT: Post pin
- 6 PM PT: Post pin
- 10 PM PT: Post pin
- **Total: 4 pins/day = 28 pins/week**

**Pin Types (Auto-selected)**
- **40%** Blog posts (full content pins with featured image)
- **35%** Tips/hacks (high-contrast design pins)
- **25%** City guides (local rebate summary pins)

**Content Sources**
- Blog posts from `/blog/` directory
- City pages from `/ca/bc/*/` directory
- Automatically updated as you add new content

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

### Update Pin Distribution

Edit `index.js`:

```javascript
const PIN_TYPES = {
  BLOG: 0.40,      // Change to 0.50 for 50% blog pins
  TIPS: 0.35,      // Change to 0.30 for 30% tips pins
  CITY: 0.25       // Change to 0.20 for 20% city pins
};
```

### Add More Content Sources

Edit `CONTENT_SOURCES` in `index.js` to include new blogs:

```javascript
const CONTENT_SOURCES = {
  blogs: [
    { path: "/blog/new-post.html", type: "blog", title: "Your New Post Title" },
    // ... more blogs
  ]
}
```

## Monitoring

### View Logs
```bash
npx wrangler logs
```

### Check Successful Posts
Look for messages like:
```
[Pinterest] Pin posted successfully: 987654321
[Pinterest] Scheduled execution at 2026-07-25T18:00:00.000Z
```

### Verify in GA4
All pins include UTM params: `?source=pinterest&medium=pin&campaign=[topic]`

Check Google Analytics for:
- Sessions from source=pinterest
- Medium=pin
- Landing pages
- Conversion rate

## Troubleshooting

### Worker not posting?
1. Check logs: `npx wrangler logs`
2. Verify token: `npx wrangler secret list`
3. Test manually: `curl -X POST https://pinterest-automation.yoursubdomain.workers.dev/test`

### "401 Unauthorized"
- Token expired → Regenerate in Pinterest Developers
- `npx wrangler secret put PINTEREST_ACCESS_TOKEN` (new token)

### Board ID wrong?
- Verify exact board slug from Pinterest URL
- Update: `npx wrangler secret put PINTEREST_BOARD_ID`

### Only 1 pin posting instead of 4?
- Check cron syntax in `wrangler.toml`
- Verify times are in 24-hour format
- Deploy changes: `npx wrangler deploy`

## Full Documentation

See:
- **Strategy & Planning:** `../pinterest-strategy.md`
- **Setup Guide:** `../PINTEREST_SETUP.md`
- **Pin Templates:** `../pinterest-pin-templates.html`

## Next Steps

1. ✅ Deploy worker (this directory)
2. ✅ Set API credentials
3. ✅ Test first pin
4. ✅ Monitor logs for 24 hours
5. 📊 Check GA4 after 1 week for traffic data
6. 🔄 Optimize based on performance

---

**Questions?** Open the full setup guide: `../PINTEREST_SETUP.md`
