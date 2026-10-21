# AUDIT_RECON — FINDINGS

## ROUND 2 (2026-09-07 04:1x) — audit of the RE-EMITTED causal champion
Target: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv (committed 8f98da1, 2026-09-07 00:45,
causal nav.shift(1) re-emit). All work scripts in AUDIT_RECON/work/. Run from repo root.

### (a) Full blotter reconciliation — ALL 8 CHECKS PASS (r2_blotter_recon.py, exit 0)
- Byte-repro precheck: `rawew13v2_build.py --verify` → n=4805 both, max|new-old|=9.996e-17
  IDENTICAL; weights max dev 2.220e-16 IDENTICAL.
- A1 cost per-day == FULL |dW| x 6.4bp: max dev 9.999e-17. Charged 94.1899 bp-sum over 4805
  days = mean 0.019602 bp/day → **4.9398 bp/yr** (charter expected ~4.94 — matches exactly).
- A2 margin per-day == 4.5%*(1.6-1)/252 = 1.07142857e-04: max dev 9.998e-17, csv-implied
  daily margin has exactly 1 unique value (constant, no drift).
- A3 algebra ret == port − cost − margin: max dev 9.996e-17 (reconciles to float precision).
- A4 no-lookahead perturbation:
  - corr(sum|dW_t|, portret_t) = **+0.2059** (charter: ~0.2 legitimate responsiveness; the
    leak signature was 0.34) — PASS.
  - archived leak mechanism rebuilt for contrast: corr(|dW_t|, r_t)=0.4590, next-day 0.2092
    vs NEW 0.2059/0.0849.
  - **R1's 0.78 leak signature reproduced apples-to-apples**: mean per-day cross-sectional
    corr(dW_i, r_i) = +0.7846 under the unshifted (archived) mechanism vs **−0.0277** under
    the committed causal mechanism (want ~0) — the R1 diagnosis is confirmed on the exact
    archived construction, and the re-emit removed it.
  - Direct causality (strongest evidence): zeroing ALL sleeve returns from day t onward and
    rebuilding the ENTIRE pipeline leaves Wg_t byte-identical at 8 probe days
    (t=0,1,2,100,1200,2400,3600,4804; max dev 0.000e+00) → Wg_t uses returns ≤ t−1 only.
- A5 gross: mean 1.600000000, max 1.600000000000, 0 days > 1.6+1e-9. Day-1 turnover charged
  = 0.0 (no entry-cost charge; uncharged entry leg = 10.24 bp ONE-TIME = 0.00214 bp/yr-equiv
  — immaterial, same convention as before the re-emit).
- Honest headline of committed champion: n=4805 (2008-03-31..2026-08-27) **ann 39.85%,
  SR 3.296, MDD −6.84%, 0/19 neg years**; archived leak file recomputed: ann 40.84%,
  SR 3.339 (−0.99pp honest gap as reported in R1).

### (b) DEAD_IDEAS.csv spot-audit — 3/3 dead verdicts REPRODUCE (r2_deadeas_spot.py, exit 0)
1. COT sw-follow lb=12 (row 64, HUNT_COT2): reproduced **SR=0.287** (ledger 0.287, exact),
   ann 2.484%, halves (−0.14, +0.58), negyr 4, scramble_p 0.652, corr −0.020 → fails
   SR≥1.0/halves≥0.5/yearly. DEAD CONFIRMED.
2. TIPS real-yield reversion DFII10 N=252 th=1.0 (row 61, HUNT_TREASFUT): reproduced
   **SR=−0.11, 13 neg years, worst −26.6%**, H1/H2 −0.12/−0.10, corrChamp 0.039; full 4x3
   re-scan (N{63,126,252,504} x th{0.5,1.0,1.5}) every cell SR in [−0.30, −0.09] — all
   negative. DEAD CONFIRMED.
3. Intl 10y yield-spread carry lag0 (row 63, HUNT_TREASFUT): reproduced **blend SR 0.77,
   ann 1.21%** (ledger 0.77 / 1.2%), corrChamp 0.316 (ledger 0.319–0.328, within 0.003),
   best pair US-JP 0.48 (exact); 9 neg years monthly. Fails SR≥1.0 and |corr|<0.15.
   DEAD CONFIRMED.

### (c) Lineage pin — new-vs-archived diff is the causal mechanism ONLY
Pre-existing untracked R2 test files (from the re-emit/parallel wave) already pin the
lineage; I audited them for vacuity, then added mutation guards:
- campaign/bt/tests/test_audit_recon_lineage.py (6 tests) + test_auditrecon_r2_lineage.py
  (4 tests): both generations byte-reproduce from their own mechanism (<1e-15/1e-14),
  same sleeves/relw/gear/cost/margin (L1), no-shift==archived & shift(1)==re-emitted (L2),
  cross-match negative control — each csv MISmatches the other mechanism by >1e-6 (L3),
  day-1 convention unchanged (L4), honest headline pin 39.85/40.84/−0.99pp. **10/10 PASS.**
- NEW: campaign/bt/tests/test_auditrecon_r2_pin_mutations.py — 5 mutation guards proving
  the pin has teeth (measured deviation of committed csv vs mutated in-memory rebuild):
  baseline 9.996e-17 (reproduces); cost 6.4→7.4bp → dev 5.260e-06 CAUGHT; gear 1.6→1.55 →
  dev 5.717e-03 CAUGHT; one slot relw −1% → dev 9.797e-05 CAUGHT; mechanism swap
  (unshifted) → dev 3.962e-03 CAUGHT. Thresholds calibrated to these measurements (2 RED
  runs fixed first: a `_dev/_rebuild` kwarg typo, and thresholds recalibrated after probing
  measured devs — the slot-mutation threshold 1e-4 would have failed against 9.797e-05).
  **5/5 PASS.**

### Verdict + flags
- The re-emitted champion is HONEST and internally exact: costs/margin/algebra reconcile to
  ~1e-16, weight path is provably causal (truncation-invariant), leak signature gone
  (xsec corr 0.7846 → −0.0277), 4.9398 bp/yr turnover as chartered, ann 39.85% confirmed.
- 3/3 sampled dead ideas reproduce their ledger numbers — DEAD_IDEAS.csv is trustworthy
  (spot-audit level).
- Out-of-scope flag for coordinator: full bt suite currently 139 passed / 7 failed — all 7
  failures are in the UNTRACKED campaign/bt/tests/test_gates_audit_r2.py (another agent's
  in-flight round-2 TDD RED: bt.gates.run() exposes no 'scr_ok' key yet). Not touched by
  AUDIT_RECON; bt/ source unmodified this round.

ROUND 2 DONE

## ROUND 3 (2026-09-07 10:3x CST) — re-emit ACCEPTANCE TOOL built + run; re-emit wave ACCEPTED
Read GATES_CONTRACT.md + DEAD_IDEAS.csv (95 rows incl. header, 68 dead) first; no dead family
re-tested, no dead signal re-tuned. All work scripts/reports in AUDIT_RECON/work/. Run from
campaign/.

### (a) bt/verify_champion.py — ACCEPTANCE TOOL (7 checks, exit 0/1, JSON, fail-closed)
- Scope guard: a round-3 tool file pre-existed UNTRACKED (written today 08:49-09:41, after the
  07:2x charter — an earlier interrupted AUDIT_RECON session; my work/ had no R3 artifacts).
  Treated as untrusted input: audited its algebra line-by-line against
  campaign/scripts/rawew13v2_build.py (relw=max(IS_SR,0)^0.55 on index<2017-01-01;
  nav=(1+r).cumprod().shift(1).fillna(1) row-normalized *relw, Wg sums to gear=1.6; full
  |dW| x 6.4bp with day-1 entry NOT charged; margin (1.6-1)*4.5%/252). Imports only
  numpy/pandas/stdlib — NO engine internals (independence holds). Mtime-snapshotted before/
  after every run: not modified by anyone else mid-round.
- TDD (campaign/bt/tests/test_verify_champion.py, 12 tests, all GREEN in 2.3s): honest
  3-sleeve mini-champion GREEN via API and CLI (exit 0 + JSON file); RED on each injected
  defect — half-turn cost diagnosed model="half_dw", ratio 0.5 (<0.75); same-day weights
  caught by causality (causal_max_dev>tol AND truncation violated); gross 1.7 caught vs the
  1.6 wall (n_over>0); one neg year caught by yearly; fail-closed on missing champion /
  missing sleeve / weights-naming-unknown-sleeve; vacuity guard (honest book implied/full
  cost ratio = 1.0 +/-1e-6, max_dev<1e-12).
- ONE REAL BUG FOUND+FIXED (TDD, RED->GREEN): the loader rejected any non-finite value, but
  NaN is BUILDER-LEGITIMATE (rawew13v2_build.load() dropna()s per series, arithmetic
  fillna(0)s; the real brwt10/brwt7/brwt5 files carry 59 NaNs each). First acceptance run
  fail-closed-blocked on exactly this -> the tool could not accept the real champion. Fix:
  reject only inf; NaN flows through the mirrored arithmetic like the builder. New tests:
  test_nan_in_sleeve_file_is_builder_legitimate (RED first, dev 8.6e-3 before fix),
  test_inf_in_sleeve_file_still_fails_closed. 12/12 PASS after.
- Stale-fixture sync: bt/tests/fixtures/mini_champion/ was emitted 08:49 but its generator
  constants were recalibrated 08:53 (drift x1.0/1.5/2.0 left 2026 neg) — interrupted before
  re-emit; old csv failed yearly/mdd gates under the tool. Regenerated with the committed
  generator (byte-identical, idempotent) and re-accepted: exit 0, 7/7 checks, SR 2.29,
  MDD -5.67%, negyr 0.

### (b) Acceptance runs — 4 production scenarios (work/r3_acceptance_driver.py, exit 0)
S1 CURRENT worktree champion (results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv,
    re-emitted today 07:28) + weights + 13 sleeves: **exit 0, ACCEPTED, 7/7 checks** —
    weights_repro 2.2e-16 (<1e-9; is_end 2017-01-01 correctly INFERRED from the grid),
    byte_repro 1.08e-16 (<1e-12), cost_reconciliation model=full_dw max_dev 1.08e-16,
    implied/full ratio 1.0000000000, bp/yr 4.9615 (R2: 4.9398 on the pre-costfix book —
    the +0.022bp/yr is the CAMP_COST costfix landing), day-1 entry charged 4.6e-13 (~0),
    causality mechanism=nav.shift(1) causal_max_dev 1.08e-16 vs sameday dev 4.04e-3,
    truncation-invariance 0.0 at 7 probes (t=0,1,2,1201,2402,3603,4804), gross max
    1.6000000000006 (0 days over; margin implied 2.70000000%/yr = expected 2.7),
    neg_years 0 (worst year +8.34%), MDD -6.789% (> -7% limit).
    Stats: n=4805 2008-03-31..2026-08-27, ann CAGR 39.69%, SR 3.289, MDD -6.79%.
S2 ARCHIVED same-day-leak champion vs current sleeves: **exit 1, REJECTED** — mechanism
    diagnosed same_day (causal_dev 4.4e-3 > sameday_dev 1.0e-3), truncation violated
    (max_dev 3.13e-3), byte_repro 4.44e-3. The tool has teeth on the exact R1 leak.
S3 HEAD-committed champion (8f98da1) + HEAD weights + HEAD sleeves (all extracted from git,
    its own vintage): **exit 0, ACCEPTED 7/7** — ann 39.85%, SR 3.296, MDD -6.84%. The R2-
    audited triple was internally exact too.
S4 HEAD champion vs CURRENT sleeves (vintage mismatch): **exit 1, REJECTED** — weights_repro
    max_dev 4.01e-2 (relw drift), byte_repro 8.8e-4. A champion verifies ONLY against its own
    sleeve vintage — coordinator should run the tool post-commit, where it reduces to S1.
- COSTFIX-DELTA documented: worktree champion 39.69% vs HEAD 39.85% vs leak 40.84%.
  The -0.16pp HEAD->current delta decomposes as data-refresh (4 sleeve inputs refreshed
  today 06:10-07:03 by other agents) + CAMP_COST costfix: the 4 slots whose relw moved
  (brwt15 -2.36%, QAxasts -0.78%, dualmom -0.51%, diescrack -3.38%) are EXACTLY the four
  CAMP_COST R2 COSTFIX slots; 421/4805 days move >1bp, cumulative-simple -2.3bp. Same causal
  mechanism (S1/S3 both truncate at 0.0); honesty IMPROVES (turnover cost charged rises
  4.9398 -> 4.9615 bp/yr).

### Full-suite regression + out-of-scope flags (coordinator items, none mine)
- bt/run_tests.sh: 234 passed / 15 failed. All 15 in OTHER agents' files:
  test_beats_passive.py x12 (module exists but every test asserts — in-flight RED, files
  08:22-08:26); test_audit_champ2_round3.py x2 (09:23, in-flight); test_camp_cost_r2.py x1
  (import bug: `import campaign.scripts.rawew13v2_build` with sys.path=campaign/ ->
  ModuleNotFoundError; and the assertion would fail anyway: brwt10/7/5 remain un-rebuilt
  half-turn sleeves — pre-existing CAMP_COST gate RED, consistent with its FINDINGS note).
- bt/ source unmodified by me except the tool file itself; no other agent's directory or the
  committed champion touched. Worktree champion/weights/sleeves are MODIFIED vs HEAD (the
  re-emit wave's own output) — that is the state the coordinator will commit; my acceptance
  (S1) applies to it as-is.

ROUND 3 DONE


## ROUND 4 (2026-09-08 01:4x CST) — champion-bytes integrity report for the R4 wave
Read GATES_CONTRACT.md + DEAD_IDEAS.csv FIRST. DEAD_IDEAS is now 120 rows incl. header
(119 data rows; charter said 108 — it grew via coordinator edits 2026-09-07 23:12, noted,
not a champion-byte issue). No dead family re-tested; no dead signal re-tuned. Round ran
01:41-01:46 concurrent with coordinator edits (banner, cmd.sh, fleet_keeper.py plan()).
Scope per charter: the CHAMPION BYTES ONLY. Work in AUDIT_RECON/work/r4/
(t0_snapshot.txt, t0.json, r4_acceptance.json, t1.json). Repo root is /Users/daxu (a git
repo whose tree contains software/world-trader/) — git show paths must be
software/world-trader/campaign/... (first attempt used campaign/... and silently hashed
the empty string; corrected).

### (1) T0 byte snapshot 2026-09-08 01:41:20, HEAD=5638a19 — 22 files sha256'd
- champion GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv:
  **sha256 4358dfab95679b975e4867f9ace806fe053367d6842fd8879aaaf11e87bb3665**
  (worktree == HEAD bytes, cmp YES; status clean; mtime 2026-09-07 11:24:47, size 159879)
- weights RAWEW13v2_IS_SR_weights.csv:
  **sha256 149164b3b01aa1104b69d6c50b8898440bda64a8757a7cc9e1b4de326023283c**
  (worktree == HEAD, clean, same mtime)
- ALL 13 sleeve inputs byte-identical to HEAD and clean (brwt15, brwt10/7/5 __costfix,
  C5ng, C5ngsum, A5r2, a6r7, QAxasts, carryv2, dualmom, diescrack, CFX4). The three
  __costfix sleeves resolve to CAMP_COST/sleeves/ — coordinator-owned, clean at T0.
- builder rawew13v2_build.py + acceptance tool bt/verify_champion.py: clean == HEAD.
  (verify_champion.py committed at 5638a19; my R3 work is now champion-of-record tooling.)

### (2) Builder --verify IDENTICAL (exit 0; outputs re-hashed after, unchanged)
- champion: n_committed=4805 n_built=4805 inner=4805 max|new-old|=9.996e-17 IDENTICAL
- weights:  max|committed-built|=2.220e-16 IDENTICAL
- gross mean 1.600000 max 1.600000000000 days>1.6 0; turnover 5.2622 bp/yr; margin 2.70%/yr
  (turnover 4.9615->5.2622 bp/yr vs R3-S1: the costfix re-emit changed slot weights, and
  the champion's own |dW| path changed with them — larger charge, honesty direction).

### (3) Charter stats re-verified from CSV bytes INDEPENDENTLY (own pandas, not the tool)
- n=4805 (2008-03-31..2026-08-27), 19 calendar years.
- SR 3.181 (mean/std ddof=1 * sqrt252) EXACT; MDD -6.69% EXACT (nav/cummax); neg years 0
  (worst year +7.31%, best +157.50%); 0 neg of 19.
- ann: charter 37.195% = (1+r).prod()**(252/n)-1 with n=4805 trading years — EXACT match
  (nav_end 415.638940). For honesty: calendar-day CAGR is 38.762%; the tool and the charter
  both use the n/252 convention, so no conflict, but both numbers are quoted here.

### (4) Acceptance tool re-run THROUGH THE COORDINATOR'S NEW cmd.sh — exit 0, 7/7 checks ok
bash campaign/bt/verify_champion_r3_cmd.sh <my work>/r4_acceptance.json ->
- weights_repro 2.220e-16 (tol 1e-9); byte_repro 1.110e-16 (tol 1e-12)
- cost_reconciliation model=full_dw, max_dev 1.246e-16, implied/full ratio 1.0000000000008,
  bp/yr 5.2622 (== builder turnover), max_dev_half 1.680e-05 (book is NOT half-turn),
  day-1 entry charged 3.87e-13 (~0)
- causality mechanism=nav.shift(1) matched=causal causal_max_dev 1.110e-16 vs sameday dev
  4.927e-3; truncation-invariance 0.0 at 7 probes (t=0,1,2,1201,2402,3603,4804)
- gross max 1.6000000000007, n_over 0; margin implied 2.700000000000002% = expected 2.7
- yearly neg 0 (worst +7.3104%); MDD -6.6922% (limit -7)
- stats: ann_cagr 37.19539675684982%, SR 3.180994199561701, MDD -6.692185534307193%
  -> charter headline (37.195/3.181/-6.69/0 neg) reproduces to the last digit.
- cmd.sh AUDIT: its 13 --sleeve paths == rawew13v2_build.py PATHS exactly (incl. the 3
  __costfix files); out default coord/verify_champion_r3_last.json; set -e; exec exit
  propagates. The footgun it fixes is real (tool docstring usage is a template; <13 rows
  fails closed). NO defect found in cmd.sh. Tool's own 12 TDD tests: 12 passed in 1.70s.

### (5) Champion bytes did NOT move during the round — T1 re-hash 01:46:31
22/22 files byte-UNCHANGED vs T0 (moved: NONE). Champion sha256 at T1 ==
4358dfab95679b975e4867f9ace806fe053367d6842fd8879aaaf11e87bb3665 (same as T0 and HEAD),
mtime still 2026-09-07 11:24:47. All my writes were to AUDIT_RECON/work/r4/ + FINDINGS.md.

### (6) Coordinator-file drift flags (NONE touched by me; reported as found)
- GOAL100_CHAMPION.md (M vs HEAD): coord banner added at section 11 — declares
  CHAMPION20Y_V2 --verify step 3 NO LONGER REPRODUCES (BAL 3.107e-3 / SAFE 6.160e-3 /
  AGGR 6.206e-3) and quarantines it; points at
  HUNT_TREASFUT/work_r3/TRUTH20Y_QUARANTINE.md. Banner's restated champion-of-record
  stats (37.195/3.181/-6.69/0 neg, 7/7 ok) match my independent numbers EXACTLY.
- campaign/bt/verify_champion_r3_cmd.sh: NEW untracked coordinator file (17:19); audited,
  correct, adopted as the canonical invocation above.
- fleet_keeper.py (M vs HEAD): plan() supervision fix + ROUND env default 4 + line-wise
  roster parse; TDD tests beside it (test_fleet_keeper_supervise.py,
  test_roster_comments.py). Diff read; consistent with its stated intent; not executed by me.
- DEAD_IDEAS.csv: M vs HEAD, +~30 rows vs HEAD and 119 data rows vs charter's 108 count
  (includes R2/R3-dead additions and repro-path correction rows; e.g. TimesFM, ALFRED
  overlays, FRED composites). Growth is coordinator bookkeeping — flagged, no action.
- Other in-flight coordinator drift (notified, untouched): bt/ engine.py, gates.py,
  metrics.py, reconcile.py, shortability.py, README.md + 8 test files modified vs HEAD;
  ~20 untracked bt/ modules + tests (align.py, beats_passive.py, blend.py, borrow.py,
  financing_stress.py, leakcheck.py, test_camp_*_r3/r4 …); scripts/cot_delta_weekly.py M.
  The committed champion does NOT depend on any untracked bt/ module: verify_champion.py
  (clean==HEAD) imports numpy/pandas/stdlib only, and rawew13v2_build.py imports
  numpy/pandas/sys only — both verified by re-run above.
- champion/weights/sleeves/builder/tool: ZERO drift. The champion of record is stable and
  its honesty gates all pass as of this round.

ROUND 4 DONE

## ROUND 5 (2026-09-08 ~09:2x-09:5x CST) - POST-FLIP ACCEPTANCE (charter a/b/c)

Flip status at my start: **LANDED** - commit 539f50e 2026-09-08 09:17:32 +0800
"GATES_CONTRACT_V2 section-12 Step-2 flip: leak_check default ON (AUDIT_FWBUGS R5, TDD)".
Charter conditional resolved: post-flip acceptance round executed.

### (a) verify_champion 7/7 + champion-neutral flip proof
- `bash campaign/bt/verify_champion_r3_cmd.sh .../AUDIT_RECON/r5/verify_champion_r5.json`
  -> **ok=true, 7/7 checks, exit 0.** Stats match charter exactly: n=4805,
  2008-03-31..2026-08-27, ann_cagr 37.19540 pct, SR 3.180994, MDD -6.69219 pct,
  0 neg years (worst year +7.310 pct). Detail: weights_repro max_dev 2.22e-16;
  byte_repro max_dev 1.11e-16; cost_reconciliation model=full_dw ratio
  1.0000000000008158 (5.2622 bp/yr both sides, day1_entry charged ~3.9e-13);
  causality mechanism nav.shift(1) causal, sameday dev 0.0049, 7 truncation probes
  max_dev 0.0; gross max 1.6000000000007 <= 1.6 (margin 2.70 vs 2.70); mdd -6.692 >= -7.
- **Champion-neutral proof (byte level, 3 states):** sha256 of
  GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv = 4358dfab95679b97...3665 at 539f50e^
  (pre-flip), at 539f50e (post-flip), and in the working tree at round end (re-hashed
  09:5x) - IDENTICAL. Weights CSV RAWEW13v2_IS_SR_weights.csv = 149164b3b01aa110...
  at all three states - IDENTICAL. Flip commit touched 0 campaign/results/ files
  (name-only scan); its scope was exactly 5 files: gates.py + 4 test files.
- Flip is live in code: gates.py:104 `leak_on = bool(p.pop('leak_check', True))`.
- Drift-independence: campaign/bt/ carries 13 dirty (uncommitted) files at HEAD+worktree
  (engine/metrics/reconcile/shortability + 8 test files - FWBUGS R1/R2-era fail-closed
  fixes, disclosed by them as "landed-but-uncommitted"). To prove my acceptance verdict
  is not an artifact of that drift I extracted a PRISTINE bt/ at 539f50e via
  `git archive` and re-ran the identical 13-sleeve harness from it: **ok=true, 7/7,
  all 7 verdicts and full stats block identical to the dirty-tree run** (exit 0 both).
  So: acceptance is bt-drift-independent AND the flip is champion-neutral.
- Full bt suite from repo root (my own run, not trusted from FWBUGS): **403 passed /
  0 failed in 69.33s** - matches their claim.

### (b) Independent call-site census + verdict-neutrality
- My own scanner (r5/census_r5.py + census_r5.json, saved): **47 call lines / 33 files
  in campaign/ = 46 production / 32 files + 1 scratch** (work_r4 docstring mention in
  HUNT_INTERNATIONAL2). Independently reproduces FWBUGS's 46/32.
- Classification: **16 SIGFUL_EXPLICIT_OK** (sig= + leak_check=True explicit or via a
  resolved `kw = dict(leak_check=True,...)` splat), **31 SIGLESS** (already
  composite-False via scr fail-closed), **0 hole-class** (sig-ful without explicit
  leak_check), **0 leak_check=False (s6e violation)**.
- Scanner-honesty note: first pass flagged HUNT_FXCARRY2_round5.py:266
  `bgates.run(r_pu, ref=ref, sig=sig, **kw)` as hole-class - a REGEX false positive.
  Lines 263-265 build `kw = dict(leak_check=True, ...)` immediately above; I upgraded
  the scanner to resolve backward for the splatted var's dict/update (committed in the
  saved script), after which it is correctly counted explicit. Method correction, not
  a tree defect.
- **Empirical hole-closure probe (R2 probe C re-run under the NEW default, no
  leak_check kwarg anywhere):** same-day sign(alpha) book on AR(1) rho=0.25 alpha,
  n=900 -> pass=False, leak_ok=False, leak=True, same_period_corr=+0.8016. Honest
  T+1 shift(1) book on identical alpha -> leak_ok=True, leak=False, c0=+0.2415
  (composite pass=False only via the measurement-only ref=None scr/corr fail-closed
  path - the leak axis is green). Hole closed, empirically, by me. (r5/probe_c_holeclosure.json)

### (c) Commit-wave B5 state (for the coordinator)
- Scope discipline: the git repo root is /Users/daxu (home), NOT world-trader - raw
  `git status` counts 2190 dirty paths of which most are non-campaign (qntelli,
  codex skills, ITRF paper). B5 wave below is scoped to software/world-trader.
- **world-trader dirty paths: 1667 total = 69 tracked (M/D) + 1598 untracked.**
- Tracked modifications include TWO classes the coordinator should see:
  1. **bt/ drift (13 files, +255/-33): engine.py zero-row guard, metrics.py
     ann_geo min_count=1 + neg_years DatetimeIndex guard, reconcile.py zero-row
     turnover fail-closed, shortability.py +51 lines, README.md, 8 test files.**
     These are the FWBUGS R1/R2 landed-but-uncommitted fixes; suite is green with
     them (403/0 above) and my pristine-vs-dirty harness A/B proves they do not
     affect champion acceptance. But they are UNCOMMITTED at HEAD - the flip commit
     is not the whole bt/ story on disk.
  2. campaign md files (GOAL100_CHAMPION.md, FINAL_REPORT, FINAL_STATE,
     ITER10_WEIGHTED_CHAMPION, ITER11_COORDINATOR, PROGRESS, TRUTH_MEMO),
     fleet_keeper.py, DEAD_IDEAS.csv, champion_card.py, cot_delta_weekly.py +
     loop_team scratch/logs - normal R4/R5 agent residue.
- **DEAD_IDEAS.csv recount (charter-required): 132 data rows in the working tree**
  (133 physical lines incl header; proper csv parse, not wc -l). HEAD@539f50e has
  63 committed rows -> **69 uncommitted rows** (R2-R5 hunt waves: FX-carry nominal,
  RS-momentum rotation, vol-gates, crypto families, USREC/T5YIFR/VIXCLS/TOTALSL
  overlays, CPER/WTI-Brent/UNG/LQD-TLT/T10YIE/T10Y2Y, HY-stress gate, COT-crowded).
  The V2 contract's "120 at R4-end" was also a working-tree count - the committed
  file has lagged since R2. Row count is dynamic by design; the COMMITTED count is
  the one that is stale (63), and that is a B5-wave artifact for the coordinator.

### Escalations
- **None.** No verdict change under default-on leak at any production call site
  (0 hole-class rows); champion bytes + weights bytes unchanged across the flip;
  7/7 acceptance reproduced on pristine and dirty bt/ trees; 403/0 suite green.

### Artifacts (this round, all under coord/AUDIT_RECON/r5/)
verify_champion_r5.json (dirty-tree 7/7), census_r5.py + census_r5.json (my scanner),
probe_c_holeclosure.json (hole-closure proof). Pristine-tree A/B was run from
/tmp/r5_pristine (git archive of 539f50e); its verify JSON + stdout also in /tmp.

ROUND 5 DONE


## ROUND 6 (2026-09-08 ~16:2x-16:5x CST) - CANDIDATE-book reconciliation + fleet status
Read GATES_CONTRACT_V2.md (in force; sig=/leak_check=True discipline honored - my probes are
own-code leakcheck implementations, no gates.run call) + DEAD_IDEAS.csv FIRST. Recount:
**145 data rows** (146 incl header) vs charter's 137 at R5-end - grew via R6 curation appends
(tail rows HUNT_TREASFUT-R5, HUNT_CREDIT2-R6, CAMP_SHORT-R6, HUNT_SECTOR2-R6). No dead family
re-tested; no dead signal re-tuned. Work in AUDIT_RECON/r6/ (r6_candidate_recon.py + .json,
r6_blend_convention_probe.py, r6_blend_exact_pin.py, champion_verify_r6.json, t1_shas.json).
Round ran concurrent with CAMP_COST R6 (their work_r6 mtimes 15:05-16:15) - read as untrusted
input; every number below recomputed with MY OWN algebra (zero imports of their scripts or
bt/verify_champion).

### (a) 14-sleeve CANDIDATE book (RAWEW14_HOBR) vs champion of record - reconciled to 1e-16
Candidate of record: results/RAWEW14_HOBR_CANDIDATE_{daily,weights}.csv (untracked, emitted
by CAMP_COST 15:22; shas 4a662985a408129b / dc0dc87fea2ef4b0). Construction mirrored from
rawew13v2_build.py: relw=max(IS_SR,0)^0.55 on <2017-01-01, nav.shift(1) causal NAV-drift
weights, gross exactly 1.6, FULL |dW| @6.4bp, margin (1.6-1)*4.5%/252, day-1 entry uncharged.
1. Byte repro: my 14-sleeve rebuild vs candidate csv **max_dev 9.996e-17 (n=4805)**;
   weights_repro max_dev **2.220e-16** - the committed candidate CSVs reproduce exactly.
2. Cost reconciliation (charter 6.4bps FULL-dW, own algebra): implied-vs-modeled max_dev
   **1.000e-16** (model=full_dw) vs **1.966e-05** for half-turn (half-turn REJECTED, book is
   full-dW), ratio ~1.0000000009, charged **5.4972 bp/yr** (champion 5.2622 - the added HOBR
   slot raises turnover cost honestly), day-1 entry charged **7.52e-14 bp** (uncharged).
3. Causality: nav.shift(1) - same-day-weight rebuild deviates max **2.540e-02** (my probe,
   stricter than the tool's 4.815e-03; both >> tol => same-day REJECTED);
   **truncation-invariance 0.0 at 7 probes** (t=0,1,2,1201,2402,3603,4804) with relw FROZEN
   (weights are an input; recomputing relw from the zeroed frame is a probe bug, caught and
   fixed - my first run NaN'd the truncation check exactly that way).
4. Leak probes (V2 s6b rule: |corr|>=0.20 AND p<0.05 AND lag-0-argmax): scalar |dWg| vs book
   **+0.2255** (p 6.65e-58 - matches CAMP_COST to all digits) but argmax is lag **-1**
   (+0.4882) = the causal weights-chase-yesterday's-NAV signature => **leak=False**; signed
   dWg +0.0089 leak=False; wide per-slot mean **-0.0354** over 13 measurable slots (CFX4
   excluded: relw 0.0 => dW identically 0, corr undefined); cross-sectional mean per-day
   corr(dW_i, r_i) = **-0.0429** (R2 pins: +0.7846 leaked / -0.0277 causal). Leak=False in
   EVERY construction.
5. Gates: gross max **1.6000000000000**, 0 days >1.6; **0 neg years** (worst +7.8443%);
   MDD **-6.2354%** (better than champion's -6.6922); HOBR capital share min/mean/max
   **1.456% / 5.758% / 9.981%** - under the 15% cap as an outcome of the re-solve.
6. Deltas vs champion of record (inner 4805-day span, own stats): **dSR +0.0909,
   dAnn -0.9069pp, dMDD +0.4568pp** - EXACT reproduction of CAMP_COST's battery
   (0.09087186 / -0.90689593 / +0.45680645). Book halves at my midpoint split:
   c13 3.564/2.979 -> c14 3.802/3.001 (dH1 +0.238 / dH2 +0.022 == their byhalf
   0.2376/0.0223). Book IS SR 3.7252 (n=2208) / OOS 3.0655 (n=2597); corr(c14,c13) +0.9961.
7. Rung grid (own bisection on relw override to hit target mean share): 5% -> dAnn
   **-0.786pp**; 10% -> **-1.594pp**; 15% -> **-2.424pp**; natural(adopted) 5.758% ->
   **-0.907pp**; all 0 neg years, dSR +0.08..+0.19, dMDD +0.40..+1.20pp.
   **dAnn < 0 at EVERY rung => V2 s8c (dAnn > 0, HARD) FAILS for the certifiable book.**
8. CONVENTION RECONCILIATION - the round's main finding (r6_blend_exact_pin.py): the
   coordinator's blend arithmetic (+0.199 dSR / +4.21 dAnn / +0.05 dMDD @ w=0.25 fill-0)
   reproduces EXACTLY as **dSR +0.1989 / dAnn +4.2128 / dMDD +0.0508** under the
   GROSS-EXPANDING ADDITIVE overlay `champ + 0.25*hobr` (ann_cagr metric, no vol-match).
   That book carries 1.6+0.25 = 1.85 effective gross => violates s8e (<=1.6) and the
   gear-1.6 capital contract, and it is NOT the book verify_champion certifies (a capped
   re-solve is forced by weights_repro). The certifiable re-solve delivers dAnn **-0.907pp**
   (8c fail) instead. So the two disclosed numbers are DIFFERENT BOOKS: within the capital
   contract the candidate FAILS 8c at every weight; the +4.21pp number is unreachable
   without breaching 8e.
9. Placebo reconciliation (own 200-draw circular shift, seed 0): fixed additive blend -
   null dSR p50 **+0.2492 vs real +0.2270**, frac_null>=real **0.940** (coordinator
   169/200 = 0.845; same conclusion, RNG mechanics differ) => the blend dSR delta is
   mean-injection arithmetic, NOT skill. Full re-solve - null dSR p50 +0.0420 vs real
   +0.0909, frac_null>=real **0.030** (consistent with CAMP_COST B1 right-tail pass /
   circular reproduced_frac 0.0) => the re-solve's small dSR is real but buys NEGATIVE dAnn.
10. Sleeve stats conventions reconciled: coordinator's sleeve halves 2.182/0.753 and
    IS/OOS 2.145/0.807 are the RAW full-span sleeve (n=4604, 2008-02-19..2026-08-25;
    halves split 2017-04-20): I reproduce **2.1823/0.7533** and **2.1450/0.8074** exactly.
    My 2.259/0.684 was the champion-span slice at its own midpoint - span convention, not a
    discrepancy. Sleeve ann 12.54% @ vol 9.22% (champ vol 10.10%, 1.10x); corr vs champ
    +0.0227 (orthogonal, as submitted). Sleeve tail ends 2026-08-25 vs frame 08-27 (fill-0,
    immaterial).
11. Input pins: my 17 sha16 (14 sleeves + champion + weights + builder) match CAMP_COST's
    declared work_r6/input_shas_round.json **17/17 value-level**. RB_hobr sleeve
    da0285b9a7a5e6a2 confirmed byte-identical all round. Note: CFX4 relw = 0.0 (inherited
    from the champion; the "14-sleeve" book is 13 live slots + HOBR).

### VERDICT on the candidate (audit input to the adoption decision, not the decision)
HONEST and internally exact: costs/causality/leak/gates all clean, every CAMP_COST number
reproduces with independent code, zero arithmetic defects found. But as a V2 s8 overlay it
**FAILS 8c (dAnn > 0) at every certifiable weight** (-0.79..-2.42pp); the only dAnn>0
construction (+4.21pp) is the gross-expanding additive overlay that breaches 8e (1.85
effective gross). Both facts were disclosed by the coordinator as open concerns; this audit
confirms they are the SAME book seen through different conventions and only one of the two
is certifiable. Champion of record remains **4358dfab95679b97** (unchanged T0==T1;
verify_champion_r3_cmd.sh re-run by me this round: **exit 0, 7/7**, ann 37.1954 / SR
3.180994 / MDD -6.6922 / 0 neg - charter line to the last digit; cost 5.2622 bp/yr full_dw).

### (b) Fleet-status artifact (16:49 snapshot, cross-checked two ways)
- fleet_keeper.py status (ROUND default 5): **17 DONE / 4 pending** - pending = CAMP_COST,
  AUDIT_RECON (me), AUDIT_GATES2, HUNT_TIMESFM, accurate under done() semantics (their
  FINDINGS last lines are ROUND 5 DONE; no false-DONE possible).
- monitor_v4.sh ONE_SHOT ROUND=6 (16:49:09): **17 DONE / 3 RUNNING / 1 BLOCKED**. RUNNING =
  CAMP_COST (log 16:33), AUDIT_GATES2 (log 16:46), AUDIT_RECON (me) - all genuinely alive.
- HUNT_TIMESFM **BLOCKED is NOT the benign ROUND-mismatch wall**: its round-6 process IS
  alive (pgrep pids 66420 launch_agent_chief.sh + 66425 claude -p round-6 prompt) but its
  log has been silent since **10:30 (>6h vs 900s TTL)** -> wedge candidate. Flag for
  coordinator: SIGKILL/TTL risk class (launcher ROUND-env memory applies).
- B6 commit-wave state (results/): untracked RAWEW14_HOBR_CANDIDATE_{daily,weights}.csv +
  other agents' JSON artifacts (CAMP_BORROW_FINANCING_R3, CAMP_SHORT_LIBRARY_BORROW_CENSUS,
  CAMP_SHORT_SHORTABILITY_R2, GOAL100_TRUTH20Y*) + 5 DEAD_IDEAS.csv.bak_standup* files.
  DEAD_IDEAS.csv itself is tracked-M at 145 data rows (committed count still lags - B5-wave
  artifact noted in R5, still true).

### Escalations
None affecting verdicts. One adoption-relevant finding (8c fail-as-built + the 1.85-gross
convention behind the +4.21pp number) - decision input for the coordinator, not a tree
defect. One ops flag (HUNT_TIMESFM wedge). My writes this round: AUDIT_RECON/r6/* +
FINDINGS.md only; champion/weights/builder/sleeve bytes untouched (T0==T1).

ROUND 6 DONE


## ROUND 7 (2026-09-08 ~23:2x-23:5x CST) - blotter DAY-weight reconciliation centerpiece + fleet snapshot
Read GATES_CONTRACT_V2.md (in force, flip banner + verify-pin re-point noted; my probes are own-code
implementations, no gates.run call) + DEAD_IDEAS.csv FIRST. Recount: **152 data rows** (153 incl
header) vs charter's 145-146 at R6-end - grew via R7 curation appends (tail rows: ECB SDMX yield-curve
R7 corner, AUDIT R7 short/borrow curation, AUDIT R7 FXCARRY2 2nd confirmation). No dead family
re-tested; no dead signal re-tuned. Work in AUDIT_RECON/r7/ - generator ships WITH the artifact
(R5 scalar-probe lesson): r7_blotter_day_recon.py -> r7_blotter_day_recon.json +
r7_blotter_day_bydate.csv (4805-row day table) + r7_weight_mismatch_rows.csv (EMPTY).
Input pins (sha16, T0==T1==T2, champion bytes UNTOUCHED all round): champion 4358dfab95679b97 /
weights 149164b3b01aa110 / builder 1095b4f896b9bebb / ledger 6bb5cbaf61083a98 - first three
IDENTICAL to my R6 t1_shas.json.

### (a) CENTERPIECE - day-granularity reconciliation of the charged |dW| cost series vs the blotter
Method: my OWN weight algebra (nav.shift(1) T+1 causal, relw read from the committed weights CSV as
FROZEN INPUT - slot order asserted vs builder NAMES, row-normalize to 13, x 1.6/13); builder engine
called only as cross-check, no bt/verify_champion import.
1. Engine cross-check: charged-series max_dev **5.898e-16**, net-series **2.776e-17**; champion
   byte-repro **1.110e-16** (n=4805) - my path == engine == committed bytes.
2. DAY reconciliation (the round's deliverable): 4805 days, 4804 with ledger trades.
   **Ex-day-1 max |ledger_qty - charged_qty| = 3.387e-08 across all 4804 days; 0 days over the
   1e-7 rounding-aware tol** (4446 days show dev at the 1e-9 level = pure round-to-8dp of qty -
   blotter prints round(|dw|,8), half-ulp 5e-9/row).
3. Day-1 (2008-03-31): charged **0.0** vs ledger **1.60000001 qty / 10.240000064 bp** (12 slot-entry
   rows) - the builder's NaN-skipped Wg.diff() misses day-1 entry; the blotter charges it. This is
   the DISCLOSED superset direction (ledger = honest upper bound); cost impact exactly **10.24 bp
   one-time = 0.537 bp/yr** on the 19.05-yr span.
4. Frozen day **2009-07-27** identified and explained (charged 0 == ledger 0): the union sleeve index
   contains exactly ONE weekend row - Sunday 2009-07-26 (only QAxasts + dualmom carry data that day,
   both EXACTLY 0.0) -> zero NAV drift -> the weight refresh lands on the Sunday row and Monday is
   exactly frozen (my |dW| table: max 0.000000 that day). Sunday portfolio return is exactly 0 (no
   phantom P&L). BENIGN - no defect.
5. Cost totals: charged **100.3374 bp total = 5.2622 bp/yr** (5.262230719945142 - matches the charter
   line to all digits); ledger **110.5774 bp = 5.7993 bp/yr**; ledger EX-day-1 = **5.2622 bp/yr**
   (5.262230195812696; dev vs charged 5.2e-10). The 6.4-budget accounting is exact once day-1 is
   separated.
6. Per-sleeve: 12 sleeves in the ledger; **CFX4 absent** (relw 0.0 -> dW identically 0 - consistent
   with my R6 finding, the 13-slot book is 12 live + CFX4 nil). Max per-sleeve dev **4.978e-07**
   (A5r2, 4804 rows) vs rounding-aware bound **2.402e-05** (5e-9 x rows) - WITHIN bound. HONEST
   self-correction logged: my first gate used a flat 1e-7 per-sleeve tolerance and FAILED (exit 1);
   hypothesis-tested the rounding-accumulation mechanism (all 12 sleeves: 4804 rows; worst-case
   5e-9 x 4804 = 2.402e-05) before recalibrating - my miscalibration, not a data defect.
7. Day-WEIGHT reconciliation (57,648 rows x weight_from/weight_to vs my path): **0 mismatch rows**
   (tol 1e-8), max dev **5.0e-09** (= the round-to-8dp half-ulp exactly); ledger self-connectivity
   weight_from[t] == weight_to[t-1] per sleeve: **0 gaps**. GATE_OK **true**, script exit 0.

### (b) Fleet-status snapshot (keeper 23:41:31 / monitor 23:50:14 CST, cross-checked)
- fleet_keeper.py status: **17 DONE / 4 pending-alive** (DATA_FREDMORE, AUDIT_RECON=me,
  AUDIT_GATES2, HUNT_TIMESFM).
- monitor_v4.sh ONE_SHOT ROUND=7 (env-var invocation; my first arg-style call was wrong and started
  the 90s loop - killed): **17 DONE / 3 RUNNING / 1 BLOCKED**.
- Authoritative per-role resolution of the 4 non-DONE: DATA_FREDMORE genuinely RUNNING (last line
  ROUND 6 DONE, log fresh 348s). AUDIT_GATES2 genuinely RUNNING - log stale (18:40:44, 18623s > 900s
  TTL) BUT work_r7/ has fresh artifacts (<15 min: r7_class_b_calibration.py, r7_vol2_validate_rerun
  .py/.json - it is validating VOL2's V3 per-class placebo proposal, charter-relevant); the v4.1
  fresh-file check catches this, the log-only view does not. AUDIT_RECON = me. **HUNT_TIMESFM
  BLOCKED / wedge candidate (2nd consecutive round)**: last line ROUND 6 DONE; its round-6 process
  exited 0 at 18:23:06; a round-7 launcher (pid 46249, `launch_agent_chief.sh HUNT_TIMESFM 7`) is
  alive but ZERO log bytes and ZERO fresh files since 18:23 (>5.5h) - same SIGKILL/TTL wedge class
  as R6. Escalated to coordinator.
- Commit-wave state (campaign/ scoped, 23:5x): **361 dirty paths = 329 untracked + 32 modified**.
  results/ highlights: DEAD_IDEAS.csv M (152 data rows, committed count lags), untracked
  RAWEW14_HOBR_CANDIDATE_{daily,weights}, RAWEW15_REFRESH_CANDIDATE_{daily,weights},
  GOAL100_TRUTH20Y* family, CAMP_BORROW/CAMP_SHORT JSONs, 5x DEAD_IDEAS.csv.bak_standup*.
- Champion bytes re-verified T2 (23:5x): 4358dfab95679b97 / 149164b3b01aa110 - UNCHANGED.

### Escalations
1. HUNT_TIMESFM round-7 wedge (ops, above). 2. Zero verdict-affecting findings: the blotter IS the
charged book plus the disclosed day-1 superset; reconciliation PASSES at day, sleeve, and row
granularity. My writes this round: AUDIT_RECON/r7/* + FINDINGS.md only.

ROUND 7 DONE
