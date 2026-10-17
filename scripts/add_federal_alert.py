#!/usr/bin/env python3
"""Put the "email me the day the federal heat pump rebate opens" sign-up box on the pages where people read about it (2026-10-16).

Pages: the federal pillar page and articles, every Canadian province and city heat pump page, and the Nova Scotia HARP pages
(HARP households skew lower income, the group the $10,000 tier is for, so they get their own wording).
Added 2026-10-17 (the launch list is the top metric, so the box goes wherever a Canadian reads about rebates): the homepage
(right under the hero, with id="federal-alert" for the hero link), /ca/, every Canadian province hub (after the open-programs
table), every Canadian city hub and city or province category page (after the rebate cards), the Canadian calculators (after
the calculator), Canadian program pages, Canadian rebate and heat pump blog posts, the rebate finder (/get-quotes/, shown
only when a Canadian province is picked) and the share page /heat-pump-rebate-alert/ (share row always open there; elsewhere
it opens after a signup).
The form posts to the lead router's /alert route (table `alerts`, schema-alerts.sql). One shared component: this script writes
plain HTML from block(), styles are .fed-alert in _partials/nav-footer.html, and the submit handler sits once in the same partial's
SHARED JS (stamped on every page), so a change to the box is one edit here or there, never per page. Which pages get it, with
what words and where, is the JOBS table in main(). Wording states only what data/verified-facts/federal.json says: amounts, early 2027,
and that the income line is not published. Never add retroactivity or a launch date until an official page states it.
The block sits between FED-ALERT-START/END, so re-runs replace it. Placement: right after the FED-HP callout when a page has
one (add_federal_links.py), otherwise before the second <h2> of the article, so readers get the first answer first.
Usage: python3 scripts/add_federal_alert.py"""
import html
import json
from urllib.parse import quote
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402

S, E = "<!-- FED-ALERT-START -->", "<!-- FED-ALERT-END -->"
FED_HP_END = "<!-- FED-HP-END -->"
HERE = "<!-- FED-ALERT-HERE -->"
GUIDE = "/programs/national-heat-pump-rebate/"
SHARE_PAGE = "/heat-pump-rebate-alert/"  # short page made for sharing (scripts/build_alert_page.py); noindex
SHARE_URL = "https://homepowerrebate.com" + SHARE_PAGE
SHARE_TEXT = "Ottawa is bringing in a heat pump rebate of up to $10,000. Get an email the day it opens:"
OTTAWA = "https://www.canada.ca/en/environment-climate-change/campaigns/one-million-home-energy-retrofits.html"
PROVINCES = [("AB", "Alberta"), ("BC", "British Columbia"), ("MB", "Manitoba"), ("NB", "New Brunswick"), ("NL", "Newfoundland and Labrador"),
             ("NS", "Nova Scotia"), ("ON", "Ontario"), ("PE", "Prince Edward Island"), ("QC", "Quebec"), ("SK", "Saskatchewan"),
             ("NT", "Northwest Territories"), ("NU", "Nunavut"), ("YT", "Yukon")]
NAMES = {"st-albert": "St. Albert", "fort-st-john": "Fort St. John", "fort-mcmurray": "Fort McMurray", "niagara-falls": "Niagara Falls",
         "sault-ste-marie": "Sault Ste. Marie", "st-johns": "St. John's"}

# Every box carries the same headline (HEADLINE), so a reader knows at a glance that this is a heat pump rebate sign-up, and the
# two amounts as a small ledger, so the lead line below never repeats them. Each page group gets one lead line that ties the
# rebate to what the reader came for. Grade-6 words. Only claims from data/verified-facts/federal.json (amounts, early 2027,
# stacking, $1,400 savings, $2 billion). Redesigned 2026-10-17: the headline used to change per page and never said "heat pump".
# What a signup gets, shown as a list right above the email field (the promise the confirmation email and the list keep).
GETS = ["A short hello now, so you know it worked", "One email the day applications open",
        "One email when Ottawa says who gets $10,000"]
HEADLINE = "Get an email the day Canada\u2019s new heat pump rebate opens"
FEDERAL = "Applications are not open yet. Ottawa says they open in early 2027, and that you can add this rebate on top of provincial ones."
CITY = "Ottawa says you can add it on top of provincial rebates like the ones on this page."
HARP = ("Getting the heating rebate? A bigger one is coming. Ottawa says homes that switch off oil, propane or electric "
        "baseboard heat save over $1,400 a year on average.")
CLOSED = "The old rebate closed. Ottawa\u2019s new one opens in early 2027, and we\u2019ll tell you the day it does."
HOME = ("Ottawa is putting $2 billion into heat pump rebates for Canadian homes. "
        "We\u2019ll email you the moment applications open, so you can apply right away.")
HUB = "Ottawa says you can add it on top of the {province} rebates you can claim today."
CITY_HUB = "Planning a heat pump in {city}? Ottawa says you can add this on top of provincial rebates."
OTHER = "Planning a heat pump too? This one is on top of the rebates above, and we\u2019ll email you the day it opens."
NOT_COUNTED = "It isn\u2019t open yet, so it\u2019s not in your total. We\u2019ll email you the day it opens."
# posts about closed programs (Greener Homes, the Greener Homes Loan in Ontario, Nova Scotia's OHPA); box goes at <!-- FED-ALERT-HERE -->
CLOSED_PAGES = [("blog/greener-homes-grant-explained", ""), ("blog/ontario-loan-closed", "ON"), ("blog/nova-scotia-heat-pump-rebate-disappeared", "NS")]
HARP_PAGES = ["programs/nova-scotia-heating-assistance-rebate-harp", "blog/nova-scotia-harp-heating-assistance-rebate-explained",
              "blog/nova-scotia-heating-rebate-2026-27-payment-dates-status"]
FEDERAL_PAGES = ["programs/national-heat-pump-rebate", "blog/should-you-wait-federal-heat-pump-rebate",
                 "blog/federal-heat-pump-rebate-stacking-by-province", "blog/heat-pump-natural-gas-home-federal-rebate",
                 "blog/heat-pumps-alberta-saskatchewan-cold-federal-rebate", "blog/fair-heat-pump-quote-canada",
                 "blog/federal-heat-pump-rebate-renters-condos-landlords"]

# Canadian program pages (provincial and utility programs a heat pump buyer reads before the federal one opens)
PROGRAM_PAGES = [("programs/bc-hydro-rebates", "BC"), ("programs/cleanbc-rebates", "BC"), ("programs/fortisbc-rebates", "BC"),
                 ("programs/home-renovation-savings", "ON"), ("programs/save-on-energy-rebates", "ON"), ("programs/enbridge-gas-rebates", "ON"),
                 ("programs/alberta-energy-rebates", "AB"), ("programs/efficiency-nova-scotia", "NS"),
                 ("programs/newfoundland-oil-to-electric-rebate", "NL")]
# Canadian blog posts (data/blog-index.json region) about heat pumps or rebates in general; city variants of BC posts too
BLOG_REGIONS = {"Canada": "", "BC": "BC", "Ontario": "ON", "Alberta": "AB", "Nova Scotia": "NS", "Newfoundland and Labrador": "NL"}
BLOG_TOPIC = re.compile(r"heat-pump|cleanbc|federal|greener|canada|provinces|hpcn|rebate-deadlines|renovation-savings|listicle|"
                        r"rebate-rejected|insulation-rebates|alberta-100|alberta-16|ranked|newfoundland|stack-bc-hydro|energy-saving-ideas")


# How Ottawa says it will work (fact federal-2: canada.ca release, direct deposit per CBC's reading of the government document)
STEPS = [("Apply online", "when your heating breaks or gets old"), ("Approved in 24 hours", "no home energy audit needed"),
         ("Payment approved in 5 days", "sent by direct deposit after you upload receipts")]


def share_row(open_=False):
    """Share buttons. Hidden until a signup on every page except the share page itself; each link carries its own src."""
    u = lambda s: f"{SHARE_URL}?src={s}"
    links = [("Facebook", "facebook", f"https://www.facebook.com/sharer/sharer.php?u={quote(u('share-facebook'), safe='')}"),
             ("Email", "email", f"mailto:?subject={quote('Heat pump rebate of up to $10,000 is coming')}&body={quote(SHARE_TEXT + ' ' + u('share-email'))}"),
             ("Text message", "text", f"sms:?&body={quote(SHARE_TEXT + ' ' + u('share-text'))}")]
    btns = "".join(f'<a href="{html.escape(h)}" data-method="{m}" rel="noopener" target="_blank">{n}</a>' for n, m, h in links)
    btns += f'<button type="button" data-method="copy" data-copy="{u("share-link")}">Copy link</button>'
    lead = "Know someone with old heating? Send them this." if not open_ else "Tell a friend or neighbour:"
    return f'<div class="fed-alert-share"{"" if open_ else " hidden"}><p>{lead}</p><div>{btns}</div></div>'


# Small outdoor heat pump unit (authored SVG, currentColor) so the box reads as "heat pump" before a word is read.
UNIT = ('<svg class="fed-alert-unit" viewBox="0 0 64 56" aria-hidden="true" focusable="false">'
        '<rect x="3" y="5" width="58" height="42" rx="5" fill="none" stroke="currentColor" stroke-width="3"/>'
        '<circle cx="26" cy="26" r="14" fill="none" stroke="currentColor" stroke-width="3"/>'
        '<g class="fed-alert-fan"><path d="M26 26c0-6 2-9 6-9-1 4-3 7-6 9zM26 26c5 3 7 6 5 10-3-2-5-5-5-10zM26 26c-5 3-9 3-11 0 3-2 7-2 11 0z" fill="currentColor"/></g>'
        '<path d="M47 16h8M47 22h8M47 28h8" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>'
        '<path d="M12 47v5M52 47v5" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg>')


def block(lead, province="", city="", follow=False, anchor="", big=False, wrap=False, more=True, share_open=False):
    """The one alert box: a light notice (headline, lead line, the two amounts, how it will work) and a dark sign-up stub.
    province "" shows a province picker; follow=True is the rebate finder version, hidden until a Canadian province is
    picked there (the shared JS reads data-follow). big=True adds "how it will work" (homepage, hubs, federal and heat pump
    pages). wrap=True centres it on full-width pages (homepage, hubs). more=True links the full guide (every page except the
    guide itself)."""
    sel = ""
    if not province and not follow:
        opts = "".join(f'<option value="{c}">{html.escape(n)}</option>' for c, n in PROVINCES)
        sel = f'<label for="fed-alert-prov">Province</label><select id="fed-alert-prov" name="province"><option value="">Your province</option>{opts}</select>'
    data = f' data-province="{province}"' if province else ""
    data += f' data-city="{html.escape(city)}"' if city else ""
    attrs = f' id="{anchor}"' if anchor else ""
    if follow:
        attrs += f' data-follow="gq-region" data-follow-city="gq-city" data-provinces="{" ".join(c.lower() for c, _ in PROVINCES)}" hidden'
    link = f'<p class="fed-alert-more"><a href="{GUIDE}">Read everything we know so far</a></p>' if more else ""
    steps = ""
    if big:
        steps = ('<p class="fed-alert-steps-h">How Ottawa says it will work</p><ol class="fed-alert-steps">'
                 + "".join(f"<li><b>{html.escape(a)}</b> {html.escape(b)}</li>" for a, b in STEPS) + "</ol>")
    pre, post = ('<div class="hp-fed-wrap">', "</div>") if wrap else ("", "")
    how = f'<div class="fed-alert-how">{steps}{link}</div>' if steps or link else ""
    gets = "".join(f"<li>{x}</li>" for x in GETS)
    return (f'{S}{pre}<section class="fed-alert{" fed-alert-big" if big else ""}"{attrs} aria-label="Heat pump rebate email alert"><div class="fed-alert-in">'
            '<div class="fed-alert-main">'
            f'<div class="fed-alert-head">{UNIT}<p class="fed-alert-title">{html.escape(HEADLINE)}</p></div>'
            f'<p class="fed-alert-body">{html.escape(lead)}</p>'
            '<dl class="fed-alert-amounts"><div><dt>Up to $10,000</dt><dd>if your household earns below the median income</dd></div>'
            '<div><dt>$2,000</dt><dd>for other homeowners who qualify</dd></div></dl></div>'
            '<div class="fed-alert-stub">'
            '<p class="fed-alert-badge"><span aria-hidden="true"></span>Applications open early 2027</p>'
            '<p class="fed-alert-ask">Join the launch alert</p>'
            f'<ul class="fed-alert-gets" aria-label="What you get">{gets}</ul>'
            '<p class="fed-alert-count" hidden></p>'
            f'<form class="fed-alert-form" data-list="federal-hp"{data}>'
            '<label for="fed-alert-email">Email</label><input id="fed-alert-email" type="email" name="email" required autocomplete="email" placeholder="Your email">'
            f'{sel}<input class="fed-alert-hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">'
            '<button type="submit">Email me when it opens</button></form>'
            f'<p class="fed-alert-done" role="status" hidden></p>{share_row(share_open)}'
            '<p class="fed-alert-note">Just these emails. No spam, no sales calls, unsubscribe anytime. '
            f'Ottawa also has <a href="{OTTAWA}">its own sign-up</a>.</p></div>{how}</div></section>{post}{E}\n')


def _after_grid(t):
    """End of the first <div class="rebate-grid">, so readers see what they can claim today before the box."""
    m = re.search(r'<div class="rebate-grid">', t)
    if not m:
        return -1
    depth = 0
    for tag in re.finditer(r"<(/?)div\b[^>]*>", t[m.start():]):
        depth += -1 if tag.group(1) else 1
        if depth == 0:
            return m.start() + tag.end()
    return -1


def _after_div(t, opener):
    """End of the div that starts with `opener` (calculator mount, rebate finder card)."""
    a = t.find(opener)
    if a < 0:
        return -1
    depth = 0
    for tag in re.finditer(r"<(/?)div\b[^>]*>", t[a:]):
        depth += -1 if tag.group(1) else 1
        if depth == 0:
            return a + tag.end()
    return -1


def _second_h2(t):
    for opener in ('<article class="article">', "<article>", "<article ", '<main id="main"'):
        a = t.find(opener)
        if a >= 0:
            hs = [m.start() for m in re.finditer(r"<h2[\s>]", t[a:])]
            if len(hs) >= 2:
                return a + hs[1]
    return -1


PLACE = ("here", "fedhp", "h2", "end")  # federal, HARP, closed-program and heat pump pages: unchanged from 2026-10-16


def place(t, blk, how=PLACE):
    # add_federal_links re-inserts its callout with a newline in front, which lands between the callout and this box;
    # drop it so running both scripts again changes nothing.
    t = t.replace(FED_HP_END + "\n" + S, FED_HP_END + S)
    t = re.sub(re.escape(S) + r"[\s\S]*?" + re.escape(E) + r"\n?", "", t)
    for h in how:
        i = -1
        if h == "here":  # hand-edited posts mark the spot themselves
            i = t.find(HERE)
            i = i + len(HERE) if i >= 0 else -1
        elif h == "fedhp":
            i = t.find(FED_HP_END)
            i = i + len(FED_HP_END) if i >= 0 else -1
        elif h.startswith("after:"):
            m = h[6:]
            i = t.find(m)
            i = i + len(m) if i >= 0 else -1
        elif h == "grid":
            i = _after_grid(t)
        elif h == "calc":
            i = _after_div(t, '<div id="rc-mount">')
        elif h == "finder":
            i = _after_div(t, '<div class="gq-card"><h2 class="gq-h" id="gq-r-title">')
        elif h == "h2":
            i = _second_h2(t)
        elif h == "end":
            i = navfooter.content_insert_point(t)
        if i >= 0:
            if h in ("after:<!-- HOME-HERO-END -->", "after:<!-- HUB-TOP-END -->", "after:<!-- HP-LINKS-END -->"):
                return t[:i] + "\n" + blk.rstrip("\n") + t[i:]
            return t[:i] + blk + t[i:]
    return None


def canadian_pages():
    """(rel, copy, province, city, how, kwargs) for every page group beyond the federal, HARP and closed-program posts."""
    regions = json.loads((ROOT / "data" / "regions.json").read_text(encoding="utf-8"))["regions"]
    ca = [r for r in regions if r["country"] == "ca"]
    city_dirs = {(r["code"], c[0].strip("/").split("/")[-1]): c[1] for r in ca for c in r["cities"]}
    out = [("index.html", HOME, "", "", ("after:<!-- HOME-HERO-END -->",), {"anchor": "federal-alert", "big": True, "wrap": True}),
           (SHARE_PAGE.strip("/"), HOME, "", "", ("here",), {"anchor": "federal-alert", "big": True, "share_open": True}),
           ("ca", HUB.replace("the {province} rebates", "provincial rebates"), "", "", ("after:<!-- HP-LINKS-END -->", "h2"), {"big": True, "wrap": True}),
           ("get-quotes", NOT_COUNTED, "", "", ("finder",), {"follow": True})]
    for r in ca:
        code = r["code"]
        if (ROOT / r["path"] / "index.html").exists():
            out.append((r["path"], HUB.format(province=r["name"]), code.upper(), "", ("after:<!-- HUB-TOP-END -->", "fedhp", "h2"), {"big": True, "wrap": True}))
        if (ROOT / "calculator" / code / "index.html").exists():
            out.append((f"calculator/{code}", NOT_COUNTED, code.upper(), "", ("calc",), {}))
        for d in sorted((ROOT / r["path"]).iterdir()):
            if not (d / "index.html").exists() or d.name == "heat-pump":
                continue
            name = city_dirs.get((code, d.name))
            if name:  # city hub, then its category pages
                out.append((str(d.relative_to(ROOT)), CITY_HUB.format(city=name), code.upper(), name, ("grid", "h2"), {"big": True}))
                for c in sorted(d.iterdir()):
                    if (c / "index.html").exists() and c.name != "heat-pump":
                        out.append((str(c.relative_to(ROOT)), OTHER, code.upper(), name, ("grid", "h2"), {}))
            else:  # province topic page (appliances, HRV, EV charger) or region page
                out.append((str(d.relative_to(ROOT)), OTHER, code.upper(), "", ("grid", "h2"), {}))
    out += [(p, FEDERAL, pr, "", ("fedhp", "h2", "end"), {}) for p, pr in PROGRAM_PAGES]
    taken = set(FEDERAL_PAGES) | set(HARP_PAGES) | {p for p, _ in CLOSED_PAGES}
    bc_cities = [s for (c, s) in city_dirs if c == "bc"]
    idx = json.loads((ROOT / "data" / "blog-index.json").read_text(encoding="utf-8"))
    for sec in idx["sections"]:
        for post in sec.get("posts", []):
            slug, reg = post.get("slug", ""), post.get("region", "")
            if reg not in BLOG_REGIONS or not BLOG_TOPIC.search(slug) or f"blog/{slug}" in taken:
                continue
            out.append((f"blog/{slug}", FEDERAL, BLOG_REGIONS[reg], "", ("here", "fedhp", "h2", "end"), {}))
            if reg == "BC":
                for c in bc_cities:
                    if (ROOT / "blog" / f"{slug}-{c}" / "index.html").exists():
                        out.append((f"blog/{slug}-{c}", FEDERAL, "BC", city_dirs[("bc", c)], ("here", "fedhp", "h2", "end"), {}))
    return out


def main():
    jobs = [(p, FEDERAL, "", "", PLACE, {"big": True, "more": p != GUIDE.strip("/")}) for p in FEDERAL_PAGES] + [(p, HARP, "NS", "", PLACE, {}) for p in HARP_PAGES]
    jobs += [(p, CLOSED, pr, "", PLACE, {}) for p, pr in CLOSED_PAGES]
    for f in sorted((ROOT / "ca").glob("*/heat-pump/index.html")):
        jobs.append((str(f.parent.relative_to(ROOT)), FEDERAL, f.parts[-3].upper(), "", PLACE, {"big": True}))
    for f in sorted((ROOT / "ca").glob("*/*/heat-pump/index.html")):
        slug = f.parts[-3]
        jobs.append((str(f.parent.relative_to(ROOT)), CITY, f.parts[-4].upper(), NAMES.get(slug, slug.replace("-", " ").title()), PLACE, {"big": True}))
    jobs += canadian_pages()
    n, missing, seen = 0, [], set()
    for rel, copy, prov, city, how, kw in jobs:
        if rel in seen:
            continue
        seen.add(rel)
        f = ROOT / rel if rel.endswith(".html") else ROOT / rel / "index.html"
        if not f.exists():
            missing.append(rel)
            continue
        t = f.read_text(encoding="utf-8")
        out = place(t, block(copy, prov, city, **kw), how)
        if out is None:
            missing.append(rel)
            continue
        if out != t:
            f.write_text(out, encoding="utf-8")
            n += 1
    print(f"federal alert box: {n} pages changed, {len(seen) - len(missing)} have it")
    for m in missing:
        print("  no place for the box:", m)


if __name__ == "__main__":
    main()
