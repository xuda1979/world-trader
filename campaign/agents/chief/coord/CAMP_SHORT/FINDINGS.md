# FINDINGS — CAMP_SHORT

## ROUND 1 (summary of record)
`bt/shortability.py` (gate + pregate + tier_delta_cost + mcap_tier + 2 ladders),
`bt/tests/test_shortability.py` (10 tests), research frac measurement
(`work_r2/measure_short_fracs.py`). Champion has NO single-name L/S slot at 0.5% flat
borrow — hence round 2's tiered re-run. Details in CHARTER R1 deliverables.

---

# ROUND 2 — 2026-09-07

## R2(a) — INTEGRATION SNIPPET (charter item a) — PASS, tests pinned, WORKS ON REAL DATA

Any round-2 hunt candidate that shorts SINGLE NAMES must run this BEFORE gates.
Contract pinned by `bt/tests/test_shortability_r2.py` (7 tests). Verified end-to-end on
the real diescrack stream (338 short days): HARD tier prices 0.5796%/yr borrow
(= 8% tier x 6.9% mean short frac — arithmetic confirmed), NONE tier drops the leg.

```python
# ---- paste into hunt sleeve template, AFTER T+1 weights, BEFORE costs & gates ----
from bt.shortability import shortability_pregate, mcap_tier

# 1) tier per name: measured mcap rank frac (0=smallest), or a borrowed-cost lookup.
#    Fail-closed: any name whose tier you cannot justify must be "NONE", not defaulted.
tier = {n: mcap_tier(frac_n) for n, frac_n in mcap_rank_fracs.items()}   # 1-liner mapping
tier["TICKER_I_CANNOT_VERIFY"] = "NONE"        # unknown -> unshortable (fail-closed)

# 2) pre-gate BEFORE costs/gates. Drops NONE-tier shorts (never silently costed),
#    re-levers surviving legs to preserve book gross, prices borrow same-day
#    (no lookahead — the fee applies to the live weight that day).
W_gated, borrow_cost, info = shortability_pregate(W, tier)   # W = T+1 weights DataFrame

# 3) add the borrow line into the sleeve's net return stream alongside normal costs:
net = gross_ret - turn*6.4/1e4 - borrow_cost                  # borrow_cost is /yr/252 already

# 4) record it: info["dropped"], info["borrow_ann_frac"] go into the sleeve JSON header.
# ----------------------------------------------------------------------------------
```

Pipeline order (ops): `signal -> T+1 weights -> shortability_pregate -> costs -> gates`.
Edge cases tested: surviving short re-levered up on drop (gross preserved exactly,
1e-12); unknown tier string raises (never silently EASY); negative/NaN short notional
raises in `tier_delta_cost`; a cheaper tier produces a NEGATIVE delta (a credit, never
clipped to zero).

## R2(b) — CHAMPION UNDER TIERED BORROW — PASS: champion is ~insensitive, as predicted

Artifact: `campaign/results/CAMP_SHORT_SHORTABILITY_R2.json` (ops runbook scenario, item c).
Method: every number MEASURED, none assumed —
- champion weight stream Wg rebuilt with canonical builder arithmetic from the 13 sleeve
  CSVs, pinned GIT-HEAD byte-exact vs committed champion: max|diff| = 1.0e-16 (test-pinned
  `< 1e-12`);
- per-slot short-notional streams reconstructed from frozen generators and re-netted
  against committed sleeve CSVs (tol 2e-4); per-slot artifacts `work_r2/short_frac_*.csv`;
- census: 13 slots -> 10 FUTURES_SPOT_ETF (no stock-loan fee exists), 2
  LONG_ONLY_CONSTRUCTION (dualmom, A5r2 — no short leg by construction),
  2 STOCKLOAN_0.5% (diescrack, CFX4). **CFX4 carries zero champion weight** (starts
  2019-09, after the 2017 IS cut -> IS-SR 0 -> relw 0), test-pinned; so the champion's
  entire real stock-loan exposure is diescrack at mean notional 0.19% of NAV.

Base (committed champion, honest T+1): ann 39.85%, SR_d 3.296, SR_m 2.325, MDD -6.84%,
neg years 0/19, worst year +8.61%.

Delta ann vs base (pure borrow effect — rungs diffed against the REBUILT base, which is
byte-exact to committed):

| ladder | treatment | T1 | T2 |
|---|---|---|---|
| 0.5/1/3% | REALISTIC (stock-loan slots only) | +0.00pp (drag 0.0010%/yr) | **-0.01pp** (drag 0.0048%/yr) |
| 0.5/1/3% | BOUND (every short = cash borrow) | -0.26pp | -0.79pp |
| 0.5/2/8% | REALISTIC | +0.00pp (drag 0.0029%/yr) | **-0.02pp** (drag 0.0143%/yr) |
| 0.5/2/8% | BOUND | -0.53pp | **-2.11pp** (drag 1.523%/yr) |

Gates never move: **neg_years 0/19 and MDD > -7% at every rung of both ladders, both
treatments** (`gate_moves: NO` in the JSON). Worst-year stays >= +6.64%.

Answer to the charter's R1 flag (MHX-style 75bps/yr tier risk): even the deliberate
OVERSTATEMENT upper bound (every futures/ETF short re-priced as cash stock loan at 8%/yr)
costs only 2.11pp ann and moves no gate. The REALISTIC number is -0.02pp: the champion's
shorts are futures/spot/ETF legs whose financing is already inside the futures/margin
book (4.5%/yr charged on the 0.6 leverage), not stock loan. Champion borrow sensitivity
= ~0, quantified.

## R2(c) — OPS RUNBOOK SCENARIO — PASS
`CAMP_SHORT_SHORTABILITY_R2.json` now carries an `ops_runbook` block: entry point
(`bt.shortability.shortability_pregate`, bt/shortability.py:45), pipeline order,
champion headroom (0.02pp realistic / 2.11pp bound), gate-move threshold
(`neg_years > 0 or MDD <= -7%` vs rebuilt T0 -> escalate), escalation procedure, and
status GREEN. Pinned by 4 tests in `bt/tests/test_shortability_r2c_stressjson.py`.

## Bugs found and fixed this round (TDD, RED->GREEN)

1. **REALISTIC/BOUND collapse (real bug, would have published a wrong number).**
   `champ_tier_delta` used `base_rate.get(n, 0.0)` semantics: slots absent from the base
   map were re-priced from an implicit 0.0 base, making REALISTIC identical to BOUND
   (stale JSON: REALISTIC drag 1.522% == BOUND 1.523% — the tell). Fixed to skip
   unlisted slots (REALISTIC touches only true stock-loan slots). RED: 3 tests failed
   (`work_r2/test_champ_short.py`); GREEN after fix. Consequence: REALISTIC T2 corrected
   from -2.10pp to **-0.02pp** — a 100x overstatement of champion borrow risk caught
   before publication.
2. **delta-vs-base conflation (reporting bug).** Rungs were diffed against the COMMITTED
   headline while being computed on the REBUILT base, so any upstream sleeve drift was
   silently folded into the borrow delta (showed as -0.18pp "borrow" that was really
   0.16pp rebuild drift + 0.02pp borrow). Fixed: rungs diff against rebuilt T0; the
   committed-vs-rebuilt gap is reported separately (`rebuild_gap_ann_pp`, now 0.0).
   RED: 3 contract tests; GREEN after fix.
3. **Reproducibility vs working-tree drift.** 4 champion-input sleeves were regenerated
   by CAMP_COST's 06:09 costfix AFTER the champion commit, so working-tree rebuilds
   drifted (max|diff| 9.9e-4). Fix: `load_sleeve(pin_git_head=True)` reads the
   git-COMMITTED blobs — champion stress tests are reproducible from committed inputs
   (max|diff| 1.0e-16) and immune to unrelated working-tree churn; drift is a reported
   monitor, not a silent contaminant.
4. **Self-contradictory pin.** `test_camp_short_r2b.py::test_runbook_rungs_monotone_…`
   demanded `delta >= 0` at T2, i.e. zero borrow drag — contradicting its own census.
   Corrected contract: weakly decreasing in tier, never positive, >= -5pp envelope.

## Test status (my lane): 38/38 PASS
`test_shortability.py` (10) + `test_shortability_r2.py` (7) + `test_shortability_r2b_ladder.py`
(6) + `test_shortability_r2c_stressjson.py` (4) + `test_camp_short_r2b.py` (7, 1 repaired)
+ `work_r2/test_champ_short.py` (3) + census pins.

## Cross-lane incident (NOT mine — flagging for coordinator, no files touched)
CAMP_COST's 06:09 costfix (half-turn -> FULL |dW| @6.4bps) regenerated 4 champion-input
sleeves (QA_dualmom_band121, E1_QAxasts_tsmom189, E1_brwt_rev15, diescrack_L40Z20) and
`scripts/QA_dualmom_band121.py` after the champion was committed at 00:45. This breaks
exact-repro pins OUTSIDE my lane (12 failures): `test_audit_champ2_round2` (4),
`test_audit_recon_lineage` (3), `test_auditrecon_r2_lineage` (1),
`test_auditrecon_r2_pin_mutations` (1), `test_camp_cost_full_dw` (1), `test_camp_cost_r2`
(2), `test_rawew13v2` (1), `test_camp_borrow_round2` (1 — dualmom generator pin drifted).
I verified these were green before 06:09's regen and did NOT modify CAMP_COST/CAMP_BORROW/
AUDIT files. Either the champion needs a re-emit on costfixed inputs (a coordinator
decision — it would move the committed headline) or those pins need the same
git-HEAD-pinning treatment my lane uses. My lane is immune either way.

## Verdict
R2(a) PASS — snippet published, contract-tested, works on a real candidate stream.
R2(b) PASS — champion borrow sensitivity quantified: REALISTIC -0.02pp, BOUND upper bound
-2.11pp, gates never move (0/19 neg years, MDD > -7% everywhere). R1's MHX-style tier
risk is real for single-name sleeves but immaterial to THIS champion.
R2(c) PASS — ops scenario JSON committed with runbook block, test-pinned.

ROUND 2 DONE


---

# ROUND 3 — 2026-09-07 (per charter: read GATES_CONTRACT.md + DEAD_IDEAS.csv FIRST)

Dead-family discipline: no listed-dead family was re-tested; the census re-prices
borrow on EXISTING library/intake sleeves (measurement, not signal re-tuning).
Everything below reproduces from saved scripts in `campaign/agents/chief/coord/
CAMP_SHORT/work_r3/`.

## R3(a) — LIBRARY BORROW CENSUS — PASS with honest fail-closed rows
Artifact: `campaign/results/CAMP_SHORT_LIBRARY_BORROW_CENSUS.json` (36 rows = top-30
library sleeves by recomputed SR_d + 6 BLEND_CANDIDATE_SUBMISSION intake). Tests:
`bt/tests/test_camp_short_r3_census.py` (17, RED->GREEN).

Method (every number MEASURED, none assumed):
- Generators-of-record re-run; a sleeve counts MEASURED only if the rebuilt
  equity-curve pct_change matches the committed library bytes on the inner join at
  tol 2e-4 (float/CSV round-trip). Dual cost-era validation (6bps pre / 12bps post the
  2026-08-13 rebaseline) resolved byte-exact matches for files from both eras.
- Validation quality: 11 MEASURED (10 byte-exact at 5e-16..8e-16 + XGB1y
  activity-validated), 18 STRUCTURAL (no stock-loan market exists: FF-factor legs,
  DV01 spread synth, real futures panel, long-only construction, perp), 7
  SHORT_LEG_UNKNOWN (fail-closed, loud: AP_gold, MSSW, Multi_Strategy_EW,
  L_S_Market_Neutral, CTA_CTA_10/15vol_21d — the latter two arithmetic-validated
  e-16 on 2008-2019 but the published bytes need a 2020+ price-panel vintage no
  longer on disk (8 twelve_big names regenerated 08-17/08-28); NOT_INTEGRABLE).

## HEADLINE FINDING 1 — the library's "L/S" equity books are long-only BY BUG
`strat_ls_equity.py:134` multiplies the short leg by `-1` after normalization
(`neg / |neg|.sum() * short_scale * -1`), flipping every intended short weight
positive. Byte-exact re-nets (5.2e-16) prove the published books carry mean |short|
= 0.0000: L_S_130_30, L_S_120_20, L_S_Dollar_Neutral, L_S_130_30_volmanaged. They are
borrow-clean, but by BUG not design, and the intended short notional was added to the
long side (130/30 is really 160/0).

## HEADLINE FINDING 2 — XGB1y_deploy: the one real, sized, un-priced short leg
Bottom-decile-by-prediction monthly L/S (67 quarterly cohorts, 12m hold), |short|/NAV
= 1.0 on every live month (validated 100.0% of published rows). Generator charges
ZERO borrow (24bp trade cost only). Tier drag on a 15.33%-ann sleeve: 0.5%/yr at
EASY, 2.0% at MEDIUM, 8.0%/yr at HARD — integration-grade pricing would more than
halve it. The library's other un-priced shorts: StatArb_40pairs (|short| 0.8933,
SR -0.09), EMN (0.7965, SR -0.35), Global_Macro (0.4048 incl. FX/crypto legs,
SR 0.20), Merger_Arb PEAD family (0.40-0.42, SR 0.33-0.46).
ls_n10r14_2018 is the CONTRAST case done right: generator already charges
(DFF-150bps rebate)+25bps ETB (measured base 1.1%/yr over its window) — EASY rung is
a -0.38pp CREDIT delta, never a double charge.

Verdicts: 7 INTEGRATION_RISK (real shorts, un-priced or tier-sensitive), 18
INTEGRATION_OK (no borrowable leg), 11 NOT_INTEGRABLE (fail-closed).

## R3(b) — BLEND_PREGATE.md PUBLISHED — PASS
`campaign/agents/chief/coord/CAMP_SHORT/work_r3/BLEND_PREGATE.md` for HUNT_VOL2:
pipeline order, snippet, tier ladder, integration rule, PLUS the R3 correction to the
blend lane's standing assumption ("published nets already cost 0.5% EASY borrow" is
FALSE for library equity books — `blend_r3_lib.py:322` cites it), and per-candidate
borrow status for all 6 intake sleeves (MSSW NOT_INTEGRABLE: SharpeW blend generator
off-disk since ad-hoc commit e0e47e0, legs unpriceable; A_rs/A11/COMP50d long-only
delta 0; CMDTrot_h2 already charges 0.5%; CRX1030 needs funding-stress delta, not a
borrow tier).

## R3(c) — CHAMPION RE-EMIT HAPPENED MID-RUN (TWICE); LADDER RE-RUN — PASS
- 10:59:48: worktree re-emit (4 input sleeves regenerated: brwt15/QAxasts/dualmom/
  diescrack, max|head-worktree| 9.94e-4) — HEAD 39.8510% vs worktree 39.6873%.
- 14:27:09: coordinator COMMITTED the costfix re-emit (b268e52, "full |dW|@6.4bps on
  all 13 sleeves", brwt10/7/5 swapped to CAMP_COST costfix CSVs): committed champion
  now ann 37.1954%, SR_d 3.181, SR_m 2.263, MDD -6.69%, 0/19 neg years, worst year
  +7.31%. My independent rebuild with the new pool pins it byte-exact: max|diff|
  9.996e-17.
- Ladder re-run vs the NEW champion (work_r3/cache/champ_ladder_new.json):
  REALISTIC 0.5/2/8%: -0.001/-0.004/-0.02pp. BOUND (deliberate overstatement: every
  short as cash stock-loan): -0.27/-0.54/-2.15pp. Gates NEVER move: 0/19 neg years
  and MDD > -7% at every rung of both ladders (worst-year floor +5.31% at BOUND T2).
- `CAMP_SHORT_SHORTABILITY_R2.json` ops-runbook refreshed against the new champion
  (committed_headline 37.2, rebuild_gap 0.0); its 11 pin tests GREEN.

## Test status (my lane): 55/55 PASS
test_shortability (10) + r2 (7) + r2b_ladder (6) + r2c_stressjson (4) + camp_short_r2b
(7) + r3_census (17) + work_r2/test_champ_short (3) + stressjson/census reruns.
New: `bt/tests/test_camp_short_r3_census.py` (17, written RED first, 4 contract
expectations corrected during GREEN as measurement revealed the flip-bug reality).

## Bugs/risks flagged (not mine, not touched)
1. `strat_ls_equity.py:134` flip bug (above) — affects every consumer of the L/S
   library labels, incl. HUNT_VOL2's blend_l3 pool via MSSW.
2. `blend_r3_lib.py:322` "already costed" assumption — corrected in BLEND_PREGATE.md;
   HUNT_VOL2 should switch library-sleeve candidates to the pregate.
3. CTA-panel library bytes are unreproducible on the current data vintage (documented
   in census rows; the 2008-19 exactness proves the arithmetic, not the data).

ROUND 3 DONE


---

# ROUND 4 — 2026-09-07 (fix the library bug I found in R3)

Charter order honored: GATES_CONTRACT.md + DEAD_IDEAS.csv read FIRST (117 data rows —
file grew past the charter's 108; no listed-dead family re-tested). MHX guardrail:
DEAD_IDEAS row 11 kills "MHX annual retrain" (SR 0.45 vs claimed 5.20, unreproducible)
— I did NOT re-run that signal. What the charter pre-registers for me is re-costing the
R1 borrow-impact numbers under the fixed generator, which is measurement, not signal
re-tuning. Every number below reproduces from
`work_r4/r4_mhx_impact.py` (artifact: `work_r4/r4_impact.json`).

## R4(1) — TDD RED->GREEN fix in strat_ls_equity.py — PASS

Test file: `campaign/bt/tests/test_camp_short_r4_lsfix.py` (4 tests; written by the
21:40 attempt of this agent that died on a launcher 429 BEFORE touching production
code — I re-witnessed the RED myself rather than trusting an unseen failure, then
repaired one test's contract during GREEN, see below).

RED (pre-fix, actual pytest output): 4 failed in 4.08s —
`AssertionError: no negative weights anywhere — short legs flipped long (the R3 flip
bug)`; the captured weight matrix is all-positive (0.271/0.270/0.223/... summing to
1.6 on every signal day), i.e. the five intended shorts landed long. Right reason.

Fix (one convention change, cited): `tools/quant/hedge_fund_strats/strat_ls_equity.py:139`
now reads `neg / neg.abs().sum() * short_scale` — short weights STAY NEGATIVE.
Convention citations (charter: "pick the convention that matches the docstring"):
  - core.py BacktestEngine.run docstring: target_weights are
    "(positive=long, negative=short, sum=net exposure)";
  - strat_ls_equity module docstring: "130/30 (130% long, 30% short, 100% net)" —
    short book must sum to -gross*(1-net)/2 = -0.3;
  - compute_ls_signals (same module) already emits negative short weights; the
    rescale must preserve that sign, not flip it.

GREEN (post-fix): 4 passed in 4.83s. Full bt suite: **348 passed** (46.3s, 0 failures).
Lane suite: **56 passed** (all 7 CAMP_SHORT test files). Because I repaired a test's
assertions during GREEN, I re-witnessed RED for the corrected file: `git stash` of the
fix -> 4 failed; `stash pop` -> 4 passed. Fixture honesty note: the one repaired test
had asserted exact short-book membership, but the documented composite is 70% momentum
+ 30% 5-day reversal, so a high-drift name that just ran up legitimately lands short;
the contract now asserts book ORIENTATION (short mean drift-rank > long mean drift-rank,
>70% of shorts in the bottom half) instead of exact membership.

## R4(2) — MHX impact re-run under the fixed code — what changed: NOTHING (proven, 3 ways)

R1's number on record (combined-role FINDINGS, still the only surviving R1 copy):
"champion has NO single-name L/S slot -> no champion impact; MHX-type books flagged
~75bps/yr borrow-tier uplift". R1's script did not survive, so I re-derived:

  (A0) AST import audit: xgb_multi_horizon.py imports {features, features6,
       pipeline_common, xgboost, numpy, pandas, ...} — strat_ls_equity: False,
       hedge_fund_strats: False. The flip bug is not in MHX's code path.
  (A1) Generator-of-record proof: rebuilt the MHX blend from the surviving prediction
       pickle horizon_preds_20y_f6.pkl and byte-validated vs the committed
       COORD/sleeves/MHX_multihorizon_xgb.csv: max|diff| = 9.983e-17 (n=4682), tol 2e-4.
       The committed bytes contain ZERO strat_ls_equity code path. (The other three
       caches miss: f5 8.1e-2, 20y 1.5e-1, f5fix 2.1e-1 — f6 is the vintage.)
  (A2) Borrow ladder re-priced on the MEASURED short book. Book convention is EW 1/K
       per name on both sides (xgb_multi_horizon.py:141-143: ret = mean(topK fwd) -
       mean(botK fwd) - 2*cost), so |short|/NAV = 1.0 pre-vol-target; blended across
       H=1/5/21 with each horizon's own 13% vol-target scale (mean scale 0.2960):
       mean |short|/NAV = 0.296012. Drag: EASY 0.148% / MEDIUM 0.592% / HARD 2.368%/yr.

  State what changed vs R1: (i) the strat_ls fix changes MHX by exactly 0.000pp —
  proven by import graph AND by byte-reproduction of the committed sleeve without the
  buggy module; (ii) R1's ~75bps/yr MHX flag is confirmed in order of magnitude and now
  has a reproducible derivation — my EASY/MEDIUM rungs (15-59bps/yr) bracket it; the
  honest HARD number is 2.37%/yr on the vol-targeted book; (iii) champion impact
  remains 0.000pp — MHX was removed from the champion pool (GOAL100_FINAL_TRUTH.json
  removed_after_audit), and the champion's real stock-loan slot (diescrack) was already
  priced in R2/R3.

  Measurement correction caught mid-round (flagging myself): my first A2 pass wrote
  |short|/NAV = K/n (mean 0.0112 -> HARD 0.089%/yr), understating borrow ~30x by
  reading the return-difference convention as an allocation. Corrected to 1.0 pre-VT
  before publishing; the JSON on disk is the corrected run.

## R4(3) — the fix's real blast radius: the library L_S books (found by measurement)

Committed bytes vs fixed rebuild (same engine shim as R3 census, 12bps cost era;
buggy-sign replication validates provenance at 5.2e-16 / 5.4e-16 / 5.2e-16 for
130_30 / 120_20 / Dollar_Neutral — direct proof the committed books ARE the bug's
output; tol 2e-4, n=4682-4683):

| book (library label) | committed ann/SR/MDD | FIXED ann/SR/MDD | mean\|short\|/NAV | borrow drag EASY/MED/HARD %/yr |
|---|---|---|---|---|
| L_S_130_30 | +19.995% / 0.822 / -45.84% | +13.159% / 0.732 / **-28.90%** | 0.2825 | 0.14 / 0.57 / 2.26 |
| L_S_120_20 | +15.525% / 0.825 / -34.99% | +14.812% / 0.877 / -30.63% | 0.0944 | 0.05 / 0.19 / 0.75 |
| L_S_Market_Neutral | +25.428% / 0.867 / -46.50% | **-1.119% / 0.002 / -33.06%** | 0.9417 | 0.47 / 1.88 / 7.53 |
| L_S_Dollar_Neutral | +23.291% / 0.814 / -46.60% | **-1.119% / 0.002 / -33.06%** | 0.9417 | 0.47 / 1.88 / 7.53 |
| L_S_130_30_volmanaged | +16.153% / 0.805 / -26.64% | +14.475% / 0.736 / -23.83% | n/a (rescale) | scales with 130/30 |

Provenance caveat, stated honestly: L_S_Market_Neutral committed bytes do NOT
byte-validate against my buggy replication (max diff 7.6e-3, n=4680 vs 4683 — a
slightly different panel vintage), so its row is provenance-soft; the other three are
byte-exact. Dollar_Neutral and Market_Neutral are the same book by construction
(census R3 pinned the rename), hence identical fixed stats.

HEADLINE: the library's "market neutral" equity books earn **-1.12% ann (SR 0.00)
when actually neutral** — the published +23-25% ann / 0.81-0.87 SR is 100% flip-bug
artifact (the bug turned them into gross-2.0 long-only momentum books that rode a
bull market and ate 2008). Secondary: honest shorting IMPROVES 130/30's MDD by 16.9pp
(-45.84% -> -28.90%) because the short book finally hedges the long book's crash
exposure. The momentum+reversal composite's claimed L/S alpha does not survive its
own short leg: this is a NEW honest-negative corner (properly-signed book, byte-pinned
engine), not a DEAD_IDEAS re-test.

Downstream consumers of the buggy bytes (historical, prior rounds, NOT modified by
me — listed for the coordinator): campaign/scripts/a1_mix_breadth_cta.py,
a4_r2_overlays.py, a5_idea1b_blend.py, a5_idea7_blend_msew.py (corr_to_lib),
a5_common.py; tools/quant/hedge_fund_strats/blend_{monthly,6stream,refined,variants}.py.
Any of those published numbers that leaned on L_S_130_30's "short" leg inherits the
artifact. Regenerating the library L_S CSVs is a coordinator call (it would change
library bytes 5 agents have pinned); my lane's pins are all on my own artifacts.

## Champion integrity — untouched, verified
git status clean for campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
(mtime 11:24, before my session), campaign/results/sleeve_library/ (L_S bytes Aug 28),
COORD/sleeves/ (MHX Sep 1). My only production-code diff:
tools/quant/hedge_fund_strats/strat_ls_equity.py (+6/-1). The equity_FactorMom_*.csv
working-tree diffs predate my session (19:21 — another agent's wave), and none of my
runs write outside work_r4/ + bt/tests + that one tool file.

## Verdict
R4(1) PASS — flip bug fixed RED->GREEN (4 failed -> 4 passed; suite 348; lane 56),
convention cited from docstrings. R4(2) PASS — MHX impact re-run: the fix changes MHX
by 0.000pp (proven), R1's ~75bps/yr flag reproducibly bracketed by measured EASY/MEDIUM
rungs (0.148/0.592%/yr; HARD 2.368%/yr), champion impact 0.000pp. R4(3) DELIVERED —
committed L_S books proven to be the bug's bytes (5e-16), honest rebuilds quantified;
the "market neutral" family's published alpha is a sign-flip artifact.

ROUND 4 DONE


---

# ROUND 5 — 2026-09-08 (per charter: read GATES_CONTRACT_V2.md + recount DEAD_IDEAS.csv FIRST)

Contract V2 read first (RATIFIED 09-08 03:1x; v1 gates 1-5 unchanged; two-track rule §0
noted — this round is a CHAMPION-track audit, not a sleeve submission). DEAD_IDEAS.csv
recounted myself: **126 data rows** (127 lines incl header; charter said 120 at R4-end,
file grew by 6 uncommitted overnight rows: FX-carry-nominal, SPY/EWH/EWM rotation,
vol-gates, crypto regime overlays, USREC switch, T5YIFR tilt, COT-copper — none mine).
Discipline: DEAD_IDEAS row 11 kills "MHX annual retrain" (SR 0.45 vs claimed 5.20) —
NOT re-run. What R5 pre-registers for me is a composition/shortability AUDIT of the
current pool (measurement, carried from the CHAMPION20Y_V2 deprecation banner,
GOAL100_CHAMPION.md:274). No new signals. bt/ treated as QUIET (my only writes:
work_r5/). Every number reproduces from `work_r5/r5_shortability_reaudit.py`
(artifact: `work_r5/r5_audit.json`); pins: `work_r5/test_r5_audit_pins.py` (5, green).

Champion integrity first, fresh: `bash campaign/bt/verify_champion_r3_cmd.sh` re-run
exit 0, ok=true **7/7**, ann 37.1954% / SR 3.1810 / MDD -6.6922% / 0 neg yrs / n=4805
(2008-03-31..2026-08-27), sha256 prefix 4358dfab95679b97, cost model full_dw ratio
1.0000000000008, gross max 1.6000000000007 <= 1.6 — matches the charter's quote exactly.

## R5(a) — MHX shortability re-audit / single-name-short exposure post-costfix — PASS: NO

Question (banner + charter): does any CURRENT champion sleeve imply single-name short
exposure post-costfix? **Answer: NO — zero single-name short exposure, proven at three
levels**, with the 7 relw moves measured from git (charter quoted 4; I add the 3
CAMP_COST source-swap slots):

| slot | relw pre b268e52 | post | delta | short legs? |
|---|---|---|---|---|
| brwt15 | 1.698432 | 1.658306 | -0.040126 | Brent-WTI FUTURES spread (fungible) |
| brwt10 | 1.888141 | 1.838027 | -0.050113 | " (costfix source swap) |
| brwt7 | 1.917666 | 1.859950 | -0.057716 | " |
| brwt5 | 1.889186 | 1.822379 | -0.066807 | " |
| diescrack | 0.948122 | 0.916052 | -0.032070 | HO-CL FUTURES spread (fungible) |
| QAxasts | 0.989936 | 0.982196 | -0.007740 | leg signs, fungible (below) |
| dualmom | 0.994271 | 0.989144 | -0.005128 | NONE — long-only (below) |

(C5ng/C5ngsum/A5r2/a6r7/carryv2/CFX4: delta exactly 0.000000.)

Level 1 — slot weights: rebuilt Wg from COMMITTED sleeve bytes with the builder-of-record
arithmetic pins the committed champion byte-exact (max|diff| **1.11e-16**); min slot
weight = 0.0000, **0 negative slot-weight days** across 13 slots x 4805 days — the
champion never holds a net-short slot, so no single-name short can appear at slot level.

Level 2 — inside the one single-name equity slot (dualmom, 298-name panel, closes()
measured 5006 rows x 298 names, 2006-09-20..2026-08-12): re-ran its costfix generator
(QA_dualmom_band121.py, 6.4bps FULL|dW|) and measured the position stream: **0 negative
weights in the month-end target matrix and 0 in the live T+1 stream**; long top tercile
only, mean 90.4 names held when invested (max 99), min weight 0.0. LONG-ONLY re-proven
on the post-costfix bytes — the R2 census class survives the costfix.

Level 3 — the two STOCKLOAN-census slots re-measured from the frozen generators:
diescrack shorts 338/4665 days, mean short frac 0.0725 of sleeve — HO-CL diesel-crack
FUTURES spread (spot proxy); CFX4 959/1800 days at 0.1256 — GBP/NZD/AUD/EUR FX crosses
(cash-FX margin). Both fungible; neither touches a single-name stock-loan market.
QAxasts leg audit: shorts are leg-level TSMOM signs on OIL/GOLD/BOND(UST10y synth)/
DXY/VIXS (futures-ETF-fungible, no single names); VIXS short 35.21% of champion-span
days (1628/4624) — consistent with harness C5's cited 35.1% (their vintage). Shares:
QAxasts SLOT = 2.345% of portfolio gross post-costfix (vs 2.16% pre-costfix,
AUDIT_CHAMP2 R1); the VIX LEG inside it = 0.452% of portfolio gross (short-side
contribution ~0.16% of gross). Self-correction during drafting: my first pass called
2.34% the "leg" share — it is the slot share; the leg is 0.452%.

MHX itself: still ABSENT from the champion of record (not in the 13-sleeve weights
file; GOAL100_FINAL_TRUTH.json removed_after_audit). For the chartered CHAMPION20Y_V2
rebuild (which keeps MHX in its pool), the carried borrow caveat stands with R4's
reproducible numbers: MHX book mean |short|/NAV 0.2960 pre-vol-target -> EASY 0.148% /
MEDIUM 0.592% / HARD 2.368%/yr drag on the vol-targeted book — disclose or drop MHX
when that rebuild runs.

## R5(b) — harness C5 spot-check on the champion of record — PASS, exact numbers

`audit_harness_newconstraints.audit_C5` ("fungible short (no single-name eq)") re-run
against the live post-costfix builder: **ok=True** — "13/13 instrument classes verified
(dualmom LONG-ONLY => no single-name short); min slot weight=0.0000 (no net-short
slots); top gross shares: brwt10=23.0%, brwt7=20.0%, brwt5=17.0%; CFX4 weight=0.00".
My independent decomposition (more decimals, same result): **brwt10 22.95% / brwt7
19.96% / brwt5 16.97% / brwt15 13.23% / C5ng 8.80%** of portfolio gross. Full C1-C7
battery green in the same run: C1 cost ratio 1.0000; C2 margin 2.70%/yr residual 0.0;
C3 gross mean 1.600000, 0 over-days; C4 0/19 neg yrs worst +7.31%; C5 above; C6
construction=causal(nav.shift(1)), perturbation excess 7.0e-16 (<1e-6), corr(dW_t,r_t)
=-0.032; C7 files match maxdev 1.0e-16.

V2 §6 bonus evidence (not mandatory for a champion-track audit, run anyway): formal
`bt.leakcheck.leak_probe` on the byte-exact rebuilt Wg — **leak=False**, same-period
corr **-0.0329** (p 6.4e-7), lag argmax at -1 (+0.795, the nav-drift causal signature),
n=4657 — reproduces the contract's quoted champion calibration (-0.032) on today's tree.

## Post-costfix borrow re-price (REALISTIC treatment, census slots only)

diescrack mean short notional = **0.196% of champion NAV** (relw 0.9161). Tier deltas
vs its already-charged 0.5% base: EASY +0.000pp / MEDIUM **+0.0029pp/yr** / HARD
**+0.0147pp/yr**. CFX4: relw 0.0 -> 0.000pp at every rung. The R2/R3 runbook headline
(REALISTIC -0.02pp, BOUND -2.15pp, gates never move) remains valid and now extends to
the post-costfix champion: even the full 8% HARD tier on the only stock-loan slot costs
1.5bps/yr — three orders below gate-moving materiality.

## Test status (my lane): 59/59 lane + 5/5 new pins, all PASS

Lane suite (7 bt test files + work_r2/test_champ_short.py): **59 passed** (7.94s).
New `work_r5/test_r5_audit_pins.py` (5 tests): acceptance/sha/headline pin, no-single-
name-short (slot + dualmom generator), top gross shares exact (brwt10 22.95 / brwt7
19.96 / brwt5 16.97), borrow immateriality at every tier (<0.05pp), C5 green with
13/13 classes. Pins deliberately live in work_r5/ — bt/ is a QUIET tree this round.

## Flag for the coordinator (not mine, not touched)

audit_C5's message hard-codes two AUDIT_CHAMP2-R1 vintage numbers that have drifted
slightly post-costfix: VIXS short-day share (cited 35.1% of days; fresh champion-span
measure 35.21%) and QAxasts slot gross share (cited 2.16%; post-costfix 2.345%, VIX
leg inside it 0.452%). Both disclosures remain substantively correct
(futures-fungible, immaterial); AUDIT_CHAMP2 owns the file and may want to refresh
the constants when it next touches it.

## Verdict

R5(a) PASS — the current (post-costfix) champion implies ZERO single-name short
exposure: no net-short slots (0/62,465 slot-days), the only single-name panel is
re-measured long-only on its costfix generator, and both stock-loan-class slots are
futures/FX books. MHX stays outside the champion; its borrow caveat is quantified for
the CHAMPION20Y_V2 rebuild. R5(b) PASS — harness C5 green on the live builder with top
gross shares confirmed to two decimals (brwt10 22.95 / brwt7 19.96 / brwt5 16.97),
full C1-C7 green, champion of record re-verified 7/7 at sha 4358dfab95679b97.

ROUND 5 DONE

## ROUND 6 (coordinator standup 2026-09-08 11:5x CST) — charter (a) FRAUD-CATCH cross-verification + (b) short/borrow-row curation

READ FIRST honored: GATES_CONTRACT_V2.md (in force; no gates.run call this round — evidence
only) + DEAD_IDEAS.csv recounted MYSELF at round start: **141 data rows** (charter said 137 at
R5-end; concurrent appends are by design). No dead family re-tested, no re-tuning; the only
ledger write is my own curation row (charter duty (b)). bt/ untouched; champion/weights/builder
untouched; my writes: coord/CAMP_SHORT/work_r6/ + one DEAD_IDEAS row.

Champion integrity fresh at round start: `bash campaign/bt/verify_champion_r3_cmd.sh` exit 0,
ok=true **7/7**, ann 37.1954% / SR 3.1810 / MDD -6.6922% / 0 neg yrs / n=4805
(2008-03-31..2026-08-27), sha 4358dfab95679b97 — matches the charter quote exactly.

## R6(a) — CAMP_BORROW R5 verdict reproduced with OWN code — CONFIRMED, 75/75 checks, 0 mismatches

`work_r6/r6_repro_borrow.py` (own algebra; imports NEITHER rawew13v2_build NOR bt.borrow NOR
bt.financing_stress NOR any CAMP_BORROW module — only their published artifacts are READ).
Every load-bearing R5 claim reproduced independently:
- builder rebuild byte-matches the committed champion: max|dev| **9.996e-17**; relw table
  reproduces from max(IS_SR,0)^0.55 to **2.22e-16**.
- margin **2.70%/yr** = 0.6 x 4.5%/252 = **1.0714 bps/day**, single distinct daily value;
  gross exactly 1.6 (max 1.6, 0 days over); committed file priced at EXACTLY 4.5% (residual
  **9.996e-17** vs 2.38e-05/4.76e-05 at 5.5%/6.5%).
- **62,465 slot-days, ZERO negative slot weights** (their C1); CFX4 relw = max(IS_SR,0)^0.55
  = 0 (IS_SR = -0.076 in my rebuild), weight exactly 0 on all 4805 days (their C4).
- diescrack embedded borrow re-derived from an OWN zrev+VT reconstruction (FRED
  DJFUELUSGULF*42 minus wti_full, log spread, L40 z2.0, vt 0.08, 6.4bps FULL|dW|): committed
  file embeds EXACTLY **0.005/252 on 733/4605 rows (331 short / 173 long / 229 cost-only)**,
  max ||line|-0.005/252| = 9.999e-17 (their C2, row-for-row identical).
- champion embedded drag **0.2195 bps/yr**; HTB 2% -> **0.6586 bps/yr**, 8% -> **3.2931
  bps/yr** (their C3).
- drift flags reproduce EXACTLY from their fetched FRED artifacts (DFF 3.63% n=26363, SOFR
  3.66% n=2198, both 2026-09-03): implied call 5.13/5.63/5.16% -> rel +14.00/+25.11/+14.67%;
  elementwise DFF+1.5pp path mean 2.9315% -> drag 1.7589% rel **-34.86%**; champion reprices
  ann **36.6784 / 36.2695 / 36.6538 / 38.4910%** (dAnn -0.517/-0.926/-0.542/+1.296pp, SR
  3.1436/3.1139/3.1418/3.2741, MDD never worse than -6.7024%, **0 neg yrs in all four**).
- 6-rung ladder (their r5_tier_ladder.json) reproduced to worst dev **8.0e-15** across
  ann/SR/MDD/arithmetic-slope, incl. the **-0.60pp per +1pp** slope EXACT (my first pass
  failed this check - my bug, missing x252x0.01 unit conversion; fixed, now 1.6e-15).
- borrow 100%-relative-drift impact **0.2196 bps/yr** (their B11 note).
Self-caught my-side defects en route (3 units/convention bugs in MY script, none in theirs);
final state: 75/75 OK, exit 0. Artifact: work_r6/r6_borrow_repro.json.

## R6(a) — CAMP_COST R5 verdict reproduced with OWN code — CONFIRMED, 46/46 checks, 0 mismatches + 1 escalated flag

`work_r6/r6_repro_cost.py` (own algebra + own leak-probe implementation; no CAMP_COST imports).
- verify_champion_r5.json: **7/7 ok**; every reported number re-derived with my own algebra:
  weights_repro 2.220e-16, byte_repro 1.110e-16; cost model **full_dw** (resid 1.2457e-16 vs
  half 1.6798e-05 -> half-turn REJECTED by 5 orders); bp/yr **5.2622** == turnover 5.2622;
  day-1 entry **UNCHARGED** (their day1_entry_charged 3.87e-13 bp is the day-1 cost_implied
  RESIDUAL = float noise; my day-1 |dW| charge is exactly 0 — same fact, both ~0); causality
  sameday 4.927e-03 != 0 with causal mechanism matched; truncation 7 probes dev 0.0; gross max
  1.6000000000007, n_over 0, margin 2.70%/yr; yearly 0 neg / worst +7.3104%; MDD -6.6922%;
  stats n=4805 / ann_cagr 37.1954 / ann_arith 32.1373 / SR 3.1810 / span 2008-03-31..2026-08-27;
  is_end 2017-01-01 inferred.
- byte-stability: I re-hashed all **16/16** files — all == their shas_round_end.json == round
  start, champion **4358dfab95679b97**, weights **149164b3b01aa110**, builder **1095b4f896b9bebb**
  — AND **16/16 committed-byte-exact** vs git HEAD (own git ls-tree + hash-object).
- leak probe: my own wide probe in 3 conventions brackets their number and matches the verdict:
  champ-span fill0 **-0.0324/n4802**, champ-span NaN-keep **-0.0329/n4657**, full-history
  NaN-keep **-0.0206/n7384** vs their **-0.0196/n7026**; argmax at lag -1 (causal, +0.65..+0.79)
  in ALL FOUR; leak=False all four.

### ESCALATED FLAG (verdict-preserving; documentation/reproducibility defect in CAMP_COST work_r5)
Their SCALAR probe (leak_probe_r5.json: corr **+0.0156** / p **0.2796** / n 4805, labeled
"aggregate |dWg| vs champion same-period ret") is **NOT reproducible from the described
input**: faithful |dWg| gives **+0.2034** (champ-span) / **+0.1395** (full-history), both
carrying the causal nav-drift signature at lag -1 (+0.461/+0.443, argmax -1). Their published
lag scan (+0.0156 at lag0 with -0.036/-0.016/+0.003/+0.017 at -2/-1/+1/+2 — NO lag-1
structure at all) matches, to 1.5e-3 on the corr, the **SIGNED float-noise sum**
(Wg.diff().sum(axis=1), std 3.3e-16): +0.01525 / p 0.2906 — i.e. the probe was almost
certainly fed a degenerate signed series instead of |dWg|. 16 constructions swept
(work_r6/r6_scalar_variants.py): NONE reproduces the exact published pair. No generator
script for leak_probe_r5.json exists in CAMP_COST/work_r5/ (only the JSON). **Verdict
UNAFFECTED**: leak=False in EVERY construction including theirs (the flag rule requires
lag-0 argmax, true in none), and this is a guard observation on the standing champion, not
an acceptance call. Escalate to CAMP_COST/AUDIT_CHAMP2: re-run with
score=Wg.diff().abs().sum(axis=1) and commit the generator script. (The faithful scalar
number +0.2034 is itself evidence FOR champion honesty: turnover spikes precede large
champion days at the causal lag, never same-day.)

## R6(b) — DEAD_IDEAS short/borrow-row curation — DONE, row appended (verified)

Audited all **26 of 143** rows (at my append) that touch short/borrow exposure. Finding:
**ZERO dead families died because of borrow cost** — every short-bearing family died on
signal/cost grounds LONG before borrow could matter: L/S equities signal-dead (BAB -0.64
row 113; xs mom -2.2..-1.6 row 26; sector L/S best 0.038 with 8-13 negyr row 89; intl L/S
6/6+14/14 fail row 64; industry L/S zero-to-negative PIT rows 3/111); futures/ETF L/S die
on SR (CMDT2 USCI-DBC/DBE-DBP peak 0.709 rows 91/102); HYG/IEF carry -0.30 net row 105
(its disclosed proxy bias is yield-proxy, not borrow); TimesFM L/S killed by 112-154x
turnover row 128; MHX row 11 stays dead on unreproducibility (SR 0.45 vs claimed 5.20),
with the borrow caveat quantified in my R5 for the CHAMPION20Y_V2 rebuild. Row 133
(RES_BASIS RB_hobr_crack_hyst, standalone V2-PASS pending adoption): sleeve sha
**da0285b9a7a5e6a2** byte-reverified this round; instrument class = HO/Brent FUTURES-proxy
spread, dollar-neutral, its declared 0.5% borrow sits on the spread leg — stock loan N/A,
same class as diescrack. **Borrow is immaterial to the pending-adoption decision**; the open
coordinator concerns (mean-injection placebo 169/200, halves 2.182/0.753, OOS 0.807) are
untouched by this audit. My curation row (source CAMP_SHORT-R6, status verified) records all
of the above + the R6(a) results + ledger state: **143 -> 144 data rows**, file sha256[:16]
at read 7be122a38f074f40 -> cf9a0af284b6fbaf at write, zero byte-dup (idea,source) pairs
(swept before + after append).

## Test status (my lane) + honesty
Lane suite re-run after the ledger append: **413 passed, 0 failed** (55.6s, from repo root;
includes my work_r2 5 pins + prior CAMP_SHORT bt tests; 413 vs 410 at R5 start reflects the
fleet-wide test additions this round, not mine). Both R6 repro scripts re-run clean after
all edits: exit 0, 0 mismatches each. Three of my own first-pass bugs were caught and fixed
by my own checks before any verdict was recorded (units missing x252x0.01 on the arithmetic
slope; borrow-drift factor (1/0.5-1) applied as x2.0; day1-entry compared a residual to a
charge) — each is visible in the script history and none touches the agents' numbers.

## Verdict
R6(a) PASS — both R5 verdicts (CAMP_BORROW borrow-immaterial-at-champion-level with 4
drift flags >10% rel; CAMP_COST full_dw/byte-stable/guard-green) reproduce from published
artifacts with my own code: 75/75 + 46/46 checks, 0 verdict mismatches, **no escalation of
any verdict**; one verdict-preserving reproducibility defect escalated (CAMP_COST scalar
leak-probe input mislabeled/degenerate, no generator script saved). R6(b) PASS — 26
short/borrow rows curated, zero borrow-driven deaths, curation row appended (144 rows).
Capability verdict of R5 stands: 0/62,465 slot-days net-short; borrow immaterial at champion
level (0.2195 bps/yr embedded; 8% HTB tier 3.2931 bps/yr — three orders below gate-moving).

ROUND 6 DONE

## ROUND 7 (coordinator standup 2026-09-08 18:3x CST) — (a) AUDIT_GATES2 V2-conformance spot-recompute (2 of 5 lanes, own code) + (b) capability-lane refresh

READ FIRST honored: GATES_CONTRACT_V2.md re-read (Step-2 flip in force since commit 539f50e; I
pass sig= and leak_check=True explicitly via the RES_BASIS v2_battery wrapper, which calls
gates.run(sig=..., leak_check default-ON) — no dependence on either default state); VOL2's V3
per-class placebo proposal NOT depended on either way. DEAD_IDEAS.csv recounted MYSELF at round
start: **150 data rows** (charter said 145-146 at R6-end; concurrent appends are by design),
sha16 accd64c3173f15f6. No dead family re-tested; no re-tuning. bt/ untouched; champion,
weights, builder untouched. My writes: coord/CAMP_SHORT/work_r7/ (3 scripts + 3 JSONs + 1 pin
test) + one DEAD_IDEAS curation row.

Champion integrity fresh: sha16 re-hashed **4358dfab95679b97** unchanged; n=4805
2008-03-31..2026-08-27 confirmed in-script.

### R7(a) Lane A — HUNT_CMDT2 R5 "0/28 honest-negative" (propane) — VERDICT REPRODUCES, prose-defect numbers CONFIRMED

`work_r7/r7_laneA_cmdt2.py` — own regexes, own stats, no AUDIT_GATES2 imports.
- **28/28 metas parse and reproduce from the 28 prop_*.csv held books** with my own stats:
  27/28 headline-exact; the single non-exact is MY OWN 2dp rounding tie (prop_trend_w63_lo_vt
  own SR 0.295208 vs meta 0.295, dev 0.0002 — exactly the max |SR dev| 0.0004 AUDIT_GATES2
  reported). **All 28 v2_corrected lines report pass=false / bp_ok=False → 0/28 adoptable
  CONFIRMED.** Max |corr_champ| across the 28 = **0.053** (decorrelation never binding — claim
  confirmed from my own intersection-corr recompute).
- Family bests (held-book SR, my stats): seasonality **0.205** / trend **0.370** /
  spreadmr **0.122** — byte-agree with AUDIT_GATES2's published recompute.json.
- **AG2's three CMDT2 prose-defect quotes re-verified from the CSVs with my own code:**
  prop_seas_11-03_vt held-book SR **-0.196** (not the quoted -0.324); prop_seas_11-03_novt
  **-0.109** (not -0.104); prop_spreadmr_w63_z2_vt **-0.017** (not 0.609); prop_trend_w21_lo_vt
  **0.370** held / **0.422** contract-corrected (not 0.465). All lower-half-of-gate either way;
  the defect is exactly as AG2 described (FINDINGS quotes superseded distorted-battery SRs),
  and it changes no verdict.

### R7(a) Lane E — RES_BASIS row-137 standalone V2-PASS — FULLY REPRODUCED (12/12 pin checks)

`work_r7/r7_laneE_resbasis.py` — own algebra layer 1 + their published code path layer 2.
- Sleeve sha16 **da0285b9a7a5e6a2** unchanged; every meta headline reproduces from the CSV
  with my own stats: n=4604, SR **1.3498**, ann **13.25%**, MDD **-22.29%**, H1 **2.182**,
  H2 **0.753**, neg 1/18, worst **-0.69%**, corr_champ **+0.0219**, ac1 **-0.1083**, span
  2008-02-19..2026-08-25. IS/OOS **2.145/0.807** exact.
- Rebuild from FRED raws via their own hunt_r1/run_hunt: max|dev| vs committed CSV
  **9.97e-17** (n=4604). V2 battery re-run MYSELF with sig= explicit: sr 1.6031, corr +0.0215,
  leak_corr0 **+0.1071** p 2.74e-13, lag argmax at -1 (**-0.1885** — causal profile), leak_ok
  True, scr_p 0.000, bp sixty_forty 0.602 < 1.6031, **PASS=True** — matches the meta exactly.
- Plateau re-run per-window LIVE-start: **1.356/1.357/1.350/1.302/1.148** @ w21/40/63/90/126 —
  exact (my first pass re-used the w63 live-start for all windows and got 1.334/1.343 — my
  bug, caught by my own pin test, fixed; the committed meta is right).
- Blend arithmetic, BOTH conventions re-derived: champ-span fill-0 (the meta's + coordinator's
  convention) w=0.25 **dSR +0.199 / dAnn +4.21pp / MDD -6.64% / 0 neg** and w=0.10
  +0.101/+1.68, w=0.35 +0.231/+5.91, w=0.50 +0.235/+8.48 with MDD **-7.96%** breaking the
  wall — every cited number exact. Sleeve-span fill-0 (my convB) is far more flattering
  (+0.789 dSR @0.25, MDD -15.6%) but is NOT the convention anyone published; AG2's own JSON
  numbers (0.204/4.50/0.059) use a THIRD variant (champ fill-0 on sleeve-span, base = fill-0
  champ) which I also reproduced exactly — so AG2's prose (meta convention) and AG2's JSON
  (its own variant) disagree by convention, not by error; both are honest, and neither
  changes the adoption story (adoption rests with CAMP_COST's full rebuild, and the blend is
  informational-only per the meta).
- One thing my own series-level lag probe adds: cand-vs-champ lag scan peaks at lag -1
  (+0.109) not lag 0 (+0.022) — the sleeve leads the champion slightly, consistent with the
  causal, no-lookahead verdict.

### R7(b) Capability refresh — census invariant HOLDS, HTB arithmetic RE-PINNED, drift flags RE-VERIFIED against a FRESH fetch

`work_r7/r7_capability_census.py` (own builder rebuild from the 13 committed sleeve CSVs).
- **62,465 slot-days (4,805 days x 13 slots), ZERO net-short slot-days — invariant holds on
  the current tree.** min slot weight = 0.0 (CFX4 all-zero); the only single-name panel
  (dualmom) min weight **+0.008826** — still long-only by construction and re-measurement.
  All 13 sleeve files sha'd fresh today; no champion-file modification (git: champion clean,
  only ledger/appended artifacts moved).
- **8% HTB tier re-pinned at 3.2931 bps/yr** (2% → 0.6586, baseline 0.2195 embedded) —
  re-derived with my own borrow-line isolation (committed diescrack file minus borrow-free
  reconstruction, slot-weighted, annualized), NOT copied: dev < 5e-4 bps on all three. Still
  three orders below gate-moving.
- **All 4 CAMP_BORROW drift flags re-computed and CONFIRMED against a FRESH FRED fetch I made
  this round** (DFF 3.63% n=26363, SOFR 3.66% n=2198, both last obs 2026-09-03 — identical to
  their R5 artifacts, so the flags are still current): implied call 5.13/5.63/5.16% → rel
  **+14.00/+25.11/+14.67%**; path DFF+1.5pp drag 1.7589% → rel **-34.86%**. Champion
  re-prices with my own margin-line swap: **36.6784 / 36.2695 / 36.6538 / 38.4910%** (dAnn
  -0.52/-0.93/-0.54/+1.30pp, **0 neg years in all four**) — all match published to 5e-4.
  Materiality verdict unchanged: the drift is a disclosed modelling-lane item, not a
  gate-mover; borrow remains immaterial at champion level.

### Honesty notes (my own first-pass bugs this round, all caught by my own checks)
1. `[:-5]` vs `[:-9]` meta-name strip → name lookups empty; fixed before any verdict.
2. Plateau grid re-used w63 live-start for all windows (1.334/1.343 wrong) — caught by my pin
   test AFTER I had the "wrong" JSON on disk; per-window live-start reproduces 1.356/1.357
   exactly. The committed RES_BASIS plateau line was never wrong.
3. Drift-flag rel-drift SIGN convention mine vs theirs, my reprice sign flip, and one
   DFF percent-vs-fraction unit bug — each produced absurd numbers I refused to report
   (216% ann, +3114% rel); fixed to the R6-proven conventions; every final number now
   matches published artifacts to 5e-4 or better.

### Test status + ledger
Pin suite `work_r7/test_r7_audit_pins.py` **12/12 passed**; bt suite from repo root
**436 passed / 0 failed** (83.1s; 426 at R6 close — delta is fleet additions, none mine).
DEAD_IDEAS.csv **150 → 151** data rows (my curation row appended with trailing newline, 0
malformed, 0 byte-dup (idea,source) pairs swept before + after; sha16
accd64c3173f15f6 → 82bf4bcc91b71c1f).

### Verdict
R7(a) PASS — both spot-checked AUDIT_GATES2 lane claims (HUNT_CMDT2 0/28 with the disclosed
prose defect; RES_BASIS row-137 standalone V2-PASS with disclosed OOS 0.807 / halves 2.182
/ 0.753) reproduce from published artifacts with my own code; **zero escalations** (the two
R6 documentation defects were already escalated by AUDIT_GATES2 itself; my work confirms
their corrected numbers). R7(b) PASS — 0/62,465 net-short invariant holds; 3.2931 bps/yr 8%
HTB tier re-pinned; all 4 drift flags re-verified against fresh FRED data and remain open,
disclosed, and immaterial (worst reprice -0.93pp, 0 neg yrs). Capability verdict of R5/R6
stands: no stock-loan borrow exposure exists anywhere in the champion; borrow is not a
binding constraint on any current or pending acceptance decision.

ROUND 7 DONE
