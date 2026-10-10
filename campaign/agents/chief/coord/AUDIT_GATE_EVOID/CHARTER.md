# CHARTER: AUDIT_GATE_EVOID — scoped record audit: void degenerate gate-e p-values in two prior chief hunts

Pre-registered 2026-10-09, coordinator session (autonomous loop). This is a
SCOPE REGISTRATION audit of an already-discovered defect (found during
HUNT_ENSO_AG, recorded in its FINDINGS and the 5af80bf7 standup record) —
not a hypothesis hunt. Per house convention for audit rounds (cf.
AUDIT_GATES2), the charter fixes scope and acceptance BEFORE the record is
edited.

## Defect under audit

GATES_CONTRACT.md gate e reads: "Signal-scramble 200x: real SR > 95th
pctile (p < 0.05)". Two prior chief hunts implemented the scramble by
shuffling the NET RETURN series and comparing |SR| before/after:

- HUNT_WX_DEMAND/work/hunt_wx_demand.py::scramble_p — shuffles the net
  (post-cost, post-vol-target) return array in place, 200x, counts
  real > |SR_shuffled|.
- HUNT_NG_REGIONAL/work/hunt_ng_regional.py::scramble_p — same pattern.

SR = mean/std is PERMUTATION-INVARIANT: every shuffle reproduces the real
|SR| to ~1e-16 (float noise). The reported p-values are therefore
degenerate coin-flips over float-noise comparisons — measurements, not
evidence. Verified numerically this session (synthetic demo: max
|SR_scram - SR_real| = 3.7e-16 over 200 shuffles; p = 0.795 pure noise).

## Scope (ALL and ONLY these record edits)

1. HUNT_WX_DEMAND/FINDINGS.md — annotate the reported scramble p-values
   (best 0.120 and the full-table column) as VOID (degenerate), with
   pointer to this audit. No other edits.
2. HUNT_NG_REGIONAL/FINDINGS.md — same for its scramble-p column
   (0.450/0.925/etc.), including the "FAIL e (p=0.93!)" narration.
3. campaign/results/DEAD_IDEAS.csv rows 73 (HUNT_NG_REGIONAL) and 74
   (HUNT_WX_DEMAND) — annotate the p-value mentions in the evidence
   fields as void (append-only intent; rows are edited in place ONLY to
   add the void marker, verdict field untouched).
4. STANDUP_LOG.md — round record for this audit (house convention).

Explicitly OUT of scope: verdict changes (both hunts stay honest-negative
DEAD), the hunt scripts themselves (they are historical artifacts; the
defect is documented, not erased — HUNT_ENSO_AG already implements gate e
correctly and the canonical bt/gates.py scramble_positions is correct),
champion files, weights, manifest, suite, and any file not listed above.

## Verdict-invariance evidence (pre-registered acceptance basis)

Both hunts failed gates a/c/d by wide margins INDEPENDENT of gate e:

- HUNT_WX_DEMAND: best positive SR 0.248 vs gate a >= 1.0 (gap ~4x);
  negY 7-19 vs gate d <= 2; halves fail gate c. Gate e is moot.
- HUNT_NG_REGIONAL: expressible mechanisms |SR| <= 0.14 (gate a); the
  high-SR rows fail gate d (6-13 negY vs <= 2) and are quantity-book
  artifacts (non-tradable) — gate d failure alone kills every row.

Since gate e is a conjunct (ALL gates must pass), and gates a/d fail by
wide margins for every config in both hunts, voiding gate e cannot change
any verdict. This is the formal basis for VOID-without-re-measure.

## Acceptance criteria

- A scan demonstrating the defect bound: exactly 2 defective
  implementations (the named hunts); all other gate-e implementations in
  the repo (HUNT_BINANCE_AXES hunt_lib, HUNT_ENSO_AG, HUNT_TREASFUT r1/r5,
  hunt_vol2_lib, hunt_sector2 family, bt/gates.py scramble_positions)
  permute signal/weights against real returns (correct class).
- FINDINGS.md here records: the numeric invariance demo, the exact
  p-values voided with their sources, and the corrected reading of each
  hunt's verdict with gate e struck.
- The 4 record edits land via explicit-pathspec commits; staged champion
  trio untouched (verified staged-file set identical before/after).

## Reproduce

python3 campaign/agents/chief/coord/AUDIT_GATE_EVOID/work/demo_invariance.py
