#!/usr/bin/env python3
"""HUNT_CBOE_IV R8 - data inspection for tools/quant/data/cboe_hist/.

Charter: INSPECT FIRST - confirm what each file actually contains (underlying OHLCV vs
option statistic) and each series TRUE start date. Do not assume. Report coverage honestly.

Classification is by VALUE, not by filename.
Run: python3 campaign/agents/chief/coord/HUNT_CBOE_IV/work_r8/r8_data_inspect.py
Writes: r8_coverage.json + r8_coverage.csv
"""
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
CBOE = os.path.join(ROOT, "tools/quant/data/cboe_hist")
WORK = os.path.join(ROOT, "campaign/agents/chief/coord/HUNT_CBOE_IV/work_r8")

PRE2007 = pd.Timestamp("2007-01-01")
BOUND13 = pd.Timestamp("2013-01-01")


def span_class(first):
    if first < PRE2007:
        return "pre2007"
    if first < BOUND13:
        return "2007plus"
    return "inception_fail"


def inspect_one(path):
    name = os.path.basename(path)[:-4]
    raw = pd.read_csv(path)
    cols = [str(c).strip().lower() for c in raw.columns]
    raw.columns = cols
    out = {"file": name, "header": list(cols), "n_rows": int(len(raw))}
    if "date" not in cols:
        out["error"] = "no date column"
        return out
    d = pd.to_datetime(raw["date"], errors="coerce")
    out["bad_dates"] = int(d.isna().sum())
    raw = raw.loc[d.notna()].copy()
    raw["date"] = d[d.notna()]
    raw = raw.sort_values("date")
    idx = pd.DatetimeIndex(raw["date"])
    out["first"] = str(idx.min().date())
    out["last"] = str(idx.max().date())
    out["n_unique_dates"] = int(idx.nunique())
    out["n_dup_dates"] = int(len(idx) - idx.nunique())
    out["span_class"] = span_class(idx.min())
    gaps = idx.to_series().diff().dt.days.dropna()
    out["max_gap_days"] = int(gaps.max()) if len(gaps) else 0
    out["n_gaps_gt10"] = int((gaps > 10).sum())
    c = "close" if "close" in cols else cols[-1]
    cl = pd.to_numeric(raw[c], errors="coerce")
    out["close_col"] = c
    out["close_first"] = float(cl.iloc[0])
    out["close_last"] = float(cl.iloc[-1])
    out["close_min"] = float(np.nanmin(cl.to_numpy(dtype=float)))
    out["close_max"] = float(np.nanmax(cl.to_numpy(dtype=float)))
    out["close_nan"] = int(cl.isna().sum())
    out["close_nonpos"] = int((cl <= 0).sum())
    has_vol = "volume" in cols
    out["has_volume"] = bool(has_vol)
    if has_vol:
        v = pd.to_numeric(raw["volume"], errors="coerce")
        out["vol_all_zero"] = bool((v.fillna(0) == 0).all())
        out["vol_mean"] = float(v.mean())
    else:
        out["vol_all_zero"] = None
        out["vol_mean"] = None
    volish = bool(out["close_min"] > 5.0 and out["close_max"] < 200.0
                  and (not has_vol or out["vol_all_zero"]))
    out["looks_like_vol_stat"] = volish
    out["looks_like_price"] = bool((has_vol and not out["vol_all_zero"])
                                   or out["close_max"] > 200.0)
    return out


def main():
    files = sorted(f for f in os.listdir(CBOE) if f.endswith(".csv"))
    rows = [inspect_one(os.path.join(CBOE, f)) for f in files]
    pd.DataFrame(rows).to_csv(os.path.join(WORK, "r8_coverage.csv"), index=False)
    with open(os.path.join(WORK, "r8_coverage.json"), "w") as fh:
        json.dump(rows, fh, indent=1)
    print("file      first       last          n  span            kind   min      max    vol0 gap")
    for r in rows:
        if "first" not in r:
            print(" ".join([r["file"].ljust(9), "(no date column)", str(r.get("error"))]))
            continue
        kind = "VOL" if r.get("looks_like_vol_stat") else ("PX" if r.get("looks_like_price") else "?")
        print(" ".join([r["file"].ljust(9), r["first"], r["last"], str(r["n_rows"]).rjust(5),
                        r["span_class"].ljust(15), kind.ljust(5),
                        ("%.2f" % r["close_min"]).rjust(9), ("%.2f" % r["close_max"]).rjust(9),
                        str(r["vol_all_zero"]).rjust(5), str(r["max_gap_days"]).rjust(4)]))
    print()
    print("inception_fail (NOT hunt-eligible, V2 9a):",
          [r["file"] for r in rows if r.get("span_class") == "inception_fail"])
    print("wrote r8_coverage.json/.csv")


if __name__ == "__main__":
    main()
