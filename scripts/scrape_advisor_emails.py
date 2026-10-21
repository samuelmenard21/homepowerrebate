#!/usr/bin/env python3
"""Find public contact emails on advisor/auditor company websites (homepage + contact pages).
Writes outreach/advisor-emails.csv. Only addresses printed on the company's own site; same-domain preferred."""
import json, re, csv, sys, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from html import unescape
D = json.load(open("data/energy-advisor-directory.json"))["companies"]
SUPP = set()
for f in ("outreach/suppress.txt", "../Powerrebate/outreach/suppress.txt"):
    try: SUPP |= {l.strip().lower() for l in open(f) if l.strip() and not l.startswith("#")}
    except OSError: pass
PATHS = ["", "contact", "contact-us", "about", "about-us", "contact.html"]
BAD = re.compile(r"(\.(png|jpe?g|gif|svg|webp|css|js)$|sentry|wixpress|example\.|@2x|noreply|no-reply|donotreply|privacy@|wordpress|godaddy|domain\.com|yourname|your@|email@email)", re.I)
RX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
def get(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (compatible; HomePowerRebateBot/1.0; +https://homepowerrebate.com)"}), timeout=12)
        return r.read(600000).decode("utf-8", "ignore")
    except Exception: return ""
def scrape(c):
    g = c.get("google") or {}
    site = c.get("website") or g.get("website") or ""
    if not site: return c["name"], site, []
    if not site.startswith("http"): site = "http://" + site
    dom = urllib.parse.urlparse(site).netloc.lower().removeprefix("www.")
    found = {}
    for p in PATHS:
        h = unescape(get(urllib.parse.urljoin(site if site.endswith("/") else site + "/", p)))
        for m in RX.findall(h.replace("mailto:", " ")):
            m = m.lower().strip(".")
            if BAD.search(m) or m in SUPP: continue
            found[m] = found.get(m, 0) + 1
        if any(e.endswith("@" + dom) or e.split("@")[1].endswith(dom) for e in found): break
    same = [e for e in found if e.split("@")[1].removeprefix("www.").endswith(dom)]
    pick = same or []
    pick.sort(key=lambda e: (e.split("@")[0] in ("info","contact","hello","office","admin") , -found[e]), reverse=False)
    return c["name"], site, pick[:2], [e for e in found if e not in same][:2]
rows = [c for c in D if not c.get("email")]
with ThreadPoolExecutor(12) as ex: res = list(ex.map(scrape, rows))
out = csv.writer(open("outreach/advisor-emails.csv", "w", newline=""))
out.writerow(["name", "website", "email", "other_found"])
n = 0
for r in res:
    if len(r) == 3: out.writerow([r[0], r[1], "", ""]); continue
    name, site, pick, other = r
    out.writerow([name, site, ";".join(pick), ";".join(other)]); n += bool(pick)
print(f"{len(rows)} companies, {sum(1 for r in res if r[1])} with a site, {n} with a same-domain email")
