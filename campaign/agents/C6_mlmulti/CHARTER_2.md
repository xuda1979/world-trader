# C6 Round-2: ML — combine what round-1 learned (which ML inputs had signal?)

Round-1 verdicts (from your FINDINGS.md): fill in based on your round-1 results.
1. If curve-ML had OOS signal: scale to full curve (all tenors) multi-output.
2. If KF-industry-ML had signal: deep feature set (all 48 industries x 5 horizons ranks).
3. Positioning-ML: dead per C3 — skip.
4. FX-cross/dxy ML: test with DEX* daily panel (16 pairs) + DTWEXBGS target.
5. NEW: ML on sleeve-pool meta-state: features = sleeve trailing 21/63d SRs, pairwise corr
   regime, dispersion of sleeve returns -> predict next-21d best sleeve (meta-model for
   dynamic weights). Purged time split. Must beat EW OOS to count.
6. NEW: XGB on full US curve shape: features = level/slope/curvature (PCA of 11 DGS tenors)
   1d/5d/21d changes + vix + hy_oas -> predict DGS10 book. Train 2008-16, test 2017+.

All gates. OOS discipline. Log numbers. Last line: ROUND 2 DONE
