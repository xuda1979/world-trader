# DATA_MORE_CRYPTO — download MORE free crypto + alt daily data (track C)

Existing: tools/quant/data/binance/{BTC,ETH}.csv (1000 rows, 2023-10+). Extend coverage with more
coins and longer history using working keys in .env.local (TWELVEDATA, FINNHUB) and/or public APIs.
Crypto is a potentially DECORRELATED daily engine family (low corr to equity/rates/commodities) —
the only caveat is short/missing history (need 2008+ for main gates; crypto 2020+ may still help as
a low-corr satellite; record the real span honestly).

Try in order (stop when one works):
1. Twelvedata: symbol=BTC,ETH,BNB,SOL,ADA,XRP,DOGE,LTC,DOT,LINK,AVAX,MATIC with interval=1day,
   outputsize up to 5000 (free tier).  Check they return full history.
2. Finnhub: crypto via symbol 'BINANCE:BTCUSDT' (candles endpoint) if twelvedata insufficient.
3. Binance public klines: https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=1000
   (no key; max 1000 bars per call — paginate with startTime to extend to 2017+ for BTC/ETH).
   NOTE: binance public may be geo-blocked; if so log it and use twelvedata.

DELIVER into tools/quant/data/more_crypto/<SYMB>.csv (date,open,high,low,close,vol + source tag in
.meta). For each: span lint (n, start/end, gaps), manifest.csv. Record spans in FINDINGS.md.
DATA-ONLY, no backtests. Be honest about data span (2020+ crypto cannot satisfy 2008+ gates, but
record it as a candidate low-corr satellite). Last line exactly: DATA_MORE_CRYPTO DONE
