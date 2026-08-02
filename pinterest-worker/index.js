/**
 * Pinterest Automation Worker for HomePowerRebate
 * Posts 3-4 pins per day automatically
 *
 * Scheduled: 6am, 12pm, 6pm, 10pm PT (optimal posting times)
 * Content sources: Blog posts + city pages
 * Pin types: Blog posts (40%), Tips/hacks (35%), City guides (25%)
 */

const PINTEREST_API_URL = "https://api.pinterest.com/v5/pins";
const SITE_URL = "https://homepowerrebate.com";
const CONTENT_SOURCES = {
  blogs: [
    { path: "/blog/bc-hydro-peak-saver-battery-rebate-5000-vs-1500.html", type: "blog", title: "BC Hydro Peak Saver Battery Rebate: Get $5,000 Instead of $1,500" },
    { path: "/blog/tesla-powerwall-bc-hydro-rebate-not-qualified-alternatives.html", type: "blog", title: "Why Tesla Powerwall Doesn't Qualify for BC Hydro's Battery Rebate (And What Does)" },
    { path: "/blog/cleanbc-income-qualified-free-heat-pump-2026.html", type: "blog", title: "CleanBC Income Qualified Program 2026: Do You Qualify for 100% Free Heat Pump?" },
    { path: "/blog/insulation-rebates-bc-stack-federal-provincial.html", type: "blog", title: "BC Insulation Rebates 2026: Stack Federal + Provincial Grants for Up to $11,350" },
    { path: "/blog/bosch-vs-mitsubishi-heat-pump.html", type: "blog", title: "Bosch vs Mitsubishi Heat Pump: Which Qualifies for BC Rebates?" },
    { path: "/blog/mysa-vs-ecobee-thermostat.html", type: "blog", title: "Mysa vs Ecobee Smart Thermostat: Which Works Best with BC Heat Pumps?" },
  ],
  tips: [
    { title: "5 Installer Red Flags: Payment Before Install = STOP", keywords: ["installer", "red flags", "payment"] },
    { title: "Peak Saver Battery: $5K vs $1.5K (This One Decision)", keywords: ["peak saver", "battery", "rebate"] },
    { title: "Tesla Powerwall Doesn't Qualify for BC Hydro (Why It Matters)", keywords: ["powerwall", "bc hydro", "rebate"] },
    { title: "Heat Pump Brands Ranked by BC Homeowners", keywords: ["heat pump", "brands", "comparison"] },
    { title: "Solar Cost After BC Rebate: Real Numbers", keywords: ["solar", "cost", "rebate"] },
  ],
  cities: [
    "abbotsford", "burnaby", "chilliwack", "coquitlam", "fort-st-john",
    "kamloops", "kelowna", "langley", "maple-ridge", "nanaimo",
    "penticton", "prince-george", "richmond", "squamish", "surrey",
    "vancouver", "vernon", "victoria"
  ]
};

// Pin distribution by type
const PIN_TYPES = {
  BLOG: 0.40,      // 40% blog posts
  TIPS: 0.35,      // 35% tips/hacks
  CITY: 0.25       // 25% city guides
};

export default {
  async fetch(request, env) {
    if (request.method === "POST" && new URL(request.url).pathname === "/test") {
      return handlePinterestPost(env);
    }
    return new Response("Worker is running", { status: 200 });
  },

  async scheduled(request, env) {
    return handlePinterestPost(env);
  }
};

async function handlePinterestPost(env) {
  try {
    console.log(`[Pinterest] Execution at ${new Date().toISOString()}`);

      // Verify prerequisites
      if (!env.PINTEREST_ACCESS_TOKEN) {
        throw new Error("PINTEREST_ACCESS_TOKEN not set in Cloudflare secrets");
      }

      // Select pin type based on distribution
      const pinType = selectPinType();
      let pin;

      switch (pinType) {
        case "blog":
          pin = await createBlogPin(env);
          break;
        case "tips":
          pin = await createTipsPin(env);
          break;
        case "city":
          pin = await createCityPin(env);
          break;
      }

      // Post to Pinterest
      const result = await postToPinterest(pin, env);
      console.log(`[Pinterest] Pin posted successfully: ${result.id}`);

      // Log to D1 (optional analytics)
      if (env.DB) {
        await logPinPosted(env.DB, pin, result);
      }

      return new Response(JSON.stringify({ success: true, pin_id: result.id, type: pinType }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      });

    } catch (error) {
      console.error(`[Pinterest] Error: ${error.message}`);
      return new Response(JSON.stringify({ success: false, error: error.message }), {
        status: 500,
        headers: { "Content-Type": "application/json" }
      });
    }
}

/**
 * Select pin type based on distribution weights
 */
function selectPinType() {
  const rand = Math.random();
  if (rand < PIN_TYPES.BLOG) return "blog";
  if (rand < PIN_TYPES.BLOG + PIN_TYPES.TIPS) return "tips";
  return "city";
}

/**
 * Create a blog post pin
 */
async function createBlogPin(env) {
  const blog = CONTENT_SOURCES.blogs[Math.floor(Math.random() * CONTENT_SOURCES.blogs.length)];

  // Fetch blog metadata (assuming you have a JSON API or parse HTML)
  // For now, use static data
  const content = {
    title: blog.title,
    url: `${SITE_URL}${blog.path}`,
    description: "Complete guide with expert tips and savings calculator",
    image_url: `${SITE_URL}/images/blog-featured-${blog.path.split('/').pop().replace('.html', '')}.jpg`
  };

  return {
    title: content.title,
    description: content.description,
    link: content.url,
    image_url: content.image_url,
    board_id: env.PINTEREST_BOARD_ID || "homepower-bc-heat-pump-rebates",
    rich_metadata: {
      article: {
        headline: content.title,
        description: content.description
      }
    }
  };
}

/**
 * Create a tips/hacks pin
 */
async function createTipsPin(env) {
  const tip = CONTENT_SOURCES.tips[Math.floor(Math.random() * CONTENT_SOURCES.tips.length)];

  // Route to relevant blog post based on keywords
  let relatedBlog = CONTENT_SOURCES.blogs[0];
  for (const blog of CONTENT_SOURCES.blogs) {
    if (tip.keywords.some(kw => blog.title.toLowerCase().includes(kw))) {
      relatedBlog = blog;
      break;
    }
  }

  return {
    title: tip.title,
    description: "Learn more on HomePowerRebate",
    link: `${SITE_URL}${relatedBlog.path}`,
    board_id: env.PINTEREST_BOARD_ID || "homepower-tips-hacks",
    rich_metadata: {
      article: {
        headline: tip.title
      }
    }
  };
}

/**
 * Create a city guide pin
 */
async function createCityPin(env) {
  const city = CONTENT_SOURCES.cities[Math.floor(Math.random() * CONTENT_SOURCES.cities.length)];
  const cityTitle = city.charAt(0).toUpperCase() + city.slice(1).replace('-', ' ');

  // Map city to typical rebate amounts (these would come from your data)
  const rebateAmounts = {
    heat_pump: "$4K–$16K",
    solar: "$5K",
    battery: "$5K"
  };

  return {
    title: `${cityTitle} Homeowners: Get ${rebateAmounts.heat_pump} in Rebates`,
    description: `Heat Pump (${rebateAmounts.heat_pump}) + Solar (${rebateAmounts.solar}) + Battery (${rebateAmounts.battery})`,
    link: `${SITE_URL}/ca/bc/${city}/`,
    board_id: env.PINTEREST_BOARD_ID || "homepower-bc-cities",
    rich_metadata: {
      article: {
        headline: `${cityTitle} Rebates 2026`,
        description: `Complete breakdown of all rebates available in ${cityTitle}`
      }
    }
  };
}

/**
 * Post pin to Pinterest API
 */
async function postToPinterest(pin, env) {
  const response = await fetch(PINTEREST_API_URL, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${env.PINTEREST_ACCESS_TOKEN}`,
      "Content-Type": "application/json",
      "X-Pinterest-API-Version": "v5"
    },
    body: JSON.stringify({
      title: pin.title,
      description: pin.description,
      link: pin.link,
      image_url: pin.image_url,
      board_id: pin.board_id,
      media_source: {
        source_type: "image_url",
        url: pin.image_url
      }
    })
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Pinterest API error: ${response.status} ${error}`);
  }

  return await response.json();
}

/**
 * Log pin posting to D1 database (optional analytics)
 */
async function logPinPosted(db, pin, result) {
  try {
    await db.prepare(`
      INSERT INTO pinterest_pins (pin_id, title, link, posted_at, board_id)
      VALUES (?, ?, ?, ?, ?)
    `).bind(result.id, pin.title, pin.link, new Date().toISOString(), pin.board_id).run();
  } catch (error) {
    console.warn(`[Pinterest] Could not log to D1: ${error.message}`);
  }
}
