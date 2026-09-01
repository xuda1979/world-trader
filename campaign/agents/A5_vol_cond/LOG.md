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

# r4 (2026-08-30)
- Champion rebuild integrity check vs saved vt10 CSV: max|diff| ~1e-17, SR 1.019 ✓
- Idea 1 vt15 re-budget: SR 1.02 ann 13.5% negyr2 (2011 -0.7, 2022 -3.1) H1 0.94 H2 1.10
  scram p=0.000 (real==eval SR consistency ✓) plateau vt 0.12-0.18 flat + signal grid
  0.872-1.005 corrChamp 0.71 / corrEW5 0.49 / corr vt10-twin 1.000 → SAVED
  A5_r4_vt15_contango (+ script a5_r4_vt15_contango.py, full .meta incl verified
  champion-swap numbers after correcting an unverified draft claim)
- Idea 2 triple-gate vt18 (x VIX-spike veto thr 28/32/40): SR 0.85/0.91/1.00 but negyr
  3-4, 2011 -7..-21.5% (veto exits mid-2011 re-entry whipsaw); neighbors worse → FAIL d
- Idea 3 capitulation reversion thr 28/32/36 mh21: SR 0.27/0.21/0.16, 2008 -11/-23/-35%
  → decisive FAIL (confirms r1/r3: T+1 long-crash-reversion rides continuation)
- Idea 4 gold126 + bond63 TR-trend mix w .3-.6: SR 0.22-0.52, negyr 7-10 → FAIL a+c
  (bond trend leg dead post-2016, r3 conclusion reconfirmed); NOT the r3 gold+contango mix
- Champion swap quantified (daily EW6 recon corr 0.88 official): vt10 SR_m 2.15 ann 9.8 ->
  vt15 SR_m 2.05 ann 10.4, 0 negyr both → coordinator tradeoff decision
r5 (2026-08-30): charter 4 ideas executed via scripts/a5_r5_charter.py — vt18 re-budget (relaxed-gate PASS, SR_m 1.08<1.1 mission miss, corr 1.000 to saved twins → NOT saved), continuous contango scaling (FAIL d, worst -25%), contango+capitulation mix (FAIL e p=1.000 + dilution vs 75%-cash control, despite negyr=1), bond contango@vt18 (FAIL, SR 0.20). 0 saved. Champion rebuild QA 1e-16. Details in FINDINGS.md.
r6 (2026-08-30): charter 4 ideas via scripts/a5_r6_{lib,idea1_term_premium,idea2_vix_level_gate,idea3_overnight,idea4_credit_carry}.py — term-premium timing best cell SR 0.40 (18 cells 0.14-0.40, FAIL a/c/d), VIX-level gate best 0.37 + corr 0.52 to champion (FAIL a/d), overnight premium gross SR 0.53 but 12bp/d round-trip -> net -23.9%/yr (FAIL by cost arithmetic), credit DV01-neutral bands: charter direction inverted, always-long best 0.43 (FAIL a/d). COORDINATOR ALERT: all 4 library Credit_* sleeves degenerate (vol<1.2%, SR -0.41..-0.49). 0 saved. QA: champion rebuild 1e-16, scram-real==eval. ROUND r6 DONE
- r7 (2026-08-31): 9 ideas on data_fred_new (VIXCLS/DGS10/DAAA/DBAA/TEDRATE 1990+); charter 1/2/4 failed, charter 3 inverted+tuned+hedged -> SAVED A5_r7_credit_composite SR=1.51 n=9163 (H1 1.69/H2 1.35, 2 negYr worst -2.8%, scram p=0.000, corr<=0.13 lib). 8 scripts in campaign/scripts/a5_r7_*. Also caught+discarded a same-day-macro lookahead variant (SR 2.30 fake -> 1.13 honest).
