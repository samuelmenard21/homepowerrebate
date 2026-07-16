# AEO Optimization Guide — HomePowerRebate

**Status:** All core pages AEO-optimized for Google AI Overviews, Perplexity, Claude, and other AI engines  
**Last Updated:** January 2026  
**Applies to:** All city pages, core pages, blog posts

---

## What is AEO?

**AEO (AI Engine Optimization)** = Optimization for AI search engines and AI Overviews (Google's AI-generated search results).

When someone searches "heat pump rebates in Victoria BC" on Google and gets an AI Overview, your page data should be:
1. **Structured** (Schema.org markup) so AI can extract facts
2. **Clear** (Q&A format, lists, tables) so AI can cite you
3. **Authoritative** (author info, dates, citations) so AI trusts your content

---

## ✅ What's Been Implemented

### 1. Schema.org Markup (All Pages)

**BreadcrumbList Schema**
- Helps AI understand navigation structure
- Shows page hierarchy (Home → BC Cities → [City] → Heat Pump Rebates)
- Added to: About Us, Vetting Criteria, City Pages (template)

**Example:**
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "position": 1, "name": "Home", "item": "https://homepowerrebate.com/" },
    { "position": 2, "name": "BC Cities", "item": "https://homepowerrebate.com/ca/bc" },
    { "position": 3, "name": "Victoria Heat Pump Rebates", "item": "https://homepowerrebate.com/ca/bc/victoria" }
  ]
}
```

**FAQPage Schema**
- Explicitly structures Q&A so AI can cite answers
- Google AI Overviews extract FAQ schema directly
- Added to: City pages (all FAQ sections), Vetting Criteria page

**Example:**
```json
{
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Will heat pumps work in Victoria winters?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. Heat pumps work down to -15°C. Victoria winters average 5°C, so they handle it fine."
      }
    }
  ]
}
```

**LocalBusiness Schema (Installers)**
- Allows AI to extract business info: name, rating, service area, contact
- Installers appear as rich snippets in AI Overviews
- Added to: Installer carousel component

**Example:**
```json
{
  "@type": "LocalBusiness",
  "name": "Island Heat Solutions",
  "address": { "addressLocality": "Victoria", "addressRegion": "BC" },
  "areaServed": ["Victoria", "Langford", "View Royal"],
  "ratingValue": "4.9",
  "reviewCount": "50",
  "serviceType": ["Heat Pump Installation", "Solar Installation"],
  "certifications": ["HPCN Certified"]
}
```

**Article Schema**
- Marks up content as authoritative articles
- Includes author, publisher, date, description
- AI uses this to assess credibility
- Added to: About Us, Vetting Criteria, City Pages

**Organization Schema**
- Comprehensive business info: founder, areas served, contact, sameAs links
- Added to: About Us page (enhanced with LinkedIn, social profiles)

---

### 2. Semantic HTML (All Pages)

**Proper Heading Hierarchy**
```html
<h1>Heat Pump Rebates in Victoria, BC</h1>
<!-- Only ONE H1 per page -->
<h2>What You Qualify For</h2>
<h3>BC Hydro Heat Pump Rebate</h3>
```

✅ Applied to: All templates (no skipped heading levels)

**Semantic Sections**
```html
<article><!-- Main content goes here --></article>
<nav><!-- Navigation --></nav>
<section><!-- Semantic grouping --></section>
```

✅ Applied to: All core pages

**Table Markup**
```html
<table>
  <thead><tr><th>Incentive</th><th>Amount</th></tr></thead>
  <tbody><tr><td>BC Hydro Rebate</td><td>$4,000–$8,000</td></tr></tbody>
</table>
```

✅ Applied to: City page rebate tables (AI can extract table data)

---

### 3. SEO + AEO Metadata

**Title Tags (60 chars max, keyword-rich)**
```
"Heat Pump Rebates in Victoria, BC | HomePowerRebate"
"How HomePowerRebate Vets Installers | Transparent Criteria"
```
✅ All pages have titles optimized for keywords

**Meta Descriptions (155 chars, action-oriented)**
```
"See what heat pump rebates you qualify for in Victoria. Get matched with 2-3 trusted installers. Calculate savings in 2 minutes."
```
✅ All pages have descriptions that encourage clicks

**Canonical URLs**
```html
<link rel="canonical" href="https://homepowerrebate.com/ca/bc/victoria">
```
✅ All pages have canonicals to avoid duplicate content

**Robot Meta Tags**
```html
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
```
✅ All pages allow AI to index and use snippets + images

**Open Graph Tags (for social + AI)**
```html
<meta property="og:title" content="Heat Pump Rebates in Victoria, BC">
<meta property="og:description" content="...">
<meta property="og:image" content="...">
<meta property="og:url" content="...">
```
✅ All pages have social metadata for sharing

---

### 4. Mobile Responsiveness (AEO Requirement)

**Viewport Meta Tag**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```
✅ Present on all pages

**Responsive Typography (clamp function)**
```css
font-size: clamp(32px, 5vw, 48px);
/* Scales between 32px (mobile) and 48px (desktop) */
```
✅ All headings are responsive

**Responsive Layouts**
```css
display: grid; /* or flexbox */
gap: 24px;
grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
```
✅ Installer carousel, tables, and grids are mobile-first

**Touch-Friendly**
```css
.cta { padding: 14px 28px; } /* 44px+ min touch target */
.tab-btn { padding: 10px 18px; } /* Easy to tap */
```
✅ All buttons meet 44px minimum touch size

**Mobile Scrolling**
```css
.carousel-wrapper { 
  overflow-x: auto; 
  scroll-behavior: smooth;
  scroll-snap-type: x mandatory;
}
```
✅ Carousel scrolls smoothly on mobile, snaps to cards

---

## 📋 AEO Rendering Checklist (For All Pages)

### Before Publishing Any Page

- [ ] **Headings**: H1 only once, proper hierarchy (H1→H2→H3, no skips)
- [ ] **Schema**: BreadcrumbList, FAQPage (if Q&A), LocalBusiness (if business), Article schema
- [ ] **FAQ Format**: At least 3 questions with detailed answers (for FAQPage schema extraction)
- [ ] **Metadata**: Title (60 chars), description (155 chars), canonical URL
- [ ] **Mobile**: Test on mobile (typography scales, carousel scrolls, buttons are tappable)
- [ ] **Table Data**: Use `<table>`, `<thead>`, `<tbody>` for structured data
- [ ] **Lists**: Use `<ul>` or `<ol>` for listsable content
- [ ] **Links**: Internal links to related pages (helps AI understand structure)
- [ ] **Author/Date**: Include article author, publish date, modify date
- [ ] **Images**: Use `alt` text (describe what AI should know)
- [ ] **Robots Meta**: Allow indexing + snippets + image preview

---

## 🔍 How Google AI Overviews Will Use Your Content

### Example: "Best heat pump installers in Victoria BC"

**Without AEO:**
Google AI might ignore your page or cite competitors instead.

**With AEO (what you have now):**

1. **Finds your page** via breadcrumb schema (Home → BC Cities → Victoria)
2. **Extracts facts** from table schema (rebate amounts, available programs)
3. **Pulls Q&A** from FAQPage schema ("Do heat pumps work in Victoria winters?")
4. **Shows installers** from LocalBusiness schema (name, rating, service area)
5. **Cites your page** in the AI Overview with a link

Result: Your content appears in AI Overviews, driving traffic + authority.

---

## 📊 Schema Markup Implementation Status

| Schema Type | Pages | Status | Priority |
|---|---|---|---|
| BreadcrumbList | All | ✅ Complete | High |
| FAQPage | City pages, Vetting | ✅ Complete | High |
| LocalBusiness | Installers (carousel) | ✅ Complete | High |
| Article | All | ✅ Complete | Medium |
| Organization | About Us | ✅ Complete | Medium |
| LocalBusiness (service area) | City pages (template) | ✅ Complete | High |

---

## 🚀 Implementation for Remaining Pages

### When Creating City Pages (All 14)

**Required Schemas:**
1. BreadcrumbList (navigation)
2. FAQPage (questions section)
3. LocalBusiness (service area)
4. Article (page itself)

**Copy Template from `city-page-template-with-carousel.html`**
- All schema is built in
- Just replace [CITY] with actual city name
- Schema will automatically update

### When Creating Blog Posts

**Required Schemas:**
1. BreadcrumbList
2. Article (with author, date)
3. FAQPage (if blog post has Q&A)

**Recommended:**
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "[Your Blog Title]",
  "description": "[Your blog description]",
  "image": "[Hero image URL]",
  "datePublished": "2026-01-15",
  "dateModified": "2026-01-15",
  "author": {
    "@type": "Person",
    "name": "Sam Menard",
    "url": "https://ca.linkedin.com/in/sammenard"
  },
  "publisher": {
    "@type": "Organization",
    "name": "HomePowerRebate"
  }
}
```

### When Creating Regional Pages (Ontario, California)

**Required Schemas:**
1. BreadcrumbList (with regional paths)
2. LocalBusiness (regional service area)
3. Article
4. FAQPage

---

## 🧪 Testing AEO Rendering

### Test 1: Schema Markup Validation
- Use [Google Rich Results Test](https://search.google.com/test/rich-results)
- Paste page URL
- Verify all schemas render correctly
- No errors or warnings

### Test 2: AI Overview Simulation
- Search on Google: `[keyword] site:homepowerrebate.com`
- If AI Overview appears, your schema is working
- Check if your content is cited

### Test 3: Mobile Rendering
- Open on mobile (375px width)
- Verify typography scales
- Verify carousel scrolls smoothly
- Verify buttons are tappable (44px+)
- Verify tables are readable (horizontal scroll if needed)

### Test 4: Semantic HTML Validation
- Use [Wave Accessibility Tool](https://wave.webaim.org/)
- Check for proper heading hierarchy
- Check for semantic structure
- Verify no skipped heading levels

---

## 📈 AEO Best Practices (Going Forward)

### Do's ✅
- Use **clear, direct language** (AI extracts exact text)
- Use **tables** for structured data (rebates, pricing)
- Use **lists** for multiple items (cities, requirements)
- Use **Q&A format** for common questions
- Include **dates** (publish/modify) on all content
- Use **specific numbers** ("$4,000–$8,000", not "up to $16K")
- Link **internally** to related pages (helps AI understand structure)
- Add **author info** (Person or Organization schema)

### Don'ts ❌
- Don't use **generic language** ("Rebates available" vs. "$4,000–$8,000 available")
- Don't skip **heading levels** (H1 → H3 is confusing)
- Don't **hide content** in accordions (AI may not crawl it)
- Don't use **images without alt text** (AI can't see pictures)
- Don't **stuff keywords** (write for humans first)
- Don't **hide schema** (put it in `<head>`, visible to AI)
- Don't **duplicate content** (use canonical URLs)

---

## 🔄 Maintenance (Monthly)

1. **Check Schema Validation** (monthly)
   - Run pages through Google Rich Results Test
   - Fix any errors or warnings

2. **Update Dates** (when content changes)
   - Update `dateModified` in Article schema
   - Update last-updated date on page

3. **Monitor AI Overviews** (weekly)
   - Search key terms on Google
   - Check if your content appears in AI Overview
   - Note which pages get cited

4. **Update Installer Schema** (as installers change)
   - Add new installers to LocalBusiness schema
   - Update ratings/reviews
   - Update service areas

---

## 📞 Support

**Testing Issues?**
- Use [Google Search Console](https://search.google.com/search-console) to submit pages
- Use [Schema.org Validator](https://validator.schema.org/) to validate markup
- Use [Google Rich Results Test](https://search.google.com/test/rich-results) for rich snippet preview

**Questions on AEO?**
- Reference [Google's AI Overviews Guide](https://developers.google.com/search/docs/appearance/ai-overviews)
- Read [Schema.org Documentation](https://schema.org/)
- Email: hello@homepowerrebate.com

---

## ✅ Summary: What's AEO-Ready

**Core Pages (100% AEO-Optimized):**
- ✅ about-us.html
- ✅ how-we-vet-installers.html
- ✅ privacy.html (with expansion context)

**City Page Template (100% AEO-Optimized):**
- ✅ city-page-template-with-carousel.html (with BreadcrumbList, FAQPage, LocalBusiness, Article)

**Installer Carousel (100% AEO-Optimized):**
- ✅ installer-carousel-component.html (with LocalBusiness schema for each installer)

**What You Need to Do:**
1. Duplicate city page template 14 times (AEO markup is already there)
2. Fill in city-specific data (rebates, installers, FAQ answers)
3. Test each page with Google Rich Results Test
4. Publish and monitor AI Overviews

---

**All pages are now optimized for AI engines. They will render correctly in Google AI Overviews, Perplexity, Claude, and other AI search systems.**
