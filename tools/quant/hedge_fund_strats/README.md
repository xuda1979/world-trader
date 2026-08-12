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
- **14 macro series (2000-2026) via FRED API** (free, unlimited): WTI/Brent
  crude, nat gas, US 2/10/30y yields, 5 FX crosses, S&P500, Dow, VIX
  (`data_fred/`). Yields are inverted to trade the BOND direction.
- **21 real futures via Stooq** (`fetch_stooq.py`, free): ES/NQ/YM, CL/NG/RB/HO,
  GC/SI/HG, ZB/ZN/ZF, 6E/6J/6B/6C/6A, ZC/ZS/ZW — downloads currently blocked
  by Stooq IP throttling; `fetch_stooq.py` solves the SHA-256 PoW headlessly
  and is ready to rerun when the block lifts.

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
| **CTA Futures (FRED macro, 21d)** | **+2.5%** | **12.5%** | **0.16** | **-37.8%** | **0.00** |
| StatArb 80 pairs | ~0.0% | 6.2% | **0.16** | -16.9% | 0.04 |
| FI Arb (curve z-score) | -1.4% | 0.6% | -3.44 | -3.0% | 0.00 |
| StatArb 40 pairs z1.0 | -0.3% | 5.9% | **0.11** | -15.2% | 0.04 |
| Global Macro | +1.1% | 4.7% | -0.12 | -10.7% | 0.08 |
| CTA equities (3 variants) | -0.6% to -1.4% | 10-12% | -0.06 to -0.14 | -30%+ | ~0.05 |
| Merger Arb PEAD | +1.1% | 2.6-2.9% | -0.21 to -0.28 | -8% | ~0.01 |
| EMN | -12.3% | 20.1% | -0.59 | -90.3% | -0.37 |
| **Multi-Strategy EW** | **+6.8%** | **8.0%** | **0.61** | **-12.2%** | **0.00** |

**Honest findings (after 6 bps round-trip costs):**
- **L/S momentum (Sharpe 0.85) is the best standalone** — but its edge is
  mostly market beta (β≈1.1) on the 130/30 net-long book; the "market
  neutral" L/S variant holds β=1.32, i.e. the vol-adjustment accidentally
  concentrates in high-beta names.
- **CTA on the FRED macro panel (Sharpe 0.16, β=0.00) beats CTA on
  equities/FX/crypto (-0.06..-0.14)** — trend following needs genuinely
  uncorrelated cross-asset instruments, monthly rebalance (21d), and the
  yield inversion (long bond = short yield). Monthly is the sweet spot:
  5d/10d rebalance give -0.15/-0.04 (churn), 21d +0.16.
- **Multi-Strategy EW with futures CTA: Sharpe 0.61** (was 0.41 with equity
  CTA): the futures-CTA stream is negatively correlated with L/S (-0.07)
  and stat arb (-0.15), lifting the blend. The multi-strategy thesis —
  low-correlation streams with independent edges — is the suite's strongest
  result, not any single strategy.
- **Fixed Income Arbitrage fails** (Sharpe -3.4, both reversion AND momentum
  z-score variants on 10y-2y/30y-10y): naive curve z-score timing has no
  gross edge on 2008-2026 — inversion periods were trend continuations, and
  FI arb economics are carry/term-premium driven, not z-score driven. Cost
  drag is negligible (0.13%/yr) — the edge itself is negative.
- **CTA window robustness**: Sharpe +0.16 on 2008+ but -0.04 on 2000+
  (2000-2008 subperiod loses): the missing metals complex (gold/copper
  discontinued on FRED — the 2000s supercycle was metals-led) and
  equities/FX trends were mixed. Real futures via Stooq would fill the gap
  when the IP block lifts.
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
- `strat_fi_arb.py` - Relative Value / Fixed Income Arbitrage (curve z-score)
- `strat_cta_futures.py` - CTA on real futures/macro (Stooq/FRED)
- `run_all.py` - master runner + comparison
- `run_extras.py` - stat arb variants + multi-strategy blend (appends)
- `sweep_stat_arb.py` - stat-arb parameter sweep (documents the search)
- `download_data.py` - free data download (Polygon, Alpha Vantage, yfinance)

## Stat-arb tuning exploration (Aug 2026)

Systematic sweep of the relative-value strategy at 6 bps found the baseline
config is already the best: **z-window 60d, entry |z|>1.5, exit |z|<0.5,
semiannual refit, weekly rebalance, gross cap 2.0, basket 80 → Sharpe 0.16,
beta 0.04**. Everything else is worse:
- rebalance slowdown 5→42d (0.16 → −0.06; execution lag kills the edge)
- top-K forced exposure (−0.37..−0.59; forces weak setups)
- slow signals, z-window 120/250d (−0.15..+0.11; edge is short-horizon)
- full-convergence exit z=0 (turnover drops 46x→11x but edge decays faster)
- cooldown after exit (no help)

The binding constraint is cost, not signal: ~46x annual turnover × 6 bps =
2.7%/yr drag vs ~3%/yr gross edge. A materially better stat-arb needs a
genuinely different construction (sector constraints, vol-regime timing,
fundamental legs), not parameter tuning.
