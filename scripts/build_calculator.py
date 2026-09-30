#!/usr/bin/env python3
"""Build the rebate calculator for every region that has data/calc/<code>.json.

One engine (calculator/rebate-engine.js) serves every province and state. A region is data only:
  data/calc/<code>.json        questions, rules (who qualifies, how much), FAQ. No amounts are typed twice:
  data/verified-facts/*.json   each program points at a fact id; status, verified_on and source_url come from the fact.
Outputs:
  calculator/data/<code>.json          public rules with status/source resolved (read by the engine)
  calculator/<code>/index.html         the calculator page for the region
  calculator/embed/<code>/index.html   chrome-less version for the installer widget (noindex)
  calculator/index.html                region picker
Adding a region: write data/facts + data/calc/<code>.json, run this script, run check_facts.py. See CLAUDE.md.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_furnace_pages import shell, AUTHOR, BASE  # noqa: E402

e = html.escape
CSS = """
.rc-wrap{max-width:820px;margin:0 auto;padding:0 20px 8px}
.rc-form{display:grid;grid-template-columns:1fr 1fr;gap:14px 18px;background:#fff;border:1px solid #d9d0c1;border-radius:12px;padding:20px;margin:18px 0}
.rc-field label{display:block;font-weight:600;font-size:15px;margin-bottom:5px}
.rc-field select,.rc-field input{width:100%;min-height:44px;padding:8px 10px;border:1px solid #b9ae9c;border-radius:8px;font:inherit;background:#fff}
.rc-field:first-child{grid-column:1/-1}
.rc-help{font-size:13px;color:#4a5f5b;margin:4px 0 0}
.rc-total{background:#0d4f5c;color:#fff;border-radius:12px;padding:20px;margin:8px 0 16px}
.rc-total-label{font-size:14px;opacity:.9}.rc-total-num{font-family:Fraunces,Georgia,serif;font-size:44px;font-weight:600;line-height:1.1;margin:2px 0 6px}
.rc-total,.rc-wrap .rc-total div,.rc-wrap .rc-total p{color:#fff}.rc-total-sub{font-size:13px;margin:0;opacity:.95}
.rc-h{font-family:Fraunces,Georgia,serif;font-size:22px;margin:24px 0 8px}
.rc-card{background:#fff;border:1px solid #d9d0c1;border-left:4px solid #2d6a4f;border-radius:10px;padding:14px 16px;margin:10px 0}
.rc-card.rc-muted{border-left-color:#b9ae9c;background:#faf7f2}
.rc-card-top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.rc-card h4{margin:0;font-size:16px}.rc-amt{font-weight:700;color:#2d6a4f;white-space:nowrap}
.rc-meta{margin:6px 0 0;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.rc-rules{margin:8px 0 4px;font-size:14.5px;line-height:1.5}.rc-src{margin:0;font-size:13px;color:#4a5f5b}
.rc-note{font-size:12.5px;color:#8a4a06}
.rc-pill{display:inline-block;padding:1px 9px;border-radius:99px;font-size:12px;font-weight:600}
.rc-active{background:#e3f1e8;color:#1f5a3d}.rc-upcoming,.rc-waitlist{background:#fdeccf;color:#8a4a06}
.rc-paused,.rc-closed{background:#f3dcdc;color:#8a2b2b}.rc-check,.rc-info{background:#e8e8e8;color:#444}
.rc-hint,.rc-empty{background:#f5efe5;border-radius:8px;padding:12px 14px;font-size:15px}
.rc-closed{padding-left:18px}.rc-notes{font-size:13.5px;color:#4a5f5b;padding-left:18px}
.rc-save{background:#f5efe5;border-radius:12px;padding:6px 18px 16px;margin:20px 0}
.rc-save input{min-height:44px;padding:8px 10px;border:1px solid #b9ae9c;border-radius:8px;font:inherit;width:min(320px,100%)}
.rc-save button{min-height:44px;margin-left:8px;padding:0 18px;border:0;border-radius:8px;background:#d4751c;color:#fff;font-weight:700;cursor:pointer}
.rc-links{font-size:15px}
.rc-inst{background:#fff;border:1px solid #d9d0c1;border-radius:12px;padding:4px 18px 12px;margin:20px 0}.rc-inst-list{margin:6px 0 0;padding-left:20px;line-height:1.9}
.rc-plan{grid-column:1/-1;border:0;padding:0;margin:0}.rc-plan legend{font-weight:600;font-size:15px;margin-bottom:6px;padding:0}
.rc-check{display:inline-flex;align-items:center;gap:6px;min-height:44px;margin:0 14px 4px 0;font-size:15px}.rc-check input{width:20px;height:20px}
.rc-more{margin:18px 0}.rc-more summary{cursor:pointer;font-weight:600;padding:8px 0}
@media(max-width:600px){.rc-form{grid-template-columns:1fr}.rc-total-num{font-size:38px}.rc-card-top{flex-direction:column;gap:2px}}
"""


def load_facts():
    facts = {}
    for f in sorted((ROOT / "data" / "verified-facts").glob("*.json")):
        for x in json.loads(f.read_text())["facts"]:
            facts[x["id"]] = x
    return facts


SERVICES = ("heat-pump", "solar", "battery", "insulation")


def link_cities(spec):
    """Give every city option its city page and its installer list pages, from the files that exist.
    spec['installers_dir'] = folder under /installers/ (for example 'on'); spec['city_page'] = path pattern with {c}."""
    q = next((x for x in spec["questions"] if x["id"] == "city"), None)
    if not q:
        return
    for o in q["options"]:
        c = o["value"]
        d = spec.get("installers_dir")
        found = {s: f"/installers/{d}/{c}/{s}/" for s in SERVICES if d and (ROOT / "installers" / d / c / s / "index.html").exists()}
        if found:
            o["installers"] = found
        pat = spec.get("city_page")
        if pat and not o.get("page"):
            hits = sorted(ROOT.glob(pat.format(c=c).strip("/") + "/index.html"))
            if hits:
                o["page"] = "/" + str(hits[0].parent.relative_to(ROOT)) + "/"


def resolve(spec, facts):
    """Public region JSON: rules from data/calc, status/source/date from the linked fact."""
    out = json.loads(json.dumps(spec))
    link_cities(out)
    for p in out["programs"]:
        fx = facts[p["fact"]]
        p["status"], p["verified_on"], p["source_url"] = fx["status"], fx["verified_on"], fx["source_url"]
        del p["fact"]
    out["closed"] = [{"name": facts[i]["program"], "status": facts[i]["status"], "source_url": facts[i]["source_url"]} for i in out.pop("closed_facts", [])]
    src = facts[out["derived"]["income_level"].pop("source_fact")] if out.get("derived") else None
    out["income_source"] = src["source_url"] if src else None
    for k in ("faq", "short", "h1", "title", "desc", "intro", "installers_dir", "city_page"):
        out.pop(k, None)
    out["verified_on"] = max([p["verified_on"] for p in out["programs"]])
    return out


def money(p):
    a = p["amount"]
    if a.get("label"):
        return a["label"]
    if "per" in a:
        r = a["per"]
        return f"${r['rate']:,} per {r['unit']}" + (f" (${r['bonus_rate']:,} with the gas bonus)" if r.get("bonus_rate") else "")
    if "by" in a:
        vals = sorted(set(a["values"].values()), reverse=True)
        return "$" + f"{vals[0]:,}" + (f" to ${vals[-1]:,}" if vals[-1] != vals[0] else "")
    return f"Up to ${a['max']:,}"


def program_table(spec, facts):
    rows = ""
    for p in spec["programs"]:
        fx = facts[p["fact"]]
        rows += (f"<tr><td><b>{e(p['name'])}</b></td><td>{e(money(p))}</td>"
                 f"<td>{e(p['rules'])} <a href='{e(fx['source_url'])}' rel='nofollow noopener' target='_blank'>Source</a> "
                 f"<span class='small'>({e(fx['status'])}, verified {e(fx['verified_on'])})</span></td></tr>")
    return f"<div class='tw'><table><tr><th>Program</th><th>Amount</th><th>Rules</th></tr>{rows}</table></div>"


def inline_calc(pub, opts=""):
    """Engine + region data inlined in the page. Cloudflare's firewall on this zone returns 403 for any .js or .json
    outside a short allow-list, so the calculator must not fetch either file."""
    engine = (ROOT / "calculator" / "rebate-engine.js").read_text(encoding="utf-8")
    data = json.dumps(pub, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f"<script>{engine}</script>\n<script>HPRCalc.mount(document.getElementById(\"rc-mount\"),{data}{opts});</script>"


def region_page(spec, facts):
    code = spec["code"]
    path = f"/calculator/{code}/"
    pub = resolve(spec, facts)
    vdate = date.fromisoformat(pub["verified_on"]).strftime("%B %-d, %Y")
    faq = spec["faq"]
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/calculator/">Calculators</a></li><li aria-current="page">{e(spec['name'])}</li></ol></nav>
<header class="hero"><div class="wrap"><h1>{e(spec['h1'])}</h1><p>{e(spec['intro'])}</p><p class="meta">By {e(AUTHOR['name'])} · Rules last verified {e(vdate)}</p></div></header>
<section class="body"><div class="wrap rc-wrap">
<div style="background:#f5efe5;border-left:4px solid #d4751c;border-radius:8px;padding:18px 20px;"><p style="margin:0;"><b>Short answer:</b> {e(spec['short'])}</p></div>
<div id="rc-mount"><noscript><p>The calculator needs JavaScript. The full list of programs is in the table below.</p></noscript></div>
<h2>How we work it out</h2>
<ul><li>Every amount comes from the program's own page, linked on each result.</li>
<li>We count only programs that are open today. Programs that start later or have a waitlist are listed but not added.</li>
<li>Your answers stay in your browser. We only get your email if you ask us to notify you.</li>
<li>Nobody pays to be included, and installers cannot change what you see.</li></ul>
<h2>Every {e(spec['name'])} program in this calculator</h2>
{program_table(spec, facts)}
<h2>Common questions</h2>
{"".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in faq)}
<p><b>Next:</b> <a href="{e(spec['hub'])}">{e(spec['name'])} rebate guide</a> · <a href="/installers/">Top-rated installers by city</a> · <a href="/rebate-tracker/">Recent rebate changes</a></p>
<p class="small">Something out of date? Email <a href="mailto:hello@homepowerrebate.com">hello@homepowerrebate.com</a> and we'll check it within a week.</p>
</div></section>
{inline_calc(pub)}"""
    ld = [
        {"@context": "https://schema.org", "@type": "WebApplication", "name": spec["title"], "url": BASE + path, "applicationCategory": "FinanceApplication",
         "operatingSystem": "Any", "description": spec["desc"], "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
         "publisher": {"@type": "Organization", "name": "HomePowerRebate", "url": BASE}},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Calculators", "item": BASE + "/calculator/"},
            {"@type": "ListItem", "position": 3, "name": spec["name"]}]},
    ]
    out = shell(spec["title"] + " | HomePowerRebate", spec["desc"], path, code, body, ld)
    out = out.replace("</style>", ".tw{overflow-x:auto;-webkit-overflow-scrolling:touch}.tw table{min-width:520px}" + CSS + "</style>", 1)
    return path, out, pub


def embed_page(spec, pub):
    code = spec["code"]
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(spec['name'])} rebate calculator</title><meta name="robots" content="noindex, follow"><link rel="canonical" href="{BASE}/calculator/{code}/">
<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;600;700&display=swap" rel="stylesheet">
<style>body{{margin:0;padding:12px;font-family:'Inter Tight',system-ui,sans-serif;color:#0a2a2e;background:#faf7f2}}a{{color:#0d4f5c}}{CSS}
.rc-form{{margin-top:0}}.rc-by{{font-size:13px;margin:14px 0 0;text-align:center}}</style></head><body>
<div id="rc-mount"></div>
<p class="rc-by"><a href="{BASE}/calculator/{code}/" target="_blank" rel="noopener">{e(spec['name'])} rebate calculator by HomePowerRebate</a></p>
{inline_calc(pub, ",{embed:true}")}
<script>function h(){{parent.postMessage({{hprCalcHeight:document.documentElement.scrollHeight}},"*")}}new ResizeObserver(h).observe(document.body);h();</script>
</body></html>"""


COMING = [("Ontario", "/ca/on/"), ("Alberta", "/ca/ab/"), ("Nova Scotia", "/ca/ns/"), ("California", "/us/ca/"), ("Colorado", "/us/co/"),
          ("Massachusetts", "/us/ma/"), ("New York", "/us/ny/"), ("Pennsylvania", "/us/pa/"), ("Vermont", "/us/vt/")]


def picker(specs):
    def li(s):
        return f'<li><a href="/calculator/{s["code"]}/"><b>{e(s["name"])} rebate calculator</b></a> <span class="small">rules verified {e(s["_v"])}</span></li>'
    ca = "".join(li(s) for s in specs if s["country"] == "ca")
    us = "".join(li(s) for s in specs if s["country"] == "us")
    live = {s["name"].lower() for s in specs}
    left = [(n, u) for n, u in COMING if n.lower() not in live]
    coming = ""
    if left:
        coming = ("<h2>Coming next</h2><p>We add a calculator only when every program in it has been checked against the program's own page. Until then, use the rebate guide: "
                  + " · ".join(f'<a href="{u}">{e(n)}</a>' for n, u in left) + ".</p>")
    body = f"""<header class="hero"><div class="wrap"><h1>Home Rebate Calculators</h1><p>Pick your province or state, answer a few questions and see the rebates you can claim, with the official source for every amount. Free for homeowners, and we show top-rated installers in your city.</p></div></header>
<section class="body"><div class="wrap rc-wrap"><h2>Canada</h2><ul>{ca}</ul><h2>United States</h2><ul>{us}</ul>{coming}
<h2>How these calculators work</h2><p>Each amount comes from the program's own page, and every result shows the date we last checked it. We only add up programs that are open today. Programs on a waitlist, paused or closed are shown but never counted. Nobody pays to be included.</p>
<h2>Are you an installer?</h2><p>Add a free rebate calculator to your website. It links back to us and nothing else changes. <a href="/calculator/widget/">See how</a>.</p></div></section>"""
    return shell("Home Rebate Calculators: Heat Pump, Solar and Battery | HomePowerRebate",
                 "Free home rebate calculators for 10 provinces and states. Choose yours to see the rebates you can claim, with an official source for every amount.",
                 "/calculator/", "bc", body, [])


def widget_page(specs):
    code = specs[0]["code"]
    names = ", ".join(f"{e(s['name'])} (<code>{s['code']}</code>)" for s in specs)
    snippet = (f'<iframe src="https://homepowerrebate.com/calculator/embed/{code}/" title="Rebate calculator" width="100%" height="760" '
               f'style="max-width:820px;border:1px solid #d9d0c1;border-radius:12px;" loading="lazy"></iframe>\n'
               f'<p><a href="https://homepowerrebate.com/calculator/{code}/">Rebate calculator by HomePowerRebate</a></p>')
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/calculator/">Calculators</a></li><li aria-current="page">Installer widget</li></ol></nav>
<header class="hero"><div class="wrap"><h1>Free Rebate Calculator for Your Website</h1><p>Let your customers check which rebates they qualify for, without leaving your site.</p></div></header>
<section class="body"><div class="wrap rc-wrap"><h2>Copy and paste</h2>
<pre style="background:#0a2a2e;color:#fff;padding:14px;border-radius:8px;overflow-x:auto;white-space:pre-wrap;">{e(snippet)}</pre>
<p>Change <code>{code}</code> in both places to your region's code: {names}.</p>
<h2>What you get</h2><ul><li>A working calculator for your province or state. It shows top-rated installers in the visitor's city, ranked by Google reviews.</li>
<li>Rebate amounts that update on their own when a program changes. You never edit them.</li>
<li>No script to install, no tracking, no cookies, no ads, and no fee.</li></ul>
<h2>What we ask</h2><p>Leave the "Rebate calculator by HomePowerRebate" link under the frame. It is a normal link. Listing here never changes where your company ranks: installers are ranked by Google reviews only.</p>
<h2>Preview</h2><iframe src="/calculator/embed/{code}/" title="Rebate calculator preview" width="100%" height="760" style="max-width:820px;border:1px solid #d9d0c1;border-radius:12px;" loading="lazy"></iframe>
</div></section>"""
    return shell("Free Rebate Calculator Widget for Installers | HomePowerRebate",
                 "Add a free home rebate calculator to your installer website. Amounts update automatically and it links back to HomePowerRebate.",
                 "/calculator/widget/", "bc", body, [])


def link_hub(spec):
    """One line on the region hub pointing at its calculator (own marker block, replaced on re-run)."""
    f = ROOT / spec["hub"].strip("/") / "index.html"
    s = f.read_text(encoding="utf-8")
    S, E = "<!-- CALC-LINK-START -->", "<!-- CALC-LINK-END -->"
    blk = (f'{S}<p style="max-width:880px;margin:12px auto;padding:0 20px;"><b>Not sure what you qualify for?</b> '
           f'<a href="/calculator/{spec["code"]}/">Use the {e(spec["name"])} rebate calculator</a>.</p>{E}')
    if S in s:
        s = re.sub(re.escape(S) + ".*?" + re.escape(E), lambda m: blk, s, count=1, flags=re.S)
    else:
        anchor = next(a for a in ("<!-- PROGRAM-LINKS-END -->", "<!-- HUB-CHANGES-END -->") if a in s)
        s = s.replace(anchor, anchor + "\n" + blk, 1)
    f.write_text(s, encoding="utf-8")


def main():
    facts = load_facts()
    specs = []
    for f in sorted((ROOT / "data" / "calc").glob("*.json")):
        spec = json.loads(f.read_text())
        for p in spec["programs"]:
            if p["fact"] not in facts:
                sys.exit(f"{f.name}: program {p['id']} points at missing fact {p['fact']}")
        path, out, pub = region_page(spec, facts)
        spec["_v"] = pub["verified_on"]
        specs.append(spec)
        pub["code"] = spec["code"]
        for rel, text in ((f"calculator/data/{spec['code']}.json", json.dumps(pub, ensure_ascii=False, separators=(",", ":"))),
                          (f"calculator/{spec['code']}/index.html", out),
                          (f"calculator/embed/{spec['code']}/index.html", embed_page(spec, pub))):
            t = ROOT / rel
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_text(text, encoding="utf-8")
        link_hub(spec)
        print("Wrote", path)
    (ROOT / "calculator" / "index.html").write_text(picker(specs), encoding="utf-8")
    (ROOT / "calculator" / "widget").mkdir(exist_ok=True)
    (ROOT / "calculator" / "widget" / "index.html").write_text(widget_page(specs), encoding="utf-8")
    print("Wrote /calculator/, /calculator/widget/")


if __name__ == "__main__":
    main()
