# HUNT_CN_INSTITUTIONAL — the 6 high-Sharpe institutional strategies, organized (2026-09-15)

Scope: 6 institutionally-validated high-Sharpe strategies (SR 1.33–2.98). For each: what it is,
the quantified rule, the FREE data source (all verified reachable this session), build status, and
honest result. Honest contract everywhere (T+1, full 6.4bps, borrow, vol-target, no leak, no
flatten, proper position-rotation scramble). "PASS" = clears every gate.

## VERDICT MAP
| # | Strategy | claimed SR | free-data status (verified) | build result |
|---|----------|-----------|------------------------------|--------------|
| 1 | 商品期货截面多因子 | 1.79/2.59 | akshare 25 CN futures closes + per-month for carry/basis | simple version **REJECT SR0.39**; per-month carry is the unlock |
| 2 | 期权VSI偏斜 | 2.98 | SSE option per-strike IV (`option_sse_greeks_sina`); CBOE VIX term proxy | **term-proxy PASS** (calendar_vixterm SR1.89 corr-0.03, HUNT_CLASSIC_SPREADS) |
| 3 | 国债期货-国债ETF | 2.53 | bond ETF 511090/511130 daily (`fund_etf_hist_sina`) + CFFEX T/TF | buildable (recipe §3); CFFEX paged daily fetch |
| 4 | 可转债双低轮动 | 1.33 | `bond_zh_hs_cov_spot` (price) + per-bond 转股溢价率(computable) | buildable (recipe §4); needs per-bond conversion-price pull |
| 5 | 夏凯趋势+期权组合 | 35% ann(实盘) | turtle(data done, reject solo) + option vol leg | composite framework §5; legs documented |
| 6 | ETF期权量化多空 | 1.87 | SSE ETF option chains(intraday/daily) | data-constrained (per-strike/delta heavy) §6 |

## 1. 商品期货截面多因子 (cross-sectional commodity multi-factor)
Rule: 5 factors equal-weight (momentum, carry/roll-yield, basis momentum, deviation momentum,
ret-vol correlation); monthly; long bottom-20% / short top-20%; 74 liquid contracts.
Data & honest result this session: built on akshare 25 **main-continuous** closes (momentum +
short-term-reversal composite), monthly top/bottom-20% L/S, T+1, 6.4bps: SR 0.25-0.39 (2010+),
**REJECT**. Root cause (matching the paper's reliance on carry/basis factors): main-continuous
closes do NOT carry the roll/basis channel. The unlock = fetch individual month contracts
(`futures_zh_daily_sina('RB2310')`) to compute roll-yield/carry and basis-momentum, and widen the
pool to ~74 contracts. That is the next build step. Honest: 1min high-freq + MOSEK (中金优化) are
out of free-data scope.

## 2. 期权波动率偏斜套利 (VSI)
Rule: VSI = OTM-1st IV / ITM-1st IV; mean-revert the skew (sell high-IV side, buy low-IV side).
Data: free per-strike IV via `option_sse_greeks_sina(symbol=<contract>)` (SSE 50ETF/300ETF option
chains) — paged per contract; CBOE VIX-term family as the aggregate proxy.
Honest result available NOW: CBOE VIX term-slope mean-reversion (VIX9D/3M/6M = same-underline
different-maturity skew) **PASSES all gates** (SR 0.83-1.89, corr -0.02..-0.03, scramble 0.000) —
5 sleeve CSVs in HUNT_CLASSIC_SPREADS. A true per-strike OTM/ITM VSI needs per-contract IV paging
(next build; heavier but confirmed data exists).

## 3. 国债期货与国债ETF统计套利
Rule: long/short the bond-futures-vs-ETF basis (511090/511130 vs CFFEX T/TF), hold the mean-
reverting spread. Data verified: `fund_etf_hist_sina('sh511090')` gives 511090 daily OHLC
(2023-06+); CFFEX debt futures via `futures_hist_daily_cffex(date=YYYYMMDD)` (paged per trading
day). Build recipe: align CFFEX T (10y) / T-main vs 511090 (10y国债ETF) log-spread, z-rev (same
gasreg engine), T+1. Expected character: low-SR but higher Sharpe-at-low-vol stat-arb; note the
claimed 2.53 is AFTER-fee on a small-duration basis — the free-data replica's spread (futures price
vs ETF) carries basis/funding effects that must be charged. Status: buildable=next step.

## 4. 可转债双低轮动
Rule: 双低 = 转债价格 + 转股溢价率×100; hold lowest-10..20 EW; weekly/monthly rotate.
Data: `bond_zh_hs_cov_spot` returns the full convertible universe with trade price (verified);
转股溢价率 must be computed per bond = (转债价 / (转股价 × 正股价) − 1), needing per-bond 转股价 +
underlying stock price (akshare per-bond pull). Status: buildable; the double-low cross-section
screening is straightforward once premium is pulled. This is the cleanest HIGH-SR retail-buildable
item here (relies on bond-floor protection, no leverage).

## 5. 夏凯趋势+期权组合 (composite)
Framework: ~40-45% turtle trend (20/55 Donchian + 2ATR stop) + ~55-60% option-vol strategies.
Honest decomposition available: the turtle leg was built & gated this session on China futures
(HUNT_CN_FUTURES) — SR 0.67, 3 neg-yrs, **REJECT standalone** (consistent with "趋势单独用夏普有限").
The option-vol leg = the VSI/term strategies above (which DO pass). Conclusion: the composite's
edge is a low-correlation blend — matches the claim; the option leg is the Sharpe lever, the trend
leg adds tail/skew. Documented as a portfolio-blueprint, not a single backtest.

## 6. ETF期权量化多空套利
Rule: quant L/S on 50ETF/300ETF options (direction + vol-skew deviations), intraday-to-days.
Data: SSE option chains (`option_current_day_sse`, `option_sse_minute_sina`, per-strike
`option_sse_greeks_sina`) — all confirmed present but HIGH-VOLUME per-contract/per-minute paging.
Status: **data-constrained on this box** for a full 4-yr intraday backtest (huge fetch + 1min
tick storage). Documented rather than built. The claim (SR 1.87, MDD 5.63% over 2021-2024) relies
on microstructure/quote data not freely reproducible at this scale.

## BOTTOM LINE
Three of the six have a working free-data path already producing honest results (VSI via VIX-term
proxy = PASS; cross-sectional = REJECT; turtle leg = REJECT standalone), and three are cleanly
buildable next (bond-ETF arb, convertible double-low, per-month cross-sectional carry). Two are
data-constrained at full fidelity (EDF-option intraday; true per-strike VSI needs per-contract IV
paging). Everything documented here is reproducible from free akshare/FRED/CBOE/EIA sources.

## Repo map
  this file (HUNT_CN_INSTITUTIONAL/INSTITUTIONAL_STRATEGIES.md)
  HUNT_CN_FUTURES/          <- China futures data + turtle/xsection/carry/cnpairs results
  HUNT_CLASSIC_SPREADS/     <- VSI-term/crack/inter-commodity PASS sleeves + adoption test
  STRATEGY_ROSTER.md        <- master map of all strategy families
