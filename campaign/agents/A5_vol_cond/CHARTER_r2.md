# A5 round 2 — 2022-proofing + portfolio sleeves (per your r1 diagnosis)
Your r1: contango real but 2022 -20.8%; VIX3M-MM SR 0.75; gate-d blocker for long books.
Missions:
1. Rate-shock conditioner: us10y FRED 2000+; rule = us10y>3% AND 126d change > +50bps -> halve
   exposure of contango sleeve (lag 1d, plateau check 100-150d MA, +25/+75bps). Does 2022 -20.8% -> > -6%?
2. VIX3M-implied Moreira-Muir vol-managed SPX at LOWER vol target (6-7%): recheck gates.
3. PORTFOLIO SLEEVES (coordinator-allowed): pair/mix of your best 2 with XGB1y_deploy or Credit_z120_1986
   (load via shared harness; both 2022-flat/positive). A mix passing ALL gates may be saved as a sleeve
   (name it clearly as a mix, .meta must list members + weights + why).
4. Continuous z-score term structure scaling (monthly) instead of binary — check gates.
Append FINDINGS.md; last line ROUND r2 DONE.
