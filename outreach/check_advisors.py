"""Check advisor-list.csv: email domain vs company website, MX record, website loads. Writes advisor-review.csv (flagged rows); does not edit the list."""
import csv, json, os, re, subprocess, urllib.request
from concurrent.futures import ThreadPoolExecutor
D = os.path.dirname(os.path.abspath(__file__)); H = "/Users/sammenard/Downloads/hpr-advisors/"
FREE = {"gmail.com","hotmail.com","outlook.com","yahoo.com","yahoo.ca","shaw.ca","telus.net","live.com","icloud.com","me.com","aol.com","msn.com","comcast.net","protonmail.com"}
dirc = {c["name"]: c for c in json.load(open(H + "data/energy-advisor-directory.json"))["companies"]}
sites = {}
for x in csv.DictReader(open(H + "outreach/advisor-emails.csv")): sites[x["name"]] = x["website"]
core = lambda h: re.sub(r"[^a-z0-9]", "", re.sub(r"^www\.", "", h.lower()).split(".")[-2] if "." in h else h)
def mx(dom):
    r = subprocess.run(["dig", "+short", "MX", dom], capture_output=True, text=True, timeout=15).stdout.strip()
    return bool(r)
def web(u):
    try: return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=12).status < 400
    except Exception: return False
def chk(r):
    dom = r["email"].split("@")[1].lower(); c = dirc.get(r["name"], {})
    w = sites.get(r["name"]) or c.get("website") or (c.get("google") or {}).get("website") or ""
    host = re.sub(r"^https?://", "", w).split("/")[0]
    flags = []
    if not mx(dom): flags.append("no MX")
    if dom in FREE: flags.append("free mail")
    elif host and core(dom) != core(host): flags.append(f"domain differs from {host}")
    if w and not web(w if w.startswith("http") else "http://" + w): flags.append("site not loading")
    if not w: flags.append("no website on file")
    return {**r, "flags": "; ".join(flags)}
rows = list(csv.DictReader(open(f"{D}/advisor-list.csv")))
with ThreadPoolExecutor(10) as ex: res = list(ex.map(chk, rows))
bad = [r for r in res if r["flags"]]
w = csv.DictWriter(open(f"{D}/advisor-review.csv", "w", newline=""), list(res[0].keys())); w.writeheader(); w.writerows(bad)
print(len(rows), "checked,", len(bad), "flagged")
from collections import Counter
print(Counter(f.split(" from")[0] for r in bad for f in r["flags"].split("; ")))
