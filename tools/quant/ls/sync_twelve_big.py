#!/usr/bin/env python3
"""Sync the fresher twelvedata CSVs into twelve_big (AP composite universe).

twelve_big (291 names, the AP gold composite universe) is maintained by
fetch_twelvedata_universe.py, which SKIPS existing files - it never
refreshes. The twelvedata dir refreshes nightly via the scanner. This
tool copies the fresher overlapping files across (schema is identical:
open/high/low/close/vol). Non-overlapping names are reported so they can
be re-fetched via the API tool if desired.

Usage:
  python -m tools.quant.ls.sync_twelve_big         # sync overlapping names
  python -m tools.quant.ls.sync_twelve_big --check # report only, no copy
"""
from __future__ import annotations
import os, sys, shutil, glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
BIG = os.path.join(ROOT, "tools", "quant", "data", "twelve_big")
TD = os.path.join(ROOT, "tools", "quant", "data", "twelvedata")


def main() -> int:
    check_only = "--check" in sys.argv
    tb = {os.path.basename(f): f for f in glob.glob(os.path.join(BIG, "*.csv"))}
    td = {os.path.basename(f): f for f in glob.glob(os.path.join(TD, "*.csv"))}
    copied = stale = missing = 0
    for name, tb_path in sorted(tb.items()):
        td_path = td.get(name)
        if td_path is None:
            missing += 1
            continue
        tb_mtime = os.path.getmtime(tb_path)
        td_mtime = os.path.getmtime(td_path)
        if td_mtime > tb_mtime:
            if not check_only:
                shutil.copyfile(td_path, tb_path)
            copied += 1
        else:
            stale += 1
    print(f"twelve_big: {copied} refreshed from twelvedata"
          f"{' (check only)' if check_only else ''}, {stale} already current, "
          f"{missing} not in twelvedata (need API re-fetch)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
