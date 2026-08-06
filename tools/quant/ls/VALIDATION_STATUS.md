# Alpha-Leg Validation Status (high-Sharpe portfolio @ 3.8bps)

Consolidated 2026-08-06. **Definitive gate: a leg must beat a price-lag
scramble/noise control to count as real alpha.** Raw OOS Sharpe > 0 is NOT
sufficient (every trend/fx/pairs leg clears it yet fails the noise test).

## Validated alpha (today)
| leg | OOS SR | evidence |
|-----|--------|----------|
| **LS_GBRT** (equity L/S, 85-stock tw320_d4) | ~0.79-0.84 | deep 8y walk-forward OOS; IC/ICIR time-series; overfitting_flags=[]; real 8y diagnostic set |

This is currently the ONLY scramble-validated high-Sharpe asset. There is
NO validated multi-leg high-Sharpe portfolio yet.

## Failed scramble / do-not-quote
| leg | raw OOS SR | scramble result | verdict |
|-----|-----------|-----------------|---------|
| cross_asset_tsmom | 0.90 | 25-seed P(null>real)=52% | FAIL |
| gold_trend        | 0.96 | 25-seed P(null>real)=44% | FAIL |
| fx_momentum       | 0.50 | scramble42 SR 2.09 (real<noise) | FAIL |
| pairs stat-arb    | 6.96 | scrambled seeds 4.0-4.8 (real) | FAIL |
| etf_mom           | 0.18 | (non-equity side) | no edge |
| WINNER_LS/rev variants | 1.42 | same-family as champion (not independent) | corr. |

Numbers to NEVER quote as achievable: **2.28, 2.1, 6.6, 5.6** — all artifacts
of combining non-alpha legs or window-selection.

## Data constraints blocking a validated independent leg
- polygon/twelvedata: same 85-90 US stock universe (correlated to champion)
- cn: 27 names, only 1.5y history (too short for robust OOS)
- binance: BTC/ETH only; fx: 8 pairs (already failed); intraday: 17 names, 1.5y

## Required next step (real work to advance)
Build a genuinely INDEPENDENT, noise-beating leg, e.g.:
- TRUE cross-sectional stat-arb on a large (>300 names) panel with ≥4y history
- A factor probe in a decorrelated market/universe, validated against
  price-lag scramble BEFORE it is promoted into the book.
Validated tooling now enforces this gate:
  build_high_sharpe_portfolio.py (scramble gate; refuses unvalidated combos)
  build_strategy_portfolio.py (emits validated_book = ls-only)
