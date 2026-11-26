#!/usr/bin/env python3
"""Save hourly crawler requests (Cloudflare) next to hourly impressions (Search Console), so the next on/off switch
can be lined up to the hour with what the server did. Read-only. Added 2026-11-26.

Why: organic impressions switch between about 2,000 a day and under 150 within one hour (Nov 17 7 am PT on, Nov 21
noon PT off). Cloudflare keeps request data for only about 3 days on this plan, and Search Console hourly data for
about 10 days, so the switch hours had gone before anyone could look. This keeps both.

What it saves, one JSON file per run in the snapshot folder (default ~/.homepowerrebate/crawl-snapshots/), merged by hour
so overlapping runs never double count:
  - cloudflare_crawlers: verified Googlebot, Bingbot and all other verified bots, requests per hour per status code
  - cloudflare_robots_sitemap: verified-bot requests to /robots.txt and /sitemap.xml per hour per status code
  - cloudflare_zone: all requests per hour per status class (200/300/400/500)
  - gsc_hourly: impressions, clicks and position per hour (Pacific time)

Credentials: wrangler's own OAuth login (~/.wrangler/config/default.toml). The token is read in memory, sent only to
api.cloudflare.com and never printed or written. Run `npx wrangler whoami` once if it says the token expired.

Usage: python3 scripts/snapshot_crawl_and_impressions.py [--dir DIR] [--report]
  --report  also print hours that look like a switch (impressions fall or rise by 5x against the 6 hours before)
"""
import argparse
import collections
import datetime as dt
import json
import os
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

ZONE = "2029f62ba5c5e52c16609b7afe3ddccc"  # homepowerrebate.com
PROJECT = "homepowerrebate"
API = "https://api.cloudflare.com/client/v4/graphql"


def token():
    cfg = tomllib.load(open(os.path.expanduser("~/.wrangler/config/default.toml"), "rb"))
    return cfg.get("oauth_token")


def gql(query, variables, tok):
    req = urllib.request.Request(API, data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=60))


def cf(query, variables):
    tok = token()
    try:
        r = gql(query, variables, tok)
    except urllib.error.HTTPError as e:
        if e.code not in (400, 401, 403):
            raise
        subprocess.run(["npx", "--no-install", "wrangler", "whoami"], capture_output=True, text=True)  # refreshes the login
        r = gql(query, variables, token())
    if r.get("errors") or not r.get("data"):
        raise SystemExit("Cloudflare query failed: " + str(r.get("errors"))[:300])
    return r["data"]["viewer"]["zones"][0]


CRAWLERS = """query($z:String!,$a:Time!,$b:Time!){viewer{zones(filter:{zoneTag:$z}){httpRequestsAdaptiveGroups(
limit:10000,filter:{datetime_geq:$a,datetime_leq:$b,verifiedBotCategory_neq:""},orderBy:[datetimeHour_ASC]){
count dimensions{datetimeHour edgeResponseStatus userAgent}}}}}"""

# robots.txt and sitemap.xml fetched by verified bots: a 4xx or 5xx on these is what Google reads as "blocked" or "unreachable"
ROBOTSQ = """query($z:String!,$a:Time!,$b:Time!){viewer{zones(filter:{zoneTag:$z}){httpRequestsAdaptiveGroups(
limit:10000,filter:{datetime_geq:$a,datetime_leq:$b,verifiedBotCategory_neq:"",clientRequestPath_in:["/robots.txt","/sitemap.xml"]},
orderBy:[datetimeHour_ASC]){count dimensions{datetimeHour edgeResponseStatus userAgent clientRequestPath}}}}}"""

ZONEQ = """query($z:String!,$a:Time!,$b:Time!){viewer{zones(filter:{zoneTag:$z}){httpRequests1hGroups(limit:200,
filter:{datetime_geq:$a,datetime_leq:$b},orderBy:[datetime_ASC]){dimensions{datetime}
sum{requests responseStatusMap{edgeResponseStatus requests}}}}}}"""


def bot_name(ua):
    u = ua.lower()
    if "googlebot" in u:
        return "Googlebot"
    if "bingbot" in u:
        return "Bingbot"
    return "other"


def cloudflare(now):
    a = (now - dt.timedelta(hours=72)).strftime("%Y-%m-%dT%H:00:00Z")  # the plan keeps about 3 days and 1 hour
    b = now.strftime("%Y-%m-%dT%H:00:00Z")
    out = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for g in cf(CRAWLERS, {"z": ZONE, "a": a, "b": b})["httpRequestsAdaptiveGroups"]:
        d = g["dimensions"]
        out[d["datetimeHour"]][bot_name(d["userAgent"])][str(d["edgeResponseStatus"])] += g["count"]
    robots = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(collections.Counter)))
    for g in cf(ROBOTSQ, {"z": ZONE, "a": a, "b": b})["httpRequestsAdaptiveGroups"]:
        d = g["dimensions"]
        robots[d["datetimeHour"]][d["clientRequestPath"]][bot_name(d["userAgent"])][str(d["edgeResponseStatus"])] += g["count"]
    robots = {h: {p: {b: dict(c) for b, c in bots.items()} for p, bots in paths.items()} for h, paths in robots.items()}
    zone = {}
    for g in cf(ZONEQ, {"z": ZONE, "a": a, "b": b})["httpRequests1hGroups"]:
        cls = collections.Counter()
        for s in g["sum"]["responseStatusMap"]:
            cls[f"{s['edgeResponseStatus'] // 100}xx"] += s["requests"]
        zone[g["dimensions"]["datetime"]] = {"requests": g["sum"]["requests"], **cls}
    return {h: {k: dict(v) for k, v in bots.items()} for h, bots in out.items()}, zone, robots


def gsc_hourly(now):
    start = (now - dt.timedelta(days=9)).strftime("%Y-%m-%d")
    end = now.strftime("%Y-%m-%d")
    body = {"startDate": start, "endDate": end, "dimensions": ["HOUR"], "dataState": "HOURLY_ALL", "rowLimit": 1000}
    f = Path("/tmp/hpr_gsc_hourly_body.json")
    f.write_text(json.dumps(body))
    r = subprocess.run(["seo", "gsc-query", f"--project={PROJECT}", "--refresh", f"--body-file={f}", "--json"],
                       capture_output=True, text=True)
    try:
        rows = json.loads(r.stdout).get("rows")
    except ValueError:
        rows = None
    if not rows:
        print("Search Console hourly data not available:", (r.stdout or r.stderr)[:200], file=sys.stderr)
        return {}
    return {x["keys"][0]: {"impressions": x["impressions"], "clicks": x["clicks"], "position": round(x["position"], 1)} for x in rows}


def merge(path, key, new):
    old = json.loads(path.read_text()) if path.exists() else {}
    cur = old.get(key, {})
    cur.update(new)  # a newer pull of the same hour replaces the older one (late data fills in)
    old[key] = dict(sorted(cur.items()))
    return old


def robots_report(data):
    tot, bad = 0, collections.Counter()
    for h, paths in data.get("cloudflare_robots_sitemap", {}).items():
        for path, bots in paths.items():
            for st, n in bots.get("Googlebot", {}).items():
                tot += n
                if not st.startswith("2"):
                    bad[(path, st)] += n
    if tot:
        print(f"  Googlebot robots.txt and sitemap.xml fetches in the saved hours: {tot}, not 200: {sum(bad.values())} {dict(bad) or ''}")


def report(gsc):
    hrs = sorted(gsc)
    for i in range(6, len(hrs)):
        before = sum(gsc[h]["impressions"] for h in hrs[i - 6:i]) / 6
        now = gsc[hrs[i]]["impressions"]
        if (before >= 30 and now * 5 < before) or (before < 10 and now >= 50):
            print(f"  switch? {hrs[i]}: {now} impressions after about {before:.0f} an hour before")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.expanduser("~/.homepowerrebate/crawl-snapshots"))
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    d = Path(a.dir)
    d.mkdir(parents=True, exist_ok=True)
    crawlers, zone, robots = cloudflare(now)
    gsc = gsc_hourly(now)
    f = d / "snapshot.json"  # one growing file, merged by hour
    data = merge(f, "cloudflare_crawlers", crawlers)
    data["cloudflare_robots_sitemap"] = dict(sorted({**data.get("cloudflare_robots_sitemap", {}), **robots}.items()))
    data["cloudflare_zone"] = dict(sorted({**data.get("cloudflare_zone", {}), **zone}.items()))
    data["gsc_hourly"] = dict(sorted({**data.get("gsc_hourly", {}), **gsc}.items()))
    data["updated"] = now.isoformat(timespec="seconds")
    f.write_text(json.dumps(data, indent=1))
    print(f"saved {f}: {len(data['cloudflare_crawlers'])} crawler hours, {len(data['cloudflare_zone'])} zone hours, "
          f"{len(data['gsc_hourly'])} Search Console hours")
    if a.report:
        report(data["gsc_hourly"])
        robots_report(data)


if __name__ == "__main__":
    main()
