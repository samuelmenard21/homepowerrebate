"""Send the installer outreach email through Resend.

  python3 outreach/send.py --test you@example.com   # one sample email to you
  python3 outreach/send.py --send --limit 50        # next 50 unsent installers
Prompts for the Resend API key (hidden) and mailing address unless set in the environment. Logs to outreach/sent.csv;
emails in outreach/suppress.txt (one per line) are never sent."""
import argparse, getpass, subprocess, csv, html, json, os, re, sys, time, urllib.request, datetime
D = os.path.dirname(os.path.abspath(__file__))
FROM = "Sam Menard <hello@homepowerrebate.com>"
BADGE = "https://homepowerrebate.com/installers/badge/"
DAILY_CAP = 80  # most intro emails sent per calendar day, across all runs
# Which email copy went out, logged per send so check_links.py results can be compared by version.
# v1 = Oct 13 original (first 180, saved for a future email 2); v2 = Oct 17 links-first copy.
VARIANT = "v4"  # v3 = Oct 17 short names, rating line, preview text; v4 = Oct 21 asks for their 3 biggest challenges, no badge/calculator/P.S.

KC = "hpr-outreach-resend"
def keychain_get():
    out = subprocess.run(["security", "find-generic-password", "-s", KC, "-w"], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else ""

REGION_NAMES = {r["abbr"]: r["name"] for r in json.load(open(os.path.join(D, "..", "data", "regions.json")))["regions"]}
CA_REGIONS = {r["abbr"] for r in json.load(open(os.path.join(D, "..", "data", "regions.json")))["regions"] if r["country"] == "ca"}
ALERT = "https://homepowerrebate.com/heat-pump-rebate-alert/"  # federal rebate launch list; ?src= tells the weekly report who shared it
LINK = 'style="color:#0d4f5c;font-weight:600;"'

# Google rating and review count per (email, ranking page), from the rankings build.
_RATINGS = {}
_rp = os.path.join(D, "..", "data", "outreach-rankings.csv")
if os.path.exists(_rp):
    for x in csv.DictReader(open(_rp)):
        _RATINGS[(x["email"].strip().lower(), x["ranking_url"])] = (x["rating"], x["reviews"])

_SUFFIX = re.compile(r"[\s,]+(ltd|limited|inc|incorporated|llc|corp|corporation|co|company)\.?$", re.I)


def short_name(name):
    """The name a person would say: Google listing names often carry keywords, a city, a licence number or a legal
    suffix ("Waywest Mechanical Ltd - 24 Hour service Nanaimo" -> "Waywest Mechanical")."""
    n = re.split(r"\s+[|\u2013\u2014-]\s+|\s*\|\s*|\s+(?:TSBC\s+)?LIC\b|\s+#", name.strip())[0]
    n = re.sub(r"\s+", " ", n).strip(" ,.-")
    if len(n) > 45 and "," in n:  # keyword lists: "Sun Peak Solar Services Solar System, Solar Panels, ..."
        n = n.split(",")[0]
    for _ in range(2):
        n = _SUFFIX.sub("", n).strip(" ,.")
    if n.isupper() and len(n) > 4:  # "DS CLAYTON ELECTRIC" -> "DS Clayton Electric" (keep short acronyms)
        n = " ".join(w if len(w) <= 3 else w.capitalize() for w in n.split())
    return n or name.strip()


def rating_of(r, ranks):
    """(rating, reviews) for the installer's first ranking, or None."""
    return _RATINGS.get((r["email"].strip().lower(), ranks[0][1]))

def badge_url(rank_url):
    """The installer's own badge, already picked (the badge page reads ?r=&c=&s=)."""
    r, c, s = rank_url.rstrip("/").split("/installers/")[1].split("/")
    return f"{BADGE}?r={r}&c={c}&s={s}"

REGION_PATHS = {r["abbr"]: r["path"] for r in json.load(open(os.path.join(D, "..", "data", "regions.json")))["regions"]}
SITE = os.path.join(D, "..")


def rebate_page(r, ranks):
    """The installer's city page for the service they're ranked for (falls back to the city hub, then the region hub)."""
    region_path = REGION_PATHS.get(r["region"], "")
    city, svc = ranks[0][1].rstrip("/").split("/")[-2:]
    for path in (f"{region_path}/{city}/{svc}", f"{region_path}/{city}", region_path):
        if path and os.path.exists(os.path.join(SITE, path, "index.html")):
            return f"https://homepowerrebate.com/{path}/"
    return None


def alert_ps(r):
    """A P.S. that fits what the installer does. Canadian heat pump installers get the federal heat pump rebate alert page,
    tagged with their profile slug so the weekly report (scripts/federal_alert_report.py) shows who shares it; everyone
    else gets their city's rebate page for their own service."""
    ranks = json.loads(r["rankings"])
    hp = next(((s, u) for s, u in ranks if u.rstrip("/").endswith("/heat-pump")), None)
    if r["region"] in CA_REGIONS and hp:
        slug = r["profile_url"].rstrip("/").rsplit("/", 1)[-1][:40]
        return (f'\n<p>P.S. Ottawa\'s new heat pump rebate (up to $10,000) opens in early 2027, and your customers may start asking about it. '
                f'This page lets them get an email the day it opens: <a href="{ALERT}?src=inst-{slug}" {LINK}>heat pump rebate alert</a>. '
                "Feel free to share it.</p>")
    url = rebate_page(r, ranks)
    if not url:
        return ""
    service, city = html.escape(ranks[0][0]), html.escape(r["city"])
    return (f'\n<p>P.S. Customers often ask which {service} rebates they can get. This page shows what is open in {city} right now, '
            f'each with a link to the official source: <a href="{url}" {LINK}>{service} rebates in {city}</a>. Feel free to share it.</p>')

def body(r, address):
    """Intro email, 2026-10-21 version: one ask, their 3 biggest challenges (v3 asked for the badge and calculator; response was about 1%).
    Installer copy never says "free" or mentions price (see memory feedback-never-promise-always-free)."""
    ranks = json.loads(r["rankings"])
    lines = "".join(f'<li><a href="{u}">Top-rated {html.escape(c)} installers in {html.escape(r["city"])}</a></li>' for c, u in ranks)
    name, city = html.escape(short_name(r["name"])), html.escape(r["city"])
    service = html.escape(ranks[0][0])
    region = html.escape(REGION_NAMES.get(r["region"], r["region"]))
    calc = f"https://homepowerrebate.com/calculator/widget/?r={r['region'].lower()}"
    rt = rating_of(r, ranks)
    praise = (f"Congrats on building such a strong reputation in {city}. {float(rt[0]):.1f} stars from {int(float(rt[1])):,} Google reviews is impressive, "
              "and because of it we've added you to our top-rated list:") if rt else \
        f"Congrats on building such a strong reputation in {city}. Your Google reviews speak for themselves! Because of your great rating, we've added you to our top-rated list:"
    preview = f"Congrats, you're on our top-rated {service} list in {city}. Quick question about your business."
    # hidden preview text: the line inboxes show next to the subject
    pre = (f'<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;mso-hide:all;">{preview}'
           + "&nbsp;&zwnj;" * 40 + "</div>")
    return f"""{pre}<p>Hi {name} team,</p>
<p>I'm Sam, founder of <a href="https://homepowerrebate.com/">HomePowerRebate</a>. We help local homeowners find the energy rebates they qualify for, then point them to top-reviewed local installers to do the work.</p>
<p>{praise}</p>
<ul>{lines}</ul>
<p>Here's your profile: <a href="{r['profile_url']}">{name} on HomePowerRebate</a>.</p>
<p>I'm building this around what installers actually need, so I have one question: <b>what are the 3 biggest challenges in your business right now?</b> Finding good customers, rebate paperwork, hiring, slow seasons, anything at all.</p>
<p>Just reply with a few lines. I read every answer myself, and I'll tell you honestly whether I can help.</p>
<p>Best regards,<br>Sam Menard<br>Founder, HomePowerRebate<br><a href="https://homepowerrebate.com/">homepowerrebate.com</a> &middot; <a href="https://www.linkedin.com/company/homepowerrebate/">LinkedIn</a></p>
<p style="font-size:12px;color:#777">HomePowerRebate, {html.escape(address)}<br>You're receiving this because your business email is listed on Google Maps. Reply "remove" and we won't email you again.</p>"""

def send(to, subject, htm, key):
    req = urllib.request.Request("https://api.resend.com/emails", method="POST",
        data=json.dumps({"from": FROM, "to": [to], "subject": subject, "html": htm,
                         "reply_to": "hello@homepowerrebate.com"}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "hpr-outreach"})
    with urllib.request.urlopen(req, timeout=30) as resp: return json.load(resp).get("id")

def main():
    a = argparse.ArgumentParser(); a.add_argument("--test"); a.add_argument("--send", action="store_true")
    a.add_argument("--limit", type=int, default=50); a.add_argument("--preview", action="store_true"); o = a.parse_args()
    key, addr = os.environ.get("RESEND_API_KEY"), os.environ.get("MAILING_ADDRESS")
    rows = list(csv.DictReader(open(f"{D}/installer-list.csv")))
    subj = lambda r: f"Featured: {short_name(r['name'])} on HomePowerRebate (+ congrats on the great reviews!)"
    if o.preview:
        open(f"{D}/preview.html", "w").write(body(rows[0], addr or "[MAILING ADDRESS]")); print(subj(rows[0])); return
    if not key: key = keychain_get()
    if not key:
        key = getpass.getpass("Resend API key (hidden, saved to your Mac keychain): ").strip()
        if key: subprocess.run(["security", "add-generic-password", "-U", "-s", KC, "-a", "resend", "-w", key])
    cfg_path = f"{D}/config.json"
    cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}
    addr = addr or cfg.get("mailing_address")
    if not addr:
        addr = input("Mailing address for the footer (with postal code): ").strip()
        if addr: json.dump({**cfg, "mailing_address": addr}, open(cfg_path, "w"))
    if not key or not addr: sys.exit("Need both a Resend API key and a mailing address.")
    if o.test:
        print("sent", send(o.test, "[TEST] " + subj(rows[0]), body(rows[0], addr), key)); return
    if not o.send: sys.exit("Use --preview, --test or --send.")
    sent_path = f"{D}/sent.csv"
    done = {r["email"] for r in csv.DictReader(open(sent_path))} if os.path.exists(sent_path) else set()
    sup = {l.strip().lower() for l in open(f"{D}/suppress.txt")} if os.path.exists(f"{D}/suppress.txt") else set()
    today = datetime.date.today().isoformat()
    sent_today = sum(1 for r in csv.DictReader(open(sent_path)) if r["sent_at"].startswith(today)) if os.path.exists(sent_path) else 0
    limit = min(o.limit, max(0, DAILY_CAP - sent_today))
    if limit < o.limit: print(f"Daily cap {DAILY_CAP}: {sent_today} already sent today, sending at most {limit}.")
    new = not os.path.exists(sent_path); n = 0
    if not new:  # older files have no variant column: add it once (blank = v1)
        lines = open(sent_path).read().splitlines()
        if lines and not lines[0].endswith(",variant"):
            open(sent_path, "w").write("\n".join([lines[0] + ",variant"] + lines[1:]) + "\n")
    with open(sent_path, "a", newline="") as fh:
        w = csv.writer(fh)
        if new: w.writerow(["email", "name", "city", "resend_id", "sent_at", "variant"])
        for r in rows:
            if n >= limit: break
            if r["email"] in done or r["email"] in sup: continue
            try: rid = send(r["email"], subj(r), body(r, addr), key)
            except Exception as e: print("FAILED", r["email"], e); continue
            w.writerow([r["email"], r["name"], r["city"], rid, datetime.datetime.now().isoformat(timespec="seconds"), VARIANT]); fh.flush()
            n += 1; print(n, r["email"]); time.sleep(0.6)
    print(f"Sent {n}. Total sent: {len(done) + n} of {len(rows)}.")
main()
