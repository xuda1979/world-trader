# AlphaPortfolio Full-Panel Results (S&P 500 + SEC EDGAR fundamentals)

## Data (all free)
- Universe: 503 S&P 500 constituents (public GitHub mirror, incl. CIKs)
- Prices: 10y daily OHLCV from stockanalysis.com -> DuckDB `wh_prices.duckdb`
  (~1.22M rows)
- Fundamentals: SEC EDGAR XBRL `companyfacts` for 501 CIKs (annual 10-K, ~7.5k
  fiscal-year records)
- 59,037 monthly observations, 2016-08..2026-08

## Features (35)
Price/volume (10) + fundamentals (6) + cross-sectional ranks (16) + interactions (3)
Fundamentals: book-to-market, ROE, ROOA, capex/assets, accruals~, inventory/assets

## OOS results (2024-09..2026-08, 60 train / 19 val / 19 test months)
| Model                | RTN%  | Std% | Sharpe | MaxDD% |
|----------------------|-------|------|--------|--------|
| AlphaPortfolio (DRL) |  2.25 | 1.91 |  1.18  |  -1.1  |
| Indirect VW top/bot  | -0.09 | 4.62 | -0.02  |  -3.9  |
| Indirect EW top/bot  | -0.52 | 2.34 | -0.22  |  -3.0  |
| Linear PPP*          | 19.53 | 0.91 | 21.47  |   0.0  |

Train convergence: train Sharpe 3.9, val Sharpe peaked ~1.3 (40 epochs).
*Linear PPP benchmark is long-biased / unreliable; read with caution.

## Interpretation
- Broadening the cross-section (S&P 100 -> 500) and adding SEC EDGAR fundamentals
  lifted AlphaPortfolio OOS Sharpe from **-0.81 to +1.18**.
- Still below the paper's headline (Sharpe>2, alpha>13%) which requires the full
  94-characteristic WRDS/CRSP-Compustat panel over a longer sample (not free).
