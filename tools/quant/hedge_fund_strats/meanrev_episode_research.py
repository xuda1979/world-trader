"""Mean-reversion MARKET-NEUTRAL sleeve — does it profit in the flagship's loss episodes?

User ask: mean-reversion market-neutral strategies for the episodes where the
flagship lost money (2018 Q4, 2020 COVID, 2022-24, 2011, etc.).

Approach (crash-seeking short-term reversal, strictly no lookahead, daily
returns during each k-day holding period; 6 bps/side cost on rebalance):
  - Universe: twelve_big 290-name equity panel (2006-2026).
  - Signal: past-k-day cross-sectional return. Each rebalance (every k days),
    LONG bottom-N worst, SHORT top-N best, equal weight, dollar-neutral.
  - T+1 execution; realized returns each day; cost on weight-delta at rebalance.
  - Evaluate: full Sharpe + per flagship-loss-episode PnL + outside-window PnL.

Usage: python tools/quant/hedge_fund_strats/meanrev_episode_research.py
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from tools.quant.hedge_fund_strats.core import DataLoader

RES = Path(__file__).resolve().parent / "results"
COST_BPS = 6.0  # one side

LOSS_EPISODES = [
    ("2018 Q4", "2018-10-10", "2019-08-07"),
    ("2020 COVID", "2020-02-24", "2020-04-17"),
    ("2011 Euro", "2011-07-27", "2012-01-13"),
    ("2022-24 bear", "2022-01-05", "2024-02-29"),
]

def load_prices_rets():
    eq = DataLoader.load_equities(source="twelve_big", min_rows=1000)
    prices = DataLoader.build_price_panel(eq)
    prices = prices[prices.index >= "2007-01-01"]
    rets = prices.pct_change(fill_method=None)
    return prices, rets

def backtest(prices, rets, k, n, rng=None, scramble=False):
    """Non-overlapping k-day reversal, market-neutral. T+1 + cost. Daily returns.
    If scramble=True, per-rebalance ranks are randomized (rng) destroying the
    'long-worst/short-best -> future return' mapping -- for the signal-scramble
    validation gate."""
    dates = rets.index
    if rng is None:
        rng = np.random.default_rng(0)
    T = len(dates)
    sig = rets.rolling(k).sum().shift(1)  # sum over prior k days, known at t-1
    liquid = rets.notna().rolling(k + 1, min_periods=1).sum() >= k + 1
    ret_daily = []
    dnum = []
    w = None
    for i in range(T):
        d = dates[i]
        if i % k == 0:
            # rebalance using signal at t-1 (sig[d] uses returns up to d-1)
            sc = sig.loc[d]
            liq = liquid.loc[d]
            cand = sc[liq & sc.notna()].dropna()
            if len(cand) >= 2 * n:
                if not scramble:
                    worst = cand.nsmallest(n).index
                    best = cand.nlargest(n).index
                else:
                    idx = rng.permutation(len(cand))
                    worst = cand.index[idx[:n]]
                    best = cand.index[idx[n:2 * n]]
                w = pd.Series(0.0, index=sc.index)
                w[worst] = 1.0 / n
                w[best] = -1.0 / n
        if w is not None and i + 1 < T:
            nx = rets.iloc[i + 1]
            r = float((w * nx).sum())
            # cost at rebalance day (applied on the day after rebalance)
            if i % k == 0:
                r -= 2 * COST_BPS / 1e4  # both sides traded
            ret_daily.append(r)
            dnum.append(dates[i + 1])
    return pd.Series(ret_daily, index=dnum)

def main():
    prices, rets = load_prices_rets()
    out_all = {}
    print("=" * 76)
    print("MEAN-REVERSION MARKET-NEUTRAL — EPISODE-CONDITIONAL (with costs, no lookahead)")
    print("=" * 76)
    for k in [3, 5, 10]:
        for n in [10, 20, 30]:
            r = backtest(prices, rets, k, n)
            if r.std() == 0:
                continue
            sr = r.mean() / r.std() * np.sqrt(252)
            cum = (1 + r).cumprod()
            mdd = (cum / cum.cummax() - 1).min()
            cagr = (1 + r).prod() ** (252 / len(r)) - 1 if len(r) else 0
            eps = {}
            for name, a, b in LOSS_EPISODES:
                x = r[(r.index >= a) & (r.index <= b)]
                eps[name] = {
                    "total_pct": round(float(x.sum() * 100), 2),
                    "sharpe": round(float(x.mean() / x.std() * np.sqrt(252)), 2) if x.std() else 0,
                }
            mask = pd.Series(False, index=r.index)
            for _, a, b in LOSS_EPISODES:
                mask |= (r.index >= a) & (r.index <= b)
            out = r[~mask]
            out_sr = out.mean() / out.std() * np.sqrt(252) if out.std() else 0
            key = f"k{k}_n{n}"
            out_all[key] = {
                "full_sharpe": round(float(sr), 3), "cagr_pct": round(float(cagr * 100), 2),
                "maxdd_pct": round(float(mdd * 100), 2), "n_days": int(len(r)),
                "loss_episodes": eps, "outside_sharpe": round(float(out_sr), 2),
            }
            print(f"\nk={k} n={n}: full SR {sr:+.2f} CAGR {cagr*100:+.1f}% MaxDD {mdd*100:.0f}% (n={len(r)})")
            for name, e in eps.items():
                print(f"    in {name:12s}: {e['total_pct']:+7.2f}%  SR {e['sharpe']:+5.2f}")
            print(f"    OUTSIDE: SR {out_sr:+.2f}")
    with open(RES / "meanrev_episode_research.json", "w") as fh:
        json.dump(out_all, fh, indent=2, default=str)
    print("\nWrote results/meanrev_episode_research.json")

if __name__ == "__main__":
    main()
