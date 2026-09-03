# HUNT_VXV_TERM — VIX/VXV (VXMT) term-structure + GVZ/OVX vol-structure timing (iter 7.5)

PREMISE: HUNT_VOLOVERLAY and the dead-idea ledger concluded the ONLY untested family left was a
VIX-term-structure / credit-stretch overlay, explicitly blocked because VIX3M/VXV "not on disk".
NEW DATA (just downloaded, linted): tools/quant/data/more_fred/VXVCLS.csv (VIX 3M, 2007-12-04..
2026-09-01), GVZCLS.csv (gold vol 2008-06+), OVXCLS.csv (oil vol). Also VIXCLS on disk (fred/VIXCLS.csv).
TEST the term-structure signal VXV/VIX (normalized) as a REGIME/TIMING overlay on the committed
V3 champion OR as a vol-structure satellite (signal -> tradeable instrument = VIX ETP proxies? NOTE:
VIXY/VXX ETFs NOT on disk; use the signal only to TIMe the champion or a liquid book already on disk
(e.g. SPY/bonds/commodities sleeves). If no direct tradeable instrument exists, treat it is a
champion-overlay test and disclose that).

READ FIRST: campaign/results/DEAD_IDEAS.csv (SR-lift overlay family is DEAD — but it used rv63/z,
NOT VIX-term-structure; this is the distinct untested family), campaign/goal100_FINAL_STATE.md.

## METHOD (superpowers TDD; use campaign/bt)
- Signal candidates at t (all trailing, T+1 verified): (a) z-score of VXV/VIX ratio (term slope),
  (b) VXV 1M-change, (c) VIX-to-VXV contango sign, (d) GVZ/OVX 63d z, (e) combined.
- Overlay: state -> scale champion daily return or gate on/off; measure dSR (charged 6.4bps·gross,
  borrow, T+1). State whether it lifts SR/ann, reduces MDD, keeps 0/19 neg, at <=1.6x capital-real.
- Satellite alternative: use the term-structure as a REGIME for a book already on disk (SPY short/long
  via twelve_big, or rate/commodity sleeves) — pick ONE clean testable instrument from on-disk data.
- GATES for overlay: must add SR (dSR>0.15 threshold like prior overlay hunt) AND not hurt MDD/neg-yrs;
  for satellite: SR>=0.6 (2008+ if span allows; VXV is 2007+, usable 2008+), |corr|<0.15, H1/H2>=0.3,
  200x position-lag scramble p<0.05 (use campaign/bt.gates.scramble_positions with CORRECT baseline).
- Be honest: prior overlay hunt showed the champion is "whitened" (timing dead); VXV term-structure is
  the one distinct family — but set and report the prior honestly. If it fails, log exact dSR and the
  dead-variant, do NOT force.

DELIVER: scratch repro + FINDINGS.md gate cards (exact numbers) + trade-record note (instrument/path).
Last line exactly: HUNT_VXV_TERM DONE
