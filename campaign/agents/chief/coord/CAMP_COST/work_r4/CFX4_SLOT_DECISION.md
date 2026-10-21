# CFX4 SLOT DECISION — CAMP_COST Round 4 (2026-09-07, analysis only)

Charter: quantify the three options for the CFX4 slot, champion level, FULL |dW| @ 6.4bps
one-side, margin 4.5% on 1.3x, under the CURRENT committed champion of record
(GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv, commit b268e52 re-emit). No champion,
weights, builder, or results file touched.

Reproduction: `work_r4/cfx4_analysis.py` (headline table), `work_r4/cfx4_precision.py`
(P1-P5), `work_r4/cfx4_c1b.py` (artifact decomposition). All in-memory; stdout only.

## 0. Starting-state verification (everything below rests on this)

- `rawew13v2_build.py --verify`: n=4805/4805, maxdev **9.996e-17 IDENTICAL**; weights
  maxdev 2.220e-16 IDENTICAL; gross mean=max=1.600000, 0 days >1.6; turnover
  **5.2622 bps/yr**. The committed bytes are the honest costfix re-emit.
- CFX4 committed relw = **0.0 exactly** (grep RAWEW13v2_IS_SR_weights.csv).
- Mechanism (charter premise confirmed): CFX4 data starts **2019-09-10** > IS_END
  2017-01-01 -> IS-SR = 0 (len<200 branch) -> max(0,0)^0.55 = 0 -> weight 0 every day.
  The "13-sleeve" champion is a 12-sleeve book.
- Champion span vs CFX4 span: CFX4 ends 2026-08-05, champion ends 2026-08-27 ->
  CFX4 is ALSO stale for the last **16 champion rows** (would earn fillna(0) if weighted).

## 1. The three options (exact numbers, 252d ann, daily SR)

| option | ann% | SR | MDD% | neg yrs | worst yr% | H1/H2 SR | OOS17+ ann% | turnover bp/y |
|---|---|---|---|---|---|---|---|---|
| **OPT-A keep-as-is** (= committed) | **37.195** | **3.181** | **-6.69** | **0/19** | +7.31 | 3.56/2.98 | 40.65 | 5.2622 |
| **OPT-B drop slot** (12 slots, IS refit) | 37.195 | 3.181 | -6.69 | 0/19 | +7.31 | 3.56/2.98 | 40.65 | 5.2622 |
| OPT-C1 OOS 2y-live-SR weight (as run) | 36.301 | 3.168 | -6.63 | 0/19 | +6.99 | 3.56/2.98 | 40.42 | 5.2396 |
| OPT-C1b same, weight from CFX4 inception | 37.158 | 3.186 | -6.69 | 0/19 | n/c | n/c | n/c | n/c |
| OPT-C2 walk-forward live-SR (min 500 obs, qtrly) | 37.186 | 3.183 | -6.69 | 0/19 | +7.31 | 3.56/2.98 | 40.64 | 5.2762 |

Deltas vs OPT-A (exact, `cfx4_precision.py` P2):
- OPT-B: dAnn +0.0000pp, dSR +0.00000, dMDD +0.0000pp, max|dNet| **2.776e-17**.
- OPT-C1: dAnn **-0.8941pp**, dSR -0.01255, dMDD +0.0660pp (improvement), max|dNet| 3.328e-03.
- OPT-C2: dAnn -0.0091pp, dSR **+0.00184**, dMDD +0.0000pp, max|dNet| 3.284e-04.

OPT-A recon vs committed champion: inner=4805, maxdev **9.996e-17 BYTE-EXACT**.

## 2. Why OPT-B is an exact no-op (proven, not asserted)

P1 identity: max|netA - netB| = 2.776e-17, max|turnoverA - turnoverB| = 1.563e-15.
Algebra: Wg_i = nav_i*relw_i / Σ_j(nav_j*relw_j) * GEAR (the row-scalar nav.mean cancels in
d2/d2.sum(); verified max|WgA - identity| = 3.886e-16). With relw_CFX4 = 0 the slot
contributes 0 to the numerator AND 0 to the denominator: **a zero-relw slot is
algebraically inert**. Dropping it refits nothing (the other 12 weights are unchanged by
construction — the weight engine never renormalizes across the dropped name's relw).

BUT "no-op in returns" ≠ "no-op in bytes": float summation order over 13 vs 12 columns
differs at the ~1e-17 level on **3941/4805 rows**, and 3941/4805 rows change their CSV
`repr` -> a drop-slot re-emit would rewrite 82% of the champion CSV, dirty the weights CSV
(remove the CFX4,0.0 line), and churn the champion/lineage pin tests — for a 2.8e-17
return delta. Zero benefit, real re-emit + test churn.

## 3. Why OPT-C moves almost nothing: NAV-drift starvation (the structural finding)

Capital share under NAV-drift weights ∝ relw_i x nav_i / Σ_j relw_j x nav_j. The 12 live
slots have compounded since 2008; any slot starting 2019 has a NAV ~1.5 orders of
magnitude smaller. Measured (`cfx4_analysis.py` + snapshots):

- Committed book capital shares (Dec-31 snapshots): brwt10/7/5/15 hold
  26.1/20.4/18.0/14.3% (2017) -> 24.5/23.0/18.3/9.7% (2026); the brwt family holds
  **~80% of capital** throughout; the smallest legacy slots (a6r7, carryv2, diescrack)
  sit at **0.27-1.1%** despite committed relw 0.31-0.55.
- Under OPT-C2, CFX4 relw rises to 1.3649 (first nonzero 2021-10-01) -> 1.4307 final, all
  INSIDE the committed 12-sleeve relw range [0.651, 1.860] — yet its **capital share never
  exceeds 0.6879%** (mean 0.5499% over active days). The entire OPT-C2 intervention moves
  the champion by ≤0.009pp ann.
- Same starvation hits ANY late-start sleeve in this engine: the weight rule is
  effectively closed to sleeves born after the book has compounded for years.

**This is the key decision input: option C is not merely "unproven", it is structurally
impotent in the committed weight engine.** Making late-start sleeves matter would require
a NAV-reset / inception-anchored weight scheme — an ENGINE change out of scope here
(analysis-only charter), not a slot decision.

## 4. OPT-C honesty audit (charter's concern, quantified)

- OPT-C1's headline -0.8941pp is **NOT the rule's effect**: it is an idle-capital
  artifact. As-run, CFX4's fitted weight (sr_2y = 1.6494 on 2019-09-10..2021-09-09 n=523 ->
  relw 1.3168) is applied from 2008-03-31; `fillna(0)` parks **2.996% of gross** at zero
  return for 11.5y (2987 days). Decomposed (`cfx4_c1b.py`): artifact = +0.8563pp of the
  -0.8941pp; the true inception-corrected effect is **-0.0378pp ann / +0.005 SR** (C1b).
- OPT-C1 (either variant) fits the weight on 2019-2021 data INSIDE the reported 2008-2026
  backtest -> rule-change backtest, optimistic by construction. Charter-flagged; disclosed.
- OPT-C2 (walk-forward: quarterly refit from ≥500 prior live obs, weight 0 before
  2021-10-01) is the honest variant and is the one reported in §1/§3. Note its +0.0018 SR
  is 1 quarter of nothing — inside noise, and only meaningful at ≤0.7% capital anyway.
- Rule generality probe (n=2, NOT a gate, P5): applied to the two youngest POOL sleeves,
  the walk-forward rule lands at 1.041 vs committed 0.982 (QAxasts, ratio 1.06) and 0.863
  vs 0.651 (carryv2, ratio 1.33) — sane tracking, no blow-up, but n=2 and both sleeves
  pre-date IS_END so their committed weights are IS-legal anyway.

## 5. CFX4 the signal, separate from the slot (for the record)

Standalone on its own span 2019-09-10..2026-08-05, n=1799: ann 14.91%, SR **1.911**,
MDD -9.26%, H1 2.44 / H2 1.28, neg 2/8 (2019 -0.33%, 2026 -4.13%), worst -4.13% ->
charter gate d PASS; corr to eq-w 12-book **+0.0618** -> gate f PASS (|corr|<0.15);
gate a (SR>=1.0) PASS. Span 7y << 19y charter intent (unjudgeable long-horizon,
disclosed). CFX4 is a GOOD sleeve with a slot problem, not a bad sleeve. Note the family
context: FX-carry as a family is DEAD_IDEAS rows 7/65/95 — CFX4 stays a live champion
SLOT question only; no new carry signal is proposed here (no re-testing of dead families).

## 6. RECOMMENDATION

**OPT-A: keep-as-is** — with a bookkeeping amendment, not a re-emit:

1. The champion is a 12-sleeve book; CFX4 is a vestigial 0-weight slot. Document that
   (this file + a one-line note in the builder) rather than re-emitting anything.
2. Do NOT drop the slot (OPT-B): byte-churn on 3941/4805 champion rows + weights-file +
   pin-test churn for a 2.8e-17 return delta.
3. Do NOT adopt an OOS weight rule (OPT-C): structurally impotent (≤0.69% capital share
   ceiling for any 2019+ slot; net effect ≤0.01pp) and the C1 variant carries an
   in-backtest fit. If late-start sleeves are ever to matter, that is a deliberate
   NAV-reset ENGINE decision for coordinator+user, taken on its own evidence.
4. Forward note: CFX4 the signal passes gates a/d/f on its own span. If the campaign ever
   adopts inception-anchored weights, CFX4 is first in line — decide then, not now.
5. Disclose the staleness: CFX4 ends 2026-08-05, 16 champion rows before the book's end;
   under ANY include-rule its tail would currently be fillna(0). Worth fixing in the CFX4
   feed regardless of the slot decision.
