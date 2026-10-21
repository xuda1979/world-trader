# CHAMP_HUNT_CONSTRUCTION — construction/weight/spec audit + in-spec weight refinement

Champion: RAWEW13v2 WEIGHTED (ann 39.50% / SR 3.22 / MaxDD -6.52% / 0-neg / gross 1.6), built by
campaign/scripts/rawew13v2_build.py. Constraints are FIXED SPEC (do NOT relax): leverage <= 1.6
capital-real, MaxDD >= -7.00%, >= 0 every year, 6.4bps/side FULL |dW|.

Your job:
1. SPEC-COMPLIANCE audit: re-run build() and confirm (a) capital-real gross EXACTLY 1.6 (0 overshoot),
   (b) MaxDD within -7%, (c) 0 negative years, (d) costs full-|dW|, (e) weights deterministic from
   IS-window only (no OOS leak in the fit). Confirm the IS-only weight fit (IS_END 2017-01-01).
2. WEIGHT-SENSITIVITY: the fit uses shrink_d=0.98 and W_MAX=2.0. Sweep shrink_d in {0.90,0.95,0.98,
   0.995} STILL FITTED ON IS-ONLY (<2017) and report the OOS (2017+) ann/SR/MaxDD for each — this
   is the honest way to find a better in-spec weight. If any improves OOS materially AND stays within
   all spec gates AND the weights are IS-fitted (no OOS touch), report it as a CANDIDATE (do NOT
   overwrite the champion).
3. COST-HONESTY: verify turnover is FULL |dW| at 6.4bps and margin on (gross-1); confirm no hidden
   charge. Report the true per-gross return of the champion's energy core vs a new decorrelated add.

Output: FINDINGS.md. Report any in-spec weight candidate with exact OOS numbers, else confirm the
ITER15/19 fit is already optimal. Last line: CHAMP_HUNT_CONSTRUCTION DONE
