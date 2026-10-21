# DATA_FREDMORE ROUND-1 MANIFEST (2026-09-06)
Fetcher: work_r1/fetch_fredmore.py (reuses fred_dl.fetch + fail-closed lint). 17 attempted, 13 PASS, 5 FAIL.

## PASS (written to tools/quant/data/more_fred/{id}.csv, [date,value])
| series | freq | role | start | end | n | note |
|---|---|---|---|---|---|---|
| VIXCLS | daily | eq vol idx (regime gates) | 2004-01-02 | 2026-09-03 | 5737 | pre-2004 CBOE publish holes => lint-failed, refetched from 2004 |
| T10Y2Y | daily | 2s10s curve | 1976-06-01 | 2026-09-04 | 12563 | |
| T5YIFR | daily | 5y5y fwd infl exp | 2003-01-02 | 2026-09-04 | 5924 | |
| DGS2 | daily | 2y CMT | 1976-06-01 | 2026-09-03 | 12562 | |
| DGS10 | daily | 10y CMT | 1962-01-02 | 2026-09-03 | 16154 | |
| DGS30 | daily | 30y CMT | 1977-02-15 | 2026-09-03 | 12384 | |
| AWHAETP | monthly | avg wkly hours | 2006-03-01 | 2026-08-01 | 246 | |
| CSUSHPISA | monthly | S&P/CS house price | 1987-01-01 | 2026-06-01 | 474 | |
| TOTALSL | monthly | consumer credit | 1943-01-01 | 2026-06-01 | 1002 | |
| IPMAN | monthly | mfg output | 1972-01-01 | 2026-07-01 | 655 | |
| DGORDER | monthly | durable goods orders | 1992-02-01 | 2026-07-01 | 414 | |
| USREC | monthly | NBER recession flag | 1854-12-01 | 2026-08-01 | 2061 | |
| HSN1F | monthly | new home sales | 1963-01-01 | 2026-07-01 | 763 | |

## FAIL (fail-closed lint, NOT written)
- NROU (quarterly): gaps=702 — series includes forecast rows to 2036, unusable as history.
- LNS11300060, IRLTLT01NZM156N, CPILFESL (monthly): gaps=1 each (isolated missing month).
Coverage notes: new daily CMT/DGS family completes the curve-construction set for HUNT_CREDIT2;
VIXCLS complements existing OVXCLS/GVZCLS/VXVCLS.
