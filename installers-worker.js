/**
 * Cloudflare Worker for HomePowerRebate Installers API
 * Fetches installer data from Google Sheets and serves it as JSON
 */

async function getInstallers(city) {
  try {
    // Get Google Sheets API credentials from environment
    const sheetId = 'HomePowerRebate-Installers';
    const apiKey = env.GOOGLE_SHEETS_API_KEY;

    // Note: In production, use service account OAuth2 flow
    // For now, this attempts to fetch from a published sheet or use cached data

    // Fetch all installer data from Google Sheets
    // This URL uses a Google Sheets API v4 request
    const url = `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/Sheet1?key=${apiKey}`;

    const response = await fetch(url);
    if (!response.ok) {
      return { error: 'Failed to fetch from Google Sheets' };
    }

    const data = await response.json();
    const rows = data.values || [];

    if (rows.length < 2) {
      return { error: 'No installer data found' };
    }

    // Parse headers
    const headers = rows[0];
    const installers = [];

    // Parse rows and filter by city
    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      const installer = {
        city: row[0] || '',
        name: row[1] || '',
        location: row[2] || '',
        phone: row[3] || '',
        website: row[4] || '',
        rating: parseFloat(row[5]) || 0,
        reviews: parseInt(row[6]) || 0,
        gmaps_url: row[7] || '',
        recommended: row[8]?.toLowerCase() === 'yes',
        specialty: 'Heat Pump Installation',
        description: 'HPCN-certified heat pump and solar installer'
      };

      if (installer.city.toLowerCase() === city.toLowerCase()) {
        installers.push(installer);
      }
    }

    // Sort: recommended first, then by rating, then by review count
    installers.sort((a, b) => {
      if (a.recommended !== b.recommended) return b.recommended ? 1 : -1;
      if (a.rating !== b.rating) return b.rating - a.rating;
      return b.reviews - a.reviews;
    });

    return installers;
  } catch (error) {
    console.error('Error fetching installers:', error);
    return { error: 'Failed to fetch installers' };
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        }
      });
    }

    // Extract city from path: /api/installers/vancouver.json
    const match = path.match(/\/api\/installers\/([a-z\-]+)\.json/);

    if (!match) {
      return new Response(JSON.stringify({ error: 'Not found' }), {
        status: 404,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }

    const city = match[1].replace(/-/g, ' ');
    const installers = await getInstallers(city);

    return new Response(JSON.stringify(installers), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'max-age=3600'
      }
    });
  }
};
