#!/usr/bin/env python3
"""
Printable one-page rebate sheet for every city: /rebate-sheet/<region>/<city>/ (added 2026-10-17).

Made for energy advisors and auditors to hand to clients: every open program for the city, grouped by upgrade,
with the amount, the main rule and the official source. Built from calculator/data/<code>.json (written by
build_calculator.py from data/calc and the verified facts), so status, amounts and sources are the same ones the
calculator uses, and a closed program can never show. A city's utility comes from the calculator's city option
("set"), so Kelowna gets FortisBC programs and Albany gets National Grid's.

Sheets are noindex: within a region they share most programs, and they exist to be printed, not searched.

  python3 scripts/build_rebate_sheets.py
"""
import html
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import apply_canonical_nav_footer as navfooter  # noqa: E402
import regions  # noqa: E402
from status_pills import STATUS  # noqa: E402

BASE = "https://homepowerrebate.com"
SHOW = ("active", "upcoming", "check")
esc = html.escape


def money(v, cur):
    return f"${v:,.0f}"


def amount_text(a, cur):
    if a.get("label"):
        return a["label"]
    if "max" in a:
        return f"Up to {money(a['max'], cur)}" if a["max"] else ""
    if "per" in a:
        p = a["per"]
        cap = f", up to {money(p['cap'], cur)}" if p.get("cap") else ""
        return f"{money(p['rate'], cur)} per {p['unit']}{cap}"
    if "by" in a:
        vals = sorted(v for v in a["values"].values() if v)
        if not vals:
            return ""
        return f"Up to {money(vals[0], cur)}" if len(vals) == 1 or vals[0] == vals[-1] else f"{money(vals[0], cur)} to {money(vals[-1], cur)}"
    return ""


def applies(prog, answers):
    """False when a condition the city answers (utility, city, north...) rules the program out."""
    when = prog.get("when") or {}
    for k, allowed in when.items():
        if k in answers:
            allowed = allowed if isinstance(allowed, list) else [allowed]
            if answers[k] not in allowed:
                return False
    return True


CSS = """
body{background:var(--paper);color:var(--ink);font-family:'Inter Tight',system-ui,-apple-system,sans-serif}
.rs{max-width:860px;margin:0 auto;padding:28px 16px 56px;color:var(--ink)}
.rs-tools{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;background:var(--paper-warm);border:1px solid var(--card-rule);border-radius:12px;padding:14px 16px;margin-bottom:22px;font-size:15px}
.rs-tools button{min-height:44px;padding:0 18px;border:0;border-radius:10px;background:var(--teal-deep);color:#fff;font:inherit;font-weight:700;cursor:pointer}
.rs-sheet{background:#fff;border:1px solid var(--card-rule);border-radius:14px;padding:26px 24px}
.rs-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;border-bottom:3px solid var(--amber);padding-bottom:12px;margin-bottom:14px}
.rs-head h1{font-family:'Fraunces',Georgia,serif;font-size:26px;line-height:1.15;margin:0}
.rs-head p{margin:4px 0 0;font-size:14px;color:var(--ink-soft)}
.rs-brand{font-weight:700;font-size:14px;white-space:nowrap}.rs-brand span{color:var(--amber)}
.rs h2{font-size:16px;margin:16px 0 6px;color:var(--teal-deep);text-transform:uppercase;letter-spacing:.04em}
.rs table{width:100%;border-collapse:collapse;font-size:14px}
.rs td{border-top:1px solid var(--card-rule);padding:7px 6px;vertical-align:top}
.rs td.amt{font-weight:700;white-space:nowrap;width:1%}
.rs td.st{width:1%;white-space:nowrap;font-size:12px}
.rs .rule{display:block;color:var(--ink-soft);font-size:12.5px;margin-top:2px}
.rs .src{font-size:12px;color:var(--teal-deep)}
.rs-first{background:#fff7ea;border-left:4px solid var(--amber);padding:10px 12px;margin:4px 0 6px;font-size:14px}
.rs-foot{display:grid;gap:10px;margin-top:18px;padding-top:12px;border-top:1px solid var(--card-rule);font-size:13.5px}
@media(min-width:640px){.rs-foot{grid-template-columns:1fr 1fr}}
.rs-sign{border-bottom:1px solid var(--ink);min-height:30px;font-size:12px;color:var(--ink-soft)}
.rs-small{font-size:12px;color:var(--ink-soft)}
@media(max-width:560px){.rs-head{flex-direction:column}.rs td.amt{white-space:normal}}
@media print{
  body{background:#fff!important}
  .nav,.site-footer,footer,.rs-tools,.hpr-breadcrumb,.skip-link,#sticky-cta,.sticky-cta,.fed-alert,[class*="newsletter"]{display:none!important}
  .rs{padding:0;max-width:none}.rs-sheet{border:0;padding:0}
  .rs table{font-size:11.5px}.rs td{padding:4px 5px}.rs .rule{font-size:10.5px}
  .rs h2{font-size:12.5px;margin:10px 0 3px}.rs-head h1{font-size:21px}
  a{color:inherit;text-decoration:none}
  @page{margin:12mm}
}
"""


def sheet(reg, data, city):
    code, cur = data["code"], data.get("currency", "CAD")
    abbr = reg["abbr"]
    answers = dict(city.get("set") or {}, city=city["value"])
    upgrades = data.get("upgrades") or []
    month = date.today().strftime("%B %Y")
    sections = []
    for up in upgrades:
        rows = []
        for p in data["programs"]:
            if p.get("upgrade") != up["id"] or p.get("status") not in SHOW or not applies(p, answers):
                continue
            amt = amount_text(p.get("amount") or {}, cur)
            if not amt:
                continue
            rule = (p.get("rules") or "").split(". ")[0].rstrip(".")
            pill = STATUS[p["status"]][0]
            src = f' <a class="src" href="{esc(p["source_url"])}" rel="noopener" target="_blank">Source</a>' if p.get("source_url") else ""
            rows.append(f'<tr><td>{esc(p["name"])}<span class="rule">{esc(rule)}.{src}</span></td>'
                        f'<td class="amt">{esc(amt)}</td><td class="st">{esc(pill)}</td></tr>')
        if rows:
            sections.append(f'<h2>{esc(up["label"])}</h2><table>{"".join(rows)}</table>')
    if not sections:
        return None
    city_page = city.get("page") or f"/{reg['path']}/"
    calc = f"/calculator/{code}/"
    path = f"/rebate-sheet/{code}/{city['value']}/"
    adv = "energy advisor" if reg["country"] == "ca" else "energy auditor"
    first = ("Book the energy advisor visit <b>before</b> any work starts if your program needs one. "
             "Most programs also need approval or a registered contractor before you buy.") if reg["country"] == "ca" else (
             "Many programs need an energy assessment, pre-approval or a participating contractor <b>before</b> you buy. "
             "Check the rule for each program first.")
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="{city_page}">{esc(city['label'])}</a></li><li aria-current="page">Rebate sheet</li></ol></nav>
<main id="main" class="rs">
<div class="rs-tools"><span><b>For {adv}s and installers:</b> print this sheet or save it as a PDF to hand to clients in {esc(city['label'])}. It updates when programs change.</span>
<button type="button" onclick="window.print()">Print or save as PDF</button></div>
<article class="rs-sheet">
<div class="rs-head"><div><h1>Home energy rebates in {esc(city['label'])}, {abbr}</h1>
<p>Open programs, checked {month}. Amounts are maximums; your amount depends on your home.</p></div>
<div class="rs-brand">Home<span>Power</span>Rebate</div></div>
<p class="rs-first">{first}</p>
{"".join(sections)}
<div class="rs-foot">
<div><b>Your exact estimate:</b> homepowerrebate.com{calc}<br><b>All {esc(city['label'])} rebates:</b> homepowerrebate.com{city_page}</div>
<div><div class="rs-sign">Prepared by:</div><div class="rs-sign">Phone or email:</div></div>
</div>
<p class="rs-small">Programs change. Confirm the amount and rules with each program before you sign a contract. Status: Open = taking applications; Starts soon = announced, not open yet; Check first = we could not confirm every detail.</p>
</article>
</main>"""
    title = f"{city['label']} Rebate Sheet, {abbr} (Printable)"
    desc = f"A printable one-page list of open home energy rebates in {city['label']}, {abbr}, for energy advisors and installers to hand to clients."
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{BASE}{path}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
{navfooter.render_nav(code, city['value'])}
{body}
{navfooter.render_footer(code, city['value'], city['label'], path)}
</body>
</html>
"""
    return path, navfooter.ensure_shared_assets(page)


def index_page(done):
    """/rebate-sheet/: every city's sheet, by province or state (noindex, like the sheets)."""
    path = "/rebate-sheet/"
    parts = []
    for reg in regions.REGIONS:
        cities = done.get(reg["code"])
        if cities:
            links = " · ".join(f'<a href="/rebate-sheet/{reg["code"]}/{v}/">{esc(l)}</a>' for v, l in cities)
            parts.append(f'<h2>{esc(reg["name"])}</h2><p>{links}</p>')
    body = f"""<nav class="hpr-breadcrumb" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li aria-current="page">Rebate sheets</li></ol></nav>
<main id="main" class="rs"><article class="rs-sheet">
<div class="rs-head"><div><h1>Printable rebate sheets by city</h1>
<p>One page per city with every open home energy rebate, its main rule and the official source. For energy advisors, auditors and installers to print or email to clients.</p></div>
<div class="rs-brand">Home<span>Power</span>Rebate</div></div>
{"".join(parts)}
<p class="rs-small">Sheets update when programs change. Want clients to check their own amount? <a href="/calculator/widget/">Add the rebate calculator to your website</a>.</p>
</article></main>"""
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Printable Rebate Sheets by City</title>
<meta name="description" content="Printable one-page home energy rebate sheets for every city we cover, for energy advisors and installers to hand to clients.">
<meta name="robots" content="noindex, follow"><link rel="canonical" href="{BASE}{path}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{CSS}.rs h2{{text-transform:none;letter-spacing:0;font-size:18px}}</style></head>
<body>
{navfooter.render_nav("bc", "")}
{body}
{navfooter.render_footer("bc", "", "", path)}
</body></html>
"""
    (ROOT / "rebate-sheet").mkdir(exist_ok=True)
    (ROOT / "rebate-sheet" / "index.html").write_text(navfooter.ensure_shared_assets(page), encoding="utf-8")


def main():
    n = 0
    done = {}
    for reg in regions.REGIONS:
        f = ROOT / "calculator" / "data" / f"{reg['code']}.json"
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        q = next((x for x in data["questions"] if x["id"] == "city"), None)
        for city in (q or {}).get("options", []):
            out = sheet(reg, data, city)
            if not out:
                continue
            path, page = out
            dest = ROOT / path.strip("/") / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(page, encoding="utf-8")
            done.setdefault(reg["code"], []).append((city["value"], city["label"]))
            n += 1
    index_page(done)
    print(f"{n} rebate sheets written under /rebate-sheet/.")


if __name__ == "__main__":
    main()
