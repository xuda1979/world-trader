# AUDIT2_sleeves — forensic audit of the 16-sleeve champion pool (read-only)
Agent: AUDIT2_sleeves | Date: 2026-09-01 | Method: code read + raw-data re-derivation + zero-run replay + materiality what-ifs. Scratch scripts in `scratch/`. No campaign file was modified.

## 0. VERDICT TABLE (12 charter sleeves + 4 additional pool members)

| Sleeve | Repro vs committed CSV | T+1 discipline | Zero-run explanation | Verdict |
|---|---|---|---|---|
| H21_f5 | **FAIL** (best corr 0.685, maxdiff 6.3e-2; no code/cache state reproduces) | **VIOLATION: day-0 MTM entry** (contrarian, hurts returns) | 152 zeros = panel holidays/1 Sunday + book-boundary gaps; 0 on rebalance grid | **FLAG** |
| H21_br | **FAIL** (best corr 0.904; generator state predates all git commits of producer) | UNVERIFIED (file not reproducible; likely same day-0 convention as H21_f5) | same as H21_f5 | **FLAG** |
| XGB1y | **EXACT** (daily = monthly book spread; total cum diff 7e-13; 204/213 months exact) | OK (monthly PIT purged WF; slice k=0 books ret_next(m0)=m0→m0+1 close) | 273d lead-in zero = pre-first-cohort warmup (first cohort 2009-02) | PASS (see 6.3 leverage note) |
| A5r7 | IDENTICAL (maxdiff 1.0e-16, n=9163) | OK (pos shift1, vt shift1, hedge shift1) | all 9 runs ≥100d gate-explained (z-hysteresis) | PASS |
| A5r2 | IDENTICAL (maxdiff 9.98e-17, n=4249) | OK (pos=P.shift(1), vt shift1) | 112d run = rate-shock veto; verified | PASS (but dup w/ A5r4, §7.2) |
| A5r4 | IDENTICAL (maxdiff 1.00e-16, n=4249) | OK (same code as A5r2) | same 112d run | **FLAG**: corr=1.000 to A5r2, yet counted as pool member |
| a6r7 | IDENTICAL (maxdiff 9.98e-17, n=4918) | OK (W.shift(1)*tr, vt shift1) | 461d run = trend gate, verified exactly | PASS |
| A1inf | IDENTICAL to committed (maxdiff 9.97e-17) — **but committed file itself carries a leak** | **VIOLATION: signal(t) paired with return(t−1→t)** | none (0 zeros) | **FAIL** |
| QAxasts | IDENTICAL (maxdiff 9.98e-17, n=4679) | OK (wback_rb: weights t→effective t+1) | 55d run = MA189 warmup | PASS |
| dualmom | IDENTICAL (maxdiff 9.98e-17, n=4743) | OK (W[t] applied from t+1; cost at t+1) | 250d run = FF-mkt 200d-MA band gate, verified exactly | PASS |
| carryv2 | IDENTICAL (maxdiff 9.98e-17, n=4848) | OK (all 3 members shift1) | 60d run = z-window warmup | PASS |
| brwt | IDENTICAL (maxdiff 9.98e-17 on 4560 common rows; file's 59 leading NaN = vt warmup) | OK (pos at close t earns sp.diff().shift(−1); cost half-turn correct) | 33d interior run: max|z|=1.471<1.5 flat-by-design; 59d lead-in = z warmup | **FLAG**: harness vt has no shift(1) → +0.10 SR inflation |
| B3momhml | IDENTICAL (maxdiff 9.98e-17, n=5154) | OK (pos.shift(1)*combo, vt shift1) | 61d warmup | **FLAG**: own meta says "NOT gate-passing reference"; sits in champion pool |
| C5ng | IDENTICAL (maxdiff 9.99e-17, n=4641) | OK (pos at close t earns lr.shift(−1)=log s_{t+1}/s_t) | max run 7d (calm-filter) | PASS (same vt shift note as brwt) |
| C5ngsum | IDENTICAL (maxdiff 9.98e-17, n=4641) | OK | ALL 18 runs ≥97d are Nov→Mar/Apr winter flat — by design | PASS (same vt note) |

Champion assembly: `champion_build.py --verify` → all 3 configs **IDENTICAL**, max|new−old| ≈ 9.99e-17, n=4696 (float-noise only). SAFE: ann 48.5% SR 5.18 DD −7.3%; AGGRESSIVE: 62.4% / 5.27 / −7.9%; BALANCED 55.5% / 5.24 / −6.9%.

## 1. Reproduction runs (recomputed from raw inputs, compared to committed CSV)
All comparisons: inner join on dates, max abs diff. "IDENTICAL" = < 1e-12.

- a6r7 (campaign/scripts/a6_r7_bond2y_trend.py logic re-run): n=4918/4918, corr 1.000000, maxdiff 9.975e-17 → IDENTICAL
- A1credit (a1_credit_regime.py re-run): n=9503/9503, 1.000000, 9.986e-17 → IDENTICAL
- A1inf (a1_inflation_breadth.build()): n=4825/4825, 1.000000, 9.975e-17 → IDENTICAL
- carryv2 (a1_carry_seasonal.sleeve): n=4848/4848, 1.000000, 9.980e-17 → IDENTICAL
- A5r2 (module import): n=4249/4249, 1.000000, 9.975e-17 → IDENTICAL
- A5r4 (module import): n=4249/4249, 1.000000, 9.996e-17 → IDENTICAL
- brwt (backtest_brwt_spread_rev15.run + B2 vol_target): n=4560/4619, 1.000000, 9.975e-17 → IDENTICAL (59-row NaN warmup tail in file)
- C5ng, C5ngsum (run()): n=4641/4641 each, 1.000000, ≤9.99e-17 → IDENTICAL
- B3momhml (inline re-run): n=5154/5154, 1.000000, 9.975e-17 → IDENTICAL
- QAxasts (inline re-run of wback_rb pipeline): n=4679/4679, 1.000000, 9.975e-17 → IDENTICAL
- dualmom (inline re-run): n=4743/4743, 1.000000, 9.975e-17 → IDENTICAL
- A5r7 (inline re-run): n=9163/9163, 1.000000, 1.0e-16 → IDENTICAL; recomputed SR 1.51 / ann 4.8% = meta claims
- XGB1y: daily file = constant-per-month spread of tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv: corr 1.000000, per-month maxdiff 3.4e-15; cum total 13.162326295611393 vs 13.162326295610706 (7e-13). Spread convention: day in month m carries pnl(m)/n_days(m) — 204/213 constant months exact at offset 0, next-best offsets ≤3 votes.
- **H21_f5: NOT REPRODUCIBLE.** Tried every committed portfolio-code state (1d4ddb5, 82733af, a407c4c, 5e2713a, 028c84f, HEAD 6cd93b0) × every pred cache (horizon_preds.pkl, _20y.pkl, _20y_f5.pkl, _20y_f5fix.pkl, _20y_f6.pkl), raw and vol-targeted: corr ranges 0.21–0.69. Best: HEAD+f5.pkl+vt → corr 0.6845, maxdiff 6.3e-2. The committed CSV's own stats (SR 1.9165, ann 32.4%) match neither the committed multi_horizon_book_results_f5.json vt row (SR 1.847, ann 31.1%) nor any rebuild (best vt SR 1.988/raw 1.807). Also h21_breadth_gate_daily.csv mtime 16:41:57 predates the first git commit of its producer (17:05) and the f5 pred cache (17:36): the exact generator state is NOT in git → **UNVERIFIED provenance; not frozen**.
- **H21_br: NOT REPRODUCIBLE EXACTLY.** Best: horizon_preds_20y.pkl + survivor-in filter (tickers with data ≤2007-02) + causal breadth gate (shift(1), 0.35/0.80→0.5, per xgb_horizon_ddfilter.py recipe): corr 0.9043, maxdiff 7.6e-2. With f5 cache: 0.4559. UNVERIFIED exact construction.

## 2. Zero-run forensics (charter mandate) — every coordinator number confirmed and explained
Measured longest interior zero-runs (rows with |ret|<1e-12): A5r7 367d (2014-09-30..2016-03-18), a6r7 461d (2021-11-29..2023-09-29), A5r2/A5r4 112d (2022-08-09..2023-01-18), XGB1y 273d lead-in (2008-01-02..2009-01-30; 113 zero rows inside the champion window from 2008-09-01 — coordinator's "105" consistent up to window/row-count convention), dualmom 250d (2022-02-02..2023-01-31), C5ngsum 111d (2016-11-01..2017-04-04), brwt 33d (2016-05-02..2016-06-16).

Gate replay (recomputed from raw data, compared day-by-day to the committed CSVs):
- **a6r7**: signal = 378-obs mean of synthetic 2y TR > 0, W frozen every 42 obs. Rolling mean went negative 2021-10-15 (−8e-6 around run start) and positive 2023-09-22; W.shift(1)==0 for **every** row of the 461d run; file all-zero across run: TRUE. FLAT-BY-DESIGN.
- **A5r2/A5r4**: contango state C=1 for the entire 112d window (no exit); rate-shock veto RS=0 throughout (US10y 2.78–4.25%, 150d Δ up to +215bp > +25bp and > 2.75%); veto lifts 2023-01-18; P.shift(1)==0 across run; file all-zero: TRUE. FLAT-BY-DESIGN.
- **A5r7**: all 9 zero-runs ≥100d replayed against the z-hysteresis gate (enter z<0.5, exit z>0.75 on DAAA−DBAA z(252d)): exit z at run starts 0.73–2.79 (>0.75), re-entry z at run ends 0.32–0.50 (<0.5); gate position series zero across each run; file all-zero in each: TRUE. (Also 363d run 2007-11-19..2009-05-01 = GFC credit stress exit — economically sensible.) FLAT-BY-DESIGN.
- **dualmom**: gate=0 at decision month-end 2022-01-31 (mkt = 0.964× 1.03·MA200, inside/below exit band), 0 at every month-end through 2023-01-30, back to 1 on 2023-01-31; weights stay 0 through the run (last off-gate month-end books flat from next day); file all-zero in run: TRUE. FLAT-BY-DESIGN.
- **brwt**: |z(15d)| < 1.5 on every day of the 33d run; max |z| in window 1.471. FLAT-BY-DESIGN (band gate).
- **C5ngsum**: every zero-run ≥97d starts in October/November and ends in March/April — exactly the Apr–Oct season filter (18 consecutive winters). FLAT-BY-DESIGN.
- **XGB1y**: 273d lead-in zeros end 2009-01-30; first cohort forms 2009-02 (FIRST_ENTRY=(2009,2) in xgb_1y_deploy.py). WARMUP, by design.
- **H21_f5/H21_br**: 152 zero days each; **0 on the rebalance grid** (rebal = panel dates[::21]); pattern = single days at month-ends (book expiry boundary when a rebalance is skipped because n<2K+2 names) + holidays with empty panel (2008-11-28) + **one Sunday row 2009-07-26 in the source panel** (data-quality artifact; all-zero, no PnL invented). No strategy-gate zero-runs exist; not missing data (all zeros coincide with panel gaps/book boundaries).
**No unexplained zero-run found. No sleeve FAILs on the zero-run criterion.**

## 3. T+1 / lookahead discipline per sleeve
- **H21_f5 — VIOLATION (same-day entry, contrarian sign).** build_position_book credits `daily_ret.loc[rb]` (close rb−1→rb) to the tranche formed at close rb using close-rb features. On the committed file: mean rebalance-day return −0.43% vs +0.14% other days (t=−5.32); −17.8% of cumulative PnL sits on 216 day-0 rows; zeroing day-0 raises SR 1.9165→2.3644. On the raw rebuild: day-0 MTM mean −0.63%/day (t=−3.41), SR 1.807→2.263 when day-0 is set to cost-only. So the leak is AGAINST the strategy (depresses returns) — an honesty positive, but the charter's criterion is mechanical: positions earn PnL the same day their signal was computed → **mechanical T+1 FAIL, favorable-materiality**.
- **H21_br — UNVERIFIED** (file not reproducible; produced by the same build_position_book family → same day-0 convention likely).
- **A1inf — VIOLATION (same-close signal, pro-cyclical, INFLATES).** `ex = sig*rets` where sig is computed from prices through close t and rets = close t−1→t. The `lev.shift(1)` only lags leverage, not the signal. Correction sig.shift(1): SR 1.146→0.643, ann 12.5%→7.0%, neg years 1→5, worst −0.7%→−3.8% (gate-a 0.7 would now pass only marginally; the r6 half/halves claims do not survive). 173/4834 days have signal flips. **This sleeve FAILS the charter's same-day criterion and its committed stats are inflated.**
- **brwt / C5ng / C5ngsum — minor**: campaign/agents/B2_highfreq/gates.vol_target scales day t by expanding std INCLUDING day t (no shift). Effect (recomputed): brwt SR 2.500 as-is vs 2.400 with shifted vt; C5ngsum 2.192 vs 2.161. Direction: slight inflation (~0.03–0.10 SR), undisclosed.
- All other 12 sleeves: shift(1) on signal/positions and trailing shift(1) vol-target verified in code (a5_r6_lib.build_net L15–22; a5_r2/r4 L38–42; a6_r7 W.shift(1)*tr; a1_credit pos.shift(1); a1_infl lev.shift(1) — note its residual leak above; carryv2 members shift(1); dualmom W applied t+1 cost t+1; QA_xasts via wback_rb (weights effective i+1, cost at i+1); B3 pos.shift(1); C5 pos*lr.shift(−1); XGB1y monthly ret_next(m)=close m→m+1 with purged training (labels end ≥252d before block)).

## 4. Champion-level checks
- `python3 campaign/scripts/champion_build.py --verify`: GOAL100_CHAMPION / _AGGRESSIVE / _BALANCED max|new−old| = 9.994e-17 / 9.975e-17 / 9.991e-17, n=4696 each → byte-identical within float noise. Construction itself uses only shift(1) vol and a shift(1) 126d trailing-peak throttle.
- Champion throttle/costs sanity re-run from raw sleeves reproduces ann 48.5/SR 5.18/DD −7.3/OOS 5.52 (A) exactly.
- **Sleeve deaths → silent renormalization:** 6 sleeves' last nonzero rows end 2026-06-30/07-31 (A5r2, A5r4, A1inf, B3momhml, brwt, XGB1y) while the champion runs to 2026-08-27; the EW mean simply averages the surviving columns (capital implicitly re-spreads to survivors rather than to cash). 2026-YTD champion ann 29.6% as-committed vs 24.8% if dead sleeves were held at zero. Minor headline inflation confined to the final ~2 months.
- **Gross exposure / financing convention (disclosure check):** with 1/16 weights and per-sleeve scale clip(0.10/vol,≤8), mean gross = 4.03× NAV (p5–p95: 1.81–6.71). Largest scales: XGB1y 5.05, A5r7 4.25, A1credit 3.26, A1inf 3.23, a6r7 3.00. Financing is NOT charged (disclosed in champion_build docstring as the GOAL80 convention); at 4.5% money rate ≈ **13.6%/yr** — material to the headline "48–62% ann" (this convention is disclosed, not hidden, but any cross-comparison vs leveraged-unaware numbers must charge it).

## 5. Data quality
- Source panel for H21 books contains 1 Sunday row (2009-07-26) out of 5006 dates → propagates into champion-window indices as an all-zero day; harmless but sloppy.
- brwt CSV stores 59 literal empty (NaN) leading cells; champion_build's vt() maps them to scale 0 → no effect downstream (verified: verify run identical).
- All 16 sleeve files git-clean (no uncommitted modifications) except unrelated bigmove report files (h1/h5/h21_daily.csv, blend_daily.csv, multi_horizon_results.json — modified, uncommitted; not champion inputs).

## 6. Concentration / pool-integrity findings
1. **A5r2 + A5r4 both in POOL with corr 1.000 (vt-normalized 0.9933, n=4249).** A5r4's own meta says "REPLACES the vt10 member — NOT a new diversifier", yet champion_build keeps both and the docs count "16 unique sleeves" (economically 15). What-if drop A5r4: A 48.5→50.4 ann, SR 5.18→5.40; B 62.4→64.8, 5.27→5.47. Not inflationary — the duplicate *hurts* — but the pool framing overstates breadth.
2. XGB family: H21_f5/H21_br corr 0.6335 (vt-normalized 0.6159); XGB1y shares the ML family (already disclosed in GOAL100_CHAMPION.md risk notes).
3. **B3momhml is in the champion pool despite its own committed meta: "REFERENCE (NOT gate-passing)… FAILS halves… 7 neg yrs".** It contributes 1/16 of the champion. Mechanically clean (T+1 verified, repro identical), but including a self-declared invalid sleeve contradicts the "validated sleeves only" framing.
4. C5ng/C5ngsum vt-corr 0.4348 — related but distinct (season filter), acceptable.

## 7. Materiality summary (what-ifs, recomputed with the exact champion_build construction)
| Scenario | Config A (SAFE) | Config B (AGGRESSIVE) |
|---|---|---|
| As committed | 48.5 ann / SR 5.18 / DD −7.3 / OOS 5.52 | 62.4 / 5.27 / −7.9 / 5.68 |
| A1inf signal shift(1) (leak fixed) | 47.7 / 5.07 / −7.5 / 5.38 | 61.1 / 5.15 / −8.5 / 5.53 |
| H21 day-0 PnL zeroed (both books) | 49.6 / 5.29 / −7.4 / 5.62 | 63.8 / 5.38 / −8.4 / 5.77 |
| Drop A5r4 (dedup) | 50.4 / 5.40 / −8.2 / 5.73 | 64.8 / 5.47 / −7.8 / 5.86 |
| Dead sleeves zeroed in 2026 | 48.3 / 5.24 / −7.5 / 5.58 | 61.8 / 5.29 / −7.7 / 5.70 |
- XGB1y month-stamping tested (pnl(m) relabeled to month m+1 days): A 48.5/5.18→49.1/5.25 — spread convention is NOT lookalike-lucky; committed labeling matches the monthly file's own convention (k=0 slice books ret_next(m0) = m0→m0+1) → no issue.
- Net: no single fix flips the champion's story (SR ~5 stays ~5); the two real defects (A1inf leak, H21 day-0 entry) push in opposite directions and are individually ≤0.1–0.2 SR at champion level.

## 8. Items I could NOT verify (explicit UNVERIFIED)
1. **H21_f5 exact generator state** — no committed code+cache reproduces the CSV (best corr 0.685); the CSV predates the current code (CSV committed 17:53 at a407c4c; current HEAD 18:14; JSON saved 18:00 disagrees with CSV).
2. **H21_br exact generator state** — file (16:41:57) predates ALL commits of its producer; best-effort corr 0.904.
3. **H21_br day-0 treatment** (depends on 1–2).
4. The claim "trained on 2008-2016 only, model versioning separate from eval" for the XGB books (GOAL100_CHAMPION.md) — pred caches contain full 2008–2026 OOS preds with quarterly refits (TRAIN_WIN=504d rolling); no artifact demonstrates a 2016 training cut. Flagged as UNVERIFIED disclosure.
5. ddfilter-baseline h21 book uses `horizon_preds_20y.pkl` survivor-in universe while h21_book_daily_f5.csv uses the f5 full-universe cache — which universe the champion's h21_br file actually used is UNVERIFIED (closest repro = 20y.pkl + survivor).

## 9. Final verdicts (charter: verify from raw data or FAIL)
- PASS (10): A5r7, A5r2*, a6r7, QAxasts, dualmom, carryv2, XGB1y*, C5ng*, C5ngsum*, A1credit — *carrying noted conventions (duplication, synthetic daily granularity, vt-shift nits) that do not invalidate the sleeve.
- FAIL (1): **A1inf** — same-close signal enters same-day PnL; committed SR 1.15 → honest 0.64; neg years 1 → 5. Remove or re-gate before any further promotion.
- FLAG (3): **H21_f5** (unfrozen provenance + mechanical day-0 entry, favorable direction), **H21_br** (provenance not in git), **A5r4** (duplicate of A5r2, overstates pool breadth), plus governance flag **B3momhml** (self-declared non-validated reference inside a "validated" pool).
- Champion assembly itself is deterministic, reproducible (9.9e-17), and uses trailing-only/throttle shift(1) — the assembly is clean even where two inputs are not.
AUDIT DONE
