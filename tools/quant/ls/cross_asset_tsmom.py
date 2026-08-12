"""Cross-asset time-series momentum (Moskowitz-Ooi-Pedersen 2012 style).

Honest design, 2026-08-05:
- Universe: 6 ETFs with full 8y history (SPY, QQQ, IWM, DIA, GLD, XLF).
- Signal at t: excess return over past 12m excluding most recent month (12m-1m).
- Each asset is vol-scaled to 40% annualized using trailing 60d realized vol.
- Combined equal-risk-weight (1/N).
- Long assets with positive momentum, flat on negative-momentum assets.
- Daily signal, T+1 execution, 3.8bps one-side cost.
- Scramble control: per-asset lag shuffle -> edge must die.

Output: daily returns CSV + metrics + scrambled control metrics.
Run: python tools/quant/ls/cross_asset_tsmom.py [--scramble SEED]
"""
from __future__ import annotations
import os, sys, argparse

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA = os.path.join(ROOT, "tools/quant/data/twelvedata")

TICKERS = ["SPY", "QQQ", "IWM", "DIA", "GLD", "XLF"]

COST_BPS_ONE_SIDE = 3.8
VOL_TARGET = 0.40
VOL_WINDOW = 60
MOM_FAST = 21
MOM_SLOW = 252


def load_panel():
    frames = {}
    for tkr in TICKERS:
        fp = os.path.join(DATA, f"{tkr}.csv")
        df = pd.read_csv(fp, parse_dates=["date"])
        frames[tkr] = df.set_index("date")["close"].sort_index()
    return pd.DataFrame(frames).dropna()


def run(prices, scramble_seed=None):
    rng = np.random.default_rng(scramble_seed)
    if scramble_seed is not None:
        p = prices.copy()
        for c in p.columns:
            vals = p[c].values.copy()
            lag = int(rng.integers(21, len(vals) // 3))
            p[c] = np.roll(vals, lag)
        p.iloc[:lag] = np.nan
        prices = p.dropna()

    rets = prices.pct_change()
    mom = prices.shift(MOM_FAST) / prices.shift(MOM_SLOW) - 1.0
    direction = (mom > 0).astype(float)

    rv = rets.rolling(VOL_WINDOW).std() * np.sqrt(252)
    n_assets = len(prices.columns)
    raw_weight = 1.0 / n_assets

    with np.errstate(divide="ignore", invalid="ignore"):
        vol_scale = np.where(rv > 0, VOL_TARGET / rv, 0.0)
    vol_scale = np.clip(vol_scale, 0, 3.0)
    pos_raw = raw_weight * vol_scale * direction
    pos = pd.DataFrame(pos_raw, index=prices.index, columns=prices.columns)
    pos = pos.shift(1)  # T+1

    daily = (pos * rets).sum(axis=1)
    to = pos.diff().abs().sum(axis=1)
    daily = daily - to * (COST_BPS_ONE_SIDE / 1e4)

    # Portfolio-level vol target 15%
    port_vol_target = 0.15
    port_vol = daily.rolling(VOL_WINDOW).std() * np.sqrt(252)
    port_scale = np.clip(port_vol_target / port_vol.replace(0, np.nan), 0, 2.0).fillna(0)
    daily = daily * port_scale.shift(1).fillna(0)

    start = max(MOM_SLOW, VOL_WINDOW) + 10
    out = pd.DataFrame({"daily_return": daily}, index=prices.index)
    return out.iloc[start:]


def metrics(r):
    r = r.dropna()
    if len(r) < 60 or r.std() == 0:
        return {"sharpe": 0.0, "ann_ret": 0.0, "vol": 0.0, "maxdd": 0.0, "n": len(r)}
    eq = (1 + r).cumprod()
    return {
        "sharpe": round(float(r.mean() / r.std() * np.sqrt(252)), 2),
        "ann_ret": round(float(eq.iloc[-1] ** (252 / len(r)) - 1), 3),
        "vol": round(float(r.std() * np.sqrt(252)), 3),
        "maxdd": round(float((eq / eq.cummax() - 1).min()), 3),
        "n": len(r),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scramble", type=int, default=None)
    args = ap.parse_args()
    prices = load_panel()
    print(f"cross-asset tsmom panel: {prices.shape[0]}d x {prices.shape[1]} "
          f"({prices.index[0].date()}..{prices.index[-1].date()})")
    r = run(prices, args.scramble)
    m = metrics(r["daily_return"])
    tag = "real" if args.scramble is None else f"scramble{args.scramble}"
    print(f"cross-asset tsmom ({tag}): {m}")
    out_dir = os.path.join(ROOT, "tools/quant/ls/results/cross_asset_tsmom")
    os.makedirs(out_dir, exist_ok=True)
    r.to_csv(os.path.join(out_dir, f"daily_{tag}.csv"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
