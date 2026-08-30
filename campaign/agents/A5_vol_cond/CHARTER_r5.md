# A5 r5 — decisive round. Frontier: SR_m 1.95 @ 20.5% (L=2). Need SR_m>=1.1 ann>=15% corr<0.2.
Your A5_r4_vt15_contango (SR 1.02, ann 13.5%) is the closest asset in the campaign. Push:
1. vt18 re-budget (SR ~1.0, ret ~16.5%): verify halves >=0.45 both, negYears<=3, worst>-8% (relaxed).
2. Contango with CONTINUOUS scaling (r2 mission-4, was 0.86-0.98 area) at vt18: z=(vix/vix3m -1), pos=clip(1-z*5, 0, 1).
3. Contango@vt18 + capitulation long (VIX>32, maxhold 21d, 25% weight) mix — the capitulation book pays
   exactly when contango is off: natural pair, corr negative internally.
4. Bond contango@vt18 (your r3 0.19 solo is too low; but at vt18 ret 12%+? need SR>=0.9 — probably fails,
   attempt only if time).
Append FINDINGS.md; last line ROUND r5 DONE.
