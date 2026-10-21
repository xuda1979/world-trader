> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
> **[ITER21 SUPERSEDE BANNER — 2026-09-18]** The champion of record is now the ITER21
> gear-1.0 book: the SAME committed weights as ITER20 (shrink 0.70 + brwt-cap 0.30, weights
> sha16 d2d11c92a98683df) at canonical gross 1.0 — the margin term (4.5%/yr on gross-1)
> makes net SR strictly decreasing above gear 1, so the SR argmax under the operator's
> gross<=1.6 cap is the de-gear: **ann 23.61% / SR 3.751429 / MDD -3.61% / 0 neg years /
> gross 1.0 exact** (sha16 8559fa55ee9a3417). Objective unchanged: Sharpe-max s.t.
> ann>=20% and gross<=1.6. The prior ITER20 gear-1.6 vintage (36.41% / SR 3.4551, sha16
> 766fc0ce9926d793) is archived byte-exact as
> archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily_SUPERSEDED_by_ITER21_gear10.csv and
> stays reproducible via build(gear=1.6). Every earlier headline quoted below (36.41,
> 39.50, 38.11, 37.49, 37.195, ...) is SUPERSEDED history kept for provenance — it WAS
> current once, it is not current now. See campaign/GOAL100_ITER21_ADOPTION.md.
>
> **[ITER20 SUPERSEDE BANNER — 2026-09-18]** The champion of record is now the ITER20
> SR-max book: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv — ann 36.41% / SR 3.4551 /
> MDD -5.93% / 0 neg years / gross 1.6 exact (sha16 766fc0ce9926d793). Operator objective
> 2026-09-18: Sharpe-max subject to ann>=20% and gross<=1.6; the prior ann-max vintage
> (39.50 / 3.2176, ITER19) is archived byte-exact as archive_*_SUPERSEDED_by_ITER20_srmax.csv.
> Every earlier headline quoted in this document (39.50, 38.11, 37.49, 37.195, 40.84,
> 55.5, 62.4, ...) is SUPERSEDED history kept for provenance — it WAS current once, it is
> not current now.

# REALISTIC COSTS FOR A SMALL INTERACTIVE-BROKERS CLIENT + CHAMPION RE-BACKTEST
**Date:** 2026-09-17 | **Goal:** research the realistic trading/execution cost and the realistic
call (margin/borrow) rate for a small IBKR-style retail client, then re-backtest the champion.

---

## 1. Researched realistic parameters

### 1a. Call / margin rate (the dominant lever)
The champion's margin assumption is a single constant **RATE = 4.5%/yr** over the whole 2008-2026
backtest. Reality: IBKR Pro uses a **tiered USD borrow schedule** benchmarked to **SOFR**:
| tier (borrowed) | IBKR margin over SOFR |
|---|---|
| $0 - $100k | +1.50% |
| $100k - $1M | +1.00% |
| $1M - $3M | +0.50% |
| $3M - $200M | +0.25% |

A **small client** (borrowing ~0.6x of a ~$100k-$1M book, i.e. $60k-$600k) straddles the first two
tiers -> blended **~SOFR + 1.0-1.5%**. Current **SOFR = 3.65%** and Fed Funds (DFF) = 3.63%
(read from disk 2026-09) -> the **current realistic small-client call rate ≈ 4.7-5.1%/yr**.
We model it as **benchmark (Fed-Funds pre-2018, SOFR from 2018) + 1.25%** blended, producing a
realistic **time-consistent historical path** (no flat-4.5% assumption):
- Realized **mean margin drag = 1.61%/yr** (not the assumed 2.70%): the book's biggest years
  (2020 +169%, 2016 +64%, 2013-15) were all low-rate, so margin was nearly free exactly when it
  compounded most; margin only rose to ~3.9-4.0pp/yr in 2023-24 (still positive years).
- Current (2026-09) path value ≈ **4.9%/yr**.

### 1b. Execution / trading cost
Champion uses **BPS = 6.4 one-side** on full |dW| turnover (a conservative standard, no half-turn).
For a small IBKR retail client trading energy futures (the champion's dominant block), commission
is ~$0.85-$2.10/contract + fees on notional of $30k-$90k/contract -> **~1-3bps each way**; market
impact is negligible for small size. **6.4bps one-side is therefore conservative (2x-6x the
realistic footprint)** and is kept as a prudent buffer.

---

## 2. Re-backtest results (champion, fixed 1.6x gross, full |dW| costs)

### Base (current single constant RATE=4.5%)
ann **39.50%** | SR **3.22** | MaxDD **-6.52%** | 0 neg yrs

### Conservative CONSTANT-rate stress grid
| call rate | ann | SR | MaxDD | neg yrs | Δann vs 4.5% |
|---|---|---|---|---|---|
| 4.50% | 39.50% | 3.218 | -6.52% | 0 | 0 |
| **4.75% (current realistic)** | **39.29%** | **3.203** | **-6.53%** | **0** | -0.21 |
| 5.00% | 39.08% | 3.189 | -6.53% | 0 | -0.42 |
| 5.50% | 38.67% | 3.161 | -6.53% | 0 | -0.83 |
| 6.00% (2023 peak, flat) | 38.25% | 3.132 | -6.54% | 0 | -1.25 |
| 7.00% (harsh stress) | 37.43% | 3.075 | -6.55% | 0 | -2.07 |

Even at a punishing flat **7% call rate**, the champion keeps **37.4% ann, SR 3.08, ZERO negative
years, MaxDD -6.55%**. There is ample margin of safety.

### Realistic TIME-VARYING path (FF/SOFR + 1.25%)
ann **41.03%** | SR **3.32** | MaxDD **-6.51%** | **0 neg yrs**
-> **BETTER than the flat 4.5% assumption** (realism of rate timing is favorable: low rate in the
dominant high-return years, higher rate only in the still-positive 2023-24).

---

## 3. Conclusion / recommendation
- The **realistic small-client call rate** is ~**SOFR/Fed-Funds + 1.0-1.5%** (≈4.7-5.1% today), best
  modeled as a **time-consistent path**, not a flat constant. Current 4.5% is a reasonable single
  constant, but slightly conservative on average and inexact on timing.
- The champion is **highly robust to realistic cost assumptions**: under the realistic path it
  actually shows **41.03%/SR 3.32**, and survives even a flat 7% call rate with zero negative years.
- **Execution cost 6.4bps one-side is conservative** for small retail futures and does not need
  raising.
- **Recommended deployment parameter:** the realistic margin schedule (§1a) should replace the
  flat 4.5% in any forward replication/live P&L projection for a small client; the headline
  performance is *at least* the constant-cost figure and plausibly higher on rate timing.

## Files
- `/tmp/realistic_call_rate_path.csv` - the FF/SOFR+1.25% time path used.
- This memo. Champion builder unchanged (RATE stays 4.5% for the committed-of-record book).
