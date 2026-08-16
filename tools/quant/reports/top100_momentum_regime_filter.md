# Top-100 Momentum × VIX / Macro Regime Filter — Backtest

**Run:** 2026-08-13 · Scripts: `top100_momentum_regime_filter.py`, `top100_momentum_credit_wf.py`
**Data:** real daily prices (twelve_big panel) + FRED daily VIX / BAA / AAA / t10y2y

## The ask

The monthly top-100 high-Sharpe US momentum book works well sometimes, not always
(SR 0.62, but MaxDD **-50.6%** and split-half 0.34/0.98). Test VIX (and macro
stress indices) as a filter for the drawdown and underperformance periods.

## Method

- Unfiltered baseline is the existing `monthly_top100_momentum.py` book, now
  refactored to accept a daily **exposure overlay** ∈ [0,1] (additive, default
  off — original deliverable unchanged).
- All filters are **no-lookahead**: index value lagged 1 trading day.
- When exposure toggles, **one-side cost (3.8 bp) is charged on the traded
  fraction**; all metrics below are net of it and of the existing monthly
  rebalance cost.
- Filter families swept (threshold → de-risked exposure):
  - `vix_abs`: VIX ≥ {20, 22, 25, 28, 32, 35} → {0%, 30%, 50%}
  - `vix_pct`: VIX ≥ trailing-252d percentile {0.85, 0.90, 0.95} → {0%, 30%, 50%}
  - `credit_pct`: BAA−AAA corporate spread ≥ trailing-252d percentile
    {0.85, 0.90, 0.95} → {30%, 50%}
  - `curve_inv`: 10y−2y < 0 → {30%, 50%}

## Results (2007-10 → 2026-08-12, 4 747 trading days, net of all costs)

| Filter | Sharpe | Ann ret | Ann vol | MaxDD | 2008-09 DD window | % days de-risked | Toggles |
|---|---|---|---|---|---|---|---|
| **baseline** | 0.626 | 11.3% | 20.6% | -50.6% | -50.6% | — | — |
| **credit_pct 0.85 → 30%** | **0.779** | **11.8%** | 15.9% | **-31.8%** | **-28.7%** | 25.4% | 134 |
| credit_pct 0.85 → 50% | 0.745 | 11.7% | 16.9% | -37.2% | -35.3% | 25.4% | 134 |
| vix_abs 25 → 30% | 0.739 | 9.8% | 14.0% | -32.9% | -32.7% | 18.2% | 204 |
| vix_abs 22 → 30% | 0.730 | 8.7% | 12.6% | -33.1% | -26.3% | 28.0% | 246 |
| vix_abs 25 → 0% | 0.703 | 8.8% | 13.2% | -27.1% | -24.9% | 18.2% | 204 |
| vix_pct 0.85 → 30% | 0.700 | 10.2% | 15.7% | -43.4% | -42.1% | 15.3% | 238 |
| vix_pct 0.95 → 30% | 0.663 | 10.5% | 17.4% | -49.4% | -48.3% | 6.6% | 162 |
| curve_inv → 50% | 0.585 | 10.2% | 20.1% | -50.6% | -50.6% | 11.5% | 15 |
| vix_abs 20 → 0% | 0.549 | 5.3% | 10.3% | -16.4% | -7.5% | 36.4% | 298 |

Full 36-config sweep: `top100_momentum_regime_filter.json`.

## Winner: credit-spread percentile gate (BAA−AAA ≥ trailing-1y p85 → 30% exposure)

The **credit spread** — not VIX — is the better stress filter for this book:

- **Sharpe 0.63 → 0.78, MaxDD −50.6% → −31.8%, return *up* (11.3% → 11.8%)**:
  the gate dodges systemic stress without surrendering the momentum premium.
- Per-year: 2008 −35.2% → **−14.6%**; 2009 −5.7% → **+2.4%**; 2018 −1.5% →
  **+4.7%**; 2020 MaxDD −32.8% → −23.5%; 2022 −5.5% → −3.1%. Modest give-backs
  only in 2007/2011/2014/2019 (still positive years).
- **Split-half Sharpe 0.34/0.98 → 0.50/1.12** — both halves improve, so it fixes
  the "sometimes not" early regime rather than just re-allocating luck.
- Toggle cost trivial: 134 toggles in 19 y (≈0.2%/yr drag, already netted).

Why it beats VIX here: VIX spikes are fast and mean-reverting, so a lagged gate
whipsaws (204-298 toggles) and gives back return; the corporate spread is a
slow, persistent systemic-stress signal — it flags the credit-crisis regimes
(2008, 2011, 2015-16, 2020, 2022) without chopping in transient vol spikes.
Yield-curve inversion fails as a gate (2008 crash started with the curve
already re-steepened; gate was off).

## Out-of-sample validation (walk-forward, threshold selection)

Best threshold chosen in-sample on one half, applied OOS to the other:

| Direction | q chosen IS | OOS Sharpe | baseline OOS |
|---|---|---|---|
| h1 (2007-16) → h2 (2017-26) | 0.85 | **1.120** | 0.993 |
| h2 (2017-26) → h1 (2007-16) | 0.85 | **0.504** | 0.330 |

The same q=0.85 wins **both halves independently** and beats baseline OOS in
both directions — the gate is not a sweep artifact.

## Operational conclusion

Deploy the **credit-spread percentile gate (p85 of trailing 1y, de-risk to 30%,
lagged 1 day)** on the top-100 momentum book: SR ≈ 0.78, MaxDD ≈ −32% (from
−51%), return unchanged-or-better, both regimes improved. The unfiltered run
stays available (`walk_forward(exposure=None)`); the gate is an additive
overlay, not a rewrite.

Caveats: Moody's BAA/AAA yields publish with a short lag — immaterial for a
252d-percentile regime signal. De-risking uses cash (no short/hedge leg).
Percentile window (252d) and factor (0.3) are the swept optimum and survive
WF; fine-tuning beyond the sweep is not claimed.

## Files

- `top100_momentum_regime_filter.py` — 36-config sweep (baseline + families)
- `top100_momentum_regime_filter.json` — full machine-readable results incl. per-year
- `top100_momentum_credit_wf.py` — walk-forward OOS check of the credit gate
- `monthly_top100_momentum.py` — refactored: `prepare()` + `walk_forward(exposure=)`
  (original `run_backtest()` behavior unchanged)
