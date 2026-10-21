# CAMP_BORROW — FINDINGS

## ROUND 1 (2026-09-06, credited by coordinator in coord/FINDINGS.md sec.10)
Margin verified on the then-committed champion: 4.5%/yr on exactly (1.6-1)=0.6 gross →
2.70%/yr drag (1.0714 bps/day). Stress on the SAME-DAY-LEAK construction (ann 40.84%):
4.5%→40.84/3.339/-6.80%; 5.5%→40.00/3.281/-6.81%; 6.5%→39.16/3.224/-6.82% (≈-0.84pp ann
per +1pp call rate). Borrow: 0.5%/yr on shorts per standard; HTB tier 5% on dualmom's short
frac ≈ 10.6bps/yr champion-level — immaterial.

## ROUND 2 (2026-09-07) — re-audit of the CAUSAL re-emit (00:45, ann 39.85% / SR 3.296)
R1 numbers were computed on the leaked champion. R2 re-runs everything on the shipped
T+1-causal construction. Evidence: every number below is from a fresh command run this round.

### (a) Margin + gross exactness on the new weight stream — PASS
- Committed net reconciles to an INDEPENDENT reconstruction (raw sleeve frame → causal
  nav.shift(1) weights → port − FULL|dW|×6.4bps − (gross−1)×4.5%/252): max|diff| = 0.00e+00.
  No tautology: port is rebuilt from sleeve files, never back-derived from net (the R1
  audit_C2 trap; guarded by new test `test_champion_net_reconciles_to_independent_margin_reconstruction`).
- Margin drag at 4.5%/yr on (gross-1)=0.6: **2.70%/yr = 1.0714 bps/day, unchanged**, and
  constant by construction (np.unique(margin_daily) = single value 0.00010714).
- **GROSS EXACTNESS (charter c): |gross−1.6| max = 1.110e-15 over all 4,805 days
  (2008-03-31→2026-08-27); 0 days beyond the 1e-9 gate, 0 days beyond 1e-12, 0 days >1.6.**
  NO FLAG. The re-emit did not regress the leverage constraint. Fail-closed flag is itself
  tested (`test_gross_exact_flag_fires_on_doctored_stream`: a 1e-6 doctored day → flag fires).
- Harness cross-check: `python3 campaign/audit_harness_newconstraints.py` → C1..C7 ALL PASS;
  C2 residual 0.00e+00 [causal(nav.shift1)]; C3 gross mean 1.600000 over_days=0.
- `rawew13v2_build.py --verify`: IDENTICAL (net max dev 9.996e-17, weights 2.220e-16);
  sha256 champion e6d8b9c0631aac24…, weights 8107aab3bb33fd6f… (weights hash matches R1).

### (b) Call-rate stress ladder on the NEW headline — PUBLISHED
Recomputed at each rung as `port − full|dW|×6.4bps − 0.6×rate/252` (only the margin term moves;
linearity verified to 1e-9 by `test_call_rate_ladder_is_exactly_linear_0p60pp_per_pp`):

| call rate | margin drag | ann_geo | SR_d | SR_m | MDD | neg yrs | worst yr | vol | Δann vs 4.5% |
|---|---|---|---|---|---|---|---|---|---|
| 4.5% | 2.70% | **39.85%** | 3.296 | 2.325 | −6.84% | 0/19 | +8.61% | 10.34% | — |
| 5.5% | 3.30% | 39.02% | 3.238 | 2.285 | −6.85% | 0/19 | +7.94% | 10.34% | −0.84pp |
| 6.5% | 3.90% | 38.18% | 3.180 | 2.245 | −6.86% | 0/19 | +7.27% | 10.34% | −1.67pp |
| 8.0% | 4.80% | 36.95% | 3.093 | 2.185 | −6.87% | 0/19 | +6.27% | 10.34% | −2.90pp |

- Exact arithmetic slope: 0.60pp ann per +1pp call rate (= gross−1), −0.84pp on the
  geometric headline — matches R1's −0.84pp/+1pp finding; MDD/worst-year move ≤0.03pp/1.34pp.
  Goal-irrelevant: even at an 8% call rate the champion holds 0/19 negative years and MDD
  −6.87% (< −7% goal line), ann 36.95%.
- The committed file is priced at EXACTLY 4.5%: max|committed − rebuild(r)| = 0.00e+00 at
  4.5% vs 2.38e-05 (5.5%), 4.76e-05 (6.5%), 8.33e-05 (8.0%). Pinned by
  `test_committed_champion_is_priced_at_4p5_not_a_stressed_rate`.
- IBKR reasonableness (carried from R1, unchanged): 4.5% ≈ fed funds + ~1.5-2pp margin
  spread; IBKR Pro margin loans at this balance size track Fed funds + spread, so 4.5% is a
  fair central proxy and the 5.5/6.5/8 rungs bracket a Fed-hike cycle.

### Borrow reality check — 2 corrections to R1 wording, immaterial to the champion
1. **R1 claim "borrow 0.5%/yr charged inside pool sleeve files" verified for only 2/13
   committed slots.** Evidence: sleeve `.meta` files declare it for diescrack
   (HUNT_BASIS2: "Borrow 0.5%/yr charged on 1-unit short leg on ALL nonzero rows") and CFX4
   (HUNT_CARRYFX: "+ borrow 0.5%/yr on |sig|"). For the other 11 slots the generators are
   futures/ETF/spot-proxy books where stock-loan borrow does not apply (futures shorts are
   margin-financed, already covered by the (gross−1) call-rate term), and no borrow line
   exists in their generators (grep 'borrow|0.005|htb' over A5/A3/E1/loop_team generator
   trees: only HUNT_BASIS2/HUNT_CARRYFX hits). NET EFFECT ON THE CHAMPION: correct — the
   0.5% cash-borrow fee belongs ONLY where stock loan exists, and charging nothing on
   futures shorts is right, not an omission. R1's blanket sentence overstated coverage.
2. **R1 sec.10 said "only dualmom has an equity-type short exposure" — WRONG, and
   contradicted by R1's own sec.9.** The dualmom generator
   (campaign/scripts/QA_dualmom_band121.py) is LONG top-tercile ONLY (docstring + no short
   leg in code; contains no borrow line and no short weights). Champion-level HTB uplift is
   therefore even smaller than R1's 10.6bps/yr figure. Measured census on the actual causal
   weight stream: slot gross shares brwt10 23.65%, brwt7 20.75%, brwt5 18.16%, brwt15
   13.10%, C5ng 7.85%, C5ngsum 5.97%, dualmom 2.47%, QAxasts 2.17%, diescrack 1.71%, A5r2
   1.64%, a6r7 1.43%, carryv2 1.10%, CFX4 0.00%.
3. **HTB tier stress on the only real cash-borrow short leg (diescrack, short leg on 15.8%
   of rows per its meta, slot short notional ≈ 0.0103 of NAV on those days):** MEDIUM 2%
   tier uplift **+0.24bps/yr**; HARD 8% tier uplift **+1.22bps/yr** at champion level —
   immaterial both, no gate moves. Even the absurd upper bound (entire 0.6 of levered
   capital re-financed as 8% stock loan instead of 4.5% margin: +2.1pp/yr) keeps the
   champion at ≈34.8% ann with 0 negative years — a bound no IBKR client would actually pay
   since the book is futures/ETF, financed at the margin rate.
- TDD: campaign/bt/borrow.py (margin_daily / margin_ann / gross_exact /
  borrow_tier_uplift, fail-closed GROSS_TOL=1e-9) + campaign/bt/tests/
  test_camp_borrow_round2.py — 9 tests, ALL GREEN. Full suite 82 → **91 passed, 0 failed**
  (`python3 -m pytest campaign/bt/tests/ -q`: "91 passed in 20.48s").

### Verdict
The causal champion's margin algebra is exact (residual 0.0), leverage is exactly 1.600000
every day (max dev 1.11e-15 ≪ 1e-9 gate — charter (c) NO FLAG), the headline survives an
8% call rate with 0/19 negative years, and borrow modeling needs no correction (only
2 slots have stock-loan legs; HTB stress ≤ 1.22bps/yr champion-level). No changes to the
committed champion or builder. Deliverables: bt/borrow.py, test_camp_borrow_round2.py
(+9 tests), this file.

ROUND 2 DONE

## ROUND 3 (2026-09-07) — financing stress runbook v2 + blend support
Charter (a) rate-path scenarios + ops-JSON rate_paths block + pin tests; (b) blend helper
with exact margin-delta algebra. Evidence: every number below is from a fresh command run
this round. GATES_CONTRACT.md + DEAD_IDEAS.csv read FIRST (106 rows) — no listed-dead
family re-tested, no dead signal re-tuned into a new config (see compliance note).

### Stale-champion catch and re-anchor (fail-closed did its job) — the round's main event
The morning session (09:39-09:52) had built all round-3 machinery anchored to the then-HEAD
champion blob e6d8b9c0… (ann 39.851% / SR 3.2964). At 11:24, commit b268e52 re-emitted the
champion with the cost fix (FULL |dW|@6.4bps on ALL 13 sleeves; the old blob charged
half-notional@6.0bps on the brwt family ≈150-190bps/yr undercharge) — new book of record
**sha256 4358dfab95679b97…, ann 37.195% / SR_d 3.1810 / MDD −6.6922% / 0/19 neg years,
worst year +7.3104%** (independent builder rebuild matches worktree CSV to max|dev| 9.996e-17).
The 09:52 ops JSON still said base ann 39.851% — i.e. the morning's scenario table was priced
on a champion that no longer exists. TDD RED first: pinning the JSON to the costfix headline
made **2 tests fail with gap = 2.6556pp exactly (39.851% − 37.195%)**
(`test_json_base_headline_is_the_costfix_book_of_record`,
`test_json_rate_paths_block_pins_scenarios_and_gates`), then GREEN after re-anchoring.
Two new guards: `test_book_of_record_sha_is_the_costfix_champion` (test refuses to certify
scenario numbers after any re-emit) and a hard sha assert in run_financing_r3.py itself —
the script now REFUSES to run against any champion sha other than 4358dfab…, so a future
re-emit forces a re-anchor instead of silently carrying stale numbers. The morning's
frozen-input two-variant machinery is retired: the 4 formerly-drifted sleeves
(dualmom/QAxasts/brwt15/diescrack) are committed at HEAD, so committed == worktree
(the 09:52 run recorded drifted=true, ann_gap 0.164pp; both variants are superseded).
The 09:52 JSON is overwritten; its numbers are recorded as SUPERSEDED in the JSON's
`champion_drift.reprice_history` block and in this file — not silently deleted.

### Gross exactness on the costfix champion — PASS (charter-adjacent, re-verified)
gross_exact on the new weight stream: ok=True, max|gross−1.6| = **1.110e-15** over all
4,805 days, 0 days beyond the 1e-9 gate.

### (a) Call-rate PATH scenarios on the costfix champion (bt/borrow.py machinery)
Margin charged daily on max(gross−1,0)=0.6 at the PATH rate r_t/252; only the margin term
moves vs base. Constant-path machinery reproduces the champion to <1e-10 (pinned).
Scenarios are calendar-anchored (Lehman 2008-09-15, COVID 2020-02-21, liftoff 2022-03-16);
the two oracle rows are an EXHAUSTIVE argmin over all 4,716 possible 90-trading-day
placements of a sustained 12% rate (vectorized scan cross-checked to the machinery at 1e-9,
and the ann scan asserts agreement) — a true worst-placement bound, not an anchored guess:

| scenario | window | extra drag (% NAV) | ann | SR_d | MDD | neg yrs | gate move |
|---|---|---|---|---|---|---|---|
| base 4.5% | — | — | 37.195% | 3.181 | −6.692% | 0/19 | — |
| 12% × 90d (2008-style) | 2008-09-15..2009-01-16 | 1.6071% | **37.080%** | 3.173 | −6.692% | 0/19 | no |
| 8% × 30d (2020-style) | 2020-02-21..2020-04-02 | 0.2500% | 37.178% | 3.180 | −6.692% | 0/19 | no |
| 6% × 252d (hike cycle) | 2022-03-16..2023-03-02 | 0.9000% | 37.131% | 3.176 | −6.692% | 0/19 | no |
| oracle worst-ann window | 2013-10-21..2014-02-21 | 1.6071% | 37.0798% | 3.172 | −6.692% | 0/19 | no |
| oracle worst-MDD window | 2018-05-02..2018-09-04 | 1.6071% | 37.0799% | 3.173 | **−6.760%** | 0/19 | no |

- Closed-form extra drags match the machinery exactly: 0.6×0.075×90/252 = 1.6071% NAV
  (2008-style), 0.6×0.035×30/252 = 0.25% (2020-style), 0.6×0.015 = 0.90%/yr (hike cycle).
- **NO GATE MOVES anywhere**: 0 negative years in every scenario; MDD never breaches −7%
  (worst case −6.760% under the worst-placed 12%×90d path). Financing stress is
  goal-irrelevant at this gross — margin sensitivity is only 2.38bps/day per 100% rate
  (0.6/252), so even Lehman-style pricing costs 1.6% of NAV spread over 90 days.
- Honest wrinkle worth recording: the oracle argmin for geometric ann lands in
  2013-10..2014-02 (a low-vol grind), NOT 2008 — with a constant daily drag the geometric
  headline is hurt most where daily returns are smallest, and 2008's big up-days compound
  the drag back. Both windows differ by <0.001pp in ann anyway (−0.1155 vs −0.1156pp).

### (b) Blend support — bt/blend.py, exact margin-delta algebra (TDD RED fixture first)
Constant-mix daily-rebalanced split B_t = w·N_c,t + (1−w)·N_s,t; margin charged ONCE on
the BLENDED gross−1 (never per-sleeve at full notional = double-count; never a rebate).
The RED fixture (`test_wrong_margin_sign_fixture_subsidized_blend_is_rejected`) fails a
sign-flipped blender that would add margin as a subsidy: the subsidized blend exceeds the
true blend by exactly 2×m_b on every day, and a blended net beating its own gross-of-costs
port is asserted impossible. `blend_rebuild` re-prices from gross level and raises rather
than silently absorbing a convention mismatch; linear vs rebuilt blend agree to <1e-10 on
the real champion + its unlevered twin (same causal weights at gross 1.0, no margin).

| w_champ | gross | margin/yr | ann | SR_d | MDD | neg yrs |
|---|---|---|---|---|---|---|
| 1.0 | 1.600 | 2.700% | 37.195% | 3.181 | −6.692% | 0/19 |
| 0.8 | 1.480 | 2.160% | 34.479% | 3.217 | −6.195% | 0/19 |
| 0.5 | 1.300 | 1.350% | 30.491% | 3.284 | −5.446% | 0/19 |
| 0.3 | 1.180 | 0.810% | 27.890% | 3.340 | −4.945% | 0/19 |
| 0.0 | 1.000 | 0.000% | 24.072% | 3.448 | −4.190% | 0/19 |

Margin drag is exactly linear in w (w×2.70%/yr, asserted to 1e-9 in the script per rung).
Honest observation for the goal: SR_d RISES monotonically as leverage falls (3.181 → 3.448
at w=0) and MDD improves at every rung — the 1.6× gear buys annual return, not
risk-adjusted quality. GOAL100's headline is ann, so the gear stands; but if the objective
ever switched to SR, the unlevered twin would dominate. No gate moves at any rung.

### DEAD_IDEAS / charter compliance
Read GATES_CONTRACT.md and DEAD_IDEAS.csv (106 rows) before any work. No dead family
re-tested. Note on one apparent overlap: "champion-blend integration (published
decorrelated sleeves, w<=15% NAV)" is DEAD per HUNT_VOL2-R3 **as a candidate sleeve**.
Charter (b) here asked for blend SUPPORT infrastructure (a bt helper + exact margin
algebra), which is what was delivered; the JSON ladder blends the champion with its OWN
unlevered twin (a de-levering ladder), uses no published sleeve, proposes no new
configuration, and re-tunes nothing. Likewise "sector-rs-ratio + barbell composite
(allocation-level blends)" (HUNT_SECTOR2-R3, dead) is a candidate family — not touched.

### Verdict + deliverables
All scenarios and blend rungs pass every goal gate on the costfix book of record; no
change to the committed champion or builder (still untracked-then-owned files only:
bt/borrow.py, bt/blend.py, this test file, work_r3/run_financing_r3.py,
work_r3/champion_committed_4358dfab.csv, campaign/results/CAMP_BORROW_FINANCING_R3.json).
TDD: RED (2 stale-JSON pin failures, gap 2.6556pp) → GREEN. Round-3 file: **18 tests**;
full suite **290 passed, 0 failed** (`python3 -m pytest campaign/bt/tests/ -q`, 35.32s,
from repo root per the known import-path rule). Caveats stated plainly: named scenarios
are calendar-anchored (oracle rows bound placement risk); drags are small because margin
sensitivity is 2.38bps/day per 100% of rate at gross 1.6; and the blend ladder shows the
gear lowers SR_d — kept because the goal metric is ann.

ROUND 3 DONE

## ROUND 4 (coordinator standup 2026-09-07 17:2x CST) — productize the R3 ladder: campaign/bt/financing_stress.py
Pre-flight per charter: GATES_CONTRACT.md read FIRST; DEAD_IDEAS.csv read FIRST — now **119 data rows** (charter said 108; grew via concurrent hunts 09-07/09-08). No dead family re-tested: this round touches ZERO signal families — it packages already-adopted cost-model infrastructure (R3's scenario ladder) into a fleet tool. The only adjacent dead rows (champion-blend-as-sleeve HUNT_VOL2-R3; sector composites HUNT_SECTOR2-R3) are candidate sleeves, not tooling; untouched.

### State found on arrival (honesty)
A prior CAMP_BORROW session (00:13-00:37 tonight) had already drafted bt/financing_stress.py + tests/test_financing_stress.py + work_r4 JSONs — all UNTRACKED, no FINDINGS entry, session died before finishing. Audit showed the job was incomplete: **TDD RED state was live**.

### TDD RED (confirmed before any fix)
`python3 -m pytest campaign/bt/tests/test_financing_stress.py -q` → **2 failed, 29 passed**:
 1. test_cli_fail_closed_nonzero_exit_on_missing_file — `NameError: name 'sys' is not defined` at financing_stress.py:316/320 (the `__main__` block calls sys.exit; module never imports sys). The CLI was fail-OPEN in effect: even SUCCESS exited via the crashing traceback (nonzero), and the error path printed a NameError instead of the real message.
 2. test_cli_emits_json_table_for_a_net_csv — after fix 1, `TypeError: stress_table() got an unexpected keyword argument 'rungs'`: the CLI's `--rungs` flag was dead plumbing; stress_table didn't accept it.

### GREEN (fixes applied)
 - added `import sys` (financing_stress.py:22).
 - `stress_table(..., rungs=DEFAULT_RUNGS)` param added, forwarded to rung_ladder.
 → **31 passed in 2.10s**. Full bt suite: **386 passed, 0 failed** (46.31s; was 290 at R3 close — growth is other agents' R4 files).

### Charter validation pins (all executed, none skipped — `-rs` shows zero skips)
 - **R3 reproduction to 1e-12**: regenerated work_r4/financing_stress_champion_4358dfab95679b97.json through the FIXED CLI, diffed base vs CAMP_BORROW_FINANCING_R3.json base_headline: |d.ann|=2.220e-16, |d.sr_d|=7.105e-15, |d.mdd|=0.0 → max 7.105e-15 **< 1e-12 PASS**. Pin test also re-runs every R3 rate_paths row through the tool at recorded placements (5 scenarios: crash_2008_style_12pct_90d, covid_2020_style_8pct_30d, hike_cycle_6pct_1y, oracle_worst_window, oracle_worst_mdd_window) to 1e-12.
 - **R1/R2 4.5/5.5/6.5% table**: on the pre-costfix stream e6d8b9c0 (ann 39.851%) rungs reproduce 39.851/39.02/38.18% geometric (tol 5e-4), geometric slope **-0.84/-0.83pp per +1pp (tol 0.02)**, arithmetic slope EXACTLY **-0.60pp/+1pp** (gross-1=0.6); SR 3.296→3.180, MDD -6.84→-6.86%.
 - **Fail-closed**: 10-way parametrized (None/empty/misaligned/NaN/nonpositive-gross/bare-ndarray/None-base_rate/negative-rung/base-not-in-rungs) all raise; CLI exits nonzero on missing --net file with the filename on stderr.

### Tool output on the committed champion (sha256[:16] re-verified = 4358dfab95679b97)
base: **ann 37.1954% / SR_d 3.1810 / MDD -6.6922% / 0 neg yrs / worst yr +7.31%** (headline exact).
Call-rate rungs (per-rung totals: margin_drag 2.70→3.90%/yr):
| rate | dAnn pp | dSR_d | MDD % | gate_moves |
|------|---------|-------|-------|-----------|
| 4.5% | 0.0 | 0.0 | -6.6922 | False |
| 5.5% | -0.8197 | -0.0594 | -6.7012 | False |
| 6.5% | -1.6345 | -0.1188 | -6.7103 | False |
| 8.0% | -2.8477 | -0.2079 | -6.7238 | False |
No gate moves anywhere (goal line MDD>-7%, 0 neg yrs holds to 8% call rate).
Borrow tiers on committed book: 2% MEDIUM → **+1.545 bps/yr** (ann 37.1742%), 8% HARD → **+7.725 bps/yr** (ann 37.090%); both gate_moves=False — R1's conclusion stands: borrow tier risk is two orders of magnitude below call-rate risk on this book.
Honest caveat preserved: -0.84pp/+1pp geometric belongs to the PRE-costfix stream; the committed 4358dfab book's geometric slope is -0.8197pp/+1pp (costfix lowered both level and slope slightly). The tool pins each to its correct stream.

### Fleet usage
`PYTHONPATH=campaign python3 -m bt.financing_stress --net <net.csv> --gear 1.6 --base-rate 0.045 --rungs 0.045,0.055,0.065,0.08 --json out.json` (JSON written only on success; any error → traceback + exit 2). Library API: stress_net / rung_ladder / path_scenarios / borrow_tier_block / stress_table.

### Verdict
Charter items all satisfied: reusable tool (1), TDD with demonstrated RED→GREEN on two real defects (2), 1e-12 R3 reproduction + R1 -0.84pp table reproduction (3), fail-closed (4). Files: bt/financing_stress.py, bt/tests/test_financing_stress.py, work_r4/financing_stress_champion_4358dfab95679b97.json (regenerated post-fix). No champion or builder changes; untracked-then-owned files only.

ROUND 4 DONE

## ROUND 5 (coordinator standup 2026-09-08 04:0x CST) — freshness audit of the financing stack vs published rates
Pre-flight: GATES_CONTRACT_V2.md read FIRST (RATIFIED 2026-09-08 03:1x; V1 gates 1-5 unchanged; §6 Step-1 leak rule noted — no submission this round, evidence-only audit). DEAD_IDEAS.csv recounted myself: **130 data rows** (charter said 120; dynamic by design per V2 preamble). Zero signal families touched — pure cost-model audit, so no dead-family re-test and no p-hacking surface exists. bt/ left untouched (quiet-tree rule honored; the `M` entries under campaign/bt/ are AUDIT_FWBUGS' pre-existing edits per V2 §12, not mine). No champion edits.

### State found on arrival (honesty)
A dead prior CAMP_BORROW session (07:00-08:08 today) had left work_r5/ artifacts (freshness script, short census, two ladder JSONs, fresh FRED fetches) with NO FINDINGS entry. I audited then re-executed everything fresh rather than trusting it: both scripts exit 0 with all fail-closed asserts green; the dead session's published-rate ladder JSON regenerates through `bt.financing_stress` CLI to **max|dev| = 0.0** over 6 rungs x {ann, sr_d, mdd}; my independent drift script reproduces the same rung numbers (5.13% rung ann 36.6784% both ways). FRED fetches confirmed fresh (DFF n=26,363 through 2026-09-03; SOFR n=2,198).

### (a) Freshness re-derivation — PASS (all fresh command runs this round)
- Book of record re-verified: champion sha256[:16] **4358dfab95679b97**; independent builder rebuild max|dev| **9.996e-17** (n=4805, 2008-03-31..2026-08-27).
- **Margin re-derived exactly: 2.700000%/yr = 1.0714 bps/day** on max(gross-1,0)=0.6 at 4.5%/252; np.unique on the daily margin stream = a single distinct value; gross_exact ok=True max|gross-1.6| = **1.110e-15**, 0 days beyond the 1e-9 gate.
- Committed file priced at EXACTLY 4.5%: priced-at-rate residual **1.00e-16** at 4.5% vs 2.38e-05 (5.5%) and 4.76e-05 (6.5%) — the champion carries no stale-rate pricing.
- **Slot gross-share census (fresh)**: brwt10 22.95%, brwt7 19.96%, brwt5 16.97%, brwt15 13.23%, C5ng 8.80%, C5ngsum 6.81%, dualmom 2.67%, QAxasts 2.34%, A5r2 1.78%, diescrack 1.77%, a6r7 1.54%, carryv2 1.19%, CFX4 0.00% (sums 100.0).

### Borrow: which sleeves actually carry short legs (measured, not asserted)
- **C1: ZERO of the 13 champion slots have a negative weight on any of the 4,805 days** — total mean short notional at slot level = 0.000000 of NAV. All shorts live INSIDE sleeve net files; those books are futures/ETF/spot proxies where stock loan does not apply (financing already covered by the (gross-1) call-rate term).
- **C2: the only embedded stock-loan borrow is diescrack** — the committed file embeds EXACTLY -0.005/252 per day on **733 of 4,605** champion-window rows (331 short-leg, 173 long-leg, 229 cost-only — the meta discloses long/cost-only charging as a conservative overcharge); borrow-free reconstruction agrees to <1e-9 on every charged row.
- **C3 champion-level: embedded borrow drag = 0.2195 bps/yr.** HTB tiers through actual champion weights: 2% MEDIUM → **0.6586 bps/yr** (dAnn -0.00659pp), 8% HARD → **3.2931 bps/yr** (dAnn -0.03293pp). Immaterial; no gate moves.
- **C4: CFX4 (the other borrow-declaring sleeve) carries weight exactly 0.0 on all 4,805 days** — relw = max(IS_SR,0)^0.55 = 0 because its data starts 2019-09, after IS_END 2017-01-01. Its declared borrow never touches the champion.

### (b) Drift flags vs published benchmarks — 4 computed, ALL 4 exceed the 10% relative bar → FLAGGED
Benchmarks fetched fresh from FRED (IBKR prices Pro margin loans at Benchmark + spread; BM = DFF/SOFR): **DFF 3.63% (2026-09-03)**, **SOFR 3.66% (2026-09-03)**. R1's on-record rationale: 4.5% ~= fed funds + ~1.5-2pp spread.

| flag | modeled | implied (published) | rel drift | abs |
|---|---|---|---|---|
| call vs DFF+1.5pp | 4.50% | 5.13% | **+14.00%** | +0.63pp |
| call vs DFF+2.0pp | 4.50% | 5.63% | **+25.11%** | +1.13pp |
| call vs SOFR+1.5pp | 4.50% | 5.16% | **+14.67%** | +0.66pp |
| margin drag vs TRUE DFF+1.5pp path | 2.70%/yr | 1.76%/yr (path mean 2.93%+1.5pp) | **-34.86%** | -0.94pp |

Champion impact (only the margin term re-priced; everything else untouched):
| scenario | call rate | ann | dAnn | SR_d | MDD | neg yrs |
|---|---|---|---|---|---|---|
| base (committed) | 4.50% | 37.1954% | — | 3.1810 | -6.6922% | 0/19 |
| flat DFF+1.5pp | 5.13% | 36.6784% | -0.517pp | 3.1436 | -6.6979% | 0/19 |
| flat DFF+2.0pp | 5.63% | 36.2695% | -0.926pp | 3.1139 | -6.7024% | 0/19 |
| flat SOFR+1.5pp | 5.16% | 36.6538% | -0.542pp | 3.1418 | -6.6982% | 0/19 |
| TRUE DFF+1.5pp path (elementwise, history honored) | mean 2.93+1.5 | 38.4910% | **+1.296pp** | 3.2741 | -6.6824% | 0/19 |

Reading, stated honestly both directions: (i) vs TODAY's BM+spread the modeled 4.5% is CONSERVATIVE — a live IBKR client at DFF+1.5pp pays 5.13% and the current-environment ann is ~36.68% (-0.52pp), i.e. the committed headline overstates today's-realizable ann by ~0.5pp (0.9pp at the spread cap). (ii) Over the FULL 2008-2026 backtest window the elementwise rate PATH averages only 2.93%+1.5pp, so the flat-4.5% convention UNDERSTATES the period ann by +1.30pp — the flat convention is not drift-neutral in time, and both directions are now measured. **No gate moves in any scenario: 0 negative years everywhere; MDD never worse than -6.7024% (goal line -7%).** Borrow-side: even a 100% relative borrow-rate move (0.5->1.0%) moves the champion exactly 0.2196 bps/yr — borrow is immaterial by three orders of magnitude vs call rate on this book.

Citation limitation (flagged, not papered over): IBKR's own published margin/borrow pages were unreachable this round — curl exit 7 direct AND with --noproxy (interactivebrokers.com, www1, .hk mirrors; .co.uk 404), WebFetch domain-verification blocked, webReader 500. The benchmark leg is therefore cited from FRED (authoritative for IBKR's BM index), and the 1.5-2pp spread band is carried from R1's recorded rationale — the IBKR-specific published spread table and stock-borrow schedule were NOT re-verified against the live source this round. Replay path: any session with IBKR reachability can re-run work_r5/r5_drift_flag.py after swapping the spread band for the published breakpoints.

### Verdict
Charter (a): margin 2.70%/yr re-derived exactly (residual 1e-16 vs committed; single distinct daily margin value); borrow exposure measured at the slot level (zero shorts on all 4,805 days), the embedded leg level (diescrack 733 rows to 1e-9), and the champion level (0.2195 bps/yr; HTB 8% tier 3.2931 bps/yr). Charter (b): all four drift flags exceed 10% relative and are FLAGGED with exact citations + champion-impact table. Deliverables (all in work_r5/): r5_freshness_audit.py, r5_short_census.py (re-executed fresh), r5_drift_flag.py (new this session), r5_drift_flags.json, r5_published_rate_ladder.json + _regen.json (reproduced to 0.0), fred_dff.csv/fred_sofr.csv (fresh fetches). bt suite: **401 passed, 0 failed** (59.16s, from repo root). No new signals, no champion edits, no bt/ edits.

ROUND 5 DONE

## ROUND 6 (coordinator standup 2026-09-08 11:5x CST) — (a) financing-convention disclosure (docs-only) + (b) fraud-catch on DATA_FREDMORE R5
Pre-flight: GATES_CONTRACT_V2.md read FIRST (in force; pass sig= and leak_check=True explicitly — no submission this round, docs + evidence only). DEAD_IDEAS.csv recounted myself at round start: **142 data rows** (charter quoted 137; dynamic per V2 preamble — a concurrent HUNT_CREDIT2-R6 curation append took it to 143 mid-round, 0 duplicate idea texts). Champion of record re-hashed this round: sha256[:16] **4358dfab95679b97 — UNCHANGED**. bt suite from repo root: **410 passed / 0 failed** (57.64s) — matches the coordinator's 11:4x count. bt/ untouched (quiet-tree rule), results/ untouched, no champion edits.

### (a) FINANCING CONVENTION DISCLOSURE appended — DONE (docs-only, additive)
Appended '## FINANCING CONVENTION DISCLOSURE (2026-09-08)' to campaign/GOAL100_CHAMPION.md: the 4 R5 rate-drift flags with exact numbers (call 4.50 vs DFF+1.5pp 5.13 = +14.00% rel / +0.63pp; vs DFF+2.0pp 5.63 = +25.11% / +1.13pp; vs SOFR+1.5pp 5.16 = +14.67% / +0.66pp; margin drag 2.70 vs TRUE DFF+1.5pp-path 1.76%/yr = -34.86% / -0.94pp), the both-directions reading (vs TODAY's benchmark+spread the flat 4.5% is CONSERVATIVE — current-environment ann ~36.68% (-0.52pp), i.e. the 37.195% headline overstates today-realizable by ~0.5-0.9pp; over the FULL 2008-2026 window the flat convention UNDERSTATES by +1.30pp since the elementwise path mean is 2.93%+1.5pp), champion-impact rows (0/19 neg years in every scenario, MDD never worse than -6.7024%), and the borrow-immateriality line (0.5->1.0%/yr borrow = 0.2196 bps/yr champion impact). Insert-only verified: file grew 23,489 -> 25,919 chars, diff is +77 lines total of which my append is the last 40; the 37 pre-existing diff lines are the coordinator's own banners (not mine). No results/ or bt/ file touched.

### (b) Fraud-catch on DATA_FREDMORE's R5 verdicts — VERDICTS CONFIRMED, 37/37 checks pass, ONE live incident caught
Reproduced with MY OWN code (work_r6/r6_fredmore_fraudcatch.py; imports only their shipped alfred_dl public API, never their verifier) from published artifacts + LIVE FRED/ALFRED re-pulls:
- Level lint V1 (9 checks): DRALACBS n=166 1985-01-01..2026-04-01, DRCLACBS n=158 1987-01-01..2026-04-01, WPU05320104 n=511 1984-01-01..2026-07-01 — counts/spans/gap-lint/ordering/no-NaN all exact to their claims.
- Live equality V2 (3): all 3 delivered CSVs byte-value-equal to a fresh api.stlouisfed.org re-pull (n=166/158/511), delivered end == live max obs.
- Vintage V3 (15): rebuilt first-release vintages LIVE: n=61/61/136, lag_min 136/136/37 >= floors 130/130/35 (lag_max 166/166/105), ordered, post-birth coverage holes == {} / {} / {2015-10-01} exactly (the documented suppressed-at-first-release obs).
- WPU census V4 (5): their saved wpu_full_history.json re-derived independently — 587 obs; the 3 structure events re-found as ABSENT monthly grid slots (exactly 1983-04/08/12 — the '.' values never entered their artifact, so my derivation is independent of their hard-coded dot dates); 9 swings >=30% with first 1990-01 +95.8%; none coincide; interlude continuous within 30% -> refuse=False.
- Ledger V5 (4): both DATA_FREDMORE-R5 rows present, data-acquired, series named; ledger count sane (>=142, zero dup idea texts).
**Verdict: NO FRAUD. Every published R5 number reproduces exactly; 37 PASS / 0 FAIL, exit 0** (r6_fredmore_repro_output.txt + r6_fredmore_repro_scorecard.json in my work_r6). My script's 3 initial failures were MY bugs (naive full-span hole diff vs their post-birth semantics; wrong artifact JSON shape; an over-strict DEAD_IDEAS count pin against a dynamic ledger), not theirs — each fixed with their stated convention located in their code.

### LIVE INCIDENT: concurrent DATA_ORGANIZE team agent destroyed the R5 vintage artifacts (uncommitted tree mutation, caught 14:1x 2026-09-08)
- FREDMORE's own verifier (work_r5/verify_round5.py) **PASSED 64/0 at 09:04 today** (their saved output) but when I re-ran it as-is at ~14:2x it now **FAILS: exit 1, 'FAIL vintage:DRALACBS exists' then FileNotFoundError on tools/quant/data/alfred/DRALACBS/vintage.csv**. All three tools/quant/data/alfred/<SID>/vintage.csv files (61/61/136 rows) are GONE tree-wide and were NEVER git-tracked (git ls-files: empty; no git history at those paths).
- Attribution: campaign/team DATA_ORGANIZE session started 13:44:52; organize_lib.cpython-314.pyc compiled 14:10:10; tools/quant/data/alfred/ dir mtime = 14:10:22 (subdir removal stamps parent); more_fred manifest+README rewritten 14:10:24; README.md says 'Generated: 2026-09-08' matching organize_lib.write_readme. The same session's write_manifest('alfred') truncated alfred/manifest.csv to **0 bytes** (empty-glob crash mid-write: file opened/truncated BEFORE rows[0] IndexError — organize_lib.py had no self-exclusion at that time; a concurrent patch has since fixed the glob). more_fred/manifest.csv was likewise REGENERATED and LOST 6 rows: FREDMORE's verifier pinned 'manifest: 166 rows total (160+6) incl. 6 R5 rows with lag_days floors + ALFRED:SID vintage rows'; the current regenerated file has 145 lines with ZERO ALFRED rows and no lag-floor fields (flat 6-col schema). DATA_ORGANIZE's own charter says 'Do not delete any CSV' and their session has NO FINDINGS.md / no 'DATA_ORGANIZE DONE' marker — an incomplete, unwitnessed destructive pass.
- Impact: V1 item 4 (save-per-contract artifacts) + V2 §10a broken for the R5 delivery; FREDMORE's repro chain is dead until restored. No champion/bt impact (sha verified unchanged; suite 410/0).
- Remediation delivered THIS ROUND: my V3 checks rebuilt all three first-release vintages from LIVE ALFRED (birth-anchored; n=61/61/136, lags verified) into **campaign/agents/chief/coord/CAMP_BORROW/work_r6/vintage_rebuilt/{DRALACBS,DRCLACBS,WPU05320104}/vintage.csv** (their exact CSV format via alfred_dl.write_vintage_csv). Restore = move those into tools/quant/data/alfred/<SID>/ (not done by me: tools/ is outside my charter) and regenerate the 6 lost manifest rows. FREDMORE's verifier should then go back to 64/0 — the only other diffs would be their manifest-count pin (166 vs the regenerated 145) which is a DATA_ORGANIZE-caused stale pin, not a FREDMORE honesty issue.
- Escalation for the coordinator: (1) restore/track the vintage files (data dirs are untracked blobs — at minimum record the sha256 inventory DATA_ORGANIZE's charter demanded and never saw); (2) the DATA_ORGANIZE layout test only allows RESERVED raw subdir names, and DRALACBS/-style PIT vintage subdirs are NOT in that list — that two-way fail-closed test is the mechanism that will re-flag these dirs as illegal; either reserve a '_pit' class or move vintages under an agreed reserved dir; (3) write_manifest must not truncate-then-crash (write to temp + atomic rename), and a fail-closed guard should refuse to regenerate a manifest that currently references artifacts (lag floors, vintage rows) the flat schema cannot express.

### Verdict
Charter (a) DONE (docs-only disclosure appended to GOAL100_CHAMPION.md, insert-only). Charter (b) DONE: FREDMORE R5 verdicts CONFIRMED 37/0 from published artifacts + live sources with own code — no fraud; but the fraud-catch surfaced a REAL concurrent-session artifact destruction (R5 vintage CSVs + 6 manifest rows) with attribution evidence and a delivered live-ALFRED remediation path. New files this round (all in my coord/CAMP_BORROW/work_r6/): r6_fredmore_fraudcatch.py, r6_fredmore_repro_output.txt, r6_fredmore_repro_scorecard.json, vintage_rebuilt/{DRALACBS,DRCLACBS,WPU05320104}/vintage.csv. Plus campaign/GOAL100_CHAMPION.md (charter-named docs append). No bt/ edits, no results/ edits, no champion edits.

ROUND 6 DONE


## ROUND 7 (coordinator standup 2026-09-08 18:3x CST) — (a) fraud-catch re-run of FXCARRY2-R6 treasfut repro + (b) borrow lane: drift flags re-measured, 0.2195 bps/yr re-pinned

Pre-flight: GATES_CONTRACT_V2.md opened and read this session (Step-2 leak flip EXECUTED,
commit 539f50e, leak_check default-ON; VOL2's V3 per-class placebo NOT yet in the contract —
AUDIT_GATES2 tail still "ROUND 6 DONE", so treated strictly as PROPOSAL, not depended on; no
submission this round, evidence-only audit so no gates.run call needed). DEAD_IDEAS.csv
recounted MYSELF at round start: **151 data rows** (charter quoted 145-146 at R6-end; CAMP_SHORT-R7's
row was #151; ledger at my append = **152 rows**, dynamic per V2 preamble — see concurrent-writer
note below). Champion of record re-hashed this round: sha256[:16] **4358dfab95679b97 UNCHANGED**;
builder-vs-committed max dev 9.996e-17; base headline re-derived ann 37.1954% / SR_d 3.1810 /
MDD -6.6922% / 0 neg years (assert-locked in my script). bt suite from repo root: **444 passed /
0 failed** (88.50s; coordinator's R6-close count was 426 — fleet grew it, none mine).

### State found on arrival (honesty)
A dead prior CAMP_BORROW session (21:28-21:40 tonight) had left work_r7/ artifacts with NO
FINDINGS entry (same pattern as R5). I audited rather than trusted, then re-executed fresh:
(1) its drift re-measure script has a REAL DEFECT — it derives charged borrow rows from
`positions != 0`, which counts only 331+173=504 rows and silently drops the 229 meta-disclosed
cost-only rows (would under-pin the borrow drag at ~0.15 bps/yr); my own script uses the
borrow-free-recon + exact -0.005/252 signature method (R5 C2/C3 convention) and is what
produced the pinned numbers below; the defective script is quarantined as
`r7_drift_flag_remeasure.py.SUPERSEDED_DEFECTIVE` and its JSON was overwritten by mine.
(2) its treasfut fraudcatch (258/8 self-count) is superseded by my bit-exact rerun below
(`r7_treasfut_fraudcatch*.{py,json}.DEAD_SESSION_SUPERSEDED`); its ledger conclusion (row 142
present, pickaxe 0) agrees with mine.

### (a) Re-run of HUNT_FXCARRY2-R6 `r6_treasfut_repro_scorecard.json` path — REPRODUCED BIT-FOR-BIT, ZERO FRAUD
Method: copied their shipped `work_r6/fxc2_r6_treasfut_repro.py` into my work_r7/treasfut_a/
with EXACTLY two edits — OUT redirected to my dir (their published scorecard untouched: mtime
13:19, sha16 ffad4b6c6756e5d7) + an input-pin note — and re-ran end-to-end (exit 0).
- **All 19 books x every cell: max |diff| = 0.0 exactly** vs their published scorecard
  (devA_vs_pub ~1e-16 on 15 primary books; dev_pos_vs_pub 0.0; 19/19 meta net_sr cells match
  the double-net rebuild <5e-5; every drift field identical to the last float).
- **DEFECT-#1 reconfirmed**: honest vs double book spread identical to theirs (POST5_5 +0.216
  honest vs -0.325 double = the sign flip; POST5_30 0.441 vs 0.468). Verdict cells: 0/19
  honest SR >= 1.0, max honest SR 0.4407, 0/19 beats spy_bh 0.5171 matched-span — family DEAD
  on the honest convention exactly as they concluded.
- **DEFECT-#2 reconfirmed 4/4**: POST3_10_long/COND3_10/POST10_10_long/COND10_10 published CSVs
  byte-identical to their k=5 siblings (metas record k=5); my honest rebuild of those books
  diverges (dev 5.6e-2/6.5e-2, dev_pos 3.0 = the k delta) — published plateau CSVs are k=5
  copies, exactly as they reported. Plateau FAIL verdict correct either way.
- **DEFECT-#3 (missing TREASFUT-R5 ledger row) — RESOLVED, remediation VERIFIED**: the row now
  EXISTS as data row 142 (status dead, source HUNT_TREASFUT-R5), re-appended by the coordinator
  and disclosing both the loss (RES_BASIS section-4 repair clobber) and FXCARRY2's honest-SR
  correction (0.441 alongside the published 0.468). Absence re-confirmed from every reachable
  historical state myself: HEAD commit (64 data rows) = 0 hits, git pickaxe -S over all history
  = 0 commits, bak_standup1300 (143 rows, 09-08 12:57) = 0 hits. Current = 3 hits (the row +
  FXCARRY2-R6 + CAMP_SHORT-R6 curation rows referencing it).
- **NEW nit #1 (their side, disclosed)**: the SHIPPED script revision (mtime 14:29, AFTER its
  13:19 scorecard) CRASHES in section C as-is — it reads drift_table_DGS*_k5.csv with
  `parse_dates=["date"]` but those CSVs index on `auction_date` — so the shipped copy cannot
  regenerate its own scorecard unmodified; my one-line patch (auction_date + to_datetime)
  completed the run. The published numbers themselves are sound (bit-exact above).
- **NEW nit #2 (data hygiene)**: tauctions.csv was REFRESHED 09-08 14:07 (sha16 b0e243c4e4681e32
  -> c83d7a984fed0e73, DATA_ORGANIZE-window mtimes), after their 13:19 run. Proven
  CONTENT-NEUTRAL for the consumed columns: my rerun under the refreshed file still reproduces
  their scorecard bit-for-bit (15/15 books byte-exact at 1e-16); row count unchanged (7857);
  cross-check vs TREASFUT's own 06:35 probe file = 0 value diffs on all 29 overlapping
  bid-to-cover dates. BUT no frozen copy of the pinned bytes b0e243c4e4681e32 exists anywhere
  in the tree, so future fail-closed pin re-checks (like their data_pins block) can no longer
  pass — flagging for the coordinator's artifact-preservation lane.

### (b) Borrow lane — 4 drift flags re-measured vs CURRENT curves: ALL 4 STILL FLAGGED; borrow pin EXACT
Benchmarks fetched fresh THIS round (fredgraph.csv): **DFF 3.63% as of 2026-09-03 (n=26363,
unchanged)**; **SOFR 3.65% as of 2026-09-04 (n=2199 — ONE new print since R5, was 3.66% 09-03)**.
Champion margin engine re-verified first: builder==committed 9.996e-17; strip/re-add reprice at
4.5% reproduces the committed headline exactly (assert-locked).

| flag | modeled | implied (current) | rel drift | R5 rel | status |
|---|---|---|---|---|---|
| call vs DFF+1.5pp | 4.50% | 5.13% | **+14.00%** | +14.00% | STILL FLAGGED |
| call vs DFF+2.0pp | 4.50% | 5.63% | **+25.11%** | +25.11% | STILL FLAGGED |
| call vs SOFR+1.5pp | 4.50% | 5.15% | **+14.44%** | +14.67% | STILL FLAGGED |
| margin drag vs TRUE DFF+1.5pp path | 2.70%/yr | 1.7589%/yr | **-34.86%** | -34.86% | STILL FLAGGED |

Champion-impact re-price (margin term only; R5 elementwise convention): flat 5.13% -> ann
36.6784% (dAnn -0.517pp), flat 5.63% -> 36.2695% (-0.9259pp), flat 5.15% -> 36.6620% (-0.5334pp),
TRUE path (mean 2.9315%+1.5pp) -> 38.4910% (+1.2956pp) — R5 numbers reproduce to the 4th decimal;
the only movement in any cell is the new SOFR print (5.16->5.15). **0 negative years in every
scenario; MDD never worse than -6.7024% (goal line -7%).** Both-directions reading UNCHANGED:
flat 4.5% remains conservative vs today's BM+spread (~0.5-0.9pp understated today-cost) and
history-dominated over the full window (+1.30pp path-mean overstatement of period ann).
**NEW this round — 12-month tail re-price**: margin re-priced at DFF+1.5pp on 2025-08-27..
2026-08-27 only (path mean 5.2581%): ann 31.4175% vs base 32.0160% = **dAnn -0.5985pp** — i.e.
in the CURRENT rate environment the conservative-flag direction is the live one: the committed
book's most recent 12m would have earned ~0.6pp less at a realistic call rate. Flags stay OPEN
until either the convention is re-based to BM+spread or IBKR's published table is reachable.

**Borrow re-pin: 0.2195 bps/yr reproduced EXACTLY (drift vs R5 pin = 0.0)** — my independent
re-execution of the C2/C3 chain on the current tree: borrow-free recon (DJFUELUSGULF/42 x WTI
log spread, zrev L40 gate 2.0, VT8%) vs committed diescrack file -> 733 charged rows of the
EXACT -0.005/252 signature (max dev 9.999e-17), split 331 short / 173 long / 229 cost-only;
champion-weight drag 0.2195 bps/yr; HTB tiers through actual champion weights: 2% MEDIUM =
0.6586 bps/yr, 8% HARD = 3.2931 bps/yr (all R5-exact, assert-locked). C1 re-certified: 0
negative weights across 13 slots x 4,805 days (total mean short notional 0.000000 of NAV).
All asserts green, exit 0 (r7_drift_remeasure.py; r5_short_census.py ALSO re-executed fresh
this round, exit 0, same numbers). Borrow remains immaterial by three orders of magnitude vs
call rate on this book — unchanged conclusion.

### Concurrent-writer ledger note (R7 append, self-caught defect)
My first append attempt used csv.writer's default CRLF terminator plus a conditional extra
newline: the row LANDED (as row 152) but left a blank line and CRLF tail. My guarded re-append
script then fail-closed on the count (152+1 blank = 153 -> "expected 151") and on the duplicate
check — the guards worked as designed, no concurrent writer was involved. Repaired my own
artifact only: blank line dropped, my row's CRLF -> LF (file convention); final state verified
**152 data rows, 0 blank rows, trailing LF, CAMP_BORROW-R7 row exactly 1x** (last-3 srcs
HUNT_TREASFUT-R7 / CAMP_SHORT-R7 / CAMP_BORROW-R7). Append script retained at
work_r7/r7_ledger_append.py in its now-idempotent (refuses-duplicate) form.

### Verdict
Charter (a) DONE: their published scorecard regenerated bit-for-bit (max |diff| 0.0 across all
19x-cells + drift), DEFECT-#1/2 reconfirmed, DEFECT-#3 RESOLVED-and-verified, 2 new nits
disclosed with evidence. Charter (b) DONE: 4/4 drift flags re-measured against fresh FRED
(DFF 3.63 09-03, SOFR 3.65 09-04) and ALL STILL FLAGGED (+14.00/+25.11/+14.44/-34.86% rel);
embedded borrow re-pinned EXACT at 0.2195 bps/yr (733 rows, 331/173/229); HTB 0.6586/3.2931
bps/yr; slot census 0 shorts re-certified; NEW 12m-tail read (-0.5985pp at today's path mean
5.2581%). DATA_ORGANIZE remediation path: NOT implemented by me per charter (assigned to
DATA_FREDMORE/DATA_ETF_MORE; landing verified NEXT round). New files, all in my
coord/CAMP_BORROW/work_r7/: treasfut_a/{r7_treasfut_repro_rerun.py, rerun_output.txt,
r6_treasfut_repro_scorecard.json (regenerated)}, r7_drift_remeasure.py, r7_drift_flags.json,
fred_dff_r7_fresh.csv, fred_sofr_r7_fresh.csv, r7_ledger_append.py; two dead-session artifacts
quarantined with .SUPERSEDED suffixes; one curation row appended to DEAD_IDEAS.csv (152nd data
row). No bt/ edits, no champion edits, their published artifacts untouched.

ROUND 7 DONE
