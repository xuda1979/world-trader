# V7.1 REPLICATION SPEC — single source of truth (standalone)
**REPLICATION CONTRACT:** this document alone must regenerate V7.1. Gate:
`python3 replicate_from_doc_v71.py` — it parses the §1 sleeve table from this file,
re-runs the §4 recipe (SLSQP, IS data only), and must reproduce the V7.0 vector
(max diff < S1_TOL, see §4.1), then applies the §4.2 zero+renorm transform to reach
the committed V7.1 weights. `python3 reproduce_v71.py` asserts the §6 canonical
numbers. If any number fails reproduction, STOP and investigate.

**PROVENANCE (governance):** V7.1 = V7.0 (V7_REPLICATION_SPEC.md, preserved byte-exact)
under the A4_ZERO_RENORM act of the HARD-STOP governance decision. The 2 decay-monitor
HARD stops (FXD1_KRWTRI_raw_daily.csv w 3.0%, crossasset_rev_L8.csv w 8.9%) were
zeroed from 2024-10-01 and the 18 survivors renormalized by 1/0.880835 = 1.135286.
Decision evidence: HARDSTOP_GOVERNANCE_MEMO_2026-09-30.md + V8GOV_ADOPTION_PACKAGE_2026-09-30.md
(committed CSVs regenerated post-E1-refresh, deterministic). Operator ACT decision
2026-09-29 (A4 zero+renorm over hold and over the 18-slv recipe re-solve, which
measured worse on all selection-free metrics and was rejected).

## 1. UNIVERSE (20 sleeves — exact files under `campaign/`)
| # | Sleeve file (relative to `campaign/`) | Weight |
|---|----------------------------------------|--------|
| 1 | `agents/C4_metaalloc/sleeves/C4_construct_v2.csv` | 17.029297% |
| 2 | `agents/COORD/sleeves/brwt7.csv` | 17.029297% |
| 3 | `agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_gasreg_nyh_gulf_L60Z1.0.csv` | 3.405859% |
| 4 | `agents/B2_highfreq/sleeves/crossasset_rev_L8.csv` | 0.000000% |
| 5 | `agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_9_3_L40Z1.5.csv` | 3.405859% |
| 6 | `team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv` | 12.586083% |
| 7 | `agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/calendar_vixterm_3_6_L20Z1.5.csv` | 3.405859% |
| 8 | `agents/A6_reversal/sleeves/a6_r2_pair_residmom_fm1926.csv` | 3.405859% |
| 9 | `agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv` | 5.673290% |
| 10 | `agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/crack_crack321_nyh_L60Z1.0.csv` | 3.405859% |
| 11 | `agents/loop_team/HUNT_FXDEPO/sleeves/FXD1_KRWTRI_raw_daily.csv` | 0.000000% |
| 12 | `agents/chief/coord/CAMP_COST/sleeves/diescrack__prefix.csv` | 3.405859% |
| 13 | `agents/loop_team/HUNT_CN_FUTURES/sleeves/cnpair_M0_RM0_L60Z1.5.csv` | 3.405859% |
| 14 | `agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv` | 3.405859% |
| 15 | `results/sleeve_library/Merger_Arb_PEAD_5pct.csv` | 3.405859% |
| 16 | `agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv` | 3.405859% |
| 17 | `agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT_intlcarry3_lag1_NEG.csv` | 3.405859% |
| 18 | `team/agents/RES_CREDIT/sleeves/RC_t102_d5mr_w21_band50_vt5.csv` | 3.405859% |
| 19 | `agents/loop_team/HUNT_CLASSIC_SPREADS/sleeves/inter_dieseljet_L60Z1.0.csv` | 3.405859% |
| 20 | `agents/chief/coord/HUNT_SECTOR2/sleeves/D_xlu_ief.csv` | 3.405859% |

Weight sum: 1.0000000000 | nonzero 18 | min 3.4059% | max 17.0293%

Zeroed sleeves (§4.2 HARD stops, w=0 from 2024-10): #4 `crossasset_rev_L8.csv`,
#11 `FXD1_KRWTRI_raw_daily.csv`. All others are live.

## 2. DATA CONVENTIONS (non-negotiable)
- Each sleeve CSV: first column = date (parse), return column = `ret` if present else first column.
- Drop NaN/±Inf rows. Daily returns are NET of sleeve-internal costs (campaign convention).
- Monthly return: compound within calendar month -> `(1+r_daily).resample("ME").prod()-1`.
- PORTFOLIO (static-weight marks, **realistic net** (financing + costs)**, daily basis:
  `r_net(d) = 1.6·Σ w_i·r_i(d) − 0.6·rate/252 − Σ_days |Δw|·6.4bp·legs`
  with rate = 5.3% (IBKR call rate), legs = 2 for the ten spread sleeves
  (brwt7, RB_hobr_crack, inter_gasreg, calendar_vixterm×2, crack_crack321,
  inter_dieseljet, diescrack, cnpair, D_xlu_ief), else 1.
- Windows: IS = dates < 2017-01-01 (fit window, historical only). OOS = ≥ 2017-01-01.
- WEIGHT SWITCH DATE: 2024-10-01. Before it, weights are V7.0's (the 20-sleeve solved
  vector). From it, weights are V7.1's (this document's §1 table: 2 zeros, survivors
  renormalized). This mirrors the governed act: the stops fired on data through
  2026-09-19 but the act applies the zeroing to the book from the first rebalance
  after the decision — the ledger convention used by the committed CSVs uses
  2024-10-01 (TRAIL2Y) so the trail2y evidence window is measured under the act.

## 3. PORTFOLIO RETURN
- `r_gross(d) = 1.6 × Σ w_i · r_i(d)` (gross of financing+costs, static weights of §1).
- Realistic net ledger: see §2 formula and OPT_20V71_FULL_LEDGER.csv (committed).

## 4. WEIGHT-CONSTRUCTION RECIPE (how V7.1 was made — reproducible)
- Objective: maximize IS monthly mean return `μ = mean_IS × 12`.
- Constraint: IS shrunk Sharpe ≥ 6.5, with `Σ = 0.3·C + 0.7·diag(C)`, `C = IS monthly cov × 12`.
- Bounds per sleeve: [3%, 15%]; weights sum to 1; post-solve floor re-applied then renormalize.
- Solver: SLSQP, maxiter 5000, ftol 1e-14, x0 = equal weight.
- Sleeve set: 20 honest-pool sleeves (no FAILED_NO_PROMOTION, no overlays, no MHX/HT_TAIL),
  selected on IS only (drop=0.35 decorrelation greedy, IS-SR>0) — fixed list in §1; DO NOT reselect.

### 4.1 S1 WEIGHT-REPLICATION TOLERANCE (retired to baseline by this V# bump)
- Baseline tolerance: **1e-6** (recipe must regenerate committed weights to 1e-6 whenever
  the sleeve inputs are unchanged since the weights were solved).
- The V7.0 3e-4 vintage-drift pin (F-F 202608 a6 restatement, pinned 2026-09-26) is
  RETIRED by this governed V# bump per its own documented retirement condition.
- The recipe (§4) still regenerates the V7.0 vector from the same solve: replication
  of V7.1 = (recipe re-solve → V7.0 vector) + (§4.2 zero+renorm transform). A
  zero+renorm is NOT a re-solve. The S1 gate decomposes (gate: replicate_from_doc_v71.py):
  (i) §4.2 transform applied to the COMMITTED V7.0 vector must reproduce committed
  V7.1 weights to **1e-6** (exact arithmetic; float noise only — measured 9.0e-17);
  (ii) the recipe re-solve stage carries V7.0's attributed a6-restatement drift
  (3e-4 pinned per V7_REPLICATION_SPEC.md §4.1), and the full doc path
  (recipe+transform) is gated at 1.135286 × 3e-4 (renorm amplification of the
  attributed stage-1 drift; no additional error allowed).
- Any OTHER sleeve restating its IS window re-opens S1: the gate will RED at >1e-6
  on the transform stage only if the committed V7.0 vector itself changes; a
  material (w>10%) sleeve restating IS data should trigger a governed re-solve
  instead of a new pin.

### 4.2 THE ZERO+RENORM TRANSFORM (V7.0 → V7.1, exact)
- Take the committed V7.0 weights (OPT_20V7_weights.csv, FROZEN).
- Set `w[FXD1_KRWTRI_raw_daily.csv] = 0` and `w[crossasset_rev_L8.csv] = 0`
  (the 2 decay-monitor HARD stops; monitor exit 2 since 2026-09-19, commit b9f8dee).
- Renormalize: `w71 = w / w.sum()` (survivors scale by 1/0.8808349436825245 =
  1.135286476963869).
- The result is the committed OPT_20V71_weights.csv (byte-exact by construction).

## 5. METRIC DEFINITIONS (official)
- **Annual return = ARITHMETIC = monthly mean × 12. NEVER geometric.**
- SR quoted on MONTHLY basis: `mean/std of monthly net × √12` (daily×√252 overstates: +autocorr).
- MaxDD: daily-compounded net equity vs running max.
- Negative months/years: count of net compound returns < 0.

## 6. CANONICAL NUMBERS (reproduce_v71.py asserts these)
| Metric | Value |
|--------|-------|
| Full-window SR (monthly, net ledger) | 4.0792 |
| OOS SR (monthly, net ledger) | 3.6718 |
| Full ann, net ledger (arith) | 27.969%/yr |
| OOS ann, net ledger (arith) | 30.481%/yr |
| trail2y SR (monthly, net ledger) | 3.9223 |
| trail2y ann (net ledger) | 28.125%/yr |
| Daily MaxDD (net ledger) | -3.161% |
| Negative years (full and OOS) | 0 |
| H1/H2 SR (net ledger) | 5.671 / 3.5790 |

(All values = the A4_ZERO_RENORM row of the committed V8GOV_EVAL_2026-09-30.csv,
regenerated post-E1-refresh on the 105,636-row ledger, recon 1.04e-17; REFRESHED
2026-09-30 by the RB_hobr FRED data refresh — DHOILNYH/DCOILBRENTEU extended
2026-08-26..2026-09-22, +19 rows each, append-only, overlap exact; V7.1 ledger
105,590 rows. Prior vintage: full SR 4.0740 / OOS SR 3.6648 / OOS ann 30.455%.)

## 7. DECAY-MONITOR HISTORY (governance log)
- 2026-09-19: decay monitor first exited 2 (2 HARD stops): FXD1_KRWTRI_raw_daily.csv
  (trail2y SR -0.52), crossasset_rev_L8.csv (trail2y SR -0.10). Commit b9f8dee vintage.
- 2026-09-30: HARDSTOP_GOVERNANCE_MEMO_2026-09-30.md + V8GOV_ADOPTION_PACKAGE_2026-09-30.md
  landed (5-arm counterfactual + 18-slv re-solve comparison; both deterministic).
- 2026-09-29 (operator decision, executed this session): ACT — A4 zero+renorm adopted
  via this V7.1 spec bump. The 18-sleeve recipe re-solve (V8GOV) was evaluated and
  REJECTED (loses to A4 on all selection-free metrics: full SR -0.116, OOS SR -0.047,
  OOS ann -0.59pp, deeper DD; mechanism: dropping XREV unbinds the SR>=6.5 corner and
  forces the solver to raid C4).
- The monitor continues to run against V7.0 weights for sleeve-health REPORTING (the
  2 stopped sleeves remain visible in it until their files retire); its exit-2 state
  is acknowledged as ACTED-ON, not open.

## 8. CHANGE CONTROL
Any edit to weights/conventions invalidates this document. New versions = new V# spec file.
V7_REPLICATION_SPEC.md (V7.0) is preserved byte-exact as superseded history.

## 9. NET-RETURN CONVENTIONS
- LEDGER convention (committed OPT_20V71_FULL_LEDGER.csv): static-weight marks with the
  §2 weight switch; costs from the ledger's own trade rows. Used for daily post-trade
  verification (`reproduce_v71.py`). OOS net ann 30.481%/yr, monthly SR 3.6718.
- DEPLOYMENT convention (drifted weights, monthly rebalance, `backtest_pseudocode_v71.py`):
  **31.13%/yr OOS (arith), monthly SR 3.65, daily DD -3.18%, 0 neg years** — canonical
  for live. Drift capture +0.68pp over ledger, the same pattern as V7.0 (+0.67pp).
- Evaluation CSVs (V8GOV_EVAL_2026-09-30.csv A4 row, HARDSTOP_COUNTERFACTUAL_2026-09-30.csv
  A4 row) are the same engine on the same panel — cross-check values to 4dp.
