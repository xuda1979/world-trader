# D5_meta — champion construction upgrade (IS-disciplined only)

Current champion: 55.5% BALANCED (A: vt.085/thr.04 50-50 with B: vt.11/thr.03).
Your mission: BEAT it under the same IS/OOS discipline (IS = 2008-2016 only for any new
parameter; single OOS reveal; report both windows for every candidate).

Tools: campaign/scripts/champion_build.py (canonical builder — import construct(), POOL).
Pool: the 16 sleeves in champion_build.POOL. You may also include:
  campaign/agents/C5_newdata/sleeves/C5_ng_summer_weekday_ddt.csv (ddt variant)
  as a 17th sleeve variant to test (replacing C5ngsum or alongside — test both, IS-decide).

IDEAS (in order; each IS-frozen, OOS-revealed once):
1. Throttle FR grid (currently fixed 0.5): IS-select fr in {0.4,0.45,0.5,0.55,0.6} for A
   and B; does IS prefer deeper cuts? OOS-check honestly.
2. Dual throttle: A-throttle (thr .04 lb 126) AND slow throttle (thr .06 lb 252) stacked —
   IS-select both thresholds from small grids.
3. Per-sleeve vt targets: defensive sleeves (A5r7, A1credit, a6r7) at vt12, aggressive
   (XGB1y, H21) at vt9 — IS-decide the split, OOS-reveal.
4. 17th sleeve test: add C5ngsum_ddt; EW-17 vs EW-16 on IS; keep only if IS better on BOTH
   ann and DD, then OOS reveal.
5. Champion-of-champions: IS-select among {A, B, BAL, your variants} by IS DD<=6.5% then
   max IS ann; reveal once.
6. Bootstrap the winner: 1000x block bootstrap (21d blocks) of the OOS SR difference vs
   current BALANCED — report the p-value that yours is better.

Deliver only if you BEAT BALANCED on IS AND OOS with DD<=8% everywhere.
Report in FINDINGS.md with full IS/OOS tables. Last line: ROUND 1 DONE
