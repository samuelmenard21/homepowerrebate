// Cloudflare Pages Function for the homepage only (_routes.json limits it to "/", so no other page runs code).
// Adds <html data-country="US|CA"> from the visitor's IP country, so the homepage puts that country first
// (order rules in _partials/templates/home.css). Both countries' content is always in the page; only the order changes.
// Other countries get the page unchanged, and the page's own time zone check (build_home.country_script) decides.
export async function onRequest(context) {
  const res = await context.next();
  const country = context.request.cf && context.request.cf.country;
  const type = res.headers.get('content-type') || '';
  if ((country !== 'US' && country !== 'CA') || !type.includes('text/html')) return res;
  const out = new HTMLRewriter()
    .on('html', { element(el) { el.setAttribute('data-country', country); } })
    .transform(res);
  const headers = new Headers(out.headers);
  headers.set('Vary', 'Accept-Encoding');
  headers.set('Cache-Control', 'private, max-age=0, must-revalidate');
  return new Response(out.body, { status: out.status, headers });
}
