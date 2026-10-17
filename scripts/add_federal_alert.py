#!/usr/bin/env python3
"""Put the "email me the day the federal heat pump rebate opens" sign-up box on the pages where people read about it (2026-10-16).

Pages: the federal pillar page and articles, every Canadian province and city heat pump page, and the Nova Scotia HARP pages
(HARP households skew lower income, the group the $10,000 tier is for, so they get their own wording).
The form posts to the lead router's /alert route (table `alerts`, schema-alerts.sql); styles live in
_partials/nav-footer.html (.fed-alert); the submit handler is inline in the block. Wording states only what data/verified-facts/federal.json says: amounts, early 2027,
and that the income line is not published. Never add retroactivity or a launch date until an official page states it.
The block sits between FED-ALERT-START/END, so re-runs replace it. Placement: right after the FED-HP callout when a page has
one (add_federal_links.py), otherwise before the second <h2> of the article, so readers get the first answer first.
Usage: python3 scripts/add_federal_alert.py"""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402

S, E = "<!-- FED-ALERT-START -->", "<!-- FED-ALERT-END -->"
# Submit handler, inline because new .js files 403 at Cloudflare and only these pages need it.
JS = 'document.querySelectorAll(\'.fed-alert-form\').forEach(function (f) { f.addEventListener(\'submit\', async function (e) { e.preventDefault(); var box = f.closest(\'.fed-alert\'), done = box.querySelector(\'.fed-alert-done\'), b = f.querySelector(\'button\'), sel = f.querySelector(\'select\'); var t = b.textContent; b.disabled = true; b.textContent = \'Saving...\'; try { var r = await fetch(\'https://leads.homepowerrebate.com/alert\', { method: \'POST\', headers: { \'Content-Type\': \'application/json\' }, body: JSON.stringify({ list: f.dataset.list, email: f.querySelector(\'input[type="email"]\').value, province: (sel && sel.value) || f.dataset.province || \'\', city: f.dataset.city || \'\', page: location.pathname, website: f.querySelector(\'.fed-alert-hp\').value }) }); if (!r.ok) throw new Error(\'alert signup failed\'); f.hidden = true; done.textContent = "You\'re on the list. Check your inbox for a short note from us."; } catch (err) { done.textContent = \'That did not go through. Please try again, or email hello@homepowerrebate.com.\'; b.disabled = false; b.textContent = t; } done.hidden = false; }); });'
FED_HP_END = "<!-- FED-HP-END -->"
OTTAWA = "https://www.canada.ca/en/environment-climate-change/campaigns/one-million-home-energy-retrofits.html"
PROVINCES = [("AB", "Alberta"), ("BC", "British Columbia"), ("MB", "Manitoba"), ("NB", "New Brunswick"), ("NL", "Newfoundland and Labrador"),
             ("NS", "Nova Scotia"), ("ON", "Ontario"), ("PE", "Prince Edward Island"), ("QC", "Quebec"), ("SK", "Saskatchewan"),
             ("NT", "Northwest Territories"), ("NU", "Nunavut"), ("YT", "Yukon")]
NAMES = {"st-albert": "St. Albert", "fort-st-john": "Fort St. John", "fort-mcmurray": "Fort McMurray", "niagara-falls": "Niagara Falls",
         "sault-ste-marie": "Sault Ste. Marie", "st-johns": "St. John's"}
AMOUNTS = "up to $10,000 for households below the median income and $2,000 for other eligible homeowners"

FEDERAL = ("Get an email the day it opens",
           f"Ottawa plans a heat pump rebate of {AMOUNTS}, starting in early 2027. Applications are not open yet.")
CITY = ("Want to know the day it opens?",
        "Applications are not open yet. We'll email you when they open, and when Ottawa publishes the income line.")
HARP = ("Getting the heating rebate? A bigger one may be coming.",
        f"Ottawa plans a heat pump rebate of {AMOUNTS}, starting in early 2027. It says homes moving off oil, propane or "
        "electric resistance heat (like baseboards) save over $1,400 a year on average. The income line is not published yet, so nobody can say "
        "who gets $10,000.")
HARP_PAGES = ["programs/nova-scotia-heating-assistance-rebate-harp", "blog/nova-scotia-harp-heating-assistance-rebate-explained",
              "blog/nova-scotia-heating-rebate-2026-27-payment-dates-status"]
FEDERAL_PAGES = ["programs/national-heat-pump-rebate", "blog/should-you-wait-federal-heat-pump-rebate",
                 "blog/federal-heat-pump-rebate-stacking-by-province", "blog/heat-pump-natural-gas-home-federal-rebate",
                 "blog/heat-pumps-alberta-saskatchewan-cold-federal-rebate", "blog/fair-heat-pump-quote-canada",
                 "blog/federal-heat-pump-rebate-renters-condos-landlords"]


def block(copy, province="", city=""):
    title, body = copy
    sel = ""
    if not province:
        opts = "".join(f'<option value="{c}">{html.escape(n)}</option>' for c, n in PROVINCES)
        sel = f'<label for="fed-alert-prov">Province</label><select id="fed-alert-prov" name="province"><option value="">Your province</option>{opts}</select>'
    data = f' data-province="{province}"' if province else ""
    data += f' data-city="{html.escape(city)}"' if city else ""
    return (f'{S}<section class="fed-alert" aria-label="Federal heat pump rebate email alert">'
            f'<p class="fed-alert-eyebrow">Federal heat pump rebate</p><p class="fed-alert-title">{html.escape(title)}</p>'
            f'<p class="fed-alert-body">{html.escape(body)}</p>'
            f'<form class="fed-alert-form" data-list="federal-hp"{data}>'
            '<label for="fed-alert-email">Email</label><input id="fed-alert-email" type="email" name="email" required autocomplete="email" placeholder="Your email">'
            f'{sel}<input class="fed-alert-hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">'
            '<button type="submit">Email me when it opens</button></form>'
            '<p class="fed-alert-done" role="status" hidden></p>'
            '<p class="fed-alert-note">We only email you about this rebate. Unsubscribe anytime. '
            f'Ottawa also has <a href="{OTTAWA}">its own sign-up</a>.</p></section><script>{JS}</script>{E}\n')


def place(t, blk):
    t = re.sub(re.escape(S) + r"[\s\S]*?" + re.escape(E) + r"\n?", "", t)
    i = t.find(FED_HP_END)
    if i >= 0:
        i += len(FED_HP_END)
        return t[:i] + blk + t[i:]
    a = t.find('<article class="article">')
    if a >= 0:
        hs = [m.start() for m in re.finditer(r"<h2[\s>]", t[a:])]
        if len(hs) >= 2:
            i = a + hs[1]
            return t[:i] + blk + t[i:]
    i = navfooter.content_insert_point(t)
    return t[:i] + blk + t[i:] if i >= 0 else None


def main():
    jobs = [(p, FEDERAL, "", "") for p in FEDERAL_PAGES] + [(p, HARP, "NS", "") for p in HARP_PAGES]
    for f in sorted((ROOT / "ca").glob("*/heat-pump/index.html")):
        jobs.append((str(f.parent.relative_to(ROOT)), FEDERAL, f.parts[-3].upper(), ""))
    for f in sorted((ROOT / "ca").glob("*/*/heat-pump/index.html")):
        slug = f.parts[-3]
        jobs.append((str(f.parent.relative_to(ROOT)), CITY, f.parts[-4].upper(), NAMES.get(slug, slug.replace("-", " ").title())))
    n, missing = 0, []
    for rel, copy, prov, city in jobs:
        f = ROOT / rel / "index.html"
        if not f.exists():
            missing.append(rel)
            continue
        t = f.read_text(encoding="utf-8")
        out = place(t, block(copy, prov, city))
        if out is None:
            missing.append(rel)
            continue
        if out != t:
            f.write_text(out, encoding="utf-8")
            n += 1
    print(f"federal alert box: {n} pages changed, {len(jobs) - len(missing)} have it")
    for m in missing:
        print("  no place for the box:", m)


if __name__ == "__main__":
    main()
