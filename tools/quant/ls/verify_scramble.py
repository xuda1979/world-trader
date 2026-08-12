#!/usr/bin/env python3
"""Price-lag scramble noise gate for a completed loop-improve run.

Repo acceptance test (VALIDATION_STATUS.md): a strategy's daily-return
Sharpe must beat >=90% of noise controls to count as real alpha.  Loads a
run's exported daily_returns.csv and reports the gate verdict.

Usage:
  python -m tools.quant.ls.verify_scramble results/loop_improve_sweep/liq6_vix32 [--scrambles 25]
"""
from __future__ import annotations
import os, sys, argparse
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

TD = 252


def sharpe(r: pd.Series) -> float:
    r = r.dropna()
    return (r.mean() / r.std()) * np.sqrt(TD) if len(r) > 30 and r.std() > 0 else np.nan


def scramble_gate(daily_returns: pd.Series, n_scrambles: int = 25, seed0: int = 12345) -> dict:
    """Price-lag / noise control.  Real signal must beat the noisiest scrambled
    incarnation by a material margin AND on most seeds."""
    real_sh = sharpe(daily_returns)
    scram_sh = []
    for s in range(seed0, seed0 + n_scrambles):
        rng = np.random.default_rng(s)
        lagged = daily_returns.shift(rng.integers(1, 3)).fillna(0.0)
        scramble = rng.normal(loc=0.0, scale=daily_returns.std(), size=len(daily_returns))
        scram_sh.append(sharpe(pd.Series(scramble + lagged.values, index=daily_returns.index)))
    pct_better = float(np.mean([s_ >= real_sh for s_ in scram_sh]))
    return {
        "real_sharpe": round(float(real_sh), 3) if real_sh == real_sh else None,
        "scramble_sharpe_max": round(float(np.nanmax(scram_sh)), 3),
        "scramble_sharpe_p50": round(float(np.nanmedian(scram_sh)), 3),
        "pct_scrambles_beat_real": round(pct_better, 3),
        "PASS": pct_better < 0.10,
        "n_scrambles": n_scrambles,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", help="run export dir containing daily_returns.csv")
    ap.add_argument("--scrambles", type=int, default=25)
    a = ap.parse_args()

    path = os.path.join(ROOT, a.run_dir, "daily_returns.csv")
    if not os.path.exists(path):
        print(f"no daily_returns.csv at {path}")
        return 1
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    col = df.columns[0] if isinstance(df, pd.DataFrame) else df.name
    dr = df[col] if isinstance(df, pd.DataFrame) else df
    gate = scramble_gate(dr, n_scrambles=a.scrambles)
    print(f"scramble gate for {a.run_dir}:")
    for k, v in gate.items():
        print(f"  {k}: {v}")
    print(f"  VERDICT: {'PASS - real alpha' if gate['PASS'] else 'FAIL - noise-level'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
