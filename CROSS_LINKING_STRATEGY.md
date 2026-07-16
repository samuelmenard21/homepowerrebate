# Strategic Cross-Linking Strategy — All 14 Cities

This document maps the internal linking web that connects all 14 city guides, city pages, and comparison posts to maximize SEO authority and user navigation.

---

## Linking Structure Overview

### 1. City Guides ↔ City Pages (Bidirectional)

**City Guide → City Page CTA:**
Add at the end of each guide (before "Next Steps" section):
```html
<h2>Ready to see your installer?</h2>
<a href="/ca/bc/[city-slug].html" class="city-link">See [City]'s current installer profile →</a>
```

**City Page → City Guide Link:**
Add at the end of each city page (in footer area or before "Next Steps"):
```html
<p style="margin-top: 28px;"><strong>Want the full guide?</strong> <a href="/blog/[city-slug]-heat-pump-guide">Read [City]'s complete heat pump guide →</a></p>
```

---

### 2. City Guides → Comparison Posts (One-way)

Each guide links to relevant comparison posts. Add this section before "Next Steps":

```html
<h2>Compare [City] to other BC cities</h2>
<p><a href="/blog/kelowna-vs-kamloops-solar-comparison">Kelowna vs Kamloops: Which has better solar?</a></p>
<p><a href="/blog/island-vs-mainland-bc-heat-pump-comparison">Island vs Mainland: Grid resilience comparison</a></p>
<p><a href="/blog/bc-hydro-vs-fortisbc-rebates-comparison">BC Hydro vs FortisBC: Rebate comparison</a></p>
```

---

## City-Specific Linking Map

### BC Hydro Cities (12)

#### Interior Solar Cities (Kelowna, Kamloops)
- **Kelowna Guide** → Links to:
  - `/ca/bc/kelowna` (city page)
  - `/blog/kelowna-vs-kamloops-solar-comparison`
  - `/blog/bc-hydro-vs-fortisbc-rebates-comparison`
  
- **Kamloops Guide** → Links to:
  - `/ca/bc/kamloops` (city page)
  - `/blog/kelowna-vs-kamloops-solar-comparison`
  - `/blog/bc-hydro-vs-fortisbc-rebates-comparison`

#### Lower Mainland Cities (Vancouver, Burnaby, Surrey)
- **Vancouver Guide** → Links to:
  - `/ca/bc/vancouver` (city page)
  - `/blog/island-vs-mainland-bc-heat-pump-comparison`
  - `/blog/bc-hydro-vs-fortisbc-rebates-comparison`

- **Burnaby Guide** → Links to:
  - `/ca/bc/burnaby` (city page)
  - `/blog/island-vs-mainland-bc-heat-pump-comparison`
  - `/blog/bc-hydro-vs-fortisbc-rebates-comparison`

- **Surrey Guide** → Links to:
  - `/ca/bc/surrey` (city page)
  - `/blog/island-vs-mainland-bc-heat-pump-comparison`
  - `/blog/bc-hydro-vs-fortisbc-rebates-comparison`

#### Island Cities (Victoria, Nanaimo)
- **Victoria Guide** → Links to:
  - `/ca/bc/victoria` (city page)
  - `/blog/island-vs-mainland-bc-heat-pump-comparison`
  - `/blog/bc-hydro-vs-fortisbc-rebates-comparison`

- **Nanaimo Guide** → Links to:
  - `/ca/bc/nanaimo` (city page)
  - `/blog/island-vs-mainland-bc-heat-pump-comparison`
  - `/blog/bc-hydro-vs-fortisbc-rebates-comparison`

#### Remaining BC Hydro Cities (Abbotsford, Chilliwack, Penticton, Squamish, Vernon)
- **Abbotsford Guide** → Links to:
  - `/ca/bc/abbotsford` (city page)
  - `/blog/bc-hydro-vs-fortisbc-rebates-comparison`

- **Chilliwack Guide** → Links to:
  - `/ca/bc/chilliwack` (city page)
  - `/blog/bc-hydro-vs-fortisbc-rebates-comparison`

- **Penticton Guide** → Links to:
  - `/ca/bc/penticton` (city page)
  - `/blog/bc-hydro-vs-fortisbc-rebates-comparison`

- **Squamish Guide** → Links to:
  - `/ca/bc/squamish` (city page)
  - `/blog/island-vs-mainland-bc-heat-pump-comparison`
  - `/blog/bc-hydro-vs-fortisbc-rebates-comparison`

- **Vernon Guide** → Links to:
  - `/ca/bc/vernon` (city page)
  - `/blog/bc-hydro-vs-fortisbc-rebates-comparison`

### FortisBC Cities (2)

- **Fort St. John Guide** → Links to:
  - `/ca/bc/fort-st-john` (city page)
  - `/blog/bc-hydro-vs-fortisbc-rebates-comparison`

- **Prince George Guide** → Links to:
  - `/ca/bc/prince-george` (city page)
  - `/blog/bc-hydro-vs-fortisbc-rebates-comparison`

---

## Comparison Posts → All Relevant Cities

### Kelowna vs Kamloops
Links to city guides/pages:
- Kelowna Guide & City Page
- Kamloops Guide & City Page

### Island vs Mainland
Links to city guides/pages:
- Nanaimo Guide & City Page
- Victoria Guide & City Page
- Vancouver Guide & City Page
- Burnaby Guide & City Page
- Squamish Guide & City Page (bonus — coastal connection)

### BC Hydro vs FortisBC
Links to city guides/pages:
- All 12 BC Hydro cities (selective links)
- Fort St. John Guide & City Page
- Prince George Guide & City Page

---

## Implementation Checklist

### Phase 1: Add Comparison Links to City Guides (14 edits)
- [ ] Kelowna Guide — Add comparison section + link to city page
- [ ] Kamloops Guide — Add comparison section + link to city page
- [ ] Vancouver Guide — Add comparison section + link to city page
- [ ] Burnaby Guide — Add comparison section + link to city page
- [ ] Surrey Guide — Add comparison section + link to city page
- [ ] Victoria Guide — Add comparison section + link to city page
- [ ] Nanaimo Guide — Add comparison section + link to city page
- [ ] Abbotsford Guide — Add comparison section + link to city page
- [ ] Chilliwack Guide — Add comparison section + link to city page
- [ ] Penticton Guide — Add comparison section + link to city page
- [ ] Squamish Guide — Add comparison section + link to city page
- [ ] Vernon Guide — Add comparison section + link to city page
- [ ] Fort St. John Guide — Add comparison section + link to city page
- [ ] Prince George Guide — Add comparison section + link to city page

### Phase 2: Add Guide Links to City Pages (14 edits)
- [ ] All city pages — Add link back to corresponding guide in footer

### Phase 3: Verify Link Structure
- [ ] Test internal links work correctly
- [ ] Verify all 14 cities link to comparison posts
- [ ] Confirm bidirectional city guide ↔ city page links

---

## SEO Impact

This cross-linking strategy:
1. **Signals topical authority:** All city guides link to comparisons, showing Google they're part of a cohesive BC heat pump topic
2. **Increases internal PageRank flow:** City pages + guides + comparisons pass authority to each other
3. **Captures multi-city searches:** "Kelowna vs Kamloops" query lands on comparison → routes to both cities
4. **Improves navigation:** Users naturally flow from guides → comparisons → other cities → city pages
5. **Reduces bounce rate:** Every page has 3-5 internal links to related content

**Expected result:** All 14 city pages + 14 guides + 3 comparison posts begin ranking for "[City] heat pump" + comparison keywords within 4-6 weeks.

---

## Template Code (Copy-Paste Ready)

### For City Guides (before "Next Steps"):
```html
<h2>Compare [City] to Other BC Cities</h2>
<p><strong>Interior solar comparison:</strong> <a href="/blog/kelowna-vs-kamloops-solar-comparison">Kelowna vs Kamloops: Which has better solar potential?</a></p>
<p><strong>Island vs Mainland:</strong> <a href="/blog/island-vs-mainland-bc-heat-pump-comparison">Island vs Mainland BC: Heat pump grid resilience comparison</a></p>
<p><strong>Utility comparison:</strong> <a href="/blog/bc-hydro-vs-fortisbc-rebates-comparison">BC Hydro vs FortisBC: Which offers better rebates?</a></p>

<h2>Ready to See Your Installer?</h2>
<p><strong>Next step:</strong> <a href="/ca/bc/[city-slug]" class="city-link">See [City]'s current installer profile →</a></p>
```

### For City Pages (before "Next Steps"):
```html
<p style="margin-top: 28px; border-top: 1px solid #d9d0c1; padding-top: 16px;">
  <strong>Want the full guide?</strong> <a href="/blog/[city-slug]-heat-pump-guide">Read [City]'s complete heat pump installation guide →</a>
</p>
```

---

## Total Impact: Link Density

- **14 city guides** × 3 outgoing links to comparisons = **42 authority flows**
- **14 city guides** × 1 link to city page = **14 bidirectional flows**
- **14 city pages** × 1 link back to guide = **14 bidirectional flows**
- **3 comparison posts** × 4-5 links to cities = **15 inbound authority links**

**Result:** Every piece of content is interconnected. One successful ranking lifts all 31 pieces (14 guides + 14 pages + 3 comparisons).
