# Capacity-tier momentum IC — can we see the agile-operator edge in the covered universe? (2026-08-16)

**Question** (thesis Pillar 1 + 4): the agile/low-capital edge should concentrate in
capacity-constrained (illiquid/smaller) names where institutions can't deploy.
Do we observe momentum IC *rising* as we move from the most-liquid to the
least-liquid tier of the covered universe — i.e., is the capacity-constrained
momentum edge visible in the data we can actually price?

This is a direct, no-look-ahead, cross-sectional test using only the **reliable
local price panels** (no gated live endpoints). It complements the firing's other
finding (the PEAD/event edges of Pillar 2) and its prior ones (funding-capture of
Pillar 1+3) by isolating the *capacity* axis of Pillar 1 on price-momentum.

---

## 1. Method

- Universe: 676 named price series from `twelve_big`∪`twelve_liq`∪`twelvedata`
  ∪`polygon[_v2]`, aligned on 973 daily bars (2023-06 → 2026-08, ~3y recent).
- **Capacity proxy:** each name's median daily dollar-turnover (close × vol).
  Split into terciles: `large` (med **$566M/day**), `mid`, `small` (med
  **$28.5M/day**).
- **Signal:** past-252d risk-adjusted momentum (log-return over 1y) — the
  canonical medium-frequency (Pillar 4) signal.
- **Forward:** 21d and 63d return. Monthly rebalance, rank-IC (Spearman) per
  month within each tier, then mean IC +- SE across months. No look-ahead.

Artifacts: `tools/quant/capacity/tier_ic.py`, `reports/capacity_tier_ic.json`.

---

## 2. Results (mean rank-IC +- SE, monthly, no look-ahead)

| tier | med $vol/day | IC 21d | IC 63d |
|------|--------------|--------|--------|
| large | $566M | +0.028 ± 0.035 | +0.021 ± 0.029 |
| mid   | —    | +0.012 ± 0.029 | +0.022 ± 0.024 |
| small | $28.5M | +0.006 ± 0.030 | +0.012 ± 0.021 |

**Read 1 — momentum is a real, weakly-positive medium-frequency signal.**
Mean rank-IC is positive in *every* tier at *both* horizons (+0.01 to +0.03).
Consistent with a modest but genuine Pillar-4 predictive signal (the same
family the flagship's momentum sleeves monetize at the portfolio level).

**Read 2 — NO statistically distinguishable capacity-tier effect in the covered
universe.** The apparent "large > small" ordering (0.028 vs 0.006 at 21d) is
**within ~1 standard error** everywhere (SE are ~0.02-0.035; only 18-34 monthly
obs per tier). We **cannot** claim the edge strengthens OR weakens with
liquidity in this data.

**Read 3 — the true micro-cap sandbox is NOT in the panels.** The "small" tier
here still trades ~$28.5M/day — small/mid-cap at best)Skip to the real micro-caps
($1-5M/day) where mega-funds "can't fit" are *entirely absent* from the free
panels. So this study **does not and cannot test the thesis's actual
capacity-constrained (micro-cap) claim** — it only shows momentum in the covered
small-mid/large tier is flat-by-liquidity.

---

## 3. Why this matters (steering Pillar-1 research)

The honest conclusion is **directionally useful, not a thesis refutation**:

1. **Price-momentum is the WRONG expression of the capacity-constrained edge.**
   In the covered universe it is liquidity-flat — so chasing "small-cap momentum"
   in the observable tier adds nothing. This redirects Pillar-1 effort OFF
   price-momentum and ONTO the structural/depth edges where capacity constraints
   truly bite (funding-capture, PEAD drift, event/dividend, niche-commodity
   basis) — precisely the families firing #1 (funding, mechanism-real-but-gated)
   and #2 (PEAD, sub-significant) examined.
2. **The observable universe cannot reach the target sandbox.** Consistent with
   the recurring finding across all firings: the free feed prices the
   efficient/liquid universe where an agile operator's edge is weakest, and the
   edge-rich micro-cap / niche universe is data-gated (paid tier).

---

## 4. Verdict

> Momentum gives a real-but-modest Pillar-4 signal, liquidity-flat in the covered
> universe within noise. The capacity-tier *amplification* the thesis predicts is
> **not observable** in the free panels (SE too wide; true micro-caps absent).
> Action: keep momentum as a portfolio sleeve (it is already monetized); do NOT
> size a separate "small-cap momentum" conviction on this evidence; acquire true
> micro-cap OHLC (paid tier) before claiming the capacity-constrained edge is
> reachable with price data. Consistent with repo discipline: an honest
> within-noise negative/refining result, documented.
