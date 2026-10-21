# HUNT_MACRO2 FINDINGS

## ROUND 1 (2026-09-07) — multi-series composite macro premia: ALL DEAD (0/17 variants pass)

Charter families (a) credit-cycle, (b) activity-nowcast, (c) policy/real-rate, (d) liquidity,
each PIT-timed (released-as-known: monthly ref-month m visible at m_end + pub_days calendar;
daily/weekly series +1/+5 cal d), T+1 shift(1), 6.4bps one-side on FULL |dW| day-1 seeded,
borrow 0.5%/yr on shorts, margin 4.5%/yr on gross>1, VT10% trailing-only clip<=3.0.
Prior-session state on entry: work_r1/HUNT_MACRO2_round1.py + 8 TDD tests existed but were RED
(2 failures) and FINDINGS.md did not exist (R1 was never executed or logged).

### Framework fixes first (TDD red -> green, 8/8 pass)
- ENGINE BUG (genuine, fixed in HUNT_MACRO2_round1.py): net_of() paired W,R via
  R.reindex(columns=W.columns).fillna(0) — when the signal frame and returns frame share NO
  labels ('sig' vs 'qqq') this silently zeroed gross -> every sleeve read as PURE COST CHURN
  (test data: net = -0.00128/day exactly = 6.4bps x 2.0 turnover, gross identically 0). Same
  bug broke the scramble permutation (Wp*Re also all-NaN). Fix = pair_wr(): by-name on full
  label overlap, positional 1:1 on disjoint sets, RAISE on partial overlap (fail-closed).
- TEST-SPEC BUG (fixed in test_macro_r1_no_lookahead.py): test_net_of_multi_leg_column_order
  expected +0.03/day but its own data gives 1*0.02 + (-1)*0.01 = +0.01 gross (comment assumed
  b=-0.01) minus borrow 0.5%/252 on the 1.0 short minus margin (2-1)*4.5%/252 = 0.0098015873
  = exactly what the engine produced. Engine was contract-correct; expectation was wrong.
  test_net_of_column_name_mismatch also assumed 'weights static -> no costs after day1',
  false for +/-1 flip weights; now asserts net == We*R - turnover - borrow exactly.
- GATE HONESTY PROBE: scramble p=0.000 on ALL 17 sleeves is VACUOUS here, not evidence:
  permuted books churn 3.16 bps/d vs real book 0.21 bps/d (15x) -> scramble SR ~ -18 is pure
  cost, so 'real > 95th pctile' passes for ANY low-churn book regardless of signal content.
  Flagged so nobody reads scram_p=0.000 as signal validation; it cannot rescue an SR<1 sleeve.
- CONTRACT ITEM 4 was unmet (save_sleeve defined, never called -> zero sleeve CSVs). Saved
  4 representative sleeves to sleeves/ with .meta (econ rationale + result + config).

### Exact numbers (FULL window, net of all costs; SR gate needs >=1.0, halves >=0.5 each)
| variant | n | SR | ann | H1 | H2 | negyr | worst | corr_champ | pass |
|---|---|---|---|---|---|---|---|---|---|
| credit_long_hist->QQQ | 5000 | 0.26 | +2.1% | 0.35 | 0.16 | 8 | -16.6% | 0.072 | NO |
| credit_long_hist->LQD | 5000 | -0.06 | -1.1% | 0.20 | -0.33 | 10 | -16.0% | 0.114 | NO |
| credit_long_hist->HY/IG | 5000 | -0.17 | -2.0% | -0.16 | -0.17 | 11 | -21.3% | -0.091 | NO |
| credit_dbaa_only->QQQ | 5000 | 0.28 | +2.3% | 0.53 | 0.05 | 9 | -10.1% | 0.043 | NO |
| credit_dbaa_only->LQD | 5000 | -0.11 | -1.5% | 0.18 | -0.38 | 9 | -25.3% | 0.097 | NO |
| credit_dbaa_only->HY/IG | 5000 | -0.23 | -2.7% | -0.31 | -0.13 | 13 | -28.5% | -0.111 | NO |
| credit_+hyoas23+->QQQ | 5000 | 0.21 | +1.6% | 0.35 | 0.05 | 8 | -16.6% | 0.071 | NO |
| credit_+hyoas23+->LQD | 5000 | -0.07 | -1.1% | 0.20 | -0.34 | 10 | -16.0% | 0.113 | NO |
| credit_+hyoas23+->HY/IG | 5000 | -0.19 | -2.3% | -0.16 | -0.23 | 12 | -21.3% | -0.088 | NO |
| activity->QQQ | 5000 | -0.23 | -2.8% | -0.02 | -0.43 | 12 | -15.6% | 0.048 | NO |
| activity->DBC | 4699 | 0.13 | +0.8% | 0.00 | 0.25 | 8 | -15.8% | 0.036 | NO |
| policy_dfii->TLT | 5000 | -0.40 | -4.6% | -0.74 | -0.03 | 14 | -23.8% | -0.027 | NO |
| policy_dfii->IEF | 5000 | -0.69 | -6.9% | -1.01 | -0.36 | 15 | -26.4% | -0.022 | NO |
| policy_breakeven->TLT | 5000 | -0.03 | -0.8% | 0.09 | -0.15 | 10 | -18.2% | 0.073 | NO |
| policy_breakeven->IEF | 5000 | -0.17 | -2.1% | 0.05 | -0.39 | 12 | -20.8% | 0.058 | NO |
| liq(WALCL-RRP)->QQQ | 5000 | 0.26 | +3.1% | -0.53 | 0.64 | 6 | -24.4% | -0.019 | NO |
| liq(WALCL-RRP)->DBC | 4699 | 0.23 | +2.5% | 0.34 | 0.15 | 6 | -21.1% | -0.023 | NO |

Gate-by-gate: SR>=1.0 FAILED by every variant (best = credit_dbaa_only->QQQ SR 0.28, 3.6x
short of the bar). Halves>=0.5 each FAILED everywhere (best H1 0.53 pairs with H2 0.05 —
the signal decays or flips; liquidity is the extreme: H1 -0.53 -> H2 +0.64 pure regime flip).
Yearly FAILED (6-15 neg years vs <=2 allowed). |corr|<0.15 vs champion PASSED everywhere
(0.019-0.114) — decorrelation was never the problem; edge was. HY-OAS (BAMLH0A0HYM2) confirmed
truncated by FRED to 2023-09-05..2026-09-03 (788 rows, verified on disk), so the charter's
"long-history credit composite with HY OAS" is untestable back-history; the 2023+ variant
changes nothing (SR 0.21 vs 0.26 without it).

### Conclusion
ALL FOUR charter composites DEAD standalone. Best of 17 = SR 0.28 (credit_dbaa_only->QQQ),
3.6x below the SR>=1.0 gate; every family also fails halves + yearly. This CONFIRMS and
extends the prior macro negatives (NFCIRISK gate SR 0.90, gold x macro maps, WALCL>median
gate, TIPS real-yield reversion): no multi-series FRED macro composite tested here produces
a tradable standalone premium after honest PIT timing + full costs. Recommendation: macro
data is only useful to this campaign as a defensive OVERLAY, not as a standalone sleeve.

### DEAD_IDEAS.csv rows (submitted to coordinator for append)
multi-series FRED composites (credit/activity/policy/liquidity x 17 variants),dead,"best credit_dbaa->QQQ SR0.28 ann2.3% (9 negyr, H2 0.05); activity SR -0.23..0.13; policy_dfii->IEF SR -0.69 (15 negyr); liq H1 -0.53/H2 +0.64 regime flip; all fail SR>=1.0+halves+yearly; |corr|<0.15 everywhere; scramble gate vacuous (permuted churn 15x real)",HUNT_MACRO2

EVIDENCE: campaign/agents/chief/coord/HUNT_MACRO2/work_r1/HUNT_MACRO2_round1.py (8/8 TDD
tests green: pytest campaign/agents/chief/coord/HUNT_MACRO2/tests/ -q); sleeves/*.csv + .meta
(4 files); reproduction = python3 campaign/agents/chief/coord/HUNT_MACRO2/work_r1/HUNT_MACRO2_round1.py

ROUND 1 DONE


## ROUND 2 (2026-09-07) — FRED macro OVERLAYS on the champion: 4/28 variants PASS (MDD arm)

Charter round 2 pivots to defensive overlays on GOAL100_RAWEW13v2_WEIGHTED_GEAR16
(ann 39.85% SR 3.296 MDD -6.84% 0-neg-years gross exactly 1.6; rebuilt byte-identical,
max|rebuilt-committed|=1e-16, gross max 1.600000 days>1.6 = 0). Acceptance = ann >= +0.3pp
OR MDD >= +0.5pp, WITHOUT breaking 0-neg-years, gross<=1.6, scramble-stable, PIT lags.

### Session state on entry + framework repairs (all TDD)
- work_r2/ contained ONLY a 202-byte __pycache__ stub (prior session died before writing
  HUNT_MACRO2_round2.py); tests/test_macro_r2_overlays.py existed and pre-specified the API
  but every test was silently SKIPPING (importorskip). Recovered spec from the test file.
- 7 TEST-SPEC BUGS repaired in test_macro_r2_overlays.py (never executed before -> wrong
  expectations; each fix documented inline): (1) pit_daily 'd[t]==print[t]' asserted same-day
  visibility = the exact leak the docstring forbids -> day t sees print t-1; (2) TOTALSL test
  expected NO value visible before m_end+40d but the PRIOR ref month is legitimately visible
  -> assert only the new ref-month value is absent; (3) USREC test expected flag 0.0 as the
  first value at/after Dec+365d but Nov flag (0.0) becomes visible 2009-11-30 and Dec flag
  (1.0) lands EXACTLY on 2009-12-31 -> pinned visibility sequence; (4) VIX 'sustained 21d'
  pinned cases (20 obs at 40 then 0 must not fire; 21x31 must) are ALL-21-OBS semantics =
  rolling(21).min()>30 — the stale 'mean' gate computes 20*40/21=38.1>30 on case 1 and CANNOT
  satisfy it -> mode='sustained' added, mean kept as a softer variant; (5) T+1 test used an
  all-zero baseline m so day-300 went flat (not 'identical to champion') -> baseline 1.0 with
  single-day 0.6 dip; (6) same test expected day t+2 == champion after the dip-back, but
  exposure-returning-to-full still costs |0.4|*1.6*6.4e-4 = 4.096bp honest exit turnover ->
  pinned c_t - cost; (7) turnover test expected ov[4]==-cost exactly while the sibling
  margin test co-specifies the flat-book pnl stream = +MARGIN_CONST/day -> consistent
  identity 0.6*MARGIN_CONST - cost (both tests pin the same construction).
- ENGINE SIGN BUG (mine, caught before acceptance): d_mdd computed as pc-po, but
  bt.metrics.max_dd returns NEGATIVE numbers -> every MDD improvement scored as a penalty.
  First run mislabeled all 28 variants FAIL; fixed (d_mdd = po - pc, docstring now states
  the sign convention) -> 4 variants correctly meet the raw MDD arm.
- 25/25 tests green (8 r1 + 17 r2): pytest campaign/agents/chief/coord/HUNT_MACRO2/tests/ -q

### Construction (fail-closed, PIT)
Book-level overlay: m_t in {scale, 1.0} decided at close t, held from t+1; exact decomposition
ov_t = held_t*(c_t + MARGIN_CONST) - |d held_t|*1.6*6.4e-4 - max(held_t*1.6 - 1, 0)*4.5%/252.
m==1 reproduces the committed champion to <1e-12 (identity tests). Slot-level variant scales
only RISK_ON slots (C5ng C5ngsum carryv2 QAxasts dualmom diescrack CFX4 — classification
pre-committed in the test file BEFORE evaluation); exact full |d(M*Wg)| turnover.
PIT lags: USREC m_end+365 cal d (charter; NBER ex-post dating); TOTALSL m_end+40 (G.19 ~day-7
of m+1 padded); T10Y2Y/VIXCLS/T5YIFR print t visible t+1. T+1 everywhere.

### Trigger frequencies (champion window 2008-03-31..2026-08-27)
USREC-3mo 351d (7.30%, 2009-04-28..2010-08-30 only) | VIXsus21 218d (4.54%) | VIXmean21 418d
(8.70%) | T10Y2Y z63<-2 373d (7.76%) | TOTALSL yoy<0 673d (14.01%) | T5YIFR rising126 54.28%.

### Exact numbers (deltas vs champion ann 39.85% / MDD -6.84% / SR 3.296; all neg=0, gross<=1.6)
| variant | on | ann | dAnn | MDD | dMDD | SR | p(scram,MDD) | verdict |
|---|---|---|---|---|---|---|---|---|
| book USREC x0.6 | 7.30% | 38.65% | -1.198pp | -6.84% | +0.000 | 3.23 | - | NO (no dd to relieve; USREC fires only 2009-10) |
| slot USREC x0.6 | 7.30% | 39.58% | -0.270pp | -6.84% | -0.000 | 3.28 | - | NO |
| book USREC x0.0 | 7.30% | 36.46% | -3.390pp | -6.84% | +0.000 | 3.09 | - | NO |
| slot USREC x0.0 | 7.30% | 39.17% | -0.676pp | -6.84% | -0.000 | 3.26 | - | NO |
| a6r7 tilt rising x0.0/x0.5 | 54.28% | 39.81/39.83% | -0.040/-0.020pp | -6.84% | ~0 | 3.30 | - | NO (a6r7 flat at every trigger day; tilt is cosmetic) |
| a6r7 tilt falling x0.0/x0.5 | 45.72% | 39.82/39.84% | -0.031/-0.016pp | -6.84% | +0.001 | 3.30 | - | NO |
| book T10Y2Y z63<-2 x0.6 | 7.76% | 37.80% | -2.054pp | -5.73% | +1.114pp | 3.24 | 0.015 | **PASS (MDD arm)** |
| slot T10Y2Y x0.6 | 7.76% | 39.50% | -0.347pp | -6.83% | +0.006pp | 3.28 | - | NO (relief is in DEF slots) |
| book T10Y2Y x0.0 | 7.76% | 34.31% | -5.538pp | -5.73% | +1.114pp | 3.02 | 0.005 | PASS-raw but dominated by x0.6 |
| slot T10Y2Y x0.0 | 7.76% | 38.98% | -0.869pp | -6.83% | +0.014pp | 3.24 | - | NO |
| book VIXsus21 x0.6/x0.0 | 4.54% | 38.22/35.50% | -1.63/-4.36pp | -6.84% | 0.000 | 3.32/3.20 | - | NO (champion max-dd window has no 21d-sustained VIX>30) |
| book VIXmean21 x0.6/x0.0 | 8.70% | 36.57/31.16% | -3.28/-8.69pp | -6.84% | 0.000 | 3.62/3.56 | - | NO (SR up to 3.62 but MDD unchanged -> fails both arms) |
| **book JOINT x0.6** | 12.13% | 36.19% | -3.662pp | -5.46% | +1.376pp | 3.26 | 0.000 | **PASS (MDD arm)** |
| book JOINT x0.0 | 12.13% | 30.14% | -9.708pp | -5.24% | +1.602pp | 2.90 | 0.000 | PASS-raw but 9.7pp ann cost |
| slot JOINT x0.6 | 12.13% | 39.38% | -0.467pp | -6.83% | +0.006pp | 3.27 | - | NO |
| book TOTALSL x0.6/x0.0 | 14.01% | 38.09/34.72% | -1.76/-5.13pp | -6.84% | 0.000 | 3.21/2.98 | - | NO |
| slot TOTALSL x0.6/x0.0 | 14.01% | 39.32/38.52% | -0.53/-1.33pp | -6.84% | 0.000 | 3.27/3.22 | - | NO |
| (b)+(c)+(d) grid x0.9..x0.6 for T10Y2Y/JOINT | - | - | -0.51..-9.71pp | - | +0.68..+1.60pp | - | - | monotone trade; x0.9 T10Y2Y = +0.68pp MDD at -0.51pp ann |
Scale grid (robustness, book): T10Y2Y x0.9 +0.677pp MDD / -0.509pp ann; x0.8 +1.009 / -1.018;
x0.7 +1.110 / -1.527; x0.6 +1.114 / -2.054. JOINT x0.9 +0.677 / -0.912; x0.8 +1.296 / -1.822.
Param plateau (T10Y2Y gate, book x0.6): zthr x N in {-1.5,-2.0,-2.5} x {42,63,126} -> 7/9
neighbors keep dMDD >= +0.5pp (only z=-2.5 with N=42/126, 2.2-2.6% on-freq, loses relief);
dAnn stays in [-4.4, -0.6]pp. Not a single-point artifact.

### Mechanism (brutal honesty)
Champion max-dd is a 4-day June-2018 episode (peak 2018-06-19, trough 2018-06-25, -6.84%),
and its slot decomposition is 96% ENERGY-BASIS REVERSION (brwt10 -1.53%, brwt7 -1.25%,
brwt15 -0.93%, brwt5 -0.83%; all risk-on slots combined only -0.19%). So the charter's
risk-on-only slot overlay CANNOT relieve the max dd (measured: +0.006pp) — book-level
de-risking is the honest implementation of (c). T10Y2Y z63<-2 was on 67% of days in the
Jun-2018 window; JOINT also covers Dec-2008/Feb-2009 (100% of days) and pushes the binding
trough to 2026-03-17. VIXsus21 never overlaps the max-dd window (VIX>30 sustained for 21d
happened 2008-10..2009 and 2020-04, but the champion's dd there is shallow) -> 0.000 MDD
delta despite a positive SR drift. USREC (1yr lag) fires only mid-2009..mid-2010, AFTER the
recession damage — too late to help, consistent with its known ex-post nature. TOTALSL yoy<0
(14% of days) never coincides with a dd trough either.
The ann cost is real: the overlay pays ~1.8-2.7pp ann per 1pp MDD relief (ratio -1.84 T10Y2Y,
-2.66 JOINT at x0.6) because 2008/2018 crash-day alpha is being clipped along with the dd.
Scramble p-values (200 perms, MDD-metric, cost-incl): T10Y2Y x0.6 0.015, x0.0 0.005,
JOINT x0.6/x0.0 0.000 — a random same-frequency trigger rarely buys this much MDD relief.

### Conclusion
Charter round-2 acceptance is met by 4 book-level variants, all via the MDD arm
(>= +0.5pp) with ann cost; none meets the ann arm (+0.3pp) — NO macro overlay ADDS return
to this champion, extending the R1 conclusion (macro = defensive tool, not alpha).
Best risk-adjusted pass: **book T10Y2Y z63<-2 x0.6** (+1.114pp MDD, -2.054pp ann, SR
3.296->3.235, 0 neg years, scramble 0.015, plateau 7/9, gross<=0.96<=1.6). Deepest MDD
relief: **book JOINT(VIXsus21 OR T10Y2Y) x0.6** (+1.376pp, -3.662pp ann, scramble 0.000).
Both saved as sleeves/ champ_overlay_T10Y2Yz63m2_x06.csv and
champ_overlay_VIXsus21_OR_T10Y2Yz63_x06.csv (+ .meta with econ rationale, construction,
exact result, coordinator-decision status). These are OVERLAYS on the committed champion
(not replacements); adopting one is a coordinator call because it trades 2-3.7pp ann for
1.1-1.4pp MDD on a book whose -7% MDD goal is already met (-6.84%).
(b) T5YIFR tilt is DEAD in-place (a6r7 slot returns are exactly 0.0 on every trigger day —
the bond slot is flat whenever the 5y5y trend signal would act, both directions, both scales).
(a) USREC-1yr-lag, (d) TOTALSL, VIXsus21/VIXmean21 standalone: DEAD as overlays on this
book (MDD relief exactly 0.000 because the champion has no dd inside their trigger windows).

### DEAD_IDEAS.csv rows (submitted to coordinator for append)
USREC 1yr-lag recession switch overlay (book+slot riskon x0.6/x0.0),dead,"fires 2009-04..2010-08 only (after the damage): dAnn -0.27..-3.39pp, dMDD +0.000pp (champion has no dd in window); fails both acceptance arms",HUNT_MACRO2
T5YIFR 126d TIPS-vs-nominal tilt on a6r7 slot,dead,"a6r7 ret exactly 0 on all trigger days (54%/46% of window, both directions, x0/x0.5): dAnn -0.016..-0.040pp dMDD ~0; overlay is cosmetic",HUNT_MACRO2
VIXCLS>30 sustained-21d vol-regime overlay (book x0.6/x0.0),dead,"on 4.54% (2008-10, 2020-04 windows only): dMDD +0.000pp (champion dd shallow there), dAnn -1.63..-4.36pp; SR drift 3.32/3.62 but fails both arms; mean-21 variant same MDD null, dAnn -3.28..-8.69pp",HUNT_MACRO2
TOTALSL yoy<0 risk-appetite gate overlay (book+slot x0.6/x0.0),dead,"on 14.01% (2009, 2020, 2025 windows): dMDD +0.000pp dAnn -0.53..-5.13pp; fails both arms",HUNT_MACRO2
Slot-level (risk-on-only) macro de-risk overlays (T10Y2Y/JOINT x0.6/x0.0),dead,"max-dd episode is 96% brwt* energy-basis (DEF) slots -> slot overlay relieves +0.006..+0.014pp only; dAnn -0.13..-1.17pp for nothing; book-level is the honest form",HUNT_MACRO2

### PASS rows (for coordinator; charter acceptance MET, MDD arm)
champ_overlay_T10Y2Yz63m2_x06 (book T10Y2Y z63<-2 x0.6): dMDD +1.114pp (-6.84->-5.73),
dAnn -2.054pp (39.85->37.80), SR 3.235, neg=0, gross<=0.96, scramble p 0.015, plateau 7/9.
champ_overlay_VIXsus21_OR_T10Y2Yz63_x06 (book JOINT x0.6): dMDD +1.376pp (-6.84->-5.46),
dAnn -3.662pp (39.85->36.19), SR 3.258, neg=0, gross<=0.96, scramble p 0.000.

EVIDENCE: campaign/agents/chief/coord/HUNT_MACRO2/work_r2/HUNT_MACRO2_round2.py +
round2_results.csv (28 rows); tests/test_macro_r2_overlays.py (17 tests); reproduction =
python3 campaign/agents/chief/coord/HUNT_MACRO2/work_r2/HUNT_MACRO2_round2.py && python3 -m
pytest campaign/agents/chief/coord/HUNT_MACRO2/tests/ -q (25 passed)

ROUND 2 DONE


## ROUND 3 (2026-09-07) — ALFRED vintage macro-SURPRISE standalone: 0/252 PASS (DEAD); VOL2 negatives independently CONFIRMED 34/34

Session entered with the prior round-3 session dead mid-TDD: work_r3 had real ALFRED cubes
(9 series, 24,838 rows) + a 315-line engine + a 16KB test file, but the suite was RED
(6 failed / 30 passed) and round3_results.csv did not exist — never executed, same failure
mode as R1/R2 entry states.

### Data authenticity (charter 3a) — REAL, no substitutes needed
fetch_alfred_cube.py hit api.stlouisfed.org (FRED_KEY from .env.local) for 9 release series
(PAYEMS UNRATE CPIAUCSL RSXFS IPMAN UMCSENT HOUST DGORDER ICSA); all HTTP 200, no failures.
Anchor verified on-disk: PAYEMS obs 2009-11-01 first vintage = 2009-12-04 (the actual
first-Friday release), 2009-12-01 -> 2010-01-08, 2010-01-01 -> 2010-02-05. Vintages run
2005-01-01 (PAYEMS/UNRATE/CPI/RSXFS/UMCSENT/HOUST/DGORDER), 2007-12-14 (IPMAN birth),
2009-05-28 (ICSA) .. 2026-09-04. 24,838 (obs, vintage, value) rows total. No synthetic data.

### TDD repair before any evaluation (6 red -> 36/36 green)
7 TEST-SPEC bugs repaired in tests/test_macro_r3_surprise.py (each documented inline; the
file had never been executed): (1) test_first_prints_and_releases indexed the release
calendar for an obs the module's own clamp rule drops; (2) clamp fixture pinned TWO obs at
the floor but expected only one dropped + real-PAYEMS assertions compared obs dates to
vintage thresholds (cube fact: obs 2004-12-01 carries TRUE release 2005-01-07 -> kept, so
cal.index.min() == 2004-12-01, not 2005-01-21); (3) surprise-units expectation used 104.0
as prev-known for the 05-01 release — 104 is the NEXT obs's value, unpublished until 06-01
(lookahead); honest prev is 101.0 -> jump log(105/101), exactly what the engine produced;
(4) holiday fixture was 2 releases short of its own min_hist arithmetic (zero finite z) ->
rebuilt 4-obs fixture whose scored release carries z = (log(104/103)-mu)/sd = -0.72; (5) my
own sign expectation wrong at that fixture (jump +0.97% < trailing mu +1.47% -> SHORT, -1.0,
not +1.0); (6) hold=2 fixture asserted the 2nd hold day == 0 while its own comment said it
is held; (7) gate-battery too-short path asserted key 'pass_'. 2 ENGINE bugs fixed in
HUNT_MACRO2_round3.py: (a) FAIL-OPEN REPORTING — evaluate() early branches (n<500, missing
scramble inputs) reported under key 'pass_' while the main path and every reader use 'pass';
a too-short book's verdict was a key nothing read; both branches now 'pass': False;
(b) release_calendar logged the floor as first.min() AFTER filtering, naming a real release
date as the clamp floor in the evidence line. Scramble gate here = bt.gates.scramble_positions
on HELD POSITIONS (200 draws, block>=20) — the R1 probe showed cost-only scrambles are vacuous.
Final: pytest campaign/agents/chief/coord/HUNT_MACRO2/tests/ -q -> 36 passed (8 r1 + 17 r2 + 11 r3).

### Construction (fail-closed, PIT)
Release calendar = min vintage per obs period; obs whose first vintage == cube global min
(fetch-floor/birth clamps: 23 PAYEMS, 59 IPMAN, 282 ICSA) dropped, never treated as releases.
Surprise = log(print / latest-known PRIOR obs value as of release date) z-scored by trailing
mean/sd of STRICTLY EARLIER scored releases (min_hist=12; mu needs 12 priors, sd needs 2).
Event position = sign(z)*size at the first TRADING day strictly after release (holiday-aware;
NaN-z warmup never fires). Standalone single-ETF book (QQQ TLT IEF TIP XHB ITB XLI), T+1,
6.4bps one-side FULL |d(held)| day-1 seed = first held position, borrow 0.5%/yr, VT10%
trailing-only clip<=3.0. Grid: 9 series x {FOLLOW,FADE} x {thr 1.0/1.5/2.0 x hold 1/3, hold 3,
2.0} + mu-only variants = 252 sleeves, n 5114..6968.

### Exact numbers — 0/252 pass ALL gates (round3_results.csv)
Best per series (FULL window net): ICSA->QQQ FOLLOW thr2.0 h1 SR 0.321 ann +0.21% H1 0.12/H2
0.44 negyr 2 corr 0.000 scram_p 0.040 | UNRATE->QQQ FOLLOW thr1.0 h3 SR 0.264 ann +0.30% H1
0.18/H2 0.36 negyr 3 | RSXFS->QQQ FADE thr1.0 h1 SR 0.276 H1 0.54/H2 -0.05 negyr 3 scram 0.060 |
PAYEMS->QQQ FOLLOW thr2.0 h1 SR 0.159 ann +0.10% negyr 0 scram 0.185 | CPIAUCSL->QQQ FADE
thr2.0 h1 SR 0.240 scram 0.105 | IPMAN->QQQ FOLLOW thr2.0 h1 SR 0.169 | HOUST->ITB FOLLOW
thr2.0 h3 SR 0.158 | UMCSENT->QQQ FOLLOW thr1.0 h1 SR 0.152 | DGORDER->XLI FOLLOW thr1.0 h3
SR 0.096. Grid stats: SR max 0.321, median -0.136, min -1.200; ann max +0.42% (VT10 book),
median -0.12%; 0 of 252 reach SR>=0.5, let alone 1.0; halves>=0.5 fails 252/252; yearly fails
on most; |corr|<0.15 everywhere (max 0.085 — decorrelation was never the problem, edge is);
position-scramble p<0.05 only 10/252. FOLLOW mean SR -0.199 vs FADE -0.166: NO directional
prior wins; z vs mu-only: max 0.321 vs 0.045 (normalization helps, still 3x short). Release
frequency is high (22-32% of releases fire |z|>=1) so the failure is not event scarcity: the
T+1 ETF move after a vintage surprise is simply already priced / noise-dominated at 6.4bps.
PAYEMS median abs jump 12.5bp, ICSA 374.6bp, HOUST 570.1bp — the low-signal series are the
high-frequency releases with tiny jumps; nothing survives either way.

### Conclusion (charter 3b): macro-SURPRISE standalone = DEAD
0/252 across 9 release series, 2 directions, 3 thresholds, 2 holds, 2 normalizations, 7 ETFs.
Best SR 0.321 is 3.1x below the SR>=1.0 gate; halves gate fails everywhere. This completes
the macro family sweep for this campaign: R1 multi-series composites dead standalone (best
0.28), R2 overlays can only buy MDD relief by selling ann (no ann adds), R3 vintage-release
surprises dead standalone. FRED/ALFRED macro data has no tradable standalone premium on this
universe after honest PIT vintage timing + full costs. DEAD_IDEAS row below for the coordinator.

### Charter 3(c): HUNT_VOL2 round-2 negatives independently CONFIRMED (34/34)
xverify_vol2_r2.py re-derives all 34 gates from their spec (VVIX expanding-z x trail-ret
conditional, SKEW 5d-change expanding-q tail w/ hold, VIX9D>3M sustained; their exact cost
convention) WITHOUT importing their lib, and compares to their saved vol2_round2_scan.csv:
trigger fracs match to 2.7e-03 max (gates identical); 34/34 verdicts agree on their +0.3pp
bar; best dAnn mine -0.114pp vs theirs -0.144pp (both << +0.3pp) -> 0/34 negative STANDS.
Two honesty notes: (i) their CSV stores the name column with literal single quotes (join
must strip them); (ii) their scan ran 02:56 against the PRE-costfix champion (8f98da1: ann
39.851% SR 3.296 MDD -6.840%); the 11:24 re-emit (b268e52) changed the committed champion to
ann 37.195% SR 3.181 MDD -6.692% (corr 0.9988, mean|diff| 1.93e-04), so my per-variant deltas
differ by up to 0.63pp — but no variant crosses the bar on either base. My OWN first draft
had the reverse bug (double-scaling p = 1.6*g on already-gross-1.6 returns -> phantom +27.7pp
dAnn); caught by the cross-check itself (gates matched, pnl could not) and fixed before any
claim. Their negative is CONFIRMED, robust to the champion re-emit.

### Side-finding: R2 overlay passers re-verified on the costfix champion
The b268e52 re-emit invalidated R2's base book, so its two MDD-arm passers were re-measured
on the rebuilt committed champion (rescramble_r2_passers.py; max|rebuilt-committed| = 1.0e-16):
  book T10Y2Y z63<-2 x0.6: dAnn -1.932pp dMDD +1.016pp (39.851->37.195 base) MDD -6.69->-5.68%
    SR 3.119 neg=0 scramble_p(mdd) = 0.015 — unchanged from R2's numbers; STILL PASSES MDD arm.
  book JOINT(VIXsus21|T10Y2Y) x0.6: dAnn -3.467pp dMDD +1.494pp MDD -6.69->-5.20% SR 3.139
    neg=0 scramble_p(mdd) = 0.000 — STILL PASSES MDD arm.
An apparent "+0.602pp ann flip" of the T10Y2Y sleeve vs the new champion was diagnosed as an
ARTIFACT of comparing R2's saved overlay series (built on the old book) to the new book; the
correct same-construction rebuild shows dAnn still negative. Both remain coordinator-decision
overlays (buy 1.0-1.5pp MDD with 1.9-3.5pp ann), not new alpha. Everything else in R2's table
re-ran identically (28/28 variants, all verdicts unchanged, round2_results.csv re-written).

### DEAD_IDEAS.csv row (submitted to coordinator for append)
ALFRED vintage macro-release surprise standalone (9 series x FOLLOW/FADE x thr/hold z+mu, 252 variants),dead,"best ICSA->QQQ thr2.0 SR 0.321 ann +0.21% (halves 0.12/0.44); 0/252 reach SR 0.5 (gate 1.0); halves fail 252/252; FOLLOW -0.199 vs FADE -0.166 mean SR (no direction); |corr|<0.085 everywhere; pos-scramble p<0.05 10/252; PIT vintage cubes 2005-2026 real (PAYEMS anchor 2009-12-04 verified)",HUNT_MACRO2

EVIDENCE (all reproduce from saved scripts):
- python3 campaign/agents/chief/coord/HUNT_MACRO2/work_r3/HUNT_MACRO2_round3.py  (grid; writes
  work_r3/round3_results.csv, 252 rows)
- python3 -m pytest campaign/agents/chief/coord/HUNT_MACRO2/tests/ -q  (36 passed)
- python3 campaign/agents/chief/coord/HUNT_MACRO2/work_r3/xverify_vol2_r2.py  (34/34 confirm;
  writes xverify_vol2_r2_mine.csv)
- python3 campaign/agents/chief/coord/HUNT_MACRO2/work_r3/rescramble_r2_passers.py
- data: work_r3/alfred/{9 series}.csv + _fetch_summary.json (FRED ALFRED, HTTP 200 all)

ROUND 3 DONE


## ROUND 4 (2026-09-07) — CROSS-SLEEVE event study of ALFRED surprise days on the champion: 0/10 overlays PASS; own-vol control confirms NO macro content (DEAD)

Charter: on top-quintile surprise days (the 9 R3 ALFRED series), which of the 13 champion
slots earn/lose abnormally? Is there a stable sleeve-rotation or day-of-release de-levering
overlay that survives costs, T+1, halves, scramble AND beats the generic own-vol control?
Session state on entry: work_r4/ did not exist; tests/test_macro_r4_events.py was written
NEW this session as a pre-registration spec (red first, module missing) BEFORE any
evaluation; R3 vintage cubes + R2 overlay algebra reused unchanged.

### TDD (red -> 8/8 green; full suite 44/44)
8 tests pre-registered and now green (test_macro_r4_events.py): champion rebuild pin
(max|rebuilt-committed| = 9.996e-17 <= 1e-12; 13 slots in builder order); T+1 holiday-aware
event mapping (Fri release -> Mon, release day itself never fires, sub-threshold never
fires); pre-committed RISK_ON/DEFENSIVE split pinned before evaluation; event table must
come from R3 PIT z (2,944 scored releases, 9 series, all finite); own-vol control PIT
(truncated-history == full-history trigger) + fail-closed frequency matcher (tol 0.3pp);
slot decomposition identity sum(Wg*df) - turnover - margin == champion net to 1e-12;
de-lever wrapper == R2.overlay_book exactly (atol 1e-15). 2 test-spec bugs fixed during
bring-up (mine, never executed before): R2.rb not a module attribute (import rawew13v2_build
inside the test) and kw q= vs qtarget=.

### Event study (332 event T+1 days = 6.91% of 4805; union of |z| >= 1.2816 top-quintile)
Slot pnl bp/day, event days vs rest (r4_event_study.csv): BOOK 15.78 on vs 13.70 off
(diff +2.08, t=0.41 NS) - macro-release event days are ABOVE-AVERAGE champion days, so
de-levering them sells premium. Per slot: brwt15 +0.27 (t 0.28), brwt10 +1.04 (t 0.65),
brwt7 +1.01 (t 0.72), brwt5 +0.65 (t 0.49), C5ng -0.32 (-0.74), C5ngsum -0.79 (-2.03),
A5r2 -0.01 (-0.14), a6r7 +0.09 (0.64), QAxasts -0.02 (-0.11), carryv2 -0.07 (-0.87),
dualmom +0.16 (0.77), diescrack +0.06 (0.88), CFX4 0.00 (flat). The only |t|>=2 cell
(C5ngsum) is the expected false-positive rate in action: P(|t|>=2.03)=0.0428 -> 0.56
expected among 13 slots; the rotation overlays built on exactly that signal lose money
(below), so it does not survive as content.

### Overlay grid (r4_overlay_results.csv; base champion ann 37.195% / SR 3.181 / MDD -6.692% / 0 neg)
| variant | dAnn | dMDD | SR | verdict |
|---|---|---|---|---|
| DELEVER book x0.8 macro events | -1.394pp | +0.000pp | 3.11 | NO (fails both arms) |
| DELEVER book x0.6 macro events | -2.794pp | +0.000pp | 3.04 | NO |
| ROTATE riskon up1.1/dn0.9 (signed agg surprise) | -0.112pp | +0.000pp | 3.17 | NO |
| ROTATE up1.15/dn0.85 | -0.169pp | +0.000pp | 3.17 | NO |
| ROTATE up0.9/dn1.1 (inverted) | -0.106pp | -0.000pp | 3.17 | NO |
| ROTATE up0.85/dn1.15 (inverted) | -0.161pp | -0.000pp | 3.17 | NO |
| DELEVER all-slots x0.8 | -1.386pp | -0.000pp | 3.12 | NO |
| DELEVER all-slots x0.6 | -2.787pp | -0.000pp | 3.04 | NO |
| CONTROL ownvol x0.8 (q=0.927, on 6.62% vs macro 6.91%) | -1.622pp | +0.000pp | **3.32** | control |
| CONTROL ownvol x0.6 | -3.261pp | +0.000pp | **3.44** | control |
Scramble not reached by any macro variant under the fail-closed rule (scramble only runs
for raw-arm-accepting rows; none accepted). Random same-frequency masks (200 draws):
dAnn median -2.802pp p95 -2.378pp; dMDD median +0.000pp p95 +0.713pp - i.e. ~5% of
content-free masks get >=0.5pp MDD relief by LUCK while the macro trigger gets exactly 0.

### Mechanism (brutal honesty) - the charter's control question answered
The champion max-dd is 2018-06-19 -> 2018-06-25 (-6.692%, 5 days) and contains ZERO macro
release-event days; 0 of the top-10 drawdown days are event days (largest dd days cluster
in 2008-12/2009-02/2026-03, none event-tagged). So day-of-release de-levering has nothing
to relieve: dMDD is exactly +0.000pp on every macro variant - the identical failure mode
R2 found for USREC/VIX/TOTALSL. Event days carry slightly ABOVE-average pnl (+2.08bp,
t=0.41), so de-levering is a pure ann giveaway (-1.4 to -2.8pp). Sleeve-rotation by
surprise sign is even thinner: +/-1 aggregate-surprise days are indistinguishable
(dAnn -0.11..-0.17pp both directions, inverting the sign does not flip the loss).
The charter's kill-test verdict: at matched on-frequency the CONTENT-FREE own-vol control
also gets +0.000pp MDD but preserves far more risk-adjusted return (SR 3.32/3.44 vs macro
3.11/3.04 at x0.8/x0.6; dAnn comparison is moot since neither passes an arm). The macro
trigger is indistinguishable from - on SR, strictly worse than - a generic vol mask.
Per charter: the control beats the macro gate (nothing passes for either, and on the
metric that separates them the content-free mask wins) -> macro-release event conditioning
on this champion is DEAD.
EXPLORATORY per-series scan (9 series x 2 scales = 18 cells, NOT pre-registered, labeled
as such; no selection allowed): all 18 cells dAnn<0 (-0.08..-0.85pp) and dMDD +0.000pp;
best |dSR| = ICSA x0.6 at -0.054. No per-series rescue exists even before multiplicity
correction.

### Conclusion
0/10 pre-registered overlays pass any acceptance arm; the cross-sleeve event angle closes
the macro family for this campaign with the same mechanism as R2 (the champion's risk is
concentrated in non-event windows - 96% energy-basis DEF slots, June-2018, zero macro
releases). Full arc: R1 macro composites dead standalone (best SR 0.28); R2 overlays can
only buy MDD relief by selling ann, and the one nominally-passing trigger (T10Y2Y) was a
single-episode lottery; R3 vintage surprises dead standalone (best SR 0.321); R4 event-day
cross-sleeve conditioning dead - own-vol control matches or beats it. ALFRED macro-release
information has no tradable content for this champion at 6.4bps full-costs, T+1, PIT
vintages.

### DEAD_IDEAS.csv row (submitted to coordinator for append)
ALFRED top-quintile surprise-day cross-sleeve overlays on champion (de-lever book/slots + signed sleeve-rotation, 10 variants + 18 exploratory),dead,"""332 event days (6.91%): event-day book pnl ABOVE average (+2.08bp, t 0.41) so de-levering sells premium: dAnn -1.39..-2.79pp, dMDD exactly +0.000pp (max-dd window 2018-06-19..25 has ZERO event days, 0/10 top-10 dd days); rotation by surprise sign dAnn -0.11..-0.17pp both directions; own-vol control at matched freq (6.62%) also +0.000pp MDD but HIGHER SR 3.32/3.44 vs macro 3.11/3.04 - control >= macro, content-free per charter kill-test; random same-freq masks p95 dMDD +0.713pp by luck > macro's 0.000; 18 exploratory per-series cells all dAnn<0 dMDD 0.000""",HUNT_MACRO2-R4

EVIDENCE: campaign/agents/chief/coord/HUNT_MACRO2/work_r4/HUNT_MACRO2_round4.py (writes
r4_event_study.csv + r4_overlay_results.csv); tests/test_macro_r4_events.py (8 tests,
pre-registered); reproduction = python3
campaign/agents/chief/coord/HUNT_MACRO2/work_r4/HUNT_MACRO2_round4.py && python3 -m pytest
campaign/agents/chief/coord/HUNT_MACRO2/tests/ -q (44 passed). Champion of record re-verified
this round: 37.195% ann / SR 3.181 / MDD -6.692% / 0 neg yrs / rebuild dev 9.996e-17.

ROUND 4 DONE


## ROUND 5 (2026-09-08) — Eurostat/BLS/WorldBank macro-regime covariates as champion OVERLAY: 0/37 PASS (DEAD); own-vol control separates nothing because nothing fires near the risk

Charter corner (a): keyless altdata5 cubes (Eurostat / BLS / WorldBank) as champion-overlay
covariates, V2 §8 battery + era-split + mandatory §6 leak_probe. Corner (b) (standalone
variant) NOT triggered: no overlay showed any raw-arm effect, so per the charter's own
condition there is nothing to advance.

### Data (data-backed, fetched live this round, sha-pinned)
fetch_regime_data.py hit all 5 keyless endpoints HTTP 200 (work_r5/data/fetch_summary.json):
eurostat_hicp_ea20_cp00_rch_a 301 rows 2000-12..2025-12 (sha16 85b813300226e9f0) |
bls_cusr0000sa0 30 rows 2024-01..2026-07 (82efedd7c9e9dfc3) | bls_wpsfd49207 31 rows
2024-01..2026-07 (46ee12d45fbfe888) | worldbank_usa_gdp_growth 36 rows 1990..2025
(9364ce90ab36af4d) | worldbank_usa_cpi_annual 35 rows 1990..2024 (2d54c5c8c525ade2).
Endpoint facts recorded: BLS keyless v1 GET serves ONLY the 3 most recent years (so the
BLS monthly covariates are 2024+-only, span_class materially-short and labeled as such in
the grid); the World Bank `date=A:B` range query shape returned HTTP 502 three times
(~1s each, 2026-09-08) while the same indicator without the date param returns 200 with
all 66 rows in one page — fetched via the no-date shape + local year filter, same
altdata5 parser (_parse_wb), failure recorded. PIT lags documented per series: Eurostat
flash m_end+40 cal d; BLS mid-month m_end+45 cal d; WB annual Y_end+240 cal d.
Champion of record re-verified this round: rebuild dev 9.996e-17, sha 4358dfab95679b97
(matches the charter pin).

### TDD (red first: 9 errors / 1 pass -> 10/10 green; full suite 54/54)
10 tests pre-registered in tests/test_macro_r5_regime.py BEFORE evaluation: data files
present w/ row counts + PIT-lag docs; PIT visibility (first visible value >= first raw
obs + documented lag; truncation invariance at 2019-06-30 for long-history series, and
2024+-series must be INVISIBLE at that cutoff); trailing-only transforms (dropping the
last raw obs cannot change the panel before that obs's visibility stamp); overlay
identity (m==1 reproduces the committed champion, max dev <1e-12); T+1 (flipping the
day-t decision leaves day t unchanged and moves t+1); pre-registered scale ladder +
plateau helper; own-vol control matchable to ±0.3pp fail-closed; era-split +
delta-halves helpers (identity overlay -> all-zero deltas); leak_probe wrapper (published
leak dict; sig-less fails closed); results-CSV column contract (V2 battery columns).
3 test-spec bugs repaired during bring-up (all mine, fixtures never executed before,
each documented inline in the test file): (1) >500-overlap demanded at a 2019 cutoff for
series that are 2024+-only (impossible; long-history vs short-span split instead);
(2) trailing-only probe compared the full ffilled index where a dropped newest print
legitimately changes the tail — invariant re-pinned to "no diff BEFORE the dropped obs's
PIT stamp"; (3) random trigger fixture flipped 0->0 at the probed index (97% off-days),
so the t+1 response check compared identical books — deterministic on-day pinned.

### Construction (pre-registered, fail-closed, PIT)
Book-level de-lever overlays (R2 algebra: m=1 normal, m=scale on gate days, decided at
close t, held t+1, full |d(m*W)| at 6.4bps, margin on overlaid gross):
 DEFLev  = WB US-CPI yoy > expanding q85 OR WB US-GDP growth < expanding q15
 DEFLev2 = EA HICP yoy > expanding q85 OR WB US-GDP growth < expanding q15
 DEFLev3 = BLS US CPI yoy > expanding q85 (2024+ span only, min_obs 60)
Scale ladder {1.0, 0.9, 0.8, 0.7, 0.6, 0.5} (8g plateau); every macro variant paired
with an own-vol control matched to its on-frequency (±0.3pp fail-closed) — the
HUNT_CREDIT2-R2 / R4 falsifier. REGROT = RISK_ON slots ±5% by US-CPI-vs-expanding-median
sign. Slot-level de-lever forms excluded at pre-registration (R2/R4 established the
champion's dd lives in DEF energy-basis slots). One engine bug found by inspection and
fixed before any verdict was read (documented in-file): first run built m = trig*scale,
which makes the book FLAT off-trigger (m=0 on ~88% of days) — the -29..-37pp dAnn
pathology in the first printed grid; correct R2 semantics m=1 normal / m=scale on-gate.

### Exact numbers (r5_overlay_results.csv, 37 rows; champion 37.1954% / SR 3.1810 / MDD -6.6922% / 0 neg)
ALL macro variants: dAnn < 0 and dMDD EXACTLY +0.000pp at every scale (the same R2/R4
failure mode — the champion's risk is not in macro-stress windows):
| variant | on-freq | dAnn @x0.6 | dMDD @x0.6 | dSR @x0.6 | neg | raw arm |
|---|---|---|---|---|---|---|
| DEFLev wb-cpi-hi \| wb-gdp-lo | 11.88% | -1.781pp | +0.000pp | -0.079 | 0 | NO |
| DEFLev2 hicp-hi \| wb-gdp-lo | 12.76% | -0.973pp | +0.000pp | -0.019 | 0 | NO |
| DEFLev3 bls-cpi-hi (2024+) | 2.33% | -0.200pp | +0.000pp | +0.005 | 0 | NO (dAnn<0) |
| REGROT cpi-median tilt | 97.8% sign-on | -0.020pp | -0.001pp | -0.0009 | 0 | NO |
Era-split (V2 §8j, dSR 2008-13 / 2014-19 / 2020-26): DEFLev x0.6 -0.0393 / +0.0000 /
-0.1897; DEFLev2 x0.6 -0.0393 / +0.0000 / -0.0543; DEFLev3 x0.6 +0.0000 / +0.0000 /
-0.0027; REGROT -0.0022 / +0.0007 / -0.0042. Delta-halves (8f): DEFLev x0.6
-0.0227 / -0.1358 — no halves-consistency anywhere (all deltas ≤ 0 or sign-flipping).
The dSR>0 on the DEEPEST de-levers of DEFLev3 (x0.5 +0.004) is the control effect, not
content: its matched own-vol control gets MORE (+0.309 at x0.5).
Controls at matched frequency (max dSR across scales): DEFLev-control +0.271, DEFLev2
+0.294, DEFLev3-control +0.309 — the content-free vol mask preserves MORE risk-adjusted
return than every macro gate at the same on-frequency, i.e. the macro covariates are
strictly worse than random vol conditioning on this book (the control question again,
now for a third overlay family).

### Mechanism (brutal honesty)
Champion max-dd is 2018-06-19 -> 2018-06-25 (-6.692%) and the panel shows WHY nothing can
help: US CPI yoy 1.26 vs expanding q85 3.84; WB GDP 1.82 vs expanding q15 0.11; EA HICP
1.4 (at-target). Macro-regime gates fire ZERO days in the dd window and overlap 0 of the
top-10 drawdown days (own-vol control: 0 in window, 4/10 top-dd days — even it has
nothing to relieve but at least it touches the tail days). The 2018-06 episode is
idiosyncratic energy-basis reversion (R2: 96% brwt* slots; R4: zero event days) — no
inflation/growth regime condition can see it, in any data source. DEFLev3's trigger is
confined to 2025-10-15..2026-08-27 (the 3-year keyless BLS window), 112 days, no dd
inside it.

### Conclusion + V2 track statement
CHAMPION/OVERLAY track: 0/37 variants meet ANY §8 acceptance arm (8c dAnn>0 fails
everywhere; the MDD arm is vacuous at +0.000pp relief; 8d/8f fail on every reported
delta). Own-vol control dominates on the metric that separates them. Charter corner (b)
does not trigger. This closes the LAST pre-registered macro data family for this
campaign: FRED composites (R1), FRED overlays (R2), ALFRED vintage surprises (R3),
ALFRED cross-sleeve events (R4), and now Eurostat/BLS/WorldBank regime covariates (R5)
— five rounds, zero adoptable macro alpha on this champion at 6.4bps full-|dW|, T+1,
PIT. The recurring mechanism is not data quality: the champion's entire risk sits in
short idiosyncratic windows (June-2018 energy-basis; 2008-12/2009-02/2026-03 tails) that
low-frequency macro regime variables structurally cannot see day-of.

### DEAD_IDEAS.csv row (submitted to coordinator for append)
Eurostat/BLS/WorldBank macro-regime covariate overlays on champion (DEFLev x3 bands x 6 scales + REGROT + matched own-vol controls, 37 variants),dead,"all dAnn<0 (-0.02..-2.33pp @x0.6 band) and dMDD exactly +0.000pp at every scale; dd window 2018-06-19..25 has US CPI 1.26 vs q85 3.84 / GDP 1.82 vs q15 0.11 / HICP 1.4 - zero trigger days in window, 0/10 top-dd days; own-vol controls at matched freq get HIGHER dSR (+0.27..+0.31) than every macro gate; BLS keyless = 2024+-only span; WB date-range shape HTTP 502 (no-date shape 200, 66 rows); era-split shows 2020-26 worst (DEFLev x0.6 dSR -0.19)",HUNT_MACRO2-R5

EVIDENCE: campaign/agents/chief/coord/HUNT_MACRO2/work_r5/fetch_regime_data.py (5/5 live,
fetch_summary.json sha-pinned) + HUNT_MACRO2_round5.py (writes r5_overlay_results.csv 37
rows + r5_leak_probe.json: leak_ok=True corr=-0.0031); tests/test_macro_r5_regime.py
(10 tests, pre-registered red-first); reproduction = python3
campaign/agents/chief/coord/HUNT_MACRO2/work_r5/fetch_regime_data.py && python3
campaign/agents/chief/coord/HUNT_MACRO2/work_r5/HUNT_MACRO2_round5.py && python3 -m pytest
campaign/agents/chief/coord/HUNT_MACRO2/tests/ -q (54 passed). Champion vintage pinned:
sha256 4358dfab95679b97, rebuild dev 9.996e-17.

ROUND 5 DONE


---

# HUNT_MACRO2 — round 6 (independent agent run, 2026-09-08 12:5x-13:4x CST) — CONSOLIDATION

READ FIRST done: GATES_CONTRACT_V2.md (in force; all my battery-class calls this round pass
sig= + leak_check=True explicitly) + DEAD_IDEAS.csv recounted myself at round start = 143 data
rows (charter quote 137; dynamic as V2 preamble documents). Champion of record sha re-pinned by
me this round: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha256_16 4358dfab95679b97 (computed
from the file, not trusted). No new macro corner attempted — charter (c) honored: the five
macro families are closed R1-R5 and no data-backed gap was pre-registered.

## (a) FRAUD-CATCH cross-verification — BOTH VERDICTS CONFIRMED, verdicts stand

Method: my OWN builders + my OWN scorer for everything (no import of either agent's code);
shared campaign bt/ conventions only (engine cost/borrow semantics, SR = mean/std*sqrt(252));
base leg for SECTOR2 = their published artifact (their own R3 precedent: rebuild corr 0.844,
artifact is authoritative).

HUNT_INTERNATIONAL2 R5 (9/9 sleeves, raw NIKKEI225.csv rebuilt from scratch):
- Vintage pin verified: NIKKEI225.csv sha16 92f09efca6eeb9fa, 20,166 data rows 1949-05-16..2026-08-31. Match.
- MY rebuilt SR vs their claimed SR, exact to 4 decimals on 9/9, max |dSR| 0.0000:
  MOM_252_LF 0.7354 / MOM_63_LF 0.6303 / MOM_126_LF 0.5772 / MOM_252_LS 0.4396 /
  CAL_SELLMAY 0.5350 / CAL_TOM_dates 0.4021 / CAL_TOM_rank3 0.3691 / CAL_TOY_dates 0.2669 /
  CAL_TOY_rank5 0.3470. Pre/post-1990 sub-span SRs also exact 9/9 (e.g. MOM_252_LF
  +1.209/+0.257; CAL_TOY_rank5 +0.809/-0.029). Verdict agreement: FAIL 9/9 (all SR<1.0,
  all era-imbalanced). corr_to_champion max dev 0.0006 on 9/9 (e.g. MOM_252_LS +0.0284 both).
- Claimed H1/H2/negyr use their DISCLOSED r_pu*sig battery-feed convention (feed_notes:
  flat-exit-cost rows not representable). I reconciled their printed halves EXACTLY on the
  calendar configs under that convention (e.g. CAL_TOM_dates 0.8434/0.2673/24 neg = claim
  0.843/0.267/24) and confirmed the exact-net numbers differ ONLY by that disclosed gap, in
  the CONSERVATIVE direction (net lower: MOM_126_LF 34 neg exact vs 32 claimed; my H1/H2
  1.009/0.226 vs claimed 1.024/0.247). No undisclosed discrepancy. Their leak probe convention
  differs slightly (my same-period corr +0.0231 vs their +0.0376 on MOM_252_LF) but the
  verdict is identical (leak=False, both far under the 0.20 threshold).
- Note: their "DEAD_IDEAS row appended" landed as an UPDATE of the pre-registered NKY-calendars
  row (SKILL_ALPHAAGM row, now 'CORNER CONSUMED R5' with 9/9 FAIL evidence) — legal curation,
  row content verified accurate.

HUNT_SECTOR2 R5 (A11 attention de-risk overlay):
- Vintage pins verified: A11_rs_ratio#lb126k4.csv sha16 0354fd437047d221, 2047 rows 2018-06-20..2026-08-12;
  wiki_attention/aapl.csv sha16 609cca25738461c0, 4,086 rows from 2015-07-01. Match.
- EVERY headline number reproduces EXACTLY with my own code and MY OWN placebo seed:
  base SR 0.6793 (claim 0.679), overlay SR 0.8205 (0.821), dSR +0.1412 (+0.141), gate
  fire_frac 0.223 / 300 flips (same), dSR halves +0.407/-1.087 (same), excl-2020 dSR -0.979
  (same), leak probe same-period corr +0.0844 / p 1.31e-04 / argmax lag -2 / leak=False
  (theirs +0.084 / 0.000127 / lag -2 / False — 4dp match), corr_to_champion -0.0629 (exact),
  bp trio PASS confirmed (spy_bh 0.7553 my computation vs 0.7538 theirs; margin +0.067).
- ONE INTERPRETATION CORRECTION (the only mismatch found, and it is in a FINDINGS/DEAD_IDEAS
  sentence, not in any number or verdict): their text 'placebo p=0.000 (200 matched random
  gates reproduce the entire lift)' is INVERTED. Their own comparator is P(placebo >= overlay);
  p = 0/200 means NO random gate reached the overlay. My independent placebo (seed 20260908)
  confirms the opposite of the sentence: placebo SR mean 0.2059 / std 0.1220 / max 0.5712 vs
  overlay 0.8205 — matched random de-risk timing DESTROYS SR on this book (mean dSR -0.473,
  best draw still -0.108 below the attention gate; overlay beats 200/200 draws, z=5.04;
  a constant 0.85x scale leaves SR 0.6793 unchanged, so it is timing, not scaling).
  HONEST RESTATEMENT: the attention gate's lift is real RELATIVE TO matched-random timing,
  but single-episode (2020; halves +0.407/-1.087, excl-2020 -0.979) — the R4 TimesFM
  span-gate kill applies to it exactly as they concluded, on the era-concentration evidence
  (which is what their verdict actually used). DISPOSITION UNCHANGED: span_class
  inception_fail -> NOT_HUNT_ELIGIBLE (V2 9a), FAIL_SR 0.821 < 1.0, honest negative stands.
  Escalation not required (no verdict mismatch); the correction row in DEAD_IDEAS is the
  record. Their DEAD_IDEAS row's evidence cell carries the inverted sentence and should be
  read with this correction.

## (b) DEAD_IDEAS curation — macro rows

- Recount: 143 data rows at round start. Macro-family rows audited: R1 composites,
  R2 overlays, R4 ALFRED cross-sleeve all present and accurate vs my saved artifacts.
- MY OWN R5 row was MISSING (FINDINGS said 'submitted to coordinator for append' but it never
  landed — coordinator-side gap). Re-verified my R5 numbers from the artifact BEFORE filing:
  work_r5/r5_overlay_results.csv sha16 16d6bae3a9535567, 37 rows (19 macro + 18 controls);
  macro dAnn -2.33..-0.02pp at every scale (x1.0 baselines excluded), max dMDD relief
  2.2e-14pp (exactly zero -> 8b arm vacuous), 0/19 with dAnn>0, leak dict published
  (r5_leak_probe.json corr -0.0031, leak_ok=True). APPENDED as HUNT_MACRO2-R5.
- CONCURRENT-WRITE EVENT (disclosed for the audit trail): while I worked, the HUNT_CMDT2-R6CUR
  dedup (their row-139 finding) executed and removed the 5 byte-identical dup macro rows
  (old idx 116-120 = dup of 69-73; my own md5 sweep confirms they were byte-equal and that
  ZERO byte-identical dup pairs remain). Sequence: 143 (round start) -> 138 (post-dedup, at my
  append) -> 140 (after my 2 rows: HUNT_MACRO2-R5 + HUNT_MACRO2-R6 curation/correction row,
  status 'verified'). Final ledger: 140 data rows, field-count clean 4/4 on every record.
- Chartered (c): NO new macro corner — none pre-registered, none attempted.

## ROUND 6 ARTIFACTS
campaign/agents/chief/coord/HUNT_MACRO2/work_r6/{verify_intl2_r5.py (own-code INTL2 verifier,
writes intl2_r5_verify.csv), verify_sector2_r5.py (own-code SECTOR2 verifier, writes
sector2_r5_verify.json)}. Reproduction: python3 campaign/agents/chief/coord/HUNT_MACRO2/work_r6/verify_intl2_r5.py
&& python3 campaign/agents/chief/coord/HUNT_MACRO2/work_r6/verify_sector2_r5.py (repo root).
Both scripts are self-contained; no edits made to any other agent's directory, the champion,
or bt/ this round.

ROUND 6 DONE

---

# HUNT_MACRO2 — round 7 (independent agent run, 2026-09-08 19:4x-20:3x CST)

READ FIRST done: GATES_CONTRACT_V2.md (in force; no gates.run acceptance call this round —
this is an audit round, evidence-only) + DEAD_IDEAS.csv recounted MYSELF at round start:
**147 data rows** (charter said 145-146 at R6-end; the delta = HUNT_COT2-R5 coordinator
append + HUNT_CRYPTO2-R7 blocked row, both verified in the tail; field-count clean 4/4 on
every record; ZERO byte-identical (idea,source) dup pairs by my own sweep; sha16 at read
e0e61605c76c38e0). Champion of record re-verified FRESH this round by me:
`bash campaign/bt/verify_champion_r3_cmd.sh` (canonical full 13-sleeve map) -> exit 0,
ok=true **7/7**, ann 37.19539675684982 / SR 3.180994199561701 / MDD -6.692185534307193 /
0 neg yrs / n=4805 (2008-03-31..2026-08-27), sha 4358dfab95679b97 — output pinned
work_r7/verify_champ_r7.json. Charter quote matched exactly.

## R7(a) — OWN-CODE re-derivation of BOTH CAMP_SHORT-R6 scorecards: 121/121 reproduce, 0 mismatches, no escalation

Method: `work_r7/r7_repro_engine.py` + RED-first spec `work_r7/test_r7_repro_published.py`
(RED confirmed pre-engine: 8 errors on the missing module + 1 precondition failure that was
MY test bug — `COST["mismatches"]` is a list, I asserted == 0; fixed the test). Engine imports
NO agent code and NO bt/ modules — only published artifacts are read (13 sleeve CSVs, champion
CSV, weights CSV, CAMP_BORROW work_r5 JSONs+CSVs, CAMP_COST work_r5 JSONs, git HEAD via
ls-tree/rev-parse/hash-object); every my-side number comes from my own algebra (independent
rebuild of the 13-sleeve relw/weight/turnover/margin book). GREEN final: **9/9 tests** (52s),
and each of the 121 published checks is compared mine-vs-theirs at the scorecard's OWN tolerance:

- BORROW scorecard: **75/75 match, mismatches=[]** (evidence JSON
  work_r7/r7_repro_evidence.json block `borrow`). Load-bearing re-derivations, all exact:
  own-algebra rebuild vs committed champion max|dev| 9.996344030316351e-17; relw table from
  max(IS_SR,0)^0.55 to 2.220446049250313e-16; margin 2.70%/yr = 0.6 x 4.5%/252 = 1.0714 bps/day
  single distinct daily value; priced-at-4.5% residual 9.996e-17 (5.5%/6.5% residuals >1e-6,
  asserted, pricing identification holds); slot gross-share census reproduced all 13
  (brwt10 22.9518 / brwt7 19.9556 / brwt5 16.9737 / brwt15 13.2284 / C5ng 8.7977 / C5ngsum
  6.8112 / dualmom 2.6674 / QAxasts 2.3448 / A5r2 1.7769 / diescrack 1.7654 / a6r7 1.5402 /
  carryv2 1.1869 / CFX4 0.0, sum 100.0); 0 negative slot weights on 62,465 slot-days;
  diescrack embedded borrow re-derived from my OWN zrev+VT reconstruction (DJFUELUSGULF x42
  minus wti_full, log spread, L40 z2.0, vt 0.08 clip 3.0): exactly 0.005/252 on 733 rows
  (331 short / 173 long / 229 cost-only), line-unit dev 9.999e-17; drift flags reproduce from
  their fetched FRED artifacts (DFF n=26363 last 3.63% / SOFR n=2198 last 3.66%; implied
  5.13/5.63/5.16, rel +14.00/+25.11/+14.67%; path mean 2.9315 -> drag 1.7589 rel -34.86%;
  reprices 36.6784/36.2695/36.6538/38.4910 all 0-neg); 6-rung tier ladder worst dev 7.99e-15
  incl. the -0.60pp per +1pp arithmetic slope EXACT (1.55e-15).

- CHARTER-NAMED borrow-immaterial figure: **0.2195 bps/yr** champion embedded drag — mine
  0.2195372208472071 vs theirs 0.2195 (dev 3.72e-05 << 5e-4 tol); HTB tiers 2% -> 0.6586
  (mine 0.6586116625416214), 8% -> 3.2931 (mine 3.2930583127081063); borrow 100%-relative-
  drift impact 0.2195 bps/yr (mine 0.2195372208472071 vs theirs 0.2196, dev 6.28e-05).
  CONFIRMED: three orders of magnitude below gate-moving.

- COST scorecard: **46/46 match, mismatches=[]** (evidence block `cost`). verify_champion_r5
  self-consistency re-checked line by line (7/7 ok; weights_repro 2.220e-16; byte_repro
  1.110e-16; cost model full_dw resid 1.2457e-16 vs half 1.6798e-05 -> half-turn REJECTED by
  5 orders; bp/yr 5.2622 == turnover 5.2622; day-1 entry 3.87e-13 ~ 0; causality sameday
  4.927e-03 with matched causal mechanism; truncation 7 probes dev 0.0; gross 1.6000000000007,
  n_over 0, margin 2.70; 0 neg / worst +7.3104; stats n=4805 ann 37.1954 SR 3.1810 span
  2008-03-31..2026-08-27; is_end 2017-01-01). C2 byte-stability re-hashed by me: 16/16 files
  == shas_round_end.json == shas_round_start.json AND **16/16 committed-byte-exact vs git
  HEAD** (champion 4358dfab95679b97, weights 149164b3b01aa110, builder 1095b4f896b9bebb).
  C3 wide leak probe, MY OWN implementation, 3 conventions (champ-span fill0 -0.0323834/n4802,
  champ-span NaN-keep -0.0329087/n4657, full-history NaN-keep -0.0205571/n7384): published
  -0.0195663/n7026 sits inside the bracket; leak=False in ALL FOUR; argmax lag -1 (causal)
  in all four. C4 cost-model verdict re-derived with my own algebra: turnover 5.262230719945143
  bp/yr, full residual 9.996e-17, half residual 1.6798e-05, half_rejected=True.

- CHARTER-NAMED scalar-probe distinction — re-derived EXPLICITLY both constructions, and the
  R6 escalation is now a CLOSED THREE-WAY TRIANGLE: (i) faithful aggregate |dWg| =
  Wg.diff().abs().sum(axis=1) on the champion span: corr **+0.20336432961823633** (p 5.59e-47,
  n 4805) with the causal lag-(-1) argmax +0.46123290259832483; full-history +0.13945926418482227;
  (ii) the PUBLISHED leak_probe_r5.json pair +0.015600155730274267 / p 0.2795726814471842
  matches MY signed float-noise construction (Wg.diff().sum(axis=1), series std 3.35e-16) at
  +0.015246 / p 0.2906 (within the 1.5e-3/1.5e-2 screen CAMP_SHORT used) — degenerate-input
  diagnosis CONFIRMED independently; (iii) CAMP_COST's own R6 closeout
  (work_r6/closeout_r5_scalar_probe.json + generator closeout_r5_scalar_probe.py, which I
  re-ran read-for-read, deterministic, exit 0) publishes faithful +0.20336432961823633 /
  signed +0.015245577854695755 — my numbers agree to **0.000e+00 / 1.166e-15 / 0.000e+00**.
  VERDICT (leak=False) is unaffected and confirmed in every construction (lag-0 is never the
  argmax anywhere). Escalation queue: EMPTY — the R6 defect is resolved upstream and my
  derivation is the third independent confirmation.

## R7(b) — corner survey: NO data-backed gap found, NO corner opened (charter: honest negative expected either way)

The only visibly new keyless source in my lane is the FOMC decision-day calendar — and it is
ALREADY on disk (tools/quant/data/newdata/fomc_dates.csv, 119 rows 2008-01-29..2027-09-03;
wiki_attention/fomc.csv also present) and ALREADY effectively covered: DEAD_IDEAS row 14
"FOMC x natgas/gold" (dead, 'no edge', SKILL_ALPHAAGM, with the row-114 repro-path correction),
the coordinator's own campaign/scripts/coord_fomc.py pre-FOMC-drift study, my R4 cross-sleeve
event-day verdict (de-levering sells premium: event-day book pnl ABOVE average +2.08bp t 0.41;
content-free own-vol control at matched frequency BEAT the macro gate SR 3.32/3.44 vs
3.11/3.04), and my R5 0/37 regime-overlay sweep. DECISIVE NEW MEASUREMENT this round: the
champion's top-10 drawdown days contain **0/10 FOMC decision days** (2018-06-25 trough =
June-2018 energy basis, then 2008-12-19/26/30, 2009-02-11, 2026-03-17, 2014-01-08 — none are
macro-release events). A FOMC-calendar overlay corner would therefore be a dead-family re-tune
with no pre-registered data-backed gap — BANNED by the charter ground rules. Eurostat/BLS/
WorldBank re-tunes remain BANNED per the charter's own 0/19 R5 verdict. Corner (b): NOT
attempted, per rules.

## R7 ledger
- bt/ untouched; campaign/*.md untouched except this FINDINGS.md; no other agent's directory
  written (the one CAMP_COST re-run — closeout_r5_scalar_probe.py — is MY disclosed read-back
  verification of THEIR generator; it re-wrote their JSON byte-identically, sha16
  b2242cdef1d17eab, deterministic, exit 0).
- My lane suites: HUNT_MACRO2/tests/ 54 passed / 0 failed (45s); work_r7 R7 suite 9 passed /
  0 failed (52s) — RED-first evidenced above.
- Artifacts: work_r7/{r7_repro_engine.py, test_r7_repro_published.py, dump_r7_evidence.py,
  r7_repro_evidence.json, verify_champ_r7.json}. Reproduction: from repo root,
  python3 -m pytest campaign/agents/chief/coord/HUNT_MACRO2/work_r7/test_r7_repro_published.py -q
  && python3 campaign/agents/chief/coord/HUNT_MACRO2/work_r7/dump_r7_evidence.py
- DEAD_IDEAS: NO row this round — (a) confirmed two standing verdicts with zero mismatches
  (curation adds nothing the scorecards don't already say), and (b) opened no new family.

ROUND 7 DONE
