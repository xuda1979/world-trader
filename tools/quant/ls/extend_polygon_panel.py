"""Refresh the L/S polygon panel (fresh bars + keep depth), 2026-08-04.

Polygon free tier: 5 calls/min, 500 bars/call (returns the MOST RECENT 500
bars in range).  For each of the 84 panel tickers: fetch 500 daily bars
ending today, union-merge with the existing CSV (existing rows win on
overlap except where the new fetch is newer), write back in the panel's
schema (date,open,high,low,close,vol).  ~84 calls at 13s spacing ≈ 18-20 min.

Run:  python -m tools.quant.ls.extend_polygon_panel
"""
from __future__ import annotations
import os, sys, time, csv

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pandas as pd

from tools.wt import sources

POLY_DIR = os.path.join(ROOT, "tools", "quant", "data", "polygon")


def main() -> int:
    files = sorted(f for f in os.listdir(POLY_DIR) if f.endswith(".csv"))
    print(f"refreshing {len(files)} tickers from Polygon (13s pacing, ~18 min)",
          flush=True)
    ok, fail = 0, 0
    for i, fn in enumerate(files):
        sym = fn[:-4]
        path = os.path.join(POLY_DIR, fn)
        try:
            old = pd.read_csv(path, parse_dates=["date"])
        except Exception:
            old = pd.DataFrame(columns=["date", "open", "high", "low", "close", "vol"])
        h, err = sources.polygon_history(sym, start="2019-01-01", end=None, limit=500)
        if not h:
            fail += 1
            print(f"  [{i+1}/{len(files)}] {sym} FAIL: {err}", flush=True)
            time.sleep(13.0)
            continue
        new = pd.DataFrame({"date": pd.to_datetime(h["date"]),
                            "open": h["open"], "high": h["high"],
                            "low": h["low"], "close": h["close"], "vol": h["vol"]})
        merged = pd.concat([old, new], ignore_index=True)
        merged = (merged.drop_duplicates(subset="date", keep="last")
                       .sort_values("date"))
        tmp = path + ".tmp"
        merged.to_csv(tmp, index=False, date_format="%Y-%m-%d")
        os.replace(tmp, path)
        ok += 1
        print(f"  [{i+1}/{len(files)}] {sym} OK: {len(old)} -> {len(merged)} bars "
              f"({merged['date'].iloc[0].date()}..{merged['date'].iloc[-1].date()})",
              flush=True)
        time.sleep(13.0)
    print(f"\n=== refresh complete: {ok} ok, {fail} fail ===", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
