# Validation: 2026-10-19

The target GitHub repository was empty when this work began. There was no existing trading strategy,
test suite, or backtest to integrate or benchmark. This change establishes the data-ingestion package.

## Deterministic tests

`python -m unittest discover -v`: **58 tests passed** on Python 3.12.14.
Fixtures are explicitly synthetic and test normalization, pagination and truncation, transient errors,
Retry-After seconds and HTTP dates, denied access, secret redaction, cache expiration/offline replay,
cross-connection throttling, revision selection, publication/vintage/first-seen clocks, and CLI exports.
No network or credentials are used by these tests. CI also runs Python 3.11 and 3.13.

Packaging was built and installed with `pip install --no-build-isolation --no-deps --target <temporary-dir> .`.
Both `python -m world_trader sources` and the installed `world-trader sources` entry point succeeded
from outside the checkout. `python -m compileall -q world_trader tests` succeeded.

## Actual API requests

A new empty database was used with `--refresh`, followed by offline replay. The run finished at
2026-10-19T04:08:40Z (12:08:40 China Standard Time). The machine-readable report is
[live-smoke-2026-10-19.json](live-smoke-2026-10-19.json).

| Collector | Real query | Normalized records | Result |
|---|---|---:|---|
| World Bank | USA GDP growth, 2020–2023 | 4 | Passed live fetch, storage, and cached replay |
| BLS | LNS14000000, v1 recent window | 33 | Passed; `-` observation retained as null with footnote |
| ClinicalTrials.gov | Industry-sponsored study NCT07281105, projected metadata | 1 | Passed live fetch, storage, and cached replay |
| SEC submissions | CIK 0000320193, recent default-form events | 145 | Passed live fetch, storage, and cached replay |
| SEC XBRL | CIK 0000320193, us-gaap/Assets, USD | 146 | Passed live fetch, storage, and cached replay |
| FRED/ALFRED | UNRATE historical vintage | — | Skipped: FRED_API_KEY not configured; fixture tests passed |
| CoinGecko Demo | Bitcoin 1-day charts | — | Skipped: COINGECKO_DEMO_API_KEY not configured; fixture tests passed |
| Finnhub | AAPL company news | — | Skipped: FINNHUB_API_KEY not configured; fixture tests passed |

**329 real records** were inserted into the new database. Replaying each query from the response cache
produced identical records and zero additional revisions. The audit recorded five successful network
requests and five cache hits. The first exploratory run exposed BLS's `-` missing-value marker;
the adapter was corrected, a regression test added, and the new-database smoke run above passed.

SEC requests used an identifiable project User-Agent with the public repository issues URL as contact.
Operators should configure their own organization and monitored contact email, as described in the README.
No subscription keys were invented, borrowed, or embedded. Initial CoinGecko keyless ping connectivity
was observed, but it is **not** counted as validation of the credentialed Demo chart collector.

A CLI `asof` query against the collected World Bank series at 2024-01-01T00:00:00Z returned zero rows.
At 2026-10-20T00:00:00Z it exported four CSV observations. This checks the first-seen guard on the
actual collected records; it does not establish full historical point-in-time coverage.

## Limits of this result

Successful ingestion establishes endpoint connectivity and the checked normalization/replay paths.
It does not establish predictive alpha, completeness across companies/dates, economic units for every
provider series, a historical clinical-status panel, 13F holdings extraction, or real-money strategy results.
The three credentialed free-tier adapters need an operator-key live check before operational use.
No raw API caches, news payloads, populated credentials, or personal contact datasets are checked in.
