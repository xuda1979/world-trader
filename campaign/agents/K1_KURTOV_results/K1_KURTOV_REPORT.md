# K1-KURTOV — inverse-kurtosis scaling overlay on the V7.1 champion (2026-09-30)

GOAL5DIR action D. Pre-registered (PREREGISTRATION.md): 3 arms K=126/252/378,
s=1/(1+clip(kurt_K,0,20)), renormalized to gross 1 (zeroed sleeves stay 0),
T+1 causal, overlay cost 6.4bps x LEV on |d(w_eff)| turnover, gates G1-G6 OOS.
Champion OOS reference: SR 3.6718 ann 30.72% DD -3.16% neg-yrs 0

## Results (all 3 pre-registered arms)
  K    is_sr   oos_sr  oos_ann   oos_mdd  neg_yrs_oos    to_yr  oos_edge   is_edge    G1    G2   G3   G4    G5    G6
126 3.634888 3.335248 0.354764 -0.059841            0 6.639352 -0.336505 -0.444360 False False True True False False
252 3.202051 3.469130 0.381385 -0.053288            0 3.252311 -0.202623 -0.877197 False False True True  True False
378 3.177181 3.452786 0.391879 -0.051734            0 2.179863 -0.218968 -0.902067 False False True True  True False

## IS-best arm K=126 -> OOS verdict
- OOS SR 3.3352 (edge -0.3365), ann 35.48%, DD -5.98%, neg-yrs 0, overlay to/yr 6.64
- gates: {'G1': False, 'G2': False, 'G3': True, 'G4': True, 'G5': False, 'G6': False} -> **REJECT**

## VERDICT
**REJECT — inverse-kurtosis overlay fails the pre-registered OOS gates.**
GOAL5DIR action D closed: kurtosis scaling does not lift the champion book
either standalone (K1: 0.26 vs 0.43 on trend) or as a 20-sleeve overlay.
With A (H1 harness, live), B (F2-DDC, REJECT) and C (DEAD_IDEAS discipline,
ongoing) also actioned, GOAL5DIR is now FULLY closed.

## Honesty notes
- 3 arms only (pre-registered, no post-hoc grid added).
- The overlay reallocates within the book (gross stays 1): any de-grossing
  variant is a DD-control policy and was already REJECTED by F2-DDC (this
  session); not re-tested here by design.
- Expected outcome per K1-standalone + F2-DDC prior: REJECT.

DONE K1_KURTOV
