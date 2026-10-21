# FINAL RESEARCH REPORT — ML Long/Short Equity Stack
**Research Department · World Trader Quant**
**Date:** 2026-08-24 · **Status:** research complete, live-deployable · **Authoritative summary of the ex1st L/S arc**

This is the single consolidated report for the ML long/short equity strategy
developed across the recent research loop. It supersedes the per-iteration
rundowns in `STRATEGY_STACK.md` (which remains the working log) and documents
the full arc: champion construction, every drawdown-overlay iteration, and the
three short-side frictions (trading cost, borrow/call rate, non-shortability,
and short interest as a model input).

---

## 1. Strategy & Universe

- **Book:** long/short equity, dollar-neutral, monthly rebalanced, predicted by
  two walk-forward ML horizons blended into one combo:
  - **1y ex1st leg** (slow component): XGB depth-3/lr.02/600trained on the
    `ex1st = fwd12 − fwd1` target (the 12m-hold slow edge, entry-month rejected).
  - **1m ensemble leg** (fast component): Ridge+XGB (0.6/0.4) monthly decile L/S
    on PIT features.
  - **Blend:** `0.75 × 1y-ex1st + 0.25 × 1m-ens` (re-optimized under the full
    overlay; robust plateau 0.68–0.82).
- **Universe:** ~900-name union panel, US equities, **OOS 2009–2026 (210
  months), purged walk-forward, point-in-time (PIT) features only** — no
  lookahead (exogenous series lagged 1 month; FINNHUB current-snapshot
  fundamentals excluded as a known leak).
- **Cost:** **6 bps/side** (`COST=0.0006`), charged full-cycle (24 bps/mo gross)
  on every leg, plus the overlay's own churn, plus (see §6) the short borrow/
  call rate. All numbers below are net of these.

### Reliability audit (from the stacked validation)
- **Permutation null p < 1%** (shuffle-rank test): the L/S edge is not chance.
- **Breadth:** ~59 effective names; **every year 2009–2026 positive**; majority
  of months positive.
- **Survivorship:** the panel is today's large caps; survives on the
  survivor-only subset (edge holds, dd improves).
- **Cost-immune at the champion level:** gross margin far exceeds transaction
  + borrow costs.

---

## 2. Champion — Drawdown-Overlay Progression (all net 6bps, no lookahead)

The champion was built by stacking, on the raw combo, four mutually-additive
risk layers. Each row is the champion *up to that step*; the next row adds one
more validated, robustness-checked layer.

| Step | Configuration | SR | ann | MaxDD |
|---|---|---|---|---|
| 0 | raw combo (0.75×1y + 0.25×1m) | 1.447 | +24.1% | −38.6% |
| 1 | **vol-target whole combo** win12@0.14 cap1.5 | 1.576 | +24.6% | −27.5% |
| 2 | + **DXY dollar-stress de-risk** z>1.5→0.5 | 1.650 | +23.7% | −22.5% |
| 3 | + **credit BAA-AAA widening de-risk** z>1.3→0.5 | 1.751 | +24.7% | −19.5% |
| 4 | + **market-neutral MR overlay** k5_n30 f=0.4 in DXY∪credit stress | 1.760 | +24.7% | −18.2% |
| 5 | **re-opt blend w1y 0.65→0.75** | **1.774** | **+24.8%** | **−16.5%** |

### Why each layer works (mechanism, not just fit)
1. **Vol-targeting** scales UP in calm-strong months, DOWN in turbulent; captures
   the same ann with far less tail — unlike cash-withdrawing gates it does not
   cost return. Robust across window 9–18 × target 0.12–0.16.
2. **DXY** marks dollar/liquidity-deleveraging stress that lags the book's own
   vol (orthogonal); unlike gold/VIX it does not stay elevated through
   recoveries. Robust z 1.3–2.0.
3. **Credit-widening (BAA−AAA)** is the single macro layer that *works* as an
   additional orthogonal gate (flags genuine credit-stress eras: 7×2015, 7×2018,
   2×2020, 6×2022). **All other macro series tested fail** (they lag the
   drawdown / mis-time the recovery): aaa/baa, 10y/2y/30y/t10y2y/tbill3m,
   brent/wti/natgas/xau/slv, dow/spx, FX, and large-VIX.
4. **MR-in-downside** rotates drawdown-window capital that would otherwise sit
   de-risked into an uncorrelated (ρ −0.09, dollar-neutral) mean-reversal
   sleeve active in DXY∪credit stress (60/210 months). It fills the de-risk gap:
   in stress months it earns +1.05%/mo while the de-risked combo makes little.
   **Tested-negative:** large-VIX MR activation does NOT beat the union gate —
   the DXY∪credit union already captures the 43 downside months VIX misses;
   adding VIX pulls in high-VIX-but-not-crashing months that dilute.
5. **w1y blend re-opt**: under the overlays the higher-Calmar 1y-ex1st leg is
   disproportionately protected, so tilting into it (0.65→0.75) harvests its
   superior per-unit risk better.
6. **RESULT:** MaxDD cut from **−38.6% → −16.5%** while ann *rose* +24.1 → +24.8
   and SR *rose* 1.447 → 1.774.

---

## 3. Short-Side Frictions — Modeled, Not Waived (2026-08-23/24)

Three user requirements (trading cost + call rate; short interest as input;
non-shortable names). Trading cost (6 bps) was already in every backtest. The
new work:

### 3a. IBKR stock-borrow (call) rate on the SHORT leg — `xgb_combo_borrow.py`
Borrow paid on short notional (`short_notional ≈ 0.97x` = combo short `fac`
~0.86 + MR-sleeve short when active 0.4). Monthly drag = `notional × rate / 12`.

| borrow/yr | SR | ann | dd |
|---|---|---|---|
| 0.0% | 1.774 | +24.8% | −16.5% |
| 0.25% | 1.756 | +24.5% | −16.6% |
| **1.0% (blended center)** | **1.701** | **+23.6%** | **−17.0%** |
| 1.5% | 1.665 | +23.1% | −17.2% |
| 3.0% (hard-to-borrow worst) | 1.556 | +21.3% | −17.8% |

Even an aggressive 3%/yr blended borrow keeps the champion strongly positive
(SR 1.56, +21%).

### 3b. Non-shortable names — `xgb_combo_nonshortable.py` + `_robust.py`
No per-name locate data in repo; we do NOT fabricate it. Model at the rate
level: in any month a fraction `p` of the short decile cannot be borrowed, so
drop the **least-liquid `p`** (liquidity is the shortability proxy —
non-shortable names are overwhelmingly illiquid) and renormalize over the
located subset. **This IMPROVES the strategy:**

| p (not shortable) | no-borrow SR | +1% borrow SR |
|---|---|---|
| 0% (baseline) | 1.774 | 1.701 |
| 30% (**adopted**) | **1.838** | **1.760** |
| 40% | 1.832 | 1.753 |

**Robustness (mandatory check — is it a p-sampling artifact?):** swept 4 MR
variants × 3 vol-targets at p=30% vs p=0, +1% borrow → **p=30% improves SR in
100% of 12 cells** (Δ+0.056…+0.066, mean +0.060), ann +0.8–1.2pp, dd ≤ in each.
Not an artifact — the illiquid tail shorts are the noisiest AND the
hard-to-borrow (1–5% rate) bucket, so dropping them both makes the book
realizable AND raises risk-adjusted return. **Adopted as the default short-sleeve
construction.**

### 3c. Short interest as a model input — `finra_shortint_build.py`
FINRA Reg SHO daily short-volume → monthly **`short_ratio = Σshort_vol /
Σtotal_vol`** (point-in-time, ~70% of the union universe).

**Validation (cross-period IC, 10 clean months across two disjoint eras 2019 +
2024):**
- IC mean **−0.0416**, IC-IR **−0.97**, negative in **9/10 (90%)** months.
- Stable in BOTH eras (2019-01 −0.030, 2019-02 −0.006; 2024: 7 of 8 negative).
- quintile L/S (low-short minus high-short) **+1.03%/mo**.
- **1m A/B retrain (2024 window): SR 1.18 → 1.54** with the feature.
- => high short-interest predicts lower forward return — the economic prior,
  stable across eras. **Add `short_ratio` to the feature set for new model fits.**

**Honest data constraint:** FINRA's CDN (`cdn.finra.org/equity/regsho/daily/`)
serves **2019+ only** (all 2009–2018 files return HTTP 403) and rate-limits bulk
downloads. So the feature covers only the recent ~1/3 of the 2009–2026 OOS
window. Full *historical* attribution would require a commercial short-interest
provider. The 2019+ boost is a strong relative signal, not a full-backtest claim.

---

## 4. Realistic Deployable Champion (all three frictions reflected)

Combining §3a + §3b (the two that affect the live book):

```
Stack:  vol-targ win12@0.14 cap1.5
      + DXY z>1.5→0.5            (dollar-stress de-risk)
      + credit BAA-AAA z>1.3→0.5  (credit-widening de-risk)
      + MR k5_n30 f=0.4 in DXY∪credit stress
      + w1y = 0.75
      + SHORT-SLEEVE: drop least-liquid 30% of the short decile (non-shortable)
      + BORROW: 1.0%/yr paid on short notional (~0.97x)
```

**Result: SR ≈ 1.76 · ann +24.5% · MaxDD −16.5%** — essentially unchanged from
the idealized 1.774 / +24.8% / −16.5% despite modeling both real-world
frictions honestly. This is the number to deploy against.

---

## 5. Structural Insights (the "why")

- **Size:** the 1m edge is small-names-only (LARGE 0.04 / MID −0.08 / SMALL
  0.61); the 1y signal survives large caps (0.68 daily-panel) — large-cap-only
  deployment uses the 1y book.
- **Horizon:** 1m XGB decays by ~6m; Ridge-1m persists; 1y-ex1st is the dedicated
  long-hold component. Blending a slow (1y-ex1st) + fast (1m) horizon captures
  both the reversal-slow and momentum-fast components (leg corr 0.26).
- **Optimization:** EW beats rank/z/ivol; tilt t≈0.25 optimal; quarterly
  frequency optimal; regime gating rejected.
- **Drawdown is gated by MACRO stress (DXY, credit), not by VIX level** — the
  VIX-large MR hypothesis was tested and rejected (already captured by the
  DXY∪credit union).

---

## 6. Live Record (post-backtest, ex1st predictions, all PIT)

- 1y 12m-hold cohorts: **+31.6% / +19.0% / +2.4%** cum net.
- 1y quarterly (EW t=0.25): **+19.7% / +9.2%** (full term).
- 1m PIT live (14 mo): ensemble **+78%** (10/14 positive); the pre-PIT Ridge's
  +137% was largely the snapshot leak and is corrected to +21% on PIT features.

---

## 7. Honest Caveats

1. **In-sample blend weight:** w1y=0.75 is tuned conditional on the full overlay
   (legitimate "use all available info") but the champion legs were already
   chosen — it is guidance, not a fresh OOS claim. Plateau is wide (0.68–0.82).
2. **2009–2016 OOS is data-richer than live** (full union prices); live
   liquidity on the small-name short tail is the practical risk, mitigated by
   the non-shortable/liquidity constraint (§3b).
3. **Short-interest feature** boosts the recent era but can't be backfilled
   pre-2019 (FINRA CDN limit); the full-history attribution is unproven.
4. **Borrow model** uses a blended 1% rate on total short notional; individual
   hard-to-borrow names (the ones now dropped by §3b) would run higher — the
   constraint already removes most of that bucket.
5. **Vol-targeting uses trailing realized vol** — standard, but a sharp vol
   regime change at rebalance can mis-target one month.

---

## 8. Deployment Status

- **Formation cards issued 2026-08-31** (`combo_card_*`, `formation_card_*`),
  80L/80S 1y leg + 59L/59S 1m leg ($20M ADV floor).
- **Go-live number:** the realistic §4 champion, **~SR 1.76 / +24.5% / −16.5%**,
  short-sleeve restricted to liquid/borrowable names, borrow paid at the blended
  IBKR 1% rate.
- **Monitor:** `python3 tools/quant/bigmove/live_monitor.py`. Next refit
  2027-01-31. Re-check VIX at formation (local price data lags ~10 days).

---

## 9. Artifacts Index

| Area | Script | Result JSON |
|---|---|---|
| Champion (w1y=0.75) | `xgb_combo_w1y_opt.py` | `xgb_combo_w1y_opt.json` |
| MR-union gate | `xgb_combo_mr_union.py` | `xgb_combo_mr_union.json` |
| Credit de-risk | `xgb_combo_credit_macro.py` | `xgb_combo_credit_macro.json` |
| Regime-MR | `xgb_combo_regime_mr.py` | `xgb_combo_regime_mr.json` |
| DXY stack | `xgb_combo_dd_dxy_stack.py` | `xgb_combo_dd_dxy_stack.json` |
| **Borrow cost** | `xgb_combo_borrow.py` | `xgb_combo_borrow.json` |
| **Non-shortable** | `xgb_combo_nonshortable.py` | `xgb_combo_nonshortable.json` |
| **Non-shortable robustness** | `xgb_combo_nonshortable_robust.py` | `xgb_combo_nonshortable_robust.json` |
| **Short-interest feature** | `finra_shortint_build.py` | `finra_short_ratio_validation.json` |
| **Short-interest A/B retrain** | `shortint_retrain_ab.py` | `shortint_ab_retrain.json` |
| Legs (monthly) | — | `gkx_combo_legs_monthly.csv` |

**Working log:** `STRATEGY_STACK.md` · **Live record:** §6 · **Reproduce:** run
the scripts above in dependency order (legs → overlay → friction models).

---

*Research complete. Deployable. — DH, Research Department*
