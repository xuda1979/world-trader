"""Rigorous validation of the HONEST multi-horizon L/S result (no retrain).

Uses the cached walk-forward OOS predictions to test whether the H=21
long/short edge is real or artifact:
  1. Permutation null  - shuffle predicted ranks per rebalance date, re-run
     the honest hold-H book -> SR distribution under pure chance.
  2. Sub-period split   - 2014-2020 vs 2020-2026 (both halves positive?).
  3. Simple momentum baseline - does rank-by-raw past 20d return (a plain
     momentum strategy, no ML) beat XGB? Ensures ML adds value.
  4. Cost / K sensitivity - K in {5,10,20}, cost 0/3/6bps.
"""
from __future__ import annotations
import sys, os, json, pickle
import numpy as np
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xgb_horizon_portfolio import build_position_book, vol_target, stats, OUT, PRED_CACHE

COST = 0.0006
K = 10


def load():
    with open(PRED_CACHE, "rb") as fh:
        c = pickle.load(fh)
    frame = c["frame"]; preds = c["preds"]
    frame["date"] = pd.to_datetime(frame["date"])
    return frame, preds


def perm_null(frame, preds, H, n_perm=200, K=10):
    """Shuffle the predicted ranking within each rebalance date; return SRs."""
    fw = frame.copy()
    fw["pred"] = preds[H]
    fw = fw[np.isfinite(fw["pred"])]
    srs = []
    for _ in range(n_perm):
        # permute pred within each date
        g = fw.copy(); g["pred"] = g.groupby("date")["pred"].transform(lambda s: np.random.permutation(s.to_numpy()))
        res = build_position_book(g, g["pred"].to_numpy(), H)
        res = res.sort_index()
        srs.append(stats(res)["sr"])
    return srs


def main():
    frame, preds = load()
    result = {}

    # ---- 1. permutation null for H=21 ----
    print("Permutation null (n=200) for H=21...", flush=True)
    srs = perm_null(frame, preds, 21, n_perm=200, K=K)
    srs = np.array([s for s in srs if s is not None])
    # actual
    res = build_position_book(frame, preds[21], 21).sort_index()
    actual = stats(res)["sr"]
    pct = (np.mean(srs >= actual) * 100)
    print(f"  H=21 actual SR={actual:.3f} | null mean={np.nanmean(srs):.3f} "
          f"std={np.nanstd(srs):.3f} | pct null>=actual={pct:.1f}% "
          f"(want <5% for significant)")
    result["perm_null_H21"] = {"actual_sr": actual, "null_mean": float(np.nanmean(srs)),
                               "null_std": float(np.nanstd(srs)),
                               "pct_null_ge_actual": float(pct),
                               "n_perm": len(srs)}

    # ---- 2. sub-period split H=21 ----
    print("\nSub-period split H=21:")
    res_vt = vol_target(res.copy())
    for a, b, lab in [("2014", "2020", "2014-2019"), ("2020", "2026", "2020-2026")]:
        seg = res_vt.loc[(res_vt.index >= a) & (res_vt.index < b)]
        st = stats(seg)
        print(f"  {lab}: SR {st['sr']} ann {st['ann']:.1%} dd {st['dd']:.1%}")
        result[f"sub_{lab}"] = st

    # ---- 3. momentum baseline (rank by 20d momentum) ----
    print("\nSimple momentum baseline (rank by past 20d return), H=21:")
    close_long = frame.pivot(index="date", columns="ticker", values="close")
    mom20 = close_long.pct_change(20).stack().rename("mom20")
    mom20.index.names = ["date", "ticker"]
    fw = frame.copy().set_index(["date", "ticker"])
    fw["mom20"] = mom20.reindex(fw.index).to_numpy()
    fw = fw.reset_index()
    res_m = build_position_book(fw, fw["mom20"].to_numpy(), 21).sort_index()
    st = stats(res_m)
    st_vt = stats(vol_target(res_m.copy()))
    print(f"  XGB H21 SR={stats(res)['sr']:.3f} | momentum-baseline raw SR={st['sr']:.3f} "
          f"ann={st['ann']:.1%} | vt SR={st_vt['sr']:.3f}")
    result["mom_baseline_H21"] = {"xgb_sr": stats(res)["sr"], "mom_sr": st["sr"],
                                  "mom_ann": st["ann"], "mom_vt_sr": st_vt["sr"]}

    # ---- 4. cost / K sensitivity H=21 ----
    print("\nCost/K sensitivity H=21 (vol-targeted):")
    sens = {}
    for k_ in [5, 10, 20]:
        for c_ in [0.0, 0.0003, 0.0006]:
            res_ = build_position_book(frame, preds[21], 21, K=k_, cost=c_).sort_index()
            st_ = stats(vol_target(res_.copy()))
            sens[f"K{k_}_c{int(c_*1e4)}bp"] = st_["sr"]
            sens[f"K{k_}_c{int(c_*1e4)}bp_ann"] = st_["ann"]
            sens[f"K{k_}_c{int(c_*1e4)}bp_dd"] = st_["dd"]
            print(f"  K={k_:2d} cost={c_:.4f} -> vt SR {st_['sr']} ann {st_['ann']:.1%} dd {st_['dd']:.1%}")
    result["sens_K_cost_H21"] = sens

    with open(os.path.join(OUT, "multi_horizon_validate.json"), "w") as fh:
        json.dump(result, fh, indent=2, default=str)
    print("\nsaved", os.path.join(OUT, "multi_horizon_validate.json"))


if __name__ == "__main__":
    main()
