# "Request My City" Form + Flow

---

## HTML Form (Add to City List Page)

```html
<section class="request-city-section">
  <div class="wrap">
    <h2>📍 Can't find your city?</h2>
    <p>We're expanding every week. Tell us where you are and we'll prioritize your city for launch.</p>
    
    <form id="request-city-form" class="request-form">
      <fieldset>
        <legend>Request HomePowerRebate in Your City</legend>
        
        <!-- Name -->
        <div class="form-group">
          <label for="name">Your name</label>
          <input type="text" id="name" name="name" required placeholder="Sam">
        </div>
        
        <!-- Email -->
        <div class="form-group">
          <label for="email">Email (so we can notify you)</label>
          <input type="email" id="email" name="email" required placeholder="you@example.com">
        </div>
        
        <!-- City -->
        <div class="form-group">
          <label for="city">City</label>
          <input type="text" id="city" name="city" required placeholder="Toronto, Hamilton, London, etc.">
        </div>
        
        <!-- Region -->
        <div class="form-group">
          <label for="region">Province or State</label>
          <select id="region" name="region" required>
            <option value="">— Select —</option>
            <option value="on">Ontario</option>
            <option value="ca">California</option>
            <option value="other">Other (US/Canada)</option>
          </select>
        </div>
        
        <!-- Interests (Multiple) -->
        <div class="form-group">
          <label>What are you interested in?</label>
          <div class="checkboxes">
            <label class="checkbox">
              <input type="checkbox" name="interests" value="heat-pump"> Heat pump
            </label>
            <label class="checkbox">
              <input type="checkbox" name="interests" value="solar"> Solar
            </label>
            <label class="checkbox">
              <input type="checkbox" name="interests" value="battery"> Battery storage
            </label>
            <label class="checkbox">
              <input type="checkbox" name="interests" value="all"> All of the above
            </label>
          </div>
        </div>
        
        <!-- Privacy note -->
        <p class="privacy-note">
          We'll only use your email to notify you when we launch in your city. 
          <a href="/privacy">Privacy policy</a>
        </p>
        
        <!-- Submit -->
        <button type="submit" class="btn-primary">Request [City]</button>
      </fieldset>
    </form>
    
    <!-- Success message (hidden until submitted) -->
    <div id="success-message" class="success-message" style="display: none;">
      <h3>✓ Thanks, [Name]!</h3>
      <p>We'll launch in [City] and email you at [Email] the moment we're live.</p>
      <p style="font-size: 14px; color: #666; margin-top: 12px;">
        In the meantime, check out our <a href="/blog">guides and comparisons</a> to learn about heat pumps, solar, and rebates.
      </p>
    </div>
  </div>
</section>

<style>
.request-city-section {
  background: var(--paper-warm);
  border: 1px solid #d9d0c1;
  border-radius: 12px;
  padding: 40px 28px;
  margin: 40px 0;
}

.request-form {
  max-width: 500px;
  margin: 24px auto 0;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  font-size: 14px;
  color: var(--ink);
}

.form-group input[type="text"],
.form-group input[type="email"],
.form-group select {
  width: 100%;
  padding: 12px;
  border: 1px solid #d9d0c1;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--teal);
  background: #fff;
}

.checkboxes {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.checkbox {
  display: flex;
  align-items: center;
  font-weight: normal;
  cursor: pointer;
}

.checkbox input[type="checkbox"] {
  margin-right: 10px;
  cursor: pointer;
}

.privacy-note {
  font-size: 12px;
  color: #666;
  margin-bottom: 16px;
}

.btn-primary {
  width: 100%;
  padding: 14px;
  background: var(--amber-bright);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: var(--amber);
}

.success-message {
  background: #f0f9f7;
  border-left: 4px solid var(--teal);
  padding: 20px;
  border-radius: 6px;
  margin-top: 24px;
}

.success-message h3 {
  margin: 0 0 8px 0;
  color: var(--teal-deep);
}

.success-message p {
  margin: 8px 0;
  font-size: 14px;
}
</style>

<script>
document.getElementById('request-city-form').addEventListener('submit', function(e) {
  e.preventDefault();
  
  const name = document.getElementById('name').value;
  const email = document.getElementById('email').value;
  const city = document.getElementById('city').value;
  const region = document.getElementById('region').value;
  const interests = Array.from(document.querySelectorAll('input[name="interests"]:checked'))
    .map(cb => cb.value)
    .join(', ');
  
  // Send to your backend
  fetch('/api/request-city', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name,
      email,
      city,
      region,
      interests,
      timestamp: new Date().toISOString()
    })
  })
  .then(response => response.json())
  .then(data => {
    // Hide form, show success message
    document.getElementById('request-city-form').style.display = 'none';
    const successMsg = document.getElementById('success-message');
    successMsg.innerHTML = `
      <h3>✓ Thanks, ${name}!</h3>
      <p>We'll launch in ${city} and email you at ${email} the moment we're live.</p>
      <p style="font-size: 14px; color: #666; margin-top: 12px;">
        In the meantime, check out our <a href="/blog">guides and comparisons</a> to learn about heat pumps, solar, and rebates.
      </p>
    `;
    successMsg.style.display = 'block';
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Something went wrong. Please try again or email us at samuelmenard@gmail.com');
  });
});
</script>
```

---

## Backend (API Endpoint: `/api/request-city`)

### What It Does
1. Accepts POST request with form data
2. Saves to database: `requested_cities` table
3. Sends confirmation email to user
4. (Optional) Sends notification to Sam: "New request for [City]"

### Database Schema
```sql
CREATE TABLE requested_cities (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100),
  city VARCHAR(100),
  region VARCHAR(100),
  interests TEXT,
  timestamp TIMESTAMP DEFAULT NOW(),
  notified_at TIMESTAMP,
  launched_at TIMESTAMP
);

CREATE INDEX idx_region_city ON requested_cities(region, city);
CREATE INDEX idx_email ON requested_cities(email);
```

### SQL Queries You'll Need
```sql
-- Count requests by city (to prioritize launches)
SELECT city, COUNT(*) as requests
FROM requested_cities
WHERE region = 'on' OR region = 'ca'
GROUP BY city
ORDER BY requests DESC;

-- Get email list for launch notification
SELECT email FROM requested_cities
WHERE city = 'Toronto' AND region = 'on' AND notified_at IS NULL;

-- Mark as notified after sending launch email
UPDATE requested_cities
SET notified_at = NOW()
WHERE city = 'Toronto' AND region = 'on';
```

---

## Email Templates

### Template 1: Confirmation Email (Auto-sent after form submission)

**To:** [Email from form]
**Subject:** We'll launch HomePowerRebate in [City] soon!

```
Hi [Name],

Thanks for requesting HomePowerRebate in [City], [Region].

We're launching new cities every week, and [City] is on our priority list based on demand.

In the meantime, here's what you should know about home energy rebates in [Region]:
- [Placeholder: Learn about [Region] heat pump rebates]
- [Placeholder: Solar incentives in [Region]]
- [Placeholder: How to find trusted installers]

→ [Link to relevant blog post for their region]

**We'll email you the moment we launch in [City].**

Questions? Reply to this email or contact us at samuelmenard@gmail.com

— Sam
HomePowerRebate
```

---

### Template 2: Launch Notification (Sent when city goes live)

**To:** [All emails from requested_cities where city = "Toronto"]
**Subject:** HomePowerRebate is live in [City]! 🎉

```
Hi [Name],

You requested HomePowerRebate in [City], and we're live now!

See what rebates you qualify for:
→ [https://homepowerrebate.com/ca/on/toronto]

You'll get matched with 2-3 trusted installers in [City], all vetted for:
✓ No sales pressure
✓ Transparent pricing
✓ Case studies & references
✓ HPCN certification + insurance

**Next steps:**
1. Calculate your rebate (2 min)
2. Get matched with installers (instant)
3. Compare proposals (on your time)
4. We guide you through the paperwork

Have questions? Reply to this email.

— Sam
HomePowerRebate
```

---

### Template 3: Weekly Digest (Optional: send to all requesters on Day 7)

**Subject:** What [Region] homeowners should know before going solar + heat pump

```
Hi [Name],

This week, we're launching in [City], [Region]. While we finish setup, here's what you should know about home energy in your area.

📖 **This week's guide:**
[Link to most relevant blog post for their region/interests]

🔗 **You might also like:**
- [Link to comparison post]
- [Link to regional guide]
- [Link to FAQ]

**Still waiting on your city?** [Link to request form]

We're prioritizing based on requests, so the more people who request, the faster we launch.

— Sam
HomePowerRebate
```

---

## Launch Dashboard (For You)

Track expansion readiness:

```
REQUESTED CITIES (All Regions)

Ontario:
- Toronto: 487 requests | 💬 Interests: heat pump (320), solar (180), battery (150)
- Ottawa: 234 requests
- Hamilton: 178 requests
- London: 92 requests
- Kitchener: 67 requests
[Next highest: Mississauga (54), Brampton (48), etc.]

California:
- Los Angeles: 312 requests
- San Francisco: 198 requests
- San Diego: 145 requests
[Next highest: Oakland (89), Fresno (67), etc.]

ACTION ITEMS:
☐ Research Ontario top 5 cities (Toronto, Ottawa, Hamilton, London, Kitchener)
☐ Research California top 3 cities (LA, SF, SD)
☐ When Ontario goes live: Send launch email to all Toronto requesters
☐ When California goes live: Send launch email to all LA requesters
```

---

## Analytics to Track

Add these to your analytics tool (Google Analytics, Mixpanel, etc.):

- **Event: "City Requested"** 
  - City dimension
  - Region dimension
  - Interests dimension
  - [Optional: traffic source — where did they come from?]

- **Event: "Launch Notification Sent"**
  - City dimension
  - Email count

- **Event: "Post-Launch Conversion"**
  - City dimension
  - Did user who requested actually complete rebate assessment? [Y/N]
  - How many days between request and assessment?

This gives you data on:
1. Which cities to prioritize (demand)
2. Which regions drive highest quality leads (post-launch conversion)
3. How long requesters wait before acting (helps you plan launch timing)

