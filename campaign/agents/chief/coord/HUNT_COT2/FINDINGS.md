# FINDINGS.md — HUNT_COT2 round 1 (COT aggregation & cross-market)
Date: 2026-09-07. Charter: test NEW COT aggregates (a) cross-market rank, (b) hedger fade, (c) OI-change overlay, (d) spec L/S asymmetry — clean forward timing, 6.4bps full-|dW|, ALL gates. Verdict: **ALL 24 CONFIGS FAIL — honest negative.**

## Framework state on arrival + TDD work (21 tests, all green)
Found the round-1 library half-implemented (13 tests passing under pytest, 7 RED on unimplemented charter functions, and the `__main__` runner sat mid-file so a bare `python3 test_lib_hunt.py` silently ran only 9 tests). Fixed harness, implemented functions TDD-style, and found+fixed **4 real library bugs** (each RED->GREEN):
1. **`load_hedger` returned ALL 9 families mixed** (gold n=6181 rows, dup index 5469) — no family filter — and matched markets by fuzzy keyword (`'GOLD' in name` catches MICRO GOLD, ICE gold). Fixed to use the repo's audited exact matcher `tools/quant/data/more_cot/cot_matcher.py` + priority rule for same-date collisions (physical NATGAS over HENRY HUB). Validation: re-parsed `mm_pct` now reproduces the committed legacy `net_noncomm_pct_oi` with **corr=1.0000 and max|diff|<6e-7 (legacy 6-dp rounding bound) for all 9 charter markets incl. wti/nat_gas** (was corr 0.165 gold / 0.397 natgas / 0.591 wti with mixed rows). Regression test `test_load_hedger_single_market_exact_match`.
2. **Scramble null was degenerate**: circular roll of the *return* series preserves mean/std exactly -> null SR == real SR -> p=1.0 for every strategy (gate permanently stuck) while the old test's "iid noise must pass p<0.05" expectation was statistically impossible. Rebuilt `scramble_pvalue(pos, prices)` as a true SIGNAL-scramble (circular shift of the POSITION series vs returns: keeps position persistence/cost structure, destroys date alignment). Test proves skilled AR(1) timing passes (p<0.05) and random timing fails; `eval_gates` without signal is now **fail-closed** (scramble gate FAILS, NaN p).
3. **Late price history duplicated release index**: copper px starts 2010-04-20 vs COT 2010-01-05 -> all earlier releases mapped to session 0 via `searchsorted(side='right')` -> "cannot reindex on duplicate labels" crash. Fixed keep-last (latest report wins at first tradable session — PIT-correct). Regression test `test_signal_to_daily_price_history_starts_late`.
4. **OI overlay sign bug**: negative growth / negative trailing-mean growth = positive ratio -> overlay=1.0 on *falling* OI. Fixed denominator `.where(denom > 0)`. Test `test_oi_change_overlay` catches it.
Also fixed: holiday-week Mon/Tue report collisions on the same release session (keep later report); test `weekmask` needed `freq='C'`.

## Timing chain (clean, per charter)
COT report Tue -> +3d = Friday release (public) -> `release_lag=1`: position set at NEXT session close (Mon) -> **first P&L Tuesday** — never same-week. Verified by 4 timing tests. Costs 6.4bps one-side FULL |dW| + 0.5%/yr borrow; vol-target 10% trailing-only clip 3.0; champion corr vs working-tree GOAL100_RAWEW13v2_WEIGHTED (SR 3.2964).

## Results (exact, net of costs, 2013-01..2026-08 weekly panels n=712 reports; spec-net panel n=869 from 2010)
**(a) Cross-market rank basket** (long k most-crowded-short specs / short k most-crowded-long, 1wk hold): k=2 SR **-0.581** ann -4.97% negyr 11(7<-5%) halves(-0.77,-0.43) scramble 0.229 corr -0.019; k=3 SR **-0.343** ann -2.64% negyr 8 scramble 0.169 corr -0.023; k=4 SR **-0.477** ann -3.24% negyr 10 scramble 0.517 corr -0.013. MIRROR (follow crowding) k=3 SR **+0.214** negyr 10 halves(+0.56,-0.05) — fails halves/yearly/SR.
**(b) Hedger fade** (fade commercial crowding, z-cap 2): pm lb=8 SR **+0.031**, lb=12 **-0.046**, lb=26 **-0.398**, lb=52 **-0.322** (negyr 5-10, scramble 0.18-0.68). swap lb=8/12/26/52 SR **-0.533/-0.530/-0.525/-0.202**, negyr up to 12, scramble 0.44-0.88. MIRRORs: pm-follow lb=8 SR **-0.296**; sw-follow lb=12 SR **+0.287** halves(-0.14,+0.58) negyr 4 — best of round, still fails SR/halves/scramble(0.652).
**(c) OI-change overlay** (0-1 new-money regime scale): on (a)k3 lb=4/8/13 SR **-0.206/-0.141/-0.382**; on (b)pm12 SR **+0.013** scramble 0.095. Standalone OI-growth xs rank k=3 (long OI-accreters / short OI-rotators): SR **+0.119** halves(+0.47,-0.15) negyr 8 scramble 0.164 corr -0.052.
**(d) Spec L/S asymmetry** L/(L+S) fade (separate long_pct/short_pct, disagg-only 2013+): lb=8/12/26/52 SR **-0.333/-0.306/-0.099/-0.317**, negyr 8-10, scramble 0.24-0.37. MIRROR lb=26 SR **-0.091**.
**Lookahead control** (+1wk artificial delay on best config pm-fade lb=8): SR +0.031 -> **-0.220** — timing chain is live and honest (a real weekly signal would degrade only modestly under +1wk; this one just flips within noise, consistent with pure noise).

## Verdict
- 24/24 configs FAIL. Not one reaches SR>=0.35, let alone SR>=1.0; every halves pair fails; negyr 4-12; scramble p 0.10-0.88 (never <0.05); the only gate any candidate passes is champion decorrelation (all |corr|<=0.052 — these signals are orthogonal to the champion, just not profitable).
- Signs are unstable across mirrors and lookbacks (pm fade ~0 but swap fade strongly NEGATIVE, i.e. swap-crowding *follow* is weakly positive) — no economic edge, pure noise around zero. Commercial hedgers are NOT the smart counterparty in these 9 markets post-2013 at 1wk horizon; cross-sectional COT crowding carries no 1wk cross-section return info after costs.
- Nothing saved to sleeves/ (sleeves dir stays empty), no champion impact, champion CSV untouched by this agent (working-tree diff present before my session = round-1 AUDIT_RECON causal re-emit, SR 3.2964, pending coordinator commit — I used it read-only as corr reference).
- Economic rationale for the negative: COT spec net %OI is a slow (≈4-8wk half-life) crowding measure; the prior round already showed same-period level corr +0.16..+0.22 is artifact (forward corr +0.03). Round 1 shows the *cross-sectional* and *counterparty-decomposition* transforms of the same underlying series also carry no exploitable 1wk-forward info at 6.4bps full-|dW| — the four charter aggregates are re-arrangements of a signal with ~zero forward information ratio in these markets.
- Repro: `campaign/agents/chief/coord/HUNT_COT2/hunt_r1.py` (driver), `lib_hunt.py` (lib), `test_lib_hunt.py` (21 tests, `python3 -m pytest test_lib_hunt.py -q` = 21 passed). DEAD_IDEAS.csv row to be added via coordinator per contract item 5.

ROUND 1 DONE

## ROUND 2 (2026-09-07, matched horizons / TFF / CIT / champion overlay) — verdict: **ALL 55 EVALUATED CONFIGS FAIL — honest negative.**

### State on arrival: round 2 was HALF-DONE and its committed log was INVALID
Found `hunt_r2.py` + `lib_r2.py` + a full `r2_output.log` (03:56) + tests edited at 04:05 — i.e. the prior
session was killed mid-TDD, AFTER editing tests, BEFORE fixing lib or re-running. Hard evidence the old log
is wrong: every single (b) TFF row shows `halves=(0.00,…)` — an exactly-zero H1 SR is not a market outcome,
it is a degenerate zero-variance block. Cause: `TestBookLiveWindow` (2 RED tests already written) pinned the
bug — `book_backtest_generic` used `dp.notna().any()` for the live window, but `signal_to_daily` fillna(0)s
all pre-signal sessions, so gbp/jpy books (prices 1971 vs TFF 2010) injected ~40y of fake-flat zeros: H1
pinned to 0.00 and SR diluted ~sqrt(live/total)≈0.54. Every (b) number in the old log is invalid and
(a)/(c) were mildly understated (GLD px 2004 vs signals 2010). Fixed TDD (RED->GREEN):
1. `lib_r2.book_backtest_generic`: per-market `started` mask (signal_to_daily of a unit series > 0) masks
   pre-first-tradable sessions to NaN so they cannot enter the book; also accepts in-memory Series prices.
2. Both `TestBookLiveWindow` fixtures were broken (2009/2010 releases AFTER prices ending ~1986/1990 ->
   zero tradable sessions -> IndexError; and `n_days<1200` ignored that the last held position legitimately
   ffills to end of prices). Fixed to pin the actual property: `start == first_tradable` and `n_days < n_px`.
Final suite: `python3 -m pytest test_lib_hunt.py test_lib_hunt_r2.py -q` -> **45 passed** (21 R1 + 24 R2).
Driver re-run (`python3 hunt_r2.py > r2_output_fixed.log`): all-fail conclusion survives, but numbers moved
materially (e.g. lev_follow_ext h=4 SR -0.305 -> **-0.566**; rank_k3 h=4 -0.348 -> **-0.381**; book vols
4.2% -> 7.7% once 40y of zero-vol days dropped). The corrected log is the evidence base below.

### Results (net, corrected engine; gates per GATES_CONTRACT, 6.4bps full-|dW| + 0.5%/yr borrow)
**(a) HORIZON MATCH — matched horizons do NOT rescue COT.** Same R1 signals at 4/8/13wk holds (turnover
correctly scales ~1/hold, e.g. pm_fade_lb8 52.9 -> 20.6 to/yr, so costs are NOT the story):
rank_k3 SR -0.381/-0.364/-0.291 (R1 1wk: -0.343) — sign-UNSTABLE, ~zero everywhere; pm_fade_lb8
-0.030/-0.126/**-0.701** (degrades monotonically with horizon); pm_fade_lb26 -0.392/-0.460/-0.794;
sw_fade_lb8 -0.146/+0.030/-0.283; sw_fade_lb26 -0.381/-0.229/-0.171. 15/15 FAIL (SR, halves, yearly,
plateau all false; scramble p 0.015-0.930; all |corr|<=0.043).
**(b) TFF dealer fade / lev-money follow (10 financial mkts; VIX/ED/SOFR no proxy — documented):**
dealer_fade_z -0.134/-0.010/+0.020 (h=1: -0.322); dealer_fade_ext -0.155/-0.169/-0.319; lev_follow_z
-0.199/+0.129/+0.182 (h=1: -0.379) — the only weak positives, but halves (0.19,0.07)/(0.37,-0.00): H2 is
DEAD, classic in-sample artifact; lev_follow_ext -0.566/-0.490/+0.037. 16/16 FAIL (best negyr 2-12;
scramble p 0.005-0.731; |corr|<=0.072). Dealer extreme-short fade is consistently NEGATIVE — dealers are
not a dumb-money fade in these markets either.
**(c) CIT index-trader fade (4 of 13 mkts with in-repo proxies; documented):** cit_fade_z h=4/8/13 SR
+0.027/+0.060/**+0.294** (ann +2.95%, halves 0.56/0.04 — H2 zero), cit_fade_ext +0.097/+0.104/+0.007
(halves -0.34,+051 / -0.43,+0.60 — sign-flipped halves). 6/6 FAIL.
**(d) Champion regime overlay — 18 variants, ALL WORSEN the champion:** aggregate spec-crowding
percentile (104wk trailing, self-excluded) applied to GOAL100_RAWEW13v2_WEIGHTED (baseline SR 3.252-3.311
on matched windows): mean_net_pct scale cut=0.5 hi=0.85/0.9 dSR **-0.237/-0.178**; cut=0.0 (flat at
extremes) dSR **-0.565/-0.429**; flip dSR **-1.390/-1.089** (MDD -0.070 -> -0.337/-0.188). NEW this round:
12 TFF-aggregate overlays (dealer/lev_money mean %OI crowding, same chain): best dSR **-0.069**
(lev_money cut=0.5 hi=0.9), worst -1.461; MDD never improves; scramble p 0.119-1.000 (never <0.05).
`mean_xs_rank` overlay variant is VACUOUS BY CONSTRUCTION, not failed: cross-sectional ranks always
average to a constant (measured: agg series std=0.0, range [0.5,0.5] after deviation-from-first-row),
so no aggregate-crowding regime exists to overlay on — logged as skipped with reason.

### Verdict
- 55/55 evaluated configs FAIL; nothing saved to sleeves/ (dir stays empty); champion CSV untouched
  (read-only corr/baseline reference, working-tree round-1 AUDIT_RECON diff predates my session).
- The charter's round-2 hypothesis is REFUTED: the slow 4-8wk COT half-life does NOT pay at matched
  horizons — at 4/8/13wk holds the same signals stay ~zero or get WORSE (pm_fade_lb8 -0.03 -> -0.70),
  so the R1 negative was not a horizon-mismatch artifact. New counterparties (TFF dealers, leveraged
  money, CIT index traders) carry no edge either, and aggregate COT crowding carries NO regime
  information for the champion (every one of 18 overlays lowers SR; scramble p never < 0.05).
- Honesty corrections this round: the inherited r2_output.log (b)-section was invalid (zero-variance H1)
  and is superseded by r2_output_fixed.log; 2 RED tests + invalid fixtures repaired to 45 green.
- DEAD_IDEAS.csv rows for coordinator (contract item 5): cot_horizon_match_4_8_13wk,
  tff_dealer_fade, tff_lev_money_follow, cit_extreme_fade, cot_crowding_champion_overlay (all:
  SR gate fail, exact numbers above).
- Repro: `campaign/agents/chief/coord/HUNT_COT2/`: `hunt_r2.py` (driver), `lib_r2.py` (round-2 lib),
  `test_lib_hunt_r2.py` (24 tests), corrected log `r2_output_fixed.log`;
  `python3 -m pytest test_lib_hunt.py test_lib_hunt_r2.py -q` = **45 passed**.
ROUND 2 DONE

## ROUND 3 (2026-09-07, verification + curation charter) — verdict: **NO FRAUD FOUND; family CLOSED.**

### State on arrival: round 3 was ~70% done by a killed prior session; I audited rather than redid
Found `verify_cmdt2_r3.py` + 2 rebuild scripts (in campaign/scripts/) + logs + 2 R3 test files with
mtimes 09:18-10:10, AFTER my FINDINGS round-2 entry (05:13), and no round-3 FINDINGS section. The
verifier's own history shows an honest TDD arc: rerun2.log flags 11/12 sleeves as MISMATCH **on
worstyr alone** (e.g. "worstyr -8.4% vs claimed -8.4%") - a verifier-side rounding artifact (metas
publish percentages on a 0.1pp grid), fixed by TOL_PCT_PUBLISHED=0.05 + test_worstyr_rounding_tolerance.py.
My re-audit (all rerun by me, exit codes recorded):
- `python3 verify_cmdt2_r3.py` -> exit 0, **12/12 MATCH** (SR, annGeo, vol, halves 2 conventions,
  negyrs, worstyr, corr-vs-champion, n, window, integrity probes dup/nonmono/nonfinite all clean).
- `python3 -m pytest tests_r3/... -q` -> **6 passed**; `test_lib_hunt.py test_lib_hunt_r2.py -q` ->
  **45 passed** (51 total).
- `python3 campaign/scripts/HUNT_COT2_rebuild_cmdt2.py` (rebuild 4 sleeves from RAW data, own engine)
  -> rerun today, output CSV **byte-identical** to committed (diff clean), summary "4/4 reproduce,
  no-lookahead truncation probes 4/4 bitwise-identical".

### (a) Cross-verification result: HUNT_CMDT2 round-2 verdicts CONFIRMED, with one data-vintage finding
Independent recompute of all 12 sleeve CSVs matches their metas exactly. **Max SR claimed among the 12:
0.577** (CMDT_SectorRot_6m_h2_LS); best COT-family sleeve CMDT2_CotGatedMom 0.245. Every sleeve fails
gate (a) SR>=1.0 by a wide margin - their round-2 all-fail verdict stands.
**Data-vintage finding (NOT fraud):** rerunning the p2 rebuild today produced corr 0.99998 (max|d|=4.5e-3)
on the two 9-market books where the committed CSV recorded 1.0/1e-16. Localized: diffs confined to
**exactly 2 sessions, 2026-09-03/04**. Cause: the 09:01-09:09 more_etf data refresh (between CMDT2's
08:35 p2 run and my rerun) appended real bars for 09-03/04; their saved sleeve ends 09-02 with -4e-6
stub rows. Evidence (rebuild_p2_vintage_analysis.log): cut at 2026-09-02 -> max|d|=9.97e-17, dSR
+0.0000 for both books (EXACT match); full-overlap dSR only +0.0010/+0.0013 (immaterial). Truncation
no-lookahead probes bitwise-identical 4/4 => no history revision, no lookahead, no fabrication.
I restored the committed p2 CSV (my rerun log saved separately as rebuild_p2_datavintage_rerun_1205.log)
and did not edit any HUNT_CMDT2 file.

### (b) DEAD_IDEAS curation
Audited all 9 COT/TFF/CIT rows (lines 49, 53, 56, 63, 75, 76, 84, 87, 88): every evidence cell has
exact numbers (programmatic check). Gap: **no row carries an explicit repro path**, and rows 49/53's
source cells (HUNT_CIT_AG / HUNT_TFF) resolve to dirs that do NOT exist under coord/ - the artifacts
actually live in campaign/agents/loop_team/ (I first looked in the wrong place; the paths needed
recording). Verified row 49/53 headline numbers against loop_team FINDINGS.md (grep, not full
recompute): 0.21/0.465/0.705 (CIT_AG) and 156 variants/0.275/0.203 (TFF) all present. Row 56 repro
path located: campaign/scripts/cot_positioning_hunt.py + cot_delta_momentum.py + cot_delta_weekly.py.
**Appended 4 "- repro-path correction" rows (HUNT_COT2-R3)** with verified paths + re-verified
numbers; existing rows byte-preserved (asserted pre/post), file parses clean, 96 -> 100 data rows,
all 4-field. Never deleted/modified existing rows.

### (c) Domain-closure memo: HUNT_COT2/COT_CLOSURE_R3.md
Family CLOSED on 250+ configs across 4 campaigns: no forward information at any transform (level,
delta, xs-rank, counterparty decomposition, L/S asymmetry, aggregate regime); horizon mismatch ruled
out (4/8/13wk holds stay ~zero or worsen); signs unstable; overlay always hurts champion (30/30
variants). Reopen candidates, verified against what is actually on disk: **(1) trader-count breadth
from the in-repo _raw disagg zips (verified: 191 cols incl. Traders_Tot_All etc. - never tested, no
new data needed, cheapest candidate); (2) CFTC supplemental futures-options report (delta-adjusted
net; NOT in repo, fut zips verified futures-only); (3) proxy completion for VIX/ED/SOFR TFF/CIT
panels; (4) daily/concentration/entity data (not publicly available).**

### Charter compliance
No champion file touched (read-only corr reference). Nothing passed gates => nothing new saved to
sleeves/ (stays empty). Fraud-catch duty executed: 12/12 verified, 7/12 independently REBUILT from
raw data, one data-vintage effect investigated and explained with exact numbers. All claims reproduce
from saved scripts + logs in HUNT_COT2/ and campaign/scripts/HUNT_COT2_*.py.
PROCESS NOTE: my first append accidentally landed in coord/FINDINGS.md (shell cwd reset); caught via
tail -1 showing ROUND 2 DONE, truncated back byte-exactly (16011 bytes, marker at 16011, prior tail
"ROUND 2 DONE" intact), then appended here. coord/FINDINGS.md verified unmodified vs git.

ROUND 3 DONE

## ROUND 4 (2026-09-07 17:3x-18:0x CST) - panel-absent -> DEAD_IDEAS audit rotation (charter path b)

### (a) trader_count_panel.csv: NOT PRESENT (checked twice)
Charter path `DATA_COTMORE/work_r4/trader_count_panel.csv` does not exist. Checked at round start
(`ls coord/DATA_COTMORE/` -> CHARTER/FINDINGS/sleeves/work_r3 only, no work_r4) and re-checked at
round end; repo-wide `find . -name "*trader_count*"` -> zero hits; `find -type d -name work_r4`
-> zero hits. My R3 closure memo listed trader-count breadth as the cheapest reopen candidate but
the DATA_COTMORE build has not landed it. No config was pre-registered => per charter rule
(pre-register BEFORE running) I did not stand up the panel myself; that remains DATA_COTMORE's lane.
Executed (b) instead: 6-row DEAD_IDEAS audit rotation, non-COT families.

### Selection rule (pre-registered before any verification)
Programmatic scan of all 108 data rows: 85 non-COT; score each on (numbers present >=3) x
(evidence length) x (source dir resolvable). Picked the thinnest across 6 DISTINCT families:
L2 (HUNT_FF2), L3 (HUNT_FUNDAMENTAL), L5 (HUNT_FUNDAMENTAL), L14/L15/L16 (SKILL_ALPHAAGM), L33
(SKILL_ALPHAAGB_B), L13 (LOOP_XGB1YFLAT - found unresolvable initially, dir is
campaign/agents/LOOP_XGB1YFLAT not loop_team/). SCAN-BUG DISCLOSED: my first pass reported
SKILL_ALPHAAGM/ALPHAAGB_B/FINAL_STATE as unresolvable because my name matcher dropped underscores
asymmetrically; re-check showed both SKILL dirs exist under loop_team/. Fixed before conclusions
were drawn; only selection was affected, not any verdict.

### (b) The 6-row audit: what was verified (exact numbers from the actual sources)

1. L2 FF factor premia -> HUNT_FF2 confirmed dead WITH numbers: RAW factors 2008+ SR MKT +0.57 /
   SMB -0.00 / HML -0.01 / MOM +0.11; factor TS-mom 44 cells best 0.58; E-L 2008+ -0.04; deciles
   HML_from_6pf -0.02, OP_Hi30_Lo30 +0.29 (halves FAIL). **Hash-verified repro: recomputed sha256 of
   both delivered sleeves matches FINDINGS claims EXACTLY (raw 1adcb4b7fbbdc079, poolvt
   55a9b3e5661bd871).**
2. L3 industry/decile L/S -> HUNT_FUNDAMENTAL confirmed: 5 composites all FAIL (value_comp +0.06
   11negy ... comp_vgp -0.16 13negy); annual IC value +0.0249 IR 0.23; best pair s_ta+roic IC
   +0.1042 -> backtest SR +0.39 7negy; survivorship short-leg inversion 15/17 yrs. Scripts exist
   (fund_screen_all.py / hf_engine.py / final_candidate.py).
3. **L5 BAB - SOURCE-ATTRIBUTION ERROR FOUND (escalating per charter):** row cites HUNT_FUNDAMENTAL,
   but grep of HUNT_FUNDAMENTAL/FINDINGS.md for BAB/beta/ivol/Moreira -> ZERO hits. The evidence
   lives in HUNT_FF2 (BAB_v25_L05S05 SR -0.64, short-highvol leg -0.74%/yr, built in recon3.py,
   sleeve-C long-only in recon5.py). Verdict unchanged (dead either way) but the citation was wrong.
4. **L4 MM naive ivol - SAME ATTRIBUTION ERROR:** cites HUNT_FUNDAMENTAL, zero MM/ivol content
   there; actual evidence = HUNT_FF2 Angle 2 (recon1: MOM -0.19 H2, MDD -55.7%; "do not retry
   without a sign-gate"). This is the exact same class of thin-attribution defect I flagged in R3
   for COT rows - it is a DEAD_IDEAS-wide hygiene issue, not fraud (the underlying work exists and
   is honest; only the `source` cell pointed at the wrong agent).
5. L14 FOMC x natgas/gold -> SKILL_ALPHAAGM explicitly did NOT re-run it ("documented dead by prior
   agents"); ORIGINAL numbers found in campaign/agents/D4_microstruct: post-FOMC NG k=1 raw t=-3.32
   NEGATIVE drift, best book SR 0.51 H1 0.22, gold SR 0.18, scramble p 1.000, family best 0.53.
6. L15/L16 M2-gold + CFNAI -> same pattern; originals in campaign/agents/D2_macroregime: M2 yoy
   vs 5y-median (+28d lag) long gold SR 0.28 (H1 -0.06, sig_p 0.000); M2 yoy>5% SR 0.12; always-long
   gold baseline SR 0.56 6negy; CFNAI FAIL data-blocked (BAMLC0A0CM starts 2023-08 = honestly
   untestable, gated corp SR 0.02 sig_p 0.000). L33 USDJPY 30-grid verified directly: best map SR
   +0.599 fails 0.6 gate by 0.001 AND is best-of-30 multiple-tested (ALPHAAGB_B P7).

### DEAD_IDEAS.csv append (append-only; existing rows byte-preserved)
6 correction rows appended (HUNT_COT2-R4): 2 repro-path+numbers (L2, L3), 2 source-attribution
corrections (L4, L5), 2 repro-path+numbers for the SKILL_ALPHAAGM not-rerun pointers (L14, L15+16
merged row). Integrity asserted programmatically: 26,986-byte prefix byte-identical pre/post,
108 -> 114 data rows, all rows 4-field, file parses clean. Never deleted/modified an existing row.
L33/L13 were verified but NOT appended (both already carry exact numbers in-cell: 0.599 and
0.951/211; L13's dir location is the only gap and it is minor - noted here instead of churning the
file).

### Charter compliance
Champion untouched (not even read for corr this round - no new sleeve was tested). Nothing passed
gates => sleeves/ stays empty; no new scripts saved (audit round, no signal code written). All
claims above reproduce from grep/shasum/python-assert commands against
campaign/agents/loop_team/{HUNT_FF2,HUNT_FUNDAMENTAL,SKILL_ALPHAAGB_B}/FINDINGS.md,
campaign/agents/{D2_macroregime,D4_microstruct}/FINDINGS.md, and the sha256s inside
HUNT_FF2/sleeves/. Honest outcome: family stays CLOSED pending the trader-count panel; DEAD_IDEAS
is now 114 rows with 2 attribution defects fixed at the source-pointer level.

ROUND 4 DONE

## ROUND 5 (2026-09-08 04:3x-05:1x CST) — trader-COUNT breadth (NEW corner, pre-registered below)

### Pre-registration (charter rule: BEFORE running; written first, configs not yet executed)
Grep-before-build done: DEAD_IDEAS.csv now has **120 data rows** (recounted myself, 121 lines
incl header — charter's "120 at R4-end" confirmed). No row covers trader-COUNT breadth: the
only "trader" hits are the two TFF rows (line 53/98) which are POSITION families
(`pct_of_oi`, verified in loop_team/HUNT_TFF/tff_eng.py:12) — participation COUNTS
(Traders_Tot_All etc.) are genuinely untested. Panel verified present and honest:
- `campaign/agents/chief/coord/DATA_COTMORE/work_r4/trader_count_panel.csv` — **29,017 data
  rows x 51 cols, 35 families** (my own count matches charter).
- Charter-mandated BREAK verification (both directions, exact numbers from raw panel data):
  nat_gas_nymex 2022-02-08 TotAll **281 -> 40 = -86%** (OI 1,162,813 -> 590,294 = -49%;
  stitched z prints **-10.74** = family min = the exact artifact MANIFEST_R4 bans); lumber
  2023-04-25 TotAll **21 -> 43 = +105%** (OI +234%). Builder lint re-run in-memory by me:
  **33 PASS / 2 PASS_WITH_EXN (nat_gas_nymex, lumber) / 0 FAIL** — the fail-closed BREAK
  gate fires on both. Synthetic fixture probe: a -80% seam flags PASS_WITH_EXN, a +10%
  rename stays PASS (gate discriminates, not just a name-change tripwire). Their suite:
  `pytest test_trader_count_panel.py` = **24 passed**. Panel z range [-10.74, 4.10] matches
  the manifest.
- Proxy coverage: **21/35 families** have in-repo price proxies (PX map below); 14 have
  none (canola, cocoa, coffee_c, cotton_no2, eurodollar_3m, feeder_cattle, lean_hogs,
  live_cattle, lumber, rough_rice, sofr_3m, soybean_meal, soybean_oil, vix) — excluded from
  books, documented, not silently dropped.
- TDD: `test_lib_hunt_r5.py` written FIRST (RED: ModuleNotFoundError), then `lib_r5.py`
  implemented to green. Suite now **58 passed** (21 R1 + 24 R2 + 13 R5).
- Engine: panel PIT z (expanding, min_periods=26, ddof=0 — re-derived per segment for break
  families) -> Friday release_date -> T+1 (position Monday close, first P&L Tuesday) ->
  6.4bps one-side FULL |dW| + 0.5%/yr borrow + vol-target 10% trailing clip 3.0. Segmenting
  verified by test: no nat_gas/lumber z read crosses the break; stitched -10.74 cannot
  survive (load_breadth raises if a < -5 value appears in an unbroken family).

### PRE-REGISTERED CONFIGS (fixed before any backtest; no tuning after seeing results)
Breadth signal = count-z tail events (contract: new corner is PARTICIPATION breadth, not
positioning). Two book shapes x direction mirrors x 2 thresholds:
- C1  TS gate, Tot_All, tail=LOW (breadth-thin -> LONG), thr 1.5, 21 proxy families, EW book
- C2  TS gate, Tot_All, tail=HIGH (breadth-thick -> LONG) thr 1.5, same book (mirror)
- C3  = C1 @ thr 2.0 (extremes only); C4 = C2 @ thr 2.0
- C5  XS rank k=3: long thinnest-breadth 3 / short thickest 3, weekly, 21 families
- C6  = C5 k=4
- C7  participant-mix: TS gate on z of MM Long-count (spec breadth), tail=LOW, thr 1.5
- C8  TS gate on z of Dealer Long-count (fin format), tail=LOW, thr 1.5, fin-proxy families
- C9  = C8 mirrored (tail=HIGH)
Every config judged on the FULL V2 battery: gates.run(sig=book_pos, leak_check=True
EXPLICIT, beats_passive trio) + lib gates (SR>=1.0, halves>=0.5, yearly<=2 neg > -5%,
200x position-scramble p<0.05, plateau on thr neighbors C1-C4, |corr|<0.15 vs champion of
record GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha 4358dfab95679b97).

### Execution (configs run EXACTLY as pre-registered; log = r5_output.log)
Framework note (disclosed): two cosmetic driver fixes were needed DURING the first run
(CTA csv lacks a parseable 'date' dtype -> explicit to_datetime; newdata DEX* files use
'observation_date' header -> load_px_r5 wrapper) and one panel z-column name lookup was
corrected (z_Traders_<col>, panel naming) — none touch signal math, costs, timing, or
gates; all 13 r5 tests stayed green through the changes. The log's "worst nan%" cells are
a print-key miss in my driver (eval_gates carries no 'worst' key); worst-year numbers below
were recomputed directly from the saved book CSVs.

| config | SR | ann% | H1/H2 | negyr | worstyr% | MDD% | scr_p | corr | V2 pass |
|---|---|---|---|---|---|---|---|---|---|
| C9 ts dealerLong-count HIGH 1.5 (10 fin fams) | +0.590 | +2.76 | +0.79/+0.55 | 3 | -14.26 | -16.2 | 0.055 | +0.027 | FAIL |
| C3 ts Tot_All LOW 2.0 (21 fams) | +0.335 | +0.81 | +0.30/+0.39 | 3 | -2.64 | -7.3 | 0.015 | +0.007 | FAIL |
| C8 ts dealerLong-count LOW 1.5 | +0.260 | +1.07 | +0.12/+0.36 | 7 | - | -10.0 | 0.109 | -0.045 | FAIL |
| C1 ts Tot_All LOW 1.5 | +0.243 | +1.03 | +0.33/+0.21 | 6 | -3.92 | -8.9 | 0.149 | -0.022 | FAIL |
| C4 ts Tot_All HIGH 2.0 | +0.188 | +0.97 | +0.23/+0.14 | 9 | - | -21.3 | 0.194 | +0.008 | FAIL |
| C2 ts Tot_All HIGH 1.5 | +0.118 | +0.88 | +0.19/+0.01 | 7 | - | -32.8 | 0.433 | -0.001 | FAIL |
| C7 ts mmLong-count LOW 1.5 (11 disagg fams) | +0.081 | +0.41 | +0.22/-0.12 | 5 | - | -13.2 | 0.065 | +0.012 | FAIL |
| C5 xs rank k=3 | -0.223 | -0.61 | -0.26/-0.19 | 10 | - | -21.2 | 0.015 | -0.041 | FAIL |
| C6 xs rank k=4 | -0.290 | -0.73 | -0.39/-0.21 | 9 | - | -21.2 | 0.015 | -0.055 | FAIL |

(families_used verified: C7=11 disagg-proxy families, C8/C9=10 fin-proxy families — the
5 disagg-format names in my FIN list have structurally-blank Dealer cols per the manifest
and were dropped by the engine, exactly as MANIFEST_R4 warns.)

### V2 battery detail (every submission-grade probe, all 9 configs)
- **SR gate 3a**: 0/9 reach 1.0. Best C9 = 0.590. The R4 "span gate" bar (effect over >=8y)
  also fails: C9 halves +0.79/+0.55 pass halves but the book makes +2.76%/yr against a
  10% vol target and has 3 negative years incl. one at -14.26%.
- **leak_probe (V2 §6 Step-1, sig= + leak_check=True EXPLICIT)**: leak=False, leak_ok=True
  on ALL 9. same_period_corr range +0.0098..+0.0577 (threshold 0.20), lag-0 argmax holds,
  all fail-closed contract keys published in the run dict. No timing artifact anywhere.
- **scramble 3e (200x position-lag)**: pass on C3/C5/C6 (p 0.015) but those FAIL SR and
  yearly; C9 p 0.055 — misses the 0.05 bar too.
- **beats-passive trio (V2 §7c pinned inputs: twelvedata SPY, more_etf IEF,
  sleeve_library CTA_15vol), supplemental on the 2 leaders**: C9 candidate SR 0.590 vs
  sixty_forty 0.763 (spy_bh 0.758, cta -0.112) -> beats_passive_ok=False
  (reason candidate_sr_le_passive); C3 0.335 vs 0.827 -> False. Both lose to passive
  buy-hold on their own span at campaign costs.
- **corr 3f**: all |corr| <= 0.055 vs champion of record (sha 4358dfab95679b97) —
  orthogonal to the champion but unprofitable, the same signature as R1/R2 COT.
- Plateau (C1-C4 threshold neighbors): no thr-1.5/2.0 pair is jointly gate-worthy
  (1.5 LOW 0.243 -> 2.0 LOW 0.335 and 1.5 HIGH 0.118 -> 2.0 HIGH 0.188 — unstable, and
  both legs fail SR/halves regardless).

### Verdict
**9/9 PRE-REGISTERED CONFIGS FAIL THE FULL V2 BATTERY — honest negative; the new corner is
CLOSED with the rest of the COT family.** Trader-COUNT breadth (participation) carries no
exploitable weekly-forward info in the 21 proxy markets at 6.4bps full-|dW|: the
breadth-thin long book (C1/C3) is the best-shaped but at SR 0.24-0.34, its mirror
(C2/C4 HIGH) is positive-only-by-vol-drag, the direct cross-sectional analog of R1's rank
basket is NEGATIVE (-0.22/-0.29: long thinnest-breadth markets LOSES), and the single
"interesting" cell (C9 dealer-count-crowding mirror, SR 0.590, halves +0.79/+0.55) fails
SR 1.0 by 0.41, scramble 0.055 vs 0.05, yearly 3 vs <=2 with worst -14.26%, and loses to
sixty-forty by 0.17 SR. Nothing saved to sleeves/; no champion or bt/ file touched;
DEAD_IDEAS.csv untouched by me this round (working-tree diff on it predates my session,
02:24 vs my 04:34 start — other agents' R3/R4 rows, coordinator-owned file per item 5).
- Economic read: breadth-of-participation is a SLOW crowd measure like positioning itself
  (its z tails are rare: most families 0-11% of weeks beyond |z|=2), and where a tail
  fires it mostly re-encodes the same crowding information R1-R2 already proved
  informationless — counts do not add a direction.
- Reopen candidates remaining from COT_CLOSURE_R3: CFTC supplemental futures-options
  (delta-adjusted, NOT in repo), TFF/CIT proxy completion for VIX/ED/SOFR, and
  daily/concentration/entity data (not publicly available). Trader-count breadth is now
  REMOVED from that list.
- Repro: campaign/agents/chief/coord/HUNT_COT2/: hunt_r5.py (driver, pre-registered
  config table verbatim), lib_r5.py (segment-safe breadth lib), test_lib_hunt_r5.py
  (13 tests; full suite 58 passed), r5_output.log, r5_book_C{1,3,9}_*.csv (book series,
  V2 §10a). Panel + builder: coord/DATA_COTMORE/work_r4/ (theirs, unmodified — my lint
  run was in-memory only).

ROUND 5 DONE

## ROUND 4 RE-RUN SESSION (2026-09-08 09:0x CST) - re-executed as INDEPENDENT VERIFICATION (fraud-catch duty)

Context discovered at round start: this 09:0x prompt re-fires the round-4 charter AFTER round 4 was
already completed (09-07 17:3x-18:0x, charter path b: panel absent -> 6-row DEAD_IDEAS audit) AND
round 5 already ran the now-landed panel as its pre-registered new corner (09-08 04:3x-05:1x,
9/9 configs FAIL full V2 battery - see prior section). Evidence of sequence: FINDINGS.md had
"ROUND 4 DONE" at line 228 and "ROUND 5 DONE" at line 348 before I wrote anything; panel file
mtime 2026-09-08 02:32; work_r5/ contents 08:06. This is the known launcher re-run pattern
(env loss -> DONE rounds re-run). Re-testing the panel corner again would duplicate a
PRE-REGISTERED R5 run (p-hacking-adjacent, zero new information) - so the honest round-4
execution here is the charter's own verification lane (R3-style fraud-catch): independently
reproduce the existing round-4/5 record with my own code. Every number below is from commands
I ran this session.

### (1) Panel + charter R5 preconditions
- coord/DATA_COTMORE/work_r4/trader_count_panel.csv EXISTS: 11,141,330 bytes, 29,018 lines
  (= 29,017 data rows, matches charter R5 claim) x 51 cols (awk -F, NF), mtime 09-08 02:32.
- sleeves/ dir EMPTY (0 files) - correct: nothing passed gates, nothing was saved.

### (2) BREAK-gate numbers re-derived from RAW panel (my own csv pass, no builder code)
- nat_gas_nymex: 2022-02-01 TotAll 281 -> 2022-02-08 TotAll 40 = **-86 pct**; OI 1,162,813 ->
  590,294 = **-49 pct**. EXACTLY as recorded.
- lumber: 2023-04-18 TotAll 21 -> 2023-04-25 TotAll 43 = **+105 pct**; OI 1,136 -> 3,794 =
  **+234 pct**. EXACTLY as recorded. Both PASS_WITH_EXN breaks are real in the raw data; verdict:
  the stitched-panel ban on z-reads across these dates is data-justified.

### (3) R5 book gates INDEPENDENTLY RECOMPUTED (own SR/halves/corr code on saved book CSVs)
| book | n | span | annSR (mine) | annRet arith | halves (mine) | corr vs champ (mine) |
|---|---|---|---|---|---|---|
| C9 dealerLong HIGH 1.5 | 3951 | 2011-01-18..2026-09-04 | **+0.590** | +2.76 pct | +0.79/+0.55 | +0.0271 (n=3945 common) |
| C3 tot LOW 2.0 | 4087 | 2010-07-06..2026-09-04 | **+0.335** | +0.81 pct | +0.30/+0.39 | +0.0070 (n=4081) |
| C1 tot LOW 1.5 | 4087 | 2010-07-06..2026-09-04 | **+0.243** | +1.04 pct | +0.33/+0.21 | -0.0217 (n=4081) |
ALL match r5_output.log + the R5 FINDINGS table to 3 decimals. C9 neg calendar years = 3 (matches);
worst calendar year 2022 -13.74 pct vs FINDINGS' -14.26 pct - minor year-bucketing definitional
variance (their recomputation vs my calendar-year product); yearly-gate verdict FAIL unchanged.

### (4) Champion of record re-verified fresh this session
- sha256[:16] of campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv =
  **4358dfab95679b97** = EXACT charter match.
- My naive stats: n=4805, 2008-03-31..2026-08-27, ann arith 32.1373 pct, SR 3.1813, MDD
  -6.6922 pct, 0 neg years.
- Coordinator verify_champion_standup_0445.json (04:45 today): ok=true errors=[] with
  weights_repro max_dev 2.2e-16, byte_repro 1.1e-16, cost_reconciliation full_dw
  charged 100.34bp (5.26bp/yr), causality matched_mechanism=causal (sameday dev 4.9e-3
  rejected), yearly neg_years 0, mdd -6.6922 pct ok.
- **APPARENT-DISCREPANCY CLOSED (documenting because it looked like one):** charter's
  37.1954 pct = tool ann_cagr_pct (geometric); my 32.1373 pct = tool ann_arith_pct - both
  present in the SAME stats block (37.19539675684982 / 32.13733812888786). Not an error;
  convention difference. SR 3.180994 (tool) vs 3.1813 (my ddof=0 periodic) - rounding-level.
  7/7 checks ok confirmed by me reading the JSON, independent of the coordinator's claim.

### (5) R4 audit-rotation record re-verified
- DEAD_IDEAS.csv parses clean via csv module: 132 data rows (108 at R4 start + 6 mine + other
  agents' rows since), ZERO rows with field-count != 4; my 6 HUNT_COT2-R4 rows present
  (file lines 110-115, supplementing original lines 2,3,4,5,14,15-16).
- HUNT_FF2 sleeve sha256s RECOMPUTED: FF2_DUALGATE_raw_daily.csv 1adcb4b7fbbdc079,
  FF2_DUALGATE_poolvt_daily.csv 55a9b3e5661bd871 - exact match to my R4 audit claims.

### (6) Test suite reproducibility
- pytest test_lib_hunt.py + test_lib_hunt_r2.py + test_lib_hunt_r5.py: **58 passed in 16.29s**
  (matches R5's claimed 58 green).

### (7) GAP FOUND (escalating per charter, NOT fixed by me)
- NO DEAD_IDEAS row yet for the trader-COUNT breadth corner (R5's 9/9-fail verdict). The file's
  working-tree diff (+69 lines vs HEAD) predates my session and belongs to other agents; item 5
  of GATES_CONTRACT routes DEAD_IDEAS appends through the coordinator. R5 section correctly did
  not touch the file; the row remains the coordinator's to append. Suggested row:
  "COT trader-count breadth (cnt_Traders_* z-tails, 29,017x51 panel) - dead - 9/9 pre-reg configs
  fail V2 (best C9 SR 0.590 halves 0.79/0.55 negyr 3 scr 0.055 corr 0.027, loses to 60/40 0.763);
  repro HUNT_COT2/{hunt_r5.py,lib_r5.py,r5_output.log}".

### Verdict
ROUND-4/5 RECORD REPRODUCES IN FULL: every gate number I could recompute independently (books,
BREAKs, champion, shas, tests) matches the saved record; zero fraud, zero arithmetic error, one
definitional variance (worst-year bucket) and one open bookkeeping gap (missing DEAD_IDEAS row for
the trader-count corner, coordinator-owned). Family stays CLOSED. No new sleeve, nothing to
sleeves/, champion untouched (read-only via verify JSONs), no other agent's file modified.

ROUND 4 DONE

## ROUND 5 RE-FIRE SESSION (2026-09-08 09:2x CST) - launcher re-run; executed the NEW verification lane: V2 s6 verdict-neutrality of the Step-2 leak flip measured on the R5 artifacts

Round start evidence: FINDINGS.md already carried "ROUND 5 DONE" (04:3x-05:1x, 9/9 pre-registered
configs FAIL full V2 battery) plus a 09:0x independent re-verification session - the known launcher
re-run pattern. Re-executing the pre-registered panel corner a third time would duplicate a
pre-registered run (p-hacking-adjacent, zero information). But the tree MOVED since my R5 entry in a
way that touches R5's evidence base: commit 539f50e (09:17, minutes before this session) landed the
GATES_CONTRACT_V2 section-12 Step-2 flip - leak_check default ON in bt/gates.run - AFTER the R5
battery ran under the old default. V2 s6 claims the flip "changes NO existing verdict"; the flip
commit claims "403 passed / 0 failed". Both claims are now MEASURED BY ME on my family's artifacts
(new work, not duplication).

### Fresh round-start state (all re-derived this session)
- GATES_CONTRACT_V2.md re-read in full (RATIFIED 09-08 03:1x). DEAD_IDEAS.csv recounted:
  **132 data rows** (charter guessed ~120; V2 preamble says dynamic, recount - confirmed), 0 bad
  field counts. All-field grep for breadth/cnt_/trader_count/traders_tot/participant: **ZERO rows**
  - the trader-COUNT-breadth DEAD_IDEAS row I flagged at 09:0x is still missing (coordinator-owned
  per v1 item 5; gap OPEN, escalation stands).
- Panel: coord/DATA_COTMORE/work_r4/trader_count_panel.csv present, 11,141,330 bytes, mtime 09-08
  02:32; builder + its test mtimes 02:31/02:27 - UNCHANGED since R5 ran, so the two charter BREAKs
  I re-derived from raw data at 09:0x (nat_gas_nymex 2022-02-08 -86 pct; lumber 2023-04-25 +105 pct)
  need no third derivation. BREAK gate verified fail-closed on both (R5 entry: 33 PASS / 2
  PASS_WITH_EXN / 0 FAIL).
- Champion of record: sha256[:16] **4358dfab95679b97** = exact charter match; fresh naive recompute
  n=4805 2008-03-31..2026-08-27, SR(ddof0) 3.1813, annGeo 37.1954 pct, MDD -6.6922 pct, 0 negyrs.
- sleeves/ dir EMPTY (0 files) - correct, nothing passed gates.

### (1) Flip commit integrity (V2 s12 runbook steps 2-5, verified in tree)
- bt/gates.py:104 `leak_on = bool(p.pop('leak_check', True))` - COMMITTED, worktree clean vs HEAD
  (no dirty mid-round edit; the s6 concern about racing AUDIT_FWBUGS is moot post-commit).
- Old migration pin test_gates_default_has_no_leak_gate: **0 hits** in test_fwbugs_audit_r3.py
  (deleted per runbook step 3).
- RED-first pair moved to campaign/bt/tests/test_fwbugs_audit_r5_leakflip.py: present in HEAD AND
  worktree byte-identical (git diff HEAD clean); runs standalone **3 passed**.
- Initial confusion disclosed: commit paths are prefixed software/world-trader/ (repo root is
  /Users/daxu, not the world-trader dir) - my first `git cat-file -e HEAD:campaign/...` probed a
  nonexistent path and briefly looked like a missing file. Resolved with full paths; no defect.

### (2) Full bt suite post-flip: **403 passed / 0 failed in 65.46s** from world-trader root
Reproduces the flip commit's evidence claim exactly. My own suite (test_lib_hunt + r2 + r5):
**58 passed in 14.44s** - matches the R5 record.

### (3) V2 s6 verdict-neutrality measured on R5 books under the FLIPPED default
gates.run called with the leak_check kwarg OMITTED (now defaults True; the exact caller class V2 s6
analyzed), ref = champion of record, scramble_n=200 seed=7. Step A used a crude reconstructed sig
((r>0).shift(1) from the saved book-return CSVs): leak dict published, leak=False, leak_ok=True,
composite pass=False on ALL THREE books (C9/C3/C1; sp_corr -0.0078/+0.0019/-0.0152 vs 0.20 bar).
DISCLOSURE: that reconstruction is mechanically correlated with returns and makes its lag_scan
meaningless - superseded by Step B with the TRUE positions. Step B: regenerated C9 through the
unmodified lib_r5.run_config (v2_battery wrapped read-only to capture its sig= argument) - engine
regen reproduces the R5 record EXACTLY: **SR +0.590 (record +0.590), halves +0.788/+0.554
(record +0.79/+0.55), negyr 3, corr +0.0271 (record +0.027)**, n=3951 2011-01-18..2026-09-04,
2402 nonzero positions. True-sig flipped-default probe: **leak=False, leak_ok=True,
same_period_corr +0.0293 (p 0.066) - far under the 0.20 leak bar; composite pass=False**.
(lag0-argmax False is correct-not-a-flag here: the argmax condition only bites when |sp_corr|>=0.20.)
Convention note (not a defect): gates.run's internal daily SR prints +0.493 vs the engine's +0.590
on the same book - different estimator convention; BOTH fail the SR>=1.0 gate identically and the
composite verdict is unchanged.
CONCLUSION: **the Step-2 flip is verdict-neutral on the R5 record, as V2 s6 claims** - every R5
book stays composite-False with a published, fail-closed leak dict under the new default. The R5
9/9-FAIL verdict survives the flip. Also confirms the R5 charter discipline ("pass sig= and
leak_check=True explicitly") was the right call: R5's v2_battery already passed both explicitly, so
no R5 number ever depended on the default.

### Charter compliance
No new corner executed (none pre-registered for this re-fire; the R5 corner is closed 9/9). Nothing
passed gates; sleeves/ untouched (stays empty); champion read-only; NO bt/ or campaign/*.md file
touched by me (bt/ was verified read-only). One new artifact: verify_flip_r5.py (Step-A probe,
saved for repro; Step B inline heredoc, recipe recorded above). DEAD_IDEAS.csv untouched by me
(working-tree diff belongs to other agents; the missing trader-count-breadth row remains the
coordinator's append per v1 item 5 - suggested row text unchanged from my 09:0x entry).
Repro: python3 campaign/agents/chief/coord/HUNT_COT2/verify_flip_r5.py; pytest from world-trader
root: campaign/bt/tests/ (403 passed); from HUNT_COT2/: test_lib_hunt*.py (58 passed).

ROUND 5 DONE


====================================================================
## ROUND 6 (2026-09-08 ~13:0x CST) - CONSOLIDATION round: fraud-catch cross-verification
of HUNT_CMDT2 + HUNT_CREDIT2 R5 verdicts (charter a) + DEAD_IDEAS positioning curation
(charter b). Family stays CLOSED (charter c: no new corner run; none surfaced).

READ-FIRST done: coord/GATES_CONTRACT_V2.md in force (Step-2 flip banner: leak_check default
ON, commit 539f50e) + DEAD_IDEAS.csv recounted MYSELF at round start: 137 data rows (charter
said "137 at R5-end" - exact match; 138 by mid-round, 139 when HUNT_CMDT2-R6CUR appended
concurrently, 142 after my 3 append-only curation rows + one fused-row repair, see below).

### (0) Champion of record re-verified (prereq for every corr below)
GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha256 4358dfab95679b97... EXACT MATCH (shasum).
Own-code recompute: n=4805 2008-03-31..2026-08-27, geometric ann 37.1954 pct (arithmetic
32.1373 - the 37.2 headline is geometric cagr, convention confirmed), SR 3.1810, MDD -6.6922,
0 neg years, worst year +7.31 pct. All five headline stats reproduce to 4dp.

### (a) FRAUD-CATCH: 72/72 sleeve CSVs field-exact; verdicts STAND
Own code (no imports of their libs; stats from raw date,ret CSVs; corr vs champion of record):
verify_r6_cmdt2.csv (28 rows) + verify_r6_credit2.csv (44 rows), saved in this dir.
  - CMDT2 R5 propane (28): my SR range -0.196..+0.370, meta -0.196..+0.370 - 0/28 mismatches
    on SR/negyrs/worstyr/corr_champ/n at reported rounding. 0 sleeves SR>=1.0 (best trend w21
    LO vt 0.370, H1 0.60/H2 0.16 fail halves, 8 negyr); 0/28 pass halves; 0/28 negyrs<=2.
    max |corr_champ| 0.053 (prose says <=0.052 - rounding of -0.05306, not a defect).
  - CREDIT2 R5 credit-carry (44): my SR range -1.878..+0.112 - 0/44 mismatches. 0/44 SR>=1.0,
    0/44 halves, 0/44 negyrs<=2. run_log.txt head-to-tail matches my recompute line-for-line
    (44/44 gates lines). |v2corr|<=0.15 in 28/44 metas; run_log corr|<0.15:True count = 28 -
    the FINDINGS prose "26/44" is a stale count (28 is the artifact-true number; verds unchanged).
  - PIPELINE RE-EXECUTION (stronger than CSV recompute): re-ran CREDIT2's own
    campaign/scripts/HUNT_CREDIT2_round5.py end-to-end OFFLINE with save_sleeve no-op'd
    (their files untouched; script is fully offline, data staged in their work_r5):
    44/0 scorecard reproduced, best cell CRED5_nfci_credit_k26_i_vt v2_sr=0.2063.
    The scr_p=0.185 scramble claim - quoted in their FINDINGS but serialized in NO meta or
    log - is CONFIRMED: my re-run of their battery printed scr_p=0.185 on that cell
    (evidence r6/credit2_rerun_battery.json + r6/rerun_credit2_r5.py).
  - COST + ERA claims re-derived: cpois_w21_stress_vt net SR -1.878 (claim -1.88) vs gross
    -0.179 (claim -0.18) - cost-impact claim exact. Best-cell era split on the GROSS book:
    +0.206 (2008-12) / -0.246 (2013-19) / +0.056 (2020-26) vs their claims
    +0.21/-0.25/+0.06 - exact (my earlier calendar-year recompute of the NET CSV book
    +0.663/+0.157/-0.454/-0.040 was the wrong slice; the gross book is the claim's basis).
  - Sign-mirror check: nfci_credit_k26 v2sr +0.2063 (invert=True) vs -0.2063 (False) with
    mirrored corr -0.1752 - symmetric noise around zero, as disclosed.
  - Independent block-scramble (my own, block=20, 2000 draws, circular-shift) on the best
    cell's published book: p=0.487 - their book shows NO scramble-resistant signal either
    way; direction consistent with their fail verdict.

### CATCH 1 (escalated): DEAD_IDEAS row 126 (HUNT_CREDIT2-R5) carries RUN-1 numbers
Row 126 evidence: "mortgage-gap RV best SR 0.62 H2 0.18; NFCI gates best 0.4-0.5 halves
split; CP-OIS stress best SR 0.52 3 negyr". NO surviving artifact matches: sleeves+run_log
give mortgage family best SR -0.739 (CRED5_mortgap_w252_mom_vt), nfci best +0.112,
nfci_risk +0.079, cpois best -0.826, negyrs 13-25 (never 3). Root cause: CREDIT2's FINDINGS
disclose run-1 had the weekly-intersection/TB3MS alignment defects (their TDD RED phase) and
the verdict was re-run - but the DEAD_IDEAS row was written from the SUPERSEDED run-1 output
and never refreshed. VERDICT UNCHANGED and STRONGER (their re-run is strictly worse).
Row appended (append-only), not edited: see row 141, source HUNT_COT2-R6.

### CATCH 2: DEAD_IDEAS row 129 (HUNT_CMDT2-R5) quotes superseded distorted-battery SRs
Row 129: "best trend w21 LO vt SR 0.465" and "spread MR family best local w63 z2 SR 0.609".
0.465 = meta 'v2:' battery sr (0.464) NOT the held book (CSV+meta+run_log local SR 0.370);
0.609 = the self-caught bp_ok=True ARTIFACT (meta 'v2:' sr=0.607) whose corrected value is
-0.017 local. Both artifacts were already disclosed+superseded by CMDT2's own 'v2_corrected:'
lines; the DEAD_IDEAS cell conflated battery-sr with book-sr. Corrected-battery v2sr range
re-derived from their own json (/tmp/cmdt2_r5_v2_correct.json): -0.185..+0.422, n=28.
VERDICT UNCHANGED (0/28 either way). Row appended: see row 142, source HUNT_COT2-R6.
NOTE: HUNT_CMDT2-R6CUR appended a row with the same catch CONCURRENTLY (row 139-adjacent,
"row 129 headline SR-convention correction") - independent convergence on the same defect;
my row 142 + their row 139 are consistent (mine adds the 0.465 battery-vs-book conflation
they did not flag; theirs adds the ledger-duplicate finding I did not audit).

### (b) Curation sweep of the positioning family rows (grep cot|tff|cit|position|crowd)
Rows verified for exact-numbers + repro-path (all PRE-EXISTING rows untouched):
 63/97 (COT 9-mkt R1): numbers re-checked vs my own R1 FINDINGS (sw-follow lb12 SR +0.287
   halves -0.14/+0.58 negyr 4 scramble 0.652 - all present); repro scripts exist:
   campaign/scripts/cot_positioning_hunt.py EXISTS.
 53/98 (TFF): repro path campaign/agents/loop_team/HUNT_TFF/run_tff.py EXISTS.
 49/99 (CIT): campaign/agents/loop_team/HUNT_CIT_AG/cit_ag.py EXISTS.
 75/76/84 (CMDT2 COT-gated mom): campaign/scripts/HUNT_CMDT2_round1/2/3/5.py EXIST.
 87/88 (COT2-R2 horizon/TFF/CIT/overlays): my own R2 artifacts (55/55 fail; numbers match
   my FINDINGS R2 section). 100 (COT_ITER11) repro EXISTS.
 128/129 (CMDT2-R5 propane): sleeves+metas+run logs verified this round (catch 2 above).
 126 (CREDIT2-R5): verified this round (catch 1 above - row corrected append-only).
 130 (CRYPTO2-R5 crypto funding): work_r5/hedged_results_v3.json spot-checked: HEDGE_BTC_W
   net_sr 1.628, ann 11.61, neg 1, worst -0.82, corr 0.079, scr_p 0.0, leak c0 0.177
   (<0.20 bar, correctly leak_ok=true), bp ok=true - row's numbers EXACT vs artifact.
 137 (RES_BASIS-R1): repro path campaign/team/agents/RES_BASIS/run_hunt.py EXISTS (dir
   hunt_r1.py/robust_r1.py/fine_z.py etc. present). NOTE row 137's evidence cell was
   counted from row 137 = RES_BASIS ho_brent standalone-V2-PASS row (post-concurrent-append
   shift; index drift acknowledged - content verified, not row number).
Verdict: the positioning rows are curation-CLEAN except catches 1-2 (both now carry
append-only correction rows). Nothing deleted or edited.

### (c) Charter compliance
Family CLOSED - no new COT corner executed, none surfaced (R1-R5 55/55 + trader-count
closure stands; no data-backed gap absent from DEAD_IDEAS). No bt/ or campaign/*.md file
touched. Champion read-only (sha re-verified unchanged). Their files read-only throughout:
save_sleeve was monkeypatched to a no-op inside MY wrapper only (r6/rerun_credit2_r5.py);
their sleeves/ dir untouched (ls -la mtimes predate this round).
DEAD_IDEAS append-only + one REPAIR: a concurrent writer (HUNT_CMDT2-R6CUR) appended a row
with no trailing newline between my read and my append, fusing their source field with my
row-140 idea field (7-column row 139). I split it back into their intact row + my row
(no content lost either side; file re-validated 4 columns x all rows). This is the
concurrent-append hazard v1 item 5 warns about - recommend appenders end with a trailing
newline and re-read-before-append.

Artifacts (all in coord/HUNT_COT2/ unless noted): verify_r6_cmdt2.csv, verify_r6_credit2.csv
(own-code recomputes), r6/rerun_credit2_r5.py + r6/credit2_rerun_battery.json (their
pipeline, my run, scr_p captured), DEAD_IDEAS rows 140-142 (HUNT_COT2-R6), champion sha
re-verified. No sleeve saved: nothing passed (nothing was expected to - both verdicts stand).

ROUND 6 DONE

========================================================================
## HUNT_COT2 — ROUND 7 (2026-09-08 19:0x-19:2x CST) — audit round: SECTOR2-R6 nasdaq_history fix verification + placebo 200/200 claim re-run + DEAD_IDEAS 143-145 spot-check + ledger recount
========================================================================
READ FIRST done: GATES_CONTRACT_V2.md in force (V3 per-class placebo noted as PROPOSAL, not
depended on either way); DEAD_IDEAS.csv recounted at round start (145 data rows, dynamic by
design). Champion pin untouched this round (audit-only; no bt/ or campaign/*.md writes except
this FINDINGS + my own agent dir). No dead-family re-test; no new COT corner (family CLOSED,
none pre-registered - charter says so explicitly).

R7 (a)(i) nasdaq_history fix audit — VERDICT: CLAIMS CONFIRMED, fix is sound, one scope note.
  - Their 5 tests, my run, repo root: "5 passed in 1.66s"
    (python3 -m pytest campaign/agents/chief/coord/HUNT_SECTOR2/tests_tdd_r6.py -q)
  - Their RED-first claim re-verified with my own run of their red_run_head.py harness
    (read-only; exec's `git show HEAD:./tools/wt/sources.py` in-memory, touches nothing):
    "3 failed, 2 passed in 1.02s" / "RED RUN pytest exit code: 1 (expected 1)" — the two
    cap-truncation tests + the unparseable-oldest-date test fail under HEAD semantics exactly
    as claimed; the 2 healthy-window guards pass under both semantics by design.
  - LIVE probe of the R4-era failure mode, my own driver against the real API:
      XLK days=6500: FAIL-CLOSED | truncated history: asked 6500 bars from 1998-03-09, served
        2514 bars from 2016-09-06 - endpoint ignores fromdate beyond its archiv[e cap]
      XLK days=3000: FAIL-CLOSED | served 2514 bars from 2016-09-06
      XLK days=2600: FAIL-CLOSED | served 2514 bars from 2016-09-06
      SPY days=400: OK n=440 first=12/03/2024 ; days=200: OK n=226 first=10/13/2025 ;
      days=60: OK n=72 first=05/26/2026 ; err=None everywhere on healthy asks
    (all three R5 cap numbers reproduced exactly, now carried in the error text).
  - MY OWN adversarial cases (tests_r7_nasdaq_audit.py, written before running, 3 tests,
    no shared modules with SECTOR2): "3 passed in 1.32s". They isolate the fix's two
    coverage arms separately — which their 5 tests do not:
      (1) gap-arm boundary: serve starting EXACTLY max(30, 0.25*days) after frm PASSES
          (strict > is correct); +1 calendar day FAILS. Boundary verified tight, no off-by-one.
      (2) bar-count arm: on-time window start (D[0]=frm) with 0.98*days-1 bars FAILS;
          exactly 0.98*days bars PASSES.
      (3) OBSERVATION (recorded, not a defect gate): only the OLDEST served bar's date is
          parse-validated; a corrupt mid-series date flows through into the returned dict.
          Pre-existing semantics, now documented. If any consumer ever needs per-bar date
          validity, that is a separate ask — not a regression of this fix.
    AUDIT FRITION found while building (2): the two arms are COUPLED for short serves ending
    today (a 0.97*days-bar serve ending today necessarily starts ~0.23*days+10 after frm, so
    the GAP arm fires for days>=88 even when testing the bar arm). Fail-closed direction is
    safe either way (OR-logic), so this is documentation, not a bug.
  - Regression sweep on healthy callers re-run: test_options_cboe.py "ALL GREEN" exit 0
    (incl the 'removed _nasdaq_rows' pin); rviv revival suite "8 passed in 0.11s"; cumulative
    SECTOR2 tests_tdd{,_r3,_r5,_r6}.py "44 passed in 5.12s" — all match their FINDINGS.
  - sources.py git state as they disclosed: working-tree modified, fix uncommitted (git log
    HEAD file = c3c8730 'Add intraday ORB infrastructure'). Coordinator to commit; the three
    co-resident concurrent hunks (kr_history/_stooq/polygon) untouched by me.

R7 (a)(ii) placebo_direction_seedsweep.py re-run — VERDICT: 200/200 CONFIRMED verbatim;
MY OWN independent re-derivation confirms the DIRECTION but finds the placebo MAGNITUDE is
cost-convention-sensitive (noted for the record; changes no verdict).
  - Their script verbatim (my run): "overlay SR=0.8205 fire_frac=0.223 nflip=300 n=2047";
    seeds 0..4 all "overlay beats 200/200 (p=0.000)"; placebo SR mean +0.1957..+0.2121,
    dSR mean -0.6084..-0.6248 — exactly inside the FINDINGS-quoted +0.196..+0.212 / ~-0.61.
  - MY OWN code (r7_placebo_own_derivation.py: own z-build from the 7 raw wiki_attention
    CSVs, own ddof-0 SR, own cost application; overlay SR 0.8207 vs their 0.8205 = the
    ddof(0) vs ddof(1) convention, exact factor sqrt(2047/2046)), own placebo scheme =
    CIRCULAR PERMUTATION of the real gate vector (exact flip-count match, stricter than
    their Bernoulli+nflip-tolerance loop): 987/1000 draws beaten across 5x200
    (per-seed 196..199/200, empirical p<0.001), placebo dSR max +0.2259 never approaches 0.
    DIRECTION identical: matched random de-risk timing is destructive on this book.
  - ATTRIBUTION of the magnitude gap (their +0.20 vs my +0.45 placebo mean): their
    nflip-matching loop NEVER BINDS — 0/200 draws matched in my replication of it; a plain
    Bernoulli(0.223) draw over n=2047 carries mean ~709-710 gate flips vs the real gate's
    300 (std 26, min 590 in my sweep), so their placebo gates pay ~2.4x the allocation cost
    of the real gate (6.4bps on |diff(scale)|). Re-running THEIR construction under MY SR
    code: placebo SR mean +0.1966 (reproduces their +0.20); MY flip-matched permutation:
    +0.4559; gap -0.2593 = pure flip-count/cost asymmetry. This is a placebo-construction
    convention artifact, NOT a leak and NOT a direction issue: under EITHER convention the
    overlay beats ~200/200 or ~987/1000 and random de-risk timing destroys SR. The honest
    negative disposition (admission inception_fail + single-episode halves +0.407/-1.087 +
    excl-2020 -0.979 + FAIL_SR 0.821<1.0) is untouched by any of this. Suggestion for any
    future placebo use (8h Class A): match BOTH fire_frac and flip count (circular
    permutation does both exactly) so the placebo pays the same allocation cost as the real
    gate; otherwise the placebo is conservative-inflated against the overlay.

R7 (a)(iii) DEAD_IDEAS rows 143-145 spot-check (not my rows) — VERDICT: all three carry
exact numbers + repro paths; cited artifacts exist and MATCH:
  - row 143 (HUNT_CREDIT2-R6, dead): DRALACBS n=166 / DRCLACBS n=158 re-counted from
    tools/quant/data/more_fred/ EXACT as claimed.
  - row 144 (CAMP_SHORT-R6, verified): work_r6/{r6_repro_borrow.py,r6_repro_cost.py,
    r6_scalar_variants.py,r6_borrow_repro.json,r6_cost_repro.json} all present;
    r6_borrow_repro.json verdicts=75, match=75, 0 mismatches; r6_cost_repro.json verdicts=46,
    match=46, 0 mismatches -> "75/75 checks match" + "46/46 checks match" VERBATIM TRUE.
    Nit, no action: the row's "worst dev 8e-15" describes the exact-recompute subset; the
    JSON's largest abs_dev overall is 0.00479 (B5.QAxasts, theirs=2.34, tol=0.005) — those
    top-dev entries are checks against PUBLISHED ROUNDED values, a distinct class from the
    exact-recompute subset the 8e-15 claim describes. Consistent, not a mis-statement.
  - row 145 (HUNT_SECTOR2-R6, dead): work_r6/r6_bugfix_rerun.json matches the row's every
    number — probes XLK 6500/3000/2600 fail_closed=True served 2514 from 2016-09-06;
    wiki_attention 4086 rows sha256_16 609cca25738461c0 vintage_match=True; admission 0/4
    admissible verdict CORNER_DEAD_ON_DATA_ADMISSION; sleeve n=2047 span 2018-06-20..2026-08-12
    base 0.679 overlay 0.821 dSR +0.141 placebo_p 0.000 halves [+0.407,-1.087] excl-2020
    -0.979 fire_frac 0.223 flips 300 verdict FAIL_SR|NOT_HUNT_ELIGIBLE; leak dict published
    (same_period_corr +0.0844, p 0.00013, lag-0 NOT argmax -> leak_ok True, V2 6b-consistent);
    corr_champ -0.0629 as quoted (-0.063); fresh crawls recorded UNMEASURED (45s timeout /
    conn reset), not folded into window evidence — honesty rule as stated.
  No thin rows; no corrections to append; escalation not required.

R7 (b) LEDGER RECOUNT + well-formedness (csv-parser, not line-count):
  - 145 data rows at round start (19:0x), 145 at this append (no concurrent appends landed
    mid-round this time), header [idea,status,evidence,source], 0 rows with field count != 4,
    0 rows with empty idea/evidence/source, 0 byte-identical (idea,source) dup pairs,
    trailing newline present, 60963 bytes, file sha256_16 97bd6b603a1aa09c at read.
  - Row count lineage: charter said 145-146 at R6-end; my recount 145 = consistent (the 146
    figure counts the header line).

VERDICT SUMMARY: SECTOR2-R6's nasdaq_history fix DOES what its tests claim (5/5 green,
RED-first reproduced 3F/2P, live R4-era failure mode now fails closed with the exact R5 cap
numbers in the error, healthy callers untouched 8+44+ALL GREEN); the 200/200 placebo claim
reproduces verbatim and my independent stricter re-derivation confirms the direction
(987/1000, p<0.001) while documenting the placebo's cost-convention sensitivity; DEAD_IDEAS
143-145 verbatim-verified with zero thin cells; ledger well-formed at 145 rows. Zero fraud
found. Nothing adopted, nothing passed, nothing re-opened; family stays CLOSED.

ARTIFACTS (all in coord/HUNT_COT2/): tests_r7_nasdaq_audit.py (my 3 adversarial cases,
pass 3/3), r7_placebo_own_derivation.py (own-code direction re-derivation + attribution runs
inline in the transcript). No shared module touched; no bt/ or campaign/*.md write; champion
sha 4358dfab95679b97 untouched (not re-pinned this round — audit round, no champion-path
command run).

ROUND 7 DONE
