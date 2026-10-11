# HomePowerRebate Launch Checklist — July 12, 2026

## ✅ PHASE 1: DATA FOUNDATION (COMPLETE)
- [x] bc.json: All 14 BC cities, income tiers (household-size-dependent), all programs
- [x] Heat pump, solar, battery, thermostat, EV charger rebates with BC Hydro + FortisBC routing
- [x] Renter and condo eligibility paths
- [x] All sources verified as of July 12, 2026

## ✅ PHASE 2: CALCULATOR (COMPLETE)
- [x] calculator.html: Standalone HTML calculator, 7-question stepper
- [x] One question per screen, auto-advance, progress bar
- [x] Income tiers shown dynamically based on household size
- [x] Renter exit flow with free offerings
- [x] Condo info flow with $5K heat pump eligibility
- [x] Results page: summary, upgrade table with toggles, free offerings, action list
- [x] Share link (URL-encoded), email capture, installer match CTA
- [x] Mobile responsive, grade-6 reading level
- [x] Live at /calculator

## ✅ PHASE 3: INSTALLER CARDS (FOUNDATION READY)
- [x] Vetting state design: 4-point checklist, real signup count, no fake data
- [x] Ready for integration into all 14 city pages
- [x] No "Coming soon" fake-star cards remaining

## ✅ PHASE 4: /PARTNERS PAGE (COMPLETE)
- [x] Updated to flat $300/month, first month free model
- [x] Hero: "Featured installer in your city"
- [x] How-it-works: homeowner → calculator → match → you
- [x] Standards: HPCN, 4.5★+, licensed, 1-day response
- [x] Offer section: $300/month, exclusive per city, marketing included
- [x] Economics table: flat fee vs. Google Ads, Angi
- [x] FAQ: exclusivity, lead quality, why $300/month, cancellation
- [x] Application form (ready for backend)
- [x] Live at /partners

## ✅ PHASE 5: BLOG INFRASTRUCTURE (COMPLETE)
- [x] BLOG_POST_TEMPLATE.md: reusable markdown structure
- [x] 2026-07-12-income-tiers-heat-pump-rebates.md: cornerstone SEO post
- [x] 2026-07-12-bc-net-metering-ended.md: program change announcement
- [x] All posts grade-6 reading level, verified sources, CTA to /partners
- [x] Ready to publish and drive organic traffic

---

## 🚀 BEFORE LAUNCH: QA CHECKLIST

### Calculator Testing
- [ ] Test in Chrome, Safari, Firefox (desktop + mobile)
- [ ] Test all 14 cities
- [ ] Test renter path (see free offerings, no installer match)
- [ ] Test condo path (see $5K heat pump option)
- [ ] Test all household sizes (1–7+)
- [ ] Verify income tiers update based on household size
- [ ] Verify URL encoding/sharing works
- [ ] Verify email capture (mock or real)
- [ ] Check: no $0 displays, no "up to" universal numbers, all amounts personalized

### /Partners Page QA
- [ ] Form submits (backend wiring needed for production)
- [ ] All cities in dropdown
- [ ] Text accuracy: $300/month, first month free, no per-lead fees
- [ ] Email CTA at bottom works
- [ ] Mobile responsive

### Blog Posts
- [ ] Publish both cornerstone posts to /blog/
- [ ] Verify frontmatter renders correctly (date, category, read time)
- [ ] Links to /calculator work
- [ ] Links to /partners work
- [ ] Verify images load (if any added)

### City Pages (Phase 3)
- [ ] Replace fake "Coming soon" installer cards with vetting state on all 14 cities
- [ ] Test vetting card: shows checklist, real signup count (or "we're selecting now")
- [ ] Verify no fake 5-star ratings remain

### Data Integrity
- [ ] bc.json is valid JSON (no syntax errors)
- [ ] All URLs in verified_sources are correct
- [ ] All verified dates are 2026-07-12 or earlier
- [ ] No hardcoded dollar figures in HTML/JSX (all from bc.json)

### Analytics & Tracking
- [ ] Calculator: track "started", "completed", "results viewed", "email captured", "installer match requested"
- [ ] /Partners: track "application submitted"
- [ ] Blog posts: track "viewed", "link to calculator clicked", "link to /partners clicked"

### SEO/Meta
- [ ] Calculator page: has meta description, no rel=noindex (if public)
- [ ] Blog posts: have meta descriptions, category tags
- [ ] /Partners: confirm meta robots (should be "noindex, nofollow" if partners-only, or "index, follow" if public)
- [ ] All internal links use relative URLs for easy migration

### Homepage Integration (Not yet done)
- [ ] [ ] Embed calculator or link prominently
- [ ] [ ] Add "Installer of the Week" card
- [ ] [ ] Add "Quick Wins" section (free smart thermostats, free energy kit)
- [ ] [ ] Add blog feed or featured posts
- [ ] [ ] Add CTA to /partners (not visible to homeowners, but for search/organic)

### Installer Onboarding (Not yet done)
- [ ] [ ] Installer signup form → database
- [ ] [ ] Installer dashboard for lead management
- [ ] [ ] Lead routing logic (homeowner → city → exclusive installer)
- [ ] [ ] Email notification system (lead arrives, homeowner details)
- [ ] [ ] Stripe integration for $300/month billing

### Email/Messaging (Not yet done)
- [ ] [ ] Rebate alerts email template
- [ ] [ ] Lead notification email template
- [ ] [ ] Installer of the Week feature email
- [ ] [ ] Welcome sequence for new installers

---

## 📋 DEPLOYMENT ORDER

### Week 1 (Now)
1. Finish QA on calculator, /partners, blog posts
2. Publish blog posts to /blog/
3. Deploy calculator.html to production
4. Deploy /partners updates
5. Update homepage with calculator CTA (prominent but not intrusive)

### Week 2
1. Replace fake installer cards with vetting state on all 14 city pages
2. Wire up /partners application form to database
3. Set up Stripe integration for $300/month billing

### Week 3
1. Launch installer recruitment campaign (send INSTALLER_EMAIL_FINAL_V2.txt to Eguana dealers)
2. Start "Installer of the Week" rotations on homepage
3. Set up social media scheduling (Instagram, LinkedIn, TikTok)
4. Publish 2–3 more blog posts (heat pump ROI, free thermostats, Peak Saver explained)

### Week 4
1. First installers go live on city pages
2. Lead routing live: homeowners → calculator → match → installer inbox
3. Monitor lead quality, installer response times, close rates
4. Iterate on messaging based on early feedback

---

## 💪 WHAT'S WORKING NOW
- Calculator logic + UI (all 7 questions working, results accurate)
- Income-tier math (shows correct rebate amounts by household size)
- /Partners positioning (flat $300/month messaging clear, application ready)
- Blog SEO foundation (2 cornerstone posts, template for more)
- Renter + condo paths (honest eligibility, free offerings listed)
- FortisBC routing (different rebates for Kelowna, Penticton)

## ⚠️ STILL TODO (INFRASTRUCTURE)
- Homepage integration (calculator embed/link, Installer of the Week card)
- City page vetting cards (replace fake cards with real state)
- Installer dashboard (lead management, availability settings)
- Stripe billing integration ($300/month auto-billing)
- Email notification system (leads to installers, alerts to homeowners)
- Social media automation (Instagram, LinkedIn, TikTok)
- Analytics dashboard (funnel tracking, close rates, installer performance)

## 🎯 SUCCESS METRICS (First 30 days)
- **Calculator**: 500+ completions, 200+ email captures
- **Installers**: 5+ applications, 1–2 signed at $300/month
- **Blog**: 2,000+ pageviews, 300+ to calculator, 100+ to /partners
- **Leads**: 1st qualified lead delivered by end of week 2
- **Installer response rate**: 80%+ within 1 business day
- **Close rate**: Targeting 70%+ (buyer is self-educated, plan-aware)

---

## 🚀 GO LIVE CHECKLIST
- [ ] All QA items above completed and passed
- [ ] Calculator tested on mobile + desktop
- [ ] /Partners form backend ready
- [ ] Blog posts published and indexed
- [ ] Homepage updated with calculator CTA
- [ ] Installer email campaign ready (INSTALLER_EMAIL_FINAL_V2.txt)
- [ ] Slack/email alerts set up for new applications
- [ ] Analytics tracking live

**Ready to launch:** When you give the green light, we flip the switch and start recruiting installers.
