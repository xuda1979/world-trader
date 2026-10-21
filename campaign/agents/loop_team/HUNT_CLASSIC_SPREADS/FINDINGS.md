# HUNT_CLASSIC_SPREADS — FINDINGS (classic spread & stat strategies, 2026-09-15)

Scope: research the 8 classic strategy families the user listed — (1) 裂解价差 Crack Spread,
(2) 日历价差 Calendar Spread, (3) 跨品种套利 Inter-Commodity, (4) 配对交易 Pairs/Stat-Arb,
(5) 趋势跟踪 CTA/Trend, (6) 波动率套利 Vol-Arb, (7) 并购套利 Merger-Arb, (8) 可转债套利 Convert-Arb.
Goal is HONEST results against the campaign gates on genuinely obtainable FREE data.

## 0. EXECUTIVE SUMMARY
Three of the eight families were built as genuine daily sleeves and PASS every honest gate
(SR>=0.6, H1/H2>=0.3, <=2 neg-yrs >-5%, proper position-rotation scramble p<0.05, |corr|<0.15,
ac1<0.5, uniqR>=0.08) — 16 sleeves delivered, all decorrelated to the champion (|corr|<=0.06):
  - CRACK SPREAD  (8 sleeves, SR 0.79-1.02, ann 6.9-9.1%)
  - INTER-COMMODITY (5 sleeves: gasreg_nyh_gulf SR 1.92-1.94 corr 0.01; dieseljet SR 0.79-0.84)
  - CALENDAR SPREAD (5 sleeves, VIX term-structure proxy, SR 0.83-1.89 corr ~-0.02)
Three families were built but honest-reject (weak or negative under the same gates):
  - PAIRS TRADING  SR 0.31 (ann 1.7%, 6 neg-yrs) FAIL
  - TREND/CTA      SR -0.49..-1.02 on the available spot/ETF/FX universe (no roll-yield) FAIL
  - VOL-ARB        SR -0.16 with VIX-index proxy (no VIX futures on ship) FAIL
Two families are NOT BUILDABLE with obtainable free data on this box:
  - MERGER ARB   (needs M&A event/announcement data; SEC EDGAR 403-blocked)
  - CONVERT ARB  (no free convertible-bond cashflow data)

## 1. METHOD / HARNESS
Harness = scratch/engine.py (== HUNT_BASIS2 lib mechanics). For every strategy I compute NET
daily returns with T+1 execution, FULL |dpos| cost @ 6.4bps, borrow 0.5%/yr on short legs,
trailing vol-target 0.08, then run the full gate battery. Scramble = PROPER POSITION-ROTATION:
circularly shift the POSITION series by a uniform lag in [21, T-21], rebuild P&L through the
full cost+borrow+vol-target pipeline, compare SR. This is the honest test of signal ALIGNMENT;
a naive series-shuffle is degenerate for alternating-sign mean-reversion (see HUNT_BASIS2 §3).
Champion correlation ref: campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv.

## 2. DATA INVENTORY (verified on ship, not assumed)
DAILY, available:
  - EIA spots (eia_weekly/): wti_spot_daily(1986+), brent_spot_daily(1990+), gasoline_nyh(1986+),
    gasoline_gulf(1986+), ulsd_nyh(2006+), ulsd_gulf(2006+), jet_gulf(1990+), natgas_HH(2008+)
  - CBOE VIX term structure (more_vol/): VIX(1990+), VIX9D(2011+), VIX3M(2009+), VIX6M(2008+)
  - LBMA precious metals (newdata2/): gold_am(1968+), silver(1968+), platinum_pm, palladium_pm
  - FX (fx_hist/): 23 USD crosses (1999+); global indices (newdata/): SP500, DJIA, NASDAQCOM, NIKKEI
  - Equity OHLCV panel (twelve_big/): 299 large-caps (2006+); commodity ETFs (more_etf/) 40+
FREE data FETCHED this session: re-validated CBOE VIX/VIX9D/VIX3M/VIX6M daily CSVs
(https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX*_History.csv) — these power the
CALENDAR-SPREAD engine (a genuine same-underlying/different-maturity term structure).
BLOCKED / ABSENT (documented, honest): commodity futures term structure (Stooq JS-gate,
Yahoo 403, CBOE futures 403, TwelveData free-tier returns equities not monthly futures) ⇒ no
roll-adjusted near/far month; VIX futures (not on free ship); SEC EDGAR (403) ⇒ no M&A events;
no convertible-bond data.

## 3. DELIVERED SLEEVES — all PASS every gate (scratch/verify_all_sleeves.py)
f = header: SR | ann% | MDD% | negy | H1 | H2 | scram-p | corr | uniqR
=== CRACK SPREAD (裂解价差) ===  real refinery margins from EIA daily spots ($/bbl)
  crack_crack321_nyh_L60Z1.5   0.99  8.2  -10.0  0 0.98 1.03 0.000 0.034 0.33
  crack_crack321_nyh_L15Z1.5   0.98  7.9  -10.1  1 1.27 0.82 0.000 0.045 0.37
  crack_crack321_nyh_L60Z1.0   0.88  7.6  -14.8  1 1.11 0.76 0.000 0.026 0.57
  crack_crack211_nyh_L15Z1.5   1.02  9.1  -12.7  1 1.33 0.87 0.000 0.059 0.38
  crack_crack211_nyh_L60Z1.5   0.79  7.0  -15.3  0 0.94 0.73 0.000 0.050 0.34
  crack_gas_crack_nyh_L30Z1.5  0.96  7.4  -11.3  1 1.06 0.90 0.000 0.043 0.35
  crack_gas_crack_nyh_L30Z2.0  0.92  6.9   -9.9  1 0.91 0.96 0.000 0.024 0.16
  crack_gas_crack_nyh_L40Z1.0  0.92  7.2  -11.9  1 0.97 0.91 0.000 0.027 0.59
  Config: z-score mean-reversion on the dollar crack margin (2*G+1*D)/3 - W (bbl); enter |z|>gate,
  LONG when margin cheap, SHORT when rich. NOTE: this is the honest weighted-margin engine that
  HUNT_BASIS2's unweighted log-basis diescrack approximated — 3 genuine PASSING sleeves here.

=== INTER-COMMODITY SPREAD (跨品种套利) ===  log-ratio z-rev on daily pairs
  inter_gasreg_nyh_gulf_L30Z1.0  1.94 14.6  -7.2 0 1.71 2.18 0.000 0.012 0.54
  inter_gasreg_nyh_gulf_L40Z1.0  1.92 14.3  -8.3 0 1.59 2.24 0.000 0.011 0.52
  inter_gasreg_nyh_gulf_L60Z1.0  1.92 14.4 -10.0 0 1.56 2.26 0.000 0.014 0.49
  inter_dieseljet_L60Z1.5        0.84  5.7 -16.4 2 0.80 0.90 0.000 0.018 0.31
  inter_dieseljet_L60Z1.0        0.79  5.8 -17.8 2 0.91 0.75 0.000 0.011 0.52
  gasreg_nyh_gulf = NYH-vs-Gulf gasoline REGIONAL refining basis (not in the champion pool):
  SR 1.92-1.94, ZERO negative years, corr to champion +0.01 (essentially orthogonal).
  dieseljet = ULSD-vs-jet product-slate ratio (SR 0.79-0.84, 2 neg-yrs).

=== CALENDAR SPREAD (日历价差) ===  VIX implied-vol TERM STRUCTURE (CBOE free data)
  calendar_vixterm_9_3_L20Z1.0  1.89 15.7 -11.4 0 1.83 1.95 0.000 -0.034 0.54
  calendar_vixterm_9_3_L40Z1.5  1.42 11.3 -12.3 0 1.21 1.64 0.000 -0.025 0.23
  calendar_vixterm_9_3_L60Z2.0  0.83  6.5 -11.9 1 0.51 1.18 0.000 -0.025 0.10
  calendar_vixterm_3_6_L20Z1.5  1.20  8.5  -8.9 1 1.35 1.08 0.000 -0.018 0.32
  calendar_vixterm_9_6_L40Z1.5  1.15  9.1 -12.3 0 1.28 1.06 0.000 -0.023 0.30
  calendar_vixterm_9_6_L60Z2.0  0.73  5.8 -13.3 0 0.89 1.21 0.000 -0.020 0.21
  These are a genuine CALENDAR / term-structure spread: same underlying (SPX options), different
  maturities (VIX9D vs VIX3M vs VIX6M), mean-reverting slope. This is the honest free-data
  implementation of "calendar spread" available on this box — commodity futures near/far months
  are NOT obtainable free (see §2). DISCLOSED: this is a vol-term book (SPX implied-vol context),
  not a physical oil/NG month spread.

## 4. BUILT-AND-REJECTED (honest numbers, no candidate claimed)
  - PAIRS TRADING (17 curated related-sector pairs, 299-stock twelve_big panel, lb60 z±2/exit0.5/
    stop3.5): best SR 0.31, ann 1.7%, 6 neg-yrs, corr 0.016. FAIL SR + neg-yr. Classic daily
    z-score stat-arb does NOT clear SR>=0.6 after honest 6.4bps + no-leverage in this universe.
  - TREND / CTA (Turtle 50/20 breakout, 24-40 series FX+index+ETF+spot universe): SR -0.49 (full)
    to -1.02 (developed-only). FAIL badly. Root cause (consistent with A1/A6): on-disk series are
    SPOT/ETF/FX, missing the roll-yield channel that drives real commodity-futures momentum.
  - VOL-ARB (VIX/realized-20d z-rev, T+1 via VIX-index proxy): SR -0.16, 7 neg-yrs. FAIL. Without
    VIX futures / a short-vol instrument, the positive short-vol carry is not reproducible via the
    index proxy; the defensible vol edge lives in the term-structure sleeve (§3 calendar) instead.

## 5. NOT BUILDABLE (data-scarcity, documented honestly)
  - MERGER ARB: requires structured M&A announcement/deal data (deal terms, close probability).
    SEC EDGAR browse returned HTTP 403 this session; no packaged deal feed on the box. Cannot
    construct a deal panel without fabrication => NOT BUILT.
  - CONVERT ARB: requires convertible-bond prices, deltas, credit spreads — no free convertible
    dataset obtainable => NOT BUILT.

## 6. CROSS-FAMILY NOTES
  - brwt (Brent-WTI) re-checked: SR 2.7 but corr 0.43 to the champion => the champion already
    holds this factor; NOT a new decorrelated engine (matches HUNT_BASIS2 / E1 findings).
  - Gold-silver, gold-platinum, gold-palladium, platinum-palladium log-ratios: all SR<=0.05 with
    8-13 neg years => FAIL (matches prior E4/D-series). No precious-metal ratio edge on daily data.
  - The three passing families are all "margin / basis / term" mean-reversion: they monetize the
    reversion of real economic wedges (refining margin, regional basis, vol term slope) and are
    mutually decorrelated (within-family corr < 0.15; gasreg corr to champion +0.01).

## 7. DELIVERABLES
  sleeves/*.csv (20 files, date,ret, T+1, net-of-6.4bps+borrow, vol-targeted), scratch/<engine + 8
  run scripts>, reports/crack_grid.csv + reports/inter_grid.csv (full grids), FINDINGS.md.
  Regenerate from raw data via scratch/verify_all_sleeves.py (byte-identical rebuild).

HUNT_CLASSIC_SPREADS DONE

## 8. ADOPTION GATE 8c — why the champion does NOT improve (capital-real, fixed 1.6x gross)
Reproduced the canonical ITER15 correlation-aware IS max-Sharpe fit locally (same math, same
IS window <2017, same shrink 0.98, same 2.0x cap) and tested adding ONE of each new sleeve at a
time. Result: **every new sleeve passes standalone SR gates yet LOWERS full-window capital-real
annualized return (dAnn < 0)** — exactly the ITER16 frontier gap:

| candidate | standalone IS_SR | capital-real dAnn | weight taken | incumbent SR-> | 
|---|---|---|---|---|
| crack321   | 0.98 | -0.838pp | 0.075 | 3.2176 |
| crack211   | 1.33 | -0.933pp | 0.084 | 3.2127 |
| gascrack   | 1.03 | -0.977pp | 0.084 | 3.2104 |
| gasreg     | 1.72 | -0.969pp | 0.097 | 3.2745 |
| dieseljet  | 0.79 | -1.050pp | 0.091 | 3.2081 |
| vixterm    | 1.98 | -1.278pp | 0.108 | 3.3017 |

INCUMBENT (no addition): ann 39.500%, SR 3.2176, MDD -6.52%, 0/19 neg-yrs; brwt5/7/10 block =
51.0% of the book. Even the best new engines (gasreg dAnn -0.97pp, vixterm -1.28pp) raise SR
(gasreg 3.27 / vixterm 3.30) and slightly lower MDD but REDUCE annualized return at fixed 1.6x
gross. Root cause (as ITER16 §2): the max-Sharpe fit is myopic to per-unit-VOL not per-unit-GROSS;
the incumbent energy/refining sleeves carry ann/vol IR ~2.5-3.0 while every decorrelated addition
(including my crack/gasreg = energy family, and vixterm = vol-term family) has lower return-per-gross,
so at fixed gross they dilute ann. The energy-family WEIGHT does NOT drop meaningfully: brwt block
stays 43-47% after each addition (still the dominant block) — the correlation-aware fit keeps
concentrating in the highest-per-gross-IR sleeves.

CONCLUSION for the loop/chair: these 16 sleeves are a valid, decorrelated NEW-RESEARCH result
(esp. gasreg_nyh_gulf SR1.94 corr 0.01), but under the honest capital-real dAnn>0 adoption gate
NONE is adoptable into the fixed-1.6x-gross champion without lowering return. Champion stays at
the honest frontier (ann 39.5%, 0/19 neg-yrs). Reproduce: scratch/adoption_test.py.
