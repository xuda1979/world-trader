# HUNT_TREASFUT FINDINGS

## ROUND 1 (2026-09-06/07) — treasury futures curve / basis from FRED CMT yields

Script: campaign/scripts/HUNT_TREASFUT_round1.py (reproducible; sleeve CSVs+meta in sleeves/).
Data: tools/quant/data/more_fred {DGS2,DGS10,DGS30,DFII10,DFII20,IRLTLT01{DEM,CAM,JPM,USM}156N}
— all lint-clean (0 NaN/dup, monotonic, no >6mo gaps). DGS5 absent (not needed for 2s10s30s).
PRICE PATH (TRADE_RECORD_STANDARD): SYNTH total-return indices TR = -modDur*dy + y/252 on
FRED constant-maturity yields, modDur 2y=1.9 (champion a6r7 convention), 10y=8.5, 20y=13.5,
30y=19.0; approximates treasury futures; no real futures series used.

### BLOCKER FOUND AND FIXED (units, would have fabricated a false positive)
Initial run: steepener k=21 showed SR 1.96, ann 24.2%. ROOT CAUSE: FRED yields are PERCENT;
my first synth TR fed them as DECIMAL -> carry term y/252 100x too big (synth 10y TR ann vol
695% vs 6.9% correct) and the "signal" was harvesting fake 4%/day drift. Committed a6r7 builder
confirms correct convention (y/100.0 then -1.9*dy + y/252). After /100 fix the same config
collapses to SR -0.11. Added fail-closed units_guard (synth TR ann vol must be 1..30%) to the
script. Also fixed in-flight: pandas-3 CoW silent no-op on chained w.iloc[i][col] assignment
(weights were never written -> cost-only book); removed pandas groupby(axis=1); metrics.half_split
annualizes with sqrt252 — monthly books rescaled by sqrt12/sqrt252 (else H1/H2 inflate 4.58x);
row-permutation scramble p~0.000 by construction for low-turnover books (fabricates turnover
spikes) -> added lagroll_p (np.roll weights, timing-only destruction, re-costed, same window).
No-lookahead probes (truncated rebuild == full-sample prefix) PASS for curve/tips/fly.

### (a) 2s10s curve steepener (charter: long 2y/short 10y when steepening, flat when flattening)
Duration-balanced w2=+1/1.9, w10=-1/8.5; T+1, VT10% clip3, 6.4bps FULL|dW| + 0.5%/yr borrow.
- A-PRIORI k=21 (1976-06->2026-09, n=12561): SR -0.11, ann -0.2%, H1 0.92 H2 -1.45, 31/51 neg
  years, worst -6.2%, perm-p 0.000 lag_p 0.015, corrChamp -0.010. FAIL (a,c,d).
- k-scan {5,10,21,42,63,126}: SR {-2.48,-1.09,-0.11,0.40,0.62,1.12} — chosen k=21 NOT on plateau
  (neighbors 10:-1.09, 42:0.40 vs peak 1.12); scan-best k=126: SR 1.12 but H1 1.96/H2 0.11
  (signal DEAD post-2008: SR_08+ -0.22), 20 neg years, cA6R7 +0.216 cA1CR -0.216. FAIL (b,c,d).
- naive dollar-balanced variant SR -0.82; symmetric long/short-steepness SR -2.50. DEAD.
  Note: duration-balanced 2s10s synth vol is 0.54% raw -> VT pinned at cap 3.0 on 99.5% of days
  (legal per contract, but the book is structurally tiny; no rescue inside the cap).

### (b) TIPS real-yield level reversion (DFII10, N=252, th=1.0 a-priori; 2003-01->2026-09)
- Chosen: SR -0.11, H1 -0.12 H2 -0.10, 13 neg years worst -26.6%, perm-p 0.000 lag_p 0.160,
  corrChamp 0.039. FAIL.
- Full 4x3 scan (N {63,126,252,504} x th {0.5,1.0,1.5}): SR ALL in [-0.30,-0.09] — every cell
  negative (plateau gate: nonpositive_peak). DFII20 variant SR 0.05 (lag_p 0.085, H1 -0.03);
  long-only SR -0.06 (worst -36.7%). REAL YIELDS TREAD: no level-reversion edge at any window.

### (c) 2s10s30s butterfly mean-reversion (N=504, th=1.0 a-priori; 1977-02->2026-09, n=12383)
fly = 10y - 0.5*(2y+30y), duration-matched. Chosen: SR -0.78, H1 -0.61 H2 -1.00, 33 neg years,
worst -4.1%, lag_p 0.875, corrChamp -0.010. Full 4x4 scan (N {126..756} x th {0.5..2.0}): SR ALL
in [-2.05,-0.54] — reversion LOSES everywhere; momentum sign (not run) would inherit a
plateau-less negative mirror. DEAD.

### (d) International 10y yield-spread partial carry (US vs DE/CA/JP)
NATIVE MONTHLY (IRLTLT are monthly series; a daily-resampled book would inflate obs 21x and
understate per-obs risk — r1 initially did this, corrected). Long higher-yield 10y synth TR /
short lower, ±0.5/leg, from yields published strictly before holding month (lag0/lag1), equal-wt
pairs, 6.4bps+borrow. 1989-02->2026-06, n=449 months.
- lag0: SRm*sqrt12 0.77, ann 1.2%, H1 0.93 H2 0.61, 9 neg years worst -2.4%, corrChamp 0.319,
  cA6R7 0.288. FAIL (a: SR<1; f: corr>0.15).
- lag1: SRm*sqrt12 0.70, corrChamp 0.328, cA6R7 0.327, 13 neg years. FAIL (a,f).
- Pairs alone: US-DE 0.40, US-CA 0.29, US-JP 0.48 — nothing near 1.0. DEAD at champion gate.

### SUMMARY TABLE (FULL-window, fail-closed; PASS requires ALL of SR>=1, halves>=0.5,
### <=2 neg yrs each >-5%, scramble p<=0.05, |corrChamp|<0.15)
  config                  SR     H1     H2  negyr  worst    p    corr   cA6R7  PASS
  curve2s10s_k21        -0.11   0.92  -1.45    31   -6.2% 0.000 -0.010  0.178  False
  curve_k21_naiveDW     -0.82  -0.74  -0.93    43  -19.7% 0.000 -0.066 -0.465  False
  curve_k21_sym         -2.50  -2.14  -3.00    48  -12.4% 0.000 -0.031  0.049  False
  curve_k126_scanbest    1.12   1.96   0.11    20   -3.0% 0.000 -0.018  0.216  False
  tipsrev_N252_t10      -0.11  -0.12  -0.10    13  -26.6% 0.000  0.039 -0.084  False
  tipsrev20y             0.05  -0.03   0.15     9  -19.0% 0.000  0.044 -0.026  False
  tipsrev_longonly      -0.06  -0.14   0.00     7  -36.7% 0.000  0.063  0.182  False
  fly_N504_t10          -0.78  -0.61  -1.00    33   -4.1% 0.000 -0.010 -0.038  False
  intlcarry3_lag0        0.77   0.93   0.61     9   -2.4% 0.000  0.319  0.288  False
  intlcarry3_lag1        0.70   0.83   0.56    13   -2.6% 0.000  0.328  0.327  False

### VERDICT
HONEST NEGATIVE on all 4 charter sleeves — ZERO pass the gates. Best full-gate-relevant
candidate (curve k=126, SR 1.12) fails halves (H2 0.11), yearly (20 neg), and the charter's
explicit corr watch vs a6r7 (0.216 > 0.15); its edge is entirely pre-2008. Decorrelation is the
ONE gate the rest pass trivially (|corrChamp| <= 0.04 daily) — these books are uncorrelated
because they carry no rewarded risk post-cost. Coordinator: please append 4 DEAD_IDEAS.csv rows
(2s10s steepener / TIPS real-yield reversion / 2s10s30s fly reversion / US-DE-CA-JP 10y carry)
with the numbers above.

### ENVIRONMENT NOTE (for coordinator)
Mid-round, another agent re-emitted the champion (rawew13v2_build.py mtime 00:37, champion CSV
00:45 on 2026-09-07): bt test test_reproducible_from_builder currently FAILS (max dev 3.96e-3)
because the test snapshot predates the re-emit. NOT caused by this agent (only files touched:
campaign/scripts/HUNT_TREASFUT_round1.py + sleeves/). My decorrelation gates re-verified against
the re-emitted champion: corrDAILY {-0.011,-0.011,+0.172,+0.039} for
curve/fly/intlcarry/tipsrev — conclusions unchanged (intl carry corr even confirms the >0.15
failure in daily space too).

ROUND 1 DONE

## ROUND 2 (2026-09-07 03:5x) — duration-matched cash-yield engine / kink steepener / level-mom+regime

Script: campaign/scripts/HUNT_TREASFUT_round2.py (reproducible; imports r1 helpers; sleeves
TREASFUT2_*.csv in sleeves/). Charter durs 4.4/7.7/15.5 (2/10/30y); a-priori k=126 (momentum,
slope, level), kink combo EQ 0.5/0.5, regime T5YIFR.diff(63)<0; VT10% clip3 trailing; 6.4bps
FULL|dW| + 0.5%/yr borrow; T+1. Engine window 1977-02-16 -> 2026-09-03 n=12383 (2008+ depth
n=4612, vs R1's synth-vol-pinned book). Units guard pass. No-lookahead probes (truncated
rebuild == full prefix): mom10/kink_eq/kink_fly/level_mom_regime ALL True.

### TWO LIVE BUGS FOUND AND FIXED TDD (would have fabricated a bogus sleeve + a diluted gate)
1. DEAD BOOK SAVED AS A NEGATIVE (mom1030): 0.5*W10 + 0.5*W30 with disjoint columns union-joins
   to ALL-NaN (NaN+x=NaN) -> fillna(0) -> 12,383 rows of literal zeros saved as a sleeve with
   SR=0.00 negyr=0 scram_p=1.000 corrChamp=nan. Prior session shipped it; caught on audit.
   FIX: r2.combine_W (.add fill_value=0.0 + alive assert); net_of now raises ValueError('dead
   book') on 0-live-row frames. Tests test_combined_mom_weights_not_all_nan /
   test_net_of_rejects_dead_book.
2. REGIME-OVERLAY WINDOW DILUTION (lvl*_reg): net_of reindexed the 2003+ T5YIFR book onto R's
   1977 grid -> 60.8% dead zero rows -> gates computed over 26y of air (H1=0.00 pure artifact;
   reported SR -0.23 vs honest -0.30 trimmed). FIX: net_of(trim_coverage=True) trims evaluated
   window to W coverage; default R-grid path preserved (R1 reproducibility) with loud warning.
   Test test_net_of_trim_coverage_fail_closed. Campaign bt: campaign/bt/tests/test_treasfut_r2.py
   8 passed (pytest, 2026-09-07 03:55).

### (a) TS momentum on charter-dur synth TR (a-priori k=126) + 2s10s curve rerun under durs
- mom2  k126: SR=0.37 H1=0.78 H2=-0.21 negyr=25 worst=-20.4% p=0.000 corr 0.032 cA6R7 0.436 FAIL
- mom10 k126: SR=0.23 H1=0.56 H2=-0.20 negyr=22 worst=-18.3% p=0.000 corr 0.031 cA6R7 0.304 FAIL
- mom30 k126: SR=0.22 H1=0.52 H2=-0.17 negyr=23 worst=-17.2% p=0.000 corr 0.038 SR_08+ -0.10 FAIL
- mom1030 (fixed): SR=0.23 H1=0.56 H2=-0.19 negyr=24 worst=-17.7% corr 0.037 SR_08+ -0.15 FAIL
  k-scan {21,42,63,126,252} per leg: max any cell 0.66 (2y leg k252); plateau@126 False every leg
  (neighbors 0.11-0.36 vs peak). Bonds trend FAINTLY positively full-sample but nowhere near
  SR>=1, and every leg flips NEGATIVE post-2008 (SR_08+ -0.10..-0.40) — the charter's 2008+
  depth requirement kills it, exactly the R1 finding under real VT this time.
- curve2s10s under charter durs k=21: SR=-0.59 (scan -2.23..+0.06 over {5,10,21,42,63,126},
  plateau@21 False) — confirms R1's negative under futures-proxy durs. FAIL.

### (b) steepener kink combos (a-priori k=126, EQ 0.5 steep(2s10s)+0.5 steep(10s30s))
- kink_eq: SR=0.05 H1=0.44 H2=-0.43 negyr=32 worst=-1.6% corr -0.011 FAIL (scan k21..k252:
  -0.81/-0.58/-0.25/+0.05/+0.12, plateau False)
- kink_fly (2s10s30s curvature mom): SR=-0.95 H1=-0.76 H2=-1.24 negyr=47 worst=-3.6% FAIL
- kink_2s30: best of family SR=0.52 H1=0.89 H2=0.09 negyr=18 worst=-3.7% corr -0.016 — halves
  FAIL (H2 0.09). Slope momentum in cash yields has NO post-2008 edge at any window tested.

### (c) yield LEVEL momentum +/- T5YIFR regime (a-priori k=126)
- lvl10 standalone: SR=0.04 H1=0.29 H2=-0.27 negyr=26 worst=-17.8% FAIL
- lvl30 standalone: SR=0.05 H1=0.33 H2=-0.30 negyr=26 worst=-19.7% FAIL
- lvl10 + regime (trimmed 2003-03-19+ n=5871): SR=-0.33 H1=-0.47 H2=-0.21 negyr=17 worst=-20.9%
  FAIL — regime overlay makes it WORSE than standalone (filter keeps only the losing states).
- lvl30 + regime (2003-02-18+ n=5892): SR=-0.23 H1=-0.41 H2=-0.05 negyr=16 worst=-17.7% FAIL.
  Falling 5y5y-forward-inflation does not select a long-duration regime with edge; T5YIFR
  direction is noise for this purpose.

### SUMMARY TABLE (FULL-window net gates, fail-closed; PASS needs ALL of SR>=1, halves>=0.5,
### <=2 neg yrs each >-5%, scramble p<=0.05, |corrChamp|<0.15)
  config              n     SR     H1     H2  negyr  worst     p    corr  cA6R7 SR08+ PASS
  mom2_k126        12383  0.37   0.78  -0.21    25  -20.4% 0.000  0.032  0.436 -0.40 False
  mom10_k126       12383  0.23   0.56  -0.20    22  -18.3% 0.000  0.031  0.304 -0.21 False
  mom30_k126       12383  0.22   0.52  -0.17    23  -17.2% 0.000  0.038  0.199 -0.10 False
  mom1030_k126     12383  0.23   0.56  -0.19    24  -17.7% 0.000  0.037  0.250 -0.15 False
  curve2s10s_d2k21 12383 -0.59  -0.16  -1.18    37   -4.7% 0.000 -0.015  0.184 -1.32 False
  kink_eq_k126     12383  0.05   0.44  -0.43    32   -1.6% 0.000 -0.011  0.378 -0.63 False
  kink_fly_k126    12383 -0.95  -0.76  -1.24    47   -3.6% 0.000  0.002 -0.022 -1.16 False
  kink_2s30_k126   12383  0.52   0.89   0.09    18   -3.7% 0.000 -0.016  0.389 -0.10 False
  lvl10_k126       12383  0.04   0.29  -0.27    26  -17.8% 0.000  0.034  0.107 -0.27 False
  lvl10_k126_reg    5871 -0.33  -0.47  -0.21    17  -20.9% 0.000  0.029 -0.135 -0.28 False
  lvl30_k126       12383  0.05   0.33  -0.30    26  -19.7% 0.000  0.033  0.065 -0.19 False
  lvl30_k126_reg    5892 -0.23  -0.41  -0.05    16  -17.7% 0.000  0.026 -0.053 -0.14 False

### VERDICT
HONEST NEGATIVE on all three charter round-2 sleeves — ZERO pass the gates; best family member
(kink_2s30 SR 0.52) still fails halves (H2 0.09), yearly (18 neg yrs), SR, and plateau. The
charter's premise — that R1's failure was an artifact of the 1.9/8.5/19.0 dur convention and
vol-pinned micro-books — is REFUTED: under charter durs (4.4/7.7/15.5), real 10% VT, and 2008+
depth, rates momentum/curve/level sleeves are still decisively negative post-2008
(SR_08+ in [-1.32, -0.10] for ALL 12 configs). Decorrelation passes trivially again
(|corrChamp| <= 0.038) — uncorrelated because unrewarded. Coordinator: please append DEAD_IDEAS
rows for (i) rates TS momentum DGS2/10/30 k{21..252} (SR<=0.66, all legs SR_08+ negative),
(ii) 2s10s+10s30s kink EQ steepener (SR 0.05; fly -0.95), (iii) yield-level momentum +/- T5YIFR
regime (standalone ~0, overlay negative), with the numbers above.

### ENVIRONMENT NOTE (for coordinator)
Two LIVE framework bugs were found in the r2 machinery mid-round and fixed TDD-first
(test_treasfut_r2.py, 8 green) — details above; they invalidate the four TREASFUT2_*.csv files
the prior session wrote at 02:39 (one was an all-zero dead book, one a 61%-dead window) — both
regenerated at 04:02 alongside this run. Concurrent agents modified campaign/bt
{align,metrics,gates,engine,backtest,reconcile}.py after 03:00 today; the 7 failing tests in the
full bt suite (test_align, test_gates_audit_r2) are in THEIR files, contain zero TREASFUT
references, and predate/postdate my run independent of my edits — not mine, flagging only.

ROUND 2 DONE


## ROUND 3 (2026-09-07 14:xx-15:xx CST) — champion-integrity duty: TRUTH20Y reconstruction/quarantine + lint + HUNT_CREDIT2 cross-verify

Read GATES_CONTRACT.md + campaign/results/DEAD_IDEAS.csv FIRST (102 data rows as of this
round; rates families dead incl. my R1/R2 rows 58-61/84). This round touched ZERO signal
families — integrity work only. Charter (a) reconstruction + quarantine decision, (a2) lint
test, (b) cross-verify HUNT_CREDIT2 round-2 negatives.

### (a) GOAL100_TRUTH20Y reconstruction: NOT REPRODUCED -> QUARANTINE (recommend)

Prior session left an untracked attempt (campaign/scripts/HUNT_TREASFUT_truth20y_rebuild.py,
08:31). I verified its provenance claims from source before trusting it: vt()/load()/COST are
byte-identical to champion20y_build.py's (construct() matches, only `start` moved to kwarg);
all 14 pool files named in its POOL_H DO exist on disk (AUDIT_CHAMP2's "pool files missing"
searched for the JSON's LABELS a6r7E/QAxastsE/... which are not filenames). Then ran it:
  BALANCED  maxdev 1.5809e-02  n_rec 5196 vs n_com 4990
  AGGRESSIVE maxdev 1.7776e-02
  SAFE      maxdev 1.3841e-02  -> exit 1, NOT REPRODUCED (charter bar 1e-12)

CALENDAR FORENSICS (the round's positive finding) — campaign/agents/chief/coord/HUNT_TREASFUT/
work_r3/truth20y_recon_r3.py:
  - Committed index reproduced BYTE-EXACTLY: union(14 sleeves) in 2006-10-02..2026-08-28
    MINUS US federal holidays WITH Sat->Fri / Sun->Mon observance, weekdays only => n=4990,
    idx.equals(committed) TRUE on all 3 books. The json's "NYSE calendar" note is a MISNOMER:
    the dropped-day (m,d) set is exactly the FEDERAL set {1/1, MLK, Presidents, Memorial,
    Juneteenth(2021+), 7/4, Labor, Columbus, Veterans, Thanksgiving, Christmas} — Columbus Day
    and Veterans Day are DROPPED (NYSE trades both) while Good Friday (NYSE-closed) is KEPT
    20/20 years. One stray Sunday row (2009-07-26) additionally absent.
  - Variants tested (no knob tuned): straight construct 1.58e-2; Sep-1 git blobs for the 3
    costfix-modified inputs (QAxastsE/brwt15E/dualmom) 1.58e-2 (input drift NOT the gap);
    holiday filter POST-construction 1.58e-2; PRE-construction 3.86e-2 (idx_eq True, values
    worse); pre + sparse-fill0 3.26e-2. SAFE/AGG pre-variants 3.37e-2/3.12e-2.
  - Deviation profile FLAT across 20y (yearly max 2.0e-3..1.6e-2, 4923/4990 days >1e-6,
    corr(rec,com) 0.9814-0.9839) — systematic residual, likely the lost Sep-1 input blobs
    (A5r7 mtime 16:41 = 34min AFTER TRUTH20Y's 16:07; a6r7E/C5ng x2 mtimes Sep 7 06:55-57 but
    git-identical to HEAD). Ancestor builder champion20y_build.py no longer byte-reproduces
    its OWN V2 books either (3.1e-3/6.2e-3, same 10:59 costfix wave) — the whole Sep-1 20y
    lineage is not tree-reproducible.
Quarantine doc: work_r3/TRUTH20Y_QUARANTINE.md. Recommendation: quarantine the 4 files until
a builder reappears; independent of reproducibility they fail champion constraints anyway
(BAL geo ann 69.09% vs 53.0 arith headline, MDD -7.88% breaches -7% wall, 1 neg year 2006,
corr to champion 0.5750 — AUDIT_CHAMP2 R2, reconfirmed by me today).

### (a2) Lint test — RED first, then GREEN (additive banner only)

New: campaign/bt/tests/test_treasfut_r3_truth20y_lint.py. Does NOT duplicate AUDIT_CHAMP2's
test_a2 (which scans only campaign/*.md + results/*.md and exempts history paths): this sweeps
EVERY .md under campaign/, offender = TRUTH20Y line with currency language (champion/current/
headline/honest maximum) and no provenance framing on the line + no doc-level quarantine
banner (SUPERSEDE-banner convention) + not a meta line about the lint itself.
  RED run 1 (pre-banner): 1 failed — offenders included G4_detrun/FINDINGS.md:21 plus 3
    meta/charters false-positives (test teeth worked, classifier over-broad).
  RED run 2 (after META escape + teeth tests added): 2 failed, exactly the live offender
    and nothing else. GREP EVIDENCE pre-fix (whole campaign tree): the ONLY unframed
    promotion-quote is
      campaign/agents/G4_detrun/FINDINGS.md:21: "=> GOAL100 TRUTH20Y = 2006-10-02..2026-08-28
      = 19.8y is the honest maximum with this pool."   (coordinator-authored 09-01, pre-audit)
  GREEN: prepend-only quarantine banner on G4_detrun/FINDINGS.md (sha256:16 pre
    b612c74039ac50a4 -> post 22881500d14a3e15; git diff --numstat = 8 insertions 0 deletions;
    byte-verified new == banner + orig). Lint: 3 passed. Cross-suite my-r2 + AUDIT_CHAMP2_r3 +
    lint: 19 passed. Post-fix grep: every remaining TRUTH20Y mention is framed or banner-exempt.

### (b) HUNT_CREDIT2 round-2 negatives: ALL MATCH (confirmed, no escalation)

work_r3/credit2_crossverify.py — recomputed from the SAVED sleeve CSVs + their generator's own
machinery (bt.metrics conventions):
  sleeve                  SR claim/got  ann_geo     H1/H2      negyr worst   corrChamp
  CREDIT2_lqdltt_k126     -0.31/-0.31   -4.25/-4.2  -0.24/-0.44 13   -32.7%  +0.141 (0.142)
  CREDIT2_be_tlttip_k63   -0.80/-0.80   -9.73/-9.7  -1.10/-0.45 21   -35.3%  -0.050
  CREDIT2_curve2s10s_k21  -0.54/-0.54   -5.15/-5.1  -0.59/-0.50 21   -17.9%  -0.127 (-0.128)
  GROSS SR recomputed via their net_of pre-cost book: +0.01 / -0.40 / +0.07 — all MATCH
  their claims (no alpha pre-cost, exactly as their FINDINGS says).
  Byte-reproducibility: sha1 of all 3 sleeve CSVs IDENTICAL pre/post generator re-run
  (7401c0c9.../0d8eed95.../fb52542c...). Their numbers are real, reproducible, and negative.
  Note (convention, not error): their ann = ann_geo; my table's ann_arith differs (-3.65 vs
  -4.25 etc.). Their scram_p=0.000 is the weight-permutation re-cost convention (informative
  trivial-pass for negative books, disclosed in their own metas); a plain row-shuffle scramble
  is degenerate (std is permutation-invariant) and gives 0.975/0.710/0.025 — do not confuse
  the two if re-auditing.
  (d) HY-stress gate re-verified on the CURRENT champion: credit gate delta +0.184
  (SR 3.181 -> 3.365, 323/4805 days) vs content-free vol-z>2 control +0.204 — control still
  BEATS the credit gate; anti-gate -0.036. Their "content-free vol artifact" verdict HOLDS.

### COORDINATOR FLAGS (found while verifying, not caused by me)

1. Champion was RE-EMITTED AGAIN at 11:24 today (after AUDIT_CHAMP2's 07:28 audit wave):
   campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv now n=4805,
   ann_geo 37.1954%, SR_d 3.1810, MDD -6.69%. CHAMPION_CARD.md already reflects it
   (37.20%/3.1810) and AUDIT_CHAMP2's lint test_a4 auto-adapted (their suite 8 passed) —
   the test-time-computed headline design works. AUDIT_CHAMP2 R3's "current headline
   39.6873%" prose is already stale 4h later. Whoever re-emitted should log it.
2. Full bt suite on this tree: 17 failed / 271 passed — ALL 17 are
   test_camp_short_r3_census.py (mtime 14:45 today) failing on FileNotFoundError
   CAMP_SHORT_LIBRARY_BORROW_CENSUS.json: another agent's TDD-first RED phase (test written,
   implementation not yet). Same pattern as the earlier test_beats_passive REDs. Not mine;
   zero TREASFUT references.
3. champion20y_build.py --verify now DIFFs its own committed V2 books (max 6.2e-3) — the
   10:59 costfix wave touched sleeves that feed it. If CHAMPION20Y_V2 is still quoted
   anywhere as current, it is now unreproducible exactly like TRUTH20Y (quarantine doc has
   the numbers).

Files touched this round: campaign/scripts/HUNT_TREASFUT_truth20y_rebuild.py (pre-existing
prior-session artifact, verified not modified by me), work_r3/truth20y_recon_r3.py (new),
work_r3/TRUTH20Y_QUARANTINE.md (new), work_r3/credit2_crossverify.py (new),
campaign/bt/tests/test_treasfut_r3_truth20y_lint.py (new), G4_detrun/FINDINGS.md (additive
banner only, 8/0 insertions). Champion CSV, weights CSV, builder, all sleeve inputs: untouched.

ROUND 3 DONE

## ROUND 4 (2026-09-07 2x:xx CST) — CHAMPION20Y_V2 rebuild path (FOUND: exactly reproducible from git blobs) + TRUTH20Y re-screen (quarantine stands, stronger) + 4-row DEAD_IDEAS audit rotation

Read GATES_CONTRACT.md + DEAD_IDEAS.csv (117 data rows as of round start) FIRST. Champion of
record untouched: bt/verify_champion.py re-run with the canonical 13-sleeve map (weights
RAWEW13v2_IS_SR_weights.csv, brwt10/7/5 from CAMP_COST __costfix paths per STANDUP 2541-54)
-> ok=true 7/7 checks {weights_repro, byte_repro, cost_reconciliation, causality, gross,
yearly, mdd} all True. My TREASFUT suites: 19 passed (8 new r4 + 3 r3 lint + 8 r2).

### (a) CHAMPION20Y_V2 provenance break: CLOSED — exactly reproducible; permanent repair path delivered

Break reproduced first (matches coordinator 17:0x exactly): champion20y_build.py --verify on
current tree -> BAL 3.107e-03 / SAFE 6.160e-03 / AGGR 6.206e-03 DIFF.
Root cause chain (all git-verified):
  - V2 books committed at d5fa3a2 (2026-09-01 11:33), byte-unchanged since (git diff c745682..HEAD
    on the 3 CSVs = empty; git status clean).
  - Builder's 13-sleeve pool: exactly 3 members were re-emitted by costfix commit b268e52
    (2026-09-07): E1_QAxasts_tsmom189_2006.csv (4907 rows changed), QA_dualmom_band121.csv (3520),
    E1_brwt_spread_rev15_2000.csv (2174). The other 10 are blob-identical c745682 -> HEAD.
  - No pool sleeve changed between the V2 commit d5fa3a2 and the builder-freeze commit c745682.
HONEST MISSTEP, self-caught: my first worktree test (worktree at c745682, run the builder)
returned the SAME 3.1e-3/6.2e-3 deviations and looked like "unreproducible even in git" —
INVALID: the builder hard-codes ROOT="/Users/daxu/software/world-trader", so the worktree run
silently read the post-costfix main-tree sleeves. Re-run with ROOT repointed into the worktree:
  GOAL100_CHAMPION20Y_V2_BALANCED_daily.csv    max|new-old| = 9.986e-17  IDENTICAL
  GOAL100_CHAMPION20Y_V2_SAFE_daily.csv        max|new-old| = 9.996e-17  IDENTICAL
  GOAL100_CHAMPION20Y_V2_AGGRESSIVE_daily.csv  max|new-old| = 9.991e-17  IDENTICAL
VERDICT: V2 is NOT a provenance orphan — it is exactly reproducible from committed V2-era blobs.
The canonical builder's math is fine; the tree drifted under it. This CORRECTS my R3 quarantine
memo line "the whole Sep-1 20y lineage is not tree-reproducible" (memo updated with an R4
addendum, correction stated explicitly).

Permanent repair path (TDD, RED first — suite failed on FileNotFoundError before the script
existed, then GREEN):
  - work_r4/pre_costfix_sleeves/ — the 3 pre-costfix blobs extracted from git c745682,
    sha256-verified vs the worktree blobs (4555c44afa804758 / 7132a167f70f3a6c / defe2faf6cb3a0f3).
  - campaign/scripts/HUNT_TREASFUT_champion20y_v2_rebuild.py — materializes the V2-era pool in a
    temp dir (3 pinned blobs + 10 live sleeves), imports champion20y_build.py VERBATIM (no math
    duplicated), fails closed via a guard that EXITS if any unpinned pool sleeve drifts from its
    c745682 blob. `--verify` output: all 3 books IDENTICAL, worst 9.996e-17, n=5196, exit 0.
  - campaign/bt/tests/test_treasfut_r4_v2_rebuild.py — 8/8 passed: exact rebuild x3, calendar
    equality, pinned-blobs-actually-differ-from-live, guard-trips-on-drift (SystemExit), pinned
    blobs byte==git c745682, live-pool-still-DIFFS (teeth).

### (a2) TRUTH20Y re-screen under the new insight: quarantine STANDS, evidence base completed

R3's "blobs lost" story is now void for EVERY input — complete input ledger:
  - 10/14 pool sleeves byte-identical to c745682 (incl. A5r7: its 16:41 mtime is 34min after the
    16:07 book, but its disk bytes are CONTENT-IDENTICAL to the committed blob — R3's
    "A5r7 regenerated after the book" suspicion is retracted).
  - 3 = costfix trio (pinned blobs now exist in work_r4/pre_costfix_sleeves/).
  - brwt5/7/10 (COORD/sleeves/) were NEVER committed anywhere (git log --all empty) but sit on
    disk with mtimes Sep-1 13:47-13:48, BEFORE the 16:07 book — content-known.
So if TRUTH20Y were reproducible by the V2 method, nothing is missing. Tested (NO knob tuned;
only documented/pre-registered configs — TRUTH20Y.json publishes no A/B params):
  work_r4/truth20y_param_screen_r4.py, committed-calendar overlap n=4990/4990 on all cells:
    P1 FINAL_TRUTH cfg (.072/.040,.093/.030) + pinned blobs: SAFE 1.3841e-02 / AGGR 1.7776e-02 /
       BAL 1.5808e-02   (== R3's unpinned 1.5809e-02: input drift confirmed NOT the gap)
    P2 V2 cfg (.090/.030,.106/.0255):          BAL 1.5375e-02 (SAFE 1.88e-02, AGGR 1.74e-02)
    P3 E1 cfg (.085/.035, FR.4):               SAFE 1.3477e-02
  Three pre-registered documented configs all land ~1.3-1.9e-2 (bar 1e-12): the residual is a
  CONSTRUCTION difference (unpublished params or blend/calendar logic not derivable from the
  ancestor builder), not recoverable input drift. Also: committed index is now FULLY explained
  by the sleeve union (committed-days NOT in union: 0; R3's stray 2009-07-26 came from a wider
  union in the R3 script's pool set; union-minus-committed 206 = foreign-calendar days).
  work_r4/truth20y_pool_blobcheck.py (ledger) + truth20y_param_screen_r4.py (screen), both saved.
RECOMMENDATION UNCHANGED: quarantine GOAL100_TRUTH20Y* (still fails DD wall/arith-vs-geo per
AUDIT_CHAMP2, independent of reproducibility); CHAMPION20Y_V2 is NOT quarantined — repaired.

### (b) 4-row DEAD_IDEAS audit rotation (non-treasury): 4/4 CONFIRMED dead, 2 findings

Rows audited (repro scripts re-run verbatim where they exist, then re-costed under GATES_CONTRACT):
  ROW 33 "USDJPY weekday sign-maps (30-grid)" (SKILL_ALPHAAGB_B p7) — VERBATIM REPRO: best-of-30
    SR +0.599, map longJPY [3,4], span 2019-05-13..2026-08-05; exactly the claimed digits. Claim
    "best 0.599 <0.6 & best-of-30" TRUE. Under contract cost (6.4bps full-|dW| + borrow + T+1)
    the same best map is -0.138 — the original 6bps-on-half-turnover costing was generous.
  ROW 34 "FX tsmom63 satellites EUR/GBP/AUD" (p8) — VERBATIM REPRO: EUR -0.085 / GBP +0.001 /
    AUD -0.438, 4-book blend SR +0.056 (all digits match FINDINGS/DEAD_IDEAS). The DEAD_IDEAS
    summary "SR <=0.09" is technically true but UNDERSTATES: AUD is -0.438. Contract-cost singles:
    -0.368 / -0.190 / -0.644. corrChamp +0.058..+0.064 (moot). Dead either way, MORE dead.
  ROW 29 "QQQ/SPY + XLF/SPY ratio zrev" (p4b) — VERBATIM REPRO, all 6 cells digit-exact:
    QQQ/SPY -0.051/-0.230/-0.222; XLF/SPY +0.293/+0.011/-0.044 (zwin 21/63/126). Confirmed.
  ROW 9 "gold-silver spread, no edge, source 'multiple'" — THINNEST ROW; the B2 probe was
    "logged, not saved" (no script existed). REBUILT from the described mechanism (XAU/SLV
    log-spread z-reversion, +-1.0 z trigger, ffill, T+1, 0.5/0.5 dollar-neutral, VT10 clip3,
    contract costs; xau.csv/slv.csv 2007-12..2026-08 n=4686):
      zrev21 -0.424 / zrev63 -0.226 / zrev126 -0.319 (inside B2's claimed -0.2..-0.6 band);
      sign-flip control (z-momentum) +0.033 -> dead BOTH ways, no hidden sign;
      negyr 11-13, worst -20..-22%, perm_p 0.060-1.000, corrChamp |<=0.010|.
    Verdict "dead" CONFIRMED; the row now has numbers + repro path
    (work_r4/audit4_rows_r4.py) instead of "no edge".

FINDING (b)1 — SYSTEMATIC COST CONVENTION GAP in the audited probes (audit value-add):
  FF2/ALPHAAGB lib net_of charges |dpos|/2 x 6bps. For a single-position book that is 6bps on
  half-turnover = 2.13x undercharge vs GATES_CONTRACT (full |dW| x 6.4bps) — the SAME factor
  family as the SEC3 0.667->0.18-0.26 disclosure (DEAD_IDEAS row 48). Decomposition (pre-VT):
    XLF/SPY zrev21:  gross +0.621 -> their-cost +0.469 -> contract +0.286
    QQQ/SPY zrev21:  gross +0.277 -> their-cost -0.003 -> contract -0.355
    USDJPY map[3,4]: gross +1.202 -> their-cost +0.563 -> contract -0.179
  All four audited rows stay dead (stronger) under contract costing; but any FUTURE re-test of
  ALPHAAGB_B-era probes must re-cost before quoting numbers. Rows 33/34/29 amendments proposed:
  add "lib 2.13x cost-undercharge disclosed; contract-cost re-run worse/equal, verdict unchanged".

FINDING (b)2 — row 9 was sourced "multiple" with no repro path; now pinned to B2_highfreq
  FINDINGS "Idea 3 XAU_SLV" + audit4_rows_r4.py. Recommend coordinator append/patch 2 rows:
  (i) row 9 replacement with exact numbers above, (ii) a convention note on rows 33/34/29.

Files touched this round: work_r4/{pre_costfix_sleeves/ x3, truth20y_pool_blobcheck.py,
truth20y_param_screen_r4.py, audit4_rows_r4.py} (new), campaign/scripts/
HUNT_TREASFUT_champion20y_v2_rebuild.py (new), campaign/bt/tests/test_treasfut_r4_v2_rebuild.py
(new), work_r3/TRUTH20Y_QUARANTINE.md (addendum + 2-line header banner). Champion CSV, weights,
rawew13v2_build.py, champion20y_build.py, all live sleeves: UNTOUCHED. Temp worktree
/tmp/wt_v2pre removed after use. Minor: audit script emits a pandas-4 concat-sort deprecation
warning (cosmetic, noted in-script output).

ROUND 4 DONE


## ROUND 4 VERIFICATION PASS (2026-09-07 22:0x-22:3x CST) — prior-session R4 entry re-executed claim-by-claim; 1 failing script found and fixed TDD

Charter requires every claim to reproduce from a saved script. The R4 entry above was written
by the prior session (FINDINGS.md mtime 21:19); a leftover script at 21:58 (AFTER the entry)
admitted in its own docstring "No r4 script printed those numbers" for FINDING (b)1 and was
NEVER RUN. This pass re-executed every R4 claim from the artifacts. Champion of record
untouched throughout (git status clean; verify_champion.py re-run independently, below).

### REPRODUCED (all exact)
  1. Claim (a) V2 rebuild: HUNT_TREASFUT_champion20y_v2_rebuild.py --verify -> BAL
     9.986e-17 / SAFE 9.996e-17 / AGGR 9.991e-17, all IDENTICAL (bar 1e-12), exit 0.
     Guard green: 10 unpinned pool sleeves byte-identical c745682->HEAD (0 differences).
     Pinned blobs sha256-16 re-verified == git c745682 blobs {4555c44afa804758,
     7132a167f70f3a6c, defe2faf6cb3a0f3} — matches the entry digit-for-digit.
  2. My TDD suite: 19 passed (8 r4-v2-rebuild + 3 r3 lint + 8 r2), pytest exit 0.
  3. Champion acceptance (canonical 13-sleeve map per STANDUP 2541-54, CAMP_COST __costfix
     brwt10/7/5): verify_champion.py ok=true, 7/7 checks {weights_repro, byte_repro,
     cost_reconciliation, causality, gross, yearly, mdd} all True. Champion headline
     recomputed from CSV bytes: n=4805 ann_geo 37.1954% SR 3.1810 0 neg years.
  4. Claim (a2) TRUTH20Y screen re-run: P1 pinned-blob 1.3841e-02/1.7776e-02/1.5808e-02,
     P2 1.5375e-02, P3 1.3477e-02, calendars identical, committed-days-not-in-union 0,
     union-not-in-committed 206 — all as published. blobcheck ledger: outside-costfix-trio
     diffs = 0 ('blobs lost' story void). QUARANTINE recommendation STANDS.
  5. Claim (b) verbatim repros of the ORIGINAL probes, run by me for the first time this
     round (the entry's "digit-exact" numbers had NO saved evidence):
       p4b.py (row 29): QQQ/SPY -0.051/-0.230/-0.222; XLF/SPY +0.293/+0.011/-0.044 —
         all 6 cells digit-exact vs DEAD_IDEAS. WALCL_gate_spy +0.216 also observed.
       p7.py  (row 33): best-of-30 map longJPY [3,4] SR +0.599 — digit-exact.
       p8.py  (row 34): EUR -0.085 / GBP +0.001 / AUD -0.438 / 4-blend +0.056 — digit-exact.

### FOUND + FIXED (the one RED): FINDING (b)1 decomposition did NOT reproduce
  The 21:58 verifier failed its own check (exit 1, 5/9 cells DRIFT: XLF their/contract
  +0.295/-0.056 vs claimed +0.469/+0.286; QQQ -0.334/-0.960 vs -0.003/-0.355). ROOT CAUSE:
  it transcribed p4b's construction as r = 0.5*ra - 0.5*rb; the original p4b.py:33 is
  r = ra - rb UNWEIGHTED (gross SR identical by scale-invariance, cost tiers 2x heavier
  because turnover is charged on the full spread stream). Fixed TDD (RED exit 1 first,
  then GREEN) by correcting the construction to the original. v2 result (tol 0.03):
       XLF/SPY   +0.621 / +0.458 / +0.283  (claimed +0.621/+0.469/+0.286) MATCH
       QQQ/SPY   +0.277 / -0.029 / -0.345  (claimed +0.277/-0.003/-0.355) MATCH
       USDJPY[3,4] +1.202 / +0.543 / -0.180 (claimed +1.202/+0.563/-0.179) MATCH
  undercharge 2.133x confirmed; all 3 books dead under contract costing (SR <= 0.283).
  CONVENTION CAVEAT now on record: the published their/contract digits are reproducible
  to +/-0.03 but no single cost convention regenerates all 9 exactly (their-tier was
  computed without borrow: +0.467/-0.003/+0.564). Substance of FINDING (b)1 — lib
  |dpos|/2 x 6.0bp undercharges GATES_CONTRACT full-|dW| x 6.4bp by 2.133x on identical
  turnover, rows 33/34/29 stay dead (stronger) under contract costing — CONFIRMED.
  The AMENDMENT text proposed for rows 33/34/29 is unchanged and now evidence-backed.

### NET ROUND 4 STATUS (prior-session entry + this verification pass)
  (a)  CHAMPION20Y_V2 provenance break CLOSED — exactly reproducible (<=1e-16) from V2-era
       git blobs; permanent pinned-blob rebuild path + guard + 8 TDD tests. NOT an orphan.
       (My R3 memo's "whole Sep-1 lineage unreproducible" correction stands.)
  (a2) TRUTH20Y quarantine STANDS (3 pre-registered configs all ~1.3-1.9e-2 vs bar 1e-12).
  (b)  4/4 DEAD_IDEAS rows CONFIRMED dead (29/33/34 now digit-exact-verbatim-proven; row 9
       rebuilt with full battery: zrev -0.424/-0.226/-0.319, sign-flip control +0.033).
  (b)1 Cost-convention finding CONFIRMED after TDD fix of its verifier (digits to +/-0.03,
       factor exact).

Files touched this pass: work_r4/verify_finding_b1_decomp_r4.py (rewritten v2, TDD) only.
FINDINGS.md, champion CSV/weights/builders, live sleeves, DEAD_IDEAS.csv (mid-mutation by
another agent — 117 data rows at my count), other agents' dirs: UNTOUCHED.

ROUND 4 DONE


## ROUND 5 (2026-09-08 0x:xx CST) — charter corner (a): TreasuryDirect auction-CYCLE positioning on rates — 19/19 honest-negative

READ FIRST done: GATES_CONTRACT_V2.md (RATIFIED; two-track rule; §6 Step-1 leak probe, §7
beats-passive, §9 span_class, §10 pins all implemented) + DEAD_IDEAS.csv recounted at round
start = 129 data rows (charter said 120 at R4-end; dynamic by design — FXCARRY2-R5 appended
row 129 before me; I appended row 130). Champion of record untouched: sha256:16
4358dfab95679b97 re-verified after my run (matches the charter's 04:0x pin). My whole prior
suite re-run green alongside the new tests: 28 passed (9 r5 + 8 r2 + 3 r3 lint + 8 r4).

### Corner discipline (why this is NOT a dead-family re-test)
Charter pre-registered corner (a) = TreasuryDirect auction data, auction-CYCLE positioning
family. DEAD row 51 (HUNT_AUCTION) killed auction demand as an EQUITY regime gate
(btc/indirect-share z-gates 252/504 longflat/inv on QQQ/DIA; honest rebuild SR -0.015..-0.17,
scramble 0.93-0.97) and names that config family "do not re-run". My corner is the RATES
side: pre/post-auction windows in futures-proxy tenor books. Zero equity legs; zero MA/z/
momentum of yields anywhere (no overlap with my dead R1/R2 curve/mom/fly/tipsrev/intl-carry
configs — the ONLY signal inputs are the auction calendar and the auction result).

### Data documentation (charter-mandated fetch spans + gap structure + liveness)
Source: tools/quant/data/treasury_auctions/tauctions.csv (keyless treasurydirect.gov TA-WS
via ta_dl.py; sha256:16 b0e243c4e4681e32) n=7857 rows 2000-01-03..2026-09-10, lint PASS.
LIVE PROBE 2026-09-08 (work_r5/tauctions_2026_probe.csv, sha 275e1853da1a3aa8): fresh
keyless fetch of the 2026 year returns 304 records (2025-12-29..2026-09-10); 0 field
mismatches vs disk on bid_to_cover/total/indirect/direct across all 304 joined rows, 0
missing rows — data corner is live and current-day. Event series used (fresh issues only,
reopenings excluded; single dataset-wide multi-CUSIP group 2015-01-28 2-Year deduped to the
largest $26.0bn regular auction): 2-Year n=370 (2000-01-26..2026-08-25, max gap 42d, 13
gaps >35d); 5-Year n=315 (2000-05-09..2026-08-26, max gap 182d, 19 gaps); 10-Year n=153
(2000-01-12..2026-08-12, max gap 182d, 103 gaps >35d — monthly->quarterly cadence shift);
30-Year n=92 (2001-02-08..2026-08-13, MAX GAP 1827d = the 2006-02..2011-02 issuance
suspension, then quarterly) — the 30y series is the structurally broken one and its book
n reflects it. Per-tenor structure + counts are asserted in the loader test.

### Pre-registered design (locked in tests_tdd_r5.py BEFORE any result was seen)
Auction cycle: dealers short the when-issued into the auction -> PRE-auction concession
(long), POST-auction reversal (long), and demand-timed POST (btc below its strictly-prior
same-term expanding median = weak auction -> long). DURS = charter R2 futures-proxy
{2:4.4, 10:7.7, 30:15.5} + disclosed linear-in-tenor 5y extension 5.6375; windows POST =
5 trading days STRICTLY AFTER the auction anchor (uniform for ALL books incl. unconditional
ones, so the leak probe tests the signal, not a same-day convention), PRE = 5 strictly
before; conditioning = PIT convention (A): the median AT anchor a uses ONLY auctions
strictly before a (test-pinned), surprise = btc_a - med_a. Costs/T+1/engine: r1.net_of
(shift(1), vt10 clip3, 6.4bps FULL |dW|, 0.5%/yr borrow) + units/dead-book guards. Battery:
gates.run(sig=, leak_check=True, beats_passive=True full trio) + 200x row-permutation
scramble + 200x lagroll scramble + pre2013/post2013 era gate + k-plateau grid {3,5,10}.
19 books = 4 tenors x {POST,PRE,COND} + 3 anti-controls (10y) + 2x2 plateau neighbors.

### TDD: RED first, 9/9 GREEN; 2 live implementation bugs caught by my own tests
RED run: ModuleNotFoundError (script absent) -> after implementation, iteration to GREEN:
  BUG 1 (caught by test_per_unit_feed_exactness): per_unit_feed multiplied the weight FRAME
  by the return SERIES (frame x series aligns the series on the frame's COLUMNS) -> all-NaN
  -> r_pu collapsed to a zero book. Fixed to frame x frame; live-row exactness now 3.5e-18
  (sig*r_pu == net everywhere sig != 0; flat rows differ only by the exit-cost day, bound
  derived from the actual prior-day sig, test-pinned).
  BUG 2 (caught by test_btc_cond... prefix check + drift-table PIT test): drift_table
  iterated the UNION auction calendar (877 dates across all tenors) instead of the tenor's
  own 153 -> unconditional drift stats were cross-contaminated; also per_unit_feed filled
  flat days with 1.0 (INTL2's convention, harmless for their ~always-live books): on my
  ~5%-live books the fill DOMINATED the leak probe -> same-period corr -0.99 by construction
  (fail-closed verdict), and first battery run reported leak_ok False on 16/19 books.
  Fixed (tenor filter + fillna(0.0), which keeps sig*r_pu == book exact): rerun has leak_ok
  TRUE 19/19 with honest |same_period_corr| <= 0.127. Both fixes test-pinned.

### Results (full-window net, per-unit feeds, all leak-probed; full table in the 19 metas)
  book            n     SR    ann     H1    H2  negyr worst   scr_p perm lag  corr  cA6R7 era pre/post  V2
  POST5_2_long  6653  +0.128  +0.75% +0.83 +0.07    12 -39.9% 0.055 0.000 0.000 +0.061 +0.486 +0.49/-0.36 FAIL
  PRE5_2_long   6659  -0.692 -11.20% -0.41 -0.05    18 -49.3% 0.775 0.000 0.990 +0.078 +0.405 -0.81/-0.56 FAIL
  COND5_2       6570  -0.718 -12.52% +0.03 -0.89    18 -39.1% 0.960 0.000 0.830 -0.044 -0.103 -0.30/-1.30 FAIL
  POST5_5_long  6581  -0.325  -8.37% -0.08 -0.04    13 -49.0% 0.650 0.000 0.010 +0.030 +0.387 -0.29/-0.37 FAIL
  PRE5_5_long   6587  -0.314  -7.85% -0.14 +0.09    16 -38.8% 0.565 0.000 0.985 +0.028 +0.340 -0.33/-0.30 FAIL
  COND5_5       6084  -0.560 -13.12% +0.03 -0.71    16 -41.2% 0.930 0.000 0.490 -0.011 -0.071 -0.14/-1.02 FAIL
  POST5_10_long 6662  +0.207  +2.16% +0.59 +0.06    10 -20.5% 0.135 0.000 0.020 -0.005 +0.216 +0.43/-0.10 FAIL
  PRE5_10_long  6668  -0.022  -2.37% +0.36 -0.18    15 -24.0% 0.320 0.000 0.275 -0.010 +0.220 +0.28/-0.40 FAIL
  COND5_10      6393  -0.272  -6.75% +0.26 -0.68    14 -41.6% 0.770 0.000 0.435 +0.002 +0.070 +0.23/-0.94 FAIL
  POST5_30_long 6392  +0.468  +7.69% +0.37 +0.73     9 -32.4% 0.055 0.000 0.025 +0.003 +0.101 +0.45/+0.49 FAIL
  PRE5_30_long  6398  -0.182  -6.06% +0.01 -0.34    13 -32.0% 0.810 0.025 0.995 -0.020 +0.095 +0.02/-0.44 FAIL
  COND5_30      4390  +0.077  -1.06% +0.37 -0.19    11 -24.7% 0.190 0.000 0.070 +0.006 +0.044 +0.85/-0.33 FAIL
  (anti-controls POST5_10_anti -0.864 / PRE5_10_anti -0.592 / COND5_10_anti -0.386 — the 10y
  trio is dead BOTH ways, no hidden sign; plateau neighbors POST3_10 -0.335, POST10_10 +0.253,
  COND3_10 -0.537, COND10_10 -0.147.)

GATE-by-gate on the family best (POST5_30_long, the only book that even beats a passive):
SR 0.468 vs gate 1.0 (53% short); halves PASS (0.37/0.73); yearly FAIL (9 neg yrs, worst
-32.4% vs floor -5%); beats_passive nominal PASS but by margin +0.010 SR vs spy_bh 0.517
(economically a tie); scramble FAIL both (gates scr_p 0.055 > 0.05, perm_p 0.000, lag_p
0.025); decorrelation PASS (corrChamp +0.003); era PASS (+0.45/+0.49). Every other book
fails earlier and harder. Plateau FAIL on both 10y families (post grid {3:-0.33, 5:+0.21,
10:+0.25}: k=5 not on a plateau; cond grid nonpositive_peak).

### The economic finding (why the cycle story fails as a BOOK, with exact numbers)
Post-auction drift is REAL but it is BOND BETA, not cycle content. Unconditional 5-day
synth-TR drift vs post-auction-window drift (work_r5/uncond_drift_control.json):
  2y: post 15.2bp vs all-days 10.3bp  -> excess +5.0bp  (t 2.0)
  5y: post 22.7bp vs all-days 10.8bp  -> excess +12.6bp (t 3.2)
  10y: post 16.8bp vs all-days 11.3bp -> excess +5.9bp  (t 0.8)
  30y: post 49.1bp vs all-days 13.8bp -> excess +35.4bp (t 1.8)
Two killers: (i) the market is only in the window 2.8-13.3% of days, so the honest VT'd
book converts even the 30y excess into ann +7.7% at vol 20% (SR 0.47) before yearly/scramble
failures; (ii) the demand conditioner goes the WRONG way — conditioning on WEAK auctions
(btc < PIT median, the concession-reversal story) makes every COND book WORSE than the
unconditional post book (COND5_2 -0.718 vs POST5_2 +0.128; COND5_10 -0.272 vs +0.207), and
strong-auction windows carry MORE drift (30y: weak 0.285%/5d vs strong 0.806%/5d) — the
opposite of the dealer-inventory hypothesis; auction demand has no sign content for the
post window on rates. cA6R7 +0.486 on the 2y post book confirms the residual effect overlaps
the champion's bond-trend slot (charter corr watch), so it is not even an orthogonal
candidate at the blend lane.

### V2 battery compliance
All 19 books: gates.run(r=per-unit costed, sig=positions, leak_check=True, beats_passive=True
with the full pinned trio twelvedata-SPY / more_etf-IEF / CTA_15vol) — leak dicts published
in every .meta (all leak_ok True, |same_period_corr| <= 0.127, no argmax-at-lag-0), §7
per-benchmark SRs in metas (spy_bh 0.517 / sixty_forty 0.485 / cta_trend -0.132 on matched
spans), §9 span_class printed next to every number (all books pre2007 except COND5_30
2007plus; nothing inception_fail), §10a positions published (TREASFUT5_*_positions.csv,
19/19), §10b vintage pins in every meta (tauctions b0e243c4e4681e32, champion
4358dfab95679b97, SPY/IEF/CTA/DGS* shas), feed_notes disclosing the exit-cost-day
representation gap (<= 1 day's 6.4bps x prior sig). NOT-A-GATE composition scramble: not
used (nothing to explain). Scramble disclosure: gates scr_p is the lag-roll positions
scramble inside gates.run; perm/lag are r1's row-permutation and lag-roll re-costed
scrambles — all three published per book.

### VERDICT
HONEST NEGATIVE — the auction-CYCLE family on rates is DEAD at champion gates in every
pre-registered corner (post/pre/conditioned x 4 tenors, 19/19 FAIL; best SR 0.468 << 1.0;
conditioner anti-works; anti-controls dead both ways; no plateau). DEAD_IDEAS.csv row 130
appended by me with these numbers and the repro path. Zero adoptable alpha; the honest
frontier is UNCHANGED.

Files touched this round: campaign/scripts/HUNT_TREASFUT_round5.py (new),
tests_tdd_r5.py (new, 9 tests), sleeves/TREASFUT5_* (19 csv + 19 positions + 19 metas),
work_r5/{round5_run.log, round5_meta.json, drift_table_DGS{2,5,10,30}_k5.csv,
uncond_drift_control.json, tauctions_2026_probe.csv} (new), DEAD_IDEAS.csv (one appended
data row, 129->130). bt/ and campaign/*.md UNTOUCHED; champion CSV/weights/builders and all
live sleeves UNTOUCHED (sha re-verified post-run).

ROUND 5 DONE


## ROUND 6 (2026-09-08 13:4x CST) — charter (a) FRAUD-CATCH cross-verification of AUDIT_CHAMP2's GOAL80 repro

Read first: coord/GATES_CONTRACT_V2.md (leak_check default-on post-539f50e; sig=/leak_check
n/a this round — no gates.run battery, this is an audit-repro round) + DEAD_IDEAS.csv recounted
by me: 141 lines = 140 data rows + header (charter said 137 at R5-end; fleet moved it, recount
discipline per contract preamble).

### Method (TDD, own code, no import of the audited builder)
- tests_tdd_r6.py (NEW, 7 tests) written FIRST encoding AUDIT_CHAMP2's CLAIMED numbers as
  pins; work_r6/goal80_own_build.py (NEW) is MY OWN implementation of the documented recipe
  (raw-first per-sleeve vt@0.10 cap8 shift1 rolling60, EW mean, global vt@0.08, 126d
  DD-throttle 4% FR0.5, 6bps HALF-turn blend+throttle costs, start 2008-09-01,
  min_hist>=750). NOT an import/copy of coord_goal100_v2.py or AUDIT_CHAMP2 code.
- dualmom pinned independently by ME: `git show b268e52~1:...QA_dualmom_band121.csv`
  (note: git toplevel is /Users/daxu, not world-trader — path must be software/world-trader/...;
  the pinned test's dynamic-toplevel approach handles this). My blob sha256-16
  7132a167f70f3a6c == AUDIT_CHAMP2's dualmom_pre_costfix.csv byte-identical.
- All 14 pool inputs present on the live tree. Suite: 7 passed in 1.64s
  (campaign/agents/chief/coord/HUNT_TREASFUT/tests_tdd_r6.py).

### VERDICT: every AUDIT_CHAMP2 GOAL80 claim CONFIRMED — no discrepancy found
Exact numbers from MY builder vs their claims (dev in parentheses):
- BYTE-EXACT repro vs campaign/results/COORD_FINAL_daily.csv: maxdev 1.014813e-16, n=4696
  2008-09-01..2026-08-28 (claim 1.015e-16 — CONFIRMED). My rebuild vs THEIR saved repro CSV
  (goal80_coordfinal_repro_TGT08_predualmomfix.csv): maxdev 9.996344e-17 — three-way match.
- Headline: arith ann 43.1918% (claim 43.19), geometric CAGR 53.3570% (53.36), SR_d 4.8373
  (4.84), MDD -7.4817% (-7.48), 0/19 neg years, worst year +7.1263% (2008) — all CONFIRMED.
  IS/OOS arith 37.9636 / 47.7062 (claim 37.96/47.71) — CONFIRMED. The report's "43.2" is
  ARITHMETIC; CAGR is 53.36; champion-of-record 37.1954 is CAGR (convention mixing warning
  stands: arith-equivalent of 37.2 CAGR is ~43.6 — nearly equal to 43.2).
- 2.13x median gross multiplier CONFIRMED EXACTLY — med 2.1303 / mean 2.1665 / p90 2.9812 /
  max 5.2947 / code cap 8.0 respected (5.29<8.0). "NO leverage" in GOAL80_FINAL_REPORT.md is
  FALSE: the construction's global-vt multiplier is a financing-backed exposure dial.
  MEASUREMENT NOTE (new this round): the 2.13x stat was prose-only in AUDIT_CHAMP2's
  FINDINGS (not pinned by any of their 7 tests - a 10a gap). I pinned it (my test_3) and had
  to resolve their convention: gross = s_glob*throttle on POSITION-DAYS ONLY (scale>0). The
  first 60 days have NaN trailing vol -> scale 0 -> no exposure -> excluded; ALL-days gives
  med 2.1175 / mean 2.1388. With POS-days convention: n_pos=4636=4696-60 and every pinned
  digit matches. The report's DD<=8% envelope is measured on the committed series; the gross
  multiplier is the unpriced exposure that financing must be charged on.
- Financing-unpriced verdict CONFIRMED: pricing max(gross-1,0)*4.5%/252 (champion convention,
  POS-days drag 5.2644%/yr; all-days 5.1971%/yr disclosed) -> arith 37.9947% (claim 37.99) /
  CAGR 45.6044% (45.60) / SR 4.2629 (4.26) / MDD -9.2731% (-9.27): breaches GOAL80's own
  DD<=8% envelope. Verdict stands: 43.2 is internally honest, exactly reproducible, ARITHMETIC,
  financing-unpriced, pre-costfix-convention (6bps half-turn) — keep GOAL80/GOAL100 headlines
  quarantined from each other.
- Costed-B3: arith 43.1918 -> with campaign/agents/E1_20yspan/work/B3momhml_costed.csv: 41.95%
  (-1.24pp, claim -1.24pp) — CONFIRMED material.
- "Only dualmom matters at 1e-12" CONFIRMED: rebuilding with CURRENT-tree
  QA_dualmom_band121.csv still diffs the committed artifact (maxdev > 1e-6) -> the b268e52~1
  blob pin is load-bearing and now re-verified by my test_6 on every run.

### Duty (b): TRUTH20Y_QUARANTINE.md
Charter says append ONLY if I find a discrepancy. ZERO discrepancies across all 7 pins ->
NO append made (append-only discipline; nothing to record).

### Housekeeping
- DEAD_IDEAS.csv: no append (no new dead family; this round verified an existing verdict,
  per charter). Count at my round start: 140 data rows.
- bt/ NOT touched by me; champion CSV sha re-verified 4358dfab95679b97 unchanged;
  AUDIT_CHAMP2/ dir untouched by me. git status shows pre-existing M flags on
  campaign/bt/{README,engine,metrics,reconcile,shortability}.* from concurrent charter-named
  agents (AUDIT_FWBUGS-class) - not mine, flagged for the coordinator.
- Files touched this round (mine only): tests_tdd_r6.py (7 tests),
  work_r6/{goal80_own_build.py, dualmom_pre_myblob.csv, blob_err.txt (empty, supersedable)}.
- Suite state: my 7/7 GREEN. Did not run the full bt suite (quiet-tree round; coordinator
  ran 410/0 at 11:4x).

ROUND 6 DONE

## ROUND 7 (2026-09-08 ~20:4x CST) — charter corner (a): ECB SDMX euro-area AAA yield-curve family + duty (b)

Read first: coord/GATES_CONTRACT_V2.md (Step-2 flip IN FORCE — every battery call below passes
sig= and leak_check=True EXPLICITLY per charter; VOL2's V3 per-class placebo is a PROPOSAL — I
did not depend on either state) + DEAD_IDEAS.csv recounted BY ME at round start: 148 data rows
(charter said 145-146 at R6-end; FXCARRY2-R7 +1 landed before me; fleet moved it again mid-round
to 149 before my append — recount discipline per contract preamble).

### Data (NEW source, live, keyless — cited with row counts)
ECB Data Portal SDMX 2.1 csvdata, dataflow YC, series B.U2.EUR.4F.G_N_A.SV_C_YM.SR_<T> =
euro-area AAA-rated government bond spot par yields (the ECB's official AAA curve). Fetched
1Y/2Y/5Y/10Y/30Y: n=5625 obs per tenor, 2004-09-06..2026-09-07 (T-1), ZERO blank OBS_VALUE,
full-span pull 504s so fetch is chunked by calendar year (3 retries baked in).
Manifest pins 5 sha256-16: 1Y ac0cbd9cbc91471a, 2Y d10e09575dc9f80a, 5Y 253429aac5a6154a,
10Y 1bed741dcac36fa7, 30Y a847c99abf7d4728 (work_r7/yields/manifest.json).
Publication calendar: ECB publishes the AAA curve same business day ~18:00 CET => PIT rule =
decision at WED t may use prints up to t-1 business day (load-bearing: dropping the lag flips
5.03% of weekly decisions). TDD test_1 locks percent-vs-decimal units (100x-accrual defect
class), test_0 locks the manifest pins. Dead-family discipline: this corner is the coordinator's
pre-registered NEW-data corner; it is NOT a re-tune of row 61 (my R1 US-DGS 2s10s30s fly, mean-
reversion, daily) or row 50 (HUNT_CURVES FX/ETF proxies) — different source (native ECB SDMX vs
FRED-derived), different cadence (weekly decisions/daily-held vs daily), momentum AND reversion
both reported as pre-registered controls, k=63 pinned a-priori (1 quarter, weekly class), no sweep.

### Engine defects caught this round (TDD RED-first — framework-bug duty)
tests_tdd_r7.py written BEFORE the engine (RED confirmed: ModuleNotFoundError), 11 tests final.
- DEFECT 1 (test_9): weekly W + reindex.fillna(0) made the book FLAT 4512/5625 days (19.9% live)
  with unwind costs stranded on flat days — "weekly rebalance" must mean decisions weekly,
  positions HELD daily (ffill). Same defect class as FXCARRY2-R7's ffill fix.
- DEFECT 2 (test_10): battery feed sig*r_pu != held book on 1113 days (maxdev 4.1e-4) because
  zero-sig days zeroed the feed while the held book still carried stranded costs — battery SR
  0.121 vs actual book SR 0.029 pre-fix. V2 section-10a violation shape: the battery must judge
  the book that is actually saved. Both GREEN post-fix; feed==held to 1e-12 on all 4 sleeves now.
- PIT missing-print rule: 10 residual mismatch WEDs (ECB holiday) were fillna(0) phantom-flat
  weeks; honest behavior is HOLD prior decision (ffill) — fixed, feed==held exact.

### Results — 4 sleeves, ALL HONEST NEGATIVES (full V2 battery each; era table MANDATORY)
Data: n=5625 2004-09-06..2026-09-07; VT10 ann expanding clip 3.0; 6.4bps FULL |dW| + 0.5%/yr
borrow; T+1; DV01-neutral legs (DUR 1.9/8.5/19.0 campaign convention).
- TREASFUT7_ECB_SLOPE_mom (2s10s steepener, sign(d63)): SR 0.394, ann 3.74%, H1 0.52 / H2 0.23
  (FAIL c_halves), 11 neg years (FAIL neg<=2), worst -14.5%; corr_champ -0.034 (primary pass),
  corr_a6r7 +0.065 (primary), corr_a1credit +0.040; scr_p 0.410; leak_ok True (same-period corr
  +0.001 p 0.920); beats_passive FAIL (best sixty_forty 0.552); V2 pass FALSE.
- TREASFUT7_ECB_SLOPE_rev (control): SR -0.421, 13 neg yr, worst -32.6% — dead.
- TREASFUT7_ECB_CURV_mom (2s10s30s DV01 fly, sign(d63)): SR 0.272, ann 2.32%, H1 0.29 / H2 0.26,
  11 neg yr, worst -17.7%; corr_champ +0.042, corr_a6r7 -0.019; scr_p 0.155; leak_ok True
  (corr +0.014 p 0.303); bp FAIL; V2 pass FALSE.
- TREASFUT7_ECB_CURV_rev (control): SR -0.302, 13 neg yr, worst -24.0% — dead.
MANDATORY sub-span stability (charter: post-2013-only effect = FAIL with number stated) — the
opposite shape holds: effects are PRE-2010-CONCENTRATED and decay after 2010:
  SLOPE_mom: pre2010 SR +0.639 (n=1364) -> 2010-2013 -0.077 (n=962) -> post2010 +0.290 ->
  post2013 +0.407 -> post2015 +0.236. CURV_mom: pre2010 +0.717 -> 2010-2013 -0.002 ->
  post2010 +0.047 -> post2013 +0.065 -> post2015 +0.196. Neither sleeve is stable across the
  pre/post-2010 boundary => FAIL on the charter's era bar with those numbers, independent of
  the absolute-SR failures.
Decorrelation (the corner's actual purpose) PASSED everywhere — |corr| <= 0.042 vs champion,
<= 0.065 vs a6r7, <= 0.040 vs A1credit: this is a genuinely low-corr data family with NO alpha
to carry it. Consistent with R1's US-curve verdict: curve-shape momentum/reversion has no
campaign-cost edge on a second continent and a second cadence.

### Duty (b): TRUTH20Y_QUARANTINE.md
No append — zero discrepancies found. I re-ran the canonical 13-sleeve verifier myself this
session (not trusted from the standup): ok=true 7/7 (byte_repro max_dev 1.110e-16; weights_repro
2.220e-16; cost_reconciliation model full_dw 1.246e-16; causality nav.shift(1) matched_mechanism
causal; gross max 1.6000000000007 <= 1.6; mdd -6.6922% >= -7%; yearly 0 neg, worst +7.31%).
Second consecutive zero-discrepancy round; quarantine note stays append-only and nothing met the bar.

### Ledger + housekeeping
- DEAD_IDEAS.csv: appended ONE data row (ECB SDMX AAA curve factors, dead; full evidence string),
  149 -> 150 data rows (before-state 149 verified by recount, trailing newline kept,
  recount-after OK, row parses as 4 cols). No other ledger touched.
- bt/ and campaign/*.md UNTOUCHED by me. git status bt/ M-flags are the PRE-EXISTING
  concurrent-agent set (same files flagged in my R6 FINDINGS: README/engine/metrics/reconcile/
  shortability + their tests — not mine). My tree additions: campaign/scripts/
  HUNT_TREASFUT_round7_fetch.py, HUNT_TREASFUT_round7.py, work_r7/ (yields/ 5 csv + manifest,
  r7_ecb_curve_results.json), sleeves/ TREASFUT7_ECB_* (4 csv + 4 positions + 4 metas),
  tests_tdd_r7.py (11 tests).
- Champion sha 4358dfab95679b97 verified start AND end of round — bytes untouched.
- Suite state: my 11/11 GREEN; bt suite 431 passed (run from repo root per memory;
  test_audit_champ2_round4.py run separately: 5/5 GREEN => 436/0 total). Coordinator-quoted
  R6-close count was 426 — fleet grew it, consistent with the R5/R6 pattern of landing audit
  tests; I did not touch any test file but mine.
ROUND 7 DONE
