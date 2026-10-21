# Top-100 Momentum — Signal Horizon Test (90d trend vs 252d Sharpe)

**Run:** 2026-08-13 · Script: `top100_momentum_horizon.py`
**Ask:** "how about 90 day trend top 100" — rank the top-100 names by past-90d
cumulative return instead of past-year Sharpe.

## Setup

Same monthly rebalance, same 285-name universe, same window (2007-10 →
2026-08-12) and same costs — the ONLY change is the ranking signal, so the
comparison isolates signal quality. Positive-signal screen unchanged
(only names with signal > 0 are eligible).

## Raw books (no overlay)

| Signal | Sharpe | Ann ret | Ann vol | MaxDD | Split-half |
|---|---|---|---|---|---|
| t252_sharpe (current) | 0.626 | 11.3% | 20.6% | -50.6% | 0.33/0.99 |
| t63_ret | 0.718 | 12.7% | 19.3% | -49.8% | 0.58/0.89 |
| **t90_ret** | **0.695** | 12.3% | 19.4% | -47.7% | 0.54/0.87 |
| **t126_ret (6m)** | **0.730** | 13.0% | 19.3% | -47.2% | 0.61/0.86 |
| t252_ret | 0.685 | 12.1% | 19.5% | -53.0% | 0.49/0.90 |
| t90_sharpe | 0.594 | 10.3% | 20.0% | -53.6% | 0.37/0.87 |

Findings:

1. **90d trend beats the current book**: SR 0.70 vs 0.63, higher return, and
   the first-half Sharpe nearly doubles (0.33 → 0.54) — the "sometimes not"
   early regime improves.
2. **The sweet spot is ~6 months, not 3**: t126_ret is the best raw signal
   (SR 0.730, ann 13.0%).
3. **Sharpe-normalizing the signal hurts**: every `_sharpe` variant loses to
   its `_ret` counterpart (t90: 0.594 vs 0.695) — the volatility penalty in
   the denominator discards exactly the strong-trend, high-vol names that
   drive momentum returns.

## With the layered DD overlay (credit0 + SPY200d + VIX32 + vt12)

| Book + overlay | Sharpe | Ann ret | Ann vol | MaxDD | Split-half | % invested |
|---|---|---|---|---|---|---|
| **t252_sharpe + overlay** | **0.890** | 8.7% | 9.9% | -12.6% | 0.78/0.99 | 34% |
| t126_ret + overlay | 0.874 | 8.3% | 9.7% | -13.3% | 0.96/0.80 | 32% |
| t90_ret + overlay | 0.786 | 7.4% | 9.7% | -12.5% | 0.70/0.87 | — |
| t90_sharpe + overlay | 0.757 | 7.2% | 9.8% | -16.1% | 0.65/0.86 | — |

The overlay cuts every variant's MaxDD to ~-12…-13%, but the **252d Sharpe
book keeps the edge with it** (SR 0.890 vs 0.874 t126 vs 0.786 t90): the
slower signal interacts better with the 200d trend gate + vol targeting and
keeps more return (8.7% vs 7.4%). t126_ret is a near-tie second.

## Verdict

- Raw: 90d trend top-100 is real (better than the current raw book) and 6m
  trend is better still — worth remembering if we ever run the book WITHOUT
  the overlay.
- With the DD overlay (the deploy config): keep **252d Sharpe + overlay**
  (SR 0.890, MaxDD -12.6%). 6m trend + overlay is a respectable alternative
  (0.874, -13.3%) if a simpler signal is preferred.
- MaxDD is signal-agnostic at this point — the overlay, not the ranker,
  owns drawdown control.

## Files

- `top100_momentum_horizon.py` — signal sweep + overlay comparison
- `top100_momentum_horizon.json` — machine-readable results
