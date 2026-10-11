# Installer Onboarding Flow

## Stage 1: Application & Vetting (You)

**Trigger:** Installer emails or books call expressing interest.

**What you do:**
1. Confirm they're HPCN-certified (check registry)
2. Pull their Google My Business rating — must be 4.5+
3. Review recent reviews (any red flags?)
4. Verify they operate in the city (address, service area)

**If they don't meet criteria:**
- Polite decline: "Thanks for your interest. We're looking for partners with 4.5+ ratings. Focus on collecting reviews first, then we'd love to revisit."

**If they meet criteria:**
- Send: Onboarding link (see Stage 2 below)
- Message: "You're approved to become [City]'s preferred installer. Let's get you live in 48 hours."

---

## Stage 2: Installer Self-Setup (Installer Does This)

**Timeline:** 30-60 min for installer to complete

**You send them this sequence:**

### Email 1: Welcome + Action Items

---

**Subject:** Get live as [City]'s preferred installer (1 hour of setup)

Hi [Name],

Welcome! You're approved to be the preferred installer for [City] on HomePowerRebate. Here's how to go live:

**Step 1: Connect your Google My Business (5 min)**
- Go to: [LINK TO GMB AUTH PAGE]
- Sign in with your Google account
- Approve access
- We'll pull your rating, reviews, and photos automatically

**Step 2: Upload 3 before/after photos (10 min)**
- Go to: [INSTALLER DASHBOARD LINK]
- Upload 3-5 best project photos (JPG/PNG, 1-2MB each)
- Add captions (optional): "Heat pump install in [neighborhood]" etc.
- We display these on your profile

**Step 3: Record a 30-60 second video (10 min, optional)**
- Film on your phone: "Hi, I'm [name]. I've been installing heat pumps and solar in [City] for [X] years..."
- Keep it simple: lighting, genuine, no script needed
- Upload to your dashboard (we handle hosting)
- Or skip this — you can add it later

**Step 4: Review & approve (5 min)**
- Check how your profile looks: https://homepowerrebate.com/ca/bc/[city]
- Confirm your Google rating pulled correctly
- Make sure info is accurate

**That's it.** Once approved, you start getting leads immediately (if we have traffic).

**Questions?** Reply here or book a quick call: [CALENDLY LINK]

\- Sam

---

### Email 2: Follow-up (24 hrs later if no response)

---

**Subject:** [City] profile — need your GMB sign-in

Hi [Name],

Just checking in — did you get the setup link? The main thing holding us up is connecting your Google My Business.

Once you sign in (1 click, ~2 min), your profile goes live.

[LINK TO GMB AUTH PAGE]

Thanks,  
Sam

---

### Email 3: Final nudge (if still no response after 48 hrs)

---

**Subject:** One click to go live

Hi [Name],

This is the last nudge — I want to get you live this week. All that's left is one Google sign-in.

[LINK TO GMB AUTH PAGE]

If this isn't the right time, just let me know. No pressure.

\- Sam

---

## Stage 3: Technical Setup (You)

**Trigger:** Installer completes GMB auth + uploads photos

**What you do (backend):**

1. **Pull GMB data**
   - Rating, review count, recent reviews
   - Photos (if they have them)
   - Business hours

2. **Create profile**
   - HTML rendered on /ca/bc/[city]/index.html
   - Replace "Coming soon" with real name
   - Replace placeholder photo with initials avatar (if no photo provided)
   - Display their Google rating + review count
   - Display their uploaded photos in gallery

3. **Set up lead dashboard**
   - Create unique dashboard URL (e.g., https://homepowerrebate.com/dashboard/[installer-id])
   - Database entry: installer name, email, city, GMB ID
   - Lead tracking table (empty to start)

4. **Enable booking**
   - "Get free quote" button on their profile links to their Calendly or booking form
   - Or use Stripe booking (if they want)

5. **Send confirmation**
   - Email installer: "You're live! Here's your dashboard link."
   - Show screenshot of how they appear on the city page

---

## Stage 4: Go Live (You + Installer)

**Email to installer:**

---

**Subject:** You're live as [City]'s preferred installer

Hi [Name],

🎉 You're now live on HomePowerRebate.

**Your profile:** https://homepowerrebate.com/ca/bc/[city]

**Your dashboard:** https://homepowerrebate.com/dashboard/[installer-id]

**What to expect:**
- Your Google rating, reviews, and photos are live
- Homeowners who see you on the page can book direct (via Calendly / your booking link)
- Leads appear in your dashboard in real-time
- You have full control of your availability

**Next steps:**
- Check your profile looks right
- Make sure your booking link works
- Test getting a lead (or have a friend)

**Questions?** Reply to this email or visit your dashboard.

Thanks for being [City]'s preferred installer!

\- Sam

---

**You do:**
- Verify profile renders correctly (check on mobile + desktop)
- Verify Google rating pulled live
- Test "Get quote" button works
- Monitor first 3 days for any bugs

---

## Stage 5: First Lead (Ongoing)

**Trigger:** Homeowner books on installer's profile

**What happens:**
1. Homeowner fills out booking form on installer's Calendly (or your form)
2. Installer receives notification
3. Installer reaches out to homeowner
4. You track: lead generated, quote sent, job won/lost (installer reports)

**Monthly check-in (You):**
- Email installer: "You've received X leads this month, closed Y jobs. How's it going?"
- Ask for feedback: profile, booking flow, lead quality
- Collect testimonials for case studies

---

## Installer Dashboard Features (To Build Later)

- [ ] Real-time lead count
- [ ] Lead details (name, email, phone, service area)
- [ ] Conversion tracker (leads → quotes → jobs)
- [ ] Availability calendar (pause/unpause)
- [ ] Profile editor (update photos, video, availability)
- [ ] Performance stats (response time, close rate)
- [ ] Lead feedback form (quality rating)

---

## Quick Reference: Installer Checklist

**What installer needs to provide:**
- ✓ Google My Business account (we connect via OAuth)
- ✓ 3+ before/after photos
- ✓ Booking link (Calendly, Stripe, or your form)
- ✓ Video intro (optional)

**What you provide:**
- ✓ Live profile on city page
- ✓ Google rating auto-updated
- ✓ Lead dashboard
- ✓ Booking integration
- ✓ Email support

**Timeline:**
- Day 1: Email outreach + approval
- Day 2: Installer completes setup
- Day 3: You enable profile + send live confirmation
- Day 4+: Leads start flowing

---

## FAQ for Installers (Copy This)

**Q: When will I start getting leads?**  
A: Once your profile is live and you're in our search results, leads begin within days. Volume grows as we drive more traffic to the site.

**Q: What if I don't get many leads in the first month?**  
A: We're building traffic through content, Reddit, PR, and video. Early adopters may see fewer leads initially, but they also lock in $300/month forever. We're investing in this.

**Q: Can I control my availability?**  
A: Yes. Your dashboard lets you pause/unpause bookings anytime. You're in control.

**Q: What if a lead is not qualified?**  
A: Tell us. We refine over time. The goal is homeowners actively seeking rebates, not just phone calls.

**Q: Can I add a video intro later?**  
A: Yes. Upload it anytime via your dashboard.

**Q: How do I cancel?**  
A: Month-to-month billing. Cancel anytime, but there's a 30-day notice (so you don't leave mid-month).

**Q: Do you handle rebate filing?**  
A: No. You do (you're HPCN-certified). We connect you with homeowners who want rebates. You close the sale and file the rebate.
