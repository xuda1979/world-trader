# STATS_REVIEW — independent statistical certification of GOAL100_HONEST11FIX (2026-09-02)

Auditor: loop_team/STATS_REVIEW. All numbers computed by my own code on the COMMITTED-FILE
BYTES (worktree copies, see §0); scripts in `STATS_REVIEW/scratch/stats_main.py, stats2-4.py`.
Unless noted, stats are on the comparable span 2008-03-31..2026-08-27 (BAL n=4616).

## 0. PROVENANCE — reproducible, but UNCOMMITTED, and the charter's metadata is wrong
- Charter says "committed". **The three FIX CSVs are NOT in git** (untracked; `git log` on them
  is empty; worktree sha256 BAL 72475976bc33c43a, SAFE 4eb1e69939bda630, AGGR 9e7e3c34a9a743d4;
  mtime 2026-09-02 18:39). Provenance hole until they are committed. I could still verify the
  RECIPE: rebuilding via canonical `honest11_build.build(0.07,0.04,0.08,REBAL=True,KEEP=True)`
  (SAFE) / `(0.091,0.03,…)` (AGGR) / their mean (BAL) matches the files with
  **max|diff| = 9.986e-17 (BAL, SAFE), 9.996e-17 (AGGR) over all 4989 rows** — reproduced to
  float precision. `--verify` HONEST11 and `--verify-l16` also IDENTICAL (9.996e-17/9.986e-17).
- **Charter error 1:** "n=4989, comparable-span starts 2008-03-31" — 4989 is the FULL span
  (2006-10-02..2026-08-27) row count; the comparable span 2008-03-31+ is **n=4616**, not 4522
  (4522 was the L16 inner-join count; the rows-kept fix adds 94 in-window days).
- **Charter error 2:** "2006-10..2026-07" — the files actually run to **2026-08-27** (19 extra
  trading days beyond July; Aug-2026: 19 rows, mean +20.65bp/day, all 19 values distinct, max
  flat run 1 day — no hygiene problem, but the coordinator must disclose the true end date).

## 1. HEADLINE STATS + 95% CIs (BAL 2008-03-31..2026-08-27, n=4616)
- **ann(geo) 45.66%** (full span incl. 373 warmup rows 2006-10..2008-03: 44.82%)
- **SR daily 4.029**; block bootstrap (2000x, 10d blocks): **95% CI [3.549, 4.549]**
- **SR monthly 4.095** (222 months); iid bootstrap (2000x): **95% CI [3.578, 4.794]**
- Spread: SAFE ann 39.05% / SR_d 4.016 [3.577,4.527] / SR_m 4.187 [3.672,4.809];
  AGGRESSIVE ann 52.55% / SR_d 4.029 [3.587,4.556] / SR_m 4.019 [3.506,4.671].
- BAL == (SAFE+AGGR)/2 exactly (max|diff| 7.8e-17, n=4989). Internally consistent.
- Honesty cost vs L16 on the COMMON span (2008-03-31..2026-07-31): FIX 45.57%/SR_d 4.020/
  SR_m 4.082/MDD -5.60% vs L16 47.55%/4.177/4.173/-4.85%. The two fixes (rows-kept + overlay
  rebalance cost) cost **-1.98pp ann, -0.16 SR_d, +0.75pp DD depth**; common-row mean diff
  -0.37bp/day (≈ -0.93%/yr arithmetic, matching the predicted overlay-rebalance cost).

## 2. DRAWDOWNS / WINDOWS (BAL)
- **MaxDD -5.60%**; worst 1260d rolling subwindow MaxDD **also -5.60%** (window
  2017-03-20..2022-03-29 — one single >3y episode contains it). SAFE -5.02%, AGGR -6.47%.
- Worst 252d rolling subwindow return **+11.20%** (2021-10-12..2022-10-13) — positive; there is
  NO losing 1-year window anywhere in 18.4 years.

## 3. CALENDAR YEARS 2008–2026 (BAL): **0/19 negative**, worst **2011 +15.12%**, best 2020 +91.04%.
Full: 2008 +42.93, 2009 +37.55, 2010 +50.02, 2011 +15.12, 2012 +42.93, 2013 +27.15,
2014 +31.53, 2015 +41.07, 2016 +56.35, 2017 +59.28, 2018 +52.60, 2019 +52.69, 2020 +91.04,
2021 +34.81, 2022 +25.40, 2023 +56.36, 2024 +55.89, 2025 +54.42, 2026(partial) +21.51 (%).
SAFE worst year +14.51%, AGGR +15.72%; 0/19 negative in all three.

## 4. OUT-OF-SAMPLE (BAL, comparable span)
| OOS start | n | ann(geo) | SR_d | MaxDD |
|---|---|---|---|---|
| 2017-01-01 | 2418 | **51.78%** | 4.161 | -5.60% |
| 2020-01-01 | 1666 | **50.27%** | 3.865 | -5.60% |
| 2023-01-01 | 915 | **52.00%** | 4.948 | -4.21% |
Recent-regime check PASS: no IS/OOS decay (full-sample 45.7% vs OOS17+ 51.8%; the 2023+
regime is the strongest, SR 4.95). SAFE/AGGR OOS17+ 44.1%/59.8%.

## 5. DEFLATED SHARPE (Bailey/López de Prado, N=500 effective trials, per-period units)
Expected-max-SR-under-H0 haircut and DSR of SR_ann=4.0285 (T=4616, skew +4.29, raw kurt 85.7):
| cross-trial SR dispersion (ann units) | SR* haircut | DSR |
|---|---|---|
| sd 0.25 | 0.763 | 1.0000 (z=+12.4) |
| sd 0.50 | 1.526 | 1.0000 (z=+9.5) |
| sd 1.00 | 3.053 | 0.9999 (z=+3.7) |
| sd 1.13 (7 distinct engines measured) | 3.821 | **0.784** |
| sd 1.442 (measured sd of the 11 sleeve SRs) | 4.403 | **0.078** (z=-1.4) |
- **Threshold: SR 4.03 survives N=500 selection at the 95% level iff the effective cross-trial
  SR dispersion ≤ 1.178 (ann units).** The measured 11-sleeve dispersion (1.44) does NOT
  survive (DSR 0.08); a 7-distinct-engine anchor (1.13) survives only at 78%. Caveat: sleeve
  SRs are correlated, so 1.44 overstates independent-trial dispersion — the true anchor lies
  between; the claim "SR 4.0 survives DSR at N=500" is therefore **NOT certifiable**, it is
  anchor-dependent. What IS certifiable: PSR against SR*=0 is 1-4e-50 (z=+17.0) — the edge is
  real even at maximum plausible selection haircut; monthly DSR under the same anchors:
  1.0000/0.9998/**0.825**/0.147.
- Sanity: my first DSR pass used annualized SR in the daily-units formula (haircuts inflated
  ~16x, all DSR=1) — discarded; numbers above use daily units consistently.

## 6. LJUNG-BOX (daily, 10 lags, BAL 2008+): **LB(10)=35.34, p=1.09e-4 — REJECTS iid at 0.1%.**
- acf lags 1-10: -0.0701, +0.0073, +0.0096, -0.0037, +0.0262, -0.0054, +0.0032, +0.0390,
  -0.0187, -0.0012. No lag |ρ|>0.071.
- The rejection is NOT driven by the 24σ outlier: zeroing 2020-09-01 RAISES LB to 50.46
  (p=2.2e-7). Squared returns show NO clustering at all (LB=0.751, p=0.99995).
- Materiality: ac1 is NEGATIVE; an AR(1)-consistent long-horizon SR is 4.03/0.932 = **4.32**,
  i.e. the iid sqrt(252) annualization is ~7% CONSERVATIVE. Verdict: no SR-inflating artifact;
  the residual autocorrelation likely comes from the binary throttle (0.5/1.0) and zero-gated
  sleeves. FLAG for honesty: the series is not formally white (p≈1e-4), and squared-return
  p=0.99995 is implausibly clean for real markets (whitened by the vt layers) — both disclosed.
- Flatten gate: uniqR = 1.0000 (4616/4616 distinct); ac1 -0.0701 (SAFE -0.0750, AGGR -0.0663);
  Aug-2026 max flat run 1 day. PASS.

## 7. TAIL: skew/kurtosis, worst days, VaR/CVaR, and the ~24σ day
- **skew +4.289, excess kurtosis +82.72** (raw 85.72) — the skew is POSITIVE.
- Worst 5 days: 2008-09-19 **-3.68%**, 2026-03-06 -3.19%, 2010-04-01 -3.11%, 2021-11-26
  -2.55%, 2011-06-10 -2.46%. **Max loss -3.68% vs max gain +14.399%**; counts: ≥±3.68%:
  0 losses vs 7 gains; ≥±3%: 3 vs 13; ≥±2%: 11 vs 40. The loss tail is TRUNCATED vs the gain
  tail — MaxDD is built by accumulation, not single-day crashes.
- **VaR 5% daily -0.553%, CVaR 5% -0.970%** (SAFE -0.48/-0.85, AGGR -0.62/-1.09).
- The 24.3σ day: 2020-09-01 **+14.399% = +23.9σ** (σ_d 59.5bp) — only 2 days |z|>12 in 4616
  (2020-09-01 +23.9σ, 2021-03-31 +12.8σ, both GAINS). Recurrence probability estimates:
  - Normal: 1.6e-129 (meaningless, obviously mis-specified).
  - Student-t MLE on standardized returns (df≈2.14): **1.15e-4/day ≈ once per 34y**.
  - Empirical/Poisson 95% upper bound for ANY ≥12σ day: 3/4616 = 6.5e-4/day ≈ **once per 6.1y**.
  - EVT: GEV on 21d |r| block maxima gives shape -0.764 with implied upper endpoint 2.15% —
    which the data themselves violate (14.4% observed); GPD(u=2%, 11 exc.) gives ξ=-0.232 and
    P(loss≥14.4%)=0. **Both EVT fits are degenerate (bounded-tail artifact of small blocks +
    one dominant outlier) and I REJECT them; only the t-fit and Poisson numbers are usable.**
  - Asymmetry note: the mechanism behind +14.4% (4 zero-gated brwt books + NG gates all
    simultaneously on, corr 0.66-0.86) is direction-symmetric; a -14.4% day has simply never
    fired. Treat the loss-side risk as LIVE, not excluded.
- **Breach answer: YES — a single -14.4% day breaches MaxDD≤7% from EVERY state.** Equity is
  never above its running peak when the day lands, so DD jumps to ≥14.4% from flat, and to
  **-19.19% from a -5.60% DD**. Even a repeat of the worst OBSERVED loss (-3.68%) from -5.60%
  gives -9.1% (breach); from flat, breach needs ≤-7.0% (0 of 4616 days). The backward-looking
  -5.60% MaxDD therefore understates forward gate risk; only the throttle (halving after
  trailing DD<-4%) softens SECOND breaches, not the first hit.

## 8. LEVERAGE — capital-real all-in gross on the FIX construction (mean_i |scale_i| ×
global vt scalar × throttle; /11 convention, 2008+; scales captured from build machinery):
| variant | mean | median | p95 | max | days>1.6 | years(mean)>1.6 |
|---|---|---|---|---|---|---|
| SAFE | **2.945x** | 2.708 | 6.046 | 9.248 | 84.7% | 19/19 |
| BAL | **3.367x** | 3.095 | 6.953 | 10.635 | 90.9% | 19/19 (2.04..5.14) |
| AGGR | **3.789x** | 3.490 | 7.860 | 12.023 | 92.6% | 19/19 |
BAL per-present-sleeve convention: 3.421x (≈same; borrow sleeves span nearly all days).
BAL yearly means: 2008 3.19, 2009 2.82, 2010 2.94, 2011 3.00, 2012 4.42, 2013 3.86, 2014 3.55,
2015 2.42, 2016 2.87, 2017 3.41, 2018 3.96, 2019 2.61, 2020 2.59, 2021 4.32, 2022 4.99,
2023 5.14, 2024 2.19, 2025 3.17, 2026 2.04.
**"≤1.6x capital-real" does NOT hold on the champion under ANY variant, in ANY year.**
- TGT sweep (THR 0.04, per-sleeve vt 0.08, FIX costs): gross≤1.6 mean is reached at TGT≈0.0375:
  **ann 18.85%, SR_d 3.90, MDD -2.75%, 0/19 neg, gross mean 1.580 / p95 3.24 / max 4.95**
  (TGT 0.038 → 1.601x → ann 19.14%). Full ladder: TGT 0.02→ann 9.09% @0.842x; 0.03→14.57% @1.264x;
  0.04→20.31% @1.685x; 0.05→26.32% @2.106x; 0.06→32.53% @2.527x; 0.07→39.05% @2.945x.
  **Max ann achievable at capital-real mean gross ≤1.6: ≈18.9–19.1%** (confirms VET_HONESTY ~20%).
- The 80% attempt on the honest FIX machinery (TGT 0.11/0.14): **ann 76.94%, SR_d 4.05,
  MaxDD -7.13% (DD wall BREACHED), 0/19 neg, worst year +21.21%, at all-in gross mean 5.13x,
  p95 10.78x, max 16.51x.** So 80% is not even reached at 5x gross without breaching 7%.

## 9. FINAL GOAL TABLE (honest FIX construction; BAL comparable span unless stated)
| Goal | Achieved (exact) | Verdict |
|---|---|---|
| Ann ≥ 80% | **45.66%** champion; 76.94% = max seen on honest machinery, at 5.13x gross and a DD breach | **FAIL** |
| SR ≥ 5 | **SR_d 4.029 [3.549,4.549]; SR_m 4.095 [3.578,4.794]**; scale-invariant (SR_d 3.68→4.05 across TGT 0.02→0.11); OOS23+ 4.95 best regime | **FAIL** (CI excludes 5) |
| MaxDD ≤ 7% | **-5.60%** (worst 1260d subwindow -5.60%); all champion variants ≤ -6.47%; single-day tail (§7) can breach from any state | **PASS** on history; **conditional** forward |
| lev ≤ 1.6 (capital-real mean) | **3.367x** (p95 6.95, max 10.64; 90.9% of days >1.6); feasible only at ann 18.9% | **FAIL** |
| profit ≥ 0 every year | **0/19, worst +15.12% (2011)**; holds in every swept variant | **PASS** |
**BINDING-DEFINITION STATEMENT:** the 5-goal set is INFEASIBLE on this engine pool, and the
binding constraint is leverage *only when stated in capital-real terms* (all-in gross incl.
the global vt scalar). Under that definition {≤1.6x} caps ann at ~19%; ann≥80 needs ≥5x gross
and still breaches the 7% wall (76.94% @ -7.13%). Under the campaign's older published
definition (EW of per-sleeve scales, global scalar excluded) the gate is vacuous: raising only
the global dial keeps EW-scale ≈1.6x while gross explodes — that definition MUST NOT be used
in any external claim. SR≥5 is unreachable by scaling (SR is scale-invariant ~4.0-4.1 here);
only genuinely new decorrelated high-SR daily engines can move it.

## 10. NEW FINDINGS THIS REVIEW (beyond the charter checklist)
1. Charter metadata errors (§0): comparable-span n is 4616 (not 4522); data end 2026-08-27
   (not 2026-07). The "n=4989" figure is the full-span count.
2. FIX CSVs uncommitted to git (§0) — commit them; the builder reproduces them exactly, so the
   provenance hole closes on commit.
3. Good-Friday rows kept (18 in 2008+, 19 incl. 2008-03-21): mean +5.60bp (range -202.9..+337.4bp);
   dropping them would RAISE ann to 45.80% / SR_d 4.053 (MDD unchanged) — i.e. keeping GF P&L is
   conservative here, unlike L16's adverse-selected inner join. The 75 in-window added rows mean
   +5.07bp vs +15.11bp overall: the rows-kept fix COSTS ~2pp ann — honesty paid for, as designed.
4. Ljung-Box formally rejects white noise (p=1.1e-4) but with conservative sign (§6); squared
   returns are implausibly clean (p=0.99995) — disclosed, not a leak.
5. EVT tail fits are degenerate (negative shape contradicted by own data) — do not quote GEV/GPD
   numbers from this series; use t-df≈2.1 (≈1/34y) or the Poisson bound (≈1/6y) for the 24σ day.
6. Loss tail truncation (max loss -3.68% vs max gain +14.40%, skew +4.29) means MaxDD≤7% history
   overstates safety against a symmetric-gate re-fire (§7 breach math).

## UNVERIFIED (stays UNVERIFIED)
- Instrument-realism/cost-honesty of the 11 sleeve INPUTS (inherited from L16_AUDIT/VET_HONESTY;
  I verified byte-reproduction of the blend, not the underlying fills/borrow data).
- C5ng print-timing open item (inherited); NYSE-vs-federal calendar identity (FIX keeps GFs, so
  the old GF issue is moot, but no exchange-holiday file was independently checked).
- Whether 2026-08 sleeve prints are final (revisions would change the last 19 rows).
- The true effective number of independent trials behind N=500 (DSR verdict is anchor-dependent).

STATS_REVIEW DONE
