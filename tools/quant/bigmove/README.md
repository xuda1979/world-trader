# bigmove — Next-Day Huge-Return Prediction & Trading

## Objective
Predict the probability that a stock's **next-day return** satisfies
`next_close / today_close - 1 >= +5%` (user's return definition), computed
only from information available at today's close (no look-ahead). Trade LONG
when the predicted probability is high (target >= 70%) and exit at tomorrow's
close.

## Files
| file | purpose |
|------|---------|
| `data_panel.py`        | load panel + base-rate stats for next-day big moves |
| `features.py`          | base technical features (momentum, vol, RSI, range, vol-ratio, ...) |
| `features2.py`         | enhanced: vol-normalized + market-relative + stock risk features |
| `explore_signal.py`    | one-time-split signal check (train/val/test) — is there any signal? |
| `explore_signal2.py`   | same with enhanced features + calibration check |
| `backtest_walkforward.py` | HONEST rolling walk-forward backtest (quarterly refit, 3y window) |
| `multi_target_diag.py` | precision ceiling across target definitions (>=3%, >=5%, abs, short) |
| `pipeline_common.py`   | panel/OHLCV loader |

## Data & Methodology
- **Universe**: 285 US large-cap common stocks from `twelve_big` daily panel,
  excluding ETFs + foreign ADRs (QQQ, SPY, XLF, ASML, HMC, TM). ~2006–2026.
- **Target**: `ret_next[T] = close[T+1]/close[T] - 1`; positive if >= +5%.
- **Features** (49, all causal w.r.t. close[T]): multi-horizon momentum,
  realized vol, scaled-momentum, RSI, distance-to-MA, intraday range & close
  position, overnight gap, log-volume & volume ratios, per-stock normalized
  moves, market-relative moves, historical stock big-move frequency, etc.
- **Model**: `HistGradientBoostingClassifier`, class-weighted for the rare
  positive class, calibrated-prone raw probabilities.
- **Honesty**: rolling walk-forward — model retrained quarterly on a 3-year
  window of data strictly before each prediction window. NO look-ahead.

## Headline Finding (out-of-sample 2018–2026, daily-close technical data)
> **70% confidence on next-day >=5% moves is NOT achievable from daily
> OHLCV technical features.** A single-day >=5% move in a large cap is almost
> always an idiosyncratic news event (earnings, guidance, macro shock) that is
> fundamentally unpredictable from price/volume history.

Achievable **precision** (fraction of fired trades that actually hit the target):

| target | pred>=0.7 | pred>=0.9 |
|--------|-----------|-----------|
| next-day >= +5% (long) | ~10.3% | ~16.4% |
| next-day >= +3% (long) | ~18.6% | ~27.8% |
| \|next-day\| >= 5% (long/short) | ~18.7% | ~30.1% |
| next-day <= -5% (short) | ~7.7% | ~8.6% |

Base rate for next-day >=+5%: **~1.6%**. The model lifts precision ~10–18x, a
real and statistically significant edge (OOS ROC-AUC ~0.82), but it cannot
concentrate certainty to 70%.

## Why it's still not a "70% strategy"
A >=5% single-day move is dominated by unobservable-to-daily-bars information.
To reach ~70% hit you would need materially richer data that reveals *when*
news is coming and *what* it will say:
earnings calendars & consensus, analyst revisions, news/NLP sentiment, options
flow, level-2 order flow, and event-likelihood features. None of those exist in
an OHLCV-only panel.

## Practical framing (if pursued anyway)
Even below 70% precision the payoff is **asymmetric**: losing trades are small
(median next-day move ~0%), winning trades are +5%+. Using threshold >= 0.9 on
the >=5% target produced an avg +0.18% net/trade and ~0.63 daily-EW Sharpe in
the no-look-ahead walk-forward, but with heavy concentration (~3.4 signals/day),
high vol and deep drawdowns — NOT suitable for standalone deployment. Deploying
on this alone is not recommended.

## Stop-Loss variant (backtested 2026-08-13)

Per user spec, re-ran with a **1% intraday stop-loss** and 6bp one-side cost
(12bp round trip): buy at close(T), exit next day at open (if gap below stop),
else at stop (if low < stop), else at next close. No look-ahead walk-forward,
OOS 2018-2026.

**@ probability>=0.9** (best config):
| variant | hit≥5% | avg net/trade | active-day Sharpe | maxDD |
|---------|--------|---------------|-------------------|-------|
| no stop | 16.5% | +0.18% | +0.63 | −48% |
| **stop 1%** | 12.8% | +0.20% | −0.12 | −61% |
| stop 3% | 15.1% | +0.08% | −0.02 | −63% |

**Decision/verdict**: The 1% stop does NOT help this strategy. It caps per-trade
loser risk (net/trade ~flat) but truncates the right-tail +5% wins the edge
depends on (72% of predicted-big-up trades dip <−1% intraday). hit-rate and
active-day Sharpe worsen. Chosen operational rule = probability>=0.9 + 1% stop
(best per-trade net, runnable via `backtest_stoploss.py`), but it remains far
below the 70% precision ideal and is NOT standalone-deployable.
