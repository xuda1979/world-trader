# GOAL100 ITER55 - BRWT-ZB SCALAR STALENESS RE-ADJUDICATION AT THE CURRENT CHAMPION

Session 35, 2026-09-20. HONEST NEGATIVE - SECOND CERTIFICATE RE-AFFIRMATION ON RECORD (first
PURE one: no police consumed at either frame). NO ADOPTION. Champion of record UNCHANGED:
campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 cfa9ec4d38158691 / weights
a384d6b92e258fd5 / FS SR 3.820357 / cagr 23.92 pct / gross 1.0 / MDD -3.7339 pct / 0 neg yrs.

## The cell (31st measured axis - the LAST remaining staleness cell)
The brwt trio (brwt10 + brwt7 + brwt5, 9.9772 + 9.1924 + 10.8304 = 30.0000 pct recomputed
fresh - EXACTLY at the 0.30 brwt-block cap, unchanged from the cert frame) shares ONE generator
scalar zb=1.0: the Brent-WTI log-spread rolling-z mean-reversion threshold (pos = +1 when z <
-zb, -1 when z > zb, else flat; lb 10/7/5 with min_start 2000/2008 = variant identity; a
per-variant grid would be a mining surface and is refused). Certificate = ITER34+ITER35
(session 16): right side MONOTONE FALLING from the anchor, left side MONOTONE RISING INTO it -
STITCHED FULL INTERIOR-MAX at zb=1.0, the strongest closure shape, NO reveal consumed, NO
police verdict exists on this axis. The cert predates the THREE adopted rescales (ITER43/47/49)
- NONE touched the brwt files (A1 re-proves the committed streams at the exact cert-frame
digits) - the staleness runs entirely through the FIT covariance per the #48 law; the rescaled
fit is WALL-ADJACENT (1.9736x vs 1.8115x at cert frame) and the cert-frame geometry had Wmax
RISING toward the wall with zb (1.9867x at zb=2.0).

## Legality (recorded AT SEAL, precommit 3d9e4163bff420b1, 7054 bytes, sealed pre-candidate)
The brwt vt scalar is the HARNESS DEFAULT (vol_target(net) = vt_ann 0.10, min 60, clip 3.0) -
the #131/#142 coverage audits recorded the trio FULLY covered (zb sealed 34/35, per-variant lb
REFUSED mining surface - stays refused, vt = design treatment); sweeping vt or lb here =
re-running sealed/refused cells = ILLEGAL. Grid = ITER34 UNION ITER35 stitched VERBATIM:
{1.0 anchor, 0.25, 0.50, 0.75, 1.25, 1.50, 1.75, 2.00} - all 8 cert-frame points, anchor-FIRST
presentation, ZERO new points, NO envelope extension (zb=0 degenerate always-in stays outside
per iter35; finer pitch refused). ADMISSION ADDENDUM pre-registered BEFORE the run: projid ==
0.0 required (a projected arm = wall breach = INADMISSIBLE per the ITER50 convention recorded
in #141; project_wmax retained only as the identity-on-feasible check). Frozen in every arm:
pool 12 slots byte-frozen (B.PATHS LIVE = A5r2 vt024 + QAxasts vt015), gear 1.0, SHRINK 0.70,
brwt-cap 0.30, CFX4 relw 0, Wmax_sf <= 2.0 at k 11, BAR 4.218504 (fresh-grepped
driver_iter52.log line 11), FS_BAR 3.820357 (fresh gauntlet). D17 SCOPE: the chain is
r6lib-FREE; the iter51-form single-identity harness patch retained as the documented inert
safety patch. Driver = driver_iter54.py via asserted-exactly-once substitutions, verified by
make_driver_iter55.py (rebuild == landed bytes, 16/16 after the defect repairs below).

## Verify-first (pre-seal)
Gauntlet ok=true 7/7 fresh (verify_champion_r3_last_session35.json: weights 7.632783294297951e-17
/ bytes 1.0408340855860843e-16 / half-turn rejected 1.644349418787801e-05 / gross
1.0000000000005784 n_over 0 / SR 3.8203573009568794 / cagr 23.92147218901779 / MDD -3.7339 /
turnover 4.331113668256489 bp/yr / n 4806) - EVERY digit identical to s32/s33/s34. Champion
pair + vt015 c40d008ddbf7c579 + vt024 7ec85336e7f7d00f + parent driver_iter54 c5c7855346fbd31c
re-hashed intact. Baseline suite 672 passed / 0 failed (own run 74.81s). Coord quiet. Stray
writers: 16 claude-ish procs = this session + OTHER-repo prompts only, no coord-writing batch.

## Pre-seal probes (probe_iter55_a1.log, BEFORE the seal)
A1 regen-vs-committed ok=True at the EXACT cert-frame digits: brwt10 9.999e-17 (inner 6567
FULL) / brwt7 9.986e-17 (4580) / brwt5 9.996e-17 (4580) - generator AND brent/wti vintages
bit-stable since session 16 (fred mtimes 08-12, eia 09-06/09-07, proven content-identical by
the devs; regen tails 09-01 vs committed cut 08-28 = post-frame, the iter36 disclosure class).
Calendar-vs-zb probe: index IDENTICAL (threshold-only scalar). vt-clip probe: bound_frac
0.000000 ALL THREE variants - the default-vt treatment is nowhere near its clip (the iter54
clean case, not the iter53 a6r7 CAP-saturation class). Trio share recomputed 30.0000 pct; max
share C5ng 17.9422 pct -> 1.9736x (matches the record).

## RUN (driver_iter55.py sha16 c607d7fa9d90e9a5, log sha16 efe59d15ffbf4048, THREE runs
byte-identical) - A2 committed-frame continuity EXACT (projid 0 / weights 7.633e-17 / bytes
9.991e-17 / rows 1809 / k 11 / IS-SR 4.218504 = bar BOTH sides); A2b jitter weights 1.050e-08 /
IS-SR 6.066e-10 (SLSQP landing class; admission margin ~9,500x).

CURVE (current frame; cert-frame in parens):
  0.25  3.904022 (3.897552) projid 0         Wmax 1.9273x (1.8017x)
  0.50  4.067581 (4.057100) projid 0         Wmax 1.9702x (1.8243x)
  0.75  4.189759 (4.175140) projid 1.878e-04 Wmax 2.0000x PROJECTED - WALL-CAPTIVE (1.8385x)
  1.00  4.218504 (4.198632) projid 0         Wmax 1.9736x (1.8115x) = ANCHOR = BAR
  1.25  4.072818 (4.060778) projid 0         Wmax 1.9428x (1.7859x)
  1.50  3.897461 (3.884666) projid 0         Wmax 1.8800x (1.7584x)
  1.75  3.488150 (3.477293) projid 0         Wmax 1.8383x (1.7148x)
  2.00  3.237666 (3.230354) projid 0         Wmax 1.8247x (1.9867x)

ADMISSION EMPTY (0/7; every arm below bar+1e-4, 0.75 additionally wall-captive) -> NO reveal
per the sealed stop rule -> honest negative. Champion sha16 pre==post driver-asserted.

## Readings
1. CERTIFICATE RE-AFFIRMED: strictly single-peaked at the incumbent zb=1.0 at BOTH frames; the
   rescale lifted every cell ~+0.006..+0.013 and moved NO ranking. Second re-affirmation of
   the staleness class (after ITER54) and the FIRST PURE one - an interior-max certificate
   re-certifies with zero police involvement on either side.
2. THE ADDENDUM FIRED: zb=0.75 = the family's FIRST wall-captive cell (projid 1.878e-04 ->
   projected to exactly 2.0000x; cert frame 1.8385x). Belt-and-suspenders here (the arm is
   ALSO below bar), but the pre-registered rule did real work: absent it, a bar-cleared 0.75
   would have been revealed on a rescued vector.
3. WALL GEOMETRY: the rescale re-ranked concentration across the curve - mid-curve shifted UP
   ~+0.09..+0.16x while the FAR RIGHT FELL (2.00: 1.9867x -> 1.8247x). The iter34 monotone
   toward-the-wall reading does NOT survive the rescale; only the incumbent's neighborhood is
   wall-hugging. The 2.0x Wmax wall remains the binding geometry (+0.024 IS-SR behind it,
   operator item unchanged).
4. STALENESS-CLASS LEDGER COMPLETE - all three shapes measured: plateau (50/51/52), movement
   (53, the only one), re-affirmation (54 c5ng-k with police re-fire, 55 brwt-zb pure).
   Solver-family plateau count STAYS SIX (22/29/30/50/51/52). Every sealed roster scalar now
   carries a CURRENT-FRAME certificate.

## Frontier
31 axes measured-closed; ZERO remaining staleness cells - the per-session-cell program is
EXHAUSTED. Remaining levers (unchanged, now the ONLY levers): purchased data outside the
census, or an operator rule change with recorded price tags (Wmax +0.024 behind the wall; G7
police 2-of-12 approved; ITER39 WIN=150 remains the only pass-the-literal-objective kill).
Champion: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv, SR 3.820357, cagr 23.92 pct, gross 1.0.

## Defects disclosed (caught fail-closed this session)
1. INHERITED LOG FILENAME (D19 class, three sites): driver's final open() + print() carried
   driver_iter54.log (my hygiene list was case-sensitive: "ITER54" misses "iter54"). Fixed by
   R15+R16 substitutions; hygiene token now "iter54" lowercased; driver re-run - all three
   runs byte-identical in science content and the final log sha16 efe59d15ffbf4048 equals the
   FIRST run's content verbatim: the repair is proven cosmetic.
2. make_driver print hardcoded "14/14" - fixed to format the count (16/16).

Pins: campaign/bt/tests/test_iter55_brwt_zb_readj.py (6, mutation-checked RED x2 -> byte-exact
restore -> GREEN). Memo landed BEFORE the final suite (round4b race law). Coord dir:
campaign/agents/chief/coord/ITER55_BRWT_ZB_READJ/ (precommit, probe, make_driver, driver, log,
32 arm files, NO candidate CSV, FINDINGS.md 016ba3e1cae05181).
