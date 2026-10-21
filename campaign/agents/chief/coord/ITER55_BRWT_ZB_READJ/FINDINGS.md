# ITER55 FINDINGS - BRWT-ZB STALENESS RE-ADJUDICATION (2026-09-20, session 35)

HONEST NEGATIVE / SECOND CERTIFICATE RE-AFFIRMATION ON RECORD. NO-ADMISSION 0/7, no reveal,
no candidate CSV (none may exist under no-admission). Champion UNCHANGED
cfa9ec4d38158691 / a384d6b92e258fd5 / SR 3.820357 / cagr 23.9215 / gross 1.0.
Precommit sha16 3d9e4163bff420b1 SEALED BEFORE any candidate; driver hash-asserts it.

## Verification-first
- Gauntlet ok=true 7/7 fresh (verify_champion_r3_last_session35.json): weights 7.632783294297951e-17
  / bytes 1.0408340855860843e-16 / half-turn rejected 1.644349418787801e-05 / gross
  1.0000000000005784 n_over 0 / SR 3.8203573009568794 / cagr 23.92147218901779 / MDD -3.7339
  / turnover 4.331113668256489 bp/yr / n 4806 - EVERY digit identical to s32/s33/s34.
- Champion pair re-hashed intact; vt015 c40d008ddbf7c579 / vt024 7ec85336e7f7d00f intact;
  parent driver_iter54 c5c7855346fbd31c intact.
- BAR 4.218504 fresh-grepped (driver_iter52.log line 11); FS_BAR 3.820357 from the fresh gauntlet.
- Baseline suite 672 passed / 0 failed (own run, 74.81s). Coord quiet (last write 04:24 s34 standup).
- Stray writers: 16 claude-ish procs = this session + OTHER-repo prompts (quantum,
  independent_papers, cmri wrappers, 6 --bare); NO world-trader coord-writing batch.

## THE CELL (31st measured axis - the LAST remaining staleness cell)
brwt trio 30.0000 pct (recomputed 9.9772 + 9.1924 + 10.8304, EXACTLY at the 0.30 block cap),
ONE shared generator scalar zb=1.0 (Brent-WTI log-spread rolling-z reversion threshold).
Certificate ITER34+35 (session 16): STITCHED FULL INTERIOR-MAX at zb=1.0 (left monotone rising
3.897552/4.057100/4.175140 into the anchor; right monotone falling 4.060778/3.884666/3.477293/
3.230354 away) - strongest closure shape, NO police consumed. Cert predates the 43/47/49
rescales; staleness runs through the FIT covariance only (#48 law); fit now WALL-ADJACENT
(1.9736x vs 1.8115x at cert frame) and the cert-frame geometry had Wmax RISING toward the wall.

## Legality (precommit 1-6)
vt = harness DEFAULT (0.10) - trio design treatment, #131/#142 audits recorded covered,
sweeping vt/lb = re-running sealed/refused cells = refused. Grid = ITER34 UNION ITER35
stitched VERBATIM, 8 points, anchor-first, ZERO new points, no envelope extension (zb=0
degenerate stays outside; finer pitch refused). ADMISSION ADDENDUM pre-registered: projid == 0.0
required (a projected arm = wall breach = inadmissible, the ITER50 convention; project_wmax
retained only as the identity-on-feasible check). D17: r6lib-FREE chain, iter51-form inert
patch retained. Driver = driver_iter54.py via asserted substitutions (make_driver_iter55.py
verifies rebuild == landed bytes; final count 16 subs after the defect repairs below).

## Probes (pre-seal, probe_iter55_a1.log)
A1 brwt10/7/5 regen-vs-committed ok=True maxdev 9.999e-17 (n=6567 FULL) / 9.986e-17 (4580) /
9.996e-17 (4580) - EXACTLY the cert-frame digits: generator AND brent/wti vintages bit-stable
(fred mtimes 08-12, eia 09-06/09-07, proven content-identical by the devs). Regen tails reach
09-01 vs committed cut 08-28 (post-frame, unreachable - iter36 disclosure class).
Calendar-vs-zb: index IDENTICAL (threshold-only scalar). vt-clip bound_frac 0.000000 all three
(clean case, not the iter53 CAP-saturation class).

## RUN (driver_iter55.py sha16 c607d7fa9d90e9a5, log sha16 efe59d15ffbf4048)
A1 in-driver EXACT (same three digits, FULL). A2 committed-frame continuity EXACT: projid 0
/ weights 7.633e-17 / bytes 9.991e-17 / rows 1809 / k 11 / IS-SR 4.218504 = bar BOTH sides.
A2b jitter: weights 1.050e-08 / IS-SR 6.066e-10 (SLSQP landing class, iter52 3.249e-09 cousin;
admission margin ~9,500x above the IS-SR jitter).

CURVE (current frame; cert-frame value in parens):
  zb=0.25  3.904022 (3.897552)  projid 0        Wmax 1.9273x (1.8017x)
  zb=0.50  4.067581 (4.057100)  projid 0        Wmax 1.9702x (1.8243x)
  zb=0.75  4.189759 (4.175140)  projid 1.878e-04  Wmax 2.0000x PROJECTED (1.8385x) WALL-CAPTIVE
  zb=1.00  4.218504 (4.198632)  projid 0        Wmax 1.9736x (1.8115x)  = ANCHOR = BAR
  zb=1.25  4.072818 (4.060778)  projid 0        Wmax 1.9428x (1.7859x)
  zb=1.50  3.897461 (3.884666)  projid 0        Wmax 1.8800x (1.7584x)
  zb=1.75  3.488150 (3.477293)  projid 0        Wmax 1.8383x (1.7148x)
  zb=2.00  3.237666 (3.230354)  projid 0        Wmax 1.8247x (1.9867x)

## VERDICT AND READINGS
1. CERTIFICATE RE-AFFIRMED: strictly single-peaked at the incumbent zb=1.0 at BOTH frames
   (left 3.904 < 4.068 < 4.190 < 4.2185; right 4.2185 > 4.073 > 3.897 > 3.488 > 3.238).
   The rescale lifted the whole curve ~+0.006..+0.013 but moved the RANKING not at all.
   Second re-affirmation of the staleness class (after ITER54) and the FIRST PURE one: the
   cert-frame closure consumed no reveal and this re-adjudication consumes none - the
   interior-max certificate re-certifies with zero police involvement on either side.
2. THE ADDENDUM FIRED: zb=0.75 is the FIRST wall-captive cell of the brwt family (projid
   1.878e-04 -> projected to exactly 2.0000x; at the cert frame it sat at 1.8385x). Belt-
   and-suspenders here - the arm is ALSO below bar (4.189759 < 4.218604) so IS-SR alone
   denies admission - but the pre-registered rule did real work, and the near-miss (bar
   minus 0.0287) would have been the closest cell without it. HONESTY NOTE: had 0.75
   cleared the bar, the addendum (not IS-SR) is what would have excluded it - disclosed
   as pre-registered in the precommit before the run.
3. WALL GEOMETRY (new reading): the rescaled fit re-ranked concentration across the curve.
   The whole mid-curve shifted UP ~+0.09..+0.13x (0.25: +0.126, 0.50: +0.146, 0.75: +0.16+,
   anchor: +0.162, 1.25: +0.157, 1.50: +0.122, 1.75: +0.124) while the FAR RIGHT FELL
   (2.00: 1.9867x -> 1.8247x, -0.162) - the iter34 monotone-toward-the-wall reading does
   NOT survive the rescale; only the incumbent's neighborhood is now wall-hugging. The
   2.0x Wmax wall remains the binding geometry of the fit (+0.024 IS-SR behind it, the
   operator item unchanged).
4. STALENESS-CLASS LEDGER - SHAPE TAXONOMY NOW COMPLETE WITH ALL THREE SHAPES MEASURED:
   plateau (50 solver / 51 c5ng-vt / 52 tsmom-MAW), movement (53 a6r7-DUR, the only one),
   re-affirmation (54 c5ng-k with police re-fire, 55 brwt-zb pure). Plateau count of
   SOLVER-family certs stays SIX (22/29/30/50/51/52). Acceptance-era freeze #6 (brwt-zb)
   joins the vindicated list: every sealed scalar of the roster now carries a CURRENT-FRAME
   certificate.

## FRONTIER STATEMENT
31 axes measured-closed. ZERO remaining staleness cells (the per-session-cell program is
EXHAUSTED): gear 21 / weights 22 / grid-edges 23 / census 24+117b+27+28+46 / 8c-ledger 25 /
credit-at-cap 26 / solver 22+50 / cov-target 29+31 / recipe 30 / DUR 32+53 / c5ng-k 33+54 /
brwt-zb 34+35+55 / diescrack-Z 36+40 / tsmom-MAW 37+52 / dualmom 38+39 / vt-overlay 41 /
brwt15-readmit 42 / a5r2-vt 43+47 / carryv2 44+45 / c5ng-vt 48+51 / tsmom-vt 49.
Remaining levers UNCHANGED and now the ONLY levers: (a) purchased data outside the census
(regional basis, VIX futures, EM local-curve composites), (b) operator rule change with
recorded price tags (Wmax relaxation up to +0.024 IS-SR at the current wall; G7 relaxation
- police approved 2 of 12 reveals; the 39 WIN=150 3/5 exhibit remains the only pass-the-
literal-objective kill). NO self-relax (the #109/#116/#118 law).

## DEFECTS DISCLOSED (this session, caught fail-closed)
1. INHERITED LOG FILENAME (D19 class, three sites): the driver's final open() wrote
   driver_iter54.log; the hygiene sweep then caught the print("LOG WRITTEN: ...") line too;
   the make_driver hygiene list itself needed the token. Root cause: my hygiene token list
   was case-sensitive ("ITER54") while the filename is lowercase. Fixed by R15+R16
   substitutions; driver re-run THREE times total, all three runs byte-identical in
   science content and the final log sha16 efe59d15ffbf4048 is the FIRST run's content
   verbatim (the LOG list never contained the filename) - the repair is proven cosmetic.
2. A stray sentence in iter54's make_driver print (14/14 hardcoded) - fixed to format the
   count; cosmetic, caught in review.

## Artifacts (this dir)
FINDINGS_PRECOMMIT.md 3d9e4163bff420b1 (sealed pre-candidate) / probe_iter55_a1.py+log /
make_driver_iter55.py (rebuild == landed, 16/16) / driver_iter55.py c607d7fa9d90e9a5 /
driver_iter55.log efe59d15ffbf4048 / 32 arm files (8 arms x [3 streams + weights]) /
NO candidate CSV. Pins: campaign/bt/tests/test_iter55_brwt_zb_readj.py (6, mutation-checked).
Memo: campaign/GOAL100_ITER55_BRWTZB_READJ.md. Suite: 678 expected (672 + 6).
