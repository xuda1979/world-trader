"""China A-share cross-sectional momentum (portfolio leg I), 2026-08-05.

27 liquid A-shares + index ETFs (sina, 400 daily bars).  Signal: 6m-1m
momentum z-scored cross-sectionally, long top-3 / short bottom-3, monthly
rebalance, T+1.  Costs: 10bps one-side (commission + stamp duty + slippage),
20bps RT.  Scramble control built in.
"""
from __future__ import annotations
import os, sys, argparse

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA = os.path.join(ROOT, "tools/quant/data/cn")
COST_ONE_SIDE_BPS = 10.0
MOM_FAST = 21
MOM_SLOW = 126
REBAL = 21
N_LONG = 3
N_SHORT = 3


def load_panel() -> pd.DataFrame:
    frames = {}
    for fn in sorted(os.listdir(DATA)):
        if not fn.endswith(".csv"):
            continue
        df = pd.read_csv(os.path.join(DATA, fn), parse_dates=["date"])
        frames[fn[:-4]] = df.set_index("date")["close"].sort_index()
    return pd.DataFrame(frames).dropna()


def run(prices: pd.DataFrame, seed: int | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    if seed is not None:
        p = prices.copy()
        for c in p.columns:
            vals = p[c].values.copy()
            lag = int(rng.integers(15, len(vals) // 3))
            p[c] = np.roll(vals, lag)
        p = p.iloc[lag:]
        prices = p.dropna()

    mom = prices.shift(MOM_FAST) / prices.shift(MOM_SLOW) - 1.0
    z = mom.sub(mom.mean(axis=1), axis=0).div(mom.std(axis=1), axis=0)
    rets = prices.pct_change()
    dates = prices.index
    pos = pd.DataFrame(0.0, index=dates, columns=prices.columns)
    for t in range(REBAL + MOM_SLOW, len(dates)):
        if (t - REBAL - MOM_SLOW) % REBAL != 0:
            continue
        zt = z.iloc[t].dropna()
        if len(zt) < 8:
            continue
        w = pd.Series(0.0, index=prices.columns)
        w[zt.nlargest(N_LONG).index] = 0.5 / N_LONG
        w[zt.nsmallest(N_SHORT).index] = -0.5 / N_SHORT
        pos.iloc[t] = w
    pos = pos.shift(1)
    daily = (pos * rets).sum(axis=1)
    to = pos.diff().abs().sum(axis=1)
    daily = daily - to * (COST_ONE_SIDE_BPS / 1e4)
    return pd.DataFrame({"daily_return": daily}, index=dates)


def metrics(r: pd.Series) -> dict:
    r = r.dropna()
    if len(r) < 30 or r.std() == 0:
        return {"sharpe": 0.0, "ann_ret": 0.0, "vol": 0.0, "maxdd": 0.0, "n": len(r)}
    eq = (1 + r).cumprod()
    return {"sharpe": round(float(r.mean() / r.std() * np.sqrt(252)), 2),
            "ann_ret": round(float(eq.iloc[-1] ** (252 / len(r)) - 1), 3),
            "vol": round(float(r.std() * np.sqrt(252)), 3),
            "maxdd": round(float((eq / eq.cummax() - 1).min()), 3),
            "n": len(r)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scramble", type=int, default=None)
    args = ap.parse_args()
    prices = load_panel()
    print(f"CN panel: {prices.shape[0]} days x {prices.shape[1]} "
          f"({prices.index[0].date()}..{prices.index[-1].date()})")
    r = run(prices, args.scramble)
    m = metrics(r["daily_return"])
    print(f"CN momentum (scramble={args.scramble}): {m}")
    out_dir = os.path.join(ROOT, "tools/quant/ls/results/cn_momentum")
    os.makedirs(out_dir, exist_ok=True)
    tag = f"scramble{args.scramble}" if args.scramble is not None else "real"
    r.to_csv(os.path.join(out_dir, f"daily_{tag}.csv"))
    print(f"saved -> {out_dir}/daily_{tag}.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
