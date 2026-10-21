# COMMIT-WAVE MANIFEST — definitive (AUDIT_FWBUGS R6, charter item (a))

Generated 2026-09-08 16:0x-16:3x CST at HEAD `2f0ccc0` by AUDIT_FWBUGS (docs-only round;
zero code edits by this agent). Every uncommitted path under `campaign/` enumerated and
classified. NOT-A-GATE: this is a manifest, not an adoption verdict for anything.

## 0. Census headline (all numbers from commands run this session)

- `git status --porcelain -- campaign/` (default collapse): **336 lines** — this is the
  "317" the charter quoted (11:4x snapshot of the same collapsed view).
- `git status --porcelain -uall -- campaign/` (true file level): **2,202 paths at census
  time = 31 tracked-modified + 2,171 untracked files**; the collapsed view hides 68
  untracked directories (they contain ~1,900 files, e.g. coord/work_r*, team/agents/*,
  STRICTAUDIT_*). Census-time total size 198.2 MiB.
- The tree is LIVE: suite grew 401 (R5 baseline) -> 410 (coordinator 11:4x) -> **422**
  (my runs, 16:0x); DEAD_IDEAS grew 137 (charter) -> **145 data rows** (my csv recount;
  71 distinct sources; concurrent R6 appends HUNT_CREDIT2-R6, CAMP_SHORT-R6,
  HUNT_SECTOR2-R6 landed mid-census, mtime 14:55).
- Exhaustive per-path index backing this manifest: `commit_wave_appendix.txt` (2,206
  paths at its own generation instant; regenerable with `git status --porcelain -uall`).

## 1. HEADLINE DEFECT: the framework does not reproduce from a fresh clone (COMMIT-NOW, highest priority)

`git show HEAD:campaign/bt/gates.py` line 104 has the R5 flip (`leak_on = bool(p.pop(
'leak_check', True))`) and lines 135/150 lazily `from bt.leakcheck import ...` / `from
bt.beats_passive import ...` — but **`bt/leakcheck.py` and `bt/beats_passive.py` are
UNTRACKED** (mtimes 09-07 15:59 / 18:20; provenance: this agent's R3 work + AUDIT_GATES2/
INTL2 R3). Measured this session via `git archive HEAD ... + import`:

```
FRESH-CLONE CRASH: ModuleNotFoundError No module named 'bt.leakcheck'
```

Any `gates.run(...)` on a fresh clone dies instead of returning a result dict — the R5
flip's "sig-less fail-closed" contract degrades into a crash. Tracked files importing the
untracked modules: `bt/gates.py` (leakcheck, beats_passive), `bt/tests/test_fwbugs_audit_r3.py`
(leakcheck), `bt/tests/test_beats_passive.py` + `bt/tests/test_gates_audit_r3.py`
(beats_passive; both committed in 539f50e). Blast radius is exactly the R5 commit's deps.

**Classification: COMMIT-NOW — commit `bt/leakcheck.py`, `bt/beats_passive.py` (and their
directly-imported helpers `bt/align.py`, `bt/blend.py`, `bt/borrow.py`,
`bt/financing_stress.py`, `bt/verify_champion_r3_cmd.sh` — all untracked, all green in
suite, referenced by `bt/README.md` which is already tracked-modified) as the first commit
of any wave.** Test evidence this session: full suite 422/0 twice (runs A 70.99s / B
91.29s) WITH the files present; fresh-clone crash WITHOUT. No code changes needed — the
files already on disk are the tested bytes.

Champion inputs verified SAFE on a fresh clone: all 13 sleeve paths in committed
`rawew13v2_build.py` checked with `git ls-files --error-unmatch` — **13/13 TRACKED**
(brwt10_2000__costfix, brwt7__costfix, brwt5__costfix, diescrack_L40Z20_net,
CFX4_DTF21_63_raw_daily, QA_dualmom_band121, E1_brwt_spread_rev15_2000, E1_C5ng_weekday_prem,
E1_a6r7_bond2y_trend_1990, E1_QAxasts_tsmom189_2006, E1_carryv2_GLD_2006,
A5_r2_contango_rateshock, E1_C5ng_summer_weekday). Champion CSV of record already tracked.

## 2. The 31 tracked-modified files (one line each: why / evidence / classify)

### bt/ source (4) — R1/R2 landed-but-uncommitted framework fixes (my lineage) + README
| file | why-changed | evidence | classify |
|---|---|---|---|
| `bt/engine.py` (+3) | R2 zero-row guard: `iloc[0]=0.0` on len-0 frame would enlarge past end; now returns empty series | suite green; comment cites AUDIT_FWBUGS R2 | commit-now (with §1 wave) |
| `bt/metrics.py` (+7/-1) | R2 `ann_geo` min_count=1 (all-NaN prodded to 1.0 -> fail-open, same class as R1 neg_years) + neg_years DatetimeIndex guard | mutants M3/M20/M21 caught (work/r4/full_pass.txt); 422/0 | commit-now |
| `bt/reconcile.py` (+7) | R2 zero-row pos_path fail-closed (nonzero ledger = coverage violation, not crash) | test_reconcile additions green | commit-now |
| `bt/shortability.py` (+51) | R2 hunt-template pregate: `shortability_pregate` (NONE-tier drop + preserve_gross relever), `tier_delta_cost` (NaN/neg fail-closed), 2 borrow ladders | 5 new tests in test_shortability.py | commit-now |
| `bt/README.md` (+6/-1) | doc: rows for beats_passive/borrow/blend/financing_stress | docs | commit-now |

### bt/tests tracked-modified (8) — R2 mutation-coverage pins + un-leak of fixture
| file | why | evidence | classify |
|---|---|---|---|
| `tests/test_backtest.py` (+35) | R2(b) M28/M29 pins: book/sleeve T+1 day-0 PnL == 0 (deleting .shift(1) used to pass the whole file) | docstrings cite mutants | commit-now |
| `tests/test_camp_cost_full_dw.py` (+32/-32 rewritten) | R1's "offender must exist" pin INVERTED after the R2 dualmom fix: now asserts 0.5-half-turn pattern ABSENT + FULL |dW| + COST_STD present | reads committed QA_dualmom_band121.py | commit-now |
| `tests/test_gates.py` (+10) | R2(b) M23 pin: sub-round(10) float noise collapses (uniq) | green | commit-now |
| `tests/test_gates_audit.py` (+15/-5) | composite-strong fixture supplied real timing sig (scr_ok enforced since R2; old fixture was sig-less luck) | green; scr_ok=True asserted | commit-now |
| `tests/test_metrics.py` (+16) | R2(b) M21 pin: exact half-split point on ODD length (even length = no-op) | green | commit-now |
| `tests/test_rawew13v2.py` (+27/-12) | legacy "weighted beats EW >= 1.30x" compared to a cost-undercharged baseline; replaced with like-for-like same-inputs EW (33.30 vs 37.20, MDD both in wall, 0 neg) | numbers in docstring from coordinator probe 09-07 | commit-now |
| `tests/test_reconcile.py` (+12) | R2(b) M27 pin: max_abs_diff NaN -> inf, repro_ok rejects | green | commit-now |
| `tests/test_shortability.py` (+67) | R2(b) M5 pin (NONE-tier keeps LONG leg) + 5 pregate tests | green | commit-now |

### scripts/ + harness (4)
| file | why | evidence | classify |
|---|---|---|---|
| `scripts/champion_card.py` (+6) | AUDIT_CHAMP2 R5b: bare-invocation sys.path fix (works from any cwd, clean env) | AUDIT_CHAMP2's round5b tests in suite | commit-now |
| `scripts/cot_delta_weekly.py` (+18/-11) | HUNT_CMDT2 R4 audit: np.where de-Seriesd (.shift crashed, swallowed by bare except -> 3/4 configs silently dead); build_weekly fail-loud (no more except->None) | cited tests_tdd_r4_audit; hunt negative unaffected | commit-now |
| `audit_harness_newconstraints.py` (+145/-37) | AUDIT_CHAMP2 R1-R4: C2 was tautological (back-derived port from net; proven by counterexample) -> independent gross reconstruction; C1 causal nav; C5 substantive fungible-short facts | test_audit_champ2_round1..4 in suite (all green) | commit-now |
| `agents/E1_20yspan/work/e1_idea2_a6r7_brwt_detrunc.py` (2-line) | CAMP_COST R2 costfix: half@6.0 -> FULL |dW| @6.4 in the archived detrun script (its sleeve E1_brwt_spread_rev15_2000 is a committed champion input) | sleeve CSV already tracked+costfixed | commit-now |

### coordination tooling (1 + its tests in coord/, untracked — see §3)
| file | why | evidence | classify |
|---|---|---|---|
| `agents/chief/coord/fleet_keeper.py` (+90/-40) | TDD 09-07: roster() comment-line fix (whole-file .split() pgrep'd ~8 bogus agents); plan() fail-closed supervision (old loop exited "nothing pending" while fleet was LIVE mid-round — stranded agents); ROUND env default 5 (09:00:41 stale-default incident); status subcommand (a `status` query used to START a second keeper) | coord test scripts run this session: test_roster_comments ALL GREEN, test_fleet_keeper_argv ALL PASS (A3/A4), test_fleet_keeper_supervise ALL PASS (K2/K3), test_launch_all_cap ALL GREEN | commit-now (with its 4 test files) |

### campaign docs (9) — quarantine/supersede banners (the AUDIT_CHAMP2 R5 charter-named doc fixes)
| file | why | classify |
|---|---|---|
| `GOAL100_CHAMPION.md` (+77) | 2 banners: CHAMPION20Y_V2 verify step 3 no longer reproduces (BAL 3.1e-3/SAFE 6.2e-3/AGGR 6.2e-3) -> DEPRECATED FOR QUOTING 09-08 03:1x; §12 runbook steps 2-3 DIFF banner; CAMP_BORROW financing-convention disclosure (4 drift flags incl. -34.86% true-path; champion impact: no gate moves, 0/19 neg everywhere) | commit-now |
| `GOAL100_PROGRESS.md` (+11) | SUPERSEDE banner: stale "CURRENT champion 48.2%" row; champion of record named | commit-now |
| `GOAL100_FINAL_REPORT.md` (+14) | SUPERSEDE banner: 55.5%/62.4% are V1-generation, not current | commit-now |
| `GOAL100_FINAL_STATE.md` (+14) | SUPERSEDE banner: HONEST13V2/11 books run 3.45x mean gross + pre-T+1 + half-cost | commit-now |
| `GOAL100_TRUTH_MEMO.md` (+12) | SUPERSEDE banner: §16 49.4% STRICTTRADE = hidden-leverage vintage | commit-now |
| `GOAL100_ITER10_WEIGHTED_CHAMPION.md` (+7) | SUPERSEDE banner: 40.88% -> current 37.195 lineage | commit-now |
| `GOAL100_ITER11_COORDINATOR.md` (+26) | SUPERSEDE banner (40.84/39.85 -> 37.195) + RE-EMIT WAVE addendum (leak provenance, archived leaky CSV sha 0516e543) | commit-now |
| `agents/G4_detrun/FINDINGS.md` (+8) | QUARANTINE notice: TRUTH20Y books recon 3.86e-2, MDD -7.88%, 1 neg year — do not quote | commit-now |
| `team/docs/DATA_COVERAGE.md` (+130/-29) | DATA_MAESTRO regenerated: 11 hand-written "CLEAN-pending" rows -> manifest-driven table incl. EMPTY/UNPARSABLE lint states (fail-closed) | commit-now |

### results/ (1)
| file | why | classify |
|---|---|---|
| `results/DEAD_IDEAS.csv` (+211/-~) | ledger appends R4->R6 (137->145 rows this window) + HUNT_CREDIT2-R6 curation corrections (row 105 label fix, row 121 stale cells) | commit-now (append-ledger; each wave commit takes the then-current bytes) |

## 3. Untracked groups (2,171 files; curated by directory — counts from census)

### COMMIT-NOW (framework-adjacent, tests-green, fresh-clone blockers)
1. `bt/*.py` untracked production modules (7): `align.py` (09-07 03:44), `beats_passive.py`
   (18:20), `blend.py`, `borrow.py`, `financing_stress.py`, `leakcheck.py` (15:59),
   `verify_champion_r3_cmd.sh` (17:19). WHY: gates.py imports two of them at run() time
   (§1 crash); README already documents all of them. EVIDENCE: 422/0 x2 this session.
2. `bt/tests/test_*.py` untracked (32): the R2-R6 round files of AUDIT_RECON,
   AUDIT_CHAMP2 (round2..round6), CAMP_BORROW (r2/r3), CAMP_COST (r2/r3/r4/r6-hobr),
   CAMP_SHORT (r2b/r3/r4), HUNT_TREASFUT (r2/r3-lint/r4), shortability r2/r2b/r2c,
   gates_audit_r2, fwbugs r2/r3_verify/r4, align, financing_stress. All pass in suite.
3. `bt/tests/fixtures/make_mini_champion.py` + `fixtures/mini_champion/sleeves/{alfa,
   bravo,charlie}.csv` (4): fixture generators; no tracked file references them (grep
   clean) but they are the repro for the lineage tests above.
4. coord keeper/launcher test scripts (5): `test_fleet_keeper_argv.py`,
   `test_fleet_keeper_supervise.py`, `test_roster_comments.py`, `test_launch_all_cap.py`,
   `test_launch_all_plan.py` — ALL GREEN when run directly this session (see §2 fleet_keeper
   row). Ship with fleet_keeper.py.
5. coord launch/monitor/standup scripts (7): `launch_all.sh` (includes the done_marker +
   comment-line TDD fixes), `launch_agent_chief.sh`, `monitor.sh`, `monitor_v4.sh`,
   `standup.sh`, `keeper_takeover.sh`, `AGENTS.txt` (roster with CIO comment line).
6. coord contracts + audit truth (5): `GATES_CONTRACT.md` (v1), `GATES_CONTRACT_V2.md`
   (RATIFIED + flip banner), `GATES_CONTRACT_V2_DRAFT.md`, `MANIFEST.md`, `FINDINGS.md`
   (coord aggregate). The V2 contract is cited by dozens of committed-ish artifacts; its
   absence from git is itself a provenance hole (V2 §10).
7. coord standup verify JSONs (~30 `verify_champion_standup_*.json` + `standup_*.json`,
   `verify_champion_r3_last.json`, `coord_accept_r3_brwtcostfix.json`): champion-7/7
   evidence trail. Classify commit-now (small, frozen); NOTE the charter's cited
   `verify_champion_standup_1140.json` is a **145-byte ok:false record** ("missing sleeve
   inputs: no --sleeve name=path given") — the ok:true 7/7 records at the same headline
   (ann 37.19539675684982 / SR 3.180994199561701) are `verify_champion_r3_last.json`
   (00:09), `..._1445.json`, `..._1540.json` (ok True, read this session). Coordinator may
   want to re-point that charter citation.
8. `campaign/GOAL100_ITER8/9/12/13_NEWDATA_*.md` (4) + campaign-root launcher logs (4):
   historical round reports; commit-now as history.
9. `scripts/` untracked hunt libs + round scripts (56): HUNT_CMDT2 (incl. round5),
   HUNT_CREDIT2 (incl. round5), HUNT_CRYPTO2, HUNT_FXCARRY2 (incl. r6_treasfut_repro),
   HUNT_INTL2 r1-r4, HUNT_TREASFUT (incl. round5 + 2 rebuild scripts),
   hunt_sector2/vol2 libs, `__init__.py` (0 bytes, makes `scripts.` importable for
   champion_card.py — REQUIRED by the champion_card fix), test_hunt_vol2_lib2.py.
   EVIDENCE: many are the repro paths for DEAD_IDEAS rows (V2 §10a artifact
   verifiability); commit-now.
10. `team/` untracked (149): DATA_MAESTRO (build_coverage.py + FINDINGS + tests),
    DATA_ORGANIZE lib + legacy findings + probes, RES_* (BASIS incl. 52 sleeve CSVs +
    metas — the RB_hobr family of the pending-adoption candidate, CREDIT, VOL, STATARB,
    CALENDAR, META, REVERSAL, CARRY), team/lib/merge.py, team/tests/ (5 test files),
    team/agents launch logs. The RES_BASIS sleeves are the pending RB_hobr_crack_hyst
    candidate's artifact set (V2 §10a) — commit the sleeve CSVs + metas + repro scripts
    regardless of adoption (the DEAD_IDEAS row cites them).
11. `campaign/tests/` (3): test_cmdt2_r3_fetch, test_hunt_fxcarry2_r3_tail/r5.
12. `tools/parsers/README.md` (1): new team tools stub.
13. per-agent FINDINGS/CHARTER/LOG under `agents/loop_team/*` and
    `agents/chief/coord/<AGENT>/` (FINDINGS.md for CAMP_COST, CAMP_SHORT, CAMP_BORROW,
    DATA_*, HUNT_*, AUDIT_*; CHARTER.md CAMP_COST): the DONE-marker protocol
    (launch_all.sh done_marker reads `$ROOT/$a/FINDINGS.md` tail) and every DEAD_IDEAS
    row's evidence pointer live in these files. COMMIT-NOW: losing them breaks round
    bookkeeping + V2 §10 auditability. The combined-dir FINDINGS.md
    (`coord/HUNT_CRYPTO2 HUNT_.../FINDINGS.md`, the space-named 13-role dir) must ship
    too — launch_all.sh's done_marker falls back to exactly that path.

### NEEDS-DISCUSSION (correct-looking, but coordinator call)
- `agents/coord/CAMP_COST/sleeves/*__prefix.csv|__R3COSTFIX.csv` (12 files, 1.67 MiB):
  pre-costfix/duplicate-vintage sleeve bytes. The COMMITTED builder consumes only the
  `__costfix` variants (all tracked, §1 check). The `_prefix`/`_R3COSTFIX` files are
  audit trail for the CAMP_COST R3 adoption (test_camp_cost_r2's gate enforces the swap).
  Suggest: commit under an `archive/` name or leave untracked deliberately (vintage-dup
  risk: someone re-pointing PATHS at a `_prefix` file would silently re-introduce the
  150-190bps/yr undercharge — a builder PATHS lint would be the fix, new code = needs
  discussion).
- `results/DEAD_IDEAS.csv.bak_standup*` (5): coordinator's own standup backups. Fine to
  commit or to .gitignore; do NOT delete (recovery trail for the 09-07 19:10
  `bak_standup1900_fix` curation incident).
- `results/GOAL100_TRUTH20Y*` (4: json + 3 CSVs, 09-01 vintage): QUARANTINED artifacts
  (G4_detrun banner, HUNT_TREASFUT TRUTH20Y_QUARANTINE.md). Recommend commit under a
  QUARANTINED/ subdir or commit-as-is — the quarantine banners reference these exact
  paths; a missing path makes the quarantine unverifiable. Coordinator call.
- `results/RAWEW14_HOBR_CANDIDATE_daily.csv` + `_weights.csv` (09-08 15:22) +
  `CAMP_COST/work_r6/adoption_*` artifacts: the RB_hobr pending-adoption evidence. NOT
  decided (charter); committing the candidate CSVs does not adopt them — but any commit
  wave including them MUST carry the banner text "candidate, adoption pending full
  rebuild verdict (CAMP_COST charter)". Needs-discussion only because adoption is open.
- `coord/logs/*` + `coord/status_history.txt` (1.1 MiB) + `coord/logs/.attempt.*` dotfiles:
  operational logs. Recommend .gitignore (regenerable, churny) — coordinator call.
- `coord/write_r5_charters.py`, `coord/test_fred_round3.py`, `coord/
  test_launch_all_skip*.sh|py`, `test_launch_retry*` (older keeper TDD): superseded test
  generations vs current keepers. Suggest commit-as-archive; owner = coordinator.
- `loop_team/*` 09-02..09-04 epoch (LOG_iter6/6b/7/75 + scratch + FINDINGS for
  DATA_MORE_*, HUNT_LIQREV, HUNT_FXDEPO, HUNT_OVNIGHT incl. 5 .pkl, SKILL_ALPHAAG*,
  BLOTTER_*, AUDIT_V3, AUDIT_LEVFRONTIER incl. 6.1 MiB blotter CSV, VERIFY_BEST,
  STRICTAUDIT_* FINDINGS...): prior-epoch audit trails, superseded by the R2+ rounds but
  cited by older committed docs. 6-7 MiB heavy. Coordinator call: commit as history or
  prune with a MANIFEST.md note. NO deletion by this agent.
- `work/pre_banner_snapshot/` (2): the pre-banner copies of the two bannered docs —
  natural companions of the §2 doc banners; commit alongside.
- `campaign/logs/iter4/5_launch.log`, `campaign/logs/launch_strict_parallel.out`,
  `campaign/LOG_iter*launcher.log`, `campaign/launch_strict_parallel.sh`,
  `campaign/retest_r3_run.log`: launcher logs + one launcher script. .gitignore or commit
  as history — coordinator call.
- 9 numeric-dot temp files (`coord/logs/.AUDIT_FWBUGS.attempt.26714` etc.): live liveness
  markers (launch_all.sh attempt files, one is TODAY's pid 26714). DISCARD (they are
  runtime state, not artifacts) — they should be .gitignored.
- 2 quoted-name stragglers (`.md"`, `.log"`): the space-named combined-dir FINDINGS.md +
  combined logs dir, git-quoting only. NOT junk — commit under the exact quoted name.

### DISCARD (after eyeball; none deleted by this agent)
- `__pycache__/` trees (coord/__pycache__, CAMP_COST/work_r6/__pycache__): bytecode.
- `*.pkl` scratch (HUNT_OVNIGHT 5, STRICTAUDIT_STATISTICS 2, CAMP_SHORT cache/recon.pkl):
  regenerable pickles behind saved repro scripts.
- `DATA_COTMORE/work_r5/_raw_live/*.zip` (2, raw CFTC vendor blobs): raw fetches; the
  parsed artifacts + repro scripts carry the evidence. (If the team wants raw-vendor
  retention for V2 §9d vintage pinning, move to a data-lake path, not git-LFS-by-accident.)
- `team/agents/DATA_ORGANIZE/.../FINDINGS_...md.from_ecb_fx` (1): stray editor/transform
  suffix duplicate of a file that exists un-suffixed next to it.
- empty/placeholder dirs (`agents/STRICTAUDIT_{CONSTRUCTION,EXECUTION,METRICS,SLEEVES,
  STATISTICS}/` contain only their own subdirs/logs, `campaign/{tools,work,tests}/`
  stubs): git cannot store empty dirs anyway; nothing to do unless placeholdering.

## 4. Suggested wave order (dependency-honest; nothing executed this round)
1. **fresh-clone fix**: bt untracked modules (§3.1) + bt source/test tracked-modified
   (§2) + fixtures (§3.3) — one commit, suite must re-run 422/0 after.
2. framework tooling: scripts/ + audit_harness + champion_card + cot_delta_weekly +
   campaign/tests + tools stub (§2/§3.9).
3. coordination: fleet_keeper + its tests + launch/monitor/standup + contracts + verify
   JSONs + per-agent FINDINGS (§3.4-6, §3.13).
4. docs+ledger: the 9 bannered docs + DATA_COVERAGE + DEAD_IDEAS + ITER reports +
   pre_banner_snapshot (§2/§3.8).
5. team/ + research artifacts incl. RES_BASIS sleeves (§3.10) + candidate-with-banner
   if coordinator approves (needs-discussion).
6. gitignore sweep for the DISCARD class (§3 last bullets).

Caveats, stated plainly: (i) the tree moved during this census (suite 410->422, ledger
137->145); every count is timestamped to this session and is a floor, not a ceiling.
(ii) This manifest is audit-doc only; nothing was committed, deleted, renamed, or
code-edited by AUDIT_FWBUGS in R6. (iii) My own work_r6 artifacts (this file, appendix,
suite_run_a.txt, FINDINGS round-6 section) are themselves new uncommitted paths —
commit-with-wave per §3.13.
