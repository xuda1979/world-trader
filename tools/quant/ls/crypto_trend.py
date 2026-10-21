"""Crypto trend strategy (portfolio-of-strategies leg D), 2026-08-05.

Honest design:
- Universe: BTC, ETH (tools/quant/data/binance, 1000 daily bars).
- Signal: 12m-1m momentum + 200d MA filter; long asset when trend up,
  equal-weight across those up-trending; vol-targeted 40% annualized.
- Daily signal, T+1 execution, 10bps round-trip cost (taker + margin).
- Scramble control (per-asset lag shuffle) -> edge must die.

Output: daily returns CSV (real + scrambled).
Run: python tools/quant/ls/crypto_trend.py [--scramble SEED]
"""
from __future__ import annotations
import os, sys, argparse

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA = os.path.join(ROOT, "tools/quant/data/binance")
COST_RT_BPS = 10.0
VOL_TARGET = 0.40


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
            lag = int(rng.integers(20, len(vals) // 3))
            p[c] = np.roll(vals, lag)
        p = p.iloc[lag:]
        prices = p.dropna()

    rets = prices.pct_change()
    mom = prices.shift(21) / prices.shift(252) - 1.0   # 12m-1m
    ma200 = prices.rolling(200).mean()
    up = (prices > ma200).fillna(False) & (mom > 0).fillna(False)

    pos = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    n_up = up.sum(axis=1)
    w = (1.0 / n_up.clip(lower=1)).to_numpy()[:, None]
    pos = pd.DataFrame(np.where(up.to_numpy(), w, 0.0),
                       index=prices.index, columns=prices.columns)

    pos = pos.shift(1)  # T+1
    daily = (pos * rets).sum(axis=1)
    to = pos.diff().abs().sum(axis=1)
    daily = daily - to * (COST_RT_BPS / 1e4)

    # vol target: scale to 40% ann vol using trailing 60d realized vol
    vol = daily.rolling(60).std() * np.sqrt(252)
    scale = (VOL_TARGET / vol).clip(upper=2.0).fillna(0.0)
    daily = daily * scale

    out = pd.DataFrame({"daily_return": daily}, index=prices.index)
    return out[out.index >= prices.index[252 + 60]]


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
    prices = load_panel()
    print(f"crypto panel: {prices.shape[0]} days x {prices.shape[1]} "
          f"({prices.index[0].date()}..{prices.index[-1].date()})")
    r = run(prices, args.scramble)
    m = metrics(r["daily_return"])
    print(f"crypto trend (scramble={args.scramble}): {m}")
    out_dir = os.path.join(ROOT, "tools/quant/ls/results/crypto_trend")
    os.makedirs(out_dir, exist_ok=True)
    tag = f"scramble{args.scramble}" if args.scramble is not None else "real"
    r.to_csv(os.path.join(out_dir, f"daily_{tag}.csv"))
    print(f"saved -> {out_dir}/daily_{tag}.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
