// Roof check proxy. Holds the Google API key, counts lookups, and refuses past a monthly cap so the
// Google free allowance (10,000 Solar API Building Insights and 10,000 Geocoding requests a month) is never exceeded.
// One lookup = one Geocoding request + one Building Insights request. Nothing from Google is stored or cached (Solar API policy).
// Bindings: secret GOOGLE_API_KEY, KV namespace USAGE, vars MONTHLY_CAP (default 8000), IP_HOURLY (default 6).

const ORIGINS = ["https://homepowerrebate.com", "https://www.homepowerrebate.com"];

function cors(origin) {
  const ok = ORIGINS.includes(origin);
  return {
    "Access-Control-Allow-Origin": ok ? origin : ORIGINS[0],
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
    "Cache-Control": "no-store",
  };
}
const json = (obj, status, origin) => new Response(JSON.stringify(obj), { status, headers: { ...cors(origin), "Content-Type": "application/json" } });
const monthKey = () => "usage:" + new Date().toISOString().slice(0, 7);

export default {
  async fetch(req, env) {
    const origin = req.headers.get("Origin") || "";
    const url = new URL(req.url);
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(origin) });
    if (!ORIGINS.includes(origin)) return json({ error: "forbidden" }, 403, origin);
    const cap = parseInt(env.MONTHLY_CAP || "8000", 10);

    if (url.pathname === "/status" && req.method === "GET") {
      const used = parseInt((await env.USAGE.get(monthKey())) || "0", 10);
      return json({ open: used < cap }, 200, origin);
    }
    if (url.pathname !== "/check" || req.method !== "POST") return json({ error: "not_found" }, 404, origin);

    let body;
    try { body = await req.json(); } catch { return json({ error: "bad_request" }, 400, origin); }
    const address = String(body.address || "").trim();
    const country = body.country === "CA" ? "CA" : body.country === "US" ? "US" : "";
    if (address.length < 8 || address.length > 200 || !country) return json({ error: "bad_address" }, 400, origin);

    // Per-visitor limit (stops one person burning the month).
    const ip = req.headers.get("CF-Connecting-IP") || "unknown";
    const ipKey = `ip:${ip}:${new Date().toISOString().slice(0, 13)}`;
    const ipUsed = parseInt((await env.USAGE.get(ipKey)) || "0", 10);
    if (ipUsed >= parseInt(env.IP_HOURLY || "6", 10)) return json({ error: "slow_down" }, 429, origin);

    // Monthly hard cap. Increment first so a burst cannot overshoot by much.
    const mk = monthKey();
    const used = parseInt((await env.USAGE.get(mk)) || "0", 10);
    if (used >= cap) return json({ error: "cap" }, 429, origin);
    await env.USAGE.put(mk, String(used + 1), { expirationTtl: 60 * 60 * 24 * 40 });
    await env.USAGE.put(ipKey, String(ipUsed + 1), { expirationTtl: 3700 });

    const key = env.GOOGLE_API_KEY;
    const g = await fetch(`https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&components=country:${country}&key=${key}`, { cf: { cacheTtl: 0 } });
    const gj = await g.json();
    if (gj.status !== "OK" || !gj.results || !gj.results.length) return json({ error: "not_found_address" }, 404, origin);
    const r = gj.results[0];
    const types = r.types || [];
    if (!(types.includes("street_address") || types.includes("premise") || types.includes("subpremise"))) return json({ error: "need_street_address" }, 422, origin);
    const comp = (t) => (r.address_components || []).find((c) => c.types.includes(t));
    const admin = comp("administrative_area_level_1");
    const loc = r.geometry.location;

    const s = await fetch(`https://solar.googleapis.com/v1/buildingInsights:findClosest?location.latitude=${loc.lat}&location.longitude=${loc.lng}&requiredQuality=BASE&key=${key}`, { cf: { cacheTtl: 0 } });
    if (s.status === 404) return json({ error: "no_data", region: admin ? admin.short_name : "", country }, 404, origin);
    if (!s.ok) return json({ error: "upstream" }, 502, origin);
    const b = await s.json();
    const sp = b.solarPotential || {};
    const configs = (sp.solarPanelConfigs || []).map((c) => ({ panels: c.panelsCount, dcKwh: Math.round(c.yearlyEnergyDcKwh) }));
    // Thin the list so the response stays small.
    const step = Math.max(1, Math.floor(configs.length / 40));
    const thin = configs.filter((_, i) => i % step === 0 || i === configs.length - 1);
    return json({
      country, region: admin ? admin.short_name : "", address: r.formatted_address,
      imageryQuality: b.imageryQuality, imageryDate: b.imageryDate,
      maxPanels: sp.maxArrayPanelsCount, panelWatts: sp.panelCapacityWatts,
      maxSunshineHours: Math.round(sp.maxSunshineHoursPerYear || 0),
      roofAreaM2: sp.wholeRoofStats ? Math.round(sp.wholeRoofStats.areaMeters2) : null,
      configs: thin,
    }, 200, origin);
  },
};
