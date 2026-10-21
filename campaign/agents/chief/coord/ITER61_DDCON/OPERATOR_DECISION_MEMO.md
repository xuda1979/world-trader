# OPERATOR DECISION MEMO — ITER61 candidate adoption + Option-A champion provenance

Date: 2026-10-12. Author: chief (consolidation round; no champion change this round).
Scope registered before any edit: this memo consolidates the two pending operator
decisions into one decision document with all numbers independently re-verified
from the published CSV artifacts on 2026-10-12 (recomputation script inline in
coord/ITER61_DDCON/work; results below). Nothing in this memo changes repo state.

## Decision 1 — ITER61 candidate (A_cap28): adopt or hold

### What is on the table
The ITER61_DDCON candidate (`campaign/results/ITER61_DDCON_candidate_daily.csv`,
weights `ITER61_DDCON_candidate_weights.csv`): incumbent RAW-EW13v2 relw with the
(C5ng + C5ngsum) block share capped at 0.28 (incumbent fitted share 0.32857),
non-NG sleeves renormalized pro-rata, gross 1.6 unchanged. This is family A —
the incumbent post-fit cap mechanism (same W_BRWT_CAP pattern), not a new engine.

### Independently re-verified numbers (2026-10-12, from CSVs)

| Metric | Incumbent | A_cap28 | Gate | Pass |
|---|---|---|---|---|
| Full SR | 3.820357 | 3.784489 | >= 3.770357 (G1) | YES |
| Full ann | 23.9215% | 23.8610% | >= 23.4215% (G2) | YES |
| Full MDD | -3.73394% | -3.30485% | strictly shallower (G3) | YES |
| OOS MDD | -3.73394% | -3.30485% | strictly shallower (G4) | YES |
| Neg years / worst yr | 0 / +7.906% | 0 / +7.553% | 0 neg, worst >= +5% (G5) | YES |
| Turnover | 4.3311 bp | 4.1917 bp | <= 6.4 bp (G6) | YES |
| Gross max | 1.6 | 1.6 | <= 1.6 (G7) | YES |
| NG block share | 0.32856826 | 0.28000000 | = 0.28 cap (G8 construction) | YES |

Weight-file verification: NG block = C5ng 0.15290004 + C5ngsum 0.12709996 =
0.28000000 exactly; non-NG sleeves rescaled proportionally (each up by
share-scaled factor); relw sums 1.0 both sides; day-level corr with incumbent
0.995579, mean |diff| 1.89 bps. Battery B1-B5 (post-hoc checks, charter §6):
seasonal split, placebo-cap discriminancy (B4: non-NG placebo cap makes MDD
WORSE, -3.7501% — the improvement is NG-specific, not "any cap helps"),
cost-stress 6.4/8/10 bps all preserve the MDD advantage with stable SR gap.

### What the operator is actually choosing
This is NOT a beat (SR 3.7845 < 3.820357 incumbent). It is an operator-objective
trade: pay ~0.036 SR and ~0.06pp ann to buy ~0.43pp shallower max drawdown
(-3.73% -> -3.30%) and a structurally less NG-concentrated book. The 8 gates were
pre-registered in FINDINGS_PRECOMMIT.md BEFORE any arm ran; A_cap28 passed all
8 plus the battery. Family read-out: only the post-fit cap family (A) works;
in-fit constraints (B) and DD-soft objectives (C) both make DD worse — the DD
is a weight-space concentration problem.

Cost of the trade (honest): 2024 gives up ~2.3pp, 2023 ~1.0pp annual return
(NG-strong upside years); 9 of 18 years are slightly worse; the remaining DD
episodes (-2.25% 2026-03-17 brwt-driven, -1.92% 2026-06-03) are NOT NG and are
untouched by the cap. The cap fixes the NG concentration, not all drawdown.

### Options
1. ADOPT now (its own round per §7): builder cap_block extension (family A —
   same pattern as W_BRWT_CAP, flagged low-risk) + --verify chain, archive
   supersede (archive_*_SUPERSEDED_by_ITER61_DDCON), champion card update,
   unstage Option-A trio in favor of the new champion trio. Chief recommends
   this: all gates green, battery clean, mechanism is the incumbent's own.
2. HOLD as candidate: keep incumbent champion of record; ITER61 files stay
   parked under campaign/results/ITER61_*. Zero action cost; candidate is
   deterministic and re-derivable.
3. REJECT: if the operator reads the 0.036 SR cost as too high for 0.43pp MDD,
   append a DEAD_IDEAS row and free the namespace.

Chief's pre-registered recommendation (FINDINGS.md §5): ADOPT (option 1).
The operator has not decided; nothing executes until they do.

## Decision 2 — Option-A champion provenance (resolves the staged trio)

### Current state
The Option-A trio sits STAGED in the main git index (not committed):
- campaign/CHAMPION_CARD.md
- campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
- campaign/results/RAWEW13v2_IS_SR_weights.csv
Staged-tree sha1 (git diff --cached --binary | shasum): b1669940c2fa0f31
(as of 2026-10-12). Byte-identity vs the 2026-10-08 Option-A staged state was
re-verified 2026-10-12 (badcommit_sideeffect_verify round) against durable
pins: the standup record tree sha16 and the side-commit tree — the staged trio
is untouched since 2026-10-08.

Stash warning (binding, from incidents 82fa7401): stash is UNSAFE while this
trio is staged (two near-loss incidents, both self-caught and recovered).
Any baseline-isolation work must use a HEAD worktree, never stash.

### What Option-A is
Option-A is the champion-provenance regularization: it makes the champion
card + daily CSV + weights CSV on disk consistent as a coherent provenance
triple for the current champion of record (RAW-EW13v2 WEIGHTED @1.6x), instead
of the card/daily/weights drifting independently. It does NOT change champion
performance numbers (same champion, regularized provenance).

### Interaction with Decision 1 (why they are one memo)
- If the operator ADOPTS the ITER61 candidate (option 1): the Option-A trio is
  superseded at adoption — the adoption round stages the NEW champion trio
  (ITER61 daily + weights + updated card) and the Option-A staged content is
  dropped in favor of it. One decision collapses the other. The provenance
  regularization intent of Option-A carries forward into the new champion's
  triple.
- If the operator HOLDS (option 2) or has no near-term adoption plan: committing
  the Option-A trio resolves the long-lived staged state (which has already
  caused two stash-near-loss incidents) and pins champion provenance durably.
- If the operator REJECTS ITER61 (option 3): same as HOLD for Option-A — commit
  the trio.

### Options
1. If adopting ITER61: supersede (drop Option-A staged content at the adoption
   commit; carry its provenance intent into the new champion triple).
2. If not adopting: commit the Option-A trio as-is (explicit pathspecs, no
   stash, per the standing constraint) and close the staged state.
3. Leave staged indefinitely: NOT recommended — the staged state is an
   operational hazard (stash unsafety) with no offsetting benefit once the
   decision above is made.

## Standing constraints (unchanged, binding on any execution round)
- Champion of record until any adoption: RAW-EW13v2 WEIGHTED @1.6x
  (daily sha16 cfa9ec4d38158691, weights sha16 a384d6b92e258fd5).
- Frontier-closure law (#147/#148): new hunts need NEW data or rule change.
- Explicit-pathspec commits only while the trio is staged; NO git stash.
- Adoption is its own round: builder extension + --verify, archive supersede
  naming, champion card update, DEAD_IDEAS/standup records.

## Recommendation summary
Adopt the ITER61 candidate (Decision 1, option 1) in a dedicated adoption
round; supersede Option-A at that commit (Decision 2, option 1). If the
operator declines adoption, commit the Option-A trio to close the staged
state. No action is taken by the chief on either decision without the
operator's explicit go.

— end of memo —
