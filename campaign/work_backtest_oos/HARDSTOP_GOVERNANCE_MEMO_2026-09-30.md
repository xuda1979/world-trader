# HARD-STOP GOVERNANCE MEMO — decision evidence for the 2 standing V7 HARD stops

**Date:** 2026-09-30 | **Scope:** evidence only — no weights, specs, or manifests changed.
**Question:** the decay monitor (exit 2 since 2026-09-19, b9f8dee) flags 2 HARD stops:
`FXD1_KRWTRI_raw_daily.csv` (w 3.0%, trail2y SR -0.52) and `crossasset_rev_L8.csv`
(w 8.9%, trail2y SR -0.10). Both fail the pre-committed hard rule (trail2y SR < 0) and
decay rule (trail2y < 0.8 x full), both below the w < 10% prune trigger, so the monitor
prunes nothing and the question stands open. This memo gives the operator the numbers
to decide: HOLD, or ACT (zero + renormalize via a governed V# bump).

## 1. The five pre-registered arms (full daily-ledger simulation, v2 conventions)

Identical cost model to `rebuild_v7_ledger.py` (LEV 1.6, 6.4bp/side on |dW| at monthly
rebalance, margin (LEV-1)x5.3%/252, drifted positions). **A0 reconciles with the
committed ledger to 7.2e-16/day** — every arm below is measured on the same engine
that reproduces the canonical V7 record. Script: `hardstop_counterfactual.py`;
table: `HARDSTOP_COUNTERFACTUAL_2026-09-30.csv`.

| arm | full SR | OOS SR | full ann | OOS ann | trail2y SR | trail2y ann | daily DD |
|---|---|---|---|---|---|---|---|
| A0 BASELINE (V7 as committed) | 4.042 | 3.593 | 27.47% | 29.57% | 3.641 | 23.70% | **-3.16%** |
| A1 DROP-BOTH from 2009 (18 sleeves) | 3.982 | 3.668 | 29.21% | 31.90% | 3.849 | 27.91% | -3.95% |
| A2 DROP-KRW only | 4.039 | 3.593 | 28.30% | 30.52% | 3.674 | 24.67% | -3.21% |
| A3 DROP-XREV only | 3.987 | 3.669 | 28.27% | 30.81% | 3.803 | 26.74% | -3.90% |
| A4 ZERO both from 2024-10 (monitor-obeyed) | **4.070** | **3.660** | 27.95% | 30.44% | **3.850** | **27.91%** | **-3.16%** |

## 2. What the numbers say

**The stops are costing real money in the current regime.** Over the trail2y window the
two sleeves contributed -0.26pp/yr of book return net (KRW -0.09pp, XREV -0.18pp); the
+4.2pp A1/A4 trail2y delta decomposes as +3.9pp pure renormalization uplift (the
remaining 88.1% of weight scales up 1.135x) and +0.3pp removed negative marks.

**The decay is recent, progressive, and real — not a one-month artifact.**
Rolling 24m SR: KRW 2.53 (2024-06) -> 2.12 (2025-06) -> 0.24 (2026-06) -> -0.52 (now);
XREV 1.09 -> 0.42 -> 0.09 -> -0.10. XREV has decayed steadily since mid-2024; KRW
collapsed within the last 12 months. Both retain positive FULL-window SRs (0.76 / 1.10),
so this is regime decay, not total-edge death — the monitor is doing exactly its job.

**Dropping from 2009 (A1/A3) deepens the max DD -3.16% -> -3.95%** because XREV was
+1.7pp positive in the Apr-May 2022 rate shock (the DD trough). A4 — the "monitor
obeyed from its trail2y start" arm — captures nearly all the trail2y gain (27.91% vs
27.91% for A1) with DD identical to baseline (-3.16%, trough predates the change), and
weakly dominates A0 on every metric (full SR 4.070 vs 4.042; OOS SR 3.660 vs 3.593).

**KRW is the weaker stop; XREV is the bigger dollar stop.** A2 (drop KRW only) barely
moves anything (trail2y +0.97pp). A3 (drop XREV only) captures +3.04pp of the +4.21pp.
If the operator acts on only one, XREV is the one that matters.

## 3. HONESTY CAVEAT — read before deciding (selection bias)

The arms respond to a signal (the HARD stops) measured on the SAME trail2y window used
to evaluate them. The +4.2pp trail2y delta is therefore **in-sample to the decision**
and must NOT be read as a forward expectation. The honest forward-looking deltas are
the small OOS/full-window differences (A4 vs A0: +0.07 full SR, +0.87pp OOS ann) —
the stops cost little averaged over the whole book history; they cost ~4pp/yr in the
specific 2y regime that fired them, and whether that regime persists is unknowable.
The decision is therefore a judgment call about regime persistence, not arithmetic.

## 4. Decision options (vehicle matters)

1. **HOLD (A0).** Consistent with FROZEN-weights governance (spec §8) and the w<10%
   prune rule. Cost: continued drag IF the decay regime persists; benefit: no
   spec invalidation, no re-verification burden, no hindsight-selection risk.
2. **ACT via governed V# bump (the A4-forward equivalent: zero both sleeves at the
   next rebalance, renormalize the remaining 18).** This is a weight change: it
   invalidates V7_REPLICATION_SPEC.md by its own §8 ("any edit to weights invalidates
   this document; new versions = new V# spec file"). The governed path is: new spec
   file (V8 or V7.1) -> re-run the full verification harness (reproduce_v7-equivalent,
   doc-replication, pseudocode, decay monitor) on the new weights -> new pins.
   Side benefit: the S1 3e-4 pin retires to the 1e-6 baseline (its documented
   retirement condition — "a governed V# bump re-solving weights" — is met by any
   governed bump; a zero+renorm is not a re-SOLVE, so §4.1 language would need the
   V8 spec to state which tolerance applies; a clean re-solve retires it unambiguously).
3. **Partial act (zero XREV only).** Captures 72% of the trail2y delta; same vehicle
   requirement as (2).

## 5. What this memo does NOT decide

Per the maintenance-scope boundary (2026-09-26 session doc), the weight decision is
the operator's. The monitor's rules and this memo are the complete evidence package.
Re-verify trigger for this memo: decay monitor re-run at the next CFTC/data refresh;
if either sleeve's trail2y SR recovers above 0, the stop clears on its own and
this memo is moot; if it deepens, the HOLD cost grows.

---
*Reproducibility: `python3 campaign/work_backtest_oos/hardstop_counterfactual.py`
writes the 5-arm table; A0-vs-ledger recon prints 7.2e-16. Rolling-SR and
contribution decompositions inline in the session log (2026-09-30).*

## ADDENDUM 2026-09-28 16:5x (landing session): E1-refresh vintage note

The table above was computed pre-E1-refresh (11:04). The committed
HARDSTOP_COUNTERFACTUAL_2026-09-30.csv is regenerated post-refresh (commit 17e5be6
ledger) by hardstop_counterfactual.py — same arms, same conventions, deterministic.
Vintage shift = the 19 new E1 marks only (A0 full SR 4.042 -> 4.0458; A4 4.070 ->
4.074; A1 DD -3.95% -> -3.952% etc.). All qualitative conclusions unchanged.
