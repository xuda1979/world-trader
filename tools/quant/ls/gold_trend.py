"""Gold trend-following strategy, 2026-08-05.

Honest design:
- Universe: GLD only (gold ETF, 2000 daily bars from Twelve Data).
- Signal: 200d simple moving average crossover.
- Long GLD when price > MA200, flat/cash otherwise.
- Vol-targeted to 15% annualized (trailing 60d realized vol).
- T+1 execution, 3.8bps one-side cost (7.6bps round-trip).
- Scramble control: price series lag-shuffled -> edge must die.

Rationale: gold has near-zero long-run correlation with US equities,
making it an ideal diversifier for the L/S equity book.
"""
from __future__ import annotations
import os, sys, argparse
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
COST_BPS = 3.8
VOL_TARGET = 0.15
MA_WINDOW = 200
VOL_WINDOW = 60


def load():
    fp = os.path.join(ROOT, "tools/quant/data/twelvedata/GLD.csv")
    df = pd.read_csv(fp, parse_dates=["date"])
    return df.set_index("date")[["close"]].sort_index()


def run(prices, scramble_seed=None):
    rng = np.random.default_rng(scramble_seed)
    if scramble_seed is not None:
        p = prices.copy()
        vals = p["close"].values.copy()
        lag = int(rng.integers(30, len(vals) // 3))
        p["close"] = np.roll(vals, lag)
        p.iloc[:lag] = np.nan
        prices = p.dropna()

    rets = prices["close"].pct_change()
    ma = prices["close"].rolling(MA_WINDOW).mean()
    signal = (prices["close"].shift(1) > ma.shift(1)).astype(float)

    rv = rets.rolling(VOL_WINDOW).std() * np.sqrt(252)
    with np.errstate(divide="ignore", invalid="ignore"):
        scale = np.where(rv > 0, VOL_TARGET / rv, 0.0)
    scale = np.clip(scale, 0, 2.0)
    pos = (signal * scale).shift(1)
    pos = pos.fillna(0)

    daily = pos * rets
    to = pos.diff().abs()
    daily = daily - to * (COST_BPS / 1e4)

    start = MA_WINDOW + VOL_WINDOW + 10
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
    prices = load()
    print(f"GLD panel: {len(prices)}d ({prices.index[0].date()}..{prices.index[-1].date()})")
    r = run(prices, args.scramble)
    m = metrics(r["daily_return"])
    tag = "real" if args.scramble is None else f"scramble{args.scramble}"
    print(f"gold trend ({tag}): {m}")
    out_dir = os.path.join(ROOT, "tools/quant/ls/results/gold_trend")
    os.makedirs(out_dir, exist_ok=True)
    r.to_csv(os.path.join(out_dir, f"daily_{tag}.csv"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
