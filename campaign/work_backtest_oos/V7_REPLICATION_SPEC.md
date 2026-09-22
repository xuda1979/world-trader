# V7 REPLICATION SPEC — single source of truth (standalone)
**REPLICATION CONTRACT:** this document alone must regenerate V7. Gate:
`python3 replicate_from_doc.py` — it parses the §1 sleeve table from this file,
re-runs the §4 recipe (SLSQP, IS data only), and must reproduce the §1 weights
(max diff < 1e-6) AND the §6 canonical metrics. Exit 0 = document is valid for
live trading; non-zero = document is stale, STOP.
Generated 2026-09-21 from committed artifacts. Live trading uses ONLY this document
plus `replicate_from_doc.py` (doc→weights→metrics gate) and `reproduce_v7.py` (post-trade verifier). If any number below fails reproduction, STOP and investigate.

## 1. UNIVERSE (20 sleeves — exact files under `campaign/`)
| # | Sleeve file (relative to `campaign/`) | Weight |
|---|----------------------------------------|--------|
| 1 | `agents/C4_metaalloc/sleeves/C4_construct_v2.csv` | 15.000000% |
| 2 | `agents/COORD/sleeves/brwt7.csv` | 15.000000% |
| 3 | `agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_gasreg_nyh_gulf_L60Z1.0.csv` | 3.000000% |
| 4 | `agents/B2_highfreq/sleeves/crossasset_rev_L8.csv` | 8.916506% |
| 5 | `agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_9_3_L40Z1.5.csv` | 3.000000% |
| 6 | `team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv` | 11.086262% |
| 7 | `agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_3_6_L20Z1.5.csv` | 3.000000% |
| 8 | `agents/A6_reversal/sleeves/a6_r2_pair_residmom_fm1926.csv` | 3.000000% |
| 9 | `agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv` | 4.997232% |
| 10 | `agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_crack321_nyh_L60Z1.0.csv` | 3.000000% |
| 11 | `agents/loop_team/HUNT_FXDEPO/sleeves/FXD1_KRWTRI_raw_daily.csv` | 3.000000% |
| 12 | `agents/chief/coord/CAMP_COST/sleeves/diescrack__prefix.csv` | 3.000000% |
| 13 | `agents/loop_team/HUNT_CN_FUTURES/sleeves/cnpair_M0_RM0_L60Z1.5.csv` | 3.000000% |
| 14 | `agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv` | 3.000000% |
| 15 | `results/sleeve_library/Merger_Arb_PEAD_5pct.csv` | 3.000000% |
| 16 | `agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv` | 3.000000% |
| 17 | `agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT_intlcarry3_lag1_NEG.csv` | 3.000000% |
| 18 | `team/agents/RES_CREDIT/sleeves/RC_t102_d5mr_w21_band50_vt5.csv` | 3.000000% |
| 19 | `agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_dieseljet_L60Z1.0.csv` | 3.000000% |
| 20 | `agents/chief/coord/HUNT_SECTOR2/sleeves/D_xlu_ief.csv` | 3.000000% |

Weight sum: 1.0000000000 | min 3.0000% | max 15.0000%

## 2. DATA CONVENTIONS (non-negotiable)
- Each sleeve CSV: first column = date (parse), return column = `ret` if present else first column.
- Drop NaN/±Inf rows. Daily returns are NET of sleeve-internal costs (campaign convention).
- Monthly return: compound within calendar month -> `(1+r_daily).resample("ME").prod()-1`.
- Panel start: 2009-01-01. Missing sleeve-months (sleeve not yet live): value **0.0** (`fillna(0)`).
- NO other cleaning. No resampling of weekly prints. No forward fill of returns.

## 3. PORTFOLIO RETURN
- Static weights (never refit). Portfolio gross monthly return `G_m = Σ w_i · r_i(m)`.
- **Gross levered (headline convention)**: `R_gross = 1.6 × G_m`.
- **Realistic net (financing + costs)**, daily basis:
  `r_net(d) = 1.6·Σ w_i·r_i(d) − 0.6·rate/252 − Σ_days |Δw|·6.4bp·legs`
  with rate = 5.3% (IBKR call rate), legs = 2 for the ten spread sleeves
  (brwt7, RB_hobr_crack, inter_gasreg, calendar_vixterm×2, crack_crack321,
  inter_dieseljet, diescrack, cnpair, D_xlu_ief), else 1.
- Windows: IS = dates < 2017-01-01 (fit window, historical only). OOS = ≥ 2017-01-01.

## 4. WEIGHT-CONSTRUCTION RECIPE (how V7 was made — reproducible)
- Objective: maximize IS monthly mean return `μ = mean_IS × 12`.
- Constraint: IS shrunk Sharpe ≥ 6.5, with `Σ = 0.3·C + 0.7·diag(C)`, `C = IS monthly cov × 12`.
- Bounds per sleeve: [3%, 15%]; weights sum to 1; post-solve floor re-applied then renormalized.
- Solver: SLSQP, maxiter 5000, ftol 1e-14, x0 = equal weight.
- Sleeve set: 20 honest-pool sleeves (no FAILED_NO_PROMOTION, no overlays, no MHX/HT_TAIL),
  selected on IS only (drop=0.35 decorrelation greedy, IS-SR>0) — fixed list in §1; DO NOT reselect.

## 5. METRIC DEFINITIONS (official)
- **Annual return = ARITHMETIC = monthly mean × 12. NEVER geometric.**
- SR quoted on MONTHLY basis: `mean/std of monthly net × √12` (daily×√252 overstates: +autocorr).
- MaxDD: daily-compounded net equity vs running max.
- Negative months/years: count of net compound returns < 0.

## 6. CANONICAL NUMBERS (reproduce_v7.py asserts these)
| Metric | Value |
|--------|-------|
| IS SR (gross, monthly) | 6.3821 |
| OOS SR (gross, monthly) | 4.0983 |
| OOS arithmetic ann, gross 1.6x (headline) | 33.7243%/yr |
| OOS MaxDD (gross, monthly) | -0.8000% |
| Full-window SR (gross) | 4.5946 |
| OOS neg years (gross) | 0 |
| Realistic net @5.3% — LEDGER convention (static-weight marks) | 29.66%/yr |
| Realistic net @5.3% — DEPLOYMENT convention (drifted weights, pseudocode S3-S4) | **30.33%/yr (canonical for live)** |
| Realistic net: monthly SR | 3.63 ledger / 3.62 deployment |
| Realistic net: daily MaxDD | -3.16% ledger / -3.18% deployment |
| Realistic net: neg months (OOS) | 14/117 (both conventions) |

## 7. LIVE (IBKR PAPER) RUNBOOK
1. Browser-download **IB Gateway stable standalone (macOS)** from IBKR (site blocks CLI here);
   install to /Applications. Python side is ready: `ib_async 2.1.0` installed.
2. Launch Gateway → login with **PAPER** credentials → Global Configuration → API → Settings:
   ✅ Enable ActiveX/Socket Clients, port **4002**, trusted 127.0.0.1.
3. Dry run (no orders): `python3 campaign/ibkr_v7_engine.py --dry-run`
4. Paper live:        `python3 campaign/ibkr_v7_engine.py --live`
5. Reconcile daily: engine logs vs `OPT_20V7_FULL_LEDGER.csv` (tolerance 5bp/day).
6. Mapping status: energy/curve/VIX sleeves map to futures combos (BZ/CL, HO, RB, NG, VX, ZT/ZN).
   Pure-research sleeves (C4, Merger_Arb, crossasset_rev internals) trade as PROXIES in pilot;
   do not scale until 1:1 mapping is validated. Pilot sizing: see margin note (~6.4% NAV).

## 8. CHANGE CONTROL
Any edit to weights/conventions invalidates this document. New versions = new V# spec file.

## 9. NET-RETURN CONVENTIONS (why two numbers)
- LEDGER convention (29.66%): marks PnL on STATIC weights; costs from the committed
  blotter. Slightly conservative; used for daily post-trade verification
  (`reproduce_v7.py`).
- DEPLOYMENT convention (30.33%): marks PnL on DRIFTED weights — positions ride
  between monthly rebalances, exactly as the live account behaves (pseudocode S3-S4).
  `backtest_pseudocode.py` gates on this. Difference (+0.67pp) is drift capture.
- Both: 14 negative months / 0 negative years OOS. Ann = ARITHMETIC.
