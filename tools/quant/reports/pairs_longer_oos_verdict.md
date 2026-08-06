# Pair Portfolio — Long-OOS Truth Test: the 6.96 does NOT survive

**Date:** 2026-08-06  |  **Cost:** 3.8 bps RT  |  **Drivers:** v5 Kalman mean-reversion, z=2.0

## Headline
The static 60/40 walk-forward OOS net Sharpe of **6.96** does **not** reproduce
under a longer, more honest out-of-sample test. When pairs must **re-qualify over
time** (rolling walk-forward, ~309 traded days all out-of-sample), the real net
Sharpe collapses to **~0.3** — statistically indistinguishable from a lag-scramble
control (z ≈ 0.4). **The 6.96 was a fixed-selection artifact.**

## Why the static 6.96 was misleading
- Data tier only holds **~509 bars/pair (2024-07 → 2026-08)**.
- The static book qualifies 11 pairs **once** on the first 60% (≈305 bars) and
  tests only the fixed last 40% (204 days). Pairs are never re-tested.
- A single favorable 10-month window + survivor selection (keep any pair whose
  one-shot IS looks good) inflates OOS Sharpe by ~20x.

## The longer OOS test (rolling walk-forward)
Pairs re-qualify on a trailing IS window every `step` bars and trade forward, so
**every traded day is OOS relative to its own qualification**.

| IS | step | traded days | real net Sharpe | scramble (n=5) | z |
|----|------|------------|-----------------|----------------|-----|
| 150 | 30 | 359 | 0.023 | 0.057 (±0.27) | -0.1 |
| 200 | 50 | 309 | 0.287 | -0.048 (±0.08) | +4.1* |
| 200 | 100 | 309 | 0.288 | 0.427 (±0.76) | -0.2 |
| 250 | 50 | 259 | 0.12 | -0.044 (±0.09) | +1.9 |
| 250 | 30 | 259 | -0.024 | -0.053 (±0.02) | +1.4 |

\* The IS=200/step=50 row looked promising with 5 scramble seeds. It was re-tested
with **14 scramble seeds** (focused run):

```
STATIC WF: OOS net Sharpe = 6.96   (204 OOS days)
ROLLING IS=200 step=50:
  real net Sharpe      = 0.29
  scramble (n=14)      = 0.14 ± 0.33  (max 0.92)
  real z vs scramble   = 0.43          <- NOT significant
```
With a proper control size the "promising" config is **z=0.43** — pure noise.

## Verdict
| Question | Answer |
|----------|--------|
| Is the 6.96 arithmetically reproducible? | Yes — exact, no bug. |
| Is it free of lookahead in the static sim? | Yes — trailing-window entry, IS-only fit. |
| Does it survive longer/more-honest OOS? | **No — collapses to ~0.3, z≈0.4 vs scramble.** |
| Is the pair MR edge (real, persistent) above noise? | **No.** |

The 6.96 is real *as computed* but is **not a tradeable, persistent edge**. Under
rolling re-qualification the geometric-mean-reversion alpha on these pairs is
statistically indistinguishable from noise at 3.8bps. 

## Action
- **Do NOT size capital on the static 6.96.**
- The deployment spec's "optimistic upper bound 3.5-5.5" must be revised to
  **~0.3 (noise)**.
- The likely genuine unlock remains **longer data history** (paid tier) — the
  2-year window is too short to separate this weak MR edge from selection noise.
- Prefer the **scramble-validated L/S model champion** over this pair book.

## Artifacts
- `tools/quant/pairs_rolling_oos.py` — rolling-OOS truth test w/ scramble
- `tools/quant/reports/pairs_rolling_oos.json` — full config results
- `tools/quant/reports/pairs_sharpe_verified.md` — the (now-superseded) static audit
