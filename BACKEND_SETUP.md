# Backend Setup: Newsletter Signup API

## What This Does

- Receives newsletter signups (email + city) from your website forms
- Saves them to `data/signups.json` for your records
- Forwards them to Resend automatically
- Enables tracking which page signups came from (homepage, blog, assessment)

---

## Quick Start (5 minutes)

### 1. Install Node.js dependencies

```bash
npm install
```

This installs: `express`, `cors`, `dotenv`

### 2. Create `.env.local` file

Copy the template:
```bash
cp .env.local.example .env.local
```

Your `.env.local` should contain:
```
RESEND_API_KEY=re_Tk3drtA2_9A7SmeJTwMpw6RibZbRVdmrQ
PORT=3000
```

(The API key is already in the template — don't commit `.env.local` to git)

### 3. Start the server

```bash
npm start
```

You should see:
```
✓ Server running on http://localhost:3000
✓ Static files served from ./
✓ POST /api/newsletter-signup ready
```

### 4. Test it

Open http://localhost:3000 in your browser. Fill out a newsletter form on the homepage.

You should see:
- ✓ Success message on the page
- ✓ New file created: `data/signups.json` with your email + city
- ✓ Email added to Resend audience (check dashboard)

---

## What's Happening

```
User fills form (email + city)
        ↓
Form POSTs to /api/newsletter-signup
        ↓
Backend saves to data/signups.json
        ↓
Backend sends to Resend API
        ↓
Email added to Resend audience
        ↓
Success message shown to user
```

---

## File Structure

```
/Users/sammenard/Downloads/Powerrebate/
├── server.js                    # Main backend server
├── api/
│   └── newsletter-signup.js      # API endpoint code
├── package.json                 # Dependencies
├── .env.local                   # Your API keys (not in git)
├── .env.local.example           # Template
├── data/
│   └── signups.json             # Saved signups (created on first signup)
└── index.html, blog/, etc       # Static files
```

---

## Usage: Viewing Signups

Your signups are logged to `data/signups.json`. Each entry looks like:

```json
{
  "email": "kelowna@example.com",
  "city": "Kelowna",
  "page": "homepage",
  "date": "2026-07-03T14:22:00.123Z"
}
```

**Use this data for:**
- Marketing: See which cities have the most interest
- Analytics: Track which pages (homepage/blog/assessment) drive signups
- Segmentation: Group signups by city for targeted Email 2

---

## Deployment

### For Production (Vercel, Netlify, etc.)

1. Set environment variable on your host:
   - `RESEND_API_KEY=your_key_here`

2. Deploy `server.js` as your serverless function or node app

3. Point your domain to the server

### Simple: Keep running locally

```bash
nohup npm start > server.log 2>&1 &
```

This keeps the server running even if you close the terminal.

---

## Troubleshooting

**Port 3000 already in use?**
```bash
# Use a different port
PORT=3001 npm start
```

**"Cannot find module 'express'"?**
```bash
npm install
```

**Signups not appearing in Resend?**
- Check `.env.local` has the correct API key
- Check server logs: `cat server.log`
- Test manually:
  ```bash
  curl -X POST http://localhost:3000/api/newsletter-signup \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","city":"Vancouver","page":"test"}'
  ```

**Data not saving to file?**
- Check `data/` folder exists and is writable
- Run `mkdir -p data` to create it

---

## Next Steps

1. ✓ Start server: `npm start`
2. ✓ Test signup on homepage
3. ✓ Check `data/signups.json` was created
4. ✓ Verify email appears in Resend dashboard
5. ✓ Set up Email 2 in Resend (city-specific)
6. Execute marketing plan (Reddit, Facebook, etc.)

