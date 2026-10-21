# ITER35 FINDINGS - BRWT Z-THRESHOLD LOWER-ENVELOPE EXTENSION - HONEST NEGATIVE (NO-ADMISSION); AXIS FULLY CLOSED AS INTERIOR-MAX

Session 16, 2026-09-19. Operator objective verbatim: keep improving; leverage <= 1.6;
maximize Sharpe; annual return >= 20 pct. Champion of record UNCHANGED:
GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 8559fa55ee9a3417 / weights
d2d11c92a98683df. Gauntlet 7/7 fresh earlier this session
(verify_champion_r3_last_session16.json); coord quiet at run time.

# THE CELL
ITER34 (#126) swept zb over the acceptance envelope {1.0..2.0}: monotone DECLINE from
the anchor, 0/5 admitted - and disclosed zb<1.0 as the only unmeasured direction. This
seal measures it: grid {0.25, 0.5, 0.75, 1.0} = the reflection of the ITER34 novel
cells about the anchor, excluding the degenerate zb=0 always-in limit. Motivation
disclosed at seal time: the family's own acceptance evolution walked zb DOWN 1.5 -> 1.0,
and IS-ann rises as zb falls. Precommit sealed 3c8c6083b33fb3b8 BEFORE any candidate;
A1 re-run pre-seal (identical to ITER34's: 9.999e-17 / 9.986e-17 / 9.996e-17). Primary
pre-stated risk: lower zb holds MORE 2021-22 energy-crisis exposure (the ITER33-style
fragility).

# RESULT (driver_iter35.log)
- Anchors ALL EXACT (same values as ITER34: A1 x3, A2 identity 0.0 / weights 8.327e-17 /
  bytes 9.996e-17 / rows 1809 / k 11 / IS-SR 4.198632 / Wmax_sf 1.8115x; anchor cell
  8.903e-09 / 4.044e-10 / block 0.300000).
- ADMITTED 0 / 4: the LEFT side RISES monotonically INTO the anchor: 3.897552 (zb=0.25)
  -> 4.057100 (0.5) -> 4.175140 (0.75) -> 4.198632 (anchor). IS-MDD degrades steeply as
  zb falls: -2.56 -> -3.04 -> -3.70 -> -4.36 pct. Cells LIVE (regen-dev 0.179-0.205).
- NO reveal per the sealed stop rule. No candidate CSV. Champion sha pre==post True.

# VERDICT
HONEST NEGATIVE (NO-ADMISSION). Stitched with ITER34, the FULL measured curve over
zb in {0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0} is SINGLE-PEAKED with the INTERIOR
PEAK EXACTLY AT THE INCUMBENT zb=1.0: left side rises 3.898 -> 4.199, right side falls
4.199 -> 3.230. The incumbent freeze is the IS-interior-argmax of its own one-scalar
family - upgrading the ITER34 edge-max reading. The zb axis is now FULLY CLOSED on both
sides of the anchor (the degenerate zb=0 always-in limit remains outside the family by
construction). ITER17-law closure 10.

# READINGS
1. Strongest possible closure shape, realized: interior-max certified by BOTH neighbors,
   at family weight 30.00 pct. Three of three structural facts pointed the right way
   before the run (monotone right side, acceptance history walking down, IS-ann
   gradient) - and the answer is still: the freeze is where IS peaks.
2. The pre-stated fragility risk did not need G7: the IS-MDD gradient (-2.56 -> -4.36
   pct as zb falls) already prices the cost of holding more crisis-window exposure; the
   police were never consumed because nothing reached the bar.
3. Closest miss: zb=0.75 at 4.175140 = bar - 0.0235. A real competitor, honestly below
   the 1e-4 jitter bar; unrevealed by law.

Landed: coord/ITER35_BRWT_ZBLOW/ (FINDINGS_PRECOMMIT 3c8c6083b33fb3b8 + anchor_iter35.py
+ driver_iter35.py + driver_iter35.log + FINDINGS + 4 arm weights CSVs),
test_iter35_brwt_zblow.py 6 pins (mutation RED -> byte-exact restore -> GREEN),
campaign/GOAL100_ITER35_BRWTZBLOW.md, STANDUP_LOG, memory 127. SUITE 557 passed /
0 failed (551 + 6, own run).
