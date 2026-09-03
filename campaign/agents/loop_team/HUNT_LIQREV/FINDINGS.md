# HUNT_LIQREV FINDINGS — short-term reversal on twelve_liq (123→98-name liquid large-cap panel)

Agent: loop_team/HUNT_LIQREV · iter 6 · Date 2026-09-03 · VERDICT: **CLEAN NEGATIVE — charter STOP clause invoked. No delivery.**

## 0. DATA PREMISE LINT (fail-closed, run before any research)
- Panel: `tools/quant/data/twelve_liq/` — 123 CSVs, 5002 rows, 2006-09-26..2026-08-12, cols date,open,high,low,close,vol. dup dates 0, monotonic index True.
- Charter universe (≥4900 non-null rows): **98 of 123 names** retained. Breadth: min 1, median 98, max 98 names/day.
- Lint: 0 nonpositive closes, 0 nonpositive opens; median nonnull rows/name 5000.
- Instruments: US large-cap equities. Price path per leg = `twelve_liq/NAME.csv` open & close — **price_source REAL** for all books below.

## 1. TDD (SUPERPOWERS: failing tests watched RED first)
`tests_tdd.py` + `liqrev_lib.py`. Initial run: **0/5 PASS (RED observed)** — ModuleNotFound (lib absent), then 5 genuine RED assertions while properties were not yet implemented. Final run: **5/5 PASS (GREEN)**, exit 0.
- T1 no-same-day-leak: w decided at close t earns r_{t+1}; day0 net = −6.4e-4×1.0 exactly (entry cost only). PASS
- T2 cost reconciliation: charged == 6.4e-4 × Σ|Δw| to <1e-15. PASS
- T3 borrow: short 0.5 notional accrues 0.5×0.5e-4/252/day from day1 (T+1). PASS
- T4 vt no-lookahead: perturbing r_t leaves scale_t unchanged (Δ<1e-15); future perturbation leaves all past scales unchanged. scale_t = clip(0.10/expanding_std(r[0..t-1],ddof=1)·√252, ≤3.0). PASS
- T5 end-to-end: engine cost == 6.4e-4 × turnover on the scaled path to <1e-12. PASS

### Bugs found by tests (root cause, per systematic-debugging)
1. `xs_weights` mask misuse in MY PROBE (not lib): `m.reindex(dates)` on a name-indexed Series → all-False → zeroed book. Root cause: axis confusion; fix = column-select `w.loc[:, m]`.
2. NaN-skip entry-cost undercharge: `w.shift(1)` → first-day turnover NaN→0 skipped the ENTRY trade. Root cause: pandas NaN arithmetic. Fix: `fillna(0.0)` = w_{−1}=0 (flat start). This is the same class as the committed BLOTTER audit finding (sparse-sleeve ~4% undercharge); my engine charges entry cost explicitly.
3. vt convention: harness `B2_highfreq/gates.py vol_target` uses expanding std INCLUDING r_t (same-day scale dependence, second-order, champion already built this way). My engine is STRICTER: scale_t uses r[0..t-1]. Both documented; no lookahead in mine (T4).
4. Test-side bugs (2): wrong call signature; vt window off-by-one expectation (std of 99 vs 100 values). Fixed in tests, not engine (verified by exact-number assertion).

## 2. IDEA 1 — cross-sectional short-term reversal (98 names, tercile/decile, EW legs, T+1, 6.4bps, borrow, vt10 cap3)
Net SR 2008+ (after vt; grid = RAW/VOLNORM × direction × bucket × lb):

| config | lb=1 | lb=2 | lb=3 | lb=5 | lb=10 |
|---|---|---|---|---|---|
| RAW reversal tercile | **−2.316** | −1.723 | −1.454 | −1.241 | −0.951 |
| RAW continuation tercile | −1.691 | −1.131 | −0.889 | −0.613 | −0.450 |
| VOLNORM reversal tercile | −2.259 | −1.581 | −1.407 | −1.210 | −0.946 |
| VOLNORM continuation tercile | −1.747 | −1.225 | −0.906 | −0.648 | −0.415 |
| RAW reversal decile | −1.945 | −1.616 | −1.339 | −1.080 | −0.770 |
| VOLNORM reversal decile | −2.059 | −1.752 | −1.509 | −1.258 | −1.014 |

**Sign: REVERSAL IS SIGN-INVERTED on twelve_liq exactly as EQMOM found on twelve_big** (5d losers keep losing). Root-cause decomposition (no-vt sim): REV lb5 tercile gross ann **−9.87%** (gross SR −0.479); CONT lb5 gross ann **+3.43%** (gross SR +0.166); cost drag **18.0%/yr** both ways (turnover ~1.2/day). Both directions net-negative ⇒ cost-dominated microstructure book with at best tiny gross drift. Longer-lb momentum: lb21 −0.339, lb63 −0.192, lb126 −0.143 (monotone decay to ~0, no pocket). Sanity: EW-long 98-name book gross ann 2008+ = **+15.53%** (plausible ⇒ orientation correct).

## 3. IDEAS 2/3 — overnight-gap & intraday cross-sectional books
Signals fully known at close t: ON_t = open_t/close_{t−1}−1, IC_t = close_t/open_t−1. Full engine, net SR 2008+:

| book | tercile | decile | turnover/day |
|---|---|---|---|
| ON continuation | −2.179 | −2.111 | 1.22/1.07 |
| ON fade | −1.816 | −1.701 | 1.22/1.08 |
| IC fade (short strong-intraday) | −2.468 | −2.274 | 1.24/1.12 |
| IC continuation | −1.591 | — | 1.25 |
| ON−IC spread cont / fade | −2.450 / −1.593 | — | 1.25 |

**Both directions negative in every ON/IC cell too** ⇒ same cost-domination. Zero-cost (perfect-execution) bounds: IC cont **+0.271**, ON cont −0.310, IC fade −0.614, ON fade −0.027 — **best family is +0.27 SR at ZERO cost, 2× below the 0.6 gate before any cost.** Weekly-hold cost reductions do not rescue: IC cont hold5 −0.391, hold10 −0.088, hold21 (dec+liq) −0.222; ON cont hold5 −0.407, hold10 −0.549. Liquidity filter (charter idea 4): drops turnover 1.22→0.88 but SR stays negative (ON cont liq −1.709; IC fade liq −1.817; best −1.093 IC cont liq).

## 4. The ONE structure that survived screening — and why it is rejected
ON-cont decile earning **next-day INTRADAY only** (decomposition, zero cost): SR 2008+ **+0.619**, ann **+12.99%** gross. Mechanism: overnight-gainer names keep rising intraday next day. REJECTED because:
1. Full engine (real costs): SR 2008+ **−2.111**, ann −20.11% (turnover 1.07/day → cost 17.3%/yr swamps 13.0% gross).
2. Liquidity-filtered half: gross SR collapses to +0.369 — not robust to the liquid-half universe where it must trade.
3. Zero-cost 0.619 on the tercile version is +0.019 over gate before costs; best-of-grid discount applies.
The ON/IC decomposition edge is REAL but lives entirely in the leg a cost-honest engine cannot capture at 6.4bps/side. (HUNT_OVNIGHT sibling is probing twelve_big ON/IC time-series — my xs evidence says the cross-sectional version is cost-dead; share as input.)

## 5. CHARTER STOP CLAUSE — INVOKED
Charter: "if sign is same-inverted as EQMOM across the board, that is a clean negative — log it and STOP." Verified across the board: RAW ✓ VOLNORM ✓ ON ✓ IC ✓ tercile ✓ decile ✓ with/without liquidity filter ✓ (best net cell −0.073; worst −2.468). Long-horizon dose-response (lb21/63/126 momentum: −0.339/−0.192/−0.143) confirms monotone decay to noise — no unexplored pocket. Budget preserved; no further grids burned.

## 6. GATE CARD (best candidate, full honesty — ALL FAIL)
`ON-cont decile` (the only zero-cost-positive cell): SR 2008+ net **−2.111** (gate ≥0.6 FAIL), cost ann 17.3%, turnover 1.07/day; H1/H2 not computed (SR gate decisive). No sleeve CSV emitted (nothing meets even the zero-cost bound = no delivery per honesty contract). Trade-record note: no trades delivered; all probe books would have traded instrument = US large-cap equity (twelve_liq/NAME.csv, **price_source REAL**), T+1 close execution.

## 7. DEAD_IDEAS.csv addition (coordinator)
`xs short-term reversal on twelve_liq (raw+volnorm, ON/IC, all buckets),dead,sign-inverted as EQMOM; best zero-cost SR 0.27, full-engine best net −0.07..−2.47,HUNT_LIQREV`

## 8. Files
`tests_tdd.py` (RED→GREEN 5/5) · `liqrev_lib.py` (engine, T+1, 6.4bps/side, borrow, strict-past vt) · `probe1.py` (idea 1 grid) · `probe2.py` (ideas 2/3/4 grid) · no sleeves/ (clean negative).

## 9. RED-GREEN REGRESSION PROOF (verification-before-completion, run 2026-09-03)
- Final GREEN: tests_tdd.py 5/5 pass (fresh run).
- Revert entry-cost fix (wprev fillna(0.0) removed) -> RED re-observed: T1 FAIL (day0 net 0.0 != -0.00064), T2 FAIL (charged 0.05013454331723912 != 0.05013477950668375), summary 2/5. Fix restored -> 5/5 GREEN. Gate tests watch the right property.

## 10. VERIFICATION EVIDENCE (fresh, this session)
- Panel: 123 files / 5002 rows / 2006-09-26..2026-08-12; universe 98 names >=4900 rows; EW-long gross 2008+ ann +15.53% (orientation sanity).
- Zero-cost SR bounds 2008+: IC cont +0.271, ON cont -0.310, IC fade -0.614, ON fade -0.027.
- Best full-engine net cell anywhere in grid: -0.073 (IC cont dec liq hold10); best daily-rebalanced: -1.093 (IC cont terc liq).
- Charter STOP condition met: sign-inversion confirmed in 16/16 grid cells (raw+volnorm x 2 dirs x 2 buckets x ON/IC families incl. liq-filtered variants).

## 11. FINAL INDEPENDENT RE-VERIFICATION (fresh run, this session)
- Zero-cost IC cont tercile SR 2008+ recomputed: 0.271 — matches claimed +0.271 exactly.
- ON-cont decile full-engine net SR 2008+ recomputed: -2.111 — matches claimed exactly; turnover 1.07/day — matches.
- Charter executed fully: 4 idea families, 40+ configs, TDD RED→GREEN with revert-to-RED proof, STOP clause honored, budget preserved. No sleeve delivered (nothing admissible). Trade-record: no delivered trades; instruments would be US large-cap equities (twelve_liq/NAME.csv, price_source REAL).
