#!/usr/bin/env python3
"""Single list of launched regions, read from data/regions.json.

Add a region once in data/regions.json (code, abbr, name, country, path, tab_label, cities, programs, hub_verified, calc_label)
and every script that used to carry its own copy of the region list reads it from here: the nav and footer, the hub pipeline,
get-quotes, the home feed, the PowerScore tables, the SEO fixer and the layout check.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGIONS = json.loads((ROOT / "data" / "regions.json").read_text())["regions"]
BY_CODE = {r["code"]: r for r in REGIONS}

CODES = [r["code"] for r in REGIONS]                       # ["on", "bc", ...]
HUBS = [r["path"] for r in REGIONS]                        # ["ca/on", "ca/bc", ...]
HUB_URL = {r["abbr"]: f"/{r['path']}/" for r in REGIONS}   # {"ON": "/ca/on/", ...}
HUB_URL_BY_CODE = {r["code"]: f"/{r['path']}/" for r in REGIONS}
ABBR_BY_PATH = {r["path"]: r["abbr"] for r in REGIONS}     # {"ca/on": "ON"}
NAME_BY_ABBR = {r["abbr"]: r["name"] for r in REGIONS}
CODE_BY_PATH = {r["path"]: r["code"] for r in REGIONS}
CODE_BY_PREFIX = {tuple(r["path"].split("/")): r["code"] for r in REGIONS}   # {("ca","on"): "on"}
FACTS_FILES = {r["path"]: r["facts_files"] for r in REGIONS}
PROGRAMS = {r["path"]: [tuple(x) for x in r.get("programs", [])] for r in REGIONS}
VERIFIED = {r["path"] for r in REGIONS if r.get("hub_verified")}
CALC = {r["code"]: (f"/calculator/{r['code']}/", r["calc_label"]) for r in REGIONS if r.get("calc_label")}
TOP_NAMES = {r["path"]: {"code": r["abbr"], "name": r["name"]} for r in REGIONS}
COUNTRY_NAME_BY_PATH = {r["path"]: ("Canada" if r["country"] == "ca" else "United States", r["name"]) for r in REGIONS}


def region_dirs_exclusion():
    """Folder names to ignore when guessing a city from a URL path."""
    return {"ca", "us"} | set(CODES) | {"stacking-calculator"}


_BTN = ("flex:1; padding:9px; border-radius:8px; border:1px solid var(--rule); background:%s; color:%s; font-weight:600; "
        "font-size:13px; cursor:pointer; font-family:'Inter Tight',sans-serif;")


def nav_tabs_html(indent="      "):
    """Province/state tab buttons, three per row; the first (Ontario) is the default-highlighted tab."""
    rows = []
    for i in range(0, len(REGIONS), 3):
        btns = []
        for j, r in enumerate(REGIONS[i:i + 3]):
            style = _BTN % (("var(--teal-deep)", "#fff") if i + j == 0 else ("#fff", "var(--ink)"))
            btns.append(f"{indent}  <button type=\"button\" onclick=\"showProvinceCities('{r['code']}')\" id=\"province-tab-{r['code']}\" "
                        f"style=\"{style}\">{r['tab_label']}</button>")
        rows.append(f"{indent}<div style=\"display:flex; gap:6px; margin-bottom:12px;\">\n" + "\n".join(btns) + f"\n{indent}</div>")
    return "\n".join(rows)


def nav_panels_html(indent="    "):
    out = []
    for i, r in enumerate(REGIONS):
        links = "".join(f'<a href="{h}">{l}</a>' for h, l in r["cities"])
        out.append(f'{indent}<div id="province-cities-{r["code"]}" style="display:{"grid" if i == 0 else "none"}; gap:8px;">\n'
                   f'{indent}  {links}\n{indent}</div>')
    return "\n".join(out)


def footer_items_html(country, indent="          "):
    return "\n".join(f'{indent}<li><a href="/{r["path"]}/">{r["name"]}</a></li>' for r in REGIONS if r["country"] == country)


def codes_js():
    return "[" + ", ".join(f"'{c}'" for c in CODES) + "]"


def expand_tokens(text):
    """Replace the {{REGION_*}} tokens in the nav/footer partial or any generator template."""
    return (text.replace("{{REGION_TABS}}", nav_tabs_html()).replace("{{REGION_PANELS}}", nav_panels_html())
            .replace("{{REGION_FOOTER_CA}}", footer_items_html("ca")).replace("{{REGION_FOOTER_US}}", footer_items_html("us"))
            .replace("{{REGION_CODES_JS}}", codes_js()))
