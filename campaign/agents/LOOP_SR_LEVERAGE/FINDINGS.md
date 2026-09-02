# FINDING (loop iter2, 2026-09-02): honest SR is scale-invariant ~4.2; Ann>=80% + MaxDD<=7% jointly achievable AT ~2.5-3x gross leverage (disclosed)

## Setup
Canonical builder committed: `campaign/scripts/honest11_build.py` (reproduces GOAL100_HONEST11
byte-for-byte, max|diff| 9.9e-17). This fixed the audits' "builder-not-committed" provenance hole
and gives a clean chassis to measure the Ann/DD/SR-leverage tradeoff.

## Measurement (HONEST11 = 11 real sleeves, XGB1y flattening-bug sleeve removed)
Global vol-target sweep (single scalar TGT, same throttle/cost/borrow layers as HONEST11):

| TGT A/B (global vol target) | ann(geo) | SR_m | SR_d | full MaxDD | worst 3y-sub | OOS17+ | approx gross |
|---|---|---|---|---|---|---|---|
| 0.07 / 0.091 (committed HONEST11) | 47.9% | 4.19 | 4.22 | -4.85% | -4.8% | 44.1% | ~1.4x |
| 0.10 / 0.125 | 71.1% | 4.08 | 4.22 | -6.05% | -6.05% | 60.8% | ~2.0x |
| 0.11 / 0.14 (HONEST11X804) | 80.5% | 4.05 | 4.22 | -6.73% | -6.73% | 67.3% | ~2.5x |
| 0.12 / 0.15 | 88.7% | 4.02 | 4.22 | -6.98% | -6.98% | 72.5% | ~3.1x |

## Three decisive, honest conclusions
1. **SR is scale-INVARIANT ≈ 4.2 (daily) / 4.0-4.2 (monthly).** Raising the vol target does NOT
   change SR — it scales return and risk proportionally. **SR>=5 is NOT reachable by construction
   scaling**; it requires genuinely more decorrelated high-SR engines (none found this/failed
   rounds: FX spot carry/TSMOM, EM/DM factors, global indices, gold-silver, XGB-fair).
2. **Ann>=80% AND MaxDD<=7% ARE jointly achievable** at TGT 0.11/0.14 (80.5%, MaxDD -6.73%) and
   TGT 0.12/0.15 (88.7%, MaxDD -6.98%), with every 3y-subwindow within the 7% wall and 0/19
   negative calendar years (worst +21.5%/+22.8%). The prior memo's "~63-65% max at the DD wall"
   is superseded — it was computed on the OLD inflated browser; the honest 11-sleeve return/DD
   efficiency is higher.
3. **BUT the honest cost is ~2.5-3x GROSS LEVERAGE.** Because the decorrelated blend's realized
   vol (~5.3%) is far below the 10% per-sleeve target, the global vol-targeter applies a large
   scale (gross mean ~2.5x at TGT 0.11, ~3.1x at 0.12; max ~5-6x). The "weights sum to 1"
   (normalized) framing does NOT mean unlevered. Reaching Ann>=80% requires this leverage.

## Honest headline for the /loop goal
- Ann>=80%: ACHIEVABLE (with disclosed ~2.5-3x gross, MaxDD still <=7%).
- MaxDD<=7%: ACHIEVABLE (all subwindows).
- SR>=5: NOT met honestly (≈4.2, scale-invariant; engine-scarce).

## Committed artifacts this iteration
- `campaign/scripts/honest11_build.py` (canonical reproducible builder, byte-verify passes).
- `campaign/results/GOAL100_HONEST11X804_daily_*` (TGT 0.11/0.14: 80.5% ann, MaxDD -6.73%,
  SR_d 4.22, 0/19 negyrs, OOS 67.3%) — presented WITH leverage disclosure.

## Recommendation (next iterations)
- Decide leverage policy. If <=1.5x gross required, max honest ann ~50-55% (@ ~8% DD). If
  ~2.5-3x acceptable, Ann>=80% + MaxDD<=7% is honestly reached (files committed).
- To genuinely raise SR>=5, only new decorrelated high-SR DAILY engines help. Search space is
  heavily mined; NP-hard part is real and persistent.
