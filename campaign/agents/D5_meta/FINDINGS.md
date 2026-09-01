# D5_meta FINDINGS — Round 1 (2026-09-01)

Mission: beat GOAL100 BALANCED (55.5% ann, SR 5.24, DD -6.9%) under IS(2008-2016)-frozen /
single-OOS(2017+)-reveal discipline, using champion_build.POOL (16 sleeves) and exact
construct() conventions. Harness: wb.py generalizes construct() (verified byte-identical to
committed champions, max dev 1e-16). All returns net of 6bps incl. per-sleeve + throttle turnover.

## Baseline (regenerated, identical to committed)
| config | IS ann | IS SR | IS DD | OOS ann | OOS SR | OOS DD | FULL ann | FULL SR | FULL DD |
|---|---|---|---|---|---|---|---|---|---|
| A (vt.085 thr.04 fr.5) | 43.9 | 4.79 | -5.6 | 52.5 | 5.52 | -7.3 | 48.9 | 5.21 | -6.9 |
| B (vt.11 thr.03 fr.5) | 56.2 | 4.79 | -6.8 | 67.8 | 5.68 | -7.9 | 62.4 | 5.31 | -7.9 |
| BALANCED (A+B)/2 | 50.0 | 4.80 | -6.2 | 60.2 | 5.62 | -6.9 | 55.5 | 5.24 | -6.9 |

## Idea 1 — FR grid {0.40..0.60}, IS-select
IS SR flat 4.78-4.80 (pure plateau); IS ann monotone increasing in fr (deeper cuts only hurt).
IS pick fr=0.6 both configs. OOS reveal: A 52.7@-7.3, B 68.1@-7.7 (vs fr.5: 52.5@-7.3 / 67.8@-7.9).
VERDICT: no IS preference for deeper cuts; fr differences = noise (see idea 6). Kept as evidence only.

## Idea 2 — Dual throttle (fast lb126 + slow lb252), grids thr .03-.05 / .05-.07
IS best: B .05/.07 ann 57.1 SR 4.81 DD -7.6; B .05/.05 56.8/-6.7. OOS reveal of dd<=7 rule pick
(.05/.05): OOS DD **-10.4%** FAIL. True IS-argmax (.05/.07) revealed: OOS ann 67.7 SR 5.57 DD **-9.7%** FAIL (>8%).
A-family dual = identical to single throttle (slow throttle never triggers IS or OOS).
VERDICT: REJECT — slow throttle overfits IS calm (2009-2016) and blows DD OOS.

## Idea 3 — Per-sleeve vt (defensive A5r7/A1credit/a6r7 -> 12, aggressive XGB1y/H21_f5/H21_br -> 9)
All 4 variants LOSE on IS for both configs. A: base SR 4.79 vs best variant 4.74 (ann 43.9 vs 43.5).
B @thr.03: base 56.2/-6.8 vs def12agg9 55.3/-7.3, agg9 55.4/-7.3, def12 56.0/-6.8 (ann strictly worse).
VERDICT: REJECT on IS (no OOS reveal needed) — uniform vt0.10 already optimal; tilting adds DD without IS return.

## Idea 4 — 17th sleeve C5_ng_summer_weekday_ddt
+ddt-as-17th: IS SR collapses 4.79 -> 4.39 (A), 4.79 -> 4.39 (B). REJECT.
ddt-replacing-C5ngsum: A IS 42.9/-6.3 vs EW-16 43.9/-5.6 — fails BOTH-ann-and-DD rule. REJECT.
(B OOS 68.5 would look better but IS says no — not revealed as candidate.)
VERDICT: keep 16-sleeve pool.

## Idea 5 — Champion-of-champions (IS DD<=6.5% & neg0 -> max IS ann)
Eligible: all A_fr (dd -5.3..-6.0), BAL_fr.4/.5. B variants ineligible (IS DD -6.6..-7.3 > -6.5).
IS winner: **BAL_fr0.5 = the incumbent champion itself** (ann 50.0). Selection is self-consistent;
no constructed variant dominates it on IS. Candidate BAL_fr0.6 (from idea 1 IS-ann rule, dd -6.6) 
full: 55.7% ann SR 5.24 DD -7.2 (worst yr DD 2025 -7.2) vs incumbent 55.5/5.24/-6.9 — within noise.

## Idea 6 — Block bootstrap (1000x, 21d circular blocks) OOS SR diff BAL_fr0.6 vs BALANCED
OOS SR: new 5.608 vs old 5.620, diff -0.012. Bootstrap mean diff -0.0008, 90% CI [-0.0035, +0.0013].
**P(new <= old) = 0.654** -> fr=0.6 is NOT better; the IS-ann gain does not transfer.
VERDICT: NULL — incumbent BALANCED stands. CSV of candidate deleted (not saved to sleeves/).

## NUMBERED SUMMARY
1. Idea 1 FR grid: IS flat (SR 4.78-4.80), IS-pick fr.6; OOS A 52.7/-7.3, B 68.1/-7.7 vs fr.5 52.5/-7.3, 67.8/-7.9. NOISE.
2. Idea 2 dual throttle: IS best B.05/.07 57.1@-7.6; OOS DD -9.7% (alt .05/.05: -10.4%) -> REJECT (DD gate).
3. Idea 3 per-sleeve vt: all variants IS-worse (B thr.03: 55.3-56.0 ann vs 56.2; DD worse) -> REJECT on IS.
4. Idea 4 17th sleeve ddt: IS SR 4.39 vs 4.79; replace-variant fails BOTH-rule (A 42.9/-6.3 vs 43.9/-5.6) -> REJECT.
5. Idea 5 champ-of-champs (dd<=6.5): selects incumbent BAL_fr0.5 (IS 50.0); self-consistent, no dominator.
6. Idea 6 bootstrap: OOS SR diff -0.012, P(new<=old)=0.654 -> BAL_fr0.6 not better; candidate discarded.

FINAL VERDICT: **NO DELIVERY.** Charter bar = beat BALANCED on IS AND OOS with DD<=8%: not met.
Incumbent GOAL100_CHAMPION_BALANCED (55.5% ann, SR 5.24, DD -6.9%; IS 50.0@-6.2 / OOS 60.2@-6.9) is
unchanged and survives its own IS selection. Every meta-parameter move (fr, dual throttle, per-sleeve
vt, 17th sleeve) is inside bootstrap noise or fails the DD gate. Honest implication: this 16-sleeve
pool + construction is at a LOCAL PLATEAU ~55-56% ann; reaching 100% requires NEW decorrelated
high-SR sleeves (data-domain expansion), not more meta-tuning.
ROUND 1 DONE
