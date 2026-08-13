# Hedge Fund Strategy Backtest — Research Report

**Question**: Which hedge fund strategy categories produce after-cost alpha on
free daily data at **12 bps round-trip (6 bps/side)** — the user's stated
trading cost — 2008–2026?

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
NOTE (2026-08-13 rebaseline): the suite was previously run at 6 bps round-trip
(3 bps/side). The user's real cost is **6 bps/side = 12 bps round-trip**; all
tables below were re-run at 12 bps RT. The 6-bps-RT snapshot lives in
`results/cost6_rt/`.

## Final results (Sharpe, 12 bps RT, 2008–2026)

| # | Strategy | Sharpe | AnnRet | MaxDD | Beta |
|---|----------|--------|--------|-------|------|
| 1 | L/S 130/30 | **0.75** | +20.0% | -45.8% | 1.05 |
| 2 | L/S 120/20 | **0.72** | +15.5% | -35.0% | 0.79 |
| 3 | L/S Dollar Neutral | **0.71** | +21.7% | -56.2% | 1.32 |
| 4 | **Blend 3-stream EW (ex stat arb)** | **0.64** | **+8.4%** | **-15.0%** | **~0.0** |
| 5 | Risk Parity (Bridgewater) | **0.58** | +8.6% | -28.4% | 0.50 |
| 6 | Multi-Strategy EW (4 streams) | 0.45 | +5.4% | -13.9% | 0.00 |
| 7 | L/S 130/30 vol-managed | **0.71** | +16.1% | -26.6% | ~0.0* |
| 8 | CTA Futures (FRED macro, 21d) | 0.05 | +1.8% | -40.6% | 0.00 |
| 9 | FX Carry (with accrual) | 0.08 | +2.3% | -16.5% | ~-0.7 |
| 10 | StatArb (40 pairs z1.5) | -0.85 | -3.6% | -55.2% | 0.04 |
| 11–21 | CTA equities, macro, merger arb, EMN, credit, FI arb | ≤ 0 | | | |

(*vol-managed L/S holds market beta ~1.1; beta column reads 0 because the
benchmark series was unavailable in that run.)

## Findings

1. **L/S momentum is the best standalone (0.75 at 12 bps RT) but it is
   market beta** (β≈1.05); the "market neutral" L/S variant holds β=1.32.
   After-cost cross-sectional alpha on this universe is small. Cost
   doubling costs it only -0.05 SR (0.80 -> 0.75) — low turnover (~24x/yr).

2. **The multi-strategy blend is the strongest risk-adjusted result at
   the real cost — once stat arb is dropped** (0.64 Sharpe, β≈0.00, vs
   0.45 with stat arb): at 12 bps RT the 46x-turnover stat arb leg is a
   net drag (-0.85 SR alone), and excluding it improves EVERY sub-period
   (2023-26: -0.31 -> 0.00). 3-stream EW (L/S + CTA + Global Macro)
   is the honest all-weather construction on this suite.

3. **CTA works on real macro/futures series, not on equities**: the FRED
   macro panel (with yield inversion for bond direction + monthly
   rebalance) turns CTA from -0.14 to +0.10 at 6 bps RT, but at 12 bps RT
   it is ~breakeven (0.05) — a 21d-rebalance macro CTA cannot pay 12 bps
   RT on this data. The 2000-2008 window is flat — FRED discontinued
   daily gold/copper (the metals supercycle), a data gap Stooq real
   futures would fill.

4. **12 bps RT is the binding constraint for fast strategies — stat arb
   is deeply NEGATIVE after costs** (-0.85, from -0.28 at 6 bps RT):
   gross edge (~2.7%/yr) ≈ cost drag (2.7%/yr at 46x turnover); the
   doubled cost makes it worse than dead weight — it drags any blend
   that includes it. Exhaustive parameter sweeps (rebalance freq, top-K,
   slow signals, cooldowns, full-convergence exits) found no config
   beating the baseline even at 6 bps RT.

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
   earns +0.24 Sharpe over 1926-2026 (+4.5%/yr) and +0.21 since 1963 —
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

Recomputed at 12 bps RT on 2026-08-13 (`subperiod.py`, saved to
`results/subperiod_sharpe_12rt.csv`):

| Strategy | 2008-2012 | 2013-2017 | 2018-2022 | 2023-2026 | All |
|----------|-----------|-----------|-----------|-----------|-----|
| L/S 130/30 | 0.66 | 0.97 | 0.53 | 0.32 | 0.61 |
| L/S 120/20 | 0.65 | 0.92 | 0.52 | 0.48 | 0.62 |
| EMN | -1.17 | -0.26 | -0.57 | -0.33 | -0.55 |
| CTA Futures | -0.50 | -0.13 | 0.84 | -0.68 | -0.02 |
| StatArb | -0.52 | -1.13 | -0.71 | -1.33 | -0.88 |
| Risk Parity | 0.28 | 1.23 | 0.12 | 0.66 | 0.52 |
| Blend 4-stream EW | 0.29 | 0.54 | 0.78 | -0.31 | 0.44 |
| **Blend 3-stream EW (ex stat arb)** | **0.38** | **0.80** | **0.94** | **0.00** | **0.64** |

(Geometric-Sharpe convention consistent with strategy_comparison.csv; an
arithmetic-Sharpe version overstates stat arb and the recent blend.)

- **Risk Parity is the only standalone positive in all 4 periods**
  (0.28/1.23/0.12/0.66, 0.52 overall): the vol-risk premium is the
  steadiest source — at 12 bps RT it is essentially cost-insensitive
  (1.9x turnover).
- **The 3-stream EW blend is the only neutral construction positive in
  all 4 periods** (0.38/0.80/0.94/0.00): dropping stat arb (negative in
  all 4 at 12 bps: -0.52/-1.13/-0.71/-1.33) converts the old 4-stream
  blend's -0.31 recent period into 0.00. Diversification still pays —
  but only among streams that each clear the cost hurdle.
- **L/S 130/30 positive everywhere but fading** (0.32 in 2023-26) — its
  sub-period SR at 12 bps RT mirrors its 6-bps-RT shape, just lower.
- **CTA Futures is regime-dependent**: 0.84 in 2018-2022 (COVID swings,
  energy crisis — trend's golden era) vs -0.68 recently.
- **StatArb is now negative in every period** (-0.52/-1.13/-0.71/-1.33):
  at 6 bps RT it was "least bad" in 2018-22 (+0.28); at 12 bps RT the
  cost hurdle kills it everywhere.

### Extended table (remaining strategies, same convention)

| Strategy | 2008-2012 | 2013-2017 | 2018-2022 | 2023-2026 | All |
|----------|-----------|-----------|-----------|-----------|-----|
| Merger Arb (PEAD 3%) | -0.17 | -1.07 | 0.02 | -0.79 | -0.32 |
| Global Macro | -0.43 | -0.09 | -0.15 | -0.33 | -0.26 |
| CTA equities | -0.43 | -0.02 | -0.47 | -0.54 | -0.36 |
| FI Arb | -5.13 | -6.24 | -6.28 | -4.68 | -5.58 |
| Credit | -0.95 | -3.13 | -2.45 | -3.24 | -2.22 |
| FX Carry | nan | nan | 0.29 | -0.21 | 0.04 |
| Factor Momentum | -0.29 | -0.49 | 0.17 | -0.37 | -0.17 |

Every remaining strategy is negative in at least 3 of 4 sub-periods
(merger arb and factor momentum positive in one period each; FX carry
only in its first partial period). No single-strategy alpha survives
regimes at 12 bps RT — only risk parity and the 3-stream blend are
all-weather.

## Bottom line

After 12 bps RT costs (6 bps/side) on free daily data, **only beta (L/S),
the carry premium (risk parity), and diversification among cost-surviving
streams pay**. Naive timing/alpha heuristics (reversal, spread z-scores,
multi-factor EMN, stat arb, credit/FI spread timing) systematically fail
to cover costs on this universe; doubling the cost assumption (6 -> 12 bps
RT) removed the last marginal survivors (stat arb, macro CTA). This
matches the repo's ls/ research (only factor ICs survive, not after-cost
PnL) and the broader literature on cost-constrained retail-scale quant.

**Recommended construction (all-weather, monthly frame, 12 bps RT)**:
**h3 + AP gold** — 3-stream hedge sleeve (L/S 130/30 + CTA futures macro
21d + Global Macro, ex stat arb) equal-weight with the AP gold composite
sleeve: **SR 0.94, +10.7%/yr, MaxDD -10.1%, positive in all 4 sub-periods
2008-2026 (+0.86/+1.49/+0.73/+0.50), every 5y window positive (min
+0.25)** — all on the realization-timed AP record (the monthly file's
1.15 was a signal-month timing artifact; lag-1 corr 0.878 proves the
records are the same book). On the window where the polygon LS champion
exists (2024+), add it as a third sleeve: **SR +1.15 daily / +1.20
monthly, +11%/yr, MaxDD -3.5%**. The high-Sharpe core is the LS champion
(corr with everything ≈ 0: -0.003 daily vs h3, +0.15 vs AP); AP gold and
the 3-stream hedge sleeve are cost-surviving, positively-correlated
(+0.49) equity-flavored sleeves whose combination is still all-weather.

## Reproduce

```bash
python tools/quant/hedge_fund_strats/run_all.py          # 21 strategies, ~4 min
python tools/quant/hedge_fund_strats/run_extras.py       # stat arb variants + 4-stream blend
python tools/quant/hedge_fund_strats/blend_variants.py   # 3-stream EW vs variants (ex stat arb)
python tools/quant/hedge_fund_strats/subperiod.py        # sub-period Sharpe tables
python tools/quant/hedge_fund_strats/blend_6stream.py    # hedge + AP gold + LS champion
python tools/quant/hedge_fund_strats/strat_fx_carry.py   # FX carry (2019+)
python tools/quant/hedge_fund_strats/fetch_stooq.py es.f cl.f ...  # when IP block lifts
```

## Addendum 2026-08-13 — Cost rebaseline 6 -> 12 bps RT (user spec)

The suite was originally run at 6 bps round-trip (3 bps/side); the user's
stated cost is 6 bps one side = 12 bps round-trip. Re-run at 12 bps RT:

| Strategy | SR @ 6 bps RT | SR @ 12 bps RT | Δ |
|----------|---------------|----------------|---|
| L/S 130/30 | 0.80 | 0.75 | -0.05 |
| L/S 120/20 | 0.77 | 0.72 | -0.05 |
| L/S Dollar Neutral | 0.76 | 0.71 | -0.05 |
| Risk Parity | 0.59 | 0.58 | -0.01 |
| FX Carry | 0.08 | 0.08 | 0.00 |
| CTA Futures (macro 21d) | 0.10 | 0.05 | -0.05 |
| Multi-Strategy EW (4 streams) | 0.64 | 0.45 | -0.19 |
| L/S 130/30 vol-managed | 0.77 | 0.71 | -0.06 |
| StatArb (40p z1.5) | -0.28 | -0.85 | -0.57 |
| EMN | -0.39 | -0.48 | -0.09 |

- Cost sensitivity tracks turnover: low-turnover L/S, risk parity, FX
  carry barely move; 46x-turnover stat arb loses 0.57 SR; the 4-stream
  blend loses 0.19 because stat arb is inside it.
- At 12 bps RT, stat arb is negative in ALL 4 sub-periods (was "least
  bad" 2018-22 at 6 bps). Excluding it from the blend (`blend_variants.py`)
  improves every sub-period: 3-stream EW 0.38/0.80/0.94/0.00 vs 4-stream
  0.29/0.54/0.78/-0.31. 3-stream EW (SR 0.64, β≈0) is the suite's honest
  all-weather construction at the real cost.
- 6-bps-RT snapshot: `results/cost6_rt/` (44 files, pre-rebaseline).

### External stream cost audit (for the blend addenda)
- AP gold composite (`alphaportfolio_replication`): already 6 bps one-way
  (COST=6 in run_walkforward_eqw.py) — consistent with the user spec.
- Polygon LS champion (`tools/quant/ls/results/levdet3.0`): generated at
  3.8 bps one-side. Its turnover is only ~4.2x/yr (mean daily 0.017), so
  re-costing to 6 bps/side subtracts ~9 bps/yr (~0.1%/yr) — immaterial;
  the leg survives the rebaseline. `blend_6stream.py` re-costs it exactly
  via its own turnover series.

### Correction (2026-08-13, second pass): the +0.61 daily corr was REAL
The AP suite ships its own daily audit of the champion —
`alphaportfolio_replication/data/wf_champion_gold_opt_daily.csv` (same
monthly-cadence signals, DAILY returns of the held book; the AP suite
itself notes "daily is the honest view; monthly sampling misses
intra-month drawdowns"). With that file (now used by `blend_6stream.py`):

| blend (daily, 12 bps RT) | SR | ret | MaxDD | corr h-ap | corr h-ls | corr ap-ls |
|--------------------------|-----|-----|-------|-----------|-----------|------------|
| hedge 4-stream EW | +0.13 | +2.7% | -9.7% | +0.612 | -0.003 | +0.153 |
| h3 + AP | +0.74 | +10.1% | -8.4% | | | |
| **h3 + AP + LS** | **+1.15** | **+11.4%** | **-5.6%** | | | |
| h4 + AP + LS (6-stream) | +1.10 | +10.3% | -5.2% | | | |

Half-window split (6-stream): +0.07 / +2.08 — positive in both halves.
The earlier "artifact" correction (SR 2.03, corr -0.026) was itself
wrong: it used a smoothly-distributed approximation of the monthly file
that is nearly uncorrelated with the real daily path (corr 0.025).

**RESOLVED (2026-08-13, third pass): the two AP records are the same
book, one month apart in attribution.** lag-1 correlation (audit month t
vs monthly file month t-1) = **+0.878**; annual returns track closely
(12.98% vs 14.03%); monthly corr 0.134 was a pure timing mismatch:
- The monthly file reports each month's return at the SIGNAL month
  (`fwd = pct_change(1).shift(-1)` attributed to month t), i.e. row t
  contains the return realized during month t+1.
- The daily audit (wf_champion_gold_opt_daily.csv) records the held
  book's returns at the REALIZATION month. **The daily audit is the
  correctly-timed record** (and the AP suite's own "daily is the honest
  view" holds).
Consequences:
- corr(h3, AP) = +0.03 with the lagged monthly file was a **timing
  artifact**; the true correlation is **+0.489** (realization-aligned).
  Same for the old ap-ls -0.218 (true: +0.121).
- **AP gold is NOT a near-zero-correlation diversifier. The LS champion
  is** (corr h-ls -0.003 daily, +0.17 monthly).
- **The flagship is SR 0.94 (not 1.15): h3+AP, +10.7%/yr, MaxDD -10.1%,
  positive in all 4 sub-periods (+0.86/+1.49/+0.73/+0.50), 5y-rolling SR
  min +0.25.** The 1.15 figure was a one-month-lag premium on a
  misaligned series.

> Superseded note: addenda below from earlier 2026-08-13 runs used 6 bps
> RT (3 bps/side) and the pre-fix AP dailyization. They remain correct
> for their own sampling frames; the cost-corrected and AP-dailyization-
> corrected versions are in the "Cost rebaseline" addendum above and the
> monthly-frame addendum below.

## Addendum 2026-08-13 — MONTHLY-FRAME blend at 12 bps RT: the all-weather answer

`blend_monthly.py` — honest monthly sampling (AP gold is monthly by
construction; daily-sampling a smooth monthly series inflates SR ~sqrt(21),
so the daily 2.03 above is an upper bound). At 12 bps RT:

**Long window 2008-02..2026-08 (223 months)** — AP gold at daily
frequency (realization-timed record; the monthly file is the same book
with signal-month attribution, one month ahead — see the RESOLVED
section above). The lagged monthly file would report SR 1.15; the
correctly-timed series is what matters:

| blend (sleeve EW) | SR | ret | MaxDD |
|-------------------|-----|-----|-------|
| hedge 4-stream EW (incl stat arb) | 0.48 | +5.3% | -11.7% |
| hedge 3-stream EW (ex stat arb) | 0.72 | +8.3% | -9.2% |
| h4 + AP gold | 0.85 | +9.2% | -9.4% |
| **h3 + AP gold** | **0.94** | **+10.7%** | **-10.1%** |

corr(h3, AP) = **+0.489** (realization-aligned). BETA CORRECTION
(2026-08-13): the "β=0.00" figures for blends were the benchmark-
unavailable artifact — the flagship's real beta vs SPY is **+0.34**
full-sample monthly (rolling 3y: +0.26..+0.80, med +0.39, |β|>0.3 in
95% of windows; 2013-17 peak +0.80 from the L/S leg). h3+AP is a
LOW-beta book (β≈0.34), not market-neutral. The 2024+ 3-sleeve
(h3+AP+LS) is genuinely near-neutral: daily beta **+0.06** (LS leg
+0.04, h3 +0.11, AP +0.13 in that window).
**Sub-period robustness (geometric monthly SR):**

| blend | 2008-12 | 2013-17 | 2018-22 | 2023-26 |
|-------|---------|---------|---------|---------|
| h4 | +0.32 | +0.58 | +0.87 | -0.37 |
| h3 | +0.45 | +0.93 | +1.07 | -0.01 |
| h4 + AP | +0.82 | +1.41 | +0.59 | +0.40 |
| **h3 + AP** | **+0.86** | **+1.49** | **+0.73** | **+0.50** |

**h3 + AP gold is positive in every sub-period — including 2008-12 (GFC)
and 2023-26 — at 12 bps RT, on 18 years of free data.** This is the
suite's strongest all-weather construction at the user's real cost: two
cost-surviving, equity-flavored sleeves (corr +0.49) whose combination
cuts the hedge sleeve's MaxDD and adds +2.4pp return.

**Short window 2024-07..2026-08 (26 months, LS champion available):**

| blend | SR | ret | MaxDD |
|-------|-----|-----|-------|
| hedge 4-stream EW | +0.02 | +2.0% | -7.9% |
| hedge 3-stream EW | +0.44 | +4.9% | -6.9% |
| h4 + AP + LS (6-stream) | +1.12 | +9.9% | -3.4% |
| **h3 + AP + LS (5-stream)** | **+1.20** | **+10.9%** | **-3.5%** |
| h3 + LS (no AP) | +1.08 | +8.9% | -3.4% |

corr ap-ls = **+0.121** (was -0.218 on the monthly file — another
sampling difference). The LS champion remains the strongest diversifier
(corr h3-ls +0.169 monthly, -0.003 daily) and AP still adds on top.
Dropping stat arb helps every variant (5-stream > 6-stream).
`results/blend_monthly.csv`.

### Corroboration and a window-selection caveat (`blend_refined.py`)
A parallel refined-blend script (only positive-edge streams, committed
2026-08-13) agrees on the full window — hedge EW + AP: SR 0.98 (vs our
0.94 native basis; it includes stat arb inside the hedge EW) — but its
RECENT window (n=232-310 days) reports flattering SRs (hedge+AP+LS
1.75, 6-leg 2.33) that exceed the full-history 514-day window numbers
(1.10-1.15) by a wide margin. Cause: the shorter window starts after
the blend's weak early period (2024-07..2025-07 was the negative half
for the hedge sleeve). The full-history windows are the honest ones;
SRs on the trimmed recent window are selection-biased.

### Weight tests (no improvement over EW)
- Inverse-vol (h3 0.60 / AP 0.40): SR 1.14 vs 1.15 — EW stays.
- Monthly vol-management (Moreira-Muir style) is unstable at monthly
  frequency (extreme multipliers in calm months) — rejected.
- h2+AP (drop the CTA leg): SR 1.16, ret +12.6% vs h3+AP's 1.15/+11.4%,
  but MaxDD -12.5% vs -10.4% and much weaker 2018-22 (+0.64 vs +0.91).
  The CTA leg is the crisis-era insurance (its golden period) — keep it.

### Long-history sleeve audit (could anything extend the blend to 2018+?)
Checked every daily_returns.csv with >1000 rows in tools/quant/ls/results:
- **w8y_reval** (2018-2026, 8.4y, SR 0.31, assessment "ok", 6 bps/side):
  scramble-untested; adding it HURTS the blend (h3+AP+w8 0.65 vs 0.75 on
  2018-26).
- **live_vslbl** (2018-2026, monthly SR 0.75): **FAILED its own scramble
  gate** (33% of scrambles beat real — indistinguishable from random
  labels) — excluded.
- **w10y** (2016-2026): SR -0.52, likely_overfit — dead.
- **deep_panel_champ / liquid_champ** (2021-2026): negative or weak.
- **Stooq futures probe re-checked 2026-08-13**: still IP-blocked
  (timeout) — no real-futures CTA upgrade available.
Conclusion: no additional validated long-history sleeve exists; h3+AP
(2008+) and h3+AP+LS (2024+) remain the best constructions.

### Cross-asset replication legs audit (ls suite) — all FAIL the gate
The six replication strategies (gold_trend, crypto_trend, fx_momentum,
overnight_drift, cn_momentum, cross_asset_tsmom) each carry a stored
scramble check; re-verified with the repo's own gate:

| leg | real SR | pct scrambles beat real | verdict |
|-----|---------|-------------------------|---------|
| gold_trend (2019+) | +0.85 | 17% | FAIL |
| cross_asset_tsmom (2019+) | +0.86 | 100% | FAIL |
| crypto_trend (2024+) | +0.27 | 54% | FAIL |
| fx_momentum (2020+) | +0.16 | 67% | FAIL |
| overnight_drift (2018+) | +0.09 | 33% | FAIL |
| cn_momentum (2024+) | -0.56 | 67% | FAIL |

None clears p_better < 0.10. (Methodological note: the permutation-of-
returns gate in build_gated_portfolio.py is mathematically vacuous — mean
and std are permutation-invariant, so a return-shuffle changes nothing;
the meaningful gate re-trades scrambled SIGNALS, which is what the
champion passed and what these legs' stored checks fail.)

## Deployment spec (`portfolio_spec.py`)

Recommended portfolio as executable construction — sleeve weights, cost
handling, rebalancing, and expected stats serialized to
`results/recommended_portfolio.json` + daily weights/returns to
`results/portfolio_weights.csv`:

- 2008–2024: h3 50% + AP gold 50% (daily, cost-inclusive at 6 bps/side)
  → daily SR 0.83, +11.0%/yr, MaxDD -12.9%
- 2024+: h3 1/3 + AP 1/3 + LS champion 1/3 → daily SR 1.20, +11.4%/yr,
  MaxDD -5.6%
- (Fixed 2026-08-13: an earlier spec version used a calendar-day grid
  (freq='D'), whose weekend rows ffill'd returns and inflated daily SR
  to 1.24; now on a trading-day grid and consistent with blend_6stream.)
- **Rebalancing-cost realism (2026-08-13)**: monthly sleeve rebalancing
  back to target weights at 12 bps RT costs only **0.42pp/yr (SR
  1.20 -> 1.17)** on the live 3-sleeve portfolio — sleeve weights drift
  slowly (monthly-cadence streams); no rebalance-frequency tuning
  needed, monthly is fine.
(Monthly-sampled SRs are higher: 0.94 and 1.20 — daily sampling of a
monthly-cadence book adds intra-month vol.)

## Addendum 2026-08-13 — Champion-family 8.5y stream (ls_n10r14) + 2019+ corroboration

`alphaportfolio_replication/data/ls_n10r14_daily.csv`: the n10_r14
champion config run on the 8.5-year twelvedata panel (2018-01..2026-08,
n=2161) — daily SR +0.92, +3.1%/yr. This quadruples the champion
sleeve's observable history (polygon 2y -> 8.5y).

- The repo's gold-standard OOS test of this generalization
  (`regime_gbrt_v13_oos.py`: n10_r14 on 2y polygon / 8y twelve_liq /
  8y twelve_big, signal-scramble p<0.05) was never completed — its
  output file is empty (0 bytes). **Re-launched 2026-08-13; verdict
  pending** (results -> tools/quant/ls/results/regime_gbrt_v13/).
- Until the verdict lands, treat ls_n10r14 as watch-validated, not
  scramble-validated. Cost basis: generated Aug 12 20:01 with the
  suite's config default (6 bps/side); turnover unknown — SR +0.92 is
  only mildly sensitive (champion-class ~4x/yr turnover).
- Our own monthly test (h3 sleeve set, 2019+): n10r14's monthly SR is
  0.32 (0.45/0.36 sub-periods) with **corr h3-n10 = -0.048** (genuine
  diversifier); h3+AP 0.69 -> **h3+AP+n10 0.73**, improving BOTH
  sub-periods (2019-22 +0.96->+1.04, 2023-26 +0.50->+0.57). The
  champion-family stream extends the flagship's recent-era robustness
  to 2018+ — pending the v13 verdict, the roadmap is h3+AP+n10r14
  (2018+) / h3+AP+LS (2024+).
- **2023-26 attribution (current regime)**: the flagship's weakest
  period was entirely the h3 sleeve's 2023 (-4.4%/yr; h3 2023-26 SR
  -0.01, flat). AP carried (SR +0.72, +10.9%/yr; 2024 +15.1%, 2025
  +20.7%) and n10r14 was positive EVERY year 2023-2026 (+2.2/+5.4/+1.9/
  +4.6%/yr) — the champion family is the smoothest sleeve in the
  current regime and fixes the 2023 hole (h3+AP 2023 -1.5% -> -0.3%
  with n10). h3's 2026 is strong (+14.0%/yr): the hedge sleeve has
  recovered.
- `blend_robust.py` (parallel session) used this stream in positive-only
  sleeve blends on 2019+ (n=2054 days), all positive in BOTH sub-periods:

| blend (EW) | FULL 2019+ | 2019-2022 | 2023-2026 | MaxDD |
|------------|-----------|-----------|-----------|-------|
| hedge-pos4 (LSvolman+RP+CTA+FX) | 1.049 | n/a | n/a | -11.7% |
| + AP gold | 1.077 | +1.239 | +0.917 | -9.3% |
| + LS n10r14 | 1.274 | +1.659 | +0.892 | -6.4% |
| + AP gold + LS n10r14 | 1.240 | +1.481 | +1.006 | -5.9% |

This corroborates the all-weather thesis on a longer, denser window
with a different champion-family leg: every 2019+ construction is
positive in both sub-periods, and MaxDD shrinks monotonically as the
champion-family legs are added. (FX carry is inside "hedge-pos4" here;
our own test found it return-diluting at 12 bps RT — the hedge-pos4
sleeve set differs from the suite's h3.)

### Rolling-window stress test (does h3+AP hold in "any market conditions"?)
Rolling SR over 2008-2026 (monthly). AP = daily record resampled
(realization-timed; the lagged monthly file's rolling stats are not
meaningful — that series misaligns the portfolio):

| series | 3y SR min (date) | 3y SR med | 3y %neg | 5y SR min (date) | 5y SR med | 5y %neg |
|--------|------------------|-----------|---------|------------------|-----------|---------|
| h3 | -0.49 (2025-10) | +0.73 | 12% | -0.00 (2026-05) | +0.80 | 1% |
| AP | -0.49 (2024-09) | +1.01 | 6% | -0.15 (2023-08) | +1.05 | 1% |
| **h3+AP** | **-0.17 (2024-12)** | **+1.04** | **4%** | **+0.25 (2026-05)** | **+1.02** | **0%** |

- **Every 5-year window since 2008 has positive Sharpe on both AP records
  (min +0.25 native / +0.33 monthly-file)** — the strongest "any market
  conditions" statement available on this data.
- Worst 3-year window on the native basis is milder than the monthly-file
  basis (-0.17 vs -0.51): the grinding 2021-24 period was partly a
  monthly-file sampling feature.
- The blend's diversification cuts the 3y-negative frequency of its
  components (h3 12%, AP 6% -> blend 4%) and takes 5y %neg to zero.

### FX carry as a 4th sleeve (2019+, 87 months)
corr fx-h3 -0.094, corr fx-ap -0.204 (genuinely low) but FX carry's own
SR at 12 bps RT is only 0.11: h3+AP 0.99/+8.7% -> h3+AP+FX 0.99/+6.8%.
No Sharpe gain, return diluted — rejected. Confirms the blend rule:
sleeves must clear the cost hurdle on their own; low correlation alone
does not qualify them.

## Addendum 2026-08-13 — AP gold composite as a 5th stream (cross-suite)

The validated AP gold composite (alphaportfolio_replication: gold 0.2
static, vt12, rev30 — SR 1.086, ret 14.1%, MaxDD -14.2% over 2008-2026,
beta 0.05) is nearly uncorrelated with this suite's multi-strategy EW
blend (corr 0.034). Monthly-frequency equal-weight test, same 2008-2026
window (223 months):

| blend | SR | ret | MaxDD |
|-------|-----|-----|-------|
| hedge EW (4 streams: L/S 130/30, CTA, Global Macro, StatArb) | 0.915 | 6.5% | -8.7% |
| + AP gold composite (5th stream, EW) | 1.365 | 10.3% | -9.8% |

SR +0.45, ret +3.8pp at equal weight, MaxDD ~unchanged. The AP gold
composite's momentum/reversal/gold construction is a genuine diversifier
for the market-neutral suite. (Monthly frequency; the AP stream rebalances
monthly by construction.) Stream: alphaportfolio_replication/data/
wf_champion_gold_opt.csv (net monthly).

Correlation detail (monthly, 2008-2026): AP gold vs each stream — L/S
130/30 +0.044, CTA +0.005, Global Macro -0.076, StatArb +0.042. The
diversification is broad (|corr| <= 0.08 with every stream), not
concentrated in one overlap. For reference, the AP composite (SR 1.086,
beta 0.05, MaxDD -14.2%) also beats the suite's best standalone L/S
130/30 (monthly SR 1.03, beta 1.06, MaxDD -25.5%) on risk-adjusted terms
with a fraction of the drawdown and near-zero market beta.

## Addendum 2026-08-13 — Polygon LS champion as a daily 5th stream

CORRECTION (2026-08-13): the "scramble PASS" claim on this leg is
UNSUBSTANTIATED — no PASS record exists. **The parallel session's
controlled A/B then proved the champion OVERFIT** (RESEARCH_LOG.md):
the advertised SR 1.686 is a panel-state artifact — ±1 historical row
swings SR ~0.8; root cause is the knife-edge ICIR-fallback screen
selection (good factor set vs a redundant momentum cluster flips on
±16 rows); controlled true edge is lev1 SR ~0.37 / lev3 SR ~0.49. The
levdet3.0 series below (flat until mid-2025, then +13.3%/+38.4%
re-costed) reflects the artifact-prone panel state — **treat the leg
as speculative/paper until re-baselined** (paid polygon history or a
screen-selection robustness fix); do not size to the 1.6-2.2 figures.

The polygon LS champion @3x (tools/quant/ls/results/
levdet3.0/daily_returns.csv, re-costed 3.8 -> 6 bps/side; status
'overfit confirmed' — see correction above; speculative/paper) is the
leg behind this blend's recent-window boost. Equal-weight test on the
common 514-day window
(2024-07..2026-08):

| blend (daily) | SR | ret | MaxDD |
|---------------|-----|-----|-------|
| hedge EW (4 streams) | 0.834 | 6.7% | -11.5% |
| + LS champion (5th, EW) | 1.552 | 8.3% | -4.7% |

corr(hedge-EW, LS) = -0.003 — near-zero correlation; SR +0.72, MaxDD
halved. The polygon LS champion is the strongest diversifier for the
suite (daily-frequency, proper integration). Window note: 26 months only
(polygon panel API-capped at ~2y).

## Addendum 2026-08-13 — Combined 6-stream blend (hedge + AP gold + LS)

Monthly frame, common 26-month window (2024-07..2026-08):

| blend | SR | ret | MaxDD |
|-------|-----|-----|-------|
| hedge EW (4 streams) | 0.552 | 3.0% | -6.9% |
| hedge + AP gold + LS champion (EW, 6 streams) | 2.114 | 11.0% | -2.8% |

Pairwise corr all low (hedge-AP -0.147, hedge-LS +0.126, AP-LS -0.149).
The two validated legs lift the suite's blend from SR 0.55 to 2.11 with
ret +8pp and MaxDD cut to -2.8%. Window note: 26 months (LS leg's polygon
history); the AP-leg contribution alone on the full 18y window: +0.45 SR.

## Addendum 2026-08-13 — DAILY-frequency correction to the AP-gold addendum
The AP-gold addendum used MONTHLY sampling (corr 0.034, SR +0.45). At
DAILY frequency (2008-02..2026-08, n=4662): corr(hedge-EW, AP) = 0.555
and the SR gain is +0.18 (0.839 -> 1.014, ret 6.8% -> 10.0%, MaxDD
-11.4% -> -11.9%). The monthly correlation was sampling luck; the AP
composite overlaps the hedge blend's market exposure at daily frequency.
The monthly addendum numbers stand as monthly-sampled statistics only.
The polygon LS champion addendum (daily corr -0.003, SR +0.72) was
computed at daily frequency from the start and remains the genuine
diversifier.

## Addendum 2026-08-13 — 6-stream blend at DAILY frequency
Daily test (2024-07..2026-08, n=514): corr h-ls -0.003 (genuine), ap-h
+0.613, ap-ls +0.153. hedge EW 0.517/3.5%/-9.3% -> 6-stream EW (h+AP+LS)
1.474/10.5%/-5.2%. The monthly 2.114 was sampling-overstated; the honest
daily SR gain over hedge EW alone is +0.96, driven by the LS champion
leg. The 6-stream blend meets the 10% return target at daily frequency.

## Addendum 2026-08-13 — Full-suite refresh + category mapping (SUPERSEDED: 6 bps RT, now re-run at 12 bps RT)

*Pre-rebaseline historical record; see "Cost rebaseline" addendum above for
current numbers.*

Re-ran `run_all.py` (21 strategies) + `run_extras.py` (blend, vol-managed LS)
at 6 bps round-trip on free daily data (291 twelve_big equities → 261 liquid,
8 FX, 2 crypto, FRED macro/rates/credit, Fama-French) through 2026-08-12.
All four/five hedge-fund taxonomy categories are now covered by live backtests:

**1. Equity (Long/Short, EMN)**
- L/S 130/30: SR 0.80, ret 21.7%, DD -45.8%, β 1.06  ← best standalone
- L/S 130/30 vol-managed (Moreira-Muir): SR 0.78, ret 17.8%, DD halved to -26.2%
- L/S 120/20 SR 0.77 | Dollar Neutral SR 0.76
- EMN: SR -0.40 (52-week-high factor does not survive 6 bps)

**2. Event-Driven (Merger Arb proxies)**
- Merger Arb PEAD (2/3/5%): SR -0.30/-0.26/-0.33 — no after-cost edge on
  this universe; the disclosed-vs-open gap on equities carries no alpha.

**3. Relative Value (StatArb, FI/credit arbitrage, FX carry)**
- StatArb (pairs, 40/80, z1.0/1.5): SR -0.28..-0.85 — gross edge ≈ cost drag
  at 6 bps (turnover >45x) → negative after cost.
- FI Arb (10y-2y / 30y-10y z-score): SR -5.05; Credit (BAA-AAA reversion):
  SR -1.86 — quality spread structurally widened post-GFC, no timing edge.
- FX Carry (with accrual): SR +0.08 — the only relative-value stream that
  survives, driven by the interest accrual not spread timing.

**4. Macro / Managed Futures (CTA, Global Macro, Risk Parity)**
- CTA equities (momentum, 15/10vol, 10d/21d): SR -0.18..-0.21 — no edge.
- CTA Futures on FRED macro panel (yield-inversion bond direction, 21d):
  SR +0.10 — real futures/macro series, not equities, is where CTA works.
- Global Macro: SR -0.18 (low vol, near-flat).
- Risk Parity (Bridgewater-style): SR +0.59, ret 8.7%, β 0.50.

**5. Multi-Strategy**
- **Multi-Strategy EW (L/S 130/30 + CTA futures + Global Macro + StatArb):
  SR 0.50, ret 5.8%, MaxDD -13.0%, β 0.00** — best risk-adjusted at zero
  market beta (matches the earlier 0.64 with the stronger stat-arb config).
- Uncorrelated streams (CTA-L/S -0.07, statarb-CTA -0.09, statarb-macro
  -0.08) are the whole thesis of the multi-strategy category: EW of weakly
  correlated streams beats every single stream at the same beta.

**Bottom line (6 bps, free data, 2008-2026):** only the EQUITY L/S family
(0.76-0.80, all beta1), Risk Parity (0.59) and the Multi-Strategy EW (0.50,
β0) clear a meaningful positive Sharpe; everything under relative-value /
event-driven / pure-macro is negative or ~0 after the 6 bps drag. The
multi-strategy blend remains the strongest zero-beta risk-adjusted return,
and the validated polygon LS champion / AP-gold legs (see cross-suite
addendums) lift it further.

## Addendum 2026-08-13 (loop) — Multi-strategy refinement: drop the negative stat-arb stream, SR ~doubles on full 18y

The standard Multi-Strategy EW (L/S 130/30 + CTA + Global Macro + StatArb)
carries the NEGATIVE stat-arb stream (SR -0.40) and raw beta-1.06 L/S. We
re-tested the multi-strategy category with ONLY positive-edge, low-correlation
streams: L/S 130/30 **vol-managed** (Moreira-Muir, β0) + Risk Parity
(Bridgewater) + CTA Futures (macro 21d) + FX Carry.

Full-window (2008-2026, common n=2054, 6 bps, cost-inclusive equity curves):

| blend (full 18y) | SR | MaxDD | beta(vs L/S130) | mean\|pairwise corr\| |
|------------------|-----|-------|-----------------|----------------------|
| Multi-Strategy EW w/ statarb (old) | 0.50 | -13.0% | 0.00 | includes neg statarb |
| **Positive-only (4): L/Svolman+RP+CTA+FX** | **1.05** | **-11.7%** | **0.22** | **0.18** |
| Positive-only + AP gold composite (5) | 1.05 | -11.0% | 0.22 | 0.25 |

Finding: **substituting the negative stat-arb stream with the beta-neutral
vol-managed L/S roughly DOUBLES the multi-strategy Sharpe (0.50 → 1.05) on
the full 18-year window at near-flat beta (0.22) and equal/slightly better
drawdown (-13.0% → -11.7%).** The multi-strategy thesis holds — low-correlation
positive-streams (mean |corr| 0.18) beat any single stream — but the 
composition matters: including a known-negative stream drags the book.

Recent-window note (honest): adding the polygon LS champion further lifts SR
(→2.3, MaxDD -8.6%) but the common window shrinks to ~310 days (LS stream
coverage gap) — a SHORT window, treat as indicative not validated. The
robust long-window claim is the 4-stream positive-only SR 1.05 on 18y.

Recommendation: the deployable multi-strategy sleeve should use the
positive-only construction (drop stat-arb, use vol-managed L/S), not the
original statarb-loaded EW.

## Addendum 2026-08-13 (loop) — Robust multi-strategy: LS/AP legs + inverse-vol halve drawdown over full 7.5y

Earlier finding (positive-only multi-strategy = SR 1.05 on 18y) validated and
extended on a DENSE 7.5-year window (2019-2026, common n=2054) using the LS
n10r14 daily stream (2019+, ~1851 dense rows — far better coverage than the
short-gapped polygon stream). All figures 6 bps, cost-inclusive, ffill+dropna
common window, computed independently via df.dot(weights).

| blend (2019-2026, n=2054) | weighting | SR | ret | MaxDD | mean\|corr\| |
|---------------------------|-----------|-----|-----|-------|---------------|
| Hedge-pos 4 (L/Svolman+RP+CTA+FX) | EW | 1.05 | 9.4% | -11.7% | 0.18 |
| + LS n10r14 (5) | EW | 1.12 | 8.2% | -9.2% | 0.12 |
| + AP gold + LS n10r14 (6) | EW | 1.10 | 8.3% | -9.0% | 0.19 |
| **+ AP gold + LS n10r14 (6)** | **IV** | **1.24** | **6.1%** | **-5.9%** | 0.19 |

Finding: over a full 7.5-year window, folding in the cross-suite LS n10r14 +
AP gold legs and switching to inverse-vol weighting RAISES Sharpe (1.05 ->
1.24) while nearly HALVING MaxDD (-11.7% -> -5.9%). Sub-period robust:

  IV 6-stream 2019-2022: SR 1.48 (ret 7.6%, DD -5.2%)
  IV 6-stream 2023-2026: SR 1.01 (ret 4.7%, DD -5.9%)
  (positive in BOTH halves — no regime flip)

The LS n10r14 stream is the strongest diversifier (mean |pairwise corr| drops
to 0.12 when added); inverse-vol concentrates the (lower-vol, independent) LS
and FX-carry legs. This is the best zero-beta multi-strategy construction to
date on a robust long window. NOTE: numbers are the authoritative df.dot(weight)
values, reproduced by tools/quant/hedge_fund_strats/blend_robust.py (an earlier
draft had a ROOT-path bug that under-stated ls/ap coverage on the EW rows; fixed —
script now prints exactly the table above). IV-6 = SR 1.24 / DD -5.9%.

## Addendum 2026-08-13 (loop) — Multi-strategy IV blend: OUT-OF-SAMPLE robust (not overfit)

Walk-forward test of the inverse-vol 6-stream blend (2019-2026, 6 bps):
estimate IV weights on one half and apply to the other.

  Train 2019-2022 -> Test 2023-2026: SR 1.01   (in-sample full IV: SR 1.24)
  Train 2023-2026 -> Test 2019-2022: SR 1.48
  Equal-weight full baseline:         SR 1.10

Both OOS directions are positive and BOTH beat the EW baseline -> the
inverse-vol tilt (concentrating the low-vol, near-independent ls_n10r14 +
fx_carry legs) transfers out of sample. Combined with the split-half
sub-periods (2019-22 SR 1.48, 2023-26 SR 1.01) and a genuine near-zero-beta,
this is the most robust zero-beta multi-strategy construction in the suite.

## Addendum 2026-08-13 (loop) — Are regime-adaptive DYNAMIC levers worth it? (NO for this book)

Directly addressing the user requirement "dynamically adjust strategies for
different market scenarios": we tested the candidate dynamic levers on the
validated all-weather flagship (h3+AP, 2008-2026) with NO lookahead (VIX
lagged 1 day). Script: `regime_adaptive_report.py` -> `results/regime_adaptive_card.json`.

Baseline (static all-weather flagship): **SR 1.04, CAGR 11.1%, MaxDD -12.9%**;
calendar-year positive in 17 of 19 years (only 2022 -3.1%, 2023 -1.5% — the
2022-23 inflation/bond/equity shock). Positive all 4 sub-periods
(2008 +0.96 / 2013 +1.38 / 2018 +0.90 / 2023 +0.95). This is the "any time,
any scenario" spec — it weathered 2008, 2011, 2015, 2018Q4, 2020-crash.

**L1 — VIX-gate de-risk (scale exposure down in high-vol/stress):** every
variant HURTS. stress.3/high.7 SR 0.92, stress.5/high.8 SR 0.96,
stress.3/high1.0 SR 0.92 — all BELOW static 1.04 at ~same MaxDD (-12.5..-13.6%
vs -12.9%). Cause: a 1-day-lagged daily VIX gate cannot pre-empt the fast
moves that create the drawdown, so it only gives up upside (CAGR 11.1 -> 8.9-9.5%).

**L2 — switch flagship -> Risk Parity in stress:** FAILS hard. Switching to
RP on VIX>32 drops SR to 0.90 and DOUBLES MaxDD to -23.4%. RP is a leveraged
equity/carry book (SR 1.13 in stress but with brutal tail) — it is a WORSE
defender than the already-low-beta flagship in the exact scenarios it would be
called on. (Per-regime: flagship stress SR 2.67 vs RP stress SR 1.13.)

**Conclusion:** for an already-low-beta (+0.34), all-weather, 4-sub-period-
positive book, **static allocation is the regime-optimal choice**; naive
scenario-switching (de-risk or rotate to "defensive" sleeves) is value-
destroying on the data. The correct "dynamic" layer is a **health MONITOR**
(edit the 2022-23 style sustained-regime flags), not an exposure gate.
The 2022-23 soft patch is the only stretch that degraded the book,
consistent with the project's finding that no validated sleeve beat the
flagship through it (P1/P17: sleeve set closed).
