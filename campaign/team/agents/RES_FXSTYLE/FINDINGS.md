# RES_FXSTYLE FINDINGS — cross-sectional FX momentum on the NEW 508-pair fx_hist
> Chartered to build a broad cross-sectional FX carry/momentum engine decorrelated to the
> equity-momentum champion. Honest verdict below: **REJECT (weak, fails all gates).**

## Data used (this session, verified)
- tools/quant/data/fx_hist/: 554 pairs, USD crosses + majors span 1999-01..2026-09 (7,087 daily).
- 28 major/widely-traded crosses selected for a clean basket (USD_JPY, EUR_USD, GBP_USD, AUD_USD,
  NZD_USD, USD_CAD, USD_CHF, USD_SEK, USD_NOK, USD_CNY, USD_HKD, USD_SGD, USD_KRW, USD_THB,
  USD_INR, USD_ZAR, USD_BRL, USD_MXN, USD_DKK, EUR_JPY, EUR_GBP, EUR_CHF, AUD_JPY, GBP_JPY,
  USD_HUF, USD_PLN, USD_CZK, USD_TRY). Each file is (date, close) daily.

## Survived algorithm (fx_mom_engine.py + fx_grid.py, both in this dir)
- Cross-sectional FX momentum: factor_i(t) = ret_i(t, lb, skip) over [t-lb, t-skip], rank
  cross-sectionally each day, long top-n / short bottom-n (dollar-neutral, equal-weight),
  positions T+1 (shift 1), rebalanced every `hold` days, gross exactly long+short per day.
- Grid: lb in {126, 189, 252}, skip=21, (nlong,nshort) in {(3,3),(4,4),(5,5),(3,5)}, hold in {10,21}.

## Results (honest, computed this session)
| lb | nl/ns | hold | ann | SR | MDD | negYrs |
|----|-------|------|-----|-----|-----|--------|
| 189 | 4/4 | 10 | +5.40% | 0.419 | -44.8% | 8 |
| 252 | 3/5 | 21 | +5.28% | 0.402 | -55.5% | 10 |
| 252 | 3/3 | 21 | +5.16% | 0.379 | -62.3% | 10 |
| 126 | 4/4 | 10 | +3.88% | 0.329 | -26.7% | 9 |
- Best SR across the ENTIRE grid = 0.419 << the SR>=1.0 champion-eligibility floor.
- Every cell has huge drawdowns (-25%..-64%): the 28 USD-cross basket is dollar-correlated;
  vol-scaled long-short FX books get run over in 2008/2020 dislocations. Cancer.

## Verdict
**REJECT.** Broad cross-sectional FX momentum on the new fx_hist data does not clear SR>=1.0
(peak 0.42), has 8-10 negative years, and destroys capital under honest drawdown accounting.
This is consistent with the FX-literature reality: cross-sectional FX momentum edges are modest
and era-dependent; the champion's existing FX z-rev sleeve (CFX4, 0 weight) is the stronger FX
expression. NOTE: fx_hist is still a NEW and useful dataset — it just does not contain a
standalone SR>=1.0 decorrelated engine of its own (confirmed dead on this family).

## Delivered
- fx_mom_engine.py (single-basket constructor), fx_grid.py (honest grid, no cherry-picking).
- No sleeve emitted (REJECT-with-numbers, per charter).

RES_FXSTYLE DONE
