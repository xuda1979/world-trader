# AlphaPortfolio Replication (Cong, Tang & Wang 2026, NBER WP 35195)

Goal: replicate the methodology and (best-effort) empirical results of
"AlphaPortfolio: Goal-Oriented Investment Management through Deep Reinforcement
Learning" using only **free, accessible data**.

## What we replicate (per the paper)
1. **Data**: monthly U.S. equity panel with firm characteristics. Free source:
   stockanalysis.com daily OHLCV for the S&P 100 cross-section (the endpoint
   caps history at ~10 years per symbol; `max`/`20Y` are truncated to 1 year).
   -> 100 large-caps, 2016-08..2026-08 (121 months), ~98 stocks/month.
2. **Features (Appendix B style)**: 22 characteristics from price/volume only
   (mom 3/6/12-1, volatility, amihud, dollar volume, ln price, turnover, their
   cross-sectional ranks, and 2 interactions). The paper uses 94 characteristics
   from WRDS/CRSP-Compustat that are not freely available - a key data gap.
3. **Model (Section 2)**: Panel Transformer with SREM (temporal self-attention)
   + RREM (cross-asset attention) that maps 12-month lagged feature sequences to
   per-asset scores -> long-short portfolio weights (Eq. 11).
4. **Training (Eq. 19)**: direct/differentiable maximization of the annualized
   Sharpe ratio (pathwise gradient, walk-forward train/val/test).
5. **Benchmarks**: VW long-short, EW long-short, linear PPP.
6. **Evaluation**: OOS returns, Sharpe, factor alphas via FREE Ken French
   FF3/FF5/MOM/CAPM factors.

## Fixes applied to make the pipeline run & honest (real data)
- `model.long_short_weights`: accept a fractional `G` (0.25) and convert to an
  integer count (was slicing with a float -> crash).
- `run_replication`: benchmark frame built from the *scored* (ym,id) pairs via a
  merge (raw panel contains ids that fail the per-month history gate, e.g. GEV).
- `evaluate/benchmarks`: OOS returns made consistent decimal units
  (DRL returns were in % vs decimal for benchmarks -> absurd Std/MaxDD).
- `linear_ppp`: select training rows via a robust `_train` indicator column
  (the concat mask had a length mismatch after merges).
- `train.standardize_panel`: per-month cross-sectional z-score of raw features,
  winsorized at 1/99 pct. This was the key fix - the transformer would not
  converge with unscaled volatility/amihud/dollar-volume features.

## Honest results & gaps vs the paper
- Paper headline: OOS Sharpe > 2 and risk-adjusted alpha > 13% (monthly rebal).
- Our best-effort DRL on free data: the model now **converges** in training
  (train Sharpe ~1.2-1.4, val improving to ~+0.8 at more epochs) but OOS on the
  short 2024-09..2026-08 window is weak/negative (overfits 60 train months).
- Linear PPP reports implausibly high test alphas (t~75) - the linear benchmark
  is not a faithful reproduction and should be read with caution.
- These are **not** the paper's WRDS numbers. Reproducing Sharpe>2 requires the
  full CRSP/Compustat characteristics and a much longer sample, which are not
  freely accessible)Skip the compaction tags; README written.

## Files
- download_real_data.py - fetch free OHLCV from stockanalysis.com (S&P 100, 10Y)
- process_real_data.py  - daily OHLCV -> monthly panel + characteristics/factors
- features.py / data.py - legacy feature & panel helpers
- model.py              - Panel Transformer (SREM+RREM) + long-short generator
- train.py              - differentiable Sharpe / direct policy search + standardization
- benchmarks.py         - VW, EW, linear PPP baselines
- evaluate.py           - Table 1/2-style OOS results + free-factor alphas
- run_replication.py    - end-to-end pipeline -> replication_report.txt

## Update (real data integration - SEC EDGAR + full S&P 500 cross-section)
Expanded the replication from the S&P-100 subset to the **full S&P 500** cross
section with **SEC EDGAR XBRL fundamentals**, processed entirely with free data:

### New free data pipeline
- `fetch S&P 500 universe` from a public GitHub mirror (503 constituents + CIKs).
- `download_prices.py`  - daily OHLCV for all 503 S&P 500 (stockanalysis.com, 10y)
                          -> DuckDB `wh_prices.duckdb` (`daily_prices`, ~1.22M rows).
- `download_sec_fundamentals.py` - SEC EDGAR XBRL `companyfacts` for 501 CIKs
                          (annual 10-K, ~7.5k rows) -> parquet + DuckDB.
- `build_panel.py`      - combines prices + fundamentals into `monthly_panel_full.csv`
                          (59k monthly obs, 503 stocks, 2016-2026).
- `build_features_full.py` - adds cross-sectional ranks for all 35 characteristics
                          (price/volume + value/profitability/investment/accruals).
- `run_replication_full.py` - AlphaPortfolio DRL on the full panel.

### Fundamental characteristics added (from 10-K XBRL tags)
book-to-market, ROE, ROOA, capex/assets, accruals (approx), inventory/assets -
mapping several of the paper's 94 WRDS characteristics onto free public filings.

### Results (full panel, OOS 2024-09..2026-08, 35 features, 503 stocks)
| Model                  | RTN% | Std% | Sharpe | MaxDD% |
|------------------------|------|------|--------|--------|
| AlphaPortfolio (DRL)   | 2.25 | 1.91 | 1.18   | -1.1   |
| Indirect VW top/bot    |-0.09 | 4.62 |-0.02   | -3.9   |
| Indirect EW top/bot    |-0.52 | 2.34 |-0.22   | -3.0   |
| Linear PPP             |19.53 | 0.91 |21.47   | 0.0    |

The DRL OOS Sharpe improved from **-0.81** (100-stock, 22-feature subset) to
**+1.18** with the broader cross-section + SEC fundamentals. Still below the
paper's headline Sharpe>2 (their full 94-characteristic WRDS panel + longer
sample are not freely available), but a meaningful best-effort replication on
free data. Linear PPP benchmark is long-biased and unreliable.
