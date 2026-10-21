# HUNT_CRYPTO_SAT — low-correlation crypto satellite (iter 7.5)

PREMISE: crypto (BTC/ETH/...) is genuinely DECORRELATED from the champion (equity/rates/commodities/
FX). NEW DATA: tools/quant/data/more_crypto/{BTC,ETH,BNB,SOL,ADA,XRP,DOGE,LTC,DOT,LINK,AVAX,MATIC}.csv
+ .meta (Binance Vision real prints, full OHLCV; BTC 2017-08+, most 2020+). This is a SATELLITE due to
short history — it CANNOT satisfy 2008+ yearly gates. Test honestly and disclose span.

READ FIRST: campaign/results/DEAD_IDEAS.csv, campaign/GOAL100_FINAL_STATE.md.

## METHOD (superpowers TDD; use campaign/bt engine/metrics/gates/reconcile)
1. Build TS-momentum (lb 21/63/126) and short-term reversal (lb 1/3/5) L/S or single-asset books on
   the crypto panel, T+1, vt10 expanding-60 cap3, 6.4bps/side, borrow 0 (spot, no shortable; only LONG
   satellite is honest — crypto shorting is costly/limited, so test LONG-only and L/S-paper separately
   and disclose that shorts are unrealistic).
2. Span: report SR/H1/H2/neg-yrs/MDD on the actual crypto span (2017+/2020+), AND on the overlap with
   the champion (corr to GOAL100_HONEST14V3_BALANCED). Corr is the KEY value: aim |corr|<0.10.
3. If a long-only crypto TSMOM satellite has SR>=0.6 on its own span, low corr, and adds diversification
   (test adding it at slot w<=0.10 to the RAW-EW13@1.6x blend: does blended SR/risk improve without
   violating lev<=1.6 or 0-neg?), deliver it as a sleeve. Else log exact numbers as negative.
4. Trade-record: instrument = BTC/ETH/... spot (price path = more_crypto/X.csv close), price_source
   REAL; note crypto not shortable at retail 6.4bps => long-only realistic.

DELIVER: sleeves/*.csv+meta + repro + FINDINGS.md gate cards (exact span-capped numbers, corr, blended
effect). Be brutally honest about the short-history limitation. Last line exactly: HUNT_CRYPTO_SAT DONE
