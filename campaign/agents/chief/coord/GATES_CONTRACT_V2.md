# GATES_CONTRACT v2 — RATIFIED (ADDITIVE successor to v1) — AUDIT_GATES2 R4 2026-09-08

> **V2.1 RATIFICATION BANNER (2026-09-09, AUDIT_GATES2 R7, insert-only):** the §8h
> placebo is now CLASS-SPLIT — the V3 per-class instruments proposed in
> HUNT_VOL2/work_r6/placebo_orthogonal_memo.md are RATIFIED as §14 below. Class A
> (|corr| > 0.50) keeps 8h exactly as flown; Class B (|corr| < 0.40) replaces the
> mistiming null with the LEVEL-MATCHED null (real dSR at p95+ of its own matched
> null); straddlers (0.40 ≤ |corr| ≤ 0.50) run BOTH, stricter reading wins. ZERO
> thresholds move; §1-13 stand exactly as ratified.

> **STEP-2 FLIP STATUS BANNER (2026-09-08, AUDIT_GATES2 R5, insert-only):** the
> section-12 Step-2 flip HAS NOW BEEN EXECUTED — commit `539f50e` (AUDIT_FWBUGS R5,
> TDD): `gates.py` `leak_on = bool(p.pop('leak_check', True))` = **DEFAULT-ON**, the
> [OLD] migration pin deleted, the two bp-positive fixtures migrated to honest T+1
> sig, and the RED-first pair landed as `campaign/bt/tests/test_fwbugs_audit_r5_leakflip.py`.
> Everything below that describes Step 2 as "SCHEDULED"/"NOT yet executed" is the
> ratification-time record and is now superseded on exactly that one point; sections
> 6/12 otherwise stand as ratified. Post-flip validation (AUDIT_GATES2 R5): landed pair
> 3/3 GREEN, R4 fixtures 3 GREEN + pin RED-by-design, suite 403 passed / 0 failed both
> with and without the R4 shadow plugin (plugin now a no-op semantics-wise; it touched
> 29 sig-less calls with zero attributable failures). `leak_check=False` remains
> measurement-only and a violation on acceptance-track calls (§6e, unchanged).

> **VERIFY-PIN REPOINT BANNER (2026-09-08, AUDIT_FWBUGS R7, insert-only — nothing below
> edited or deleted):** the R7 charter asked this agent to banner the stale
> `coord/verify_champion_standup_1140.json` citation in GATES_CONTRACT_V2.md. Measured
> audit result: **GATES_CONTRACT_V2.md contains NO 1140 citation** (exhaustive grep incl.
> line-wrap variants; neither `standup_1140` nor `standup_1830` appears anywhere in this
> file). This document's only verify pin is line-19
> `coord/verify_champion_standup_0305.json` — which is **NOT stale**: it is an ok:true
> 7/7 record whose headline (n=4805, cagr 37.19539675684982, sr 3.180994199561701,
> mdd -6.692185534307193, 0 neg yrs, sha 4358dfab95679b97) is numerically identical to
> the fresh 18:3x pin. The stale-citation issue is real but lives OUTSIDE this file, in
> the R6 round-text copied into the fleet charters + STANDUP_LOG.md (measured:
> `standup_1140` appears in 21 coord CHARTER.md files + 5 STANDUP_LOG.md lines);
> `verify_champion_standup_1140.json` is a **145-byte ok:false record** ("missing sleeve
> inputs: no --sleeve name=path given") — a failed no-args invocation, not a 7/7
> verification. **Re-point: any line citing `verify_champion_standup_1140.json` as the
> 11:4x 7/7 evidence should be read as citing `coord/verify_champion_standup_1830.json`
> (ok:true 7/7, fresh 18:3x, coordinator-run, 13-sleeve, same sha 4358dfab95679b97,
> byte-repro and cost_reconciliation 1.0000-class deviations ~1e-16); `..._0305.json`
> (line 19 here) remains valid as the 03:1x ratification pin.** No charters were edited
> by this agent (not charter-named files); the re-point is recorded here + in
> AUDIT_FWBUGS/FINDINGS.md. Fresh-clone companion audit this round: HEAD b772958
> bt/ is clone-broken (ModuleNotFoundError bt.leakcheck / ImportError bt.beats_passive
> on collection + default-on gates.run) — exact recipe and GREEN-side evidence in
> AUDIT_FWBUGS/FINDINGS.md R7.

STATUS: **RATIFIED by coordinator standup 2026-09-08 03:1x CST** - in force alongside
v1 (additive; v1 gates 1-5 unchanged per section 13). Ratification evidence re-executed by
the coordinator this session, NOT trusted from the R4 report: (a) champion of record
independently re-verified ok=true 7/7 (coord/verify_champion_standup_0305.json, sha
4358dfab95679b97 unchanged, byte-identical lineage); (b) the section-12 RED-first pair
re-run BOTH ways by the coordinator - old semantics 3 RED / 1 GREEN (KeyError: 'leak_ok'),
shadow-plugin new semantics 3 GREEN / 1 RED (the migration pin, by design) - matching
AUDIT_GATES2's reported outcomes exactly. Section-12 Step-2 flip NOT yet executed:
campaign/bt/ was live-edited by AUDIT_FWBUGS (work/r4 touched 03:00) at decision time;
the flip lands in a quiet window per the section-12 runbook step 1.

PRIOR STATUS (superseded by the ratification above): PROPOSED successor to
`GATES_CONTRACT.md` (v1, which stays in force until the
coordinator ratifies this file). Nothing here removes or weakens a v1 gate; sections 6-12
are ADDITIVE. Supersedes `GATES_CONTRACT_V2_DRAFT.md` (R3), reconciled this round against
what actually shipped in R3: `bt/leakcheck.py` + `gates.run(leak_check=True)` (opt-in,
fail-closed incl. sig=None), `bt/beats_passive.py` + `gates.run(beats_passive=True)` with
the R3 full-trio fail-closed fix, `bt/verify_champion.py` (7-check acceptance tool), and
the R3 near-miss full-tree sweep (`AUDIT_GATES2/r3/r3c_full_results.json`, 15/15 FAIL).

Provenance: every number in this file was re-derived this round from the live tree or from
a command re-run this session (champion verify_champion re-run 02:3x 2026-09-08: ok=true,
7/7 checks; NOT-A-GATE guard re-run: exit 0). Corrections vs the draft are listed in §13.
Champion of record: `campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv`
(sha256 prefix 4358dfab), independently re-verified this round: n=4805
2008-03-31..2026-08-27, SR 3.1810, cagr 37.195%, MDD −6.692%, 0 neg years, worst year
+7.31%, byte_repro max_dev 1.1e-16, cost model full_dw ratio 1.0000, causality
nav.shift(1) + truncation probes max_dev 0.0, gross max 1.6000000000007 ≤ 1.6.

DEAD_IDEAS.csv row count discipline: the charter said 108, the draft header said 107,
the file now has **120** rows (hunt agents appended 12 rows on 09-07 evening / 09-08
overnight, e.g. HUNT_COT2-R4, HUNT_MACRO2-R4, HUNT_TIMESFM, HUNT_CMDT2-R3CUR,
HUNT_CREDIT2-R3). The count moves between rounds BY DESIGN — always recount at round
start; never re-test a listed family without a pre-registered new corner (v1 §5 rule).

## 0. Two acceptance tracks (what "pass" means, explicitly)

- NEW-SLEEVE track (a candidate standalone sleeve): the full gates.run battery (v1 §3 +
  v2 §6-§7) on its own admitted span. `gates.run(...)['pass']` is necessary; it is NOT
  sufficient for T+1 (§6d) and it is NOT the champion bar (halves 0.5 / neg ≤2 vs the
  champion's 0-neg).
- CHAMPION/OVERLAY track (anything submitted as champion replacement or champion
  overlay/blend): `bt/verify_champion.py` 7/7 checks (weights_repro, byte_repro,
  cost_reconciliation full_dw, causality nav.shift(1) + truncation-invariance, gross ≤ gear,
  yearly 0-neg, mdd ≥ −7%) for a champion re-emit; blend battery §8 for an overlay.
  Canonical invocation: `bash campaign/bt/verify_champion_r3_cmd.sh` (full 13-sleeve map —
  fewer sleeves fails closed with "missing sleeve input(s)", the 09-07 footgun).
- An acceptance claim that does not name its track is incomplete. An overlay must not be
  failed for corr_to_champion (§8j) and a standalone sleeve must not be accepted on the
  blend battery alone.

## 1-5. v1 gates — UNCHANGED and still in force

v1 items 1-5 (T+1 procedural rule, costs 6.4bps full-|dW| + borrow 0.5%/yr + shortability,
gate battery a)-g), save-per-contract artifacts, honest negatives into DEAD_IDEAS.csv) are
carried forward verbatim. The only deltas are ENFORCEMENT upgrades from R2-R3, none of
which loosens v1: scramble enforced inside run() fail-closed (R2), corr ref=None fails
closed (R1), plateau all-neighbors (R1), entry trade charged (FWBUGS R1), beats-passive
trio fail-closed (R3). Thresholds stay: sr_min 1.0, h_min 0.5, neg_max 2, neg_floor −5%,
corr_max 0.15 (0.15-0.35 = "corr_ok_secondary"), p_max 0.05.

## 6. T+1 / leak gate — RESOLVED PROPOSAL (replaces draft §6a's "pending ratification")

The gap: `gates.run()` does not certify no-lookahead (R2 probe C: `sig=sign(r)` scores
SR 20.85, scr_p 0.000, composite pass=True without leak_check). `bt.leakcheck` now exists
and detects it (committed champion corr(dW_t,r_t) = −0.032 → leak=False; archived
same-day-leak vintage +0.78 → leak=True; both pinned by FWBUGS-R3 tests).

**PROPOSAL: YES, DEFAULT-ON for new sleeves — staged in two steps.**

- **Step 1 (NOW, zero code change, ratifiable immediately):** every NEW-sleeve-track
  submission MUST call `gates.run(..., leak_check=True, sig=<positions>)` and publish the
  leak dict (same_period_corr, same_period_p, lag_scan, leak verdict) in the .meta.
  Enforcement is audit-procedural (any AUDIT agent re-running without the flag gets
  scr_p=NaN/leak=None fail-closed and flags the meta). This is the actual protection;
  Step 2 is belt. Audit severity: a new-sleeve meta with no leak dict = escalated
  mis-statement (same class as R3c's 13 unverifiable scramble claims, §10a).
- **Step 2 (SCHEDULED SINGLE COMMIT, coordinator-executed when no agent is mid-round in
  bt/):** flip the `leak_check` default to ON in `gates.run`, delete the migration pin
  test, land the RED-first pair's [NEW] tests. Preconditions and measured cost below.

Why not flip the code default today: `AUDIT_FWBUGS` is live-editing `bt/` mid-round
(their work/ touched 2026-09-08 01:51) and their `test_gates_default_has_no_leak_gate`
pins default-OFF; a concurrent flip turns their green round red through no fault of
theirs (R1/R3 concurrency discipline). The flip is one line + test migration and must be
one atomic commit nobody is racing.

**Measured migration cost (shadow experiment, this round — zero edits to bt/):**
`r4/leak_default_shadow_plugin.py` patches run() to leak_check=True when the caller omits
it and the full suite runs under it (2026-09-08 02:3x):
- 27 run() calls in the suite had the default applied.
- Exactly **3** plugin-attributable failures (baseline 394 passed/2 failed is CONCURRENT
  NOISE from AUDIT_CHAMP2's own in-flight `test_audit_champ2_round4.py` — those 2 fail
  identically without the plugin and are doc-billing checks, not gates):
  1. `test_fwbugs_audit_r3.py::test_gates_default_has_no_leak_gate` — the pin; DELETE at
     flip time (its replacement IS the RED-first pair).
  2. `test_beats_passive.py::test_gates_run_opt_in` — asserts `pass is True` on a sig-less
     bp positive; under the flip it fails closed via leak_ok=False. FIX: supply `sig=`
     (the fixture has positions available) or scope the assertion to non-leak gates.
  3. `test_gates_audit_r3.py::test_r3_bp_full_trio_still_passes_genuine_alpha` — same
     shape (AUDIT_GATES2-owned file; I will migrate it with the flip commit).
- Production callers: **26 call sites in 19 files (all hunt scripts), 0 in tools/, 0 in
  bt/ internals. ZERO pass `sig=`, ZERO pass `leak_check=True`.** Every one of them is
  ALREADY composite-False via scr_ok (sig-less → scr_p=NaN fail-closed, R2). The flip
  changes NO existing verdict — it adds leak/leak_ok keys to dicts that already report
  pass=False. Verdict-neutral migration, cost ≈ 0 for production callers.
- The hole the flip closes is the sig-ful non-opt-in caller (R2 probe C's pass=True leak).
  No current caller is in that class — which is exactly why the flip is cheap NOW, before
  someone writes one.

- 6a. (Step-1 rule, mandatory at submission; see above.) Keep the per-agent
  prefix-no-lookahead harness test as a second line of defense until Step 2 lands.
- 6b. Implemented thresholds (verified in `bt/leakcheck.py` this round): leak=True requires
  |same_period_corr| ≥ MIN_ABS_CORR **0.20** AND Fisher two-sided p < **0.05** AND lag 0 is
  the argmax of the lag scan (−2..+2); MIN_OBS 30; unmeasurable ⇒ leak=NaN ⇒ fail-closed.
  Calibration pins: causal champion −0.032 not flagged, leaky vintage +0.78 flagged.
- 6c. Extra-lag stability 0..3 must degrade gracefully (MACRO2 JOINT overlay dMDD
  +1.385/+2.330/+1.817/+2.540pp at lags 0-3 is the positive precedent).
- 6d. Never cite `gates.run(...)['pass']` as T+1 evidence (it is not, even after Step 2 —
  the probe is statistical, not a proof; the §0 track rules still apply).
- 6e. `leak_check=False` on an acceptance-track call is a contract violation (it exists
  only for measurement-only module use, like `beats_passive.evaluate` subset semantics).

## 7. beats-passive — mandatory at submission for NEW STANDALONE sleeves

Shipped: `bt/beats_passive.py`, opt-in `gates.run(..., beats_passive=True, spy=, ief=,
cta=)`, ANDed into composite; acceptance layer requires the COMPLETE trio (R3 fix:
missing benchmark ⇒ reason='incomplete_trio', fail-closed; `evaluate` keeps subset
semantics for measurement). Verified in-module this round: MIN_OBS 60 and ≥50% span
coverage, ties fail, unmeasurable benchmarks skipped.

- 7a. Candidate net SR must EXCEED best of {spy_bh, sixty_forty, cta_trend} on the
  candidate's matched span at campaign costs.
- 7b. Publish per-benchmark SRs in the .meta.
- 7c. Keep the three benchmark inputs pinned (twelvedata SPY, more_etf IEF, sleeve_library
  CTA_15vol); re-fetch ⇒ re-run on open submissions.
- 7d. NEW vs draft: mandatory-at-submission for the NEW-SLEEVE track (procedural, Step-1
  style) but NOT required for champion/overlay submissions (§8's battery judges those —
  an overlay trivially beats passive through the champion and the check is uninformative
  there). R3c evidence it bites: 9/15 near-miss sleeves (SR 0.53-0.70) fail beats_passive,
  incl. all six 2018-inception COMP_50_50 variants (0.60-0.65 vs sixty_forty 0.705).

## 8. Champion-BLEND gate (overlays / w≤15% NAV additions) — RATIFIED, numbers re-verified

For any candidate submitted as champion overlay/blend (not a standalone sleeve), ALL of:
- 8a. Blend yearly: 0 negative years (champion bar).
- 8b. Blend MDD > −7%; report dMDD vs current champion.
- 8c. Blend dAnn > 0 (HARD). Re-verified: VOL2-R3 0/6 decorrelated sleeves had dAnn>0 at
  any w (best −0.69pp @2.5%); CRYPTO2-R3 best −0.77pp @ w=.025.
- 8d. dSR ≥ 0 AND dH2 ≥ 0 (CRYPTO2-R3 dH2 −0.003..−0.072 at every rung = the bite).
- 8e. Blend gross ≤ 1.6, full |dW| @ 6.4bps one-side.
- 8f. Halves-consistency of the DELTA (report dSR_H1, dSR_H2 separately).
- 8g. w-plateau across the rung grid (plateau_ok logic on the rung grid); relever-to-cap
  variants need the same ladder disclosure (CRYPTO2 0/5, VOL2 0/30).
- 8h. Vol/corr-matched placebo, 200 draws: a delta the placebo reproduces is arithmetic
  (VOL2: 2/6 pure artifact, frac_pos=1.000; SECTOR2-R3: A11 +0.141@15% 100% reproduced).
- 8i. Single-episode exclusion test on dMDD: recompute excluding the dominant dd window;
  relief must stay ≥ +0.5pp. Re-verified from STANDUP_LOG.md:958-961 this round:
  T10Y2Y +1.161pp → +0.319pp excl 2018-05..07 (REJECTED); JOINT +1.495 → +0.653
  (broad-based, still not adopted on the −2.7pp ann trade).
- 8j. Report corr_to_champion for overlays but do not fail on it (0.94-0.98 is expected);
  the acceptance path is 8a-8i. Do not cite corr_ok=False as an overlay's rejection reason.

## 9. span_class discipline (data admission) — RATIFIED

Implemented in `DATA_ETF_MORE/work_r3/manifest_r3.py` + `retest_r3.classify` (both
re-verified present this round). 9a: every new series carries span_class ∈ {pre2007,
2007plus, inception_fail} (bounds 2007-01-01/2013-01-01); inception_fail not
hunt-eligible. 9b: materially-short spans are judged as such (EM-HY n=753 = unjudgeable,
failed closed anyway). 9c: champion-eligible NEW sleeves demonstrate the battery on ≥
their admitted span with span_class printed next to every gate number. 9d: metas pin the
manifest vintage (sha/mtime) of every price file consumed (CMDT2 GLD extension rotated
SR 0.35→0.17).

## 10. Artifact verifiability (audit requirement) — RATIFIED

- 10a. Every .meta gate number reproducible from published artifacts. Positions or signal
  series must be published, or scramble claims labeled "agent-run, not
  artifact-verifiable" (R3c: 13/15 near-miss metas currently unverifiable).
- 10b. Champion-vintage pinning: metas name champion file + sha256 prefix used (R3c: the
  costfix re-emit moved 15/15 corrs, max 0.0042; all 13 corr-bearing metas matched the
  OLD vintage within ±0.0020 — provable only by git reconstruction, hence pin it).
- 10c. Scale lock: retired SR≥0.6-scale labels must be re-labeled on re-read; contract
  scale is SR ≥ 1.0.

## 11. Composition-preserving scramble = DIAGNOSTIC, never a gate — RATIFIED

`AUDIT_GATES2/r3/r3b_composition_scramble.py`: champion p=0.775 (common-lag), noise flag
rate 9/200=4.5% nominal, DETECT fixture p=0.010; per-slot lags are a negative result
(p degenerates to 1.000 — synchrony probe, not timing). Guard re-run this round:
`r3/not_a_gate_guard.py` exit 0, "NOT-A-GATE GUARD: OK". Never wired into gates.run;
use to UNDERSTAND timing, never to accept/reject.

## 12. The Step-2 flip execution plan (coordinator runbook, one commit)

1. Confirm no agent mid-round in bt/ (check AUDIT_FWBUGS / any hunt agent ROUNDS).
2. `gates.py`: `leak_on = bool(p.pop('leak_check', True))` (one line) + docstring update.
3. Delete `test_fwbugs_audit_r3.py::test_gates_default_has_no_leak_gate`.
4. Add `sig=` to the two bp-positive fixtures (`test_beats_passive.py::test_gates_run_opt_in`,
   `test_gates_audit_r3.py::test_r3_bp_full_trio_still_passes_genuine_alpha`) so their
   `pass is True` assertions test alpha, not leak-absence.
5. Move `AUDIT_GATES2/r4/test_r4_leakflip_pair.py`'s four tests into `campaign/bt/tests/`
   (drop the [OLD] pin) — RED-first pair already executed this round: old semantics
   3 RED/1 GREEN (KeyError: no leak gate), new semantics 3 GREEN/1 RED (pin fails, by
   design). bt/gates.py was NOT touched this round; "new semantics" was demonstrated with
   the semantics-identical shadow plugin.
6. Full suite green; grep 26 production call sites unaffected (verdict-neutral, §6).

## 13. Diff vs V1 (point-by-point) + corrections vs the R3 draft

| v1 item | v2 disposition |
|---|---|
| 1. T+1/no-lookahead (procedural) | KEPT procedural for the harness + UPGRADED to measured: §6 leak_probe mandatory at submission (Step 1) / default-on (Step 2, §12 runbook). `pass` still is not T+1 proof (6d). |
| 2. Costs 6.4bps full-\|dW\| + borrow + shortability | UNCHANGED; enforcement proven by verify_champion cost_reconciliation (model=full_dw, ratio 1.0000) on the champion of record. |
| 3a. SR ≥ 1.0 | UNCHANGED (near-miss sweep: 15/15 library sleeves 0.53-0.70 fail it; 9/15 also fail beats-passive). |
| 3b. plateau | UNCHANGED threshold; enforcement hardened R1 (all-neighbors, half-spike rejected). |
| 3c. halves ≥ 0.5 | UNCHANGED for new sleeves; champion bar stays 0-neg-years (§0 two tracks; 8a). |
| 3d. yearly ≤2 neg > −5% | UNCHANGED for new sleeves; 0-neg champion bar via verify_champion check 6 / 8a. |
| 3e. scramble 200x | UNCHANGED threshold; enforcement upgraded R2 (in run(), fail-closed without sig). Composition-scramble stays OUT (§11 guard). |
| 3f. decorrelation 0.15/0.35 | UNCHANGED for new sleeves; overlays exempt via 8j (report, don't fail). ref=None fail-closed (R1). |
| 3g. vol-target trailing-only, clip ≤3.0 | UNCHANGED (R1 probe: trailing-only verified, clip observed [0.277, 1.0]). |
| 3h. economic rationale in .meta | UNCHANGED. |
| 4. save-per-contract artifacts | UNCHANGED + §10a (positions/signal published or scramble labeled unverifiable) + §10b (vintage pin). |
| 5. honest negatives | UNCHANGED; DEAD_IDEAS row count is dynamic (120 as of this round — recount, don't trust quoted counts). |
| (nothing) | NEW §6 leak gate, §7 beats-passive (new standalone sleeves), §8 blend battery, §9 span_class, §10 artifact verifiability, §11 diagnostic, §0 two-track rule, §12 flip runbook. |

Corrections vs `GATES_CONTRACT_V2_DRAFT.md` (carried here): (1) header row count 107 →
dynamic/120 (§ preamble); (2) §6a "opt-in pending ratification" → resolved two-step
proposal with measured migration cost (§6/§12); (3) §7 near-miss count restated with its
source artifact (`r3/r3c_full_results.json`, 9/15) — unchanged number, now traceable;
(4) everything else in the draft was re-verified against the live tree and ships verbatim
(thresholds, blend battery numbers, span_class files, guard).

## 14. V2.1 per-class placebo instruments (§8h redefined per candidate class) — RATIFIED 2026-09-09, AUDIT_GATES2 R7

**Status:** IN FORCE. ADDITIVE successor section to V2 (sections 1-13 untouched; this
section only re-specifies HOW the §8h placebo null is constructed, per candidate class).
Source proposal: `coord/HUNT_VOL2/work_r6/placebo_orthogonal_memo.md` §3 (adopted
exactly as proposed; see "Boundary instantiation" below for the one place the memo's
"~0.5" is made exact, fail-closed). Reference implementation (VALIDATED, not
reimplemented): `coord/HUNT_VOL2/work_r7/class_b_placebo.py`, pinned by
`campaign/bt/tests/test_placebo_class_b.py` (10 tests) +
`coord/HUNT_VOL2/work_r7/test_class_b_placebo.py` (15 tests). Still NOT wired into
`bt/gates.py` — the instrument is invoked by submission metas/auditors; the
no-leak guard test pins that gates.py carries no placebo surface.

### 14a. Why (the documented §8h failure mode)

§8h-as-mistiming (circular shifts / matched random trims) is a valid significance
instrument exactly when a candidate's blend delta lives in CO-MOVEMENT with the
champion (Class A overlays). For an ORTHOGONAL positive-mean candidate the mistiming
null saturates by arithmetic: variance reduction is shift-invariant, mean injection
survives re-ordering, and the dSR metric rewards both (coordinator R6 measurement on
RB_hobr corr_champ +0.0219: 169/200 mistimed draws reproduce the blend dSR delta —
an instrument reading, not a sleeve failure). Class B instead prices mean-injection
OUT of the statistic.

### 14b. The classes (routing on |corr to champion|)

| class | band | instrument |
|---|---|---|
| A — correlated overlay | \|corr\| > 0.50 | §8h AS FLOWN, UNCHANGED (vol/corr-matched Gaussian or matched-trim null, 200 draws; a delta the null reproduces is arithmetic) |
| B — orthogonal standalone/blend | \|corr\| < 0.40 | **B1 LEVEL-MATCHED null**: 200 block-bootstrap draws of the candidate's OWN stream, re-matched on (mean, vol) EXACTLY and (skew, ac1) approximately (moment-retry within the candidate's own data family — no synthetic observations). SURVIVES only if the real blend dSR sits at **p95+ of its own null** (P_TAIL 0.95) |
| STRADDLER | 0.40 ≤ \|corr\| ≤ 0.50 | BOTH instruments; **stricter reading wins** (any PLACEBO_ARTIFACT kills) |

Boundary instantiation: the charter/memo phrase "Class B (|corr|<0.5)" resolves into
the B band plus a straddler belt [0.40, 0.50] that runs both instruments — strictly
STRONGER than treating everything <0.5 as B-only (fail-closed direction; band values
0.40/0.50 themselves route to STRADDLER). These are instrument-routing bands, NOT
moved thresholds: the §8j corr gates (0.15/0.35), 8a-8g/8i/8j and every §1-13 number
are untouched.

### 14c. Reading rules and safety rules

- The timing-split (B2 subsample halves) is DEMOTED TO DIAGNOSTICS-ONLY per §11 — it
  emits no verdict and can never accept or reject anything (reference impl returns
  `status="DIAGNOSTIC_ONLY_never_a_gate"` and no `verdict` key).
- A placebo verdict can NEVER upgrade a candidate: composite survival requires EVERY
  run instrument to read SURVIVES_PLACEBO.
- A placebo is never the SOLE downgrade outside its domain: the class split IS that
  guarantee (each class is judged by the instrument built for its geometry), and
  straddlers — the ambiguous belt — get both readings with the stricter one.
- Placebo verdicts are NECESSARY-CONDITION readings, never adoption claims: adoption
  still requires the FULL V2 battery (8a-8j incl. leak_probe, 8c dAnn>0 capital-real).
  The reference impl hard-codes this (`not_an_adoption` field on every verdict).
- Determinism: every instrument takes an explicit seeded `rng`; nulls are seeded and
  reproducible (validation JSONs are byte-stable across re-runs).

### 14d. Re-analysis exposure (bounded)

All historical §8h applications in the fleet are Class A (VOL2-R3 2/6 frac_pos=1.000;
SECTOR2-R3 A11 100% reproduced; VOL2-R5 z +10.3/+12.5) — every past verdict is
UNCHANGED under V2.1. The one Class-B case in flight (RES_BASIS row 132/137,
RB_hobr) was NOT adopted or rejected on a placebo: its R6 rejection rested on 8c
(capital-real dAnn −0.9069pp at every certifiable rung), which V2.1 does not touch;
B1 is the instrument for any future book-level placebo at an adopted w.

### 14e. Ratification evidence (AUDIT_GATES2 R7, all commands re-run this round)

- Pair tests: `25 passed in 6.29s` (10 bt + 15 author-dir). RED-first contract
  demonstrated live: with the helper unreachable, collection fails with exactly
  `class_b_placebo.py helper missing (RED-first contract)` — it does NOT skip.
- Known-cases validation reproduced deterministically (HOBR Class-B, full 14-sleeve
  re-solve machinery): real dSR 0.090872 → percentile 0.995 (≥0.95 SURVIVES; published
  p1.00), real dAnn −0.009069 → percentile 0.015 (published p0.00), null dSR p50
  0.041576 / p95 0.069367; Class-A geometry: synthetic rho=−0.15 → frac_null_dsr_pos
  1.0 PLACEBO_ARTIFACT, rho=0 control → 0.0 SURVIVES (discriminator works).
  `charter_validated: true`; zero thresholds moved; gates.py untouched.
- Independent calibration (AUDIT_GATES2 `work_r7/r7_class_b_calibration.py`, fresh
  run): Lane 1 real-sleeve — A11 frac 1.0 PLACEBO_ARTIFACT / MSSW 0.0 SURVIVES
  (matches published direction); Lane 2 coin false-pass 1/60 = 1.67% ≤ 5% nominal
  (binom 95% CI 3.24%), uniformity quintiles [0.156, 0.314, 0.487, 0.590, 0.796],
  median 0.487 ≈ 0.5, top 0.796 vs the 0.95 bar = mild fail-closed conservatism; Lane 3
  power 30/30 timed candidates survive, 0/30 negative-timing controls survive.
- Fail-closed pins (tests): NaN interior, zero-vol, short span, block bounds, n_nulls
  < 2, index mismatch, w outside (0, 0.15] all raise ValueError — no silent pass.
