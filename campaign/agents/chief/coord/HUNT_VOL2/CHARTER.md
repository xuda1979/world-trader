# CHARTER: HUNT_VOL2 — options-implied vol term-structure round-2 (VVIX/SKEW/GVZ/OVX)

ROUND 1

Prior VXV/VIX term-structure overlay was dead. Test NEW vol-surface features from more_vol
(9 vol series) as RISK-ON/OFF or HEDGE overlay, not just term-structure:
 (a) VVIX (vol-of-vol) level/change as a risk-off timing gate.
 (b) SKEW (25-delta) change: sharp SKEW rise -> equity/commodity risk-off tilt.
 (c) VIX9D vs VIX3M vs VIX6M short-term term-structure as a 2-3 window signal.
 (d) GVZ(gold vol)/OVX(oil vol) as asset-specific vol-timing overlays.
 (e) Cross-asset vol (VIX/GVZ/OVX ratio) as relative-value signal.
Implement as T+1 overlays or standalone vol-timing sleeves, 6.4bps full-|dW|, all gates,
|corr|<0.15 vs champion. Data tools/quant/data/more_vol/*.csv (VIX,VIX3M,VIX6M,VIX9D,VVIX,SKEW,
GVZ,OVX,RVX,VXV,VIXMO). Read GATES_CONTRACT.md first.

## ROUND 2 (coordinator standup 2026-09-07 01:3x)
R1: standalone vol gates dead; VVIX-trim passed scramble but -6.7pp ann as overlay. Round 2
reuses the R1 167-variant machinery for champion-integrated designs R1 flagged promising but
sparse:
 (a) VVIX-spike DE-RISK on champion only when VVIX z>2 AND champion trailing-20d return<0
     (conditional, not unconditional trim - targets the sparsity R1 diagnosed).
 (b) SKEW 5d-change tail-gate: scale gross 1.6->1.0 for 10d after extreme SKEW jumps.
 (c) VIX9D/VIX term-structure inversion (9d>3m) sustained 3d as short-horizon de-risk.
 (d) VIXMO (5y data only) as an out-of-sample check of the round-2 winner on 2018.
Measure CHAMPION deltas (ann, MDD, worst-year); require ann delta > +0.3pp net of costs.
End FINDINGS.md with ROUND 2 DONE.
## ROUND 3 (coordinator standup 2026-09-07 07:2x CST)
Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv (90 rows) FIRST - do NOT re-test any
listed-dead family; do NOT re-tune a dead signal into a new config (that is p-hacking). Honest
negatives with exact numbers are fine results. Every claim must reproduce from a script you save.
FLAGSHIP round-3 lane - champion-blend integration. Champion (39.85 pct ann, SR 3.296,
0/19 negy, MDD -6.84 pct, gross exactly 1.6) cannot lever up (cap 1.6) and every de-risk overlay
subtracts. The one honest path to more profit: ADD small weights of decorrelated positive-SR
sleeves. Charter:
 (a) Candidate pool: published sleeves AS-IS (no re-fit), own-span net SR >= 0.5 AND
     abs(corr vs champion) <= 0.35: expected HUNT_SECTOR2 Arm A (0.679/-0.147) + composite,
     HUNT_CMDT2 sector-rot (0.40 = below bar, list as rejected with numbers), R1 crypto TS-mom if
     submitted (4/10 negyr, expect reject but test), library CTA_15vol / Multi_Strategy_SharpeW
     (note the 0.87 cross-corr: pick ONE). Candidates arriving mid-run may be admitted.
 (b) Blend machinery: champion_net*(1-w) + sleeve_net*w for w in 2.5/5/7.5/10/15 pct NAV, FULL
     honesty: blend-weight drift turnover at 6.4bps FULL dW; margin delta via bt/borrow.py; short
     legs via bt/shortability pregate with CAMP_SHORT tiers (work_r3/BLEND_PREGATE.md when ready).
 (c) ADOPTION gates (report exact deltas at every w): negy stays 0/19; MDD stays > -7 pct;
     dAnn > 0; dSR >= 0; daily gross <= 1.6; dSR > 0 in BOTH halves; w-plateau (not knife-edge);
     ADVERSARIAL CONTROL: vol-and-corr-matched RANDOM sleeve at same w must NOT show consistent
     dSR>0 across 200 draws (else the gain is a diversification artifact, not signal).
 (d) Output blend table (candidate x w -> dAnn/dSR/dMDD/negy/gross) + recommendation JSON in
     work_r3 + FINDINGS. Do NOT modify the committed champion or other agents' files. A
     recommendation of nothing-adoptable with exact numbers is a fine result.

## ROUND 4 (coordinator standup 2026-09-07 17:2x CST) - fleet drained, R3 all-honest-negative; capacity restored (CIO round-4b: options-skew sleeve, data-coupled)
(a) If DATA_FREDMORE has landed usable CBOE history: test cross-sectional pc_vol/skew/atm_iv
    as a champion-eligible sleeve per GATES_CONTRACT (SR>=1, halves>=0.5, neg-yrs, scramble,
    abs corr<0.15). FULL honest cost stack. If data is absent/short-span (<8y), say NOT
    JUDGEABLE and stop - do not force a verdict on a short sample.
(b) Regardless: switch your library-sleeve candidates to the BLEND_PREGATE (R3 CAMP_COST/
    CAMP_SHORT finding: blend_r3_lib.py already-costed assumption is wrong) and re-state your
    R2/R3 blend pool verdicts under the pregate. 2-3 sentence delta summary required.
Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv (108 rows) FIRST - do NOT re-test any dead family without an explicitly pre-registered new corner. Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv ann 37.195 pct / SR 3.181 / MDD -6.69 pct / 0 neg yrs (re-verified 17:0x, 7/7 checks ok). End FINDINGS.md with exactly: ROUND 4 DONE

## ROUND 5 (coordinator standup 2026-09-08 04:0x CST) - fleet drained 21/21 R4 ALL-HONEST-NEGATIVE; capacity restored; GATES_CONTRACT_V2 RATIFIED
READ FIRST: coord/GATES_CONTRACT_V2.md (RATIFIED 2026-09-08 03:1x CST, supersedes V1; V1 gates
1-5 unchanged) + campaign/results/DEAD_IDEAS.csv (recount rows yourself; 120 at R4-end, dynamic).
Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv ann 37.1954 pct / SR 3.1810 /
MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), champion sha 4358dfab95679b97 -
re-verified fresh 04:0x by the coordinator, 7/7 checks ok (verify_champion_r3_cmd.sh pattern).
R4 verdict across all 21: ZERO adoptable alpha; honest frontier UNCHANGED (ann 37.2 vs 80 goal).
The R4 TimesFM kill generalizes: single-era lifts (Mar-2020-only) are NOT repeatable sleeves -
the span gate (>=8y of effect) is the bar. No dead-family re-test; no re-tuning a dead signal
into a new config (p-hacking ban); your R5 corner is pre-registered below and must be
data-backed (cite fetched source files + row counts in FINDINGS). bt/ is a QUIET tree this
round - only the charter-named agents (AUDIT_FWBUGS flip; AUDIT_GATES2 validate; AUDIT_CHAMP2
card fix) touch bt/ or campaign/*.md, and only the named files. Submissions carry the FULL V2
battery incl. mandatory leak_probe (V2 section-6 Step 1; the gates.run default flip lands this
round - do not depend on either state, pass sig= and leak_check=True explicitly).
End FINDINGS.md with exactly: ROUND 5 DONE
 (a) NEW CORNER (pre-registered): CBOE put/call archive 1995-2019
 (tools/quant/data/cboe_pcr/_raw/ 10/10 byte-identical; stitched pcr_covariates_SPY_daily.csv
 PIT strictly-prior, 1-session-carry cap, NaN after 2019-10-07). Vol-timing OVERLAY evaluated
 ONLY over 2006-2019 (frozen archive - disclose that hard limit; NOT a current-day signal).
 Era-robustness WITHIN the window is the gate (TimesFM single-era kill applied).

## ROUND 6 (coordinator standup 2026-09-08 11:5x CST) - fleet drained 21/21 R5 ALL-HONEST-NEGATIVE; ONE live V2-PASS candidate pending adoption; capacity restored; CONSOLIDATION round
READ FIRST: coord/GATES_CONTRACT_V2.md (in force; pass sig= and leak_check=True explicitly) +
campaign/results/DEAD_IDEAS.csv (recount rows yourself; 137 at R5-end, dynamic).
Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv ann 37.1954 pct / SR 3.1810 /
MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), champion sha 4358dfab95679b97 -
re-verified fresh 11:4x by the coordinator, 7/7 checks ok (13-sleeve verify_champion.py run,
json pinned coord/verify_champion_standup_1140.json; bt suite 410/0 coordinator-run 11:4x).
R5 verdict across all 21: ZERO adoptable alpha from the fleet; frontier UNCHANGED (37.2 vs 80
goal). NEW: team agent RES_BASIS-R1 submitted RB_hobr_crack_hyst_w63_z10_zo10 (heating-oil/
Brent crack hysteresis, sleeve sha da0285b9a7a5e6a2, DEAD_IDEAS row 137) as standalone
V2-PASS pending coordinator adoption. Coordinator independent checks 11:4x: sleeve sha MATCH;
blend arithmetic REPRODUCED (dSR +0.199 / dAnn +4.21pp / dMDD +0.05pp at w=0.25, fill-0
convention); rung grid w=0.05/0.10/0.15 all dAnn>0 dMDD>0 0 neg yr. OPEN concerns: (8e) gross
<=1.6 after re-solve (champion rides the cap exactly); halves H2 0.753 vs H1 2.182; IS/OOS
2.145/0.807 disclosed; AND the coordinator's 200-draw circular-shift placebo at w=0.25
reproduces the dSR delta in 169/200 draws - the blend delta is mean-injection-dominated
(expected for an orthogonal candidate, corr_champ +0.0219; the 8h instrument was built for
correlated overlays). Adoption is NOT decided - it must EARN a full rebuild verdict (see
CAMP_COST charter). No dead-family re-test; no re-tuning a dead signal into a new config
(p-hacking ban). bt/ is a QUIET tree except charter-named agents and the named files.
End FINDINGS.md with exactly: ROUND 6 DONE

 (a) FRAUD-CATCH cross-verification: reproduce HUNT_MACRO2's R5 verdicts from published
 artifacts with your own code. Mismatch -> escalate.
 (b) METHODOLOGY MEMO (docs-only, work_r6/placebo_orthogonal_memo.md): formalize the
 circular-shift placebo discipline you pioneered (0/200 draws) AND its documented failure mode
 for ORTHOGONAL positive-mean candidates (coordinator measurement 11:4x: RES_BASIS crack sleeve
 at w=0.25 reproduces dSR in 169/200 mistimed draws - the 8h instrument was designed for
 CORRELATED overlays, corr 0.94-0.98). Propose the correct significance instrument per candidate
 class (correlated overlay vs orthogonal standalone vs 14th-sleeve addition). NO gate/threshold
 changes - this is a memo for the V3 contract discussion, not a contract edit.

## ROUND 7 (coordinator standup 2026-09-08 18:3x CST) - fleet drained 19/20 R6 (AUDIT_GATES2 finishing in flight); HOBR adoption REJECTED on 8c; placebo instrument formalized Class A/B; 2 NEW-DATA corners + refresh-adoption centerpiece
READ FIRST: coord/GATES_CONTRACT_V2.md (in force; pass sig= and leak_check=True explicitly; VOL2's V3
per-class placebo is a PROPOSAL until AUDIT_GATES2 ratifies it THIS round - do not depend on either
state) + campaign/results/DEAD_IDEAS.csv (recount rows yourself; 145-146 at R6-end, dynamic).
Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv ann 37.1954 pct / SR 3.1810 /
MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), champion sha 4358dfab95679b97 -
re-verified fresh 18:3x by the coordinator, 7/7 checks ok (13-sleeve run, pinned
coord/verify_champion_standup_1830.json; cost 5.2622 bp/yr full_dw of the 6.4 budget; gross rides
the cap at exactly 1.6).
R6 verdict across the fleet: ZERO adoptable alpha. RB_hobr adoption formally REJECTED on 8c -
capital-real dAnn -0.9069pp at every constructible rung; the +4.21pp standup number was a fill-0
artifact breaching 8e; 8e RESOLVED (gross is CONSTRUCTED at exactly 1.6 by weight normalization -
there is no re-lever headroom); the Class-B level-matched placebo confirmed timing is real but the
CAGR trade is negative (real dSR p1.00 / real dAnn p0.00 vs its own null). Refresh staged
source-limited (brwt10/7/5 -> 08-28, diescrack -> 08-24; disclosed unreachable: EIA spots end
09-01, diesel/HO newdata end 08-25). All R6 cross-audits CLEAN - zero fraud in ~12 independent
rebuilds; frontier UNCHANGED (37.2 vs 80 goal).
GROUND RULES (unchanged): no dead-family re-test; no re-tuning a dead signal into a new config
(p-hacking ban); your corner below is pre-registered and must be data-backed (cite fetched source
files + exact row counts in FINDINGS); new sleeves DECORRELATE from the champion first (corr gate
0.15/0.35) and clear the FULL V2 battery incl. leak_probe; weekly-or-slower rebalance unless your
lane states otherwise; honor 6.4 bps full-|dW| cost, IBKR call-rate/borrow realism, non-shortable
universe, 0 negative years, gross<=1.6. bt/ and campaign/*.md are QUIET except your charter-named
files. Concurrent-writer discipline on shared ledgers: re-read the tail before append, end your
row with a trailing newline, recount after append. bt suite at R6 close: 426/0.
End FINDINGS.md with exactly: ROUND 7 DONE
 (a) CENTERPIECE - V3 REFERENCE IMPLEMENTATION (not a contract edit;
 AUDIT_GATES2 ratifies): build the Class-B LEVEL-MATCHED null exactly per your R6 memo (200
 block-bootstrap draws matched on mean/vol/skew/autocorr; real dSR must sit at p95+ of its own
 null; timing-split demoted to diagnostics-only; straddlers run BOTH instruments, stricter
 reading wins) as a reusable helper + tests in YOUR dir (TDD RED-first), plus ONE charter-named
 test file campaign/bt/tests/test_placebo_class_b.py pinning behavior on a synthetic fixture.
 Validate against both known cases: VOL2-R3 frac_pos=1.000 (Class A - 8h unchanged) and the HOBR
 Class-B result (real dSR p1.00 / real dAnn p0.00). ZERO thresholds move; gates.py UNTOUCHED by
 you. (b) DEAD_IDEAS recount; no new vol corner (pcr dead 0/224 + 0/148 stand).

## ROUND 8 (coordinator standup 2026-09-09 04:03 CST) - fleet drained 21/21 R7 DONE; capacity restored (16 procs); domains closed: audit rotation + seeded lanes
READ FIRST: coord/GATES_CONTRACT_V2.md (RATIFIED, supersedes V1) + campaign/results/DEAD_IDEAS.csv
(recount rows yourself; 153 at R7-end, dynamic). Champion of record: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
ann 37.1954 pct / SR 3.1810 / MDD -6.6922 pct / 0 neg yrs / n=4805 (2008-03-31..2026-08-27), sha 4358dfab95679b97,
re-verified 2026-09-09 03:5x standup via 23:40 artifact (bytes unchanged since Sep 7 11:24, ok=true 7/7).
R7 verdict across all 21: ZERO adoptable alpha; honest frontier UNCHANGED (ann 37.2 vs 80 goal).
HARD RULES: no dead-family re-test; no re-tuning a dead signal into a new config (p-hacking ban); all r8 work
stays in YOUR OWN dir; nothing is applied to bt/, shared data trees, or the champion without explicit chief
instruction; honest negatives with exact numbers are fine results; every claim must reproduce from a script you save.

YOUR R8 LANE: SEEDED LANE (r7 close-out): FINDINGS prose errata - your prose states a metric 0.063 while the artifact max is 0.1901; write ERRATA.md in YOUR dir reconciling every prose-vs-artifact divergence with exact numbers + artifact filenames. Then AUDIT ROTATION: 4 other-family DEAD_IDEAS rows reproduced from cited scripts.
End FINDINGS.md with exactly: ROUND 8 DONE


## R8 ADDENDUM (coordinator standup 2026-09-09 ~21:5x CST) - CHAMPION OF RECORD UPDATED: supersedes the champion sha/stats lines in the ROUND 8 header above
At 19:03 2026-09-09 the R7 RAWEW15 refresh candidate was PROMOTED in place to champion of record (ratified by
the 59th coordinator standup, independently re-verified fresh 21:5x: coord/verify_champion_standup_2150.json,
ok=true 7/7). Champion of record NOW: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv, n=4806 (2008-03-31..2026-08-28),
ann 37.4923 pct geo / SR 3.1951 / MDD -6.6922 pct / 0 neg yrs (worst +7.31 pct 2013) / cost 5.2734 bp/yr full-dW
of the 6.4 budget / gross 1.6 exactly (0 overshoot) / margin 2.70 pct-yr / causal nav.shift(1) + 7 truncation
probes dev 0.0 / champion sha 8d7e711e6d05a2b1 / weights sha 8c19ef227cf9b7b0 (== the RAWEW15 candidate shas
CAMP_COST pinned at R7; weights VALUES unchanged, row order only - no refit, IS<2017 fit rule intact; champion
rows pre-2026-08-12 byte-identical to archived pre-promotion bytes, tail extension only). Pre-promotion bytes
archived as archive_*_ann37.20.csv.
THEREFORE: the header lines above quoting sha 4358dfab95679b97 / n=4805 / 37.1954 / 3.1810 / 5.2622 bp/yr are
SUPERSEDED. Do NOT flag the champion byte change as divergence, tampering, or fraud - it is the sanctioned,
coordinator-ratified promotion. Baseline for any no-gate-regresses comparison in your lane is now
37.4923 / 3.1951 / -6.6922 / 0-neg / 5.2734 bp/yr.
