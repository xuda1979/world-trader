# ITER24 FINDINGS - DATA-AXIS WAVE 1 (rates families): ALL 5 CANDIDATES REJECTED. Champion UNCHANGED.

Session: 2026-09-19 (session #6 on the operator objective, verbatim unchanged). Pre-commit:
FINDINGS_PRECOMMIT.md (sealed before any candidate return was computed; Amendment 1
pre-reveal). Driver: driver_iter24.py (parts 1-3, deterministic). Artifacts: part1_hygiene.json,
part2_candidates.json, part3_trials.json, sleeve_*.csv (this dir). Anchor: byte dev 9.996e-17,
weights dev 8.3e-17 vs the committed champion; B0 rebuild = n 4806 / SR 3.7514287 / CAGR
23.6054% / MDD -3.6130% EXACT. Causality probes (G9): all five sleeves 0.0 exact.

## Result table (book = incumbent 12-pool + slot, frozen weight rule, gear 1.0)
bar = max(B0.SR, Bwm.SR) = 3.7514 (BwmSR 3.7485 in every trial - the window effect is tiny).

| slot      | book SR | CAGR%  | OOS dSR vs B0 | bins pos | verdict |
|-----------|---------|--------|---------------|----------|---------|
| bund2y    | 3.7253  | 23.207 | -0.0036       | 2/5      | G1+G5 FAIL |
| bund10y   | 3.7420  | 23.378 | -0.0019       | 2/5      | G1+G5 FAIL |
| cad2y     | 3.7297  | 23.190 | -0.0033       | 2/5      | G1+G5 FAIL |
| cad10y    | 3.7388  | 23.475 | -0.0011       | 1/5      | G1+G5 FAIL |
| seliccary | 3.7528  | 23.620 | -0.00002      | 3/5      | G5 FAIL (G8 2.54%>2%) |

KEPT: none. Champion of record UNCHANGED: 8559fa55ee9a3417 / weights d2d11c92a98683df /
SR 3.751429 / CAGR 23.6054% / leverage 1.0 (<= 1.6 operator cap) / ann floor satisfied.

## What was learned (the honest negatives, each pre-committed)
1. The four RATE-TREND transplants fail G1 outright and G5 confirms it OOS: decorrelated
   positive-IS-SR sleeves (IS SR 0.83-1.26, corr to the pool <= 0.13 except cad-vs-a6r7
   0.56-0.65) still LOSE FS SR under the frozen max-Sharpe fit because the incumbent
   sleeves' IS SR (~3-4) dwarfs theirs; the fit's marginal allocation to them dilutes
   more than their diversification adds at gross 1.0. The EUR/DM rates families
   (bund_daily, dm_rates-CAD) are CLOSED on the a6r7 trend recipe - like ITER18, recorded
   as a family-level no-edge, not a recipe-tuning invitation (no parameter search allowed).
2. seliccary is the ITER17-law exhibit: it PASSES G1 nominally (3.7528 > 3.7514) and even
   the retired dAnn>0 gate (+0.014pp CAGR) - and dies on OOS honesty: full-OOS dSR vs B0
   is -2e-5/day (zero-to-negative), 3/5 bins positive vs the >=4 required. The IS fit
   liked its 2008-2016 carry-trend pattern; 2017+ contributes nothing. This is exactly
   the failure shape the 5-bin gate exists to catch. EM-carry (selic+usdbrl) CLOSED.
3. Hygiene screens passed cleanly after eyeball: the four yield series had zero >100bp
   spikes and <=10-day flat runs; selic units VERIFIED as daily percent ((1.000522)^252-1
   = 14.0%/yr = the 2025-26 target; (1.00154)^252-1 = 47.6%/yr = post-Real 1995); usdbrl
   has exactly ONE >10%/day relative move ever (1999-01-15 float, +11.1%) - the 137
   absolute-unit "spikes" were a screen mis-scale, all flagged moves are the 1999 float /
   2002 election crisis / 2008 GFC, real events.
4. The Bwm (window-matched) baseline design paid off: BwmSR was 3.7485 in every trial vs
   B0 3.7514 - the 0.003 gap is pure date-union arithmetic (candidate-holiday zero-days),
   not signal; and fit-window shrink measured 1.44% (bund) / 1.60% (cad) / 2.54% (selic).
5. G7 normalization note (disclosed): the printed wmax_ratio divides by 1/13 (all slots
   incl. the IS-dead CFX4). The fit's own cap is 2x equal over the IS-covered set (the
   two-stage solver that reproduces the committed weights byte-exactly enforces 2/k_have
   by construction). Under the have-set normalization all trials satisfy the cap within
   solver tolerance (cad10y 1.88x; seliccary ~2.00x at 1.4e-4 slack). No trial was
   adopted-or-rejected ON G7; the decisive gates were G1/G5/G8.

## Frontier after ITER24-wave-1
In-family (gear/weights/edges): exhausted (#115/#116). Data axis wave 1 (rates + EM carry):
exhausted this session. Charted and OPEN for the next iteration: (a) cboe_hist vol complex
(VIX/VIX6M/VVIX term structure; A5r2 mines contango already - a wave-2 transplant must
read the A5r2 construction and pre-commit its own recipe; no VIX-futures cost model exists
in-repo yet, which may be disqualifying); (b) eia_weekly energy spots (WTI/Brent/gasoline
cracks - diescrack already mines the diesel crack; correlation screening required first).
Both face the same gates. The pool-geometry lesson of this wave stands: at gross 1.0 with
the frozen fit, a new sleeve must bring OOS-real marginal Sharpe, not just decorrelation.
