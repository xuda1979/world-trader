#!/usr/bin/env python3
"""Restore the leading bars of tools/quant/data/polygon/*.csv from twelvedata.

On 2026-08-13 an earlier refresh truncated every polygon file to Polygon's
free-tier 501-bar cap, dropping the earliest ~16 sessions (start 2024-07-24
-> 2024-08-12). Verified: twelvedata prices for this window match polygon's
split/dividend-adjusted series EXACTLY (e.g. NVDA 116.14 both, same OHLC,
~equal volume), so prepending twelvedata rows restores the original panel
with no adjustment mismatch. This is a one-shot repair backfill, not a
refresh (kept separate from refresh_polygon_panel.py).

Behaviour:
  - for each polygon/*.csv, prepend twelvedata rows in [panel_start, earliest_polygon_date)
  - skips symbols already starting 2024-07-21 or earlier
  - writes a .bak of the truncated file for audit, then overwrites in place
  - reports rows added per symbol

Usage: python -m tools.quant.ls.restore_polygon_panel
"""
from __future__ import annotations
import os, glob
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PANEL = os.path.join(ROOT, "tools/quant/data/polygon")
TWL = os.path.join(ROOT, "tools/quant/data/twelvedata")

def main() -> int:
    twl = {os.path.splitext(os.path.basename(f))[0]: pd.read_csv(f)
           for f in glob.glob(os.path.join(TWL, "*.csv"))}
    total_added = 0
    for pfile in sorted(glob.glob(os.path.join(PANEL, "*.csv"))):
        sym = os.path.splitext(os.path.basename(pfile))[0]
        p = pd.read_csv(pfile)
        earliest = p["date"].iloc[0]
        if earliest <= "2024-07-21" or sym not in twl:
            continue
        tw = twl[sym]
        back = tw[tw["date"].between("2024-07-20", earliest, inclusive="left")].copy()
        back = back[["date", "open", "high", "low", "close", "vol"]]
        if back.empty:
            continue
        os.rename(pfile, pfile + ".bak")
        restored = pd.concat([back, p], ignore_index=True).drop_duplicates("date").sort_values("date")
        restored.to_csv(pfile, index=False)
        total_added += len(back)
        print(f"{sym}: +{len(back)} rows ({back['date'].iloc[0]}..{back['date'].iloc[-1]}) -> {len(restored)} rows")
    print(f"\nTotal backfilled: {total_added} rows across the panel.")

if __name__ == "__main__":
    raise SystemExit(main())
