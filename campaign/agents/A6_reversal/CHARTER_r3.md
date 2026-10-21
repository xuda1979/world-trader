# A6 round 3 — coordinator directive: ONE more orthogonal sleeve, SR>=0.9, |corr|<0.3 to champion
Champion (5 sleeves) is at SR_m 1.87 with A6_pair_fm as the equity-side anchor. What is MISSING:
high-frequency equity-market-NEUTRAL books. Your r1 weekly xs reversal was real but cost-killed.
Try (order matters):
1. MONTHLY xs reversal L/S (21d cadence, top/bottom quintile, vol-scaled): r1 tested weekly only.
   Costs drop ~4x. Target SR>=0.7, corr<0.3 (book is $-neutral so decorrelated from long books).
2. Idio-vol residual REVERSAL: 5-21d reversal on FF4 residuals (you have resid engine), monthly.
3. Residual momentum at higher breadth: long top tercile + SHORT bottom tercile (pure L/S),
   MA150-gated, monthly — L/S form decorrelates from your long-only pair.
4. If one passes gates + low corr: save it; also save champion+candidate 6-sleeve mix if the MIX SR_m > 1.95
   (mix allowed: equal weights, document in .meta).
Use .mul(axis=0) alignment; scramble = circular shift of weight path w/ costs repriced (your fixed version).
Append FINDINGS.md; last line ROUND r3 DONE.
