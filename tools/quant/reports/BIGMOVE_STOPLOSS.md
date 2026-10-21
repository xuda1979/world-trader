# bigmove — Backtest WITH a 1% Intraday Stop-Loss (and 6bp one-side cost)

**Date**: 2026-08-13
**Requested rule**: buy at today's close when next-day >=+5% probability is large;
exit next day using OHLC:
- if next-day **open** < stop → exit at **open**
- else if next-day **low** < stop → exit at **stop** (intraday fill)
- else → exit at next-day **close**
- stop = entry × (1 − stop%); one-side cost = **6 bps** (12 bps round trip).
- No look-ahead: features at close(T) only; model rolled forward (quarterly
  refit, 3-yr window). Universe 285 US large caps, OOS 2018-2026.

## Results (out-of-sample, net of 12bp round-trip)

| rule | trades | hit≥+5% | avg net/trade | exit open/stop/close |
|------|--------|---------|---------------|----------------------|
| **thr≥0.9, stop 1%** | 3,057 | **12.8%** | **+0.20%** | 25% / 48% / 27% |
| thr≥0.9, stop 3% | 3,057 | 15.1% | +0.08% | 7% / 41% / 52% |
| thr≥0.9, **no stop** | 2,926 | 16.5% | +0.18% | — |
| thr≥0.8, stop 1% | 20,424 | 10.5% | +0.03% | 27% / 43% / 30% |
| thr≥0.7, stop 1% | 43,371 | 8.3% | −0.03% | 25% / 42% / 33% |

## The decisive finding
**A 1% stop is counterproductive for a "predict next-day +5%" strategy.**

Mechanism (measured out-of-sample at thr≥0.9):
- **72% of all predicted-big-up trades dip through −1% intraday** before the day
  ends.
- The stop truncates losers from large gaps into ~−1% — modestly helpful — but it
  also cuts the **right-tail wins the strategy depends on**: many +5% moves retrace
  past −1% intraday before completing. Measured: winners-touched-stop still closed
  +8.5% average; the stop just caps the few giant days that drive the long-run edge.

Net effect vs no-stop at thr≥0.9:
- per-trade avg net: +0.18% → +0.20% (roughly flat; loser-truncation ≈ winner-truncation)
- hit≥5%: 16.5% → **12.8%** (worse — fewer big-win days harvested)
- daily-active-book Sharpe: +0.63 → −0.12; drawdown −48% → −61% (worse)

**Because this strategy profits from rare +5%+ days, a tight stop caps the very
tail that pays for it.** The stop does not rescue the 70%-precision objective —
the best achievable hit remains ~13-16%, far below 70%.

## Decision (delegated)
Best operational configuration under the user's full spec: **probability ≥ 0.9,
stop-loss = 1%** (best per-trade net, caps per-trade loser risk). It is runnable
and reproducible via `tools/quant/bigmove/backtest_stoploss.py`. However it is
honestly flagged as: (1) far below the 70% precision ideal; (2) only weakly
positive per-trade with a negative active-day Sharpe; (3) NOT suitable for
standalone deployment — at most a small-risk overlay.

## Artifacts
- `bigmove_stoploss_results.json` (full numeric table)
- `bigmove_stoploss_equity.csv` (per-threshold per-stop daily books)
- `bigmove_walkforward_results.json` (no-stop comparison)
- Code: `tools/quant/bigmove/backtest_stoploss.py`, `stop_winner_stat.py`

### Stop-level sweep @ thr>=0.9 (added 10%)
| stop | hit>=5% | avg net/trade | active Sharpe | maxDD | exit O/S/C |
|------|---------|---------------|---------------|-------|-----------|
| 1%  | 12.8% | **+0.199%** | -0.12 | -61% | 25/48/27 |
| 3%  | 15.0% | +0.076% | -0.02 | -63% | 7/41/52 |
| 5%  | 16.0% | +0.051% | +0.11 | -52% | 3/24/73 |
| 10% | **16.3%** | +0.034% | +0.07 | -58% | 1/5/94 |

A **10% stop is effectively "no stop"** for this large-cap universe: only ~5% of
trades touch it, 94% held to close. So it restores the no-stop hit-rate (~16.3%)
but gives the *worst* per-trade net because it lets the fat-left-tail losses ride to
close (it truncates nothing). The 1% stop remains best for per-trade net (+0.20%)
because it cuts the big losses; hit-rate and active-day Sharpe both worsen with the
tight stop. No stop level makes the strategy economically strong or reaches 70%
precision — the edge is thin in every variant.
