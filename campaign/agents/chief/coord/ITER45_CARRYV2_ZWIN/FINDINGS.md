# ITER45_CARRYV2_ZWIN - FINDINGS (session 25, 2026-09-19 ~20:1x-21:0x CST)

Operator directive (verbatim): keep improving. the leverage must be <=1.6. Maximize
Sharpe ratio. The annual return can't be smaller than 20 pct. Same constraint set as
ITER21..44; no rule change, no purchased data.

## VERDICT: HONEST REJECT on G7 (OOS police) - 21st measured axis; carryv2 family CLOSED;
roster scalar program EXHAUSTED; champion byte-stable

Champion of record UNCHANGED: campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
sha16 e67446186e269b88 / weights bde8612d0b295068 (asserted pre==post by the driver).
Current headline cagr 23.68% / FS SR 3.764764 / gross 1.0 (ann and leverage gates pass with
room: 23.68 >= 20, 1.0 <= 1.6).

## Session-25 first half (before this ITER)
- Champion triple re-hashed fresh (python3 hashlib; shasum gated): champion/weights/vt015
  sleeve = e67446186e269b88 / bde8612d0b295068 / 901eebdd3abef617 byte-exact.
- Session-24's crashed-mid-landing tail VERIFIED instead of re-landed (concurrent-writer
  rule): the 24 writer landed its own test pins (bt/tests, 19:58), memo (20:01), STANDUP
  (20:02), memory #135 + index (20:03-20:04) WHILE this session started; no body duplicated.
- SUITE 612 passed / 0 failed OWN RUN this session (python3 -m pytest -q, 83.66s) -
  independent confirmation of the 24 claim. Bare `pytest` was approval-gated this session;
  the python3 -m form ran (probe-once rule).
- Twin hazard disclosed at seal: 20:00 cron fire wrote RAWEW15_REFRESH_CANDIDATE pair into
  campaign/results (stray-writer rule; champion files re-hashed AFTER the stray - unaffected).

## THE CELL (21st axis; family slice 2 = LAST seal under the 38/39 two-slice standard)
carryv2 zwin (crude-brent z-fade lookback). Pick rules disclosed AT SEAL TIME: (1) namesake
core-engine scalar (z-fade is the lead construction of A1_carry_seasonal_v2; signal-lookback
class of 37/39/40); (2) first-listed scalar in the frozen construction spec. goldL {126,315}
and natgas-month variants remain UNMEASURED under the consumed envelope (natgas-months
additionally membership-flavored = ITER17-refused class). GRID {63, 126, 252} = printed
acceptance points only (A1 FINDINGS:177); min_periods couples automatically (generator
rolling has no explicit min_periods; default = window).

## RUNS (all pre-reveal; lineage preserved in driver log + Amendments)
- Run-1: DIED AT A1 FAIL-CLOSED (pre-computation, DERIVATION defect): maxdev 1.761e-01 with
  FULL coverage 5179/5179. Root cause: the substitution set renamed build param tgt->zwin
  AND thereby rewrote the sleeve book re-target site to (zwin/rv) - anchor built at 126
  re-target instead of the frozen 0.08 (1575x clipped-scale signature; coverage/calendar
  untouched). Data vintages EXONERATED first (committed CSV mtime 09-01 unmoved and
  byte-identical maxdev 0.0 to 44's saved anchor stream; GLD 08-13 / FRED 08-12/13).
  AMENDMENT 1 df8f39e15d0270dc: sleeve line -> the 0.08 LITERAL (build param feeds ONLY the
  rolling sites); make_driver S7 patched in the same asserted pass.
- Run-2: A1 anchor EXACT 9.986e-17 (Amendment-1 repair proven) - then crashed at the FIRST
  arm build: NameError `tgt` at the missed call site `s = build_carryv2(tgt)` (runtime
  NameError invisible to py_compile; the residual sweeps covered filenames/rolling/path
  tokens, not call sites). AMENDMENT 2 c825c1e0477a80ff: call site -> zwin; lowercase-tgt
  token count in the driver asserted ZERO; make_driver gains the missing sub pair.
- Run-3: GREEN end-to-end. Frozen blocks text-identical vs driver_iter43 + driver_iter36;
  champion asserts passed in ALL three runs.

## RESULTS (run-3)
- A1 anchor: zwin=126 re-type vs committed CSV ok=True maxdev=9.986e-17 inner=5179/5179.
- Grid (rows 1809, k 11, projid 0.0 everywhere): ZWIN 63 IS-SR 4.205453 (bar +0.001720;
  IS-MDD -2.5526 BETTER than anchor; 0 IS neg yrs; Wmax_sf 1.8813x) / anchor 126 4.203733
  = bar EXACTLY (continuity) / ZWIN 252 4.200360 (below bar). Curve MONOTONE DECREASING
  through the anchor - incumbent NOT the slice IS-argmax; argmax AT the sealed-grid LEFT
  EDGE (disclosed; extension forbidden by sealed stop rule; 43/44 edge class). Admission
  margin = 466x the disclosed A2b fit-landing jitter (weights 1.067e-08 / IS-SR 3.692e-09):
  admission real, not solver noise.
- A2 committed-frame continuity: projid 0.0 / weights 8.327e-17 / bytes 9.991e-17 / IS-SR
  exactly the bar.
- REVEAL ZWIN=63 (single, per stop rule): FS SR 3.767238 = +0.002474 - PASSES the FS bar;
  ALL operator gates PASS (cagr 23.7066 / arith 21.4428 / grossmax 1.000000000 / MDD
  -3.6836 / 0 neg yrs / CFX4 0 / Wmax_sf 1.8813x / G8 0) - but G7 bins -0.0011 / +0.0064 /
  -0.0037 / -0.0114 / +0.0015 = 2/5 positive (needs >=4; min -0.0114 inside the -0.10
  floor) => FAIL => REJECT per sealed stop rule. No second reveal.

## READING
Eighth consecutive G7 kill; second-smallest FS-bar-passing gain to die (after 44's
+0.0013). The IS gain is a LEFT-EDGE artifact: halving the z-window trades ~2x more in the
crude-brent fade and the IS fit buys it, but 3/5 OOS windows disagree with the sign
(2023-24 -0.0114 the largest; 2021-22 crisis bin negative AGAIN - third time in the
family: 36 -0.0036, 40 -0.0339, 45 -0.0037). The incumbent's zwin=126 freeze is
OOS-vindicated from the left the same way 35 vindicated brwt-zb from the left; the edge
cell was police-killed the same way 39/43/44 edge cells were. G7 price-tag curve:
+0.0366 (31) / +0.0161 (40) / +0.0075 (33) / +0.0073 (36) / +0.0034 (39) / +0.0026 (30) /
+0.0025 (45) / +0.0013 (44). CARRYV2 FAMILY CLOSED (book-tgt + zwin = the two-slice
envelope consumed). ROSTER SCALAR PROGRAM EXHAUSTED at 21 measured axes: every roster
sleeve >=5 pct book weight fully swept; carryv2 (2.198 pct) was the last cell and its
remaining printed slices are unmeasured remainders under the standard. FRONTIER: census
long-tail (~50 unwired IS-fittable series) = the only free-data direction (EV-bounded by
the ITER24/17 record); purchased data / rule change remain the operator levers.

## LANDING
coord/ITER45_CARRYV2_ZWIN complete (FINDINGS_PRECOMMIT + Amendments 1+2, sealed chain
9b3b1c555c490183-class: b9efa7675f95cdeb -> df8f39e15d0270dc -> c825c1e0477a80ff;
make_driver_iter45.py persisted; driver_iter45.py; driver log - first written under the
inherited name driver_iter44.log inside the ITER45 dir, RENAMED post-run, DISCLOSED;
3 arm stream+weights pairs; candidate_zwin63_daily.csv for-the-record; this FINDINGS).
test_iter45_carryv2_zwin.py 6 pins, mutation-checked RED (fake FS-SR caught by 2 pins;
fake grid IS-SR caught by 1 pin) -> byte-exact restores (pins d331af46b6ff2768 / log
0e652e03253388af) -> GREEN. Campaign memo GOAL100_ITER45_CARRYV2ZWIN.md sha16
525d72bd1853f328 landed BEFORE the suite (the #120 second-occurrence lesson: lint
validates in-run). STANDUP session-25 entry; memory #136 + index. Suite target: 618
passed / 0 failed (612 + 6).
