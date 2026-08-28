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
