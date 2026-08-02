/**
 * Meta Automation Worker for HomePowerRebate
 *
 * Two posts a day, each with a distinct job:
 *
 *   08:00 PT — a question. No link. This is what earns reach: Facebook
 *              suppresses posts that send traffic off-platform, so a page
 *              publishing nothing but links stays invisible.
 *   18:00 PT — a link, cycling through guides, Q&A pages, blog posts and
 *              city pages.
 *
 * Both pools advance by day rather than being sampled at random, so the full
 * library gets covered instead of some entries repeating while others never
 * surface. With 18 questions and 46 link targets, nothing repeats inside a
 * month and a half.
 */

import { QUESTIONS, LINKS, CITIES } from "./content.js";

const FACEBOOK_GRAPH_API_URL = "https://graph.facebook.com/v18.0";
const META_GRAPH_API_URL = "https://graph.instagram.com/v18.0";
const SITE_URL = "https://homepowerrebate.com";

// Cloudflare crons are UTC. Must match wrangler.toml exactly — the scheduled
// handler routes on these strings.
const CRON_QUESTION = "0 15 * * *";  // 08:00 Pacific
const CRON_LINK     = "0 1 * * *";   // 18:00 Pacific

// Provincial programs, so the figures hold across BC rather than varying by city.
const REBATES = { heatPump: "$4K–$16K", solar: "up to $5K", battery: "up to $5K" };

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return handleHealthCheck(env);
    }

    if (request.method === "POST" && url.pathname === "/test") {
      // ?type=question or ?type=link to exercise a specific slot; defaults to
      // whichever the schedule would post next.
      const type = url.searchParams.get("type") || "link";
      return handleMetaPost(env, type === "question" ? "question" : "link");
    }

    return new Response("Meta automation worker is running", { status: 200 });
  },

  async scheduled(event, env) {
    const slot = event.cron === CRON_QUESTION ? "question" : "link";
    console.log(`[Meta] Cron ${event.cron} -> ${slot} slot`);
    return handleMetaPost(env, slot);
  }
};

/**
 * Index into a pool by day, so consecutive days advance through the list.
 * Stateless — no KV or D1 needed to remember position.
 */
function cycleIndex(length, offset = 0) {
  const daysSinceEpoch = Math.floor(Date.now() / 86_400_000);
  return (daysSinceEpoch + offset) % length;
}

/**
 * Link pool: everything in content.js plus one entry per city page.
 */
function linkPool() {
  const cityEntries = CITIES.map((city) => {
    const name = city.charAt(0).toUpperCase() + city.slice(1).replace(/-/g, " ");
    return {
      path: `/ca/bc/${city}/`,
      hook: `${name} homeowners — here's what's actually on the table right now.\n\n` +
            `💡 Heat pump: ${REBATES.heatPump}\n` +
            `☀️ Solar: ${REBATES.solar}\n` +
            `🔋 Battery: ${REBATES.battery}\n\n` +
            `Stacked in the right order, that covers most of a retrofit. The order is the part people get wrong.`,
      tags: `#${name.replace(/\s/g, "")} #BritishColumbia #BCHydro #CleanBC`
    };
  });
  return [...LINKS, ...cityEntries];
}

async function handleMetaPost(env, slot) {
  try {
    console.log(`[Meta] ${slot} post at ${new Date().toISOString()}`);

    if (!env.META_ACCESS_TOKEN) {
      throw new Error("META_ACCESS_TOKEN not set in Cloudflare secrets");
    }
    if (!env.FACEBOOK_PAGE_ID) {
      throw new Error("FACEBOOK_PAGE_ID not set in Cloudflare secrets");
    }

    const post = slot === "question" ? buildQuestionPost() : buildLinkPost();

    const result = await postToFacebook(post, env);
    console.log(`[Meta] Facebook post created: ${result.id}`);

    // Instagram needs a real, reachable image. Questions have none, so they
    // stay Facebook-only.
    let instagramResult = null;
    if (env.INSTAGRAM_BUSINESS_ACCOUNT_ID && post.image_url) {
      instagramResult = await postToInstagram(post, env);
      console.log(`[Meta] Instagram post created: ${instagramResult.id}`);
    }

    const platforms = ["facebook"];
    if (instagramResult) platforms.push("instagram");

    return json({
      success: true,
      post_id: result.id,
      slot,
      target: post.path || null,
      platforms
    }, 200);

  } catch (error) {
    console.error(`[Meta] Error: ${error.message}`);
    return json({ success: false, slot, error: error.message }, 500);
  }
}

function buildQuestionPost() {
  return {
    caption: QUESTIONS[cycleIndex(QUESTIONS.length)],
    path: null,
    campaign: "question"
  };
}

function buildLinkPost() {
  const pool = linkPool();
  const item = pool[cycleIndex(pool.length)];
  return {
    caption: `${item.hook}\n\n${item.tags}`,
    path: item.path,
    campaign: campaignFor(item.path)
  };
}

/**
 * Group UTM campaigns by content type so GA4 can show which format converts,
 * rather than lumping every link into one bucket.
 */
function campaignFor(path) {
  if (path.startsWith("/guides/")) return "guide";
  if (path.startsWith("/questions/")) return "qa";
  if (path.startsWith("/ca/bc/")) return `city-${path.split("/")[3]}`;
  return "blog";
}

function trackedLink(path, medium, campaign) {
  return `${SITE_URL}${path}?utm_source=meta&utm_medium=${medium}&utm_campaign=${campaign}`;
}

async function postToFacebook(post, env) {
  // The `link` param renders its own preview card, so the URL is deliberately
  // kept out of the message body. Question posts carry no path and publish as
  // a plain status update.
  const body = { message: post.caption };
  if (post.path) {
    body.link = trackedLink(post.path, "facebook", post.campaign);
  }

  const response = await fetch(
    `${FACEBOOK_GRAPH_API_URL}/${env.FACEBOOK_PAGE_ID}/feed`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${env.META_ACCESS_TOKEN}`
      },
      body: JSON.stringify(body)
    }
  );

  if (!response.ok) {
    throw new Error(`Facebook API error: ${response.status} ${await response.text()}`);
  }
  return response.json();
}

async function postToInstagram(post, env) {
  const create = await fetch(
    `${META_GRAPH_API_URL}/${env.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${env.META_ACCESS_TOKEN}`
      },
      body: JSON.stringify({
        image_url: post.image_url,
        // Instagram captions can't hold a clickable link, so point at the bio.
        caption: `${post.caption}\n\nLink in bio 🔗`
      })
    }
  );

  if (!create.ok) {
    throw new Error(`Instagram API error: ${create.status} ${await create.text()}`);
  }

  const { id: creationId } = await create.json();

  const publish = await fetch(
    `${META_GRAPH_API_URL}/${env.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${env.META_ACCESS_TOKEN}`
      },
      body: JSON.stringify({ creation_id: creationId })
    }
  );

  if (!publish.ok) {
    throw new Error(`Instagram publish error: ${publish.status} ${await publish.text()}`);
  }
  return publish.json();
}

/**
 * Read-only credential check. Confirms the stored token still works without
 * publishing, and previews what the next two posts will be.
 */
async function handleHealthCheck(env) {
  const pool = linkPool();
  const report = {
    token_set: Boolean(env.META_ACCESS_TOKEN),
    page_id_set: Boolean(env.FACEBOOK_PAGE_ID),
    instagram_configured: Boolean(env.INSTAGRAM_BUSINESS_ACCOUNT_ID),
    library: {
      questions: QUESTIONS.length,
      link_targets: pool.length,
      cycle_days: `${QUESTIONS.length} / ${pool.length}`
    },
    next_up: {
      question: QUESTIONS[cycleIndex(QUESTIONS.length)].split("\n")[0],
      link: pool[cycleIndex(pool.length)].path
    }
  };

  if (!report.token_set || !report.page_id_set) {
    return json({ ...report, healthy: false, error: "Missing token or page ID" }, 500);
  }

  const res = await fetch(
    `${FACEBOOK_GRAPH_API_URL}/${env.FACEBOOK_PAGE_ID}?fields=id,name&access_token=${env.META_ACCESS_TOKEN}`
  );
  const data = await res.json();

  if (!res.ok) {
    return json({ ...report, healthy: false, error: data?.error?.message || `HTTP ${res.status}` }, 502);
  }

  return json({ ...report, healthy: true, page_name: data.name, page_id: data.id }, 200);
}

function json(obj, status) {
  return new Response(JSON.stringify(obj, null, 2), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}
