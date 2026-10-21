# C2_ratescurve — FINDINGS (GOAL100 Round 1)

Agent: C2_ratescurve | Domain: US Treasury curve (FRED DGS 1MO-30Y), breakevens, real yields, credit, intl 10y
Data facts discovered: DGS daily 1976+ (1MO from 2001); T10YIE/T5YIE/DFII10 daily 2003+; **T5YIFP.csv is corrupt HTML — unusable**; hy_oas only 2023+ (786 obs, too short); intl 10y (au/ca/ch/ez/gb/jp/nz) are MONTHLY 2018+ only (103 rows — too short for daily engines, idea 5 infeasible); DGS3/DGS7 files missing from disk.

## SAVED SLEEVE (ALL GATES PASS)

### C2_fly2AB_75 — UST curve butterfly z-reversion, 2 flies (2s5s10s + 5s10s30s)
- Files: `campaign/scripts/C2_fly2AB_75.py`, `campaign/agents/C2_ratescurve/sleeves/C2_fly2AB_75.csv` (+meta). 2006-03-30..2026-08-27, n=5108.
- Construction: fly = 2*y_belly - y_wing1 - y_wing2; z over 75d rolling; enter |z|>1.0, position = z clipped to [-2,2], duration-neutral PnL legs (A: 5y vs 0.62*2y+0.38*10y; B: 10y vs 0.69*5y+0.31*30y); bond returns approximated ret = -D*dy + y/252 (D: 2y=1.9, 5y=4.4, 10y=8.5, 30y=17.5, documented); T+1 shift; 6bps/side on one-side turnover; trailing expanding vol target 10% ann (min 60d, clip 3.0, scale shifted 1d); EW of 2 flies.
- GATES: full SR **1.85** (ann 14.8%, vol 8.0%, mdd -10.6%) >= 1.0 PASS | H1 1.80 / H2 2.02 PASS | yearly: 1 neg year (2021 -4.0%) > -5% PASS | signal-scramble 200x p=**0.000** (real 1.85 vs scrambled p95 0.14) PASS | plateau center/peak = 1.85/2.05 = **0.90** PASS | corr vs COORD blend **0.017** PASS | corr vs best lib (FI_Arb_curve) 0.179 → secondary band, no Credit sleeve >0.12 | econ rationale in meta.
- OOS: IS 2006-16 SR 1.76 (ann 16.3%) / OOS 2017-26 SR **2.09** (ann 13.1%, mdd -9.5%). OOS stronger than IS.
- Yearly (eval.py): 2006 51.3, 2007 30.5, 2008 42.7, 2009 10.7, 2010 3.0, 2011 15.9, 2012 9.0, 2013 3.8, 2014 8.9, 2015 11.1, 2016 7.1, 2017 14.1, 2018 9.7, 2019 14.3, 2020 25.9, 2021 -4.0, 2022 7.6, 2023 28.2, 2024 11.5, 2025 12.6, 2026 15.2. Positive in 2022 (+7.6) — bond-crash year — because belly-vs-wings reversion is duration-neutral.
- Key construction lesson: equal-notional 50/50 wings (SR 1.26) and DV01-matched wing notionals D_b/D_w (SR 0.46!) both UNDERPERFORM the true duration-neutral interpolation weights (SR 1.27 single fly). Wing sizing matters more than the signal.

## FAILED IDEAS (exact numbers, not saved)

1. **Curve reversal (charter 1)** — REJECTED. 2s10s/5s30s/3m10y daily spread changes are NOT mean-reverting: corr(z126, next-day dSpread) = +0.015/-0.018/-0.003; extreme-z buckets show MOMENTUM (corr(z, fwd 21d) = +0.132, fwd 63d +0.172, monotone). Reversal backtests: best SR 0.27 (5s30s w126 sign); momentum backtests best SR 0.20 — all fail gate a. Daily curve moves are noise around drift; only monthly-horizon drift exists and is insufficient after costs.
2. **Level+curve regime steepener (charter 2)** — REJECTED. Inversion-gated steepener: gate sp<0 → SR 0.01 (on 15% of days); near-inversion gate → SR -0.30. Level-anchored duration (fade 10y z vs 252/504/756/1260d mean): best SR 0.25 (w504), mdd -33%, 10-11 neg years. UST level moves 2013/2015/2021-23 crush all level strategies.
3. **Breakeven mean-reversion (charter 3)** — REJECTED. BE10 = DGS10-DFII10: corr(z21, next dBE) = +0.035 (momentum-signed, tiny); T10YIE z-reversion corr +0.034 max; dBE vs dT10YIE corr = 1.000 (series redundant). BE trend (w63 sign) SR 0.02; all 8 configs |SR|<0.6.
4. **Real-vs-nominal spread (charter 4)** — REJECTED. DFII10 trend: best SR 0.31 (w504 sign) with 8 neg years; w126-756 all ≤0.31. Real-yield vol-regime fade: best SR 0.15 (thr 1.5, 8% days on).
5. **Global 10y momentum / cross-country (charter 5)** — INFEASIBLE. au/ca/ch/ez/gb/jp/nz 10y data are MONTHLY, 2018-01+ only (103 rows). Cannot build a 2006+ daily engine; logging honestly rather than fabricating a 2018+ monthly backtest.
6. **Credit z-reversion (charter 6)** — REJECTED + DATA GAP. hy_oas.csv only 2023-08+ (786 rows) — too short to gate. baa-aaa (1986+) z-reversion with spread-DV01 PnL: SR -0.93 (w63) / -0.25 (w126) / -0.11 (w252). Direction wrong (quality spread widening continues after z spikes).
7. **3M-1M bill-spread reversion (charter 7)** — NEAR MISS, not saved (honest gate a failure). Real reversion exists: corr(z63, next chg) = -0.155. Best strategy (w63, |z|>1, dur-neutral 1m vs 0.32x3m, T+1, 6bps, trailing VT): SR **0.98**, ann 9.8%, mdd -21.3%, H1 0.98/H2 0.98, neg years {2010 -0.5, 2011 -0.0, 2025 -1.8, 2026 -2.2} — fails gate a by 0.02 (0/24 grid configs >= 1.0; plateau 0.96-0.99). Full-window scan capped at 0.99 (w63 thr0.75). Combo with saved fly sleeve: SR 1.90, corr(bill,AB) = -0.005, negy 1 (2021 -0.9%) — marginal (+0.05 SR) gain; coordinator may consider as add-on but sleeve itself failed the gate so NOT saved per honesty contract.
8. **Extra flies tested**: 1s2s5s fly SR 0.53 (5 neg yrs incl -12.8% 2013, -11.8% 2016), degrades ensemble to 1.32 — dropped. 3s7s10s fly impossible (DGS3/DGS7 files missing).
9. **PnL-scramble degenerate**: gates.py scramble_pval permutes the PnL series itself, which preserves mean/std → p=1.0 for any strategy (observed on combo). Replaced with proper SIGNAL permutation (permute signal alignment vs returns, rebuild both legs, 200x): real 1.85 vs scrambled mean -0.20, p95 0.14, p=0.000. Coordinators should fix gates.py scramble semantics.

## COORDINATOR NOTES
- Blend candidate: C2_fly2AB_75 (corr 0.017 vs blend, SR 1.85 net, OOS 2017+ SR 2.09) is a genuine new-domain engine: pure curve-shape reversion, no equity/credit/commodity exposure, +7.6% in 2022 (bond crash), +42.7% in 2008.
- Approximation caveat (documented): bond returns from yield changes via constant duration, no roll-down adjustment; ETF-executable proxies (SHY/IEI/IEF/TLT) would add tracking noise ~1-2bp/day.
- If a future round can pull DGS3/DGS7 or daily intl 10y from FRED directly, fly D and cross-country engines become testable.

ROUND 1 DONE

# C2_ratescurve — ROUND 2 (2026-09-01): CRITICAL AUDIT FINDING + CHARTER RESULTS

**ROUND-1 SLEEVE C2_fly2AB_75 QUARANTINED (units bug — as-saved SR 1.85 is invalid).**
Bug: gross leg return `fret = -DUR*Δy` used Δy in percentage POINTS, so fret was in
percent scale, while costs were subtracted as decimal (`to*6e-4`) — i.e. 6bps charged as
0.006bp on a 100×-larger PnL, 100× cost understatement. Honest rerun (fret/100, per-leg
6bps: Σ|Δ(sig·w_leg)|×6e-4): FULL SR **-2.04**, ann -7.6%, mdd -78.8%, 21/21 neg years.
Sleeve moved to sleeves/QUARANTINED/ with README; COORD blend does not reference it (grep=0).

## The physics of the failure (exact numbers)
- Data clean: max |Δy| 2006+ = 0.51-1.06 pct-pt, all on real crisis days (2008-09, 2020-03, 2023-03).
- Gross edge is REAL: flyA(2s5s10s) pre-cost SR 1.20-1.25, flyB(5s10s30s) 1.26-1.42,
  flyC(10s20s30s) 1.75 (signal-scramble 200x p=0.000), billfly(1s3s6s) 2.05. Fly reversion exists.
- But fly PnL scale is tiny: gross vol 1.3-2.8%/yr (duration-neutral spreads barely move),
  gross ann return 1.7-4.7%/yr, while turnover 0.5-0.9 legs/day × 6bps/side = **7-13%/yr costs**.
- Cost/gross-return ratio 3-30×. Breakeven cost for flyC SR≥1.0 = **0.010 bp/side** (600× cheaper
  than assumed 6bps). Hysteresis no-trade bands (h=0.25-1.0) cut turnover only 15-25% and cost
  more gross edge than they save (flyA D h1.0 net SR -6.04). Weekly rebalancing (correct,
  no-lookahead prior-week position) halves turnover but gross SR collapses (flyC wk 0.17,
  flyA wk 0.52) because fly reversion is a DAYS-scale effect. Monthly: all SR ≤ -1.4.
- Combo backtests (AB/ABC/ABb/ABCb EW): net SR -3.7 to -5.5, 21 neg years. All fail gate a by a mile.

## Charter items (all REJECTED, honest numbers, nothing saved)
1. **flyA solo** (w63/d75): best honest net SR **-3.71** (weekly w75); gross 1.24. FAIL.
   flyB solo: best **-3.10**; gross 1.42. FAIL. (Gross SRs pass; economics fail.)
2. **2-leg steepeners** (2s10s, 5s30s; z-rev & mom, w50/75/126): best SR **0.30** (5s30s mom w75),
   10 neg yrs — pre-bug scan was on inflated units; at honest units worse. FAIL.
3. **Breakeven/TIPS legs**: BE-slope(10-5) reversion best SR -0.05..-1.11 (17-23 neg yrs);
   BE10/BE5 solo rev/mom best **+0.08** (w63 H1). FAIL (also on pct-pt scale, still fails).
4. **Intl curve flies**: au/ca/ch/ez/gb/jp/nz 10y confirmed MONTHLY 2018+ (103 rows) — infeasible (re-verified).
5. **bill-area fly 1s3s6s** (2001+): gross SR 2.05-2.06 real, but gross ann +0.3%/yr vs costs
   11.6-13.4%/yr at to 0.77-0.89/day. Honest net SR **-8.98..-10.7**. The round-1 "bill-spread
   near-miss SR 0.98" is also an artifact (honest rerun: gross ann -0.15%/yr, net SR -9.92). FAIL.
6. **Extreme-z asymmetric bands** (|z|>2 enter, |z|<0.5 exit, w75): inflated-units scan SR 0.33-0.68
   (below 1.0 gate even with the bug favoring it). FAIL harder honestly.
- Bonus flyC (10s20s30s, 20y belly): strongest gross edge found (gSR 1.75, p=0.000, 0/19 neg yrs
  pre-cost) — worth revisiting ONLY with sub-bp execution (futures DV01 spreads) or weekly holding
  period design that preserves the days-scale edge. Logged as the best lead for round 3.

## HONEST VERDICT
The US curve fly/steepener domain cannot produce a net-SR≥1.0 GOAL100 sleeve at 6bps/side ETF
execution: edges are real but 1-3%/yr against 7-13%/yr costs. Round-1's C2_fly2AB_75 must be
removed from any blend. Coordinators should re-audit other yield-approximation sleeves for the
same pct-pt vs decimal units bug (check: any sleeve whose meta says "ret ~ -D*dy").

ROUND 2 DONE

# C2_ratescurve — ROUND 3 (2026-09-01): low-turnover charter executed; 0 sleeves saved (honest)

Charter premise tested and REFUTED: low-turnover structure does NOT rescue the fly family —
the days-scale reversion edge dies faster than costs under every turnover-reduction design.
BONUS discovery (fails gates, logged for coordinator): always-on DV01-neutral steepener carry,
net SR 1.33, corr_blend -0.054 — a real new carry engine that fails only the neg-year/scramble gates.

## Charter items (exact numbers; all decimal units, per-leg 6bps/side, T+1, VT 10% clip 3.0)
1. **Weekly-step fly z-reversion (flyC 10s20s30s lead)** — REJECTED. Reproduced round-2's flyC
   daily-step gross SR exactly (w42 thr1.0 g1.76/w35 1.84; continuous signal). But sampling z every
   5 sessions collapses gross to 0.44-0.61, step10 0.10-0.36, step21 0.15-0.51; best weekly-step NET
   across w{50,75,126} x thr{0.75,1,1.5} x step{5,10,21}: flyC -0.02, flyB 0.17, flyA -0.05.
   Event-driven entries (|z|>thr, K-day hold; K in 3/5/10/21, thr up to 2.5) also kill it:
   flyC best net -0.32 (gross 0.32 vs 1.75 continuous). The reversion horizon is ~days; any
   multi-day position gap destroys the edge. Physics unchanged: gross ann ~0.3-1.5% vs cost 0.6-3.6%/yr.
2. **flyA/flyB weekly-step** — best net 0.17 (B) / -0.05 (A). FAIL gate a.
3. **Monthly 2s10s reversion 1976+ (51y)** — REJECTED. Monthly-sampled z (w126): net SR 0.17,
   20/51 neg yrs; sign(+) only; w252-1260 all 0.12-0.16 net. Too slow, spread drifts are tiny vs
   dv01-neutral 5.47x notional costs. (1976+ replication confirms round-1 round numbers.)
4. **FOMC event-driven** — SKIPPED as planned (no free structured FOMC calendar on disk).
5. **20y-belly fly variants** — REJECTED. D_5s20s30s best weekly-step net 0.05 (9 neg yrs),
   E_2s20s30s 0.12 (8 neg yrs). Daily-step per-leg-honest: D -0.43, E -0.71 at w75.
6. **Fed-regime curve switching** (bonus, economically motivated) — REJECTED. Two-sided
   (steep when 2y<252d mean, flat otherwise): net -0.53, 11 neg yrs — flattener-in-hiking
   loses catastrophically (2013 -18.9%, 2016 -35.6%, 2023 -33.8%). One-sided easing-gated
   steepener looks good only if you forget leg-notional costs: honest = 0.52 net, 9 neg yrs.
7. **Bull-flattening filter on steepener** (de-risk when 10y in rally) — REJECTED: destroys the
   edge (best 0.06 across w{63,126,252}) because steepener PnL IS 10y-underperforming-2y.

## BONUS ENGINE FOUND (does NOT qualify as sleeve — fails gates d & f-scramble — NOT SAVED)
**Always-on DV01-neutral steepener carry** (hold long 2y x4.474 vs short 10y x1 forever, zero
signal): net SR **1.33**, ann 13.4%, mdd -28.9%, H1 1.13/H2 1.57, corr_blend **-0.054**, IS/OOS
1.13/1.57, turnover 0 (costs = initial entry only). Variants: 2s5s 1.08 (corr -0.083), 5s30s 0.74
(corr 0.031), EW-5-spreads 0.97, EW 2s10s+5s30s 1.05 (5 neg yrs), 60/40 VT pair 1.29 (6 neg yrs,
worst -14.9). Neg years are bull-flattening episodes: 2011 -15.0%, 2014 -15.8% (2s10s).
FAILS: gate d (8 neg years > 2, worst -15.8% < -5%) and scramble gate is DEGENERATE (constant
position → permuted positions identical, p=0.93; a no-signal carry cannot pass a signal test).
This is classic positive-carry steepener (roll-down + convexity), executable via ETF pairs
(SHY vs IEF) or futures; its -0.05 corr vs blend and H2>IS stability make it interesting for a
coordinator-level blend as a *carry overlay*, NOT as a gated C2 sleeve. Recorded honestly here.
Repro: campaign/scripts/C2_r3_final.py (runs the full grid + this engine in ~20s).

## Audit notes for coordinator
- Round-2 flyC "gross 1.75" REPRODUCES exactly with C2_r2_honest.py pipeline (verified).
- c2lib.py cost convention differed (fly notional vs per-leg): per-leg (x(1+w_legs)) is honest;
  differences are ~2x on costs, material for low-edge engines.
- gates.py scramble_pval remains PnL-permutation (degenerate p=1.0); use signal-permutation.

## HONEST VERDICT
Rates/curve domain at 6bps/side ETF execution: fly/steepener/BE/credit REVERSION engines are all
uneconomic (edges 1-3%/yr vs costs 7-13%/yr at daily turnover; every low-turnover design kills the
days-scale edge). The only strong net engine is signal-free steepener CARRY (SR 1.33, corr -0.05)
which fails the yearly-drawdown gate in Fed easing-surprise years (2011, 2014) — a genuine
macro risk, not a data artifact. Recommend coordinator evaluate it separately as carry overlay.

ROUND 3 DONE
