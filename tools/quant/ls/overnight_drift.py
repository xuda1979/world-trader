"""US overnight-drift strategy (portfolio leg J), 2026-08-05.

The overnight anomaly (returns earned from close-to-next-open persist for
names with high overnight drift; correlated with the next day's close).
Signal: trailing 20d mean OVERNIGHT return (open/prev close - 1), z-scored
cross-sectionally; long top-12 / short bottom-12; DAILY rebalance, T+1;
3.8bps one-side.  Panel: 8y twelvedata (has open).  Scramble control.
"""
from __future__ import annotations
import os, sys, argparse

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA = os.path.join(ROOT, "tools/quant/data/twelvedata")
COST_ONE_SIDE_BPS = 3.8
LOOKBACK = 20
N_LONG = 12
N_SHORT = 12


def load_panel() -> pd.DataFrame:
    frames = {}
    for fn in sorted(os.listdir(DATA)):
        if not fn.endswith(".csv"):
            continue
        df = pd.read_csv(os.path.join(DATA, fn), parse_dates=["date"])
        df = df.set_index("date").sort_index()
        frames[fn[:-4]] = df
    cols = ["open", "close"]
    prices = pd.DataFrame({f"{s}_{c}": frames[s][c] for s in frames for c in cols})
    return prices


def run(panel: pd.DataFrame, seed: int | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(panel) // 2
    opens = panel[[c for c in panel.columns if c.endswith("_open")]]
    closes = panel[[c for c in panel.columns if c.endswith("_close")]]
    names = [c[:-5] for c in opens.columns]
    opens.columns = names
    closes.columns = names

    if seed is not None:
        p = closes.copy()
        for c in p.columns:
            vals = p[c].values.copy()
            lag = int(rng.integers(20, len(vals) // 3))
            p[c] = np.roll(vals, lag)
        p = p.iloc[lag:]
        closes = p.dropna()
        opens = opens.reindex(closes.index)

    overnight = opens / closes.shift(1) - 1.0
    sig = overnight.rolling(LOOKBACK).mean()
    z = sig.sub(sig.mean(axis=1), axis=0).div(sig.std(axis=1), axis=0)

    # hold from today's close to tomorrow's close (T+1 on daily signal)
    rets = closes.pct_change()
    dates = closes.index
    pos = pd.DataFrame(0.0, index=dates, columns=names)
    for t in range(LOOKBACK + 1, len(dates)):
        zt = z.iloc[t].dropna()
        if len(zt) < 20:
            continue
        w = pd.Series(0.0, index=names)
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
    if len(r) < 60 or r.std() == 0:
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
    panel = load_panel()
    print(f"panel: {panel.shape[0]} days x {panel.shape[1]//2} names")
    r = run(panel, args.scramble)
    m = metrics(r["daily_return"])
    print(f"overnight drift (scramble={args.scramble}): {m}")
    out_dir = os.path.join(ROOT, "tools/quant/ls/results/overnight_drift")
    os.makedirs(out_dir, exist_ok=True)
    tag = f"scramble{args.scramble}" if args.scramble is not None else "real"
    r.to_csv(os.path.join(out_dir, f"daily_{tag}.csv"))
    print(f"saved -> {out_dir}/daily_{tag}.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
