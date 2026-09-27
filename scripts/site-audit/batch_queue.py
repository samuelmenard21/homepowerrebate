#!/usr/bin/env python3
"""
Pulls the next batch of BC installers (with email + website), audits them,
generates reports, and tracks who's already been queued so re-runs don't repeat.

Usage:
    .venv/bin/python batch_queue.py --batch-size 10

Outputs:
    - reports/bc-batches/batch_NNN.json  (name, email, website, score, grade, report path)
    - reports/bc-batches/html/*.html     (the actual reports to attach/link)
    - queue_state.json                   (tracks who's been queued, so reruns give fresh names)
"""
import argparse
import json
from pathlib import Path

from audit import audit_installer
from generate_report import render_report, slugify

BC_CITIES = [
    "abbotsford", "burnaby", "chilliwack", "coquitlam", "fort-st-john",
    "kamloops", "kelowna", "langley", "maple-ridge", "nanaimo",
    "penticton", "prince-george", "richmond", "squamish", "surrey",
]

INSTALLERS_DIR = Path(__file__).resolve().parents[2] / "installers" / "json"
STATE_FILE = Path(__file__).resolve().parent / "queue_state.json"
BATCH_DIR = Path(__file__).resolve().parent / "reports" / "bc-batches"


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"queued": []}  # list of installer names already queued


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_bc_installers():
    installers = []
    for city in BC_CITIES:
        fp = INSTALLERS_DIR / f"{city}.json"
        if not fp.exists():
            continue
        data = json.loads(fp.read_text())
        for installer in data:
            installer["_city"] = city
            installers.append(installer)
    return installers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=10)
    args = ap.parse_args()

    state = load_state()
    already_queued = set(state["queued"])

    all_installers = load_bc_installers()
    eligible = [
        i for i in all_installers
        if i.get("email") and i.get("website") and i.get("name") not in already_queued
    ]

    if not eligible:
        print("No more eligible BC installers (email + website) that haven't already been queued.")
        return

    batch = eligible[: args.batch_size]

    html_dir = BATCH_DIR / "html"
    html_dir.mkdir(parents=True, exist_ok=True)

    batch_num = len(list(BATCH_DIR.glob("batch_*_full.json"))) + 1
    summary = []
    full_results = []

    for installer in batch:
        print(f"Auditing: {installer['name']} ({installer['website']}) — {installer['_city']}")
        result = audit_installer(installer)
        result["email"] = installer["email"]
        result["city"] = installer["_city"]
        full_results.append(result)

        html = render_report(result)
        fname = slugify(result.get("name", "installer")) + ".html"
        (html_dir / fname).write_text(html)

        summary.append({
            "name": installer["name"],
            "email": installer["email"],
            "website": installer["website"],
            "city": installer["_city"],
            "score": result.get("score"),
            "grade": result.get("grade"),
            "report_path": str(html_dir / fname),
        })
        print(f"  -> score={result.get('score')} grade={result.get('grade')} report={html_dir / fname}")

    # Full audit data (breakdown, recommendations, growth ideas) — use THIS file to
    # regenerate reports later (e.g. after a template change). The plain batch_NNN.json
    # is a slim summary for quick reference only and is NOT enough to re-render a report.
    full_file = BATCH_DIR / f"batch_{batch_num:03d}_full.json"
    full_file.write_text(json.dumps(full_results, indent=2, default=str))

    batch_file = BATCH_DIR / f"batch_{batch_num:03d}.json"
    batch_file.write_text(json.dumps(summary, indent=2))

    state["queued"].extend(i["name"] for i in batch)
    save_state(state)

    print(f"\nSaved batch of {len(summary)} to {batch_file}")
    print(f"Reports in {html_dir}")
    remaining = len(eligible) - len(batch)
    print(f"{remaining} more eligible installers remain in the queue for next batch.")


if __name__ == "__main__":
    main()
