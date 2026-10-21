# TRUTH20Y_QUARANTINE.md — HUNT_TREASFUT round 3(a), 2026-09-07
# R4 ADDENDUM (2026-09-07 evening): see bottom — CHAMPION20Y_V2 IS exactly reproducible
# from git blobs (corrects the "whole Sep-1 lineage unreproducible" line below);
# TRUTH20Y itself re-screened on pinned pool + 3 documented configs: still NOT reproduced.

## Recommendation: QUARANTINE `campaign/results/GOAL100_TRUTH20Y*` (3 CSVs + JSON)

Builder is absent from the tree; reconstruction attempt did NOT reach the charter's
1e-12 bar on any of the 3 books. Until a builder reappears, do not quote TRUTH20Y as
champion, candidate, or current anything; it is a provenance-orphan artifact.

## What was attempted (exact numbers)

Scripts (saved, rerunnable):
- `campaign/scripts/HUNT_TREASFUT_truth20y_rebuild.py` — straight `construct()` from
  `champion20y_build.py` (vt/load/COST byte-identical; only `start` moved to kwarg),
  14-pool mapping FINAL_TRUTH names -> on-disk E1 files. Result (today's tree):
  BALANCED maxdev **1.5809e-02**, AGGRESSIVE **1.7776e-02**, SAFE **1.3841e-02**;
  n_rec 5196 vs n_com 4990. Exit 1 = NOT REPRODUCED.
- `campaign/agents/chief/coord/HUNT_TREASFUT/work_r3/truth20y_recon_r3.py` — the
  calendar-forensics variant below. Result: **calendar exactly solved; values not.**

### Forensics that DID land (positive findings)

1. **Committed calendar reproduced byte-exactly.** Committed index =
   union(14 sleeves) in 2006-10-02..2026-08-28 MINUS US federal holidays WITH
   Sat->Fri / Sun->Mon observance, weekdays only: n=4990, `idx.equals` True on all
   3 books. The json note "NYSE calendar" is a MISNOMER: the dropped set is exactly
   the federal-holiday set {NewYear, MLK, Presidents, Memorial, Juneteenth(2021+),
   July4, Labor, Columbus, Veterans, Thanksgiving, Christmas}. Evidence:
   Columbus Day (10-09/10-08/10-13, 3 hits) and Veterans Day (11-11/11-10/11-12,
   3 hits) are DROPPED — NYSE trades both; Good Friday (NYSE-closed) is KEPT 20/20
   years. One stray row (2009-07-26, a Sunday in the sleeve union) is additionally
   absent from the committed file.
2. Deviation profile is FLAT across all 20 years (yearly maxdev 2.0e-3..1.6e-2,
   4923/4990 days >1e-6, corr 0.9814-0.9839) — a systematic construction-vs-input
   difference, not a localized event or one bad sleeve leg.

### Variants tested and rejected (no knob tuned; each a documented-or-implied reading)

| variant | BAL maxdev | verdict |
|---|---|---|
| straight construct (today's tree) | 1.5809e-02 | 5196 rows, calendar wrong |
| same, Sep-1 git blobs for the 3 costfix-modified inputs (QAxastsE, brwt15E, dualmom) | 1.5808e-02 | input drift is NOT the gap |
| federal-holiday filter POST-construction (drop rows) | 1.5809e-02 | calendar solved, values unchanged |
| federal-holiday filter PRE-construction (sleeves filtered before vt/blend/DD) | 3.8607e-02 | idx_eq True, values worse |
| pre + sparse sleeves earn 0 on foreign days (campaign convention) | 3.2567e-02 | idx_eq True, values still off |

(SAFE maxdev 3.37e-2 / 3.40e-2, AGGRESSIVE 4.35e-2 / 3.12e-2 across the pre variants.)

### Why the residual ~3e-2 gap is likely unrecoverable

Pool provenance: A5r7 (mtime Sep 1 16:41, 34 min AFTER TRUTH20Y's 16:07) and the two
C5ngE files + a6r7E (Sep 7 06:55/06:57) were re-generated after TRUTH20Y was written;
the Sep-7 files are git-identical to HEAD, so the blobs that built TRUTH20Y are lost
except where git happens to hold them. `champion20y_build.py` (the ancestor builder)
no longer byte-reproduces its OWN committed V2 books either (maxdev 3.1e-3 / 6.2e-3,
same day-10:59 costfix wave) — the whole Sep-1 20y lineage is not tree-reproducible.
Commit de890d0 (Sep 1 11:24) predates TRUTH20Y but no builder was committed with it.

## Why quarantine (not just "unreproduced")

Independent of reproducibility, the committed files fail champion constraints
(AUDIT_CHAMP2 R2, pinned in their tests): BAL geometric ann **69.09%** (the json's
53.0 headline is ARITHMETIC ann — a +16.1pp convention gap), MaxDD **-7.88%**
breaches the -7% wall, **1 negative year (2006)**, corr to the actual champion
0.5750. Anyone quoting "53.0% / 19.8y TRUTH" as a campaign result is quoting an
arith-ann number from a book that breaches the DD wall, from a builder that no
longer exists.

## Charter duty 2: lint test (RED first)

`campaign/bt/tests/test_treasfut_r3_truth20y_lint.py` — fails if any gated campaign
doc quotes GOAL100_TRUTH20Y as current champion. RED evidence captured in
FINDINGS.md before GREEN.

---

## R4 ADDENDUM (2026-09-07 evening, HUNT_TREASFUT round 4)

Two corrections/extensions to the R3 memo, from round-4 forensics:

### 1. CORRECTION: CHAMPION20Y_V2 IS exactly reproducible (the blanket claim below was wrong)

The R3 line "the whole Sep-1 20y lineage is not tree-reproducible" is REFUTED for V2:
in a clean worktree at the V2-snapshot commit c745682 (ROOT repointed — the builder
hard-codes ROOT to the main tree, which invalidated the first naive worktree run),
the UNMODIFIED campaign/scripts/champion20y_build.py verifies all 3 committed V2 books:
  BALANCED 9.986e-17 / SAFE 9.996e-17 / AGGRESSIVE 9.991e-17
Root cause of the R3-era DIFF (3.107e-03 / 6.160e-03 / 6.206e-03): commit b268e52
(2026-09-07 costfix re-emit) changed exactly 3 of the 13 pool sleeves (QAxasts,
dualmom, brwt); the other 10 are byte-identical c745682 -> HEAD. Permanent repair
path (TDD, 8/8 green): campaign/scripts/HUNT_TREASFUT_champion20y_v2_rebuild.py +
campaign/bt/tests/test_treasfut_r4_v2_rebuild.py + work_r4/pre_costfix_sleeves/
(3 pinned blobs, sha256-vs-git checked). TRUTH20Y remains quarantined; V2 does NOT.

### 2. TRUTH20Y re-screen (stronger evidence, same verdict: NOT REPRODUCED)

R3's "blobs lost" story is now void for every input: all 14 TRUTH20Y-pool sleeves
are content-known (10 byte-SAME vs c745682; 3 = costfix trio, pinned; brwt5/7/10
untracked but on disk since Sep 1 13:47-13:48, BEFORE the 16:07 book). A5r7's 16:41
mtime is misleading — its disk bytes are content-identical to the c745682 blob.
work_r4/truth20y_param_screen_r4.py, committed n=4990 overlap on all cells:
  P1 FINAL_TRUTH cfg (.072/.040, .093/.030) + pinned blobs:
     SAFE 1.3841e-02 / AGGRESSIVE 1.7776e-02 / BAL 1.5808e-02   (R3 control: 1.5809e-02)
  P2 V2 cfg (.090/.030, .106/.0255):      BAL 1.5375e-02 (SAFE 1.88e-02, AGGR 1.74e-02)
  P3 E1 cfg   (.085/.035 FR.4):           SAFE 1.3477e-02
Three pre-registered documented configs all land ~1.4-1.9e-2 — the residual is a
CONSTRUCTION difference (params unpublished in TRUTH20Y.json, or blend/calendar
logic not derivable from the ancestor builder), not input drift. No further knob
was tuned. Quarantine recommendation STANDS, now with a complete input ledger.

---

## R5 ADDENDUM (2026-09-08, AUDIT_CHAMP2 round 5a) — CHAMPION20Y_V2: REBUILD REJECTED, STAYS DEPRECATED (DROP with numbers)

The coordinator's 03:1x deprecation banner chartered "rebuild ... with fresh --verify
IDENTICAL, OR complete the quarantine doc on why it stays deprecated." Both halves were
executed; the rebuild was CARRIED OUT in sandbox (never emitted) and REJECTED on gate-2
grounds. Evidence pins: `campaign/bt/tests/test_audit_champ2_round5b.py` (7/7 GREEN,
inserted into the fleet suite this round; full bt suite 410 passed / 0 failed post-insert).

### Why the "V2 is exactly reproducible" R4 line does NOT rescue V2

R4 was right that V2 reproduces from c745682-era blobs (their 8/8 pins stand, re-run
GREEN this round). But reproducibility is not admissibility. The two defects the rebuild
would re-certify with a fresh IDENTICAL stamp:

1. **Retired cost convention (gate-2 violation).** `champion20y_build.py` charges
   `0.5*|dW| @ 6bps` (line 66/71: `(W - W.shift(1)).abs() * 0.5`, `sc.diff().abs() * 0.5`,
   `COST = 6/10000`). The campaign convention since the 09-07 costfix (b268e52, champion
   of record + all 13 rawew13v2 sleeves) is FULL `|dW| @ 6.4bps`. A faithful V2 re-emit
   under-charges blend+throttle turnover exactly the way the archived 40.84%-era champion
   did before iter11.
2. **B3momhml is UNCOSTED (disclosed flaw, load-bearing).** Its own meta: "no-cost-here",
   "NOT gate-passing ... Kept as reference only". Swapping in E1's costed series
   (`E1_20yspan/work/B3momhml_costed.csv`, 6bps one-side half-turn) moves the BAL book by
   **-3.47pp CAGR** (89.44% -> 85.98% post-costfix rebuild; pinned
   `test_v2_b3_uncosted_premium`). The vt'd uncosted premium on the sleeve itself is
   3.628bp/day = 9.14%/yr at slot weight ~4.5%.

### The post-costfix sandbox rebuild (executed, NOT emitted)

Through the UNMODIFIED builder on today's tree (3 drifted pool sleeves: QAxasts, dualmom,
brwt — exactly b268e52's trio; other 10 byte-identical since c745682):

| book | maxdev vs committed | CAGR | arith | SR | MDD | neg yrs |
|---|---|---|---|---|---|---|
| BALANCED | **3.107e-03 DIFF** | 89.44% | 64.52% | 6.12 | **-7.21% (breach)** | **1 (2006)** |
| SAFE | **6.160e-03 DIFF** | 80.26% | 59.46% | 6.10 | -7.90% | 1 (2006) |
| AGGRESSIVE | **6.206e-03 DIFF** | 99.07% | 69.58% | 6.13 | -7.35% | 1 (2006) |

(The committed pre-costfix vintage: BAL CAGR 90.45% / arith **65.05%** — the JSON's
"ann": 65.1 is the ARITHMETIC convention, matching to 0.05pp; SR 6.17 / MDD -7.15% /
1 neg year. Committed SAFE breaches -7.90% and committed AGGR -7.53% too.)

The DIFFs equal the coordinator banner's numbers exactly — input drift is the only knob
that moved; the builder math is unchanged (consistent with HUNT_TREASFUT R4).

### Compliance matrix (sandbox variants, BAL book)

| variant | CAGR | arith | SR | MDD | neg | verdict |
|---|---|---|---|---|---|---|
| committed-rebuild (half 6.0bps, B3 uncosted, MHX in) | 89.44% | 64.52% | 6.12 | -7.21% | 1 | gate-2 violation |
| + full \|dW\| @ 6.4bps | 87.26% | 63.36% | 6.01 | -7.84% | 1 | cost-fixed |
| + costed B3 (half 6.0bps) | 85.98% | 62.67% | 5.97 | -7.17% | 1 | still half-turn |
| + full 6.4 + costed B3 | 83.83% | 61.51% | 5.85 | -7.29% | 1 | **V3-shaped, MHX caveat stands** |
| fully compliant + drop MHX | 63.78% | 49.92% | 4.83 | **-9.97%** | 1 | MDD collapses |

MHX borrow (CAMP_SHORT R5a, cited not duplicated): mean |short|/NAV 0.2960 pre-vt ->
EASY +0.148% / MEDIUM +0.592% / HARD +2.368%/yr on the vol-targeted book; MHX mean slot
weight 3.87% -> worst-case ~0.09pp/yr book drag. Disclosable, not disqualifying.

### Verdict (AUDIT_CHAMP2 R5a): DROP — V2 stays deprecated; no re-emit

- A faithful re-emit stamps IDENTICAL on the retired half-turn cost model and the
  uncosted B3 disclosure (-3.47pp if repaired) — re-opening a gate-2 violation.
- Every variant that REPAIRS the convention still breaches the champion wall: post-costfix
  BAL -7.21% (breach), 1 negative year (2006) in ALL variants, and the MDD>=-7%
  envelope was the original selection criterion on the pre-costfix numbers — repairing
  costs invalidates the selection.
- Even fully repaired, CAGR 83.83% @ -7.29%/1-neg-yr is a NON-champion-track artifact
  (verify_champion 0-neg + MDD>=-7% both fail). It could only ever be quoted as a
  disclosed 20y research book, never as champion or champion-overlay.
- No file in campaign/results/ was touched by this audit (sandbox rebuilds only; the
  committed V2 CSVs keep their quarantine status).

Recommended quoting language (replaces "deprecated for quoting"): "CHAMPION20Y_V2 =
superseded 20y research artifact; retired cost convention (0.5|dW|@6bps) + uncosted
B3momhml; post-costfix compliant rebuild would be 83.8% CAGR @ -7.29% MDD / 1 neg year
(AUDIT_CHAMP2 R5), which fails the champion track. Do not quote as current."

Artifacts: `campaign/agents/chief/coord/AUDIT_CHAMP2/work/r5/`
(r5_rebuild_{BAL,SAFE,AGGR}.csv, r5_{SAFE,AGGR,BAL}_full64.csv,
r5_BAL_costedB3_noMHX.csv, rebuild_vs_committed.json, v2_compliance_matrix.json).
