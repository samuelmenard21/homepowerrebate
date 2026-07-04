import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { email, city, heating, income, estimate } = req.body;

    if (!email) {
      return res.status(400).json({ error: 'Email is required' });
    }

    // Log to local JSON file for your records
    const dataDir = path.join(__dirname, '../data');
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
      page: req.body.page || 'unknown',
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
      // If already exists, that's fine
      if (resendData.message?.includes('already exists')) {
        return res.status(200).json({
          success: true,
          message: 'Email already in audience',
          resendId: null
        });
      }
      throw new Error(resendData.message || 'Resend API error');
    }

    res.status(200).json({
      success: true,
      message: 'Signup successful',
      resendId: resendData.id,
      email,
      city: city || 'Not specified'
    });
  } catch (error) {
    console.error('Newsletter signup error:', error);
    res.status(500).json({
      error: 'Failed to process signup',
      message: error.message
    });
  }
}
