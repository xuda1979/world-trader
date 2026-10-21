---
name: trade-scout
description: >-
  Scan the internet for short-term (intraday to a few weeks) trading
  opportunities across any liquid instrument (equities, ETFs, futures, FX,
  crypto, options) and surface asymmetric setups with favorable
  reward-to-risk. Use when the user asks to "find trades", "scan for
  opportunities", "what should I trade", screen markets, or evaluate a
  ticker/symbol for a short-term entry. Produces a ranked, evidence-backed
  watchlist with explicit entry, stop, target, sizing, and invalidation.
---

# Trade Scout

## HARD TRADING RULES (non-negotiable — read first, never violate)

Trading is serious. Acting on stale data loses real money. These rules are
enforced in code (`tools/wt/markets.py` + `report.py`) and MUST also govern any
manual analysis you do:

1. **ONLY surface instruments whose market is OPEN right now** (or just-closed
   within a short, tradeable buffer). A US-equity quote from Friday's close shown
   on a Sunday is ~36h stale and **useless** — worse than nothing, because it
   looks actionable but isn't. Never present such a row as an opportunity.
2. **Freshness gate**: even in an open market, the quote must be recent
   (crypto ≤ 15 min, FX ≤ 30 min, equities within the current/just-closed
   session ≤ 8h). No timestamp ⇒ not tradeable.
3. **Know the sessions** (UTC; US is DST-aware):
   - **Crypto** — 24/7, always open (the only always-tradeable book).
   - **FX** — Sun 21:00 → Fri 21:00 UTC; **closed all weekend**.
   - **US equities** — Mon–Fri 13:30–20:00 UTC (EDT) / 14:30–21:00 (EST).
   - **China A-shares** — Mon–Fri 01:30–03:30 & 05:00–07:00 UTC (lunch break).
   - **Taiwan** — Mon–Fri 01:00–05:30 UTC. **Hong Kong** — 01:30–04:00 & 05:00–08:00.
4. **If no market is open** (e.g. a weekend with crypto-only), say so plainly and
   show only crypto — or "stand aside". An empty table because markets are closed
   is the CORRECT, honest answer; never pad it with stale closed-market rows.
5. **Always print which markets are open** and the data age, so the user can see
   at a glance that every shown row is live and actionable.

The scanner now prints a `MARKETS OPEN NOW (...)` banner and gates every row;
`Data` column shows RT/age. If you ever see a stale row surfaced as an
opportunity, that is a **bug** — fix it, don't trade it.

## Honest framing (read first, always tell the user)

There is **no such thing as guaranteed high return with low risk**. If a
setup were truly high-reward and risk-free, it would be arbitraged away
instantly. What is achievable and what this skill targets:

- **Asymmetry**: setups where the potential reward is several multiples of
  the money risked (reward:risk >= 2:1, ideally >= 3:1).
- **Defined, capped downside**: every idea has a hard stop, so "low risk"
  means *small, known, pre-committed loss per trade*, not "cannot lose".
- **Edge from confluence**: multiple independent signals (catalyst +
  technical + flow + sentiment) pointing the same way.

Always restate this to the user. Never imply certainty. This is research,
**not financial advice**, and the user is responsible for their own trades.

## Reference files (read these — they hold everything needed to run)
- `SOURCES_CATALOG.md` -- **the master catalog**: every data/news/alt-data
  source, which API keys exist (in `.env.local`), what works/blocked in this
  environment, and the exact endpoints. Do not lose this.
- `DATA_SOURCES.md` -- search patterns + the local fetcher quick-reference.
- `EXAMPLE.md` -- a full worked example showing the expected output shape.

Read these when you need source ideas or output formatting.

## Fast path — run the scanner (preferred)

The repo ships a one-command opportunity scanner (`tools/scan.py`, stdlib only,
package in `tools/wt/`). It already does Phases 2-4 quantitatively. **It now
scans the ENTIRE US equity market (~12k tickers) every run** via a two-stage
funnel — Polygon grouped-daily pulls the whole market in one call, a cheap
pre-screen (price/liquidity/range/move) picks the top ~150, and those get the
full backtest. Plus the curated core: crypto (real-time), US core, China
A-shares (live), Taiwan (live), and **FX majors** (TwelveData history). The top
US candidates the table displays also get **per-ticker company news** (Finnhub
headline flow + Polygon per-ticker sentiment) shown in a `News` column and a
sourced `CATALYSTS` section. **Run it first**, then layer WebSearch for deeper
catalysts/news on the top candidates.

```bash
cd /Users/daxu/software/world-trader      # must run from repo root (.env.local + tools/wt)
python3 tools/scan.py            # regime + WIDE US funnel + curated quotes + ranked table
python3 tools/scan.py --quiet    # opportunity table only
python3 tools/scan.py --narrow   # legacy: curated universe only, skip the whole-market funnel
python3 tools/scan.py --altdata  # + FRED macro, Treasury curve, BTC funding, CFTC COT
python3 tools/scan.py --news     # + expanded RSS headlines + GDELT tone
python3 tools/scan.py --no-news-enrich  # skip per-candidate company news + CATALYSTS
python3 tools/scan.py --full     # everything
python3 tools/scan.py --doctor   # self-check: keys + every live source
```

Output: a table ranked by **per-trade expected Sharpe (E[R]/sigma)**, where E[R]
is the NET backtested return after realistic costs. To clear the **bar** a setup
must have E[R]>=+1%, sigma<=7%*sqrt(h/5) (horizon-aware: a 10-day trade gets a
~9.9% ceiling, a 3-day trade gets ~5.4%), Sharpe>=0.40, n>=20, be
**statistically significant** (t>=2, Bonferroni-adjusted per-candidate at
m=setups×horizons ≈ 7-21, NOT globally), AND **survive out-of-sample** (positive
Sharpe on a held-out recent 30%). Rows that don't fully qualify are shown as
"best measured edge", OOS-positive ones first. Long-only markets (China
A-shares, Taiwan) auto-suggest a shortable ETF/ADR proxy (FXI/KWEB/ASHR,
EWT/TSM) for bearish signals.

A full wide scan takes ~3-4 min (whole-market call + ~150 history fetches +
backtests). Use `--narrow` for a fast curated-only scan.

### Always-on hourly job (don't lose this)
`tools/hourly_scan.sh` runs a scan every hour, logging to `tools/logs/`. It is
scheduled via a **launchd agent**; the plist is checked into the repo at
`tools/launchd/com.worldtrader.hourly-scan.plist`. To (re)install on a fresh
machine: `bash tools/launchd/install.sh`.

If `tools/scan.py` errors, fall back to the manual phases below + WebSearch.

## Operating procedure

Work through these phases in order. Use `WebSearch`/`WebFetch` (or any
configured market-data / news tools) heavily -- this skill is internet-driven.

### Phase 1 -- Scope the scan
Clarify or assume sensible defaults, then state them:
- **Universe**: which instruments? (default: large/mid-cap US equities + major
  ETFs + liquid crypto majors. Expand to FX/futures/options on request.)
- **Horizon**: intraday, swing (2-10 days), or position (2-6 weeks).
- **Capital & risk tolerance**: account size and max % risk per trade
  (default assume 1% risk per trade if unspecified -- ask if it matters).
- **Constraints**: shortable? options allowed? no leverage? sectors to avoid?

### Phase 2 -- Gather information from the internet
For the chosen universe, collect and cite sources for:
1. **Catalysts** -- earnings dates, guidance, FDA/regulatory events, product
   launches, M&A, index rebalances, macro prints (CPI, FOMC, jobs), token
   unlocks/upgrades for crypto.
2. **Price/volume action** -- recent trend, support/resistance, breakouts,
   gaps, volatility (ATR), volume surges, relative strength vs sector/index.
3. **Order flow & positioning** -- unusual options activity, short interest,
   days-to-cover, futures COT, funding rates (crypto).
4. **Sentiment & narrative** -- news flow, analyst rating/target changes,
   social momentum -- treated as *secondary, contrarian-aware* signals.
5. **Macro/regime context** -- overall market trend, VIX, rates, sector
   rotation, risk-on/off.

Prefer multiple independent, reputable sources. Note data freshness and
flag anything stale or unverified. Distinguish fact from rumor.

### Phase 3 -- Filter for asymmetry and low risk
Discard anything that fails these gates:
- **Liquidity**: tight spreads, enough volume to enter/exit cleanly.
- **Defined risk**: a logical, nearby stop level must exist (structure,
  prior swing, ATR multiple). If you can't define a stop, drop it.
- **Reward:risk >= 2:1** measured to a realistic target, not a fantasy one.
- **Confluence**: at least 2-3 independent signals agree.
- **Avoid traps**: skip illiquid names, binary unhedged event gambles,
  pump-and-dump patterns, and anything you cannot source.

### Phase 4 -- Rank and size
Score each surviving candidate (0-100) by weighting:
- Reward:risk ratio (30%)
- Strength/number of confluent signals (25%)
- Catalyst proximity & quality (20%)
- Liquidity & ease of execution (15%)
- Macro/regime alignment (10%)

Compute **position size** from the user's risk budget:
`shares/contracts = (account * risk%) / (entry - stop)`.

### Phase 5 -- Report
Output a ranked watchlist. For **each** idea use this template:

```
#<rank> TICKER -- Direction (Long/Short) | Horizon | Score: <n>/100
Thesis      : one-sentence why (the edge)
Catalyst    : event + date/window
Entry       : price or trigger condition
Stop        : level + why (invalidation point)
Target(s)   : T1 / T2 + why
Reward:Risk : e.g. 3.1:1
Size        : shares/contracts for the stated risk budget
Signals     : bullet list of confluent evidence
Sources     : links / references with dates
Risks       : what kills this thesis; confidence level (Low/Med/High)
```

End every report with:
- A **summary table** (rank, ticker, direction, R:R, score).
- **Portfolio note**: correlation/overlap between ideas, total risk if all
  taken, and a reminder to never risk more than the predefined budget.
- The disclaimer: *Research only, not financial advice. Verify live prices
  and data before acting; markets move fast.*

## Hard rules
- Always cite sources from the internet; never invent prices, dates, or news.
- If live data is unavailable or stale, say so explicitly and lower confidence.
- Never promise profits or describe any trade as "safe" or "guaranteed".
- Every single idea must have a stop and a quantified reward:risk.
- Prefer fewer high-quality, well-sourced ideas over a long noisy list.
