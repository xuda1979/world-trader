# DATA_MORE_CRYPTO FINDINGS (2026-09-03)

## Deliverable
tools/quant/data/more_crypto/<SYMB>.csv for 12 coins: BTC,ETH,BNB,SOL,ADA,XRP,DOGE,LTC,DOT,LINK,AVAX,MATIC
(date,open,high,low,close,vol) + <SYMB>.csv.meta + manifest.csv + fail-closed lint_crypto.py +
TDD test_merge_property.py + build_csv.py + fetch_vision_vol.py + raw sources (raw_td/, raw_vision/ 1066 files).

## Source tried-in-order results (charter order, stop-when-works was overridden by data-quality evidence)
| # | Source | Result (exact) |
|---|--------|----------------|
| 1 | Twelvedata time_series 1day outputsize=5000 | 11/12 symbols OK with full history (BTC n=3294 2017-08-28..2026-09-03) BUT **no volume field returned** for crypto (bar keys = open,high,low,close,datetime only); MATIC 404 (renamed POL) |
| 2 | Finnhub crypto/candle BINANCE:BTCUSDT | **DENIED**: {"error":"You don't have access to this resource."} (not in free tier) |
| 3 | Binance api.binance.com / api.binance.us public klines | **GEO-BLOCKED**: HTTP 000 (connection refused), 0 bytes |
| 3b | **Binance Vision static CDN (data.binance.vision) monthly 1d klines** | **WORKS, no key**: HTTP 200 valid zips 2017-08..2026-07 per coin; FULL OHLCV |
| - | CryptoCompare min-api | Key-required 401 (moved to CoinDesk, free key needed) |
| - | CoinGecko api/v3 market_chart | HTTP 000 (blocked) |

## FINAL PIPELINE (evidence-driven, different from naive TD-only)
PRIMARY = Binance Vision monthly klines OHLCV (real Binance spot prints, string-exact, <=2026-07-31).
TAIL = Twelvedata 2026-08-01..2026-09-03 (34 days, vol=NA honest — Vision 2026-08 monthly dump not yet published: 12x HTTP 404 verified).
MATIC = stitched MATICUSDT (..2024-08-31) -> POLUSDT (2024-09-13..); **12-day genuine exchange gap 2024-09-01..12**
(Binance delisted MATICUSDT before POLUSDT listing; TD has no data for the gap either — verified empty).

## TDD RED->GREEN evidence (superpowers)
- lint_crypto.py written BEFORE any final CSV: RED observed (EXIT=1, "12x FILE MISSING").
- test_merge_property.py v1 RED (no outputs) -> after TD-first build caught real problems:
  P2 ETH 11/890, DOT 13/622, **MATIC 169/532 sampled rows >0.5% close mismatch vs Vision**.
- Root cause (systematic-debugging):
  (a) TD "POL/USD" pre-migration history is a DIFFERENT ASSET: MATIC/TD-POL ratio drifts 0.82x (2020-08) -> 90x (2023-10),
      =1.0000 exactly only from 2024-10; TD POL backfill REJECTED for MATIC.
  (b) TD vs Binance-print sporadic OHLC divergence (not timezone: same-day median |diff| 0.022%, shifted-day median 2.04% —
      boundaries align; divergences are TD aggregation artifacts, e.g. ETH 2021-01-13 td=1010.59 vs vision=1129.89, -10.56%).
  => switched to VISION-FIRST builder; TD demoted to tail-only.
- test v2 (strengthened: string/float-exact vision equality for all pre-tail rows) RED observed
  (e.g. "P2 BTC: 3259/3260 pre-tail rows differ") -> rebuilt -> **GREEN: ALL MERGE PROPERTIES PASS (v2), EXIT=0**
  (BTC 3271/3271 vision_exact, ... MATIC 2179/2179; P1 BTC 2020-01-01 vol=16792.388165 exact).
- lint final: **12/12 PASS, EXIT=0**; manifest.csv written with n/start/end/gaps/vol_zero_or_blank=34 each.

## SPANS (exact, from lint)
| symb | n | start | end | vol NA (tail only) | gaps |
|------|---|-------|-----|-----|------|
| BTC  | 3305 | 2017-08-17 | 2026-09-03 | 34 | 0 |
| ETH  | 3168 | 2018-01-01 | 2026-09-03 | 34 | 0 |
| BNB  | 3224 | 2017-11-06 | 2026-09-03 | 34 | 0 |
| SOL  | 2215 | 2020-08-11 | 2026-09-03 | 34 | 0 |
| ADA  | 3062 | 2018-04-17 | 2026-09-03 | 34 | 0 |
| XRP  | 3045 | 2018-05-04 | 2026-09-03 | 34 | 0 |
| DOGE | 2378 | 2020-03-01 | 2026-09-03 | 34 | 0 |
| LTC  | 3187 | 2017-12-13 | 2026-09-03 | 34 | 0 |
| DOT  | 2208 | 2020-08-18 | 2026-09-03 | 34 | 0 |
| LINK | 2652 | 2019-06-01 | 2026-09-03 | 34 | 0 |
| AVAX | 2103 | 2020-12-01 | 2026-09-03 | 34 | 0 |
| MATIC| 2213 | 2020-08-01 | 2026-09-03 | 34 | 1 documented (2024-08-31->09-13) |

vol coverage: vision real volume for every pre-tail row (e.g. BTC 3271/3305; NA exactly = tail 34 days on every coin).

## HONEST assessment for campaign use
- BTC/LTC span 2017+ (8.9/8.7y): still NOT 2008+; cannot satisfy main 2008+ gates. NOT a champion-replacement domain.
- Candidate use: LOW-CORR SATELLITE. BTC+ETH alone give 2018+ ~8.5y common; 6 coins (BNB,ADA,XRP,LTC + BTC,ETH) give 2018+;
  full 12-coin panel only 2021+ (min span = AVAX 2020-12-24). 2017/2018 cohort (BTC,ETH,BNB,ADA,XRP,LTC,LINK) is the
  longest usable subset for TSMOM/carry-style tests with n>2000 daily bars.
- Vision dumps are monthly-lagged: re-run fetch_vision_vol.py + build_csv.py + tests to extend past 2026-07-31 later.
- twelvedata free tier rate limit hit once (429 on DOGE) -> waited 25s, retried OK; all fetches batched with 8s sleeps.

## Bugs found & root-caused (systematic-debugging, fix evidence in git/file trail)
1. Vision monthly klines switched open_timestamp precision ms->us for newer dumps (228/1066 files, 16-digit);
   build/test parsers normalize: ts/1e6 if ts>1e14 else ts/1000. Symptom: "year must be in 1..9999, not 56971".
2. TD MATIC 404 root cause: ticker renamed POL (Sep-2024 migration); but TD POL/USD pre-migration backfill is a
   different asset (ratio evidence above) — documented as TD data-quality defect.
3. fetch loop shell-cwd bug (relative .env.local path + doubled relative paths in background shell) — fixed with absolute paths.

DATA-ONLY per charter: no backtests run.
