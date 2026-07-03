# How to Deploy City Pages with Local Elements

## What You Now Have

1. **CITY_PAGE_TEMPLATE.html** — Reusable template with all sections
2. **vancouver/city_page_enhanced.html** — Fully populated example
3. **CITY_ELEMENTS_BY_CITY.md** — Local data for all 14 cities
4. **INSTALLER_BRIEF.md** — To get installer confirmation of local data

---

## Quick Deployment (2-3 hours for all 14 cities)

### Step 1: Copy Template (5 minutes)
1. Open `CITY_PAGE_TEMPLATE.html`
2. For each city, copy this entire file
3. Save as `/ca/bc/[city_name]/city_page_enhanced.html`

### Step 2: Fill in Local Data (15 minutes per city)
Use `CITY_ELEMENTS_BY_CITY.md` to find city-specific data:

**Find/Replace in each file:**
```
[CITY] → Kelowna (or Victoria, etc.)
[BC Hydro / FortisBC] → BC Hydro (from guide)
[X peak sun hours/day average] → 5.0 (from guide)
[Local context note] → Copy from guide
[LOCAL INCENTIVE 1] → Solar Property Tax Exemption (from guide)
[LOCAL INCENTIVE 2] → City heat pump grant (from guide)
[LOCAL INCENTIVE 3] → Expedited permitting (from guide)
[X-X weeks typical] → 6-10 weeks (from guide)
```

### Step 3: Customize FAQ (10 minutes per city)
Update the 5 FAQ questions with city-specific context:
- "Will solar work in [CITY]?" — Use sun hours and local context
- "What's the real cost in [CITY]?" — Use typical cost estimates
- "Why heat pump?" — Reference common heating system in that city
- "Condos?" — Note if city has strata programs
- "When apply?" — Reference local permitting timeline

### Step 4: Deploy (1 minute per city)
Replace current city page with the enhanced version:
```bash
cp city_page_enhanced.html /ca/bc/[city]/index.html
```

---

## City Deployment Checklist

### Tier 1: Highest Priority (Do First)
- [ ] Vancouver (biggest market, most search traffic)
- [ ] Kelowna (strong market, clear local data)
- [ ] Victoria (large, clear incentives)

### Tier 2: Mid-Priority (Do Next)
- [ ] Burnaby
- [ ] Surrey
- [ ] Kamloops
- [ ] Nanaimo

### Tier 3: Complete the Set
- [ ] Chilliwack
- [ ] Abbotsford
- [ ] Vernon
- [ ] Penticton
- [ ] Squamish
- [ ] Prince George
- [ ] Fort St. John

---

## Time Estimate

- **Templates + copy:** 1 hour
- **Fill city data:** 15 min × 14 = 3.5 hours
- **Customize FAQ:** 10 min × 14 = 2.3 hours
- **Deploy to live site:** 15 minutes
- **Total:** ~7 hours for all 14 cities

**Or do it in phases:**
- Week 1: Top 3 cities (1.5 hours)
- Week 2: Next 5 cities (2.5 hours)
- Week 3: Remaining 6 cities (2.5 hours)

---

## What Each City Page Now Shows

✓ Local utility (BC Hydro vs FortisBC)
✓ Local weather data (peak sun hours)
✓ Common home types in that city
✓ Common heating systems
✓ Grid reliability notes
✓ **3-5 local incentives specific to that city**
✓ Real permitting timelines for that city
✓ Income-qualified heat pump tiers
✓ City-specific FAQ answers
✓ CTA to local installer

---

## Sample Variations (From Guide)

### Vancouver
- Utility: BC Hydro
- Sun: 3.5/day (cloudy)
- Incentive #1: Solar tax exemption
- Incentive #2: Strata programs
- Incentive #3: Expedited permitting (2-3 weeks)

### Kelowna
- Utility: BC Hydro
- Sun: 5.0+/day (sunniest)
- Incentive #1: City heat pump grant
- Incentive #2: Solar tax exemption
- Incentive #3: Reduced electrical inspection fees

### Penticton
- Utility: BC Hydro
- Sun: 5.0+/day (sunniest interior)
- Incentive #1: Heat pump rebates
- Incentive #2: Solar tax exemption
- Incentive #3: Oil-to-heat-pump conversion incentive

---

## FAQ Content by City Type

### Cloudy Coast Cities (Vancouver, Victoria, Squamish, Nanaimo)
**"Will solar work here?"**
- "Yes, but you get fewer peak hours than interior. [X] peak sun hours/day. Winter production is lower, but summer is strong. Combined with heat pump and battery, you achieve energy independence."

### Sunny Interior Cities (Kelowna, Penticton, Vernon, Kamloops)
**"Will solar work here?"**
- "Absolutely. [X] peak sun hours/day makes [City] one of BC's best solar markets. Payback is 6–8 years, fastest in the province."

### Cold Northern Cities (Prince George, Fort St. John)
**"Why do I need a heat pump?"**
- "Your winters are harsh. Heat pumps work down to -15°C and cut heating costs by 50-70%. They're extremely attractive in [City]'s climate."

### Oil Heating Common (Kelowna, Penticton, interior areas)
**"Do I need a heat pump?"**
- "If you have an oil furnace, yes. Oil heating is expensive. Heat pump rebates are substantial, and you'll save significantly on fuel costs."

---

## Installer Confirmation Workflow

**After you deploy city pages:**

1. Send INSTALLER_BRIEF.md to local installer
2. Ask them to confirm/correct:
   - Local incentives listed
   - Permitting timeline
   - Typical costs
   - Any local "hacks"

3. They provide:
   - 2-3 case studies with photos
   - Local insights
   - Contact info

4. You update their section on the city page with their name + projects

---

## Next Steps After Deployment

1. **Week 1:** Deploy to live site
2. **Week 2:** Send INSTALLER_BRIEF.md to installers
3. **Week 3:** Start getting installer responses
4. **Week 4:** Add case studies + installer contact info to city pages
5. **Month 2:** Monitor traffic, leads, and Google rankings

---

## SEO Boost from Local Pages

Once deployed, these city pages will rank for:
- "[City] solar rebate"
- "[City] heat pump cost"
- "[City] solar installer"
- "[City] home energy retrofit"
- "[City] battery rebate"

Each city page becomes a SEO asset. 14 pages × strong local keywords = huge organic traffic opportunity.

---

## Files You Have Ready

All these files are in `/Users/sammenard/Downloads/Powerrebate/`:

- `CITY_PAGE_TEMPLATE.html` — Copy this for each city
- `ca/bc/vancouver/city_page_enhanced.html` — Example (use as reference)
- `CITY_ELEMENTS_BY_CITY.md` — Data for all 14 cities (copy/paste from here)
- `INSTALLER_BRIEF.md` — Email to installers
- `DEPLOY_CITY_PAGES.md` — This file (step-by-step)

---

## Go Live Timeline

- **Today/Tomorrow:** Deploy top 3 cities (1.5 hours)
- **Within 1 week:** All 14 cities live (7 hours total)
- **Week 2:** Send installer briefs
- **Weeks 3-4:** Get installer responses + add case studies
- **Month 2+:** Watch organic traffic grow from local keywords

You're ~7-8 hours of work away from 14 fully localized city pages that will dominate local search.
