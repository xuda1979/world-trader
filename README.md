# world-trader

Free API data collection for quantitative research. Python 3.11+, **no runtime dependencies**.
The collectors use documented HTTPS JSON APIs, keep a local SQLite cache and request audit,
and export normalized JSONL or CSV. They do not trade or claim investment performance.
Timezone-aware day boundaries use the operating system's IANA database; on systems without it
(commonly Windows), install `tzdata` with `python -m pip install tzdata`.

本项目优先接入官方开放 API，保存数据来源、采集时间、可用时间和修订版本。
当前快照与历史可得信息分开处理，便于后续回测避免前视偏差。

## Start without an account or API key

Run from the repository root:

```bash
python -m world_trader sources
python -m world_trader fetch worldbank --country USA --indicator NY.GDP.MKTP.KD.ZG --start 2020 --end 2023 --output data/gdp.jsonl
python -m world_trader fetch bls --series LNS14000000 --format csv --output data/unemployment.csv
python -m world_trader fetch clinicaltrials --ids NCT07281105 --output data/trials.jsonl
python -m world_trader stats
```

Optional installation: `python -m pip install .`, then replace `python -m world_trader` with `world-trader`.
Shell examples use bash. Credentials are read from environment variables; `.env` files are not loaded automatically.

## Implemented sources

| Command | Data | Credential/access | Historical knowledge time |
|---|---|---|---|
| `sec-filings` | 10-K/10-Q/8-K/13F filing metadata | `SEC_USER_AGENT`, no API key | SEC acceptance timestamp; conservative next New York day when missing |
| `sec-facts` | XBRL concept, separate units and accessions | `SEC_USER_AGENT`, no API key | First collection of the current aggregate |
| `fred` | FRED/ALFRED macro observations | Free registered `FRED_API_KEY` | First collection, or explicit `--vintage` snapshot |
| `bls` | Monthly US economic series | No key; v1 default recent three-year window | First collection |
| `worldbank` | Country-level macro indicators | No key | First collection of revised observations |
| `clinicaltrials` | Industry-sponsored trial status, phase, sponsor, enrollment | No key; projected fields exclude contacts and locations | First collection of current study metadata |
| `coingecko` | Crypto price, market cap, 24-hour volume | Free `COINGECKO_DEMO_API_KEY`; Demo history at most 365 days | First collection |
| `finnhub-news` | Company-news headline, summary, publisher, URL | Free `FINNHUB_API_KEY`, subject to account entitlement | First collection; publication retained separately |

SEC filing metadata includes 13F events; **13F holdings tables and full filing text are not parsed**.
CoinGecko chart volume is market volume, not active-address or wallet-distribution data.
Current clinical-trial status cannot be used as a historical trial-status panel.
No article URLs are followed. Provider terms and your account's data-use rights still apply.

### SEC and XBRL

Set an identifiable operator User-Agent with a monitored contact email (preferred) or HTTPS contact URL:

```bash
export SEC_USER_AGENT='Your organization research contact@your-domain.org'
python -m world_trader fetch sec-filings --cik 320193 --forms 10-K,10-Q,8-K --start 2024-01-01 --end 2025-12-31 --output data/aapl-filings.jsonl
python -m world_trader fetch sec-facts --cik 320193 --concept Assets --unit USD --output data/aapl-assets.jsonl
```

Without `--start`, filings collection covers the SEC's recent filing window. With `--start`, overlapping
SEC archive JSON files are included. `--max-pages` bounds the total submission requests, including the
initial page. A page-budget error saves no partial normalized result; narrow the query or increase the budget.

### FRED and explicit vintage snapshots

Obtain a key from the [FRED API key page](https://fred.stlouisfed.org/docs/api/api_key.html):

```bash
export FRED_API_KEY='your-own-free-key'
python -m world_trader fetch fred --series UNRATE --start 2020-01-01 --end 2024-06-01 --vintage 2024-07-15 --output data/unrate-vintage.jsonl
```

This is what the series looked like **on 2024-07-15**, not what every observation looked like on its original
release date. For conservative intraday alignment, the snapshot becomes available after that entire
America/Chicago day. Fetch successive vintages if a historical revision panel is needed. Without `--vintage`,
availability starts at collection time. Missing values remain null.

### Optional free-tier market data

```bash
export COINGECKO_DEMO_API_KEY='your-own-free-demo-key'
python -m world_trader fetch coingecko --coin bitcoin --currency usd --days 30 --output data/btc.jsonl
export FINNHUB_API_KEY='your-own-free-key'
python -m world_trader fetch finnhub-news --symbol AAPL --start 2026-10-01 --end 2026-10-02 --output data/aapl-news.jsonl
```

Finnhub news requests are limited locally to 31-day windows. The endpoint does not supply a completeness
or pagination certificate; account coverage and any provider result cap still need to be checked before
using news counts as a factor. Premium transcripts, ESG, and congressional-trade endpoints are not called.

### Offline replay and backtest exports

```bash
python -m world_trader --offline fetch worldbank --country USA --indicator NY.GDP.MKTP.KD.ZG --start 2020 --end 2023 --output data/gdp-replay.jsonl
python -m world_trader asof --at 2026-10-19T23:59:59Z --source worldbank --entity USA --output data/known-at-cutoff.jsonl
```

Use the same query and environment credentials for offline replay. Expired cache entries can be replayed
offline with their **original** fetch times. Online reads never silently fall back to expired data.
`--refresh` bypasses a fresh cache. `--db PATH` selects the database. Global flags precede the command.

The `asof` query selects the latest stored revision per source/dataset/entity/record ID with
`available_at <= cutoff`. It cannot reconstruct uncollected historical snapshots or fix survivorship bias,
entity mapping, source coverage, or an incorrectly designed return horizon.

## Reliability and provenance

- Fixed API host allowlist, HTTPS, no redirects, no browser automation or private website endpoints.
- Conservative service rates, shared across processes using the same database. SEC defaults to at most
  2 requests/second. Limits across other applications, other databases, or the same public IP are not coordinated.
- Bounded retries for transient network errors, 429 and selected 5xx responses; `Retry-After` is respected.
  A delay beyond 60 seconds stops the request. 401/403 responses stop immediately.
- JSON response cache, original response SHA-256, redacted request URLs, and request-attempt audit.
  Auth headers are not persisted. FRED's query-string key is redacted from stored URLs and errors.
- Atomic revision insertion, idempotent cached replay, bounded pagination, and atomic file exports.
  BLS `-` and FRED `.` remain null; no prices or fundamentals are invented or forward-filled.
- Observation, publication, availability, and fetch timestamps remain separate. Date-only availability
  uses timezone-aware day boundaries. Current snapshots default to first-seen availability.

Keep `data/` and populated credentials out of git. Local rate limits do not replace provider daily/monthly
quotas. No purchases, paid API domains, or subscription upgrades are performed by the code.

## Tests and live checks

```bash
python -m unittest discover -v
python -m world_trader --refresh smoke --report data/live-smoke.json
```

The deterministic suite runs without internet or credentials. Live smoke checks fetch small real queries,
store them, then verify offline replay and idempotent insertion. Missing credentials appear as `skipped`;
they are never counted as live passes. A real collection failure returns a nonzero exit status.
The checked-in [validation report](docs/validation.md) distinguishes real requests from synthetic fixtures.

See [source access notes](docs/data-sources.md) for official documentation and suggestions deliberately
left out of this first implementation. An ingestion pass does not establish predictive alpha; subsequent
factor research needs time-aligned, out-of-sample IC/IR, cost-aware returns, baseline correlations, and
universe/coverage checks.
