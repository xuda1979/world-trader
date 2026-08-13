# Hedge Fund Strategy Backtest Framework

Backtests all **four/five hedge fund strategy categories** on REAL daily price
data with **12 bps round-trip trading cost** (6 bps per side, user spec;
rebaselined 2026-08-13 — the old 6 bps RT / 3 bps per side snapshot lives in
`results/cost6_rt/`).

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
- **US equities**: 261 names with 16+ years of daily OHLCV (twelve_big,
  2006-2026) form the 2008+ backtest universe (min-history filter 1000d).
  351 additional names (Polygon API, ~2y history, 2024+) can't join an
  18-year panel (>50% NaN), but matter where their history exists: L/S
  on 2024+ with the 585-name cross-section runs Sharpe 0.79 vs 0.27 on
  the 261-name book — cross-sectional breadth nearly triples the Sharpe
  in the recent window. EMN also gains modestly (0.13 -> 0.19 on 2024+,
  and is POSITIVE in the recent window vs -0.32 on 2008+) while stat arb
  DEGRADES (-0.08 -> -0.65: more pair candidates = more spurious
  selections). Breadth helps ranking-based strategies, not selection-based
  ones.
- **8 FX pairs** (EUR/USD, USD/JPY, etc., 2019+)
- **2 crypto** (BTC, ETH, 2023+)
- **27 Chinese stocks** (cn/, 1.7y history only — 2024-12+; excluded from
  backtests: below the suite's 500-day minimum, results would be noise)
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
- **12 bps round-trip cost (6 bps/side)**: charged on weight deltas at each rebalance
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

## Results Summary (2008-2026, 12 bps RT cost)
See `results/strategy_comparison.csv` for full metrics.

| Strategy | Ann Ret | Ann Vol | Sharpe | Max DD | Beta |
|----------|---------|---------|--------|--------|------|
| L/S 130/30 | +20.0% | 26.5% | **0.75** | -45.8% | 1.05 |
| L/S 120/20 | +15.5% | 19.9% | **0.72** | -35.0% | 0.79 |
| L/S Dollar Neutral | +21.7% | 32.5% | **0.71** | -56.2% | 1.32 |
| L/S 130/30 vol-managed | +16.1% | 21.5% | **0.71** | -26.6% | ~1.1 |
| Risk Parity (Bridgewater) | +8.6% | 12.0% | **0.58** | -28.4% | 0.50 |
| **Blend 3-stream EW (ex stat arb)** | **+8.4%** | **8.3%** | **0.64** | **-15.0%** | **~0.0** |
| Multi-Strategy EW (4 streams) | +5.4% | 8.3% | 0.45 | -13.9% | 0.00 |
| CTA Futures (FRED macro, 21d) | +1.8% | 12.5% | 0.05 | -40.6% | 0.00 |
| StatArb 80 pairs | -2.7% | 6.2% | -0.73 | -46.3% | 0.04 |
| FX Carry (with accrual) | +2.3% | 7.7% | 0.08 | -16.5% | ~-0.7 |
| FI Arb (curve z-score) | -2.6% | 0.6% | -5.58 | -38.9% | 0.00 |
| Credit (spread z reversion) | -0.6% | 1.1% | -2.21 | -15.6% | 0.00 |
| Global Macro | +0.8% | 4.7% | -0.23 | -10.7% | 0.08 |
| Merger Arb PEAD | +0.9-1.1% | 2.6-2.9% | -0.31 to -0.39 | -8% | ~0.01 |
| EMN (beta-neutral) | -6.6% | 15.8% | -0.48 | -73.7% | -0.04 |
| StatArb 40 pairs z1.5 | -3.6% | 5.9% | -0.85 | -55.2% | 0.04 |

**Honest findings (after 12 bps RT costs, 6 bps/side):**
- **L/S momentum (Sharpe 0.75) is the best standalone** — but its edge is
  mostly market beta (β≈1.05) on the 130/30 net-long book; the "market
  neutral" L/S variant holds β=1.32, i.e. the vol-adjustment accidentally
  concentrates in high-beta names.
- **CTA on the FRED macro panel (Sharpe 0.10, β=0.00) beats CTA on
  equities/FX/crypto (-0.18..-0.21)** — trend following needs genuinely
  uncorrelated cross-asset instruments, monthly rebalance (21d), and the
  yield inversion (long bond = short yield). Monthly is the sweet spot:
  5d/10d rebalance churn, 21d +0.10.
- **Multi-Strategy EW with futures CTA: Sharpe 0.64** (was 0.41 with equity
  CTA): the futures-CTA stream is negatively correlated with L/S (-0.07)
  and stat arb (-0.15), lifting the blend. The multi-strategy thesis —
  low-correlation streams with independent edges — is the suite's strongest
  result, not any single strategy.
- **Fixed Income Arbitrage fails** (Sharpe -3.4, both reversion AND momentum
  z-score variants on 10y-2y/30y-10y): naive curve z-score timing has no
  gross edge on 2008-2026 — inversion periods were trend continuations, and
  FI arb economics are carry/term-premium driven, not z-score driven. Cost
  drag is negligible (0.13%/yr) — the edge itself is negative.
- **Credit Strategies fail too** (Sharpe -1.0..-2.5): z-score timing of the
  BAA-AAA / BAA-10y spreads (Moody's, 1983+) and even unconditional credit
  carry (Sharpe -1.0, +0.6%/yr vs -9.8% MaxDD) — the quality spread
  structurally WIDENED post-GFC, so long-credit timing lost more than carry
  earned. Both windows (1986+, 2008+) negative. Consistent with the FI arb
  finding: spread timing on yields/credit has no naive edge; carry is real
  but spread-level risk dominates at this sizing.
- **CTA window robustness**: Sharpe +0.16 on 2008+ but -0.04 on 2000+
  (2000-2008 subperiod loses): the missing metals complex (gold/copper
  discontinued on FRED — the 2000s supercycle was metals-led) and
  equities/FX trends were mixed. Real futures via Stooq would fill the gap
  when the IP block lifts.
- **FX Carry (ARP, Sharpe 0.08)**: long top-3 / short bottom-3 currency pairs
  by yield differential (FRED OECD country yields + daily DGS10 for USD),
  monthly rebalance, 2019+ window. Spot-only P&L is ~zero (-0.18) — the
  edge IS the carry accrual (+2.3%/yr with the rate differential accrued
  daily). Honest caveat: the window contains two carry crashes (2020 COVID,
  2022 USD surge); 3.5x turnover means costs are negligible.
- **Vol-managed L/S (Moreira-Muir, Sharpe 0.77)**: scaling the 130/30 book
  by min(20%/21d realized vol, 2x) using t-1 info trades a little Sharpe
  (0.85 -> 0.77) for HALF the drawdown (MaxDD -45.7% -> -26.2%, Calmar
  0.47 -> 0.68) — the classic volatility-management result.
- **Data-collision lesson**: a monthly OECD yield file accidentally written
  over the daily DGS10 silently degraded CTA Futures (0.16 -> -0.10), FI
  arb and credit — the FRED loader now rejects <500-row files.
- **Blend construction matters**: Sharpe-weighted allocation (weights ~
  full-sample Sharpe, floor 0.05) gives 0.73 Sharpe / +12.5%/yr vs 0.64 EW
  — but the weights are IN-SAMPLE (selection bias; EW is the honest
  out-of-sample choice). The Sharpe-weighted blend also has the better
  regime profile (sub-period Sharples 0.84/1.31/0.81/0.56 vs EW5
  0.69/1.23/1.09/0.35 — best in 3 of 4 periods incl. the weak 2023-26).
  Inverse-vol/var weighting is worse (0.27/-0.07): the low-vol streams
  (macro, stat arb) have LOW Sharpe, so de-weighting L/S hurts. Dropping
  the two weakest streams (macro, FX carry) also helps (best-4 EW: 0.67).
  Vol-managed L/S IN the blend does NOT help (0.30 vs 0.35 recent) — the
  lower-return stream dilutes the book despite its better drawdown.
- **Factor Momentum (Fama-French, Ehsani-Linnainmaa) — a premium that
  died**: momentum of factor returns (long top-2 / short bottom-2 of
  MKT/SMB/HML/UMD by trailing 12m, monthly) is a real century-long
  anomaly — 1926+: Sharpe +0.26, +4.5%/yr; 1963+: +0.24 — but is
  GONE post-GFC: 2008+ Sharpe -0.04. Consistent with factor-premium
  crowding since ~2010. Uses the FF daily factors (1926-2026) that no
  other suite strategy traded.
- **Crypto trend-following loses (2023-2026, 2.8y)**: the multi-timeframe
  CTA machinery on BTC+ETH gives Sharpe -0.10 (21d) to -0.33 (5d) at 6 bps
  vs BTC buy-and-hold +0.62 — trend-following on two hyper-volatile assets
  whipsaws and churns; with only 2 instruments there is no breadth to
  diversify. Buy-and-hold dominates on a single asset class.
- **Global Macro's weakness is construction, not universe**: moving the
  strategy to the FRED macro panel changes nothing (-0.12 -> -0.10), and
  switching to inverse-vol weighting helps only marginally (-0.04 at 26%
  vol). The fatal flaw is cross-sectional momentum RANKING across
  heterogeneous instruments (ranking crude's 30% vol against a yield's 1%
  vol is meaningless) plus the noisy vol-regime gate. The CTA construction
  (multi-timeframe trend, inverse-vol, vol-target) on the SAME panel is
  the superior macro implementation (+0.16).
- **EMN beta-neutralization fixed** (was a silent no-op): pandas 3.x
  DataFrame.rolling().cov(Series) returns all-NaN, so `beta_neutralize`
  never changed weights (β stayed -0.37 on the 'neutral' book); also fixed
  a sign-flip that doubled the long book when betas were negative. With the
  vectorized numpy beta + sign fix: portfolio β ≈ 0.00-0.03 and EMN
  improves -0.59 -> -0.32 Sharpe (2008+), MaxDD -90% -> -62%. Still
  negative: the 52-week-high factor's alpha does not survive 6 bps costs in
  this construction (consistent with the repo's ls/ research: reversal and
  multi-factor composites fail; only the factor IC is positive, not
  after-cost PnL).
- **Statistical arbitrage does NOT survive the real cost** (Sharpe -0.73
  to -0.85 at 12 bps RT; -0.28 at the old 6 bps RT): gross edge (~2.7%/yr)
  is less than the cost drag (46-49x annual turnover × 12 bps ≈ 5.6%/yr).
  At 12 bps RT it is negative in ALL four sub-periods, so it drags any
  blend that includes it — the classic 4-stream EW blend loses 0.19 SR
  versus dropping it.
- **Risk Parity (0.58 Sharpe, β=0.50) beats raw macro**: inverse-vol allocation
  across uncorrelated asset classes captures the vol risk premium with far
  lower cost drag (1.9x turnover); at 12 bps RT it is the only standalone
  positive in all 4 sub-periods.
- **CTA and EMN fail after cost** — trend signals on equity names are too
  noisy/costly; naive multi-factor EMN composites have no stable after-cost
  edge on this universe (consistent with the repo's ls/ research: only
  single-factor 52-week-high distance survives, at +0.34 gross).
- **Blend 3-stream EW (Sharpe 0.64, β≈0.00) demonstrates the core HF thesis
  at the real cost**: L/S + CTA + Global Macro, each individually marginal
  after 12 bps RT, combine to a positive-Sharpe, near-market-neutral book
  that is positive/flat in all 4 sub-periods (0.38/0.80/0.94/0.00). The
  lesson sharpened by the cost rebaseline: diversify among streams that
  each clear the cost hurdle — marginal losers (stat arb at 46x turnover)
  are blend poison, not blend fertilizer.
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
- `strat_credit.py` - Credit Strategies (spread z reversion + carry variants)
- `strat_fx_carry.py` - Alternative Risk Premia / FX carry (with accrual)
- `strat_cta_futures.py` - CTA on real futures/macro (Stooq/FRED)
- `run_all.py` - master runner + comparison
- `run_extras.py` - stat arb variants + multi-strategy blend (appends)
- `sweep_stat_arb.py` - stat-arb parameter sweep (documents the search)
- `download_data.py` - free data download (Polygon, Alpha Vantage, yfinance)

## Stat-arb tuning exploration (Aug 2026)

Systematic sweep of the relative-value strategy at 6 bps found the baseline
config is already the best: **z-window 60d, entry |z|>1.5, exit |z|<0.5,
semiannual refit, weekly rebalance, gross cap 2.0, basket 80 → Sharpe -0.28
after costs (beta 0.04)**. Everything else is worse:
- rebalance slowdown 5→42d (−0.28 → −0.40; execution lag kills the edge)
- top-K forced exposure (−0.37..−0.59; forces weak setups)
- slow signals, z-window 120/250d (−0.15..+0.11; edge is short-horizon)
- full-convergence exit z=0 (turnover drops 46x→11x but edge decays faster)
- cooldown after exit (no help)

The binding constraint is cost, not signal: ~46x annual turnover × 6 bps =
2.7%/yr drag vs ~2.7%/yr gross edge — the after-cost result is NEGATIVE
(-0.28). A materially better stat-arb needs a
genuinely different construction (sector constraints, vol-regime timing,
fundamental legs), not parameter tuning.
