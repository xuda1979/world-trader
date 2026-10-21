# Alpha-Leg Validation Status (high-Sharpe portfolio @ 6bps)

Consolidated 2026-08-06, updated 2026-08-12. **Definitive gate: a leg must beat
a price-lag scramble/noise control to count as real alpha.** Raw OOS Sharpe > 0
is NOT sufficient (every trend/fx/pairs leg clears it yet fails the noise test).

## Validated alpha (today)
| leg | OOS SR | evidence |
|-----|--------|----------|
| **LS_GBRT** (equity L/S, 86-stock tw320, @6bps) | ~0.81-0.86 | deep 8y walk-forward OOS; IC/ICIR time-series; overfitting_flags=[]; real 8y diagnostic set |
| **LS_GBRT h21+n13+refit4** (current champion, @6bps) | **1.32** | 8y OOS 2018-2026, 21d horizon, 13+13 names, refit every 4d, OOS IC +0.010, verdict ok (0 flags), ret 17.6% dd -17.5% |

This is currently the ONLY validated high-Sharpe asset. There is NO validated
multi-leg high-Sharpe portfolio yet.

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

## Scramble-gate state (2026-08-12, important correction)
Two scramble gates exist and BOTH are unreliable as currently written:
- `build_gated_portfolio.py` permutation gate: BROKEN by construction --
  permutation preserves the return multiset, so scrambled Sharpe == real
  Sharpe ALWAYS => always FAIL. Old "champion passes scramble" JSON claims
  predate this bug (different gate era). Do not trust permutation output.
- `verify_scramble.py` price-lag+noise gate: too strict for a 0.8-1.2 Sharpe
  on 2005 days -- gaussian noise at the same std + 1-2d lag reaches max
  Sharpe ~1.24 by construction; every run incl. the champion FAILS it
  (champion pct=0.28, h21_n13 pct=0.20). It still RANKS correctly
  (winner beats champion beats failed-20y panels) and is kept for ranking.
- Honest discriminators that DO separate champion from noise: OOS IC
  (+0.014 winner vs ~0 on failed panels), verdict flags, window sweep.

## 6bps champion improvements (2026-08-12)
@6bps one-side (12bps RT) on the 8y twelvedata panel (86 names, OOS
2018-2026), champion family:
- baseline champion: SR 0.856
- **h21 (21d horizon + 21d rebalance): SR 1.156**
- **h21 + n13 (13+13 names): SR 1.202**
- **h21 + n13 + refit_freq=4 (fresher retrain): SR 1.318** <- CURRENT CHAMPION
  (ret 17.6%, dd -17.5%, to 7.1x, OOS IC +0.010, verdict ok 0 flags)
- h21 + n13 + vix32 gate: SR 1.164, maxDD -9.4% (vs -15.3%) -- optional
  drawdown halving at ~4% Sharpe cost
Promoted to live_signal config (2026-08-12): h21_n13 @6bps + refit_freq=4.
20y panels (86/120/262 names) ALL fail -- conclusively (w20y SR 0.279
likely_overfit; w20y_fx forced-factor refutation). Root cause: early-era
(2014-17) model-state contamination poisons even 2018+ predictions
(2018+ IC +0.004 in 20y-start run vs +0.014 in 8y-start run). Raw factor
ICs fine pre-2018; FF data complete; not screen selection, not data quality.
The 8y window is the reliable window for this model family.

## VIX risk-filter update (2026-08-06)
Full 2001-day OOS sweep of VIX drawdown-filters (real CBOE VIX, FRED):
- percentile 0.90 / factor 0.5 (champion): SR 0.843, maxDD -19.9% (halves DD vs none)
- **VIX>=32 / factor 0.3 (absolute gate): SR 0.855, maxDD -19.9%**  <- best risk-filter
- no filter: SR 0.847, maxDD -33.4%
VIX de-risk cuts drawdown ~in half; the absolute VIX>=32/0.3 gate (stress-only
trigger) slightly beats both no-filter Sharpe AND the baseline drawdown.
Combined gate applied to live config (percentile 0.5 + level 32/0.3).
Best honest single-leg OOS Sharpe: ~0.85. Still no validated multi-leg book.

## Deep free-data panel update (2026-08-07)
Bulk free data added: **288-name / ~20y US panel** (TwelveData free tier ->
`data/twelve_big`; liquid top-120 -> `data/twelve_liq`). This is the
>300-proxy, >=4y independent panel the book was missing.
Honest gate results at 3.8 bps (price-lag scramble control):
- champion GBRT on 120 liquid names (2021-2026): **SR +0.22, FAIL gate** (50%
  scrambles beat it) -> NOT real alpha.
- champion GBRT on 288-name window: SR -0.63; XS stat-arb combos: SR -1.3.
- **No independent scramble-validated high-Sharpe leg found on new data**,
  consistent with the repo-wide finding that naive alpha fails the noise gate.
Keep research; do not promote unvalidated legs. Full report:
`results/deep_free_data_high_sharpe_REPORT.md`.

## High-Sharpe portfolio verdict (2026-08-07, urgent request)
Only LS_GBRT passes the scramble gate; every other leg (pairs/tsmom/gold/fx/
new xs probes) is rejected by the noise control.  Deployable book is therefore
single-leg champion: OOS SR 0.81-0.87 @3.8 bps (FRED VIX de-risk, DFF short
cost, vol-target 30%).  Combining rejected legs would manufacture a fake 2.0+
Sharpe (fixed-selection artifact).  Report: results/HIGH_SHARPE_DELIVERABLE.md
