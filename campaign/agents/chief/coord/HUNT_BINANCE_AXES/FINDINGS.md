# FINDINGS — HUNT_BINANCE_AXES (first measurement of ITER60's two new axes)

Date: 2026-09-30. Charter: `../CHARTER.md` (pre-registered before any result).
Gates: `coord/GATES_CONTRACT.md`. Cost model: T+1, 6.4bps one-side FULL |dW|,
0.5%/yr borrow, vol-target 10% ann trailing-63d, scale clip 3.0,
signal-scramble 200x (p95), |corr| < 0.15 vs champion
(campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv).

## VERDICT: HONEST NEGATIVE — no family clears the SR >= 1.0 bar. No sleeve added.

40 configs pre-registered and measured across 3 families (metrics 40, depth 24,
cross-sectional RV 6 — 70 total). Full sweeps: `work/run_axis_metrics.py`,
`work/run_axis_depth_rv.py`; finalist gates: `work/finalist_gates.py`.

## Family 1: binance_metrics (positioning + taker flow, BTC 2020-09+, ETH 2021-12+)

Top of family (both windows = plateau, sign = contrarian fade of crowding):

| config | net SR | H1 | H2 | negyr | worst yr | scramble p95 | corr champ | vol |
|---|---|---|---|---|---|---|---|---|
| BTC glob_ls fade w21 | **0.945** | 1.16 | 0.71 | 1 | -3.0% | PASS (real > p95) | -0.011 | 9.5% |
| BTC glob_ls fade w63 | **0.914** | 1.06 | 0.75 | 1 | -9.9% | PASS | -0.016 | 9.5% |

This is a genuine NEAR-MISS (5.5% below the 1.0 bar): every other gate passes
(halves, plateau 21/63, scramble, decorrelation, vol-target, 1 neg yr > -5%).
Mechanism: fade global long/short account-ratio crowding on BTC (when retail
crowds long, future BTC returns are lower). It is NOT adopted:
gate (a) is fail-closed at SR >= 1.0 and the contract forbids forcing a pass.
Re-measure trigger: span grows +1y (2027-09, ~6y) or a governed bar-change
decision; the effect is real enough (scramble p < 0.05, plateau) to keep on the
watch list, not real enough to trade.

Everything else in family 1 is decisively dead or noise:
- taker flow: best 0.177 (BTC w63 mom) — noise.
- toptrader position ratio: best 0.156 — noise; fade side negative both assets.
- oi/oi_value change: all |SR| <= 0.81 with wrong-signed or unstable halves;
  OI momentum is consistently NEGATIVE on both assets (crowded-leverage fade).

## Family 2: binance_bookdepth (microstructure, 2023-01+ — SHORT-SPAN flag)

Top of family: BTC imb5_lvl (5% depth imbalance level, positive sign):

| config | net SR | H1 | H2 | negyr | scramble | corr | vol |
|---|---|---|---|---|---|---|---|
| BTC imb5_lvl (SHORT-SPAN 2.7y) | 0.811* | 1.04 | 0.58 | 1 | PASS | -0.011 | 11.2% |

*0.811 vs 0.755 in the sweep: the sweep's next_ret alignment differs at the
depth-start seam (2023-01-01, no prior price row in some joins); finalist
number is the canonical one (same pipeline as family 1).

Below the 1.0 bar even before the short-span discount. Per charter's
SHORT-SPAN honesty rule, a 2.7y "pass" would never have been champion-eligible
anyway. ETH depth variants are weaker (best 0.494); depth-change momentum
is noise (best 0.326).

## Family 3: cross-sectional BTC-vs-ETH (metrics RV, 1:1 book)

ALL SIX configs decisively negative (SR -1.19 to -1.67). The relative-value
construction (long the less-crowded, short the more-crowded) loses on both
halves. Dead — the crowding-fade edge is a BTC beta-time effect, not
cross-sectional.

## Dead-idea rows added

- `campaign/results/DEAD_IDEAS.csv` +2 rows (metrics axis, depth axis) with
  exact numbers; RV family folded into the metrics row.

## What would change the verdict (pre-registered re-measure triggers)

1. Span growth: +1y of data (2027-09) re-runs the SAME pre-registered configs.
   The near-miss at 0.945 needs +6% SR to clear; that is within the range
   where one more year can flip it either way — which is exactly why it is
   documented, not traded.
2. Governed bar change (operator decision, NOT this round's scope).
3. New pre-registered families on these axes would need a new charter
   (multiple-testing budget already spent: 70 configs).

## Charter caps held

- No sleeve CSV added (no gate pass). No champion/weights/manifest touched.
- LEDGER_AXES unchanged (33); this round MEASURED the two ITER60 inputs but
  measured-as-dead axes are not added to the ledger of live axes.
- All numbers from committed data files (no re-download).

HUNT_BINANCE_AXES DONE — honest negative, near-miss documented with triggers.
