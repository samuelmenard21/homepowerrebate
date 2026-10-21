"""Send the energy advisor / home energy auditor intro email through Resend (separate from the installer email).

  python3 outreach/send_advisors.py --preview              # writes advisor-preview.html
  python3 outreach/send_advisors.py --test you@example.com
  python3 outreach/send_advisors.py --send --limit 20      # next 20 unsent
List: outreach/advisor-list.csv (companies in data/energy-advisor-directory.json with an email). Logs to advisor-sent.csv;
skips outreach/suppress.txt, anyone in sent.csv (installer emails) and anyone already in advisor-sent.csv."""
import argparse, csv, datetime, html, json, os, sys, time
sys.argv, _argv = sys.argv[:1], sys.argv  # send.py runs main() on import; reuse its helpers via exec of the top part
D = os.path.dirname(os.path.abspath(__file__))
_src = open(f"{D}/send.py").read().split("def main():")[0]
_ns = {"__file__": f"{D}/send.py", "__name__": "send_helpers"}
exec(compile(_src, f"{D}/send.py", "exec"), _ns)
sys.argv = _argv
send, keychain_get, short_name, REGION_NAMES, LINK, FROM = (_ns[k] for k in ("send", "keychain_get", "short_name", "REGION_NAMES", "LINK", "FROM"))
VARIANT = "adv1"
DAILY_CAP = 15

def body(r, address):
    ca = r["country"] == "ca"
    name = html.escape(short_name(r["name"]))
    reg = r["regions"].split(",")[0]
    region = html.escape(REGION_NAMES.get(reg, reg))
    role = "energy advisors" if ca else "home energy auditors"
    reg_src = "NRCan's list of licensed EnerGuide service organizations" if ca else "RESNET's list of HERS rating companies"
    calc = f"https://homepowerrebate.com/calculator/widget/?r={reg.lower()}"
    preview = f"{name} is listed in our directory of {role}, plus a rebate calculator for your website."
    pre = (f'<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;mso-hide:all;">{preview}'
           + "&nbsp;&zwnj;" * 40 + "</div>")
    return f"""{pre}<p>Hi {name} team,</p>
<p>I'm Sam, founder of <a href="https://homepowerrebate.com/">HomePowerRebate</a>. We help homeowners find the energy rebates they qualify for and explain why an assessment often comes first.</p>
<p>We built a directory of {role} for homeowners, and we listed you from {reg_src}: <a href="{r['profile_url']}" {LINK}>{name} on HomePowerRebate</a>.</p>
<p>Your page shows homeowners what you do and how to reach you. If anything on it is wrong, or you want us to add services or the cities you cover, just reply.</p>
<p>One tool you can use right away: a <a href="{calc}" {LINK}>rebate calculator for {region}</a> that you can put on your own website. Visitors see which rebates they qualify for, and the amounts update on their own when programs change.</p>
<p>Best regards,<br>Sam Menard<br>Founder, HomePowerRebate<br><a href="https://homepowerrebate.com/">homepowerrebate.com</a></p>
<p style="font-size:12px;color:#777">HomePowerRebate, {html.escape(address)}<br>You're receiving this because your business is on a public register of {role}. Reply "remove" and we won't email you again.</p>"""

def main():
    a = argparse.ArgumentParser(); a.add_argument("--test"); a.add_argument("--send", action="store_true")
    a.add_argument("--limit", type=int, default=DAILY_CAP); a.add_argument("--preview", action="store_true"); o = a.parse_args()
    rows = list(csv.DictReader(open(f"{D}/advisor-list.csv")))
    subj = lambda r: f"{short_name(r['name'])} is listed on HomePowerRebate"
    addr = json.load(open(f"{D}/config.json")).get("mailing_address", "")
    if o.preview:
        open(f"{D}/advisor-preview.html", "w").write(body(rows[0], addr)); print(subj(rows[0])); return
    key = os.environ.get("RESEND_API_KEY") or keychain_get()
    if not key or not addr: sys.exit("Need the Resend key in the keychain and a mailing address in config.json.")
    if o.test: print("sent", send(o.test, "[TEST] " + subj(rows[0]), body(rows[0], addr), key)); return
    if not o.send: sys.exit("Use --preview, --test or --send.")
    sp = f"{D}/advisor-sent.csv"
    rd = lambda p: {r["email"].lower() for r in csv.DictReader(open(p))} if os.path.exists(p) else set()
    done = rd(sp) | rd(f"{D}/sent.csv")
    sup = {l.strip().lower() for l in open(f"{D}/suppress.txt")}
    today = datetime.date.today().isoformat()
    sent_today = sum(1 for r in csv.DictReader(open(sp)) if r["sent_at"].startswith(today)) if os.path.exists(sp) else 0
    limit = min(o.limit, max(0, DAILY_CAP - sent_today)); new = not os.path.exists(sp); n = 0
    with open(sp, "a", newline="") as fh:
        w = csv.writer(fh)
        if new: w.writerow(["email", "name", "city", "resend_id", "sent_at", "variant"])
        for r in rows:
            if n >= limit: break
            e = r["email"].lower()
            if e in done or e in sup: continue
            try: rid = send(r["email"], subj(r), body(r, addr), key)
            except Exception as ex: print("FAILED", r["email"], ex); continue
            w.writerow([r["email"], r["name"], r["regions"], rid, datetime.datetime.now().isoformat(timespec="seconds"), VARIANT]); fh.flush()
            n += 1; print(n, r["email"]); time.sleep(0.6)
    print(f"Sent {n}. Advisor list: {len(done & {x['email'].lower() for x in rows}) + n} of {len(rows)}.")
main()
