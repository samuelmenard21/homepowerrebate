#!/usr/bin/env python3
"""Clean installers/*-installers-real.csv before rankings are built.

Google Places searches ("battery installer", "solar installer", ...) return some businesses
that don't do the job: car and phone battery shops, window tint, panel cleaners, drywallers,
marketplaces. Emails scraped from websites also include template placeholders and addresses
on unrelated domains. This removes both, in place, and logs every removal to
data/installer-cleanup-log.csv (private, not published).

  python3 scripts/clean_installers.py --dry-run   # show what would change
  python3 scripts/clean_installers.py
Re-run after every scrape, before build_installer_rankings.py.
"""
import csv
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
INST = ROOT / "installers"
LOG = ROOT / "data" / "installer-cleanup-log.csv"

# Never a home-energy installer, whatever the search type.
NOT_INSTALLER = re.compile(
    r"tint|window film|cleaning|cleaners?\b|wash|lighting store|energysage|solar panel guide|\bguide\b|"
    r"auto\b|automotive|\bcar\b|tire|cellular|phone|batteries plus|battery world|interstate|battery (shop|center|centre|sales)|"
    r"golf cart|marine|drywall(?!.*insulat)|stucco(?!.*insulat)|\blaw\b|lawyer|dental|dentist|casino|realty|real estate|shades", re.I)
# A battery listing must look like a home energy company (or also be on the solar list).
BATTERY_OK = re.compile(r"solar|sun|energy|power|renew|volt|electri|battery storage|tesla|enphase|off.?grid|home backup", re.I)
# Battery shops, EV/hybrid battery repair and EV-charger firms: not home battery installers unless also on the solar list.
BATTERY_RETAIL = re.compile(r"batter|hybrid|\bev\b|ev charg|charging|charger|alternator|starter", re.I)
BATTERY_SOLAR = re.compile(r"solar|sun|energy|renew|storage|off.?grid", re.I)
INSULATION_OK = re.compile(r"insulat|foam|spray|attic|weather|seal|energy|efficien|comfort|thermal|home perform|cellulose|retrofit|green", re.I)

JUNK_EMAIL = re.compile(r"@(example|domain|mysite|email|yourdomain|sentry|wixpress|wix|godaddy|squarespace|doe)\.|"
                        r"^(john|jane|name|user|test|your|email)@|\.(png|jpe?g|gif|svg|webp)$", re.I)
FREE_MAIL = ("gmail.", "hotmail.", "outlook.", "yahoo.", "ymail.", "live.", "icloud.", "shaw.ca", "telus.net", "rogers.com",
             "bell.net", "sympatico.ca", "aol.com", "comcast.net", "verizon.net", "me.com", "msn.com")


def root_domain(host):
    host = host.lower().split(":")[0]
    host = host[4:] if host.startswith("www.") else host
    parts = host.split(".")
    return ".".join(parts[-3:]) if len(parts) > 2 and parts[-2] in ("co", "com", "on", "bc") else ".".join(parts[-2:])


def email_ok(email, website, name):
    """Emails came from each company's own website, so free-mail (gmail etc.) found there is real.
    Drop placeholders, site-builder hosts, and company-domain addresses that match neither the
    company's website nor any word of its name (e.g. a law firm's address picked up from a footer)."""
    e = email.strip().lower()
    if not e or "@" not in e or JUNK_EMAIL.search(e) or re.search(r"hostingersite|wpengine|myshopify|weebly", e):
        return False
    dom = e.split("@", 1)[1]
    if any(dom.startswith(f) or dom == f for f in FREE_MAIL):
        return True
    if website:
        site = root_domain(urlparse(website if "://" in website else "https://" + website).netloc)
        if root_domain(dom) == site or site.split(".")[0] in dom:
            return True
    words = [w for w in re.findall(r"[a-z0-9]+", name.lower()) if len(w) >= 4 and w not in
             ("heating", "cooling", "solar", "energy", "electric", "electrical", "services", "service", "home", "homes",
              "insulation", "plumbing", "mechanical", "contracting", "systems", "power", "company", "group")]
    return any(w in dom.replace("-", "") for w in words)


def service_of(name):
    m = re.match(r"(?:[a-z]{2}-)?(heat-pump|solar|insulation|battery)-installers-real\.csv$", name)
    return m.group(1) if m else None


def main():
    dry = "--dry-run" in sys.argv
    files = {f: service_of(f.name) for f in sorted(INST.glob("*-installers-real.csv")) if service_of(f.name)}
    solar_names = set()
    for f, sv in files.items():
        if sv == "solar":
            solar_names |= {r["Business Name"].strip().lower() for r in csv.DictReader(f.open(encoding="utf-8"))}
    log = [["file", "business", "city", "action", "detail"]]
    kept_total = 0
    for f, sv in files.items():
        rows = list(csv.DictReader(f.open(encoding="utf-8")))
        fields = list(rows[0].keys()) if rows else []
        out = []
        for r in rows:
            name, site = r["Business Name"].strip(), (r.get("Website") or "").strip()
            text = f"{name} {site}"
            why = None
            if NOT_INSTALLER.search(name) or "energysage" in site.lower():
                why = "not an installer"
            elif sv == "battery" and name.lower() not in solar_names and BATTERY_RETAIL.search(name) and not BATTERY_SOLAR.search(name):
                why = "battery shop or EV service, not home battery installs"
            elif sv == "battery" and not (BATTERY_OK.search(text) or name.lower() in solar_names):
                why = "no sign of home battery work"
            elif sv == "insulation" and not INSULATION_OK.search(text):
                why = "no sign of insulation work"
            if why:
                log.append([f.name, name, r["City"], "removed", why])
                continue
            if r.get("Email") and not email_ok(r["Email"], site, name):
                log.append([f.name, name, r["City"], "email dropped", r["Email"]])
                r["Email"] = ""
            out.append(r)
        kept_total += len(out)
        if not dry and out != rows:
            with f.open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=fields)
                w.writeheader()
                w.writerows(out)
    removed = sum(1 for l in log[1:] if l[3] == "removed")
    dropped = len(log) - 1 - removed
    if not dry:
        LOG.parent.mkdir(exist_ok=True)
        with LOG.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(log)
    for l in log[1:]:
        if dry:
            print(" | ".join(l))
    print(f"{removed} listings removed, {dropped} emails dropped, {kept_total} kept"
          + (" (dry run)" if dry else f". Log: {LOG.relative_to(ROOT)}"))


if __name__ == "__main__":
    main()
