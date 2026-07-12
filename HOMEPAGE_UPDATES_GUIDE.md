# Homepage Updates Guide

Add these sections to your existing `index.html` to complete the launch. Each section is standalone and can be inserted in order.

---

## 1. CALCULATOR HERO (Add after main header, before current content)

```html
<!-- CALCULATOR SECTION -->
<section style="background: #f0f9ff; border: 2px solid #bfdbfe; border-radius: 12px; padding: 48px 32px; margin: 40px 0; text-align: center;">
  <h2 style="font-size: 28px; font-weight: 700; margin-bottom: 12px; color: #1e40af;">See exactly what YOU qualify for</h2>
  <p style="font-size: 15px; color: #1e3a8a; margin-bottom: 24px; max-width: 600px; margin-left: auto; margin-right: auto;">
    Run our calculator. In 2 minutes you'll know your personalized rebate amount, your net cost, and your monthly savings.
  </p>
  <a href="/calculator" style="background: #2563eb; color: white; padding: 14px 32px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 15px; display: inline-block; cursor: pointer;">
    Start the calculator →
  </a>
  <p style="font-size: 12px; color: #6b7280; margin-top: 16px;">No email required. Takes 2 minutes. Results are personalized to your home, income, and city.</p>
</section>
```

---

## 2. QUICK WINS SECTION (Add after calculator)

```html
<!-- QUICK WINS: FREE OFFERINGS -->
<section style="padding: 40px 0; margin: 40px 0;">
  <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 24px; color: #111;">Even if big rebates don't apply yet</h2>
  <p style="font-size: 15px; color: #666; margin-bottom: 32px;">Here's what you can get TODAY (no waiting for income qualification, no big application):</p>
  
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px;">
    
    <!-- Free Thermostats -->
    <div style="background: #f0fdf4; border: 2px solid #bbf7d0; border-radius: 12px; padding: 24px;">
      <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 12px; color: #15803d;">5 Free Smart Thermostats</h3>
      <p style="font-size: 13px; color: #166534; margin-bottom: 8px;"><strong>~$350 value</strong></p>
      <p style="font-size: 13px; color: #166534;">If you have electric baseboard heat, BC Hydro will send you up to 5 free Mysa or Sinopé thermostats. Registration open now, devices ship October 2026. Plus $50–$100/year reward via Peak Saver.</p>
      <p style="font-size: 12px; color: #15803d; margin-top: 12px;"><a href="https://www.bchydro.com/powersmart/residential/rebates-programs/product-rebates.html#thermostat" style="color: #15803d; font-weight: 600; text-decoration: none;">Register now →</a></p>
    </div>

    <!-- Free Energy Kit -->
    <div style="background: #fef3e6; border: 2px solid #fde68a; border-radius: 12px; padding: 24px;">
      <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 12px; color: #92400e;">Free Energy Saving Kit</h3>
      <p style="font-size: 13px; color: #b45309; margin-bottom: 8px;"><strong>Income-qualified</strong></p>
      <p style="font-size: 13px; color: #b45309;">LED bulbs, weather stripping, high-efficiency showerheads, tap aerators, and more. Free shipping. Arrives in 3–6 weeks.</p>
      <p style="font-size: 12px; color: #b45309; margin-top: 12px;"><a href="https://www.bchydro.com/powersmart/residential/rebates-programs/savings-based-on-income/free-energy-savings-kit.html" style="color: #b45309; font-weight: 600; text-decoration: none;">Check if you qualify →</a></p>
    </div>

    <!-- Free Retrofit -->
    <div style="background: #fce7f3; border: 2px solid #fbcfe8; border-radius: 12px; padding: 24px;">
      <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 12px; color: #be123c;">Free ECAP Retrofit</h3>
      <p style="font-size: 13px; color: #be185d; margin-bottom: 8px;"><strong>Low-income households only</strong></p>
      <p style="font-size: 13px; color: #be185d;">Free heat pump, insulation, and weatherization installation through BC's Energy Conservation Assistance Program. Expanded June 2026 to include renters.</p>
      <p style="font-size: 12px; color: #be185d; margin-top: 12px;"><a href="https://www.bchydro.com" style="color: #be185d; font-weight: 600; text-decoration: none;">Learn more →</a></p>
    </div>
  </div>
</section>
```

---

## 3. INSTALLER OF THE WEEK CARD (Add after Quick Wins)

```html
<!-- INSTALLER OF THE WEEK -->
<section style="padding: 40px 0; margin: 40px 0; border-top: 1px solid #e5e7eb; border-bottom: 1px solid #e5e7eb;">
  <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 24px; color: #111;">Featured Installer</h2>
  
  <div style="background: white; border: 2px solid #e5e7eb; border-radius: 12px; padding: 32px; display: grid; grid-template-columns: auto 1fr auto; gap: 24px; align-items: start;">
    
    <div style="width: 100px; height: 100px; border-radius: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 40px;">
      🔨
    </div>
    
    <div>
      <h3 style="font-size: 18px; font-weight: 600; margin-bottom: 6px; color: #111;">[Installer Name]</h3>
      <div style="display: flex; gap: 8px; margin-bottom: 12px;">
        <span style="color: #fbbf24; font-size: 14px;">★★★★★</span>
        <span style="color: #666; font-size: 13px;">4.8 (34 reviews)</span>
      </div>
      <span style="background: #dbeafe; color: #1e40af; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; display: inline-block; margin-bottom: 12px;">HPCN Certified</span>
      <p style="font-size: 13px; color: #666; margin-bottom: 8px;">Heat pumps • Solar • Battery • Insulation</p>
      <p style="font-size: 12px; color: #999;">Serving [City] and surrounding areas</p>
    </div>
    
    <div style="text-align: center;">
      <button style="background: #2563eb; color: white; padding: 12px 20px; border: none; border-radius: 8px; font-weight: 600; font-size: 13px; cursor: pointer; width: 100%; margin-bottom: 12px;">Get a Quote</button>
      <p style="font-size: 11px; color: #666; background: #f9fafb; padding: 8px 12px; border-radius: 6px;">⚡ Responds within<br>1 business day</p>
    </div>
  </div>
  
  <p style="font-size: 12px; color: #666; margin-top: 16px; text-align: center;">
    Featured installer changes weekly. <a href="/ca/bc/[city]" style="color: #2563eb; text-decoration: none; font-weight: 600;">See all installers in [City] →</a>
  </p>
</section>
```

---

## 4. CASE STUDIES / TESTIMONIALS (Add in existing content area)

```html
<!-- CASE STUDIES -->
<section style="padding: 40px 0; margin: 40px 0;">
  <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 24px; color: #111;">Real projects. Real savings.</h2>
  
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px;">
    
    <!-- Case Study 1 -->
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
      <div style="height: 160px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 60px;">📸</div>
      <div style="padding: 20px;">
        <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 6px; color: #111;">Heat Pump + Solar + Battery</h3>
        <p style="font-size: 12px; color: #666; margin-bottom: 12px;">Kelowna</p>
        <p style="font-size: 13px; font-weight: 600; color: #2563eb; margin-bottom: 12px;">$18,000 in rebates | $170/month savings</p>
        <p style="font-size: 13px; color: #666; margin-bottom: 12px; font-style: italic;">"We had no idea we qualified for that much. [Installer] made it simple and walked us through every step."</p>
        <p style="font-size: 12px; color: #999; margin-bottom: 12px;">— Sarah & Mike, Kelowna</p>
        <a href="/blog" style="color: #2563eb; text-decoration: none; font-weight: 600; font-size: 12px;">Read the full story →</a>
      </div>
    </div>

    <!-- Case Study 2 -->
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
      <div style="height: 160px; background: linear-gradient(135deg, #f59e0b 0%, #ec4899 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 60px;">📸</div>
      <div style="padding: 20px;">
        <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 6px; color: #111;">Heat Pump + Insulation</h3>
        <p style="font-size: 12px; color: #666; margin-bottom: 12px;">Vancouver</p>
        <p style="font-size: 13px; font-weight: 600; color: #2563eb; margin-bottom: 12px;">$22,000 in rebates | $140/month savings</p>
        <p style="font-size: 13px; color: #666; margin-bottom: 12px; font-style: italic;">"Our heating bill is now half of what it was, and we actually feel warmer in winter."</p>
        <p style="font-size: 12px; color: #999; margin-bottom: 12px;">— James, Vancouver</p>
        <a href="/blog" style="color: #2563eb; text-decoration: none; font-weight: 600; font-size: 12px;">Read the full story →</a>
      </div>
    </div>

    <!-- Case Study 3 -->
    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden;">
      <div style="height: 160px; background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 60px;">📸</div>
      <div style="padding: 20px;">
        <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 6px; color: #111;">Solar + Battery + EV Charger</h3>
        <p style="font-size: 12px; color: #666; margin-bottom: 12px;">Victoria</p>
        <p style="font-size: 13px; font-weight: 600; color: #2563eb; margin-bottom: 12px;">$16,000 in rebates | $200/month savings</p>
        <p style="font-size: 13px; color: #666; margin-bottom: 12px; font-style: italic;">"Now charging our EV for free and selling excess power back to the grid."</p>
        <p style="font-size: 12px; color: #999; margin-bottom: 12px;">— Linda, Victoria</p>
        <a href="/blog" style="color: #2563eb; text-decoration: none; font-weight: 600; font-size: 12px;">Read the full story →</a>
      </div>
    </div>
  </div>
</section>
```

---

## 5. BLOG SECTION (Add near bottom before footer)

```html
<!-- BLOG / EDUCATION -->
<section style="padding: 40px 0; margin: 40px 0; border-top: 1px solid #e5e7eb;">
  <h2 style="font-size: 24px; font-weight: 700; margin-bottom: 24px; color: #111;">Learn about BC rebates</h2>
  
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px;">
    
    <div style="border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px;">
      <p style="font-size: 12px; color: #666; margin-bottom: 8px; text-transform: uppercase; font-weight: 600;">Guide</p>
      <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 12px; color: #111;">Heat Pump Rebates by Income: Exactly What You Qualify For</h3>
      <p style="font-size: 13px; color: #666; margin-bottom: 12px;">Income tiers by household size, Level 1/2/3 amounts, application process. 4-min read.</p>
      <a href="/blog/heat-pump-rebates-income-tiers-bc-2026" style="color: #2563eb; text-decoration: none; font-weight: 600; font-size: 12px;">Read →</a>
    </div>

    <div style="border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px;">
      <p style="font-size: 12px; color: #666; margin-bottom: 8px; text-transform: uppercase; font-weight: 600;">Program Change</p>
      <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 12px; color: #111;">BC Ended Net Metering: What Changed for Solar (July 1, 2026)</h3>
      <p style="font-size: 13px; color: #666; margin-bottom: 12px;">10¢/kWh export rate, why batteries matter, rebate amounts, Peak Saver 14-day window. 5-min read.</p>
      <a href="/blog/bc-net-metering-ended-self-generation-rate-2026" style="color: #2563eb; text-decoration: none; font-weight: 600; font-size: 12px;">Read →</a>
    </div>

    <div style="border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px;">
      <p style="font-size: 12px; color: #666; margin-bottom: 8px; text-transform: uppercase; font-weight: 600;">New Program</p>
      <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 12px; color: #111;">Free Smart Thermostats for All BC Homeowners (October 2026)</h3>
      <p style="font-size: 13px; color: #666; margin-bottom: 12px;">Up to 5 free Mysa/Sinopé thermostats if you have electric baseboard heat. No income requirement. 3-min read.</p>
      <a href="/blog" style="color: #2563eb; text-decoration: none; font-weight: 600; font-size: 12px;">Read →</a>
    </div>
  </div>
  
  <p style="text-align: center; margin-top: 32px;">
    <a href="/blog" style="color: #2563eb; text-decoration: none; font-weight: 600; font-size: 14px;">View all blog posts →</a>
  </p>
</section>
```

---

## INSERTION POINTS IN index.html

1. **Calculator Hero** → After opening `<div class="container">` and main hero, before current rebate info
2. **Quick Wins** → After calculator section
3. **Installer of the Week** → After Quick Wins or in existing installer section
4. **Case Studies** → Before footer, in a new `<section>`
5. **Blog Section** → Right before `<footer>`

---

## WHAT TO CUSTOMIZE

- `[City]` → Replace with primary city (Kelowna, Vancouver, etc.) or remove for generic version
- `[Installer Name]` → Replace with first featured installer's name, or template it to rotate weekly
- Photo URLs → Add real installer photos or use emoji as placeholder
- Blog URLs → Link to your actual blog post URLs (`/blog/heat-pump-rebates-income-tiers-bc-2026`, etc.)
- Link colors, fonts → Match your existing homepage style

---

## TESTING

After adding sections:
1. View on desktop and mobile
2. Test all calculator CTA links → should go to `/calculator`
3. Test all blog links → should go to `/blog/[slug]`
4. Test installer card "Get a Quote" → should go to `/ca/bc/[city]`
5. Verify no broken links

**Ready to add these to index.html and go live.**
