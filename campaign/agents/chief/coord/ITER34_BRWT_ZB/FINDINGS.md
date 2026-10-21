# ITER34 FINDINGS - BRWT Z-THRESHOLD FAMILY SCALAR zb - HONEST NEGATIVE (NO-ADMISSION)

Session 16, 2026-09-19. Operator objective verbatim: keep improving; leverage <= 1.6;
maximize Sharpe; annual return >= 20 pct. Champion of record UNCHANGED:
GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 8559fa55ee9a3417 / weights
d2d11c92a98683df / ann 23.6054 pct / SR 3.751429 / MDD -3.6130 / gross 1.0 / 0 neg yrs.
Gauntlet ok 7/7 fresh pre-run this session
(coord/verify_champion_r3_last_session16.json: weights 8.327e-17 / bytes 1.032e-16 /
gross 1.0000000 / SR 3.751428690 / cagr 23.6054).

# THE CELL
ITER33 closed the C5ng k-axis (30.16 pct committed weight; incumbent freeze
OOS-vindicated by the G7 police). The LARGEST committed exposure is NOW the brwt
family: brwt10 9.9772 + brwt7 9.1924 + brwt5 10.8304 = 30.0000 pct of book weight,
sitting EXACTLY at the 0.30 brwt-block relw-share cap. All three are emitted by ONE
generator (Brent-WTI log-spread rolling-z mean-reversion; FULL |dW| 6.4bps sleeve cost;
vol_target) with ONE frozen scalar zb=1.0 shared by all three variants; lb in {10,7,5}
and min_start in {2000,2008} are variant identity, not family scalars. Precommit sealed
b9b9539c7dbe41ef BEFORE any candidate (driver hard-asserts the sha); anchor A1 re-run
pre-seal and disclosed inside per the 09-19 re-seal precedent. Grid zb in
{1.0, 1.25, 1.5, 1.75, 2.0}: acceptance-print bz points {1.0, 1.5, 2.0} plus midpoints,
deterministic, symmetric around the anchor, nothing outside the printed envelope.
Generator RE-TYPED into the driver from the CAMP_COST R6 refresh_sleeves documented
convention; A1 proves the re-type; the same anchors prove the Sep-17 re-emission of the
brwt costfix bytes (smaller files, mtime 2026-09-17 10:54) content-identical on the whole
builder frame (saved tails 2026-08-28).

# RESULT (driver_iter34.log)
- Anchors ALL EXACT: A1 regen-vs-saved 9.999e-17 (brwt10, n=6567) / 9.986e-17 (brwt7,
  n=4580) / 9.996e-17 (brwt5, n=4580). A2 projection identity 0.0 exact / weights
  8.327e-17 / bytes 9.996e-17 / fit rows 1809 / k_covered 11 / incumbent IS-SR 4.198632 /
  Wmax_sf 1.8115x. Anchor cell zb=1.0: weights dev 8.903e-09 / book dev 4.044e-10 /
  block share 0.300000.
- ADMITTED 0 / 5: IS-SR FALLS MONOTONICALLY from the anchor: 4.198632 (zb=1.0, the bar)
  -> 4.060778 (1.25) -> 3.884666 (1.5) -> 3.477293 (1.75) -> 3.230354 (2.0). IS-ann
  18.122 -> 11.812 pct. Cells are LIVE (regen-dev 0.129-0.187 vs saved bytes: the scalar
  moves the signal materially; the decline is a real curve, not jitter).
- NO reveal per the sealed stop rule (no cell reached bar 4.198632 + 1e-4). No candidate
  CSV. Wmax_sf rises toward the 2.0x wall as zb rises (1.9867x at zb=2.0) while the block
  share falls to 0.2819 - sparser z-entries push the fit to concentrate elsewhere.
- Champion sha16 pre==post True.

# VERDICT
HONEST NEGATIVE (NO-ADMISSION, IS level). ITER17-law closure 9 by monotone dominance:
the incumbent freeze zb=1.0 is the edge-max of the measured acceptance envelope, and
every interior cell is strictly worse by 0.14 to 0.97 IS-SR. Third closure shape in the
signal-parameter class: DUR interior-max (ITER32), k OOS-vindicated freeze (ITER33),
zb monotone-from-freeze (ITER34) - here IS itself certifies the freeze, no police needed.

# READINGS
1. Strongest negative type: unlike ITER33 (IS gradient against the freeze, G7 police
   required) the IS objective and the freeze AGREE on this axis. The acceptance-era
   freeze is load-bearing, confirmed in the direction IS cares about.
2. The zb->lower-envelope region (zb < 1.0) is UNMEASURED - disclosed pre-seal as
   outside the acceptance envelope. The costfix-era history already walked zb DOWN
   1.5 -> 1.0 (with lb changes). A lower-envelope extension cell is the only remaining
   legal direction on this axis; its EV is bounded by, but not zero from, the monotone
   right side. Next-seal decision, not this one.
3. Family axes keep confirming: the brwt trio is one bet (block share pinned at the cap
   in every admitted-region cell); sweeping its ONE shared scalar was the correct
   granularity - per-variant lb grids (125 cells) remain refused as a mining surface.

Landed: coord/ITER34_BRWT_ZB/ (FINDINGS_PRECOMMIT b9b9539c7dbe41ef, anchor_iter34.py,
driver_iter34.py, driver_iter34.log, this FINDINGS, 5 arm weights CSVs for-the-record),
test_iter34_brwt_zb.py 6 pins (mutation RED -> byte-exact restore sha b37ea2fa6df5bacf
-> GREEN), campaign/GOAL100_ITER34_BRWTZB.md, STANDUP_LOG, memory 126.
SUITE 551 passed / 0 failed (545 + 6, own run 67.56s).
