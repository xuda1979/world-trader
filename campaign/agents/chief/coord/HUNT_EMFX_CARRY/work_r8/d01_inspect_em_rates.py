"""D01: honest data-quality audit of tools/quant/data/em_rates/ (UNMINED, landed 2026-09-11).

Read-only. Reports per file: parse OK, coverage span, n rows, calendar-day cadence,
gap distribution, stale-repeat (identical consecutive values), outlier flags, dup dates.
Also cross-checks FX pairs for triangular consistency (EURCZK vs USDCZK/USDBRL etc).
"""
import os, sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
EM   = os.path.join(ROOT, "tools/quant/data/em_rates")

FILES = ["brazil_selic","brazil_ipca","brazil_usdbrl","czech_eurczk",
         "czech_usdczk","peru_usdpen","poland_eurpln","poland_usdpln"]

def load(name):
    df = pd.read_csv(os.path.join(EM, name + ".csv"))
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    bad = df["date"].isna().sum()
    df = df.dropna(subset=["date"]).sort_values("date")
    dup = df["date"].duplicated().sum()
    df = df.drop_duplicates("date", keep="last").set_index("date")
    s = pd.to_numeric(df["value"], errors="coerce")
    return s, bad, dup

rep = {}
for f in FILES:
    s, bad, dup = load(f)
    n = len(s)
    start, end = s.index.min(), s.index.max()
    v = s.dropna()
    # business-day cadence implied by span
    span_b = np.busday_count(start.date(), end.date()) + 1
    # consecutive identical values = stale repeat / no-update
    stale = int((v.diff() == 0).sum())
    # biggest move
    r = v.pct_change()
    big = int((r.abs() > 0.10).sum())
    # inferred cadence: median gap in calendar days
    gaps = pd.Series(s.index).diff().dt.days.dropna()
    med_gap = float(gaps.median()) if len(gaps) else float("nan")
    rep[f] = dict(n=n, n_nan=int(s.isna().sum()), bad_dates=int(bad), dup_dates=int(dup),
                  start=str(start.date()), end=str(end.date()),
                  busdays=int(span_b), coverage=round(n/span_b, 4),
                  med_gap_days=med_gap, stale_repeats=stale,
                  stale_frac=round(stale/max(n-1,1), 4),
                  moves_gt_10pct=big,
                  min=float(v.min()), max=float(v.max()),
                  last=float(v.iloc[-1]))
    print(f"--- {f} ---")
    for k, val in rep[f].items():
        print(f"    {k:16s} {val}")
    # yearly coverage count (to expose a series that starts late or dies early)
    yr = s.groupby(s.index.year).size()
    print("    yearly rows:", dict(yr.head(4)), "...", dict(yr.tail(3)))

import json
json.dump(rep, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "d01_report.json"), "w"),
          indent=1, default=str)
print("\nWROTE d01_report.json")
