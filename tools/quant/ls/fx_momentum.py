"""FX cross-sectional momentum strategy (portfolio-of-strategies leg E).

Honest design, 2026-08-05:
- Universe: 8 major crosses (tools/quant/data/fx/*.csv, 2000 bars each
  from Twelve Data, ends 2026-08-05).
- Signal at t: 12m-1m momentum (skip the recent month; trailing-only).
- Cross-sectional z-score -> long top-2, short bottom-2.
- Monthly rebalance (21d), T+1 execution, 2bps round-trip cost (0.2bp/side
  per leg + slippage margin, 2 legs).
- Calendar-time position state (no overlapping-trade artifact).
- Control: per-pair series scramble -> edge must die.

Output: daily returns CSV + metrics + scrambled control metrics.
Run: python tools/quant/ls/fx_momentum.py [--scramble SEED]
"""
from __future__ import annotations
import os, sys, argparse

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FX_DIR = os.path.join(ROOT, "tools/quant/data/fx")
COST_RT_BPS = 2.0
MOM_FAST = 21          # skip recent month
MOM_SLOW = 252         # 12m lookback
REBAL = 21             # monthly
N_LONG = 2
N_SHORT = 2


def load_panel() -> pd.DataFrame:
    frames = {}
    for fn in sorted(os.listdir(FX_DIR)):
        if not fn.endswith(".csv"):
            continue
        df = pd.read_csv(os.path.join(FX_DIR, fn), parse_dates=["date"])
        frames[fn[:-4]] = df.set_index("date")["close"].sort_index()
    return pd.DataFrame(frames).dropna()


def momentum(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.shift(MOM_FAST) / prices.shift(MOM_SLOW) - 1.0


def run(prices: pd.DataFrame, scramble_seed: int | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(scramble_seed)
    if scramble_seed is not None:
        p = prices.copy()
        for c in p.columns:
            vals = p[c].values.copy()
            lag = int(rng.integers(20, len(vals) // 3))
            p[c] = np.roll(vals, lag)
        p.iloc[:lag] = np.nan
        prices = p.dropna()

    mom = momentum(prices)
    z = mom.sub(mom.mean(axis=1), axis=0).div(mom.std(axis=1), axis=0)

    rets = prices.pct_change()
    dates = prices.index
    pos = pd.DataFrame(0.0, index=dates, columns=prices.columns)
    for t in range(REBAL, len(dates)):
        if (t - REBAL) % REBAL != 0:
            continue
        zt = z.iloc[t].dropna()
        if len(zt) < 6:
            continue
        longs = zt.nlargest(N_LONG).index
        shorts = zt.nsmallest(N_SHORT).index
        w = pd.Series(0.0, index=prices.columns)
        w[longs] = 0.5 / N_LONG
        w[shorts] = -0.5 / N_SHORT
        pos.iloc[t] = w

    pos = pos.shift(1)  # T+1 execution
    daily = (pos * rets).sum(axis=1)
    # costs on rebalance days: turnover = sum |w_t - w_{t-1}|
    to = pos.diff().abs().sum(axis=1)
    daily = daily - to * (COST_RT_BPS / 1e4)
    out = pd.DataFrame({"daily_return": daily}, index=dates)
    out = out[out.index >= dates[REBAL + MOM_SLOW]]
    return out


def metrics(r: pd.Series) -> dict:
    r = r.dropna()
    if len(r) < 30 or r.std() == 0:
        return {"sharpe": 0.0, "ann_ret": 0.0, "vol": 0.0, "maxdd": 0.0, "n": len(r)}
    eq = (1 + r).cumprod()
    return {
        "sharpe": round(float(r.mean() / r.std() * np.sqrt(252)), 2),
        "ann_ret": round(float(eq.iloc[-1] ** (252 / len(r)) - 1), 3),
        "vol": round(float(r.std() * np.sqrt(252)), 3),
        "maxdd": round(float((eq / eq.cummax() - 1).min()), 3),
        "n": len(r),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scramble", type=int, default=None)
    args = ap.parse_args()

    prices = load_panel()
    print(f"FX panel: {prices.shape[0]} days x {prices.shape[1]} pairs "
          f"({prices.index[0].date()}..{prices.index[-1].date()})")
    r = run(prices, args.scramble)
    m = metrics(r["daily_return"])
    print(f"FX momentum (scramble={args.scramble}): {m}")

    out_dir = os.path.join(ROOT, "tools/quant/ls/results/fx_momentum")
    os.makedirs(out_dir, exist_ok=True)
    tag = f"scramble{args.scramble}" if args.scramble is not None else "real"
    r.to_csv(os.path.join(out_dir, f"daily_{tag}.csv"))
    print(f"saved -> {out_dir}/daily_{tag}.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
