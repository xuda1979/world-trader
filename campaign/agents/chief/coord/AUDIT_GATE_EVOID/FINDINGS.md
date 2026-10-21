# AUDIT_GATE_EVOID — FINDINGS

## Result: CONFIRMED — 2 defective gate-e implementations; p-values VOID in record; verdicts UNAFFECTED

Date: 2026-10-09. Scope registered pre-edit in `CHARTER.md`. The defect
was discovered during HUNT_ENSO_AG (recorded in its FINDINGS + the
5af80bf7 standup entry); this audit executes the recommended scoped
void.

## 1. Defect (verified at code level + numerically)

GATES_CONTRACT.md gate e: "Signal-scramble 200x: real SR > 95th pctile
(p < 0.05)". Two hunts implemented the scramble by shuffling the NET
RETURN series instead of the signal:

- HUNT_WX_DEMAND/work/hunt_wx_demand.py:133 `scramble_p(net_vt)` —
  `rng.shuffle(x)` on the post-cost, post-vol-target return array.
- HUNT_NG_REGIONAL/work/hunt_ng_regional.py:95 `scramble_p(net_w)` —
  same pattern.

SR = mean/std is permutation-invariant: every shuffle reproduces |SR| to
float noise, so `real > |SR_shuffled|` is a coin-flip over ~1e-16
residuals. Repro (work/demo_invariance.py, synthetic, seed 17):

```
[1] BUGGY class: reported 'p' = 0.390 (pure float-noise coin-flip)
    max |SR_scram - SR_real| over 200 shuffles = 1.735e-16
[2] CORRECT class: real SR = -0.190, null-exceedance p = 0.040 (genuine spread)
```

## 2. Defect bound (repo-wide sweep — exactly 2)

DEFECTIVE (shuffle returns):
- HUNT_WX_DEMAND/work/hunt_wx_demand.py (line 133)
- HUNT_NG_REGIONAL/work/hunt_ng_regional.py (line 95)

CORRECT class (permute signal/weights vs real returns, re-run pipeline):
- bt/gates.py `scramble_positions` (canonical; position-lag roll)
- HUNT_BINANCE_AXES/work/hunt_lib.py `scramble_pvalue` (signal permutation)
- HUNT_ENSO_AG/work/hunt_enso_ag.py (monthly signal-state permutation,
  per contract text; implemented after the defect was found)
- HUNT_TREASFUT_round1.py `scramble_perm` (weight-row permutation, re-cost)
- HUNT_TREASFUT_round5.py (imports r1.scramble_perm)
- hunt_vol2_lib.py `scramble_p` (position permutation, re-cost)
- hunt_sector2_r2_harness.py `scramble_multi` (joint weight-path permutation)
- hunt_sector2_r2.py / r3 / round2_scan (per-leg weight permutation)
- QA_dualmom_band121.py (signal + gate permutation)

## 3. P-values VOIDED (exact values + sources)

HUNT_WX_DEMAND (FINDINGS.md table, "scram" column; ALL 20 void):
0.965, 0.745, 0.490, 0.360, 0.300, 0.330, 0.355, 0.415, 0.310, 0.800,
0.175, 0.000, 0.120, 0.070, 0.210, 0.730, 0.165, 0.670, 0.490, 0.470.
Narration citing "best scramble p (0.120)" — void. DEAD_IDEAS.csv row 74
evidence field: "best scramble p 0.120 vs <0.05" — void.

HUNT_NG_REGIONAL (FINDINGS.md table, "scram-p" column; ALL 18 void):
0.450, 0.340, 0.925, 0.010, 0.355, 0.730, 0.165, 0.675, 0.210, 0.780,
0.375, 0.755, 0.985, 0.055, 0.840, 0.005, 0.080, 0.170. Narration
"FAIL e (p=0.93!)" — void; "scramble p up to 0.93 — the 4.19 SR is
statistically indistinguishable from shuffled quantity noise" — the
p-derived clause is void (the artifact diagnosis itself stands on
independent grounds: quantity-book non-tradability + gate d). DEAD_IDEAS.csv
row 73 evidence field: "scramble p 0.45-0.93" — void.

NOT void (measured with correct-class implementations): HUNT_ENSO_AG
scramble p 0.025 (E1_oni0.5_ninalong; monthly state permutation per
contract text); HUNT_BINANCE_AXES; all other gate-e reports in the record.

## 4. Verdict invariance (pre-registered basis for void-without-re-measure)

Gate e is a conjunct (ALL gates must pass). Both hunts failed gates a/c/d
by wide margins for every config, independent of gate e:

- HUNT_WX_DEMAND: best positive SR 0.248 vs gate a >= 1.0 (~4x gap);
  best halves 0.470 < 0.5 (gate c); negY 7-19 vs <= 2 (gate d). Every
  config fails >= 2 of {a, c, d}.
- HUNT_NG_REGIONAL: expressible mechanisms |SR| <= 0.14 (gate a); the
  high-SR F1/F2 rows are non-tradable quantity-book artifacts AND fail
  gate d (negY 4-13 vs <= 2; only one row at 4, still > 2). Every row
  fails >= 1 of {a, b, d} by a wide margin.

Voiding gate e cannot flip any verdict: both hunts remain HONEST
NEGATIVE / DEAD. No re-measure required (nothing adopted from either
hunt; no sleeve exists from either).

## 5. Record edits made (explicit-pathspec commits)

1. HUNT_WX_DEMAND/FINDINGS.md — VOID banner inserted after the Result
   line (tables left byte-intact; historical measurements).
2. HUNT_NG_REGIONAL/FINDINGS.md — same.
3. campaign/results/DEAD_IDEAS.csv rows 73/74 — evidence fields
   annotated "[AUDIT_GATE_EVOID 2026-10-09: scramble p-values void —
   degenerate return-shuffle, not signal-scramble; verdict unaffected]".
   Status/idea/source fields untouched; row count 75 unchanged.
4. STANDUP_LOG.md — round record (house convention).

Champion trio STAGED-UNCHANGED (verified staged-file set identical
before/after each commit; explicit pathspecs only).

## 6. Systemic note

The defective class (shuffle the thing being summarized instead of the
input being tested) is a generic statistical-test bug pattern. The
canonical bt/gates.py implementation and every other hunt predate or
independently implement the correct class; the two defective scripts were
standalone per-hunt reimplementations rather than imports of the shared
harness. HUNT_ENSO_AG already documents the correct-contract reading.
No further action recommended beyond this void.

AUDIT_GATE_EVOID DONE
