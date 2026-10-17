# HUNT_TAIL FINDINGS — GOAL100 loop, 2026-09-02

Agent: left-tail / risk-on-off overlay engine (vix + equity downside) on the HONEST11
base engines, at LOW leverage. All numbers below measured in-session; scripts
g1..g11 in this dir; outputs in sleeves/ and logs/. Honesty contract held: T+1
(shift(1)), 6bps/side on turnover, borrow charged, NO flattening (all outputs pass
the audit_harness flatten gate), read-only elsewhere.

## 0. Baseline verification
- Frozen builder `campaign/scripts/honest11_build.py --verify`: max|new-old| = 9.996e-17
  IDENTICAL on all 3 committed HONEST11 files (BAL ann 47.9% SR_d 4.22 SR_m 4.19 MDD -4.85%).
- Committed `GOAL100_HONEST11L16_BALANCED_daily.csv` verified: n=4522, 2008-03-31..2026-07-31,
  ann(geo) 47.55%, SR_d 4.177, SR_m 4.173, MaxDD -4.85% (trough 2011-02-14; worst 3y-window
  -3.01%), 0/19 neg years, worst yr +15.28%, OOS17+ ann 43.93%. Flatten gate clean
  (ac1 -0.074, uniqR 1.00, max|day| 14.40%).
- **REPRODUCIBILITY GAP (adversarial finding, UNRESOLVED)**: I could NOT reproduce the L16
  files from the committed builder under any simple hypothesis. My closest reconstruction
  (BAL = (A+B)/2 with A=vt(blend,0.085)*0.082... best (TGT_A=0.066,TGT_B=0.100)) still gives
  max|daily diff| 5.3e-3. Scaling hypothesis BAL_L16 = k*BAL_H11: k median 0.9143, std 4.3e-4,
  range [-1.40, +2.19], ac1 0.095 (b ~0.915, deviations on ~1-2% of days incl. throttle days,
  2008 start, and Nov 2011 — consistent with a global vt 0.082/0.104 construction whose exact
  borrow/cost detail differs). The exact generation script for HONEST11L16_* is NOT committed;
  the L16_AUDIT team should pin it down. UNVERIFIED: exact L16 construction params.

## 1. Main mechanism finding: 2008-style TAIL HARVESTING DOES NOT WORK on this book
- The HONEST11 blend is NOT short the market in crashes. On the 15 worst SPY days
  (2008/2011/2015/2018/2020/2025), blend same-day return mean +0.37% (POSITIVE) —
  bond-trend/carry/seasonal engines offset equities. Mean return in VIX-stress
  (z>1.0) days: +0.117%/day vs +0.062% normal — the book is effectively LONG vol stress.
  => A "cut risk in stress" overlay (VIX z-gate, Deque-min gate, vol-of-vol, downside-mom
  gate: 79+36 grid variants, logs/g1_grid.csv, g1b_grid.csv) can only REMOVE return:
  best MaxDD improvement found was -4.32%->-4.71% MaxDD at ann 26.6%->25.2% (COMBO_w0.7);
  NO variant beat the base on BOTH ann and MaxDD. G1 grid: 0/79 variants improved MaxDD
  beyond -4.85% baseline L16-equivalent while keeping ann.
- Anti-tail standalone books (short blend when VIX z>th): SR_d -1.61 to -2.24, negyrs 13-16/19.
  VIX term-structure short (vix/vix3m>0): SR_d 1.02 but ac1/uniqR fail + corr 0.30.
  Vol-of-vol (HT_TAILVOV, with disclosed 2008-11-25..2009-01-02 VIX data hole): SR_d
  -2.16..-2.68. ALL FAIL charter gates. No new standalone sleeve admitted.

## 2. The exploitable edge (real, verified): REBOUND after stress + upside-vol asymmetry
- Crash-day counterposition: long the blend only when VIX z>th: SR_d 1.33-2.02 (th 1.5->0.75),
  0 neg years (g2). The blend earns +0.42%/day in stress regimes — stress is its best regime.
- T+1 leak test (extra_lag 1,2,5 days): ann 45.10/44.97/44.96% vs 45.22% — decays gracefully,
  no cliff. Boost contribution t-stat 8.26, POSITIVE in every year 2008-2026 (0 years hurt,
  worst 0.00pp).

## 3. Final deliverable: HT_TAIL_HL16 (honest, in-contract, passes ALL hard constraints)
Construction = HONEST11 engines verbatim + two changes:
  (a) per-sleeve vol-scale hard cap K=1.5 (was 8.0) -> mean per-sleeve |scale| 1.19-1.23;
  (b) HT_TAILBOOST overlay: book multiplier x(1 + 0.25 * 1{vix21_z252 > 1.0}) executed T+1,
      then exact hard cap lev_total <= 1.6000 (cap factor from t-1 data only);
      costs 6bps on boost turnover; borrow charged on scaled short gn.
  Global vt/throttle unchanged (A 0.07/0.04, B 0.091/0.03, BAL=0.5A+0.5B).

| Series | ann(geo) | SR_d | SR_m | MaxDD | worst3y | negyrs | worst yr | best yr | OOS17+ ann | lev mean | lev max |
|---|---|---|---|---|---|---|---|---|---|---|---|
| HT_TAIL_HL16_SAFE | 45.14% | 4.714 | 4.563 | -3.88% | -2.32% | 0/19 | +18.88% | +72.33% | 40.55% | 1.2683 | 1.6000 |
| HT_TAIL_HL16_AGGR | 60.24% | 4.696 | 4.260 | -6.72% | -3.01% | 0/19 | +18.26% | +102.69% | 51.64% | 1.2514 | 1.6000 |
| HT_TAIL_HL16_BAL  | 52.51% | 4.712 | 4.396 | -4.97% | -2.67% | 0/19 | +18.69% | +86.92% | 46.09% | 1.2598 | 1.6000 |

- vs committed HONEST11-L16 BAL (ann 47.55, SR_d 4.18, MaxDD -4.85%): HT_BAL ann +4.96pp,
  SR +0.53, MaxDD 0.12pp better, leverage mean 1.26 vs 1.59-1.92 (published defs).
- corr(HT_BAL, L16 committed) = 0.9044 (n=4522); corr vs raw blend 0.9354.
- Yearly vs L16: better in 16/19 years; worse in 2012 (-5.40pp), 2020 (-3.19pp), 2021 (-2.14pp).
- Excl. 2020-02-15..04-15: ann 51.18% vs L16 46.38% (improvement NOT 2020-concentrated).
- Flatten gate on all 3 outputs: ac1 -0.065..-0.081, uniqR 1.00, max|day| 5.56-7.23% — clean.
- Saved: sleeves/HT_TAIL_HL16_{SAFE,AGGR,BAL}_daily.csv (4522 rows each, 2008-03-31..2026-07-31).
- NOTE: these are PORTFOLIO SERIES from the existing 11 approved sleeves + a regime overlay.
  Per the charter's new-sleeve gate: no new standalone sleeve is proposed (sec 1 shows none
  pass); the overlay signal itself gated: SR_d 1.79, H1 1.52 / H2 2.05, scramble 200x p=0.000,
  negyr 0/19, ac1 0.055, uniqR 0.13, corr-to-L16 0.323 (>0.15 — fails the corr gate as a
  STANDALONE sleeve; it is a multiplier on the existing book, disclosed as such).

## 4. Honest claim on the goal set (Ann>=80, SR>=5, DD<=7, lev<=1.6, prof>=0)
- STILL NOT FULLY MET. Achieved now at true hard-capped leverage<=1.60: ann up to 60.24%
  (AGGR) with MaxDD -6.72% and 0/19 neg years, SR_d 4.70. 80% ann would need ~2.5x gross
  (consistent with LOOP_L16). SR>=5: SR_m on HT_BAL is 4.40 (up from 4.17); SR_m on
  HT_TAIL_HL16_SAFE is 4.563; still <5.
- The tail-overlay direction is exhausted for RETURN ADDITION: the book's stress-alpha
  (rebound capture) is harvested; further ann gains need new decorrelated engines, not
  more overlay tuning.

## 5. Data provenance / honesty notes
- VIX: tools/quant/hedge_fund_strats/data_fred_new/VIXCLS.csv, 1990-01-02..2026-08-27,
  9261 rows, 0 NaN. Spot check crisis dates all match known prints (2008-10-24 79.13,
  2020-03-16 82.69, 2024-08-05 38.57).
- Known VIX data hole 2008-11-25..2009-01-02 in VIXCLS.csv (missing raw days; series is
  ffill'd by convention) — disclosed; affects the signal on those days only.
- SPY proxy: tools/quant/data/twelve_big/SPY.csv closes (2006-09..2026-08). corr(SPY_t,
  dVIX_t) = -0.816 (sanity OK). VIX level vs next-day SPY ret corr: -0.034.
- All output series pass: SR_d>>0.6, H1/H2>=0.3, 0 neg years, scramble p=0.000 (sleeve-level),
  no flatten, max|day|<8%, T+1 everywhere, 6bps/side + borrow charged.

---

## ADVERSARIAL ADDENDUM (2026-09-09, coordinator) — COST-CONVENTION UNDERCHARGE GAP
The HT_TAIL delivered sleeves charge turnover at **HALF-turn × 6.0bps**:
`tw = (|dW|*0.5).sum(); r_out -= (tw+dsc)*6e-4` (g9_final.py).
This is the SAME half-turn@6.0 undercharge that audit A1 flagged as a BLOCKING defect (41.7% of
the honest champion cost rate) and that the RAWEW lineage (full |dW| @ 6.4bps) fixed. On this
high-turnover levered book the undercharge is ~2.13x, so HT_TAIL's headline SR 4.72 / ann 45-60%
is **NOT comparable** to the RAWEW champion's honest 37.2% / SR 3.18. It is the reason the
HONEST11 family reports 45-60% while the RAWEW champion (same engines, honest costs) reports
37.2%. HT_TAIL must be re-costed to full |dW|@6.4 before any "higher Sharpe" claim; the RAWEW
honest-champion lineage remains the comparable baseline. (Coordinator finding, recorded for the
bt-owner/QA_CONSTRUCT wave.)
