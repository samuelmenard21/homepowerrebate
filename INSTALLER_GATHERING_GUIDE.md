# Installer List Gathering Guide — 14 BC Cities

**Goal:** Build a list of 84–112 HPCN-certified installers (6–8 per city) who do heat pumps, solar, and/or batteries in their service area.

**Timeline:** Start Monday, complete by EOD Tuesday before sending emails Wednesday.

---

## Sources (in order of preference)

### 1. Eguana Map (Best for battery installers)
- **Link:** [eguana.com/installers](https://eguana.com/installers)
- **Why:** Eguana is the recommended battery brand; their partner network is pre-vetted and HPCN-certified
- **How:** Filter by city, extract names, phone, email
- **Coverage:** Typically 2–4 per city

### 2. HomePerformance.ca (HPCN Directory — Official)
- **Link:** [homeperformance.ca/find-a-contractor](https://www.homeperformance.ca/find-a-contractor)
- **Why:** HPCN certification is mandatory by BC Hydro as of June 2026
- **How:** Search by postal code (map each city), export list
- **Coverage:** 3–5 per city typically

### 3. Google Maps (Heat pump + solar installers)
- **Search:** "[City] HPCN certified heat pump installer" or "[City] solar installer"
- **Filters:** 4.5★+ rating, at least 20 reviews
- **Extract:** Name, phone, website, rating, review count
- **Coverage:** 2–4 per city

### 4. BC Hydro Power Smart Contractor List (if available)
- Some BC Hydro programs list pre-approved contractors
- Check: [bchydro.com/powersmart](https://www.bchydro.com/powersmart)

---

## Per-City Process (takes ~30 min per city)

1. **Eguana Map search** → Copy names/contact
2. **HomePerformance.ca search** → Add new names (avoid duplicates)
3. **Google Maps search** → Fill gaps with 4.5★+ local installers
4. **Verification** → Check website/Google for HPCN badge or mention
5. **Add to CSV** → Input into `INSTALLER_LIST_TEMPLATE.csv`

**Target per city:** 6–8 installers minimum

---

## Red Flags (Skip these)

- ❌ Rating < 4.5 stars
- ❌ < 20 reviews (unless very new, then check recent reviews)
- ❌ No response number listed
- ❌ Website dead or hasn't been updated in 2+ years
- ❌ No mention of heat pumps, solar, or batteries on their site
- ❌ Primarily HVAC-only (furnace/AC) without rebate-eligible services

---

## CSV Template

Use `INSTALLER_LIST_TEMPLATE.csv` as your working sheet:

```
City, Installer Name, Company, Phone, Email, Services, Google Rating, HPCN Certified, Source, Notes
```

**Fields to fill:**
- **City:** One of the 14 BC cities
- **Installer Name:** First + last name of owner/contact person
- **Company:** Official company name
- **Phone:** Best phone number to reach them
- **Email:** Email address (if available)
- **Services:** heat pump, solar, battery (pipe-separated: "heat pump|solar|battery")
- **Google Rating:** e.g., "4.8" or "4.5+"
- **HPCN Certified:** yes/no (if website doesn't mention it, mark "unknown" and note in Google search)
- **Source:** "Eguana map" or "HomePerformance" or "Google Maps"
- **Notes:** Anything useful ("Recommended by customer review", "Specializes in solar", "Fast response")

---

## Daily Targets

- **Monday:** Abbotsford, Burnaby, Chilliwack, Fort St. John, Kamloops (40–50 installers)
- **Monday evening:** Kelowna, Nanaimo, Penticton, Prince George (35–40 installers)
- **Tuesday morning:** Squamish, Surrey, Vancouver, Vernon, Victoria (30–35 installers)
- **Tuesday EOD:** Review, remove duplicates, verify contacts

**Total:** 84–112 installers across 14 cities

---

## Tips for Speed

1. **Bulk search:** Open 3 tabs (Eguana, HomePerformance, Google Maps) side-by-side
2. **Copy-paste to CSV:** Export HomePerformance results directly into Excel/Google Sheets
3. **Duplicate check:** Use Excel's "Remove Duplicates" before sending
4. **Phone format:** Standardize (e.g., "604-555-1234" not "604.555.1234")
5. **Email verification:** Quick Google search if email is missing
6. **Two-pass approach:** Monday = gather all names. Tuesday = verify and clean.

---

## Output

When done, you'll have:

- CSV file with 84–112 rows (cities × installers)
- All contacts verified (4.5★+, HPCN or heat pump/solar capable)
- Phone and email for 100% of entries
- Services listed per installer
- Ready to merge into email template for sending Wednesday

---

## Delivery

Save as: `/INSTALLER_LIST_FINAL.csv`

Then use for email merge:
- Subject: Personalize `[City]`
- Body: Personalize `[Name]`, `[City]`
- Preview link: Same for all (`/partners/preview`)
- Send via: Gmail, Mailchimp, or your email tool

---

## Questions During Research?

- **"Are they HPCN certified?"** → Check website or HomePerformance directory. If uncertain, include in email — they'll self-identify.
- **"Do they do solar + heat pump?"** → Google search "[company name] solar heat pump" to confirm.
- **"Old phone number/website?"** → Use current info from Google Maps (more up-to-date than their own site often).
- **"Duplicate names (same person, different companies)?"** → Include both if they operate under different entities.

---

**Go. Start with Eguana. You'll have the list done by Tuesday EOD.**
