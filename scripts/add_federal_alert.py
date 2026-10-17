#!/usr/bin/env python3
"""Put the "email me the day the federal heat pump rebate opens" sign-up box on the pages where people read about it (2026-10-16).

Pages: the federal pillar page and articles, every Canadian province and city heat pump page, and the Nova Scotia HARP pages
(HARP households skew lower income, the group the $10,000 tier is for, so they get their own wording).
Added 2026-10-17 (the launch list is the top metric, so the box goes wherever a Canadian reads about rebates): the homepage
(right under the hero, with id="federal-alert" for the hero link), /ca/, every Canadian province hub (after the open-programs
table), every Canadian city hub and city or province category page (after the rebate cards), the Canadian calculators (after
the calculator), Canadian program pages, Canadian rebate and heat pump blog posts, and the rebate finder (/get-quotes/, shown
only when a Canadian province is picked).
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
OTTAWA = "https://www.canada.ca/en/environment-climate-change/campaigns/one-million-home-energy-retrofits.html"
PROVINCES = [("AB", "Alberta"), ("BC", "British Columbia"), ("MB", "Manitoba"), ("NB", "New Brunswick"), ("NL", "Newfoundland and Labrador"),
             ("NS", "Nova Scotia"), ("ON", "Ontario"), ("PE", "Prince Edward Island"), ("QC", "Quebec"), ("SK", "Saskatchewan"),
             ("NT", "Northwest Territories"), ("NU", "Nunavut"), ("YT", "Yukon")]
NAMES = {"st-albert": "St. Albert", "fort-st-john": "Fort St. John", "fort-mcmurray": "Fort McMurray", "niagara-falls": "Niagara Falls",
         "sault-ste-marie": "Sault Ste. Marie", "st-johns": "St. John's"}

# Every box shows the two amounts as big numbers, so the copy below does not repeat them. Grade-6 words, and the title says
# what the reader signs up for. Only claims from data/verified-facts/federal.json (amounts, early 2027, stacking, $1,400 savings).
FIRST = "Be first in line. Get an email the day it opens."
FEDERAL = (FIRST, "Applications are not open yet. Ottawa says they open in early 2027, and that you can add this rebate on top of provincial ones.")
CITY = (FIRST, "Applications open in early 2027. Ottawa says you can add it on top of provincial rebates like the ones on this page.")
HARP = ("Getting the heating rebate? A bigger rebate is coming.",
        "Ottawa says homes that switch off oil, propane or electric baseboard heat save over $1,400 a year on average. "
        "Applications open in early 2027. Get an email the day they do.")
CLOSED = ("The old rebate closed. A new one opens in 2027.",
          "Get an email the day applications open, so you can apply right away.")
HOME = (FIRST, "Ottawa is putting $2 billion into heat pump rebates for Canadian homes. Applications open in early 2027. "
        "Sign up and we'll email you the moment they open, so you can apply right away.")
HUB = (FIRST, "Applications open in early 2027. Ottawa says you can add it on top of the {province} rebates you can claim today.")
CITY_HUB = ("{city}: be first in line for up to $10,000",
            "Ottawa's new heat pump rebate opens in early 2027. Get an email the day it opens, so you can apply right away.")
OTHER = ("Planning a heat pump too? Up to $10,000 is coming.",
         "Ottawa's new heat pump rebate opens in early 2027. Get an email the day it opens.")
NOT_COUNTED = ("Coming in 2027, and not in your total yet",
               "Ottawa's new heat pump rebate is not open, so we don't count it here. Get an email the day it opens.")
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


def block(copy, province="", city="", follow=False, anchor="", big=False, wrap=False, more=True):
    """The one alert box. province "" shows a province picker; follow=True is the rebate finder version, hidden until a
    Canadian province is picked there (the shared JS reads data-follow). big=True adds "how it will work" (homepage, hubs,
    federal and heat pump pages). wrap=True centres it on full-width pages (homepage, hubs).
    more=True links the full guide (every page except the guide itself)."""
    title, body = copy
    sel = ""
    if not province and not follow:
        opts = "".join(f'<option value="{c}">{html.escape(n)}</option>' for c, n in PROVINCES)
        sel = f'<label for="fed-alert-prov">Province</label><select id="fed-alert-prov" name="province"><option value="">Your province</option>{opts}</select>'
    data = f' data-province="{province}"' if province else ""
    data += f' data-city="{html.escape(city)}"' if city else ""
    attrs = f' id="{anchor}"' if anchor else ""
    if follow:
        attrs += f' data-follow="gq-region" data-follow-city="gq-city" data-provinces="{" ".join(c.lower() for c, _ in PROVINCES)}" hidden'
    link = f'<p class="fed-alert-more"><a href="{GUIDE}">Read everything we know so far &rarr;</a></p>' if more else ""
    steps = ""
    if big:
        steps = ('<p class="fed-alert-steps-h">How Ottawa says it will work</p><ol class="fed-alert-steps">'
                 + "".join(f"<li><b>{html.escape(a)}</b> {html.escape(b)}</li>" for a, b in STEPS) + "</ol>")
    pre, post = ('<div class="hp-fed-wrap">', "</div>") if wrap else ("", "")
    return (f'{S}{pre}<section class="fed-alert{" fed-alert-big" if big else ""}"{attrs} aria-label="Federal heat pump rebate email alert">'
            '<div class="fed-alert-top"><p class="fed-alert-eyebrow">New federal heat pump rebate</p>'
            '<p class="fed-alert-badge"><span aria-hidden="true"></span>Opens early 2027</p></div>'
            '<div class="fed-alert-amounts"><p><b>$10,000</b><span>if your household earns below the median income</span></p>'
            '<p><b>$2,000</b><span>for other homeowners who qualify</span></p></div>'
            f'<p class="fed-alert-title">{html.escape(title)}</p>'
            f'<p class="fed-alert-body">{html.escape(body)}</p>{steps}{link}'
            f'<form class="fed-alert-form" data-list="federal-hp"{data}>'
            '<label for="fed-alert-email">Email</label><input id="fed-alert-email" type="email" name="email" required autocomplete="email" placeholder="Your email">'
            f'{sel}<input class="fed-alert-hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">'
            '<button type="submit">Email me when it opens</button></form>'
            '<p class="fed-alert-done" role="status" hidden></p>'
            '<p class="fed-alert-note"><b>What you get:</b> a quick hello now, one email the day applications open, and one when Ottawa says who gets $10,000. That&#x27;s it. No spam, unsubscribe anytime. '
            f'Ottawa also has <a href="{OTTAWA}">its own sign-up</a>.</p></section>{post}{E}\n')


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
           ("ca", (HUB[0], HUB[1].replace("the {province} rebates", "provincial rebates")), "", "", ("after:<!-- HP-LINKS-END -->", "h2"), {"big": True, "wrap": True}),
           ("get-quotes", NOT_COUNTED, "", "", ("finder",), {"follow": True})]
    for r in ca:
        code = r["code"]
        if (ROOT / r["path"] / "index.html").exists():
            out.append((r["path"], (HUB[0], HUB[1].format(province=r["name"])), code.upper(), "", ("after:<!-- HUB-TOP-END -->", "fedhp", "h2"), {"big": True, "wrap": True}))
        if (ROOT / "calculator" / code / "index.html").exists():
            out.append((f"calculator/{code}", NOT_COUNTED, code.upper(), "", ("calc",), {}))
        for d in sorted((ROOT / r["path"]).iterdir()):
            if not (d / "index.html").exists() or d.name == "heat-pump":
                continue
            name = city_dirs.get((code, d.name))
            if name:  # city hub, then its category pages
                out.append((str(d.relative_to(ROOT)), (CITY_HUB[0].format(city=name), CITY_HUB[1]), code.upper(), name, ("grid", "h2"), {"big": True}))
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
