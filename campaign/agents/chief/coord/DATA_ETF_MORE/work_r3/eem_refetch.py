#!/usr/bin/env python3
"""EEM single clean retry (fetch-integrity retry, not a re-tune): the R3 re-test's
one-shot fetch returned a duplicate-polluted vendor frame (5000 rows over
2012-10-12..2026-09-04 ~ 380 rows/yr — impossible for trading days). Use the R2
two-window stitch (each window under the 5000-row vendor cap, dedup keep-first
at the seam) and let the SAME fail-closed lint decide. Any FAIL stays loud."""
import json
import os
import sys
import time
import urllib.request

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from retest_r3 import classify, lint_series, key, write_series

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/tools/quant/data/more_etf"


def fetch(sym, k, start_date, end_date):
    url = (f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day"
           f"&start_date={start_date}&end_date={end_date}"
           f"&outputsize=5000&apikey={k}&format=JSON")
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


k = key()
windows = [("2007-01-01", "2016-12-31"), ("2017-01-01", "2026-09-30")]
frames = []
for w, (a, b) in enumerate(windows):
    js = fetch("EEM", k, a, b)
    if js.get("status") == "error" or "values" not in js:
        print(f"window {w} ({a}..{b}) API_ERR {str(js.get('message', js))[:80]}")
        sys.exit(1)
    d = pd.DataFrame(js["values"]).rename(columns={"datetime": "date"})
    d["date"] = pd.to_datetime(d["date"])
    d["close"] = d["close"].astype(float)
    print(f"window {w} ({a}..{b}): n={len(d)} {d['date'].min().date()}..{d['date'].max().date()}")
    frames.append(d)
    time.sleep(8)

df = (pd.concat(frames, ignore_index=True)
        .sort_values("date")
        .drop_duplicates(subset="date", keep="first"))   # head wins at seam (R2 precedent)

st, cls, m = lint_series(df)
print(f"EEM stitched: n={m['n']} {m['start']}..{m['end']} dups={m['dups']} "
      f"gap={m['maxgap']}d jumps={m['jumps']} -> {st} ({cls})")
if st in ("PASS", "PASS_WAIVER"):
    n = write_series(df, f"{OUT}/EEM.csv")
    print(f"WROTE {OUT}/EEM.csv ({n} rows)")
else:
    print("KEPT-FAIL-ROW: on-disk EEM.csv (R2, 2008-01-02, 4697 rows) left intact; loud.")
