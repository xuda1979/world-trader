> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
# GOAL100 ITER32 - DUR-AXIS (SIGNAL-PARAMETER) SWEEP - HONEST NEGATIVE (2026-09-19, session 14)

Operator objective (5th verbatim resend, unchanged): keep improving; leverage <= 1.6;
maximize Sharpe; annual return >= 20 pct. Champion of record UNCHANGED:
GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 8559fa55ee9a3417 / weights
d2d11c92a98683df / ann 23.6054 pct / SR 3.751429 / MDD -3.6130 / gross 1.0 /
0 neg yrs. Gauntlet ok 7/7 fresh pre-run (coord/verify_champion_r3_last_session14.json).

## THE CELL
The ITER30 recipe sweep froze the a6r7 generator SIGNAL parameter DUR=1.9 while
measuring only the trading recipe (K x CAD x VT x CAP). DUR (coefficient of -dy in
tr = -DUR*y.diff() + y/252) is the LAST unswept scalar of the champion dominant
sleeve. ITER32 measured it: DUR in {1.40, 1.65, 1.90(anchor), 2.15, 2.40}; every
other slot byte-frozen (K378 / CAD42 / legacy-6.0bp / T+1 / expanding(60) VT12 CAP5 /
12-slot pool / gear 1.0 / shrink 0.70 diag / brwt-cap 0.30 / CFX4 pin 0 / Wmax 2.0 at
k_covered 11). Precommit sealed 8ebb2c3da5faf91f BEFORE any candidate (driver
hard-asserts the sha). No new data, no rule change; legal basis = ITER30.

## RESULT (driver_iter32.log)
- Anchors ALL EXACT: A2 generator-vs-saved 9.975e-17 (same number as the ITER30
  anchor); A3 projection identity 0.0 exact / weights 8.327e-17 / bytes 9.996e-17 /
  fit rows 1809 / k_covered 11 / incumbent IS-SR 4.198632 / Wmax_sf 1.8115x.
- ADMITTED 0/5 at the 1e-4 jitter bar; NO reveal per sealed stop rule; champion
  shas pre==post True. Grid: 1.40 -> 4.192924; 1.65 -> 4.196927; 1.90 -> 4.198632
  (ARGMAX); 2.15 -> 4.197999; 2.40 -> 4.197272. Every novel cell BELOW BAR.
- Anchor cell reproduces the incumbent through fit+build: weights dev 5.483e-09
  (the SAME SLSQP boundary-jitter digits ITER30 disclosed - same active set), book
  dev 2.477e-10.

## READINGS
1. IS-SR is CONCAVE in DUR with the interior max exactly at the incumbent: the
   champion coefficient is the IS-optimal point of its own one-parameter family.
   FOURTH independent plateau confirmation (weights ITER22, estimator target
   ITER29, recipe ITER30, signal-parameter DUR ITER32).
2. IS-ann rises monotonically with DUR (17.86 -> 18.23) while IS-SR falls: higher
   DUR buys return with more than proportional vol - the wrong direction under the
   operator literal objective (max SR).
3. Wmax_sf grows with DUR (1.61x -> 1.89x), all feasible: no concentration pressure
   anywhere on this axis.

## FRONTIER AFTER ITER32
TEN axes measured-closed: gear (ITER21), weights (ITER22), grid edges (ITER23),
census data (ITER24/#117b/27/28), 8c-era ledger (ITER25), credit-at-cap (ITER26),
covariance-target (ITER29), covariance-target-AT-CAP (ITER31), recipe (ITER30),
signal-parameter DUR (ITER32). Remaining levers UNCHANGED: purchased data or
operator rule change (the #123 G7 price tag +0.0366 / 3-of-5-windows-negative
stands; recommendation KEEP the police).

## ALSO THIS SESSION
- Item 123 audit flag CLOSED: RAWEW15_REFRESH_CANDIDATE 07:30:16 re-emit is
  byte-identical to the #123 sha16s (dc3d7c9e / 8c19ef22) => deterministic refresh
  of a dead artifact, zero drift; writer not quantum-gpt, not the cron skip path
  (07:30 fire was lock-skipped; 08:30 fire lock-skipped by the live 08:00 twin).
- CONCURRENT-WRITER note: cron twin (job_fe286bf39cb9, same operator prompt, pid
  31226) RUNNING throughout this session; it created nothing in coord/ as of
  landing; any later twin landing merges as its own entry per house convention.

Landed: coord/ITER32_DUR_AXIS/ (FINDINGS_PRECOMMIT 8ebb2c3da5faf91f + driver + log
a5280ea9a3a9f02d + FINDINGS b756a99b9599cc8c + 5 arm weights CSVs),
test_iter32_dur_axis.py 6 pins (mutation-checked RED -> byte-exact restore -> GREEN),
this doc, STANDUP_LOG, memory #124. SUITE 539 passed / 0 failed (533 + 6, own run,
75.69s).
