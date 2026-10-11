// Installer photo proxy for /installers/profiles/ pages. Holds the Google API key and, for one place ID, returns the
// place's first Google photo as a short-lived photoUri plus the author credit and the photo's Google Maps link.
// Google's Places policies forbid storing or caching anything except place IDs, so nothing is stored or cached here:
// every view asks Google again. Cost per view: one Place Details request with only the photos field (Essentials IDs
// Only SKU, no charge) and one Place Photo request (Place Details Photos SKU: 1,000 free a month, then $7 per 1,000).
// MONTHLY_CAP counts Place Photo requests and stops there, so with the default 1,000 the photos never cost anything.
// Bindings: secret GOOGLE_API_KEY, KV namespace USAGE, vars MONTHLY_CAP (default 1000), IP_HOURLY (default 60).

const ORIGINS = ["https://homepowerrebate.com", "https://www.homepowerrebate.com"];
// crawlers render pages with JavaScript too; never spend a photo request on them
const BOTS = /bot|crawl|spider|slurp|preview|lighthouse|headless|inspectiontool|facebookexternalhit|embedly|pingdom/i;
const ID_RE = /^[A-Za-z0-9_-]{10,300}$/;

function cors(origin) {
  return {
    "Access-Control-Allow-Origin": ORIGINS.includes(origin) ? origin : ORIGINS[0],
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Vary": "Origin",
    "Cache-Control": "no-store",
  };
}
const json = (obj, status, origin) => new Response(JSON.stringify(obj), { status, headers: { ...cors(origin), "Content-Type": "application/json" } });
const monthKey = () => "photos:" + new Date().toISOString().slice(0, 7);

export default {
  async fetch(req, env) {
    const origin = req.headers.get("Origin") || "";
    const url = new URL(req.url);
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(origin) });
    if (!ORIGINS.includes(origin)) return json({ error: "forbidden" }, 403, origin);
    if (url.pathname !== "/photo" || req.method !== "GET") return json({ error: "not_found" }, 404, origin);
    if (BOTS.test(req.headers.get("User-Agent") || "")) return json({ none: true }, 200, origin);
    const id = url.searchParams.get("id") || "";
    if (!ID_RE.test(id)) return json({ error: "bad_id" }, 400, origin);
    const width = Math.min(1200, Math.max(200, parseInt(url.searchParams.get("w") || "800", 10) || 800));

    const ip = req.headers.get("CF-Connecting-IP") || "unknown";
    const ipKey = `ip:${ip}:${new Date().toISOString().slice(0, 13)}`;
    const ipUsed = parseInt((await env.USAGE.get(ipKey)) || "0", 10);
    if (ipUsed >= parseInt(env.IP_HOURLY || "60", 10)) return json({ none: true, reason: "slow_down" }, 200, origin);
    const mk = monthKey();
    const used = parseInt((await env.USAGE.get(mk)) || "0", 10);
    if (used >= parseInt(env.MONTHLY_CAP || "1000", 10)) return json({ none: true, reason: "cap" }, 200, origin);

    const key = env.GOOGLE_API_KEY;
    // Place Details with only the photos field: Essentials (IDs Only) SKU, no charge.
    const d = await fetch(`https://places.googleapis.com/v1/places/${encodeURIComponent(id)}`, {
      headers: { "X-Goog-Api-Key": key, "X-Goog-FieldMask": "photos" }, cf: { cacheTtl: 0 },
    });
    if (!d.ok) return json({ none: true }, 200, origin);
    const photo = ((await d.json()).photos || [])[0];
    if (!photo || !photo.name) return json({ none: true }, 200, origin);

    // Count before the billed request so a burst cannot overshoot the cap by much.
    await env.USAGE.put(mk, String(used + 1), { expirationTtl: 60 * 60 * 24 * 40 });
    await env.USAGE.put(ipKey, String(ipUsed + 1), { expirationTtl: 3700 });
    const m = await fetch(`https://places.googleapis.com/v1/${photo.name}/media?maxWidthPx=${width}&skipHttpRedirect=true`, {
      headers: { "X-Goog-Api-Key": key }, cf: { cacheTtl: 0 },
    });
    if (!m.ok) return json({ none: true }, 200, origin);
    const media = await m.json();
    if (!media.photoUri) return json({ none: true }, 200, origin);
    const a = (photo.authorAttributions || [])[0] || {};
    return json({
      src: media.photoUri,
      width: photo.widthPx || null,
      height: photo.heightPx || null,
      author: a.displayName || "",
      authorUri: a.uri || "",
      mapsUri: photo.googleMapsUri || "",
    }, 200, origin);
  },
};
