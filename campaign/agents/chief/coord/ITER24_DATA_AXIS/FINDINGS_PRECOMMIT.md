# ITER24 PRE-COMMIT - DATA-AXIS EXTENSION OF THE CHAMPION POOL (sealed BEFORE any sleeve reveal)

Session: 2026-09-19, coordinator. Operator objective (verbatim, 4th identical send):
"keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return
can't be smaller than 20%."

## State verified BEFORE this file was written
- Canonical gauntlet `verify_champion_r3_cmd.sh` equivalent (module call, identical args):
  **ok=True 7/7** (`verify_champion_r3_iter24_start.json`), champion
  `8559fa55ee9a3417` = n 4806, SR 3.751429, CAGR 23.6054% (arith 21.3609%),
  MDD -3.6130%, 0 neg yrs, gross 1.0 exact. weights `d2d11c92a98683df`.
- No concurrent writer (no campaign/tools .py or results mtime in the prior 2h).
- Frontier per #115/#116: gear/weights-in-grid/grid-edge all exhausted; census
  (`ITER23_GRIDEDGE_REFIT/DATA_AXIS_CENSUS_2026-09-19.txt`) pre-identified the DATA AXIS.

## Why the data axis is now admissible (geometry changed under us)
The overlay track was closed (#93) because gross was PINNED at exactly 1.6, so any
additive sleeve breached the cap (SS 8e) and any diluting blend failed dAnn>0 (SS 8c).
ITER21 de-gearred the canonical book to gross 1.0. Under the operator's cap of 1.6 the
book now has 0.6 of gross headroom, and the NAV-drift mixer normalizes gross to the gear
parameter exactly - so a 13th sleeve is expressible WITHOUT breaching gross<=1.6. The
census screened 405 unwired series on the CFX4 criterion (>500 IS rows, live >=2024);
66 are IS-fittable.

## Wave-1 candidates (chosen on DATA AVAILABILITY only - zero return data seen yet)
Recipe = FROZEN TRANSPLANT of the in-pool a6r7 construction (E1_a6r7_bond2y_trend_1990,
params DUR/K/CAD/VT/CAP = trend-lookback 378 obs, 42-obs cadence freeze, T+1, vol-target
12% ann expanding-60 clipped at 5x, applied causal shift(1)). NO parameter search: K, CAD,
VT, CAP are copied verbatim; DUR is an INSTRUMENT property (1.9 for 2y bonds as in-pool;
8.5 for 10y bonds), not a tuned parameter. Sleeve-internal cost upgraded to the
TRADE_RECORD_STANDARD 6.4bp FULL |dpos| one-side (a6r7's legacy file charges 6.0 - new
sleeves use the standard). Vol-target overlay sits outside the cost, per pool convention.

| slot      | raw series                                 | synthetic TR                           | DUR |
|-----------|--------------------------------------------|----------------------------------------|-----|
| bund2y    | tools/quant/data/bund_daily/bund_02y.csv   | -1.9*dy + y/252                        | 1.9 |
| bund10y   | tools/quant/data/bund_daily/bund_10y.csv   | -8.5*dy + y/252                        | 8.5 |
| cad2y     | tools/quant/data/dm_rates/cad_govt_2y.csv  | -1.9*dy + y/252                        | 1.9 |
| cad10y    | tools/quant/data/dm_rates/cad_govt_10y.csv | -8.5*dy + y/252                        | 8.5 |
| seliccary | em_rates brazil_selic + brazil_usdbrl      | y/252 - dFX/FX (unhedged USD carry TR) | n/a |

Rationale (from the census, not from returns): bund = the only EUROPEAN rates family
(pool has none); cad = DM-rates breadth (pool has only US 2y via a6r7); seliccary = the
only EM carry fully expressible from the batch-8 verified feed (CZK/PLN/PEN have FX but
NO local rate series -> their carry is NOT buildable; noted for the census). 2y+10y per
curve expresses breadth without re-concentrating one bet x8 (the brwt lesson). NOK policy
rate is a cash level, not a bond yield -> no TR, skipped. VIX-complex deferred to wave 2
(A5r2 already mines the term structure; do not double-mine before wave 1 resolves).

## Data-hygiene gate (CFX4 lesson) - applied BEFORE any sleeve is trusted
Fail-closed per series: stuck-value runs (>=21 identical obs), zero-variance stretches,
|daily yield move| > 1.0 (100bp) spikes flagged and eyeballed against known events, unit
check (selic recent level ~10-15%/yr), IS-window start <= 2008-03-31, last obs >= 2024.
Any artifact => candidate killed, disclosed in FINDINGS.

## Adoption protocol (pre-committed, deterministic)
Book = incumbent 12-slot pool + candidate(s); SAME frozen weight rule (fit_relw
minsharpe shrink 0.70 -> apply_brwt_cap 0.30, CFX4 pinned 0); gear 1.0; START
2008-03-31; IS_END 2017-01-01; costs 6.4bp FULL |dW|; rate 4.5%; suite of mechanics
byte-identical to campaign/scripts/rawew13v2_build.py.

Greedy forward selection in census order (bund2y, bund10y, cad2y, cad10y, seliccary):
add ONE slot, refit, gate; keep it iff ALL gates pass and FS SR beats the current
kept-pool book; then try the next candidate against the enlarged pool. Stop at first
family member that fails (do not fish substitutes within a family beyond the listed
slots). NO other grids are scanned - the weight rule itself is frozen; selecting on
FS-SR over rule variants = IS-noise mining (ITER22 law).

### Gates (ALL must hold for ADOPTION; else honest REJECT)
- G1  FS SR > 3.751429 (the incumbent, re-verified this session).
- G2  FS ann >= 20% on BOTH measures (arith and CAGR; incumbent 21.36/23.61).
- G3  gross <= 1.6 every day, both weight-implied and financing-implied (auto at gear
      1.0, verified anyway, fail-closed).
- G4  0 negative FS years, worst year > -5%, FS MDD >= -7% (champion bar).
- G5  OOS honesty (ITER17 law): full-OOS dSR (>= 2017-01-01, net, gear 1.0) > 0 vs the
      same-baseline incumbent AND >= 4/5 two-year OOS bins positive. IS-only gains die.
- G6  ANTI-DILUTION RESOLUTION (disclosed deviation from the census gate text): the
      census carried "capital-real dAnn>0" from the gross-1.6 era where the champion's
      ann was 32-38% and any blend diluted it. The operator's objective is SR-MAX with a
      20% ann FLOOR, and the operator's revealed preference (ITER21: accepted -12.81pp
      ann for +0.296 SR) makes dAnn>0 NOT an operator gate at gear 1.0. G6 = G2 (the 20%
      floor both measures) + dAnn vs incumbent REPORTED. If the operator wants dAnn>0
      re-instated, that is an operator rule change, not a coordinator decision.
- G7  refit Wmax <= 2x equal weight (the fit enforces; verified, fail-closed).
- G8  fit-window integrity: the candidate's joint-dropna shrink of the IS fit window vs
      the incumbent's joint rows must be < 2% (else the comparison is confounded; report
      the exact row delta). Window-matched incumbent baseline (incumbent 12-pool rebuilt
      on the candidate's union-date frame) computed and reported alongside the
      committed-bytes baseline, so the sleeve's effect is separated from the date-union
      effect.
- G9  causality: sleeve positions from data <= t-1 only (T+1 by construction) AND a
      truncation probe (zero all candidate raw returns from probe day t onward => the
      sleeve's position at t-1 unchanged). Costs 6.4bp full |dpos| - no half-turn, no
      uncharged signal turnover.
- G10 determinism: the driver is random-free; every number in FINDINGS re-runs from it.

### Baselines reported (never cherry-picked)
B0 = incumbent committed bytes (SR 3.751429). Bwm = window-matched incumbent rebuild.
Candidate books are compared to BOTH; G1/G5 use the STRONGER (max-SR) of B0/Bwm as the
bar, so a win cannot come from the date-union change alone.

### If ADOPTED (production path, TDD)
1. Failing pin test first (pool membership + new champion shas + gauntlet knobs).
2. Builder POOL/NEW edit (13th slot), r3_cmd sleeve map + test knobs updated together.
3. Full bt suite green from repo root; `--verify` byte-identical; then
   `--emit-candidate ITER24_*`, independent verifier 7/7, THEN champion-of-record swap
   with an adoption memo. Weights file re-emitted; sha16 recorded. Git-add remains
   approval-gated => artifacts land uncommitted; STANDUP_LOG records the D7-class debt.
### If REJECTED
FINDINGS.md honest negative with the exact gate that failed; champion untouched;
census updated (family closed like ITER18).

## Deviations from prior sessions' pre-commits
None yet. This file is sealed before any candidate return series is computed.


## AMENDMENT 1 (pre-reveal, before any sleeve return was computed)
The line "Stop at first family member that fails" is AMBIGUOUS between (a) kill the
whole remaining list on the first failure and (b) each pre-listed slot gets exactly one
try in census order. SEALED READING: (b) — each of the 5 listed slots is tried exactly
once, in census order, against the current kept pool; a failed slot is dropped and NOT
retried in any variant; no slot beyond the 5 is ever created. The guard's intent (no
fishing beyond the listed set) is preserved. Nothing else changes.
