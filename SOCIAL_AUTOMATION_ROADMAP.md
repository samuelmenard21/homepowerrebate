# Social Media Automation Roadmap

**Parallel automation systems for Pinterest and Meta (Instagram/Facebook)**

---

## Overview

You're building **two independent Cloudflare Workers** that automate social media posting:

1. **Pinterest Automation** — 4 pins/day to Pinterest boards
2. **Meta Automation** — 4 posts/day to Instagram + Facebook

**Together:** 8 pieces of content/day across 3 platforms = 56 posts/week = ~240 posts/month

---

## System Architecture

```
HomePowerRebate Content
├─ Blog Posts (/blog/*.html)
├─ City Pages (/ca/bc/*/index.html)
└─ Installer Data
    ↓
    ├─ Cloudflare Worker 1: Pinterest
    │  └─ Posts 4 pins/day → Pinterest API
    │     ↓
    │     7 Pinterest Boards (searchable, SEO)
    │
    └─ Cloudflare Worker 2: Meta
       └─ Posts 4 items/day → Instagram + Facebook APIs
          ↓
          Instagram Business Account + Facebook Page
    
    ↓
    User Clicks Pin/Post → UTM tracked → GA4 Dashboard
    ↓
    HomePowerRebate Site (installer leads)
```

---

## Timeline

### Now (July 25-26)
- Pinterest: Waiting for Standard access approval (24-48 hours)
- Meta: Build worker in parallel (ready to deploy immediately)

### When Approvals Come (July 27-28)
- Pinterest: Regenerate token with write scopes, update Cloudflare secret
- Meta: Create business account + get API credentials, update Cloudflare secrets
- Both workers go live simultaneously

### Ongoing (Aug 1+)
- Monitor analytics on both platforms
- Optimize based on performance data
- Both systems post autonomously, zero daily work

---

## Files & Setup

### Pinterest System

**Setup:**
1. Read: `/Users/sammenard/Downloads/Powerrebate/PINTEREST_SETUP.md`
2. Status: Worker deployed ✅ | Awaiting approval ⏳

**Files:**
- `pinterest-worker/index.js` — Worker code
- `pinterest-worker/wrangler.toml` — Config
- `pinterest-worker/README.md` — Quick reference
- `pinterest-strategy.md` — Full strategy + content calendar
- `pinterest-pin-templates.html` — Design templates

**Posting Schedule:**
- 6 AM, 12 PM, 6 PM, 10 PM PT
- 4 pins/day = 28/week = ~100/month
- Types: 40% blog, 35% tips, 25% city guides

**Target:** 500+ clicks/month (equivalent to 10 installer leads)

---

### Meta System

**Setup:**
1. Read: `/Users/sammenard/Downloads/Powerrebate/META_SETUP.md`
2. Status: Ready to deploy | Awaiting business account setup

**Files:**
- `meta-worker/index.js` — Worker code
- `meta-worker/wrangler.toml` — Config
- `meta-worker/README.md` — Quick reference

**Posting Schedule:**
- 6 AM, 12 PM, 6 PM, 10 PM PT (same as Pinterest)
- 4 posts/day = 28/week = ~100/month
- Types: 40% blog, 35% tips, 25% city guides
- Platforms: Instagram + Facebook (simultaneous)

**Target:** 300+ clicks/month

---

## Setup Checklist

### Pinterest (Waiting for Approval)
- [ ] Business Account created
- [ ] 7 boards created
- [ ] Trial access approved ✅
- [ ] Standard upgrade requested ✅
- [ ] Worker deployed ✅
- [ ] Secrets set ✅
- [ ] Awaiting Standard upgrade approval ⏳
- [ ] Regenerate token with write scopes (when approved)
- [ ] Update Cloudflare secret with new token
- [ ] Cron schedule enabled ⏳
- [ ] First pin posted & visible

### Meta (Ready to Start)
- [ ] Meta Business Account created
- [ ] Instagram Business Account linked
- [ ] Facebook Page created
- [ ] Account IDs saved
- [ ] API app created in Meta Developers
- [ ] Instagram Graph API added
- [ ] Facebook Graph API added
- [ ] Access token generated
- [ ] Worker deployed
- [ ] Secrets set
- [ ] Cron schedule enabled
- [ ] First post posted & visible

---

## Parallel Deployment Strategy

**Phase 1: Setup (Now)**
- ✅ Pinterest worker: Deployed, waiting for token approval
- Build Meta worker: Deploy and test immediately

**Phase 2: Launch (When approvals come)**
- Pinterest: Update token, both systems go live
- Meta: All credentials ready, systems go live together
- Result: 8 posts/day across 3 platforms automatically

**Phase 3: Monitor (Week 1-4)**
- Track analytics on both platforms
- Identify top-performing content types
- Measure clicks and installer leads

**Phase 4: Optimize (Month 2)**
- Scale up winning content types
- Adjust posting frequency if needed
- Expand content if performing well
- Consider additional platforms (LinkedIn later)

---

## Content Reuse Strategy

Both systems pull from the same content sources:
- **Same blog posts** (content is platform-agnostic)
- **Same city pages** (local targeting works across platforms)
- **Different designs**: Pinterest pins vs. Instagram/Facebook cards

### Advantages
- Write content once, post everywhere
- Double the reach with single content effort
- Easy to update and add new content
- All tracked separately in GA4 by platform

### Example Flow
1. Publish new blog post: `/blog/new-post.html`
2. Add to both workers' `CONTENT_SOURCES.blogs`
3. Both workers automatically include it in rotation
4. Next 4 days: appears on Pinterest + Instagram + Facebook
5. Track performance by platform in GA4

---

## Analytics & Measurement

### UTM Parameter Tracking

**Pinterest:** `?source=pinterest&medium=pin&campaign=[topic]`
- Topics: heat-pump, solar, battery, thermostat

**Instagram:** `?source=meta&medium=instagram&campaign=[type]`
- Types: blog, tips, city-guides

**Facebook:** `?source=meta&medium=facebook&campaign=[type]`
- Types: blog, tips, city-guides

### GA4 Dashboard Setup

Create custom reports for:
```
source = pinterest (OR) source = meta
Medium = pin (OR) medium = instagram (OR) medium = facebook
Campaign = [topic]
```

Track:
- Sessions from social (vs. organic, direct, other)
- Clicks by platform
- Click-through rate (CTR)
- Landing pages
- Conversion to installer leads

### Expected Results

**Month 1:**
- Pinterest: 50-100 clicks
- Meta: 30-50 clicks
- Total: 80-150 clicks
- Equivalent: 1-3 installer leads

**Month 2:**
- Pinterest: 200-300 clicks
- Meta: 100-150 clicks
- Total: 300-450 clicks
- Equivalent: 6-9 installer leads

**Month 3+:**
- Pinterest: 500+ clicks
- Meta: 300+ clicks
- Total: 800+ clicks
- Equivalent: 15+ installer leads per month

---

## Next Steps (Immediate)

### Before Sept 1
1. ✅ Pinterest: Wait for approval, regenerate token
2. ✅ Meta: Set up business account + get credentials
3. ✅ Deploy Meta worker
4. ✅ Enable both cron schedules
5. ✅ Monitor first 7 days of posts
6. ✅ Collect baseline analytics

### Before Oct 1
7. Review performance data on both platforms
8. Optimize based on click-through rates
9. Consider expanding content (more city guides, blog posts)
10. Test new posting times if needed

### Future Expansions
- LinkedIn automation (later, lower priority)
- TikTok automation (if applicable for audience)
- Pinterest Ads integration (paid promotion)
- Email newsletter integration (drive more conversions)

---

## Files to Review

**Setup Guides:**
- `PINTEREST_SETUP.md` — Detailed Pinterest walkthrough
- `META_SETUP.md` — Detailed Meta walkthrough
- `PINTEREST_AUTOMATION_README.md` — Pinterest overview
- `SOCIAL_AUTOMATION_ROADMAP.md` (this file)

**Code:**
- `pinterest-worker/` — Complete Pinterest automation
- `meta-worker/` — Complete Meta automation

**Strategy:**
- `pinterest-strategy.md` — Pinterest keywords, boards, content calendar

---

## Troubleshooting Quick Links

**Pinterest Issues:**
- Worker not posting? See `pinterest-worker/README.md` — Troubleshooting section
- Token problems? See `PINTEREST_SETUP.md` — Phase 5
- Schedule not working? See `PINTEREST_SETUP.md` — Phase 4

**Meta Issues:**
- Worker not posting? See `meta-worker/README.md` — Troubleshooting section
- Credentials wrong? See `META_SETUP.md` — Phase 3
- Instagram specific? See `META_SETUP.md` — Phase 1-2

---

## FAQ

**Q: Do both systems use the same content?**
Yes! Both pull from the same blog posts and city pages. They post simultaneously but to different platforms.

**Q: Can I adjust posting times separately?**
Yes. Each worker has its own `wrangler.toml` with a cron schedule. Edit them independently if needed.

**Q: What if one platform performs better?**
Monitor GA4 data. If Instagram outperforms Pinterest, you could increase Meta posting frequency while keeping Pinterest steady.

**Q: How do I add new content?**
Add blog posts or city pages to both workers' `CONTENT_SOURCES` object in `index.js`. Both will automatically include them in rotation on next deploy.

**Q: Can I pause one system without pausing the other?**
Yes. Disable the cron schedule on one worker via Cloudflare dashboard without affecting the other.

**Q: What if Pinterest/Meta API changes?**
Both workers are deployed as static code on Cloudflare. If APIs change, you'd need to update the code and redeploy. This is a one-time fix, not ongoing maintenance.

---

## Success Definition

**You've won when:**
- ✅ Both workers deployed and posting automatically
- ✅ No manual intervention needed daily
- ✅ Combined 500+ clicks/month from both platforms
- ✅ 10+ installer leads/month traced back to social
- ✅ Analytics dashboard shows which platform performs best
- ✅ You can add new blog posts and they automatically post to both platforms

**Expected timeline:** 6-8 weeks from approval to achieving 500+ clicks/month baseline.

---

**Start with:** Read `PINTEREST_SETUP.md` and `META_SETUP.md` in that order, then execute in parallel.

Good luck! 🚀
