#!/usr/bin/env python3
"""Kept so older pipelines (sync_regions.py, build_hubs.py, CLAUDE.md steps) still work: the whole homepage, including
this block, is now built by scripts/build_home.py from data files (2026-10-17)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_home  # noqa: E402

if __name__ == "__main__":
    build_home.main()
