# Research Discoveries Log — high-Sharpe strategies at 6 bps/side

Cumulative findings of the 2026-08-12/13 research campaign (hedge-fund
strategy suite + cross-suite blends). Costs: **6 bps per side (12 bps
round-trip)**. Data: free daily (twelve_big, Polygon, FRED macro, FX,
Fama-French, AP-replication walk-forwards). All numbers cost-inclusive.
Primary source of detail: `RESEARCH_REPORT.md`; artifacts: `results/`,
`blend_*.py`, `subperiod.py`, `portfolio_spec.py`.

## POSITIVE discoveries (what works)

| # | Discovery | Evidence |
|---|-----------|----------|
| P1 | **The all-weather flagship: h3 + AP gold** (3-stream hedge EW: L/S 130/30 + CTA futures macro 21d + Global Macro, ex stat arb; 50/50 with AP gold composite). Monthly SR **0.94**, +10.7%/yr, MaxDD -10.1%, **positive in all 4 sub-periods 2008-2026** (+0.86/+1.49/+0.73/+0.50), **every 5y rolling window positive (min +0.25)** | `blend_monthly.py` |
| P2 | **The genuine diversifier is the polygon LS champion** (n10_r14/levdet3.0 family): corr with hedge sleeve **-0.003 daily** (+0.17 monthly) — the only near-zero-correlation validated leg found | `blend_6stream.py` |
| P3 | **2024+ construction: h3 + AP + LS champion, sleeve EW** — daily SR **1.15** (monthly 1.20), +11%/yr, MaxDD -3.5%, positive in both half-windows; deployment spec SR 1.24 daily | `blend_6stream.py`, `portfolio_spec.py` |
| P4 | **AP monthly-file/daily-audit mystery RESOLVED**: same book, one-month attribution lag (lag-1 corr **0.878**). Monthly file is signal-timed, daily audit realization-timed; the audit is the correct record | analysis in report |
| P5 | **3-stream EW > 4-stream EW**: dropping stat arb improves EVERY sub-period at 12 bps RT (0.64 vs 0.45 SR) | `blend_variants.py` |
| P6 | **Risk Parity is the only standalone positive in all 4 sub-periods** (0.28/1.23/0.12/0.66), SR 0.52-0.58 — cost-insensitive (1.9x turnover) | `subperiod.py` |
| P7 | **L/S 130/30 is the best standalone** (0.75 at 12 bps RT) but it is market beta (β≈1.05); cost doubling cost it only -0.05 SR (low turnover) | `run_all.py` |
| P8 | **Vol management (Moreira-Muir) on L/S halves MaxDD** (-45.8% -> -26.6%) at ~same SR (0.71 vs 0.75) | `run_extras.py` |
| P9 | **Champion-family 8.5y stream exists** (`ls_n10r14_daily.csv`, 2018-2026, daily SR +0.92) — quadruples the champion sleeve's history; 2019+ blends with it are positive in both sub-periods (SR 1.24-1.27) | `blend_robust.py` |
| P10 | **Cost sensitivity tracks turnover** (table in report): doubling 6->12 bps RT cost L/S 0.05, stat arb 0.57 SR | `run_all.py` re-run |

## NEGATIVE discoveries (what fails — equally valuable)

| # | Discovery | Evidence |
|---|-----------|----------|
| N1 | **Stat arb is dead at the real cost**: SR -0.85 at 12 bps RT (was -0.28 at 6), negative in ALL 4 sub-periods; 46x turnover vs ~5.6%/yr cost drag. It is blend poison, not fertilizer | `run_all.py`, `subperiod.py` |
| N2 | **FX carry rejected as a sleeve**: low corr (-0.09/-0.20) but own SR 0.11 — h3+AP+FX SR 0.99 vs 0.99, return diluted 8.7%->6.8%. Rule: sleeves must clear the cost hurdle alone; correlation alone doesn't qualify | analysis in report |
| N3 | **ALL six cross-asset replication legs FAIL their scramble gates**: gold_trend (17% scrambles beat real), cross_asset_tsmom (100%), fx_momentum (67%), overnight_drift (33%), crypto_trend (54%), cn_momentum (67%) | gate re-run |
| N4 | **The permutation-of-returns scramble gate is mathematically vacuous** (mean/std permutation-invariant — shuffling returns changes nothing); only signal-scramble gates are meaningful | `build_gated_portfolio.py` audit |
| N5 | **live_vslbl (8y, monthly SR 0.75) FAILED its signal-scramble gate** (33% of scrambles beat real) — looked great, excluded | `vs_lbl_validation.json` |
| N6 | **w8y_reval (8.4y, "ok" verdict) HURTS the blend when added** (0.65 vs 0.75 on 2018-26); w10y (10y) SR -0.52 dead | sleeve audit |
| N7 | **AP gold is NOT a near-zero-correlation diversifier** — corr with hedge sleeve +0.03/+0.61 daily/+0.49 monthly once realization-timed; the near-zero claim was a timing artifact | resolution chain |
| N8 | **The 1.15 flagship was a one-month-lag premium** on a misaligned series; the honest SR is 0.94 | lag analysis |
| N9 | **EMN, merger arb, credit, FI arb, CTA-equities, factor momentum are all ≤ 0 at 12 bps RT**; factor momentum's premium died post-GFC (-0.06) | `subperiod.py` |
| N10 | **Stooq futures still IP-blocked** (checked 3x) — no real-futures CTA upgrade | probe |
| N11 | **blend_refined.py's recent-window SRs (1.75-2.33) are selection-biased** — shorter windows exclude the hedge sleeve's negative early period; full-history windows (1.10-1.15) are the honest ones | reconciliation |
| N12 | **Monthly vol-management on the blend is unstable** (extreme multipliers in calm months) — rejected; inverse-vol weights give no gain over EW | weight tests |
| N13 | **My own first-pass "artifact" correction was wrong**: the distributed-AP approximation was nearly uncorrelated (0.025) with the real daily path; the original +0.61 corr was real. Lesson: verify native source files before approximating | second-pass audit |

## Process lessons (meta)

- **Sleeve rule**: diversify only among streams that each clear the cost
  hurdle on their own (P1/P5 vs N1/N2/N6).
- **Sampling discipline**: monthly-cadence books must be analyzed at
  their native frequency or with realization-timed records (P4, N7/N8);
  daily-sampled SR of smooth series inflates (N13).
- **Validation discipline**: a stream without a completed signal-scramble
  verdict is watch-validated, not validated (P9 pending; N4 shows why
  the gate method matters).
- **Window discipline**: report full-history windows; trimmed windows
  flatter SR (N11).

## Operational monitoring (2026-08-13)

- Champion live-health check (`tools/quant/ls/check_champion_health.py`):
  [OK] the champion's own 10d-horizon edge is intact — fresh live 10d IC
  +0.036 (last 6 months). The faster 1d-horizon IC is adverse (-0.132),
  i.e. the fast signal is decaying/regime-adverse while the deployed 10d
  signal is healthy. No action needed on the deployment leg.
- Reconfirms the validation gate: only LS_GBRT (champion family) passes
  the price-lag scramble; tsmom/gold/fx/pairs all FAIL — consistent with
  the sleeve audit (N3).

## n10_r14 8y verdict — decision tree (contingency, documented before the verdict)

The trimmed validator (`tools/quant/ls/validate_n10r14_trimmed.py`,
twelve_big 8y, 10-scramble time-shift gate) is running. Whatever it
returns, the flagship does NOT depend on it:

| Verdict | Meaning | Portfolio impact |
|---------|---------|------------------|
| PASS (p<0.05) | Champion config generalizes to 8y | h3+AP+n10r14 (2018+) / h3+AP+LS (2024+) — extended champion coverage; expected SR ~0.73 monthly on 2019+ |
| WATCH (0.05-0.10) | Marginally above the bar | Same as PASS but document as weak evidence; keep polygon LS (2024+) which passed on its own panel |
| FAIL | 8y generalization not scramble-proof | No change: flagship stays h3+AP (2008+) / h3+AP+LS (2024+); 2018-24 gap remains h3+AP-only |

The polygon LS champion (levdet3.0) already passed its own panel's
scramble gate — the 2024+ sleeve is independent of this verdict. The
n10r14 stream is a bonus (2018-24 coverage), never a dependency.

## Pending / flagged candidates

- n10_r14 8y OOS validation (`regime_gbrt_v13_oos.py`) re-launched
  2026-08-13 — signal-scramble verdict on 8y twelve_big/twelve_liq
  pending; results -> tools/quant/ls/results/regime_gbrt_v13/.
- **wf_champion_final (fundamental-tilt champion) — LIKELY OVERFIT,
  downgraded 2026-08-13**: momentum + value/quality rank-z tilt (SEC
  EDGAR fundamentals, 6-month lag, honest construction machinery) shows
  realization-timed monthly SR 1.18, positive in all 4 sub-periods,
  corr with h3 +0.095 — but it is **not reproducible from reasonable
  fixed configs**: TILT_W=0.3/TILT_MODE=all at vt12 and vt15 both give
  SR ~0.85, WORSE than the no-tilt gold-champion baseline (SR 1.05).
  The 1.19 "final" required unknown tuned parameters; a tilt that
  *hurts* at sensible weights while a tuned config shows 1.19 is the
  in-sample-tuning signature (same pattern as live_vslbl, N5).
  Conclusion: tilt idea not validated; the tuned 1.19 should not be
  deployed or blended. Thread closed unless a walk-forward selection
  test finds a config that beats the baseline OOS.
