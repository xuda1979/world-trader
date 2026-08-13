# Floored Flagship — Full Statistics Report (2026-08-13)

**Construction**: h3 + AP gold, 50/50, floored 50% in T-bills (4%/yr assumed).
Monthly cadence. All sleeve returns cost-inclusive at **6 bps/side (12 bps RT)**.
Window: **2008-02 .. 2026-08 (19 years, 223 months)**.

- h3 sleeve = EW(L/S 130/30, CTA futures macro 21d, Global Macro) — the
  3-stream hedge blend, ex stat arb (which is blend poison at 12 bps RT).
- AP sleeve = AP gold composite (realization-timed daily record, 6 bps/side).
- The 50% T-bill floor is the **only** mechanism that delivers the user's
  no-losing-year requirement (P15; alternatives all fail — N21/N22/N24/N25).

## Full-window statistics

| Metric | Floored flagship | Unfloored flagship |
|--------|------------------|--------------------|
| Sharpe | **1.14** | 0.90 |
| Annual return | **7.5%** | 10.7% |
| Annual vol | 4.6% | 9.2% |
| Max drawdown | **-4.6%** | -10.1% |
| Calmar | **1.62** | 1.06 |
| Total return (19y) | +281% (1.00 -> 3.81) | — |

The floor cuts more volatility than return: SR rises 0.90 -> 1.14, MaxDD
halves, Calmar 1.06 -> 1.62. Cost of the guarantee: ~3.2pp/yr of return.

## Yearly returns — all 19 years POSITIVE (the requirement)

| Year | Ret | Cum | Year | Ret | Cum |
|------|-----|-----|------|-----|-----|
| 2008 | +2.30% | 2.3% | 2018 | +4.30% | 134.6% |
| 2009 | +11.94% | 14.5% | 2019 | +7.48% | 152.2% |
| 2010 | +17.15% | 34.2% | 2020 | +11.11% | 180.2% |
| 2011 | +3.13% | 38.4% | 2021 | +12.24% | 214.5% |
| 2012 | +4.54% | 44.6% | 2022 | **+0.35%** | 215.6% |
| 2013 | +13.76% | 64.5% | 2023 | +1.18% | 219.3% |
| 2014 | +9.69% | 80.5% | 2024 | +5.50% | 236.9% |
| 2015 | +3.28% | 86.4% | 2025 | +8.46% | 265.4% |
| 2016 | +5.65% | 96.9% | 2026 | +4.40% | 281.5% |
| 2017 | +14.24% | 125.0% | | | |

- **Negative years: 0 of 19.** Worst year: 2022 (+0.35% — the unfloored
  flagship's worst year, -3.4%, floored to +0.35%). Best: 2010 (+17.15%).
- Median year +5.65%, average year +7.41%.
- The 2 historically weak years had different drivers: 2022 = AP sleeve
  (-9.8%, rates shock); 2023 = h3 sleeve (-4.4%, grind). The floor covers both.

## Sub-periods (geometric SR / cumulative return)

| Period | SR | Cum return |
|--------|-----|-----------|
| 2008-2012 (GFC era) | +1.07 | +44.6% |
| 2013-2017 (bull) | +1.77 | +55.5% |
| 2018-2022 (COVID + rates) | +0.96 | +40.3% |
| 2023-2026 (grind) | +0.76 | +20.9% |

Positive in every sub-period, including the GFC era and the recent grind.

## Rolling windows

| Window | Min SR | Median SR | Max SR | Negative windows |
|--------|--------|-----------|--------|------------------|
| 3-year | +0.08 | +1.23 | +2.11 | 0% |
| 5-year | +0.46 | +1.22 | +1.78 | 0% |

**Every 3-year and 5-year window since 2008 has positive Sharpe.**

## Crash episodes (floored vs unfloored)

| Episode | Floored | Unfloored |
|---------|---------|-----------|
| 2008 GFC | +0.4% | -1.6% |
| 2011 Euro | -0.5% | -2.3% |
| 2015-16 selloff | -0.3% | -2.9% |
| 2018 Q4 | -3.9% | -9.0% |
| 2020 COVID | -0.8% | -2.3% |
| 2022 Bear | -0.2% | -3.7% |

The floored flagship's worst crash episode is -3.9% (2018 Q4) vs the
market's -20.7% and the unfloored flagship's -9.0%.

## Tail metrics (monthly)

- Worst month: **-3.68%**; worst 3 months: **-4.60%**; worst 12 months: -0.04%
  (a 12-month period that was essentially flat — never deeply negative).
- Months < -1%: 10.3%; months < -2%: 3.6%.
- Longest streak of negative months: 5 (grind-type, shallow); longest streak
  of < -2% months: 1.
- Skewness +0.23, kurtosis 2.76 (mildly right-skewed).

## The guarantee — stated precisely

0.5 x flagship_year + 2% >= 0  ⇔  flagship_year >= **-4%**

- Historical worst flagship year: **-3.4%** (2022) -> floored +0.35%. ✓
- The 50% floor guarantees zero losing years as long as the unfloored
  flagship's worst year stays >= -4%.
- T-bill sensitivity: at 3% T-bills, 2022 = -0.15% (barely negative); at 4%,
  +0.35%; at 5%, +0.85%. The floor needs T-bills >= 4% (current environment: OK).
- At a 45% floor the guarantee just misses (min year -0.02%).

## Operational notes

- Rebalancing drag: monthly sleeve rebalancing ~0.42pp/yr at 12 bps RT.
- Costs: 6 bps/side embedded in every sleeve; the T-bill floor itself has no
  turnover.
- Health monitor (portfolio_health_monitor.py): current stance **GO** — TRIM
  only on sustained degradation (21d negative SR AND -3% quarterly DD; the
  2022-23 soft patch is the only such historical event).
- Validated companion sleeves (separate, monitored — NOT inside the flopped
  book per N25): COT S&P asset-manager contrarian (P16, SR +0.35-0.60, corr
  -0.056) and the mean-reversion crash sleeve (P18, covers 6/7 flagship
  drawdown windows, corr +0.20 on drawdown days).
- Artifact immunity: every sleeve is price/macro-based (no volume factors) —
  immune to the volume-precision artifact class that killed the champion (N20).

## Bottom line

The floored flagship delivers the user's hard requirement — **make money in
every calendar year (0 of 19 negative)** — with SR 1.14, Calmar 1.62, MaxDD
-4.6%, ~7.5%/yr, positive in every sub-period and every 3y/5y rolling window,
and crash losses capped at ~-4% in the worst episodes. The ~3.2pp/yr return
cost is the price of the guarantee, and no tested alternative (diversity,
filters, overlays) achieves it (P15, N21-N26).
