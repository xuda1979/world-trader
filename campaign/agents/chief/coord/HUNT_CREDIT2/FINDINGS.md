# HUNT_CREDIT2 — FINDINGS

Round-1 summary lives in coord/FINDINGS.md (all four R1 credit engines dead). Round 2 below.
====================================================================
Repro: campaign/scripts/HUNT_CREDIT2_round2.py + _gate.py + _gate2.py; TDD 4/4 green
(work_r2/test_credit2_r2.py); bt suite 148 passed. Sleeve CSVs + .meta in
HUNT_CREDIT2/sleeves/ (3 files, fail-closed diagnostics inside). DEAD_IDEAS.csv rows appended (80->84).
Charter pre-authorized substitution for (d): FRED BAMLH0A0HYM2 serves 2023-09-05+ only (787 rows,
verified with observation_start=1996-12-31; aliases BAMLH0A0HYM2EY/BAMLHE00EHYIOAS/BAMLH0A1HYBB
all 2023+), champion window is 2008-03-31+ -> used BAA10Y (1986+, same credit-stress spread
minus the AAA leg's rate content). True HY OAS gives 15/4805 gated days on the overlap = unjudgeable.

(a) LQD-TLT credit-spread momentum k=126 (a-priori), +1/-1 dollar, VT10%, 6.4bps+borrow:
    SR=-0.31 (gross +0.01 — signal has NO alpha before costs), ann=-4.2%, H1=-0.24 H2=-0.44,
    13 negyr worst=-32.7%, scram_p=0.000 (kills it from the other side), corrChamp=0.142 (the
    ONLY gate it passes), SR_08+=-0.17. k-scan 63/-0.24 126/-0.31 252/-0.17 -> plateau FAIL
    (nonpositive_peak). Post-hoc sign-flip (banned for adoption, run to kill the idea both
    ways): SR=-0.33. DEAD.
(b) T10YIE 63d breakeven trend, TLT/TIP monthly tilt, extra publish-lag day:
    SR=-0.80 (gross -0.40), ann=-9.7%, H1=-1.10 H2=-0.45, 21 negyr worst=-35.3%, scram_p=0.000,
    corrChamp=-0.050. k-scan 21/-1.21 63/-0.80 126/-0.44 252/-0.25 all negative. Flipped +0.09
    still fails SR>=1.0. DEAD.
(c) 2s10s (T10Y2Y) steepener, IEF/TLT 0.5/0.5 barbell, k=21 (a-priori):
    SR=-0.54 (gross +0.07), ann=-5.1%, H1=-0.59 H2=-0.50, 21 negyr worst=-17.9%, scram_p=0.000,
    corrChamp=-0.128. k-scan 5/-1.38 10/-0.93 21/-0.54 42/-0.45 63/-0.38 all negative. Flipped
    -0.64. DEAD.
(d) HY-stress gate overlay (0.7x champion when BAA10Y 252d trailing z>2) — LOOKED live:
    champion SR 3.296 -> 3.494, delta=+0.198, 323/4805 days gated. Killed by adversarial controls
    (scripts/HUNT_CREDIT2_round2_gate2.py) — the delta is CONTENT-FREE, not credit:
      * N x z_thr plateau (delta objective): +0.198..+0.254 everywhere = parameter-insensitive,
        i.e. generic de-levering, not a stress threshold. Lag T+1..T+10 stable (+0.19..+0.22).
      * Era split: 2008-12 +0.046 / 2013-19 -0.064 / 2020-26 +0.295 -> COVID-concentrated.
      * Gated days carry champion ann returns +66.1% (08-12), +59.5% (13-19), +201.8% (20-26);
        59% of gated days are champion POSITIVE days, mean +39bp/d. A real stress gate should
        fire on losses. Net cumulative return contribution of the gate = -0.38 (it GIVES UP
        3.8pp of return); the SR gain is purely variance-outlier suppression.
      * Concentration: 85% of gated-day variance sits in 22 positive-outlier days; top-6 |contrib|
        days are all Mar-Apr 2020 champion WINS (+18.31% z=7.0, +14.42% z=7.0, +5.91%...).
      * GENERIC CONTROL (kills it): champion's own trailing 252d realized-vol z>2 -> 0.7x (same
        machinery, ZERO credit content) gives delta +0.224 > credit gate's +0.198. Vol-matched
        CONSTANT 0.93x scale gives delta 0.000 (SR is scale-invariant) -> the entire +0.198 is
        non-uniform de-levering of the biggest WIN days. Credit information adds NOTHING
        (credit delta < content-free control). Other credit indicators same machinery:
        DAAA +0.157, DBAA +0.168, BAA10Y +0.198 — spread across the rate complex, again
        consistent with a generic vol effect, not HY-specific stress.
      * ANTI-gate (z<-2 -> 0.7x on the calmest days) delta -0.006: firing on calm days does
        nothing; the effect is entirely WHERE the outlier days sit, not what credit is doing.
      * Scramble 200x (gate values permuted, count preserved): p=0.000 — note this PASSES
        because permuting a 0.7x/1.0 mask across 4805 days still de-levers whatever big days it
        lands on (delta_real +0.198 vs scrambled mean ~+0.18, CI [+0.02,+0.31], P(delta<=0)=1.7%
        by day-iid bootstrap). Statistical nonzero-ness is NOT economic content: the control in
        the previous bullet is the decisive one.
      * Costs: 105 on<->off transitions * 0.3*1.6 gross * 6.4bps = 17.5bps/yr — small; the gate
        is not a cost artifact, it is a vol artifact.
      * Verdict: applying ANY 0.7x/1.0 state mask to a book whose SR comes from compounding a
        few huge up-days mechanically raises SR by trimming the variance of the wins. This is
        the same champion-whitening illusion documented in round 1 (VXV/VIX term overlay,
        max dSR -0.29 dead ledger). NOT adoptable; champion untouched.

Round-2 conclusion: credit & rates-spread domain is now exhausted on available instruments —
ETF spread momentum (a), breakeven trend (b), curve barbells (c) all have gross SR ~ 0
(+0.01/-0.40/+0.07), i.e. no alpha exists pre-cost to even pay for itself, and the one
apparent win (d) decomposes to a content-free vol artifact. Champion
GOAL100_RAWEW13v2_WEIGHTED_GEAR16 (ann 39.85%, SR 3.296, maxDD 6.8%) untouched.
No round-2 sleeve passed any gate combination. Honest negative.
ROUND 2 DONE

====================================================================
ROUND 3 (2026-09-07, coordinator WAIVED the 2007 bound -> the real HY leg testable)
Repro: campaign/scripts/HUNT_CREDIT2_round3.py + _kills.py; fetch
HUNT_CREDIT2_round3_fetch.py (HYG into more_etf + work_r3/HYG_manifest.json, lint PASS
re-verified independently 2026-09-07: HYG 4883d 2007-04-11+, JNK 4718d 2007-12-04+, EMB
4707d 2007-12-19+, dup=0 nonpos=0 maxgap=5d jumps=0). TDD 5/5
(work_r3/test_credit2_r3.py) — TDD caught two real bugs BEFORE the hunt ran:
  * first "dip" formulation (k-day return vs its own trailing distribution) FIRED ON
    UPTRENDS (a ramp's relative return decays monotonically, so the lagging trailing mean
    sits above it) = a trend detector, not mean-reversion;
  * on any monotonic ramp, px-vs-SMA20 z is a CONSTANT +-1.606 (scale-invariant in slope)
    -> z_thr=1.0 a-priori makes buy-the-dip structurally anti-momentum (can never long an
    uptrend), pinned by test_meanrev_signal_is_antimomentum.
DATA DISCLOSURE (affects (ii)): more_etf closes are UNADJUSTED prices (twelvedata raw;
`adjusted=true` returns identical closes; /dividends endpoint 403 paywalled on this key;
TLT 81.52->82.21 over 24y proves dividend absence). So charter "HYG total return" was
reconstructed as price return + FRED yield/365 with the yield lagged T+1
(total_return(), TDD-pinned spike-lag test); true HY OAS (BAMLEMHBHYCRPIOAS) again starts
2023-09-05 (787 rows, same R2 finding) -> the z-timed carry variant is 2023+ only (n=753,
disclosed, unjudgeable, run fail-closed anyway).

(a)+(b)(i) HY-vs-IG spread momentum, +1/-1 dollar, k=63 a-priori, k-scan 21/63/126/252:
    HYG/LQD netSR -0.87 (gross -0.35), ann -7.2%, H1/H2 -0.74/-1.07, 18 negyr worst
    -27.5%, eraSR 2008-12/2013-19/2020-26 = -0.55/-0.70/-1.03, corrChamp +0.018.
    JNK/IEF netSR -0.30 (gross +0.04), H1/H2 +0.08/-0.81, 15 negyr worst -13.8%, eraSR
    +0.15/-0.59/-0.66, corrChamp +0.116. k-scans: HYG/LQD -1.28/-0.87/-0.36/-0.47,
    JNK/IEF -0.43/-0.30/-0.10/-0.70 -> plateau FAIL both (nonpositive_peak). Sign-flips
    k63: -0.18 / -0.38 -> dead both ways (63d HY-IG spread moves mean-revert; momentum
    and its mirror both lose). Charter era-split add-on FAILS for both. DEAD.
(b)(ii) HY carry:
    * static harvest, full 2007-04+ span (TR proxy BAA10Y vs DGS10, BAA understates true
      HY yield ~1-1.5pp/yr = bias AGAINST the sleeve, disclosed): netSR -0.30 (gross
      -0.26), raw 1:1 differential -1.90%/yr PRE-COST, H1/H2 -0.47/-0.08, 10 negyr worst
      -24.6%, eraSR -0.42/-0.20/-0.01, corrChamp -0.123. The 2007+ HY ETF era paid NO
      harvestable carry premium over 7-10y treasuries. DEAD.
    * z-timed variant on true HY OAS (BAMLEMHBHYCRPIOAS, 2023+ only n=753): netSR -0.78
      (gross -0.37, T+1-corrected -0.66), H1/H2 +1.01/-1.98, 2 negyr worst -31.4%.
      Unjudgeable span + fails everything judgeable. DEAD.
(b)(iii) HY weekly buy-the-dip (W-FRI, px < SMA20 - 1.0sd, a-priori):
    HYG netSR -0.13 (gross -0.02), H1/H2 -0.18/-0.08, 8 negyr worst -19.8%, eraSR
    -0.22/+0.23/-0.20, corrChamp -0.134. JNK netSR -0.35 (gross -0.23), 9 negyr worst
    -32.1%, eraSR -0.74/+0.04/-0.22, corrChamp -0.136. zt-scan 0.5/1.0/1.5/2.0 =
    HYG -0.11/-0.13/-0.03/+0.19, JNK -0.30/-0.35/-0.26/+0.06 -> plateau FAIL both.
    T+1-corrected (as-built carried one extra shift for (ii)/(iii); conservatism checked,
    does not change any verdict): HYG -0.32, JNK -0.51. DEAD.
    The ONLY positive cell in the entire R3 grid: HYG zt=2.0 +0.19 net (73/1012 weeks
    on). Charter generic-control kill-test: 200 content-free random weekly masks (same
    on-fraction, same T+1/6.4bps/borrow/VT machinery) give mean SR -0.209, 95th pct
    +0.154 -> real +0.188 above the 95th pctile, p=0.035 = the dip effect is NOT a
    content-free mask artifact (barely). But it still fails SR>=1.0 by 5x, halves,
    yearly (8 negyr) and the era-split -> NOT adoptable; and HYG buy-and-hold over the
    same window is SR -0.08, i.e. the asset itself has been a carry-treadmill.
GATE-HONESTY NOTE (R3, disclosed in every .meta): scram_p=0.000 on these books is a
    RE-COSTING ARTIFACT — permuting daily +/-1 weight rows against real returns creates
    2825bps/yr of churn vs 390bps/yr real (verified: 30 perms, SR mean -3.35 range
    [-3.83,-2.97]), so the scramble gate passes trivially and is UNINFORMATIVE for
    high-turnover dollar books. The decisive negatives here are gross SR ~ 0 (no alpha
    pre-cost to even pay for itself) + era-split failures. Flagged for the coordinator:
    the campaign-standard scramble_perm (weight-row permutation + re-costing) is only
    meaningful for books whose cost drag is small relative to gross alpha spread.
Round-3 conclusion: with the REAL HY instruments unlocked (2007-waiver), the credit &
rates-spread domain remains exhausted: HY-vs-IG spread momentum has no pre-cost alpha
(gross +0.04 best), static HY carry over treasuries PAID NEGATIVE -1.90%/yr pre-cost
2007+, breakeven/timed carry is unjudgeable on true HY-OAS data (2023+) and negative
where judgeable, and weekly buy-the-dip fails every contract gate with its only
positive cell sitting 0.19 vs a 1.0 gate (it does pass the new generic-control
kill-test at p=0.035 — the first credit signal to do so — but a 5x gate miss is a 5x
gate miss). 0/5 sleeves pass any gate combination. 4 DEAD_IDEAS rows appended
(102->106). Champion GOAL100_RAWEW13v2_WEIGHTED_GEAR16 (ann 39.85%, SR 3.296, maxDD
6.8%) untouched. Honest negative.
ROUND 3 DONE
====================================================================
ROUND 4 (2026-09-07 20:2x CST) - AUDIT ROTATION (fraud-catch duty; own family CLOSED)
Scope per charter: 6 DEAD_IDEAS rows from OTHER families, reproduced from their CITED
SCRIPTS (not their FINDINGS prose) + the special duty. Champion of record re-confirmed
in passing: gate2 C5 prints champion ann +37.20% SR +3.181 maxDD 6.7% (matches the
re-issued costfix champion).
All runs via saved repro: work_r4/audit_runner.py (one-shot; per-row commands inline below).

SPECIAL DUTY - HUNT_CREDIT2_round2_gate2.py re-run end-to-end on today vintage (CLEAN RUN,
no errors): generic-control conclusion HOLDS and is stronger:
  * C2: generic own-vol z>2->0.7x mask delta +0.204 (486 days on) vs credit gate +0.184
    (323 days) vs both-gates-min +0.183 -> credit content adds NOTHING, unchanged verdict.
  * C2b: BAA10Y +0.184 / DBAA +0.157 / DAAA +0.146 (BAA & AAA 0 days-on = no z>2 hits).
  * C1: net cum delta-contribution -0.3636 (gate still GIVES UP return); top-6 |contrib|
    days still all Mar-Apr 2020 champion WINS (+17.78% z=7.01, +14.03% z=7.02, +5.69%...).
  * C3 lag T+1..T+10: +0.184/+0.209/+0.193/+0.193/+0.172 stable. C4: 105 transitions =
    17.52bps/yr drag (not a cost artifact). C5: champ 37.20%/10.10%/3.181 vs gated
    34.74%/8.98%/3.365 (ann -2.46pp for +0.18 SR = variance-outlier suppression).
  NOTE vs R2 numbers: deltas re-based +0.198->+0.184 because the champion was re-issued
  at 6.4bps FULL-|dW| (37.195% costfix) after R2 ran on the old 39.85% book; the
  ORDERING (generic >= credit) is what matters and is unchanged. (a)-(d) all remain DEAD.

ROW 110 - FF factor premia (HUNT_FF2, supplements) - REPRODUCED BYTE-IDENTICAL.
  Ran final1.py (audit copy: only output path differs; diff=2 lines, verified) from the
  canonical scratch cwd. sha256 16-prefix: raw 1adcb4b7fbbdc079, poolvt 55a9b3e5661bd871
  = EXACT match to delivered sleeves/*_daily.csv AND to the row's claim.
  Stats re-printed: raw SR 0.9784 ann 6.03% negy 4 / poolvt SR 1.0303 ann 8.94% negy 2,
  corrChamp +0.1367/+0.1449 (dead = corr-band fail at 0.15 + never adopted).
  PROVENANCE NOTE: the script's `sys.path.insert(0,'.')` resolves `lib` from CWD - run it
  from HUNT_FF2/scratch or it ModuleNotFounds (I proved the import comes from FF2's own
  scratch/lib.py: COST=0.0006, BORROW=0.005/252). Fragile but honest.

ROW 111 - industry/decile L/S (HUNT_FUNDAMENTAL, supplements) - REPRODUCED, 6/6 claims exact.
  * fund_screen_all.py: pair s_ta+roic IC +0.1042 IR +0.42 (EXACT); oi_ta -0.0166 vs
    claimed prof -0.0167 (0.0001 rounding); eb |0.0249| matches value with sign convention
    (E/B vs B/P).
  * run_ideas.py: value_comp SR +0.06/11negy, growth_comp -0.23/10, prof_comp -0.22/13,
    comp_vgp -0.16/13, value_q3030 +0.03/10 - ALL EXACT to the row.
  * ic_check3.py (vintage IC, carry-forward): value +0.0249 IR +0.23 (EXACT),
    prof -0.0167 (EXACT), accrual_inv -0.0510 (EXACT, matches FINDINGS line 48).
  * s_ta_backtest.py: "backtest SR +0.39 7negy FAIL" - EXACT (SR +0.39, H1 +0.51/H2 +0.24,
    negy 7, worst -18.2% 2016).

ROW 113 - equal-wt BAB (HUNT_FF2, supplements) - HEADLINES REPRODUCED EXACT; ONE STALE SUB-CLAIM.
  * recon3.py: BAB_v25_L05S05 SR -0.64, H1 -0.33/H2 -0.91 - EXACT (row + recon3_results.csv).
  * recon5.py: C_BABlong SR 0.58 ann 5.1% negy 3 - EXACT as printed by the cited script.
  * BUT two side-numbers in the row only hold on FF2's PRE-BUGFIX pipeline (their FINDINGS
    "BUGS #1": net_of() dropna collapsed books to n=684; fixed via net_of_book fillna):
    - corrChamp 0.081: on the FIXED pipeline I get corr +0.0824 n=4684 (matches! - the
      recon5 script itself prints blends-only corr, so this cell was computed on the fixed
      path and reproduces); my buggy-era reconstruction gives +0.168 n=684.
    - "short-highvol leg -0.74%/yr": NOT REPRODUCIBLE from any construction I could find.
      Fixed pipeline: -20.46%/yr geo (-19.72 arith); buggy-era reconstruction: identical
      -20.46%/yr. Recon3/5 print no such cell; no scratch CSV carries it. DIRECTION and
      CONCLUSION unchanged (short leg loses badly = survivorship inversion, and it is now
      WORSE than claimed), but the printed magnitude looks like a typo/stale number.
      Divergence flagged per charter; file: campaign/results/DEAD_IDEAS.csv line 113
      (evidence field, "-0.74%/yr") originating from HUNT_FF2/FINDINGS.md line 54.
  * recon5 blends also reproduce: A+B 0.87, A+B+C 0.90 SR - all still sub-gate/never-adopted.

ROW 114 - FOMC x natgas/gold (D4_microstruct, supplements) - REPRODUCED, 7/7 cells exact.
  * d4_i1.py Phase A (bp/d): NG dec -32.84 (claim -33), eve +17.60 (+18), gold dec +22.07
    (+22), eve +5.64 (+6); 119 meetings / 226 unique dates.
  * d4_i1b.py: NG postFOMC k=1 SR -0.66, raw t -3.32 (EXACT); k=3 -0.35, k=5 -0.14;
    gold k=1..5 -0.21..-0.35 (EXACT band); NG scramble k=1 real -0.66 vs p95 +0.25 p=1.000.
  * d4_i1c.py: best short k=1 calm=None SR 0.51 H1 0.22 (EXACT), MDD -30.7%; vol-cond
    (z<0 full else half) k=1 SR 0.53 MDD -24.8% (EXACT); AU dec-day long SR -0.48.
  * gold "+20.6bp/book SR 0.18 negy 5": decision-day mean on n=110 gold calendar days =
    +20.6bp EXACT (my t +1.91 vs their t~2.3, t-method unspecified - immaterial).

ROW 102 - commodity spread momentum USCI-DBC/DBE-DBP (HUNT_CMDT2-R3) - REPRODUCED, 16/16 cells exact.
  HUNT_CMDT2_round3.py rerun: DBE-DBP LS 63d SR 0.709 ann 8.2% H1/H2 0.78/0.63 negyr 2
  worst -13.0% corr 0.031 (EXACT); USCI-DBC LS 21d SR -1.062 = anti-signal (EXACT);
  DBE-DBP LO 63d 0.652 (EXACT); USCI-DBC LO 126d 0.306 H1 -0.11 (EXACT); all 16 FAIL as
  recorded. TDD suite tests_tdd_r3.py 7/7 green. Sleeves CMDT3_* + metas on disk.

ROW 59 - 2s10s steepener (HUNT_TREASFUT) - REPRODUCED, all cells exact.
  HUNT_TREASFUT_round1.py rerun: a-priori k=21 SR -0.11 H1/H2 0.92/-1.45 31 negyr (EXACT);
  scan k=5/-2.48 10/-1.09 21/-0.11 42/+0.40 63/+0.62 126/+1.12, plateau FAIL (EXACT);
  k=126 scan-best SR 1.12 ann 1.8% H1/H2 1.96/0.11 20 negyr SR_08+ -0.22 cA6R7 0.216
  (EXACT); naiveDW -0.82 sym -2.50 (EXACT). Verdict unchanged.

AUDIT VERDICT: 5 rows fully reproduced (110/111/114/102/59), 1 reproduced-with-one-stale-
side-number (113: -0.74%/yr short-leg figure not reproducible; headlines exact; conclusion
unchanged). 0 fraud, 0 unreproducible scripts, 1 cosmetic divergence. All dead rows remain
dead on today's data vintage; champion untouched (ann 37.20% / SR 3.181 / MDD 6.7%
re-verified live in gate2 C5 this round).
ROUND 4 DONE

====================================================================
ROUND 5 (2026-09-08) - pre-registered corner: credit-carry from FRED spread
families NOT already dead (charter R5 (a); GATES_CONTRACT_V2 RATIFIED in force)
READ FIRST done: coord/GATES_CONTRACT_V2.md (V1 gates 1-5 unchanged; §0 two tracks;
§6 Step-1 leak_probe; §7 beats-passive mandatory for new standalone sleeves) +
DEAD_IDEAS.csv recounted at round start: 125 data rows (charter quoted "120 at
R4-end, dynamic"; by round end 128 - other agents appended concurrently, my 1 row
included in that count). Champion of record sha256 4358dfab95679b97 re-verified
byte-identical this round via shasum; campaign/bt/ untouched by me (quiet-tree
rule; the M files visible in git status there are other agents' pre-existing
in-flight work).

CORNER SELECTION (data-backed, pre-registered before any backtest):
  DEAD_IDEAS greps: NFCICREDIT 0 hits; RIFSPPFAAD01NB 0 hits; MORTGAGE30US 0 hits;
  TB3MS 0 hits; NFCIRISK 1 hit = row 127 "NFCIRISK/STLFSI4/JOLTS/RRP/TED macro
  gates on equity" (HUNT_MACRO2 EQUITY-TIMING gate book - different asset class AND
  construction, not a credit-carry sleeve). TEDRATE excluded a-priori: on-disk
  series DISCONTINUED at 2022-01-21 (verified live against FRED this round, latest
  obs 2022-01-21) = not current-day tradable. OFF-LIMITS respected: D1_creditcurve
  D-family graves untouched; DAAA/DBAA/BAA10Y NOT re-used as signals (they are the
  R2 content-free-gate CONTROL series - re-using them = the banned dead-signal
  re-tune); BAMLC0A0CM true IG yield re-confirmed 2023-09-05+ only (n=786) =
  unjudgeable, excluded.
  NEW staged data (FRED api_key fetch 2026-09-08, fred_dl.lint, manifest
  work_r5/fetch_manifest.json; staged under HUNT_CREDIT2/work_r5/, more_fred
  untouched except nothing): NFCICREDIT n=2904 1971-01-08..2026-08-28 gaps=0;
  NFCIRISK n=2904 same span; MORTGAGE30US n=2893 1971-04-02..2026-09-03 (weekly
  Thursday, holiday gaps, pub-safe ffill disclosed); RIFSPPFAAD01NB n=6635
  2000-01-03..2026-09-03 (on-disk vintage was stale n=3361 2013+, superseded).
  Legs pre-existing: DGS10 n=16154 1962+, DGS3MO n=6276 2001-07-31+, LQD/IEF
  6065d 2002-07-30+.

THREE CONSTRUCTIONS x pre-registered grids (full V2 battery on EVERY config;
r=PER-UNIT spread (r_lqd - r_ief), sig=held weight s so gates.run's internal
sig*r IS the held book - the CMDT2-R5 convention defect explicitly avoided and
TDD-pinned; leak_check=True, beats_passive trio, ref=champion, scramble_n=200;
costs 6.4bps FULL-|dW| + 0.5%/yr borrow, shortability pregate all-EASY, VT 10%
cap 3.0, T+1 shift(1) everywhere):
  (i)  MORTGAGE-SPREAD RV (NEW id MORTGAGE30US): z(30y fixed - 10y CMT), w63/252
       x side{rv, mom} x vt{on,off}. rv: gap rich -> credit over treasury.
  (ii) NFCI REGIME CARRY (NEW ids NFCICREDIT/NFCIRISK): sign of 52w change,
       k13/26/52 smoothing x invert{F,T} x vt{on,off} -> LQD-vs-IEF tilt.
  (iii) CP-OIS FUNDING STRESS (NEW ids RIFSPPFAAD01NB + DGS3MO): z of overnight
       AA financial CP minus daily 3m CMT, w21/63/252 x side{stress,compress} x
       vt{on,off}. TEDRATE's living financial-CP cousin.
  44 configs total.

VERDICT: 0/44 PASS. Every gate fails everywhere.
  * BEST PRE-COST CELL in the entire grid: nfci_credit_k26_inverted_vt v2SR
    +0.206 (gross per-unit held book) vs the 1.0 gate = a 5x miss; its scramble
    p = 0.185 > 0.05 (FAILS the position-scramble gate outright - the signal is
    statistically indistinguishable from block-scrambled noise). Its exact
    sign-mirror (non-inverted) scores -0.206: the family is symmetric noise
    around zero, no directional content.
  * beats_passive: 0/44 (candidate never beats the best of spy_bh 0.514-0.551 /
    sixty_forty / cta on matched spans) - §7 rejects every config by itself.
  * leak_ok 44/44 TRUE (same-period |corr| <= 0.0118, all p >= 0.36): the
    constructions are T+1-clean; the failures are real, not timing artifacts.
  * Net-of-cost SR range -1.88..+0.11 (FULL-|dW| 6.4bps at weekly z-churn
    dominates: e.g. cpois w21 flip-heavy books net -1.88 vs gross -0.18).
    negyrs 13-25 of 24, worst years -10.9..-41.5%.
  * Era-split of the best cell: +0.21 (2008-12) / -0.25 (2013-19) / +0.06
    (2020-26) = regime flip, NOT a persistent effect (R4 TimesFM span-gate bar
    >=8y of effect not met by any cell).
  * Construction economics: mortgage-gap MEAN-REVERSION is an ANTI-signal
    (rv -1.49 vs momentum -1.16 net; the gap trend-persists rather than reverting
    at these horizons). CP-OIS stress and compress arms both negative in net and
    mirror-symmetric in gross - the spread has no LQD/IEF timing content.
  * corr_to_champion: 26/44 within the 0.15 gate (decorrelation was achievable);
    the sleeves fail on alpha, not on correlation.

TDD (work_r5/test_credit2_r5.py, written BEFORE the hunt): RED 3 -> GREEN 10/10.
  The RED phase caught THREE real defects before any verdict was recorded:
    1. weekly-vs-daily intersection alignment: naive MORTGAGE30US-DGS10 gave a
       Thursdays-only book (n=1252); fixed by reindexing the weekly series to the
       daily calendar with pub-safe ffill BEFORE differencing (run-1 mortgap
       numbers were computed on the wrong book and are SUPERSEDED; re-run verdict
       unchanged in direction, all mortgap cells fail either way).
    2. TB3MS is MONTHLY (n=1112 over 92y) - the first-draft CP-OIS treasury leg
       produced an n=102 intersection book and would have been unjudgeable; the
       leg is DGS3MO (daily 2001+), spread now n=6620 2000-01-03..2026-09-03.
    3. save_sleeve KeyError crash on short books - now fail-closed
       (INSUFFICIENT_HISTORY meta, status FAILED_NO_PROMOTION).
  TDD also pinned: sig*r == held gross book exactly (contract wiring, max dev 0.0);
  T+1 spike lands at t+1 never t; pub_safe ffill staleness cap; NFCI weekly state
  cannot flip before the Friday stamp; FULL-|dW| cost = 25.6bps on a full
  dollar-neutral flip (observed in fixture, matches engine contract).

ARTIFACTS: sleeves/CRED5_*.csv + .meta x44 (every meta carries the §6 leak dict +
§7 beats-passive line + §9 span disclosure); repro
campaign/scripts/HUNT_CREDIT2_round5.py; run log work_r5/run_log.txt; fetch
manifest work_r5/fetch_manifest.json; TDD work_r5/test_credit2_r5.py. §10a
positions published via We (reproducible from the script); §10b champion vintage
pinned (sha 4358dfab95679b97). DEAD_IDEAS.csv 1 row appended (R5 family-level
honest negative; recount 128 at round end).

Round-5 conclusion: the pre-registered NEW-series corner (mortgage-spread RV,
NFCI regime carry, CP-OIS funding stress) is CLOSED honest-negative: zero
pre-cost alpha (best gross SR 0.206 = 5x gate miss, scramble-FAILS at p=0.185,
sign-mirror symmetric), 0/44 beats-passive, era-flip not effect. The credit &
rates-spread domain remains exhausted on every expressible instrument set tested
to date. Frontier UNCHANGED: champion GOAL100_RAWEW13v2_WEIGHTED_GEAR16 ann
37.195% / SR 3.1810 / MDD -6.69% untouched (sha 4358dfab95679b97 re-verified).
ROUND 5 DONE

# FINDINGS - HUNT_CREDIT2 ROUND 6 (2026-09-08, coordinator standup 11:5x) - AUDIT ROTATION: cross-verify HUNT_CRYPTO2 R5 verdicts from published artifacts with own code; credit-rows DEAD_IDEAS curation; no new credit corner (family CLOSED - zero new engines run)
READ FIRST done: coord/GATES_CONTRACT_V2.md (in force; Step-2 flip noted - my honest-wiring
re-runs pass sig= and leak_check=True explicitly) + DEAD_IDEAS.csv recounted by me at round
start: 140 data rows (charter quoted 137 at R5-end; 3 concurrent appends landed mid-session,
dynamic by design; file well-formed, 0 malformed rows, sha16 at my round start 2433179f282f6681).
Champion of record INDEPENDENTLY RE-VERIFIED fresh this session (not trusted from standup):
bash campaign/bt/verify_champion_r3_cmd.sh -> ok=true 7/7 (weights_repro 2.22e-16,
byte_repro 1.11e-16, cost_reconciliation full_dw ratio 1.0000000, causality nav.shift(1)
causal_max_dev 1.11e-16, gross 1.6000000000007 <= 1.6, yearly 0 neg worst +7.31%, mdd
-6.6922%); sha 4358dfab95679b97 recomputed = charter. JSON pinned work_r6/verify_champ_r6.json.
bt/ untouched by me (quiet tree); HUNT_CRYPTO2 files untouched (their FINDINGS/work/sleeves
read-only; sha16s pinned in-session: bitmex_xbtusd e3ebbbdf08fbec7d, bitmex_ethusd
b65befbaab99ad98 - both match their R5 manifest).

## (a) HUNT_CRYPTO2 R5 - VERDICTS CONFIRMED (all engines fail exactly as published), 4 findings escalated (1 wiring defect class, 1 stale-generator, 1 prose-artifact mismatch, 1 missing generator script)
Own-code reimplementation work_r6/verify_crypto2_r5_own_code.py (NO import of their
carry_engine3/4 or hedged_battery for the headline numbers; own SR/halves/negyr/leak-corr/
scramble/blend arithmetic in numpy+pandas; bt.gates.run used only for the honest-wiring
re-judgment) + 5 probes work_r6/probe_*.py outputs below.

(a0) DATA VERIFIED: OKX BTC 290 rows 2026-06-03..2026-09-07 and Coinbase INTX BTC 100 rows
2026-09-03..2026-09-07 confirm the 3-month/4-day inception_fail roster audit; BitMEX depth
files n=11264 (2016-05-14..) / n=8876 (2018-08-02..) with manifest shas MATCHING on-disk.

(a1) EXPRESSIBLE CARRY 12/12 FAIL - CONFIRMED, direction exact, magnitude exact for the
construction that matches (v3, no funding leg): my from-scratch v3-convention recompute hits
all 12 net SRs to 3dp (BTC harvest W/M +0.343/-0.283, long 0.729/0.729, z +0.086/-0.228;
ETH harvest -0.111/-0.471, long +0.080/-0.033, z -0.036/-0.166 vs their identical table).
HONEST-WIRING RE-JUDGMENT (my probe: r=per-unit raw, sig=held positions, leak_check=True,
beats_passive=True trio, scramble_n=200 -> crypto2_carry_honest_wiring_gates.json): best
cell CARRY_BTC_LONG SR 0.730 halves 0.90/0.52 neg 3, all 12 pass=False, beats_passive 0/12
(best passive spy_bh 0.73-0.94 on matched spans) - their verdict (sr_min miss >4x at best
per their convention, neg 3-6 > 2, bp False everywhere) is CONFIRMED and slightly
STRENGTHENED (no cell anywhere near 1.0; ETH-harvest flips sign negative under honest wiring).

(a1-DEFECT) ENGINE WIRING: v3/v4 judged sig^2*book, not the book. Their engines pass
r=book_gross (=sig*r_raw) AND sig=sig to gates.run, which judges sig*r = sig^2*r_raw:
sign-stripped, vt-magnitude-squared. PROOF: gates.sr 0.510573 == SR(sig^2*r) to 6dp on
LONG; halves/neg identical; and all five n=2355 BTC cells share ONE bit-identical gates.corr
0.001184847674605198 (v4) because corr(sig^2*X, champ) is invariant to the +-sign pattern
of sig (sig^2 >= 0) - five different books cannot share 16 digits of correlation. Their own
published gate columns (gates.sr 0.511 vs their quoted net 0.343/gross 0.356 for the same
cell) were internally inconsistent in exactly this way. VERDICT-SAFETY: the honest wiring
(a1) fails every cell by wider margins, so 0/12 stands under BOTH wirings (their defective
one actually FLATTERED the z books: judged gross 0.511-0.652 vs honest 0.111/-0.015).
Escalated to coordinator as a bug for CRYPTO2 to fix in THEIR files (pass r=per-unit,
not r=book); I edited nothing.

(a2) HEDGED CASH-AND-CARRY HEDGE_BTC_W - CONFIRMED REAL, CONFIRMED NOT-EXPRESSIBLE, 2
escalations. Sleeve CSV of record REPRODUCES from raw BitMEX data with my own construction
to machine epsilon (aligned n=532, max|diff| 1.0e-16): net SR sqrt52 1.628-1.635 (their
1.628 honest / 3.759 sqrt252-inflated gate - their own meta discloses the 2.2x annualization
inflation), mean*52 11.61-11.70%/yr, 1 neg yr (2022 -0.81/-0.82%), flips 50, corr_champ
+0.078/+0.079, leak False all pairings (max |c0| 0.179 < 0.20 bar). ETH 0 flips CONFIRMED
(zero sign changes in 8y, funding +15.7%..+99.0%/yr every year = the published degenerate
constant-short property). Coordinator blend arithmetic direction REPRODUCED with own code
(fill-0 additive convention, w grid): dSR +0.027/+0.051/+0.073/+0.110 at w=.05/.10/.15/.25,
dAnn +0.43/+0.86/+1.29/+2.15pp, dMDD +0.03/+0.06/+0.09/+0.15pp, 0 neg yrs all rungs
(their +0.199/+4.21pp/+0.05pp at w=.25 under a different embedding convention - same
sign pattern, same conclusion). MY OWN 200-draw circular-shift placebo at w=.25 on the
weekly book: 195/200 draws reproduce the dSR delta -> INDEPENDENTLY CONFIRMS the
coordinator's 169/200 mean-injection-dominated diagnosis; the delta is arithmetic, not
skill. (a2-DEFECTS) (i) STALE GENERATOR: on-disk hedged_battery.py v1 output
(hedged_results.json) has the leg sign FLIPPED (gates.sr -2.895, bp FALSE cand -2.89 vs
0.34) - the FINDINGS' 3.759/TRUE numbers come from hedged_results_v3.json whose generator
script IS NOT ON DISK (v3 file has a different schema from anything the saved scripts
emit). (ii) PROSE-ARTIFACT MISMATCH: FINDINGS quotes leak c0 -0.104 for HEDGE_BTC_W; I
reproduce -0.104377 exactly as corr(perp_pos, net_book) = the V1 pairing (p 0.0157), while
the v3 JSON publishes +0.17713 (= corr(spot_sign, wk_funding) my +0.17910, off 0.002) -
the prose stitches v1's leak with v3's gates. Both numbers are under the 0.20 leak bar
(leak=False stands either way) and the not-expressible verdict is untouched, but the
published audit trail mixes vintages. Escalated (i)+(ii) together.

(a3) FUNDING-STATE OVERLAYS 6/6 dAnn<0 - CONFIRMED. Own from-scratch overlay engine
(z26w>2->x0.6 / z<-2->x1.0-else-x0.85 / 4w-mean>0->1.0-else-0.85, W-FRI decision, T+1):
BTC A dSR -0.012 dAnn -0.20pp; B dSR -0.088 dAnn -2.57pp; C dSR +0.103 dAnn -1.26pp
dMDD +0.71pp; ETH A -0.27pp, B +0.062 dSR but -2.29pp dAnn, C +0.000/-0.00pp (no signal).
Gate 8c (dAnn>0 HARD) fails 6/6 exactly as published (their C was the only dSR-positive
too - same survivor, still dAnn-negative). (a3-DEFECT) NO SAVED SCRIPT: the overlay engine
exists only as prose in their FINDINGS.md (no script, no JSON, no sleeves on disk carry
these names) - a V2 section-10a artifact-verifiability gap, escalated (I rebuilt it from
the prose spec myself, which is why the verdict survives).

## (b) DEAD_IDEAS credit-rows curation - COMPLETE: 7 rows audited, all evidence chains verified or strengthened, 1 row appended
Rows audited (my family): 104/105/106/107 (R3), 121 (R5), 126 (DATA_FREDMORE data-acquired,
credit-QUALITY class), 137 (COT2's R6 evidence-cell correction TO my row 121).
- Row 104: saved sleeves re-measured - HYG/LQD k63 SR -0.874 H1/H2 -0.74/-1.07 neg 18
  worst -27.5%; JNK/IEF -0.300 +0.08/-0.81 neg 15 worst -13.8%: EXACT to the row.
- Row 105: raw static differential RE-DERIVED from raw inputs (HYG/IEF px + BAA10Y/DGS10
  TR reconstruction, T+1-lagged yield): -1.90%/yr EXACT; 10 neg years EXACT. One imprecision
  FOUND: the row title says "1:1 static" with netSR -0.30, but the committed script's carry
  book is z-timed w=-z(spread) k252 (my verbatim re-run of HUNT_CREDIT2_round3.py main
  block: n=753 2023-09-06..2026-09-04 SR -0.779 H1 +1.01 H2 -1.98 neg 2 - which is row
  106's number and artifact). -0.30 was the BAA10Y/DGS10-proxy z-timed variant, not a
  static book (my own static accounting: netSR -0.178 worst -34.7%). Verdict direction
  unchanged (both deeply dead, neg-yrs/halves fail everywhere); noted in my new row.
- Row 106: EXACT - verbatim engine re-run reproduces n=753 SR -0.779 H1/H2 +1.01/-1.98
  neg 2 worst -31.4% (2023-09 inception_fail disclosure stands).
- Row 107: EXACT - saved sleeves HYG z1 -0.134 (-0.18/-0.08, 8 neg, -19.8%), JNK z1
  -0.350 (-0.58/-0.08, 9 neg, -32.1%) match the row to 3dp on every field.
- Row 121: STALE NUMBERS CONFIRMED STALE (COT2 row 137 already corrected this): my re-read
  of the 44 saved CRED5 sleeves gives best net +0.112 (nfci_credit_k26_i_vt, matching the
  meta v2sr gross 0.2063 disclosed) and worst -1.878 - the row's "best SR 0.62/3 negyr"
  cells are the superseded run-1 drafts. Verdict 0/44 stands, strengthened.
- Row 126: data files verified at tools/quant/data/more_fred/ (NOT campaign/more_fred -
  path nit): DRALACBS n=166 1985-01-01..2026-04-01 and DRCLACBS n=158 1987-01-01..2026-04-01
  EXACT to the row; status data-acquired is correct (never hunted).
- Row 137 (my ledger's corrective row): verified CORRECT against my own artifacts
  (mortgage best net -0.739 mortgap_w252_mom_vt; nfci +0.112; cpois best -0.826; negyrs
  13-25; best v2 gross 0.2063 = 5x gate miss) - the R5 verdict 0/44 as strengthened.
- R5 staged data integrity re-checked: work_r5 staged RIFSPPFAAD01NB n=6635 2000-01-03..2026-09-03
  (the on-disk tools copy is the stale n=3361 2013+ vintage my R5 FINDINGS already
  disclosed superseding), MORTGAGE30US n=2893, NFCICREDIT/NFCIRISK n=2904 - all match.
Appended 1 curation row (HUNT_CREDIT2-R6): rows 104/105/106/107/121/126/137 audit +
row-105 static-vs-z-timed labeling correction + row-126 path nit; before-sha16
2433179f282f6681 -> after-sha16 7be122a38f074f40, ledger 140->141 data rows on my
append (other agents' concurrent appends took it to 142 before mine; 143 total rows
including mine at round close), idempotency-checked, 4-column parse verified after append
(0 malformed).

## (c) No new credit corner: NONE RUN (family CLOSED per R4/R5; zero engine families opened this round; no bt/ or other-agent file edits; champion untouched sha 4358dfab95679b97)

## VERDICT: ROUND 6 = CRYPTO2 R5 verdicts 3/3 CONFIRMED (12/12 carry FAIL incl. honest-wiring strengthening; HEDGE_BTC_W real-but-not-expressible + mean-injection placebo independently confirmed 195/200; 6/6 overlays dAnn<0), 4 escalations (sig^2 wiring defect verdict-safe; stale v1 generator + missing v3 generator + v1/v3 leak-c0 prose stitch; overlay engine not artifact-verifiable), credit-row curation complete 7/7, 1 ledger row appended, 0 new engines
Frontier UNCHANGED: champion GOAL100_RAWEW13v2_WEIGHTED_GEAR16 ann 37.1954% / SR 3.1810 /
MDD -6.6922% / 0 neg yrs (7/7 fresh this session). Artifacts:
work_r6/{verify_champ_r6.json, verify_champ_r6.log, verify_crypto2_r5_own_code.py,
crypto2_own_recompute.json, crypto2_carry_honest_wiring_gates.json}.
ROUND 6 DONE

====================================================================
# ROUND 7 (2026-09-08 19:5x-20:1x CST) - AUDIT (own code): DATA_ETF_MORE-R6
more_etf manifest.csv restore - INDEPENDENTLY RE-RUN READ-ONLY, 12/12 checks PASS, claim
confirmed + one strengthening nuance; 0 divergences, 0 fraud. No new credit corner (family
CLOSED R4/R5); R6 escalations stay logged untouched.
READ FIRST done: coord/GATES_CONTRACT_V2.md (in force; VOL2 V3 per-class placebo noted as
PROPOSAL - not depended on either way; my audit work touches no gate code) +
campaign/results/DEAD_IDEAS.csv recounted by me at round start: 147 data rows / 148 incl
header (charter quoted 145-146 at R6-end; dynamic by design; 0 malformed rows, 4-col parse
verified; sha16 at my round start bd09cc6df3089397). Champion of record independently
re-verified fresh this session (not trusted from standup): shasum -a 256 ->
GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 4358dfab95679b97 = charter byte-exact.
bt/ and other-agent files untouched by me.

## (a) DATA_ETF_MORE-R6 manifest restore audit - CONFIRMED (all 4 charter claims)
Claim under test (their FINDINGS "DATA_ORGANIZE sweep clobber + restore"): the 09-08 13:44
DATA_ORGANIZE canonicalization clobbered more_etf/manifest.csv (82x10 w/ span_class ->
foreign 82x7 family,file,date_col,kind,rows,cols,exception); restored 16:29 via their own
deterministic R3 builder; restored sha16 9b04a324ebb4db04; byte-identity claimed via
builder determinism + row-exact spot-facts because no pre-clobber sha was ever pinned.
Repro (my code, saved): work_r7/audit_r7_manifest_restore.py -> work_r7/audit_r7_results.json.
Method: their work_r3/manifest_r3.py build() invoked UNMODIFIED with DataFrame.to_csv
monkeypatched to a recorder (READ-ONLY - the builder's line-46 write suppressed; verified
afterward: sha AND mtime byte-stable, 0 actual disk writes); then every field of the on-disk
manifest re-derived by an INDEPENDENT linter of mine (no import of their lint_series/
classify; own zero-run loop instead of their cumsum trick) and compared field-by-field.
  * C1 restored sha16 == 9b04a324ebb4db04: PASS (on-disk full sha256
    9b04a324ebb4db043165daf393f91b223fb868fcbad2c2156284bbc8268a620a; mtime 16:29 =
    their stated restore time).
  * C2 schema: PASS - 82 rows x 10 cols, columns exactly
    {symbol,start,end,rows,max_gap_days,zero_ret_rows,jump_days,dup_dates,span_class,status};
    span_class populated on all 82 rows, domain {pre2007,2007plus,inception_fail}.
  * C3 loud FAILs: PASS - EXACTLY 2, both FAIL(inception): XLC start 2018-06-19 n=2063,
    XLRE start 2015-10-08 n=2741 (rest of file: PASS 50 pre2007 / PASS_WAIVER 30 2007plus).
  * C4 byte-identity-via-determinism: PASS and STRENGTHENED - my read-only re-invocation of
    their builder (a SECOND independent build draw, in a different process ~3.5h after their
    restore) re-renders the file byte-for-byte (sha16 of my in-memory render =
    9b04a324ebb4db04 == disk). Their claim as stated ("byte-identity rests on builder
    determinism, no pre-clobber sha exists anywhere") is exactly right, and my run upgrades
    it from a one-draw assertion to a cross-session two-draw reproduction.
  * DISK-TRUTH (fraud-catch, beyond the charter ask): my independent re-lint of all 82
    on-disk CSVs matches the manifest on EVERY field (start/end/rows/maxgap/zrun/jumps/dups/
    span_class/status), 0 mismatches, 0 unreadable csvs, 0 non-positive closes. Shell-level
    spot-check (pandas-free): HYG 4883 data rows 2007-04-11..2026-09-04, ENOR 3676
    2012-01-24.., XLC 2063 2018-06-19..2026-09-02, XLRE 2741 2015-10-08.., AGG 5771
    2003-09-29.., XME 5082 2006-06-22.. - all row-exact vs manifest. Their R4 spot-facts
    (HYG 4883 / ENOR 3676 / EIS 4640 / TUR 4641 / EPHE 4008 / COPX 4121, all PASS_WAIVER)
    re-verified EXACT from the restored manifest.
  * C4b no-pre-clobber-pin claim: PASS - manifest is gitignored (repo .gitignore line 5
    tools/quant/data/), `git ls-files --error-unmatch` rc=1 (untracked), `git log --all --
    tools/quant/data/more_etf/manifest.csv` EMPTY (never committed at any ref), and a
    repo-wide grep for the two candidate sha16s finds 9b04a324 only in 3 post-restore files
    (their FINDINGS 16:30, my CHARTER 18:52, STANDUP_LOG 19:58) and the foreign-schema
    13a9c9cf only in their FINDINGS prose. No pre-clobber bytes or hash pinned ANYWHERE ->
    recoverability genuinely rests on determinism, as claimed.
  * Comparator teeth (honesty check on my own audit): tampering the manifest (HYG rows +7;
    XME span_class -> inception_fail) is caught by my comparator as exactly 2 mismatches -
    the 0-mismatch clean result is not a blind pass.
  * Corroboration: 59 manifest-like files under tools/quant/data/ inventoried by sha16;
    14 still carry the foreign 47-byte 1-row schema 13a9c9cfd9952995 (their disclosed
    non-deliverables, incl twelvedata/manifest.csv head-verified foreign this session) -
    consistent with their account that only THEIR OWN deliverables were restored and the
    DATA_ORGANIZE post-mortem escalation (atomic writes + do-not-touch-pinned-artifacts)
    remains OPEN for the affected owners.
AUDIT VERDICT (a): DATA_ETF_MORE-R6 restore claim 4/4 CONFIRMED (sha16, 82x10 span_class
schema, the 2 loud inception FAILs at the exact dates, no-pre-clobber-pin provenance), plus
one strengthening finding (two-draw builder determinism) and one independent disk-truth pass
(82/82 field-exact). Zero divergences. Their files untouched (read-only; builder write
suppressed in-process, on-disk sha+mtime proven unchanged).

## (b) No new credit corner: NONE RUN (family CLOSED per R4/R5; R5 staged-data integrity not
re-staged per charter; zero engine families opened; no bt/ or other-agent file edits).
## R6 escalations (sig^2 wiring verdict-safe; stale v1 + missing v3 generators; leak-c0 prose
stitch; overlay engine not artifact-verifiable): remain LOGGED in my ROUND 6 FINDINGS section;
no edits to CRYPTO2 files this round.

VERDICT: ROUND 7 = charter (a) audit 12/12 checks PASS, restore claim 4/4 CONFIRMED,
0 divergences, 0 new engines, frontier UNCHANGED (champion GOAL100_RAWEW13v2_WEIGHTED_GEAR16
ann 37.1954% / SR 3.1810 / MDD -6.6922% / 0 neg yrs, sha 4358dfab95679b97 re-verified fresh
this session). Artifacts: work_r7/audit_r7_manifest_restore.py + audit_r7_results.json.
ROUND 7 DONE
