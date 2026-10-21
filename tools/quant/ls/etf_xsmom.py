"""ETF cross-sectional momentum strategy, 2026-08-05.

Honest design:
- Universe: 6 ETFs with 8y history (SPY, QQQ, IWM, DIA, GLD, XLF).
- Signal at t: 12m-1m momentum, cross-sectional z-score.
- Long top-2, short bottom-2; equal-weight within each leg.
- Monthly rebalance (21d), T+1 execution, 3.8bps one-side cost.
- Scramble control: per-ETF price series lag-shuffled -> edge must die.
  (Cross-sectional: scrambling destroys ranking, unlike time-series.)

Also builds:
- Mean-reversion variant: long bottom-2, short top-2 (anti-momentum).
- Return-based momentum: use cumulative return instead of price ratio.

Output: daily returns CSV + metrics + scrambled control.
"""
from __future__ import annotations
import os, sys, argparse
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA = os.path.join(ROOT, "tools/quant/data/twelvedata")
TICKERS = ["SPY", "QQQ", "IWM", "DIA", "GLD", "XLF"]
COST_BPS = 3.8
MOM_FAST = 21
MOM_SLOW = 252
REBAL = 21
N_LONG = 2
N_SHORT = 2


def load_panel():
    frames = {}
    for tkr in TICKERS:
        df = pd.read_csv(os.path.join(DATA, f"{tkr}.csv"), parse_dates=["date"])
        frames[tkr] = df.set_index("date")["close"].sort_index()
    return pd.DataFrame(frames).dropna()


def run(prices, scramble_seed=None, reverse=False):
    """reverse=True -> mean-reversion (long losers, short winners)."""
    rng = np.random.default_rng(scramble_seed)
    if scramble_seed is not None:
        p = prices.copy()
        for c in p.columns:
            vals = p[c].values.copy()
            lag = int(rng.integers(20, len(vals) // 3))
            p[c] = np.roll(vals, lag)
        p.iloc[:lag] = np.nan
        prices = p.dropna()

    # Signal: 12m-1m momentum
    mom = prices.shift(MOM_FAST) / prices.shift(MOM_SLOW) - 1.0
    if reverse:
        mom = -mom  # mean-reversion: long losers, short winners

    # Cross-sectional z-score
    z = mom.sub(mom.mean(axis=1), axis=0).div(mom.std(axis=1).clip(lower=1e-8), axis=0)

    rets = prices.pct_change()
    dates = prices.index
    pos = pd.DataFrame(0.0, index=dates, columns=prices.columns)

    for t in range(MOM_SLOW + REBAL, len(dates)):
        if t % REBAL != 0:
            continue
        zt = z.iloc[t].dropna()
        if len(zt) < N_LONG + N_SHORT:
            continue
        w = pd.Series(0.0, index=prices.columns)
        longs = zt.nlargest(N_LONG).index
        shorts = zt.nsmallest(N_SHORT).index
        w[longs] = 0.5 / N_LONG
        w[shorts] = -0.5 / N_SHORT
        pos.iloc[t] = w

    pos = pos.shift(1)  # T+1
    daily = (pos * rets).sum(axis=1)
    to = pos.diff().abs().sum(axis=1)
    daily = daily - to * (COST_BPS / 1e4)

    start = MOM_SLOW + REBAL + 10
    out = pd.DataFrame({"daily_return": daily}, index=dates)
    return out.iloc[start:]


def metrics(r):
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


def correlate(a_csv, b_csv):
    """Pearson correlation between two daily return series on common dates."""
    try:
        a = pd.read_csv(a_csv, index_col=0, parse_dates=True)["daily_return"]
        b = pd.read_csv(b_csv, index_col=0, parse_dates=True)["daily_return"]
        common = a.index.intersection(b.index)
        if len(common) < 30:
            return None
        return round(float(a.loc[common].corr(b.loc[common])), 3)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scramble", type=int, default=None)
    ap.add_argument("--reverse", action="store_true", help="mean-reversion variant")
    args = ap.parse_args()

    prices = load_panel()
    label = "rev" if args.reverse else "mom"
    print(f"ETF XS panel: {prices.shape[0]}d x {prices.shape[1]} "
          f"({prices.index[0].date()}..{prices.index[-1].date()})")

    r = run(prices, args.scramble, args.reverse)
    m = metrics(r["daily_return"])
    tag = "real" if args.scramble is None else f"scramble{args.scramble}"
    print(f"ETF XS {label} ({tag}): {m}")

    out_dir = os.path.join(ROOT, "tools/quant/ls/results/etf_xs")
    os.makedirs(out_dir, exist_ok=True)
    fn = f"daily_{label}_{tag}.csv"
    r.to_csv(os.path.join(out_dir, fn))
    print(f"saved -> {out_dir}/{fn}")

    # Correlate with L/S champion if real run
    if args.scramble is None:
        ls_path = os.path.join(ROOT, "tools/quant/ls/results/validation_test/tw320d4_deep_full/daily_returns.csv")
        corr = correlate(os.path.join(out_dir, fn), ls_path)
        if corr is not None:
            print(f"corr with L/S champion: {corr}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
