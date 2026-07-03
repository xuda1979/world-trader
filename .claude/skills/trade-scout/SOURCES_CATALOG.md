# Trade-Scout Master Source Catalog

**This file is the single source of truth for every data/news/alt-data feed,
which API keys exist, and what works vs. is blocked in this environment.**
Do not delete. Update it whenever a source is added, dies, or a key rotates.

Last verified: 2026-07-02.

---

## 1. API keys (stored in repo root `.env.local`, gitignored)

`.env.local` is **gitignored** — never commit it. Keys are read by
`tools/wt/core.py:api_key()` and the older `tools/*.py`. Current keys:

| Env var            | Provider       | Free tier limits            | Used for |
|--------------------|----------------|-----------------------------|----------|
| `ALPHAVANTAGE_KEY` | AlphaVantage   | ~25 calls/day, 5/min        | quotes, FX, movers, commodities |
| `FINNHUB_KEY`      | Finnhub        | 60 calls/min                | global equity/ADR quotes + OHLC |
| `TWELVEDATA_KEY`   | Twelve Data    | 800/day, 8/min              | **FX majors real-time + daily history (backtestable)**; indices spotty (404/paid) |
| `FRED_KEY`         | FRED (StLouis) | unlimited                   | rates, curve, VIX, macro, credit |
| `POLYGON_KEY`      | Polygon.io     | 5/min (stocks/ETF only)     | prev-day OHLCV; options need paid |

To verify keys are present:
`grep -c '_KEY=' .env.local`  (should be 5; do NOT print the values).

---

## 2. No-key real-time sources (the backbone — WORK here)

| Source | Endpoint | Coverage | Notes |
|--------|----------|----------|-------|
| Coinbase | `api.coinbase.com/v2/prices/{SYM}-USD/spot` | crypto spot | real-time 24/7 |
| Binance | `api.binance.com/api/v3/ticker/24hr?symbol={SYM}USDT` | crypto OHLC+chg | real-time; also `fapi.binance.com` for funding/OI |
| Kraken | `api.kraken.com/0/public/Ticker?pair={PAIR}` | crypto | cross-check |
| Nasdaq | `api.nasdaq.com/api/quote/{SYM}/info?assetclass={etf\|stocks}` | US equities/ETFs | has `isRealTime` + `marketStatus`; needs browser UA |
| TWSE (official) | `mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{code}.tw&json=1&delay=0` | Taiwan listed | **live during TW hours**; field z=last, y=prevclose, h/l, n=name |
| Sina | `hq.sinajs.cn/list={code}` (e.g. `sh600519`) | China A-share + HK + US(gb_) | **live**; needs `Referer: finance.sina.com.cn`; **GBK-encoded** (decode gbk); p[0]=name,p[2]=prevclose,p[3]=last,p[4]=h,p[5]=l,p[31]=time |
| Tencent | `qt.gtimg.cn/q={code}` | China A-share/HK | cross-check Sina; GBK; ~tilde-delimited |
| ECB | `data-api.ecb.europa.eu/service/data/EXR/...` | FX (EUR base) | official daily, unlimited |
| Frankfurter | `api.frankfurter.dev/v1/latest?base=USD&symbols=EUR` | FX | ECB-derived, unlimited |
| Coinlore | `api.coinlore.net/api/ticker/?id={id}` | crypto + %chg 1h/24h/7d | unlimited; ids: BTC=90 ETH=80 SOL=48543 XRP=58 BNB=2710 |
| Stooq | `stooq.com/q/l/?s={sym}&f=...&e=csv` and `/q/d/l/?s={sym}&i=d` | global EOD + **daily history** | history powers technicals; intl/futures hit-or-miss |
| Treasury.gov | `home.treasury.gov/.../xml?data=daily_treasury_yield_curve` | UST par curve | no key |
| CFTC | `publicreporting.cftc.gov/resource/6dca-aqww.json` | COT positioning | Socrata; URL-encode `$order` spaces as `%20` |
| alternative.me | `api.alternative.me/fng/?limit=1` | crypto fear & greed | no key |
| GDELT | `api.gdeltproject.org/api/v2/doc/doc?...&mode=tonechart` | global news tone | rate-limits (429) — use sparingly |

---

## 3. Blocked / unreliable in THIS environment (do not waste calls)

| Source | Symptom | Workaround |
|--------|---------|------------|
| Yahoo Finance `query1/2.finance.yahoo.com` | "sad-panda" / 403 | use Nasdaq (US), TWSE/Sina (Asia) |
| CNBC RSS | Access Denied | MarketWatch / Nasdaq / SeekingAlpha feeds |
| NSE India `nseindia.com/api` | Akamai Access Denied (even w/ cookie) | India via INDA ETF (US) or Twelve Data |
| Japan TSE/JPX direct | empty/blocked; Tencent `jp` empty | Japan via EWJ ETF or `^N225` (Stooq best-effort) |
| Polygon options snapshot | 403 NOT_AUTHORIZED | Greeks need paid tier; free = stocks/ETF OHLCV only |
| Stooq `stooq.com/q/...` | **404 on every request in THIS env** (2026-06-26) | FX history via TwelveData; US history via Nasdaq; indices/futures unavailable free |

---

## 4. News feeds (RSS) — verified-reachable set

Defined in `tools/wt/news.py:FEEDS` (22/26 returned items on 2026-06-24).
Grouped: equities (MarketWatch, Nasdaq-Mkts/Stocks, SeekingAlpha, Investing,
Yahoo-Fin, Benzinga, Zerohedge); macro/central-banks (Fed, ECB, BoE, BoJ, IMF);
crypto (Cointelegraph, Decrypt, TheBlock, CoinDesk); FX (ForexLive, FXStreet);
commodities (OilPrice, Mining.com, Kitco); regional (JapanTimes, SCMP, ET-Markets,
Livemint). Failures are skipped at runtime — re-probe periodically.

### Per-ticker company news (powers the wide-candidate `News` column + CATALYSTS)
The 26 RSS feeds above can't cover the dynamic tickers the wide funnel surfaces,
so the scanner fetches news **per displayed US-equity candidate**:

| Source | Endpoint | Gives | Notes |
|--------|----------|-------|-------|
| Finnhub | `finnhub.io/api/v1/company-news?symbol={T}&from=&to=&token=` | headline flow (count, recency, sources) | 60/min; broad coverage incl. microcaps; **equities only** |
| Polygon | `api.polygon.io/v2/reference/news?ticker={T}&apiKey=` | per-ticker **sentiment** (+/-/=) + reasoning | 5/min hard cap → used only on the top few rows (budgeted, 429-safe) |

**Equity-only**: a bare crypto symbol (`SOL` = Emeren Group) or FX pair collides
with an unrelated stock, so per-ticker news is restricted to US equities;
crypto/FX context comes from the crypto/FX RSS feeds + GDELT instead.
Wired in `tools/wt/news.py` (`finnhub_company_news`, `polygon_ticker_sentiment`,
`ticker_news`) and `tools/wt/report.py` (`enrich_with_news`, `print_catalysts`).

---

## 5. Market-structure constraints (shortability — critical for actionability)

Encoded in `tools/wt/instruments.py:SHORT_ALLOWED` / `SHORT_PROXY`:

| Market | Long | Short underlying? | Bearish view via |
|--------|------|-------------------|------------------|
| China A-shares (sh/sz) | ✅ | ❌ Connect shorting banned, 融券 restricted | FXI / KWEB / ASHR / YANG (US ETFs) |
| Taiwan (4-digit) | ✅ | ⚠️ SBL-restricted/uptick | EWT, TSM ADR |
| Hong Kong (.HK) | ✅ | ✅ designated list | — |
| US (equity/ETF/ADR) | ✅ | ✅ freely | — |
| Crypto | ✅ | ✅ perps/margin | — |
| Index (^...) | ✅ | ❌ not directly | matching country ETF / futures |

Other notes: STAR board (688xxx) and ChiNext (300xxx) have 20% daily limits;
A-share normal board ±10%.

---

## 6. The scanner toolchain (how it all fits)

```
tools/scan.py              # CLI entry: python3 tools/scan.py [--no-news --no-altdata --no-catalysts --quiet]
                            # NOTE: --full is now the DEFAULT. News + alt-data + catalysts
                            #       all run every scan (opt OUT with the flags above).
                            #       Opportunities are rare; missing one for a missing
                            #       flag is unacceptable.
tools/wt/
  core.py                  # HTTP, api_key(), CJK-aware tables, freshness, consensus
  instruments.py           # universe + shortability rules
  sources.py               # all price fetchers (crypto, Sina, Tencent, TWSE, Nasdaq, Stooq, Finnhub)
  news.py                  # FEEDS + GDELT tone
  altdata.py               # FRED, Treasury curve, CFTC COT, crypto funding/OI, fear&greed
  catalysts.py             # CATALYST CALENDAR: Finnhub earnings/FDA/IPO + Polygon dividends.
  #                        #   Per-candidate enrichment (enrich_with_catalysts) attaches
  #                        #   nearest catalyst + small composite boost. Standalone
  #                        #   print_calendar() shows the 14d actionable catalyst window.
  analysis.py              # RSI/MACD/ATR/Bollinger/zscore/momentum, regime, RS, R:R, expectancy backtest + signal-conditional STRATEGY LIBRARY, composite score (+catalyst_boost)
  report.py                # gather -> score -> shortability -> composite rank -> catalyst+news enrich -> print
```

Legacy single-file tools still present and usable as fallback:
`tools/global_markets.py`, `tools/scan_news.py`, `tools/fetch.py`,
`tools/probe_sources.py` (re-checks which sources are alive).

### The "bar" (analysis.py thresholds)
`RR_MIN=3.0  RISK_MAX=3%  RISK_MIN=0.5%(floor)  REWARD_MIN=6%  VIX_MAX=25  MAX_STALE_S=15min`
Rows clearing all of these print **above the bar**; others show best asymmetry.

### Composite score weights (0-100)
45% reward:risk asymmetry · 20% technical alignment · 20% relative strength ·
15% regime fit. Long-only-market shorts are dropped and converted to proxy notes.
