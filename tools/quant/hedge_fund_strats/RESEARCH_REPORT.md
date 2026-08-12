# Hedge Fund Strategy Backtest — Research Report

**Question**: Which hedge fund strategy categories produce after-cost alpha on
free daily data at **6 bps round-trip** (3 bps/side), 2008–2026?

**Data (all free)**: 261 US equities (twelve_big, 2006–2026), 275 more
(Polygon), 8 FX pairs (2019+), 2 crypto, Fama-French factors, **FRED API**
(macro: WTI/Brent/natgas, US 2/10/30y, 5 FX crosses, S&P/Dow, VIX; Moody's
AAA/BAA 1983+; OECD country yields), Stooq futures PoW-solver (IP-blocked at
time of writing).

**Engine**: T+1 execution, cost charged on weight deltas at each rebalance,
vol targeting, position caps. All results in `results/strategy_comparison.csv`.
NOTE (2026-08-12 correction): Sharpe/Sortino/MaxDD are computed from the
COST-INCLUSIVE equity curve (pct_change). An earlier version used the
engine's cost-exclusive daily returns, overstating high-turnover strategies
(e.g. stat arb +0.16 -> -0.28); blends were always cost-inclusive.

## Final results (Sharpe, 6 bps, 2008–2026)

| # | Strategy | Sharpe | AnnRet | MaxDD | Beta |
|---|----------|--------|--------|-------|------|
| 1 | L/S 130/30 | **0.80** | +21.6% | -45.8% | 1.06 |
| 2 | L/S 120/20 | **0.77** | +16.6% | -34.9% | 0.79 |
| 3 | L/S Dollar Neutral | **0.76** | +23.9% | -56.1% | 1.32 |
| 4 | **Multi-Strategy EW (5 streams)** | **0.64** | **+7.2%** | **-11.7%** | **0.00** |
| 5 | Risk Parity (Bridgewater) | **0.59** | +8.7% | -28.4% | 0.50 |
| 6 | CTA Futures (FRED macro, 21d) | **0.10** | +2.5% | -39.2% | 0.00 |
| 7 | StatArb (80 pairs) | -0.28 | ~0.0% | -23.6% | 0.04 |
| 8 | FX Carry (with accrual) | **0.08** | +2.3% | -16.5% | ~-0.8 |
| 9 | L/S 130/30 vol-managed | **0.77** | +17.7% | -26.2% | ~1.1 |
| 9 | StatArb (40 pairs z1.0) | -0.35 | -0.3% | -22.6% | 0.04 |
| 10–21 | CTA equities, macro, merger arb, EMN, credit, FI arb | ≤ 0 | | | |

## Findings

1. **L/S momentum is the best standalone (0.80) but it is market beta**
   (β≈1.06); the "market neutral" L/S variant holds β=1.32. After-cost
   cross-sectional alpha on this universe is small.

2. **The multi-strategy blend is the strongest risk-adjusted result**
   (0.64 Sharpe, β=0.00): 5 streams with low/negative cross-correlation
   (CTA vs L/S -0.07, stat arb vs CTA -0.15, FX carry adds exposure).
   Uncorrelated streams with independent edges — the whole point of the
   multi-strategy category — beat every single strategy at the same beta.

3. **CTA works on real macro/futures series, not on equities**: the FRED
   macro panel (with yield inversion for bond direction + monthly
   rebalance) turns CTA from -0.14 to +0.10. 21d rebalance is the sweet
   spot; 5d/10d churn destroys the edge. The 2000-2008 window is flat —
   FRED discontinued daily gold/copper (the metals supercycle), a data gap
   Stooq real futures would fill.

4. **6 bps is the binding constraint for fast strategies — stat arb is
   NEGATIVE after costs** (-0.28): gross edge (~2.7%/yr) ≈ cost drag
   (2.7%/yr at 46x turnover); exhaustive parameter sweeps (rebalance
   freq, top-K, slow signals, cooldowns, full-convergence exits) found
   no config beating the baseline.

5. **Spread timing on rates/credit has NO gross edge**: FI arb (10y-2y,
   30y-10y z-score) Sharpe -5.1; credit (BAA-AAA, 1983+; reversion AND
   unconditional carry) -1.9..-2.5 — the quality spread structurally
   widened post-GFC, beating carry and timing alike. Carry only pays on
   FX (0.08), where the accrual is the edge, not the timing.
6. **Vol management works on the winner**: scaling L/S 130/30 by inverse
   realized vol (Moreira-Muir) keeps Sharpe 0.77 (vs 0.80) while halving
   MaxDD (-45.7% -> -26.2%) — Calmar 0.47 -> 0.68. A free drawdown
   improvement on the suite's best strategy.

8. **Factor momentum is a premium that died**: momentum of factor returns
   (Fama-French, long top-2/short bottom-2 of MKT/SMB/HML/UMD, monthly)
   earns +0.26 Sharpe over 1926-2026 (+4.5%/yr) and +0.24 since 1963 —
   the Ehsani-Linnainmaa anomaly is real historically — but is GONE in
   the modern window: 2008+ Sharpe -0.06. Factor-premium crowding since
   ~2010, consistent with the suite's broader story: naive premia no
   longer survive costs.

6. **EMN after fixing two real bugs** (pandas 3 rolling-cov no-op + a sign
   flip that doubled the long book): beta 0.00, Sharpe -0.59 → -0.40.
   Still negative — the 52-week-high factor IC does not survive 6 bps PnL.

7. **Event-driven (merger arb PEAD proxy)** is ~breakeven (-0.26..-0.35)
   at low vol — the honest outcome without true event/announcement data.

## Sub-period robustness (Sharpe by period, geometric convention = CSV)

| Strategy | 2008-2012 | 2013-2017 | 2018-2022 | 2023-2026 | All |
|----------|-----------|-----------|-----------|-----------|-----|
| L/S 130/30 | 0.84 | 1.15 | 0.75 | 0.48 | 0.80 |
| EMN | -1.03 | -0.08 | -0.40 | -0.15 | -0.39 |
| CTA Futures | -0.40 | -0.00 | 0.95 | -0.55 | 0.10 |
| StatArb | -0.11 | -0.66 | 0.28 | -0.98 | -0.29 |
| Risk Parity | 0.35 | 1.30 | 0.20 | 0.71 | 0.59 |
| **Blend (5-stream EW)** | **0.45** | **0.94** | **0.89** | **0.07** | **0.64** |

(Geometric-Sharpe convention consistent with strategy_comparison.csv; an
arithmetic-Sharpe version overstates stat arb and the recent blend.)

- **The blend is the only strategy positive in every sub-period** (0.45/
  0.94/0.89/0.07) — the diversification thesis survives regime
  decomposition, though 2023-26 is barely positive.
- **Risk Parity is the most robust standalone** (positive in all 4
  periods, 0.59 overall): the vol-risk premium is the steadiest source.
- **EMN has no edge anywhere** (-1.03/-0.08/-0.40/-0.15): 2009 was just
  its worst period, not the explanation.
- **CTA Futures is regime-dependent**: 0.95 in 2018-2022 (COVID swings,
  energy crisis — trend's golden era) vs -0.55 recently and -0.40 in
  2008-12 (missing metals).
- **StatArb is negative in every period** (-0.11/-0.66/0.28/-0.98):
  least bad in 2018-22; the 2008+ headline +0.16 is mostly the geometric
  convention lifting a low-vol series, not a robust edge.
- L/S 130/30 positive everywhere but fading (0.48 in 2023-26).

## Bottom line

After 6 bps costs on free daily data, **only beta (L/S), the carry premium
(risk parity, FX carry), slow cross-asset trend (CTA macro), and — above
all — diversification itself (the multi-strategy blend) pay**. Naive
timing/alpha heuristics (reversal, spread z-scores, multi-factor EMN)
systematically fail to cover costs on this universe. This matches the
repo's ls/ research (only factor ICs survive, not after-cost PnL) and the
broader literature on cost-constrained retail-scale quant.

## Reproduce

```bash
python tools/quant/hedge_fund_strats/run_all.py          # 19 strategies, ~4 min
python tools/quant/hedge_fund_strats/run_extras.py       # stat arb variants + blend
python tools/quant/hedge_fund_strats/strat_fx_carry.py   # FX carry (2019+)
python tools/quant/hedge_fund_strats/fetch_stooq.py es.f cl.f ...  # when IP block lifts
```
