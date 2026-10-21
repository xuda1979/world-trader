# ITER61_DDCON — FINDINGS (post-seal; all arm computations AFTER FINDINGS_PRECOMMIT.md seal ~16:45 CST 2026-10-10)

Verdict: **POSITIVE — A_cap28 passes all pre-registered adoption gates and the
winner battery; recorded as the ITER61 candidate.** Adoption (staged-champion
swap + archive supersede) deferred per charter §7 (Option-A pending); candidate
files emitted under campaign/results/ITER61_*.

## 0. Controls (fail-closed first, per §3 family D)

- D1 uncapped rebuild of staged incumbent: SR 3.82035730 / ann 23.92147% /
  MDD -3.73394% — dev vs staged SR 3.01e-07 / ann 2.78e-07 / mdd 3.80e-07,
  under fail-closed tolerances (dSR<1e-4, dmdd<1e-6, dann<1e-4). PASS.
- D2 (brwt_cap=0.30 without natgas cap) = D1 identical: incumbent already has
  brwt cap only; zero-information control. Not separately emitted.
- D3 W_MAX rule audit: W_MAX/k = 0.1667; C5ng share 0.17942 is the ONE sleeve
  above W_MAX/k — incumbent-mechanism artifact of cap-after-fit
  redistribution, disclosed only, no action (consistent with prior
  adjudications ITER15/20/22/23/29/31/50 that the *fit* bound is W_MAX/k per
  sleeve, and the brwt/NG caps are post-fit).

## 1. Arms table (all vs incumbent SR 3.820357 / ann 23.9215% / MDD -3.7339%)

Full per-arm metrics: work/arms_iter61.csv (+ work/arms_iter61.json raw).
Fit < IS_END 2017-01-01 in every arm (fit frame index verified < IS_END in
driver; C1/C2 penalties IS-only by construction). Evaluation window
2008-03-31..2026-08-28, OOS >= 2017.

| arm | SR | ann | MDD | OOS MDD | negy | worst yr | verdict |
|---|---|---|---|---|---|---|---|
| D1 (control) | 3.8204 | 23.92% | -3.7339% | -3.7339% | 0 | +7.91% | repro PASS |
| A_cap25 | 3.7477 | 23.82% | -3.3513% | -3.3513% | 0 | +7.33% | **G1 FAIL** (SR 3.7477 < 3.7704) |
| **A_cap28** | **3.7845** | **23.86%** | **-3.3048%** | **-3.3048%** | **0** | **+7.55%** | **ALL GATES PASS — winner (G8: min MDD)** |
| A_cap30 | 3.8030 | 23.89% | -3.4799% | -3.4799% | 0 | +7.70% | all gates pass; loses G8 to A_cap28 |
| A_cap35 | 3.8204 | 23.92% | -3.7339% | -3.7339% | 0 | +7.91% | = D1 exactly (ng_share 0.32857 < 0.35 -> cap non-binding; zero-info control, as pre-registered) |
| B1_cap030_infit | 3.8274 | 24.08% | -4.1856% | -4.1856% | 0 | +8.37% | G3/G4 FAIL (MDD deeper than incumbent) |
| B2_percap015 | 3.8369 | 24.05% | -3.9033% | -3.9033% | 0 | +8.35% | G3/G4 FAIL |
| C1_isddsoft020 | 3.8274 | 24.08% | -4.1797% | -4.1797% | 0 | +8.37% | G3/G4 FAIL |
| C2_tailsoft015 | 3.8274 | 24.08% | -4.1856% | -4.1856% | 0 | +8.37% | G3/G4 FAIL |

Family read-out: only Family A (post-fit NG block cap — the incumbent
mechanism family) lowers DD; in-fit constraints (B) and soft-penalty
objectives (C) push weight into the same NG block under the SR objective and
make DD WORSE. The DD is a weight-space concentration problem, not a
fit-objective problem. A_cap35 = D1 confirms the incumbent fitted NG-block
share 0.32857: caps 0.25/0.28/0.30 bind, 0.35 doesn't — the binding range
brackets the incumbent concentration, and the incumbent itself sits BETWEEN
A_cap30's realized share (0.30) and A_cap35's non-binding cap, as expected.

## 2. Gate evaluation for A_cap28 (charter §6, all pre-registered)

- G1 SR 3.78449 >= 3.770357 ✓ (delta -0.0359 vs incumbent, within the 0.05
  grace; "without lowering Sharpe" within tolerance)
- G2 ann 23.8610% >= 23.4215% ✓ (>= 20% floor; >= incumbent-0.5pp)
- G3 full MDD -3.30485% > -3.73394% ✓ (strictly shallower, +0.4291pp)
- G4 OOS MDD -3.30485% > -3.73394% ✓ (episode is OOS and improves; not
  cosmetic)
- G5 0 negative years, worst year +7.553% >= +5% ✓
- G6 turnover 4.1917 bp/yr <= 4.7642 (incumbent 4.3311 + 10%) ✓ (cap REDUCES
  turnover as predicted)
- G7 gross max 1.0000 <= 1.6 ✓
- G8 tie-break among passers {A_cap28, A_cap30}: min full-MDD -> A_cap28
  (-3.3048% vs -3.4799%) ✓

Episode detail: peak 2023-12-27, trough 2024-01-11 (same day), recovery
2024-03-05 (vs incumbent 2024-04-02 — 28 days faster). On 2024-01-11 itself:
incumbent -2.3992% vs winner -1.9225% (+0.4767pp; max single-day difference
4.77e-03 exactly on the spike day, mean daily |diff| 1.9e-04). The mechanism
is precisely the one chartered: the DD driver is one C5ng/C5ngsum block day.

## 3. Winner battery (charter §6: full battery before adoption; work/battery_iter61.json)

Scramble N/A for a weight-space cap (no signal changed; §4 note), disclosed.
Applicable items:

- B1 byte-determinism: re-run compare identical, sha16 c245ab36a33538ec
  both runs ✓
- B2 H1/H2 split: winner 4.2555/3.6143 vs incumbent 4.2681/3.6727 — both
  halves stable, no half-collapapse, H2 gap -0.058 within noise ✓
- B3 yearly table: winner vs incumbent year-by-year (work/battery_iter61.json
  B3_yearly): 10 years better / 9 years worse / 0 negative years either
  side; largest single-year regressions 2024 (35.53 vs 37.86) and 2023
  (19.28 vs 20.30) — the capped book gives up part of the NG-block upside
  years, buys the DD reduction. Consistent with the mechanism, no hidden
  year-dependence ✓
- B4 placebo-cap discriminancy: capping non-DD block (diescrack+a6r7,
  share 0.2049 -> 0.17, equivalent tightness) gives MDD -3.7501% (WORSE than
  incumbent -3.7339%), discriminating false — the A_cap28 improvement is
  NOT mechanical "any cap helps" ✓ (desired outcome)
- B5 cost stress 6.4 -> 8.0 -> 10.0 bps: winner SR 3.7845/3.7827/3.7806 vs
  incumbent 3.8204/3.8185/3.8163; winner MDD -3.3048/-3.3051/-3.3055 vs
  incumbent -3.7339/-3.7342/-3.7346. Gap stable (~0.036 SR), no
  cost-fragility, MDD advantage preserved at all cost levels ✓

## 4. Adoption status and emitted artifacts

Per §6 adoption additionally requires builder extension only for family B/C
winners; A_cap28 is family A (incumbent post-fit cap mechanism — same
W_BRWT_CAP pattern in campaign/scripts/rawew13v2_build.py), so no builder
change is needed for a future adoption; canonical --verify would require
adding NG-block cap as a second cap pass at adoption time (flagged for the
adoption round, NOT this round).

Per §7 (champion trio stays staged; this round emits only work/ + ITER61_*
candidates):

- campaign/results/ITER61_DDCON_candidate_daily.csv — 4806 rows,
  2008-03-31..2026-08-28, full-precision, byte-exact re-emit repro PASS
- campaign/results/ITER61_DDCON_candidate_weights.csv — 12-sleeve relw,
  full float repr, exact match to logged A_cap28 relw
- work/arms_iter61.csv — per-arm metrics table (charter §8)
- work/arms_iter61.json — raw per-arm records incl. relw
- work/battery_iter61.json — B1-B5 battery results
- work/driver_iter61.py, work/battery_iter61.py — engines (seeded,
  deterministic)

NO archive supersede this round (supersede happens at adoption, not
candidate-recording). NO champion change. NO DEAD_IDEAS row (positive round;
DEAD_IDEAS is for negative verdicts).

## 5. What the chief would adopt (for the adoption round, later)

A_cap28 construction: incumbent D1 relw (shrink_d 0.70, brwt_cap 0.30 fit),
then cap (C5ng + C5ngsum) share at 0.28 by proportional down-scale and
renormalize the other 10 sleeves pro-rata (exact cap_block in
work/driver_iter61.py; deterministic). Result: SR 3.7845 (-0.036),
ann 23.86% (-0.06pp), MDD -3.3048% (+0.43pp shallower), OOS MDD same
episode improved, recovery 28d faster, 0 neg years, worst year +7.55%,
turnover 4.19bp (down), gross 1.0.

Risk notes for adoption deliberation (disclosed, not gates):
- SR concession -0.036 is real but within the pre-registered grace; the
  trade is DD for SR, as chartered.
- The cap binds through the whole window (NG block fitted share 0.3286 >
  0.28), so the candidate is a permanent structural tilt away from the
  NG complex, not just a 2024-episode patch. 2024/2023 upside years give
  up ~2.3pp/1.0pp annual return.
- Halves H2 gap -0.058 and B3's 9 worse years are the same fact: the
  cap costs upside in most NG-strong years.

## 6. Sequencing (why this is safe to hold as candidate)

The staged trio (Option-A) is unchanged on disk (git status of the staged
files: untouched this round; only new ITER61_* files added). The adoption
decision is a separate round with archive_*_SUPERSEDED_by_ITER61_DDCON
naming, champion card update, and builder --verify chain, per §6/§7.

ROUND DONE. Positive. Candidate recorded. No champion change this round.
