#!/usr/bin/env python3
"""Send the personal website and Google listing review notes (data/installer-reviews/emails.json), 2026-11-04.

Each note is written by hand for one company (an observation from its own site, 1 to 2 fixes) and numbers come from the review JSON
(scripts/installer_review.py). Sends through Resend like outreach/send.py, using that pipeline's state in the main checkout: Resend key in the
Mac keychain, mailing address in outreach/config.json, outreach/suppress.txt (never emailed), outreach/review-sent.csv (one note per address, ever).
Installer copy never says free or mentions price, and asks for nothing in this first note.
Usage: --preview (writes HTML to --out), --test you@example.com [--only NAME], --send [--only NAME]"""
import argparse
import csv
import datetime
import html
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent.parent
MAIN = Path("/Users/sammenard/Downloads/Powerrebate/outreach")
FROM = "Sam Menard <hello@homepowerrebate.com>"
REPLY_TO = "hello@homepowerrebate.com"
e = html.escape


def key():
    r = subprocess.run(["security", "find-generic-password", "-s", "hpr-outreach-resend", "-w"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def review_for(company):
    for f in (ROOT / "data" / "installer-reviews").glob("*.json"):
        if f.name == "emails.json":
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        if d["company"] == company:
            return d
    raise SystemExit(f"no review for {company}")


def compose(m, address):
    d = review_for(m["company"])
    g = d["google"]
    n = g["companies_in_city"]
    strong = " That is a strong score." if d["passed"] / d["of"] >= 0.8 else ""
    intro = (f"I emailed you on {m['earlier']} about our top-rated list. I should have started with something useful, so here it is. " if m["earlier"] else
             "I'm Sam, founder of <a href=\"https://homepowerrebate.com/\">HomePowerRebate</a>. ")
    rank = f"We rank heat pump installers in {e(m['city'])} by their Google reviews, and {e(m['name'])} is first of {n}."
    fixes = "".join(f"<li>{e(x)}</li>" for x in m["fixes"])
    page = d["page"]
    body = (f'<p>Hi {e(m["name"])} team,</p>'
            f'<p>{intro}{rank} Here is your page: <a href="{page}">{page.replace("https://", "")}</a>.</p>'
            f'<p>{e(m["obs"])}</p>'
            f'<p>I looked at your homepage the way a homeowner on a phone would. It passes {d["passed"]} of {d["of"]} basic checks.{strong} '
            f'{"The one thing I would change first:" if len(m["fixes"]) == 1 else "Two things I would change first:"}</p><ul>{fixes}</ul>'
            f'<p>I only looked at your homepage, so you may already cover this on other pages. If it helps, reply and I will send the full one-page review, which also covers your Google listing. '
            f'Either way, congratulations on the reviews.</p>'
            f'<p>Best regards,<br>Sam Menard<br>Founder, HomePowerRebate<br><a href="https://homepowerrebate.com/">homepowerrebate.com</a></p>'
            f'<p style="font-size:12px;color:#777">HomePowerRebate, {e(address)}<br>You are receiving this because your business email is listed on your website or Google Maps. Reply "remove" and we will not email you again.</p>')
    return f"A few ideas for the {m['name']} website", body


def post(to, subject, htm, k):
    req = urllib.request.Request("https://api.resend.com/emails", method="POST",
                                 data=json.dumps({"from": FROM, "to": [to], "subject": subject, "html": htm, "reply_to": REPLY_TO}).encode(),
                                 headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json", "User-Agent": "hpr-outreach"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r).get("id")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--out", default="/tmp")
    ap.add_argument("--test")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--only")
    a = ap.parse_args()
    notes = json.loads((ROOT / "data" / "installer-reviews" / "emails.json").read_text(encoding="utf-8"))
    if a.only:
        notes = [m for m in notes if a.only.lower() in m["company"].lower()]
    cfg = json.loads((MAIN / "config.json").read_text())
    address = cfg.get("mailing_address", "[MAILING ADDRESS]")
    if a.preview:
        for m in notes:
            subj, body = compose(m, address)
            (Path(a.out) / f"review-{m['name'].replace(' ', '-').replace('&', 'and')}.html").write_text(f"<h3>{e(subj)}</h3><p>To: {e(m['to'])}</p>{body}", encoding="utf-8")
            print(subj, "->", m["to"])
        return
    k = key()
    if not k:
        sys.exit("No Resend key in the keychain.")
    if a.test:
        for m in notes:
            subj, body = compose(m, address)
            print("test sent", post(a.test, "[TEST] " + subj, f"<p style='background:#fff3cd;padding:8px'>TEST. Would go to {e(m['to'])}.</p>" + body, k))
            time.sleep(0.6)
        return
    if not a.send:
        sys.exit("Use --preview, --test or --send.")
    sup = {l.strip().lower() for l in (MAIN / "suppress.txt").read_text().splitlines()}
    log = MAIN / "review-sent.csv"
    done = {r["email"] for r in csv.DictReader(log.open())} if log.exists() else set()
    new = not log.exists()
    with log.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["email", "company", "city", "resend_id", "sent_at"])
        for m in notes:
            to = m["to"].strip().lower()
            if to in sup or to in done:
                print("skip", to)
                continue
            subj, body = compose(m, address)
            w.writerow([to, m["company"], m["city"], post(m["to"], subj, body, k), datetime.datetime.now().isoformat(timespec="seconds")])
            fh.flush()
            print("sent", to)
            time.sleep(0.8)


if __name__ == "__main__":
    main()
