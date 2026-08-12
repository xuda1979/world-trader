# Hedge Fund Strategy Backtest Framework

Backtests all **four/five hedge fund strategy categories** on REAL daily price
data with **6 bps round-trip trading cost** (3 bps per side).

## Strategies Implemented (mapped to the 4+1-class taxonomy)

| # | Category | Strategy | Core logic | Signal |
|---|----------|----------|-----------|--------|
| 1 | Equity | **Long/Short Equity** (L/S) | Long undervalued, short overvalued | Cross-sectional momentum (70%) + short-term reversal (30%), vol-adjusted; 130/30, 120/20, market-neutral variants |
| 2 | Equity | **Equity Market Neutral** (EMN) | Zero net market exposure, pure alpha | Multi-factor composite; dominant driver = 52-week-high distance (George & Huang 2004) |
| 3 | Macro | **Global Macro** | Top-down multi-asset allocation | Multi-asset trend + momentum + vol-regime scaling |
| 4 | Macro | **Risk Parity (Bridgewater)** | Diversified leverage, vol equalization | Inverse-vol weights across equity/FX/crypto |
| 5 | Event-Driven | **Merger Arbitrage** (proxy) | Profit from event-induced drift | Post-earnings drift (PEAD) 2/3/5% thresholds + sector-pair convergence |
| 6 | Relative Value | **Statistical Arbitrage (pairs)** | Exploit relative mispricing of correlated stocks | Top-40/80 pairs by 60d return correlation, refit semiannually; log-spread z-score entry \|z\|>1.5 exit \|z\|<0.5 |
| 7 | Multi-Strategy | **EW Blend** | Low-correlation streams, one book | Equal-weight of L/S + CTA + Global Macro + StatArb |

## Data (free sources)
- **576 US equities** (2006-2026): S&P 500 + mid-cap names
  - 251 tickers with 16+ years of daily OHLCV (twelve_big)
  - 275 additional tickers with 2 years (Polygon API)
- **8 FX pairs** (EUR/USD, USD/JPY, etc., 2019+)
- **2 crypto** (BTC, ETH, 2023+)
- **27 Chinese stocks** (cn/)
- **Fama-French factors** (1926-2026)

## Key Design Decisions
- **T+1 execution**: signals on day T execute at T+1 (no look-ahead bias)
- **6 bps round-trip cost**: charged on weight deltas at each rebalance
- **No slippage/market impact** (user spec)
- **Vol targeting**: CTA and macro scale to target portfolio vol
- **Position caps**: no individual position >20-30% of capital
- **Stat arb pair selection**: pairs refit semiannually from trailing window
  ONLY (no look-ahead into the traded segment); z-scores warm up 60 days

## Running
```bash
# Quick run (fewer variants, ~60s)
python tools/quant/hedge_fund_strats/run_all.py --quick

# Full run (all variants, ~3 min)
python tools/quant/hedge_fund_strats/run_all.py

# New-category strategies + multi-strategy blend (appends to results/)
python tools/quant/hedge_fund_strats/run_extras.py
```

## Results Summary (2008-2026, 6 bps cost)
See `results/strategy_comparison.csv` for full metrics.

| Strategy | Ann Ret | Ann Vol | Sharpe | Max DD | Beta |
|----------|---------|---------|--------|--------|------|
| L/S 130/30 | +21.6% | 26.5% | **0.85** | -45.7% | 1.06 |
| L/S 120/20 | +16.6% | 19.9% | **0.82** | -34.9% | 0.79 |
| L/S Market Neutral | +23.9% | 32.5% | **0.82** | -56.1% | 1.32 |
| Risk Parity (Bridgewater) | +8.7% | 12.0% | **0.60** | -28.3% | 0.50 |
| StatArb 80 pairs | ~0.0% | 6.2% | **0.16** | -16.9% | 0.04 |
| StatArb 40 pairs z1.0 | -0.3% | 5.9% | **0.11** | -15.2% | 0.04 |
| Global Macro | +1.1% | 4.7% | -0.12 | -10.7% | 0.08 |
| CTA (3 variants) | -0.6% to -1.4% | 10-12% | -0.06 to -0.14 | -30%+ | ~0.05 |
| Merger Arb PEAD | +1.1% | 2.6-2.9% | -0.21 to -0.28 | -8% | ~0.01 |
| EMN | -12.3% | 20.1% | -0.59 | -90.3% | -0.37 |
| **Multi-Strategy EW** | **+5.2%** | **8.4%** | **0.41** | **-15.1%** | **0.00** |

**Honest findings (after 6 bps round-trip costs):**
- **L/S momentum (Sharpe 0.85) is the only alpha-positive standalone** — but
  its edge is mostly market beta (β≈1.1) on the 130/30 net-long book; the
  "market neutral" L/S variant holds β=1.32, i.e. the vol-adjustment
  accidentally concentrates in high-beta names.
- **Statistical arbitrage is the only genuinely market-neutral positive-Sharpe
  strategy** (β≈0.04, Sharpe 0.11-0.16, profit factor 1.09, positive alpha
  +2-2.5%/yr) — but 45-48x annual turnover at 6 bps (≈27-29%/yr cost drag)
  erases most of the gross edge. Higher pair count helps (0.16 vs 0.04):
  more legs = lower per-pair cost drag and better diversification.
- **Risk Parity (0.60 Sharpe, β=0.50) beats raw macro**: inverse-vol allocation
  across uncorrelated asset classes captures the vol risk premium with far
  lower cost drag (1.9x turnover vs 4.3x).
- **CTA and EMN fail after cost** — trend signals on equity names are too
  noisy/costly; naive multi-factor EMN composites have no stable after-cost
  edge on this universe (consistent with the repo's ls/ research: only
  single-factor 52-week-high distance survives, at +0.34 gross).
- **Multi-Strategy EW (Sharpe 0.41, β=0.00) demonstrates the core HF thesis**:
  the stat-arb stream is *negatively* correlated with CTA (-0.19) and macro
  (-0.08), so blending uncorrelated streams produces positive risk-adjusted
  return even when 3 of 4 components are individually ≤ 0 after cost.
- A realistic outcome for naive heuristics — real hedge funds add event
  data, fundamental data, and lower turnover.

## Files
- `core.py` - data loading, backtest engine, performance metrics
- `strat_ls_equity.py` - Long/Short Equity (130/30, 120/20, market neutral)
- `strat_emn.py` - Equity Market Neutral
- `strat_global_macro.py` - Global Macro (+ Bridgewater risk parity)
- `strat_merger_arb.py` - Merger Arbitrage (event-driven proxy)
- `strat_cta.py` - Managed Futures / CTA
- `strat_stat_arb.py` - Relative Value / Statistical Arbitrage (pairs)
- `run_all.py` - master runner + comparison
- `run_extras.py` - stat arb variants + multi-strategy blend (appends)
- `download_data.py` - free data download (Polygon, Alpha Vantage, yfinance)
