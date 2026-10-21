# A6_reversal LOG
## Round r1 — 2026-08-28
- Built lib6.py (dedupe loader; shared closes() crashes on dup dates), harness_shim.py (ff_mom parse fix).
- Idea1 weekly xs reversal: 36-config sweep + LO variants + 8 overlays + knife/calm filters → FAIL all gates (best vol-tgt SR 0.63).
- Idea2 residual momentum: LS/long/DM-gated/MA-hysteresis-gated (best SR 1.03 raw, 0.97 vol-tgt) → FAIL gate d (2022 −12.9%).
- Idea3 mom+rev blend: FAIL (2022 −13 to −16%).
- Idea4 idio-vol-managed momentum: FAIL (2022 −12%).
- Idea5/6 pair blends: FAIL (2022 −8%).
- Idea7 plain momentum control: FAIL (2008 −19.7%).
- Idea8 EXT-panel reversal: SR 3.5 = data artifact (stale $0.01 quotes); filtered SR 0.00. REJECTED as fake.
- Sleeves saved: NONE. Reference scripts: campaign/scripts/a6_idea1_lo_reversal.py, campaign/scripts/a6_idea2_residmom_gated.py.
- Tool calls: ~45. Full details in FINDINGS.md.
-r2- 2026-08-28: missions 1-2 FAIL (documented), mission 3 SAVED 2 pair sleeves (fm1926 SR .91, msew SR .88); scramble gate fixed (lib6 was degenerate); ddEntry gate + VIX findings logged
-r3- 2026-08-28: charter items 1-4 executed in order. (1) monthly xs reversal L/S 12-config sweep (k5/10/21 x quint/decile x ivw/ew, cad21): ALL FAIL, SR -0.10..0.21 — short-leg gross-negative even at 1/4 cost; (2) residual reversal (FF4, k5/10/21): SR -0.15..-0.01 FAIL; (3) resid-mom pure L/S SR 0.02-0.10 FAIL (short-bot3 gross -0.70); 3b beta-hedged long SR 0.70 but 2014 -6.7% corr 0.32 FAIL; 3c conditioned hedge SR 1.05 corr 0.61 FAIL; 1b/3d LO-rev monthly + market hedge — caught & fixed a 1-day LOOKAHEAD in first hedge test (SR 1.43 fake -> 0.84 honest); honest grid max SR 0.84, negYr 3-6, corr 0.44-0.51 FAIL; LO-rev k21 d10 cad21 passed base gates (SR 0.63, worst -1.4%) but FAILED scramble p=0.435 + plateau (isolated peak, neighbors min 0.45) + corr 0.48; (4) mix6 champion+CAND SR_m 1.80 < 1.95, swap 1.74 -> NO SAVE. Sleeves saved: NONE (0 passes of full contract). Scripts: r3_lib.py, r3_idea12.py, r3_idea3*.py, r3_idea1b.py, r3_idea1c_gates.py. Tool calls ~30. Details in FINDINGS.md.

# r4 (2026-08-30): charter 3 ideas (vt15 re-budget / triple momentum mix / trailing-SR meta-timing)
— 0/3 saved; all fail |corr|<=0.3 to champion (A6_pair_fm is itself a champion leg; simplex min
corr +0.26 only at fm-only, which fails SR/gate d). 1 impl bug caught pre-report (daily-vs-annual
trailing SR). Scramble infra note: all-legs-roll null leaks pre-2007 fm history into eval window.
Script: campaign/scripts/a6_r4_momentum_budgets.py. Details in FINDINGS.md r4.

# ROUND r6 (2026-08-30) — new-family directive: pairs / lead-lag / 52w-high / earnings-drift
All 4 charter ideas FAIL gate a (full SR>=0.7) — none reach even gross SR 0.7. 22 configs tested.
Decomposition: gross SRs 0.48-0.65 → the killer is the PREMIUM, not costs (drag 0.6-2.6%/yr).
Scripts: campaign/scripts/a6_r6_new_families.py (all 4 ideas, reproducible; verifies FINDINGS r6).
Details in FINDINGS.md r6. Nothing saved to sleeves/.

# r7 (2026-08-31) — new free-data engines
- r7_lib.py, r7_idea1_bondtrend.py (36-cfg sweep), r7_idea1b_2y_refine.py, r7_idea1c_save.py
  (plateau+scramble), r7_idea1d_control.py (always-long control), r7_idea1e_calendar.py
  (calendar forensics), r7_idea2_curve.py, r7_idea2b_carry.py (+fix idx bug), r7_idea2c_blend.py,
  r7_idea3_commod.py, r7_idea4_regime.py (+fix import), r7_idea4b_save.py (plateau fail).
- SAVED: sleeves/a6_r7_bond2y_trend.csv (+meta) — SR 1.43, negYr 2, corr6 -0.00, scramble 0.005.
- Repro: campaign/scripts/a6_r7_bond2y_trend.py (byte-verified after 2 divergence fixes).
- Eval harness verified; champion 7-leg blend SR_m 2.05 (vs 1.89).
