

========================================================================
## HUNT_SECTOR2 — ROUND 2 (2026-09-07, session resumed after prior 429 deaths)
========================================================================
Charter: (a) RS-ratio rotation, (b) sector-bond barbell w/ VIX gate, (c) XLE-vs-CRUD
lead-lag, (d) XLU/IEF stealth-rate. Gates per GATES_CONTRACT.md; 6.4bps one-side FULL
|dW| + 0.5%/yr borrow; T+1; trailing-only VT10 clip3. Champion ref:
GOAL100_RAWEW13v2_WEIGHTED_GEAR16 (SR 3.296, ann 34.1%, 2008-03-31..2026-08-27, n=4805,
0 neg years). TDD: tests_tdd.py 13 -> 16 green (3 added RED first: window_check guard,
2008-book row count, weekly grid preservation; all turned green).

PRIOR-SESSION STATE (found on arrival): lib + 13 tests + 2 scripts existed, sleeves/
EMPTY, no FINDINGS.md, stale /tmp/sector2_scan.csv (02:09) from a run killed by 429
rate-limits (8 backoffs in logs/HUNT_SECTOR2.log). DIAGNOSIS CORRECTED IN SESSION:
stale scan showed n=2048 on every variant. I first hypothesized silent window
truncation and wrote a fail-closed window_check guard (TDD). Later checks showed 2047
rows is exactly the XLC-bound 11-SPDR window (2018-06-20..2026-08-12) AND IEF.csv/
XLK.csv were re-fetched at 04:16-04:23, AFTER the 02:09 scan -> the stale scan ran on
mid-refresh data (2048 = a fetch page limit) and is INVALID. Discarded; everything
below is a fresh complete-data rerun (books 4682-4697 rows, 2008-01-02..2026-08/09).
window_check kept as a legit fail-closed regression guard.

SCAN (hunt_sector2_r2_scan.py, 72 variants, full-window, guards green):
  A RS-ratio (log sector/SPY) mom, S9 2008+ window, lb{63,126,189,252} x k{2,3,4} x {long,LS}: 24
  A11 same on literal 11-SPDR charter set (XLC binds window to 2018-06-19):      9
  B risk/def spread mom x VIX gate {off,mean100,mean110} x {IEF,IEFhalf}:       18
  C XLE/CRUD lead-lag, w{42,63,126} x {switch,longflat}:                         6
  D XLU/IEF stealth-rate, lb{21,63,126,252} x {riskoff,riskon} x {IEF,DEF,FLAT}: 24
  /tmp/sector2_r2_scan.csv, 72 rows, 0 dupes.

ARM HEADLINERS -> DEFINITIVE GATE BLOCK (hunt_sector2_r2_gates.py, 200x scramble):
  A_rs_ratio  A|lb252|k4|long   n=4682 SR=0.534 ann=6.0% H1=0.38 H2=0.70 negyr=3/19
              worst=-10.1% corr_champ=-0.042 lib_maxabs=0.87 scr_p=0.000 plateau=PASS
              -> FAIL_SR|FAIL_HALVES|FAIL_NEGYR   (VT drag raw 0.710 -> net 0.534)
  B_barbell   B|m21|mean100|IEFhalf n=4697 SR=0.613 ann=5.5% H1=0.74 H2=0.55 negyr=3/19
              worst=-15.5% corr=-0.076 lib 0.74 scr_p=0.000 plateau=PASS -> FAIL_SR|FAIL_NEGYR
  C_xle_crud  C|w126|switch     n=4696 SR=0.154 ann=1.8% H1=0.33 H2=-0.01 negyr=8/19
              worst=-18.7% corr=0.029 plateau=FAIL -> FAIL_SR|FAIL_HALVES|FAIL_NEGYR|FAIL_PLATEAU
  D_xlu_ief   D|lb21|riskoff|IEF n=4697 SR=0.585 ann=4.7% H1=0.55 H2=0.62 negyr=3/19
              worst=-6.6% corr=-0.089 lib 0.60 scr_p=0.000 plateau=PASS -> FAIL_SR|FAIL_NEGYR

  A11 near-miss (literal charter 11-SPDR set, lb126 k4 weekly): n=2047 SR=0.679
  ann=7.4% H1=0.55 H2=0.95 negyr=2/9 worst=-1.3% corr_champ=-0.147 lib_maxabs=0.82
  scr_p=0.000 plateau=PASS -> FAIL_SR ONLY (sole gate failed = SR<1.0).
  Robustness: VT-off 0.723 / monthly rebalance 0.675 (33bp/yr cost vs 78bp weekly);
  freq change immaterial -> honest ceiling ~0.68, gate is 1.0. NOT champion-eligible.

ADDITIONAL NEGATIVES (exact numbers):
  - Arm A L/S variants (long topK/short bottomK): ALL dead, best A|lb252|k3|LS SR=0.038
    (8-13 neg years each); short sector leg destroys it. Consistent with R1.
  - Bond-leg swap on B-half / D headliners: IEF 0.613/0.585, LQD 0.483/0.520,
    TLT 0.584/0.596 -> no rescue, IEF fine.
  - Correlation: all heads |corr_champ| 0.03-0.15 (PASS gate f), but Arm A correlates
    0.87 with library sleeve Multi_Strategy_SharpeW (0.86 L_S_120_20) -> would also
    fail library decorrelation; B 0.74 Risk_Parity_Bridgewater; D 0.60.
  - Scramble p=0.000 across all four arms: the signals are REAL but far too WEAK to
    clear SR>=1.0. These are honest dead ideas, not artifacts.

VERDICT: 0/4 arms pass. Nothing within 37% of the SR gate. DEAD: RS-ratio rotation
(honest net SR 0.53 long-window / 0.68 short-window), sector-bond barbell (0.61),
XLE/CRUD lead-lag (0.15), XLU/IEF stealth-rate (0.59). Sleeves + .meta saved per
contract item 4. DEAD_IDEAS rows to be filed via coordinator.

ARTIFACTS: campaign/scripts/{hunt_sector2_lib.py,hunt_sector2_r2_harness.py,
hunt_sector2_r2_scan.py,hunt_sector2_r2_gates.py}; sleeves/ 5 csv+meta;
tests_tdd.py 16/16 green; /tmp/sector2_r2_scan.csv + store pickle.

ROUND 2 DONE


========================================================================
## HUNT_SECTOR2 — ROUND 3 (2026-09-07, session resumed after a 429-killed session)
========================================================================
Charter: (a) internal composite of Arm A + Arm B at 50/50, 60/40, inverse-vol — does
diversification on PUBLISHED sleeves clear SR>=1.0? (a2) package Arm A + composite for
HUNT_VOL2's blend lane as BLEND_CANDIDATE_SUBMISSION; (b) cross-verify HUNT_FXCARRY2's
R2 negative. Read GATES_CONTRACT.md + DEAD_IDEAS.csv (102 rows) first: RS-ratio rotation,
sector-bond barbell, XLE/CRUD, XLU/IEF are all filed R2-dead; round 3 adds NO new signal
params (allocation math on published nets only + cross-verification).

PRIOR-SESSION STATE (found on arrival, diagnosed, quarantined):
The 09:42 429-killed session left hunt_sector2_r3.py + tests_tdd_r3.py WITH TWO REAL BUGS
and poisoned artifacts on disk:
  BUG 1 (weights-as-returns overflow): invvol_weights()' WEIGHT frame was passed to
     blend_dynamic as if returns -> cumprod(1.5/day) overflowed to yearly ~2e+25 and
     stamped verdict=PASS (sr=48.86, ann=5228%) on COMP_invvol_monthly.csv. The meta even
     self-labeled FAIL_SCRAMBLE_DEGENERATE|FAIL_PLATEAU while carrying the spurious PASS.
  BUG 2 (mis-targeted VT): vt_apply() vol-targeted rets.sum(axis=1), a 2x-gross book ->
     realized composite vol ~5% vs the 10% target, mis-stating every composite SR.
  BUG 3 (degenerate scramble): the scramble gate permuted a near-constant allocation
     frame (p=0.4..0.965, vacuous) instead of testing the leg.
Fixes (pre-existing in the surviving script, verified line-by-line this session):
blend_dynamic takes leg RETURNS + fail-closed guards (|ret|>25%/day and [-1,1] weight
range reject the bug class); vt_apply targets the WEIGHTED composite book; scramble gate
replaced by random_control_p (200 corr/vol-matched ZERO-MEAN random legs in B's slot;
p>=0.05 => FAIL_SCRAMBLE). HUNT_VOL2's blend lane had independently ingested the
corrupted COMP_invvol.csv and rejected it REJECT_UNUSABLE_FILE (own_ann 2.9e+20) — the
corruption propagated to another lane's pool before diagnosis; quarantined both files
with sleeves/_quarantine/README.txt (evidence kept) and re-emitted fixed versions.

TDD (30 green total): 16 (r2) + 13 pre-existing r3 + 1 added RED-first this session —
test_invvol_warmup_extension_covers_full_window: invvol_weights() has a 63d NaN warm-up
so blend_dynamic's cover-guard correctly rejected the full-window invvol blend
(AssertionError, live); added invvol_blend_weights() (first computable trailing weight
extended back over the warm-up — a convention, not a fitted param; no lookahead). RED
verified (AttributeError on missing helper), then GREEN; pytest 29->30. Full suites:
`python3 -m pytest tests_tdd_r3.py tests_tdd.py -q` => 30 passed (run from repo root).
Also fixed: FXCARRY2 cross-verify path was a relative "../HUNT_FXCARRY2/..." load that
raised FileNotFoundError; now absolute (ROOT-anchored).

R3 (a) INTERNAL COMPOSITE (hunt_sector2_r3.py, all fresh re-run this session, sleeves
re-emitted 13:34; overlap of A11_rs_ratio#lb126k4 + B_barbell, 2018-06-20..2026-08-12,
n=2047, corr(A,B)=+0.718, 6.4bps FULL |dW| at ALLOCATION level only — legs are
self-financing, their internal turnover already in the published nets — + day-0 entry;
T+1; trailing VT10 clip3 on the WEIGHTED book):
  COMP_50/50|daily   n=2047 SR=0.608 ann=6.2% vol=10.1% H1=0.56 H2=0.75 negyr=1/9
                     worst=-7.3% corr_champ=-0.115 lib_max=0.78 ctl_p=0.010 plateau=PASS
                     -> FAIL_SR|FAIL_NEGYR   (neg yr 2022 -7.3% breaches worst<=-5%)
  COMP_60/40|daily   n=2047 SR=0.641 ann=6.6% H1=0.59 H2=0.80 negyr=2/9 worst=-6.0%
                     corr=-0.111 ctl_p=0.010 plateau=PASS -> FAIL_SR|FAIL_NEGYR
  COMP_50/50|monthly n=2047 SR=0.613 ann=6.2% H1=0.56 H2=0.75 negyr=1/9 worst=-7.3%
                     corr=-0.114 ctl_p=0.010 plateau=PASS -> FAIL_SR|FAIL_NEGYR
  COMP_50/50|never   n=2047 SR=0.602 ann=6.1% H1=0.55 H2=0.75 negyr=1/9 worst=-7.3%
                     corr=-0.114 ctl_p=0.010 plateau=PASS -> FAIL_SR|FAIL_NEGYR
  COMP_invvol        n=2047 SR=0.648 ann=6.4% vol=9.9% H1=0.58 H2=0.82 negyr=1/9
                     worst=-6.0% corr=-0.115 ctl_p=0.010 plateau=PASS
                     -> FAIL_SR|FAIL_NEGYR   (headliner)
  VERDICT 0/5. The composite NEVER beats its own best leg (A11 alone 0.679): legs
  correlate +0.718, and with SR_A=0.68/SR_B=0.55 the equal-weight SR is (0.68+0.55)/
  sqrt(2*(1+0.718)) = 0.66 no-cost upper bound — measured 0.61-0.65 net. SR>=1.0 would
  need rho <= -0.25; measured +0.718. Charter hypothesis REFUTED with numbers:
  diversification math cannot clear 1.0 from two legs of 0.68/0.55 at +0.72 corr.
  Rebalance-freq cost check: daily->never costs only 0.006 SR (entry+drift are small)
  — the composite is NOT cost-killed, it is signal-poor.
  Adversarial control (charter HUNT_VOL2-style): corr/vol-matched zero-mean random leg
  in B's slot beats the real composite only p=0.010 -> B carries genuine (weak) drift;
  the composite's failure is level, not artifact.

R3 (a2) BLEND SUBMISSION (hunt_sector2_r3_submit.py; sleeves/blend_submit/
{4 csv + 4 csv.meta + MANIFEST.json}, each .meta stamped BLEND_CANDIDATE_SUBMISSION
with sha256, own-span SR/vol/mdd/corr_champ/lib-corr, rebalance-freq + cost conventions):
  A11_rs_ratio#lb126k4  n=2047 SR=0.679 ann=7.40% vol=10.90% mdd=-26.23% negyr=2/9
                        corr_champ=-0.144 lib_max=0.82(Multi_Strategy_SharpeW) sha=0354fd437047d221
  COMP_invvol           n=2047 SR=0.648 ann=6.42% vol= 9.91% mdd=-19.72% negyr=1/9
                        corr_champ=-0.115 lib_max=0.79 sha=74665c7b9a3a2280
  COMP_50_50_daily      n=2047 SR=0.608 ann=6.16% vol=10.14% mdd=-20.88% negyr=1/9
                        corr_champ=-0.115 sha=75fe5ff31ec423d5
  COMP_60_40_daily      n=2047 SR=0.641 ann=6.57% vol=10.25% mdd=-20.78% negyr=2/9
                        corr_champ=-0.111 sha=67d88611fc118977
  Pairwise corr on the common overlap: COMP family 0.988-0.997 internally, 0.892-0.910
  to A11 — blend lane should treat them as ONE slot next to A11 (pick-one satisfied).
  STATUS NOTE: HUNT_VOL2's blend lane ran to completion this cycle BEFORE this package
  existed (their recommendation.json: NOTHING_ADOPTABLE) and adjudicated A_rs (best
  dSR +0.068 at w=15%, survives their 200-null control, dAnn -0.89pp), A11 (best dSR
  +0.141 but DIVERSIFICATION_ARTIFACT: 100% of matched nulls also gain), COMP50d
  (dSR +0.060, DIVERSIFICATION_ARTIFACT), COMP_invvol (REJECT_UNUSABLE_FILE — the
  corrupted pre-fix file). Their blocker for ALL candidates was dAnn>0: champion ann
  39.85% arithmetic dominates any small-w blend of a 6-7%/yr sleeve. Re-submitting the
  fixed COMP files for the record; expectation is unchanged given their gate.

R3 (b) CROSS-VERIFY HUNT_FXCARRY2 (independent re-measure from their published CSVs):
  R2 carry_nominal_EW: n=5680 (2004-01-02..2026-08-28) SR=-0.0043 ann=-0.02% vol=5.58%
     H1=-0.133 H2=0.164 negyr=11/23 worst=-19.4% corr_champ=+0.028
     vs their claim SR=-0.004 ann=-0.18% H=(-0.133,0.164) negyr=11 worst=-19.4% corr
     0.0276 -> CONFIRMED (SR/halves/negyr/worst/corr all exact to 3dp; their ann -0.18%
     is internally inconsistent with their own SR*vol=-0.02% — cosmetic typo, verdict
     identical: FAIL sr/halves/yearly, scramble p=0.76).
  R3 ddstop10_carry_EW: n=5680 SR=-0.089 ann=-0.26% H=(-0.18,+0.03) negyr=11/23
     worst=-5.8% corr=+0.021 -> the ddstop variant is also negative on re-measure.
  ESCALATION: none needed — FXCARRY2's negative is real and honest. (Their carry sign
  convention produced ~0 gross drift, not an accounting bug; nothing to overturn.)

DEAD_IDEAS rows to file via coordinator (exact numbers):
  sector-rs-ratio + barbell composite (allocation-level blends of published R2 sector
  sleeves),dead,"composite NEVER beats best leg: legs corr +0.718, A11 0.679/B 0.547 ->
  equal-wt no-cost bound 0.66, net 0.602-0.648 across 5 splits (50/50|60/40|invvol x
  daily/monthly/never), all FAIL_SR|FAIL_NEGYR (2022 -6.0..-7.3%); SR>=1.0 needs
  rho<=-0.25; random-leg control p=0.010 (drift real but weak); blend lane: A11 dSR
  +0.141@15% is 100% reproduced by matched nulls (artifact), dAnn<0 for all",HUNT_SECTOR2-R3

ARTIFACTS: campaign/scripts/{hunt_sector2_r3.py (fixed engine), hunt_sector2_r3_submit.py
(submission builder)}; sleeves/ 5 fresh COMP_*.csv+meta (13:34) + blend_submit/ package;
sleeves/_quarantine/ (corrupted pre-fix overflow artifact + README, evidence kept);
tests_tdd_r3.py 14 tests (30/30 with r2 suite). Repro: python3 campaign/scripts/
hunt_sector2_r3.py && python3 campaign/scripts/hunt_sector2_r3_submit.py.

ROUND 3 DONE

========================================================================
## HUNT_SECTOR2 — ROUND 3 SESSION 2 (2026-09-07 13:5x CST, verification pass)
========================================================================
Found on arrival: the 13:3x session had already completed all three charter items and
written the R3 FINDINGS section. This session executed the charter's reproducibility
clause ("every claim must reproduce from a script you saved") against that state:
re-ran every engine fresh, diffed artifacts byte-for-byte, and closed ONE gap.

VERIFICATION RESULTS (all from live re-runs this session, exact numbers):
  - TDD: `python3 -m pytest tests_tdd_r3.py tests_tdd.py -q` (repo root) => 30 passed
    in 2.54s (16 r2 + 14 r3).
  - hunt_sector2_r3.py fresh re-run: all 5 composites reproduce EXACTLY (SR 0.608/
    0.641/0.613/0.602/0.648, ann 6.2-6.6%, H-pairs, negyr, worst, corr -0.111..-0.115,
    ctl_p=0.010, plateau PASS, verdicts FAIL_SR|FAIL_NEGYR) and corr(A,B)=+0.718 on the
    2018-06-20..2026-08-12 n=2047 overlap. The 5 re-emitted COMP_*.csv are
    BYTE-IDENTICAL to the pre-run snapshot (cmp clean) -> deterministic engine.
  - hunt_sector2_r3_submit.py fresh re-run: same 4 candidates, same sha256
    (0354fd43.../74665c7b.../75fe5ff3.../67d88611...), same pairwise corr matrix
    (COMP family 0.988-0.997, 0.892-0.910 to A11), 4/4 metas stamped
    BLEND_CANDIDATE_SUBMISSION. MANIFEST.json unchanged.
  - HUNT_VOL2 adjudication claims verified against their work_r3/recommendation.json:
    verdict NOTHING_ADOPTABLE; A_rs best_dsr +0.068@w=0.15 (dAnn -0.887pp); A11
    best_dsr +0.1406 with adversarial frac_null_dsr_pos=1.0 of 200 matched nulls ->
    DIVERSIFICATION_ARTIFACT; COMP50d best_dsr +0.0602; pool.COMP_invvol
    REJECT_UNUSABLE_FILE with own_ann 2.866e+20 (the corrupted pre-fix file). All
    match FINDINGS to the digit.
  - Quarantine evidence intact: _quarantine/COMP_invvol_monthly.csv.meta carries the
    original spurious PASS (sr=48.863, ann=5227.95%, 2019 yearly 2.0e+25) now stamped
    INVALID_QUARANTINED with README.

GAP FOUND AND CLOSED (this session's only code change):
  The R3 section's ddstop10 cross-verify claim (SR=-0.089) had NO saved repro script —
  hunt_sector2_r3.py covers only FXCARRY2_R2_carry_nominal_EW. Added
  campaign/scripts/hunt_sector2_r3_xverify.py (read-only w.r.t. HUNT_FXCARRY2), which
  re-measures BOTH published negatives against their published claims with hard asserts:
    FXCARRY2_R2_carry_nominal_EW  n=5680 SR=-0.0043 ann=-0.02% H=(-0.133,0.164)
        negyr=11/23 worst=-19.4% corr=0.028  -> CONFIRMED
    FXCARRY2_R3_ddstop10_carry_EW n=5680 SR=-0.0894 ann=-0.26% H=(-0.184,0.034)
        negyr=11/23 worst=-5.8% corr=0.021   -> CONFIRMED (ddstop also negative)
  Every R3 claim now has a saved script. Escalation to HUNT_FXCARRY2: none needed.

ALGEBRA RE-CHECK of the refutation (live): A11 overlap SR 0.679, B 0.547, rho=+0.718
  -> equal-wt NO-COST upper bound 0.662; rho required for SR>=1.0 is -0.248. Measured
  net 0.602-0.648 across 5 splits. Diversification cannot clear the gate; charter
  hypothesis stands REFUTED. Verdict: 0/5 composites pass; Arm A honest ceiling 0.679
  remains the sector-family ceiling and fails only SR>=1.0.

DEAD_IDEAS FILING STATUS: campaign/results/DEAD_IDEAS.csv (102 rows) contains the two
  R2 sector rows (89-90) but NOT yet the R3 composite row; the row text is drafted in
  the prior session's section below and is filed via the coordinator per contract
  item 5 (the ledger is coordinator-owned; other agents' R3 rows are likewise pending
  in the working tree). FLAGGED for coordinator pickup, not self-written.

VERDICT (unchanged, now fully repro-verified): 0/5 composite splits pass; no new
signal params were introduced; blend-lane package re-issued with fixed files.

ARTIFACTS: campaign/scripts/{hunt_sector2_r3.py, hunt_sector2_r3_submit.py,
hunt_sector2_r3_xverify.py (NEW)}; sleeves/ 5 COMP_*.csv+meta (byte-stable);
sleeves/blend_submit/ (4 csv + 4 meta + MANIFEST.json); sleeves/_quarantine/.
Repro: python3 campaign/scripts/hunt_sector2_r3.py && python3 campaign/scripts/
hunt_sector2_r3_submit.py && python3 campaign/scripts/hunt_sector2_r3_xverify.py

ROUND 3 DONE

## ROUND 4 (audit rotation, 2026-09-07 20:47-21:1x CST) - fraud-catch duty per charter

Charter: reproduce 6 DEAD_IDEAS.csv rows from OTHER agents' families, each from its CITED
SCRIPT (not prose). Method: byte-identical copies of the cited scripts into audit_r4/
(verified with diff against the originals - ALL 16 copied scripts IDENTICAL, zero edits),
path-patched driver_* wrappers (data root + sys.path only; no logic touched), fresh runs,
fresh-vs-original output comparison + fresh-vs-FINDINGS-prose comparison. DEAD_IDEAS.csv read
FIRST: 117 rows as of this session (charter said 108 - ledger has grown; my own family rows
HUNT_SECTOR_FULL/-R2/-R3 excluded). No new engines run; no new params; family stays CLOSED.

Note: audit_r4/ held an UNLOGGED partial run from a prior session today (18:48-20:32: CIT/TFF/
FF2 recon1-4 screens). I re-ran EVERYTHING fresh in this session for independent evidence and
completed the missing pieces (FUNDAMENTAL composites + s_ta, FF2 recon5, CIT deep_check +
fundamental_check/PCPS, champion re-verify). All numbers below are from THIS session's runs.

PER-ROW RESULTS (6 rows, 4 families):

1. DEAD_IDEAS line 2 [HUNT_FF2] "FF factor premia (HML/SMB/OP/INV), dead, all negative 2008+"
   -> REPRODUCED. Cited script: HUNT_FF2/scratch/recon2.py (copy byte-identical). Fresh run
   recon2_results.csv is BYTE-IDENTICAL to the original's saved scratch/recon2_results.csv
   (diff clean). Cells vs FINDINGS table: HML_from_6pf -0.02 (FINDINGS -0.02), SMB_from_6pf
   -0.13 (-0.13), OP_Hi30_Lo30 +0.29 H1 .34/H2 .24 (+0.29 .34/.24), INV_Hi30_Lo30 +0.05 (+0.05),
   MomDec_HiLo +0.16 (+0.16). All FAIL exactly as published. Verdict stands.

2. DEAD_IDEAS line 3 [HUNT_FUNDAMENTAL] "industry/decile portfolios (L/S), zero-to-negative PIT"
   + line 6 "value/growth/profitability screens"
   -> REPRODUCED. Cited scripts: scratch/run_ideas.py + s_ta_backtest.py (copies identical).
   Fresh run_ideas: value_comp SR +0.06 / 11 neg / worst -16.1% (FINDINGS +0.06/11/-16.1),
   growth_comp -0.23 / 10 / -36.7 (-0.23/10/-36.7), prof_comp -0.22 / 13 / -29.1 (match),
   comp_vgp -0.16 / 13 / -31.7 (match), value_q3030 +0.03 / 10 / -16.1 (match) - 5/5 rows to
   the digit; flatten gate uniqR ~0.62 ac1 ~0 for all, matching "failure is economic".
   Fresh s_ta_backtest: SR +0.39 H1 +0.51 H2 +0.24 ann +5.5% negy 7 {2016: -18.2, 2024: -11.0}
   MDD -37.8% - matches FINDINGS "SR +0.39, 7 neg yrs (FAIL)" line-for-line.

3. DEAD_IDEAS line 4 [HUNT_FUNDAMENTAL] "equal-wt betting-against-beta (BAB), short-highvol =
   shorting survivors" (+ line 5 "MM naive ivol, negative")
   -> REPRODUCED. Cited script: HUNT_FF2/scratch/recon3.py (BAB+QMJ construction; FF2 is the
   independent re-tester of this family). Fresh recon3_results.csv BYTE-IDENTICAL to the
   original saved file: BAB_v25_L05S05 -0.64 / 14 neg / worst -19.7%; BABmom2x2 -0.43;
   BABrev2x2 -0.61; QMJproxy_lowdownside -0.61 - matches DEAD_IDEAS "short-highvol=shorting
   survivors" (short legs -0.65 to -0.80 ann in every L/S cell). recon4 also BYTE-IDENTICAL:
   BABinvvol_longonly_half +0.58 corr 0.081 "real but below bar; NOT delivered" - reproduced
   exactly. MM row (line 5): moreiramuir cells fresh = MKT -0.947, HML -0.336, SMB -1.027
   (dead) but MOM_63 +0.207 with H2 -0.429 MDD -55.7% (fails halves) - consistent with the
   row's "negative" verdict under the full gate battery.

4. DEAD_IDEAS line 49 [HUNT_CIT_AG] "CIT/noncomm ags z on ag-ETFs (coherent mapping), best
   0.21 SR, 5+ neg yrs; cross-complex 0.705 artifact rejected"
   -> REPRODUCED with one DOCUMENTED data-vintage drift (verdict-neutral; see F1).
   Cited scripts: run_hunt.py + deep_check.py + fundamental_check.py (copies identical).
   Screen fresh: 156 rows; headline rows IDENTICAL to the original's screen_results.csv -
   lean_hogs/noncomm/SOYB 0.705 n=3754 (the artifact), lean_hogs/noncomm/CORN 0.585,
   live_cattle/noncomm/CANE 0.443. Coherent-mapping re-test (fundamental_check fresh):
   lean_hogs/cit->MOO 0.348, lean_hogs/noncomm->DBA 0.245, lean_hogs/cit->DBA 0.181 - matches
   FINDINGS "best = lean_hogs-cit->DBA 0.181 (5 neg)" (and 0.24/0.21 DBA/MOO xchecks).
   deep_check fresh: full span 3762 d 2011-09-20..2026-09-04, yearly 3 neg (2011 -7.4%, 2012
   -2.0%, 2026 -6.0%), worst -7.4% = FINDINGS "3 neg yrs own-span, worst -7.4%"; param
   neighborhood 0.440/0.543/0.500/0.497/0.580/0.470 = FINDINGS "0.44..0.58" exactly; scramble
   p = 0.005 REPRODUCED (real-book SR 0.599; required dropping the single benign pct_change
   row-0 NaN - see F2). Divergence: 12/156 wheat_hrw rows shifted (n 3189->3754/4077/4184;
   SR within [-0.64,+0.02] both vintages, none within 0.58 of any gate) - root cause is a
   same-day refresh of tools/quant/data/more_cot/cit_wheat_hrw.csv (mtime 03:33) and
   wheat_hrw_cot.csv (17:06) AFTER the original 09-03 run; untracked in git.

5. DEAD_IDEAS line 53 [HUNT_TFF] "TFF trader-category z/diff/fade on proxies, 156 variants,
   0>=0.3 SR; best 0.275/6neg; DIFF (new family) 0.203/8neg"
   -> REPRODUCED (exact). Cited script: run_tff.py + tff_eng.py (copies identical). Fresh
   screen_tff.csv BYTE-IDENTICAL to the original saved file (156 variants). Best dow_emini/
   levfade_DIA 0.275 n=4999 6 neg worst -6.6%; DIFF family best gbp/DIFF-dealer-am_mom_SPY
   0.203 8 neg worst -5.3%; every claim digit-exact.

FINDINGS FROM THE AUDIT (divergences / hazards, named):

F1 (data drift, verdict-neutral): tools/quant/data/more_cot/*wheat_hrw*.csv were refreshed
   2026-09-07 (cit 03:33, noncomm 17:06), silently shifting 12/156 rows of a 09-03 screen
   (e.g. wheat_hrw/cit/DBA SR -0.636 fresh vs -0.246 original; both far dead). Data files are
   NOT git-tracked, so no audit can currently reproduce COT-family screens byte-for-byte
   across refreshes. Flag to coordinator: either track more_cot snapshots or stamp a
   data-vintage hash into screen CSVs. Verdicts unchanged (max fresh row 0.022 vs bar 0.6).

F2 (framework drift, live hazard): campaign/bt/gates.py carries 86 UNCOMMITTED insertions
   (worktree mtime 17:05 today; fail-closed hardening by another agent, incl. a
   NaN-contamination guard in scramble_positions and an enforced scramble in gates.run).
   Under the uncommitted guard, CIT_AG's deep_check scramble returns p=NaN (its position
   series carries one benign pct_change row-0 NaN); the original 09-03 p=0.005 reproduces
   exactly once that NaN is dropped (n=3762, block=10 and block=20 both p=0.005, real-book
   SR 0.599). Not a fraud signal - the original number was computed honestly under the
   then-current framework - but audits run against a moving bt/: the framework must be
   committed BEFORE audit rotations, or audits must pin a framework commit. Not my scope to
   commit; flagged.

F3 (prose-vintage mismatch in HUNT_FF2 FINDINGS, verdict-neutral): FF2's prose quotes
   "MOM -0.19 H2, MDD -55.7%" for naive MM and "indrev125 -0.63"; FF2's own saved CSVs
   (which byte-reproduce) read moreiramuir_MOM_63 h2 = -0.4288 (mdd -0.5570 - matches) and
   indrev125_LS -0.38. The CSVs are the artifacts of record; both numbers kill the family
   either way, so DEAD_IDEAS verdicts are unaffected - but the FINDINGS prose should be
   treated as non-authoritative wherever it disagrees with the saved CSV.

F4 (label misnomer in HUNT_CIT_AG PCPS leg, verdict-neutral): FINDINGS calls the best PCPS
   cell "PSOYBUSDM/SOYB 21d = 0.465"; the cited code computes pct_change(21) on the MONTHLY
   FRED series (PSOYBUSDM is monthly, 415 rows) = ~21-MONTH momentum reindexed daily. I
   reproduced the literal path: 0.464 / 6 neg / n=3762 (matches 0.465/6neg). Recomputed with
   trading-day lookbacks on the daily-indexed series: best cell PSUGAUSAUSDM/CANE 126d 0.500
   (3-5 neg across lb) - still below the 0.6 bar. Verdict unchanged; label in DEAD_IDEAS
   prose is misleading but not verdict-changing.

UNREPRODUCIBLE rows: NONE. All 6 rows (7 with line 6) carry runnable cited scripts; all
   reproduce; the only divergences are F1 (12/156 wheat rows, data vintage) with no
   verdict change anywhere.

CHAMPION OF RECORD re-verified independently this session (bash campaign/bt/
verify_champion_r3_cmd.sh, canonical 13-sleeve map): ok=true 7/7 (weights_repro, byte_repro,
cost_reconciliation, causality, gross, yearly, mdd), ann_cagr 37.1954%, SR 3.1810, MDD
-6.6922%, neg_years 0, n=4805, 2008-03-31..2026-08-27 - matches the charter's 17:0x
re-verification to 4 decimals. /tmp copy at verify_champ_r4.json.

EXTRAS verified in passing (not charter rows): FF2 delivered sleeves campaign/agents/
loop_team/HUNT_FF2/sleeves/{FF2_DUALGATE_raw,poolvt}_daily.csv are byte-identical to the
originals; recomputed raw SR_d 0.978 / ann 6.0% and poolvt SR_d 1.030 / ann 8.9% match their
.meta claims (raw = 5/7 gates as-delivered per its own meta; poolvt 7/7) - consistent with
the DEAD_IDEAS row (premia dead, the delivered engine is a VOL-GATE construction, not a
premia bet). FF2 recon5 fresh: A+B blend SR 0.87 / 3-way 0.90 - matches FINDINGS' recon5
reference "A+B blend SR changed 0.87 -> 0.68 between recon5 and recon8" (the 0.87 leg).

ARTIFACTS: audit_r4/ (all copies byte-identical to cited originals - re-verified this
session with diff), drivers driver_cit/deepcheck/fundcheck/fundta/fundideas/recon5/tff.py,
fresh outputs screen_results.csv, screen_tff.csv, recon3_results.csv, ff2_run/recon{1,2,4}_
results.csv (byte-identical to originals), fund_run/, sleeves/ (FF2 copies). Repro:
python3 audit_r4/driver_cit.py && driver_deepcheck.py && driver_fundcheck.py &&
driver_fundta.py && driver_fundideas.py && driver_recon5.py && driver_tff.py &&
bash campaign/bt/verify_champion_r3_cmd.sh

VERDICT: 6/6 rows REPRODUCED (one with documented, verdict-neutral data-vintage drift; one
prose-vintage flag). No fraud found. Sector family stays CLOSED; no engines re-run.

ROUND 4 DONE


========================================================================
## HUNT_SECTOR2 — ROUND 5 (2026-09-08 05:3x-06:4x CST) — data-admission audit + measured NOT-HUNT-ELIGIBLE negative
========================================================================
READ FIRST done: GATES_CONTRACT_V2.md (RATIFIED 09-08 03:1x; Step-2 flip NOT yet landed —
campaign/bt/gates.py live this session still has leak_check default OFF; per charter I did NOT
depend on either state and passed sig= + leak_check=True explicitly, V2 6 Step-1). DEAD_IDEAS.csv
recounted with a csv parser: 125 data rows (charter said ~120 — ledger grew, as designed). My
family rows: 37 (CROSSASSET2), 45-46 (SECTOR_FULL), 88-89 (SECTOR2-R2), 91 (CMDT2), 102
(SECTOR2-R3). No dead family re-tested. Champion of record independently re-pinned THIS session:
sha256_16 4358dfab95679b97, 4805 rows, 2008-03-31..2026-08-27 — matches the charter byte-for-byte.

R5 CORNER (a) as chartered: sector-rotation covariates from Nasdaq historical + PIT-safe
news/social aggregates (GoogleNews / Reddit, keyless, live per altdata5 2026-09-08). Charter's
own bar: publication lag per source documented; any series whose history cannot be proven prior
-> drop it and say so.

R5 (a1) ADMISSION AUDIT — VERDICT: CORNER DEAD ON DATA ADMISSION, 0/4 sources admissible.
Every admission claim below is backed by a saved live-probe script
(hunt_sector2_r5_probe.py; probe_results.json in work_r5/ has the machine-readable output):

  1. GoogleNews RSS (altdata5 google_news, keyless): ROLLING SNAPSHOT, NO ARCHIVE.
     Two live crawls 2026-09-08: crawl1 = 100 items spanning ~1h (15:45-16:45 GMT same
     day); crawl2 = 100 items spanning 495h/20.6d (one stale item at the window edge).
     The feed's depth is bounded by its item count, not by history: there is NO archive
     endpoint -> no series can be constructed, PIT-provable history is impossible.
     -> DROP_NO_HISTORY.

  2. Reddit r/wallstreetbets top Atom (altdata5 reddit_top): ROLLING SNAPSHOT, NO
     ARCHIVE. Crawl1 = ~25 items spanning ~4d (oldest 2026-09-02, newest 2026-09-06);
     crawl2 = 15 items spanning ~5h. Same conclusion: cannot construct a series.
     -> DROP_NO_HISTORY.

  3. Nasdaq historical (api.nasdaq.com/api/quote/{sym}/historical — the rviv-revived
     keyless route of 2026-09-07): HARD ~10y ARCHIVE CAP, fromdate silently ignored.
     Live probes on XLK (assetclass=etf): fromdate=2000-01-01 AND fromdate=2007-01-01
     both return exactly 2514 rows back to 2016-09-06 (not the requested start); hard
     windows 2010-2012, 2004-2006, 2012-2013H1 ALL return 0 rows. First bar 2016-09-06
     is 3.7y after the 2013-01-01 admission bound. more_etf already supersedes it for
     price (XLK on disk back to 1998-12); the genuinely new axis it would add is VOLUME,
     which hits the same cap. span_class inception_fail. -> DROP_INCEPTION_FAIL.

  4. wiki_attention (tools/quant/data/wiki_attention, Wikimedia REST pageviews, keyless
     CC0): the ONLY charter-adjacent news/social source on disk with a REAL archive —
     10 daily series, 2015-07-01..2026-09-06, 4086 rows each, 0 gaps (manifest: status
     ok), and a documented PIT rule (day-D views aggregated in UTC, served ~00:00-04:00
     UTC D+1 -> usable D+1; README 'PIT / timing rules'). But first bar 2015-07-01 >
     2013-01-01 bound -> span_class inception_fail (V2 9a: not hunt-eligible).
     -> DROP_INCEPTION_FAIL.

  Also closed the 'did you check GDELT' gap for the record: GDELT DOC timelinevol is the
  one news aggregate WITH a server-side archive (2017Q1 window served 91 pts on probe),
  but pre-2017 windows (2013/2014/2015/2016) returned HTTP 429 on 3 attempts each at 8s
  spacing — history NOT capturable this round and never PIT-provable for the 2008+ span
  this campaign's gates demand. GDELT is also already a used family in this repo
  (wt.news.gdelt_events, country_crisis). The charter named GoogleNews/Reddit, which have
  no archive at all. [Recorded as 429-could-not-capture, NOT as absence-of-data.]

R5 (a2) THE ONE STILL-EVALUABLE CONSTRUCTION — measured, NOT a submission.
Label discipline: span_class=inception_fail -> hunt_eligible=False ->
acceptance_track=NONE_NOT_HUNT_ELIGIBLE (V2 9a/§0). Judged nowhere against the champion
bar; numbers below are the honest measurement the charter asked for ('drop it and say
so' — measured anyway so the family's negative is earned, not assumed).

  Construction (ONE pre-registered spec, no tuning): allocation-level attention de-risk
  overlay on the PUBLISHED R2 A11 sleeve (A11_rs_ratio#lb126k4, artifact of record,
  sha256_16 0354fd437047d221, 2047 rows, own-span SR 0.679 / FAIL_SR only). Base leg =
  the published net AS IS (my own R3 precedent: no signal re-construction — an in-line
  rebuild I attempted first reproduced to only corr 0.844 / SR 0.482 vs the artifact and
  was DISCARDED as non-authoritative). Attention covariate = cross-nick mean of
  trailing-252d z-scores of daily Wikipedia pageviews (aapl,nvda,tsla,spx,vix,fomc,cpi),
  then a 252d z of that mean; gate z>+1 -> scale 0.25 else 1.0; shift(2) for strict PIT
  (day-D views publish D+1 UTC; T+1 execution -> effective D+2). Allocation turnover
  |dScale| charged 6.4bps one-side to the OVERLAY book only (base already costed).
  Gate stats: fire_frac 0.223, 300 flips (301 incl day-0 boundary convention).

  NUMBERS (span 2018-06-20..2026-08-12, n=2047, span_class=inception_fail):
    base    SR=0.679  (published artifact; R2 verdict FAIL_SR only)
    overlay SR=0.821  dSR=+0.141
    delta honesty: dSR halves = (+0.407, -1.087); excluding 2020 (the dominant delta
      year): dSR = -0.979. THE LIFT IS A 2020-COVID EPISODE ARTIFACT — the exact R4
      TimesFM kill pattern generalized in the charter ('single-era lifts are NOT
      repeatable sleeves; the span gate (>=8y of effect) is the bar'). The effect
      exists for roughly 8 months of a 8.2y window.
    placebo (V2 8h logic): 200 random de-risk gates matched on fire-fraction AND flip
      count: p=0.000 — de-risk timing alone (any 22%-of-days 0.25x scale with ~300
      flips) reproduces the ENTIRE lift. The attention z adds NOTHING over generic
      de-risk arithmetic. (2020 is the year every such gate 'works': the book was
      nearly flat through the crash window.)
    V2 battery on the overlay book (explicit Step-1 args): sr 0.821 FAIL_SR;
      leak probe MEASURABLE: same_period_corr +0.084, p 0.000127, lag-0 argmax? no
      (lag -2 0.088 is argmax) -> leak=False, leak_ok=True (shift(2) provably PIT);
      beats-passive trio PASS (0.821 vs best passive spy_bh 0.754, margin +0.067);
      corr_to_champion -0.063 (would pass 0.15 anyway); scr_p 0.000; composite
      pass=False on SR. The sleeve fails the ONLY gate that ever mattered here (SR>=1.0)
      and is NOT_HUNT_ELIGIBLE on top.

  VERDICT: honest negative, double-killed. (1) admission: inception_fail (V2 9a);
  (2) substance: the dSR lift is 100% placebo-reproduced de-risk timing concentrated
  in 2020 — fails the generalized span gate even if the data had admitted.

R5 (b) FRAMEWORK NOTE (no action needed by me): gates.run leak default is still OFF in
the working tree (V2 section-12 Step-2 flip pending in a quiet window). My submission-
class call passes sig= + leak_check=True explicitly, so it is correct under EITHER
default. leak dict published in the .meta per V2 6 Step-1.

DEAD_IDEAS rows to file via coordinator (exact numbers):
  sector-rotation covariates from Nasdaq historical + news/social aggregates
  (GoogleNews/Reddit/wiki_attention),dead,"corner DEAD ON ADMISSION: GoogleNews RSS and
  Reddit Atom are rolling snapshots with NO archive (two 09-08 crawls: 100 items ~1h-20.6d;
  15-25 items sub-week) -> no series constructible; Nasdaq historical has a hard ~10y cap
  (fromdate ignored: 2000/2007 both return 2514 rows to 2016-09-06; pre-2013 windows 0
  rows) -> inception_fail; wiki_attention is PIT-safe with a real 4086-row archive but
  starts 2015-07-01 -> inception_fail (V2 9a). Measured anyway (NOT_HUNT_ELIGIBLE):
  attention-z de-risk overlay on published A11: SR 0.679->0.821 dSR +0.141 BUT placebo
  p=0.000 (200 matched random gates reproduce the entire lift) and dSR excl-2020 -0.979
  (halves +0.407/-1.087) — single-episode artifact per the R4 TimesFM span-gate rule;
  overlay itself FAIL_SR 0.821 (leak_ok True, bp trio PASS, corr -0.063)",HUNT_SECTOR2-R5

ARTIFACTS: campaign/agents/chief/coord/HUNT_SECTOR2/{hunt_sector2_r5.py (admission +
sleeve engine), hunt_sector2_r5_probe.py (live probes), tests_tdd_r5.py (9 tests,
RED-first: 9 failed pre-engine, 9 passed after), work_r5/{ATT_DE_RISK_A11.net.csv,
ATT_DE_RISK_A11.csv.meta (full V2 disclosure: admission roster, span_class next to
every number, leak dict, bp trio, placebo, dSR halves, vintage pins), probe_results.json}}.
Vintage pins: A11 artifact 0354fd437047d221 (2047 rows), wiki_attention/aapl.csv
609cca25738461c0 (4086 rows), champion 4358dfab95679b97 (4805 rows, 2008-03-31..2026-08-27).
Repro: python3 campaign/agents/chief/coord/HUNT_SECTOR2/hunt_sector2_r5.py &&
python3 campaign/agents/chief/coord/HUNT_SECTOR2/hunt_sector2_r5_probe.py &&
python3 -m pytest campaign/agents/chief/coord/HUNT_SECTOR2/tests_tdd_r5.py -q (repo root;
full 39 = 16 r2 + 14 r3 + 9 r5, all green, engine stdout byte-identical across 2 runs).

ROUND 5 DONE


========================================================================
## HUNT_SECTOR2 — ROUND 6 (2026-09-08 13:3x-14:3x CST) — TDD bugfix + pre-registered bugfix re-run
========================================================================
READ FIRST done: GATES_CONTRACT_V2.md in force; leak-check Step-2 flip CONFIRMED LIVE in
campaign/bt/gates.py:104 (`leak_on = bool(p.pop('leak_check', True))`, commit 539f50e) and my
R5 engine passes sig= + leak_check=True explicitly either way (V2 6 Step-1). DEAD_IDEAS.csv
recounted with a csv parser: 144 data rows at my append this round (charter said 137 at
R5-end — the ledger is dynamic by design; concurrent R6 rows landed during my round, last
pre-append row CAMP_SHORT-R6, incl row-141 the curation/fraud-catch pass that cross-verified
MY OWN R5 numbers). Champion re-pinned THIS session: sha256_16 4358dfab95679b97 — matches the
charter byte-for-byte. No dead family re-tested; the R5 corner re-run is charter pre-registered
as a BUGFIX RE-RUN, not a fresh hunt.

R6 (a) TDD BUGFIX — the fromdate-ignored defect I found in R5. Exact file:
tools/wt/sources.py, function nasdaq_history. RED FIRST (tests_tdd_r6.py, 5 tests written
before touching the fix):
  RED run against HEAD semantics (red_run_head.py exec's `git show HEAD:./tools/wt/sources.py`
  as wt.sources in-process — the working tree carries OTHER agents' concurrent hunks in the
  same file, so the RED side is demonstrated without touching them):
    3 failed, 2 passed in 0.74s
    - test_fromdate_ignored_beyond_cap_fails_closed[_fixture]: days=6500 returned a dict
      ('date': ['01/17/2017', ...] — 2514 bars masquerading as a 25y ask); assert res is None
      FAILED exactly as the defect predicts.
    - test_unparseable_oldest_date_fails_closed_distinct_error: 'not-a-date' flowed through
      as D[0] in the returned dict; FAILED.
    - the 2 healthy-window regression guards passed under BOTH semantics (by design — the fix
      may not change healthy behavior).
  GREEN run against the fixed module: 5 passed in 0.73s.
  The fix (in nasdaq_history only): parse the oldest served bar's date (fail-closed DISTINCT
  err 'unparseable oldest bar date (...); served-window coverage unverifiable') + coverage
  verification — fire when served window starts materially after the requested fromdate
  (gap > max(30, 0.25*days)) OR fewer bars than asked came back (len(C) < 0.98*days), error
  'truncated history: asked N bars from <frm>, served M bars from <oldest> - endpoint ignores
  fromdate beyond its archive cap / limit= page limit'.
  REGRESSION SWEEP (healthy callers must be untouched): rviv revival suite 8 passed;
  tools/test_options_cboe.py ALL GREEN exit 0 (incl the 'removed _nasdaq_rows (inlined via
  wt.sources.nasdaq_history)' pin); live healthy asks SPY days=60 -> 72 bars, 200 -> 226,
  400 -> 440, QQQ 60 -> 72, err=None everywhere. CUMULATIVE suite 44 passed (16 r2 + 14 r3 +
  9 r5 + 5 r6). DISCLOSURE for the coordinator: the uncommitted working-tree sources.py also
  carries three hunks that are NOT MINE and NOT this round's (kr_history/_kr_parse_items,
  _stooq_symbol/stooq_quote hardening, polygon_history epoch-ms date normalization) —
  concurrent work, untouched by me, not commit-verified by me.

R6 (b) BUGFIX RE-RUN of the R5 corner under corrected windows (hunt_sector2_r6.py ->
work_r6/r6_bugfix_rerun.json; driver exit 0):

  [1] Corrected-fetcher live probes — the defect ask now FAILS CLOSED against the live API
  and the R5 cap numbers are carried in the error text itself:
    XLK days=6500 -> FAIL-CLOSED | 'truncated history: asked 6500 bars from 1998-03-09,
                       served 2514 bars from 2016-09-06 - endpoint ignores fromdate ...'
    XLK days=3000 -> FAIL-CLOSED | served 2514 bars from 2016-09-06
    XLK days=2600 -> FAIL-CLOSED | served 2514 bars from 2016-09-06
    SPY days=400  -> OK n=440 first=12/03/2024 ; SPY days=200 -> OK n=226 first=10/13/2025
    probe contract OK (3 defect asks blocked, 2 healthy asks serve, R5 numbers exact).

  [2] Fresh news/social crawls: BOTH NET-DEAD MID-ROUND (google_news 'net: agent-side hard
  timeout 45s', reddit_top 'net: [Errno 54] Connection reset by peer'; raw curl confirms
  news.google.com and reddit.com TCP-timeout while api.nasdaq.com keeps serving on
  --http1.1). HONESTY RULE ADDED to the driver after the first pass silently folded crawl
  failures into the window<30 branch: A FAILED CRAWL IS NOT A MEASUREMENT of window length.
  Crawl failure is recorded UNMEASURED; the DROP verdict rests on the R5 STRUCTURAL evidence
  (rolling snapshot, NO archive endpoint -> no series constructible), which network state
  cannot change. (Also fixed: the shared http client can block indefinitely — the driver now
  hard-times crawls at 45s and returns the timeout as an error result.)

  [3] ADMISSION RE-DERIVATION — UNCHANGED, 0/4 admissible, CORNER_DEAD_ON_DATA_ADMISSION:
    google_news    -> DROP_NO_HISTORY (R5 structural; fresh crawl unmeasured this round)
    reddit_top     -> DROP_NO_HISTORY (same)
    nasdaq_hist    -> DROP_INCEPTION_FAIL — under CORRECTED fail-closed semantics the ~10y
                      cap is now an ERROR naming the served window (2514 bars from 2016-09-06,
                      3.7y after the 2013-01-01 bound), not a silent short series
    wiki_attention -> DROP_INCEPTION_FAIL (vintage re-pinned EXACT: 4086 rows,
                      sha256_16 609cca25738461c0, first bar 2015-07-01 > 2013 bound; V2 9a)
  The R5 verdicts reproduce under corrected fetcher semantics — zero divergence, no finding.

  [4] R5 sleeve re-run, spec-identical (no param change) — EXACT REPRODUCTION of the R5
  record (deterministic engine, seeded rng; every assert passed):
    base SR=0.679  overlay SR=0.821  dSR=+0.141  placebo_p=0.000
    dSR halves=(+0.407, -1.087)  excl-2020: -0.979  | verdict FAIL_SR|NOT_HUNT_ELIGIBLE
    gates: leak_ok=True; beats-passive PASS (candidate 0.8205 vs best passive spy_bh 0.7538,
    margin +0.0667; sixty_forty 0.7050, cta_trend -0.2693); corr_champ -0.063; scr_p 0.000.

  [5] Champion pin 4358dfab95679b97 unchanged.

  INTERPRETATION CORRECTION ADOPTED (row-141 audit; independently re-verified before
  adopting — placebo_direction_seedsweep.py, seeds 0..4): my R5 FINDINGS prose 'placebo
  p=0.000 — de-risk timing alone reproduces the ENTIRE lift' was INVERTED. placebo_p =
  beats/200, so p=0/200 means the attention overlay BEAT all 200 matched random de-risk
  gates. Re-verified: overlay SR 0.8205 beats 200/200 draws at EVERY seed tried
  (placebo SR mean +0.196..+0.212, i.e. dSR mean ~ -0.61: matched random de-risk timing is
  DESTRUCTIVE on this book). Residual magnitude gap vs row-141's quoted dSR mean -0.473 /
  max -0.108 is seed/convention (their own seed, dSR space); direction and verdict identical.
  DISPOSITION UNCHANGED — the honest negative now rests on: (1) admission inception_fail
  (V2 9a, all four sources); (2) single-episode concentration (dSR halves +0.407/-1.087,
  excl-2020 -0.979 — the R4 TimesFM span-gate rule); (3) FAIL_SR 0.821 < 1.0. NOT on
  placebo-reproduction, which actually pointed the other way. Verdict still dead on both
  the eligibility bar and the substance bar.

DEAD_IDEAS row appended (145 data rows now): SECTOR2-R5 family row refreshed with corrected
numbers + the adopted interpretation correction (source tag HUNT_SECTOR2-R6).

ARTIFACTS: campaign/agents/chief/coord/HUNT_SECTOR2/{tests_tdd_r6.py (5 tests, RED-first),
red_run_head.py (RED-vs-HEAD harness, working-tree-safe), hunt_sector2_r6.py (re-run driver,
hardened), placebo_direction_seedsweep.py (correction verification), work_r6/
r6_bugfix_rerun.json (machine-readable)}. Fix lives in tools/wt/sources.py nasdaq_history
(uncommitted working tree — coordinator to commit; see disclosure above re co-resident
concurrent hunks).
Repro: python3 -m pytest campaign/agents/chief/coord/HUNT_SECTOR2/tests_tdd_r6.py -q (5
passed); python3 campaign/agents/chief/coord/HUNT_SECTOR2/red_run_head.py (3 failed/2 passed
expected); python3 campaign/agents/chief/coord/HUNT_SECTOR2/hunt_sector2_r6.py; python3
campaign/agents/chief/coord/HUNT_SECTOR2/placebo_direction_seedsweep.py; python3 -m pytest
campaign/agents/chief/coord/HUNT_SECTOR2/tests_tdd*.py -q (44 passed, repo root).

ROUND 6 DONE

## ROUND 7 (2026-09-08 ~19:57-21:0x CST) — FINRA SI corner DEAD-ON-ADMISSION 0/6; R6 fix intact on tracked tree but COMMIT WAVE HAS NOT LANDED (HEAD still pre-fix)

READ-FIRST state: GATES_CONTRACT_V2.md in force (VOL2 V3 per-class placebo still a
PROPOSAL, not depended on); DEAD_IDEAS recounted at round start = 147 data rows
(charter quoted 145-146; concurrent appends are by design; 148 by my append, 149
after concurrent HUNT_FXCARRY2-R7 + mine — recounted after append below). Champion
of record pinned: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha256_16
4358dfab95679b97, n=4805, 2008-03-31..2026-08-27 (verified this session).
DEAD_IDEAS grep: NO prior short-interest family row (the pre-registered corner was
clean to run; bigmove/finra_shortint_build.py is Reg SHO daily short-VOLUME — a
different dataset from the charter's bi-weekly short-POSITION CSI).

(a) NEW CORNER (pre-registered): FINRA bi-weekly short interest (CSI level/slope)
-> sector rotation, monthly rebalance. VERDICT: DEAD ON ADMISSION — 0/6 keyless
routes construct an admissible series (inception<=2013-01-01 per V2 9a + 11-sector
cross-section). Everything probed LIVE this session, scripted in
work_r7/r7_admission_probe.py (re-runnable; machine-readable r7_admission_probe.json):

  [1] Charter endpoint api.finra.org POST otcMarket/consolidatedShortInterest —
      UNREACHABLE_WAF: HTTP 307 -> error.waf.finra.org (Cloudflare). HOST-LEVEL:
      bare GET https://api.finra.org/ also 307; alt group equityShortInterest 307;
      /docs 307; cdn.finra.org Reg SHO daily also 307 (same class). Stable across a
      45s retry. The repo's own altdata6.finra_short_interest() returns err='HTTP
      307' (roster route dead in this env; test_altdata6.py only ever pinned the
      PARSER, not live fetch). DNS resolves to legit Cloudflare IPs (172.65.90.25/26/27)
      — WAF rejection of this network, NOT the DNS-poisoning class CRYPTO2-R7
      reported for deribit. No proxy escape: 127.0.0.1:8118/8119 both closed.
  [2] NYSE Group Short Interest — the ONLY exchange file covering the
      NYSE-Arca-listed SPDRs (11/11 sector ETFs live there), history Jan 1988+ —
      PAID SUBSCRIPTION: live page states 'Purchase Now'; guessed keyless URLs 404.
  [3] api.nasdaq.com /quote/<sym>/short-interest — LIVE (200) but universe-rejected:
      'Short interest is only supported for Nasdaq Listed stocks'; XLK refused as
      assetclass=etf AND as stocks. Even for covered names the served history is
      23 semi-monthly rows (AAPL 2025-09-15..2026-08-14, ~0.9y) -> inception_fail
      on BOTH the universe axis and the span axis.
  [4] Finnhub /stock/short-interest with the repo's own FINNHUB_KEY — 403 premium.
  [5] cdn.cboe.com Bats_Listed_Short_Interest-finra-YYYYMMDD.csv (keyless, live,
      FINRA-derived) — INCEPTION_FAIL: archive starts between 2015-05-06 and
      2015-05-11 (20150506 -> 403 AccessDenied, 20150511 -> 200), ~2.4y after the
      2013-01-01 bound; AND universe mismatch: BZX-listed only, 0/11 SPDRs (SPDRs
      trade NYSE Arca; the XL* symbols in the file are Cboe's own ETF line), 5
      quasi-sector BZX ETFs in the whole 2022 file.
  [6] On-disk Reg SHO vintage (tools/quant/bigmove/data/finra_regsho/: 181 daily
      files 20190102..20240805 + finra_short_ratio_monthly.parquet n=104,004 rows,
      14,852 tickers) — REAL fetched data, but 2 DISJOINT windows (2019-01..02,
      2024-01..08) = max 8 contiguous monthly obs per SPDR -> materially-short
      span, UNJUDGEABLE (V2 9b).

  DIAGNOSTIC LEG (work_r7/r7_si_diagnostic.py -> r7_si_diagnostic.json; NOT a gate,
  never evidence of edge): z(short_ratio level) cross-section at month m -> long
  bottom-3 / short top-3, hold m+1, monthly, T+1, 6.4bps full-|dW| on the real
  vintage: n=7 hold months (2024-02..2024-08): mean net -0.4304 pct/mo = -5.16
  pct/yr ann, SR -0.376, hit 3/7. Mirrored sign +5.16 pct/yr REPORTED ONLY —
  choosing a sign after seeing 7 obs would be p-hacking; nothing here is
  adoptable or claimable. One driver bug fixed pre-results: month-END resample
  stamps vs month-START parquet stamps mis-aligned to 0 evaluable months (fixed
  via to_period('M').to_timestamp(); first run output NO_EVALUABLE_MONTHS is in
  this round's shell history for honesty).

  Consolidation-date logic + PIT lag (documented for the record): CSI settles
  semi-monthly (mid-month + month-end settlementDate), FINRA publishes +2 trading
  days; a monthly consumer would read the latest settlement <= month-end m with a
  2-day lag guard — constructible in principle, unreachable per routes above.
  Charter's non-shortable-universe constraint: MOOT (no weights ever constructed
  from admitted data). Honest negative into DEAD_IDEAS row 149 (source
  HUNT_SECTOR2-R7; recount verified 148->149, one row, trailing newline kept).

(b) R6 nasdaq_history fix survival on the tracked tree — VERDICT: FIX INTACT,
    COMMIT WAVE NOT LANDED. Evidence:
  - git: tools/wt/sources.py tracked but MODIFIED vs HEAD (139-line diff, 133
    insertions); 'git show HEAD:./tools/wt/sources.py | grep truncated history' = 0
    hits (pre-fix at HEAD); working tree = 1 hit (fix present). Last commit touching
    the file remains c3c8730 (pre-dates my fix). The 'commit wave lands this
    standup' premise did NOT materialize as of 21:0x.
  - HEAD-semantics RED harness (red_run_head.py, re-run): 3 failed / 2 passed —
    exactly the R6 RED signature, proving HEAD is still pre-fix.
  - 44-test suite from repo root on the tracked tree: 44 passed in 4.28s (16 r2 +
    14 r3 + 9 r5 + 5 r6; includes the 5 r6 fail-closed tests).
  - Clean-import live probes: SPY days=400 -> 440 bars, 200 -> 226, 60 -> 72, QQQ
    60 -> 72, err=None; defect asks still fail closed with the served window named
    (XLK days=6500 -> 'truncated history: asked 6500 bars from 1998-03-09, served
    2514 bars from 2016-09-06'; days=2600 same shape). Response is oldest-first
    ascending (verified monotonic; my R6 findings prose quoted the list tail —
    same vintage, orientation clarified here).
  - CONCURRENT-WRITER DISCLOSURE (unchanged from R6, re-verified): working-tree
    sources.py still carries 3 foreign hunks not mine (kr_history/_kr_parse_items,
    _stooq_symbol/stooq_quote hardening, polygon_history epoch-ms normalization —
    4 grep hits, untouched, uncommitted, not commit-verified by me). Coordinator:
    commit-time attribution needs a per-hunk split, not a file-level claim.

FLEET CONTEXT: HUNT_CRYPTO2-R7 (row 148) hit network blocks in the same window
(deribit DNS-poisoning class). This round's FINRA block is the WAF-rejection class
(legit IPs, Cloudflare 307->error.waf.finra.org) — distinct mechanism, same
takeaway: keyless altdata routes are degrading this week; admission probes must
run BEFORE any engine work (they did here: ~40 min of probing, zero engine code
written against unreachable data).

ARTIFACTS: coord/HUNT_SECTOR2/work_r7/{r7_admission_probe.py,
r7_admission_probe.json, r7_si_diagnostic.py, r7_si_diagnostic.json}. Repro:
python3 coord/HUNT_SECTOR2/work_r7/r7_admission_probe.py (re-probes live routes;
expect same verdict unless FINRA unblocks); python3
coord/HUNT_SECTOR2/work_r7/r7_si_diagnostic.py (deterministic); python3 -m pytest
coord/HUNT_SECTOR2/tests_tdd*.py -q from repo root (44 passed).

ROUND 7 DONE
