> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
# GOAL100 ITER33 - C5NG CALM-FILTER SCALAR k (SIGNAL-PARAMETER AXIS, LARGEST-WEIGHT FAMILY) - REJECTED ON G7 (2026-09-19, session 15)

Operator objective (unchanged verbatim): keep improving; leverage <= 1.6; maximize
Sharpe; annual return >= 20 pct. Champion of record UNCHANGED:
GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 8559fa55ee9a3417 / weights
d2d11c92a98683df / ann 23.6054 pct / SR 3.751429 / MDD -3.6130 / gross 1.0 /
0 neg yrs. Gauntlet ok 7/7 fresh pre-run this session
(coord/verify_champion_r3_last_session15.json: weights 8.327e-17 / bytes 1.032e-16 /
gross 1.0000000 / SR 3.751428690 / cagr 23.6054).

# THE CELL
ITER32 closed the signal-parameter axis for the dominant TREND sleeve (a6r7 DUR=1.9,
interior IS argmax). The LARGEST committed exposure is the C5ng FAMILY: C5ng 16.47 pct
+ C5ngsum 13.69 pct = 30.16 pct of book weight, both emitted by ONE generator
(e1_idea1: Henry Hub DHHNGSP; Wed/Thu short Fri long weekday premium; calm filter flat
when |lr| > k x trailing-90d sigma shift(1); summer variant Apr-Oct; sleeve cost 6e-4,
T+1, harness vol_target 0.10/min60/cap3) with ONE frozen scalar k=2.5, inherited from
the C5_newdata acceptance era. The acceptance-era report printed a STANDALONE sleeve-SR
k-plateau (1998+ eval, acceptance objective); the BOOK-LEVEL pool-fit IS-SR under the
current operator objective was never measured over k. Grid k in {1.5, 2.0, 2.5(anchor),
3.0, 3.5} - the same 5 points as the acceptance print - SHARED across both variants
(one generator scalar; per-variant grids would be a 25-cell mining surface).
Precommit sealed 923220d3c57bc3e1 BEFORE any candidate (driver hard-asserts the sha);
A1 anchor re-run pre-seal and disclosed inside per the 09-19 re-seal precedent.
Generator RE-TYPED into the driver (importing e1_idea1_ng_detrunc.py would execute its
module-level save_sleeve calls and rewrite live sleeve bytes); A1 proves the re-type.

# RESULT (driver_iter33.log)
- Anchors ALL EXACT: A1 regen-vs-saved 9.975e-17 / 9.996e-17 (n=7381 both, tails
  2026-08-24 both - also proves current DHHNGSP bytes content-identical to the
  sleeve-emission vintage; its Sep-8 mtime irrelevant on this axis). A2 projection
  identity 0.0 exact / weights 8.327e-17 / bytes 9.996e-17 / fit rows 1809 /
  k_covered 11 / incumbent IS-SR 4.198632 / Wmax_sf 1.8115x.
- ADMITTED 3/5 at the 1e-4 jitter bar: k=2.0 (4.199543), k=3.0 (4.204041), k=3.5
  (4.227429). k=1.5 below bar (4.171476, filter too tight). Anchor cell k=2.5:
  weights dev 2.794e-09 / book dev 4.276e-10 (SLSQP boundary-jitter class, inside
  tolerance).
- ONE REVEAL (argmax k=3.5): FS SR 3.758975 = +0.0075 over 3.751429 - SECOND-STRONGEST
  rejected candidate on record (ITER31 A3-at-cap +0.0366, recipe +0.0026, xly -0.0013,
  credit -0.0435). ALL operator gates PASS: cagr 23.5968 pct / gross 1.000000000 /
  MDD -3.5676 / 0 neg yrs / CFX4 0 / Wmax_sf 1.8359x / G8 0.0000. G7 OOS police:
  bins -0.0354 / +0.0594 / -0.2537 / +0.0640 / -0.1256 = 2/5 positive (need >= 4) with
  min bin -0.2537 breaching the -0.10 floor => FAIL => REJECT per sealed stop rule.
  ITER17-law kill 8. Champion sha pre==post True. k=2.0/3.0 UNREVEALED by the stop
  rule.

# READINGS
1. FIRST axis where a novel cell genuinely beats the incumbent INSIDE its own
   one-parameter family on IS (contrast DUR interior-max; ITER22 bar-equality; ITER30
   +0.0009 shadow price). IS-SR RISES with k above the incumbent; the incumbent sits
   in a LOCAL IS DIP between k=2.0 and k=3.0 - k=2.5 was inherited, never IS-argmaxed.
2. The calm filter is doing real OOS-PROTECTIVE work: 2021-22 dSR -0.2537 - the
   energy-crisis regime is exactly when the k=2.5 filter pulls the gas sleeve flat,
   and IS wants that exposure back. Mirror image of the usual overfitting story: the
   freeze is OOS-vindicated against its own IS gradient. A caution against both
   IS-mining AND against assuming frozen = unexamined - the cell had to be measured
   to know the freeze is correct.
3. Second G7-kill data point where the police caught regime fragility rather than
   noise (after ITER31 A3-at-cap): supports KEEP on the +0.0366 price-tag debate.

# FRONTIER AFTER ITER33
ELEVEN axes measured-closed: gear (21), weights (22), grid edges (23), census data
(24/117b/27/28), 8c-era ledger (25), credit-at-cap (26), covariance-target (29),
covariance-target-AT-CAP (31), recipe (30), signal-parameter DUR (32),
signal-parameter C5ng-k (33). Remaining levers UNCHANGED: purchased data or operator
rule change (G7 price tag +0.0366 / 3-of-5 stands, KEEP recommended; ITER33 adds
+0.0075 as a second priced data point). Unmeasured legal cells remaining are
second-tier sleeve parameters (brwt windows, QAxasts 189, dualmom band 121,
diescrack L40/Z20) - each is an acceptance-era frozen scalar of the same class; the
two signal-parameter closures so far (one interior-max, one OOS-vindicated freeze)
bound the expected value of that remainder.

Landed: coord/ITER33_C5NG_KAXIS/ (FINDINGS_PRECOMMIT 923220d3c57bc3e1 + anchor
script + driver_iter33.py + driver_iter33.log + FINDINGS + 5 arm weights CSVs +
candidate_k3.50_daily/_weights.csv for-the-record), test_iter33_c5ng_kaxis.py 6 pins
(mutation-checked RED -> byte-exact restore sha 173275b6dae5a92a -> GREEN), this doc,
STANDUP_LOG, memory 125. SUITE 545 passed / 0 failed (539 + 6, own run, 87.39s).
