> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
# ITER24 - DATA-AXIS CLOSURE (2026-09-19, coordinator)

## Objective (operator, verbatim - re-sent 2026-09-19 00:30, unchanged from 2026-09-18)
> "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return
> can't be smaller than 20%."

**CHAMPION OF RECORD UNCHANGED** (no adoption - honest negative):
`campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv`
sha16 `8559fa55ee9a3417` - weights `d2d11c92a98683df` (shrink 0.70 + brwt-cap 0.30) -
**ann 23.6054% / SR 3.751429 / MDD -3.6130% / 0 neg years / gross 1.0 exact** - all operator
constraints met with headroom (leverage 1.0 of 1.6; return 23.61% of 20% floor).

## What this iteration resolved
ITER23 named "a new admissible DATA axis" as the only remaining SR lever. ITER24 ran the
bounded test of the ITER23 census (405 unwired series screened; 66 IS-fittable): 28 frozen
capital-real candidate sleeves (pre-commit sealed BEFORE any computation:
campaign/agents/chief/coord/ITER24_DA/FINDINGS_PRECOMMIT.md), each added to the champion
12-sleeve pool and re-fitted by the pool's own IS max-Sharpe rule (the CFX4 lesson: the fit
is the selector). Anchors: build() reproduces the champion at 9.996e-17; incumbent IS-SR
4.198632 reproduces ITER22/23 exactly.

## Result
- **11/28 admitted on the IS window** - the ENTIRE bund curve family (8 tenors, best
  IS-SR 4.2729 vs incumbent 4.1986) plus cad 2y/3y/5y. The fit genuinely wanted EU/CAD
  rates trend on 2008-2016.
- EM-FX (0/6) and energy spots (0/10) were rejected at the IS level itself (no SR gain AND
  Wmax-inadmissible); WTI/propane earned exactly 0.000 weight. Vol complex was excluded
  pre-reveal (index levels are not a capital-real instrument; no futures data on disk).
- The single pre-committed reveal (IS-argmax bund_02y): FS SR **3.7282 < 3.7514** -
  the IS gain (+0.074) INVERTS to an OOS loss (-0.023). OOS dSR 2/5 bins positive
  (-0.026 / -0.094 / +0.021 / +0.138 / -0.053). Gate 7 (OOS police) FAIL -> REJECT.
  Per the sealed stop rule: no second reveal, iteration closed.
- This is the ITER17 law ("IS-only gains die at OOS") reproduced to the letter on a new
  data axis. The rates-trend signal that carried 2008-2016 (ECB secular easing) dies in
  the 2022 bund repricing and post-2022 chop.

## Frontier statement (objective: SR-max s.t. gross<=1.6, ann>=20%) -- data axis now CLOSED
- GEAR axis: exhausted (ITER21). WEIGHT axis: exhausted, edges explained (ITER22/23).
- POOL: all prior candidates OOS-rejected or dominated; OPT_V5..V7 = fraud family, never.
- DATA axis (ITER24): the census's IS-fittable families are now TESTED - bund/cad rates
  trend admitted by the fit but OOS-rejected; EM-FX and energy IS-dead; vol complex not
  capital-real on data in hand. NO admissible SR gain exists anywhere in the census.
- The book remains at the corner of its own constraints. What would ACTUALLY move SR:
  (a) operator-sanctioned invariant relaxation (Wmax 2.0x, worth ~+0.02 at the edge), or
  (b) NEW data the census does not contain (regional basis, VIX futures, EM local-curve
  composites) - purchase/mandate decisions, not iterations.

## Verification artifacts
- Pre-commit (sealed pre-reveal): campaign/agents/chief/coord/ITER24_DA/FINDINGS_PRECOMMIT.md
- Driver + log: .../ITER24_DA/driver_2026-09-19.py + driver_2026-09-19.log (28-row IS table)
- Findings: .../ITER24_DA/FINDINGS.md (deviations: NONE; 2 informational convention notes)
- Pins: campaign/bt/tests/test_iter24_data_axis.py - 3 tests, mutation-checked RED
  (inverted FS-SR assertion) then restored GREEN. Full suite: 499 passed.
