# RES_ALTDATA FINDINGS — alt/regime engine from the NEW altlib data
> Chartered to build a decorrelated regime/CYCLICAL engine from DeFi TVL/activity, fear-greed.
> Honest verdict: **REJECT (fail-closed on the charter's short/incomplete-span rule).**

## Data (verified this session)
- tools/quant/data/altlib/: manifest + downloaded series. Spans:
  - fng/crypto_fg.csv (fear-greed): 2018-02-01..2026-09-08 (3,138 rows)
  - defi_tvl/* (eth, bitcoin, bsc, solana, tron, base, arbitrum, total): 2017-09..2026-09
  - defi_activity/dex_volume.csv: 2014-02..2026-09; proto_fees.csv: 2018-03..2026-09
- ALL alt-data starts 2014-2018 (none reaches back to the champion's 2008-03-31 window).

## Charter rule applied (fail-closed, verbatim)
> "WARNING: alt data often starts 2017+ (short span). If the series can't give a 2008+
> backtest, it's NOT champion-eligible — disclose the true in-sample window and REJECT if
> < the required span."  ... "Fail-closed on short/incomplete alt span."

## Verdict
**REJECT (fail-closed on span).** The NEW altlib data's earliest series (dex_volume) starts
2014-02; fear-greed and DeFi TVL start 2017-2018. The champion's backtest must run 2008-03-31+;
no altlib series provides even a 2008+ window, so none is champion-eligible. The data could
inform an optional LIVE/REGIME overlay (2020+ only) but provides NO historical champion sleeve.
This is the byte-honest outcome the charter's fail-closed rule exists to force.

RES_ALTDATA DONE
