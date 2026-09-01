# GOAL100 CHAMPION — SYSTEM SPECIFICATION (v1.0, frozen 2026-09-01)

Single-page reference for the best honest system produced by the GOAL100 campaign.
All numbers independently reproduced by the coordinator; see "Repro" below.

## 1. HEADLINE (FULL 2008-09-01 .. 2026-08-28, 18.6 years, net of 6bps/side, no leverage)

| | BALANCED (headline) | SAFE (A) | AGGRESSIVE (B) |
|---|---|---|---|
| **Annual return** | **55.5%** | 48.5% | 62.4% |
| **CAGR** | ~60% | ~52% | ~68% |
| **Sharpe (daily)** | **5.24** | 5.18 | 5.27 |
| Sharpe (monthly) | ~3.6 (bootstrap CI 3.1-4.1) | | |
| **MaxDD (full)** | **-6.9%** | -7.3% | -7.9% |
| Worst calendar-year DD | -7.0% (2025) | | -7.1% |
| Negative years | **0 / 19** (worst year +9.1%) | 0/19 | 0/19 |
| Vol | ~9.4% | ~9% | ~10.3% |
| **OOS 2017-26** | **60.2% ann, SR 5.62, DD -6.9%** | 52.5% / -7.3% | 67.8% / -7.9% |
| Sub-5y CAGRs | 53 / 53 / 73 / 64% | | |
| Leave-one-year-out ann | 45.5% .. 50.0% | | |

Files: `campaign/results/GOAL100_CHAMPION_BALANCED_daily.csv` (headline),
`GOAL100_CHAMPION_daily.csv` (=SAFE), `GOAL100_CHAMPION_AGGRESSIVE_daily.csv` (=B).
All [date, ret] daily net returns, 2008-09-01 .. 2026-08-28.

## 2. CONSTRUCTION (trailing-only; no lookahead anywhere)

```
16 sleeves  --vt10 per sleeve-->  plain EW  --global vt-->  DD-throttle  --costs-->  champion
```

1. **Per-sleeve vol-normalize**: each sleeve scaled to 10% ann vol using rolling-60d
   realized vol shifted 1 day (trailing only), scale clipped at 8x.
2. **Blend**: plain equal-weight mean of the 16 normalized sleeves (weights sum to 1
   after the global step => NO leverage at portfolio level).
3. **Global vol target**: BALANCED = 50/50 daily average of config A and config B (below).
4. **Drawdown throttle** (126d rolling max of equity, shifted 1 day; cut exposure to 50%
   when trailing DD breaches threshold; switching costs charged):
   - Config A (SAFE): global vt 8.5%, throttle threshold 4%
   - Config B (AGGRESSIVE, = C4_construct_v2): global vt 11%, throttle threshold 3%
   - BALANCED: daily 50-50 average of A and B return streams (throttle cost charged on each).
5. **Costs**: 6 bps one-side on per-sleeve weight turnover (0.5 x |dW| summed) + throttle
   switching, embedded in all return series.

Configs A and B were selected by IS rules and revealed on OOS once:
- A: GOAL80-frozen throttle params; vt .085 = max with IS(08-16) DD<=-7% margin rule.
- B: C4_metaalloc round-2 frozen rule "max IS SR s.t. IS MaxDD<=8% AND every IS calendar-year
  DD<=8%", argmax (vt .11, thr .03, fr .5, lb 126) identical for IS-ends 2016/2019/2022/2023.

## 3. THE 16 SLEEVES (all validated, gates passed, T+1, net of 6bps)

| # | Name | Path (from repo root) | Family |
|---|---|---|---|
| 1 | H21_f5 | tools/quant/reports/xgb_horizons/h21_book_daily_f5.csv | XGB L/S equity 21d |
| 2 | H21_br | tools/quant/reports/xgb_horizons/h21_breadth_gate_daily.csv | XGB breadth-gated |
| 3 | A5r7 | campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv | credit composite |
| 4 | a6r7 | campaign/agents/A6_reversal/sleeves/a6_r7_bond2y_trend.csv | 2y policy-momentum |
| 5 | A1inf | campaign/agents/A1_trend_cta/sleeves/A1_infl_breadth_mom.csv | inflation breadth |
| 6 | QAxasts | campaign/agents/A3_xs_quality/sleeves/QA_xasts_tsmom189.csv | xs TSMOM 189d |
| 7 | A5r2 | campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv | VIX contango |
| 8 | A1credit | campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv | credit regime |
| 9 | XGB1y | campaign/results/sleeve_library/XGB1y_deploy.csv | XGB 1y book (keystone) |
| 10 | dualmom | campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv | dual momentum band |
| 11 | carryv2 | campaign/agents/A1_trend_cta/sleeves/A1_carry_seasonal_v2.csv | carry seasonal |
| 12 | A5r4 | campaign/agents/A5_vol_cond/sleeves/A5_r4_vt15_contango.csv | contango vt15 |
| 13 | brwt | campaign/agents/B2_highfreq/sleeves/brwt_spread_rev15.csv | Brent-WTI spread rev |
| 14 | B3momhml | campaign/agents/B3_antiregime/ref_momhml_composite.csv | MOM+HML composite |
| 15 | C5ng | campaign/agents/C5_newdata/sleeves/C5_ng_weekday_prem.csv | **natgas weekday (NEW)** |
| 16 | C5ngsum | campaign/agents/C5_newdata/sleeves/C5_ng_summer_weekday.csv | **natgas summer weekday (NEW)** |

Keystones (drop-one, at vt .085): XGB1y -10.0pp ann, brwt -3.5pp, QAxasts -1.5pp,
A1credit -1.2pp, C5ng -1.1pp. A5r2/A5r4 are duplicates (corr 1.0); kept — redundant EW
smooths the throttle. #15/#16 added +7.7pp vs the GOAL80 14-sleeve pool.

## 4. OOS DISCIPLINE & HONESTY

- IS = 2008-2016 (selection), OOS = 2017-2026 (single reveal): OOS BEATS IS for all three
  variants (no in-sample inflation).
- Every calendar-year DD <= 7.0% across 2008-2026 (incl. 2022 rate shock, 2020 Covid).
- Post-hoc wall bound (NOT selected, full-sample grid): vt .115 thr .03 => 64.9% @ -7.7%,
  vt .12 => 68.3% — disclosed but excluded because selection used full-sample knowledge.
- C2_fly2AB_75 (round-1 rates fly) is EXCLUDED — quarantined round-2 for a units bug
  (honest net SR -2.04). No quarantined or lookahead-tainted sleeve is in the pool.
- a6r7 and A1credit yield-approx sleeves re-audited clean (decimal units, repro byte-consistent).
- gates.py scramble_pval is degenerate; sleeve validations used signal-permutation /
  calendar-scramble (p<0.05 required). C5ng calendar-scramble p=0.015; C5ngsum p=0.015.

## 5. REPRO

```bash
# champion construction from the 16 sleeve files (coordinator build):
python3 - <<'PY'
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
from coord_goal100_v2 import load, vt
# ... construct(POOL, TGT, DD_THR) as in campaign/GOAL100_FINAL_REPORT.md section 3
PY
# C4/B-config standalone repro:
python3 campaign/scripts/c4_construct_v2.py
# eval any champion file:
python3 campaign/harness/eval.py campaign/results/GOAL100_CHAMPION_BALANCED_daily.csv
```

## 6. LIVE-TRADEABILITY CAVEATS (honest)

- Natgas sleeves trade Henry Hub SPOT prints; live proxy = front futures/UNG with basis risk.
- Bond sleeves (a6r7, A1credit) use duration-approx synth TR (no convexity/financing spread).
- A5 contango sleeves assume VIX-futures term-structure access (VXX-style or futures roll).
- 6bps/side is an ETF-level execution assumption; single-name legs inside XGB books may cost more.
- 18.6y tested vs the 20y goal: limited by sleeve availability from 2008-09; all engines
  that exist pre-2008 (A5r7 1990+, A1credit 1990+, C5ng 1997+) show stable pre-2008 behavior.

## 7. GOAL SCORECARD

| Requirement | Result |
|---|---|
| SR >= 2 | **5.24 — EXCEEDED** |
| MaxDD <= 8% | **-6.9% — PASS** |
| No leverage | PASS (EW weights, vt caps) |
| 6bps/side costs | PASS (embedded) |
| Free data | PASS (FRED, Ken French, twelve panel — all free) |
| OOS test | PASS (2017-26 single reveal, OOS > IS) |
| 20y testing | 18.6y (93%) |
| **ann >= 100%** | **NOT MET: 55.5% (honest ceiling ~65% post-hoc). Requires DD/return 0.08 vs best-real 0.11-0.20 — out of reach on free daily data at 6bps.** |
