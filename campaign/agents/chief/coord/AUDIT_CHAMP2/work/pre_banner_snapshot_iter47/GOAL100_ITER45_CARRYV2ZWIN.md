# GOAL100_ITER45_CARRYV2ZWIN - 21st measured axis: carryv2 zwin slice-2 (2026-09-19, session 25)

Directive: keep improving / leverage <=1.6 / max Sharpe / ann >=20 pct (unchanged set).
Champion of record UNCHANGED by this ITER: campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
(sha16 e67446186e269b88 / weights bde8612d0b295068; current headline cagr 23.68%, FS SR 3.764764,
gross 1.0, ann 23.68% >= 20, leverage 1.0 <= 1.6).

**Verdict: HONEST REJECT on G7** - the reveal passed EVERY operator gate and died only on the
OOS-consistency police: FS SR 3.767238 = +0.002474, cagr 23.7066, MDD -3.6836, 0 neg yrs, gross
1.000000000, Wmax 1.8813x, but bins -0.0011/+0.0064/-0.0037/-0.0114/+0.0015 = 2/5 positive
(needs >=4; min -0.0114 well inside the -0.10 floor) => REJECT per the sealed stop rule. Eighth
consecutive G7 kill; G7 price-tag curve adds +0.0025 (45): +0.0366 (31) / +0.0161 (40) / +0.0075
(33) / +0.0073 (36) / +0.0034 (39) / +0.0026 (30) / +0.0025 (45) / +0.0013 (44).

**Cell**: carryv2 zwin (the crude-brent z-fade lookback; namesake core-engine scalar, pick rules
disclosed at seal time) = slice 2 and the LAST seal of the family under the 38/39 two-slice
standard. Grid {63, 126, 252} = printed acceptance points only (A1 FINDINGS:177). Curve MONOTONE
DECREASING through the anchor: 4.205453 (63, admitted at bar +0.001720 = 466x the disclosed
3.692e-09 fit-landing jitter) / [4.203733 anchor = bar exactly] / 4.200360 (252) - incumbent NOT
the slice IS-argmax, argmax AT the sealed-grid LEFT EDGE (extension forbidden; 43/44 class).
CARRYV2 FAMILY CLOSED: book-tgt (44) + zwin (45) consumed the two-slice envelope; goldL
{126,315} + natgas-month variants remain UNMEASURED remainders (natgas-months additionally
membership-flavored, ITER17-refused class). ROSTER SCALAR PROGRAM EXHAUSTED at 21 measured
axes; census long-tail = the only free-data direction; operator levers unchanged.

**Discipline events** (both fail-closed PRE-computation; champion asserts passed in every run):
run-1 died at A1 (maxdev 1.761e-01, coverage FULL 5179/5179): my derivation-by-substitution
renamed the build parameter tgt->zwin and thereby rewrote the SLEEVE BOOK RE-TARGET site to
(zwin/rv) - a 126 re-target instead of the frozen 0.08 (1575x clipped-scale signature; data
vintages exonerated: committed CSV byte-identical to 44's saved anchor stream). Amendment 1
df8f39e15d0270dc: sleeve line back to the 0.08 literal. Run-2 crashed at the first arm build:
NameError on the missed `s = build_carryv2(tgt)` call site (runtime NameError invisible to
py_compile). Amendment 2 c825c1e0477a80ff: call site fixed, zero lowercase-tgt tokens asserted.
Run-3 GREEN: A1 anchor 9.986e-17 (5179/5179) - re-type proven on the full committed frame;
frozen blocks text-identical to driver_iter43 + driver_iter36; A2 continuity exact (8.327e-17 /
9.991e-17 / IS-SR = bar); champion sha pre==post asserted. The A1/A-gates caught BOTH
coordinator defects before any candidate computation - fail-closed design 2 for 2.

**Landing**: coord/ITER45_CARRYV2_ZWIN complete (precommit+Amendments 1+2, make_driver
persisted, driver_iter45.py, log sha16 0e652e03253388af - first written under the inherited
name driver_iter44.log, renamed post-run, disclosed - 3 arm stream+weights pairs, candidate
pair for-the-record, FINDINGS). test_iter45_carryv2_zwin.py 6 pins, mutation-checked RED
(fake FS-SR caught by 2 pins; fake grid IS-SR caught by 1) -> byte-exact restores
(d331af46b6ff2768 pins / 0e652e03253388af log) -> GREEN. This memo landed BEFORE the suite
per the #120 second-occurrence lesson (lint validates it in-run). Frontier after 45: TWENTY-ONE
axes measured; roster scalar program EXHAUSTED; remaining legal cell family = census long-tail
(~50 unwired IS-fittable series, EV-bounded by the ITER24/17 record); operator levers unchanged
(purchased data / rule change).
