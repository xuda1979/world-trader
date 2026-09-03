# HUNT_VOLOVERLAY — SR-lifting vol/timing overlay (iter 6)

GOAL: the honest SR is scale-INVARIANT ~3.92. Ann>=80% needs either new decorrelated engines OR a
lift in effective SR. This hunt targets a REGIME/TIMING OVERLAY that raises the blend's SR and/or
lowers its MaxDD (freeing volatility headroom) WITHOUT adding leverage — i.e. a decorrelated
on/off-tilt signal applied on top of the existing champion construction.

DO NOT re-run (dead): Moreira-Muir naive VIX vol-managed factor, 2022+ weak-regime gating already in
FF2, CFNAI gates, M2-gold, FOMC x gold/NG. READ loop_team/HUNT_CROSSREGIME/FINDINGS.md,
HUNT_FF2/FINDINGS.md, STATS_REVIEW/FINDINGS.md first.

GOAL OF OVERLAY: give a STATISTICALLY MEANINGFUL SR/dd improvement on the EXISTING champion
(campaign/scripts/honest13_build.py construction), with the overlay signal itself honest
(T+1, no lookahead, trailing-only), borrowed-cost-neutral (no added leverage), and NOT already
implicit in the 14 sleeves.

DATA: fred dir (VIX, DGS*, T10YIE, hy_oas, baa, aaa, international 10y), ff_factors (MKT,SMB,HML,
RMW,CMA,UMD), DEX EM FX, options? Check VIXCLS/VIX data on disk. Equity panel twelve_big for breadth.

PROTOCOL (measure on the CHAMPION ret series, not a sleeve):
1. Load GOAL100_HONEST14V3_BALANCED_daily.csv (the clean ret series).
2. Build candidate overlay signal O_t (using data<=t): regimes (vol, cross-section breadth, funding,
   rate-curve slope, credit spread stretch, EM FX stress), dictating a scale m_t in [0, scale_cap].
3. Apply modified ret'_t = ret_t * m_t (recomputing equity path), then re-run full stats:
   SR_d, ann_geo, MaxDD, 0/neg yrs, and (crucially) whether SR IMPROVES WITHOUT inflating returns
   beyond the leverage honesty contract. Since SR is scale-sensitive only to the TIME-VARYING part,
   a good overlay must raise SR by MORE than its cost; quantify using 200x position-lag scramble of
   the overlay m_t (p<0.05) and a H1/H2 split.
4. Report exact before/after. If SR rises by >0.15 with MaxDD not worse and scramble-pass and
   |corr| of the overlay-induced weight to champion <0.15, deliver it as a reusable overlay module
   campaign/scripts/*.py + FINDINGS.md.
Gates for the overlay: SR lift>0.15 sustained, MaxDD<=-current, 200x position-lag scramble of the
TIMING signal p<0.05, H1/H2 both improved or flat, <=2 neg yrs. Money-neutral (lever<=current).
Deliver FINDINGS.md with exact before/after + scatter/decile evidence. Last line: HUNT_VOLOVERLAY DONE
