# ITER32 FINDINGS_PRECOMMIT - DUR-AXIS (signal-parameter) SWEEP. SEALED BEFORE ANY ITER32 CANDIDATE COMPUTATION.

Session 14 (2026-09-19 ~08:15 CST). Operator objective (5th verbatim resend):
keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return
cannot be smaller than 20 pct.

## VERIFIED-FIRST (pre-seal)
- Gauntlet 7/7 GREEN fresh this session (coord/verify_champion_r3_last_session14.json,
  08:10): weights 8.327e-17 / bytes 1.032e-16 / gross 1.0000000 / cost full-dw ratio
  1.000000000004974 / causality causal + truncation 0.0 / 0 neg yrs / MDD -3.6130.
  SR 3.751428690 / cagr 23.6054 / n 4806 / end 2026-08-28.
- Champion shas: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv 8559fa55ee9a3417 /
  RAWEW13v2_IS_SR_weights.csv d2d11c92a98683df. coord/ quiet since 07:27 (ITER31).
- Item 123 AUDIT FLAG CLOSED: RAWEW15_REFRESH_CANDIDATE_* re-emitted 07:30:16 CST with
  bytes IDENTICAL to the session-13 sha16s (dc3d7c9e / 8c19ef22) => deterministic
  refresh of a dead OPT_V-family artifact, zero drift; writer NOT quantum-gpt (no
  references), NOT the cron skip path (07:30 fire was lock-skipped); champion pin
  graph unaffected.
- CONCURRENT-WRITER DISCLOSURE: cron job_fe286bf39cb9 (same operator prompt) fired
  08:00:00 CST and is RUNNING at seal time. House convention applies (re-read topic
  file at write time; merge as sub-entries). This session proceeds; a twin landing
  before mine will be merged, not overwritten.

## THE CELL
The number-120 recipe sweep (ITER30) froze the a6r7 generator SIGNAL parameter
DUR=1.9 while sweeping only the TRADING recipe (K x CAD x VT x CAP). DUR is the
coefficient of -dy in the legacy generator total-return proxy
tr = (-DUR * y.diff() + y / 252) and is the LAST unswept scalar of the champion
dominant sleeve. This iteration measures it: a one-parameter family of an EXISTING
census sleeve (a6r7/DGS2). No new data, no operator rule change. Legal basis
identical to ITER30 (operator objective; IS fit -> admit -> ONE reveal -> gates).

## FROZEN (byte-frozen for every cell)
K=378, CAD=42, T+1 (W.shift(1)), sleeve-internal cost = LEGACY 6.0bp FULL |dWsig|
(NOT the 6.4bp transplant: this axis lives INSIDE the legacy sleeve own convention;
anchor A2 must byte-reproduce the saved stream at DUR=1.9, expected ~1e-16),
expanding(60) VT=0.12 CAP=5.0; DGS2 source
tools/quant/hedge_fund_strats/data_fred_new/DGS2.csv;
pool = the 12 committed slots (rawew13v2_build NAMES/PATHS) byte-frozen; gear 1.0;
SHRINK 0.70 diag; brwt-cap 0.30; CFX4 relw pinned 0; Wmax_sf <= 2.0 at k_covered=11
(number-120 canonical convention); IS_END 2017-01-01; START 2008-03-31.
GRID: DUR in {1.40, 1.65, 1.90(anchor), 2.15, 2.40} - 5 cells, 4 novel, symmetric
+/-0.25 and +/-0.50 around the incumbent coefficient.

## ANCHORS (fail-closed, before any novel cell)
A1 shas of champion / weights / saved a6r7 sleeve.
A2 legacy generator at DUR=1.9 vs saved E1_a6r7_bond2y_trend_1990.csv: max dev < 1e-12.
A3 pool mirror: champion bytes < 1e-12 AND weights < 1e-9 AND IS-SR 4.198632
continuity (<5e-6) AND projection identity exactly 0.0 on the feasible incumbent.
Coverage law (ITER30 A2 lesson class): a scalar DUR cannot change the NaN pattern, so
every cell MUST produce fit rows == 1809 and k_covered == 11 - asserted fail-closed.

## ADMISSION (IS level, per cell)
is_sr > 4.198632 + 1e-4 (jitter tolerance, ITER31 formula) AND Wmax_sf <= 2.0+1e-9
AND IS MDD >= -6 pct AND 0 IS neg years.

## REVEAL + STOP RULES
ONE global argmax among admitted cells (sort: is_sr desc, then |DUR-1.9| asc, then
label). Reveal gates 1-8 VERBATIM ITER31 (FS ann>=20 pct, gross<=1.6, MDD>=-7 pct,
0 neg yrs, CFX4=0, Wmax_sf<=2.0x k=11, G7 OOS police [>=4/5 bins positive AND min bin
>= -0.10 AND FS-SR > 3.751429], fit-window shrink<=2 pct). NO admission -> honest
negative, no reveal. Any gate FAIL -> REJECT, no second reveal. Driver asserts
champion sha pre==post.

## SEALED
This file sealed BEFORE any novel-DUR stream is generated or fitted. Driver
driver_iter32.py hard-asserts sha16(this file) equals the sealed digest recorded in
its header, and aborts on any mutation.
