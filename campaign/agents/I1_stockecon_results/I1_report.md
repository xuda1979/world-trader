# I1_stockecon — DIRECTION 5: Cross-Sectional Stock Tail L/S

## VERDICT: **REJECT** (no I1_sleeve.csv written — SR gate failed)

Gate: SR>=1.5 AND corr(champion)<0.5. Best variant found: **SR=0.661** (H_es_smooth21) — fails SR by 0.84. Champion-corr gate passes (0.114<0.5) but SR is binding. Briefed (unreversed) direction is NEGATIVE (SR −0.68). All variants listed below with exact numbers; nothing hidden.

## Universe / breadth
- Source: `tools/quant/data/twelve_big/*.csv` (299 tickers, close OHLCV 2007-01-03..2026-08-12) ∩ `spy_holdings/spy_holdings.csv` (504 SPDR SPY constituents, snapshot) → **258 large-cap names traded; mean 235 names/day**; fail-closed breadth floor: no trading before 100 names have valid data (first signal 2007-03-30).
- 41 twelve_big tickers not in SPY snapshot dropped (e.g. recent listings / non-SPX: ABNB, ARM, ZM-class names etc.).
- **Survivorship disclosure**: constituent list is a 2026 snapshot applied historically; within-survivor drift not modeled. Offline-only data constraint.

## Signal (T+1 causal)
- ret = close-to-close pct change. Rolling 60d (min_periods=60, window ends at decision day t):
  - `skew60` = rolling skew of daily returns
  - `es95_loss60` = −mean(worst 5% returns in window) (positive = crash-prone)
- Cross-sectional z: `sig = z(skew60) − z(es95_loss60)`; + = stable/high-skew (briefed LONG).
- Weights: cross-sectionally z-scored, gross-normalized to 1 (dollar-neutral). **T+1**: positions formed at close t earn close-to-close returns of t+1 (`W.shift(1)·r`). No lookahead anywhere.

## Costs (full campaign stack, per rules)
- 6bps × full one-side |dW| turnover: primary variant A turns 20.7×/yr → **1.24%/yr** drag.
- 0.5%/yr borrow × short notional (~0.49) → **0.24%/yr**.
- 4.5%/yr margin × (gross−1): gross≤1 in all primary variants → **0**. (Unnormalized sensitivity I carries gross≫1 and is cost-dominated, reported as computed.)
- Math: ann=(1+r).prod()**(252/n)−1; SR=r.mean()/r.std()*sqrt(252); MaxDD=(1+r).cumprod() drawdown (negative).

## Results (all net of full cost stack, gross-1 dollar-neutral)
| Variant | Description | ann | SR | MaxDD | corr vs champ | SR by subperiod |
|---|---|---|---|---|---|---|
| A | **Briefed**: long stable/high-skew, short crash-prone, daily | **−5.60%** | **−0.682** | −68.6% | −0.083 | — |
| B | Briefed, 20% quantile book | −3.04% | −0.723 | −46.0% | −0.095 | — |
| C | Briefed, weekly rebal | −6.14% | −0.759 | −72.0% | −0.089 | — |
| D | Reversed combined | +2.17% | 0.309 | −19.3% | 0.083 | .32/.18/.38/.65 |
| E | Reversed skew-only | −3.48% | −0.689 | −51.2% | −0.054 | — |
| F | ES-only (long high tail-loss) | +6.05% | 0.563 | −22.7% | 0.114 | .58/.72/.56/1.10 |
| G | F, 5d-smoothed | +6.61% | 0.614 | −22.3% | 0.116 | 2023+: 1.20 |
| **H** | **F, 21d-smoothed (best)** | **+7.03%** | **0.661** | **−19.3%** | **0.114** | 2023+: 1.32 |
| I | Decile book, UNNORMALIZED (gross≫1 → margin-dominated) | −100% | 0.247 | −100% | 0.121 | 2023+: 0.94 |
| J | Reversed-skew + ES combo | +3.71% | 0.425 | −21.1% | 0.100 | — |
| K | H signal + 10% vol-target leverage (trailing 252d, causal) | +4.54% | 0.300 | −59.0% | 0.114 | 2023+: 0.80 |

Pre-cost variant A SR = −0.496: the sign error is the signal, not costs. Champion in-window (2008-09..2026-08): ann +60.6%, SR 5.20 (matches campaign record).

## Interpretation
1. The briefed direction is a **known negative-edge anomaly in reverse**: high-skew/lottery large-caps chronically *underperform* (MAX/lottery + low-vol anomalies). Long-stable/short-crash loses: SR −0.68 over 4,935 days.
2. The economically correct sign (short lottery / long tail-prone) is positive but **weak**: best SR 0.661 full-sample. It is better in the recent regime (2023+: SR 1.10–1.32) but that alone does not meet the gate and would be regime-fitting to adopt.
3. Champion correlation is low (≈0.11) — the sleeve is diversifying in principle — but SR gate fails by a wide margin (0.661 vs 1.5 required). **FAIL-CLOSED: REJECT. No I1_sleeve.csv.**
4. cboe_options/latest (9 tickers, single-day snapshot) provided no usable cross-section and was not used (would add lookahead/no breadth).

## Repro
`python3 campaign/scripts/i1_stockecon.py` (primary + briefed/reversed), `i1_stockecon2.py` (sign flip + components), `i1_stockecon3.py` (sensitivities). Stats dumps: `i1_stats.json`, `i1_stats_flip.json`, `i1_stats_sens.json` in this directory.

DONE I1_stockecon
