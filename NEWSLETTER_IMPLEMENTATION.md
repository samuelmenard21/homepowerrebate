# Newsletter & Social Campaign Implementation Checklist

## ✅ What's Ready Now

### Newsletter Signup Forms
- [x] Homepage newsletter form (`/`)
- [x] Blog hub newsletter form (`/blog`)
- [x] Assessment tool newsletter form (`/retrofit-assessment`)
- [x] Forms are styled and responsive
- [x] JavaScript handlers log signups to browser console
- [x] Success messages display to users

### Blog Content
- [x] 3 new foundational blog posts created and live
  - Greener Homes Grant Explained (`/blog/greener-homes-grant-explained`)
  - What Happens in an Energy Audit (`/blog/what-happens-in-an-energy-audit`)
  - Why Insulation First (`/blog/why-insulation-first-energy-retrofit`)
- [x] All blog posts featured on `/blog` hub (front-loaded)
- [x] All blog posts featured on homepage "From the blog" section
- [x] Internal linking from assessment tool to blog posts
- [x] Internal linking from guides (smart thermostats) to blog posts
- [x] Footer links to all blog posts

### Social Campaign Strategy
- [x] Reddit campaign templates (r/canada, r/HomeImprovement, r/BritishColumbia)
- [x] LinkedIn thread templates
- [x] Newsletter email templates with sample copy
- [x] Content repurposing ideas (TikTok, Twitter, Facebook, Instagram)
- [x] UTM parameter structure for tracking
- [x] Timeline recommendations

---

## 🔄 What Needs to Be Wired Up (Before Launch)

### Priority 1: Email Service Integration
**Goal:** Connect newsletter forms to email service

**Choose one:**
1. **ConvertKit** (recommended for creators/newsletters)
   - Free tier: 1,000 subscribers
   - Has automation + broadcast features
   - Native form embeds

2. **Substack** (simplest, built for newsletters)
   - Free tier with all features
   - Easiest to launch
   - Less custom integration

3. **Mailchimp** (powerful, more complex)
   - Free tier: 500 contacts
   - More marketing features
   - Requires more setup

**Implementation:**
1. Sign up for your email platform
2. Create a list called "HomePowerRebate Subscribers"
3. Replace the console.log() handlers in the forms with API calls to your email service
4. Test signup on each page

**Current form handlers (3 locations):**
```javascript
// Replace this section in index.html, blog/index.html, and retrofit-assessment/index.html
console.log('Newsletter signup:', { email, timestamp: new Date().toISOString() });

// With:
fetch('YOUR_EMAIL_SERVICE_ENDPOINT', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    email: email,
    timestamp: new Date().toISOString(),
    source: 'homepage' // or 'blog', 'assessment'
  })
});
```

### Priority 2: Analytics Setup
**Goal:** Track which social campaigns drive traffic and conversions

**Setup:**
1. Enable Google Analytics 4 on all pages (already set up based on existing code)
2. Add UTM parameters to all social post links (see SOCIAL_CAMPAIGNS.md)
3. Set up goals/events in GA4:
   - Newsletter signup (event: "newsletter_signup")
   - Assessment tool usage (event: "assessment_started")
   - Blog post views (already tracked)

### Priority 3: Social Campaign Posting
**Goal:** Test which platforms/angles resonate

**Start with (Week 1):**
- Reddit r/BritishColumbia: 1–2 posts about BC rebate stacking
- Reddit r/HomeImprovement: 1 post about insulation-first sequence
- Honest feedback: "This is my site, here's what I learned"

**Monitor:**
- Signup rate from each platform
- Traffic to blog posts
- Assessment tool clicks
- Comments/engagement (which questions come up most)

**Iterate:**
- Double down on high-engagement posts
- Refine subject lines based on what works
- Adjust newsletter copy based on feedback

---

## 📊 Metrics to Track

### Newsletter
- Signup rate by page (% of visitors)
- Email list growth week-over-week
- Open rate (after you send first email)
- Click-through rate (which links do people click?)
- Unsubscribe rate (should be <0.5%)

### Social Campaigns
- Traffic from Reddit, LinkedIn, etc. to blog posts
- Assessment tool clicks from social
- Newsletter signups from social (use UTM to track)
- Engagement rate (upvotes, comments, shares)

### Overall
- Total website visitors
- Blog post views (especially the 3 new ones)
- Assessment tool starts
- Newsletter signup funnel (homepage vs blog vs assessment)

---

## 🎯 Success Criteria (First 4 Weeks)

**Realistic targets:**
- 50–100 newsletter signups from organic + paid (if you run ads)
- 500–1,000 blog post views from social campaigns
- 2–5% of homepage visitors sign up for newsletter
- At least one Reddit post with 100+ upvotes or 10+ comments

**Red flags:**
- Zero newsletter signups after week 1 → Copy/positioning needs work
- Blog posts drive traffic but no newsletter signups → CTA is weak or unclear
- High unsubscribe rate → Email content doesn't match expectations

---

## 📝 Next Steps (Priority Order)

1. **This week:**
   - Choose email service
   - Integrate email API with 3 signup forms
   - Test signup on each page

2. **Next week:**
   - Create Reddit account (if you don't have one)
   - Post first Reddit thread to r/BritishColumbia
   - Monitor comments for questions/feedback

3. **Week 2:**
   - Post to r/HomeImprovement and r/canada
   - Create LinkedIn posts (threads)
   - Write first newsletter email and schedule

4. **Week 3+:**
   - Weekly newsletter sends (Mon or Wed morning seem to work)
   - Weekly Reddit engagement
   - Monitor analytics, iterate on copy

---

## 💡 Pro Tips for Social Posting

**Reddit:**
- Be honest about who you are ("I built this site")
- Answer questions in comments (more engagement than lurking)
- Post in evening (7–10 PM PT for BC timing)
- Don't spam links—provide value first, link second

**LinkedIn:**
- Post as yourself, not "as the company"
- Threads work better than single posts (more engagement)
- Post 2–3 times per week
- Engage with other energy/solar posts in your network

**Email:**
- Send Wednesday 9 AM or Tuesday 10 AM (test both)
- Personalize with recipient's city if possible
- Keep subject line under 50 characters
- One clear CTA per email

**General:**
- Authenticity beats polish on social
- Answer the question "Why should someone care?" first
- Track what works, double down on it
- Don't wait for perfection—launch and iterate

---

## Questions to Ask Yourself

- Which social platform does your target audience hang out on? (Probably Reddit for tech, LinkedIn for professionals)
- What's the #1 question you hear from homeowners? (Make that a blog post)
- What's your honest reason for building this? (Use that in your social bios)
- What metric actually matters to your business? (Leads? Newsletter growth? Brand awareness?)

Good luck! 🚀
