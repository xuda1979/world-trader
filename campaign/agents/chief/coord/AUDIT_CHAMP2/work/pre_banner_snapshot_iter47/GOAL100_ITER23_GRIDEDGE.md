> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
# ITER23 — GRID-EDGE CLOSURE (2026-09-19, coordinator)

## Objective (operator, verbatim — re-sent 2026-09-19 00:30, unchanged from 2026-09-18)
> "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return
> can't be smaller than 20%."

**CHAMPION OF RECORD UNCHANGED** (no adoption — honest negative):
`campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv`
sha16 `8559fa55ee9a3417` · weights `d2d11c92a98683df` (shrink 0.70 + brwt-cap 0.30) ·
**ann 23.6054% / SR 3.751429 / MDD −3.6130% / 0 neg years / gross 1.0 exact** — all operator
constraints met: leverage 1.0 ≤ 1.6 (37.5% headroom), return 23.61% ≥ 20% (18% headroom).

## What this iteration resolved
ITER22 closed the weight axis *inside* the pre-committed grid but left both grid EDGES
unresolved — and an argmax sitting on a grid edge is the classic truncation signal. ITER23
(pre-committed protocol in campaign/agents/chief/coord/ITER23_GRIDEDGE_REFIT/
FINDINGS_PRECOMMIT.md, sealed before the reveal) extended the family past both edges:

| point | shrink | cap | Wmax | IS-SR | FS-SR | admissible |
|---|---|---|---|---|---|---|
| cap edge | 0.70 | 0.29 | **2.0044x** | 4.2076 | 3.7594 | NO |
| cap edge | 0.70 | 0.28 | 2.0326x | 4.2146 | 3.7662 | NO |
| cap edge | 0.70 | 0.27 | 2.0609x | 4.2195 | 3.7715 | NO |
| cap edge | 0.70 | 0.26 | 2.0891x | 4.2220 | 3.7751 | NO |
| shrink edge | 0.60 | 0.30 | **2.0108x** | 4.2077 | 3.7525 | NO |
| shrink edge | 0.50 | 0.30 | 2.0466x | 4.2158 | 3.7523 | NO |
| shrink edge | 0.40 | 0.30 | 2.0860x | 4.2234 | 3.7505 | NO |
| **INCUMBENT** | 0.70 | 0.30 | 1.9762x | 4.1986 | 3.751429 | **YES** |

(All points: IS-MDD ≥ −6% PASS, 0 IS neg years PASS, CFX4 = 0 exactly, gross 1.0 exact —
Wmax 2.0x-equal is the ONLY binding filter. Anchor before reveal: build() vs champion bytes
9.996e-17 IDENTICAL; incumbent reproduces ITER22's IS-SR 4.1986 exactly.)

## Findings
1. **The grid edges were TRUE concentration boundaries, not truncation artifacts.** The
   Wmax 2.0x-equal invariant is crossed between cap 0.29/0.30 and between shrink 0.70/0.60 —
   the incumbent is the LAST admissible point on BOTH axes. The family has no admissible
   extension in any direction.
2. **The forbidden corner is genuinely tempting** — IS-SR rises to 4.2234 and FS-SR to
   3.7751 (> incumbent 3.751429) beyond the wall — but every such point concentrates the
   book past 2x equal weight. Taking it would be a rule change (relaxing the concentration
   invariant), not an improvement; it would also buy at most +0.024 FS-SR at the very edge.
   NOT DONE without operator sanction.
3. Reproduces ITER22's tight-cap law on freshly computed points (FS rank inverts IS rank at
   the tight-cap end — selecting on FS there is IS-noise mining).

## Frontier statement (objective: SR-max s.t. gross ≤ 1.6, ann ≥ 20%) — CLOSED at family
## resolution, edges now explained
- GEAR axis: exhausted (ITER21 cost-structure identity; SR flat ≤1.0, strictly falling above).
- WEIGHT axis: exhausted AND edge-resolved (ITER22 grid argmax + ITER23 edges = the Wmax wall).
- POOL: all candidates OOS-rejected or dominated (pinned by tests); OPT_V5..V7 = fraud family,
  never champion.
- The book sits at the corner of its own constraints. Only a new admissible DATA axis or an
  operator-sanctioned invariant relaxation moves SR from here.

## Verification artifacts
- Pre-commit (sealed pre-reveal): campaign/agents/chief/coord/ITER23_GRIDEDGE_REFIT/FINDINGS_PRECOMMIT.md
- Reveal log: campaign/agents/chief/coord/ITER23_GRIDEDGE_REFIT/driver_2026-09-19.log
- Findings: campaign/agents/chief/coord/ITER23_GRIDEDGE_REFIT/FINDINGS.md (deviations: NONE)
- Pins: campaign/bt/tests/test_iter23_gridedge_closure.py — 7 tests (mutation-checked RED,
  reverted, GREEN). Full suite: 489 + 7 = 496 expected green.
