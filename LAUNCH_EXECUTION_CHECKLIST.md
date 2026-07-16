# HomePowerRebate BC Launch — Final Execution Checklist

**Goal:** Launch BC installer network (14 cities × 1 installer each = 14 signed partners at $300/month) within 2 weeks.

**Timeline:** Installer emails send Tuesday. Close by Friday EOW. Live Week 2.

---

## COMPLETED ✅

- [x] **Homepage updates** — 5 new sections added (calculator hero, quick wins, installer spotlight, case studies, blog feed)
- [x] **Blog posts published** — 2 cornerstone posts live:
  - Heat Pump Rebates by Income (heat-pump-rebates-income-tiers-bc-2026)
  - BC Ended Net Metering (bc-net-metering-ended-self-generation-rate-2026)
- [x] **/partners page updated** — Messaging corrected to $300/month in year 1, marketing features emphasized, GMB integration highlighted
- [x] **Cold email templates** — 14 city variations ready (3 samples + formula for remaining 11)
- [x] **Installer gathering guide** — Complete roadmap (Eguana map, HomePerformance.ca, Google Maps sources)
- [x] **Data verified** — bc.json complete with all verified amounts (BC Hydro, FortisBC, income tiers, utility routing)

---

## IN PROGRESS 🔄

### Build Installer List (Mon–Tue EOD)
- [ ] **Monday morning:** Start with Eguana map (https://eguana.com/installers)
  - Extract Kelowna, Nanaimo, Victoria, Penticton installers (battery focus)
  - Target: 3–4 per city
- [ ] **Monday afternoon:** HomePerformance.ca (heat pump certified)
  - Search: https://www.homeperformance.ca/find-a-contractor
  - Filter each city, extract 3–4 per city
- [ ] **Monday evening:** Google Maps (heat pump + solar 4.5★+)
  - Search: "[City] HPCN heat pump installer"
  - Fill gaps to 6–8 per city
- [ ] **Tuesday morning:** Deduplication + verification
  - Remove duplicates in `INSTALLER_LIST_FINAL.csv`
  - Verify phone/email for all 84–112 entries
- [ ] **Tuesday EOD:** Ready to send

**Target:** 84–112 installers across 14 cities, CSV file ready by 4pm Tuesday

### Cold Email Blitz (Tue 9am – Fri 5pm)
- [ ] **Tuesday 9am:** Send Tier A cities (Kelowna + Vancouver + Burnaby + Surrey + Victoria = 30–40 emails)
- [ ] **Tuesday 10am–12pm:** Send Tier B cities 1 (Nanaimo + Abbotsford + Chilliwack + Kamloops + Penticton = 20–25 emails)
- [ ] **Tuesday 2pm–4pm:** Send Tier C cities (Fort St. John + Prince George + Squamish + Vernon = 15–20 emails)
- [ ] **Total sent by Tuesday EOD:** 84–112 emails
- [ ] **Wednesday–Thursday:** Monitor responses (texts to 905-320-5091 + samuelmenard@gmail.com)
- [ ] **Thursday:** Follow-up calls to "interested" responses (14–21 potential closes)
- [ ] **Friday EOW:** Target 10–14 signed agreements at $300/month founding rate

**Success metric:** At least 1 installer per city signed (14 total) by Friday 5pm

---

## READY TO LAUNCH (Pre-Tuesday)

### QA Checklist (Do Tuesday morning)
- [ ] Homepage loads (desktop + mobile)
- [ ] All 5 new sections render correctly
- [ ] Calculator link works (/calculator loads)
- [ ] Blog links work (both new posts accessible)
- [ ] /partners page displays correctly
- [ ] /partners/preview page loads (watermarked, noindex)
- [ ] All CTAs point to correct URLs
- [ ] No broken links on homepage

### Content Audit (Do Tuesday morning)
- [ ] Homepage hero messaging mentions "14 BC cities"
- [ ] Calculator hero section present and visible
- [ ] Blog feed section links to correct blog posts
- [ ] Installer of the Week card displays properly
- [ ] Case studies section formatted correctly
- [ ] Quick Wins cards all visible (thermostats, energy kit, ECAP)

### Data Integrity (Do Tuesday morning)
- [ ] No hardcoded rebate amounts on homepage (all pull from bc.json)
- [ ] FortisBC vs BC Hydro distinction clear on city pages
- [ ] Income tier messaging correct (if displayed)
- [ ] Calculator branching works (city → utility → heating fuel → results)

---

## TUESDAY EMAIL BLITZ — EXECUTION STEPS

### Morning Prep (8am–9am)
- [ ] Open `INSTALLER_LIST_FINAL.csv`
- [ ] Open Gmail or Mailchimp
- [ ] Open `COLD_EMAIL_TEMPLATES_BY_CITY.md`
- [ ] Set up phone + email monitoring
- [ ] Test send 1 email to yourself

### Send Batches (9am–4pm)
**Batch 1 (9am–10am):** Kelowna + Vancouver
- [ ] Send 6–8 Kelowna emails
- [ ] Send 8–10 Vancouver emails
- [ ] Log sends in `INSTALLER_RESPONSES.csv`

**Batch 2 (10am–11am):** Burnaby, Surrey, Victoria
- [ ] Send 6–8 Burnaby emails
- [ ] Send 6–8 Surrey emails
- [ ] Send 5–7 Victoria emails

**Batch 3 (11am–12pm):** Nanaimo, Abbotsford, Chilliwack
- [ ] Send 4–6 Nanaimo emails
- [ ] Send 4–6 Abbotsford emails
- [ ] Send 3–5 Chilliwack emails

**Lunch (12pm–2pm)**

**Batch 4 (2pm–3pm):** Kamloops, Penticton, Fort St. John
- [ ] Send 4–6 Kamloops emails
- [ ] Send 3–5 Penticton emails
- [ ] Send 2–4 Fort St. John emails

**Batch 5 (3pm–4pm):** Prince George, Squamish, Vernon
- [ ] Send 3–5 Prince George emails
- [ ] Send 2–4 Squamish emails
- [ ] Send 3–5 Vernon emails

**EOD (4pm–5pm):**
- [ ] Verify all 84–112 emails sent
- [ ] Log total sent count
- [ ] Set phone alerts active
- [ ] Share "emails sent" update with yourself / team

---

## RESPONSE TRACKING (Wed–Fri)

### Incoming Responses Log
Create `INSTALLER_RESPONSES.csv`:
```
Name, Company, City, Phone, Email, Response Date, Response Type, Status, Notes
```

**Response types:**
- `TEXT_YES` = Interested (text reply to 905-320-5091)
- `EMAIL_YES` = Interested (email reply)
- `CALL_INTERESTED` = Called in directly
- `EMAIL_MAYBE` = "Tell me more" / hesitant
- `NO_REPLY` = No response (follow up Friday)
- `UNSUBSCRIBE` = Not interested

**Status:**
- `INTERESTED` = Ready to talk
- `MAYBE` = Needs follow-up
- `CLOSED` = Signed agreement
- `DECLINED` = Not moving forward

---

## PHONE CALLS (Thu–Fri)

### Call Script (for "Interested" responses)

**Opening:**
"Hi [Name], thanks for texting! Great to hear you're interested. I wanted to give you a quick overview of how this works."

**The pitch (60 seconds):**
"Here's the deal: homeowners come to our calculator, see their personalized rebate and monthly savings, and ask to be matched with an installer in their city. That installer is you. Exclusively. You get every qualified lead in [City]. We handle all the marketing — homepage feature, email to 2,000+ subscribers, social media, blog spotlights. You handle the install. $300/month, first month free, cancel anytime."

**If they ask about leads:**
"We're early. First month is free so you can prove it works yourself. But the marketing features are guaranteed day one — homepage, email, social, blog. That's thousands in marketing value if you were buying ads."

**If they hesitate:**
"No contract. Cancel anytime. What do you have to lose? First month is free."

**Close:**
"Want to lock in the $300/month founding rate? I can send you the paperwork right now."

---

## CLOSING (If YES on call)

**What to ask for:**
- [ ] Their full legal name + company name
- [ ] Google My Business URL (so we can pull ratings/reviews)
- [ ] 3 best before/after project photos (email or Google Drive link)
- [ ] 30-sec video intro (optional but helps)
- [ ] Preferred contact email for lead notifications

**What to send them:**
1. Link to /partners (full terms)
2. Simple 1-page agreement:
   - City: [City]
   - Service: Heat pump, solar, battery (or subset)
   - Rate: $300/month
   - Start date: [Date]
   - First month free through [Date + 30 days]
   - Auto-renew, cancel anytime with 30 days notice
3. Lead dashboard login info (if built)
4. Onboarding checklist

**Timeline to live:**
- Thursday: Sign agreement
- Friday–Monday: Upload photos/video, profile live by Tuesday

---

## WEEK 2 EXECUTION (If 10+ installers signed)

- [ ] Upload photos, videos, GMB links to each city page
- [ ] Generate profiles for each installer
- [ ] Update "Installer of the Week" rotation (or manual feature first week)
- [ ] Send email to your list: "Kelowna, Vancouver, Burnaby installers now live"
- [ ] Post on Reddit (r/BC, r/Vancouver, r/Kelowna, etc.)
- [ ] Social media announcement (Instagram, LinkedIn if you have accounts)
- [ ] Monitor incoming leads, route to installers

---

## SUCCESS METRICS

### This Week (by Friday 5pm)
- [ ] 84–112 emails sent ✅
- [ ] 20–30 responses (text + email) — **target**
- [ ] 14–21 phone calls scheduled — **target**
- [ ] 10–14 installers signed — **minimum success**
- [ ] First installer profiles live — **ideal**

### By End of Month
- [ ] 14 installers live (one per city)
- [ ] 14 × $300/month = $4,200 MRR target
- [ ] First leads flowing to installers
- [ ] Installer retention (no cancellations)

---

## FAILURE MODES (If not hitting targets)

**If <10 responses by Wed EOD:**
- Follow-up email batch Thursday morning (different subject, urgency angle: "only 3 spots left at $300/month")

**If <8 signed by Friday:**
- Extend timeline to following week (don't drop price)
- Focus on top 5 cities (Vancouver, Kelowna, Burnaby, Victoria, Nanaimo)
- Quality > quantity

**If installers drop after signing:**
- Follow-up call within 48 hours
- Debug: Ask what's needed to make it work
- Don't lose them to objections

---

## DOCUMENTS READY TO USE

- `INSTALLER_LIST_TEMPLATE.csv` — Start here, fill in Monday
- `INSTALLER_GATHERING_GUIDE.md` — Instructions for gathering names
- `COLD_EMAIL_TEMPLATES_BY_CITY.md` — Copy-paste ready templates
- `INSTALLER_PITCH_EMAIL_WITH_PREVIEW.txt` — Original template (reference)
- `/partners/preview` — Live preview page (link in all emails)
- `/partners` — Full terms page (link in follow-ups)
- `/calculator` — Proof of concept (link in case they ask about lead quality)

---

## FINAL CHECKLIST (Tuesday 8am)

- [ ] Installer list finalized (CSV file ready)
- [ ] Email templates printed/copied
- [ ] Phone alerts on (905-320-5091)
- [ ] Email inbox cleared (ready to catch responses)
- [ ] Homepage tested (all sections working)
- [ ] Blog posts live and linked
- [ ] /partners page live
- [ ] /partners/preview watermarked and live
- [ ] Calculator working
- [ ] First batch of 30–40 emails ready to send

**Status: READY TO LAUNCH**

Send first email at 9am Tuesday. Track responses. Close installers Thu–Fri. Go live Week 2.

---

## SUCCESS LOOKS LIKE

**Friday 5pm:**
- ✅ 100+ emails sent
- ✅ 20–30 responses collected
- ✅ 14–21 phone calls completed
- ✅ 10–14 signed agreements
- ✅ First 3–5 profiles live on city pages
- ✅ First installers telling friends

**Week 2:**
- ✅ 14 installers live across BC
- ✅ "Installer of the Week" rotating weekly
- ✅ First 5–10 leads flowing
- ✅ Social proof accumulating
- ✅ Ready to expand to Ontario

---

**GO. SEND TUESDAY MORNING.**
