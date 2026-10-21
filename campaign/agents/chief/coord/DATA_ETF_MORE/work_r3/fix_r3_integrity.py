#!/usr/bin/env python3
"""Fix the two on-disk integrity defects the red TDD tests pin (work_r3):

  1. EWA silent truncation: on-disk file starts 2012-10-12 (3493 rows) while
     R2 measured attainable depth 2008-01-02 (+1206 rows, seam_rel=0.00000,
     results_extend_all.json) but could not apply it under the then-unwaived
     start gate. Apply the R2 two-window stitch (head wins at seam) and let
     the SAME fail-closed lint_series decide. Any FAIL stays loud.

  2. Charter write-spec violation: BIL EWT GDXJ INDA XLC XLRE are 6-column
     OHLCV; charter R1 spec is [date,close]. Normalize, asserting close
     values preserved exactly (no numeric rewrite) and row count unchanged.

Idempotent: re-running re-verifies rather than re-fetching when already fixed.
"""
import json
import os
import sys
import time
import urllib.request

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from retest_r3 import classify, key, lint_series, write_series

OUT = "/Users/daxu/software/world-trader/tools/quant/data/more_etf"
OHLCV = ["BIL", "EWT", "GDXJ", "INDA", "XLC", "XLRE"]


def normalize_ohlcv():
    """[date,*] -> [date,close], values preserved exactly."""
    for sym in OHLCV:
        p = f"{OUT}/{sym}.csv"
        df = pd.read_csv(p)
        if list(df.columns) == ["date", "close"]:
            print(f"{sym:<6} already [date,close]; skip")
            continue
        assert "close" in df.columns and "date" in df.columns, sym
        n0, c0 = len(df), df["close"].astype(float).copy()
        out = df[["date", "close"]].copy()
        out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
        out.to_csv(p, index=False)
        back = pd.read_csv(p)
        assert len(back) == n0, sym
        assert (back["close"].astype(float).values == c0.values).all(), sym
        assert list(back.columns) == ["date", "close"], sym
        print(f"{sym:<6} normalized 6-col OHLCV -> [date,close] "
              f"({n0} rows, close bit-identical)")


def fetch(sym, k, a, b):
    url = (f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day"
           f"&start_date={a}&end_date={b}&outputsize=5000&apikey={k}&format=JSON")
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def fix_ewa():
    p = f"{OUT}/EWA.csv"
    cur = pd.read_csv(p)
    cur_first = pd.to_datetime(cur["date"]).min()
    if cur_first <= pd.Timestamp("2008-01-02"):
        print(f"EWA    already at attainable start {cur_first.date()}; skip fetch")
        return
    k = key()
    frames = []
    for w, (a, b) in enumerate([("2007-01-01", "2016-12-31"),
                                ("2017-01-01", "2026-09-30")]):
        js = fetch("EWA", k, a, b)
        if js.get("status") == "error" or "values" not in js:
            print(f"EWA    window {w} API_ERR {str(js.get('message', js))[:80]}"
                  " -> KEPT-FAIL-ROW, loud")
            return
        d = pd.DataFrame(js["values"]).rename(columns={"datetime": "date"})
        d["date"] = pd.to_datetime(d["date"])
        d["close"] = d["close"].astype(float)
        print(f"EWA    window {w} ({a}..{b}): n={len(d)} "
              f"{d['date'].min().date()}..{d['date'].max().date()}")
        frames.append(d)
        time.sleep(8)

    raw = pd.concat(frames, ignore_index=True)

    # dup-spread gate: the vendor double-reports bars (EEM/EWA measured max
    # dup-close spread 0.072%/0.024% — the same bar twice, not conflicting
    # data), so dedup is safe ONLY while every dup date's close spread stays
    # tiny; a large spread would make keep-first pick arbitrarily -> NO_WRITE.
    dupmask = raw["date"].duplicated(keep=False)
    if dupmask.any():
        g = raw[dupmask].groupby("date")["close"]
        spread = (g.max() - g.min()) / g.mean() * 100
        print(f"EWA    dup-rows={int(dupmask.sum())} over {len(spread)} dates, "
              f"spread%%: median={spread.median():.4f} max={spread.max():.4f}")
        if (spread > 0.5).any():
            print(f"EWA    {(spread > 0.5).sum()} dup dates with >0.5% close "
                  "disagreement -> NO_WRITE, loud")
            return

    df = (raw.sort_values("date")
             .drop_duplicates(subset="date", keep="first"))  # head wins (R2)

    st, cls, m = lint_series(df)
    print(f"EWA    stitched: n={m['n']} {m['start']}..{m['end']} dups={m['dups']} "
          f"gap={m['maxgap']}d jumps={m['jumps']} -> {st} ({cls})")
    if st in ("PASS", "PASS_WAIVER"):
        n = write_series(df, p)
        print(f"EWA    WROTE {p} ({n} rows; was 3493 rows from 2012-10-12)")
    else:
        print("EWA    KEPT-FAIL-ROW: on-disk file left intact; loud.")


if __name__ == "__main__":
    normalize_ohlcv()
    fix_ewa()
