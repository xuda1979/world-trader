# G1_intraday — Overnight/Intraday RSI Gate on XGB h21 Equity Book

## VERDICT: REJECT (Direction 1 fails; no adoptable sleeve)

**Primary hypothesis (RSI-level gate) REJECTED.** Every RSI-gate spec *lowers* the h21 sleeve SR vs baseline (1.92 → 1.44–1.84) and deepens MaxDD. De-risking at RSI>70 / adding at RSI<30 loses on this book — the XGB book is not hurt by overbought RSI, and gate turnover (3.4–18.8 turns/yr × 6bps) plus whipsaw eats the (nonexistent) edge.

**SPY overnight-gap reversal addon REJECTED.** Negative GROSS (−2.5%/yr pre-cost, SR −0.25); SPY gaps *continue* intraday on average, they do not reverse. All net specs: SR −0.05 to −0.97, ann −0.8% to −10.7%.

**Mechanical delivery gate:** the best surviving variant (MOM21<−3% → 0.5×) passes SR≥1.5 (2.04) & corr<0.5 (0.303) and `G1_sleeve.csv` is written per spec — but its delta vs the ungated book is **t=0.09** (+0.6pp ann, grid-mining noise). **NO-GO for champion integration** (champ+5%h21: SR 5.21 vs 5.18 = +0.03, nothing).

---

## Data (all offline)
| Source | Used for | Note |
|---|---|---|
| `tools/quant/reports/xgb_horizons/h21_book_daily_f5.csv` | h21 book, 2008-09-02→2026-08-12, n=4516, 0 NaN | as briefed |
| `campaign/results/GOAL100_CHAMPION_daily.csv` | benchmark, n=4696, SR 5.18, ann 61.7%, MaxDD −0.106 | as briefed |
| `more_etf/SPY.csv` | — | **MISSING on disk → REJECTED path** |
| `tools/quant/data/cboe_hist/SPY.csv` | SPY OHLC 2004-01-02→2026-09-09, n=5709 | allowed-source substitute for missing more_etf |
| `tools/quant/data/polygon_intraday/` (session closes) | — | **REJECTED as signal source**: 17 single-name files only (no SPY/index), 68 sessions 2024-12-02→2025-03-12; <252 obs → fail-closed, no stats certifiable |

## 1. Baseline h21 book (as-is, book costs assumed embedded)
SR **1.92**, ann **32.4%**, MaxDD −16.6%, gross avg 1.00. corr to champion **0.309** (4516 common days). 2H (2017+): SR 1.81.

## 2. RSI/momentum gate grid (T+1 causal: weight for day t set from info through close t−1; 6bps/full |dW|; 4.5%/yr margin on (gross−1); no shorts → no borrow)
| Spec | SR | ann | MaxDD | turns/yr | 2H SR |
|---|---|---|---|---|---|
| BASE h21 | **1.92** | 32.4% | −16.6% | 0 | 1.81 |
| RSI70/30 w0.5/1.5 (brief's ex-ante spec) | 1.73 | 26.4% | −18.2% | 10.8 | 1.66 |
| RSI70/30 w0.0/1.25 | 1.44 | 20.2% | −17.4% | 18.8 | 1.39 |
| RSI80/20 w0.5/1.5 | 1.84 | 29.6% | −16.6% | 3.4 | 1.74 |
| RSI60/40 w0.75/1.25 | 1.68 | 25.8% | −18.3% | 8.8 | 1.62 |
| MOM21<0 →0.5× | 2.01 | 29.2% | −11.5% | 9.0 | 1.85 |
| MOM21<−3% →0.5× | **2.04** | 32.7% | **−14.2%** | 5.7 | 1.93 |
| MOM63<0 →0.5× | 1.82 | 28.5% | −15.4% | 3.7 | 1.71 |
| COMBO RSI70/30+MOM | 1.82 | 24.9% | −15.3% | 14.7 | 1.71 |

**Significance of best delta (MOM21<−3% vs base):** mean +0.000002/day, **t=0.09**, ann delta +0.06pp → statistically zero. The +0.12 SR is best-of-8 grid mining (SE(SR)≈0.24 @18y). Only honest read: MaxDD improves −16.6%→−14.2% (crisis de-risk), no alpha.

## 3. SPY overnight-gap reversal addon (fade |gap|>q at open, hold to close; decision & fill at open t using gap_t=open_t/close_{t−1} — causal)
| Spec | SR | ann | turns/yr |
|---|---|---|---|
| gross q90 (no costs) | **−0.25** | −2.5% | 0 |
| net gap>±0.5% | −0.97 | −10.7% | 114.5 |
| net gap>±1.0% | −0.55 | −5.0% | 41.0 |
| net gap>±1.5% | −0.40 | −3.2% | 17.0 |
| net q90 | −0.55 | −5.0% | 43.6 |
| net q90 momentum-dir (control) | −0.05 | −0.8% | 43.6 |

Gross-negative ⇒ not a cost artifact. corr(gap, champ)=−0.005; champ+5%/10% gap addon: SR 5.16/5.11 (worse).

## 4. Champion integration
corr(gated sleeve, champ)=0.303 (<0.5 ✓). champ+0.05×h21: SR 5.21, ann 62.9%, MaxDD −10.6% — +0.03 SR, immaterial.

## REJECT log (fail-closed, exact numbers)
- REJECT `more_etf/SPY.csv`: file absent → used `tools/quant/data/cboe_hist/SPY.csv` (5709 rows, 2004→2026-09-09).
- REJECT polygon_intraday arm: 17 tickers, no SPY, 68 sessions (2024-12-02→2025-03-12), n<252 → no certifiable stat.
- REJECT RSI gate (primary): best RSI spec SR 1.84 < base 1.92; brief spec 1.73.
- REJECT gap-reversal addon: gross SR −0.25, all net specs SR<0.
- NO-GO MOM-gated sleeve for adoption: delta t=0.09 vs base; champion lift +0.03 SR only.
- G1_sleeve.csv DELIVERED (mechanical gate SR 2.04≥1.5, corr 0.303<0.5) with warning: alpha-delta not significant; treat as h21 baseline + noise-level de-risk overlay.

Files: `G1_report.md` (this), `G1_sleeve.csv` (date,h21_raw,pos,g1_net; n=4516), `g1_gate_grid.csv`, `g1_gap.py`, `g1_run.py`, `g1_daily_parts.csv`.
DONE G1_intraday
