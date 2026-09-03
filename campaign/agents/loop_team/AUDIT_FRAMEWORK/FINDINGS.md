# AUDIT_FRAMEWORK FINDINGS — iter7 (2026-09-03)

Scope: `campaign/bt/{engine,metrics,gates,reconcile,backtest}.py` + tests/. READ-ONLY on bt/
(regression tests + README note written in this dir / appended to bt/README.md as chartered).
Method: superpowers rigor — 32 probe scripts executed, then TDD: 19 adversarial tests written in
`tests_audit_bt.py` (class TestAuditRED = 10 bug regressions, class TestAuditRED all RED i.e. FAILING
against current code; class TestAuditGREEN = 9 verified-correct behavior locks, all pass).
Baselines: existing suite `python3 -m pytest bt/tests/ -q` => **23 passed in 0.22s** (pandas 3.0.3,
numpy 2.4.6, python 3.14).

---

## Per-charter-item verdicts

### 1. vol_target_scale — VERDICT: PASS on lookahead, FAIL on 2 contract defects
- No-lookahead CONFIRMED by perturbation test (G1): perturb r[100] (×10); scale row 100 identical
  (max|Δ|=0.0, atol 1e-12); row 101 changes — `.shift(1)` after expanding std is semantically right.
- Bounds CONFIRMED (G2): over 300×3 random panel scale.min()>=0.2, scale.max()<=3.0.
- Constant-vol CONFIRMED (G2): series ±0.01 alternating, steady-state scale = 0.10/vol exactly:
  expected 0.6278651952650581, got 0.6278651952650581 (rel 0).
- **BUG A3 (doc/contract)**: docstring says "Returns NaN-free frame aligned to `returns`" but row0 is
  ALL-NaN (shift(1) has nothing to shift in). Probe: single-row input -> [[nan]]; 300-row panel -> 3
  NaN cells (1 per col). Downstream `fillna(1.0)` in backtest.py masks it and causes BUG A2.
- **BUG A4 (dead parameter)**: `window=60` is documented ("First `window` rows: expanding window")
  but NEVER used in the body — verified max|s(window=10) − s(window=200)| = **0.0** over the whole
  panel on non-NaN rows. Expanding-from-row-1 always. Misleading API; first-60d vol estimate is
  noisier than a caller specifying window=60 would expect.
- Initial-window vol from 1 observation: std(ddof=1) of 1 row = NaN -> scale NaN -> `where(vols>0,1.0)`
  sets 1.0 (only when vols==0 exactly, NOT when NaN — but NaN propagates via `target/vols` -> NaN ->
  shift keeps NaN). Trace verified: row0 scale NaN for every column.

### 2. cap_leverage — VERDICT: PASS on convention, 1 float-bound defect
- Day-level gross cap CONFIRMED (G4): [2.0] -> 1.6 same day (kappa_t uses gross_t, NOT shifted —
  this is the intended and documented convention: cap is applied to the position you actually hold
  on day t; costs of the cap adjustment are then charged via cost_turnover on the capped diff).
- Identity below bound CONFIRMED: [0.8, 0.5] unchanged exactly.
- **BUG A9 (floating-point overshoot)**: deterministic input [0.643858, −0.710084, 0.60464,
  −0.353216, −0.35968, 0.108407] (gross 2.780) -> kappa = 1.6/2.780...; capped gross = 1.6 +
  **2.220446049250313e-16** > max_lev. Found by 200k-trial random search (worst overshoot
  8.88e-16). No epsilon guard (e.g. `np.minimum(kappa, 1.0)` then re-clip, or gross>max_lev*(1+1e-12)
  assert). Severity: cosmetic for PnL, breaks any STRICT `gross <= max_lev` assertion downstream
  (the charter's own "exact day-level gross cap <= max_lev incl. floating-point overshoot guard").

### 3. cost_turnover — VERDICT: **FAIL — BLOCKING convention mismatch (BUG A1)**
- Code: `one_side = diff().abs().sum(axis=1) * 0.5`; charge = one_side × bps/1e4 => **0.5·|dw|·6.4bps
  = 3.2e-4 per unit |dw|** (test A1 RED: w 0->1 charges 3.2e-4, expected 6.4e-4).
- Committed champion (`campaign/scripts/honest13_build.py` build(), line 94/99, verified by reading
  the frozen source): `reb = full.diff().abs().sum(axis=1)` (NO 0.5 — i.e. Σ|dw| treated as ONE-SIDE
  traded notional) then `r_out = b − (tw + dsc)·6e-4 − reb·6e-4`. So champion reb stream = **|dw|·6.0bps**.
  (tw = (W−W.shift).abs()·0.5 same convention; dsc = throttle 0.5·|Δsc| same.)
- TRADE_RECORD_STANDARD: `qty_notional = |position change|` (ONE-SIDE) and "6.4 bps/side on ALL
  turnover" => cost = |dw| × 6.4e-4. BLOTTER v2: cost_total on trade rows = 6.0bps × qty (as charged).
- Conclusion: framework = HALF the champion/standard rate at the bps level, and 6.4 vs 6.0 label
  mismatch on top (known Tester #5 gap, 11.91bps/yr). **bt.engine.cost_turnover is NOT compatible
  with the committed champion convention; any hunt using bt defaults undercharges ~41.7% of the
  champion cost rate.** Also `borrow_cost`: code charges 1.0× short notional (matches champion's
  capW·sf·0.005 convention) but its DOCSTRING says 0.5·Σ|w_short| (BUG A10, doc wrong, code right:
  −0.5 short leg, frac 0.005 => 9.920635e-06 charged vs 4.960317e-06 docstring-implied).
- margin_cost: CONFIRMED (G3) on (gross−1)+ only; gross 0.5/1.0 -> exactly 0; 1.6 -> 0.6·0.045/252;
  2.0 -> 1.0·0.045/252. Minor: `max_lev` parameter is DEAD (never referenced in body).

### 4. margin_cost — VERDICT: PASS (see above; exact numbers in G3)

### 5. metrics — VERDICT: PASS on known inputs, 1 ruin bug
- ann_geo: 252×0.001 => 1.001^252−1 (rel 1e-9) PASS; ann_arith 0.252 exact PASS (G5).
- max_dd [0.10,−0.20] => −0.20 exact PASS; NaN row dropped silently (probe: [0.01,NaN,−0.01]→−0.01).
- sharpe guards: all-zero-vol [0.001]×50 => 0.0; alternating [1,−1] => 0.0 PASS (G5).
- neg_years: 1 neg year of 3 => (1, min) PASS; empty => (0, nan).
- **BUG A5 (ruin false-positive)**: r=[0.01, −2.0, 0.01] => (1+r).prod() = −0.0198… (negative) raised
  to fractional power => **ann_geo = +432.0969817873112%**. No guard for (1+r).prod()<=0. A single
  synthetic −200% day INCREASES reported ann to +432%. Fail-closed guard required (return nan/−1).

### 6. gates — VERDICT: PASS with 2 documented defects
- scramble_positions: matches an independent hand-rolled reference EXACTLY (G7): p=0.56 both,
  real_sr identical, same rng consumption order (seed 0, n=50, block=10, T=200). Position-roll (not
  return-roll) confirmed; lag drawn from [block, T−block] inclusive.
- `gates.run` FAIL-CLOSED on NaN ac1 CONFIRMED (G6): constant series -> ac1=NaN -> ac1_ok False ->
  pass=False. No-overlap ref -> corr=NaN -> corr_ok False -> pass=False (probe: pass=False).
- uniq_ratio: constant 50-series => 0.02 (< 0.08 flagged); empty => 0.0 (G6).
- **BUG (G8, minor)**: `zero_runs_long` slices `r.iloc[1:-1]` — a LEADING 25-zero run reports 24
  (first zero dropped), a TRAILING 25-run reports 24 (last zero dropped); interior 25-run = 25 exact.
  Off-by-one at boundaries; also documented as designed-interior-only in test G8.
- `position_lag_scramble` is a `raise NotImplementedError` stub (README/gates docstring disagree —
  `scramble_positions` is the real implementation; dead stub should be deleted).

### 7. __init__/public API + pandas 3.0 — VERDICT: FAIL (API gaps)
- `campaign/bt/__init__.py` is EMPTY (0 exports): `from bt import engine` works, `from bt import *`
  yields nothing; no `__all__`, no version. README documents `bt/backtest.py` — at session start
  (15:01) `find` did NOT list it; at 15:02 the file EXISTED (concurrent write by another agent —
  uncommitted work appeared mid-audit; git shows bt/ committed a4f38d8 without backtest.py).
- `backtest.sleeve()`/`book()` **BUG A2 (entry trade never charged)**: weights row0 = NaN (shift) →
  `cost_turnover` diff row1 = NaN → the 0→w ENTRY trade costs 0. Verified: book() with constant w=0.8,
  zero returns => first net = **0.0** (honest: −0.5·0.8·6.4e-4 = −2.56e-4). sleeve() identical
  (row1 cost 0.0 vs manual-with-entry 3.2e-4-class charge; framework total cost 0.0159126 vs manual
  with entry higher). Exit trades ARE charged (final diff nonzero), only entry from NaN-row is free —
  a systematic small cost undercharge on every sleeve/book built with bt.backtest.
- `backtest.book()` API ambiguity: it lags the caller's weights internally (`.shift(1)`); callers
  passing already-lagged positions double-lag silently. Docstring warns only vaguely.
- pandas-3.0 gotchas probed: `sharpe_m` requires DatetimeIndex (raises TypeError on RangeIndex —
  fail-loud, acceptable); `'ME'` resample ok on pandas 3.0.3; `pd.Series.resample('ME')` fine.
- PyPI `bt` package NOT installed in this env (import bt resolves to campaign/bt/__init__.py) — no
  shadowing risk here, but the generic name is a collision hazard for pip installs.

### reconcile — VERDICT: FAIL (3 fail-open gates) — worst honesty risk in the framework
- **BUG A6**: `turnover_reconciles`: ledger qty 5.0 vs pos_path turnover 0.0 -> rel = NaN (0/0) ->
  `.fillna(0)` -> max_rel 0.0 -> **ok=True**. RED test proves fail-open. A ledger with fabricated
  quantity and an all-flat pos_path PASSES the reconciliation gate.
- **BUG A7**: `ledgers_reproduce`: join='inner' + dropna => a ledger covering 1 of 2 champion days
  passes with max_diff 0.0, n=1. No coverage check (`n == len(champion)`). RED test proves it.
- **BUG A8**: `repro_ok`/`max_abs_diff`: mismatch hidden in a NaN row (a=[.01,NaN,.02] vs
  b=[.01,.99,.02]) => dropna removes it => ok=True. RED test proves it.
- These matter: TRADE_RECORD_STANDARD gate 1&2 are the campaign's core honesty gates; the framework
  implementations are the ones future hunts will call. They currently fail OPEN.

---

## BUG TABLE (all 10 regression-tested; each RED observed against current code)
| # | module | severity | one-line | RED evidence |
|---|--------|----------|----------|--------------|
| A1 | engine.cost_turnover | **BLOCKING** | charges 0.5·|dw|·6.4bps = 3.2bps/unit; champion/standard = |dw|·6.0/6.4bps one-side | A1 RED: got 3.2e-4, expected 6.4e-4 |
| A2 | backtest.sleeve/book | HIGH | entry trade (0→w) never charged (NaN row0 → NaN diff) | A2 RED: first net 0.0 vs −3.2e-4; book probe −0 vs −2.56e-4 |
| A3 | engine.vol_target_scale | MED | row0 all-NaN despite "NaN-free" docstring | A3 RED: 3 NaN cells on 300×3 |
| A4 | engine.vol_target_scale | MED | `window` param dead (max|Δ|=0.0 window 10 vs 200) | A4 RED after dropna |
| A5 | metrics.ann_geo | MED | ruin day → false +432.10% ann (negative prod fractional power) | A5 RED: +4.32097 |
| A6 | reconcile.turnover_reconciles | HIGH | fails OPEN when pos turnover is 0 (NaN rel → 0) | A6 RED: ok=True |
| A7 | reconcile.ledgers_reproduce | HIGH | passes with partial date coverage (inner join, no n check) | A7 RED: ok=True n=1 of 2 |
| A8 | reconcile.repro_ok | MED | NaN-row mismatches silently dropped | A8 RED: ok=True |
| A9 | engine.cap_leverage | LOW | strict bound overshoot 2.2204e-16 (no eps guard) | A9 RED: 1.6+2.22e-16 |
| A10 | engine.borrow_cost | LOW | docstring says 0.5×, code charges 1.0× short notional | A10 RED: 9.92e-6 vs 4.96e-6 |

Plus documented non-RED defects: `gates.zero_runs_long` boundary off-by-one (locked in G8);
`gates.position_lag_scramble` NotImplementedError stub; `engine.monthly()` dead stub returning empty
Series; `margin_cost(max_lev)` dead param; `metrics.sharpe_m` TypeError on non-DatetimeIndex (OK,
fail-loud); empty `bt/__init__.py` (no public API); `backtest.book()` silent double-lag ambiguity;
bt/README.md documented `bt/backtest.py` that did not exist at session start (appeared 15:02, uncommitted).

## What's tested GOOD (GREEN locks, all pass — 9/9)
No-lookahead vol-target (perturbation + t+1 changes), bounds 0.2/3.0, constant-vol scale=0.10/vol
exact to 0.6278651952650581, margin on (gross−1)+ only with exact values, cap same-day kappa +
identity below bound, ann_geo/arith/max_dd/neg_years known values, sharpe zero-vol guards,
scramble_positions == hand-rolled reference (p=0.56=0.56), gate fail-closed on NaN ac1/corr,
uniq_ratio, interior zero-runs, lag_signal T+1, repro_ok happy path.

## ROOT-CAUSE notes (systematic-debugging)
- A2 root cause chain: lag/shift → NaN row0 → cost_turnover uses `.diff()` which yields NaN on the
  first non-NaN row → NaN costs sum as 0 (pandas sum skipna) → entry trade free. NOT a diff-bounds
  bug; it's missing explicit `fillna(0.0)` on weights BEFORE diff (or explicit entry-cost stream).
- Probe-18 initial confusion (cost totals both 0.0): root cause was my own harness — cap_leverage
  row0 NaN propagated into `wc['w'].diff()` making ALL early diffs NaN; re-derived step-by-step
  (w head [nan, 1.0, −1.705…], cost head [0,0,8.32e-4,…]) before asserting the bug. Auditor-harness
  bug fixed before claiming (2 of my initial tests were wrong: G5 float-equality, G8 boundary
  assumption; A4 false-negative from allclose+NaN trivially False — all three corrected).
- A5 root cause: `(1+r).prod()` negative → fractional power → complex branch → real positive result.
  Classic; needs explicit `(1+r).prod()<=0 → nan` guard.
- A6/A7/A8 root cause family: pandas inner-join/dropna/fillna ergonomics silently shrink or nullify
  comparisons; reconciliation gates MUST assert COVERAGE (n days == expected, no dropped rows) and
  treat NaN as failure, not as pass-through.

## RECOMMENDATIONS before bt is the single trusted engine (blocking order)
1. FIX A1: make cost_turnover one-side (drop the 0.5) and default cost_bps aligned to the champion
   reb stream; document 6.0 (charged) vs 6.4 (standard label) and the 11.91bps/yr gap from Tester #5.
   Re-run champion reconciliation through bt after the fix (byte-level, <1e-12).
2. FIX A2: explicit entry costing in backtest.sleeve/book (weights fillna(0) before diff, or explicit
   entry stream). Add exit-cost test too.
3. FIX A6/A7/A8: reconciliation gates fail-closed — require exact coverage n, no NaN anywhere,
   zero-turnover mismatch = FAIL. (TRADE_RECORD_STANDARD gates 1–2 must be unspoofable.)
4. FIX A5 (ann_geo ruin guard), A3 (drop the NaN row or fillna(1.0) explicitly + fix docstring),
   A4 (implement rolling-window warmup or remove the param), A9 (eps guard), A10 (docstring).
5. Delete dead stubs (`monthly`, `position_lag_scramble` stub, `margin_cost.max_lev`), export an
   explicit `__all__` in `__init__.py`, pin the book() lag convention in the signature.
6. Process: `backtest.py` materialized mid-audit uncommitted — freeze bt/ with a single owner; any
   new bt file must land WITH its TDD tests in the same commit (existing 23 tests + 19 audit tests
   = the floor). Do NOT let hunts adopt bt until A1/A2/A6–A8 are GREEN.

## Verification commands (fresh, this session)
- `python3 -m pytest bt/tests/ -q` → 23 passed in 0.22s
- `python3 -m pytest agents/loop_team/AUDIT_FRAMEWORK/tests_audit_bt.py -v` → 10 failed (RED, = bugs)
  + 9 passed (GREEN locks); every RED quoted above with exact numbers
- Champion cost convention read from frozen `campaign/scripts/honest13_build.py` (lines 79–99) and
  `campaign/TRADE_RECORD_STANDARD.md` (both quoted above)

## POST-SCRIPT (fresh verification, same session): concurrent bt/ writes detected and re-checked
- Final combined run `pytest bt/tests/ agents/.../tests_audit_bt.py -q` → **10 failed, 35 passed**.
  Expected 32 passed (23+19−10); root-caused the +3: a NEW file `bt/tests/test_backtest.py`
  (mtime 15:03) and `bt/backtest.py` (mtime 15:02) appeared DURING this audit (uncommitted;
  another agent writing to bt/ concurrently — confirmed via mtime + `git status` showing bt/
  unchanged in my session). bt/tests baseline moved 23 → **26 passed in 0.22s**. My 3 new tests
  are happy-path only (finite/length asserts) and do NOT cover A2 (entry-cost) — none of my 10
  RED regressions flipped; re-verified in the same combined run (10 RED intact).
- This concurrent-write episode is itself an audit finding (see recommendation 6: freeze bt/,
  single owner, tests land in same commit). Bug list above remains exact as of 2026-09-03 15:0x
  snapshot: A1–A10 all RED, 9 GREEN locks all pass.
