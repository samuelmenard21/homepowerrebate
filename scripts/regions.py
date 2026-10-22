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


COUNTRY_LABELS = {"ca": "Canada", "us": "United States"}
COUNTRY_BY_CODE = {r["code"]: r["country"] for r in REGIONS}


def order_key(code):
    """Sort key for any region list shown to a visitor: Canada first, then the United States, each A to Z by name."""
    r = BY_CODE[code]
    return (0 if r["country"] == "ca" else 1, r["name"])


def grouped(key=lambda r: r["name"]):
    """[(country label, [region dicts])]: Canada and its provinces and territories, then the United States and its states, A to Z in each."""
    return [(COUNTRY_LABELS[cc], sorted((r for r in REGIONS if r["country"] == cc), key=key)) for cc in ("ca", "us")]


def option_groups(value=lambda r: r["code"], label=lambda r: r["name"], selected=None):
    """<optgroup>s for a province or state <select>: one group for Canada, one for the United States."""
    import html as _h
    out = []
    for name, rs in grouped():
        opts = "".join(f'<option value="{_h.escape(str(value(r)))}"{" selected" if selected == r["code"] else ""}>{_h.escape(label(r))}</option>' for r in rs)
        out.append(f'<optgroup label="{name}">{opts}</optgroup>')
    return "".join(out)


def region_dirs_exclusion():
    """Folder names to ignore when guessing a city from a URL path."""
    return {"ca", "us", "fr"} | set(CODES) | {"stacking-calculator"}


def nav_tabs_html(indent="      "):
    """Province and state tab buttons in two labelled groups (Canada, then the United States), A to Z in each; Ontario is the default-highlighted tab."""
    groups = []
    for name, rs in grouped(key=lambda r: r["tab_label"]):
        btns = "\n".join(f"{indent}    <button type=\"button\" onclick=\"showProvinceCities('{r['code']}')\" id=\"province-tab-{r['code']}\" "
                         f"class=\"nav-region-tab{' is-on' if r['code'] == 'on' else ''}\" aria-pressed=\"{'true' if r['code'] == 'on' else 'false'}\">{r['tab_label']}</button>" for r in rs)
        groups.append(f"{indent}  <div class=\"nav-region-group\" role=\"group\" aria-label=\"{name}\"><span class=\"nav-region-group-label\">{name}</span>\n"
                      f"{indent}    <div class=\"nav-region-group-tabs\">\n{btns}\n{indent}    </div></div>")
    return f"{indent}<div class=\"nav-region-tabs\">\n" + "\n".join(groups) + f"\n{indent}</div>"


def nav_panels_html(indent="    "):
    out = []
    for i, r in enumerate(REGIONS):
        links = "".join(f'<a href="{h}">{l}</a>' for h, l in r["cities"])
        out.append(f'{indent}<div id="province-cities-{r["code"]}" class="nav-region-cities"{"" if r["code"] == "on" else " hidden"}>\n'
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
