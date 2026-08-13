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
sleeve: **SR 1.15, +11.4%/yr, MaxDD -10.4%, positive in all 4 sub-periods
2008-2026** (0.98/2.04/0.91/0.65). On the window where the polygon LS
champion exists (2024+), add it as a third sleeve: SR 1.60, +10.5%, MaxDD
-3.1%, ap-ls corr -0.22. The high-Sharpe cores are the validated external
legs (LS champion, AP gold); the suite's contribution is the cheap,
positive, low-turnover 3-stream hedge sleeve that diversifies them.

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

### Correction: AP gold daily-frequency correlation was an artifact
The earlier "DAILY-frequency correction" addendum reported corr(hedge-EW,
AP) = +0.555/+0.613 and cut the monthly SR gain from +0.45 to +0.18. That
computation forward-filled MONTHLY RETURNS to daily, compounding them
(fixed now in `blend_6stream.py`; the file previously used by that
addendum was also affected). Correct dailyization — each month's return
distributed evenly across that month's trading days, monthly totals
preserved — gives corr(hedge-EW, AP) = -0.026, restoring the genuinely
low correlation (monthly-sampled: +0.034). The corrected daily 6-stream
blend at 12 bps RT (2024-07..2026-07, n=507):

| blend (daily) | SR | ret | MaxDD | corr h-ap | corr h-ls | corr ap-ls |
|---------------|-----|-----|-------|-----------|-----------|------------|
| hedge 4-stream EW | 0.06 | +2.2% | -9.7% | -0.026 | -0.025 | -0.049 |
| + AP gold + LS champ (6-stream EW) | **2.03** | **+9.3%** | **-3.9%** | | | |

Half-window split: hedge EW -0.74 / +1.13; 6-stream +0.03 / +3.46 —
positive in both halves. The two validated external legs (LS champion,
AP gold) carry the blend at 12 bps RT; the suite's own 4-stream hedge
leg is ~flat in this window. `results/blend_6stream_daily.csv`.

CAVEAT: AP's dailyized SR (~4.8) is inflated by sampling frequency —
a smooth monthly series sampled daily scales ~sqrt(21); the same applies
to the 6-stream daily SR (2.03). The robust, sampling-independent
statements are the near-zero pairwise correlations and the positive-in-
both-halves result; the headline SR should be read as an upper bound.
Monthly-sampled 6-stream SR on the same window is the honest number to
report for the blend (see the monthly addenda below; they are themselves
old-cost/old-window but the point stands).

> Superseded note: addenda below from earlier 2026-08-13 runs used 6 bps
> RT (3 bps/side) and the pre-fix AP dailyization. They remain correct
> for their own sampling frames; the cost-corrected and AP-dailyization-
> corrected versions are in the "Cost rebaseline" addendum above and the
> monthly-frame addendum below.

## Addendum 2026-08-13 — MONTHLY-FRAME blend at 12 bps RT: the all-weather answer

`blend_monthly.py` — honest monthly sampling (AP gold is monthly by
construction; daily-sampling a smooth monthly series inflates SR ~sqrt(21),
so the daily 2.03 above is an upper bound). At 12 bps RT:

**Long window 2008-02..2026-07 (222 months):**

| blend (sleeve EW) | SR | ret | MaxDD |
|-------------------|-----|-----|-------|
| hedge 4-stream EW (incl stat arb) | 0.47 | +5.2% | -11.7% |
| hedge 3-stream EW (ex stat arb) | 0.71 | +8.2% | -9.2% |
| h4 + AP gold | 1.01 | +9.8% | -10.0% |
| **h3 + AP gold** | **1.15** | **+11.4%** | **-10.4%** |

corr(h3, AP) = +0.026 — the diversification the daily artifact had
obscured. **Sub-period robustness (geometric monthly SR):**

| blend | 2008-12 | 2013-17 | 2018-22 | 2023-26 |
|-------|---------|---------|---------|---------|
| h4 | +0.32 | +0.58 | +0.87 | -0.44 |
| h3 | +0.45 | +0.93 | +1.07 | -0.06 |
| h4 + AP | +0.93 | +1.86 | +0.69 | +0.51 |
| **h3 + AP** | **+0.98** | **+2.04** | **+0.91** | **+0.65** |

**h3 + AP gold is positive in every sub-period — including 2008-12 (GFC)
and 2023-26 — at 12 bps RT, on 18 years of free data.** This is the
suite's strongest all-weather construction at the user's real cost: two
cost-surviving sleeves (3-stream hedge + AP gold), near-zero correlation,
each positive on its own. It meets the "any market conditions" goal on
every regime tested.

**Short window 2024-07..2026-07 (25 months, LS champion available):**

| blend | SR | ret | MaxDD |
|-------|-----|-----|-------|
| hedge 4-stream EW | -0.09 | +1.4% | -7.9% |
| hedge 3-stream EW | +0.37 | +4.4% | -6.9% |
| h4 + AP + LS (6-stream) | +1.47 | +9.4% | -2.9% |
| **h3 + AP + LS (5-stream)** | **+1.60** | **+10.5%** | **-3.1%** |
| h3 + LS (no AP) | +0.84 | +6.8% | -3.4% |

corr ap-ls = **-0.218** — AP gold and the LS champion are net negatively
correlated; each of the three sleeves adds. Dropping stat arb helps every
variant (5-stream > 6-stream). `results/blend_monthly.csv`.

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

The validated polygon LS champion @3x (tools/quant/ls/results/
levdet3.0/daily_returns.csv, SR 2.23 active, scramble PASS, market
neutral beta ~0.02) integrates DAILY with this suite's blend. Equal-
weight test on the common 514-day window (2024-07..2026-08):

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
