# Research plan: high net returns with no leverage and limited trading

**Date:** 2026-11-03

**Status:** proposed research protocol; no new strategy performance has been measured.

**Repository reviewed:** `ed7848dbbfd4647ac5f59f913830c51e6cc5e9c0`.

**Scope:** free public data, long-only cash-funded investments, realistic retail execution.

## 1. Research objective and recommended starting point

Build a portfolio that earns high **net compound returns** while controlling excess-return
Sharpe, daily drawdown, and executed turnover. These objectives compete: holding more cash can
reduce drawdown but reduce return; a fast signal can predict well yet lose money after costs.
The research must identify a defensible trade-off, not optimize each headline on a different run.

Start with a small portfolio of liquid, US-listed, unlevered ETFs providing global equity,
Treasury, inflation-linked bond, and physically backed gold exposures. Develop slower signals
and an explicit decision to **hold the existing position** when a trade's estimated benefit
does not cover uncertainty and execution costs. Add individual equities only after historical
security identities, corporate actions, and delistings can be reconstructed using free sources.

The central research question is:

> Can a controller that jointly accounts for signal persistence, uncertainty in public data,
> and the retail cost of changing a position improve the return–drawdown–turnover frontier over
> simple, equally funded allocation rules?

Proposed contributions are hypotheses, not established inventions. Section 5 distinguishes
them from known methods and specifies experiments that can disprove their value. A successful
ingestion test, a synthetic simulator test, and a profitable historical strategy are different
types of evidence; none substitutes for the others.

### Targets to freeze before experiments

Use USD 100,000 initial NAV as the reference research account, with separate USD 10,000,
25,000, and 1,000,000 evaluations. These are scenarios, not assumptions about the user's balance.
All figures below refer to the **same chronological evaluation path**, after implementation
costs and before investor-specific taxes. Annual return means CAGR over the evaluation interval,
not a promise to earn that return in every calendar year.

| Metric | Minimum research acceptance gate | Primary design target | Stretch hypothesis |
|---|---:|---:|---:|
| Net nominal CAGR | ≥10% | 12–15% | ≥15% |
| Annualized daily excess-return Sharpe | ≥1.00 | 1.25–1.50 | ≥1.75 |
| Daily maximum drawdown magnitude | ≤15% | ≤12% | ≤10% |
| Annualized half-turn turnover, defined in §6 | ≤100% | 50–100% | ≤75% |
| Maximum rolling 252-session half-turn turnover | ≤150% | ≤100% | ≤100% |
| Gross exposure at instrument level | ≤100% always | Same | Same |
| Borrowing, short positions, embedded leveraged products | Zero | Zero | Zero |

These are ambitious decision thresholds, **not forecasts or achieved results**. Report the whole
Pareto frontier and a failed verdict if no candidate passes. Do not lower thresholds after
examining evaluation returns. A high Sharpe achieved mainly by cash does not pass the CAGR gate;
a high CAGR from concentrated equity beta does not pass the risk and comparison gates in §8.
No minimum return for every year, hard drawdown guarantee, or universal market-regime guarantee
is claimed. Gap losses can exceed any risk-control threshold.

Metric contract: with a no-external-flow daily marked NAV path `N_t`, use
`r_t = N_t / N_(t−1) − 1`, `CAGR = (N_end / N_start)^(1 / elapsed_years) − 1`,
and `MaxDD = max_t(1 − N_t / max_(s≤t) N_s)`. Elapsed years use actual calendar
days/365.25; initial NAV and terminal liquidation are included. The ordinary Sharpe is
`sqrt(252) * mean(r_t − rf_t) / sample_std(r_t − rf_t)`, with an aligned, correctly
converted daily Treasury reference `rf_t`; report zero-variance Sharpe as undefined, never
infinite. “Positive excess CAGR” means the portfolio's compound growth rate exceeds the
compound growth rate of that reference over identical dates. Broker cash earnings belong
in portfolio NAV and may differ from `rf_t`. Also report real CAGR using a public inflation
series as an ex-post diagnostic, without feeding revised inflation back into decisions.

## 2. What exists and what must change

The current README describes a dependency-free ingestion package. The repository also contains
substantial earlier strategy research. Neither its old operating settings nor its historical
headlines are automatically admissible under this protocol.

| Existing component | Useful foundation | Required work for this study |
|---|---|---|
| [`world_trader/models.py`](../world_trader/models.py), [`store.py`](../world_trader/store.py) | Separate observation, publication, availability, collection clocks; revision-aware `asof` export | Add source/feature manifests and security-identity history; retain the prohibition on backdating current snapshots |
| [`sources/sec.py`](../world_trader/sources/sec.py), [`sources/macro.py`](../world_trader/sources/macro.py) | Filing metadata, current XBRL aggregates, explicit FRED vintages | Parse accession-specific original disclosures and successive vintages before claiming historical financial features |
| [`docs/data-sources.md`](data-sources.md), [`docs/validation.md`](validation.md) | Document access and distinguish fixture tests from real API requests | Add an entitled free price feed, action coverage, and reproducible coverage audits |
| [`campaign/bt/engine.py`](../campaign/bt/engine.py) | Lagging, full traded-weight cost convention, exposure utilities | New cash/share/settlement accounting; current defaults allow 1.6x exposure and volatility scaling above 1x; weight differences alone do not establish executed turnover |
| [`tools/quant/backtest.py`](../tools/quant/backtest.py) | Trade records and analytics | Audit overlapping holdings, event timing, and cash conservation before reuse; do not assume per-trade equity aggregation is a simultaneous portfolio ledger |
| [`alphaportfolio_replication/run_walkforward_realcost.py`](../alphaportfolio_replication/run_walkforward_realcost.py) | Prior chronological-model and financing experiments | Audit block cutoffs, drift, and cost units; it constructs long/short weights and applies a half-turn convention, so its results are not this plan's baseline |
| [`campaign/TRADE_RECORD_STANDARD.md`](../campaign/TRADE_RECORD_STANDARD.md) | Ledger reconciliation requirement and documented historical audit findings | Require executable instruments and actual price observations; synthetic index fills cannot establish investability; replace ambiguous `t−1 close` execution with explicit decision/order/fill clocks |
| [`SYSTEM_PORTFOLIO.md`](../SYSTEM_PORTFOLIO.md), [`campaign/CHAMPION_CARD.md`](../campaign/CHAMPION_CARD.md) | Historical hypotheses, failed alternatives, and provenance lessons | Keep as historical records; inspect underlying instruments, not just sleeve weights or a reported 1.0x scalar, before admitting any strategy |

The champion card documents superseded same-day and cost-accounting results. Preserve those
audit lessons and do not repeat older numbers as newly verified performance. A positive weight
on an internally short, leveraged, synthetic, or futures-based sleeve is not a long-only cash
investment. A later card's reported 1.0x exposure does not settle that question by itself.

**This change is a research plan, not a strategy implementation or a deployment instruction.**
The existing collectors, historical artifacts, and trading settings are not changed by it.

## 3. Investment and data contract

### 3.1 No leverage means no hidden leverage

At every fill and mark, enforce nonnegative shares and nonnegative funded cash. With NAV `N`,
instrument weights `w`, free cash `c`, and separately reconciled settlement receivables/payables,
the balance sheet must sum to NAV; risky security market value cannot exceed NAV. Reserve cash
for fees and price movement before sending buys. Buying power is not the broker's margin limit.

- No margin borrowing, shorts, options, futures, CFDs, leveraged/inverse ETFs, or derivative
  overlays. The initial product whitelist also excludes futures-based commodity funds and
  structured notes; gold exposure must be physically backed and unlevered.
- Ordinary equities, plain unlevered equity/bond ETFs, and an approved short Treasury ETF are
  eligible. Examine fund mandate and underlying exposure; a cash-funded wrapper can still
  contain embedded leverage. “No leverage” here concerns portfolio/product financing, not a
  claim that operating companies have no corporate debt.
- Initial caps: 35% per non-cash ETF, 60% aggregate equity, 60% aggregate bond-fund weight
  excluding the short Treasury reserve, 15% gold, 25% per equity sector on available look-through
  evidence. Report effective duration separately in years. A short Treasury reserve
  ETF may reach 100%; it remains a priced security with duration, spread, and distribution risk.
  Individual-equity expansion: 2% per issuer and 20% total satellite allocation.
- Recheck exposure after rounding, costs, partial fills, and price gaps. Reject or resize orders
  that would violate funding limits. Market-driven concentration breaches are logged and reduced
  at the next feasible fill, with the intervening breach duration reported; do not assume an
  instantaneous corrective fill or silently renormalize the return stream afterward.
- Model settlement by trade date and exchange calendar. The initial conservative cash-account
  simulation spends only settled funds; a rotation may require waiting for sales to settle.
  Apply historical settlement regimes when replaying history, including the US T+1 transition
  on 2024-05-28 [R8]. Do not treat this funding convention as the only legally permitted one.

### 3.2 Initial universe and trading frequency

Freeze an economic universe before testing. An illustrative eight-fund candidate list is
`SPY, VEA, VWO, IEF, TLT, TIP, GLD, BIL`; confirm product eligibility, inception, source coverage,
and current terms before freezing actual membership. No ticker is recommended for purchase by
this document. Start each fund only after its true inception and sufficient observed history.
Do not extend an ETF backward using a yield series, spot commodity, or future index return.

Reconsider allocation monthly; check risk and data quality daily. Ordinary holding horizons are
roughly 1–6 months. A limited risk-triggered rebalance is allowed only through the same cost,
funding, and turnover ledger. Select liquid instruments using trailing observations; never use
future average volume to qualify a historical order. Current-survivor ETF selection still has
selection bias: label retrospective tests as conditional on that universe, include historical
closures where free evidence permits, and require prospective evaluation.

Begin with the shorter history that can actually be verified. A 2016-onward free feed cannot
support a measured 2008 crash result. Earlier public indexes may supply **scenario context**;
they cannot be spliced into the strategy's executable NAV.

### 3.3 Free and public sources only

Free registration/API keys are allowed; payment, paid trials, paid fallbacks, private feeds,
and scraped access-control workarounds are excluded. Publicly accessible is not equivalent to
permission to redistribute. Store source URLs, retrieval hashes, access terms, permitted use,
coverage, adjustment rules, quota, and historical availability evidence in a versioned manifest.
Keep restricted raw payloads and credentials out of git; publish code and hashes where appropriate.

| Source and official reference | Use | Free access and historical limitation | Admission rule |
|---|---|---|---|
| SEC EDGAR [R1] | Filing dates, original financial statements, slow issuer features | Public APIs without API key; identifiable User-Agent and fair-access limits; current aggregate is not automatically an as-of panel | Join original accession and public dissemination/availability time; amendments become new versions, not replacements of old information |
| FRED/ALFRED [R2] | Rates, inflation, employment, credit context | Free registered key; default FRED observations are today's view of history | Fetch successive explicit vintages; respect source terms and release timing; a single vintage is not a full historical release panel |
| BLS and World Bank, documented in [source notes](data-sources.md) | Slow macro context | Existing free collectors retrieve current/revised snapshots | Use prospectively or with verified archived releases; otherwise exclude historical predictive features |
| US Treasury [R3] | Public bill/yield curves and reference cash rates | Free public history; yields are not total returns or guaranteed broker cash interest | Correct day count, compounding, publication lag; do not treat changes in yield as bond returns |
| Alpaca Basic market data [R4] | Candidate ETF/equity OHLCV and available action fields | Free account; published history starts in 2016; IEX and consolidated coverage/entitlements differ | Verify actual endpoint/feed/date entitlement, coverage and action support; IEX-only bars/volume are not NBBO or market-wide ADV |
| Twelve Data Basic [R5] | Candidate independent price cross-check | Published free plan has 8 credits/minute and 800/day; historical/action fields depend on endpoint entitlement | Verify allowed internal use and actual coverage; do not assume premium fundamentals, actions, or long history are free |
| ETF issuers and SEC fund filings | Inception, mandate, distributions, splits, closures | Public documents; uniform bulk historical coverage is not guaranteed | Archive exact records and effective dates; missing action history blocks total-return certification |
| EIA / CFTC [R6] | Optional energy and positioning context | Free public releases; observations can precede release by days or longer | Use actual publication timestamps, revisions and exceptional release schedules; trade only eligible ETFs/equities, never proxy futures P&L |
| Kenneth French library [R7] | Factor attribution and research diagnostics | Public downloadable research portfolios, subject to stated terms and revisions | Diagnostic factors only; no synthetic factor return may be booked as a cash investment |

Provider pages checked 2026-11-03 are access evidence, not a successful download test. Alpaca
documentation distinguishes free IEX coverage and delayed/historical access; account-level SIP
entitlement must be tested rather than inferred from a marketing table. If only IEX volume is
available, use it as a conservative venue-volume bound, without scaling it to total market
volume using an assumed market share. Report the resulting capacity restriction.

Stooq/Yahoo/community files may be evaluated only if permitted access, provenance, adjustment
semantics, and completeness can be established at zero cost. They are not required fallback
dependencies. If no free price source passes the contract, the market backtest is **blocked**;
continue collecting prospective public snapshots and testing accounting with labelled fixtures.
Do not substitute fabricated prices or a paid dataset.

### 3.4 Point-in-time panel specification

Each observation needs `instrument_id`, historical symbol/CIK mapping, source/version, unit,
observation period, public release time, `available_at`, `fetched_at`, and source hash. Each
derived feature records the latest availability of all its inputs and its computation latency.
Only values available by the decision cutoff may enter an order.

Retain the current collectors' first-seen semantics. A newly downloaded current `companyfacts`
aggregate cannot be backdated merely because a row has an old fiscal period. Reconstruct the
original accession disclosure with evidence, or use the feature only after collection. If only
a release date is known, make it usable after that local day plus the next feasible decision
cycle. Do not use quarter-end as filing availability, today's index constituents as yesterday's
universe, or later-restated fundamentals in earlier signals.

Maintain raw prices/actions for fills and a separately audited total-return series for features.
Use split-consistent share counts, ex-date entitlement and dividend receivables, and pay-date
cash. Adjusted close is not an execution price. A dividend paid into cash cannot also be credited
through a total-return NAV calculation. Missing/delisted securities cannot disappear from the
portfolio: preserve positions and use documented final proceeds, explicit unresolved valuation,
and adverse recovery scenarios; suspend certification until material gaps are resolved.

## 4. Architecture and baseline research

The proposed pipeline extends the ingestion foundation with six explicit interfaces:

1. **Versioned public records → eligible observations.** Availability joins and coverage reports.
2. **Eligible observations → slow return/risk forecasts.** Forecast horizons of 21, 63 and 126
   sessions; feature age and uncertainty travel with every estimate.
3. **Forecasts + current holdings → hold/buy/sell decision.** Optimize incremental utility,
   including the cost of eventual exit and the ability to wait.
4. **Decision → cash-feasible orders.** Net across sleeves, round shares, reserve fees, enforce
   settlement and aggregate daily participation caps.
5. **Orders → fills and ledger.** Simulate the declared execution rule, partial fills and misses;
   reconcile positions, corporate actions, cash, costs and NAV independently.
6. **Ledger → evaluation/promotion report.** The report cannot supply feedback to a locked test.

Use simple numerical models first: fixed rules, regularized linear forecasts, shrinkage
covariances and a small scenario optimizer. No expensive training or LLM service is required.
A later small tree/sequence model must beat these baselines after identical costs and search
budgets. A complex predictor is optional; reliable decisions are the actual objective.

### Signal families and controls

| Family | Economic hypothesis | Initial implementation | Main falsification |
|---|---|---|---|
| Slow trend/persistence | Some large allocation moves persist long enough to amortize retail costs | Fixed 63/126/252-session trend ensemble; monthly decisions; negative views map to reduced holdings/cash | Lag by another session, shift rebalance day, and compare with a simple fixed 126-session rule |
| Relative strength with diversification | Rotation between distinct asset risks can improve allocation | Rank trailing excess returns within economic groups; shrink estimates; enforce group caps | Compare to static and equal-weight portfolios with the same universe/caps |
| Macro-conditioned risk | Public release information may improve risk forecasts more reliably than return direction | ALFRED-based changes in inflation/rates/credit; predict covariance/tail scenarios first | Compare to price-only risk forecasts; remove each macro family; use delayed-vintage controls |
| Slow issuer quality, later stage | Original disclosures contain persistent information about balance-sheet and cash-flow strength | Accession-based cash profitability, accruals, leverage change; sector-normalized long-only ranking | Matched valuation/momentum controls; delisted/universe audit; reject if access-time corrections remove the effect |

These are known signal families, not novelty claims. Do not call a new blend “alpha” merely
because it has a high absolute Sharpe. Separate compensation for equity, duration, gold and
cash exposure from incremental performance. Energy signals must not recreate the historical
concentration documented in the campaign under different names.

## 5. Proposed research contributions

### H1. Joint uncertainty and cost threshold for holding or trading

Known work already accounts for trading costs, predictor decay and multi-period portfolio
control [R9, R10]. The proposed extension is an **auditable public-data uncertainty set** that
combines forecasting error, release/revision ambiguity and cost uncertainty in the same
hold-versus-trade decision. Provenance is not itself predictive alpha; test whether it prevents
bad trades better than a simple freshness filter.

For a feasible trade `z = w_new − w_drifted`, define the estimated incremental utility over
horizon `H`, in units of portfolio return:

$$
G_t(z)=\inf_{\theta\in\Theta_t}
\left[\widehat U_{t,H}(w^{drifted}+z;\theta)
      -\widehat U_{t,H}(w^{drifted};\theta)\right]
-\sup_{\phi\in\Phi_t}\widehat C_{t,H}(z;\phi).
$$

`U` includes predicted excess return, covariance risk and scenario tail loss; `C` includes
incremental entry, anticipated exit and maintenance costs relative to holding, each counted
once across the horizon. `Theta` covers train-only
forecast uncertainty and admissible input vintages/availability delays; `Phi` covers cost
scenarios. The same scenarios compare holding and trading. Hold unless the best feasible
candidate has `G_t(z) > delta`, with `delta` fixed during development. Risk-mandated reductions
may override this threshold, but their costs and turnover remain visible.

Calibrate forecast error using trailing blocked validation; widen uncertainty with observed
revision sensitivity and missingness. Never fabricate a 95% guarantee from dependent market
residuals. Unknown timestamps make a feature ineligible rather than merely giving it a small
penalty. Record the competing hold action, predicted benefit, cost interval and deciding
constraint for every decision. This is a model-based admission rule, not a proof of profit.

**Ablation:** identical forecasts with (a) monthly trading, (b) cost-only no-trade bands,
(c) forecast-error bands, and (d) full data/cost uncertainty. Pre-register the expectation that
(d) reduces half-turn turnover by at least 20% versus (b), loses no more than 0.5 percentage
point of net CAGR, and does not worsen drawdown by more than 1 percentage point on development
folds. These margins are hypotheses. Negative results invalidate the added complexity.

### H2. Persistent holdings and a limited turnover budget

Allocate a rolling trading budget to signals expected to survive costs, rather than reset all
weights each month. Predictor-decay weighting is established [R9]; test an account-size-aware
extension that includes minimum ticket fees, current holding/settlement state, and competing
demands on a finite turnover budget. Record tax lots for a separate tax sensitivity; taxes
are not part of the headline pre-tax objective.

Maintain a remaining rolling 252-session budget and penalize consuming it early. Use cohort
expiry dates for planned reviews, but permit sales when the hypothesis fails or risk limits
require them; there is no mandatory holding period that traps losses. Combine all cohorts and
strategies at the instrument level **before** generating broker orders. Internal transfers do
not create fictional trades, rebates, or returns.

Optimize a short horizon of future allocation decisions, execute only the first, and replan
with new information. Approximate fixed ticket costs by selecting a small eligible trade set,
solving continuous allocations, then evaluating exact integer-share orders. At this small ETF
scale compare against enumeration; if rounding breaks a limit, resize or reject. Do not claim
a convex optimum when ticket minima or discrete selection make the problem nonconvex.

**Ablation:** compare equal turnover budgets with uniform monthly spending, fixed bands, and
persistence-based spending. Compare gross versus net benefit, realized holding time, avoided
orders, minimum-fee drag, and opportunity lost by waiting. An improvement only before commission
or only at USD 1 million does not support a retail USD 10,000 claim.

### H3. Slow risk budgets with asymmetric changes

Test whether a slow allocation policy plus a separate daily risk monitor controls drawdowns
without repeated exit/re-entry whipsaw. Volatility management and multi-period control are
known methods [R10, R11]; the proposed experiment jointly prices the turnover needed to defend
a drawdown budget, including recovery delay under a strict 1x funding limit.

Estimate normal and adverse covariance/tail scenarios from prior data. A risk budget can shrink
quickly but recover gradually, with separate entry/exit thresholds and a cooldown fixed in
development. This asymmetry is a testable design, not an assumed improvement. Use a provisional
10% annual volatility budget with exposure multiplier `min(1, target_vol / forecast_vol)`;
low volatility must never cause borrowing. Compare a static allocation with no monitor-driven
trading, because earlier repository experiments found that reactive controls could hurt.

Separate data outages from market stress: stale alpha normally blocks new discretionary orders;
it does not trigger a blind liquidation at an unobserved price. Exposure breaches use a
predeclared reduction rule. For research, test 8% drawdown caution and 12% reduction thresholds,
with an explicit 20-session recovery rule, against a no-drawdown-trigger baseline. A triggered
sale fills only at the next feasible price; thresholds do not cap losses. Record emergency
turnover and all budget breaches. The strategy cannot earn a low-turnover label by excluding
these trades.

**Ablation:** static risk, volatility-only, symmetric drawdown control, and asymmetric control,
all with the same universe and fee model. Measure time underwater, recovery participation,
tail losses and turnover, including 2020 and 2022 where supported. Reject the new controller
if its drawdown improvement is explained by a matched static cash allocation.

### Research claim boundary

The potential publishable result is a measured improvement in the **net feasible frontier**
under public-data imperfections and retail account constraints, with a reproducible decision
and trade ledger. The combination may be useful without being globally novel. Complete a
prior-art comparison with robust portfolio control, no-trade regions, multi-period optimization,
and prediction-uncertainty methods before making a novelty claim. If H1–H3 fail, keep the best
simple baseline and publish the negative evidence; do not invent more variants on the test set.

## 6. Retail execution, impact and accounting

### 6.1 Trade clocks and return ownership

The initial daily-bar rule is: finish signals after session `t` closes, submit for the next
eligible session, and use session `t+1` open plus an adverse cost model **only when a valid open
exists**. The old portfolio owns the overnight move; newly purchased shares own returns only
after their fill. A one-row signal shift with close-to-close returns does not establish this.
For free feeds without reliable opens, use a separately declared next-session close execution
study and delay new-position return ownership accordingly. Do not select the better rule after
viewing performance.

An OHLC open is an execution proxy, not evidence of a fill at that price. Model auction/spread
uncertainty explicitly. Never infer a limit fill merely because a day's high/low touched the
limit. Price-bound orders can miss; remainders carry to a later session subject to cancellation
rules. Include a one-session delay and missed-fill stress. Intraday execution claims need
matching freely available intraday observations; daily bars cannot certify queues or VWAP.

### 6.2 Cost equation and share-level commissions

For each executed order, let `Q` be shares, `P` the pre-impact reference price,
`D = |Q| P` dollar notional, `V` lagged daily dollar volume on the documented feed,
`sigma` lagged daily return volatility, and `rho = D/V`. Use:

$$
C^{USD}=\text{commission}(Q,D)+\text{additional fees}
+D\left(h+\ell+Y\sigma\sqrt{\rho}\right).
$$

`h` is half-spread, `ell` additional adverse execution slippage, and `Y` the impact coefficient;
all three price-impact terms are dimensionless. The square-root term is a sensitivity model
informed by market-impact research [R12], not a calibrated law for tiny ETF orders. If impact
is embedded in the simulated fill price, do not subtract it again as a cash fee. Similarly,
implementation shortfall measured from actual fills must not be added to its own components.

Use the ordinary US whole-share IBKR Pro schedule as the reference retail example, not an
assertion about the eventual account's broker or eligibility [R13]:

| Schedule | Published first-tier per-share rate | Minimum/order | Stated commission cap |
|---|---:|---:|---:|
| Pro Fixed | USD 0.005 | USD 1.00 | 1% of trade value |
| Pro Tiered, ≤300,000 shares/month | USD 0.0035 | USD 0.35 | 1% of trade value |

For eligible standard orders, model `min(max(rate * abs(Q), minimum), 0.01 * D)`, then apply
the schedule's actual exceptions and additional fees. No order means zero commission. Use
dated fee tables, not today's rates for all historical years. Where old schedules are missing,
label a constant-current-schedule replay as a cost scenario, not historical realized costs.
Do not double-count charges already included in Fixed pricing. Tiered exchange/clearing and
sell-side regulatory charges must follow the actual schedule; assume no liquidity rebates
without evidence. Fractional shares, routing exceptions, and commission-free/API eligibility
need separate verification. Zero commission never means zero execution cost.

**Illustrative arithmetic, not a backtest:** 5 shares at USD 100 is a USD 500 order, so the
USD 1 Fixed minimum is 20 bp one way before spread/impact; 50 shares at USD 100 costs the
same USD 1 minimum, or 2 bp. This explains why very small rebalances can destroy a good signal.

Cash interest uses the broker's actual dated balance/NAV tiers, with a zero-interest fallback
when unknown. A Treasury reference yield is the Sharpe comparator, not automatically the
return on idle cash. IBKR publishes balance and NAV-dependent treatment [R14]. A Treasury ETF
earns its actual price/distribution return and costs money to enter or exit. Fund expenses
already reflected in prices must not be deducted a second time. Report taxes separately under
explicit scenarios rather than imply a universal after-tax return.

### 6.3 Preregistered stress grid and capacity

The following are **research assumptions**, not measured spreads, guaranteed upper bounds,
or estimates of future liquidity. Freeze them before scoring and revise only with new evidence
and a new protocol version.

| Variable | Base research case | Stress cases |
|---|---|---|
| Half-spread + extra slippage, per side | 2 + 2 bp for liquid ETFs; 5 + 5 bp for later equity sleeve | Double and triple both components; use larger observed values whenever available |
| Impact `Y` | 1.0 | 0.5, 2.0; compare a conservative linear-impact alternative |
| Order participation | ≤0.1% of trailing 20-session average dollar volume | Halve volume; reject/part-fill beyond cap; no overnight unlimited fill assumption |
| Volatility/liquidity shock | Lagged measured daily volatility | 2x volatility, 0.5x volume and 3x spread/slippage jointly |
| Cash interest | Verified eligible schedule | Zero interest |
| Execution | Declared next-session rule | One extra session delay; 25% of orders miss the first eligible session under a seeded rule independent of returns |
| Account size | USD 100k | USD 10k / 25k / 1m, recomputing integer shares, fees and cash tiers |

If the only volume is IEX volume, `V` means IEX volume throughout; this is a conservative
size-screening scenario, not a market-wide impact calibration. No known volume means no capacity
claim. Planned participation uses only past data; the simulator also limits fills using actual
ex-post session liquidity and carries residual orders, without leaking that volume to decisions.
Do not evade the cap by slicing one parent order into many children: aggregate same-instrument
orders across sleeves and account for cumulative impact and per-order minimum fees.

Report break-even total cost in basis points, capacity as a curve rather than one number,
and **which account sizes meet all gates**. The high-cost case doubles commissions and the
base price-friction/impact charges; it must retain positive excess CAGR and Sharpe ≥0.5.
The joint liquidity shock is a separate tail diagnostic, not a relabeled base run.

Paper fills can test software and timing, but they do not measure real market impact. Keep
model uncertainty until actual executions are separately authorized and observed. Research in
this plan never requires a paid dataset or an actual-money trade.

### 6.4 Turnover and ledger invariants

For session `t`, define executed traded notional fraction
`g_t = sum(abs(filled_shares * reference_price)) / pretrade_NAV`, excluding movements in the
cash bookkeeping account but including traded Treasury ETFs. Report both `g` and the clearly
labelled half-turn statistic `tau_t = g_t / 2`. Annualized half-turn turnover is
`252 / n_sessions * sum(tau_t)`. A full replacement sells 100% and buys 100%, so `g=2` and
`tau=1`; charge costs on **both legs**. Initial investment from cash has `g=1`, `tau=0.5`.
Report establishment and terminal liquidation costs and turnover separately **and included**
in the all-in evaluation. Liquidation follows the same delayed, capacity-constrained rule.

Compute required trades from marked, drifted shares, not consecutive target weights. A
buy-and-hold portfolio trades zero between corporate actions even though its weights drift.
Account for distributions, entry, exits, risk reductions, rejected/partial orders and re-entry
after gaps. External contributions/withdrawals are separate flows, not investment returns.

Required artifacts: instrument/action manifest, feature snapshot, decision log, order ledger,
fill ledger, corporate-action ledger, settled/unsettled cash ledger, daily positions/NAV,
cost attribution, and evaluation report. Each decision/order/fill has a unique linked ID,
timestamp/timezone, quantity, raw price source, status, cost components, strategy version,
source hashes, and reason. A fill sourced from a simulation is labelled simulated even when
its reference price is a real observation.

An independent replay from fills/actions/cash must reproduce NAV within documented monetary
rounding tolerance, with explicit residuals. Check no negative cash/shares, no synthetic asset
PnL, zero hidden borrowing, no dividends twice, all costs once, no orders before availability,
and complete account-level—not merely sleeve-level—turnover. Portfolio-level sleeve netting
must be reconciled to actual underlying holdings.

## 7. Evaluation resistant to reused history and overfitting

### Chronological design

The repository has already explored many historical periods and variants. All dates used in
its prior model/strategy selection are **development history**, even if an old report calls
them OOS. Renaming those dates or changing the train/test cutoff does not restore independence.
Inventory prior experiments and freeze a data-exposure ledger before making performance claims.

1. On verified history, use an initial 36-month training window, following 12-month inner
   validation, then a 12-month outer evaluation; roll forward annually. Prefer expanding
   training unless the rolling alternative was selected on inner folds only. With a 2016
   start, earliest evaluation is approximately 2020, subject to availability and label purging.
2. Freeze selected hyperparameters, feature transformations, estimator seeds, risk/cost model,
   and universe rules before each outer interval. Never train or select on its outcomes.
   Previously explored outer periods remain retrospective development diagnostics.
3. Purge training/validation examples whose forward-return labels intersect the next interval.
   With horizons up to 126 sessions, use exact label-end timestamps, not a token one-day gap.
   If any diagnostic trains on observations after a test block, embargo at least the maximum
   label horizon beyond that block; the primary expanding walk-forward never uses future data.
4. Carry holdings, costs, cash, signal warmups and pending orders through outer boundaries.
   No free reset to cash or free rebalancing at each refit. Fit winsorization, scaling, feature
   selection and imputation only on eligible training data. Never skip a bad or failed fold:
   failure makes the run incomplete; a genuine strategy abstention stays in its funded cash state.
5. Freeze code/config/data contracts at timestamp `T0`. A fresh historical holdout is valid only
   with evidence it has not informed selection; otherwise the primary confirmation starts on
   the first eligible session after `T0`. Do not call a 2026 historical tail unseen by default.
6. After any change motivated by confirmation returns, retire that interval to development and
   begin a new prospective confirmation clock. Append results; do not rewrite earlier decisions.

Use at least three non-overlapping annual outer intervals for a preliminary historical study;
if unavailable, mark evidence insufficient. Minimum six months and six scheduled rebalances of
paper operation tests mechanics, not a reliable annual Sharpe. Seek at least 24 prospective
months for stronger performance evidence, and longer where dependence/power analysis requires.
No short sample alone can certify the stretch targets.

### Model selection and statistical evidence

Log every candidate, failed run, manual rule change and abandoned family. Reserve a maximum of
24 development configurations for the first study, excluding fixed mechanical stress replays;
their role and seeds must be declared before scoring. H1–H3 use the same forecast inputs,
universe, cost assumptions and matched candidate counts. Combining the winning parts is an
additional registered candidate, not a free uncounted improvement.

Report daily excess-return Sharpe with daily risk-free alignment, ordinary annualization and
an autocorrelation-aware estimate; include uncertainty from paired stationary/block bootstrap
on the same portfolio and benchmark dates. Check sensitivity to 21/63/126-session blocks and
disclose effective sample size. Daily NAV includes non-trade days and accrued cash, not only
winning trades or completed round trips. Mark smooth or stale prices as a valuation concern.

Use the Deflated Sharpe Ratio as a selection/non-normality diagnostic [R15], with the raw
trial count and a disclosed correlation-based sensitivity; do not treat a convenient effective
trial count as known truth. If historical trial counts cannot be reconstructed, report DSR as
unavailable or a sensitivity range and rely on fresh confirmation. Probability of Backtest
Overfitting [R16] and blocked placebos are supplementary diagnostics, not replacements for
chronological testing. Null tests must rerun the entire selector and costs; shuffling only a
winning strategy's net returns understates search bias.

Stress publication delays, revisions, missing observations, dropped sources, provider
disagreement, corporate actions, unseen tickers, rebalance dates and nearby parameters.
Change one day of future data in a causality test: earlier decisions and orders must remain
unchanged. Performance that needs precise parameter peaks or a single crisis is fragile.

Modern pretrained LLMs can contain historical outcomes even when prompts are date-filtered
[R17]. Keep historical prediction/execution independent of those models. Optional text
extraction needs original documents, frozen extraction rules, and leakage audits; forecast
claims from a model with unknown temporal training exposure require prospective testing.
LLMs may help formulate research and inspect logs, but cannot repeatedly inspect a locked
holdout and direct another search while it remains labelled out of sample.

## 8. Baselines, ablations and promotion decisions

All strategy comparisons use the same available dates, action handling, funding convention,
actual price feeds and fee schedules. Publish both standard reference portfolios and a
constraint-matched version where appropriate; a conventional 60/40 benchmark may exceed the
candidate's single-ETF cap and must be labelled accordingly.

| ID | Frozen comparison | Why it is needed |
|---|---|---|
| B0 | Zero-interest cash; verified cash/Treasury reserve; equity buy-and-hold; conventional 60/40 equity/Treasury | Opportunity cost, market context and hidden cash-interest attribution |
| B1 | Capped equal-weight and fixed diversified allocation, monthly banded rebalance | Tests whether any forecasting is necessary |
| B2 | Fixed 126-session trend/relative-strength rule, long-only, monthly; cash when ineligible | Transparent slow-signal competitor |
| B3 | Shrinkage minimum-variance and capped inverse-volatility allocation, no borrowing | Tests whether risk allocation alone explains performance |
| B4 | Same forecasts plus fixed no-trade bands and realistic costs | Primary control for incremental H1–H3 value |
| A1–A3 | Add each of H1/H2/H3 to B4 independently | Isolate marginal benefit and cost of complexity |
| A4 | Registered combined controller and leave-one-component-out variants | Test whether components add value together |

Select the strongest simple control on **inner development data**, not the final test. Include
a matched static cash blend at comparable realized volatility as an explanatory diagnostic;
its hindsight risk match is not an investable selection rule. Report net CAGR, annual returns,
worst rolling 12 months, volatility, excess Sharpe, Sortino, Calmar, max daily drawdown, duration
underwater, expected shortfall, beta/factor exposures, turnover, trade count/size, all cost
components, cash weight/return, missed orders, data coverage and account-size sensitivity.

Admission is a sequence of evidence gates:

1. **Integrity:** free access/usage recorded, point-in-time inputs valid, no material unresolved
   prices/actions, ledger reconciles, no leverage or funding violations. Any failure blocks
   the performance claim, however attractive the result.
2. **Historical research candidate:** all minimum numerical gates in §1 hold jointly at the
   stated account size; development results show ≥0.15 Sharpe improvement over the selected
   B4/simple control, ≤0.5 percentage point CAGR sacrifice and ≤1 percentage point drawdown
   deterioration, or a separately preregistered Pareto-improvement claim. Report all folds.
3. **Robustness:** the doubled-cost gate in §6 holds; delay/parameter/provider tests do not
   reverse the economic conclusion. Report failures by stress and size rather than averaging
   them away. Tail shock losses are shown even if the ordinary gate passes.
4. **Confirmation:** on genuinely untouched/prospective data, show paired uncertainty for the
   preregistered incremental metric. A strong superiority claim requires its 95% block-bootstrap
   interval to exclude zero and adequate power; otherwise retain “inconclusive,” not “validated.”
   Report selection-adjustment limitations even if ordinary confidence intervals look positive.
5. **Operational readiness:** paper-run positions, cash, costs and orders reconcile; stale data,
   missed sessions, restarts and duplicate-order recovery are exercised. An operational pass
   does not establish alpha. Any future real-money activation is a separate decision.

Numerical thresholds cannot be satisfied by mixing the best account size, cost case, fold,
turnover definition, or portfolio variant. Keep the historical frontier visible even when no
strategy is promotable. The system must be able to conclude **“no demonstrated edge yet.”**

## 9. Implementation work packages

These are dependency-ordered work packages, not claims that the code exists. Keep research
dependencies in an optional environment so the current ingestion CLI remains dependency-free.

| Stage | Concrete deliverable and proposed location | Completion evidence |
|---|---|---|
| P0 — Freeze study | `research/protocols/unlevered_v1.json`, universe/fee/source manifests, trial and data-exposure registries | Immutable hashes, targets/cutoffs/model budget recorded; historic results explicitly classified |
| P1 — Qualify data | Extend `world_trader/sources/` with entitled price/action adapter; `research/data/` builders using existing records/store | Small real free-source fetch and cached replay; price/action reconciliation; per-instrument coverage and missingness; no fake successful download |
| P2 — Funded replay | New `research/execution/` ledger and cost modules; reuse audited utilities from `campaign/bt/` | Independent cash/share/NAV replay; commission arithmetic, partial fills, settlement transitions and causal timing tests |
| P3 — Baselines | `research/baselines/`, walk-forward runner and reporting | B0–B4 on common verified windows, complete ledgers, costs at each NAV, every failed fold disclosed |
| P4 — H1 and H2 | `research/controllers/` uncertainty/hold decision and turnover allocation | Registered ablations, trade-level benefit/cost records, exact fee/rounding check against small-universe enumeration |
| P5 — H3 and combination | Risk scenario controller and A1–A4 study | Static-cash/risk controls, stress/delay tests, negative results retained; no unregistered holdout search |
| P6 — Confirm prospectively | Frozen daily paper runner and append-only scorecard | At least six months of mechanical evidence; no live orders; continue longer confirmation without claiming short-run Sharpe certainty |

P0–P3 take priority over extra predictors. Do not train a large model while action data,
cash accounting or holdout contamination is unresolved. Stop an unsuccessful family at its
registered experiment budget and record why; indefinite search until a desired Sharpe appears
is not a valid completion criterion.

### Required implementation tests

- Hand-computed two/three-asset portfolios: buy-and-hold drift causes no trades; a full rotation
  pays both legs; entry and exit fees are charged; share rounding cannot overdraw cash.
- Corporate actions: split changes shares without a profit; ex-date entitlement/pay-date cash
  reconcile; missing dividends and delistings cannot create a false pass.
- Timing: after-close information cannot fill at the same close; new holdings do not earn the
  preceding overnight move; future-data perturbations do not change past decisions.
- Costs: zero order, tiny order, minimum/cap transitions, tiered additional fees, shared parent
  impact, falling ADV and partial-fill accumulation; no impact double-counting.
- Operations: holidays, settlement regime transitions, interrupted sessions, duplicate order
  IDs, unavailable source, stale quote, and ledger restart/replay invariance.
- Evaluation: cash risk-free subtraction, constant-price cases, loss/drawdown sign conventions,
  annualization, missing fold failure, and all-in versus ongoing turnover reconciliation.

Synthetic fixtures are appropriate for these accounting tests and must be labelled. They are
never admissible evidence for investment returns or market liquidity. Existing ingestion tests
can run with `python -m unittest discover -v`; they do not exercise the proposed trading system.

## 10. First research decision and stop conditions

The first useful result is a fully funded, costed ETF baseline and an honest explanation of
its shortcomings—not another best-Sharpe search. Then test whether H1 avoids enough weak trades
to raise net utility, whether H2 allocates a scarce turnover budget better, and whether H3
adds protection beyond simply holding less risk. Add equity fundamentals only when the free
point-in-time data supports them.

If free historical data is inadequate, say exactly which fields/dates are missing and collect
prospectively. If realistic execution removes the edge, reject or simplify the strategy. If
no portfolio meets the simultaneous targets without leverage, publish the measured feasible
frontier and retain the constraint. Do not conceal failure with synthetic returns, cash yields
the account cannot earn, hidden sleeve leverage, or new labels for reused test data.

## References and access evidence

Provider terms and schedules must be rechecked at implementation. Sources below were inspected
for this plan on 2026-11-03; papers support prior art/methods, not a claim that world-trader has
reproduced their results. The proposed thresholds and experiments are this plan's design choices.

- **R1 — SEC:** [EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
  and [access rules](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data).
- **R2 — St. Louis Fed:** [FRED/ALFRED real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html).
- **R3 — US Treasury:** [interest-rate statistics](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics)
  and [CSV archive](https://home.treasury.gov/interest-rates-data-csv-archive/).
- **R4 — Alpaca:** [market-data subscription/coverage documentation](https://docs.alpaca.markets/us/docs/about-market-data-api)
  and [historical feed documentation](https://docs.alpaca.markets/us/v1.1/docs/historical-stock-data-1).
- **R5 — Twelve Data:** [individual pricing and quotas](https://twelvedata.com/pricing).
- **R6 — EIA/CFTC:** [EIA Open Data](https://www.eia.gov/opendata/),
  [COT reports](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm),
  [release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm).
- **R7 — Kenneth R. French:** [research data library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html).
- **R8 — SEC Investor.gov:** [T+1 settlement bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/new-t1-settlement-cycle-what-investors-need-know-investor-bulletin)
  and [cash-account bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/updated-9).
- **R9 — Gârleanu and Pedersen:** [Dynamic Trading with Predictable Returns and Transaction Costs](https://www.nber.org/papers/w15205),
  working paper 2009, revised 2013. Predictor decay and partial adjustment are established prior art.
- **R10 — Boyd et al.:** [Multi-Period Trading via Convex Optimization](https://stanford.edu/~boyd/papers/cvx_portfolio.html),
  2017. Receding-horizon cost/risk control is established prior art.
- **R11 — Moreira and Muir:** [Volatility Managed Portfolios](https://www.nber.org/papers/w22208),
  working paper 2016. Results do not establish that a long-only 1x implementation preserves the same benefits.
- **R12 — Donier, Bonart, Mastromatteo and Bouchaud:** [A fully consistent, minimal model for non-linear market impact](https://arxiv.org/abs/1412.0141),
  2015. Impact models require instrument/size calibration; a square-root stress assumption is not retail fill evidence.
- **R13 — Interactive Brokers:** [US stock commissions and fee notes](https://www.interactivebrokers.com/en/pricing/commissions-stocks.php).
- **R14 — Interactive Brokers:** [cash interest and NAV/balance tiers](https://www.interactivebrokers.com/en/accounts/fees/pricing-interest-rates.php).
- **R15 — Bailey and López de Prado:** [The Deflated Sharpe Ratio](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf), 2014.
- **R16 — Bailey, Borwein, López de Prado and Zhu:** [The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf), 2015.
- **R17 — LLM evaluation:** [DatedGPT: Preventing Lookahead Bias in Large Language Models with Time-Aware Pretraining](https://arxiv.org/abs/2603.11838), 2026.
