#!/usr/bin/env python3
"""ITER62 wave-2 (2026-10-22): append-only re-emit of cnpair_M0_RM0_L60Z1.5.csv.

Canonical rebuild path = HUNT_CN_FUTURES/scratch/verify_cn_save.py logic:
  log(M0) - log(RM0) spread (2009+), zrev_margin(L=60, gate=1.5), vol_target,
  save_sleeve. Leaves were extended today to 2026-10-22 (cn_extend_report.json,
  overlap byte-verified). This script rebuilds the sleeve and EXTENDS the
  existing CSV append-only after byte-verifying the overlapping prefix
  (tol 1e-12 on returns; exact dates).

Pre-state snapshot: refresh_2026_10_22/cnpair_sleeve_snapshot_pre.csv.
"""
import json, sys
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CN_FUTURES"
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch")
import engine as E

SLEEVE = f"{ROOT}/sleeves/cnpair_M0_RM0_L60Z1.5.csv"
SNAP = "/Users/daxu/software/world-trader/campaign/work_backtest_oos/refresh_2026_10_22/cnpair_sleeve_snapshot_pre.csv"
REPORT = "/Users/daxu/software/world-trader/campaign/work_backtest_oos/refresh_2026_10_22/cnpair_reemit_report.json"
DRY = "--dry" in sys.argv


def main():
    old = pd.read_csv(SNAP, index_col=0, parse_dates=True)["ret"].astype(float)
    A = pd.read_csv(f"{ROOT}/data/M0.csv", index_col=0, parse_dates=True)["close"].astype(float)
    B = pd.read_csv(f"{ROOT}/data/RM0.csv", index_col=0, parse_dates=True)["close"].astype(float)
    sp = (np.log(A) - np.log(B)).dropna()
    sp = sp[sp.index >= "2009"]
    net, gr, pos, tup = E.zrev_margin(sp, lookback=60, gate=1.5)
    nv, _ = E.vol_target(net)
    new = nv.dropna()
    new = new[~new.index.duplicated()].sort_index()

    # overlap byte-verify
    both = old.index.intersection(new.index)
    dev = (old.loc[both] - new.loc[both]).abs().max() if len(both) else np.nan
    overlap_ok = bool(len(both) and dev <= 1e-12)
    new_dates = new.index.difference(old.index)
    entry = {
        "sleeve": "cnpair_M0_RM0_L60Z1.5.csv",
        "rebuild": "verify_cn_save.py logic (zrev_margin L60 Z1.5 + vol_target)",
        "overlap_n": int(len(both)),
        "overlap_maxdev": float(dev),
        "tol": 1e-12,
        "committed_last": str(old.index.max().date()),
        "new_rows": int(len(new_dates)),
        "new_first": str(new_dates.min().date()) if len(new_dates) else None,
        "new_last": str(new_dates.max().date()) if len(new_dates) else None,
        "overlap_ok": overlap_ok,
    }
    if not overlap_ok:
        entry["action"] = "NOT WRITTEN (overlap mismatch — fail-closed)"
        out = entry
    elif not len(new_dates):
        entry["action"] = "no new rows"
        out = entry
    else:
        merged = pd.concat([old, new.loc[new_dates]]).sort_index()
        entry["action"] = (f"extended -> {new_dates.max().date()} (n={len(merged)})"
                           if not DRY else f"would extend to {new_dates.max().date()} (dry)")
        if not DRY:
            merged.to_csv(SLEEVE, header=["ret"])
        out = entry
    # sanity stats on the extended series tail
    tail = new.loc[new.index >= "2026-09-16"]
    out["newrows_ret_stats"] = {
        "n": int(len(tail)), "mean": float(tail.mean()) if len(tail) else None,
        "std": float(tail.std()) if len(tail) else None,
    }
    json.dump(out, open(REPORT, "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))
    return 0 if out.get("overlap_ok") else 1


if __name__ == "__main__":
    sys.exit(main())
