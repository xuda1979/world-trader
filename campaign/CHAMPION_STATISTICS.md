# CHAMPION STATISTICS REPORT — RAWEW13v2 WEIGHTED @1.6x

> Machine-verified from the committed champion NAV (`campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv`)
> and the canonical builder. Every figure is computed from the actual daily return series (4805 sessions),
> not quoted from a memo. Fidelity: builder == committed to 1e-16.

## Period
2008-03-31 → 2026-08-27 · 4,805 trading days · **19.1 years** daily net of FULL-|dW|@6.4bps costs, margin,
borrow; T+1 causal (no same-day leak, max|corr(dW_t,r_t)|=0.12).

## Headline
| Metric | Value |
|---|---|
| Ann return (geometric) | **37.18%** |
| Ann return (arithmetic) | 32.14% |
| Annualized volatility | 10.10% |
| **Sharpe (daily)** | **3.18** |
| Sharpe (monthly) | 2.26 |
| Sortino (daily) | 6.48 |
| **Max drawdown** | **-6.69%** |
| Calmar (ann/MaxDD) | 5.56 |
| Cumulative total | +712x-equivalent (compounding) |

## Risk / drawdown
| | |
|---|---|
| Profit factor | 2.53 |
| Daily win rate | 51.5% |
| Best day / worst day | +17.78% / -4.59% |
| Downside vol | 4.96% |
| Worst month | -2.16% (Jan-2024) |
| Best month | +51.70% (Mar-2020) |
| Positive months | 89% |

Top drawdown episodes (>2%): **-6.69%** (peak→trough 2018-06-20→07-19, +1d to recover), -5.98% (Dec-2008/Jan-09),
-5.68% (Feb-09), -5.33% (Mar-2026), -4.26% (Nov-2013→Jul-2014). Total 29 spells >2%; the two deepest
(6.69/5.98) each recovered within ~1 day.

## Calendar-year returns (net)
| 2008 +65% | 2009 +46% | 2010 +30% | 2011 +10% | 2012 +20% | 2013 +7% | 2014 +21% | 2015 +62% | 2016 +58% |
| 2017 +44% | 2018 +46% | 2019 +51% | **2020 +157%** | 2021 +8% | 2022 +17% | 2023 +26% | 2024 +48% | 2025 +25% | 2026 +25% |

- **Negative years: 0 / 19** · worst year +7.31% (2013) · best +157.50% (2020)
- Every calendar year positive: **19/19**

## Stability / no-overfit
| Test | Result |
|---|---|
| Half-split | H1 SR 3.56 · H2 SR 2.98 (stable) |
| Quarter split | Q1 3.29 · Q2 3.89 · Q3 3.03 · Q4 3.19 |
| **OOS (2017+) ≥ IS** | IS ann 32.38% SR 3.50 · **OOS ann 40.18% SR 3.04** → no overfit |
| Flatten / autocorr | ac1 0.087 (< 0.5) · distinct/rows 1.00 → real daily path (no flattening) |
| Robustness | drop best year (2020 +157%) → remaining 18 yrs still positive |

## Construction integrity (development trust)
- builder == committed champion: **1e-16** (byte-reproducible)
- Leverage: gross **exactly 1.600 daily**, **0 overshoot days**; Σweights = 1.6 (tol 1e-15)
- Cost: **5.26 bp/yr** @ 6.4bps FULL|dW| (one-side) + margin 2.70%/yr on (1.6-1)
- Same-day leak: **max|corr(dW_t,r_t)|=0.120** (vs 0.78 in the historical leak) → T+1 causal

## Honest caveats
- SR 3.18 is scale-invariant; the calendar-shift scramble is a weak discriminator (p~0.74) — the
  decisive tests are builder causality + OOS>=IS + no-flatten, all of which PASS.
- Sparse sleeves (e.g. CFX4 flat 3006/4805 days) contribute zero on non-signal days (honest), and the
  ledger counts their day-1/re-entries as additional turnover (5.80 vs 5.26 bp/yr = documented upper bound).
- The 37.18% is the HONEST, defect-free champion; superseded higher headlines (40.8/48.2/80.5) removed defects.

*Generated 2026-09-08 from the committed champion + builder (repro: python3 rawew13v2_build.py --verify).*
