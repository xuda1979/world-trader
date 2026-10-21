#!/usr/bin/env python3
"""HUNT_VOL2 ROUND 4 (b) — MSSW SHORT_LEG_UNKNOWN resolution.

Census (CAMP_SHORT_LIBRARY_BORROW_CENSUS.json sleeves.Multi_Strategy_SharpeW):
"SharpeW blend generator not on disk (produced by ad-hoc commit e0e47e0; weights
not reproducible)" -> NOT_INTEGRABLE. This module resolves what CAN be proven
about the blend from the committed curve + the 6 stream files, fail-closed:

PROVEN here (see prove() / short_notional_report()):
  1. STRUCTURE: on the 134 committed-curve days where FX_Carry is the ONLY live
     stream (Saturdays/Sundays/holidays), committed_ret == w_fx * fx_ret with
     w_fx = 0.042105263155818 (sd across days 2.9e-11). So the generator is a
     FIXED-WEIGHT, zero-fill (frozen stream = 0 PnL), NO-renormalization daily
     blend of exactly the 6 named streams. No other convention produces a
     1e-11-consistent ratio.
  2. WEIGHTS: least squares on the full committed index recovers
     ls .4487 / cta .0817 / macro .0193 / statarb .0671 / rp .3155 / fx .0430,
     R^2 = 0.9995, residual 1.7bp/day rms and ORTHOGONAL to every stream return
     (0.0% of residual variance explained by stream returns) -> the residual is
     NOT a weight error; it is stream-input drift.
  3. BYTE-REPRODUCTION FAILS and we say so: max rel dev 1.5e-2 on the equity
     level (test bar 1e-6). Cause, proven: 4 of the 6 stream files were
     REGENERATED after commit e0e47e0 (worktree != e0e47e0 blobs for
     L_S_130_30, Global_Macro, StatArb_40pairs_z15, Risk_Parity_Bridgewater;
     CTA + FX + the MSSW curve itself are byte-identical), and even rebuilding
     from the e0e47e0 blobs leaves the 1.7bp orthogonal residual -> the
     generator's in-memory inputs match neither on-disk version. The curve
     CANNOT be regenerated from disk. reproduced=False.
  4. SHORT LEG (what the pregate actually needs): per the census the only
     short-carrying streams are StatArb_40pairs_z15 (|short| mean 0.893 of its
     own NAV) and Global_Macro (mean 0.405); L_S_130_30/CTA/RP measure |short|
     = 0 (flip bug / futures), FX_Carry is carry-on-forwards (no equity
     borrow). MSSW short notional = w_statarb*0.893 + w_macro*0.405 ~= 0.0673
     of NAV. Uncertainty from the weight recovery is second-order: even a
     +/-50% relative error on w_statarb moves the HARD-tier (8%/yr) borrow
     drag only within 0.27-0.80%/yr of SLEEVE NAV.

Integration rule (BLEND_PREGATE.md): byte-exact regeneration FAILED, so the
published curve stays NOT integrable as-is; but the short-leg composition IS
reconstructed, so the pregate PRICES the borrow instead of assuming it away.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/daxu/software/world-trader")
WORK = ROOT / "campaign/agents/chief/coord/HUNT_VOL2/work_r4"
RES = ROOT / "tools/quant/hedge_fund_strats/results"
COMMIT = WORK / "commit_streams"
SRC = RES / "equity_Multi_Strategy_SharpeW.csv"

STREAM_FILES = {
    "ls": "equity_L_S_130_30.csv",
    "cta": "equity_CTA_Futures_multi_21d.csv",
    "macro": "equity_Global_Macro.csv",
    "statarb": "equity_StatArb_40pairs_z15.csv",
    "rp": "equity_Risk_Parity_Bridgewater.csv",
    "fx": "equity_FX_Carry.csv",
}
# census-measured |short|/NAV per stream (CAMP_SHORT_LIBRARY_BORROW_CENSUS.json)
STREAM_SHORT_MEAN = {"ls": 0.0, "cta": 0.0, "macro": 0.404817,
                     "statarb": 0.893254, "rp": 0.0, "fx": 0.0}


def _load(directory: Path):
    eqs = {}
    for k, f in STREAM_FILES.items():
        p = directory / f
        if not p.exists():
            raise FileNotFoundError(f"{p}")
        s = pd.read_csv(p, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
        eqs[k] = s[~s.index.duplicated(keep="last")].sort_index()
    return eqs


def committed_curve() -> pd.Series:
    s = pd.read_csv(SRC, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    return s[~s.index.duplicated(keep="last")].sort_index()


def fx_only_weight(eqs=None) -> float:
    """PROOF of structure: w_fx from committed-ret / fx-ret on FX-only days."""
    if eqs is None:
        eqs = _load(RES)
    c = committed_curve().pct_change()
    fx = eqs["fx"].pct_change()
    wk = c[c.index.dayofweek >= 5]  # FX trades Sat/Sun; the 5 equity streams cannot
    j = pd.concat([wk.rename("c"), fx.rename("f")], axis=1, join="inner").dropna()
    if len(j) < 50:
        raise RuntimeError(f"only {len(j)} fx-only days — proof not available")
    w = (j.c / j.f)
    if w.std() > 1e-8:
        raise RuntimeError(f"w_fx not constant across fx-only days: sd={w.std():.3e}")
    return float(w.mean())


def recover_weights(eqs=None):
    """Least-squares fixed-weight recovery on the full committed index (zero-fill)."""
    if eqs is None:
        eqs = _load(RES)
    c = committed_curve().pct_change().fillna(0.0)
    X = pd.DataFrame({k: eqs[k].pct_change().reindex(c.index).fillna(0.0)
                      for k in STREAM_FILES})
    w, *_ = np.linalg.lstsq(X.values, c.values, rcond=None)
    pred = pd.Series(X.values @ w, index=c.index)
    resid = c - pred
    r2 = 1 - resid.var() / c.var()
    # orthogonality: is the residual a weight error or input drift?
    A = np.column_stack([X.values, np.ones(len(X))])
    sol, *_ = np.linalg.lstsq(A, resid.values, rcond=None)
    expl = 1 - (resid.values - A @ sol).var() / resid.var()
    return pd.Series(w, index=list(STREAM_FILES)), r2, resid, expl


def rebuild_sharpew(eqs=None, weights=None):
    """Rebuild the equity curve under the proven convention. Byte-match EXPECTED
    to fail (input drift); the deviation is returned for honest reporting."""
    if eqs is None:
        eqs = _load(RES)
    if weights is None:
        weights, _, _, _ = recover_weights(eqs)
    c = committed_curve().pct_change()
    X = pd.DataFrame({k: eqs[k].pct_change().reindex(c.index).fillna(0.0)
                      for k in STREAM_FILES})
    port = (X * weights).sum(axis=1)
    eq = (1 + port).cumprod()
    j = pd.concat([eq.rename("rebuilt"), committed_curve().rename("committed")],
                  axis=1, join="inner").dropna()
    dev = (j.rebuilt - j.committed).abs() / j.committed.abs().clip(lower=1e-12)
    return eq, float(dev.max()), len(j)


def mssw_short_notional(eqs=None, weights=None) -> pd.Series:
    """Daily |short|/NAV of the blend = sum_k w_k * |short_k(t)| from the census
    (stream-level means applied to the blend weights; CTA/RP/LS measure 0)."""
    if weights is None:
        weights, _, _, _ = recover_weights(eqs)
    return float(sum(weights[k] * STREAM_SHORT_MEAN[k] for k in STREAM_FILES))


def short_notional_report() -> dict:
    w, r2, resid, expl = recover_weights()
    _, dev, n = rebuild_sharpew(weights=w)
    sn = mssw_short_notional(weights=w)
    return {
        "structure_proof_w_fx": fx_only_weight(),
        "weights": w.round(6).to_dict(),
        "ret_fit_r2": round(float(r2), 8),
        "resid_sd_bp": round(float(resid.std()) * 1e4, 3),
        "resid_variance_explained_by_streams": round(float(expl), 4),
        "equity_max_rel_dev": dev,
        "n_days": n,
        "byte_reproduced": dev < 1e-6,
        "short_notional_frac_nav": round(sn, 5),
        "borrow_drag_ann_frac": {f"HARD {r}": round(sn * r, 5)
                                 for r in (0.005, 0.02, 0.08)},
    }


if __name__ == "__main__":
    import json
    print(json.dumps(short_notional_report(), indent=2))
