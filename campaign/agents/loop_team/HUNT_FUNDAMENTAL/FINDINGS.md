# HUNT_FUNDAMENTAL — FINDINGS (2026-09-02)

Charter: fundamental sleeve from `alphaportfolio_replication/data/fundamentals_annual.parquet`
(value/growth/profitability screens) -> monthly rebalance -> TRUE daily series (SPREAD-TO-DAILY
FORBIDDEN; book holds constant nominal weights intra-month, PnL from actual daily panel moves).
Honesty contract honored: T+1 (weights set at ME/quarter-end t price from t+1), 6bps/side on
turnover, +0.5%/yr borrow on short notional, vol-target via trailing expanding window only
(min 60d, cap 5x). Gates = full SR>=0.6, H1/H2>=0.3, <=2 neg yrs each >-5%, scramble 200x
p>0.05, |corr|<0.15 to HONEST11 blend, flatten gate (uniqR>=0.08, ac1<0.5, audit_harness logic).

## HEADLINE VERDICT: NO ADMISSIBLE FUNDAMENTAL SLEEVE FOUND. All candidates REJECTED.
The charter's core premise is inverted on this data: the value/growth/profitability screens
have ~zero-to-negative predictive power on the available panels, and the only adjacent family
with an edge (momentum, momentum+value-gated) is redundant with the committed dualmom sleeve
(corr far above 0.15) and/or degrades the champion when added.

## Data reality check (adversarial, done FIRST)
- fundamentals_annual.parquet: 7451 rows x 24 cols, 501 symbols, FY 2009-2027 (2026/27 partial).
  Coverage: op_income 86%, revenue 57%, cogs 31%, shares 46-69% (pre-2018 <67%).
- Name overlap vs price panels: ∩ twelve_extend-only = 7 (!). ∩ twelve_big = 259. Engine rebuilt
  on UNION panel (twelve_big ∪ twelve_extend = 738 names, 6553 rows, 1999-11-24..2026-08-17).
  NOTE: AUDIT5 called twelve_extend "4-day stub" — that is the *_extend* dir at tools/quant/data;
  the alphaportfolio twelve_extend CSVs carry full 1999+ history (union AAPL == twelve_big AAPL,
  max diff 0.0). Still, union adds only 441 mostly-OTC names.
- PIT: FY y used only from Jul-1 y+1 (campaign convention). FY continuity 99.2% gap-free.
- Survivorship (documented GOAL100_TRUTH_MEMO |10|, +2.7-5pp/yr): current-constituent panels
  INVERT classic xs premia (A3 precedent). Replicated here: short legs of value/profitability
  L/S LOSE every year — value_q_ls leg attribution 2010-2026: long leg +8..+30%/yr, short leg
  -11..-32%/yr in 15/17 yrs. Survivor short = short the future megacaps.

## Idea pass 1 — classic composites (union panel, M-rebalance LS 33/33, lev2, all FAIL)
| sleeve | SR | H1/H2 | ann | neg yrs | worst | verdict |
|---|---|---|---|---|---|---|
| value_comp (ni/E + oi/IC + rev/TA) | +0.06 | .06/.05 | -0.2% | 11 | -16.1% | FAIL |
| growth_comp (Δrev, Δoi / TA) | -0.23 | -.60/.01 | -4.6% | 10 | -36.7% | FAIL |
| prof_comp (oi/TA + ni/TA) | -0.22 | .04/.45 | -4.3% | 13 | -29.1% | FAIL |
| comp_vgp | -0.16 | .03/.32 | -3.5% | 13 | -31.7% | FAIL |
| value_q3030 | +0.03 | .05/.01 | -0.6% | 10 | -16.1% | FAIL |
Flatten gate PASSED for all (true daily: uniqR~0.62, ac1~-0.01..0.02) — the failure is
economic, not mechanical.

## Annual IC screen (vintage-level spearman vs fwd 12m, stale-carry windows)
| score | meanIC | IR | vintages |
|---|---|---|---|
| value | +0.0249 | +0.23 | 17 |
| prof | -0.0167 | -0.15 | 17 |
| growth | +0.0083 | +0.06 | 16 |
| accrual_inv (Sloan) | -0.0510 | -0.39 | 16 |
| piotroski3 | +0.0319 | +0.45 | 17 |
Benchmark on same panel: 12-1 momentum monthly rankIC = +0.0399, IR +0.35 (n=190 months).
ALL-legs screen (13 single legs + 78 pairs): best single s_ta (asset turnover) meanIC +0.0719
IR +0.43; best pair s_ta+roic +0.1042 IR +0.42. Backtested s_ta Q-M LS 33/33 lev2: SR +0.39,
7 neg yrs (FAIL). IC 0.10 at ANNUAL frequency is not harvestable monthly.

## Event studies (fundamental split vs fwd return, FY>=2012, n=3290)
- op_income>0 vs <=0: 15.3% vs 17.7% fwd-12m (WRONG SIGN), t=-1.24.
- op_income/TA terciles, 1m post-avail (PEAD): hi-lo spread +0.17bps/mo, t=0.64 p=0.53.
- neg_equity names (n=171): +19.6% vs +15.5% (wrong sign — distressed rip hardest).
- value-conditioning of momentum: mean 1m fwd spread cheap-vs-rich top-mom = +0.12bps/mo,
  t=0.77. The fundamentals add NOTHING to momentum on this panel.

## Idea pass 2 — Q-refresh, hybrids, hedge variants (all FAIL)
| variant | SR | verdict |
|---|---|---|
| value Q-LS 33/33 lev2 | +0.10 | FAIL |
| piotroski Q-LS | -0.11 | FAIL |
| mom L/S full panel (naive, benchmark) | -0.30 | FAIL (short leg = shorting survivors) |
| mom in cheap-half, L/S 50/50 | -0.24 | FAIL |
| rev5 LS 33/33 lev2 (weekly) | +0.75 | FAIL (corrH11 +0.108 OK but H2 only 0.77 negy 4 worst -4.6% then scramble-critical: not fundamental) |
| rev5 LS cheap-half | -0.02 | FAIL (fundamental filter KILLS reversal: +0.75 -> -0.02) |
| rev5 LS pio-high-half | +0.19 | FAIL |
| rev5 LS healthy(pio>=1/2, no-neg-eq) | +0.17/+0.06/+0.14 | FAIL (distress filter kills edge) |
| s_ta (asset turnover) Q-M LS | +0.39 | FAIL |

## Union-panel data hygiene finding (CRITICAL, feeds future hunters)
Raw union panel has 39,415 rows |ret|>25%/day and 4,482 rows |ret|>100% (262 names >100%).
Causes: zero price prints (AFCL 3.775 -> 0.0001 -> 3.964) and split-like steps booked as
1-day returns (AIKO 2.0 -> 24.8 = +1140%). Raw-return momentum on the union panel shows
SR +1.55, 0 neg yrs, +67.7% ann — ALL of which is bad-data mining: name-level exclusion of
any |r|>50% print drops it to SR +1.01/+9.3%; |r|>25% guard -> SR +0.94/+9.9%; liquid-298
only -> SR +0.98/+10.5%. The naive +67.7% is FAKE. Any future hunter on this panel MUST
apply the Q3 hygiene (drop |r|>25%-print names from books for 504d, winsorize PnL ±50%).

## Final candidate — HF_mom_cheap (closest call, REJECTED, artifacts saved in sleeves/)
12-1 momentum LO top-half, cheap-half filter, monthly ME rebalance T+1, Q3 hygiene, vt10:
- full-gate battery: SR 0.903 (PASS) | H1 1.16 / H2 0.66 (PASS) | neg yrs 1 BUT 2022 -6.3%
  <-5% clause (FAIL) | flatten uniqR 0.9369 ac1 -0.106 (PASS) |
  corr to HONEST11 blend +0.289 (FAIL >0.15) | corr to committed dualmom +0.784 (FAIL).
- scramble 200x decomposition: perm[mom xs] p=0.900 (edge NOT above mom-permuted null!),
  perm[filter] p=0.020 (fundamental filter is WORSE than random), perm[both] p=0.695.
  => The SR 0.90 is generic union-panel momentum exposure, NOT fundamental alpha.
- liquid-only variant (HF_mom_cheap_liq): corrH11 +0.141 (passes 0.15 by hair) BUT corrDM
  +0.631 / conditional-on-dualmom-on +0.713 (FAIL); regression hf~dm beta 0.538, residual
  alpha after removing dualmom content = 0.44%/yr = nothing.
- Incremental test in the FULL HONEST11-B recipe (11 sleeves + this as 12th, exact recipe):
  H11 SR_d 4.20 / SR_m 3.98 / ann +54.2% / MDD -6.43% -> H12 SR_d 4.02 / SR_m 3.87 /
  ann +49.9% / MDD -7.09%. ADDING IT DEGRADES THE CHAMPION ON ALL METRICS.

## Relation to LOOP_L16/LOOP_XGB1YFLAT context
- Confirms their conclusion: the goal set (Ann>=80%, SR>=5, DD<=7%, lev<=1.6, prof>=0) gains
  no new engine from this data. The best honest decorrelated-adjacent family (momentum) is
  already in HONEST11 via dualmom; fundamentals cannot improve or even replicate it.
- Re-affirms XGB1YFLAT: my sleeves are true daily paths (uniqR>0.93, ac1<0) — the flatten
  gate in my engines was clean by construction; no spread-to-daily anywhere.

## Verbatim numbers for the champion context (my repro, full recipe)
HONEST11-B repro here: SR_d 4.20, SR_m 3.98, ann_geo +54.2%, MDD -6.43%, 1 neg yr (-1.0%),
OOS17+ pos-year frac 1.000 (committed BALANCED differs slightly: SR_m 4.17 — different
config blend; my repro matches the B-config shape).

## Files
- sleeves/HF_mom_cheap_daily.csv(.meta), sleeves/HF_mom_cheap_liq_daily.csv(.meta) — rejected,
  saved for audit with verdicts.
- scratch/*.py — engines, IC screens, event studies, hygiene experiments, scramble harness.
- scratch/candidates_raw.csv, rev_raw.csv, rev_distress_raw.csv, mom_final_raw.csv,
  mom_gate_raw.csv — raw candidate series.

## UNVERIFIED items
- Whether a POINT-IN-TIME constituent list (real delist handling) would revive the classic
  premia: UNVERIFIED (no delisted-name price file exists in this repo — panels are current
  constituents only; everything here is survivorship-biased in the documented direction).
- Vendor data quality beyond the |r|>25% hygiene (e.g., which zero prints are true trade
  days vs vendor errors): UNVERIFIED — no alternative source in repo to cross-check OTC prints.
- SR_m >= 5 feasibility for any future engine from this data: my results support LOOP_L16's
  INFEASIBLE verdict; nothing found that changes it.
