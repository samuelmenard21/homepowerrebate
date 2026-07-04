# Resend Newsletter Setup Guide

## What is Resend?

Resend is a simple, developer-friendly email API. Perfect for this use case:
- **Free tier:** 100 emails/day (plenty for first 500 users)
- **Paid:** $20/month for 3,000 emails/month
- **No credit card required to start**
- **Dashboard shows all signups + opens**

---

## Step 1: Create a Resend Account (2 min)

1. Go to **[resend.com](https://resend.com)**
2. Click "Sign up"
3. Use your email (samuelmenard@gmail.com)
4. Verify email
5. You're in the dashboard

---

## Step 2: Get Your API Key (1 min)

1. In Resend dashboard, click **"Settings"** (gear icon, top right)
2. Click **"API Keys"** in the left sidebar
3. You'll see: `re_xxxxxxxxxxx...` (your API key)
4. **Copy this key** — you'll use it in the next step
5. ⚠️ **Keep this secret.** Never commit it to GitHub. We'll use environment variables.

---

## Step 3: Create Your Email List (2 min)

1. In Resend dashboard, click **"Audiences"** (left sidebar)
2. Click **"Create Audience"**
3. Name: `HomePowerRebate Newsletter`
4. Description: `BC homeowners interested in solar, heat pump, and battery rebates`
5. Click **"Create"**
6. You'll see: `Audience ID: xxxxxxxx`
7. **Copy this ID** — needed for the form integration

---

## Step 4: Wire Up the Homepage Form

### Current Setup (What You Have)

Your homepage has a form like this:
```html
<form id="homepage-newsletter-form">
  <input type="email" placeholder="Your email" required>
  <button type="submit">Get Matched →</button>
</form>

<script>
document.getElementById('homepage-newsletter-form').addEventListener('submit', function(e) {
  e.preventDefault();
  const email = this.querySelector('input[type="email"]').value;
  console.log('Newsletter signup:', email);  // Currently just logs to console
});
</script>
```

### New Setup (With Resend)

Replace with this:

```html
<form id="homepage-newsletter-form">
  <input type="email" placeholder="Your email" required>
  <button type="submit">Get Matched →</button>
  <p id="form-message" style="display:none; margin-top:8px; font-size:14px;"></p>
</form>

<script>
const RESEND_API_KEY = 'YOUR_API_KEY_HERE';  // You'll set this as an environment variable
const AUDIENCE_ID = 'YOUR_AUDIENCE_ID_HERE';  // From Resend dashboard

document.getElementById('homepage-newsletter-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  const email = this.querySelector('input[type="email"]').value;
  const button = this.querySelector('button');
  const messageEl = document.getElementById('form-message');
  
  // Disable button while sending
  button.disabled = true;
  button.textContent = 'Signing up...';
  
  try {
    const response = await fetch('https://api.resend.com/audiences/' + AUDIENCE_ID + '/contacts', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + RESEND_API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: email,
        unsubscribed: false
      })
    });
    
    if (response.ok) {
      messageEl.style.display = 'block';
      messageEl.style.color = '#2d6a4f';
      messageEl.textContent = '✓ You\'re in! Check your email for the first insights on BC rebates.';
      this.reset();
      button.textContent = 'Get Matched →';
      button.disabled = false;
    } else {
      throw new Error('Signup failed');
    }
  } catch (error) {
    messageEl.style.display = 'block';
    messageEl.style.color = '#d4751c';
    messageEl.textContent = 'Something went wrong. Try again or email hello@homepowerrebate.com';
    button.textContent = 'Get Matched →';
    button.disabled = false;
  }
});
</script>
```

---

## Step 5: Handle the API Key Safely

⚠️ **IMPORTANT:** Never put your API key directly in HTML or GitHub. Use one of these approaches:

### Option A: Environment Variables (Recommended for production)

1. Create a `.env.local` file in your project root:
```
RESEND_API_KEY=re_your_actual_key_here
RESEND_AUDIENCE_ID=your_audience_id_here
```

2. Add `.env.local` to `.gitignore`:
```
.env.local
```

3. In your HTML form, use a backend endpoint instead:

```javascript
// Instead of making the API call directly from the browser,
// send the email to YOUR backend:

fetch('/api/newsletter-signup', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: email })
});
```

4. Create `/api/newsletter-signup.js` (backend handler):
```javascript
export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();
  
  const { email } = req.body;
  
  const response = await fetch('https://api.resend.com/audiences/YOUR_AUDIENCE_ID/contacts', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.RESEND_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      email: email,
      unsubscribed: false
    })
  });
  
  if (response.ok) {
    res.status(200).json({ success: true });
  } else {
    res.status(400).json({ error: 'Signup failed' });
  }
}
```

### Option B: Quick Testing (Development only)

For now, just replace `YOUR_API_KEY_HERE` with your actual key in the form. This works for testing. Once you're happy, move to Option A.

---

## Step 6: Update All Forms

Apply the same pattern to:
1. **Homepage:** `/index.html` (homepage-newsletter-form)
2. **Blog page:** `/blog/index.html` (blog-newsletter-form)
3. **Assessment page:** `/retrofit-assessment/index.html` (assessment-newsletter-form)
4. **City pages:** each city has a Quick Resources section before the footer

Each form can send to the same Resend Audience ID (they all go to one list).

---

## Step 7: Test It

1. Open your homepage
2. Enter a test email: `test@example.com`
3. Submit the form
4. Check the success message
5. Go to Resend dashboard → **"Audiences"** → **"HomePowerRebate Newsletter"**
6. You should see the email added to the list

---

## Step 8: Send Your First Email (from Resend Dashboard)

1. In Resend, go to **"Campaigns"** (left sidebar)
2. Click **"Create"**
3. **Name:** `Welcome: How to Claim $16K in BC Rebates`
4. **From:** `hello@homepowerrebate.com` (or your domain once you add it)
5. **Audience:** Select your "HomePowerRebate Newsletter" audience
6. **Subject:** `Welcome to HomePowerRebate — here's your $16,000 heat pump rebate`
7. **Body:** Use their HTML editor or drag-and-drop to create a welcome email with:
   - Welcome message
   - Link to assessment tool
   - Link to your 3 blog posts
   - Link to your city pages
   - Social proof: "Join 500+ BC homeowners claiming their rebates"

8. Click **"Schedule"** or **"Send now"** (test with one email first)

---

## Email Template for First Welcome Email

Subject: `Welcome — here's your $16,000 heat pump rebate (if you qualify)`

Body:
```
Hi there,

Great news: the BC government will cover most of your home upgrades.

Here's what you can get:
• Heat pump: $4,000–$16,000 (depending on income)
• Solar: $5,000 (doubled to $10,000 with battery)
• Water heater: $1,000–$3,500

Most people don't claim any of it because the process is confusing. We fix that.

FIRST STEP: Use our free assessment tool to see exactly what YOU can claim in YOUR city:
[Link to /retrofit-assessment]

THEN: Pick your city to see local incentives you didn't know existed:
[Link to /ca/bc — where they can pick their city]

Questions? We have 3 detailed guides:
- How the federal Greener Homes Grant actually works
- Why you should insulate before installing a heat pump
- What happens in a home energy audit

You're in good company — 500+ BC homeowners are using this to claim their rebates.

Let me know if you have questions.

— The HomePowerRebate Team
hello@homepowerrebate.com
```

---

## Done ✓

Once set up:
- Every homepage visitor can sign up
- Emails flow into Resend automatically
- You can send campaigns from the Resend dashboard
- You get open rates, clicks, and subscriber stats
- **Free tier covers your first 5,000+ emails**

---

## Next Steps

1. **Add domain email** (optional but professional): `hello@yourname.com` from your own domain instead of `noreply@...`
   - Resend dashboard → Settings → Domains
   - Follow DNS setup (5 min, your domain provider)

2. **Set up drip campaign** (optional): "3 emails over 2 weeks" automatically sent to new signups
   - Email 1: Welcome + assessment tool link
   - Email 2: City pages + local incentives
   - Email 3: First blog post + success story

3. **Track which page drives signups** by adding a source param:
   - Homepage form: `/api/newsletter-signup?source=homepage`
   - Blog form: `/api/newsletter-signup?source=blog`
   - Assessment form: `/api/newsletter-signup?source=assessment`

