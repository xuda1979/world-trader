"""Fetch 8-year daily history from Twelve Data with robust retries.

Twelve Data free tier: 8 calls/min, 5000 bars max per call.  We pull 2000
daily bars (~8 years) per ticker for the 84-name universe, caching to
tools/quant/data/twelvedata/<SYM>.csv so the L/S backtester can use the
longer history.

Run:
    python -m tools.quant.ls.fetch_long_history
"""
from __future__ import annotations
import os, sys, time, csv
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.wt import sources

OUT_DIR = os.path.join(ROOT, "tools", "quant", "data", "twelvedata")
os.makedirs(OUT_DIR, exist_ok=True)

POLY_DIR = os.path.join(ROOT, "tools", "quant", "data", "polygon")
UNIVERSE = sorted([f[:-4] for f in os.listdir(POLY_DIR) if f.endswith(".csv")])

def main():
    n_total = len(UNIVERSE)
    print("fetching %d tickers x 2000 days (~8y) from Twelve Data" % n_total)
    print("  free tier 8 calls/min -> ~%d min total" % (n_total // 8))
    ok, fail, skip = 0, 0, 0
    for i, sym in enumerate(UNIVERSE):
        cache_path = os.path.join(OUT_DIR, "%s.csv" % sym)
        # Skip if already cached with >= 1500 bars
        if os.path.exists(cache_path):
            try:
                with open(cache_path) as f:
                    n = sum(1 for _ in f) - 1
                if n >= 1500:
                    skip += 1
                    if (i + 1) % 10 == 0:
                        print("  [%d/%d] %s cached (%d bars) -- skip" % (i + 1, n_total, sym, n))
                    continue
            except Exception:
                pass
        # Live fetch with aggressive retries (Twelve Data connection is flaky)
        hist = None
        err = "no provider"
        for attempt in range(2):
            try:
                hist, err = sources.twelvedata_history(sym, days=2000)
                if hist and len(hist.get("close", [])) >= 500:
                    break
            except Exception as e:
                err = str(e)[:60]
            time.sleep(3 + attempt * 2)  # backoff
        if hist and len(hist.get("close", [])) >= 500:
            with open(cache_path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["date", "open", "high", "low", "close", "vol"])
                vols = hist.get("vol", [0] * len(hist["close"]))
                for j in range(len(hist["close"])):
                    w.writerow([hist["date"][j], hist["open"][j], hist["high"][j],
                                hist["low"][j], hist["close"][j], vols[j]])
            ok += 1
            print("  [%d/%d] %s OK (%d bars) %s..%s" % (
                i + 1, n_total, sym, len(hist["close"]),
                hist["date"][0], hist["date"][-1]))
        else:
            fail += 1
            print("  [%d/%d] %s FAIL: %s" % (i + 1, n_total, sym, err))
        # Rate limit: 8 calls/min -> 7.5s sleep
        time.sleep(15.0)
    print("\n=== fetch complete: %d ok, %d fail, %d skip ===" % (ok, fail, skip))
    return 0

if __name__ == "__main__":
    sys.exit(main())
