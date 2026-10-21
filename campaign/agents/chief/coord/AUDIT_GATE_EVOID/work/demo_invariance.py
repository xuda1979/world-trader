#!/usr/bin/env python3
"""AUDIT_GATE_EVOID — numeric demo of the gate-e defect (repro artifact).

Demonstrates, without touching any hunt input:
1. SR is permutation-invariant: shuffling a return series reproduces |SR|
   to float noise (~1e-16). The buggy scramble_p (shuffle net returns,
   count real > |SR_shuffled|) therefore returns a pure float-noise
   coin-flip, not a p-value.
2. The same shuffle applied to a SIGNAL (positions), recomputed against
   real returns through the cost pipeline, produces a genuine null spread
   — the correct class of test per GATES_CONTRACT gate e text.

Seed-pinned (17, matching both hunts' scramble seeds). Pure synthetic
data; no hunt inputs are read.
"""
import numpy as np
import pandas as pd

ANN = 252


def sr(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(ANN)) if len(x) else 0.0


def buggy_scramble_p(x: pd.Series, seed: int = 17, n: int = 200) -> float:
    """Verbatim class of the defective implementation (WX_DEMAND line 133,
    NG_REGIONAL line 95): shuffle the return array in place."""
    a = np.array(x.dropna().values, copy=True)
    rng = np.random.default_rng(seed)
    real = abs(sr(pd.Series(a)))
    wins = 0
    max_dev = 0.0
    for _ in range(n):
        rng.shuffle(a)
        s = abs(sr(pd.Series(a)))
        max_dev = max(max_dev, abs(s - real))
        if real > s:
            wins += 1
    return wins / n, max_dev


def correct_scramble_p(sig: pd.Series, ret: pd.Series,
                       cost_bps: float = 6.4, seed: int = 17,
                       n: int = 200) -> float:
    """Correct class (per contract text): permute the signal, recompute the
    full net pipeline (T+1, turnover costs), compare SRs."""
    w = sig.shift(1).fillna(0.0)            # T+1
    r = ret.reindex(w.index).fillna(0.0)

    def net_of(s: pd.Series) -> pd.Series:
        to = s.diff().abs().fillna(s.abs())
        return s * r - to * cost_bps / 1e4

    real = sr(net_of(w))
    rng = np.random.default_rng(seed)
    a = w.values.copy()
    ge = 0
    for _ in range(n):
        perm = rng.permutation(a)
        if sr(net_of(pd.Series(perm, index=w.index))) >= real:
            ge += 1
    return ge / n, real


def main() -> None:
    rng = np.random.default_rng(7)
    n_days = 1500
    # synthetic underlying returns with mild autocorrelation
    r = pd.Series(rng.normal(0.0003, 0.01, n_days),
                  index=pd.bdate_range("2019-01-01", periods=n_days))
    # synthetic signal: slow-varying +/-1 position, genuinely predictive
    state = pd.Series(np.where(
        pd.Series(rng.normal(size=n_days)).rolling(63).mean() > 0, 1.0, -1.0),
        index=r.index)

    p_bug, max_dev = buggy_scramble_p(r * state)   # hunt passed `net_vt`-like series
    p_ok, real_sr = correct_scramble_p(state, r)

    print("[1] BUGGY class (shuffle net returns, as in WX_DEMAND/NG_REGIONAL):")
    print(f"    reported 'p' = {p_bug:.3f}  (pure float-noise coin-flip)")
    print(f"    max |SR_scram - SR_real| over 200 shuffles = {max_dev:.3e}"
          "  (SR is permutation-invariant)")
    print("[2] CORRECT class (permute signal, recompute pipeline):")
    print(f"    real SR = {real_sr:.3f}, null-exceedance p = {p_ok:.3f}"
          "  (genuine spread)")

    assert max_dev < 1e-12, "expected float-noise-level invariance"
    print("ASSERT PASS: shuffled-return SR deviates only at float noise;"
          " buggy p carries no evidence.")


if __name__ == "__main__":
    main()
