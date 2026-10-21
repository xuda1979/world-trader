# ITER44_CARRYV2_BOOKTGT - FINDINGS (session 24, 2026-09-19 ~20:1x-20:3x CST)

Operator directive (verbatim): keep improving. the leverage must be <=1.6. Maximize
Sharpe ratio. The annual return can't be smaller than 20 pct. Same constraint set as
ITER21..43; no rule change, no purchased data.

## VERDICT: HONEST REJECT on G7 (OOS police) - 20th measured axis; champion byte-stable

Champion of record UNCHANGED: campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
sha16 e67446186e269b88 / weights bde8612d0b295068 (asserted pre==post by the driver).
Current headline cagr 23.68% / FS SR 3.764764 / gross 1.0.

## Session-24 first half (before this ITER)
- Independent verification of the session-23 ITER43 ADOPTION: six sha16 identities
  byte-exact; own gauntlet run 7/7 dev-for-dev identical
  (verify_champion_r3_last_session24.json); full suite OWN RUN 606 passed / 0 failed
  AFTER fixing one landing-gap defect: GOAL100_ITER43_A5R2VT.md (landed after the
  session-23 suite) tripped the round4b billing lint on the NEXT run - fix = the lint
  own additive prescription (champion filename + 23.68% headline, line 5). #120 race
  class, second occurrence: landing docs after the suite is only safe if they are
  lint-clean BEFORE the next suite runs; the "after the suite" convention does not
  discharge the duty to re-run.

## THE CELL (20th axis)
carryv2 (E1_carryv2_GLD_2006.csv, 2.198 pct book weight) = the last roster sleeve with
zero campaign-swept scalars. Slice 1 of the printed acceptance plateau (14 neighbors,
A1 FINDINGS line 177 / LOG_r3): BOOK-TGT {7, 8, 9} pct, printed points only, anchor
8 = byte-identity role, bar-ineligible. Weight-grid slice REFUSED (mining surface);
zwin / goldL / natgas-month slices remain unmeasured (38/39 slice-2 eligible).

## RUNS (both pre-reveal, preserved in driver_iter44.log lineage)
- Run-1: DIED AT A1 FAIL-CLOSED (pre-computation, re-type defect): values exact
  (9.986e-17) but coverage 5002 vs 5179 - my re-type wrongly applied the generator
  line-55 STATS-WINDOW cut (2007-06+, the .meta "Eval" wording) to the EMISSION; the
  generator line-88 saves the UNCUT sleeve (2006-09-27 GLD-start .. 2026-08-03
  natgas/brent tail). Amendment 1 sealed 0c1ef55af88b6cd2 BEFORE the corrected run;
  repair = return the full sleeve (fit window unaffected; frame starts 2008-03-31).
- Run-2 (amended): GREEN end-to-end. A1 anchor recon ok=True maxdev=9.986e-17
  inner=5179/5179 FULL coverage (re-type proven on the whole committed frame incl.
  the pre-2008 head the book never sees). Frozen-block AST identity vs driver_iter43
  AND driver_iter36 GREEN at run start. Champion pair asserted pre-run.

## RESULTS
- Grid (rows 1809, k 11, projid 0.0 everywhere): TGT 0.07 IS-SR 4.203086 (BELOW bar) /
  anchor 0.08 4.203733 (= new incumbent bar, continuity) / TGT 0.09 4.204230 = bar
  +0.000497 ADMITTED (is_mdd -2.56, 0 IS neg yrs, Wmax_sf 1.8671x). Curve RISES
  monotonically through the anchor to the printed EDGE - the incumbent is NOT the
  slice IS-argmax (dualmom-win shape, class #3-after-36/39... actually the FOURTH
  edge/interior split of this kind: 33 local-dip, 36/40 interior-off-argmax, 39
  edge-max, 44 edge-max-at-tiny-weight).
- A2 committed-frame continuity: projid 0.0 / weights 8.327e-17 / bytes 9.991e-17 /
  IS-SR exactly the bar. A2b regen-vs-committed fit-landing jitter DISCLOSED:
  weights 1.067e-08, IS-SR 3.692e-09 -> the admitted margin (+4.97e-4) is ~134x the
  IS-SR jitter: admission is real, not solver noise.
- REVEAL TGT=0.09 (single, per stop rule): FS SR 3.766058 = +0.001294 - PASSES the FS
  bar; ALL operator gates PASS (cagr 23.6909 / arith 21.4300 / grossmax 1.000000000 /
  MDD -3.6665 / 0 neg yrs / CFX4 0 / Wmax_sf 1.8671x / G8 0) - but G7 bins
  +0.0001 / +0.0023 / -0.0004 / -0.0024 / +0.0018 = 3/5 positive (needs >=4) =>
  FAIL => REJECT per sealed stop rule. No second reveal.

## READING
SMALLEST-MAGNITUDE G7 KILL ON RECORD that still passed every operator gate (all
|dSR| <= 0.0024; prior minimum bin magnitudes were ~10x larger). The police binds on
CONSISTENCY, not magnitude - now measured down to the 1e-3 scale (30/36 structure-
noise family; 39 remains the only 3/5 exhibit with economically meaningful size).
G7 price-tag curve: +0.0366 (31) / +0.0161 (40) / +0.0075 (33) / +0.0073 (36) /
+0.0034 (39) / +0.0026 (30) / +0.0013 (44). At 2.2 pct book weight the sleeve moves
the book by ~covariance-shadow prices; the OOS windows cannot agree on the sign of a
+1.3e-3 effect. The freeze is OOS-vindicated for the second time on a printed-grid
cell (33 class) AND the IS edge-max shape is police-killed (39 class) - both closure
shapes in one cell. Slice 1 CLOSED. Frontier: TWENTY axes measured under the current
objective; remaining legal cells: carryv2 zwin/goldL/natgas-month slices (printed,
38/39-eligible), census long-tail (~50 unwired IS-fittable series, EV-bounded by the
ITER24/ITER17 record); operator levers unchanged (purchased data / rule change).

## LANDING
coord/ITER44_CARRYV2_BOOKTGT complete (precommit+Amendment 1, driver_iter44.py 2-chunk
heredoc w/ py_compile gate, driver log, 3 arm stream+weights pairs, candidate pair
for-the-record, FINDINGS). test_iter44_carryv2_booktgt.py 6 pins, mutation-checked.
Campaign memo GOAL100_ITER44_CARRYV2BOOKTGT.md landed AFTER the suite, lint-clean BY
CONSTRUCTION (names the champion file + 23.68% headline). STANDUP session-24 entry;
memory #135 + index. Suite target: 612 passed / 0 failed (606 + 6).
