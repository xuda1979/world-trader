# DATA_ALTLIB FINDINGS — 2026-09-08
Charter: no-key alt libraries -> NEW breadth/regime series, write only in tools/quant/data/altlib/.

## Gap check (what existed vs what was added)
- crypto_fg/, altme_fng/, coingecko_breadth/: manifests present but **0 data rows** (verified:
  manifests have only the header line) -> genuinely missing, filled.
- defillama_stables/ (per-coin stable supplies), more_crypto/, more_onchain/ (CoinMetrics),
  binance/ (2y OHLCV), deribit_dvol/, cnn_fg/ (250 rows 2025-09+), stocktwits/ (1 snapshot):
  already on disk -> NOT duplicated.

## Network reality (fail-closed, each probed fresh 2026-09-08)
| endpoint | result |
|---|---|
| api.alternative.me F&G | 200 OK, full history limit=0 |
| api.llama.fi (chains/historicalChainTvl/overview dexs+fees) | 200 OK |
| stablecoins.llama.fi | 200 OK (already covered by defillama_stables) |
| api.coinpaprika.com | connect TIMEOUT (15s) |
| api.coingecko.com + web-api host | connect TIMEOUT |
| fapi.binance.com / www.okx.com / api.bybit.com | connect TIMEOUT |
| api.kraken.com | Connection reset |
| api.exchange.coinbase.com | connect TIMEOUT |
| min-api.cryptocompare.com | 401 (key required) |
| push2.eastmoney.com | RemoteDisconnected (efinance unusable) |
| ml4t-data / coinpaprika / pycoingecko / efinance pip libs | not installed; wrappers point at blocked hosts anyway |

Charter libraries are HTTP wrappers over blocked hosts; I delivered their data via the reachable
no-key hosts (alternative.me, DeFiLlama) instead — same families, direct HTTP, no keys.

## Deliverable (all inside tools/quant/data/altlib/)
12 datasets, 3 families (manifest.csv rows, verified fresh below):
- fng/crypto_fg.csv — 3138 rows, 2018-02-01..2026-09-08, value 0-100 + classification
- defi_tvl/total.csv — 3269 rows, 2017-09-27..2026-09-08 (chain TVL USD)
- defi_tvl/{eth,bsc,solana,tron,arbitrum,base,bitcoin}.csv — 1182..3269 rows each
- defi_tvl/eth_dominance.csv — 3131 rows (eth/total share, zero-total days dropped)
- defi_activity/dex_volume.csv — 4587 rows from **2014-02-17** (long-span on-chain activity)
- defi_activity/proto_fees.csv — 3089 rows from 2018-03-26
All long-span breadths (sentiment, dominance, activity, TVL) usable for regime/decorrelation —
per charter, DATA-ONLY, no backtests.

## TDD (superpowers: RED -> GREEN)
- RED: test_altlib_dl.py written first; pytest -> collection error (module absent). Fresh output:
  `1 error during collection` -> then implemented altlib_dl.py.
- GREEN: `11 passed in 0.11s` (final run, fresh). Caught 1 real bug during RED->GREEN:
  alternative.me returns newest-first -> added sort in parse_fng (first live run failed lint
  `dates not sorted`, FAIL-CLOSED worked as designed; after fix, lint PASS 3138 rows).
- Fail-closed lint (min rows, NaN, all-NA, unsorted, dup dates) gates every write; every driver
  raise SystemExit / SKIP on lint failure.

## Fresh verification (this session, exact numbers)
- 12/12 CSVs: span listed above, nan=0, dup_dates=0, dates monotone (integration check output).
- Plausibility: FNG all in [0,100]; eth_dominance max=1.000.
- manifest.csv rebuilt via build_manifest.py: 12 datasets, 0 exceptions (no SHORT/RAGGED).
- pytest final: 11 passed. File lengths: altlib_dl.py 105, drivers 18-38 lines (all < 200).

## Limitations / honesty
- eth_dominance first date (2018-02-12) ≠ total's (2017-09-27): DeFiLlama ETH chain history has
  leading zero-total days dropped by design (no div/0) — documented, not a bug.
- base.csv 1182 rows (chain launched 2023-06); lint min lowered only for chains (180) — noted.
- Blocked hosts are environment facts, not permanent: re-run probes if network changes.

DATA_ALTLIB DONE
