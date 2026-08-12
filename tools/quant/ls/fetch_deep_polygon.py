"""Deep polygon history: extend the L/S panel from ~2y to ~4.7y, 2026-08-04.

Polygon free tier returns the MOST RECENT `limit` bars in a range.  To go
deep, paginate backward: call 1 with start=2021-06-01 (gets 2024-08..now),
then call k+1 with end = day before call k's first date, until the earliest
date <= 2021-06-01 or max 4 calls.  Union-merge into the existing panel
CSV (schema date,open,high,low,close,vol).  13s pacing, ~252 calls,
~55 min total.  Run:  python -m tools.quant.ls.fetch_deep_polygon
"""
from __future__ import annotations
import os, sys, time, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pandas as pd

from tools.wt import sources

POLY_DIR = os.path.join(ROOT, "tools", "quant", "data", "polygon")
TARGET_EARLIEST = "2021-06-01"
MAX_CALLS = 4
PAUSE = 14.0


def _fetch_pages(sym: str) -> list:
    """Paginate backward; returns list of {date,open,high,low,close,vol} rows
    oldest-first (the panel's convention).  Pauses between EVERY call (free
    tier 5/min) and only treats 'too few bars' as the data floor when the
    latest fetched page already starts at/near TARGET_EARLIEST; otherwise
    a transient error (429 etc.) just retries the same page."""
    pages = []
    end = None
    for _ in range(MAX_CALLS):
        h, err = sources.polygon_history(sym, start=TARGET_EARLIEST,
                                         end=end, limit=500)
        if h and h["date"]:
            pages.append(h)
            first = h["date"][0]
            if first <= TARGET_EARLIEST:
                break
            end = (datetime.date.fromisoformat(first)
                   - datetime.timedelta(days=1)).isoformat()
        else:
            # 'too few bars' is a genuine floor ONLY if we're already at the
            # target; otherwise treat it as a transient error and retry.
            if pages and pages[-1]["date"][0] <= TARGET_EARLIEST:
                break
            print(f"    {sym}: transient '{err}' -- retrying page", flush=True)
        time.sleep(PAUSE)  # rate limit: also between pages
    if not pages:
        return [], "no data"
    # newest-first within each page; concat pages (page0 newest) then reverse
    rows = []
    for p in pages:
        for i in range(len(p["date"]) - 1, -1, -1):
            rows.append((p["date"][i], p["open"][i], p["high"][i],
                         p["low"][i], p["close"][i], p["vol"][i]))
    rows = list(reversed(rows))  # oldest-first
    return rows, None


def main() -> int:
    files = sorted(f for f in os.listdir(POLY_DIR) if f.endswith(".csv"))
    print(f"deep fetch {len(files)} tickers ({MAX_CALLS} calls/ticker, "
          f"~{len(files)*MAX_CALLS*PAUSE/60:.0f} min)", flush=True)
    ok, fail = 0, 0
    for i, fn in enumerate(files):
        sym = fn[:-4]
        path = os.path.join(POLY_DIR, fn)
        rows, err = _fetch_pages(sym)
        if not rows:
            fail += 1
            print(f"  [{i+1}/{len(files)}] {sym} FAIL: {err}", flush=True)
            time.sleep(2.0)
            continue
        new = pd.DataFrame(rows, columns=["date", "open", "high", "low",
                                          "close", "vol"])
        new["date"] = pd.to_datetime(new["date"])
        try:
            old = pd.read_csv(path, parse_dates=["date"])
        except Exception:
            old = pd.DataFrame(columns=new.columns)
        merged = (pd.concat([old, new], ignore_index=True)
                    .drop_duplicates(subset="date", keep="last")
                    .sort_values("date"))
        tmp = path + ".tmp"
        merged.to_csv(tmp, index=False, date_format="%Y-%m-%d")
        os.replace(tmp, path)
        ok += 1
        print(f"  [{i+1}/{len(files)}] {sym} OK: {len(merged)} bars "
              f"({merged['date'].iloc[0].date()}..{merged['date'].iloc[-1].date()})",
              flush=True)
        time.sleep(2.0)
    print(f"\n=== deep fetch complete: {ok} ok, {fail} fail ===", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
