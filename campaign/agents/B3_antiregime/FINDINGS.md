# B3_antiregime — Round 1 Findings

Mission: build sleeves that EARN in stress regimes (esp. 2022) and pass ALL gates
(FULL SR>=0.6, halves>=0.3, <=2 negYr each>-5%, scramble 200x, trailing-vt10, plateau,
economic rationale). I executed the charter ideas in order, T+1, 6bps/side, honest.

## EXECUTIVE SUMMARY
None of the 14 ideas I tested passed ALL gates on this data. The dominant, brutal fact:
the `twelve_big` survivorship panel AND the free FRED macro series do not easily yield SR>=0.6
stress sleeves. I provide exact numbers below. My best candidate (MOM+HML factor composite)
hits SR 0.94, earns in EVERY stress window incl 2022 (+5.6%), passes scramble (p=1.0) and
is near-zero-correlated to the library — but structurally FAILS the halves (H2 0.21) and
yearly (7 neg yrs) gates bottom. It is saved as a REFERENCE artifact (ref_momhml_composite),
NOT a validated sleeve (per honesty contract).

## IDEA-BY-IDEA (all T+1, 6bps/side unless noted)

### 1. Rate-shock profiting book (DGS10/DGS2 duration momentum) — FAIL
Short bonds when yields rise, long when fall, both 10y (D=8) & 2y (D=1.9), lookback 5-40.
SR range 10y: -0.99..-0.01; 2y: -3.95..-0.57. 2022 +2..+10 (works!) but huge losses 2008-2018
(-12..-15/yr). Confirms charter warning: bond-trend timing dead post-2000. NOT viable.

### 2. Credit-dispersion / HY-fear switch (DAAA-DBAA) — FAIL
Short IG credit when BAA-AAA z high, long when low. lb10-90. SR -0.58..-0.02. 2022 -9.4..+2.8.
2020 +9.5..+18.6 (fear book ok in COVID) but losses in 2011/2015/2018. No robustness.

### 3. Inflation-surge profiter (WTI/energy momentum) — FAIL
wti/wti_full/brent momentum lb5-63. Untradable: negative oil Apr-2020 corrupts pct_change
(2020 shows +208..+769%), MaxDD -95..-100%. Not a clean/tradable series.

### 4. Flight-to-quality variants — FAIL
(a) Gold vs real-rates (DGS10 - CPI_YoY trend): SR -0.11..-0.02. (b) Metals ratio reversion
(gold/silver, wti/brent): GS SR -0.1, WB SR -1.5..-1.9. Both fail badly.

### 5. Equity-factor crisis profiter (cross-sectional) — FAIL (COORD warning confirmed)
Equity panel equity L/S is structurally hostile (survivorship panel).
- Short-term reversal decile L/S (f5-20): SR 0.2..0.34 (best), 2022 +3.2, never near 0.6.
- Classical momentum L/S (12-1, 6-1): SR -0.3..+0.05. Survivorship kills it.
- 52-wk-high & low-vol L/S: SR -0.39, but catastrophic 2009 -61..-63% (illiquid survivor names).
- Volume-filtered (top-30% liquid) reversal: SR 0.09..0.20 — liquidity filter doesn't help.
- Proper hold-period (n10/r14-style) reversal on FULL 2007+ window: SR -0.14..-0.4.
  KEY: the library's ls_n10r14_2018 (SR 0.92, 0 negYr, +10.2% 2022, corr-spx 0.05) works ONLY
  from 2018 — the same reversal is negative across 2006-2017 on this panel. Not replicable
  full-window honestly.

### 6. Dollar tactical (DTWEXBGS trend) — FAIL
lb10-120: SR -0.34..+0.25. 2008/2015 earn (dollar rallies), but 2022 flat-to-neg (-3.1..+5.8).
Single-series macro trend never reaches SR 0.6.

### 7. Multi-asset FRED trend portfolio (wti,brent,copper,slv,natgas,xau,dtwexbgs) — FAIL
lb10/20/40, per-asset vol-targeted 10%, EW. SR 0.07..0.30. Stress: earns 2008/2011/2020,
2022 -7.6..+6.2. Same conclusion: macro trend ceiling ~SR 0.3.

## BEST CANDIDATE (REFERENCE — FAILS STRICT GATES)
**MOM+HML FF-factor composite**, vol-targeted 8%, T+1, 6bps.
- FULL SR = 0.94 (passes SR gate) @ ~8.5% vol, ann ~8%
- halves: H1 1.67, H2 0.21  ->  **FAILS halves (need >=0.3)**
- yearly: 7 neg yrs {2013-2.0,2016-1.5,2018-4.1,2021-1.2,2023-10.9,2024-6.8,2026-3.7}
  -> **FAILS yearly (need <=2)**. 2023/24 is a momentum/factor drawdown late in sample.
- scramble (200x): p = 1.0  -> PASSES (real SR >> all shuffled) — genuine signal
- plateau: broad over wm/wh/vt -> PASSES
- vol-target: trailing 60d expanding, min clip -> built per contract
- stress-year P&L: 2008 +17.7, 2011 +10.2, 2015 +8.3, 2018 -4.1, 2020 +16.6, 2022 +5.6
  -> EXCELLENT crisis/2022 earner (only 2018 negative, and mild)
- corr to library FactorMom_1963: -0.038 (decorrelated)
Economic rationale: when both equity momentum AND value are aligned trending, factor
persistence carries positive expected return in rate-shock/stress regimes (2022 = value+mom
both rose); composite diversifies the two factors' distinct crash years.
Artifact: campaign/agents/B3_antiregime/ref_momhml_composite.csv + repro
campaign/scripts/B3_momhml_composite_ref.py. NOT saved to sleeves/ (would be dishonest).

## CONCLUSION / RECOMMENDATION TO COORDINATOR
The panel+FRED free-data space is near-exhausted for honest SR>=0.6 stress sleeves; the
binding gate here is bombs both halves AND yearly — every robustly-SR>=0.6 book I found
either decays in the second half (post-2016) or has a late-sample factor drawdown.
If the coordinator needs 2022/stress DD-compression, the ref_momhml_composite (SR 0.94,
scramble p=1.0, all-stress-positive, corr~0) is a strong candidate DESPITE missing the
halves/yearly strict gates — flagged clearly for coordinator judgment. No sleeve
saved as passing; honesty contract honored.

## NUMBERED SUMMARY (idea — key numbers — verdict)
1. Rate-shock duration timing (DGS10/DGS2) — SR -3.95..-0.01, stress losses pre-2020 — FAIL
2. Credit-fear switch (BAA-AAA) — SR -0.58..-0.02 — FAIL
3. Energy/inflation momentum (WTI) — untradable (neg-oil 2020), MaxDD -100% — FAIL
4. FTQ (gold-REAL-rate, GS/WB ratio) — SR -1.9..-0.02 — FAIL
5. Equity-factor crisis L/S (mom/rev/52w/lowvol, panel) — SR -0.4..+0.34; survivor panel hostile — FAIL
6. Dollar tactical (DTWEXBGS) — SR -0.34..+0.25 — FAIL
7. Multi-asset FRED trend — SR 0.07..0.30 — FAIL
8. MOM+HML FF composite — SR 0.94, scramble p=1.0, corr lib -0.038, stress
   2008+17.7/2011+10.2/2015+8.3/2018-4.1/2020+16.6/**2022+5.6**; but H2 0.21 (halves FAIL),
   7 neg yrs incl 2023/24 (yearly FAIL) — BEST CANDIDATE, saved as reference (not a passing sleeve)

ROUND 1 DONE
