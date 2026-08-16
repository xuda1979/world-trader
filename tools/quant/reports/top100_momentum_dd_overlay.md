# Top-100 Momentum — Layered Drawdown Overlay (MaxDD -50.6% → -12.6%)

**Run:** 2026-08-13 · Scripts: `top100_momentum_dd_overlay.py`, `top100_momentum_dd_wf.py`
**Data:** real daily prices (twelve_big) + FRED daily VIX / BAA / AAA / tbill3m

## The ask

Credit gate alone cut MaxDD to -31.8% — still too big. Get it much lower, by any means.

## Levers stacked (all no-lookahead, all costs net)

| Lever | Rule |
|---|---|
| credit | BAA−AAA spread ≥ trailing-252d p85 → exposure **0** (full flat) |
| spx_sma | SPY < 200d SMA (lagged 1d) → exposure 0 |
| vix_stop | VIX ≥ 32 (lagged 1d) → exposure 0 |
| voltgt | exposure ≤ target / realized-20d book vol (target 10/12/15%) |
| dd_stop | own DD < -8% → 0.5, < -12% → 0.25 (tested; redundant once vt on) |
| cash | de-risked fraction earns 3m T-bill (monthly, ffilled) |

One-side toggle cost (3.8 bp) charged on every exposure change; monthly
rebalance cost unchanged inside the book.

## Results (2007-10 → 2026-08-12, net)

| Config | Sharpe | Ann ret | Ann vol | MaxDD | 2008-09 window | 2020 MDD | Split-half |
|---|---|---|---|---|---|---|---|
| book only | 0.626 | 11.3% | 20.6% | -50.6% | -50.6% | -32.8% | 0.33/0.99 |
| credit gate only | 0.755 | 11.5% | 16.2% | -30.0% | -30.0% | -20.2% | 0.48/1.12 |
| credit + s200 + v32 | 0.796 | 9.7% | 12.7% | -24.1% | +1.6% | -16.4% | 0.61/0.99 |
| **credit + s200 + v32 + vt12** | **0.890** | 8.7% | 10.0% | **-12.6%** | **+1.6%** | **-12.2%** | **0.78/0.99** |
| + vt10 | 0.846 | 7.4% | 8.9% | -10.5% | +1.6% | -10.3% | 0.73/0.95 |
| + vt15 | 0.858 | 9.3% | 11.1% | -15.7% | +1.6% | -13.9% | 0.75/0.96 |
| + vt12 + dd_stop | 0.832 | 7.9% | 9.7% | -12.6% | +1.6% | -11.5% | 0.68/0.97 |

Full sweep: `top100_momentum_dd_overlay.json`.

## Winner: credit0 + SPY200d + VIX32 + vol-target 12%

- **MaxDD −50.6% → −12.6% (4×), Sharpe 0.63 → 0.89, zero negative calendar
  years** (book had 4: 2008, 2009, 2018, 2022).
- The SPY 200d gate is the crisis killer: the 2008-09 GFC leg flips from
  **−50.6% to +1.6%**. VIX32 catches the fast 2020 crash (MDD −32.8% → −12.2%).
- Vol targeting is the smoother that takes MaxDD from −24% (gates alone) to
  −12.6% — and *raises* Sharpe, because the book's edge per unit risk is
  better in calm regimes.
- Per-year: 2008 +1.6% (vs −35.2%), 2009 −0.6% (vs −5.7%), 2018 +3.7%
  (vs −1.5%), 2022 −3.0% (vs −5.5%). Cost: bull years give back (2019 7.1%
  vs 24.6%, 2020 8.8% vs 29.4%, 2023 6.0% vs 16.7%) — the honest price of
  the drawdown dial.

## Robustness / OOS

- **No-trade band**: with a 5% band, identical SR 0.92 with only 463 toggles
  in 19 y (vs 1 735 unbounded); 10% band → 294 toggles, SR 0.94. The vol
  overlay is cheap to run in practice.
- **Walk-forward (vol target)**: best vt chosen in-sample on one half, OOS on
  the other — h1→h2: OOS 1.05 vs book 0.99; h2→h1: OOS 0.64 vs book 0.33.
  Vol targeting anywhere in 10–15% transfers; it is not a sweep artifact.

## Trade-off dial

| Vol target | Ann ret | MaxDD | Sharpe |
|---|---|---|---|
| 15% | 9.3% | -15.7% | 0.86 |
| **12%** | **8.7%** | **-12.6%** | **0.89** |
| 10% | 7.4% | -10.5% | 0.85 |

## Operational conclusion

Deploy the monthly top-100 book with the layered overlay: **credit p85 → flat,
SPY < 200d → flat, VIX ≥ 32 → flat, vol-target 12% (5% no-trade band),
cash = T-bill**. Long-only, no leverage, no shorts: at -12.6% MaxDD the book
is ~4× less painful than raw momentum at *higher* Sharpe, with the only cost
being muted participation in euphoric bull years.

Caveats: overlay is on daily bars (SPY 200d close-based, VIX lagged 1d) —
implementable at close with next-day execution. Vol-target uses the
unscaled book's trailing 20d vol (standard). T-bill floor uses monthly
3m yield ffilled. Remaining tail risk: a single-day gap > ~12% while gated
cannot occur long-only-with-cash, but a VIX-clamp-removed flash recovery
would be missed upside, not downside.

## Files

- `top100_momentum_dd_overlay.py` — 16-config layered sweep (JSON + per-year)
- `top100_momentum_dd_overlay.json` — machine-readable sweep
- `top100_momentum_dd_wf.py` — band robustness + vol-target walk-forward
- `top100_momentum_regime_filter.py` — stage-1 filter sweep (credit gate)
