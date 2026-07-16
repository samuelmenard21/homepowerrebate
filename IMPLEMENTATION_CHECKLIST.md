# HomePowerRebate: Multi-Region Implementation Checklist

**Status:** Ready to implement (BC improvements + Ontario/California setup)
**Timeline:** BC rewrite (2 weeks) | Ontario launch (1-2 weeks after) | California (by Sept)

---

## PHASE 1: BC Rewrite + Multi-Region Foundation (Now → 2 weeks)

### Homepage Rewrite
- [ ] Replace hero section with region-selector model
- [ ] Add region badges (BC Live | Ontario Coming | California Coming)
- [ ] Update process section (keep same, universal language)
- [ ] Add social proof with multi-region numbers
- [ ] Create region selector (top nav or hero)
- [ ] Update CTA copy ("Calculate my rebate" not "See your money")

### Content Architecture
- [ ] Implement regional messaging guide (see REGIONAL_MESSAGING_GUIDE.md)
- [ ] Create "Request My City" page at `/request-city`
- [ ] Add form to city list page (see REQUEST_CITY_FORM.md)
- [ ] Set up database: `requested_cities` table (schema in REQUEST_CITY_FORM.md)
- [ ] Create backend API: `/api/request-city` endpoint
- [ ] Set up email automation: Confirmation + Launch notification templates

### Rewrite Core Pages (Use Regional Messaging Guide)
- [ ] **About Us Page** (NEW — Critical)
  - Your story: Why you built this
  - Mission statement: "Helping homeowners across BC, Ontario, and beyond access rebates they qualify for"
  - Track record: X homeowners matched, Y rebates claimed, Z% satisfaction
  - Photo of you (trust signal)
  - Team (if any)
  - Link to installer vetting criteria
  - Regional expansion timeline

- [ ] **Homepage** (UPDATE)
  - Remove BC-specific language
  - Add region selector
  - Update copy to use "your area," "your utility"
  - Add "Request My City" CTA (prominent)

- [ ] **Installer Vetting Criteria Page** (NEW)
  - What we require (universal)
  - BC-specific requirements
  - Ontario requirements (template — fill in after research)
  - California requirements (template — fill in after research)
  - Link from every city page

### BC City Pages (14 total)
- [ ] **Rewrite for human tone** (use examples from REGIONAL_MESSAGING_GUIDE.md)
  - Remove AI-generated language
  - Add specific examples ("Most homeowners are replacing 15+ year old furnaces...")
  - Show your thinking ("I get asked X, here's why...")
  - Make it conversational

- [ ] **Add table header** to rebate table explaining what it shows

- [ ] **Add installer section** for 2-3 vetted installers with:
  - Name, company, photo
  - Expertise tags (Heat Pump ✓ | Solar ✓ | Battery ✓)
  - Service area + response time
  - 2-3 case study examples
  - "Get a quote" link

- [ ] **Add installer vetting explanation** (link to vetting criteria page)

- [ ] **Add comparison section** linking to relevant posts:
  - Island vs Mainland (for island cities)
  - Interior solar comparison (for Kelowna/Kamloops)
  - BC Hydro vs FortisBC (all BC cities)

- [ ] **Add guide link** at bottom ("Want the full guide? Read [City]'s complete guide →")

- [ ] **Remove/update all AI language** (run through REGIONAL_MESSAGING_GUIDE audit checklist)

### BC City Guides (14 total)
- [ ] **Rewrite for human tone** (same approach as city pages)

- [ ] **Add installer expertise badges** — show which installers do what

- [ ] **Confirm solar + battery payback included** (or add if missing)

- [ ] **Add comparison section links** (island vs mainland, interior solar, BC Hydro vs FortisBC)

- [ ] **Add city page CTA** ("Ready to see your installer? See [City]'s current profile →")

- [ ] **Update all AI language** (run through audit)

### Blog/Content Library (UPDATE)
- [ ] **Rename "Blog" to "Resource Library"** (if accurate)
- [ ] Update "From the Blog" section messaging (see REGIONAL_MESSAGING_GUIDE.md)
- [ ] Add blog nav to bottom of articles
- [ ] Add related articles links at bottom

### Privacy & Legal (UPDATE)
- [ ] **Privacy Policy** — Update short version to reflect what you collect:
  - Home details for rebate calculation
  - Interest in expansion cities
  - How you use each type of data
  
- [ ] Link to full privacy from "Request My City" form

### Analytics Setup
- [ ] Track "City Requested" events (city, region, interests, source)
- [ ] Track "Launch Notification Sent" events (city, count)
- [ ] Track "Post-Launch Conversion" (city, days between request and assessment, conversion Y/N)
- [ ] Build dashboard showing requests by city/region (to prioritize launches)

---

## PHASE 2: Ontario Setup (When you return with research)

### Ontario Research (You'll do this)
- [ ] Identify top 5 cities to launch (by demand from "Request My City" form)
- [ ] Research Ontario rebate programs:
  - Provincial programs (amounts, eligibility)
  - Utility-specific programs (name format: "[Utility] Rebate")
  - Federal incentives (clean energy tax credit amounts)
  - Local incentives (if any)
- [ ] Research Ontario utilities (Hydro One, Toronto Hydro, others in your target cities)
- [ ] Research installer certification (Ontario equivalent to HPCN)
- [ ] Identify 2-3 vetted installers per city (focus on top 3 cities first)
- [ ] Get installer case studies (2+ per installer)

### Create Ontario City Pages & Guides
- [ ] Use ONTARIO_CITY_PAGE_TEMPLATE.html as starting point
- [ ] Fill in:
  - City name
  - Total available rebates
  - Utility name + amounts
  - Provincial program name + amounts
  - Federal incentive amounts
  - Local incentives (if any)
  - Temperature data for your city
  - Installer details (2-3 per city)
  - Vetting criteria (Ontario-specific)

- [ ] Create Ontario city guides (mirror BC structure, Ontario-specific data)

### URL Structure
- [ ] Create `/ca/on/toronto`, `/ca/on/ottawa`, etc. (start with top 3-5)
- [ ] Create `/ca/on/toronto-heat-pump-guide` guides (to match BC structure)

### Email Campaign
- [ ] Send launch notification to all Toronto requesters
- [ ] Include: rebate amounts, installer options, link to city page
- [ ] Track conversion: How many requesters complete assessment after launch?

### Content
- [ ] Create "Ontario Heat Pump Rebates Explained" guide
- [ ] Create Ontario utility comparison (if applicable)
- [ ] Create comparison post: "Heat Pump ROI: BC vs Ontario" (show payback difference)

---

## PHASE 3: California Setup (When you return with research)

### California Research (You'll do this)
- [ ] Identify top 3 cities (LA, SF, San Diego likely)
- [ ] Research California incentives:
  - IRA federal tax credit (30% of cost, up to $3,500 typical)
  - State programs (if any)
  - Utility-specific rebates (LADWP, SCE, PG&E, etc.)
  - Local incentives (city-specific)
- [ ] Research installer certification (NECA or equivalent)
- [ ] Identify 2-3 vetted installers per city
- [ ] Get installer case studies + references

### Create California City Pages & Guides
- [ ] Use ONTARIO_CITY_PAGE_TEMPLATE.html as starting point (adapt for CA)
- [ ] Fill in:
  - City name
  - Utility name + rebate amounts
  - IRA tax credit information
  - State programs (if any)
  - Local incentives
  - Climate/temperature data
  - Installer details (2-3 per city)
  - Vetting criteria (California-specific: permitting expertise, etc.)

### URL Structure
- [ ] Create `/us/ca/los-angeles`, `/us/ca/san-francisco`, `/us/ca/san-diego`
- [ ] Create corresponding guides

### Content
- [ ] Create "California Heat Pump Incentives Explained" guide
- [ ] Create IRA tax credit explainer
- [ ] Create comparison post: "Heat Pump ROI: BC vs Ontario vs California"

---

## ONGOING: Tracking & Optimization

### Weekly Tasks
- [ ] Check "requested cities" dashboard
  - Which cities have highest demand?
  - Which regions are you getting requests from (helps prioritize next launches)?
  
- [ ] Monitor installer quotes (quality check)
  - Are installers following "apples-to-apples" format?
  - Any quality issues to address?

- [ ] Review launch email conversion (1 week after launch)
  - Of X requesters, how many completed rebate assessment?
  - If <50%, may indicate city wasn't ready or data mismatched expectations

### Monthly Tasks
- [ ] Analyze regional performance
  - BC: which cities have highest quote acceptance?
  - Ontario (post-launch): which cities converting best?
  - California (post-launch): early performance signals?

- [ ] Update installer network (rotate low performers, add high performers)

- [ ] Refresh blog content (add new posts, update old ones with latest incentive amounts)

### Regional Content Updates (As incentives change)
- [ ] When BC Hydro/FortisBC rebate amounts change → Update all BC city pages
- [ ] When Ontario programs change → Update all Ontario city pages
- [ ] When California incentives change → Update all CA city pages
- [ ] When utilities announce new programs → Create new blog post

---

## Files You've Created

1. **REGIONAL_MESSAGING_GUIDE.md** — Tone rules, term translations, example sections (use for all rewrites)
2. **REQUEST_CITY_FORM.md** — Form HTML, backend schema, email templates, analytics setup
3. **ONTARIO_CITY_PAGE_TEMPLATE.html** — Reusable template for all Ontario city pages (fill in data from your research)
4. **IMPLEMENTATION_CHECKLIST.md** (this file) — Master plan with phases

---

## Ready-to-Use Templates

### Copy Templates (Use these for consistency)

**Ontario City Page Intro (customize):**
> "Most [CITY] homeowners I've talked to are replacing 15+ year old furnaces. A new furnace costs $4–7K with zero rebates. A heat pump costs about the same installed, but Ontario's rebate programs give you $[X]K–$[Y]K back. That cuts your upfront cost to basically zero."

**Installer Card (customize per installer):**
> "[X]+ heat pump installations in [CITY] area. Service area: [Neighborhoods/radius]. Average response time: [X] hours. [Rating if available]."

**Comparison Section (reusable):**
> "Here's what's available to you right now: [Table showing utility rebate, provincial program, federal incentive, local incentive] = Total $[X]K–$[Y]K available"

---

## Success Metrics (Track These)

**BC Phase:**
- [ ] All 14 city pages rewritten (human tone, no AI language)
- [ ] All 14 city guides updated (installer badges, comparison links)
- [ ] About Us page live (mission + your story)
- [ ] "Request My City" form capturing requests (target: 100+ in first week)

**Ontario Phase (post-launch):**
- [ ] 3-5 Ontario cities live with 2-3 installers each
- [ ] Launch email conversion rate >50% (requesters → rebate assessments)
- [ ] Average quote acceptance rate >60% (assessments → quotes accepted)

**California Phase (post-launch):**
- [ ] 2-3 California cities live
- [ ] Requests flowing in (track source: organic vs media vs word-of-mouth)
- [ ] Early conversion data showing viability

---

## Notes for Ontario/California Research

When you come back with research, have:

1. **Rebate Data** (organized by city)
   - Utility name, rebate amount, eligibility
   - State/provincial program name, amount, eligibility
   - Federal incentive amount, eligibility
   - Local incentives (if any)

2. **Installer Data** (2-3 per city)
   - Company name, contact info, service area
   - Certification type (Ontario/California equivalent)
   - Case studies (2+ with before/after and savings data)
   - Response time typical

3. **Vetting Criteria** (Ontario/California specific)
   - Required certification (name)
   - Required experience level
   - Anything region-specific (e.g., CA permitting expertise)

This data plugs directly into the templates you have.

---

## Questions Before You Start?

- Want to batch update BC pages first, or do Ontario research in parallel?
- Should Ontario template get its own code repo, or stay in same Powerrebate folder?
- For "Request My City" dashboard, what platform? (Google Sheets, custom dashboard, etc.?)
