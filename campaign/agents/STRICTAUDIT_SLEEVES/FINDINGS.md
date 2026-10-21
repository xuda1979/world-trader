# STRICTAUDIT_SLEEVES — forensic per-sleeve audit of the 12 STRICTTRADE sleeves (read-only)
Agent: STRICTAUDIT_SLEEVES | Date: 2026-09-02 | Method: raw-data re-derivation from FRED/twelvedata/panel
sources, byte-level CSV comparison, gate replay at zero-run dates, independent correlation and
instrument-reality recomputation, champion rebuild from scratch + cross-check vs recovered builder.
Scratch scripts + outputs in `scratch/` (mech_sanity.json, raw_corr_matrix.csv, vt_corr_matrix.csv, and
~40 repro scripts). No campaign file was modified (the dualmom repro was executed in place; its output
verified byte-identical to git HEAD: 4743/4743 rows, max|d|=0.000e+00, `git status` clean).

## 0. VERDICT TABLE (12 charter sleeves)

| Sleeve | Repro vs committed CSV (this audit) | T+1 | Zero-runs explained | Verdict |
|---|---|---|---|---|
| brwt15 | **EXACT** — committed `backtest_brwt_spread_rev15.py` (lb15, z±1.5, FRED brent/wti) rerun: n=6547/6547, corr 1.00000000, maxdiff 9.99e-17 | OK (pos earns `sp.diff().shift(-1)`) | 12 runs ≥5d, max 33d (2016-05-02..06-03; also 2003): z15-band gate, max|z| in each window <1.5 (2016 run: 1.471), pos==0 all days replayed | **PASS** (minor vt nit §3) |
| brwt10 | **EXACT after reverse-engineering**: lb10, **z±1.0** (not 1.5), min_start 2000, B2 gates vt → n=6547/6547, corr 1.00000000, max|d|=9.996e-17 | OK (same) | max run 14d = band gate | **PASS/FLAG** (§5: recipe undocumented) |
| brwt7 | **EXACT after reverse-engineering**: lb7, z±1.0, min_start 2008 → n=4560/4560, corr 1.0, max|d|=9.996e-17 | OK | max run 9d | **PASS/FLAG** (§5) |
| brwt5 | **EXACT after reverse-engineering**: lb5, z±1.0, min_start 2008 → n=4560/4560, corr 1.0, max|d|=9.999e-17 | OK | max run 10d | **PASS/FLAG** (§5) |
| C5ng | **EXACT** — raw DHHNGSP, Wed/Thu short + Fri long, calm filter 2.5×90d-sigma(shift1), `pos*lr.shift(-1)`: n=7381/7381, corr 1.0, max|d|=9.975e-17 | OK mechanically; **publication-lag risk quantified: SR 1.632→0.254 (−84%) with 1-day info lag** | 5 runs ≥5d, max 7d = calm filter | **PASS w/ OPEN RISK** |
| C5ngsum | **EXACT** — same + Apr–Oct filter: n=7381/7381, corr 1.0, max|d|=9.996e-17 | OK | 28 interior runs 100–111d, every one Nov→Mar/Apr 1997–2025 = season filter, list verified | **PASS w/ OPEN RISK** (same lag) |
| A5r2 | **EXACT** — committed module rerun: n=4249/4249, corr 1.0, max|d|=9.975e-17 | OK (`pos=P.shift(1)`, vt shift1) | 60d lead vt warmup; 112d run 2022-08-09..2023-01-18 = rate-shock veto (RS=0, contango C=1; lifts exactly 2023-01-18); also 98/96/92d veto windows 2011/2018/2023 — replayed | **PASS** |
| a6r7 | **EXACT** — DGS2, 2y synth TR=−1.9·dy+y/252, MA378 gate, 42-obs cadence, W.shift(1)·tr, vt12 cap5: n=9168/9168, corr 1.0, max|d|=9.975e-17 | OK | 378d lead warmup; 461d run 2021-11-29..2023-09-29 and 209d run 2017-11-15..2018-09-14 = trend gate (MA378 TR ≤ 0), W≡False replayed | **PASS** |
| QAxasts | **EXACT** — E1 path (5-leg MA189 TSMOM, wback_rb, B2 vt on full history): n=4947/4947, corr 1.0, max|d|=9.996e-17 | OK (weights effective i+1) | 37 lead zeros = MA189 warmup (first nonzero 2007-02-08); no interior runs ≥5 | **PASS** |
| carryv2 | **EXACT** — E1 idea4 script re-run (GLD/twelvedata, brent floor 2000, no 2008 cut): n=5002/5002 valid rows, corr 1.0, max|d|=9.986e-17 | OK (all 3 members shift(1); honest lag-2 on crude-brent member) | 60 lead zeros = vt warmup; no interior runs ≥5 | **PASS** |
| dualmom | **EXACT** — `QA_dualmom_band121.py` re-executed: regenerated CSV byte-identical to git HEAD (4743/4743, max|d|=0) | OK (weights from t+1, cost t+1) | 436 lead zeros (panel 12m-momentum floor); interior 250d (2022-02-02..2023-01-31), 166d (2015-09..2016-04), 103d, 100d = FF-mkt 200d-MA ±3% hysteresis; gate=0 at every month-end 2022-02..2022-12, back to 1 on 2023-01-31 — replayed | **PASS** (panel caveat §6) |
| XGB1y | **EXACT vs committed monthly artifact**: daily = geometric re-spread of `gkx_1y_deploy_monthly.csv` @ git 4662a6a: 4403/4403 rows at 9.97e-17; +281 lead-in zeros 2008-01-02..2009-01-30 (first cohort 2009-02) | OK at monthly scale (pnl(m)=close m→m+1); relabeling to m+1 changes champion 49.4→49.5% — immaterial either way | lead-in = pre-first-cohort; ac1=0.951 is the monthly STEP convention, not a data defect | **PASS/FLAG** (§5: cache outside git) |

**No FAILs. 10 PASS, 2 PASS/FLAG (brwt10/7/5 undocumented recipe — now established; XGB1y cache provenance).**

## 1. Mechanical sanity (from the CSVs alone; rf=0, 252d annualization)
| name | SRfull | SR 2008-09+ | H1/H2 | negYrs full | MaxDD% | max single-day | lag-1 ac | runs≥5 (max) |
|---|---|---|---|---|---|---|---|---|
| brwt15 | 2.76 | 2.37 | 3.02/2.49 | 0/27 | −7.9 | 15.8% | −0.043 | 12 (33d) |
| brwt10 | 3.41 | 2.88 | 3.84/2.97 | 0/27 | −8.4 | 13.0% | −0.048 | 12 (14d) |
| brwt7 | 3.19 | 3.08 | 3.30/3.10 | 0/19 | −5.6 | 12.7% | +0.041 | 12 (9d) |
| brwt5 | 3.10 | 3.01 | 3.22/3.00 | 0/19 | −9.3 | 12.9% | +0.080 | 12 (10d) |
| C5ng | 1.63 | 1.64 | 1.93/1.46 | 0/30 | −31.0 | **21.8%** (2024-01-11, real cold-snap print, AUDIT5-verified data; not a stitch error) | 0.006 | 5 (7d) |
| C5ngsum | 2.02 | 2.21 | 1.76/2.27 | 1/30 (1997) | −13.1 | 9.3% | 0.063 | 12 (111d, winter) |
| A5r2 | 1.02 | 1.02 | 0.94/1.10 | 2/18 | −12.8 | 4.6% | −0.018 | 12 (112d) |
| a6r7 | 2.03 | 1.32 | 2.61/1.28 | 4/37 | −13.1 | 5.2% | 0.013 | 5 (461d) |
| QAxasts | 1.02 | 1.08 | 0.82/1.20 | 1/21 | −13.0 | 18.7% (2020-04-20 COVID oil print, real) | −0.005 | 0 |
| carryv2 | 0.83 | 0.79 | 0.63/0.99 | 3/21 | −12.8 | 19.9% (2024-01-12, real) | −0.071 | 0 |
| dualmom | 0.89 | 0.91 | 1.00/0.79 | 1/20 | −24.5 | 8.2% | −0.089 | 8 (250d) |
| XGB1y | 4.32 | 4.40 | 3.49/5.12 | 3/19 | −22.8 | 1.3% | **0.951** (step artifact) | 0 |

- **XGB1y daily SR 4.32 is a convention artifact**: compounded monthly SR = **1.03** (mean 1.29%/mo, sd 4.33%/mo). Its daily series is constant within each month, so daily Sharpe overstates independent-information Sharpe by the autocorrelation of the steps. In any DAILY blend this inflates measured daily SR; the honest read is the monthly SR. This is a major reason SR_daily 5.24 vs SR_monthly 3.46 for the champion.
- No duplicate dates in any file; no weekend rows except the known 2009-07-26 Sunday in QAxasts/dualmom/XGB1y panel calendars (all-zero, no PnL invented).

## 2. T+1 discipline
- All 12 sleeves verified: signal/weights computed from data ≤ t, PnL earned t→t+1 (`shift(-1)` return, `shift(1)` weights, or wback_rb effective i+1). No same-close-entry violation found anywhere in the 12.
- **Minor (carried from AUDIT2, still true):** brwt×4 and C5ng/C5ngsum are saved via `B2_highfreq/gates.vol_target` whose scaler uses `rolling(60).std()` **without shift(1)** — same-day return is inside its own vol scale. Recomputed effect: brwt15 SR 3.253 (as-is) → 3.165 (shifted) = **+0.09 SR inflation**; C5ng 1.632 → 1.601 = **+0.03**. All other sleeves use shift(1) vt. Small but systematic; it survives into the champion inputs.
- A5r2/a6r7/QAxasts/carryv2/dualmom: shift(1) vt verified in committed code (champion_build.vt, a5_r2 L42, a6_r7 L28, engine.py vol_target, a1_carry_seasonal vtclip).

## 3. Zero-run forensics — every long run gate-replayed (exact dates in §0)
All 12 sleeves: no unexplained interior zero-run. All runs are (a) documented gates replayed to the exact date from raw data, or (b) warmup floors. The audit_harness.py default flags are consistent with this.

## 4. Duplicates / redundancy — THE headline finding
Pairwise vt-normalized correlations (this audit, `vt_corr_matrix.csv`):
- **brwt family**: brwt15–10 0.764, 15–7 0.756, 15–5 0.664, 10–7 0.870, 10–5 0.771, 7–5 0.831. Mean 0.793. **Position-day agreement 67–86% (2008+).** These are 4 lookback variants of ONE Brent-WTI z-reversion trade. The E1 brwt15 meta itself says "use E1 file INSTEAD, not in addition" — the 12-slot pool instead counts the family 4×. **4 slots = 1 economic engine.**
- **C5ng vs C5ngsum**: raw 0.572, vt 0.513. Same underlying weekday anomaly, one being the Apr–Oct subset → **2 slots ≈ 1.3 engines**.
- **A5r2 vs dualmom**: raw 0.543, vt 0.601 — both long-equity-beta books with different gates → **2 slots ≈ 1.5 engines**.
- Cross-family correlations are genuinely low (all |ρ|≤0.147 except the pairs above; e.g. brwt–C5ng −0.02, a6r7–XGB1y 0.01, carryv2–a6r7 0.07).
- **A5r4 confirmed OUT of the 12** (absent from GOAL100_STRICTTRADE.json pool); it is still corr 1.0000 to A5r2 on disk (vt15 rescale, mean|d|=1.7bp), so the removal was correct and complete. A5r7/A1credit also confirmed absent (§6).
- **Effective breadth**: 12-slot pool mean pairwise vt-corr 0.085 (median −0.003); the economically-deduped 8-engine pool has mean pairwise corr 0.016 → **N_eff ≈ 7.2 of 8 claimed engines (and 8 of 12 slots)**.
- Materiality (documented-pipeline recon, not the committed file): as-committed 12 slots SR 5.04; brwt→1 slot 5.07; natgas→1 slot 4.97; fully-deduped 9-engine pool 5.15. **Deduping does NOT collapse the SR story** (the blend is dominated by low pairwise corr, not by slot count), but "12 engines" is breadth overstatement; the honest count is **~8 engines (N_eff≈7)**.

## 5. Provenance
- **brwt15, C5ng, C5ngsum, a6r7, QAxasts, carryv2, A5r2, dualmom: 8/12 fully reproducible from committed code + raw free data at ≤1e-16** (verified this session; stronger than AUDIT2's earlier PASS because several were re-derived here from the raw commodity/yield files, not just from intermediate sleeves).
- **brwt10/7/5: provenance GAP closed by reverse-engineering.** No committed script or meta documents them (created in commits 7cc4ca3/45b8ff3 with no builder committed). I established the exact recipe (lb∈{10,7,5}, **z-band ±1.0**, min_start 2000/2008/2008, B2 gates vt) reproducing all rows at 1e-16. The recipe should be committed or the sleeves marked derived-from-brwt15.
- **XGB1y: daily artifact byte-verified against the COMMITTED monthly file** (git 4662a6a: 4403/4403 exact, geometric spread by trading-day count; +281 lead zeros). **BUT two honest disclosures:**
  1. The working-tree `gkx_1y_deploy_monthly.csv` (mtime 2026-09-01 16:07, AFTER the daily file was created 08-28) differs from the committed version in 210/210 months (max month diff 7.0pp in 2009-07). The champion input matches the **committed** version, so the headline is safe, but an uncommitted, post-hoc modification of a source file sits in the tree.
  2. The underlying prediction cache `gkx_preds_xgb_1y_pit.parquet` is **git-ignored** (regenerable-caches policy); a fresh full retrain was NOT attempted by this audit. Cache-level provenance therefore remains **UNVERIFIED** (weaker concern than MHX/H21 because the champion input itself is byte-frozen from a committed artifact, and AUDIT2 separately verified the monthly↔daily consistency and XGB training-window purge; the "trained only through 2016" claim remains UNVERIFIED, carried from AUDIT2).
- **dualmom**: re-executed; output byte-identical to git HEAD. Data = FF factors + harness closes() panel.

## 6. Instrument-reality cross-check (independent recomputation)
| Sleeve | Instrument | This audit's evidence | Verdict |
|---|---|---|---|
| brwt×4 | WTI/Brent futures spread | spot proxy, basis disclosed in meta | REAL |
| C5ng/C5ngsum | NG futures proxy for FRED spot | **publication-lag: C5ng SR 1.632→0.254 with 1-day info lag (−84%)**; matches memo's −85% bound | REAL with OPEN RISK (worst item in the pool) |
| A5r2 | SPY long gated | plain long ETF | REAL |
| a6r7 | 2y UST trend | synth 2y TR vs real IEF daily corr **0.721** (recomputed independently) | REAL (faithful) |
| QAxasts | 5-asset TSMOM | synth 10y (dur 8.5) vs IEF corr **0.955**; VIXS leg = synthetic spot VIX, no roll carry (conservative for its short-vol bias; worst single leg-day −35.8%) | REAL (VIX leg basis caveat) |
| carryv2 | crude-brent (lag-2 honest), NG winter, gold/GLD trend | real ETFs/futures, bad-print guarded | REAL |
| dualmom | 285-name equity L/S | survivorship-biased static panel (AUDIT5: +2.7–5pp/yr EW tilt; L/S relative legs partially cancel; disclosed) | REAL w/ panel caveat |
| XGB1y | 20-name monthly L/S | same panel caveat + §5 cache note | REAL w/ caveats |
| A5r7 / A1credit (EXCLUDED) | synthetic BAA credit TR | **independently CONFIRMED paper**: A1credit exact-convention rebuild on synth BAA SR **1.45** (2008+) vs same gate on REAL LQD SR **−0.09**; 63d credit momentum on real LQD/HYG SR **−0.18/−0.64**; synth BAA level-TR vs LQD corr 0.587 but spread-TR 0.00 / HYG 0.03 | Exclusion CORRECT |

## 7. Champion cross-checks (GOAL100_STRICTTRADE_BALANCED_daily.csv)
- **All headline stats reproduced exactly from the CSV**: n=4522, span 2008-03-31..2026-07-31 (4522/252=17.9y); **arith ann 49.4%** (geo 63.0% — the memo's number is the arithmetic convention, correct as stated), **SR daily 5.24, SR monthly 3.46** (bootstrap 95% CI [3.06,3.98] vs claimed [3.02,4.01] — consistent), **MaxDD −6.1%**, **0/19 neg years, worst +20.7% (2026 partial), best +151.1% (2023)**, **OOS 2017+ 55.9% @ −6.1%**. Max single champion day +14.72% (2020-09-01) = brwt-family convergence day under vt scale ~3.4x — consistent with inputs, not a data spike.
- **Builder provenance: NO committed script builds the 12-sleeve STRICTTRADE file** (git history + repo grep verified; only the OLD 16-pool `champion_build.py` exists). The STRICTAUDIT_CONSTRUCTION agent recovered a session-log recipe; **I independently re-implemented it from scratch and it matches the committed CSV byte-for-byte: 4522/4522 rows, max|d|=9.996e-17** (San Francisco calendar collapse: weekend/holiday returns summed into next trade day; per-sleeve vt10 cap8; instrument costs 1.5–15bp charged on weight changes; borrow-fee layer; throttle A(7%,4%)/B(9.1%,3%) averaged). So the artifact is exactly what the recipe produces — **but the recipe itself is still not committed to git. NOT-FROZEN.**
- My own from-documentation recon (before recovering exact params) reached corr 0.983 and ann 61.8% — i.e. the committed file embeds **~12.4pp/yr of execution+borrow drag** relative to the raw sleeve blend. This is the conservative instrument-cost layer working as documented; it also means headline 49.4% is NOT a no-cost number (good), and the document-pipeline alone is insufficient to regenerate it (hence NOT-FROZEN).
- Implied gross exposure (recon): mean 1.97x, p95 3.06x, max 4.02x — same order as the disclosed 1.43x mean/4.44x max; financing on gross>1x remains uncharged in the headline (disclosed).
- No dead-sleeve renormalization inside the champion window: champion ends 2026-07-31 = last date all 12 sleeves have data (A5r2 goes flat from 2026-07-02, which is its position, not missing data).
- Sleeve→champion corr: brwt7 +0.51 (max), C5ngsum +0.25, A5r2 +0.19, QAxasts +0.12 (min).

## 8. Items UNVERIFIED (explicit)
1. XGB1y full model-retrain provenance (pred parquet git-ignored; no fresh retrain attempted here). The "trained on 2008-2016 only" disclosure remains UNVERIFIED (carried from AUDIT2).
2. EIA/FRED DHHNGSP publication timing (no network); the −84% lag haircut is a bound, not a measurement (matches TRUTH_MEMO's open risk).
3. LOYO/3y-window claims of the memo — outside this charter (STRICTAUDIT_STATISTICS scope).
4. Origin of the 2026-09-01 working-tree modification of `gkx_1y_deploy_monthly.csv` (does not affect champion input, but should be committed or reverted).

## 9. FINAL VERDICT
- **Per-sleeve: 12/12 verified mechanically sound; no FAIL.** 8/12 byte-reproducible from committed code + free raw data; brwt10/7/5 reproducible with a now-documented (but uncommitted-origin) recipe; XGB1y byte-frozen to a committed monthly artifact with cache-level provenance UNVERIFIED.
- **Pooled redundancy: the "12 sleeves" are ~8 economically independent engines** (brwt×4=1; natgas×2≈1.3; A5r2+dualmom≈1.5; a6r7, QAxasts, carryv2, XGB1y). N_eff≈7.2 at the 8-engine level. The champion's SR is NOT a slot-count artifact (deduped SR 5.0–5.2 in recon), but any "12 engines" framing overstates breadth by ~50%.
- **Sharpe honesty: daily SR 5.24 is flattered by XGB1y's monthly-step construction (its own daily 4.32 vs monthly 1.03). The monthly SR 3.46 (CI ≈[3.0,4.0]) is the honest single number** — still >2, still 0 negative years, still MaxDD −6.1%.
- **Two standing risks**: (1) natgas publication lag (−84% C5ng edge under 1-day lag; pool survives per memo stress), (2) builder not committed (artifact verified reproducible only via the recovered recipe).

STRICTAUDIT_SLEEVES DONE
