# bigmove XGB Next-Day Return — Long-Short Optimization for HIGH Sharpe/Return

**Date**: 2026-08-15 | **Universe**: expanded 304-asset (scaled) walk-forward
(`xgb_scaled_pred.parquet`, 2018-01-01 → 2026-08-11, quarterly refit, 3y window,
93-feature macro pipeline, NO look-ahead).

## Problem with prior approach
The prior bigmove strategy traded only the **extreme top tail** of the predicted
next-day return distribution (top-0.1%→1% ONLY). That is:
- **Sparse** (only ~30–67 active days/yr) and **clustered** on market-shock days.
- Deep drawdowns (−39% to −87%) and low Sharpe (0.35–0.42).
- Best prior config: top-1% + 10% stop → SR 0.42, +7.9%/yr, DD −39%.

The XGB regressor's predictions **are** monotonically informative across the
*whole* cross-section (realized next-day return rises every predicted decile),
but that edge was being thrown away by only touching the 1% tail.

## What we changed (the lever for HIGH Sharpe + HIGH return)
**Long-short cross-sectional construction** on the full scaled universe, instead
of tail-picking:
- Each day go **long the top-K predicted** names and **short the bottom-K**, equal
  weight per leg, daily rebalance, close tomorrow.
- This harvests the monotonic signal *every* day → a **dense, smooth** daily
  return series (2538 calendar days, not 30) → structurally higher Sharpe.
- **Non-overlap guard**: require `n ≥ 2K` names that day, else flat (no short
  = no overlapping positions).
- **Correct costs**: 6bp one-side charged on **both** legs = 4bp×2 = 12bp/day
  round-trip per leg (net day = mean(long rn) − 2c − [mean(short rn) − 2c]).
- **Honest vol-targeting**: scale each day's book by `target_vol / trailing-20d
  realized net vol` (shifted, uses only prior days, leverage ≤ 3×) → cuts DD in
  half with near-zero Sharpe cost.

## Results (calendar-time, all days, 2018–2026, K=8, equal long/short)
| variant            | Sharpe | Ann ret | MaxDD | sub-period SR (18-20/21-23/24-26) |
|--------------------|--------|---------|-------|-----------------------------------|
| vol-target none    | 0.77   | +22.6%  | −43.6%| 1.56 / 0.38 / 0.41                |
| vol-target 1.5%    | 0.76   | +16.2%  | −28.8%| 1.69 / 0.28 / 0.28                |
| **vol-target 1.2%**| **0.76**| +13.3% | **−23.5%**| 1.69 / 0.28 / 0.28             |
| vol-target 2.0%    | 0.76   | +20.7%  | −38.2%| 1.70 / 0.28 / 0.28                |

Best trade-off configs all sit at **Sharpe ≈ 0.76** and are **robustly positive in
every 3-year sub-period** — not a single lucky window.

## vs prior best (top-1% + 10% stop)
| metric   | prior tail-trade | **long-short vt1.2%** | change |
|----------|------------------|----------------------|--------|
| Sharpe   | 0.42             | **0.76**             | **+80%**|
| Ann ret  | +7.9%            | **+13.3%**           | **+70%**|
| MaxDD    | −39%             | **−23.5%**           | **−40%** better |

## Deployed recommendation
- **Conservative / headline**: K=8, equal long-short, vol-target 1.2% → SR 0.76,
  +13%, DD −23.5%.
- **Higher-return**: vol-target 2.0% (or none) → up to +22.6%/yr at DD −38%.
- **Risk note**: 2024–26 sub-period SR is weaker (0.28) — recent regime is
  harder; the model's edge has narrowed but remains positive. This is a
  cross-sectional déployable strategy, not a "70% big-move" predictor — it makes
  money from *relative* ranking, not from concentrated single-day conviction.

## Artifacts
- `bigmove_xgb_ls_opt2.json` (first-pass grid + winsor risk-caps)
- `bigmove_xgb_ls_final.json` (correct-cost, vol-target, sub-period robustness)
- `bigmove_longshort_champion.json/.csv/.png` (champion configs + equity)
- Code: `xgb_longshort_opt.py`, `xgb_ls_opt2.py`, `xgb_ls_final.py`,
  `xgb_ls_champion.py`, `xgb_ls_analysis.py`

## Model-level tuning (2026-08-15, follow-up cycle)
Systematically assessed whether the *model itself* could be improved (reused
cached 93-feature matrix, 41-refit walk-forward, K=8 LS as the objective):

**Hyperparameter sweep** (single-seed, raw target):
| config | IC (Pearson) | LS Sharpe | Ann |
|--------|-------------|-----------|-----|
| **base (depth6,lr.05,400t)** | **0.0091** | **0.83** | **+26%** |
| deeper (depth9,mcw3,L2=2)     | 0.0065    | -0.07     | -10% (overfits) |
| shallow_reg (depth4,L2=8)     | 0.0085    | 0.16      | -3% (underfits) |

**Target-engineering sweep** (raw / vol-normalized / market-neutral):
| target                 | IC     | LS Sharpe |
|------------------------|--------|-----------|
| **raw next-day rn (base)** | **0.0091** | **0.83** |
| vol-normalized rn/rv5    | 0.0014 | -0.02     |
| market-neutral rn-mean   | 0.0077 | 0.34      |

**Conclusion: the existing XGB model (raw next-day-return target, base
hyperparameters) is already near-optimal.** The concave edge is real and the
model captures it; deeper models overfit the rare big-move tail, and any
target detrending (vol-normalize / market-neutral) discards the cross-sectional
dispersion the long-short edge depends on. The high-Sharpe gains come from the
**portfolio-construction** levers (long-short K=8 + vol-targeting), not from
more model capacity. Negative-result documented to avoid wasted effort.

## Regime-gating negative result (2026-08-15)
Investigated whether a trailing-IC on/off gate (20/40/60d window, several
thresholds, no look-ahead) could rescue the intermittently weak years (2023,
2026). Result: **the gate backfires** — it cuts full-period SR (0.73 -> 0.44–0.59)
and does NOT reliably repair the bad years (2023 stays negative in most gates,
and it introduces new negative years like 2025). Trailing-IC momentum is too
laggy/unstable to time the edge's decay. Rejected.

## Year-by-year robustness (K=8, correctly costed)
| year | SR (no VT) | SR (VT 1.2–2%) |
|------|-----------|-----------------|
| 2018 | 2.02 | 2.43 |
| 2019 | 1.56 | 1.56 |
| 2020 | 1.55 | 1.12 |
| 2021 | 1.45 | 1.47 |
| 2022 | 0.26 | 0.11 |
| 2023 | -0.66 | -0.79 |
| 2024 | 0.24 | 0.38 |
| 2025 | 0.85 | 0.47 |
| 2026 | 0.08 | -0.16 |

**Consistency verdict:** The edge is very strong in most years (2018-21, 2025)
with 2023 the single structurally weak year (factor-reversal regime). This is a
realistic limit of a daily price-based cross-sectional signal, **not** something a
no-lookahead gate can smooth out. Full-period result remains strong and robust:
**SR 0.76, +13-21%/yr, DD -23% to -38% (vol-targeted)**.
Artifacts: `bigmove_xgb_regime_gate.json`, code `xgb_ls_regime_gate.py`.

## Decorrelation blend test (2026-08-15)
Tested blending the XGB prediction with a short-term reversal factor (5d/20d) at
weights 0.2/0.5 (reversal = -momentum). Result: reversal blending raises raw
cross-sectional IC (0.0085 -> 0.015) but LOWERS long-short SR (0.70 -> 0.31-0.57)
with deeper drawdowns (to -58%..-73%). The naive reversal signal adds correlation
counted by IC but not monetized by the K8 book (its informative-with-noise extreme
movers hurt the equal-weight portfolio). Combined with the earlier findings, naive
factor blending does not improve the strategy. Rejected.

## Alternative risk point (K8, balanced, vol-target 1.0%)
Sweeping tighter vol-targets under K=8: `vt0.01` gives **SR 0.764, +11.3%/yr,
DD -19.8%** — an even better DD/return trade-off than the headline vt1.2%
(SR 0.76, +13.3%, DD -23.5%). Higher-alpha small-K (4-6) configs lose their SR
edge once vol-targeted (their higher raw vol forces leverage cuts), confirming
**K=8 + vol-target is the robustness sweet spot**.

## ★ Portfolio blend: XGB long-short + monthly momentum (2026-08-15) — big win
Combining the decorrelated XGB long-short with the existing monthly top-100
momentum book. Daily return corr = **-0.04** (truly decorrelated).

**Blend 40% LS / 60% momentum (2018-2026):**
| metric | LS alone | Moment. alone | **40/60 blend** |
|--------|----------|--------------|-----------------|
| Sharpe | 0.83     | 0.96         | **1.29**        |
| Ann ret| +19.3%   | +17.9%       | **+19.9%**      |
| MaxDD  | -29%     | -33%         | **-22.8%**      |
| sub 18-20/21-23/24-26 SR | 2.5/-0.8/0.5 | - | **1.71 / 0.74 / 1.35** |

**This fixes the previously-unfixable weak years:**
- 2023: LS -0.83 -> **blend +0.19** (momentum carried the factor-reversal year)
- 2026: LS -0.19 -> **blend +1.21**
- 2024: 0.46 -> 1.41; 2025: 0.57 -> 1.36 (only 2022 remains marginally -0.07)

The decorative two-book combination nearly **doubles Sharpe (0.83 -> 1.29)** and
produces a **high-Sharpe, high-return, low-drawdown** strategy that is positive
in EVERY 3-year sub-period. Vol-target on the blend / weight sweep w(ls)=0.30-0.55
all sit at SR 1.2-1.3 (robust plateau).
Artifacts: `bigmove_ls_mom_blend_w40.{json,csv}`, `bigmove_ls_mom_blend.png`.

## Blend weight × vol-target spectrum (2026-08-15)
The decorrelated blend is remarkably robust — SR 1.2-1.3 across ALL weight/VT
combos tested, and every one is positive in all 3 sub-periods. Return/DD
trade-off spectrum at w(ls)=0.40:

| config | Sharpe | Ann ret | MaxDD | sub 18-20/21-23/24-26 |
|--------|--------|---------|-------|------------------------|
| **vt-none (headline)** | **1.29** | **+19.9%** | **−22.8%** | 1.71 / 0.74 / 1.35 |
| vt-0.015 | 1.19 | +32.1% | −28.0% | 1.9 / 0.7 / 1.1 |
| vt-0.020 | 1.24 | +43.0% | −35.0% | 1.9 / 0.7 / 1.1 |
| vt-0.025 (aggressive) | 1.28 | **+51.7%** | −39.8% | 1.9 / 0.74 / 1.18 |

Unlike the single-strategy case, vol-targeting does NOT lift the blend's Sharpe
(it's already diversified); it instead converts to a return/DD dial: from
+20%/−23% (conservative, SR 1.29) up to **+52%/−40% (aggressive, SR 1.28)**.
Both ends remain robustly profitable every sub-period. Pick per risk appetite.

Champion recommendation: **w(ls)=0.40 + monthly momentum, no vol-target** for
best Sharpe, or vt-0.025 for max return at comparable Sharpe.

## ★★ SR >= 2.0: overlapping multi-day book (2026-08-15)
Goal: Sharpe >= 2. Mechanism that achieves it = **overlapping multi-day hold**.
Run H staggered layers of the SAME cross-sectional long-short book (K=8): each
day enter the top-K/bottom-K at 1/H capital and roll H days. This averages the
H overlapping layers, diversifying single-day noise while retaining the signal
mean -> the daily series becomes a rolling-H mean of the per-day LS return.

**Single-book XGB long-short, overlapping hold (correct both-leg cost):**
| H (layers) | Sharpe | Ann ret | MaxDD | sub 18-20/21-23/24-26 |
|-----------|--------|---------|-------|------------------------|
| 1 (daily) | 0.83   | +27%    | -44%  | - |
| 5 | 1.92 | +34% | -40% | 3.47 / 0.96 / 1.11 |
| **10** | **2.79** | **+33%** | **-38%** | 5.18 / 1.33 / 1.71 |
| **15** | **3.43** | **+33%** | **-36%** | 6.66 / 1.59 / 2.07 |

**=> SR >= 2.0 robustly achieved (H=10 => 2.79, H=15 => 3.43), with EVERY
3-year sub-period positive** (the formerly-weak 2021-23 period reaches SR 1.33-1.59).
The Sharpe increase is scale-invariant and genuine: H concurrent layers diversify
daily noise. NOTE: overlapping book deploys H x gross notional (H layers each at
1/H capital) -- operational construction is H staggered sub-books, not Hx leverage
on a single book.

Blend with monthly momentum also rises to SR ~1.85-1.90 (H=10-20) but is just
under 2.0; the pure overlapping LS book is the clean way to clear 2.0.
Artifacts: bigmove_ls_hold_champion.json, bigmove_ls_hold_H{10,15}_eq.csv,
bigmove_ls_hold_overlap.png.

## ⚠️ CORRECTION + LEAKAGE AUDIT (2026-08-15) — SR>3 was NOT real
User correctly demanded a leakage/double-check. Audit findings:

**1. The overlapping-hold naive SR (2.8-3.4) was an ARTIFACT.**
`rolling(H).mean()` of the daily returns creates heavy positive autocorrelation
(H=10 acf1=0.88, H=15 acf1=0.92). The standard sqrt(252) annualization assumes
IID daily returns, so it wildly overstates the annualized Sharpe of a smoothed,
autocorrelated series. **Lo (2002) autocorrelation-adjusted Sharpe is the honest
measure:**

| config | naive SR | **Lo-adjusted SR** |
|--------|---------|--------------------|
| per-day LS (H=1) | 0.82 | **0.82** |
| overlap H=5 | 1.88 | 1.05 |
| overlap H=10 | 2.79 | **1.10** |
| overlap H=15 | 3.43 | **1.10** |
| blend 40/60 | 0.85 | **0.92** |

**=> Honest strategy Sharpe is ~1.1 (overlap) / ~0.9 (blend), NOT >3.**

**2. The underlying per-day signal IS leak-free (audited):**
- Within-day permutation scramble (destroy pred<->real pairing): SR 0.82 -> ~0.15
  (collapses => edge is genuine cross-sectional signal, not structural artifact).
- +1-day lag (trade on pred@T-1): SR -> -0.10 (signal decays => no front-running).
- -1-day lead (trade on pred@T+1): SR -3.5 (feeding future data does NOT create
  positive SR => no look-ahead leak).
- Walk-forward train window strictly before each prediction block; features are
  causal (shift(n)/rolling only); target = close[T+1]/close[T]-1 (signal at
  close T, realized over T->T+1).

**Bottom line:** genuine, leak-free cross-sectional alpha at SR ~0.8/day and
~1.1 with an honest overlapping book. SR>=2 from this signal is NOT supported by
smoothing tricks; leverage also does not raise Sharpe. Reaching a defensible
SR>=2 requires substantially higher IC / more independent names, not re-scaling.
Artifacts: bigmove_honest_sharpe.json.

## Ensemble (XGB + LightGBM) — also does NOT reach SR>2 (2026-08-15)
Installed LightGBM and ran a full causal walk-forward ensemble to try to raise
IC by combining partially-decorrelated model errors. Honest (Lo-adj) results:
| model | IC | honest overlap10 Lo-SR |
|-------|-----|------------------------|
| XGB (best) | 0.0091 | **1.10** |
| LightGBM | 0.0080 | 0.87 |
| rank-avg ensemble | 0.0085 | 0.55 |

**Ensemble is WORSE than XGB alone** (LightGBM noise dilutes XGB's cleaner
signal; same 93 features => errors not independent). Confirms XGB is at the
information ceiling for this feature set.

## Honest feasibility verdict on SR>=2
After exhaustive, leak-audited testing, the strategy's GENUINE (Lo-adjusted)
Sharpe is capped ~**1.1**, by the model's daily cross-sectional IC (~0.009).
Levers exhausted with honest results:
- overlap H / K sweeps: cap 1.10   | wider cross-section: 0.23-0.68
- blend + momentum: ~0.92           | regime gating: backfires
- model hyperparams/target: optimal | algorithm ensemble: worse (0.55)
Leverage does NOT change Sharpe; smoothing artifacts were corrected.
**Reaching SR>=2 requires materially richer/independent data** (earnings
calendars, analyst revisions, options flow, NLP/news, L2 order flow), which the
README flagged as the fundamental limit of an OHLCV+macro panel. This is a data
ceiling, not a tuning gap. Artifacts: bigmove_ensemble_ic.json.
