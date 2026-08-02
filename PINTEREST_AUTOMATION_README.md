# Pinterest Automation System for HomePowerRebate

**Complete hands-off Pinterest automation targeting 500+ clicks/month**

---

## What You're Getting

A fully automated Pinterest marketing system that:

✅ **Posts 3-4 pins every day** (28 pins/week = ~100 pins/month)  
✅ **Automatically selects pin content** from your blog posts and city pages  
✅ **Diversifies content mix** (40% blog posts, 35% tips/hacks, 25% city guides)  
✅ **Targets high-intent keywords** (heat pump rebates, solar, thermostat, battery)  
✅ **Drives organic traffic** from Pinterest → your site with UTM tracking  
✅ **Runs completely autonomously** after initial setup (zero daily work)  

**Expected Result:** 500+ clicks/month from Pinterest (equivalent to ~10 installer leads)

---

## System Architecture

```
Your HomePowerRebate Content
    ↓
    ├─ Blog Posts (/blog/*.html)
    ├─ City Pages (/ca/bc/*/index.html)
    └─ Installer Data
    ↓
Cloudflare Worker (runs 4x daily on schedule)
    ├─ Selects random pin type (blog/tips/city)
    ├─ Pulls content + metadata
    ├─ Generates pin design
    └─ Posts to Pinterest API
    ↓
Pinterest Boards (public, searchable)
    ├─ BC Heat Pump Rebates
    ├─ BC Solar Panel Rebates
    ├─ BC Home Energy Rebates (hub)
    ├─ Homeowner Tips & Hacks
    └─ + 3 secondary boards
    ↓
Pinterest Users Click Pin
    ↓
Your Site (tracked via UTM: ?source=pinterest&medium=pin&campaign=...)
    ↓
GA4 Dashboard (measure clicks, conversions, ROI)
```

---

## Files & Setup Timeline

### 📁 Files Created

```
/Users/sammenard/Downloads/Powerrebate/

├── PINTEREST_AUTOMATION_README.md        (This file)
├── PINTEREST_SETUP.md                    (7-phase setup guide — 30 min)
├── pinterest-strategy.md                 (Strategy + content calendar)
├── pinterest-pin-templates.html          (3 design templates — visual reference)
│
└── pinterest-worker/                     (Cloudflare Worker — auto-posting agent)
    ├── index.js                          (Main worker logic)
    ├── wrangler.toml                     (Configuration + cron schedule)
    ├── package.json                      (Dependencies)
    └── README.md                         (Quick start)
```

### ⏱️ Setup Timeline

**Phase 1: Pinterest Account (10 min)**
- Create business account
- Create 7 boards

**Phase 2: API Credentials (10 min)**
- Generate Pinterest API token
- Verify token works

**Phase 3: Cloudflare Deployment (10 min)**
- Deploy worker
- Set secrets

**Phase 4: Enable Scheduling (5 min)**
- Activate cron triggers

**Phase 5: Analytics (5 min)**
- Connect GA4 tracking

**Phase 6: Manual Testing (5 min)**
- Post 5 test pins

**Phase 7: Go Live (ongoing)**
- Publish boards
- Monitor weekly

**Total: ~50 minutes setup, then zero daily work**

---

## Quick Start (TL;DR)

1. **Read the setup guide:**
   ```
   /Users/sammenard/Downloads/Powerrebate/PINTEREST_SETUP.md
   ```

2. **Follow Phases 1-3** (30 minutes):
   - Create Pinterest Business Account
   - Generate API token
   - Deploy Cloudflare Worker

3. **Test the first pin** (5 minutes):
   ```bash
   curl -X POST https://pinterest-automation.yoursubdomain.workers.dev/test
   ```

4. **Wait for automatic posting** (starting 6 AM tomorrow)
   - Worker posts 4 pins/day automatically
   - Monitor GA4 for traffic

---

## The 3 Pin Types

### Type 1: Blog Post Pins (40%)
- **Design:** Featured image + headline + stat
- **Example:** "BC Heat Pump Rebates 2026: Get $4K–$16K Back"
- **Links to:** Full blog post
- **Audience:** Research-focused homeowners

### Type 2: Tips/Hacks Pins (35%)
- **Design:** Bold headline + icon on gradient background
- **Example:** "Peak Saver Battery: $5K vs $1.5K (This One Decision)"
- **Links to:** Relevant blog post
- **Audience:** Decision-makers (high intent)

### Type 3: City Guide Pins (25%)
- **Design:** City name + key rebate amounts + CTA
- **Example:** "Vancouver: Get $10K in Rebates (Heat Pump + Solar)"
- **Links to:** City landing page
- **Audience:** Local searchers

**See:** `pinterest-pin-templates.html` (open in browser)

---

## Content Strategy

### Keyword Targeting (by topic)

**Heat Pump (60% of pins)**
- "bc heat pump rebate 2026"
- "heat pump cost bc hydro rebate"
- "best heat pump brands bc"

**Solar (30% of pins)**
- "bc solar panel rebate 2026"
- "solar panel cost bc rebate"
- "peak saver battery bc hydro"

**Battery (5% of pins)**
- "home battery storage bc rebate"

**Thermostat (5% of pins)**
- "mysa thermostat bc hydro rebate"

### 7 Pinterest Boards

1. BC Heat Pump Rebates 2026 (60+ pins)
2. BC Solar Panel Rebates (50+ pins)
3. BC Home Energy Rebates 2026 (100+ pins, hub)
4. Homeowner Tips & Hacks (40+ pins)
5. BC Thermostat Rebates (20+ pins)
6. Battery Storage & Peak Saver (15+ pins)
7. Best HVAC Brands (25+ pins)

### 12-Week Content Calendar

**Week 1-4:** Heat Pump + Solar focus (narrow, high-intent)  
**Week 5-8:** Rotate through all topics  
**Week 9-12:** Optimize based on analytics  

**See:** `pinterest-strategy.md` for full calendar

---

## Analytics & Success Metrics

### Posting Schedule
- **6 AM PT:** 1 pin (early planners)
- **12 PM PT:** 1 pin (lunch research)
- **6 PM PT:** 1 pin (evening planning)
- **10 PM PT:** 1 pin (night browsing)
- **Total: 4 pins/day = 28/week = ~100/month**

### Expected CTR
- **Month 1:** 50-100 clicks (testing)
- **Month 2:** 150-250 clicks
- **Month 3:** 300+ clicks
- **Month 4+:** 500+ clicks (steady state)

### Tracking
- **GA4:** Filter by `source=pinterest, medium=pin`
- **Pinterest Analytics:** Track impressions, pins, clicks
- **Monthly:** Review top-performing pin types, adjust strategy

### Conversion Path
- 500 clicks/month
- ~50 clicks → 1 installer lead
- **500 clicks = ~10 installer leads/month**

---

## Monitoring & Maintenance

### Daily (Automated)
- Worker posts pins automatically
- No action needed

### Weekly (5 min check)
```bash
# View logs
npx wrangler logs

# Check GA4 for traffic
# Go to Google Analytics → Acquisition → Search console → source=pinterest
```

### Monthly (15 min optimization)
1. Review analytics:
   - Which pin types got most clicks?
   - Which times performed best?
   - Which boards got most engagement?

2. Adjust strategy:
   - Increase % of best-performing type
   - Adjust posting times if needed
   - Add new content if performing well

3. Update content:
   - Add new blog posts to `index.js`
   - Update city list if expanding regions

---

## Troubleshooting

### "Pins not posting?"
1. Check Cloudflare logs: `npx wrangler logs`
2. Verify token: `npx wrangler secret list`
3. Test manually: `curl -X POST https://pinterest-automation.yoursubdomain.workers.dev/test`

### "Only 1-2 pins per day instead of 4?"
- Cron schedule issue
- Edit `wrangler.toml`, change `[[triggers.crons]]` cron value
- Redeploy: `npx wrangler deploy`

### "API token expired?"
- Generate new token in Pinterest Developers
- Update: `npx wrangler secret put PINTEREST_ACCESS_TOKEN`

**Full troubleshooting:** See `PINTEREST_SETUP.md` Phase 7

---

## Next Phase: Optimization (Week 2+)

Once automation is live and running:

1. **Collect data** (1 week)
   - Let worker post 28+ pins
   - Gather analytics on click performance

2. **Identify winners** (Week 2)
   - Which pin types got most clicks?
   - Which keywords performed best?
   - Which boards had best engagement?

3. **Optimize strategy** (Week 3+)
   - Increase % of winning pin types
   - Add more pins on winning keywords
   - Expand city guides if local searches performing well
   - Test new design variations

4. **Scale** (Month 2+)
   - If 500+ clicks achieved, maintain schedule
   - If growth slower, add more cities or keywords
   - If growth faster, expand to new topics

---

## Success Checklist

- [ ] **Week 0:** Complete all 7 setup phases (30 min)
- [ ] **Day 1:** First test pin posted successfully
- [ ] **Day 7:** Worker posted 28 pins (4/day × 7 days)
- [ ] **Week 2:** GA4 shows 50-100 clicks from Pinterest
- [ ] **Week 4:** GA4 shows 200+ clicks
- [ ] **Month 2:** 300+ clicks/month
- [ ] **Month 3:** 500+ clicks/month (target achieved)

---

## Files Reference

| File | Purpose | Read First? |
|------|---------|-----------|
| `PINTEREST_SETUP.md` | Step-by-step setup guide | ✅ YES |
| `pinterest-strategy.md` | Strategy, keywords, boards, calendar | 📖 Reference |
| `pinterest-pin-templates.html` | Visual design examples | 👀 Visual |
| `pinterest-worker/README.md` | Quick dev reference | 💻 Dev |
| `pinterest-worker/index.js` | Worker code (auto-posting logic) | 🔧 Code |
| `pinterest-worker/wrangler.toml` | Cloudflare config | ⚙️ Config |

---

## Key Takeaways

🎯 **What You Built:** Autonomous Pinterest marketing agent posting 3-4 pins/day  
⏰ **Setup Time:** 30-50 minutes (one-time)  
🚀 **Ongoing Work:** Zero (completely automated)  
📊 **Expected Result:** 500+ clicks/month → 10 installer leads/month  
💰 **Cost:** Minimal (Cloudflare Workers free tier covers this)  

---

## Next Steps

1. **Right now:** Open `PINTEREST_SETUP.md` and start Phase 1
2. **In 30 min:** Complete Phases 1-3 (account + API + deployment)
3. **In 2 hours:** Complete Phases 4-7 (enable scheduling, test, go live)
4. **Tomorrow:** First pins start posting automatically
5. **Next week:** Check GA4 for traffic results

---

**Let the automation run. Track the results. Optimize based on data.**

Good luck! 🚀
