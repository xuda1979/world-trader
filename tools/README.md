# world-trader — market opportunity scanner

One-command global scan for **short-term, defined-risk, high reward:risk**
trade ideas. Every run scans the **entire US equity market (~12k tickers)** AND
the **entire China A-share market (~5,500 names)** via a two-stage funnel — both
now fully backtested — plus crypto (24/7 real-time), Taiwan (live), Hong Kong,
and FX majors — with macro regime, technicals, a **signal-conditional strategy
library**, **per-candidate company news**, and alternative data. **Stdlib only;
no pip install.**

## HARD RULE: only OPEN markets, only FRESH prices

**Trading is serious — stale data is worse than no data.** The scanner only ever
surfaces an instrument whose **market is open right now** (or just-closed within
a short buffer) **and** whose quote is **fresh** (crypto ≤ 15 min, FX ≤ 30 min,
equities within the current/just-closed session). A Friday US close shown on a
Sunday is ~36h stale and is **never** presented as an opportunity. Every run
prints a `MARKETS OPEN NOW (...)` banner; if all markets are closed (e.g. a
weekend → only crypto), it says so and shows only what is actually tradeable —
an empty/closed-market table is the correct, honest answer. Sessions
(`tools/wt/markets.py`, UTC, US DST-aware):

| Market | Session (UTC) | Days |
|--------|---------------|------|
| Crypto | 24/7 | every day |
| FX | 21:00 Sun → 21:00 Fri | weekdays (closed weekend) |
| US equities | 13:30–20:00 (EDT) / 14:30–21:00 (EST) | Mon–Fri |
| China A-shares | 01:30–03:30 & 05:00–07:00 | Mon–Fri |
| Taiwan | 01:00–05:30 | Mon–Fri |
| Hong Kong | 01:30–04:00 & 05:00–08:00 | Mon–Fri |

## Quick start

```bash
cd /Users/daxu/software/world-trader     # run from repo root (.env.local + tools/wt)
python3 tools/scan.py --doctor           # 1) verify keys + every source is alive
python3 tools/scan.py                     # 2) WIDE scan: whole US market + curated + ranked table
python3 tools/scan.py --narrow            # 2b) fast: curated universe only (skip whole-market funnel)
python3 tools/scan.py --full              # 3) + news + alt-data (FRED/COT/curve/funding)
```

First time on a new machine: `cp .env.local.example .env.local` and fill in keys
(all free — see the example file for signup links). Missing keys degrade
gracefully; `--doctor` shows exactly what's available. To (re)install the hourly
background job: `bash tools/launchd/install.sh`.

## Commands

| Command | What it does |
|---------|--------------|
| `python3 tools/scan.py` | regime + WIDE US funnel + curated quotes + ranked table |
| `python3 tools/scan.py --narrow` | curated universe only (fast; skips whole-market funnel) |
| `python3 tools/scan.py --quiet` | opportunity table only |
| `python3 tools/scan.py --altdata` | + FRED macro, Treasury curve, CFTC COT, BTC funding/OI |
| `python3 tools/scan.py --news` | + expanded RSS headlines + GDELT tone |
| `python3 tools/scan.py --no-news-enrich` | skip per-candidate company news + CATALYSTS section |
| `python3 tools/scan.py --full` | everything |
| `python3 tools/scan.py --fast` | skip technical enrichment (faster) |
| `python3 tools/scan.py --doctor` | self-check: keys + modules + every live source |
| `python3 tools/scan.py --help` | usage |

## The wide funnel (how ~12k tickers are scanned per run)

Scanning thousands of names without thousands of API calls uses a two-stage funnel:

1. **Stage 1 — breadth (1 call):** Polygon *grouped-daily* returns every US
   ticker's daily OHLCV in a single request (~12k names). A cheap pre-screen
   (price ≥ $3, dollar-volume ≥ $5M, intraday range + directional move) ranks
   them and keeps the **top ~150**.
2. **Stage 2 — depth (~150 calls):** only those candidates get the full
   treatment — daily history, technicals, and the cost-aware backtest with
   significance + out-of-sample validation.
3. **Stage 3 — news (only the displayed rows):** the top US candidates the
   table actually shows get **per-ticker company news** — Finnhub headline flow
   (count + recency) for each, plus Polygon per-ticker *sentiment* on the top
   few — so every surfaced idea comes with its catalyst, sourced and dated.

This is the practical answer to *"broaden the space to find more good
opportunities"*: same strict bar, far more shots at clearing it. `--narrow`
skips stage 1 for a quick curated-only scan. A full wide scan takes ~3–4 min.

## The strategy library (more shots at the SAME strict bar)

Breadth of *instruments* is only half the answer — the other half is breadth of
*strategies*. A single fixed rule tests one hypothesis per name and only measures
whether a stop/target geometry drifts positive. Real low-risk/high-reward edges
are **conditional**: they exist only when a specific setup is present. So every
covered candidate (US/crypto/FX) is now backtested across a **library of
structurally-distinct setups**, each entered **only on the bars where its signal
fires**:

| Setup | Side | Fires when | Idea |
|-------|------|-----------|------|
| `OSbounce`  | Long  | RSI<32 **and** close < lower Bollinger | oversold snap-back to the mean |
| `OBfade`    | Short | RSI>68 **and** close > upper Bollinger | overbought fade to the mean |
| `Breakout`  | Long  | close > prior-20d high **and** > SMA50 | trend-confirmed momentum breakout |
| `Breakdown` | Short | close < prior-20d low **and** < SMA50 | trend-confirmed momentum breakdown |
| `Pullback`  | Long  | SMA20>SMA50 uptrend **and** RSI<45 | buy a shallow dip in an uptrend |

Each setup uses a **volatility-aware (ATR-scaled) stop** and an R-multiple target,
and is judged by the *exact same* bar — net E[R], small sigma, Sharpe, t-stat, and
walk-forward OOS. For each name the tool keeps whichever measured edge is best
(qualifying first, then Sharpe), and **only surfaces a setup when its entry signal
is firing right now** (an actionable entry exists this bar). The winning strategy
is shown in the `Tech` column as `[Breakout]`, `[OSbounce]`, etc. Every extra
setup backtested is also counted in the **Bonferroni** family, so adding
strategies raises — never lowers — the significance bar a row must clear. This is
how the scanner finds *more* genuine opportunities without loosening the risk
discipline.

## The options edge (RV/IV — a vol-regime signal, independent of price-momentum)

A directional backtest edge is only HALF the trade. The options market prices
implied vol (IV) for every US equity with listed options; if IV is **cheap vs
realized vol (RV)**, the trade has a tailwind the backtest doesn't see —
long-gamma pays more than the price-only edge suggests. If IV is **rich**
(RV/IV < 1), the directional view should be expressed with short options or a
tighter stop.

For the top US candidates the scanner now pulls the **ATM straddle** (CBOE
delayed, no key) for the nearest expiry ≤ 45d and computes:

* `RV` — realized vol proxy = `ATR% × √252` (annualized, from daily history)
* `IV` — straddle-implied vol (CBOE-provided, call/put average)
* `RV/IV` — the edge ratio; **> 1.0 = options cheap vs realized**
* `Cost%` — straddle cost / spot (the market's priced 1-sigma move)

This shows in the EDGE & RISK table as a new **`RV/IV`** column. It's a
**structurally independent** signal source — it's vol-regime, not a reskinned
price-momentum setup — so it can flip a borderline row into actionable when
the directional edge is near the bar but options are clearly cheap. Skip with
`--no-options`.

## The China A-share wide funnel (Asian breadth, fully backtested)

China gets the **same treatment as the US**, not a curated handful. Sina's
market-center API exposes **all ~5,500 A-shares** (paginated, most-liquid-first),
and Sina/Tencent kline APIs give **daily history** — so the China funnel is:

1. **Stage 1 (bulk):** pull the most-liquid A-shares (turnover-ranked), pre-screen
   on price/turnover/range/move (liquidity floor ¥80M/day), keep the top ~120.
2. **Stage 2 (depth):** each candidate gets daily history + the full strategy
   library backtest (net of A-share costs: ~5bps commission + 5bps sell stamp
   duty + spread), with the same t-stat / OOS / Bonferroni gates.

A-shares are **long-only** for foreign/retail traders, so only long setups are
surfaced; bearish A-share signals still convert to a shortable US proxy
(FXI/KWEB/ASHR/YANG). **Honest coverage note:** Hong Kong has live quotes (freely
shortable) but free daily history is blocked in this environment, and **Japanese
single-stock** data/news providers (Yahoo/JPX/Eastmoney) are all blocked here —
so Japan is traded via `EWJ`/`^N225` proxies, not single names. Taiwan is live
via TWSE but has no free history (no backtest). A real environment limitation,
stated plainly rather than faked.

## How it reads the table

The opportunity table is **ranked by per-trade expected Sharpe = E[R] / sigma** —
exactly the objective: *high expected return, small standard deviation of
outcomes*. The **bar** a trade must clear:
`E[R] >= +1%/trade, sigma <= 5%, Sharpe >= 0.40, sample n >= 20, horizon <= 5d`,
**plus** statistical significance (t ≥ 2, Bonferroni-adjusted for the number of
candidates tested) **and** a positive out-of-sample Sharpe (held-out recent 30%).
Rows clearing all of these print **above the bar**; the rest show best measured
edge (OOS-positive first). An empty table is common and correct — it means no
high-E[R]/low-sigma edge exists right now.

- **E[R]%** backtested expected return per trade (the real edge, win-rate-aware)
- **sigma%** standard deviation of outcomes — *this is the risk you want small*
- **Sharpe** E[R] / sigma — the number that's sorted to the top
- **t-stat** is the edge statistically real? `t = E[R] / standard-error`; **≥ 2**
  (~95% confidence) is required, and the threshold is **raised automatically by a
  Bonferroni correction** for how many candidates were backtested this scan
- **oosS** out-of-sample Sharpe — the rule is fit/measured on the older 70% of
  bars, then **re-measured on the most recent 30% it never saw**. An edge that
  goes negative out-of-sample was curve-fitting and is rejected.
- **Win%** historical hit-rate · **n** sample size of the backtest
- **Market** the instrument's market/asset-class (CRYPTO/US/FX/CN-A/TW/…)
- **Price (ET)** live price + quote time in US Eastern (DST-aware)
- **Chg%** today's percent move · **Risk%** max loss if stopped (hard-capped risk)
- **ATR%** daily volatility (ATR14 as % of price) · **Kelly%** optimal stake size
  (negative = no edge, don't trade — why a fat R:R with a low win-rate still says skip)
- **R:R / Stop / Target** the trade plan · **Tech** `[Setup]` (the firing
  strategy: Breakout/OSbounce/…) + RSI/trend/RS context
- **News** per-candidate company-news read (US equities): `+`/`-`/`=` sentiment ·
  `n12` = 12 articles in 7d · `2h`/`1d` = age of latest headline · `--` = not
  enriched (crypto/FX use the RSS/GDELT `--news` section instead, since a bare
  crypto/FX symbol collides with an unrelated stock ticker)
- **Data** freshness (RT / CLOSED / STALE / no-ts)

Below the table, a **CATALYSTS** section prints the freshest headline (with age,
source count, and — where Polygon supplies it — a one-line sentiment *reason*)
for each top candidate, so the narrative behind a setup is sourced and verifiable.

How E[R] is measured: for each candidate the tool replays the *exact* entry/
stop/target rule over ~1.5 years of daily bars (Nasdaq for US, Binance for
crypto, **TwelveData for FX majors**), counting stop-first as a loss
(conservative) and **charging a realistic round-trip cost on every trade**
(crypto ~20bps, US ~8bps, FX ~4bps) so E[R] is NET, not gross. A 4:1 R:R that
only wins 14% of the time has **negative** E[R] and is correctly ranked at the
bottom — R:R alone no longer rules. To clear the bar a setup must additionally
be **statistically significant (t ≥ Bonferroni-adjusted 2)** and **survive
out-of-sample** — this is what stops in-sample lucky noise from masquerading as
an edge.

> Honest caveat: backtested win rates overstate live results (slippage, regime
> change, overfitting). Treat E[R]/Sharpe as a *filter*, size small, and expect
> losing streaks even on a real positive-expectancy edge.

Long-only markets (China A-shares, Taiwan) lack free daily history here, so they
get no expectancy estimate and are excluded from the Sharpe ranking; bearish
signals there still produce a **shortable ETF/ADR proxy** (FXI/KWEB/ASHR,
EWT/TSM) suggestion.

## Package layout

```
tools/scan.py            CLI entry point
tools/wt/
  core.py        HTTP, api_key(), CJK-aware tables, freshness, consensus
  markets.py     market sessions: is a market OPEN now? (the actionability gate)
  instruments.py instrument universe + shortability rules
  sources.py     price/history fetchers (crypto, Sina, Tencent, TWSE, Nasdaq, Binance, Finnhub)
  news.py        RSS feeds + GDELT tone + per-ticker company news (Finnhub/Polygon w/ sentiment)
  altdata.py     FRED, Treasury curve, CFTC COT, crypto funding/OI, fear&greed
  catalysts.py   CATALYST CALENDAR: Finnhub earnings/FDA/IPO + Polygon dividends; per-candidate enrichment + small composite boost
  analysis.py    RSI/MACD/ATR/Bollinger/zscore/momentum, regime, RS, R:R, expectancy backtest, **signal-conditional strategy library**, composite (+catalyst_boost)
  report.py      gather -> score -> shortability -> enrich (news+catalysts) -> rank -> print
```

Legacy single-file tools remain as fallback: `global_markets.py`,
`scan_news.py`, `fetch.py`, `probe_sources.py`.

## Full source/key catalog

See `.claude/skills/trade-scout/SOURCES_CATALOG.md` — every endpoint, which keys
exist, and what's blocked in this environment. **Do not lose that file.**

## Honest framing

There is no guaranteed high return with low risk. This targets **asymmetry**
(reward several multiples of risk) with **defined, hard stops** (small known
loss per trade). Research only, not financial advice. Verify live before acting.
