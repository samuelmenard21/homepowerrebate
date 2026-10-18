#!/usr/bin/env python3
"""One quote-form script for every installer profile (2026-10-17).

The profile "Request a Quote" form used to post only city, source and `installer` (a field the lead router
ignores) with no province. The router then read the lead as unassigned and in BC: the installer never got it,
and a Vancouver, WA homeowner was sent BC Hydro rebates. This writes the script between PROFILE-QUOTE markers
with province, service, installer_name and installer_email, from the ranking CSVs (build_installer_rankings.load_rows),
so the router emails the installer (only if the address is on installers/allowed-installer-emails.json).

generate_installer_profiles.py calls quote_script() for new pages; this post-step converts existing pages.
Idempotent. Usage: python3 scripts/fix_profile_quote_form.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

START, END = "<!-- PROFILE-QUOTE-START -->", "<!-- PROFILE-QUOTE-END -->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
# The older inline script: the one <script> that holds both the form id and the lead route.
OLD_RE = re.compile(r"<script>(?:(?!</script>).)*?ip-quote-form(?:(?!</script>).)*?estimate-lead(?:(?!</script>).)*?</script>", re.S)
FIELD_RE = r"\b{}:\s*(\"(?:[^\"\\]|\\.)*\"|'[^']*')"
# The router accepts these two services and treats anything else as heat-pump.
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SERVICE_ORDER = ["heat-pump", "solar", "insulation", "battery"]


def quote_script(city, province, source, installer_name, installer_email="", service="heat-pump"):
    body = {"city": city, "province": province, "service": service, "source": source,
            "installer_name": installer_name, "installer_email": installer_email}
    fields = ",\n        ".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in body.items())
    return f"""{START}
<script>
(function() {{
  var form = document.getElementById('ip-quote-form');
  form.addEventListener('submit', function(e) {{
    e.preventDefault();
    if (document.getElementById('ip-hp').value) return;
    var btn = document.getElementById('ip-quote-btn');
    btn.disabled = true; btn.textContent = 'Sending…';
    fetch('https://leads.homepowerrebate.com/estimate-lead', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{
        firstname: document.getElementById('ip-name').value,
        email: document.getElementById('ip-email').value,
        phone: document.getElementById('ip-phone').value,
        page_url: location.pathname,
        {fields}
      }})
    }}).catch(function(err) {{ console.error('quote request error', err); }})
      .finally(function() {{
        form.style.display = 'none';
        document.getElementById('ip-quote-done').style.display = 'block';
      }});
  }});
}})();
</script>
{END}"""


def _field(script, name):
    m = re.search(FIELD_RE.format(name), script)
    if not m:
        return ""
    v = m.group(1)
    return json.loads(v) if v.startswith('"') else v[1:-1]


def profile_index():
    """profile path -> {'region', 'services', 'name', 'email', 'city'} from the ranking CSVs."""
    import build_installer_rankings as br
    out = {}
    for r in br.load_rows():
        url = br.profile_url(r["region"], r["city"], r["name"])
        if not url:
            continue
        e = out.setdefault(url.strip("/"), {"region": r["region"], "services": [], "name": r["name"], "email": "", "city": r["city"]})
        if r["service"] not in e["services"]:
            e["services"].append(r["service"])
        m = EMAIL_RE.search(r["email"] or "")  # some CSV cells carry scraped HTML around the address
        if not e["email"] and m:
            e["email"] = m.group(0).lower()
    return out


def region_codes():
    data = json.loads((ROOT / "data" / "regions.json").read_text(encoding="utf-8"))
    return {r["code"].lower() for r in data["regions"]}


def main():
    idx, codes = profile_index(), region_codes()
    changed = matched = 0
    for page in sorted((ROOT / "installers" / "profiles").rglob("index.html")):
        html = page.read_text(encoding="utf-8")
        if "ip-quote-form" not in html:
            continue
        cur = BLOCK_RE.search(html) or OLD_RE.search(html)
        if not cur:
            print(f"NO SCRIPT {page.relative_to(ROOT)}")
            continue
        old = cur.group(0)
        rel = str(page.parent.relative_to(ROOT))
        info = idx.get(rel)
        parts = rel.split("/")  # installers/profiles/[region/]city/slug
        region = info["region"] if info else (parts[2] if len(parts) == 5 and parts[2] in codes else "bc")
        services = sorted(info["services"], key=SERVICE_ORDER.index) if info else []
        name = (info or {}).get("name") or _field(old, "installer_name") or _field(old, "installer")
        new = quote_script(
            city=_field(old, "city") or (info or {}).get("city", ""),
            province=region.upper(),
            source=_field(old, "source") or f"installer-{region}-{parts[-1]}",
            installer_name=name,
            installer_email=(info or {}).get("email", ""),
            service=services[0] if services else "heat-pump",
        )
        matched += bool(info)
        if new != old:
            page.write_text(html.replace(old, new, 1), encoding="utf-8")
            changed += 1
    print(f"profile quote forms: {changed} updated, {matched} matched to a ranking")


if __name__ == "__main__":
    main()
