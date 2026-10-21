# DATA_ETF_MORE ROUND-1 MANIFEST (2026-09-06)
Fetcher: work_r1/fetch_etf_more.py (TwelveData free tier, 8 req/min, fail-closed lint:
start<=2007-01-01, max gap<=10d, |ret|>50% <=3d). 20 attempted, 10 PASS, 10 FAIL.

## PASS (written to tools/quant/data/more_etf/{id}.csv, [date,close])
| sym | start | end | n | role |
|---|---|---|---|---|
| XLE | 2006-10-19 | 2026-09-04 | 5000 | sector energy (completes 11-SPDR set) |
| XLF | 2006-10-19 | 2026-09-04 | 5000 | sector financials |
| XLI | 2006-10-19 | 2026-09-04 | 5000 | sector industrials |
| XLB | 2006-10-19 | 2026-09-04 | 5000 | sector materials |
| LQD | 2006-10-19 | 2026-09-04 | 5000 | IG credit (HUNT_CREDIT2) |
| TLT | 2006-10-19 | 2026-09-04 | 5000 | 20y UST |
| IEF | 2006-10-19 | 2026-09-04 | 5000 | 7-10y UST |
| EWH | 2006-10-19 | 2026-09-04 | 5000 | HK country |
| EWM | 2006-10-19 | 2026-09-04 | 5000 | Malaysia country |
| GLD | 2006-10-19 | 2026-09-04 | 5000 | gold (more_etf previously lacked) |

## FAIL (fail-closed, NOT written; all start>2007-01-01)
HYG 2007-04, EWC 2008-01, EIS/TUR 2008-03, DBE 2007-01, EPHE 2010-09, USCI 2010-08, COPX 2010-04, DBP 2008-01, ENOR 2012-01
Note: HYG start 2007-04 is 3 months past the bound; usable for hunts if coordinator waives.
