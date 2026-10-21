# ITER61_DDCON — PRE-REGISTRATION (charter sealed BEFORE any arm computation)

Date sealed: 2026-10-10, ~16:4x CST. Author: /loop iteration-1 (chief).
Any arm result computed AFTER this file is written; if timestamps show
otherwise, this round is VOID.

## 0. Operator objective (new statement, ITER20/21-precedent class)

/loop instruction: **"lower drawdown of the champion without lowering
ann return and Sharpe"** — i.e. a DD-objective overlay on the standing
operator objective (Sharpe-max s.t. ann>=20%, gross<=1.6). Formal
adoption gate at the bottom (§6). This is a CONSTRUCTION-level round
(sleeve mix / block caps / objective form), NOT a timing round — timing
is exhausted: F2-DDC (DEAD row 71, binding policies monotonically hurt),
K1-KURTOV (row 72, kurtosis overlay all-REJECT), SYSTEM_PORTFOLIO
L1/L2/L3 (VIX-gate/rotate/timing all lose to static). Design principle
of record: "Optimize the construction, not the timing."

## 1. Incumbent (pinned, staged Option-A trio — the champion of record)

Files (STAGED state, not HEAD-committed; Option-A pending):
- campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
- campaign/results/RAWEW13v2_IS_SR_weights.csv
- campaign/CHAMPION_CARD.md
Staged-trio content hash (git diff --cached --binary | shasum):
**b1669940c2fa0f31** (verified 2026-10-10 this session; unchanged since
the AUDIT_GATE_EVOID addendum round).

Incumbent stats (computed from the staged daily, 4806 rows,
2008-03-31..2026-08-28):
- full: ann(geo) 23.9215%, SR 3.820357, MDD -3.7339% (2024-01-11),
  0 negative years, worst yr +7.906% (2013)
- IS(<2017): ann 18.4517%, SR 4.218504, MDD -2.5701%
- OOS(>=2017): ann 24.4839%, SR 3.706437, MDD -3.7339% (= full MDD; the
  MaxDD episode is OOS)
- 12 sleeves (CFX4 weight 0): C5ng .179422, C5ngsum .149146, diescrack
  .117986, brwt5 .108304, brwt10 .099772, brwt7 .091924, a6r7 .086961,
  dualmom .062348, QAxasts .055133, carryv2 .023942, A5r2 .025062.
- Engine: campaign/scripts/rawew13v2_build.py — IS-only max-Sharpe fit
  (shrink_d=0.70, brwt_cap=0.30, W_MAX=2.0/k share rule), NAV-drift
  weights row-normalized (nav.shift(1) causal), FULL |dW| @ 6.4bps,
  margin max(gear-1,0)*4.5%/yr, gear=1.0.

DD anatomy (measured this iteration, AUDIT_C5NG_DD_DAY verified):
- MaxDD -3.7339% trough 2024-01-11, peak 2023-12-27, 15d depth-window,
  97d underwater. Driver: C5ng sleeve day -21.795% (2024-01-11,
  +143% overnight HH spot spike, Winter Storm Heather; genuine, EIA-live
  + 4 in-tree copies + monthly-aggregate confirmed; sleeve spike filter
  dodged the reversion leg but the Thu short ate the up-move).
- 2nd episode -2.579% (2026-03-17, brwt-driven), 3rd -1.919% (2026-06-03).
- C5ng family (C5ng+C5ngsum) = 32.86% of relw; natgas block is the DD
  concentration.
- C5ngsum is Nov-Mar FLAT (summer variant), so in Jan-2024 only C5ng
  was exposed; the block's winter exposure is C5ng-only.

## 2. Hypothesis (pre-registered before any arm run)

H1: The champion's DD is a WEIGHT-CONCENTRATION artifact: IS-only
max-Sharpe fit does not price the OOS tail of natgas weekday premium
(the 2024-01-11 spike is invisible in IS where MDD is only -2.57%).
A construction-level concentration limit (block cap, in the exact
W_BRWT_CAP=0.30 precedent family) or a DD-aware objective will lower
full/OOS MDD while holding ann and SR approximately (within the
adoption gates below), because the DD driver is one sleeve whose IS
risk was understated, and redistribution to the other 10 live sleeves
buys diversification the Sharpe-fit ignored.

H0 (null): any concentration relief costs more ann/SR than the gates
allow (the C5ng weight IS the Sharpe-optimal price of natgas premium;
cutting it cuts more mean than tail).

Prior expectation (honest, from the dead ledger): F2/K1-class history
says REJECT is likely. The C5ng family earned its weight in OOS too
(OOS SR 3.71 with the spike included). But those priors are TIMING
priors; the block-cap cell is genuinely untested (only brwt has a cap;
natgas never did; the champion has no per-family cap besides brwt).

## 3. ARMS (all pre-registered; grid frozen now)

Common engine: rawew13v2_build.build() math re-implemented locally in
work/ (do NOT touch the canonical builder; read-only import of PATHS/
NAMES/params), IS fit window <2017-01-01, evaluation 2008-03-31..
2026-08-28 staged-vintage sleeves, FULL |dW|@6.4bps, margin rule same,
gear=1.0. Block-cap arms follow the apply_brwt_cap pattern exactly:
cap the block's relw share, redistribute excess pro-rata to non-block
sleeves, then the standard build (NAV-drift, costs). NO re-fit of the
objective inside the cap arms (cap-after-fit, the incumbent's own
mechanism; a re-fit-with-constraint variant is arm-family B).

Family A — natgas block cap (C5ng+C5ngsum share cap, after-fit
redistribution; W_BRWT_CAP precedent):
- A1: cap 0.25
- A2: cap 0.28
- A3: cap 0.30 (mirrors brwt cap level)
- A4: cap 0.35 (loose; likely non-binding sanity point — C5ng+C5ngsum
  staged share = 0.328568, so 0.35 should reproduce the incumbent
  exactly; if it does NOT, the engine repro is broken and the round
  STOPS until fixed)

Family B — constraint-in-fit (natgas cap INSIDE the SLSQP fit, weights
re-optimized under the constraint; not the incumbent mechanism, so a
separate family):
- B1: fit s.t. (w_C5ng + w_C5ngsum) <= 0.30
- B2: fit s.t. w_C5ng <= 0.15 AND w_C5ngsum <= 0.15 (per-sleeve form)

Family C — DD-aware objective (fit objective change; IS window only,
no OOS info):
- C1: max Sharpe s.t. IS realized MDD >= -2.0% (fit on IS daily net
  path of the weighted book; SLSQP with epigraph DD constraint is not
  smooth — use the standard proxy: penalize min(0, dd_t + 0.02)^2 sum
  as a soft constraint via augmented objective with weight lambda=10;
  disclosed as proxy, hard-constraint variants are NOT run this round)
- C2: tail-penalized Sharpe: minimize -SR + lambda * (sum of IS daily
  book losses worse than -1.5%)^2, lambda=10 (worst-day penalty proxy)

Family D — control arms (must reproduce known quantities; engine
validations, not candidates):
- D1: uncapped rebuild of the staged incumbent (shrink 0.70, brwt_cap
  0.30, 12 sleeves) — MUST match staged daily sha16-relevant stats
  (SR 3.820357, ann 23.9215%, MDD -3.7339%) to |dSR|<1e-6 tolerance
  before any other arm is trusted; if it fails, STOP and fix repro.
- D2: brwt_cap=0.30 arm WITHOUT natgas cap — identical to D1 (cap
  already in incumbent); zero-information control.
- D3: W_MAX binding test — the incumbent's fit rule caps any share at
  W_MAX/k = 2.0/12 = 0.16667 (staged C5ng 0.179422 EXCEEDS this after
  cap-redistribution mechanics? VERIFY: if C5ng's staged share violates
  the documented W_MAX rule, document the exact mechanism — cap-after-
  fit redistribution is applied AFTER the fit, so redistributed weights
  may exceed W_MAX/k; this is the incumbent's own behavior, disclosed
  only, no change).

Total candidate arms: A1-A4, B1-B2, C1-C2 = 8; controls D1-D3.

## 4. Metrics (per arm, all computed the same way)

full ann(geo), full SR, full MDD + episode dates, IS SR, IS ann, IS
MDD, OOS SR, OOS ann, OOS MDD, negative years, worst year, worst day,
turnover bp/yr, gross max, natgas-block share, C5ng share, delta vs
incumbent on each. Scramble tests NOT required for cap arms (they are
weight-space perturbations of an already-scramble-tested book; the
sleeves are unchanged), but the WINNING arm (if any) gets the full
GATES_CONTRACT battery before adoption.

## 5. Fit/gate discipline (GATES_CONTRACT, IS/OOS split)

- Fit window: <2017-01-01 (IS). The 2024-01-11 driver day is OOS and
  MUST NOT inform any fit (no OOS DD in the objective; C1/C2 penalties
  are IS-only by construction — verify the fit frame index < IS_END in
  the driver log).
- Evaluation: full window 2008-03-31..2026-08-28 + OOS split >=2017.
- Fail-closed: any engine divergence from D1 stops the round.

## 6. ADOPTION GATES (pre-registered; all must pass; incumbent-beats rule)

An arm is ADOPTABLE only if ALL:
- G1: full SR >= incumbent 3.820357 - 0.05 (i.e. >= 3.770357; ~1.3%
  tolerance — "without lowering Sharpe" with small numeric grace)
- G2: full ann(geo) >= 20.0% (operator floor, unchanged) AND >=
  incumbent 23.9215% - 0.5pp (>= 23.4215%; "without lowering ann")
- G3: full MDD strictly better: > -3.7339% (strictly shallower)
- G4: OOS MDD strictly better: > -3.7339% (the DD episode is OOS; a
  full-window improvement that leaves OOS DD unchanged is cosmetic)
- G5: 0 negative years (unchanged champion property), worst year >= +5%
- G6: turnover <= 6.4bp/|ds|-equivalent: turnover bp/yr <= incumbent's
  +10% (weight-space caps should REDUCE turnover; a rise >10% fails)
- G7: gross <= 1.6 exact rule (trivially 1.0 here; state it anyway)
- G8 (tie-break): if multiple arms pass, choose min full-MDD; tie ->
  max SR.
- If NO arm passes: honest negative, DEAD_IDEAS row, no champion change.
- Adoption additionally requires: byte-exact re-emit repro, full
  GATES_CONTRACT battery on the winner, archive superseded vintage
  (archive_*_SUPERSEDED_by_ITER61_DDCON.csv), STANDUP_LOG round record,
  explicit-pathspec commit. If the winner comes from family B or C
  (non-incumbent mechanism), the canonical builder must be extended
  with the mechanism BEFORE adoption and its --verify must reproduce
  the champion; otherwise the arm is recorded as a candidate only
  (adoption deferred to a follow-up round).

## 7. Scope / non-goals

- NO timing policies (dead ledger: F2-DDC, K1-KURTOV, SP L1/L2/L3).
- NO new sleeves, NO re-fit of shrink_d / W_MAX / gear / brwt_cap grids
  (those are charted cells with prior adjudications: ITER15/20/22/23/
  29/31/50).
- NO data changes; sleeves read-only at the staged vintage.
- Champion trio stays STAGED (Option-A pending); this round emits only
  work/ artifacts + (if a winner emerges) candidate files under
  campaign/results/ITER61_* names. NO git stash (b79d7b87 +
  82fa7401 lesson). Explicit-pathspec commits only.

## 8. Records

- work/driver_iter61.py — the engine + arms, single file, seeded,
  deterministic, logs every arm's metrics table.
- work/arms_iter61.csv — per-arm metrics.
- FINDINGS.md — verdict per gates §6.
- If negative: DEAD_IDEAS.csv append (one row), STANDUP_LOG round
  record, commit.

SEALED. Time of last edit: 2026-10-10 ~16:45 CST. No arm in §3 has been
computed at seal time (D1 repro is the first run; its result goes in
FINDINGS.md).
