#!/usr/bin/env python3
"""/heat-pump-rebate-alert/: a short page made for sharing (Facebook groups, Reddit, texts, installer emails), 2026-10-17.
Redesigned 2026-10-24 as a landing page: photo hero with the sign-up panel beside the message, icon stat cards for the two
amounts, how-it-will-work step cards, the 60 second video, what the emails are, the provincial rebates open today (stack),
and who we are. The sign-up panel is the shared stub() from add_federal_alert.py inside a .fed-alert wrapper, so the shared
submit handler, share row and analytics events work unchanged. Design lives in _partials/templates/alertpage.css (scoped
under .ap). noindex, follow: the full guide (/programs/national-heat-pump-rebate/) is the page that should rank; this one
would only compete with it. Links shared from here carry ?src=, so the weekly report (federal_alert_report.py) shows what works.
Copy is Grade 6 and states only what data/verified-facts/federal.json says (federal-0 amounts and date, federal-2 steps,
federal-3 stacking, the $1,400 savings line in federal-0's eligibility). Never add retroactivity, an income line or a date
before Ottawa does. The video comes from data/youtube-embeds.json (id bU26pKKzwQg's 60 second sibling, see that file).
Usage: python3 scripts/build_alert_page.py, then python3 scripts/post_steps.py and python3 scripts/build_og_cards.py --only heat-pump-rebate-alert"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import add_federal_alert as fed  # noqa: E402
import add_youtube_embeds as yt  # noqa: E402
import apply_canonical_nav_footer as navfooter  # noqa: E402
import page_kit as kit  # noqa: E402

PATH = "/heat-pump-rebate-alert/"
TITLE = "Up to $10,000 for a Heat Pump: Get an Email the Day It Opens"
DESC = "Ottawa's new heat pump rebate opens in early 2027: up to $10,000 below the median income, $2,000 for other homeowners. Get one email the day applications open."
OTTAWA = fed.OTTAWA
RELEASE = "https://www.canada.ca/en/environment-climate-change/news/2026/10/prime-minister-carney-announces-landmark-investment-to-retrofit-one-million-homes-cutting-energy-costs-and-emissions.html"
VIDEO_ID = "gsgLyL0gCH0"
e = html.escape


def icon(name, cls="ap-ico"):
    """Authored line icons (24 px grid, currentColor, decorative)."""
    d = {
        "house-dollar": '<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10v9.5h13V10"/><path d="M12 9.4v6.2M14 11c-.4-.6-1.1-.9-2-.9-1.1 0-2 .5-2 1.4s.8 1.2 2 1.4 2 .5 2 1.4-.9 1.4-2 1.4c-.9 0-1.7-.3-2-.9"/>',
        "coins": '<ellipse cx="9" cy="8" rx="5.5" ry="2.8"/><path d="M3.5 8v4c0 1.5 2.5 2.8 5.5 2.8s5.5-1.3 5.5-2.8V8"/><path d="M14.5 11.2c.5.1 1 .1 1.5.1 3 0 5.5-1.2 5.5-2.8V6.3c0-1.500-2.500-2.800-5.500-2.800-1.600 0-3 .3-4 .9"/><path d="M3.5 12v4c0 1.500 2.500 2.800 5.500 2.800s5.500-1.300 5.500-2.800v-4"/>',
        "calendar": '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/><path d="m9 15 2 2 4-4"/>',
        "laptop": '<rect x="5" y="5" width="14" height="10" rx="1.800"/><path d="M2.500 19h19l-1.700-4H4.200z"/>',
        "clock-check": '<circle cx="12" cy="12" r="8.500"/><path d="M12 7.500V12l3 1.800"/>',
        "bank": '<path d="M3 9.500 12 4l9 5.500"/><path d="M5 10v7M9.500 10v7M14.500 10v7M19 10v7M3 20h18M3 17h18"/>',
        "mail": '<rect x="3" y="5.500" width="18" height="13" rx="2.500"/><path d="m4 8 8 5.500L20 8"/>',
        "bell": '<path d="M6 16.500V11a6 6 0 0 1 12 0v5.500l1.500 2h-15z"/><path d="M10 21h4"/>',
        "doc": '<path d="M7 3.500h7.500L19 8v12.500H7z"/><path d="M14 3.500V8.500h5M10 13h6M10 16.500h6"/>',
        "shield": '<path d="M12 3.500 19 6v5.500c0 4.200-2.900 7.300-7 9-4.100-1.700-7-4.800-7-9V6z"/><path d="m8.800 12 2.200 2.200 4.200-4.400"/>',
        "heart": '<path d="M12 20s-7.500-4.300-7.500-10A4.300 4.300 0 0 1 12 7.500 4.300 4.300 0 0 1 19.500 10c0 5.700-7.500 10-7.500 10z"/>',
        "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
        "leaf": '<path d="M5 19c0-8 5-13 14-14 0 9-5 14-13 14"/><path d="M5 19c2-4 5-7 9-9"/>',
        "search": '<circle cx="11" cy="11" r="6.500"/><path d="m16 16 4.500 4.500"/>',
        "ext": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
        "thermo": '<path d="M10 14.500V5a2 2 0 0 1 4 0v9.500a4 4 0 1 1-4 0z"/><path d="M12 9v7"/>',
    }[name]
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{d}</svg>'


def stat(ic, big, label, tone=""):
    return (f'<li class="ap-stat{" " + tone if tone else ""}">{icon(ic, "ap-stat-ico")}'
            f'<div><b class="ap-stat-n">{big}</b><span class="ap-stat-l">{label}</span></div></li>')


def hero():
    opts = "".join(f'<option value="{c}">{e(n)}</option>' for c, n in fed.PROVINCES)
    sel = f'<label for="fed-alert-prov">Province</label><select id="fed-alert-prov" name="province"><option value="">Your province</option>{opts}</select>'
    panel = f'<section class="fed-alert ap-panel" id="federal-alert" aria-label="Heat pump rebate email alert">{fed.stub(sel, "", True, "Get the launch-day email")}</section>'
    img = "/assets/learn/heat-pump-house"
    return ('<section class="ap-hero"><picture class="ap-hero-bg">'
            f'<img src="{img}-1200.webp" srcset="{img}-640.webp 640w, {img}-1200.webp 1200w, {img}-1600.webp 1600w" sizes="100vw" width="1600" height="1067" '
            'alt="A heat pump unit beside the front door of a modern home" fetchpriority="high"></picture>'
            '<div class="ap-wrap ap-hero-in"><div class="ap-hero-copy">'
            f'<p class="ap-badge">{icon("calendar", "ap-badge-ico")}Opens early 2027</p>'
            '<h1>Up to $10,000 for a heat pump. <span>Be first in line.</span></h1>'
            "<p class=\"ap-lead\">Ottawa is bringing in a new heat pump rebate in early 2027. Put in your email and we'll tell you the day it opens.</p>"
            '<ul class="ap-stats">'
            + stat("house-dollar", "<small>Up to</small>$10,000", "if your household earns below the median income", "is-lead")
            + stat("coins", "<small>Other homeowners</small>$2,000", "if you qualify")
            + '</ul>'
            '<ul class="ap-trust">'
            f'<li>{icon("shield")}<span>Free, and no sales calls</span></li>'
            f'<li>{icon("mail")}<span>Only emails about this rebate</span></li>'
            f'<li>{icon("heart")}<span>Unsubscribe anytime</span></li></ul>'
            f'</div>{panel}</div></section>')


def steps():
    cards = [("laptop", "Apply online", "when your heating breaks or gets old"),
             ("clock-check", "Approved in 24 hours", "no home energy audit needed"),
             ("bank", "Payment approved in 5 days", "sent by direct deposit after you upload receipts")]
    li = "".join(f'<li class="ap-step"><span class="ap-step-n" aria-hidden="true">{i}</span>{icon(ic, "ap-step-ico")}<h3>{e(h)}</h3><p>{e(b)}</p></li>'
                 for i, (ic, h, b) in enumerate(cards, 1))
    return ('<section class="ap-band" aria-labelledby="ap-how"><div class="ap-wrap"><div class="ap-head"><p class="ap-eyebrow">The plan so far</p>'
            '<h2 id="ap-how">How Ottawa says it will work</h2><p>These are plans from the announcement, not final rules. '
            "Who qualifies, which homes and which heating fuels count are not published yet.</p></div>"
            f'<ol class="ap-steps">{li}</ol>'
            f'<p class="ap-source">Source: <a class="ap-link" href="{RELEASE}" rel="noopener" target="_blank">Government of Canada announcement, October 8, 2026{icon("ext", "ap-ext")}</a></p></div></section>')


def video():
    cfg = json.loads((ROOT / "data" / "youtube-embeds.json").read_text(encoding="utf-8"))
    v = next(x for x in cfg["videos"] if x["id"] == VIDEO_ID)
    return yt.block(cfg, v, PATH, "See how it works in 60 seconds")


def emails():
    items = [("mail", "A quick hello now", "So you know it worked."),
             ("bell", "One email the day applications open", "So you can apply right away, not weeks later."),
             ("doc", "One email when Ottawa says who gets $10,000", "When the income line is published.")]
    li = "".join(f'<li class="ap-card">{icon(ic, "ap-card-ico")}<h3>{e(h)}</h3><p>{e(b)}</p></li>' for ic, h, b in items)
    return ('<section class="ap-band ap-band-warm" aria-labelledby="ap-emails"><div class="ap-wrap ap-split">'
            '<div class="ap-split-copy"><p class="ap-eyebrow">What you will get</p><h2 id="ap-emails">Three emails. That is all.</h2>'
            "<p>No spam, and you can unsubscribe anytime. We don't sell your email.</p>"
            f'<ul class="ap-cards">{li}</ul></div><div class="ap-split-media">{video()}</div></div></section>')


def savings():
    return ('<section class="ap-save" aria-labelledby="ap-save"><picture class="ap-save-bg"><img src="/assets/learn/thermostat-1200.webp" '
            'srcset="/assets/learn/thermostat-640.webp 640w, /assets/learn/thermostat-1200.webp 1200w" sizes="100vw" width="1200" height="800" alt="" loading="lazy"></picture>'
            '<div class="ap-wrap ap-save-in"><div class="ap-save-card">'
            f'{icon("thermo", "ap-save-ico")}<p class="ap-save-n">$1,400<span> a year</span></p>'
            '<h2 id="ap-save">Why sign up now?</h2>'
            "<p>Ottawa says homes that switch from oil, propane or electric baseboard heat save over $1,400 a year on average. "
            "Applications are not open yet. When they open we'll email you that day, so you can apply right away.</p>"
            f'<a class="ap-btn ap-btn-solid" href="#federal-alert">Get the launch-day email{icon("arrow", "ap-btn-ico")}</a></div></div></section>')


def stack():
    rows = fed.stack_rows()
    li = ""
    for c in sorted(rows, key=lambda k: rows[k]["name"]):
        d, x = rows[c], rows[c]["row"]
        if not x:
            continue
        li += (f'<li><a class="ap-prov" href="{d["link"]}"><span class="ap-prov-name">{e(d["name"])}</span>'
               f'<b class="ap-prov-amt">{e(x["amt"])}</b>{icon("arrow", "ap-prov-go")}</a></li>')
    return ('<section class="ap-band" aria-labelledby="ap-prov"><div class="ap-wrap"><div class="ap-head"><p class="ap-eyebrow">While you wait</p>'
            '<h2 id="ap-prov">What your province pays today</h2>'
            "<p>Ottawa says you can add its rebate on top of provincial ones. Each program has its own rules, and these are the most you can get.</p></div>"
            f'<ul class="ap-provs">{li}</ul></div></section>')


def about():
    return ('<section class="ap-band ap-band-warm" aria-labelledby="ap-who"><div class="ap-wrap ap-about"><div class="ap-about-copy">'
            '<p class="ap-eyebrow">Who we are</p><h2 id="ap-who">An independent site, not the government</h2>'
            "<p>HomePowerRebate tracks home energy rebates across Canada and links every amount to the official program. "
            f'Ottawa also has <a class="ap-link" href="{OTTAWA}" rel="noopener" target="_blank">its own sign-up{icon("ext", "ap-ext")}</a>, and you can use both.</p></div>'
            '<div class="ap-next"><a class="ap-next-card" href="/programs/national-heat-pump-rebate/do-i-qualify/">'
            f'{icon("search", "ap-card-ico")}<b>Check what Ottawa has said about your home</b><span>Four quick questions{icon("arrow", "ap-prov-go")}</span></a>'
            '<a class="ap-next-card" href="/programs/national-heat-pump-rebate/">'
            f'{icon("leaf", "ap-card-ico")}<b>Read everything we know so far</b><span>The full federal rebate guide{icon("arrow", "ap-prov-go")}</span></a></div></div></section>')


def main():
    trail = [("Home", "/"), ("Federal heat pump rebate alert", PATH)]
    lds = kit.ld_scripts([kit.breadcrumb_ld(trail)])
    body = hero() + steps() + emails() + savings() + stack() + about()
    page = (f'{kit.head(TITLE, DESC, PATH, lds).replace(kit.CSS, "")}\n{navfooter.render_nav("", "")}\n{kit.breadcrumb(trail)}\n'
            f'<div class="ap"><article>\n{body}\n</article></div>\n{navfooter.render_footer("", "", "", PATH)}\n</body></html>\n')
    page = page.replace('<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">',
                        '<meta name="robots" content="noindex, follow, max-image-preview:large">')
    page = page.replace('<meta property="og:type" content="article">', '<meta property="og:type" content="website">')
    out = ROOT / PATH.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")
    print("built", PATH)


if __name__ == "__main__":
    main()
