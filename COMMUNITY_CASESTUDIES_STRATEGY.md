# Community Case Studies: Building Social Proof Through Real Homeowners

## Why Community Matters

- **Trust:** "Someone like me did this in my city" → conversion boost
- **Proof:** Real numbers (costs, savings, timeline) beat generic marketing
- **Local validation:** Case study from Vancouver > national average
- **Installer credibility:** "Here's the actual work we did" > testimonial

## What to Collect

### Minimum (for every install)
```
Homeowner name (or "Sally V., Vancouver")
City
Upgrade type (solar only / heat pump only / combo)
Total cost before rebates
Total rebates received ($)
Monthly savings (estimated year 1)
Timeline (quote to installation)
Quote: "One sentence about why they did it"
Photo: Before/after roof (or family in front of house)
```

### Ideal (for featured stories)
```
[Minimum above, plus:]
Age/stage of life ("Retired, 62" or "Young family, 2 kids")
What problem they were solving ("High heating bills" / "Outages during storms")
Their hesitation going in ("Cost seemed high" / "Worried about complexity")
How installer helped ("They handled everything" / "Explained options clearly")
Payback timeline ("Paid for itself in 8 years, then 25+ years of free power")
Second photo: Install day or dashboard screenshot
Video option: 30-second testimonial (optional, high trust)
```

---

## Collection Methods

### Method 1: Post-Install Email (EASIEST - do first)
When install is complete, installer sends homeowner:

**Subject:** "Your installation is complete—help us celebrate with a case study"

**Email:**
```
Hi [Name],

We just installed your [solar/heat pump/combo] system. Congratulations!

To help other homeowners in [City] see what's possible, we'd love to feature 
your story on HomePowerRebate. It only takes 5 minutes:

[LINK to 5-question form below]

We'll use your first name + city (unless you'd prefer "Anonymous"). 
You'll see your story go live in 1-2 weeks.

Typical response: "I saved $3,000 in year 1, and I'm so glad we did this."

Thanks for helping spread the word!
[Installer name]
```

**5-Question Form (on website: /share-your-story or similar)**
1. Your first name + city (or stay anonymous)
2. What did you install? (solar / heat pump / both / battery / water heater)
3. What made you decide to do this? (1-2 sentences)
4. What surprised you most? (1-2 sentences)
5. Monthly savings estimate, year 1? (or "Not sure yet, still monitoring")

OPTIONAL:
6. Upload: Before photo (roof or home)
7. Upload: After photo (if different)
8. Quote: Would you recommend this? (1 sentence)

**Incentive:** "Featured case studies get a $50 Amazon card" (or credit toward warranty extension)

---

### Method 2: City Page Community Section (Medium effort)

Add to bottom of each city page:

```
# Real Stories from [City]

## Featured This Month

[CASE STUDY CARD 1]
Photo + Name + "Solar + Battery, installed May 2024"
Quote: "Went from $200/month electric to nearly zero"
Impact: "$2,400 year-1 savings, $5K in rebates"
[LINK: Read full story →]

[CASE STUDY CARD 2]
Photo + Name + "Heat pump retrofit, installed March 2024"  
Quote: "Oil heat was costing us $4K/year. Now $800."
Impact: "$3,200 year-1 savings, $12K rebate applied"
[LINK: Read full story →]

---

Submit your story →
Did you get solar, a heat pump, or battery installed in [City]? 
We'd love to share your story. [LINK: Tell your story →]
```

**Why this works:**
- Local proof (Vancouver homeowners see Vancouver stories)
- Real numbers (costs, savings, timelines)
- Photo + name builds credibility vs. anonymous testimonial
- Drives more submissions (seeing others → "I should share too")

---

### Method 3: Installer Partnership (Ongoing)

When you recruit installers, include in contract:

**Installer Obligations:**
- Provide homeowner contact info (with permission) for case study outreach
- Share 2-3 case studies per month (photos + basic data)
- Verify numbers (cost, rebates, timeline) for accuracy

**What you do:**
- Write up polished case study (installer provides facts, you do copywriting)
- Feature on website + city pages
- Credit installer: "Installed by [Installer Name], [City]"
- Link installer name → their intake form (lead generation for them)

**Incentive for installer:**
- Each featured case study = traffic back to their intake form
- Installers love this (social proof for their own sales)

---

## Where Case Studies Live

### 1. Individual City Pages (PRIMARY)
Show 2-3 featured community stories per city
Example: `/ca/bc/vancouver/` has 3 Vancouver stories

### 2. Dedicated Community Page
Create: `/community` or `/homeowner-stories`

Archive of ALL stories by city, upgrade type, savings amount
Sortable: "Most savings" / "Fastest payback" / "Best quote" / "Newest"
Searchable: Filter by "Vancouver" + "Solar" to see all relevant stories

### 3. Homepage Carousel (OPTIONAL)
Top of page below hero: rotate 3 random recent stories
"Real homeowners in BC just like you..."

---

## Data Model for Case Studies

```
{
  id: "story-001",
  homeowner_name: "Sally V.",
  city: "vancouver",
  install_date: "2024-05-15",
  upgrade_type: ["solar", "battery"],  // can be multiple
  
  before_cost_monthly: 215,
  after_cost_monthly: 50,
  year1_savings: 1980,
  
  total_cost: 28500,
  provincial_rebate: 4000,
  federal_rebate: 12000,
  local_rebate: 1000,
  total_rebates: 17000,
  net_cost: 11500,
  
  payback_years: 5.8,
  
  homeowner_quote: "Went from $200/month electric to nearly zero",
  why_decided: "High bills + worried about outages in winter storms",
  surprise_factor: "How quickly the installer got everything done",
  
  installer_id: "installer-van-001",
  installer_name: "Sunlight Solar Vancouver",
  
  photos: [
    { type: "before", url: "/img/stories/001-before.jpg" },
    { type: "after", url: "/img/stories/001-after.jpg" }
  ],
  
  featured: true,
  featured_date: "2024-07-01",
  
  video_url: null,  // optional
  
  created_at: "2024-06-20",
  verified: true,
  verified_by: "installer_confirmation"
}
```

---

## Implementation Timeline

### Month 1: Collection Setup
- [ ] Create `/share-your-story` form (5-minute submission)
- [ ] Set up email workflow (post-install auto-email to homeowners)
- [ ] Create data structure (JSON or database) for stories
- [ ] Design case study card component

### Month 2: Launch + First Stories
- [ ] Installer #1 provides 3 case studies
- [ ] You write them up + add to website
- [ ] Feature on Vancouver + Kelowna pages (highest volume)
- [ ] Email installers: "You're featured!" (social proof)

### Month 3: Scale
- [ ] Aim for 2-3 new stories per week
- [ ] Add "Community" page with all stories
- [ ] Start sorting by "most savings", "fastest payback"
- [ ] Create monthly "Story of the month" email to newsletter

### Month 6: Leverage
- [ ] 40-50 stories across 14 cities
- [ ] Average 3-4 stories per city (builds local trust)
- [ ] Installers competing to get their work featured
- [ ] Stories drive conversion: "People like me in my city did this"

---

## Sample Story (Template)

**Headline:** "From $215/month to $50: How Sally Saved $2,000 in Year One"

**City:** Vancouver | **Install Date:** May 2024 | **System:** 8kW Solar + 10kWh Battery

**The Story**

Sally was tired of watching her electric bills climb every summer. "I hit $215 one month," she recalls. "And I was worried about the winter storms—we had three outages last year. I wanted peace of mind."

After researching her options, she decided to combine solar panels with a home battery. "The $5,000 solar rebate from BC Hydro made sense," she says. "And the heat pump rebate I didn't even know existed."

**The Numbers**

- System cost: $28,500
- Provincial rebates: $4,000
- Federal rebate: $12,000  
- Local Vancouver incentives: $1,000
- **Net cost: $11,500**
- **Year 1 savings: $1,980**
- **Payback: 5.8 years**
- **Year 11+: Free power for life of system**

**What Surprised Her**

"Installation took just 3 days. I thought it would be chaos. The [Installer Name] team was professional and clean. They handled ALL the paperwork—the rebate applications, the utility coordination, everything."

The battery during that winter's ice storm? "We didn't even notice the outage. Fridge kept running, heat stayed on. Worth it just for the peace of mind."

**Sally's Advice**

"Don't wait. The rebates are real, the savings are real, and the technology is proven. If I can do this, anyone can."

---

**Installed by:** [Installer Name] — Vancouver  
[LINK: Get a free quote from the same installer →]

---

## Expected ROI

**Time investment:** 2-3 hours per story (collect info → write → format → add photos)

**ROI per story:**
- Installer gets leads back (direct value: $1-5K per qualified lead)
- Website gets unique local content (SEO value: $500-2K per city)
- Conversion uplift: Featured stories show 15-25% higher conversion (measured via analytics)

**At scale (50 stories):**
- 14 cities with strong local proof = competitive moat
- Installers compete to provide cases (free social proof)
- Homeowners see neighbors they trust = higher conversion
- SEO: "[City] solar stories" = new keyword ranking opportunity

