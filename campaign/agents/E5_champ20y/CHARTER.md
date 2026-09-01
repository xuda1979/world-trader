# E5_champ20y — 20-year champion validation & upgrade (IS/OOS DISCIPLINED)

Coordinator built GOAL100_CHAMPION20Y (12-pool, 2007-01 start, 20.4y span, BALANCED 39.5%
ann @ -7.1% DD, SR 4.91, 0/21 neg yrs, OOS17+ 44.9%): files
campaign/results/GOAL100_CHAMPION20Y_{BALANCED,SAFE,AGGRESSIVE}_daily.csv + .json.
Build method = champion_build.py logic with pool minus {H21_f5,H21_br,A5r2,A5r4},
A=vt.065/thr.04, B=vt.08/thr.03.

YOUR JOB — the full-validation workstream:
1. INDEPENDENT rebuild from the 12 sleeve files (import champion_build, replicate) — confirm
   byte-match with the committed CSVs; report any deviation.
2. Sub-period DD audit: every 3-year window 2007-2026 (8 windows) + every calendar year
   (21) — flag anything < -8%.
3. Cost stress: recompute at 8bps and 10bps/side — where does ann/DD land? (robustness of
   the 6bps assumption)
4. Bootstrap: 1000x 21d-block bootstrap of FULL-window SR (report CI) and of ann.
5. Scramble: signal-permutation test on the blend (200x) — p-value.
6. UPGRADE attempt (if audits pass): is there a vt/throttle pair in the small grid
   {(0.07..0.09)x(0.03..0.045)} with IS(2007-2016)-selected params that beats the
   coordinator's A/B choice on IS AND passes OOS DD<=8%? Report the honest frontier.
7. Compare vs 18.6y champion: report both, state clearly which satisfies "20-year testing".

Deliver an upgraded GOAL100_CHAMPION20Y_v2 if (6) succeeds; else confirm v1. Full tables in
FINDINGS.md. Last line: ROUND 1 DONE
