#!/usr/bin/env python3
"""Rebuild more_etf/manifest.csv under the round-3 coordinator WAIVER.

Adds the charter 3(a) span_class column: pre2007 | 2007plus | inception_fail,
from each on-disk series' actual first date. All R1/R2 non-start gates still
fire fail-closed (n>=250, dup, gap<=10d, jumps, freshness ~3.25y) — the waiver
lifts ONLY the start bound. FAIL rows stay loud in the manifest, never silent.
"""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, HERE)

from retest_r3 import (FRESH_DAYS, INCEPTION_BOUND, PRE2007_BOUND, REF_END,
                       classify, lint_series)

D = "/Users/daxu/software/world-trader/tools/quant/data/more_etf"


def build(src=D):
    """Lint every csv under src; returns the manifest DataFrame (and writes it)."""
    rows = []
    for fn in sorted(os.listdir(src)):
        if not fn.endswith(".csv") or fn == "manifest.csv":
            continue
        sym = fn[:-4]
        try:
            df = pd.read_csv(f"{src}/{fn}")
            df["date"] = pd.to_datetime(df["date"])
            st, cls, m = lint_series(df)
        except Exception as e:
            st, cls, m = f"FAIL(read) {repr(e)[:50]}", "", dict(
                n=len(df), start="", end="", maxgap="", zrun="", jumps="", dups="")
        rows.append(dict(
            symbol=sym,
            start=m.get("start", ""), end=m.get("end", ""), rows=m.get("n", ""),
            max_gap_days=m.get("maxgap", ""), zero_ret_rows=m.get("zrun", ""),
            jump_days=m.get("jumps", ""), dup_dates=m.get("dups", ""),
            span_class=cls,
            status=st,
        ))
    out = pd.DataFrame(rows)
    out.to_csv(f"{src}/manifest.csv", index=False)
    return out


if __name__ == "__main__":
    mf = build()
    fails = mf[~mf.status.str.startswith(("PASS", "STALE"))]
    waiver = mf[mf.status == "PASS_WAIVER"]
    pre = mf[mf.status == "PASS"]
    print(f"manifest rebuilt under waiver: {len(mf)} series")
    print(f"  PASS (pre2007):      {len(pre)}")
    print(f"  PASS_WAIVER (2007plus): {len(waiver)}")
    for _, r in waiver.iterrows():
        print(f"    {r.symbol:<6} {r.start}..{r.end} n={r.rows}")
    print(f"  FAIL (inception_fail/other): {len(fails)}")
    if len(fails):
        print(fails[["symbol", "start", "rows", "span_class", "status"]].to_string(index=False))
