"""Sweep stat-arb parameters (entry/exit/cooldown/basket) to search for the
config that survives 6 bps costs.

FINDINGS (Aug 2026, 2008-2026, 6 bps round-trip; cost-inclusive metric):
  - All configs are NEGATIVE after costs. Best: zw=60, entry 1.5, exit 0.5,
    refit 126d, 21d REBALANCE, gross cap 2.0, basket 80 -> Sharpe -0.14.
  - The weekly baseline (-0.32) was previously called optimal under a
    cost-exclusive metric that hid turnover drag; with costs counted,
    slower rebalancing wins (25x vs 47x turnover).
  - Rebalance slowdown 5->42d: -0.32 -> -0.26 (21d is the sweet spot).
  - Top-K forced exposure (always hold K most-extended pairs): -0.37..-0.59
    (forces weak setups; per-name overlap means effective diversification is
    far below K).
  - Slow signals (z-window 120/250, entry 2.0): -0.15..+0.11 (edge is
    short-horizon).
  - Exit threshold 0.0-0.45: monotone worse than 0.5 (holding to full
    convergence cuts turnover 46x->11x but gives back most of the edge).
  - Cooldown after exit: no help (0.057 vs 0.107).
  - Book-level gross cap is LEVERAGE control only: uncapped gross is ~70x
    (30-40 pairs x $1 each leg) -> 219% vol -> -100% return. The "avg 1 pair"
    readings earlier were an artifact of measuring gross/2 with cap=2.0.
  Conclusion: naive z-band pairs at 6 bps is NEGATIVE in every config
  (best -0.14 with 21d rebalance); turnover x 6 bps ~= the gross edge.
  Needs a genuinely different construction (sector constraints, vol-regime
  timing, fundamental legs) to do better.
"""

import sys
sys.path.insert(0, '.')
import pandas as pd, numpy as np
from tools.quant.hedge_fund_strats.core import DataLoader, BacktestEngine, compute_performance
from tools.quant.hedge_fund_strats.strat_stat_arb import select_pairs

equities = DataLoader.load_equities(source='twelve_big', min_rows=1000)
prices = DataLoader.build_price_panel(equities)
prices = prices[prices.index >= '2008-01-01'].dropna(how='all').ffill(limit=5)
nan_frac = prices.isna().mean()
prices = prices[nan_frac[nan_frac < 0.3].index.tolist()]
returns = DataLoader.build_return_panel(prices, method='simple')
good = prices.columns[prices.count() > 500]
prices_u, returns_u = prices[good], returns[good]
logp = np.log(prices_u)
yrs = len(prices_u) / 252
print(f'Universe: {prices_u.shape[1]} names', flush=True)


def build_weights(n_basket, entry_z, exit_z, z_window=60, cooldown=0):
    """Vectorized state machine with optional cooldown after exit.

    No book-level gross cap: each active pair is $1 long + $1 short, so
    gross = 2 x #active pairs. Cap only against extreme clustering at
    max_gross (never binds in practice).
    """
    w = pd.DataFrame(0.0, index=prices_u.index, columns=prices_u.columns)
    refit_pts = list(range(500, len(prices_u), 126))
    for t, s in enumerate(refit_pts):
        end = refit_pts[t + 1] if t + 1 < len(refit_pts) else len(prices_u)
        pairs = select_pairs(returns_u.iloc[s - 126:s], n_pairs=n_basket)
        seg = slice(max(0, s - z_window), end)
        lp = logp.iloc[seg]
        n_days = seg.stop - seg.start
        for (a, b) in pairs:
            if a not in lp.columns or b not in lp.columns:
                continue
            sp = (lp[a] - lp[b])
            mu = sp.rolling(z_window).mean()
            sd = sp.rolling(z_window).std().replace(0, np.nan)
            z = ((sp - mu) / sd).ffill().values
            state = np.zeros(n_days, dtype=int)
            cdown = 0
            for i in range(1, n_days):
                zi = z[i]
                if np.isnan(zi):
                    continue
                if state[i - 1] == 0:
                    if zi > entry_z and cdown == 0:
                        state[i] = 1
                    elif zi < -entry_z and cdown == 0:
                        state[i] = -1
                else:
                    if abs(zi) < exit_z:
                        state[i] = 0
                        cdown = cooldown
                    else:
                        state[i] = state[i - 1]
                cdown = max(0, cdown - 1)
            sgn = np.sign(state)
            on = state != 0
            # Only rows [s, end) take the new basket; [seg.start, s) is warmup
            # (state-only) and keeps the previous basket's positions.
            w.iloc[s:end, w.columns.get_loc(b)] += np.where(on, sgn, 0.0)[s - seg.start:]
            w.iloc[s:end, w.columns.get_loc(a)] -= np.where(on, sgn, 0.0)[s - seg.start:]
    # Emergency cap only (2x full basket gross; never binds with <= basket pairs)
    for i in range(len(w)):
        row = w.iloc[i]
        g = row.abs().sum()
        if g > 2.0 * n_basket:
            w.iloc[i] = row / g * 2.0 * n_basket
    return w


for nb, ez, xz, cd in [(80, 1.5, 0.5, 0), (80, 1.0, 0.4, 0), (80, 1.0, 0.4, 10),
                       (80, 1.25, 0.5, 0), (80, 1.25, 0.5, 5),
                       (200, 1.0, 0.4, 0), (200, 1.25, 0.5, 0)]:
    print(f'config basket={nb} entry={ez} exit={xz} cd={cd}', flush=True)
    w = build_weights(nb, ez, xz, cooldown=cd)
    engine = BacktestEngine(prices_u, cost_bps=6.0)
    rets, eq, turn = engine.run(w, rebalance_freq=5)
    perf = compute_performance(rets, eq, benchmark_returns=returns_u.mean(axis=1))
    active = w.abs().sum(axis=1) > 0
    avgp = (w[active].abs().sum(axis=1) / 2).mean() if active.any() else 0
    print(f'  Sharpe={perf.sharpe:+.3f}  AnnRet={perf.annual_return:+7.2%}  Vol={perf.annual_vol:5.2%}'
          f'  MaxDD={perf.max_drawdown:7.2%}  Turn={turn / yrs:5.1f}x  AvgPairs={avgp:4.1f}', flush=True)
