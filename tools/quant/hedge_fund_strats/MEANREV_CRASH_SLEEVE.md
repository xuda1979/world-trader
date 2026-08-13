# Mean-Reversion Crash-Sleeve — Research & Deployment Spec (2026-08-13)

**Purpose (user ask)**: a mean-reversion market-neutral strategy that profits in
the episodes where the flagship all-weather book loses money.

## Result summary

Short-horizon (k=3-5d) cross-sectional equity reversal (long worst / short best
top-N, dollar-neutral, T+1, 6bps/side, no lookahead) on the 290-name twelve_big
panel **profits strongly in the flagship's loss episodes** and is a genuine
diversifier (corr +0.089):

| sleeve (k5_n30) | full SR | 2018 Q4 | 2020 COVID | 2011 | 2022-24 |
|------------------|---------|---------|-----------|------|---------|
| raw              | +0.34   | +23% (1.7) | **+32% (2.6)** | +4% | +8% |
| + counter-cyclical VIX 1.5/1.2x | +0.40 | +23% | **+49%** | +6% | +17% |
| + counter-cyclical VIX 2/1.4x   | +0.43 | +23% | **+66%** | +7% | +26% |

## The one design rule that matters: sizing is COUNTER-cyclical, not vol-scaled

Standard Moreira-Muir inverse-vol scaling **DESTROYS** the crash alpha (2020
+32% -> -5.6%; SR 0.34 -> 0.13) because it cuts exposure in the crash where
reversal earns its money. The correct sizing raises leverage as VIX rises
(counter-cyclical): mean-reversion alpha scales with crush volatility.

## Deployment constraints (honest)

- **NOT a standalone high-Sharpe engine** (full SR only +0.34-0.43; MaxDD
  -45 to -61%). It is a **crash-insurance overlay**, not a core book.
- Deploy only as a **small, VIX-gated overlay on the flagship** (e.g. 15-30%
  weight when VIX>25/32), with a **hard gross cap** (~1.5x) to bound its
  outside-crash tails.
- Blended into flagship (15% rev / 85% flag): turns 2020 COVID from -2% to
  +8-12%; 2022-24 from -1.6% to +4-7%. Net full-window SR ~neutral (1.03-1.07
  vs 1.04) — its value is crash insurance, not added alpha.
- Helps robustly in explosive high-VIX crashes (2020) + long 2022-24 bleed;
  2011 and 2018 Q4 are less reliable.

## Caveats

- k/n/cap/quantile choices mildly in-sample; the no-lookahead VIX gate is the
  deployable form. No signal-scramble validation yet (watch, not validated).
- Universe is twelve_big 290-name free panel; liquidity/borrow on the short
  side not fully modeled beyond 12 bps RT cost.

## Artifacts
- `meanrev_episode_research.py` -> `results/meanrev_episode_research.json` (grid)
- `meanrev_volmanaged.py` -> `results/meanrev_volmanaged.json` (negative R2)
- Finding chain logged in `RESEARCH_LOG.md`
