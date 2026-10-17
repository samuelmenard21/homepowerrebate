#!/usr/bin/env python3
"""Run a page builder without writing anything and save what it would write, so two versions of a builder can be compared
byte for byte (refactors must not change output).

  python3 scripts/capture_build.py OUT.json scripts/build_bc_pages.py [--hubs ...]
  python3 scripts/capture_build.py --compare A.json B.json
"""
import json
import pathlib
import runpy
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def capture(out, script, args):
    written = {}
    real = pathlib.Path.write_text

    def fake(self, data, *a, **k):
        p = pathlib.Path(self).resolve()
        if p.suffix == ".html":
            written[str(p.relative_to(ROOT))] = data
            return len(data)
        return real(self, data, *a, **k)

    pathlib.Path.write_text = fake
    sys.argv = [script, *args]
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit as x:
        if x.code not in (None, 0):
            written["__exit__"] = str(x.code)
    real(pathlib.Path(out), json.dumps(written, sort_keys=True), encoding="utf-8")
    print(f"{len(written)} pages captured from {script} {' '.join(args)}")


def compare(a, b):
    A, B = json.loads(pathlib.Path(a).read_text()), json.loads(pathlib.Path(b).read_text())
    keys = sorted(set(A) | set(B))
    bad = [k for k in keys if A.get(k) != B.get(k)]
    for k in bad[:5]:
        x, y = A.get(k, ""), B.get(k, "")
        i = next((n for n, (p, q) in enumerate(zip(x, y)) if p != q), min(len(x), len(y)))
        print(f"DIFF {k}\n  old: {x[max(0, i - 120):i + 160]!r}\n  new: {y[max(0, i - 120):i + 160]!r}")
    print(f"{len(keys)} pages, {len(bad)} differ")
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1] == "--compare":
        sys.exit(compare(sys.argv[2], sys.argv[3]))
    capture(sys.argv[1], sys.argv[2], sys.argv[3:])
