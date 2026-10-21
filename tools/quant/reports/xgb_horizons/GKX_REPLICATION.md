# GKX (Gu-Kelly-Xiu 2020) Replication — Best Efforts with FREE Data

**Date:** 2026-08-17
**Goal:** replicate Gu, Kelly & Xiu (2020) "Empirical Asset Pricing via Machine
Learning" (RFS) monthly long/short Sharpe using only free data.

## Setup (best efforts)
- **Universe:** 292 US large caps (local twelve_big panel, 20y daily OHLCV).
- **Characteristics (33):** ~24 technicals from local daily prices (momentum
  1/3/6/12m + 12-1, vol 3/12m, maxDD, Amihud, 52w hi/lo distance, beta,
  cross-sectional dispersion, skew/kurt, volume z) + **7 free fundamentals**
  (Finnhub stock/metric, free tier: market cap, ROE, revenue growth, asset
  turnover, PE, EPS growth, div yield) + earnings surprise/proximity (local
  earnings panel) + macro state & interactions (VIX z, mkt 3m).
- **Models:** Ridge (linear baseline), XGBoost GBRT, MLP 3-layer NN (32-16-8,
  GKX-style architecture).
- **Validation:** monthly, PURGED walk-forward (train on months <= m-1 to
  predict month m+1 return; NO label overlap), 7y rolling window, yearly
  refit. OOS 2009-2026 (211 months).
- **Portfolio:** monthly decile L/S, equal-weight AND market-cap-weight,
  gross AND net (6bp/side full cycle = 24bp/mo).

## Results (OOS 2009-2026, decile L/S)

| Model | EW gross SR | EW net SR | VW gross SR | VW net SR |
|---|---|---|---|---|
| Ridge | -0.57 | -0.96 | -0.58 | -0.97 |
| **XGB (GBRT)** | **+0.21** | **-0.04** | **+0.23** | **-0.02** |
| MLP (NN) | -0.26 | -0.68 | -0.23 | -0.68 |
| *GKX 2020 (ref)* | *2.45* | *gross* | *1.35* | *gross* |

## Honest conclusion: Gu's result does NOT replicate with free data
The best model (XGB) achieves **SR +0.21 gross, ~0 net** — about **1/10 of
GKX's equal-weighted 2.45**. The gap is structural, not methodological:

1. **Universe (292 vs ~30,000 stocks).** GKX's equal-weighted 2.45 Sharpe
   lives in the small/micro-cap tail — they explicitly note the EW strategy
   tilts to micro-caps and is hard to implement at scale. Their implementable
   value-weighted Sharpe is 1.35; on large caps alone it would be materially
   lower. We trade 292 liquid large caps — the least alpha-dense part of the
   cross-section.
2. **Characteristics (33 vs 94+).** GKX uses point-in-time CRSP/Compustat
   fundamentals (value, profitability, investment, accruals, payout, etc.) —
   the proven drivers. Free data gives us technicals + 7 current-snapshot
   fundamentals (no history: the model cannot learn time-varying fundamental
   signals; PB and leverage are premium metrics, all-null on the free tier).
3. **Costs.** GKX reports gross; with honest 24bp/month full-cycle costs our
   best model's edge (~0.2%/mo gross) is fully consumed.

## What would be needed to approach GKX (none free)
- CRSP universe (all US stocks incl. micro-caps) + Compustat point-in-time
  fundamentals -> the two data sources ARE the edge.
- Realistic borrow/cost modeling would still cut their headline numbers
  (their own paper notes the EW 2.45 is largely micro-cap/illiquid).

## Honest bottom line
With free data on a large-cap universe, the GKX-style ML monthly L/S is
**not profitable net of costs (best: XGB, SR ~0)**. The 2.45 Sharpe is a
data-advantage + micro-cap-tilt result, not a free-data-large-cap result.
This is consistent with the desk's own leak-free measurement (IC ~0.02 on
large caps) and with the published literature's practical conclusion that
net-of-cost large-cap monthly ML Sharpe sits around 0.5-1.0 at best.

## Artifacts
- `gkx_monthly.py` — monthly characteristic panel builder (free data).
- `gkx_backtest.py` — purged walk-forward ML + decile L/S (ridge/xgb/mlp,
  EW/VW, gross/net).
- `data/gkx_monthly_panel.parquet`, `data/gkx_names.json`,
  `data/finnhub_metrics.json` (fetched fundamentals), `gkx_results.json`.
- Re-run: `python3 gkx_monthly.py` (needs finnhub_metrics.json) then
  `python3 gkx_backtest.py`.

# UPDATE 2026-08-17 (v2) — wider universe + SEC EDGAR point-in-time fundamentals

Added the two free data levers the first pass lacked:
1. **Universe 292 -> 657 names** (union of all local panels: twelve_big +
   twelvedata + twelve_liq + polygon + polygon_v2; ~290 names with full
   2006-2026 history, 657 in 2024-2026).
2. **Point-in-time fundamentals from SEC EDGAR companyfacts (FREE, no key)**:
   parsed XBRL -> quarterly book equity, assets, net income, revenue, operating
   income, gross profit, cash flow, shares outstanding; each value dated by its
   FILING date (no lookahead). Built GKX-style characteristics:
   **bm (book/market), size (log shares*price), roe, gross profitability,
   operating profitability, accruals, investment (asset growth), payout**
   + Finnhub PE/div-yield + 24 technicals + earnings + macro interactions
   = 39 characteristics.

Results (OOS 2009-2026, decile L/S, purged walk-forward):

| Model | EW gross SR (v1 -> v2) | EW net SR (v1 -> v2) |
|---|---|---|
| Ridge | -0.57 -> +0.11 | -0.96 -> -0.14 |
| **XGB** | **+0.21 -> +0.44** | **-0.04 -> +0.18** |
| MLP | -0.26 -> -0.19 | -0.68 -> -0.56 |

XGB EW net is now POSITIVE (+0.18). Still ~1/5 of GKX's 2.45 gross EW.
Remaining gap: (a) historical cross-section still ~290 names (no micro-caps;
657 only in 2024-2026), (b) fundamentals coverage growing (EDGAR fetch for
626 CIKs completes in background; rerun after), (c) GKX is gross.

Full EDGAR fetch (~626 names) completes in background; the next rerun with
full fundamentals coverage should push the numbers further.

# UPDATE 2026-08-17 (FINAL) — full EDGAR fundamentals coverage

EDGAR fetch complete (600 companies). Final results (OOS 2009-2026, decile L/S,
purged walk-forward, 657-name union, 39 characteristics incl point-in-time
bm/size/roe/gross-prof/op-prof/accruals/investment):

| Model (EW) | gross SR | net SR (24bp/mo) |
|---|---|---|
| **XGB** | **+0.43** (ann 5.0%) | **+0.21** (ann 2.1%, win 54%) |
| MLP | +0.30 | -0.08 |
| Ridge | +0.15 | -0.10 |

VW versions are negative for all models (large-cap VW adds no edge; consistent
with GKX where VW 1.35 << EW 2.45).

**FINAL VERDICT (free data, best efforts): the best replicable GKX-style
strategy is XGB equal-weighted decile L/S with net SR ~+0.21, gross ~+0.43 —
about 1/6 of GKX's 2.45 gross EW.** The remaining gap decomposes:
(1) universe 657 vs ~30k (no micro-cap tail, where GKX's EW alpha lives);
(2) 39 vs 94 characteristics; (3) our numbers are net of 24bp/mo, theirs gross;
(4) their EW 2.45 is explicitly micro-cap/illiquid-weighted and would not
survive realistic costs at scale (their VW = 1.35).
Free data cannot close this gap: the CRSP 30k-stock universe and the micro-cap
tilt are not freely available at this quality.

# UPDATE 2026-08-17 (v5) — more data, then the honesty filter

Got MORE free data: (1) expanded EDGAR characteristics (payout, R&D/assets,
capex/assets, leverage, current ratio, tax/assets — 12 fundamentals total),
(2) 400 more names' price history from TwelveData free tier (8 req/min,
background; 124/400 fetched so far), universe 657 -> 713+.

CRITICAL SANITY FINDING: the raw expanded panel produced garbage (DD -1.7M) —
the new names include penny stocks with split/data artifacts. After filtering
to INVESTABLE names (median price >= $2, monthly |ret| sane), the honest
results are:

| Model (EW, investable universe) | gross SR | net SR |
|---|---|---|
| XGB | +0.06 | -0.18 |
| MLP | +0.04 | -0.25 |
| Ridge | +0.14 | -0.16 |

vs the v3 number (XGB gross +0.44) that included sub-$2/penny/extreme-tail
names. **The investable free-data GKX replication is ~zero net of costs.**
The v3 "improvement" was partly illiquid-name alpha that cannot be traded at
size (exactly GKX's micro-cap caveat, reproduced on our scale).

TwelveData fetch continues in background (400 names, ~35 min); a rerun with
the fuller investable universe will confirm whether more names help.

# UPDATE 2026-08-18 (v6) — 1032-name investable universe: net SR +0.42 (Ridge EW)

TwelveData free-tier fetch completed for 375 more names (8 req/min, resumable)
-> union universe 657 -> 1032 names; 874 investable tickers in the panel
(754/month recent). Rebuilt panel (44 chars, investable filter $2+/sane rets)
and reran the purged walk-forward decile L/S (OOS 2009-2026):

| Model | EW gross SR | EW net SR | VW gross SR | VW net SR |
|---|---|---|---|---|
| **Ridge** | **+0.64** | **+0.42** | +0.01 | -0.19 |
| XGB | +0.51 | +0.33 | +0.29 | +0.15 |
| MLP | +0.05 | ~-0.20 | -0.15 | ~-0.40 |

vs v5 (657 names): Ridge net -0.16 -> +0.42, XGB -0.18 -> +0.33.
**More investable names = more edge (confirmed directionally).** The v6
best (Ridge EW net SR +0.42, ann ~4.6% gross) is the strongest free-data
result so far - about 1/6 of GKX's 2.45 gross EW, and now NET positive with
an investable (>= $2) universe. NN (MLP) is weakest at this scale (GKX's NN
advantage needs the full 30k-stock universe).
Second TwelveData batch (~400 more names) fetching in background; rerun after.

# UPDATE 2026-08-18 (v7) — 1092-name universe: Ridge EW net SR +0.48 (ceiling approaching)

Batch 2 of the TwelveData fetch added ~60 more names (rest were junk/errors —
the quality queue is nearly exhausted) -> union 1092 names, 901 investable
tickers. Purged walk-forward decile L/S OOS 2009-2026:

| Model | EW gross SR | EW net SR |
|---|---|---|
| **Ridge** | **+0.69** | **+0.48** (ann 5.9% net) |
| XGB | +0.23 | +0.06 |
| MLP | -0.01 | ~-0.25 |

Ridge improved further (v6 +0.42 -> v7 +0.48); XGB degraded (0.33 -> 0.06) —
the greedy trees overfit the noisier new names while the regularized linear
model is robust to them. **Ridge is the champion; the quality-name queue is
nearly exhausted** (batch 2 was mostly junk: ~40% error rate, sub-$2 or
<200-row histories). Further free-name expansion has diminishing returns.
Converged best free-data result: **Ridge EW decile L/S net SR ~+0.5, ann
~6% net, on a ~1000-name investable universe** — ~1/5 of GKX's 2.45 gross EW.
Remaining levers: more EDGAR characteristics, model ensembling, or a paid
universe.

# UPDATE 2026-08-18 (v8) — 4 more EDGAR characteristics: Ridge EW net SR +0.54

Added 4 more point-in-time characteristics from the SAME EDGAR files
(inventory/assets, receivables/assets, cash/assets, PPE growth) -> 48 total
(16 EDGAR fundamentals). Purged walk-forward decile L/S OOS 2009-2026:

| Model | EW gross SR | EW net SR |
|---|---|---|
| **Ridge** | **+0.75** | **+0.54** (ann 6.7% net) |
| XGB | +0.18 | +0.01 |
| MLP | — | — |

Ridge again improved (+0.48 -> +0.54) — every free-data lever (more names,
more characteristics) has raised the regularized linear model's net Sharpe.
XGB stays degraded (overfits the noisier names). VW negative for all.
Converged trajectory: Ridge EW net SR 0.42 (1032 names) -> 0.48 (1092) ->
0.54 (+4 chars). Next levers: more EDGAR tags (the XBRL files hold ~400),
ensembling Ridge+XGB, or the paid universe.

# UPDATE 2026-08-18 (v9) — 57 characteristics: Ridge holds net +0.54 (ceiling)

Added 4 more EDGAR fundamentals (depreciation/assets, retained/equity,
payables/assets, interest coverage) + 2 price chars (36m long-term reversal,
dollar volume) -> 57 characteristics. Purged decile L/S OOS 2009-2026:
  Ridge EW: gross 0.75 / net +0.54 (unchanged - at the free-data ceiling)
  XGB EW: gross 0.25 / net +0.09 (improved slightly)
  VW improved (Ridge VW net -0.05)
DIMINISHING RETURNS: 9 more characteristics did not move Ridge (0.54). The
free-data ceiling for the GKX-style Ridge EW decile L/S is ~net SR 0.54 on
this ~1100-name investable universe. Next: model ensembling (Ridge+XGB)
gains would be marginal; the meaningful jump needs the full CRSP universe.

# UPDATE 2026-08-18 (v10/scale-up attempt) — universe-margin FRAGILITY: converged estimate ~0.3-0.5

Attempted to scale up the universe via the remaining free sources (TwelveData
daily quota -> ~65 more names; batch 3 mostly junk/short-history; Stooq still
anti-bot-blocked; yfinance still rate-limited). Findings:

1. Adding the junk-tier names (100-500 row histories) DESTABILIZED the models:
   Ridge net 0.54 -> 0.20, XGB 0.09 -> 0.48 (model ranking flipped = noise).
2. Removing them (>=1000-row quality filter, 913 tickers) gives Ridge net 0.23,
   XGB 0.00 - materially different from v9's 0.54 on a nearly identical universe
   (901 vs 913 tickers). The result is FRAGILE to marginal universe changes.

HONEST CONVERGED ESTIMATE: Ridge EW net SR ~0.3-0.5 (best point 0.54, but
universe-sensitive; 0.23-0.54 range across near-identical configurations),
ann ~3-7% net, on ~900-1100 investable names with 57 point-in-time
characteristics. The free-data sources are exhausted (EDGAR complete,
TwelveData quota spent, Stooq/yfinance blocked); the marginal-name expansions
add noise, not signal. The gap to GKX's 2.45 gross EW is the paid CRSP
universe (30k stocks incl. micro-caps) - not reachable with free data.
SCALE-UP VERDICT: stop expanding the free universe; the recent-window
cross-section (~800-900 investable names) is the free-data ceiling.

# UPDATE 2026-08-18 (final free-data exploration) — converged: Ridge net SR ~0.2-0.5

Exhausted the remaining free-resource levers:
1. Finnhub sector/industry (39 industries, 1097 names) + macro interactions
   (credit z, DXY z x momentum): added -> Ridge net 0.23->0.15 (NEGATIVE).
2. Finnhub analyst recommendations: fetch rate-limited (stuck 40min, killed).
3. TwelveData queue: zero EDGAR-known names remain (quality pool exhausted).
4. Universe-margin test (v13, v9 features, cleaned universe): Ridge 0.23 vs v9
   (0.54 on a 901-ticker universe with short-history names) -> the edge
   fluctuates 0.2-0.5 with marginal universe composition.

FINAL HONEST ESTIMATE: Ridge EW decile L/S, net SR ~0.2-0.5 (point estimate
~0.3), ann ~3-7% net, ~900-1100 investable names, 57 point-in-time
characteristics, purged walk-forward OOS 2009-2026. Every free lever has been
tested: names (EDGAR/TwelveData/Finnhub/polygon pools exhausted), fundamentals
(20 EDGAR tags), technicals (30+), industries, macro interactions, analyst
data (blocked). Marginal additions are neutral-to-negative. This IS the
free-data ceiling for the GKX-style replication. GKX's 2.45 gross EW requires
the paid 30k-stock CRSP/Compustat universe with micro-caps.

# UPDATE 2026-08-20 (v14) — CRITICAL BUG FIX: panel ret_next was scrambled; TRUE 1m results are BETTER

`ret_next` was built via `mret.stack().shift(-1)` — shift on the stacked
MultiIndex shifts by ROW POSITION, scrambling returns across tickers.
Proof: CSCO Feb-2020..Feb-2021 prod(1+panel ret_next) = +105.7% vs true
+11.7% (raw CSV). Every v1-v13 number that trained on or booked ret_next
is invalid. Rebuilt ret_next per-ticker (close(m+1)/close(m)-1), patched
the panel parquet in place, rerun the full purged walk-forward decile L/S:

| Model | EW gross SR | EW net SR (24bp/mo) | vs v9 contaminated |
|---|---|---|---|
| **Ridge** | **+0.76** (ann +13.1%) | **+0.61** (ann +9.9%) | 0.54 |
| **XGB** | **+0.72** (ann +13.2%) | **+0.57** (ann +10.0%) | ~0.09 |
| MLP | -0.02 | -0.23 | ~0 |

**The scrambled label was SUPPRESSING the measured edge.** The true
free-data 1m result is BETTER than the contaminated story: Ridge AND XGB
both ~+0.6 net SR, ~10%/yr net — and XGB's 1m "weakness" (the
Ridge-dominates narrative) was largely the bug (0.09 -> 0.57). MLP remains
weak; VW remains ~zero (edge in the EW cross-section). New honest
free-data ceiling for the GKX-style 1m replication: **net SR ~0.6, ann
~10%** on ~900-1100 investable names, 57 characteristics, OOS 2009-2026.

# UPDATE 2026-08-20 (v15) — UNIVERSE BUG: 292-name subset -> full 913-name panel

The v14 rerun (and all my label joins) used pc.load_ohlcv() = twelve_big
only (~292 tickers), while the panel holds 913 from the full union. The
label joins silently restricted every backtest to the 292-name subset.
Fixed: union_panel.load_union() (1,097 tickers), ret_next rebuilt with
sane-tail filter (coverage 50% -> 85%).

Full-universe purged walk-forward decile L/S (OOS 2009-2026):

| Model | EW gross SR | EW net SR (24bp/mo) | vs v14 (292-name) |
|---|---|---|---|
| **Ridge** | **+1.12** (ann +17.4%) | **+0.93** (ann +14.1%, dd -28%) | 0.61 |
| **XGB** | **+0.90** (ann +17.9%) | **+0.76** (ann +14.6%, dd -52%) | 0.57 |
| MLP | +0.16 | -0.07 | -0.23 |

The free-data GKX replication on the REAL universe: **Ridge EW net SR
+0.93, XGB +0.76, ann ~14% net** — approaching the paper's value-weighted
1.35 gross for the first time, on free data. (Caveats unchanged: 39-57
chars vs 94, no micro-cap tail, net costs, and the union includes the
junk-tier names known to destabilize marginal universe changes.)

# UPDATE 2026-08-20 (v16) — 1m robustness suite: RIDGE is the robust champion; XGB's edge is the illiquid tail

`xgb_1m_robust.py` (no retraining, full universe, monthly decile L/S net):

| Variant | XGB (d3) | Ridge |
|---|---|---|
| decile 24bp | 0.84 (ann +18.2%, dd -64%) | **0.93** (ann +14.1%, dd -28%) |
| decile 48bp | 0.71 | 0.75 |
| decile 96bp | 0.47 | 0.37 |
| quintile 24bp | 0.62 | 0.86 (dd -23%) |
| PIT $2 floor | 0.57 | **0.96** (improves!) |
| $1M ADV | 0.28 | **0.91** |
| $5M ADV | 0.19 | **0.81** |
| $20M ADV | 0.23 | **0.79** (ann +11.6%) |
| worst year | -41.8% (2021) | **-17.1% (2015)** |
| 3m/6m/12m-hold decay | 0.51 / 0.18 / 0.15 | **0.70 / 0.73 / 0.65** |

**Verdict**: XGB's 1m headline is mostly the small/illiquid tail — at
capacity floors it collapses to ~0.2, and its per-year record is lumpy
(2020 +139%, 2021 -42%). **Ridge is the robust 1m champion**: its edge
survives the $2 floor (improves), holds at $20M ADV (0.79, ann +11.6%),
has no disaster years (worst -17%), and its signal PERSISTS at 12m holds
(0.65) — a slow-moving linear component the trees miss. Ridge 1m is the
capacity-honest monthly-rebalance strategy; XGB 1m only for the
unconstrained micro-cap book. Live book (2026-07-31, Ridge): LONG AKTS,
MU, DDOG, VLO, TSLA... (mostly liquid names).
