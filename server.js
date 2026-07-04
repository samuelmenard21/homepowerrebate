import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

dotenv.config({ path: '.env.local' });

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();

app.use(cors());
app.use(express.json());

// Serve static files from root
app.use(express.static('.'));

// Newsletter signup endpoint
app.post('/api/newsletter-signup', async (req, res) => {
  try {
    const { email, city, page, heating, income, estimate } = req.body;

    if (!email) {
      return res.status(400).json({ error: 'Email is required' });
    }

    // Log to local JSON file
    const dataDir = path.join(__dirname, 'data');
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true });
    }

    const signupsFile = path.join(dataDir, 'signups.json');
    let signups = [];
    if (fs.existsSync(signupsFile)) {
      try {
        signups = JSON.parse(fs.readFileSync(signupsFile, 'utf-8'));
      } catch (e) {
        signups = [];
      }
    }

    signups.push({
      email,
      city: city || 'Not specified',
      page: page || 'unknown',
      heating: heating || null,
      income: income || null,
      estimate: estimate || null,
      date: new Date().toISOString()
    });

    fs.writeFileSync(signupsFile, JSON.stringify(signups, null, 2));

    // Send to Resend
    const resendResponse = await fetch(
      'https://api.resend.com/audiences/c8b63b68-01ad-4727-a62e-2484dbe25ae9/contacts',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.RESEND_API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: email,
          unsubscribed: false
        })
      }
    );

    const resendData = await resendResponse.json();

    if (!resendResponse.ok) {
      if (resendData.message?.includes('already exists')) {
        return res.status(200).json({
          success: true,
          message: 'Already subscribed',
          email,
          city: city || 'Not specified'
        });
      }
      throw new Error(resendData.message || 'Resend API error');
    }

    res.status(200).json({
      success: true,
      message: 'Subscribed successfully',
      email,
      city: city || 'Not specified'
    });
  } catch (error) {
    console.error('Newsletter signup error:', error.message);
    res.status(500).json({
      error: 'Failed to process signup',
      message: error.message
    });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`✓ Server running on http://localhost:${PORT}`);
  console.log(`✓ Static files served from ./`);
  console.log(`✓ POST /api/newsletter-signup ready`);
});
