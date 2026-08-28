=== A5_vol_cond round r1 2026-08-28 ===
idea1 contango gate SPY: FAIL gate d (SR 0.72 plateau, negyr 3, worst -15.4% 2022)
idea2 Moreira-Muir 21d realized: FAIL a+d (SR 0.51-0.59, 5 neg yrs)
idea3 dxy+credit regime gate: FAIL all (best SR 0.45)
idea4 break-glass event: FAIL a solo (SR 0.29-0.41); short-during-spike SR -0.33
idea5 contango+MA filter: FAIL (SR 0.37-0.43, whipsaw)
idea6 contango+VIX-level cap: FAIL d (SR 0.45-0.72, >=4 neg yrs)
idea7 contango+MS_EW blend: FAIL d (SR 0.71, 4 neg yrs)
idea8 VIX3M-implied-vol MM on SPY: FAIL d by count (SR 0.75, H1 0.81/H2 0.70, 4 neg yrs, 2022 -9.1%)
idea9 MM overlays/blends vs library: numeric pass w=0.3+SharpeW (SR 0.90) REJECTED —
     corr 0.88-0.98 to library, attribution w=0 SR 0.76 vs 0.78 (signal adds ~nothing)
SAVED SLEEVES: none. All details in FINDINGS.md.
--- round r2 (2026-08-28) ---
idea1 rate-shock conditioner (us10y>2.75 & +25bp/150d) mult0.5: SR 0.98, 2022 -20.8->-8.1, FAIL d on count (3 negyr incl 2011 -0.28)
idea1b mult=0 (flat in rate shock): SR 1.02 H1 0.94/H2 1.10 negyr 2/18 (2011 -0.16, 2022 -1.87) — ALL GATES PASS → SAVED A5_r2_contango_rateshock
idea2 VIX3M-MM vt 0.05-0.08: SR 0.74 all vt, negyr 4 — FAIL d (lower vt does not fix count)
idea2b MM+cond: SR 0.81, 3 negyr + 2015 -3.1 -> 4 — FAIL d
idea3 XGB1y_deploy mixes: gate d unfixable (2022<0 in every member); mixes 3-4 negyr, worst -12 to -16 — FAIL d; corr to XGB up to 0.88
idea4 continuous monthly z-score TS: best z(252,0.25,cap1.0) SR 0.85 plateau OK — FAIL d (2022 -18); +cond mult0: SR 0.89 negyr 3 (2015) — FAIL d
SAVED SLEEVES: A5_r2_contango_rateshock (SR 1.02, all gates + plateau, scram p=0.000, |corr|<=0.14 to 28/42 lib sleeves)

# r3 (2026-08-28)
- a5_r3_lib.py: gates + corrected cost convention (costs on FINAL vt-scaled turnover) + signal-scramble + lib-corr.
- a5_r3_idea1_bond_contango.py: charter 1 grid (18 cells) + variants — best correct-pipeline SR ~0.30. FAIL.
- a5_r3_idea2_capitulation.py: charter 2 grid (18 cells) — all SR <= 0.00. FAIL (T+1 falling knife).
- a5_r3_idea3_carry_mix.py: charter 3 accrual-carry rebuild + mixes — SR 1.02 but gate d fail.
- a5_r3_idea4_gold_mix.py: charter 4 gold126+contango mixes — SR up to 1.21, H2 1.39, gate d fail on count (4 tiny neg yrs).
- bonus: gold VIX-level gate (20y) — SR <= 0.35. FAIL.
- CAUGHT+FIXED: double-T+1 bug in first idea-1 battery (scramble-real vs eval mismatch exposed it); contaminated numbers retracted in FINDINGS.
- 0 sleeves saved r3.
