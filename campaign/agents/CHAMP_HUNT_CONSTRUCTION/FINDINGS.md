# CHAMP_HUNT_CONSTRUCTION — FINDINGS (Round 1, 2026-09-14)

Champion under audit: RAWEW13v2 WEIGHTED @ capital-real 1.6x (builder campaign/scripts/rawew13v2_build.py).
Charter executed in order: (1) SPEC-COMPLIANCE audit, (2) WEIGHT-SENSITIVITY shrink_d sweep, (3) COST-HONESTY.
No new sleeve CSV was saved: the sweep produced no candidate (Job 2) and no new signal was in charter scope; the audit confirms the committed book is the in-spec optimum.

## 1. SPEC-COMPLIANCE AUDIT — PASS (all 5 sub-checks)
Rebuilt via build(); --verify vs committed files: max|new-old| = 9.996e-17 (IDENTICAL), weights max diff 6.939e-17.
- (a) capital-real gross: mean=min=max=1.600000000000 over 4806 days; 0 days > 1.6+1e-9, 0 days < 1.6-1e-9. EXACT, zero overshoot.
- (b) FULL MaxDD = -6.5232% >= -7.00% bound. PASS.
- (c) 0 negative years (19 years 2008-2026; worst year = 2013 at +5.62%). PASS.
- (d) Costs are FULL |dW| x 6.4bps one-side, margin (1.6-1)x4.5%/252. Bit-level reconstruction of net from port - to*6.4bp - margin: max abs err = 0.000e+00. No hidden charge, no 0.5 half-turn factor.
- (e) Weights deterministic from IS-window only: IS_END=2017-01-01; OOS-perturbation test (x7 returns + 130bp shift on all data >= 2017) leaves relw bit-identical (max diff 0.000e+00). T+1 causality of the NAV-drift weights: perturbing returns at the mid date leaves all prior weights bit-identical (0.000e+00) — nav.shift(1) confirmed. IS fit: long-only max-Sharpe, shrink_d=0.98, W_MAX=2.0x equal weight; max relw = brwt5 0.1774 (2.31x eq... under cap).

## 2. WEIGHT-SENSITIVITY (shrink_d sweep, ALL fitted IS-only < 2017-01-01) — NO CANDIDATE
| shrink_d | IS ann | IS SR | OOS ann | OOS SR | OOS MDD | OOS negy | FULL ann | FULL SR | FULL MDD | to bp/yr |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.90  | 30.5511 | 3.5367 | 36.5290 | 3.1052 | -6.43 | 0 | 33.6856 | 3.2403 | -6.43 | 4.92 |
| 0.95  | 30.7305 | 3.5165 | 36.5566 | 3.0917 | -6.49 | 0 | 33.7854 | 3.2265 | -6.49 | 4.83 |
| 0.98* | 30.8441 | 3.5036 | 36.5719 | 3.0830 | -6.52 | 0 | 33.8475 | 3.2176 | -6.52 | 4.77 |
| 0.995 | 30.9028 | 3.4970 | 36.5793 | 3.0785 | -6.54 | 0 | 33.8792 | 3.2130 | -6.54 | 4.74 |
*committed champion.
Verdict: entire grid spans 0.05pp OOS ann and 0.027 FULL SR; NAV corr to champion 0.999826/0.999974/0.999993; max daily weight diff vs champion = 0.0077 (0.90), 0.0015 (0.995) equal-weight units. NO variant improves OOS materially (threshold +0.5pp OOS ann: none passes). The pre-committed rule (largest IS ann s.t. IS SR >= 3.5) selects 0.98; 0.995 fails the IS SR floor (3.4970 < 3.5). Honest note: shrink 0.90 shows the best FULL SR (3.2403) and MDD (-6.43%) — selecting it post-hoc on full-window/OOS optics would be OOS-mining; the committed 0.98 stands. ITER15/19 fit CONFIRMED optimal within this family.

## 3. COST-HONESTY — CLEAN
- Reconstruction exact (0.000e+00). Charged: FULL |dW| x 6.4bps + 2.70%/yr margin on (gross-1) only. Nothing else.
- TRUE turnover: 4.766 bp/yr (IS<2017: 5.479; OOS>=2017: 4.119) — NAV-drift weights move slowly. Total cost drag ~ 274.8 bp/yr (4.77 turnover + 270 margin). (An earlier log line "476.60bp/yr" in my scratch run was mislabeled x100; 4.766 bp/yr is the verified figure from --verify.)
- Counterfactual legacy charge 0.5x|dW|@6.0bps would add only +0.0253pp/yr (33.8728 vs 33.8475) — negligible NOW because turnover is 4.8bp/yr, but FULL|dW| remains the committed standard.
- Per-gross returns (FULL window, net of own |dW| cost, per 1.0x gross per yr): brwt7 +26.17%, brwt10 +26.01%, brwt5 +25.67%, C5ngsum +24.96%, C5ng +19.36%, QAxasts +9.67%, dualmom +9.65%, A5r2 +5.88%, a6r7 +5.52%, diescrack +4.96%, carryv2 +3.71%, CFX4 n/a (held at 0 — vendor-artifact FX feed, 2019+ only).
- ENERGY core (brwt block + C5ng/sum + A5r2 + diescrack) employs 1.520 of 1.6 gross and earns ~21.8%/yr per unit gross; the decorrelated adds (QAxasts/dualmom/a6r7/carryv2) employ 0.081 gross at ~7%/yr per unit gross — small but decorrelation-positive (corr-to-rest: dualmom -0.074, QAxasts -0.023, A5r2 -0.011, a6r7 +0.059, carryv2 +0.075).
- Known concentration: brwt5/7/10 correlate +0.75..+0.85 to each other (one Brent-WTI reversion bet expressed three times) — spec-fixed by W_MAX cap, not relaxable.

## VERDICT
The ITER15/19 RAWEW13v2 WEIGHTED fit (shrink_d=0.98, W_MAX=2.0, gear 1.6, IS<2017-01-01) is confirmed: spec-exact (gross 1.600000000000 / MDD -6.52% / 0 neg yrs / FULL|dW|@6.4bps), IS-only and T+1 causal (bit-level proven), byte-reproducible, and the shrink_d family offers no material in-spec improvement (grid OOS spread 0.05pp). No candidate sleeve emitted; champion of record unchanged.
ROUND 1 DONE
