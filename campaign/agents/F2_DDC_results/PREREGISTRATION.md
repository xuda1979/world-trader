# F2-DDC PRE-REGISTRATION (2026-09-30, locked before any result was computed)

GOAL5DIR action B: "Deep-dive F2's drawdown-control policy as a STANDALONE research
milestone (not a sleeve; a post-processing optimizer on champion positions)."

## Question

Can a drawdown-control post-processing policy, applied to the V7.1 champion's
position stream, improve the champion's risk-adjusted numbers beyond noise — or
does the GOAL5DIR meta-conclusion ("overlays COST money": G1 RSI-gates, K1
kurt-overlay, V1 regime-gates all degraded) extend to DD-control?

## Data (frozen)

- Champion daily net returns: `OPT_20V71_FULL_LEDGER.csv`, daily
  `sum(pnl) - sum(cost)` (the canonical trade record; reproduce_v71 reconciles it).
- Window: 2009-01-01 .. 2026-09-22 (ledger bounds).
- Split (campaign convention): IS < 2017-01-01; OOS >= 2017-01-01.
  ALL parameter selection on IS only; OOS reported once per pre-registered arm.

## Champion reference (from the committed ledger, computed once, pinned below)

Computed 2026-09-30 from the ledger (daily, net):
  n=4847; SR_daily 5.3436; ann(geom) 28.81%.
Monthly convention (reproduce_v71): full SR 4.0792 / OOS SR 3.6718 / DD -3.161%.
This study reports BOTH conventions; gates use the monthly convention
(campaign canonical).

## Pre-registered policy families (the full grid — nothing added after seeing results)

Let r_t = champion daily net return; equity e_t = cumprod(1+r); DD_t = e_t/e*_t - 1
(running max); s_t = policy scale in [0,1] applied to next-day exposure:
r'_t = s_{t-1} * r_t (scale decided at close t-1 => T+1 causal).

1. **DDHALT** (hysteresis two-level halt): if DD_{t-1} <= -b: s=0 until
   DD recovers to >= -a (a < b). Grid: b in {3%, 5%, 7%, 10%}, a in {b-2%, b-1%}.
2. **DDSCALE** (linear de-risk): s = clip(1 - (|DD_{t-1}| - a)/(b - a), s_min, 1),
   s_min in {0, 0.5}. Grid: a in {1%, 2%}, b in {4%, 6%, 8%}.
3. **VOLTGT** (realized-vol target, no DD term): s = min(1, tgt/sig21_{t-1});
   sig21 = std of last 21 daily nets (known at t-1). Grid: tgt in {10%, 15%, 20%}.
4. **TLOSS** (trailing-loss halt, the "OSS-halting" tool F2 named): halt if
   rolling 63d return <= -x; resume when rolling 63d return >= 0. x in {5%, 8%, 12%}.

## Costs (charged on every scale change, conservative)

Champion gross daily = net / s_champion where s_champion=1 (ledger is net; the
policy multiplies GROSS exposure, so the cost/margin components scale too). When
the policy changes scale s_{t-1} -> s_t, the portfolio trades |Δs| of the whole
book at 6.4bps one-side (BPS=6.4, the campaign's mandated full-cost convention).
Daily policy cost = 6.4e-4 * |s_t - s_{t-1}|. Margin/borrow effects of scaling
are second-order (≤1.6x book, 4.5% margin on (gross-1)) and are charged as
0.045 * max(s_t*LEV - 1, 0)/252 * |Δs| ≈ 0 (ignored; disclosed here).
Annual turnover is reported; a policy with implausible turnover is rejected on
inspection regardless of SR.

## Gates (all must pass on OOS for PROCEED; else REJECT and the idea joins DEAD_IDEAS)

G1. OOS monthly SR >= champion OOS monthly SR + 0.10 (material, not noise).
G2. OOS MaxDD >= champion OOS MaxDD (i.e. no worse; MaxDD negative).
G3. OOS ann >= champion OOS ann - 1.0pp (SR gain must not come from gutting return).
G4. Neg years (OOS) == 0 (champion invariant preserved).
G5. Policy-year turnover <= 6 (trade feasibility).
G6. IS->OOS sign consistency: the arm's OOS SR edge vs champion must be >= 0
    (no sign flip between selection window and report window).

## Honesty notes (pre-committed)

- Multiple-comparisons: the grid has 8+12+3+3 = 26 arms. The IS champion of each
  family is carried to OOS; a family PROCEEDs only if its IS-selected arm clears
  all gates OOS. A single-arm pass anywhere is reported as exploratory, not adopted.
- Adoption bar is deliberately HIGH: the champion is the campaign's system of
  record; a post-processing layer must pay for its own model risk.
- Expected outcome per the G1/K1/V1 prior: REJECT. A clean reject with full
  numbers is the intended deliverable if the effect is absent.

DONE F2_DDC_PREREGISTRATION
