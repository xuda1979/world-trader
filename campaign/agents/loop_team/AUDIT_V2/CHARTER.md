# AUDIT_V2 — adversarial audit of GOAL100_HONEST13V2_* champion (2026-09-02, iter 5)
The coordinator committed champion V2: campaign/results/GOAL100_HONEST13V2_{BALANCED,SAFE,AGGRESSIVE}_daily.csv
= 11 FIX engines + diescrack_L40Z20 + CFX4 at capital slot weight 0.10 each
(total slots 12.2; new-sleeve capital share 4.55% each), exact position-path overlay turnover charged,
instrument-cost adjustment on the slot-weighted scale book, NYSE-rows-kept calendar.

AUDIT IT. Write campaign/agents/loop_team/AUDIT_V2/FINDINGS.md with exact numbers:
1. REPRODUCE V2 independently from the 13 sleeve CSVs (write your own code; do NOT import the
   coordinator's script — it was a heredoc, NOT committed; if you cannot reproduce within 1e-12,
   THAT IS A PROVENANCE HOLE — report it and derive the exact recipe that matches, incl. every
   cost/borrow/throttle term). Coordinate recommitted builder: campaign/scripts/honest11_build.py
   covers 11-pool only; V2 needs the slot-weight extension (--verify does NOT cover V2).
2. Verify the two new sleeves' gate claims YOURSELF: diescrack (SR 1.01, corr 0.05, pos-lag
   scramble p=0.0000), CFX4 (SR 1.91, corr 0.00, all gates) — recompute from raw data if feasible,
   else from CSVs + raw where available. Verify CFX4's concentration disclosure (top-50d = 74% PnL).
3. SCRAMBLE GATE: verify the degeneracy claim — literal return-permutation p vs position-lag
   circular-scramble p on diescrack and CFX4. Confirm/reject that the as-written charter gate is vacuous.
4. V2 HEADLINES (recompute): ann, SR_d, SR_m, MaxDD, worst 3y subwindow, 0/19 neg (2008+),
   OOS17 arithmetic. BAL == (SAFE+AGGR)/2?
5. LEVERAGE: capital-real gross (sum_i |scale_i|*global*throttle at slot weights) mean/p95/max,
   yearly means. Any day >2x the disclosed mean? Compare vs the 3.45x claim.
6. NEW-SLEEVE DILUTION CHECK: sweep slot weight 0..0.5 — confirm 0.10 is approx the
   diversification optimum and that no weight lifts SR_d >= 5 or ann >= 80 at DD <= 7.
7. T+1 probe, flatten gate, block-bootstrap SR CI, leave-one-out of the 13.
8. VERDICT: is V2 admissible as the committed champion? Any inflation found?
Last line of FINDINGS.md must be exactly: AUDIT_V2 DONE
