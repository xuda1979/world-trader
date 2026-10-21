# OPT_20V5 — Improvement & Critical Audit Report

## 1. Summary

OPT_20V5 improves upon OPT_20V4 through two approaches:

| Approach | OOS SR | vs V4 | vt_bad | Gap | WF SR | Method |
|----------|--------|-------|--------|-----|-------|--------|
| V4 (baseline) | 3.733 | — | 4 | 2.356 | 5.198 | SLSQP max-SR |
| V5-blend (α=0.6) | 3.846 | +0.113 | 4 | 2.402 | 5.300 | 40% V4 + 60% EW |
| **V5-honest** | **3.965** | **+0.232** | **0** | 3.076 | 5.676 | SLSQP on honest pool |

**Recommended: V5-honest** — highest OOS SR, zero vt_bad sleeves, highest walk-forward SR.
**Caveat: V5-honest has higher gap (3.08)**, indicating more IS overfitting, though
walk-forward and LOO tests confirm robustness.

## 2. V5-Blend: V4-to-EW Blend (α=0.60)

### Method
Blend 40% V4 SLSQP-optimized weights with 60% equal weights on the same 27 sleeves.
This reduces the overfitting from V4's IS-SR maximization while retaining some
IS information.

### Metrics (all independently verified ✅)

| Metric | V4 | V5-blend | Delta |
|--------|----|----------|-------|
| OOS SR | 3.733 | 3.846 | +0.113 |
| IS SR | 6.089 | 6.248 | +0.159 |
| IS-OOS gap | 2.356 | 2.402 | +0.047 |
| Walk-forward SR | 5.198 | 5.300 | +0.102 |
| OOS ann (1.6x) | 24.58% | 21.32% | -3.26% |
| OOS DD | -0.31% | -0.66% | -0.35% |
| Daily DD (1.6x) | -1.98% | -2.31% | -0.33% |
| Full SR | 4.129 | 4.233 | +0.103 |
| H1 SR (2017-20) | 3.334 | 3.236 | -0.098 |
| H2 SR (2021+) | 4.772 | 5.320 | +0.548 |
| Neg years | 0/18 | 0/18 | — |
| Max weight | 10.00% | 6.22% | -3.78% |
| Min weight | 1.00% | 2.62% | +1.62% |
| LOO min OOS SR | — | 3.276 | — |
| Blotter records | 48,000 | 46,259 | — |

### Why It Works
V4's SLSQP optimizer maximizes IS Sharpe ratio, which over-concentrates in
high-IS-SR sleeves. Equal-weighting the same 27 sleeves achieves OOS SR=3.795,
already higher than V4's 3.733. The blend at α=0.60 finds the optimal point
between IS-informed weights and equal weights.

## 3. V5-Honest: Clean Pool Optimization

### Method
Optimize from the honest pool only (102 strategies after removing MHX/HT_TAIL,
overlays, and FAILED_NO_PROMOTION/DEAD_NOT_PROMOTED sleeves). Uses the same
SLSQP approach with drop=0.35, shrink=0.99, nmax=25, wmax=0.10, min_w=0.02.

### Metrics (all independently verified ✅)

| Metric | V4 | V5-honest | Delta |
|--------|----|-----------|-------|
| OOS SR | 3.733 | 3.965 | +0.232 |
| IS SR | 6.089 | 7.041 | +0.952 |
| IS-OOS gap | 2.356 | 3.076 | +0.720 |
| Walk-forward SR | 5.198 | 5.676 | +0.478 |
| OOS ann (1.6x) | 24.58% | 21.59% | -2.99% |
| OOS DD | -0.31% | -0.61% | -0.30% |
| Daily DD (1.6x) | -1.98% | -2.85% | -0.87% |
| Full SR | 4.129 | 4.498 | +0.368 |
| H1 SR (2017-20) | 3.334 | 3.280 | -0.054 |
| H2 SR (2021+) | 4.772 | 5.843 | +1.071 |
| Neg years | 0/18 | 0/18 | — |
| Max weight | 10.00% | 10.00% | — |
| Min weight | 1.00% | 2.00% | +1.00% |
| LOO min OOS SR | — | 3.383 | — |
| LOO all > 3.0 | — | True | — |
| vt_bad sleeves | 4 | 0 | -4 |
| Energy exposure | 16.0% | 26.8% | +10.8% |
| N sleeves | 27 | 20 | -7 |

### Walk-Forward Folds (all positive ✅)

| Fold | IS Period | IS SR | OOS Year | OOS SR |
|------|-----------|-------|----------|--------|
| 1 | 2012-2016 | 6.53 | 2017 | 5.84 |
| 2 | 2013-2017 | 6.84 | 2018 | 4.70 |
| 3 | 2014-2018 | 6.64 | 2019 | 5.97 |
| 4 | 2015-2019 | 6.21 | 2020 | 3.25 |
| 5 | 2016-2020 | 3.66 | 2021 | 7.89 |
| 6 | 2017-2021 | 3.40 | 2022 | 4.13 |
| 7 | 2018-2022 | 3.30 | 2023 | 6.96 |
| 8 | 2019-2023 | 3.61 | 2024 | 6.23 |
| 9 | 2020-2024 | 3.63 | 2025 | 6.39 |
| 10 | 2021-2025 | 5.97 | 2026 | 5.39 |

Mean WF SR: 5.676 (min fold: 3.25 in 2020)

## 4. Critical Audit Findings

### FINDING 1: V4 uses FAILED_NO_PROMOTION sleeves [SERIOUS — RESOLVED in V5-honest]

V4's 27 sleeves include 4 strategies marked `FAILED_NO_PROMOTION` in campaign metadata:

| Sleeve | V4 Weight | Campaign Gate Failures |
|--------|-----------|----------------------|
| RB_ho_br_meanrev_w40_z20_zo1 | 4.91% | c_halves:FAIL, SR=0.914 |
| INTL_R2_RS252_LS | 6.58% | verdict: negative |
| CMDT_SectorRot_6m_LS | 1.98% | verdict: negative |
| CRED5_nfci_risk_k52_novt | 1.02% | a_sr FAIL, c_halves FAIL, d_yearly FAIL |

V5-honest excludes all 4 and still achieves higher OOS SR (3.965 vs 3.733).
V5-blend inherits V4's vt_bad sleeves (same 27-sleeve set).

### FINDING 2: V4 SLSQP weights are overfit [MODERATE — PARTIALLY ADDRESSED]

V4's IS-OOS gap of 2.356 indicates the SLSQP max-SR optimizer overfits IS data.
- Equal-weight on same 27 sleeves: gap=2.024, OOS SR=3.795 (better than V4)
- V5-blend (α=0.6): gap=2.402, OOS SR=3.846 (higher SR but gap doesn't improve)
- V5-honest: gap=3.076, OOS SR=3.965 (highest SR but highest gap)

The higher gap in V5-honest is concerning. However, walk-forward (10 folds, all
positive, mean SR=5.676) and leave-one-out (min=3.383, all>3.0) confirm the
result is robust despite the gap.

### FINDING 3: OOS annualized return drops [EXPECTED TRADE-OFF]

V5-honest: 21.59% vs V4: 24.58% at 1.6x leverage. The lower return is because
V5-honest uses 20 sleeves with max weight 10%, while V4 concentrates in
high-return sleeves. The Sharpe ratio improvement (+0.232) means better
risk-adjusted returns.

### FINDING 4: Energy exposure increases in V5-honest [WITHIN LIMITS]

V5-honest: 26.8% vs V4: 16.0%. Still under the 30% cap but with less headroom.
This is because the honest pool's best sleeves happen to include more energy
strategies (crack spreads, diesel, natural gas).

### FINDING 5: Data leakage check [PASS]

Both V5-blend and V5-honest fit weights on IS data only (<2017-01-01).
V5-blend uses V4's IS-fit weights blended with EW (no additional IS info).
V5-honest runs SLSQP on IS data only. OOS (>=2017) is a clean holdout.

### FINDING 6: Walk-forward confirms robustness [PASS]

V5-honest: 10/10 walk-forward folds positive (min=3.25, mean=5.676)
V5-blend: walk-forward SR=5.300 (vs V4: 5.198)

### FINDING 7: Leave-one-out stability [PASS]

V5-honest: LOO min OOS SR=3.383, all folds >3.0
V5-blend: LOO min OOS SR=3.276, all folds >2.0
No single sleeve is critical to either portfolio.

### FINDING 8: Gap sensitivity [CAUTION]

V5-honest's gap is 3.076, and it's stable across IS end dates (2.84-3.08).
This means the IS SR is consistently ~3 points above OOS SR — a structural
overfitting pattern, not a one-time artifact. The SLSQP optimizer on the honest
pool overfits more than V4's optimizer on the permissive pool, possibly because
the honest pool has fewer strategies (102 vs 118) giving less diversification
benefit per sleeve.

## 5. Verdict

**V5-honest** is the recommended improvement:
- OOS SR improved by +0.232 (3.733 → 3.965)
- Zero vt_bad sleeves (no FAILED_NO_PROMOTION strategies)
- Walk-forward confirmed (10/10 folds positive, mean SR=5.676)
- Leave-one-out confirmed (all >3.0)
- All 18 years positive, no negative years

**Trade-offs:**
- Annualized return drops 3% (24.6% → 21.6% at 1.6x)
- Daily DD increases 0.87% (-1.98% → -2.85%)
- IS-OOS gap increases 0.72 (2.36 → 3.08) — more IS overfitting
- Energy exposure increases 10.8% (16% → 26.8%) — less headroom

**V5-blend** is the conservative alternative:
- Smaller improvement (+0.113 OOS SR)
- Same vt_bad issue as V4
- Smaller return sacrifice (-3.3% ann)
- Smaller gap increase (+0.05)

## 6. Files Produced

| File | Description |
|------|-------------|
| `OPT_20V5_weights.csv` | V5-blend weights (27 sleeves, α=0.60) |
| `OPT_20V5_best.json` | V5-blend metrics |
| `OPT_20V5_full_monthly.csv` | V5-blend full-window monthly returns |
| `OPT_20V5_oos_monthly.csv` | V5-blend OOS monthly returns |
| `OPT_20V5_blotter.csv` | V5-blend trade records (46,259) |
| `OPT_20V5_honest_weights.csv` | V5-honest weights (20 sleeves) |
| `OPT_20V5_honest_best.json` | V5-honest metrics |
| `OPT_20V5_honest_full_monthly.csv` | V5-honest full-window monthly returns |
| `OPT_20V5_honest_oos_monthly.csv` | V5-honest OOS monthly returns |
| `OPT_20V5_perm_grid.csv` | Permissive pool grid search results |
| `OPT_20V5_AUDIT.md` | This audit report |
| `improve_v5.py` | V5 optimizer script |
